import customtkinter as ctk
import requests
import threading
import time
import os
import tkinter.colorchooser as cc

TOKEN_FILE = "../hue_token.txt"
IP_FILE = "../bridge_ip.txt"
DISCOVERY_URL = "https://discovery.meethue.com"
APP_NAME = "hue_gui_app"
DEVICE_NAME = "customtk_gui"

class HueGUIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hue Controller")
        self.geometry("650x700")

        self.bridge_ip = None
        self.token = None
        self.lights = {}
        self.sensors = {}
        self.light_widgets = {}

        self.status_label = ctk.CTkLabel(self, text="Inicjalizacja...", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=10)

        self.ip_entry = ctk.CTkEntry(self, placeholder_text="Wpisz IP mostka (opcjonalnie)")
        self.ip_entry.pack(pady=5)

        self.connect_button = ctk.CTkButton(self, text="Połącz z mostkiem", command=self.initialize_connection)
        self.connect_button.pack(pady=10)

        self.reset_button = ctk.CTkButton(self, text="Resetuj token i IP", command=self.reset_data)
        self.reset_button.pack(pady=5)

        self.lights_frame = ctk.CTkScrollableFrame(self, width=600, height=300)
        self.lights_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(pady=5, padx=10, fill="x")

        self.sensor_label = ctk.CTkLabel(self.info_frame, text="", font=ctk.CTkFont(size=13))
        self.sensor_label.pack(pady=2)

        self.motion_label = ctk.CTkLabel(self.info_frame, text="", font=ctk.CTkFont(size=13))
        self.motion_label.pack(pady=2)

        self.devices_status_label = ctk.CTkLabel(self.info_frame, text="", font=ctk.CTkFont(size=12, weight="normal"))
        self.devices_status_label.pack(pady=5)

        self.load_saved_data()

    def load_saved_data(self):
        if os.path.exists(IP_FILE):
            with open(IP_FILE, 'r') as f:
                self.bridge_ip = f.read().strip()
                self.ip_entry.insert(0, self.bridge_ip)
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                self.token = f.read().strip()

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
        self.status_label.configure(text="Zresetowano. Wpisz IP lub kliknij Połącz.")

    def initialize_connection(self):
        ip_input = self.ip_entry.get().strip()
        if ip_input:
            self.bridge_ip = ip_input
            self.save_ip()
            self.after(100, self.try_auth_or_fetch)
        else:
            self.status_label.configure(text="Szukam mostka w sieci...")
            threading.Thread(target=self.find_bridge).start()

    def find_bridge(self):
        try:
            res = requests.get(DISCOVERY_URL, timeout=5).json()
            if res:
                self.bridge_ip = res[0]["internalipaddress"]
                self.save_ip()
                self.status_label.configure(text=f"Znaleziono mostek: {self.bridge_ip}")
                self.after(100, self.try_auth_or_fetch)
            else:
                self.status_label.configure(text="Nie znaleziono mostka. Wpisz IP ręcznie.")
        except Exception as e:
            self.status_label.configure(text="Błąd wyszukiwania. Wpisz IP ręcznie.")

    def try_auth_or_fetch(self):
        if self.token:
            self.status_label.configure(text="Token znaleziony, łączenie...")
            self.start_auto_updater()
        else:
            self.status_label.configure(text="Brak tokena, wciskaj przycisk na mostku...")
            threading.Thread(target=self.request_token).start()

    def request_token(self):
        url = f"http://{self.bridge_ip}/api"
        data = {"devicetype": f"{APP_NAME}#{DEVICE_NAME}"}
        for _ in range(30):
            try:
                res = requests.post(url, json=data).json()[0]
                if "success" in res:
                    self.token = res["success"]["username"]
                    self.save_token()
                    self.status_label.configure(text="Połączono! Token zapisany.")
                    self.start_auto_updater()
                    return
            except Exception:
                pass
            time.sleep(1)
        self.status_label.configure(text="Nie udało się połączyć. Spróbuj ponownie.")

    def start_auto_updater(self):
        def update_loop():
            while True:
                self.fetch_lights()
                self.fetch_sensors()
                time.sleep(5)

        threading.Thread(target=update_loop, daemon=True).start()

    def fetch_lights(self):
        try:
            url = f"http://{self.bridge_ip}/api/{self.token}/lights"
            new_lights = requests.get(url).json()
            self.lights = new_lights
            self.update_light_widgets()
            self.status_label.configure(text=f"Załadowano {len(self.lights)} świateł.")
        except Exception as e:
            self.status_label.configure(text=f"Błąd pobierania: {e}")

    def update_light_widgets(self):
        for light_id, info in self.lights.items():
            name = info["name"]
            state = info["state"]

            if light_id not in self.light_widgets:
                frame = ctk.CTkFrame(self.lights_frame)
                frame.pack(pady=10, padx=10, fill="x")

                label = ctk.CTkLabel(frame, text=name, font=ctk.CTkFont(size=14, weight="bold"))
                label.pack(side="left", padx=10)

                toggle = ctk.CTkButton(frame, text="", command=lambda i=light_id: self.toggle_light(i, not self.lights[i]["state"]["on"]))
                toggle.pack(side="left", padx=10)

                bri = None
                if "bri" in state:
                    bri = ctk.CTkSlider(frame, from_=1, to=254, orientation="horizontal", width=100)
                    bri.pack(side="left", padx=10)
                    bri.bind("<ButtonRelease-1>", lambda e, i=light_id, s=bri: self.set_brightness(i, s.get()))

                color_btn = None
                if "xy" in state or "hue" in state:
                    color_btn = ctk.CTkButton(frame, text="Kolor", command=lambda i=light_id: self.choose_color(i))
                    color_btn.pack(side="left", padx=10)

                self.light_widgets[light_id] = {
                    "frame": frame,
                    "toggle": toggle,
                    "bri": bri,
                    "label": label
                }

            widget = self.light_widgets[light_id]
            widget["label"].configure(text=name)
            widget["toggle"].configure(text="Wyłącz" if state["on"] else "Włącz")
            if widget["bri"]:
                widget["bri"].set(state.get("bri", 1))

    def fetch_sensors(self):
        try:
            url = f"http://{self.bridge_ip}/api/{self.token}/sensors"
            self.sensors = requests.get(url).json()
            temps = [
                s['state']['temperature'] / 100.0
                for s in self.sensors.values()
                if s.get('type') == 'ZLLTemperature'
            ]
            if temps:
                avg_temp = sum(temps) / len(temps)
                self.sensor_label.configure(text=f"Średnia temperatura: {avg_temp:.1f}°C")
            else:
                self.sensor_label.configure(text="Brak czujników temperatury.")

            motions = [
                s['state']['presence']
                for s in self.sensors.values()
                if s.get('type') == 'ZLLPresence'
            ]
            if motions:
                if any(motions):
                    self.motion_label.configure(text="Ruch wykryty! 🕺")
                else:
                    self.motion_label.configure(text="Brak ruchu.")
            else:
                self.motion_label.configure(text="Brak czujników ruchu.")

            self.devices_status_label.configure(
                text=f"Wykryto: {len(self.lights)} światła, {len(temps)} temp., {len(motions)} cz. ruchu")

        except Exception as e:
            self.sensor_label.configure(text=f"Błąd czujników: {e}")
            self.motion_label.configure(text="")

    def toggle_light(self, light_id, state):
        url = f"http://{self.bridge_ip}/api/{self.token}/lights/{light_id}/state"
        try:
            requests.put(url, json={"on": state})
        except Exception as e:
            self.status_label.configure(text=f"Błąd: {e}")

    def set_brightness(self, light_id, bri):
        url = f"http://{self.bridge_ip}/api/{self.token}/lights/{light_id}/state"
        try:
            requests.put(url, json={"bri": int(bri), "on": True})
        except Exception as e:
            self.status_label.configure(text=f"Błąd jasności: {e}")

    def choose_color(self, light_id):
        rgb, _ = cc.askcolor()
        if rgb:
            x, y = self.rgb_to_xy(*rgb)
            data = {"xy": [x, y], "on": True}
            url = f"http://{self.bridge_ip}/api/{self.token}/lights/{light_id}/state"
            try:
                requests.put(url, json=data)
            except Exception as e:
                self.status_label.configure(text=f"Błąd koloru: {e}")

    def rgb_to_xy(self, r, g, b):
        r, g, b = [x / 255.0 for x in (r, g, b)]
        r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
        g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
        b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
        X = r * 0.649926 + g * 0.103455 + b * 0.197109
        Y = r * 0.234327 + g * 0.743075 + b * 0.022598
        Z = g * 0.053077 + b * 1.035763
        if X + Y + Z == 0:
            return 0, 0
        x = X / (X + Y + Z)
        y = Y / (X + Y + Z)
        return round(x, 4), round(y, 4)


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("dark-blue")
    app = HueGUIApp()
    app.mainloop()
