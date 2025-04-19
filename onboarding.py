from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QCheckBox, QVBoxLayout, QHBoxLayout, QComboBox
from PyQt6.QtCore import QTimer
from update import force_update_with_progress
import threading
from config import VERSION
import translations


class OnboardingWindow(QDialog):
    def __init__(self, parent, proceed_callback):
        super().__init__(parent)
        self.language = getattr(parent, "language", "pl")
        self.setWindowTitle(translations.translations[self.language]["welcome_title"])
        self.resize(560, 500)

        self.master = parent
        self.bridge = parent.bridge
        self.proceed_callback = proceed_callback

        self.layout = QVBoxLayout(self)

        # === Język ===
        lang_layout = QHBoxLayout()
        self.language_label = QLabel(translations.translations[self.language]["language_label"])
        lang_layout.addWidget(self.language_label)

        self.lang_switch = QComboBox()
        self.lang_switch.addItems(["PL 🇵🇱", "EN 🇬🇧"])
        self.lang_switch.setCurrentText("PL 🇵🇱" if self.language == "pl" else "EN 🇬🇧")
        self.lang_switch.currentTextChanged.connect(self.switch_language)
        lang_layout.addWidget(self.lang_switch)
        self.layout.addLayout(lang_layout)

        self.label = QLabel()
        self.layout.addWidget(self.label)

        self.version_label = QLabel()
        self.layout.addWidget(self.version_label)

        self.status_label = QLabel()
        self.layout.addWidget(self.status_label)

        self.check_button = QCheckBox()
        self.check_button.toggled.connect(self.toggle_confirm)
        self.layout.addWidget(self.check_button)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)

        self.start_button = QPushButton()
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.begin_installation)
        self.layout.addWidget(self.start_button)

        self.tips_label = QLabel()
        self.tips_label.setWordWrap(True)
        self.layout.addWidget(self.tips_label)

        self.update_button = QPushButton()
        self.update_button.clicked.connect(lambda: force_update_with_progress(self))
        self.layout.addWidget(self.update_button)

        QTimer.singleShot(300, self.find_bridge)
        self.update_texts()

    def switch_language(self, lang):
        self.language = "pl" if lang.startswith("PL") else "en"
        self.master.language = self.language
        self.update_texts()

    def update_texts(self):
        t = translations.translations[self.language]
        self.setWindowTitle(t["welcome_title"])
        self.label.setText(t["welcome_text"])
        self.version_label.setText(t["current_version"].format(version=VERSION))
        self.status_label.setText(t["searching_bridge"])
        self.check_button.setText(t["blue_led_hint"])
        self.info_label.setText(t["bridge_connection_hint"])
        self.start_button.setText(t["start_installation"])
        self.tips_label.setText(t["troubleshooting"])
        self.update_button.setText(t["check_updates"])

    def toggle_confirm(self):
        confirmed = self.check_button.isChecked()
        self.start_button.setEnabled(confirmed)

    def find_bridge(self):
        def worker():
            self.bridge.connect_fully_automatic(self.bridge_found_success)
        threading.Thread(target=worker, daemon=True).start()

    def bridge_found_success(self):
        t = translations.translations[self.language]
        self.status_label.setText(t["bridge_found"].format(ip=self.bridge.bridge_ip))

    def begin_installation(self):
        t = translations.translations[self.language]
        self.status_label.setText(t["waiting_for_button"])
        self.bridge.request_token(self.on_token_received)

    def on_token_received(self):
        t = translations.translations[self.language]
        self.status_label.setText(t["token_received"])
        QTimer.singleShot(1000, self.proceed_callback)