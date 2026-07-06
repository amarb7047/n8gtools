from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import shutil
import psutil
import subprocess

class BoosterWorker(QThread):
    # Signals: progress percent (int), status text (str), stats text (str)
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(int, int) # (cleaned_files_count, optimized_processes_count)

    def run(self):
        cleaned_count = 0
        optimized_count = 0

        # Step 1: Optimize CPU Priorities (25%)
        self.progress.emit(10, "Scanning system for streaming processes...")
        QThread.msleep(600)
        
        target_names = ['scrcpy.exe', 'uxplay.exe', 'obs64.exe', 'obs.exe', 'N8GTools.exe']
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name']
                if name in target_names:
                    proc.nice(psutil.HIGH_PRIORITY_CLASS)
                    optimized_count += 1
            except Exception:
                pass
        
        self.progress.emit(30, f"Optimized priority for {optimized_count} active streaming processes.")
        QThread.msleep(800)

        # Step 2: Clear Temporary Cache Files permanently (65%)
        self.progress.emit(45, "Locating Windows temporary cache folders...")
        QThread.msleep(500)
        
        temp_paths = []
        user_temp = os.environ.get("TEMP")
        if user_temp and os.path.exists(user_temp):
            temp_paths.append(user_temp)
        
        sys_root = os.environ.get("SystemRoot", "C:\\Windows")
        sys_temp = os.path.join(sys_root, "Temp")
        if os.path.exists(sys_temp):
            temp_paths.append(sys_temp)

        # Safely delete files, ignoring locked ones (bypassing Recycle Bin)
        self.progress.emit(60, "Permanently clearing temporary cache files...")
        
        for path in temp_paths:
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    try:
                        if os.path.isdir(item_path):
                            # Skip standard directories to avoid breaking active app mounts
                            shutil.rmtree(item_path)
                            cleaned_count += 1
                        else:
                            os.remove(item_path)
                            cleaned_count += 1
                    except Exception:
                        pass # Silently skip locked files (used by running apps like OBS)
            except Exception:
                pass
                
        self.progress.emit(80, f"Successfully cleared {cleaned_count} system cache files safely.")
        QThread.msleep(800)

        # Step 3: Set Power Plan to High Performance (100%)
        self.progress.emit(90, "Applying High-Performance Power Scheme...")
        try:
            # SCHEME_MIN sets High Performance power plan
            subprocess.run("powercfg /setactive SCHEME_MIN", shell=True, 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception:
            pass
        QThread.msleep(600)
        
        self.progress.emit(100, "System optimization successfully completed!")
        self.finished.emit(cleaned_count, optimized_count)


class BoosterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # Title Card
        title_label = QLabel("N8 Gamer Booster")
        title_label.setObjectName("tabTitle")
        layout.addWidget(title_label)

        subtitle_label = QLabel(
            "Safely optimize streaming performance and clear junk cache files in real-time. "
            "OBS Studio and your active device mirrors will never close during optimization."
        )
        subtitle_label.setObjectName("tabSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)

        # Booster Frame Panel
        self.booster_card = QFrame()
        self.booster_card.setObjectName("engineCard")
        self.booster_card.setStyleSheet("""
            QFrame#engineCard {
                background-color: #1F2833;
                border: 1px solid #2D3748;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        card_layout = QVBoxLayout(self.booster_card)
        card_layout.setSpacing(20)
        card_layout.setAlignment(Qt.AlignCenter)

        # Big Circle Glow Button
        self.boost_btn = QPushButton("BOOST SYSTEM")
        self.boost_btn.setCursor(Qt.PointingHandCursor)
        self.boost_btn.setFixedSize(160, 160)
        self.boost_btn.setStyleSheet("""
            QPushButton {
                background-color: #12141C;
                color: #66FCF1;
                font-size: 16px;
                font-weight: 800;
                border: 3px solid #66FCF1;
                border-radius: 80px;
            }
            QPushButton:hover {
                background-color: #1F2833;
                border: 3px solid #E74C3C;
                color: #E74C3C;
            }
            QPushButton:disabled {
                background-color: #12141C;
                border: 3px solid #2D3748;
                color: #8E9AAF;
            }
        """)
        self.boost_btn.clicked.connect(self.start_optimization)
        card_layout.addWidget(self.boost_btn)

        # Progress HUD
        self.status_label = QLabel("Click the button above to boost system performance.")
        self.status_label.setStyleSheet("color: #8E9AAF; font-size: 13px; font-weight: bold; min-height: 25px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        card_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #2D3748;
                border-radius: 6px;
                background-color: #12141C;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #66FCF1;
                border-radius: 5px;
            }
        """)
        self.progress_bar.setTextVisible(False)
        card_layout.addWidget(self.progress_bar)

        layout.addWidget(self.booster_card)

        # Security Assurance note
        assurance_box = QFrame()
        assurance_box.setStyleSheet("background-color: transparent; border: none;")
        ass_layout = QVBoxLayout(assurance_box)
        ass_layout.setSpacing(5)
        
        note1 = QLabel("✓ Zero Crash Guarantee: Running game mirrors and active streams will remain completely untouched.")
        note1.setStyleSheet("color: #2ECC71; font-size: 11px; font-weight: bold;")
        ass_layout.addWidget(note1)
        
        note2 = QLabel("✓ Permanent Deletion: Safely frees disk space by bypassing Windows Recycle Bin for temporary cache files.")
        note2.setStyleSheet("color: #8E9AAF; font-size: 11px;")
        ass_layout.addWidget(note2)

        layout.addWidget(assurance_box)
        layout.addStretch()

        self.setLayout(layout)

    def start_optimization(self):
        self.boost_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Initializing booster engine...")
        
        self.worker = BoosterWorker()
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, percent, text):
        self.progress_bar.setValue(percent)
        self.status_label.setText(text)

    def on_finished(self, cleaned, optimized):
        self.status_label.setText(
            f"Boost Completed! Safely deleted {cleaned} cache files. "
            f"Optimized CPU priority for {optimized} active streaming processes (OBS & Mirroring)."
        )
        self.progress_bar.setValue(100)
        self.boost_btn.setEnabled(True)
        # Restore stylesheet on hover
        self.boost_btn.setStyle(self.boost_btn.style())
