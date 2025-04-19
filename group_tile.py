from PyQt6.QtWidgets import QWidget, QLabel, QSlider, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QImage, QPainterPath
from PyQt6.QtCore import Qt, QTimer

import requests


class GroupTile(QWidget):
    def __init__(self, parent, app, group_id, group_info, on_double_click):
        super().__init__(parent)
        print(f"🧱 Creating GroupTile for group {group_id} ({group_info.get('name')})")

        self.app = app
        self.group_id = group_id
        self.group_info = group_info
        self.on_double_click = on_double_click

        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFixedHeight(100)

        self.setStyleSheet("""
            QWidget {
                border-radius: 12px;
                background-color: transparent;
            }
            QWidget:hover {
                background-color: rgba(255, 255, 255, 30);
            }
        """)

        self.background_label = QLabel(self)
        self.background_label.lower()

        self.build_ui()
        self.defer_gradient_update()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)

        name_label = QLabel(self.group_info.get("name", "Unnamed"))
        name_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(254)
        self.slider.setValue(self.group_info.get("action", {}).get("bri", 254))
        self.slider.setStyleSheet("margin-left: 4px; margin-right: 4px;")
        self.slider.sliderReleased.connect(self.set_brightness)

        top_layout = QHBoxLayout()
        top_layout.addWidget(name_label)
        top_layout.addStretch()

        layout.addLayout(top_layout)
        layout.addWidget(self.slider)
        self.setLayout(layout)

    def showEvent(self, event):
        super().showEvent(event)
        self.defer_gradient_update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_gradient_image()

    def defer_gradient_update(self):
        QTimer.singleShot(300, self.update_gradient_image)

    def mousePressEvent(self, event):
        if event.type() == event.Type.MouseButtonDblClick:
            print(f"🖱️ Double click on group {self.group_id}")
            self.on_double_click(self.group_id)
        else:
            new_state = not self.group_info.get("action", {}).get("on", True)
            print(f"🖱️ Click toggle group {self.group_id} -> {new_state}")
            self.toggle_group(new_state)

    def set_brightness(self):
        value = self.slider.value()
        url = f"http://{self.app.bridge.bridge_ip}/api/{self.app.bridge.token}/groups/{self.group_id}/action"
        print(f"💡 Setting brightness for group {self.group_id} -> {value}")
        try:
            response = requests.put(url, json={"bri": value, "on": True})
            print(f"💡 Brightness set response: {response.status_code}")
        except Exception as e:
            print(f"❌ Błąd jasności (group {self.group_id}): {e}")

    def toggle_group(self, state):
        url = f"http://{self.app.bridge.bridge_ip}/api/{self.app.bridge.token}/groups/{self.group_id}/action"
        print(f"🔁 Toggling group {self.group_id} -> {'on' if state else 'off'}")
        try:
            response = requests.put(url, json={"on": state})
            print(f"🔁 Toggle response: {response.status_code}")
            self.group_info["action"]["on"] = state
        except Exception as e:
            print(f"❌ Błąd grupy (group {self.group_id}): {e}")

    def xy_to_rgb(self, x, y, bri=254):
        try:
            z = 1.0 - x - y
            Y = bri / 254
            X = (Y / y) * x
            Z = (Y / y) * z

            r = X * 1.612 - Y * 0.203 - Z * 0.302
            g = -X * 0.509 + Y * 1.412 + Z * 0.066
            b = X * 0.026 - Y * 0.072 + Z * 0.962

            r = max(0, min(1, r))
            g = max(0, min(1, g))
            b = max(0, min(1, b))

            return (
                int((r ** (1 / 2.2)) * 255),
                int((g ** (1 / 2.2)) * 255),
                int((b ** (1 / 2.2)) * 255)
            )
        except Exception as e:
            print(f"❌ Error converting xy to RGB: {e}")
            return (60, 60, 60)

    def generate_gradient_image(self):
        width = self.width()
        height = self.height()
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(0, 0, width, height, 12, 12)
        painter.setClipPath(path)

        gradient = QLinearGradient(0, 0, width, 0)
        colors = []
        lights = self.group_info.get("lights", [])
        print(f"🎨 Generating gradient for group {self.group_id} with lights: {lights}")

        if not lights or not hasattr(self.app, "lights"):
            print(f"⚠️ No lights or app.lights not initialized for group {self.group_id}")
            return QPixmap()

        for light_id in lights:
            light = self.app.lights.lights.get(light_id)
            if light and light.get("state", {}).get("xy") and light["state"].get("on"):
                x, y = light["state"]["xy"]
                color = QColor(*self.xy_to_rgb(x, y))
                colors.append(color)

        if not colors:
            gray = QColor(60, 60, 60)
            gradient.setColorAt(0.0, gray)
            gradient.setColorAt(1.0, gray)
        else:
            for i, color in enumerate(colors):
                pos = i / max(len(colors) - 1, 1)
                gradient.setColorAt(pos, color)

        painter.fillRect(0, 0, width, height, gradient)
        painter.end()
        return QPixmap.fromImage(image)

    def update_gradient_image(self):
        try:
            pixmap = self.generate_gradient_image()
            if not pixmap or pixmap.isNull():
                raise ValueError("Generated pixmap is null!")
            self.background_label.setPixmap(pixmap)
            self.background_label.setGeometry(0, 0, self.width(), self.height())
        except Exception as e:
            print(f"❌ [Gradient update error] {e}")

    def update_group_state(self, group_info):
        print(f"🔁 update_group_state called for group {self.group_id}")
        self.group_info = group_info
        bri = group_info.get("action", {}).get("bri", 254)
        self.slider.setValue(bri)
        self.update_gradient_image()
