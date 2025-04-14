import requests
import os
import json
import threading
import time
import translations  # 👈 dodane

CONFIG_FILE = "hue_config.json"
DISCOVERY_URL = "https://discovery.meethue.com"
APP_NAME = "hue_gui_app"
DEVICE_NAME = "customtk_gui"


class HueBridge:
    def __init__(self, app=None):
        self.app = app
        self.bridge_ip = None
        self.token = None
        self.groups = {}
        self.status_label = None
        self.load_saved_data()

    def set_app(self, app):
        self.app = app

    def translate(self, key, **kwargs):
        lang = getattr(self.app, "language", "pl")
        return translations.translations[lang].get(key, key).format(**kwargs)

    def update_status(self, text, color="white"):
        if getattr(self, "_last_status_text", None) == text and getattr(self, "_last_status_color", None) == color:
            return
        self._last_status_text = text
        self._last_status_color = color
        print(f"[Bridge] {text}")
        if self.status_label:
            self.status_label.configure(text=text, text_color=color)

    def fetch_groups(self):
        url = f"http://{self.bridge_ip}/api/{self.token}/groups"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.groups = response.json()
                self.update_status(self.translate("groups_loaded"), "green")

                if self.app and hasattr(self.app, "update_group_widgets"):
                    self.app.after(0, self.app.update_group_widgets)
            else:
                self.update_status(self.translate("fetch_groups_error"), "red")
        except Exception as e:
            self.update_status(self.translate("connection_error", e=e), "red")

    def reset_config(self):
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        self.bridge_ip = None
        self.token = None
        self.update_status(self.translate("bridge_reset"), "white")

    def load_saved_data(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.bridge_ip = data.get("bridge_ip")
                    self.token = data.get("token")
            except Exception as e:
                self.update_status(self.translate("config_load_error", e=e), "red")

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"bridge_ip": self.bridge_ip, "token": self.token}, f)
        except Exception as e:
            self.update_status(self.translate("config_save_error", e=e), "red")

    def connect_fully_automatic(self, callback_on_success):
        self.update_status(self.translate("bridge_searching"), "white")

        def connect():
            try:
                response = requests.get(DISCOVERY_URL, timeout=5).json()
                if not response:
                    self.update_status(self.translate("bridge_not_found"), "red")
                    return
                self.bridge_ip = response[0]["internalipaddress"]
                self.save_config()
                self.update_status(self.translate("bridge_found", ip=self.bridge_ip), "green")
                self.request_token(callback_on_success)
            except Exception as e:
                self.update_status(self.translate("connection_error", e=e), "red")

        threading.Thread(target=connect).start()

    def request_token(self, callback_on_success):
        self.update_status(self.translate("press_button"), "white")

        def wait_for_button():
            url = f"http://{self.bridge_ip}/api"
            payload = {"devicetype": f"{APP_NAME}#{DEVICE_NAME}"}

            for i in range(30):
                try:
                    res = requests.post(url, json=payload).json()
                    if isinstance(res, list) and "success" in res[0]:
                        self.token = res[0]["success"]["username"]
                        self.save_config()
                        self.update_status(self.translate("token_success"), "green")
                        callback_on_success()
                        return
                except:
                    pass
                time.sleep(1)

            self.update_status(self.translate("token_fail"), "red")

        threading.Thread(target=wait_for_button).start()
