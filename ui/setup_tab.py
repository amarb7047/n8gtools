import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from core.downloader import EngineDownloader

class SetupWorker(QThread):
    # Signals: percent (int), status text (str), engine name (str), success (bool), error_msg (str)
    progress = pyqtSignal(int, str, str)
    finished = pyqtSignal(str, bool, str)

    def __init__(self, downloader, engine_type, action_type="install"):
        super().__init__()
        self.downloader = downloader
        self.engine_type = engine_type
        self.action_type = action_type

    def run(self):
        try:
            if self.action_type == "install":
                if self.engine_type == "scrcpy":
                    self.downloader.setup_scrcpy(self.progress_callback)
                elif self.engine_type == "uxplay":
                    self.downloader.setup_uxplay(self.progress_callback)
                elif self.engine_type == "bonjour":
                    self.downloader.setup_bonjour(self.progress_callback)
                elif self.engine_type == "usb_driver":
                    self.downloader.setup_usb_driver(self.progress_callback)
            elif self.action_type == "uninstall":
                if self.engine_type == "scrcpy":
                    self.downloader.uninstall_scrcpy(self.progress_callback)
                elif self.engine_type == "uxplay":
                    self.downloader.uninstall_uxplay(self.progress_callback)
                elif self.engine_type == "bonjour":
                    self.downloader.uninstall_bonjour(self.progress_callback)
                elif self.engine_type == "usb_driver":
                    self.downloader.uninstall_usb_driver(self.progress_callback)
            self.finished.emit(self.engine_type, True, "")
        except Exception as e:
            self.finished.emit(self.engine_type, False, str(e))

    def progress_callback(self, percent, text=""):
        self.progress.emit(percent, text, self.engine_type)


class SetupTab(QWidget):
    engines_updated = pyqtSignal()

    def __init__(self, downloader):
        super().__init__()
        self.downloader = downloader
        self.init_ui()
        self.refresh_status()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title Card
        title_label = QLabel("Engine & Driver Setup Center")
        title_label.setObjectName("tabTitle")
        layout.addWidget(title_label)

        subtitle_label = QLabel("To mirror your devices, HeroRec needs setup of mirroring engines. Setup is completely automated.")
        subtitle_label.setObjectName("tabSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)

        # Card Container
        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(15)

        # 1. Android Engine Card
        self.scrcpy_card = self.create_engine_card(
            "Android Mirror Engine (scrcpy v4.0)",
            "Enables high-performance Android mirroring (up to 120 FPS) over USB & Wi-Fi.",
            "scrcpy"
        )
        cards_layout.addWidget(self.scrcpy_card)

        # 2. iOS Engine Card
        self.uxplay_card = self.create_engine_card(
            "iOS Mirror Engine (uxplay)",
            "Enables iOS screen mirroring (up to 60 FPS) and audio streaming.",
            "uxplay"
        )
        cards_layout.addWidget(self.uxplay_card)

        # 3. Bonjour Driver Card
        self.bonjour_card = self.create_engine_card(
            "Apple Bonjour Service (Required for iOS)",
            "Handles device discovery. Required for wireless iOS screen sharing.",
            "bonjour"
        )
        cards_layout.addWidget(self.bonjour_card)

        # 4. Universal Android USB Driver Card
        self.usb_driver_card = self.create_engine_card(
            "Universal Google Android USB Driver (ADB)",
            "Required if your PC does not recognize your connected Android phone over a USB cable.",
            "usb_driver"
        )
        cards_layout.addWidget(self.usb_driver_card)

        layout.addLayout(cards_layout)
        layout.addStretch()

        self.setLayout(layout)

    def create_engine_card(self, title, desc, engine_type):
        card = QWidget()
        card.setObjectName("engineCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(10)

        # Header: Name + Status badge
        header_layout = QHBoxLayout()
        name_label = QLabel(title)
        name_label.setObjectName("engineTitle")
        
        status_label = QLabel("Checking...")
        status_label.setObjectName(f"status_{engine_type}")
        status_label.setFixedWidth(100)
        status_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        header_layout.addWidget(status_label)
        card_layout.addLayout(header_layout)

        # Description
        desc_label = QLabel(desc)
        desc_label.setObjectName("engineDesc")
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)

        # Progress Layout
        progress_layout = QHBoxLayout()
        progress_bar = QProgressBar()
        progress_bar.setObjectName(f"progress_{engine_type}")
        progress_bar.setVisible(False)
        progress_bar.setTextVisible(True)
        
        progress_text = QLabel("")
        progress_text.setObjectName(f"text_{engine_type}")
        progress_text.setVisible(False)

        setup_btn = QPushButton("Setup")
        setup_btn.setObjectName(f"btn_{engine_type}")
        setup_btn.setCursor(Qt.PointingHandCursor)
        setup_btn.clicked.connect(lambda: self.start_setup(engine_type))

        uninstall_btn = QPushButton("Uninstall")
        uninstall_btn.setObjectName("btnStop") # Red/Rose theme button
        uninstall_btn.setCursor(Qt.PointingHandCursor)
        uninstall_btn.clicked.connect(lambda: self.start_uninstall(engine_type))
        uninstall_btn.setVisible(False) # Hidden by default, shown if installed

        progress_layout.addWidget(progress_bar, 3)
        progress_layout.addWidget(progress_text, 2)
        progress_layout.addWidget(setup_btn, 1)
        progress_layout.addWidget(uninstall_btn, 1)
        card_layout.addLayout(progress_layout)

        # Store references
        setattr(self, f"label_status_{engine_type}", status_label)
        setattr(self, f"bar_{engine_type}", progress_bar)
        setattr(self, f"txt_{engine_type}", progress_text)
        setattr(self, f"btn_action_{engine_type}", setup_btn)
        setattr(self, f"btn_uninstall_{engine_type}", uninstall_btn)

        return card

    def refresh_status(self):
        """Checks if files are installed and updates badges."""
        # Check scrcpy
        if self.downloader.get_scrcpy_path():
            self.update_badge("scrcpy", True)
        else:
            self.update_badge("scrcpy", False)

        # Check uxplay
        if self.downloader.get_uxplay_path():
            self.update_badge("uxplay", True)
        else:
            self.update_badge("uxplay", False)

        # Check Bonjour
        if self.downloader.is_bonjour_installed():
            self.update_badge("bonjour", True)
        else:
            self.update_badge("bonjour", False)

        # Check USB Driver
        if self.downloader.get_usb_driver_path():
            self.update_badge("usb_driver", True)
        else:
            self.update_badge("usb_driver", False)

        self.engines_updated.emit()

    def update_badge(self, engine_type, installed):
        badge = getattr(self, f"label_status_{engine_type}")
        btn = getattr(self, f"btn_action_{engine_type}")
        un_btn = getattr(self, f"btn_uninstall_{engine_type}")
        
        if installed:
            badge.setText("INSTALLED")
            badge.setStyleSheet("background-color: #2ECC71; color: white; border-radius: 5px; font-weight: bold; font-size: 11px; padding: 2px;")
            btn.setText("Reinstall")
            btn.setObjectName("btnReinstall")
            un_btn.setVisible(True)
        else:
            badge.setText("MISSING")
            badge.setStyleSheet("background-color: #E74C3C; color: white; border-radius: 5px; font-weight: bold; font-size: 11px; padding: 2px;")
            btn.setText("Setup")
            btn.setObjectName("btnSetup")
            un_btn.setVisible(False)
        btn.setStyle(btn.style()) # Force style refresh
        un_btn.setStyle(un_btn.style())

    def start_setup(self, engine_type):
        btn = getattr(self, f"btn_action_{engine_type}")
        un_btn = getattr(self, f"btn_uninstall_{engine_type}")
        pbar = getattr(self, f"bar_{engine_type}")
        ptxt = getattr(self, f"txt_{engine_type}")
        
        btn.setEnabled(False)
        un_btn.setEnabled(False)
        pbar.setValue(0)
        pbar.setVisible(True)
        ptxt.setText("Starting...")
        ptxt.setVisible(True)

        worker = SetupWorker(self.downloader, engine_type, action_type="install")
        worker.progress.connect(self.on_progress)
        worker.finished.connect(self.on_finished)
        
        # Save worker reference to avoid garbage collection
        setattr(self, f"worker_{engine_type}", worker)
        worker.start()

    def start_uninstall(self, engine_type):
        btn = getattr(self, f"btn_action_{engine_type}")
        un_btn = getattr(self, f"btn_uninstall_{engine_type}")
        pbar = getattr(self, f"bar_{engine_type}")
        ptxt = getattr(self, f"txt_{engine_type}")
        
        reply = QMessageBox.question(self, "Uninstall Confirmation", 
                                     f"Are you sure you want to uninstall {engine_type.upper()} and delete its drivers/files?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
            
        btn.setEnabled(False)
        un_btn.setEnabled(False)
        pbar.setValue(0)
        pbar.setVisible(True)
        ptxt.setText("Uninstalling...")
        ptxt.setVisible(True)

        worker = SetupWorker(self.downloader, engine_type, action_type="uninstall")
        worker.progress.connect(self.on_progress)
        worker.finished.connect(self.on_uninstall_finished)
        
        setattr(self, f"worker_un_{engine_type}", worker)
        worker.start()

    def on_progress(self, percent, text, engine_type):
        pbar = getattr(self, f"bar_{engine_type}")
        ptxt = getattr(self, f"txt_{engine_type}")
        pbar.setValue(percent)
        ptxt.setText(text)

    def on_finished(self, engine_type, success, error_msg):
        btn = getattr(self, f"btn_action_{engine_type}")
        un_btn = getattr(self, f"btn_uninstall_{engine_type}")
        pbar = getattr(self, f"bar_{engine_type}")
        ptxt = getattr(self, f"txt_{engine_type}")
        
        btn.setEnabled(True)
        un_btn.setEnabled(True)
        pbar.setVisible(False)
        ptxt.setVisible(False)
        
        # Clear worker reference
        if hasattr(self, f"worker_{engine_type}"):
            delattr(self, f"worker_{engine_type}")

        if success:
            QMessageBox.information(self, "Success", f"{engine_type.upper()} setup completed successfully!")
        else:
            QMessageBox.critical(self, "Setup Error", f"Failed to setup {engine_type.upper()}: {error_msg}")
            
        self.refresh_status()

    def on_uninstall_finished(self, engine_type, success, error_msg):
        btn = getattr(self, f"btn_action_{engine_type}")
        un_btn = getattr(self, f"btn_uninstall_{engine_type}")
        pbar = getattr(self, f"bar_{engine_type}")
        ptxt = getattr(self, f"txt_{engine_type}")
        
        btn.setEnabled(True)
        un_btn.setEnabled(True)
        pbar.setVisible(False)
        ptxt.setVisible(False)
        
        # Clear worker reference
        if hasattr(self, f"worker_un_{engine_type}"):
            delattr(self, f"worker_un_{engine_type}")

        if success:
            QMessageBox.information(self, "Success", f"{engine_type.upper()} uninstalled successfully!")
        else:
            QMessageBox.critical(self, "Uninstall Error", f"Failed to uninstall {engine_type.upper()}: {error_msg}")
            
        self.refresh_status()
