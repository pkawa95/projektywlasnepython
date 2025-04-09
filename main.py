import customtkinter as ctk
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from hue_bridge import HueBridge
from light_manager import LightManager
from sensor_manager import SensorManager
from onboarding import OnboardingWindow
from config import VERSION

class HueGUIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hue Controller")
        self.geometry("650x800")

        self.bridge = HueBridge(self)
        self.lights = LightManager(self, self.bridge)
        self.sensors = SensorManager(self, self.bridge)

        self.lights_frame = self.lights.create_frame()
        self.info_frame, self.sensor_label, self.motion_label, self.devices_status_label = self.sensors.create_info_frame()
        self.motion_list_frame = self.sensors.create_motion_list_frame()

        self.bridge.load_saved_data()

        if not self.bridge.token or not self.bridge.bridge_ip:
            self.show_onboarding()
        else:
            self.bridge.insert_ip(self.bridge.bridge_ip)
            self.after(200, self.initialize_connection)

    def show_onboarding(self):
        OnboardingWindow(self, self.initialize_connection)

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
    app = HueGUIApp()
    app.mainloop()
