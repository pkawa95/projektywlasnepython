import requests
import os
import sys
import tkinter.messagebox
import customtkinter as ctk
from config import VERSION, UPDATE_URL

import requests
import json
import webbrowser


def check_for_updates_with_gui_and_replace(app):
    try:
        # Pobierz plik version.txt z GitHub
        response = requests.get(app.UPDATE_URL)

        # Sprawdź odpowiedź
        if response.status_code == 200:
            version_info = response.json()
            print("Odpowiedź z serwera: ", version_info)  # Debugging
        else:
            print("Błąd pobierania pliku version.txt, status:", response.status_code)
            return

        latest_version = version_info["version"]
        exe_url = version_info["exe_url"]

        print(f"Sprawdzanie aktualizacji: lokalna wersja {app.VERSION}, najnowsza wersja {latest_version}")

        # Porównaj wersję lokalną z wersją na serwerze
        if latest_version != app.VERSION:
            print(f"Dostępna nowa wersja: {latest_version}")
            app.show_update_popup(latest_version, exe_url)
        else:
            print("Aplikacja jest aktualna.")
            app.update_status("Aplikacja jest aktualna.")
    except Exception as e:
        print(f"Error checking for updates: {e}")


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
