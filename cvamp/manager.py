import datetime
import logging
import os
import platform
import random
import threading
import time

from . import logger_config, utils, sites
from .instance import Instance

logger_config.setup()
from .accounts import AccountGetter
from .proxy import ProxyGetter
from .screen import Screen
from .service import RestartChecker
from .utils import InstanceCommands

logger = logging.getLogger(__name__)


class InstanceManager:
    def __init__(
        self,
        spawn_thread_count,
        delete_thread_count,
        headless,
        auto_restart,
        proxy_file_name,
        spawn_interval_seconds=2,
        target_url=None,
        low_cpu=False,
    ):
        logger.info(f"Manager start on {platform.platform()}")

        self._spawn_thread_count = spawn_thread_count
        self._delete_thread_count = delete_thread_count
        self._headless = headless
        self._auto_restart = auto_restart
        self._low_cpu = low_cpu
        self.proxies = ProxyGetter(proxy_file_name)
        self.accounts = AccountGetter("accounts.txt")
        self.spawn_interval_seconds = spawn_interval_seconds
        self.target_url = target_url

        self.manager_lock = threading.Lock()
        self.screen = Screen(window_width=500, window_height=300)
        self.browser_instances = {}

        self.instances_overview = dict()
        self.instances_alive_count = 0
        self.instances_watching_count = 0

        self.restart_checker = RestartChecker(manager=self, restart_interval_s=1200)

        # Chat and AutoChat configurations
        self.auto_chat_enabled = False
        self.chat_message = ""
        self.chat_interval_min = 30
        self.chat_interval_max = 60
        self._autochat_thread = None
        self._autochat_stop_event = threading.Event()

    def get_headless(self) -> bool:
        return self._headless

    def set_headless(self, new_value: bool):
        self._headless = new_value

    def get_auto_restart(self) -> bool:
        return self._auto_restart

    def set_auto_restart(self, new_value: bool):
        logger.info(f"Setting auto-restart to " + str(new_value))
        self._auto_restart = new_value
        self.reconfigure_auto_restart_status()

    def get_low_cpu(self) -> bool:
        return self._low_cpu

    def set_low_cpu(self, new_value: bool):
        logger.info(f"Setting low_cpu mode to {new_value}")
        self._low_cpu = new_value

    def set_autochat(self, enabled: bool, message: str = "", interval_min: int = 30, interval_max: int = 60):
        self.auto_chat_enabled = enabled
        self.chat_message = message
        self.chat_interval_min = max(5, interval_min)
        self.chat_interval_max = max(self.chat_interval_min, interval_max)

        if enabled:
            if not self._autochat_thread or not self._autochat_thread.is_alive():
                self._autochat_stop_event.clear()
                self._autochat_thread = threading.Thread(target=self._autochat_worker, daemon=True)
                self._autochat_thread.start()
                logger.info("AutoChat thread started.")
        else:
            self._autochat_stop_event.set()
            logger.info("AutoChat thread stopped.")

    def _autochat_worker(self):
        while not self._autochat_stop_event.is_set():
            delay = random.randint(self.chat_interval_min, self.chat_interval_max)
            if self._autochat_stop_event.wait(delay):
                break
            if self.auto_chat_enabled and self.chat_message:
                self.send_chat_message(self.chat_message)

    def send_chat_message(self, message: str, instance_id=None):
        if not message:
            return
        with self.manager_lock:
            active_instances = [
                inst for inst in self.browser_instances.values()
                if inst.status != utils.InstanceStatus.SHUTDOWN
            ]
            if not active_instances:
                print("No active instances to send chat message.")
                return

            if instance_id is not None:
                if instance_id in self.browser_instances:
                    target_inst = self.browser_instances[instance_id]
                    target_inst.pending_chat_message = message
                    target_inst.command = InstanceCommands.CHAT
            else:
                # Send to random active instance
                target_inst = random.choice(active_instances)
                target_inst.pending_chat_message = message
                target_inst.command = InstanceCommands.CHAT

    def __del__(self):
        print("Deleting manager: cleaning up instances", datetime.datetime.now())
        self._autochat_stop_event.set()
        self.delete_all_instances()
        print("Manager shutting down", datetime.datetime.now())

    def update_instances_alive_count(self):
        alive_instances = filter(
            lambda instance: instance.status != utils.InstanceStatus.SHUTDOWN, self.browser_instances.values()
        )
        self.instances_alive_count = len(list(alive_instances))

    def reconfigure_auto_restart_status(self):
        if self.instances_alive_count and self._auto_restart:
            self.restart_checker.start()
        else:
            self.restart_checker.stop()

    def update_instances_watching_count(self):
        self.instances_watching_count = len(
            [1 for instance in self.browser_instances.values() if instance.status == utils.InstanceStatus.WATCHING]
        )

    def update_instances_overview(self):
        new_overview = {}
        for instance_id, instance in self.browser_instances.items():
            if instance.status != utils.InstanceStatus.SHUTDOWN:
                new_overview[instance_id] = instance.status

        self.instances_overview = new_overview

    def spawn_instances(self, n, target_url=None):
        for _ in range(n):
            self.spawn_instance(target_url)
            time.sleep(self.spawn_interval_seconds)

    def get_site_class(self, target_url):
        for site_name, site_class in Instance.supported_sites.items():
            if site_name in target_url:
                return site_class

        return sites.Unknown

    def spawn_instance(self, target_url=None):
        if not self.browser_instances:
            browser_instance_id = 1
        else:
            browser_instance_id = max(self.browser_instances.keys()) + 1

        t = threading.Thread(
            target=self.spawn_instance_thread,
            args=(target_url, self.instance_status_report_callback, browser_instance_id),
            daemon=True,
        )
        t.start()

    def instance_status_report_callback(self, instance_id, instance_status):
        # self.instances_overview[instance_id] = instance_status
        # for now simply triggers the manager to refresh status for all instances
        # maybe track status in separate list, where instances report to
        # and shutdown instances issue remove on dict with instance id
        # his would allow the removal of "instance.status != "shutdown"" in update_instances_alive_count

        logger.info(f"{instance_status.value.upper()} instance {instance_id}")

        self.update_instances_overview()
        self.update_instances_alive_count()
        self.update_instances_watching_count()
        self.reconfigure_auto_restart_status()

    def spawn_instance_thread(self, target_url, status_reporter, browser_instance_id):
        if not any([target_url, self.target_url]):
            raise Exception("No target target url provided")

        if not target_url:
            target_url = self.target_url

        with self.manager_lock:
            proxy = self.proxies.get_proxy_as_dict()

            if self._headless:
                screen_location = self.screen.get_default_location()
            else:
                screen_location = self.screen.get_free_screen_location()

            if not screen_location:
                print("no screen space left")
                return

            site_class = self.get_site_class(target_url)
            account = self.accounts.get_account(site_class.site_name)

            server_ip = proxy.get("server", "no proxy")
            logger.info(
                f"Ordered {site_class.site_name} instance {browser_instance_id}, {threading.currentThread().name}, proxy {server_ip}, auth: {bool(account)}"
            )

            browser_instance = site_class(
                proxy,
                target_url,
                status_reporter,
                location_info=screen_location,
                headless=self._headless,
                auto_restart=self._auto_restart,
                low_cpu=self._low_cpu,
                account_dict=account,
                instance_id=browser_instance_id,
            )

            self.browser_instances[browser_instance_id] = browser_instance

        browser_instance.start()

        if browser_instance_id in self.browser_instances:
            del browser_instance
            self.browser_instances.pop(browser_instance_id)

    def queue_command(self, instance_id: int, command: InstanceCommands) -> bool:
        if instance_id not in self.browser_instances:
            return False

        self.browser_instances[instance_id].command = command

    def delete_latest(self):
        if not self.browser_instances:
            print("No instances found")
            return

        latest_key = max(self.browser_instances.keys())
        self.delete_specific(latest_key)

    def delete_specific(self, instance_id):
        if instance_id not in self.browser_instances:
            print(f"Instance ID {instance_id} not found. Unable to shutdown.")
            return

        instance = self.browser_instances[instance_id]
        print(f"Issuing shutdown of instance #{instance_id}")
        instance.command = InstanceCommands.EXIT

    def delete_all_instances(self):
        for instance_id in self.browser_instances:
            self.delete_specific(instance_id)
