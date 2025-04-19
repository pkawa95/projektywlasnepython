from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QSlider, QVBoxLayout, QHBoxLayout, QColorDialog
import requests


class GroupView(QWidget):
    def __init__(self, parent, app, group_id, group_info, lights, on_back_callback):
        super().__init__(parent)
        self.app = app
        self.group_id = group_id
        self.group_info = group_info
        self.lights = lights
        self.on_back = on_back_callback

        self.main_layout = QVBoxLayout(self)

        back_btn = QPushButton("\u21A9\uFE0F Wróć do grup")
        back_btn.clicked.connect(self.on_back)
        self.main_layout.addWidget(back_btn)

        for light_id in group_info.get("lights", []):
            light_info = lights.get(light_id)
            if not light_info:
                continue

            light_frame = QWidget()
            light_layout = QHBoxLayout(light_frame)

            label = QLabel(light_info["name"])
            light_layout.addWidget(label)

            toggle_btn = QPushButton("Wy\u0142\u0105cz" if light_info["state"]["on"] else "W\u0142\u0105cz")
            toggle_btn.clicked.connect(lambda _, i=light_id: self.toggle_light(i))
            light_layout.addWidget(toggle_btn)

            if "bri" in light_info["state"]:
                slider = QSlider()
                slider.setMinimum(1)
                slider.setMaximum(254)
                slider.setValue(light_info["state"]["bri"])
                slider.setOrientation(1)  # Horizontal
                slider.sliderReleased.connect(lambda i=light_id, s=slider: self.set_brightness(i, s.value()))
                light_layout.addWidget(slider)

            color_btn = QPushButton("Kolor")
            color_btn.clicked.connect(lambda _, i=light_id: self.choose_color(i))
            light_layout.addWidget(color_btn)

            self.main_layout.addWidget(light_frame)

    def toggle_light(self, light_id):
        light = self.lights[light_id]
        new_state = not light["state"]["on"]
        url = f"http://{self.app.bridge.bridge_ip}/api/{self.app.bridge.token}/lights/{light_id}/state"
        try:
            requests.put(url, json={"on": new_state})
            self.app.bridge.update_status("\U0001F4A1 Zmieniono stan \u015bwiat\u0142a")
        except Exception as e:
            self.app.bridge.update_status(f"\u274C B\u0142\u0105d: {e}")

    def set_brightness(self, light_id, bri):
        url = f"http://{self.app.bridge.bridge_ip}/api/{self.app.bridge.token}/lights/{light_id}/state"
        try:
            requests.put(url, json={"bri": int(bri), "on": True})
            self.app.bridge.update_status("\U0001F507 Zmieniono jasno\u015b\u0107")
        except Exception as e:
            self.app.bridge.update_status(f"\u274C B\u0142\u0105d jasno\u015bci: {e}")

    def choose_color(self, light_id):
        color = QColorDialog.getColor()
        if color.isValid():
            r, g, b = color.red(), color.green(), color.blue()
            x, y = self.app.rgb_to_xy(r, g, b)
            url = f"http://{self.app.bridge.bridge_ip}/api/{self.app.bridge.token}/lights/{light_id}/state"
            try:
                requests.put(url, json={"xy": [x, y], "on": True})
                self.app.bridge.update_status("\U0001F308 Kolor ustawiony")
            except Exception as e:
                self.app.bridge.update_status(f"\u274C B\u0142\u0105d koloru: {e}")
