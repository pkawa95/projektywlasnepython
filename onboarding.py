import customtkinter as ctk
from update import force_update_from_release


class OnboardingWindow(ctk.CTkToplevel):
    def __init__(self, master, proceed_callback):
        super().__init__(master)
        self.title("Witaj w Philips Hue App!")
        self.geometry("600x500")
        self.resizable(False, False)

        self.master = master
        self.proceed_callback = proceed_callback
        self.stage = 0  # kontrola etapu onboardingu

        self.version_label = ctk.CTkLabel(self, text=f"Aktualnie zainstalowana wersja: {master.VERSION}",
                                          font=ctk.CTkFont(size=14))
        self.version_label.pack(pady=(20, 5))

        self.update_label = ctk.CTkLabel(self, text="Trwa sprawdzanie aktualizacji...",
                                         font=ctk.CTkFont(size=13))
        self.update_label.pack(pady=(0, 15))

        # Checkbox sieci
        self.check_network_var = ctk.BooleanVar()
        self.check_network_checkbox = ctk.CTkCheckBox(self, text="Zezwól na przeszukanie sieci lokalnej",
                                                      variable=self.check_network_var)
        self.check_network_checkbox.pack(pady=10)

        # Przycisk startowy
        self.start_button = ctk.CTkButton(self, text="Rozpocznij instalację HUE", command=self.start_installation)
        self.start_button.pack(pady=20)

        # Etap 2 - informacja o statusie
        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=13))
        self.status_label.pack(pady=(10, 5))

        # Etap 3 - błąd + porady
        self.retry_checkbox_var = ctk.BooleanVar()
        self.retry_checkbox = ctk.CTkCheckBox(self, text="Wszystkie diody mostka się świecą",
                                              variable=self.retry_checkbox_var)
        self.retry_button = ctk.CTkButton(self, text="Spróbuj jeszcze raz", command=self.retry_installation)

        # Sprawdzenie aktualizacji — obowiązkowe
        self.after(300, lambda: force_update_from_release(self, self.update_label))

    def start_installation(self):
        if not self.check_network_var.get():
            ctk.CTkMessagebox(title="Uwaga", message="Musisz zaznaczyć opcję zezwolenia na przeszukanie sieci.", icon="warning")
            return

        self.stage = 1
        self.update_label.configure(text="")
        self.start_button.configure(state="disabled")
        self.check_network_checkbox.configure(state="disabled")

        self.status_label.configure(text="🔍 Szukam mostka Hue i czekam na wciśnięcie przycisku...")
        self.after(3000, self.simulate_bridge_found)

    def simulate_bridge_found(self):
        # Tu można podpiąć realne połączenie
        success = False  # na potrzeby testu ustawiamy błąd
        if success:
            self.status_label.configure(text="✅ Mostek znaleziony i połączony!")
            self.after(1000, lambda: (self.destroy(), self.proceed_callback()))
        else:
            self.status_label.configure(text="❌ Instalacja nie powiodła się.\n\n"
                                             "👉 Sprawdź czy mostek Hue jest podłączony i aktywny.\n"
                                             "🔌 Jeśli to nie pomoże, odłącz go na 10 sekund, włącz i poczekaj na zapalenie się wszystkich diod.")
            self.retry_checkbox.pack(pady=(10, 0))
            self.retry_button.pack(pady=(5, 15))

    def retry_installation(self):
        if not self.retry_checkbox_var.get():
            ctk.CTkMessagebox(title="Uwaga", message="Musisz potwierdzić, że wszystkie diody się palą.", icon="warning")
            return
        self.retry_checkbox.pack_forget()
        self.retry_button.pack_forget()
        self.status_label.configure(text="🔄 Próba ponownego połączenia...")
        self.after(3000, self.simulate_bridge_found)
