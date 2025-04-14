import customtkinter as ctk
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import translations  # Dodanie importu tłumaczeń

class SensorManager:
    def __init__(self, app, bridge):
        self.app = app
        self.bridge = bridge
        self.sensors = {}

    def create_info_frame(self):
        frame = ctk.CTkFrame(self.app)
        frame.pack(pady=5, padx=10, fill="x")

        sensor_label = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=13))
        sensor_label.pack(pady=2)

        motion_label = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=13))
        motion_label.pack(pady=2)

        devices_status_label = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=12, weight="normal"))
        devices_status_label.pack(pady=5)

        self.sensor_label = sensor_label
        self.motion_label = motion_label
        self.devices_status_label = devices_status_label
        return frame, sensor_label, motion_label, devices_status_label

    def create_motion_list_frame(self):
        frame = ctk.CTkScrollableFrame(self.app, width=600, height=150)
        frame.pack(pady=5, padx=10, fill="both", expand=False)
        self.motion_list_frame = frame
        return frame

    def fetch(self):
        try:
            url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/sensors"
            self.sensors = requests.get(url).json()

            temps = [
                s['state']['temperature'] / 100.0
                for s in self.sensors.values()
                if s.get('type') == 'ZLLTemperature'
            ]
            if temps and hasattr(self, "sensor_label"):
                avg_temp = sum(temps) / len(temps)
                self.sensor_label.configure(text=translations.translations[self.app.language]["average_temperature"].format(avg_temp=avg_temp))
            elif hasattr(self, "sensor_label"):
                self.sensor_label.configure(text=translations.translations[self.app.language]["no_temperature_sensors"])

            motions = [
                (s['name'], s['state']['presence'], s['state'].get('lastupdated', ''))
                for s in self.sensors.values()
                if s.get('type') == 'ZLLPresence'
            ]

            if hasattr(self, "motion_label"):
                if motions:
                    last_motion = next((t for _, p, t in motions if p), motions[0][2])
                    try:
                        from datetime import datetime
                        from zoneinfo import ZoneInfo
                        last_time = datetime.strptime(last_motion, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=ZoneInfo("UTC"))
                        local_time = last_time.astimezone()
                        formatted_time = local_time.strftime("%H:%M:%S")
                    except:
                        formatted_time = last_motion

                    if any(p for _, p, _ in motions):
                        self.motion_label.configure(text=translations.translations[self.app.language]["motion_detected"].format(formatted_time=formatted_time))
                    else:
                        self.motion_label.configure(text=translations.translations[self.app.language]["last_motion"].format(formatted_time=formatted_time))
                else:
                    self.motion_label.configure(text=translations.translations[self.app.language]["no_motion_sensors"])

            if hasattr(self, "devices_status_label"):
                self.devices_status_label.configure(
                    text=translations.translations[self.app.language]["devices_status"].format(
                        lights=len(self.app.lights.lights),
                        temps=len(temps),
                        motions=len(motions)
                    )
                )

        except Exception as e:
            if hasattr(self, "sensor_label"):
                self.sensor_label.configure(text=translations.translations[self.app.language]["sensor_error"].format(e=e))
            if hasattr(self, "motion_label"):
                self.motion_label.configure(text="")

        except Exception as e:
            self.sensor_label.configure(text=translations.translations[self.app.language]["sensor_error"].format(e=e))
            self.motion_label.configure(text="")

