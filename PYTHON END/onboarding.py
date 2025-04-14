import customtkinter as ctk
from update import force_update_with_progress
import threading
from config import VERSION
import translations


class OnboardingWindow(ctk.CTkToplevel):
    def __init__(self, master, proceed_callback):
        super().__init__(master)
        self.language = master.language if hasattr(master, "language") else "pl"
        self.title(translations.translations[self.language]["welcome_title"])
        self.geometry("560x500")
        self.resizable(False, False)

        self.master = master
        self.bridge = master.bridge
        self.proceed_callback = proceed_callback

        # === Język switch ===
        lang_frame = ctk.CTkFrame(self, corner_radius=8)
        lang_frame.pack(pady=(10, 0))
        self.language_label = ctk.CTkLabel(
            lang_frame,
            text=translations.translations[self.language]["language_label"],
            font=ctk.CTkFont(size=12)
        )
        self.language_label.pack(side="left", padx=5)
        self.lang_switch = ctk.CTkSegmentedButton(lang_frame, values=["PL 🇵🇱", "EN 🇬🇧"], command=self.switch_language)
        self.lang_switch.set("PL 🇵🇱" if self.language == "pl" else "EN 🇬🇧")
        self.lang_switch.pack(side="left", padx=5)

        self.label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=(20, 10))

        self.version_label = ctk.CTkLabel(self, text="")
        self.version_label.pack()

        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=13))
        self.status_label.pack(pady=(20, 10))

        self.check_button = ctk.CTkCheckBox(self, text="", command=self.toggle_confirm)
        self.check_button.pack(pady=(5, 5))

        self.confirmed = False

        self.info_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            wraplength=400,
            justify="center"
        )
        self.info_label.pack(pady=(10, 15))

        self.start_button = ctk.CTkButton(self, text="", state="disabled", command=self.begin_installation)
        self.start_button.pack(pady=(10, 20))

        self.tips_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=450,
            justify="left"
        )
        self.tips_label.pack(pady=(10, 10))

        self.update_button = ctk.CTkButton(self, text="", command=lambda: force_update_with_progress(self))
        self.update_button.pack(pady=(0, 10))

        self.after(300, self.find_bridge)
        self.update_texts()  # Aktualizacja tekstów

    def switch_language(self, lang):
        self.language = "pl" if lang.startswith("PL") else "en"
        self.master.language = self.language
        self.update_texts()

    def update_texts(self):
        t = translations.translations[self.language]
        self.title(t["welcome_title"])
        self.label.configure(text=t["welcome_text"])
        self.version_label.configure(text=t["current_version"].format(version=VERSION))
        self.status_label.configure(text=t["searching_bridge"])
        self.check_button.configure(text=t["blue_led_hint"])
        self.info_label.configure(text=t["bridge_connection_hint"])
        self.start_button.configure(text=t["start_installation"])
        self.tips_label.configure(text=t["troubleshooting"])
        self.update_button.configure(text=t["check_updates"])

    def toggle_confirm(self):
        self.confirmed = self.check_button.get()
        self.start_button.configure(state="normal" if self.confirmed else "disabled")

    def find_bridge(self):
        def worker():
            self.bridge.connect_fully_automatic(self.bridge_found_success)
        threading.Thread(target=worker, daemon=True).start()

    def bridge_found_success(self):
        t = translations.translations[self.language]
        self.status_label.configure(text=t["bridge_found"].format(ip=self.bridge.bridge_ip))

    def begin_installation(self):
        t = translations.translations[self.language]
        self.status_label.configure(text=t["waiting_for_button"])
        self.bridge.request_token(self.on_token_received)

    def on_token_received(self):
        t = translations.translations[self.language]
        self.status_label.configure(text=t["token_received"])
        self.after(1000, self.proceed_callback)
