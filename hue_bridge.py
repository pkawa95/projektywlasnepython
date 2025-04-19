import requests
import os
import json
import threading
import time
import translations
from PyQt6.QtCore import QTimer

CONFIG_FILE = "hue_config.json"
DISCOVERY_URL = "https://discovery.meethue.com"
APP_NAME = "hue_gui_app"
DEVICE_NAME = "pyqt6_gui"


class HueBridge:
    def __init__(self, app=None):
        self.app = app
        self.bridge_ip = None
        self.token = None
        self.groups = {}
        self.status_label = None
        self._last_status_text = None
        self._last_status_color = None
        self.load_saved_data()

    def set_app(self, app):
        self.app = app

    def translate(self, key, **kwargs):
        lang = getattr(self.app, "language", "pl")
        return translations.translations[lang].get(key, key).format(**kwargs)

    def update_status(self, text, color="black"):
        if self._last_status_text == text and self._last_status_color == color:
            return
        self._last_status_text = text
        self._last_status_color = color
        print(f"[Bridge] {text}")

        if self.status_label:
            def update():
                self.status_label.setText(text)
                self.status_label.setStyleSheet(f"color: {color};")

            QTimer.singleShot(0, update)

    def fetch_groups_with_callback(self, callback=None):
        url = f"http://{self.bridge_ip}/api/{self.token}/groups"
        print(f"Fetching groups from URL: {url}")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.groups = response.json()
                print(f"Fetched groups: {self.groups}")
                self.update_status(self.translate("groups_loaded"), "green")
                if callback:
                    QTimer.singleShot(0, callback)
            else:
                self.update_status(self.translate("fetch_groups_error"), "red")
                print(f"❌ HTTP error fetching groups: {response.status_code}")
        except Exception as e:
            self.update_status(self.translate("connection_error", e=e), "red")
            print(f"❌ Exception fetching groups: {e}")

    def reset_config(self):
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        self.bridge_ip = None
        self.token = None
        self.update_status(self.translate("bridge_reset"), "black")

    def load_saved_data(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.bridge_ip = data.get("bridge_ip")
                    self.token = data.get("token")
                    print(f"📂 Loaded config: IP={self.bridge_ip}, token={self.token}")
            except Exception as e:
                self.update_status(self.translate("config_load_error", e=e), "red")
                print(f"❌ Failed to load config: {e}")

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"bridge_ip": self.bridge_ip, "token": self.token}, f)
            print("💾 Config saved")
        except Exception as e:
            self.update_status(self.translate("config_save_error", e=e), "red")
            print(f"❌ Failed to save config: {e}")

    def connect_fully_automatic(self, callback_on_success):
        self.update_status(self.translate("bridge_searching"), "black")
        print("🌐 Starting bridge discovery...")

        def connect():
            try:
                response = requests.get(DISCOVERY_URL, timeout=5).json()
                if not response:
                    self.update_status(self.translate("bridge_not_found"), "red")
                    print("❌ No bridges found")
                    return
                self.bridge_ip = response[0]["internalipaddress"]
                self.save_config()
                self.update_status(self.translate("bridge_found", ip=self.bridge_ip), "green")
                print(f"✅ Bridge found at: {self.bridge_ip}")
                self.request_token(callback_on_success)
            except Exception as e:
                self.update_status(self.translate("connection_error", e=e), "red")
                print(f"❌ Error during bridge discovery: {e}")

        threading.Thread(target=connect).start()

    def request_token(self, callback_on_success):
        self.update_status(self.translate("press_button"), "black")
        print("🕹️ Waiting for button press on bridge...")

        def wait_for_button():
            url = f"http://{self.bridge_ip}/api"
            payload = {"devicetype": f"{APP_NAME}#{DEVICE_NAME}"}

            for attempt in range(30):
                try:
                    res = requests.post(url, json=payload).json()
                    if isinstance(res, list) and "success" in res[0]:
                        self.token = res[0]["success"]["username"]
                        self.save_config()
                        self.update_status(self.translate("token_success"), "green")
                        print(f"✅ Token received: {self.token}")
                        QTimer.singleShot(0, callback_on_success)
                        return
                    else:
                        print("⏳ Waiting... not yet authorized")
                except Exception as e:
                    print(f"❌ Error during token request: {e}")
                time.sleep(1)

            self.update_status(self.translate("token_fail"), "red")
            print("❌ Token request failed after 30s")

        threading.Thread(target=wait_for_button).start()