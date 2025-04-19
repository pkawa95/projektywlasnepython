from PyQt6.QtWidgets import QLabel, QFrame, QVBoxLayout, QScrollArea, QWidget
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import translations


class SensorManager:
    def __init__(self, app, bridge):
        self.app = app
        self.bridge = bridge
        self.sensors = {}

        self.sensor_label = None
        self.motion_label = None
        self.devices_status_label = None

        print("📡 SensorManager initialized")

    def create_info_frame(self):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 2, 10, 2)
        layout.setSpacing(1)  # Mniejsze odstępy

        self.motion_label = QLabel()
        self.motion_label.setStyleSheet("font-size: 10px; color: white; background-color: transparent; line-height: 1;")
        self.motion_label.setWordWrap(True)
        layout.addWidget(self.motion_label)

        self.devices_status_label = QLabel()
        self.devices_status_label.setStyleSheet("font-size: 10px; color: white; background-color: transparent; line-height: 1;")
        layout.addWidget(self.devices_status_label)

        self.sensor_label = QLabel()
        self.sensor_label.setStyleSheet("font-size: 10px; color: white; background-color: transparent; line-height: 1;")
        layout.addWidget(self.sensor_label)

        print("💛 Sensor info frame created")
        return frame, self.sensor_label, self.motion_label, self.devices_status_label

    def create_motion_list_frame(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(150)

        frame = QWidget()
        scroll_area.setWidget(frame)

        print("💛 Motion list scroll area created")
        return scroll_area

    def fetch(self):
        try:
            url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/sensors"
            print(f"🌐 Fetching sensors from {url}")
            self.sensors = requests.get(url).json()
            print(f"📡 Sensors fetched: {list(self.sensors.keys())}")

            temps = [
                s['state']['temperature'] / 100.0
                for s in self.sensors.values()
                if s.get('type') == 'ZLLTemperature'
            ]

            motions = [
                (s.get('name', 'Unknown'), s['state']['presence'], s['state'].get('lastupdated', ''))
                for s in self.sensors.values()
                if s.get('type') == 'ZLLPresence'
            ]

            if self.motion_label:
                if motions:
                    motion_texts = []
                    for name, presence, last_updated in motions:
                        try:
                            last_time = datetime.strptime(last_updated, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=ZoneInfo("UTC"))
                            local_time = last_time.astimezone()
                            formatted_time = local_time.strftime("%H:%M:%S")
                        except Exception as e:
                            print(f"⚠️ Time parsing error: {e}")
                            formatted_time = last_updated

                        name_html = f"<div style='text-align:center; font-weight:bold;'>{name}</div>"

                        if presence:
                            state_text = f"🚨 {translations.translations[self.app.language]['motion_detected_short']} ({formatted_time})"
                        else:
                            state_text = f"🕐 {translations.translations[self.app.language]['last_motion_short']} ({formatted_time})"

                        sensor_block = f"{name_html}<div style='margin:0px;'>{state_text}</div>"
                        motion_texts.append(sensor_block)

                    self.motion_label.setText("<hr style='margin:1px 0;'>".join(motion_texts))
                else:
                    print("🚶 No motion sensors found")
                    self.motion_label.setText(translations.translations[self.app.language]["no_motion_sensors"])

            if self.devices_status_label:
                print(f"📊 Updating devices status: {len(self.app.lights.lights)} lights, {len(temps)} temps, {len(motions)} motions")
                self.devices_status_label.setText(
                    translations.translations[self.app.language]["devices_status"].format(
                        lights=len(self.app.lights.lights),
                        temps=len(temps),
                        motions=len(motions)
                    )
                )

            if self.sensor_label:
                if temps:
                    avg_temp = sum(temps) / len(temps)
                    print(f"🌡️ Average temperature: {avg_temp:.2f}°C")
                    self.sensor_label.setText(
                        translations.translations[self.app.language]["average_temperature"].format(avg_temp=avg_temp)
                    )
                else:
                    print("🌡️ No temperature sensors found")
                    self.sensor_label.setText(translations.translations[self.app.language]["no_temperature_sensors"])

        except Exception as e:
            print(f"❌ Error fetching sensor data: {e}")
            if self.sensor_label:
                self.sensor_label.setText(translations.translations[self.app.language]["sensor_error"].format(e=e))
            if self.motion_label:
                self.motion_label.setText("")
