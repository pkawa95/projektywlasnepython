import requests
import tkinter.colorchooser as cc
import customtkinter as ctk
from onboarding import OnboardingWindow
from hue_bridge import HueBridge
from light_manager import LightManager
from sensor_manager import SensorManager
from update import check_for_updates_with_gui_and_replace
from config import VERSION

class HueGUIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.VERSION = VERSION
        self.title("Hue Controller")
        self.geometry("720x860")

        ctk.set_default_color_theme("blue")
        ctk.set_appearance_mode("dark")
        self.font_title = ctk.CTkFont(size=16, weight="bold")
        self.font_normal = ctk.CTkFont(size=13)

        self.bridge = HueBridge(self)
        self.lights = LightManager(self, self.bridge)
        self.sensors = SensorManager(self, self.bridge)

        self.onboarding = OnboardingWindow(self, self.start_main_app)
        self.onboarding.grab_set()

    def start_main_app(self):
        self.onboarding.destroy()

        self.status_label = ctk.CTkLabel(self, text="🔄 Inicjalizacja...", font=self.font_normal)
        self.status_label.pack(pady=8)
        self.bridge.status_label = self.status_label

        self.reset_button = ctk.CTkButton(self, text="🔁 Resetuj token i IP", command=self.bridge.reset_config)
        self.reset_button.pack(pady=8)

        self.lights_frame = ctk.CTkScrollableFrame(self, width=680, height=400, corner_radius=14)
        self.lights_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.group_widgets = {}

        self.info_frame, self.sensor_label, self.motion_label, self.devices_status_label = self.sensors.create_info_frame()
        self.motion_list_frame = self.sensors.create_motion_list_frame()

        self.version_label = ctk.CTkLabel(self, text=f"📦 Wersja aplikacji: {VERSION}", font=self.font_normal)
        self.version_label.pack(pady=10)

        self.after(200, self.check_for_updates)
        self.after(400, self.start_auto_updater)

    def check_for_updates(self):
        check_for_updates_with_gui_and_replace(self)

    def start_auto_updater(self):
        import time, threading
        def loop():
            while True:
                self.lights.fetch()
                self.bridge.fetch_groups()
                self.display_groups()
                self.sensors.fetch()
                time.sleep(3)
        threading.Thread(target=loop, daemon=True).start()

    def display_groups(self):
        pass

    def display_groups(self):
        groups = self.bridge.groups
        lights = self.lights.lights

        for group_id, group_info in groups.items():
            group_name = group_info["name"]
            group_state = group_info["action"]["on"]

            if group_id not in self.group_widgets:
                group_frame = ctk.CTkFrame(self.lights_frame, corner_radius=14)
                group_frame.pack(pady=14, padx=16, fill="x")

                label = ctk.CTkLabel(group_frame, text=group_name, font=self.font_title)
                label.pack(side="left", padx=10)

                toggle_button = ctk.CTkButton(
                    group_frame,
                    text="Wyłącz" if group_state else "Włącz",
                    command=lambda i=group_id: self.toggle_group(i)
                )
                toggle_button.pack(side="left", padx=10)
                # Suwak jasności grupy
                bri = group_info["action"].get("bri", 254)
                group_brightness = ctk.CTkSlider(group_frame, from_=1, to=254, number_of_steps=253, width=100)
                group_brightness.set(bri)
                group_brightness.pack(side="left", padx=10)
                group_brightness.bind("<ButtonRelease-1>",
                                      lambda event, i=group_id, s=group_brightness: self.set_group_brightness(i,
                                                                                                              s.get()))

                # Przycisk koloru dla grupy
                group_color_button = ctk.CTkButton(group_frame, text="Kolor",
                                                   command=lambda i=group_id: self.choose_group_color(i))
                group_color_button.pack(side="left", padx=10)

                self.group_widgets[group_id] = {
                    "frame": group_frame,
                    "toggle": toggle_button,
                    "lights": {}
                }

            toggle_button = self.group_widgets[group_id]["toggle"]
            toggle_button.configure(text="Wyłącz" if group_state else "Włącz")

            for light_id in group_info["lights"]:
                light_info = lights.get(light_id)
                if not light_info:
                    continue

                light_name = light_info["name"]
                light_state = light_info["state"]
                light_widgets = self.group_widgets[group_id]["lights"]

                if light_id not in light_widgets:
                    light_frame = ctk.CTkFrame(self.group_widgets[group_id]["frame"], corner_radius=12)
                    light_frame.pack(pady=4, padx=20, fill="x")

                    label = ctk.CTkLabel(light_frame, text=light_name, font=self.font_normal)
                    label.pack(side="left", padx=10)

                    toggle = ctk.CTkButton(
                        light_frame,
                        text="Wyłącz" if light_state["on"] else "Włącz",
                        command=lambda i=light_id: self.toggle_light(i)
                    )
                    toggle.pack(side="left", padx=10)

                    # Suwak jasności
                    if "bri" in light_state:
                        slider = ctk.CTkSlider(light_frame, from_=1, to=254, number_of_steps=253)
                        slider.set(light_state["bri"])
                        slider.pack(side="left", padx=10, fill="x", expand=True)
                        slider.bind("<ButtonRelease-1>",
                                    lambda event, i=light_id, s=slider: self.set_brightness(i, s.get()))

                    # Przycisk wyboru koloru
                    color_button = ctk.CTkButton(light_frame, text="Kolor",
                                                 command=lambda i=light_id: self.choose_color(i))
                    color_button.pack(side="left", padx=10)

                    light_widgets[light_id] = {
                        "frame": light_frame,
                        "toggle": toggle
                    }

                light_widgets[light_id]["toggle"].configure(text="Wyłącz" if light_state["on"] else "Włącz")

    def toggle_group(self, group_id):
        current_state = self.bridge.groups[group_id]["action"]["on"]
        new_state = not current_state
        url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/groups/{group_id}/action"
        try:
            requests.put(url, json={"on": new_state})
        except Exception as e:
            self.bridge.update_status(f"❌ Błąd grupy: {e}")

    def toggle_light(self, light_id):
        light = self.lights.lights.get(light_id)
        if light:
            new_state = not light["state"]["on"]
            url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/lights/{light_id}/state"
            try:
                requests.put(url, json={"on": new_state})
            except Exception as e:
                self.bridge.update_status(f"❌ Błąd światła: {e}")

    def choose_color(self, light_id):
        rgb, _ = cc.askcolor()
        if rgb:
            x, y = self.rgb_to_xy(*rgb)
            url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/lights/{light_id}/state"
            try:
                requests.put(url, json={"xy": [x, y], "on": True})
            except Exception as e:
                self.bridge.update_status(f"❌ Błąd koloru: {e}")

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
    app = HueGUIApp()
    app.mainloop()
