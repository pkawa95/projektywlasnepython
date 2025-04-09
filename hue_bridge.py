#hue_bridge.py
import requests
import os
import json
import threading
import time

CONFIG_FILE = "hue_config.json"
DISCOVERY_URL = "https://discovery.meethue.com"
APP_NAME = "hue_gui_app"
DEVICE_NAME = "customtk_gui"

class HueBridge:
    def __init__(self, app):
        self.app = app
        self.bridge_ip = None
        self.token = None
        self.status_label = None

        self.load_saved_data()

    def update_status(self, text):
        print(f"[Bridge] {text}")
        if self.status_label:
            self.status_label.configure(text=text)

    def fetch_groups(self):
        url = f"http://{self.bridge_ip}/api/{self.token}/groups"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.groups = response.json()
                self.app.display_groups()  # Powiadom aplikację o załadowaniu grup
            else:
                self.app.status_label.configure(text="Błąd pobierania grup.")
        except Exception as e:
            self.app.status_label.configure(text=f"Błąd połączenia z mostkiem: {e}")

    def fetch_groups(self):
        url = f"http://{self.bridge_ip}/api/{self.token}/groups"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.groups = response.json()
                if hasattr(self.app, "display_groups"):
                    self.app.after(200, self.app.display_groups)
            # Powiadom aplikację o załadowaniu grup
            else:
                self.app.status_label.configure(text="Błąd pobierania grup.")
        except Exception as e:
            self.app.status_label.configure(text=f"Błąd połączenia z mostkiem: {e}")

    def reset_config(self):
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        self.bridge_ip = None
        self.token = None
        self.update_status("Zresetowano konfigurację mostka.")

    def load_saved_data(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.bridge_ip = data.get("bridge_ip")
                    self.token = data.get("token")
            except Exception as e:
                self.update_status(f"Błąd wczytywania configu: {e}")

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"bridge_ip": self.bridge_ip, "token": self.token}, f)
        except Exception as e:
            self.update_status(f"Błąd zapisu configu: {e}")

    def connect_fully_automatic(self, callback_on_success):
        self.update_status("🔍 Szukanie mostka Hue w sieci...")

        def connect():
            try:
                response = requests.get(DISCOVERY_URL, timeout=5).json()
                if not response:
                    self.update_status("❌ Nie znaleziono mostka.")
                    return
                self.bridge_ip = response[0]["internalipaddress"]
                self.save_config()
                self.update_status(f"✅ Znaleziono mostek Hue: {self.bridge_ip}")
                self.request_token(callback_on_success)
            except Exception as e:
                self.update_status(f"❌ Błąd połączenia: {e}")

        threading.Thread(target=connect).start()

    def request_token(self, callback_on_success):
        self.update_status("⚠️ Wciśnij przycisk na mostku Hue... (30s)")

        def wait_for_button():
            url = f"http://{self.bridge_ip}/api"
            payload = {"devicetype": f"{APP_NAME}#{DEVICE_NAME}"}

            for i in range(30):
                try:
                    res = requests.post(url, json=payload).json()
                    if isinstance(res, list) and "success" in res[0]:
                        self.token = res[0]["success"]["username"]
                        self.save_config()
                        self.update_status("✅ Połączono z mostkiem.")
                        callback_on_success()
                        return
                except:
                    pass
                time.sleep(1)

            self.update_status("❌ Nie udało się uzyskać tokenu.")

        threading.Thread(target=wait_for_button).start()
