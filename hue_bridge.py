import os
import requests
import threading
import time

TOKEN_FILE = "hue_token.txt"
IP_FILE = "bridge_ip.txt"
APP_NAME = "hue_gui_app"
DEVICE_NAME = "customtk_gui"

class HueBridge:
    def __init__(self, app):
        self.app = app
        self.token = None
        self.bridge_ip = None
        self.status_label = None
        self.ip_entry = None

    def load_saved_data(self):
        if os.path.exists(IP_FILE):
            with open(IP_FILE, 'r') as f:
                self.bridge_ip = f.read().strip()
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                self.token = f.read().strip()
    def reset_data(self):
        for file in ["hue_token.txt", "bridge_ip.txt"]:
            if os.path.exists(file):
                os.remove(file)
        self.token = None
        self.bridge_ip = None
        try:
            if hasattr(self.app, "ip_entry"):
                self.app.ip_entry.delete(0, 'end')
            if hasattr(self.app, "status_label"):
                self.app.status_label.configure(text="Zresetowano. Wpisz IP lub kliknij Połącz.")
        except Exception as e:
            print(f"[Reset] Błąd: {e}")


    def save_token(self):
        with open(TOKEN_FILE, 'w') as f:
            f.write(self.token)

    def save_ip(self):
        if self.bridge_ip:
            with open(IP_FILE, 'w') as f:
                f.write(self.bridge_ip)

    def insert_ip(self, ip):
        if ip and self.app.ip_entry:
            self.app.ip_entry.delete(0, "end")
            self.app.ip_entry.insert(0, ip)

    def get_ip_entry(self):
        if self.app.ip_entry:
            return self.app.ip_entry.get().strip()
        return ""

    def update_status(self, message):
        if self.app.status_label:
            self.app.status_label.configure(text=message)
        print(f"[Bridge] {message}")

    def search_bridge(self, on_found_callback):
        def _search():
            try:
                resp = requests.get("https://discovery.meethue.com", timeout=5)
                if resp.status_code == 200 and resp.text.strip():
                    res = resp.json()
                    if res:
                        self.bridge_ip = res[0]["internalipaddress"]
                        self.save_ip()
                        self.update_status(f"Znaleziono mostek: {self.bridge_ip}")
                        self.app.after(100, on_found_callback)
                    else:
                        self.update_status("❌ Mostek nie został wykryty.")
                else:
                    self.update_status("❌ Brak odpowiedzi z serwera discovery.")
            except Exception:
                self.update_status("Błąd wyszukiwania mostka.")

        threading.Thread(target=_search, daemon=True).start()

    def authorize(self, on_success_callback):
        def wait_for_button():
            self.update_status("Przygotowanie do autoryzacji...")
            url = f"http://{self.bridge_ip}/api"
            data = {"devicetype": f"{APP_NAME}#{DEVICE_NAME}"}

            for i in range(30, 0, -1):
                self.update_status(f"🔑 Oczekiwanie na wciśnięcie przycisku... ({i}s)")
                try:
                    res = requests.post(url, json=data).json()[0]
                    if "success" in res:
                        self.token = res["success"]["username"]
                        self.save_token()
                        self.update_status("✅ Połączono! Token zapisany.")
                        on_success_callback()
                        return
                except Exception:
                    pass
                time.sleep(1)

            self.update_status("❌ Nie udało się połączyć. Spróbuj ponownie.")

        threading.Thread(target=wait_for_button, daemon=True).start()

    def connect_fully_automatic(self, on_success_callback):
        self.update_status("🔍 Szukanie mostka Hue w sieci...")

        def do_connection():
            try:
                resp = requests.get("https://discovery.meethue.com", timeout=5)
                if resp.status_code == 200 and resp.text.strip():
                    res = resp.json()
                    if not res:
                        self.update_status("❌ Mostek nie został wykryty.")
                        return
                    self.bridge_ip = res[0]["internalipaddress"]
                    self.save_ip()
                    self.update_status(f"🟢 Znaleziono mostek Hue Bridge: {self.bridge_ip}")
                    time.sleep(1)
                    self.authorize(on_success_callback)
                else:
                    self.update_status("❌ Brak odpowiedzi z serwera discovery.")
            except Exception as e:
                self.update_status(f"Błąd połączenia: {e}")

        threading.Thread(target=do_connection, daemon=True).start()

