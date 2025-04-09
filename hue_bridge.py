
import os
import requests
import customtkinter as ctk

TOKEN_FILE = "../hue_token.txt"
IP_FILE = "../bridge_ip.txt"
DISCOVERY_URL = "https://discovery.meethue.com"
APP_NAME = "hue_gui_app"
DEVICE_NAME = "customtk_gui"

class HueBridge:
    def __init__(self, app):
        self.app = app
        self.bridge_ip = None
        self.token = None

        self.status_label = ctk.CTkLabel(app, text="Inicjalizacja...", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=10)

        self.ip_entry = ctk.CTkEntry(app, placeholder_text="Wpisz IP mostka (opcjonalnie)")
        self.ip_entry.pack(pady=5)

        self.connect_button = ctk.CTkButton(app, text="Połącz z mostkiem", command=app.initialize_connection)
        self.connect_button.pack(pady=10)

        self.reset_button = ctk.CTkButton(app, text="Resetuj token i IP", command=self.reset_data)
        self.reset_button.pack(pady=5)

    def update_status(self, text):
        self.status_label.configure(text=text)

    def get_ip_entry(self):
        return self.ip_entry.get().strip()

    def load_saved_data(self):
        if os.path.exists(IP_FILE):
            with open(IP_FILE, 'r') as f:
                self.bridge_ip = f.read().strip()
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                self.token = f.read().strip()

    def insert_ip(self, ip):
        if ip:
            self.ip_entry.insert(0, ip)

    def save_token(self):
        with open(TOKEN_FILE, 'w') as f:
            f.write(self.token)

    def save_ip(self):
        if self.bridge_ip:
            with open(IP_FILE, 'w') as f:
                f.write(self.bridge_ip)

    def reset_data(self):
        for file in [TOKEN_FILE, IP_FILE]:
            if os.path.exists(file):
                os.remove(file)
        self.token = None
        self.bridge_ip = None
        self.ip_entry.delete(0, 'end')
        self.update_status("Zresetowano. Wpisz IP lub kliknij Połącz.")

    def search_bridge(self, callback):
        def worker():
            try:
                res = requests.get(DISCOVERY_URL, timeout=5).json()
                if res:
                    self.bridge_ip = res[0]["internalipaddress"]
                    self.save_ip()
                    self.update_status(f"Znaleziono mostek: {self.bridge_ip}")
                    self.app.after(100, callback)
                else:
                    self.update_status("Nie znaleziono mostka. Wpisz IP ręcznie.")
            except Exception:
                self.update_status("Błąd wyszukiwania. Wpisz IP ręcznie.")
        import threading
        threading.Thread(target=worker).start()

    def authorize(self, on_success):
        def worker():
            url = f"http://{self.bridge_ip}/api"
            data = {"devicetype": f"{APP_NAME}#{DEVICE_NAME}"}
            for _ in range(30):
                try:
                    res = requests.post(url, json=data).json()[0]
                    if "success" in res:
                        self.token = res["success"]["username"]
                        self.save_token()
                        self.update_status("Połączono! Token zapisany.")
                        self.app.after(100, on_success)
                        return
                except Exception:
                    pass
                import time
                time.sleep(1)
            self.update_status("Nie udało się połączyć. Spróbuj ponownie.")
        import threading
        threading.Thread(target=worker).start()
