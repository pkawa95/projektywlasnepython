import requests
import customtkinter as ctk
import threading
import os
import subprocess

VERSION = "1.0.0"
UPDATE_URL = "https://raw.githubusercontent.com/pkawa95/projektywlasnepython/main/version.txt"
DOWNLOAD_URL = "https://github.com/pkawa95/projektywlasnepython/releases/latest/download/HueApp.exe"

def check_for_updates_with_gui_and_replace(app):
    try:
        response = requests.get(UPDATE_URL, timeout=5)
        if response.status_code == 200:
            latest_version = response.text.strip()
            current_text = f"Wersja: {VERSION} (najnowsza: {latest_version})"

            # Ustawiamy tekst wersji
            if hasattr(app, "version_label"):
                if latest_version != VERSION:
                    app.version_label.configure(text=current_text, text_color="orange")
                else:
                    app.version_label.configure(text=current_text, text_color="gray")

            # Jeśli nowsza wersja, pokaż przycisk i pasek
            if latest_version != VERSION:
                update_label = ctk.CTkLabel(app, text=f"Dostępna nowa wersja: {latest_version}", text_color="orange")
                update_label.pack(pady=5)

                progressbar = ctk.CTkProgressBar(app, width=300)
                progressbar.pack(pady=5)
                progressbar.set(0)

                def download_and_replace():
                    try:
                        r = requests.get(DOWNLOAD_URL, stream=True)
                        total = int(r.headers.get('content-length', 0))
                        downloaded = 0
                        target_path = "HueApp_new.exe"

                        with open(target_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    progressbar.set(downloaded / total)

                        update_label.configure(text="Pobrano. Trwa aktualizacja...", text_color="green")

                        # BAT do podmiany exe
                        bat_content = f"""@echo off
timeout /t 2 >nul
del HueApp.exe
rename HueApp_new.exe HueApp.exe
start HueApp.exe
"""
                        with open("replace_and_restart.bat", "w") as bat_file:
                            bat_file.write(bat_content)

                        subprocess.Popen("replace_and_restart.bat", shell=True)
                        app.after(1000, app.destroy)

                    except Exception as e:
                        update_label.configure(text=f"Błąd pobierania: {e}", text_color="red")

                update_btn = ctk.CTkButton(app, text="Zaktualizuj teraz", command=lambda: threading.Thread(target=download_and_replace).start())
                update_btn.pack(pady=5)

    except Exception as e:
        print(f"Błąd sprawdzania aktualizacji: {e}")
