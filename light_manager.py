#light_manager.py
import customtkinter as ctk
import requests

class LightManager:
    def __init__(self, app, bridge):
        self.app = app
        self.bridge = bridge
        self.light_widgets = {}
        self.lights = {}

    def create_frame(self):
        self.lights_frame = ctk.CTkScrollableFrame(self.app, width=600, height=300)
        self.lights_frame.pack(pady=10, padx=10, fill="both", expand=True)
        return self.lights_frame

    def fetch(self):
        try:
            url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/lights"
            self.lights = requests.get(url).json()
            self.update_widgets()
            self.bridge.update_status(f"Załadowano {len(self.lights)} świateł.")
        except Exception as e:
            self.bridge.update_status(f"Błąd pobierania: {e}")

    def update_widgets(self):
        for light_id, info in self.lights.items():
            name = info["name"]
            state = info["state"]

            if light_id not in self.light_widgets:
                frame = ctk.CTkFrame(self.lights_frame)
                frame.pack(pady=10, padx=10, fill="x")

                label = ctk.CTkLabel(frame, text=name, font=ctk.CTkFont(size=14, weight="bold"))
                label.pack(side="left", padx=10)

                toggle = ctk.CTkButton(frame, text="", command=lambda i=light_id: self.toggle(i, not self.lights[i]["state"]["on"]))
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

    def toggle(self, light_id, state):
        url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/lights/{light_id}/state"
        try:
            requests.put(url, json={"on": state})
        except Exception as e:
            self.bridge.update_status(f"Błąd: {e}")

    def set_brightness(self, light_id, bri):
        url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/lights/{light_id}/state"
        try:
            requests.put(url, json={"bri": int(bri), "on": True})
        except Exception as e:
            self.bridge.update_status(f"Błąd jasności: {e}")

    def choose_color(self, light_id):
        import tkinter.colorchooser as cc
        rgb, _ = cc.askcolor()
        if rgb:
            x, y = self.rgb_to_xy(*rgb)
            data = {"xy": [x, y], "on": True}
            url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/lights/{light_id}/state"
            try:
                requests.put(url, json=data)
            except Exception as e:
                self.bridge.update_status(f"Błąd koloru: {e}")

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
