import customtkinter as ctk
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import os

from config import VERSION, UPDATE_URL, REPO_URL
from hue_bridge import HueBridge
from light_manager import LightManager
from sensor_manager import SensorManager
from update import check_for_updates_with_gui_and_replace

use_onboarding = not os.path.exists("hue_token.txt") or not os.path.exists("bridge_ip.txt")
if use_onboarding:
    import onboarding  # UWAGA: bez importu HueGUIApp!

class HueGUIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hue Controller")
        self.geometry("650x800")

        self.bridge = HueBridge(self)

        self.status_label = ctk.CTkLabel(self, text="Inicjalizacja...", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=10)

        self.ip_entry = ctk.CTkEntry(self, placeholder_text="Wpisz IP mostka (opcjonalnie)")
        self.ip_entry.pack(pady=5)

        self.connect_button = ctk.CTkButton(self, text="Połącz z mostkiem", command=self.initialize_connection)
        self.connect_button.pack(pady=10)

        self.reset_button = ctk.CTkButton(self, text="Resetuj token i IP", command=self.bridge.reset_data)
        self.reset_button.pack(pady=5)

        self.lights = LightManager(self, self.bridge)
        self.sensors = SensorManager(self, self.bridge)

        self.lights_frame = self.lights.create_frame()
        self.info_frame, self.sensor_label, self.motion_label, self.devices_status_label = self.sensors.create_info_frame()
        self.motion_list_frame = self.sensors.create_motion_list_frame()

        self.version_label = ctk.CTkLabel(self, text=f"Wersja: {VERSION}", font=ctk.CTkFont(size=10, slant="italic"))
        self.version_label.pack(pady=2)

        self.bridge.load_saved_data()
        self.bridge.insert_ip(self.bridge.bridge_ip)

        self.after(100, self.check_for_updates)
        self.after(200, self.initialize_connection)

    def check_for_updates(self):
        check_for_updates_with_gui_and_replace(self)

    def initialize_connection(self):
        ip_input = self.bridge.get_ip_entry()
        if ip_input:
            self.bridge.bridge_ip = ip_input
            self.bridge.save_ip()
            self.after(100, self.try_auth_or_fetch)
        else:
            self.bridge.search_bridge(self.try_auth_or_fetch)

    def try_auth_or_fetch(self):
        if self.bridge.token:
            self.bridge.update_status("Token znaleziony, łączenie...")
            self.start_auto_updater()
        else:
            self.bridge.authorize(self.start_auto_updater)

    def start_auto_updater(self):
        def update_loop():
            while True:
                self.lights.fetch()
                self.sensors.fetch()
                time.sleep(5)
        import threading
        threading.Thread(target=update_loop, daemon=True).start()


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("dark-blue")

    if use_onboarding:
        app = onboarding.OnboardingWindow()
    else:
        app = HueGUIApp()

    app.mainloop()
