from PyQt6.QtWidgets import (
    QDialog, QLabel, QPushButton, QCheckBox, QVBoxLayout, QHBoxLayout, QComboBox,
    QSpacerItem, QSizePolicy, QGroupBox, QMessageBox, QProgressBar
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
import threading
from update import force_update_with_progress
from config import VERSION
import translations


class OnboardingWindow(QDialog):
    def __init__(self, bridge, proceed_callback):
        super().__init__(parent=None)
        self.language = "pl"
        self.bridge = bridge
        self.proceed_callback = proceed_callback

        self.setWindowTitle(translations.translations[self.language]["welcome_title"])
        self.resize(600, 600)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)
        self.setStyleSheet("""
            QLabel {
                font-size: 15px;
            }
            QPushButton {
                font-size: 16px;
                padding: 8px 16px;
                border-radius: 8px;
                color: white;
            }
            QPushButton:enabled {
                background-color: #4CAF50;
            }
            QPushButton:enabled:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #888888;
                color: #eeeeee;
            }
            QCheckBox {
                font-size: 14px;
            }
            QComboBox {
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)

        header = QLabel("🌈 Hue Bridge Onboarding")
        header.setFont(QFont("Arial", 18, weight=QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(header)

        self.add_language_section()
        self.add_status_section()
        self.add_control_section()
        self.add_footer_section()

        QTimer.singleShot(300, self.find_bridge)
        self.update_texts()

    def add_language_section(self):
        lang_group = QGroupBox("🌐 Język")
        layout = QHBoxLayout()
        self.language_label = QLabel()
        layout.addWidget(self.language_label)
        self.lang_switch = QComboBox()
        self.lang_switch.addItems(["PL 🇵🇱", "EN 🇬🇧"])
        self.lang_switch.setCurrentText("PL 🇵🇱")
        self.lang_switch.currentTextChanged.connect(self.switch_language)
        layout.addWidget(self.lang_switch)
        lang_group.setLayout(layout)
        self.layout.addWidget(lang_group)

    def add_status_section(self):
        status_group = QGroupBox("ℹ️ Status")
        layout = QVBoxLayout()

        self.label = QLabel()
        layout.addWidget(self.label)

        self.version_label = QLabel()
        layout.addWidget(self.version_label)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

        status_group.setLayout(layout)
        self.layout.addWidget(status_group)

    def add_control_section(self):
        control_group = QGroupBox("🛠️ Instalacja Mostka")
        layout = QVBoxLayout()
        self.check_button = QCheckBox()
        self.check_button.toggled.connect(self.toggle_confirm)
        layout.addWidget(self.check_button)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        self.start_button = QPushButton()
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.begin_installation)
        layout.addWidget(self.start_button)
        control_group.setLayout(layout)
        self.layout.addWidget(control_group)

    def add_footer_section(self):
        footer_group = QGroupBox("⚙️ Opcje")
        layout = QVBoxLayout()
        self.tips_label = QLabel()
        self.tips_label.setWordWrap(True)
        layout.addWidget(self.tips_label)
        self.update_button = QPushButton()
        self.update_button.clicked.connect(lambda: force_update_with_progress(self))
        layout.addWidget(self.update_button)
        footer_group.setLayout(layout)
        self.layout.addWidget(footer_group)

        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def switch_language(self, lang):
        self.language = "pl" if lang.startswith("PL") else "en"
        self.update_texts()

    def update_texts(self):
        t = translations.translations[self.language]
        self.setWindowTitle(t["welcome_title"])
        self.language_label.setText(t["language_label"])
        self.label.setText(t["welcome_text"])
        self.version_label.setText(t["current_version"].format(version=VERSION))
        self.status_label.setText(t["searching_bridge"])
        self.check_button.setText(t["blue_led_hint"])
        self.info_label.setText(t["bridge_connection_hint"])
        self.start_button.setText(t["start_installation"])
        self.tips_label.setText(t["troubleshooting"])
        self.update_button.setText(t["check_updates"])

    def toggle_confirm(self):
        is_checked = self.check_button.isChecked()
        self.start_button.setEnabled(is_checked)

    def find_bridge(self):
        self.progress.show()
        def worker():
            self.bridge.connect_fully_automatic(self.bridge_found_success_or_fail)
        threading.Thread(target=worker, daemon=True).start()

    def bridge_found_success_or_fail(self):
        if self.bridge.bridge_ip:
            self.progress.hide()
            t = translations.translations[self.language]
            self.status_label.setText(t["bridge_found"].format(ip=self.bridge.bridge_ip))
        else:
            self.progress.hide()
            QTimer.singleShot(0, lambda: QMessageBox.warning(
                self, "Błąd", "Nie znaleziono mostka Hue w sieci.\nSprawdź połączenie i spróbuj ponownie."
            ))

    def begin_installation(self):
        t = translations.translations[self.language]
        self.status_label.setText(t["waiting_for_button"])
        self.progress.show()
        self.bridge.request_token(self.on_token_received)

    def on_token_received(self):
        self.progress.hide()
        t = translations.translations[self.language]
        self.status_label.setText(t["token_received"])
        QTimer.singleShot(1000, self.proceed_callback)
        self.close()
