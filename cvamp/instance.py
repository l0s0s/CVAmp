import datetime
import logging
import threading

from playwright.sync_api import sync_playwright
from abc import ABC


from . import utils, stealth

logger = logging.getLogger(__name__)


class Instance(ABC):
    site_name = "BASE"
    site_url = None
    instance_lock = threading.Lock()
    supported_sites = dict()

    def __init__(
        self,
        proxy_dict,
        target_url,
        status_reporter,
        location_info=None,
        headless=False,
        auto_restart=False,
        low_cpu=False,
        instance_id=-1,
    ):
        self.playwright = None
        self.context = None
        self.browser = None
        self.status_info = {}
        self.status_reporter = status_reporter
        self.thread = threading.current_thread()

        self.id = instance_id
        self._status = "alive"
        self.proxy_dict = proxy_dict
        self.target_url = target_url
        self.headless = headless
        self.auto_restart = auto_restart
        self.low_cpu = low_cpu

        self.last_restart_dt = datetime.datetime.now()

        self.location_info = location_info
        if not self.location_info:
            self.location_info = {
                "index": -1,
                "x": 0,
                "y": 0,
                "width": 500,
                "height": 300,
                "free": True,
            }

        self.command = None
        self.pending_chat_message = None
        self.page = None

    def __init_subclass__(cls, **kwargs):
        if cls.site_name != "UNKNOWN":
            cls.supported_sites[cls.site_url] = cls

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, new_status):
        if self._status == new_status:
            return

        self._status = new_status
        self.status_reporter(self.id, new_status)

    def clean_up_playwright(self):
        if any([self.page, self.context, self.browser]):
            try:
                if self.page:
                    self.page.close()
            except Exception:
                pass
            try:
                if self.context:
                    self.context.close()
            except Exception:
                pass
            try:
                if self.browser:
                    self.browser.close()
            except Exception:
                pass
            try:
                if self.playwright:
                    self.playwright.stop()
            except Exception:
                pass

    def start(self):
        try:
            self.spawn_page()
            self.todo_after_spawn()
            self.loop_and_check()
        except Exception as e:
            message = e.args[0][:25] if e.args else ""
            logger.exception(f"{e} died at page {self.page.url if self.page else None}")
            print(f"{self.site_name} Instance {self.id} died: {type(e).__name__}:{message}... Please see cvamp.log.")
        else:
            logger.info(f"ENDED: instance {self.id}")
            with self.instance_lock:
                print(f"Instance {self.id} shutting down")
        finally:
            self.status = utils.InstanceStatus.SHUTDOWN
            self.clean_up_playwright()
            self.location_info["free"] = True

    def loop_and_check(self):
        page_timeout_s = 10
        while True:
            self.page.wait_for_timeout(page_timeout_s * 1000)
            self.todo_every_loop()
            self.update_status()

            if self.command == utils.InstanceCommands.RESTART:
                self.clean_up_playwright()
                self.spawn_page(restart=True)
                self.todo_after_spawn()
            elif self.command == utils.InstanceCommands.SCREENSHOT:
                print("Saved screenshot of instance id", self.id)
                self.save_screenshot()
            elif self.command == utils.InstanceCommands.REFRESH:
                print("Manual refresh of instance id", self.id)
                self.reload_page()
            elif self.command == utils.InstanceCommands.CHAT:
                if self.pending_chat_message:
                    print(f"Instance {self.id} sending chat message: {self.pending_chat_message}")
                    self.send_chat(self.pending_chat_message)
                    self.pending_chat_message = None
            elif self.command == utils.InstanceCommands.EXIT:
                return
            self.command = utils.InstanceCommands.NONE

    def save_screenshot(self):
        filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + f"_instance{self.id}.png"
        self.page.screenshot(path=filename)

    def spawn_page(self, restart=False):
        chromium_args = stealth.get_stealth_chromium_args(
            location_x=self.location_info["x"],
            location_y=self.location_info["y"],
            headless=self.headless,
            low_cpu=self.low_cpu,
        )

        proxy_dict = self.proxy_dict if self.proxy_dict else None

        self.status = utils.InstanceStatus.RESTARTING if restart else utils.InstanceStatus.STARTING

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            proxy=proxy_dict,
            channel="chrome",
            headless=False,
            args=chromium_args,
        )

        major_version = self.browser.version.split(".")[0]
        self.context = self.browser.new_context(
            viewport={"width": 800, "height": 600},
            user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
            color_scheme="dark",
            proxy=proxy_dict,
        )

        stealth.apply_stealth_to_context(self.context)
        self.page = self.context.new_page()
        stealth.apply_stealth_to_page(self.page)

        if self.low_cpu:
            def route_interceptor(route):
                resource_type = route.request.resource_type
                if resource_type in ["image", "media", "font"]:
                    route.abort()
                else:
                    route.continue_()

            try:
                self.page.route("**/*", route_interceptor)
            except Exception as e:
                logger.warning(f"Failed to set route interceptor for low_cpu: {e}")

    def goto_with_retry(self, url, max_tries=3, timeout=20000):
        """
        Tries to navigate to a page max_tries times. Raises the last exception if all attempts fail.
        """
        for attempt in range(1, max_tries + 1):
            try:
                self.page.goto(url, timeout=timeout)
                return
            except Exception:
                logger.warning(f"Instance {self.id} failed connection attempt #{attempt}.")
                if attempt == max_tries:
                    raise

    def todo_after_load(self):
        self.goto_with_retry(self.target_url)
        self.page.wait_for_timeout(1000)

    def reload_page(self):
        self.page.reload(timeout=30000)
        self.todo_after_load()

    def todo_after_spawn(self):
        """
        Basic behaviour after a page is spawned. Override for more functionality
        e.g. load cookies, additional checks before instance is truly called "initialized"
        :return:
        """
        self.status = utils.InstanceStatus.INITIALIZED
        self.goto_with_retry(self.target_url)

    def todo_every_loop(self):
        """
        Add behaviour to be executed every loop
        e.g. to fake page interaction to not count as inactive to the website.
        """
        pass

    def update_status(self) -> None:
        """
        Mechanism is called every loop. Figure out if it is watching and working and updated status.
        if X:
            self.status = utils.InstanceStatus.WATCHING
        """
        pass

    def send_chat(self, message: str) -> bool:
        """
        Send a chat message to the active stream.
        """
        try:
            if not self.page:
                return False
            # Generic chat input fallback
            chat_inputs = [
                'textarea[data-a-target="chat-input"]',
                'div[data-a-target="chat-input"]',
                'input#message-input',
                'textarea#message-input',
                'div[contenteditable="true"]',
                'input[placeholder*="chat" i]',
                'textarea[placeholder*="chat" i]',
            ]
            for selector in chat_inputs:
                if self.page.query_selector(selector):
                    self.page.click(selector)
                    self.page.fill(selector, message)
                    self.page.keyboard.press("Enter")
                    logger.info(f"Instance {self.id} sent message via {selector}")
                    return True
        except Exception as e:
            logger.warning(f"Instance {self.id} failed to send chat message: {e}")
        return False
