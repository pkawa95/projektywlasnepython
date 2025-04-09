import customtkinter as ctk
from update import force_update_from_release


class OnboardingWindow(ctk.CTkToplevel):
    def __init__(self, master, proceed_callback):
        super().__init__(master)
        self.title("Witaj w Philips Hue App!")
        self.geometry("500x400")
        self.resizable(False, False)

        self.proceed_callback = proceed_callback

        self.label = ctk.CTkLabel(self, text="Philips Hue App by Piotr Kawa", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=20)

        self.version_label = ctk.CTkLabel(self, text=f"Aktualnie zainstalowana wersja: {master.VERSION}", font=ctk.CTkFont(size=14))
        self.version_label.pack(pady=5)

        self.info_label = ctk.CTkLabel(self, text="Aby rozpocząć, kliknij poniższy przycisk.", font=ctk.CTkFont(size=13))
        self.info_label.pack(pady=10)

        self.check_network_var = ctk.BooleanVar()
        self.check_network_checkbox = ctk.CTkCheckBox(self, text="Zezwól na przeszukanie sieci lokalnej", variable=self.check_network_var)
        self.check_network_checkbox.pack(pady=10)

        self.start_button = ctk.CTkButton(self, text="Rozpocznij instalację HUE", command=self.start_installation)
        self.start_button.pack(pady=20)

        # Sprawdzenie aktualizacji na starcie
        self.after(300, lambda: force_update_from_release(self))

    def start_installation(self):
        if not self.check_network_var.get():
            ctk.CTkMessagebox(title="Uwaga", message="Aby kontynuować, musisz zezwolić na przeszukanie sieci lokalnej.", icon="warning")
            return

        self.destroy()
        self.proceed_callback()
