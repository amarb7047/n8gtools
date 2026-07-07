import os
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QCheckBox, QGroupBox,
                             QFormLayout, QMessageBox)
from PyQt5.QtCore import Qt, QTimer


class IosTab(QWidget):
    def __init__(self, runner, monitor):
        super().__init__()
        self.runner = runner
        self.monitor = monitor

        self.init_ui()

        # Timer to periodically refresh connected iOS devices
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.scan_ios_devices)
        self.refresh_timer.start(3000)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title Card
        title_label = QLabel("iOS AirPlay Console")
        title_label.setObjectName("tabTitle")
        layout.addWidget(title_label)

        # Main horizontal split
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(20)

        # ─── Left Panel: Settings ────────────────────────────────────────────
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # USB Detection Status
        status_group = QGroupBox("iOS USB Detection Status")
        status_group.setObjectName("settingsGroup")
        status_group_layout = QVBoxLayout(status_group)
        status_group_layout.setSpacing(10)

        self.usb_status_label = QLabel("Scanning for USB iOS devices...")
        self.usb_status_label.setObjectName("guideText")
        self.usb_status_label.setStyleSheet("font-weight: bold; color: #8E9AAF;")
        status_group_layout.addWidget(self.usb_status_label)

        self.optimize_route_check = QCheckBox(
            "Block PC Internet routing over iPhone USB (Recommended)")
        self.optimize_route_check.setChecked(True)
        status_group_layout.addWidget(self.optimize_route_check)

        left_layout.addWidget(status_group)

        # AirPlay Receiver Settings
        config_group = QGroupBox("AirPlay Receiver Settings")
        config_group.setObjectName("settingsGroup")
        config_layout = QFormLayout(config_group)
        config_layout.setSpacing(10)

        self.res_combo = QComboBox()
        self.res_combo.addItems([
            "1920x1080 (FHD - Recommended)",
            "1280x720 (HD)",
            "3840x2160 (4K UHD)",
            "2560x1440 (2K QHD)"
        ])
        self.res_combo.setMinimumHeight(35)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems([
            "60 FPS (Super Smooth)",
            "90 FPS (High Refresh)",
            "120 FPS (Pro Gaming)",
            "30 FPS (Standard)"
        ])
        self.fps_combo.setMinimumHeight(35)

        self.audio_delay_combo = QComboBox()
        self.audio_delay_combo.addItems([
            "0.25 seconds (Default)",
            "0.15 seconds (Low Latency)",
            "0.05 seconds (Ultra Low)",
            "0.00 seconds (No Delay)"
        ])
        self.audio_delay_combo.setMinimumHeight(35)

        self.sync_check = QCheckBox("Enable Audio-Video Sync (V-Sync)")
        self.sync_check.setChecked(False)

        self.audio_check = QCheckBox("Mute AirPlay Audio (Stream Video Only - Fixes Game Crashes)")
        self.audio_check.setChecked(False)

        config_layout.addRow("Mirroring Resolution:", self.res_combo)
        config_layout.addRow("Frame Rate Suggestion:", self.fps_combo)
        config_layout.addRow("Audio Buffer Latency:", self.audio_delay_combo)
        config_layout.addRow("", self.sync_check)
        config_layout.addRow("", self.audio_check)

        left_layout.addWidget(config_group)

        # Control Server
        actions_group = QGroupBox("Control Server")
        actions_group.setObjectName("settingsGroup")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(12)

        self.launch_btn = QPushButton("START AIRPLAY SERVER")
        self.launch_btn.setObjectName("btnLaunch")
        self.launch_btn.setMinimumHeight(60)
        self.launch_btn.setCursor(Qt.PointingHandCursor)
        self.launch_btn.clicked.connect(self.toggle_server)

        self.status_label = QLabel("Status: Server Offline")
        self.status_label.setObjectName("statusText")
        self.status_label.setAlignment(Qt.AlignCenter)

        actions_layout.addWidget(self.launch_btn)
        actions_layout.addWidget(self.status_label)

        left_layout.addWidget(actions_group)
        left_layout.addStretch()

        main_h_layout.addWidget(left_panel, 2)

        # ─── Right Panel: Connection Guide ───────────────────────────────────
        guide_group = QGroupBox("iOS Connection Setup Guide")
        guide_group.setObjectName("settingsGroup")
        guide_layout = QVBoxLayout(guide_group)
        guide_layout.setContentsMargins(15, 15, 15, 15)
        guide_layout.setSpacing(15)

        guide_text = (
            "<h3>Option A: USB Cable (Wired - Recommended for Low Latency)</h3>"
            "<ol>"
            "  <li>Disconnect Wi-Fi on your iOS device.</li>"
            "  <li>Go to <b>Settings &gt; Personal Hotspot</b> on iOS and turn it <b>ON</b>.</li>"
            "  <li>Connect the iOS device to your PC using a USB cable.</li>"
            "  <li>Select <b>'Trust this Computer'</b> if prompted on iOS.</li>"
            "  <li>Start the AirPlay Server in this app.</li>"
            "  <li>Open iOS Control Center, tap <b>Screen Mirroring</b>, and select <b>'N8 G Tools'</b>.</li>"
            "</ol>"
            "<hr/>"
            "<h3>Option B: Wireless (Wi-Fi)</h3>"
            "<ol>"
            "  <li>Connect both your PC and iOS device to the <b>same Wi-Fi router</b>.</li>"
            "  <li>Start the AirPlay Server in this app.</li>"
            "  <li>Open iOS Control Center, tap <b>Screen Mirroring</b>, and select <b>'N8 G Tools'</b>.</li>"
            "</ol>"
            "<hr/>"
            "<p style='color:#2ECC71; font-weight:bold;'>"
            "Tip: Mirroring will open in a high-performance floating window.<br>"
            "Use OBS window capture to stream or record the gameplay at maximum 60 FPS.<br>"
            "<span style='color:#8E9AAF; font-size:11px; font-weight:normal;'>"
            "Note: If the mirroring name still shows as 'UxPlay' on your phone, please toggle your iPhone's Wi-Fi Off and On to refresh the connection cache.</span>"
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

    # ─────────────────────────── Logic Methods ───────────────────────────────

    def scan_ios_devices(self):
        devices = self.monitor.get_ios_devices()
        iphone_devices = [
            d for d in devices
            if any(x in d["model"].lower()
                   for x in ["iphone", "ipad", "ipod", "apple mobile device"])
        ]

        if iphone_devices:
            dev_name = iphone_devices[0]["model"]
            self.usb_status_label.setText(
                f"● USB Connected: {dev_name}\n(Personal Hotspot must be active)")
            self.usb_status_label.setStyleSheet(
                "font-weight: bold; color: #2ECC71;")

            if self.optimize_route_check.isChecked():
                self.optimize_network_routing()

            is_running = self.runner.is_running("ios_airplay")
            if not is_running:
                if (self.runner.downloader.get_uxplay_path() and
                        self.runner.downloader.is_bonjour_installed()):
                    self.start_server_silent()
        else:
            self.usb_status_label.setText(
                "● USB Status: No USB iPhone Detected\n"
                "(Using Wi-Fi Mode. Connect both to same Wi-Fi)")
            self.usb_status_label.setStyleSheet(
                "font-weight: bold; color: #E74C3C;")

    def optimize_network_routing(self):
        try:
            if os.name == 'nt':
                cmd = [
                    "powershell", "-NoProfile", "-Command",
                    "Get-NetAdapter | Where-Object InterfaceDescription -like '*Apple*' "
                    "| Get-NetIPInterface -AddressFamily IPv4 "
                    "| Set-NetIPInterface -InterfaceMetric 1000"
                ]
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                subprocess.run(cmd, startupinfo=si, timeout=5)
        except Exception:
            pass

    def _parse_settings(self):
        """Parse current UI combo selections and return (res, fps, vsync, audio_delay, audio_enabled)."""
        res_text = self.res_combo.currentText()
        if "3840" in res_text:
            res = "3840x2160"
        elif "2560" in res_text:
            res = "2560x1440"
        elif "1280" in res_text:
            res = "1280x720"
        else:
            res = "1920x1080"

        fps_text = self.fps_combo.currentText()
        if "120" in fps_text:
            fps = "120"
        elif "90" in fps_text:
            fps = "90"
        elif "60" in fps_text:
            fps = "60"
        else:
            fps = "30"

        delay_map = {
            "0.25 seconds (Default)": "0.25",
            "0.15 seconds (Low Latency)": "0.15",
            "0.05 seconds (Ultra Low)": "0.05",
            "0.00 seconds (No Delay)": "0.00",
        }
        audio_delay = delay_map.get(self.audio_delay_combo.currentText(), "0.25")
        vsync = self.sync_check.isChecked()
        audio_enabled = not self.audio_check.isChecked()
        return res, fps, vsync, audio_delay, audio_enabled

    def start_server_silent(self):
        res, fps, vsync, audio_delay, audio_enabled = self._parse_settings()
        self.status_label.setText("Auto-Starting Server (USB)...")
        success, msg = self.runner.start_ios_mirror(
            fps=fps, resolution=res, vsync=vsync, audio_delay=audio_delay, audio_enabled=audio_enabled)

        if success:
            self.launch_btn.setText("STOP AIRPLAY SERVER")
            self.launch_btn.setObjectName("btnStop")
            self.launch_btn.setStyle(self.launch_btn.style())
            self.status_label.setText(
                "Status: Server Online (USB Auto). Open Control Center > Screen Mirroring > N8 G Tools")
        else:
            self.status_label.setText(f"Status: Auto-Launch failed: {msg}")

    def toggle_server(self):
        is_running = self.runner.is_running("ios_airplay")

        if is_running:
            self.runner.stop_process("ios_airplay")
            self.launch_btn.setText("START AIRPLAY SERVER")
            self.launch_btn.setObjectName("btnLaunch")
            self.launch_btn.setStyle(self.launch_btn.style())
            self.status_label.setText("Status: Server Offline")
        else:
            if not self.runner.downloader.get_uxplay_path():
                QMessageBox.warning(
                    self, "Missing Engine",
                    "iOS engine (uxplay) is not installed. Go to Setup tab first.")
                return
            if not self.runner.downloader.is_bonjour_installed():
                QMessageBox.warning(
                    self, "Missing Driver",
                    "Apple Bonjour Service is missing. Please setup drivers in Setup tab.")
                return

            res, fps, vsync, audio_delay, audio_enabled = self._parse_settings()
            self.status_label.setText("Starting Server...")
            success, msg = self.runner.start_ios_mirror(
                fps=fps, resolution=res, vsync=vsync, audio_delay=audio_delay, audio_enabled=audio_enabled)

            if success:
                self.launch_btn.setText("STOP AIRPLAY SERVER")
                self.launch_btn.setObjectName("btnStop")
                self.launch_btn.setStyle(self.launch_btn.style())
                self.status_label.setText(
                    "Status: Server Online. Open Control Center > Screen Mirroring > N8 G Tools")
            else:
                QMessageBox.critical(
                    self, "Server Error", f"Failed to start server: {msg}")
                self.status_label.setText("Status: Offline (Launch failed)")

    def closeEvent(self, event):
        self.runner.stop_process("ios_airplay")
        event.accept()
