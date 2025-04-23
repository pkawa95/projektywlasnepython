from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QSlider, QPushButton, QColorDialog, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import translations
import requests
from functools import partial

class LightPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        self.setStyleSheet("background-color: #222; color: white;")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(12)

        header_layout = QHBoxLayout()
        self.icon_label = QLabel()
        self.icon_label.setPixmap(QPixmap("icons/default_room.png").scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio))
        header_layout.addWidget(self.icon_label)

        self.title = QLabel("Group Lights")
        self.title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.title)
        header_layout.addStretch()

        self.close_btn = QPushButton("✖")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setStyleSheet("background-color: transparent; color: white; font-size: 14px; border: none;")
        self.close_btn.clicked.connect(self.on_close)
        header_layout.addWidget(self.close_btn)

        self.layout.addLayout(header_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_layout.setSpacing(10)
        self.scroll.setWidget(self.scroll_widget)

        self.layout.addWidget(self.scroll)

        self.app = None
        self.group_id = None

    def update_content(self, group_name, lights, app):
        self.title.setText(group_name)
        self.app = app

        for gid, group in app.bridge.groups.items():
            if group["name"] == group_name:
                self.group_id = gid
                break

        if self.group_id and self.app and self.group_id in self.app.group_widgets:
            self.app.group_widgets[self.group_id].slider.hide()

        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.light_sliders = {}
        self.light_states = {}

        for light in lights:
            light_id = light.get("id")

            # ✅ Pomijamy elementy, które nie są fizycznymi światłami
            if light_id not in app.lights.lights:
                print(f"⚠️ Pominięto '{light.get('name', 'unknown')}' - nie jest fizycznym światłem")
                continue

            self.light_states[light_id] = {"bri": light["state"].get("bri", 254)}

            light_widget = QWidget()
            light_layout = QVBoxLayout(light_widget)
            light_layout.setContentsMargins(6, 6, 6, 6)
            light_layout.setSpacing(6)

            top_row = QHBoxLayout()
            icon = QLabel()
            icon.setPixmap(QPixmap("icons/bulb.png").scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio))
            top_row.addWidget(icon)

            name_label = QLabel(light.get("name", "Unnamed"))
            name_label.setStyleSheet("font-weight: bold; font-size: 13px;")
            top_row.addWidget(name_label)
            top_row.addStretch()
            light_layout.addLayout(top_row)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(1)
            slider.setMaximum(254)
            slider.setValue(light["state"].get("bri", 254))
            slider.setSingleStep(1)
            slider.setTracking(True)

            slider.valueChanged.connect(partial(self.on_slider_value_changed, light_id))
            slider.sliderReleased.connect(partial(self.set_brightness, app, light_id))

            light_layout.addWidget(slider)
            self.light_sliders[light_id] = slider

            buttons_row = QHBoxLayout()
            color_button = QPushButton("🎨 " + translations.translations[app.language].get("color", "Color"))
            color_button.setStyleSheet("padding: 2px; font-size: 12px;")
            color_button.clicked.connect(partial(app.lights.choose_color, light_id))
            buttons_row.addWidget(color_button)

            is_on = light.get("state", {}).get("on", False)
            toggle_text = translations.translations[app.language]["turn_off"] if is_on else translations.translations[app.language]["turn_on"]

            toggle_button = QPushButton(f"💡 {toggle_text}")
            toggle_button.setStyleSheet("padding: 2px; font-size: 12px;")
            toggle_button.clicked.connect(partial(self.toggle_light, app, light_id))
            buttons_row.addWidget(toggle_button)

            light_layout.addLayout(buttons_row)
            self.scroll_layout.addWidget(light_widget)

        self.update_group_slider()

    def on_slider_value_changed(self, light_id, value):
        self.set_brightness_live(self.app, light_id, value)
        self.light_states[light_id]["bri"] = value
        self.update_group_slider(exclude_id=light_id)

    def update_group_slider(self, exclude_id=None):
        if self.group_id and self.app and self.group_id in self.app.group_widgets:
            all_values = [state["bri"] for lid, state in self.light_states.items() if "bri" in state and lid != exclude_id]
            if all_values:
                avg = int(sum(all_values) / len(all_values))
                group_slider = self.app.group_widgets[self.group_id].slider
                if not group_slider.isSliderDown():
                    group_slider.blockSignals(True)
                    group_slider.setValue(avg)
                    group_slider.blockSignals(False)

    def set_brightness(self, app, light_id):
        value = self.light_sliders[light_id].value()
        try:
            print(f"💡 Final brightness {value} for light {light_id}")
            app.lights.set_brightness(light_id, value)
            self.light_states[light_id]["bri"] = value
            self.update_group_slider(exclude_id=light_id)
        except Exception as e:
            print(f"❌ Error setting brightness for light {light_id}: {e}")

    def set_brightness_live(self, app, light_id, value):
        try:
            print(f"🔁 Live brightness {value} for light {light_id}")
            requests.put(f"http://{app.bridge.bridge_ip}/api/{app.bridge.token}/lights/{light_id}/state", json={"bri": value, "on": True}, timeout=0.4)
        except Exception as e:
            print(f"❌ Live brightness error: {e}")

    def toggle_light(self, app, light_id):
        try:
            print(f"🖱️ Toggle button clicked for light {light_id}")
            current_state = app.lights.lights.get(light_id, {}).get("state", {}).get("on", False)
            app.lights.toggle(light_id, not current_state)
        except Exception as e:
            print(f"❌ Error toggling light {light_id}: {e}")

    def on_close(self):
        self.hide()
        if self.group_id and self.app and self.group_id in self.app.group_widgets:
            self.app.group_widgets[self.group_id].slider.show()
