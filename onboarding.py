import customtkinter as ctk
from update import force_update_with_progress
import threading


class OnboardingWindow(ctk.CTkToplevel):
    def __init__(self, master, proceed_callback):
        super().__init__(master)
        self.title("Witaj w Philips Hue App by Piotr Kawa")
        self.geometry("560x500")
        self.resizable(False, False)

        self.master = master
        self.bridge = master.bridge
        self.proceed_callback = proceed_callback

        self.label = ctk.CTkLabel(self, text="Witaj w aplikacji Philips Hue", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=(20, 10))

        self.version_label = ctk.CTkLabel(self, text=f"Zainstalowana wersja: {master.VERSION}", font=ctk.CTkFont(size=14))
        self.version_label.pack()

        self.status_label = ctk.CTkLabel(self, text="🔍 Trwa wyszukiwanie mostka...", font=ctk.CTkFont(size=13))
        self.status_label.pack(pady=(20, 10))

        self.check_button = ctk.CTkCheckBox(self, text="💡 Świeci się niebieska dioda na mostku", command=self.toggle_confirm)
        self.check_button.pack(pady=(5, 5))

        self.confirmed = False

        self.info_label = ctk.CTkLabel(
            self,
            text="Upewnij się, że mostek jest podłączony do zasilania i routera.\nPo jego wykryciu naciśnij przycisk na mostku.",
            font=ctk.CTkFont(size=12),
            wraplength=400,
            justify="center"
        )
        self.info_label.pack(pady=(10, 15))

        self.start_button = ctk.CTkButton(self, text="Rozpocznij instalację HUE", state="disabled", command=self.begin_installation)
        self.start_button.pack(pady=(10, 20))

        self.tips_label = ctk.CTkLabel(
            self,
            text="❓ Masz problem?\n- Sprawdź połączenie z siecią lokalną\n- Sprawdź, czy mostek jest zasilany\n- Naciśnij fizyczny przycisk na mostku",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=450,
            justify="left"
        )
        self.tips_label.pack(pady=(10, 10))

        self.update_button = ctk.CTkButton(self, text="Sprawdź aktualizacje", command=lambda: force_update_with_progress(self))
        self.update_button.pack(pady=(0, 10))

        self.after(300, self.find_bridge)

    def toggle_confirm(self):
        self.confirmed = self.check_button.get()
        self.start_button.configure(state="normal" if self.confirmed else "disabled")

    def find_bridge(self):
        def worker():
            self.bridge.connect_fully_automatic(self.bridge_found_success)
        threading.Thread(target=worker, daemon=True).start()

    def bridge_found_success(self):
        self.status_label.configure(text=f"✅ Mostek wykryty: {self.bridge.bridge_ip}\n⚠️ Wciśnij przycisk na mostku, aby zakończyć instalację.")

    def begin_installation(self):
        self.status_label.configure(text="⌛ Oczekiwanie na przycisk na mostku (30s)...")
        self.bridge.request_token(self.on_token_received)

    def on_token_received(self):
        self.status_label.configure(text="✅ Token uzyskany! Uruchamiam aplikację...")
        self.after(1000, self.proceed_callback)
