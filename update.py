import requests
import os
import sys
import threading
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar
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
                    app.status_label.setText("🔄 Pobieranie aktualizacji...")
                    new_exe_path = os.path.join(os.getcwd(), "HueApp_NEW.exe")

                    with requests.get(exe_url, stream=True) as response:
                        with open(new_exe_path, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)

                    app.status_label.setText("\u2705 Pobieranie zakończone. Uruchom nową wersję.")
                    QMessageBox.information(app, "Zaktualizowano", "Nowa wersja została pobrana jako 'HueApp_NEW.exe'.")
                    sys.exit(0)

                window = QDialog(app)
                window.setWindowTitle("Dostępna aktualizacja")
                layout = QVBoxLayout(window)

                label = QLabel(f"Dostępna wersja: {latest_version}\nTwoja wersja: {VERSION}")
                layout.addWidget(label)

                download_btn = QPushButton("Pobierz teraz")
                download_btn.clicked.connect(download_and_replace)
                layout.addWidget(download_btn)

                cancel_btn = QPushButton("Anuluj")
                cancel_btn.clicked.connect(window.close)
                layout.addWidget(cancel_btn)

                window.exec()

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
            window = QDialog(parent)
            window.setWindowTitle("Aktualizacja wymagana")
            layout = QVBoxLayout(window)

            label = QLabel(f"Zainstalowana wersja: {VERSION}\nDostępna wersja: {latest_version}")
            layout.addWidget(label)

            progress = QProgressBar()
            progress.setMinimum(0)
            progress.setMaximum(100)
            layout.addWidget(progress)

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
                                    percent = int(downloaded * 100 / total)
                                    progress.setValue(percent)
                    label.setText("\u2705 Pobieranie zakończone. Uruchom nową wersję.")
                    launch_btn = QPushButton("Uruchom teraz")
                    launch_btn.clicked.connect(lambda: restart_with_new(local_path))
                    layout.addWidget(launch_btn)

                except Exception as e:
                    label.setText(f"❌ Błąd pobierania: {e}")

            def restart_with_new(path):
                os.startfile(path)
                sys.exit(0)

            threading.Thread(target=download, daemon=True).start()
            window.exec()

        else:
            QMessageBox.information(parent, "Aktualizacja", "Aplikacja jest aktualna.")

    except Exception as e:
        QMessageBox.critical(parent, "Błąd", f"Nie można sprawdzić aktualizacji: {e}")
