import datetime
import logging
import os
import sys
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


import psutil
import toml

from . import utils
from .manager import InstanceManager
from .utils import InstanceCommands

logger = logging.getLogger(__name__)


def open_multiple_urls(*urls):
    """Open multiple URLs in order with small delays"""
    for url in urls:
        webbrowser.open(url, new=2)
        time.sleep(0.1)

system_default_color = None


class GUI:
    def __init__(self, manager: InstanceManager):
        self.manager = manager
        self.instances_boxes = []

        self.root = tk.Tk()
        self.menu = tk.Menu(self.root)

        self.instances_overview = dict()

        style = ttk.Style()
        style.configure("TNotebook", padding=[0, 0, -2, -2], tabmargins=[-1, 0, 0, 0])

        # Initialize tabs
        self.notebook = ttk.Notebook(self.root, height=120, width=600)

        self.tab_main = TabMain(self.notebook, self.manager)
        self.notebook.add(self.tab_main, text="Main Controls")

        self.tab_chat = TabChat(self.notebook, self.manager)
        self.notebook.add(self.tab_chat, text="Chatting")

        self.tab_about = TabAbout(self.notebook)
        self.notebook.add(self.tab_about, text="About")

        self.notebook.place(x=0, y=0)
        self.notebook.select(self.tab_main)

        # path to use, when the tool is not package with pyinstaller -onefile
        non_pyinstaller_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

        # Pyinstaller fix to find added binaries in extracted project folder in TEMP
        path_to_binaries = getattr(sys, "_MEIPASS", non_pyinstaller_path)  # default to last arg
        path_to_icon = os.path.abspath(os.path.join(path_to_binaries, "cvamp_logo.ico"))

        if os.name == "nt" and os.path.exists(path_to_icon):
            try:
                self.root.iconbitmap(path_to_icon)
            except Exception:
                pass

        path_to_toml = os.path.abspath(os.path.join(path_to_binaries, "pyproject.toml"))
        version = "0.8.0"
        if os.path.exists(path_to_toml):
            try:
                version = toml.load(path_to_toml).get("tool", {}).get("poetry", {}).get("version", "0.8.0")
            except Exception:
                pass
        self.root.title(f"Crude Viewer Amplifier PRO | v{version} | kevin@blueloperlabs.ch")

    def run(self):
        self.root.geometry("600x335+500+500")
        self.root.resizable(False, False)

        # mid text box
        text_area = ScrolledText(self.root, height="7", width="92", font=("regular", 8))
        text_area.place(
            x=20,
            y=145,
        )

        for row in range(5):
            for col in range(50):
                box = InstanceBox(
                    self.manager,
                    self.root,
                    bd=0.5,
                    relief="raised",
                    width=10,
                    height=10,
                )
                box.place(x=24 + col * 11, y=255 + row * 12)
                self.instances_boxes.append(box)

        # bottom
        lbl = tk.Label(
            self.root,
            text=r"blueloperlabs.ch/cvamp",
            fg="blue",
            cursor="hand2",
        )
        lbl.bind("<Button-1>", lambda event: webbrowser.open("https://blueloperlabs.ch/cvamp/tf"))
        lbl.place(x=230, y=315)

        # redirect stdout
        def redirector(str_input):
            if self:
                text_area.configure(state="normal")
                text_area.insert(tk.END, str_input)
                text_area.see(tk.END)
                text_area.configure(state="disabled")
            else:
                sys.stdout = sys.__stdout__

        sys.stdout.write = redirector

        self.refresher_start()

        self.root.mainloop()

    def refresher_start(self):
        if not self.instances_overview == self.manager.instances_overview:
            self.instances_overview = self.manager.instances_overview.copy()

            for (id, status), box in zip(self.instances_overview.items(), self.instances_boxes):
                box.modify(status, id)

            for index in range(len(self.instances_overview), len(self.instances_boxes)):
                self.instances_boxes[index].modify(utils.InstanceStatus.INACTIVE, None)

            self.tab_main.alive_instances.configure(text=self.manager.instances_alive_count)
            self.tab_main.watching_instances.configure(text=str(self.manager.instances_watching_count))

        self.tab_main.cpu_usage_text.configure(text=" {:.2f}% CPU".format(psutil.cpu_percent()))
        self.tab_main.ram_usage_text.configure(text=" {:.2f}% RAM".format(psutil.virtual_memory().percent))

        self.root.after(750, self.refresher_start)


class TabChat(tk.Frame):
    def __init__(self, parent, manager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.chat_timer_start_value = tk.StringVar(value="30")
        self.chat_timer_stop_value = tk.StringVar(value="60")
        self.parent = parent
        self.manager = manager
        self.auto_chat_enabled = tk.BooleanVar(value=False)

        manual = ttk.Labelframe(self, text='Manual Chat (PRO Unlocked)', name='manual')
        manual.place(y=5, x=10, relwidth=0.96, height=50)

        self.chat_message_box = tk.Entry(manual, width=42, name="chat_message_box")
        self.chat_message_box.place(x=10, y=3)
        self.chat_message_box.insert(0, "Hello streamer! GG")

        send_button = tk.Button(
            manual,
            width=12,
            text="Send msg",
            command=self.send_manual_message,
        )
        send_button.place(x=360, y=0)

        send_all_button = tk.Button(
            manual,
            width=12,
            text="Send to all",
            command=self.send_manual_message_all,
        )
        send_all_button.place(x=465, y=0)

        auto_frame = ttk.Labelframe(self, text='Auto Chat (PRO Unlocked)')
        auto_frame.place(y=60, x=10, relwidth=0.96, height=50)

        chat_switch = ttk.Checkbutton(
            auto_frame,
            variable=self.auto_chat_enabled,
            text="Autochat enabled",
            command=self.toggle_autochat,
        )
        chat_switch.place(x=10, y=3)

        self.chat_timer_start = tk.Spinbox(
            auto_frame,
            from_=5,
            to=600,
            wrap=True,
            width=4,
            increment=5,
            textvariable=self.chat_timer_start_value,
            command=self.toggle_autochat,
        )
        self.chat_timer_start.place(x=140, y=3)

        self.chat_timer_stop = tk.Spinbox(
            auto_frame,
            from_=5,
            to=600,
            wrap=True,
            width=4,
            increment=5,
            textvariable=self.chat_timer_stop_value,
            command=self.toggle_autochat,
        )
        self.chat_timer_stop.place(x=185, y=3)

        chat_interval_text = tk.Label(auto_frame, text="Range (s)", borderwidth=1)
        chat_interval_text.place(x=230, y=3)

        send_auto_chat_button = tk.Button(
            auto_frame,
            width=16,
            text="Send one message",
            command=self.send_manual_message,
        )
        send_auto_chat_button.place(x=410, y=0)

    def get_message(self) -> str:
        return self.chat_message_box.get().strip()

    def send_manual_message(self):
        msg = self.get_message()
        if msg:
            threading.Thread(target=self.manager.send_chat_message, args=(msg,)).start()

    def send_manual_message_all(self):
        msg = self.get_message()
        if msg:
            def _send_all():
                with self.manager.manager_lock:
                    instance_ids = list(self.manager.browser_instances.keys())
                for i_id in instance_ids:
                    self.manager.send_chat_message(msg, instance_id=i_id)
                    time.sleep(0.5)
            threading.Thread(target=_send_all).start()

    def toggle_autochat(self):
        try:
            start_val = int(self.chat_timer_start_value.get())
            stop_val = int(self.chat_timer_stop_value.get())
        except ValueError:
            start_val, stop_val = 30, 60
        self.manager.set_autochat(
            enabled=self.auto_chat_enabled.get(),
            message=self.get_message(),
            interval_min=start_val,
            interval_max=stop_val,
        )


class TabMain(tk.Frame):
    def __init__(self, parent, manager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.manager = manager
        self.headless = tk.BooleanVar(value=manager.get_headless())
        self.auto_restart = tk.BooleanVar(value=manager.get_auto_restart())
        self.block_video_checkbox_value = tk.BooleanVar(value=manager.get_low_cpu())

        global system_default_color
        system_default_color = self.cget("bg")

        separator_left = ttk.Separator(self, orient="vertical")
        separator_left.place(x=170, relx=0, rely=0, relwidth=0.2, relheight=1)
        separator_right = ttk.Separator(self, orient="vertical")
        separator_right.place(x=-170, relx=1, rely=0, relwidth=0.2, relheight=1)

        # left
        proxy_available_text = tk.Label(self, text="Proxies Available", borderwidth=2)
        proxy_available_text.place(x=40, y=10)
        proxy_available = tk.Label(self, text="0", borderwidth=2, relief="solid", width=5)
        proxy_available.place(x=70, y=40)
        proxy_available.configure(text=len(self.manager.proxies.proxy_list))

        lbl_buy = tk.Label(self, text="(buy more)", fg="blue", cursor="hand2")
        lbl_buy.bind(
            "<Button-1>",
            lambda event: threading.Thread(
                target=open_multiple_urls,
                args=(
                    "https://blueloperlabs.ch/proxy/tf",
                    "https://blueloperlabs.ch/proxy-ps/tf",
                    "https://github.com/KevinBytesTheDust/cvamp/wiki/Webshare.io-Proxies-Guide",
                ),
            ).start(),
        )
        lbl_buy.place(x=58, y=62)

        headless_checkbox = ttk.Checkbutton(
            self,
            text="headless",
            variable=self.headless,
            command=lambda: self.manager.set_headless(self.headless.get()),
            onvalue=True,
            offvalue=False,
        )
        headless_checkbox.place(x=180, y=94)

        auto_restart_checkbox = ttk.Checkbutton(
            self,
            variable=self.auto_restart,
            text="auto restart",
            command=lambda: self.manager.set_auto_restart(self.auto_restart.get()),
            onvalue=True,
            offvalue=False,
        )
        auto_restart_checkbox.place(x=255, y=94)

        block_video_checkbox = ttk.Checkbutton(
            self,
            text="low cpu",
            onvalue=True,
            offvalue=False,
            variable=self.block_video_checkbox_value,
            command=lambda: self.manager.set_low_cpu(self.block_video_checkbox_value.get()),
            state=tk.NORMAL,
        )
        block_video_checkbox.place(x=344, y=94)

        # right
        instances_text = tk.Label(self, text="Instances", borderwidth=2)
        instances_text.place(x=455, y=10)

        alive_instances_text = tk.Label(self, text="alive", borderwidth=2)
        alive_instances_text.place(x=455, y=40)
        watching_instances_text = tk.Label(self, text="watching", borderwidth=2)
        watching_instances_text.place(x=455, y=60)

        self.alive_instances = tk.Label(self, text=0, borderwidth=2, relief="solid", width=5)
        self.alive_instances.place(x=530, y=40)
        self.watching_instances = tk.Label(self, text=0, borderwidth=2, relief="solid", width=5)
        self.watching_instances.place(x=530, y=60)

        self.cpu_usage_text = tk.Label(self, text="CPU", borderwidth=2)
        self.cpu_usage_text.place(x=440, y=88)
        self.ram_usage_text = tk.Label(self, text="RAM", borderwidth=2)
        self.ram_usage_text.place(x=510, y=88)

        # mid log
        channel_url = tk.Entry(self, width=40, name="channel_url_entry")
        channel_url.place(x=180, y=10)
        channel_url.insert(0, "https://www.twitch.tv/channel_name")

        spawn_one = tk.Button(
            self,
            width=15,
            anchor="w",
            text="Spawn 1 instance",
            command=lambda: self.spawn_one_func(),
        )
        spawn_one.place(x=180, y=35)
        spawn_three = tk.Button(
            self,
            width=15,
            anchor="w",
            text="Spawn 3 instances",
            command=lambda: self.spawn_three_func(),
        )
        spawn_three.place(x=180, y=65)
        destroy_one = tk.Button(
            self,
            width=15,
            anchor="w",
            text="Destroy 1 instance",
            command=lambda: self.delete_one_func(),
        )
        destroy_one.place(x=305, y=35)
        destroy_all = tk.Button(
            self,
            width=15,
            anchor="w",
            text="Destroy all instances",
            command=lambda: self.delete_all_func(),
        )
        destroy_all.place(x=305, y=65)

    def __del__(self):
        print("Gui shutting down", datetime.datetime.now())

    def spawn_one_func(self):
        print("Spawning one instance. Please wait for alive & watching instances increase.")
        target_url = self.nametowidget("channel_url_entry").get()
        threading.Thread(target=self.manager.spawn_instance, args=(target_url,)).start()

    def spawn_three_func(self):
        print("Spawning three instances. Please wait for alive & watching instances increase.")
        target_url = self.nametowidget("channel_url_entry").get()
        threading.Thread(target=self.manager.spawn_instances, args=(3, target_url)).start()

    def delete_one_func(self):
        print("Destroying one instance. Please wait for alive & watching instances decrease.")
        threading.Thread(target=self.manager.delete_latest).start()

    def delete_all_func(self):
        print("Destroying all instances. Please wait for alive & watching instances decrease.")
        threading.Thread(target=self.manager.delete_all_instances).start()


class TabAbout(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        info_text = tk.Label(
            self,
            text="CVAmp - PRO Full Edition (Unlocked)\n"
            "All PRO features (Manual/Auto Chat, Low CPU mode, Browser Stealth Anti-Detection) are active.\n"
            "Spawns low-resolution muted Chrome instances with proxy & anti-detection masking.",
            borderwidth=2,
            justify="center",
        )
        info_text.place(relx=0.5, y=10, anchor="n")

        lbl_buy = tk.Label(self, text="Proxy Setup & Guide", fg="blue", cursor="hand2")
        lbl_buy.bind(
            "<Button-1>",
            lambda event: threading.Thread(
                target=open_multiple_urls,
                args=(
                    "https://blueloperlabs.ch/proxy/tf",
                    "https://blueloperlabs.ch/proxy-ps/tf",
                    "https://github.com/KevinBytesTheDust/cvamp/wiki/Webshare.io-Proxies-Guide",
                ),
            ).start(),
        )
        lbl_buy.place(relx=0.5, y=75, anchor="n")


class InstanceBox(tk.Frame):
    def __init__(self, manager, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.instance_id = None
        self.manager = manager

        self.bind(
            "<Button-1>", lambda event: self.manager.queue_command(self.instance_id, InstanceCommands.REFRESH)
        )  # left click
        self.bind(
            "<Button-3>", lambda event: self.manager.queue_command(self.instance_id, InstanceCommands.EXIT)
        )  # right click
        self.bind(
            "<Control-1>", lambda event: self.manager.queue_command(self.instance_id, InstanceCommands.SCREENSHOT)
        )  # control left click

    def modify(self, status, instance_id):
        self.instance_id = instance_id

        # todo: enum
        color_codes = {
            "inactive": system_default_color,
            "starting": "grey",
            "initialized": "yellow",
            "restarting": "yellow",
            "buffering": "yellow",
            "watching": "#44d209",
            "shutdown": system_default_color,
        }

        color = color_codes[status.value]
        self.configure(background=color)
