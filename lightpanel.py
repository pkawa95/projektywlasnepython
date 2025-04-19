from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QSlider, QPushButton, QColorDialog, QHBoxLayout
from PyQt6.QtCore import Qt

class LightPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(260)
        self.setStyleSheet("background-color: #222; color: white;")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(12)

        self.title = QLabel("Group Lights")
        self.title.setStyleSheet("font-size: 16px; font-weight: bold; text-align: center;")
        self.layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll.setWidget(self.scroll_widget)

        self.layout.addWidget(self.scroll)

    def update_content(self, group_name, lights, app):
        self.title.setText(group_name)

        # Clear previous widgets
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for light in lights:
            light_widget = QWidget()
            light_layout = QVBoxLayout(light_widget)
            light_layout.setContentsMargins(6, 6, 6, 6)
            light_layout.setSpacing(4)

            name_label = QLabel(light.get("name", "Unnamed"))
            name_label.setStyleSheet("font-weight: bold; font-size: 13px;")
            light_layout.addWidget(name_label)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(1)
            slider.setMaximum(254)
            slider.setValue(light.get("state", {}).get("bri", 254))
            slider.sliderReleased.connect(lambda l=light, s=slider: self.set_brightness(app, l["id"], s.value()))
            light_layout.addWidget(slider)

            color_button = QPushButton("🎨 Kolor")
            color_button.setStyleSheet("padding: 2px; font-size: 12px;")
            color_button.clicked.connect(lambda _, l=light: app.lights.choose_color(l["id"]))
            light_layout.addWidget(color_button)

            self.scroll_layout.addWidget(light_widget)

    def set_brightness(self, app, light_id, value):
        try:
            print(f"💡 Setting brightness {value} for light {light_id}")
            app.lights.set_brightness(light_id, value)
        except Exception as e:
            print(f"❌ Error setting brightness for light {light_id}: {e}")