import customtkinter as ctk
import tkinter.colorchooser as cc
import requests


class GroupView(ctk.CTkFrame):
    def __init__(self, master, app, group_id, group_info, lights, on_back_callback):
        super().__init__(master)
        self.app = app
        self.group_id = group_id
        self.group_info = group_info
        self.lights = lights
        self.on_back = on_back_callback

        self.pack(fill="both", expand=True, padx=10, pady=10)

        # === Wróć ===
        back_btn = ctk.CTkButton(self, text="↩️ Wróć do grup", command=self.on_back)
        back_btn.pack(pady=10)

        # === Lista świateł ===
        for light_id in group_info.get("lights", []):
            light_info = lights.get(light_id)
            if not light_info:
                continue

            light_frame = ctk.CTkFrame(self, corner_radius=10)
            light_frame.pack(pady=6, fill="x", padx=12)

            label = ctk.CTkLabel(light_frame, text=light_info["name"], font=app.font_normal)
            label.pack(side="left", padx=10)

            toggle = ctk.CTkButton(
                light_frame,
                text="Wyłącz" if light_info["state"]["on"] else "Włącz",
                width=80,
                command=lambda i=light_id: self.toggle_light(i)
            )
            toggle.pack(side="right", padx=10)

            if "bri" in light_info["state"]:
                slider = ctk.CTkSlider(light_frame, from_=1, to=254)
                slider.set(light_info["state"]["bri"])
                slider.pack(side="right", padx=10, fill="x", expand=True)
                slider.bind("<ButtonRelease-1>", lambda e, i=light_id, s=slider: self.set_brightness(i, s.get()))

            color_btn = ctk.CTkButton(light_frame, text="Kolor", width=60, command=lambda i=light_id: self.choose_color(i))
            color_btn.pack(side="right", padx=10)

    def toggle_light(self, light_id):
        light = self.lights[light_id]
        new_state = not light["state"]["on"]
        url = f"http://{self.app.bridge.bridge_ip}/api/{self.app.bridge.token}/lights/{light_id}/state"
        try:
            requests.put(url, json={"on": new_state})
            self.app.bridge.update_status("💡 Zmieniono stan światła", "white")
        except Exception as e:
            self.app.bridge.update_status(f"❌ Błąd: {e}", "red")

    def set_brightness(self, light_id, bri):
        url = f"http://{self.app.bridge.bridge_ip}/api/{self.app.bridge.token}/lights/{light_id}/state"
        try:
            requests.put(url, json={"bri": int(bri), "on": True})
            self.app.bridge.update_status("🔆 Zmieniono jasność", "white")
        except Exception as e:
            self.app.bridge.update_status(f"❌ Błąd jasności: {e}", "red")

    def choose_color(self, light_id):
        rgb, _ = cc.askcolor()
        if rgb:
            x, y = self.app.rgb_to_xy(*rgb)
            url = f"http://{self.app.bridge.bridge_ip}/api/{self.app.bridge.token}/lights/{light_id}/state"
            try:
                requests.put(url, json={"xy": [x, y], "on": True})
                self.app.bridge.update_status("🌈 Kolor ustawiony", "white")
            except Exception as e:
                self.app.bridge.update_status(f"❌ Błąd koloru: {e}", "red")
