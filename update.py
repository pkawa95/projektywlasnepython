import requests
import os
import sys
import tempfile
import subprocess
import tkinter.messagebox as mb
import json

from config import VERSION

RELEASE_INFO_URL = "https://raw.githubusercontent.com/pkawa95/projektywlasnepython/main/release.json"

def check_for_updates():
    try:
        res = requests.get(RELEASE_INFO_URL, timeout=5)
        data = res.json()
        latest_version = data.get("version")
        exe_url = data.get("exe_url")

        if latest_version and exe_url and latest_version != VERSION:
            return latest_version, exe_url
    except Exception as e:
        print(f"[Update] Błąd sprawdzania wersji: {e}")
    return None, None

def force_update_from_release(app):
    latest_version, exe_url = check_for_updates()
    if not latest_version:
        return

    answer = mb.askyesno("Aktualizacja dostępna",
                         f"Dostępna jest nowa wersja ({latest_version}). Czy chcesz zaktualizować teraz?")
    if not answer:
        return

    try:
        app.destroy()
        mb.showinfo("Aktualizacja", "Pobieranie nowej wersji...")

        response = requests.get(exe_url, stream=True)
        temp_dir = tempfile.gettempdir()
        exe_path = os.path.join(temp_dir, "HueApp_Updater.exe")

        with open(exe_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        mb.showinfo("Aktualizacja", "Nowa wersja została pobrana.\nAplikacja zostanie uruchomiona ponownie.")
        subprocess.Popen([exe_path])
        sys.exit()

    except Exception as e:
        mb.showerror("Błąd aktualizacji", f"Nie udało się pobrać aktualizacji:\n{e}")
