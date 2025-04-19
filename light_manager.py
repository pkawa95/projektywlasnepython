from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QColorDialog
import requests


class LightManager:
    def __init__(self, app, bridge):
        self.app = app
        self.bridge = bridge
        self.light_widgets = {}
        self.lights = {}
        self.scroll_area = None
        print("💡 LightManager initialized")

    def create_frame(self):
        container = QWidget()
        layout = QVBoxLayout(container)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(container)

        self.app.main_layout.addWidget(self.scroll_area)
        print("🖼️ LightManager UI frame created")
        return self.scroll_area

    def fetch(self):
        try:
            url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/lights"
            print(f"🌐 Fetching lights from {url}")
            self.lights = requests.get(url).json()
            print(f"💡 Lights fetched: {list(self.lights.keys())}")

            for group_id, group in self.bridge.groups.items():
                for light_id in group["lights"]:
                    if light_id in self.lights:
                        self.lights[light_id]["group"] = group_id
                        self.lights[light_id]["id"] = light_id

            if hasattr(self.app, "update_group_widgets"):
                print("🔁 Triggering group widget update from LightManager")
                self.app.update_group_widgets()

        except Exception as e:
            self.bridge.update_status(f"❌ Błąd pobierania świateł: {e}")
            print(f"❌ [LightManager] Error fetching lights: {e}")

    def toggle(self, light_id, state):
        url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/lights/{light_id}/state"
        print(f"🔘 Toggling light {light_id} -> {'on' if state else 'off'}")
        try:
            requests.put(url, json={"on": state})
        except Exception as e:
            self.bridge.update_status(f"❌ Błąd: {e}")
            print(f"❌ [LightManager] Error toggling light {light_id}: {e}")

    def set_brightness(self, light_id, bri):
        url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/lights/{light_id}/state"
        print(f"💡 Setting brightness for light {light_id} -> {bri}")
        try:
            requests.put(url, json={"bri": int(bri), "on": True})
        except Exception as e:
            self.bridge.update_status(f"❌ Błąd jasności: {e}")
            print(f"❌ [LightManager] Error setting brightness for light {light_id}: {e}")

    def choose_color(self, light_id):
        print(f"🎨 Opening color dialog for light {light_id}")
        color = QColorDialog.getColor()
        if color.isValid():
            print(f"🎨 Selected color RGB({color.red()}, {color.green()}, {color.blue()})")
            x, y = self.rgb_to_xy(color.red(), color.green(), color.blue())
            data = {"xy": [x, y], "on": True}
            url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/lights/{light_id}/state"
            try:
                requests.put(url, json=data)
                print(f"🎨 Sent color data to light {light_id}: {data}")
            except Exception as e:
                self.bridge.update_status(f"❌ Błąd koloru: {e}")
                print(f"❌ [LightManager] Error setting color for light {light_id}: {e}")

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
        print(f"🎯 Converted RGB({r}, {g}, {b}) -> XY({x}, {y})")
        return round(x, 4), round(y, 4)