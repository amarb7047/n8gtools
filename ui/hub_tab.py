from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QFont, QPixmap
import os

class HubTab(QWidget):
    def __init__(self, base_dir=None):
        super().__init__()
        self.base_dir = base_dir
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title Card
        title_label = QLabel("N8 Gamer Hub")
        title_label.setObjectName("tabTitle")
        layout.addWidget(title_label)

        # Content Card
        content_card = QFrame()
        content_card.setObjectName("engineCard")
        content_card.setStyleSheet("""
            QFrame#engineCard {
                background-color: #1F2833;
                border: 1px solid #2D3748;
                border-radius: 12px;
                padding: 25px;
            }
        """)
        
        card_layout = QHBoxLayout(content_card)
        card_layout.setSpacing(30)

        # Left Column: Big Channel Logo
        logo_label = QLabel()
        logo_label.setFixedSize(140, 140)
        logo_label.setStyleSheet("border-radius: 70px; background-color: #12141C; border: 2px solid #66FCF1;")
        logo_label.setAlignment(Qt.AlignCenter)
        
        logo_path = os.path.join(self.base_dir, "N8Gamer.jpeg") if self.base_dir else "N8Gamer.jpeg"
        if not os.path.exists(logo_path):
            logo_path = os.path.join(self.base_dir, "logo.png") if self.base_dir else "logo.png"
            
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("N8")
            logo_label.setFont(QFont("Segoe UI", 32, QFont.Bold))
            logo_label.setStyleSheet("color: #66FCF1; border-radius: 70px; background-color: #12141C; border: 2px solid #66FCF1;")
        
        card_layout.addWidget(logo_label)

        # Right Column: Creator Info & Subscribe Button
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)

        channel_title = QLabel("N8 Gamer")
        channel_title.setStyleSheet("color: #66FCF1; font-size: 28px; font-weight: 800; letter-spacing: 1px;")
        info_layout.addWidget(channel_title)

        owner_label = QLabel("Owner: Amarendraa Biswas")
        owner_label.setStyleSheet("color: #E2E8F0; font-size: 14px; font-weight: bold;")
        info_layout.addWidget(owner_label)

        desc_label = QLabel(
            "Welcome to the official utility suite of N8 Gamer! This application was custom-built "
            "to bring you lag-free screen mirroring and gameplay tools. "
            "Support the developer by subscribing to our official YouTube channel for the latest updates, tutorials, and streams!"
        )
        desc_label.setStyleSheet("color: #8E9AAF; font-size: 13px; line-height: 1.6;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        info_layout.addSpacing(10)

        # Buttons side-by-side
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        # Subscribe Button
        sub_btn = QPushButton("  SUBSCRIBE ON YOUTUBE")
        sub_btn.setMinimumHeight(45)
        sub_btn.setCursor(Qt.PointingHandCursor)
        sub_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF0000;
                color: white;
                font-size: 12px;
                font-weight: 800;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #CC0000;
            }
        """)
        sub_btn.clicked.connect(self.open_channel)
        buttons_layout.addWidget(sub_btn)

        # Official Website Button
        web_btn = QPushButton("  OFFICIAL WEBSITE")
        web_btn.setMinimumHeight(45)
        web_btn.setCursor(Qt.PointingHandCursor)
        web_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                font-size: 12px;
                font-weight: 800;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4338CA;
            }
        """)
        web_btn.clicked.connect(self.open_website)
        buttons_layout.addWidget(web_btn)

        info_layout.addLayout(buttons_layout)

        card_layout.addLayout(info_layout, 1)

        layout.addWidget(content_card)

        # Version & Credits Box
        credits_box = QFrame()
        credits_box.setStyleSheet("background-color: transparent; border: none;")
        credits_layout = QVBoxLayout(credits_box)
        credits_layout.setSpacing(5)
        
        ver_label = QLabel("Build Version: 1.0.0 (Stable Edition)")
        ver_label.setStyleSheet("color: #8E9AAF; font-size: 11px;")
        credits_layout.addWidget(ver_label)
        
        dev_label = QLabel("Developed for the N8 Gamer community. All rights reserved.")
        dev_label.setStyleSheet("color: #8E9AAF; font-size: 11px;")
        credits_layout.addWidget(dev_label)
        
        layout.addWidget(credits_box)
        layout.addStretch()

        self.setLayout(layout)

    def open_channel(self):
        url = QUrl("https://youtube.com/@n8gamer70?si=10-ayl3CYBu4LF0a")
        QDesktopServices.openUrl(url)

    def open_website(self):
        url = QUrl("https://n8-g-tools.web.app")
        QDesktopServices.openUrl(url)
