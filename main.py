from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QSlider, QColorDialog
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QImage
from group_tile import GroupTile
from hue_bridge import HueBridge
from light_manager import LightManager
from sensor_manager import SensorManager
from lightpanel import LightPanel
from config import VERSION, UPDATE_URL
import sys, requests, translations

class HueGUIApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hue Controller")
        self.resize(800, 900)

        self.language = "pl"

        self.bridge = HueBridge()
        self.lights = LightManager(self, self.bridge)
        self.sensors = SensorManager(self, self.bridge)
        self.bridge.set_app(self)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        self.content_layout = QHBoxLayout()
        self.main_layout.addLayout(self.content_layout)

        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        self.left_layout.addWidget(self.scroll_area)
        self.scroll_content.setLayout(self.scroll_layout)
        self.content_layout.addWidget(self.left_widget)

        self.light_panel = LightPanel()
        self.light_panel.hide()
        self.content_layout.addWidget(self.light_panel)

        self.sensor_frame, self.sensor_label, self.motion_label, self.devices_status_label = self.sensors.create_info_frame()
        self.sensor_frame.setStyleSheet("margin-top: 8px; padding: 4px 8px;")
        self.main_layout.addWidget(self.sensor_frame)

        self.footer = QHBoxLayout()
        self.footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_version = QLabel(f"📦 Wersja: {VERSION}")
        self.footer_update_btn = QPushButton("🔍 Sprawdź aktualizacje")
        self.footer_update_btn.clicked.connect(self.check_for_updates)
        self.footer.addWidget(self.footer_version)
        self.footer.addWidget(self.footer_update_btn)
        self.main_layout.addLayout(self.footer)

        self.group_widgets = {}

        self.timer = QTimer()
        self.timer.timeout.connect(self.start_auto_updater)
        self.timer.start(1000)

        QTimer.singleShot(0, self.start_main_app)

    def start_main_app(self):
        if self.bridge.token and self.bridge.bridge_ip:
            try:
                res = requests.get(f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/config", timeout=3)
                if res.status_code == 200:
                    self.update_group_widgets()
            except Exception as e:
                print(f"❌ Bridge error: {e}")

    def start_auto_updater(self):
        self.lights.fetch()
        self.sensors.fetch()
        self.bridge.fetch_groups_with_callback(self.update_group_widgets)

    def update_group_widgets(self):
        groups = self.bridge.groups
        filtered = {gid: g for gid, g in groups.items() if g.get("type") == "Room"}

        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.group_widgets.clear()
        for group_id, group_info in filtered.items():
            tile = GroupTile(
                parent=self.scroll_content,
                app=self,
                group_id=group_id,
                group_info=group_info,
                on_double_click=self.show_lights_in_group
            )
            self.scroll_layout.addWidget(tile)
            self.group_widgets[group_id] = tile

    def show_lights_in_group(self, group_id):
        try:
            print(f"➡️ Showing lights for group {group_id}")
            group = self.bridge.groups[group_id]
            group_name = group["name"]

            lights = []
            for lid in group['lights']:
                if lid in self.lights.lights:
                    light = self.lights.lights[lid]
                    light['id'] = lid
                    lights.append(light)

            self.light_panel.update_content(group_name, lights, self)
            self.light_panel.show()

            if group_id in self.group_widgets:
                self.group_widgets[group_id].slider.hide()

        except Exception as e:
            print(f"❌ Error showing lights for group {group_id}: {e}")

    def check_for_updates(self):
        def worker():
            try:
                print("🔍 Checking for updates...")
                self.footer_update_btn.setEnabled(False)
                self.footer_update_btn.setText("⏳ Sprawdzanie...")
                res = requests.get(UPDATE_URL, timeout=5)
                data = res.json()
                latest = data.get("version")
                if latest and latest != VERSION:
                    self.footer_update_btn.setText("⬇️ Aktualizuj teraz")
                else:
                    self.footer_update_btn.setText("✅ Wersja aktualna")
            except Exception as e:
                print(f"❌ Update check failed: {e}")
                self.footer_update_btn.setText("❌ Błąd sprawdzania")
            finally:
                self.footer_update_btn.setEnabled(True)

        import threading
        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HueGUIApp()
    window.show()
    sys.exit(app.exec())