#sensor_manager.py
import customtkinter as ctk
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

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
            if temps:
                avg_temp = sum(temps) / len(temps)
                self.sensor_label.configure(text=f"Średnia temperatura: {avg_temp:.1f}°C")
            else:
                self.sensor_label.configure(text="Brak czujników temperatury.")

            motions = [
                (s['name'], s['state']['presence'], s['state'].get('lastupdated', ''))
                for s in self.sensors.values()
                if s.get('type') == 'ZLLPresence'
            ]

            if motions:
                last_motion = next((t for _, p, t in motions if p), motions[0][2])
                try:
                    last_time = datetime.strptime(last_motion, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=ZoneInfo("UTC"))
                    local_time = last_time.astimezone()
                    formatted_time = local_time.strftime("%H:%M:%S")
                except:
                    formatted_time = last_motion

                if any(p for _, p, _ in motions):
                    self.motion_label.configure(text=f"Ruch wykryty! 🕺 ({formatted_time})")
                else:
                    self.motion_label.configure(text=f"Ostatni ruch: {formatted_time}")
            else:
                self.motion_label.configure(text="Brak czujników ruchu.")

            self.devices_status_label.configure(
                text=f"Wykryto: {len(self.app.lights.lights)} światła, {len(temps)} temp., {len(motions)} cz. ruchu")

            for widget in self.motion_list_frame.winfo_children():
                widget.destroy()

            for name, presence, lastupdated in motions:
                try:
                    last_time = datetime.strptime(lastupdated, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=ZoneInfo("UTC"))
                    local_time = last_time.astimezone()
                    formatted_time = local_time.strftime("%H:%M:%S")
                except:
                    formatted_time = lastupdated
                status_text = f"{name} - {'Ruch' if presence else 'Brak ruchu'} ({formatted_time})"
                color = "green" if presence else "gray"
                label = ctk.CTkLabel(self.motion_list_frame, text=status_text, text_color=color)
                label.pack(anchor="w", padx=10, pady=2)

        except Exception as e:
            self.sensor_label.configure(text=f"Błąd czujników: {e}")
            self.motion_label.configure(text="")
