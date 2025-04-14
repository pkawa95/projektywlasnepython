import requests
import os
import sys
import threading
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
                    new_exe_path = os.path.join(os.getcwd(), "HueApp_NEW.exe")

                    with requests.get(exe_url, stream=True) as response:
                        with open(new_exe_path, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)

                    app.status_label.configure(text="✅ Pobieranie zakończone. Uruchom nową wersję.")
                    tkinter.messagebox.showinfo("Zaktualizowano",
                                                "Nowa wersja została pobrana jako 'HueApp_NEW.exe'.")
                    sys.exit(0)

                update_window = ctk.CTkToplevel(app)
                update_window.title("Dostępna aktualizacja")
                update_window.geometry("400x200")
                update_window.resizable(False, False)

                ctk.CTkLabel(update_window,
                             text=f"Dostępna wersja: {latest_version}\nTwoja wersja: {VERSION}",
                             font=ctk.CTkFont(size=14),
                             justify="center").pack(pady=20)

                ctk.CTkButton(update_window, text="Pobierz teraz", command=download_and_replace).pack(pady=10)
                ctk.CTkButton(update_window, text="Anuluj", command=update_window.destroy).pack()

        except Exception as e:
            print(f"[Aktualizator] Błąd sprawdzania wersji: {e}")

    threading.Thread(target=check, daemon=True).start()


def force_update_with_progress(parent):
    try:
        response = requests.get(UPDATE_URL, timeout=5)
        response.raise_for_status()
        version_data = response.json()

        latest_version = version_data.get("version")
        exe_url = version_data.get("exe_url")

        if latest_version and latest_version != VERSION:
            window = ctk.CTkToplevel(parent)
            window.title("Aktualizacja wymagana")
            window.geometry("400x250")
            window.resizable(False, False)

            label = ctk.CTkLabel(window, text=f"Zainstalowana wersja: {VERSION}\nDostępna wersja: {latest_version}",
                                 font=ctk.CTkFont(size=14), justify="center")
            label.pack(pady=10)

            progress = ctk.CTkProgressBar(window, width=300)
            progress.pack(pady=20)
            progress.set(0)

            def download():
                local_path = os.path.join(os.getcwd(), "HueApp_NEW.exe")
                try:
                    with requests.get(exe_url, stream=True) as r:
                        total = int(r.headers.get("content-length", 0))
                        downloaded = 0
                        with open(local_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    progress.set(downloaded / total)
                    label.configure(text="✅ Pobieranie zakończone. Uruchom nową wersję.")
                    ctk.CTkButton(window, text="Uruchom teraz", command=lambda: restart_with_new(local_path)).pack(pady=10)

                except Exception as e:
                    label.configure(text=f"❌ Błąd pobierania: {e}")

            threading.Thread(target=download, daemon=True).start()

            def restart_with_new(path):
                os.startfile(path)
                sys.exit(0)

            window.protocol("WM_DELETE_WINDOW", lambda: None)
        else:
            print("Aplikacja jest aktualna.")

    except Exception as e:
        tkinter.messagebox.showerror("Błąd", f"Nie można sprawdzić aktualizacji: {e}")
