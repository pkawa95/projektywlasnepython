import customtkinter as ctk
import time
from hue_bridge import HueBridge
from light_manager import LightManager
from sensor_manager import SensorManager
from update import check_for_updates_with_gui_and_replace
from config import VERSION
import threading


class HueGUIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hue Controller")
        self.geometry("650x800")

        self.bridge = HueBridge(self)
        self.lights = LightManager(self, self.bridge)
        self.sensors = SensorManager(self, self.bridge)

        self.status_label = ctk.CTkLabel(self, text="Inicjalizacja...", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=5)
        self.bridge.status_label = self.status_label

        self.reset_button = ctk.CTkButton(self, text="Resetuj token i IP", command=self.bridge.reset_config)
        self.reset_button.pack(pady=5)

        self.lights_frame = self.lights.create_frame()
        self.info_frame, self.sensor_label, self.motion_label, self.devices_status_label = self.sensors.create_info_frame()
        self.motion_list_frame = self.sensors.create_motion_list_frame()

        self.version_label = ctk.CTkLabel(self, text=f"📦 Wersja aplikacji: {VERSION}", font=ctk.CTkFont(size=12))
        self.version_label.pack(pady=5)

        self.after(100, self.check_for_updates)
        self.after(300, self.initialize_connection)

    def check_for_updates(self):
        check_for_updates_with_gui_and_replace(self)

    def initialize_connection(self):
        if self.bridge.bridge_ip and self.bridge.token:
            self.bridge.update_status("Token znaleziony, łączenie...")
            self.start_auto_updater()
        else:
            self.bridge.connect_fully_automatic(self.start_auto_updater)

    def start_auto_updater(self):
        def update_loop():
            first_run = True
            while True:
                try:
                    self.lights.fetch()
                    self.sensors.fetch()
                    if first_run:
                        self.bridge.fetch_groups()
                        first_run = False
                except Exception as e:
                    print(f"[Updater] Błąd: {e}")
                time.sleep(5)

        threading.Thread(target=update_loop, daemon=True).start()


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("dark-blue")
    app = HueGUIApp()
    app.mainloop()
