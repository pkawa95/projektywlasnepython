from PyQt6.QtWidgets import QWidget, QLabel, QSlider, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QImage, QPainterPath, QPen, QFont, QRadialGradient
from PyQt6.QtCore import Qt, QTimer
import requests
from threading import Timer

class StrokeLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self.setStyleSheet("background-color: transparent;")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        text = self.text()
        rect = self.rect()
        alignment = self.alignment()

        shadow_pen = QPen(QColor(0, 0, 0, 160))
        painter.setPen(shadow_pen)
        painter.drawText(rect.translated(1, 1), alignment, text)

        stroke_pen = QPen(QColor("black"), 3)
        painter.setPen(stroke_pen)
        painter.drawText(rect, alignment, text)

        painter.setPen(QPen(QColor("white")))
        painter.drawText(rect, alignment, text)

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

        self.live_brightness_timer = None
        self._cached_pixmap_key = None

        self.build_ui()
        self.defer_gradient_update()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)

        name_label = StrokeLabel(self.group_info.get("name", "Unnamed"))

        arrow_btn = QPushButton("▶")
        arrow_btn.setFixedSize(28, 28)
        arrow_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,0,0,40);
                border: none;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,40);
            }
        """)
        arrow_btn.clicked.connect(lambda: self.on_double_click(self.group_id))

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(254)
        self.slider.setValue(self.group_info.get("action", {}).get("bri", 254))
        self.slider.valueChanged.connect(self.schedule_live_brightness_update)
        self.slider.setStyleSheet("margin-left: 4px; margin-right: 4px;")
        self.slider.sliderReleased.connect(self.on_slider_released)

        top_layout = QHBoxLayout()
        top_layout.addWidget(name_label)
        top_layout.addStretch()
        top_layout.addWidget(arrow_btn)

        layout.addLayout(top_layout)
        layout.addWidget(self.slider)
        self.setLayout(layout)

    def schedule_live_brightness_update(self, value):
        if self.live_brightness_timer:
            self.live_brightness_timer.cancel()
        self.live_brightness_timer = Timer(0.15, self.send_live_brightness, args=[value])
        self.live_brightness_timer.start()

    def send_live_brightness(self, value):
        url = f"http://{self.app.bridge.bridge_ip}/api/{self.app.bridge.token}/groups/{self.group_id}/action"
        try:
            requests.put(url, json={"bri": value, "on": True}, timeout=1)
            print(f"⚡ Sent brightness update {value}")
        except Exception as e:
            print(f"❌ Error in live update: {e}")

    def on_slider_released(self):
        value = self.slider.value()
        self.send_live_brightness(value)
        self._cached_pixmap_key = None
        self.update_gradient_image()

    def showEvent(self, event):
        super().showEvent(event)
        self.defer_gradient_update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._cached_pixmap_key = None
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
        key = (width, height, self.group_info.get("action", {}).get("bri", 254))

        if key == self._cached_pixmap_key:
            return self.background_label.pixmap()

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

        bri = self.group_info.get("action", {}).get("bri", 254)
        opacity = 1.0 - (bri / 254.0)
        opacity = min(max(opacity, 0.0), 1.0)

        soft_shadow = QRadialGradient(width / 2, height / 2, max(width, height) / 1.25)
        soft_shadow.setColorAt(0.0, QColor(0, 0, 0, int(opacity * 120)))
        soft_shadow.setColorAt(0.6, QColor(0, 0, 0, int(opacity * 80)))
        soft_shadow.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.fillRect(0, 0, width, height, soft_shadow)

        painter.end()
        pixmap = QPixmap.fromImage(image)
        self._cached_pixmap_key = key
        return pixmap

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
        self._cached_pixmap_key = None
        self.update_gradient_image()