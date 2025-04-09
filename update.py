import requests
import os
import sys
import tkinter.messagebox
import customtkinter as ctk
from config import VERSION, UPDATE_URL


def check_for_updates_with_gui_and_replace(app):
    def check():
        try:
            response = requests.get(UPDATE_URL, timeout=5)
            response.raise_for_status()
            version_data = response.json()

            latest_version = version_data.get("version")
            exe_url = version_data.get("exe_url")

            if latest_version and latest_version != VERSION:
                def download_and_replace():
                    app.status_label.configure(text="🔄 Pobieranie aktualizacji...")

                    response = requests.get(exe_url, stream=True)
                    new_exe_path = os.path.join(os.getcwd(), "HueApp_NEW.exe")

                    with open(new_exe_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    app.status_label.configure(text="✅ Pobieranie zakończone. Uruchom nową wersję.")
                    tkinter.messagebox.showinfo("Zaktualizowano", "Nowa wersja została pobrana jako 'HueApp_NEW.exe'")

                update_window = ctk.CTkToplevel(app)
                update_window.title("Aktualizacja dostępna")
                update_window.geometry("400x200")

                label = ctk.CTkLabel(update_window, text=f"Dostępna wersja: {latest_version}\nTwoja wersja: {VERSION}", font=ctk.CTkFont(size=14))
                label.pack(pady=20)

                update_button = ctk.CTkButton(update_window, text="Aktualizuj teraz", command=lambda: [
                    update_window.destroy(),
                    download_and_replace()
                ])
                update_button.pack(pady=10)

                cancel_button = ctk.CTkButton(update_window, text="Zamknij", command=update_window.destroy)
                cancel_button.pack()

        except Exception as e:
            print(f"[Aktualizator] Błąd sprawdzania wersji: {e}")

    import threading
    threading.Thread(target=check, daemon=True).start()


def force_update_from_release(parent):
    try:
        response = requests.get(UPDATE_URL, timeout=5)
        response.raise_for_status()
        version_data = response.json()

        latest_version = version_data.get("version")
        exe_url = version_data.get("exe_url")

        if latest_version and latest_version != VERSION:
            update_window = ctk.CTkToplevel(parent)
            update_window.title("Aktualizacja wymagana")
            update_window.geometry("400x200")
            update_window.resizable(False, False)

            label = ctk.CTkLabel(update_window, text=f"Dostępna wersja: {latest_version}\nTwoja wersja: {VERSION}", font=ctk.CTkFont(size=14), justify="center")
            label.pack(pady=20)

            def download_and_exit():
                update_window.destroy()
                parent.update()
                parent.withdraw()

                response = requests.get(exe_url, stream=True)
                new_path = os.path.join(os.getcwd(), "HueApp_NEW.exe")

                with open(new_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                tkinter.messagebox.showinfo("Zaktualizowano", f"Nowa wersja została pobrana jako: {new_path}\nZamknij aplikację i uruchom nowy plik.")
                sys.exit(0)

            update_btn = ctk.CTkButton(update_window, text="Pobierz aktualizację", command=download_and_exit)
            update_btn.pack(pady=10)

            update_window.protocol("WM_DELETE_WINDOW", lambda: None)
        else:
            print("Aplikacja jest aktualna.")

    except Exception as e:
        tkinter.messagebox.showerror("Błąd", f"Nie można sprawdzić aktualizacji: {e}")
