
import requests
import os
import sys
import customtkinter as ctk
from config import VERSION, UPDATE_URL
import subprocess
import threading
import tkinter

def check_for_updates_with_gui_and_replace(app):
    def check():
        try:
            response = requests.get(UPDATE_URL, timeout=5)
            response.raise_for_status()
            version_data = response.json()

            latest_version = version_data.get("version")
            exe_url = version_data.get("exe_url")

            if latest_version and latest_version != VERSION:
                download_window = ctk.CTkToplevel(app)
                download_window.title("Dostępna aktualizacja")
                download_window.geometry("400x200")
                download_window.resizable(False, False)

                label = ctk.CTkLabel(download_window, text=f"Dostępna nowa wersja: {latest_version}", font=ctk.CTkFont(size=14))
                label.pack(pady=20)

                progress = ctk.CTkProgressBar(download_window, orientation="horizontal")
                progress.pack(pady=10, fill="x", padx=20)
                progress.set(0)

                def do_download():
                    download_path = os.path.join(os.getcwd(), "HueApp_NEW.exe")
                    try:
                        with requests.get(exe_url, stream=True) as r:
                            r.raise_for_status()
                            total = int(r.headers.get('content-length', 0))
                            downloaded = 0

                            with open(download_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        progress.set(downloaded / total if total > 0 else 0)

                        label.configure(text="✅ Pobieranie zakończone. Kliknij, aby uruchomić nową wersję.")

                        launch_button = ctk.CTkButton(download_window, text="Uruchom nową wersję", command=lambda: launch_new_version(download_path))
                        launch_button.pack(pady=10)

                        close_button = ctk.CTkButton(download_window, text="Zamknij", command=download_window.destroy)
                        close_button.pack(pady=(0, 10))

                    except Exception as e:
                        label.configure(text=f"Błąd pobierania: {e}")

                threading.Thread(target=do_download, daemon=True).start()

        except Exception as e:
            print(f"[Aktualizator] Błąd sprawdzania wersji: {e}")

    threading.Thread(target=check, daemon=True).start()

def launch_new_version(download_path):
    try:
        subprocess.Popen([download_path], shell=True)
        sys.exit(0)
    except Exception as e:
        print(f"Błąd uruchamiania nowej wersji: {e}")

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

            label = ctk.CTkLabel(
                update_window,
                text=f"Dostępna wersja: {latest_version}\nTwoja wersja: {VERSION}",
                font=ctk.CTkFont(size=14),
                justify="center"
            )
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

                tkinter.messagebox.showinfo(
                    "Zaktualizowano",
                    f"Nowa wersja została pobrana jako: {new_path}\nZamknij aplikację i uruchom nowy plik."
                )
                sys.exit(0)

            update_btn = ctk.CTkButton(update_window, text="Pobierz aktualizację", command=download_and_exit)
            update_btn.pack(pady=10)

            update_window.protocol("WM_DELETE_WINDOW", lambda: None)
        else:
            print("Aplikacja jest aktualna.")

    except Exception as e:
        tkinter.messagebox.showerror("Błąd", f"Nie można sprawdzić aktualizacji: {e}")
