import os
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QCheckBox, QGroupBox, 
                             QFormLayout, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, QTimer

class AndroidTab(QWidget):
    def __init__(self, runner, monitor):
        super().__init__()
        self.runner = runner
        self.monitor = monitor
        
        self.init_ui()
        
        # Timer to periodically refresh connected devices
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.scan_devices_quiet)
        self.refresh_timer.start(3000) # Check every 3 seconds

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title Card
        title_label = QLabel("Android Mirroring Console")
        title_label.setObjectName("tabTitle")
        layout.addWidget(title_label)

        # Main horizontal layout dividing settings and guide
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(20)

        # --- Settings Panel (Left) ---
        settings_panel = QWidget()
        settings_layout = QVBoxLayout(settings_panel)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(15)

        # Device connection group
        conn_group = QGroupBox("Device Connection")
        conn_group.setObjectName("settingsGroup")
        conn_layout = QFormLayout(conn_group)
        conn_layout.setSpacing(10)

        self.conn_type_combo = QComboBox()
        self.conn_type_combo.addItems(["USB (Low Latency)", "Wi-Fi (Wireless)"])
        self.conn_type_combo.currentIndexChanged.connect(self.toggle_connection_fields)
        self.conn_type_combo.setMinimumHeight(35)

        self.wifi_ip = QLineEdit()
        self.wifi_ip.setPlaceholderText("192.168.1.100")
        self.wifi_ip.setMinimumHeight(35)
        self.wifi_ip_label = QLabel("Device IP:")
        
        self.wifi_connect_btn = QPushButton("Connect Wi-Fi")
        self.wifi_connect_btn.setObjectName("btnAction")
        self.wifi_connect_btn.setCursor(Qt.PointingHandCursor)
        self.wifi_connect_btn.clicked.connect(self.connect_wifi)

        self.device_combo = QComboBox()
        self.device_combo.setPlaceholderText("No devices detected")
        self.device_combo.setMinimumHeight(35)
        
        scan_btn = QPushButton("Scan Devices")
        scan_btn.setObjectName("btnAction")
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.clicked.connect(self.scan_devices)
        
        conn_layout.addRow("Connection Method:", self.conn_type_combo)
        conn_layout.addRow(self.wifi_ip_label, self.wifi_ip)
        conn_layout.addRow("", self.wifi_connect_btn)
        conn_layout.addRow("Select Device:", self.device_combo)
        conn_layout.addRow("", scan_btn)

        # Hidden by default since USB is selected
        self.toggle_connection_fields(0)
        settings_layout.addWidget(conn_group)

        # Performance group
        perf_group = QGroupBox("Streaming Performance Settings")
        perf_group.setObjectName("settingsGroup")
        perf_layout = QFormLayout(perf_group)
        perf_layout.setSpacing(10)

        self.res_combo = QComboBox()
        self.res_combo.addItems(["Native (Original)", "3840 (4K UHD)", "2560 (2K QHD)", "1920 (1080p Limit)", "1280 (720p Limit)"])
        self.res_combo.setCurrentIndex(3) # Default to 1920
        self.res_combo.setMinimumHeight(35)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60 FPS (Super Smooth)", "90 FPS (High Refresh)", "120 FPS (Pro Gaming)", "30 FPS (Standard)"])
        self.fps_combo.setMinimumHeight(35)

        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["16 Mbps (High Quality)", "32 Mbps (4K Ultra)", "24 Mbps (Ultra Clean)", "8 Mbps (Standard)", "4 Mbps (Low Bandwidth)"])
        self.bitrate_combo.setMinimumHeight(35)

        perf_layout.addRow("Max Resolution Width:", self.res_combo)
        perf_layout.addRow("Frame Rate Limit:", self.fps_combo)
        perf_layout.addRow("Streaming Bitrate:", self.bitrate_combo)

        settings_layout.addWidget(perf_group)

        # Feature Configurations Group
        options_group = QGroupBox("Feature Configurations")
        options_group.setObjectName("settingsGroup")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(12)

        self.audio_check = QCheckBox("Forward Audio to PC (Android 11+)")
        self.audio_check.setChecked(True)
        
        self.awake_check = QCheckBox("Keep Device Screen Awake")
        self.awake_check.setChecked(True)

        self.screen_off_check = QCheckBox("Turn off device screen (Saves battery)")
        self.screen_off_check.setChecked(False)

        options_layout.addWidget(self.audio_check)
        options_layout.addWidget(self.awake_check)
        options_layout.addWidget(self.screen_off_check)

        settings_layout.addWidget(options_group)

        # Action Group
        launch_group = QGroupBox("Actions")
        launch_group.setObjectName("settingsGroup")
        launch_layout = QVBoxLayout(launch_group)
        launch_layout.setSpacing(10)

        self.launch_btn = QPushButton("LAUNCH MIRROR")
        self.launch_btn.setObjectName("btnLaunch")
        self.launch_btn.setMinimumHeight(60)
        self.launch_btn.setCursor(Qt.PointingHandCursor)
        self.launch_btn.clicked.connect(self.toggle_mirror)

        self.status_label = QLabel("Status: Ready to connect")
        self.status_label.setObjectName("statusText")
        self.status_label.setAlignment(Qt.AlignCenter)

        launch_layout.addWidget(self.launch_btn)
        launch_layout.addWidget(self.status_label)

        settings_layout.addWidget(launch_group)
        settings_layout.addStretch()

        main_h_layout.addWidget(settings_panel, 2)

        # --- Connection Setup Guide (Right) ---
        guide_group = QGroupBox("Android Connection Setup Guide")
        guide_group.setObjectName("settingsGroup")
        guide_layout = QVBoxLayout(guide_group)
        guide_layout.setContentsMargins(15, 15, 15, 15)
        guide_layout.setSpacing(15)

        guide_text = (
            "<h3>Option A: USB Cable (Wired - Recommended for Low Latency)</h3>"
            "<ol>"
            "  <li>Enable <b>Developer Options</b> and <b>USB Debugging</b> on your Android phone.</li>"
            "  <li>Connect the phone to your PC via a USB cable.</li>"
            "  <li>Select <b>'Always allow from this computer'</b> when prompted on your phone.</li>"
            "  <li>Select the device from the list above and click <b>LAUNCH MIRROR</b>.</li>"
            "</ol>"
            "<hr/>"
            "<h3>Option B: Wireless (Wi-Fi)</h3>"
            "<ol>"
            "  <li>Connect both your phone and PC to the <b>same Wi-Fi network</b>.</li>"
            "  <li>Enable <b>Wireless Debugging</b> on your phone.</li>"
            "  <li>Note the IP address and Port shown on your phone's Wireless Debugging screen.</li>"
            "  <li>Input the IP Address and Port above and click <b>Connect Wi-Fi</b>.</li>"
            "  <li>Select the connected wireless device and click <b>LAUNCH MIRROR</b>.</li>"
            "</ol>"
            "<hr/>"
            "<p style='color:#2ECC71; font-weight:bold;'>"
            "Tip: Mirroring will open in a high-performance floating window.<br>"
            "Use OBS window capture to stream or record the gameplay at maximum 120 FPS."
            "</p>"
        )

        guide_label = QLabel(guide_text)
        guide_label.setTextFormat(Qt.RichText)
        guide_label.setWordWrap(True)
        guide_label.setObjectName("guideText")
        guide_layout.addWidget(guide_label)
        guide_layout.addStretch()

        main_h_layout.addWidget(guide_group, 3)

        layout.addLayout(main_h_layout)
        self.setLayout(layout)

    def toggle_connection_fields(self, index):
        is_wifi = index == 1
        self.wifi_ip.setVisible(is_wifi)
        self.wifi_ip_label.setVisible(is_wifi)
        self.wifi_connect_btn.setVisible(is_wifi)

    def scan_devices(self):
        self.status_label.setText("Scanning USB devices...")
        self.scan_devices_quiet()
        self.status_label.setText("Status: Ready to connect")

    def scan_devices_quiet(self):
        devices = self.monitor.get_android_devices()
        current_selection = self.device_combo.currentText()
        self.device_combo.clear()
        
        for dev in devices:
            display_name = dev["model"]
            self.device_combo.addItem(display_name, dev["serial"])
            
        index = self.device_combo.findText(current_selection)
        if index >= 0:
            self.device_combo.setCurrentIndex(index)

    def connect_wifi(self):
        ip = self.wifi_ip.text().strip()
        if not ip:
            QMessageBox.warning(self, "Wi-Fi Connection", "Please input a valid IP address first.")
            return
        
        self.status_label.setText("Connecting over Wi-Fi...")
        success, msg = self.runner.connect_wifi_device(ip)
        if success:
            QMessageBox.information(self, "Wi-Fi Connected", f"Successfully connected to {ip}")
            self.scan_devices_quiet()
        else:
            QMessageBox.critical(self, "Connection Failed", f"Failed: {msg}\n\nMake sure Wireless Debugging is enabled.")
        self.status_label.setText("Status: Ready to connect")

    def toggle_mirror(self):
        is_running = any(self.runner.is_running(k) for k in self.runner.active_processes if k.startswith("android"))
        
        if is_running:
            self.stop_mirroring()
        else:
            if not self.runner.downloader.get_scrcpy_path():
                QMessageBox.warning(self, "Missing Engine", "Android engine is missing. Go to Setup tab to install it first.")
                return

            serial = self.device_combo.currentData()
            if not serial:
                QMessageBox.warning(self, "No Device", "Please connect and select a device from the list.")
                return

            res_map = {"Native (Original)": "Native", "3840 (4K UHD)": "3840", "2560 (2K QHD)": "2560", "1920 (1080p Limit)": "1920", "1280 (720p Limit)": "1280"}
            res = res_map.get(self.res_combo.currentText(), "Native")

            fps_map = {
                "60 FPS (Super Smooth)": "60",
                "90 FPS (High Refresh)": "90",
                "120 FPS (Pro Gaming)": "120",
                "30 FPS (Standard)": "30"
            }
            fps = fps_map.get(self.fps_combo.currentText(), "60")

            bit_map = {"16 Mbps (High Quality)": "16M", "32 Mbps (4K Ultra)": "32M", "24 Mbps (Ultra Clean)": "24M", "8 Mbps (Standard)": "8M", "4 Mbps (Low Bandwidth)": "4M"}
            bitrate = bit_map.get(self.bitrate_combo.currentText(), "8M")

            audio = self.audio_check.isChecked()
            awake = self.awake_check.isChecked()
            screen_off = self.screen_off_check.isChecked()

            self.status_label.setText("Launching Mirroring Session...")
            success, msg = self.runner.start_android_mirror(
                serial=serial, resolution=res, fps=fps, bitrate=bitrate,
                audio_enabled=audio, record_path=None, stay_awake=awake,
                turn_screen_off=screen_off
            )

            if success:
                self.launch_btn.setText("STOP MIRRORING")
                self.launch_btn.setObjectName("btnStop")
                self.launch_btn.setStyle(self.launch_btn.style())
                self.status_label.setText("Status: Mirroring Active")
            else:
                QMessageBox.critical(self, "Mirroring Error", f"Failed to start mirroring: {msg}")
                self.status_label.setText("Status: Launch failed")

    def stop_mirroring(self):
        serial = self.device_combo.currentData()
        process_key = f"android_{serial or 'default'}"
        self.runner.stop_process(process_key)
        
        self.launch_btn.setText("LAUNCH MIRROR")
        self.launch_btn.setObjectName("btnLaunch")
        self.launch_btn.setStyle(self.launch_btn.style())
        self.status_label.setText("Status: Mirroring stopped")

    def closeEvent(self, event):
        self.stop_mirroring()
        event.accept()
