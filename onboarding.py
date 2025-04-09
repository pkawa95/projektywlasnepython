import customtkinter as ctk
from config import VERSION
import os


class OnboardingWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Konfiguracja Philips Hue")
        self.geometry("600x400")

        self.intro_label = ctk.CTkLabel(self, text=f"Aplikacja Philips Hue by Piotr Kawa\nWersja: {VERSION}",
                                        font=ctk.CTkFont(size=16, weight="bold"))
        self.intro_label.pack(pady=20)

        self.info_label = ctk.CTkLabel(self, text="Aby rozpocząć konfigurację mostka Hue,\nkliknij poniżej:",
                                       font=ctk.CTkFont(size=13))
        self.info_label.pack(pady=10)

        self.start_button = ctk.CTkButton(self, text="Rozpocznij instalację HUE", command=self.step_one)
        self.start_button.pack(pady=10)

        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=10)

    def step_one(self):
        self.start_button.destroy()
        self.info_label.destroy()

        self.status_label.configure(text="Wyszukiwanie mostka Hue...")

        # Symulacja statusu onboarding
        self.after(2000, self.show_checkbox)

    def show_checkbox(self):
        self.checkbox = ctk.CTkCheckBox(self, text="Zezwól na przeszukanie sieci lokalnej", command=self.enable_next)
        self.checkbox.pack(pady=10)

        self.next_button = ctk.CTkButton(self, text="Dalej", state="disabled", command=self.try_connect)
        self.next_button.pack(pady=10)

    def enable_next(self):
        self.next_button.configure(state="normal")

    def try_connect(self):
        self.status_label.configure(text="Próba połączenia z mostkiem...")

        # Symulacja niepowodzenia
        self.after(3000, self.show_failed)

    def show_failed(self):
        self.status_label.configure(text="Instalacja nie powiodła się.\n\nSprawdź:\n- Czy mostek jest włączony\n- Czy jest w tej samej sieci\n\nOdłącz i podłącz mostek ponownie,\nczekaj aż wszystkie diody się zapalą.")

        self.confirm_reset = ctk.CTkCheckBox(self, text="Wszystkie diody się palą", command=self.enable_retry)
        self.confirm_reset.pack(pady=10)

        self.retry_button = ctk.CTkButton(self, text="Spróbuj jeszcze raz", state="disabled", command=self.retry)
        self.retry_button.pack(pady=10)

    def enable_retry(self):
        self.retry_button.configure(state="normal")

    def retry(self):
        self.status_label.configure(text="Ponawianie instalacji...")
        self.retry_button.configure(state="disabled")
        self.confirm_reset.configure(state="disabled")
        self.after(3000, self.complete)

    def complete(self):
        self.status_label.configure(text="Połączono z mostkiem!\nMożesz rozpocząć korzystanie z aplikacji.")
        self.launch_button = ctk.CTkButton(self, text="Uruchom aplikację", command=self.launch_main_app)
        self.launch_button.pack(pady=10)

    def launch_main_app(self):
        self.destroy()
        from main import HueGUIApp
        app = HueGUIApp()
        app.mainloop()
