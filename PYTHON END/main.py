from group_tile import GroupTile
import customtkinter as ctk
import requests
import tkinter.colorchooser as cc
import threading
import time
from config import VERSION, UPDATE_URL
from onboarding import OnboardingWindow
from hue_bridge import HueBridge
from light_manager import LightManager
from sensor_manager import SensorManager
from group_view import GroupView
import translations


class GroupSlider(ctk.CTkFrame):
    def __init__(self, master, app, group_id, group_info, on_double_click):
        super().__init__(master)
        self.app = app
        self.group_id = group_id
        self.group_info = group_info
        self.on_double_click = on_double_click
        self.group_state = group_info["action"]["on"]
        self.bri = group_info["action"].get("bri", 254)

        self.slider = ctk.CTkSlider(self, from_=1, to=254)
        self.slider.set(self.bri)
        self.slider.pack(fill="x", padx=10, pady=5)
        self.slider.bind("<ButtonRelease-1>", self.on_slider_release)

        self.label = ctk.CTkLabel(self, text=group_info["name"], font=app.font_title)
        self.label.place(relx=0.5, rely=0.5, anchor="center")

        self.slider.bind("<Button-1>", self.single_click)
        self.slider.bind("<Double-Button-1>", self.double_click)

    def on_slider_release(self, event):
        value = self.slider.get()
        self.app.set_group_brightness(self.group_id, value)

    def single_click(self, event):
        current_state = self.app.bridge.groups[self.group_id]["action"]["on"]
        self.app.toggle_group(self.group_id, not current_state)

    def double_click(self, event):
        self.on_double_click(self.group_id)


class HueGUIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(translations.translations["pl"]["app_title"])
        self.geometry("720x860")
        ctk.set_default_color_theme("blue")
        ctk.set_appearance_mode("dark")

        # Zablokowanie zmiany rozmiaru okna
        self.resizable(False, False)
        self.font_title = ctk.CTkFont(size=16, weight="bold")
        self.font_normal = ctk.CTkFont(size=13)
        self.group_widgets = {}
        self.current_view = "groups"
        self.language = "pl"

        self.bridge = HueBridge()
        self.bridge.on_groups_fetched = self.update_group_widgets
        self.lights = LightManager(self, self.bridge)
        self.sensors = SensorManager(self, self.bridge)
        self.bridge.set_app(self)

        top_frame = ctk.CTkFrame(self, corner_radius=12)
        top_frame.pack(fill="x", padx=10, pady=8)

        self.label = ctk.CTkLabel(top_frame, text=translations.translations[self.language]["welcome_text"], font=self.font_title)
        self.label.pack(side="left", padx=10)

        self.version_btn = ctk.CTkButton(top_frame, text="🔍 Sprawdź aktualizacje", width=180, command=self.check_for_updates)
        self.version_btn.pack(side="right", padx=10)

        ctk.CTkLabel(top_frame, text=f"📦 Wersja: {VERSION}", font=self.font_normal).pack(side="right", padx=(0, 5))

        self.status_label = ctk.CTkLabel(self, text="🔄 Status mostka: Oczekiwanie...", font=self.font_normal, text_color="white")
        self.status_label.pack(pady=(0, 6))
        self.bridge.status_label = self.status_label

        self.progress_bar = ctk.CTkProgressBar(self, width=600)
        self.progress_bar.set(1.0)
        self.progress_bar.pack(pady=(0, 10))

        lang_frame = ctk.CTkFrame(self, corner_radius=8)
        lang_frame.pack(pady=4)

        ctk.CTkLabel(
            lang_frame,
            text=translations.translations[self.language]["language_label"],
            font=self.font_normal
        ).pack(side="left", padx=8)

        self.lang_switch = ctk.CTkSegmentedButton(lang_frame, values=["PL 🇵🇱", "EN 🇬🇧"])
        self.lang_switch.set("PL 🇵🇱")
        self.lang_switch.pack(side="left", padx=5)
        self.lang_switch.configure(command=self.switch_language)  # Zmieniamy bind na command

        if self.bridge.token and self.bridge.bridge_ip:
            try:
                res = requests.get(f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/config", timeout=3)
                if res.status_code == 200:
                    self.start_main_app()
                else:
                    raise Exception("Token nieważny")
            except:
                self.onboarding = OnboardingWindow(self, self.start_main_app)
                self.onboarding.grab_set()
        else:
            self.onboarding = OnboardingWindow(self, self.start_main_app)
            self.onboarding.grab_set()

    def start_main_app(self):
        if hasattr(self, "onboarding"):
            self.onboarding.destroy()

        self.bridge.set_app(self)

        self.reset_button = ctk.CTkButton(self, text="🔁 Resetuj token i IP", command=self.bridge.reset_config)
        self.reset_button.pack(pady=8)

        self.rooms_label = ctk.CTkLabel(
            self,
            text=translations.translations[self.language]["rooms_label"],
            font=self.font_title,
            anchor="w"  # ⬅️ wyrównanie tekstu do lewej
        )
        self.rooms_label.pack(pady=(5, 0), padx=10, fill="x")

        self.lights_frame = ctk.CTkScrollableFrame(
            self,
            width=680,
            height=400,
            corner_radius=14,
            fg_color="transparent"  # ⬅️ dodaj to!
        )
        self.lights_frame.pack(pady=10, padx=10, fill="both", expand=True)


        self.info_frame, self.sensor_label, self.motion_label, self.devices_status_label = self.sensors.create_info_frame()
        self.info_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        #self.motion_list_frame = self.sensors.create_motion_list_frame()

        #self.version_label = ctk.CTkLabel(self, text=f"📦 Wersja aplikacji: {VERSION}", font=self.font_normal)
        #self.version_label.pack(pady=10)

        self.after(200, self.check_for_updates)
        self.after(400, self.start_auto_updater)

    def check_for_updates(self):
        def worker():
            try:
                self.version_btn.configure(state="disabled", text="⏳ Sprawdzanie...")
                res = requests.get(UPDATE_URL, timeout=5)
                data = res.json()
                latest = data.get("version")
                exe_url = data.get("exe_url")

                if latest and latest != VERSION:
                    def download_update():
                        self.version_btn.configure(state="disabled", text="⬇️ Pobieranie...")
                        r = requests.get(exe_url, stream=True)
                        with open("HueApp_NEW.exe", "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                        self.version_btn.configure(text="✅ Pobrano!", fg_color="green")

                    self.version_btn.configure(text="⬇️ Aktualizuj teraz", fg_color="red", command=download_update)
                else:
                    self.version_btn.configure(text="✅ Wersja aktualna", fg_color="green")
            except:
                self.version_btn.configure(text="❌ Błąd sprawdzania", fg_color="gray")
            finally:
                self.version_btn.configure(state="normal")

        threading.Thread(target=worker, daemon=True).start()

    def fade_out(self, on_finish, step=0.05, delay=10):
        def animate(alpha):
            if alpha <= 0:
                self.attributes("-alpha", 0)
                on_finish()
                return
            self.attributes("-alpha", alpha)
            self.after(delay, lambda: animate(alpha - step))

        animate(1.0)

    def fade_in(self, step=0.05, delay=10):
        def animate(alpha):
            if alpha >= 1:
                self.attributes("-alpha", 1)
                return
            self.attributes("-alpha", alpha)
            self.after(delay, lambda: animate(alpha + step))

        animate(0.0)
    def start_auto_updater(self):
        self.lights.fetch()
        self.bridge.fetch_groups()
        self.sensors.fetch()
        if self.current_view == "groups":
            self.update_group_widgets()

        # ⏱️ Harmonogram aktualizacji co 1000 ms (1 sekunda)
        self.after(1000, self.start_auto_updater)
    def show_lights_in_group(self, group_id):
        self.current_view = "lights_in_group"

        if self.lights_frame:
            self.scroll_position = self.lights_frame._parent_canvas.yview()
            self.fade_out(lambda: self.lights_frame.pack_forget())

        group_info = self.bridge.groups.get(group_id)
        if not group_info:
            self.bridge.update_status(f"❌ Brak danych grupy {group_id}")
            return

        self.group_view = GroupView(
            master=self,
            app=self,
            group_id=group_id,
            group_info=group_info,
            lights=self.lights.lights,
            on_back_callback=self.back_to_group_list
        )
        self.group_view.pack(pady=10, padx=10, fill="both", expand=True)
        self.fade_in()

    def back_to_group_list(self):
        self.current_view = "groups"

        if self.group_view:
            self.fade_out(lambda: self.group_view.destroy())

        if self.lights_frame:
            self.lights_frame.pack(pady=10, padx=10, fill="both", expand=True)
            if hasattr(self, "scroll_position"):
                self.lights_frame._parent_canvas.yview_moveto(self.scroll_position[0])
            self.fade_in()

    def back_to_group_list(self):
        self.current_view = "groups"

        if self.group_view:
            self.group_view.destroy()
            self.group_view = None

        if self.lights_frame:
            self.lights_frame.pack(pady=10, padx=10, fill="both", expand=True)

    def update_group_widgets(self):
        groups = self.bridge.groups

        # Usuwamy tylko te kafelki, które już nie istnieją LUB nie są typu Room
        for group_id in list(self.group_widgets):
            if group_id not in groups or groups[group_id].get("type") != "Room":
                self.group_widgets[group_id].destroy()
                del self.group_widgets[group_id]

        for group_id, group_info in groups.items():
            # Pomiń wszystkie poza "Room"
            if group_info.get("type") != "Room":
                continue

            if group_id in self.group_widgets:
                # Aktualizacja istniejącego kafelka
                tile = self.group_widgets[group_id]
                tile.group_info = group_info
                tile.slider.set(group_info["action"].get("bri", 254))
                tile.update_toggle_color()
            else:
                # Tworzenie nowego kafelka tylko jeśli nie istnieje
                tile = GroupTile(
                    master=self.lights_frame,
                    app=self,
                    group_id=group_id,
                    group_info=group_info,
                    on_double_click=self.show_lights_in_group
                )
                tile.pack(pady=10, padx=10, fill="x")
                self.group_widgets[group_id] = tile

    def toggle_group(self, group_id, new_state=None):
        current_state = self.bridge.groups[group_id]["action"]["on"]
        if new_state is None:
            new_state = not current_state
        url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/groups/{group_id}/action"
        try:
            requests.put(url, json={"on": new_state})
        except Exception as e:
            self.bridge.update_status(f"❌ Błąd grupy: {e}")

    def set_group_brightness(self, group_id, bri):
        url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/groups/{group_id}/action"
        try:
            requests.put(url, json={"bri": int(bri), "on": True})
        except Exception as e:
            self.bridge.update_status(f"❌ Błąd jasności grupy: {e}")

    def choose_group_color(self, group_id):
        rgb, _ = cc.askcolor()
        if rgb:
            x, y = self.rgb_to_xy(*rgb)
            url = f"http://{self.bridge.bridge_ip}/api/{self.bridge.token}/groups/{group_id}/action"
            try:
                requests.put(url, json={"xy": [x, y], "on": True})
            except Exception as e:
                self.bridge.update_status(f"❌ Błąd koloru grupy: {e}")

    def rgb_to_xy(self, r, g, b):
        r, g, b = [x / 255.0 for x in (r, g, b)]
        r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
        g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
        b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
        X = r * 0.649926 + g * 0.103455 + b * 0.197109
        Y = r * 0.234327 + g * 0.743075 + b * 0.022598
        Z = g * 0.053077 + b * 1.035763
        if X + Y + Z == 0:
            return 0, 0
        x = X / (X + Y + Z)
        y = Y / (X + Y + Z)
        return round(x, 4), round(y, 4)

    def switch_language(self, value):
        # Zmieniamy język w zależności od wybranego segmentu
        self.language = "pl" if value == "PL 🇵🇱" else "en"
        self.update_ui()

    def update_ui(self):
        # Zaktualizuj wszystkie teksty w aplikacji po zmianie języka
        self.label.configure(text=translations.translations[self.language]["welcome_text"])
        self.version_btn.configure(text=translations.translations[self.language]["check_updates"])
        self.lang_switch.set("PL 🇵🇱" if self.language == "pl" else "EN 🇬🇧")
        self.title(translations.translations[self.language]["app_title"])
        self.rooms_label.configure(text=translations.translations[self.language]["rooms_label"])


if __name__ == "__main__":
    app = HueGUIApp()
    app.mainloop()
