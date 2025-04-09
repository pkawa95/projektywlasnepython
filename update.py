import requests
import os
import sys
import subprocess
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
                update_window = ctk.CTkToplevel(app)
                update_window.title("Aktualizacja dostępna")
                update_window.geometry("400x200")

                label = ctk.CTkLabel(
                    update_window,
                    text=f"Dostępna wersja: {latest_version}\nTwoja wersja: {VERSION}",
                    font=ctk.CTkFont(size=14)
                )
                label.pack(pady=20)

                def download_and_restart():
                    app.status_label.configure(text="⬇️ Pobieranie nowej wersji...")
                    headers = {"Accept": "application/octet-stream"}
                    r = requests.get(exe_url, stream=True, headers=headers)

                    new_exe_path = os.path.join(os.getcwd(), "HueApp_NEW.exe")
                    with open(new_exe_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)

                    app.status_label.configure(text="✅ Pobieranie zakończone. Uruchamianie...")
                    update_window.destroy()

                    # Zamknij starą aplikację i uruchom nową
                    subprocess.Popen([new_exe_path])
                    app.destroy()
                    sys.exit()

                update_button = ctk.CTkButton(update_window, text="Zaktualizuj teraz", command=download_and_restart)
                update_button.pack(pady=10)

                cancel_button = ctk.CTkButton(update_window, text="Anuluj", command=update_window.destroy)
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

            label = ctk.CTkLabel(update_window,
                text=f"Dostępna wersja: {latest_version}\nTwoja wersja: {VERSION}",
                font=ctk.CTkFont(size=14), justify="center"
            )
            label.pack(pady=20)

            def download_and_exit():
                headers = {"Accept": "application/octet-stream"}
                r = requests.get(exe_url, stream=True, headers=headers)
                new_path = os.path.join(os.getcwd(), "HueApp_NEW.exe")

                with open(new_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

                tkinter.messagebox.showinfo("Zaktualizowano", f"Nowa wersja została pobrana jako: {new_path}\nZamknij aplikację i uruchom nowy plik.")
                parent.destroy()
                sys.exit()

            update_btn = ctk.CTkButton(update_window, text="Pobierz aktualizację", command=download_and_exit)
            update_btn.pack(pady=10)

            update_window.protocol("WM_DELETE_WINDOW", lambda: None)
        else:
            print("Aplikacja jest aktualna.")

    except Exception as e:
        tkinter.messagebox.showerror("Błąd", f"Nie można sprawdzić aktualizacji: {e}")
