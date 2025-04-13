import customtkinter as ctk
import tkinter.messagebox as mb
from update import force_update_from_release
from config import VERSION
import threading

class OnboardingWindow:
    def __init__(self, app, on_complete_callback):
        self.app = app
        self.on_complete_callback = on_complete_callback
        self.bridge = app.bridge
        self.init_gui()

    def init_gui(self):
        self.window = ctk.CTkToplevel(self.app)
        self.window.title("Witaj w aplikacji Philips Hue")
        self.window.geometry("500x400")
        self.window.grab_set()  # zablokowanie głównego okna

        self.status_label = ctk.CTkLabel(self.window, text=f"Aplikacja Philips Hue by Piotr Kawa\nWersja: {VERSION}", font=ctk.CTkFont(size=15, weight="bold"))
        self.status_label.pack(pady=20)

        # Sprawdzenie dostępności aktualizacji
        self.check_for_updates()

    def check_for_updates(self):
        threading.Thread(target=self._check_for_updates_thread, daemon=True).start()

    def _check_for_updates_thread(self):
        force_update_from_release(self.window)
        self.show_network_permission()

    def show_network_permission(self):
        self.status_label.configure(text=f"Aplikacja Philips Hue by Piotr Kawa\nWersja: {VERSION}\n\nCzy chcesz rozpocząć konfigurację mostka Hue?")

        self.permission_var = ctk.BooleanVar()
        self.permission_checkbox = ctk.CTkCheckBox(self.window, text="Zezwól na przeszukanie sieci lokalnej", variable=self.permission_var)
        self.permission_checkbox.pack(pady=10)

        self.continue_button = ctk.CTkButton(self.window, text="Dalej", command=self.start_bridge_setup)
        self.continue_button.pack(pady=20)

    def start_bridge_setup(self):
        if not self.permission_var.get():
            mb.showwarning("Wymagane zezwolenie", "Musisz wyrazić zgodę na przeszukanie sieci lokalnej.")
            return

        self.permission_checkbox.pack_forget()
        self.continue_button.pack_forget()
        self.status_label.configure(text="🔍 Szukanie mostka Hue w sieci...")

        threading.Thread(target=self.find_and_connect_bridge, daemon=True).start()

    def find_and_connect_bridge(self):
        found = self.bridge.search_bridge_gui()

        if not found:
            self.show_retry_instructions()
            return

        self.status_label.configure(text=f"Znaleziono mostek Hue\nIP: {self.bridge.bridge_ip}\n⏳ Oczekiwanie na wciśnięcie przycisku...")
        success = self.bridge.authorize_gui(timeout=30)

        if success:
            self.bridge.save_ip()
            self.bridge.save_token()
            self.status_label.configure(text="✅ Połączono z mostkiem!\nKliknij, aby rozpocząć korzystanie z aplikacji.")
            ctk.CTkButton(self.window, text="Rozpocznij korzystanie", command=self.complete).pack(pady=15)
        else:
            self.show_retry_instructions(press_failed=True)

    def show_retry_instructions(self, press_failed=False):
        text = "❌ Instalacja nie powiodła się.\n"
        if press_failed:
            text += "Nie wykryto wciśnięcia przycisku na mostku Hue.\n"
        text += "\n🔌 Sprawdź:\n- Czy mostek Hue jest podłączony do prądu\n- Czy znajduje się w tej samej sieci co komputer\n\n"
        text += "Jeśli problem nadal występuje:\n➡️ Odłącz mostek od prądu i podłącz ponownie\n⬅️ Poczekaj aż zapalą się wszystkie diody"

        self.status_label.configure(text=text)

        self.retry_var = ctk.BooleanVar()
        self.retry_checkbox = ctk.CTkCheckBox(self.window, text="Wszystkie diody się palą", variable=self.retry_var)
        self.retry_checkbox.pack(pady=10)

        self.retry_button = ctk.CTkButton(self.window, text="Spróbuj ponownie", command=self.retry_installation)
        self.retry_button.pack(pady=10)

    def retry_installation(self):
        if not self.retry_var.get():
            mb.showwarning("Wymagane potwierdzenie", "Zaznacz, że wszystkie diody się palą, zanim spróbujesz ponownie.")
            return

        self.retry_checkbox.pack_forget()
        self.retry_button.pack_forget()
        self.status_label.configure(text="🔁 Ponowne wyszukiwanie mostka...")

        threading.Thread(target=self.find_and_connect_bridge, daemon=True).start()

    def complete(self):
        self.window.destroy()
        self.on_complete_callback()
