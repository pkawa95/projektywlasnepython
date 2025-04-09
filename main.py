import customtkinter as ctk
import time
from hue_bridge import HueBridge
from light_manager import LightManager
from sensor_manager import SensorManager
from config import VERSION
from update import check_for_updates_with_gui_and_replace
from onboarding import OnboardingWindow


class HueGUIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hue Controller")
        self.geometry("650x800")
        self.VERSION = VERSION

        self.bridge = HueBridge(self)
        self.lights = LightManager(self, self.bridge)
        self.sensors = SensorManager(self, self.bridge)

        self.status_label = ctk.CTkLabel(self, text="Status mostka...", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=5)

        self.lights_frame = self.lights.create_frame()
        self.info_frame, self.sensor_label, self.motion_label, self.devices_status_label = self.sensors.create_info_frame()
        self.motion_list_frame = self.sensors.create_motion_list_frame()
        self.version_label = ctk.CTkLabel(self, text=f"Wersja aplikacji: {self.VERSION}",
                                          font=ctk.CTkFont(size=11, weight="normal"))
        self.version_label.pack(side="bottom", pady=5)

        self.after(100, self.start_app_flow)

    def start_app_flow(self):
        if not self.bridge.bridge_ip or not self.bridge.token:
            onboarding = OnboardingWindow(self, self.start_connection)
        else:
            self.after(200, self.initialize_connection)

    def start_connection(self):
        self.after(100, self.initialize_connection)

    def initialize_connection(self):
        self.try_auth_or_fetch()

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
