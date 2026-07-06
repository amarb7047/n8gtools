from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class MaintenanceTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignCenter)

        # Main alert box
        card = QFrame()
        card.setObjectName("engineCard")
        card.setFixedSize(500, 320)
        card.setStyleSheet("""
            QFrame#engineCard {
                background-color: #1F2833;
                border: 2px solid #E74C3C;
                border-radius: 16px;
                padding: 40px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setAlignment(Qt.AlignCenter)

        # Huge warning sign
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(icon_label)

        # Text warnings
        title = QLabel("System Maintenance Underway")
        title.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        self.desc_label = QLabel(
            "N8 G Tools is temporarily undergoing system maintenance.\n"
            "Mirroring consoles and telemetry diagnostics are currently offline.\n"
            "Please check back shortly."
        )
        self.desc_label.setStyleSheet("color: #8E9AAF; font-size: 12px; line-height: 1.6;")
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)
        card_layout.addWidget(self.desc_label)

        # Exit Button
        exit_btn = QPushButton("Exit Application")
        exit_btn.setFixedSize(160, 40)
        exit_btn.setCursor(Qt.PointingHandCursor)
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        exit_btn.clicked.connect(self.exit_app)
        card_layout.addWidget(exit_btn)

        layout.addWidget(card)
        self.setLayout(layout)

    def exit_app(self):
        # Find window containing widget and close it
        win = self.window()
        if win:
            win.close()

    def set_message(self, text):
        if text:
            self.desc_label.setText(text)
