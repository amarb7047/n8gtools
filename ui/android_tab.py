import os
import time
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QCheckBox, QFileDialog, 
                             QGroupBox, QFormLayout, QLineEdit, QMessageBox,
                             QStackedWidget, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QWindow

class AndroidTab(QWidget):
    def __init__(self, runner, monitor):
        super().__init__()
        self.runner = runner
        self.monitor = monitor
        
        # Timer to poll and embed scrcpy window
        self.embed_timer = QTimer()
        self.embed_timer.timeout.connect(self.check_and_embed_android)
        self.embed_ticks = 0
        
        # Timer to track recording seconds
        self.rec_seconds = 0
        self.is_recording = False
        self.rec_timer = QTimer()
        self.rec_timer.timeout.connect(self.update_recording_timer)
        
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

        # Main horizontal layout dividing settings and status
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

        self.device_combo = QComboBox()
        self.device_combo.setPlaceholderText("No devices detected")
        self.device_combo.setMinimumHeight(35)
        
        scan_btn = QPushButton("Scan Devices")
        scan_btn.setObjectName("btnAction")
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.clicked.connect(self.scan_devices)

        # Wi-Fi fields
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
        self.wifi_connect_btn.clicked.connect(self.connect_wifi)
        
        # Add to form
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
        self.res_combo.setMinimumHeight(35)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60 FPS (Super Smooth)", "90 FPS (High Refresh)", "120 FPS (Pro Gaming)", "30 FPS (Standard)"])
        self.fps_combo.setMinimumHeight(35)

        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["16 Mbps (High Quality)", "32 Mbps (4K Ultra)", "24 Mbps (Ultra Clean)", "8 Mbps (Standard)", "4 Mbps (Low Bandwidth)"])
        self.bitrate_combo.setMinimumHeight(35)

        perf_layout.addRow("Max Resolution Width:", self.res_combo)
        perf_layout.addRow("Frame Rate limit:", self.fps_combo)
        perf_layout.addRow("Streaming Bitrate:", self.bitrate_combo)

        settings_layout.addWidget(perf_group)
        main_h_layout.addWidget(settings_panel, 2) # Settings panel takes 2/5 width

        # --- Options & Launch Panel Stack (Right) ---
        self.right_stack = QStackedWidget()
        
        # 1. Controls Widget (Settings + Launch button)
        self.controls_widget = QWidget()
        controls_layout = QVBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(15)
        
        # Additional options group
        options_group = QGroupBox("Feature Configurations")
        options_group.setObjectName("settingsGroup")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(12)

        self.audio_check = QCheckBox("Forward Audio to PC (Android 11+)")
        self.audio_check.setChecked(True)
        self.audio_check.stateChanged.connect(self.audio_checkbox_toggled)
        
        self.awake_check = QCheckBox("Keep Device Screen Awake")
        self.awake_check.setChecked(True)

        self.screen_off_check = QCheckBox("Turn off device screen (Saves battery)")
        self.screen_off_check.setChecked(False)

        # Recording Path Configs
        path_title = QLabel("Recordings Save Directory:")
        path_title.setStyleSheet("font-weight: bold; color: #8E9AAF; margin-top: 5px;")
        
        save_path_layout = QHBoxLayout()
        self.save_dir_input = QLineEdit()
        self.save_dir_input.setMinimumHeight(35)
        default_videos_dir = os.path.join(os.path.expanduser("~"), "Videos", "N8GTools")
        os.makedirs(default_videos_dir, exist_ok=True)
        self.save_dir_input.setText(default_videos_dir)
        self.save_dir_input.setReadOnly(True)
        
        self.save_dir_browse_btn = QPushButton("Browse")
        self.save_dir_browse_btn.setObjectName("btnSecondary")
        self.save_dir_browse_btn.setMinimumHeight(35)
        self.save_dir_browse_btn.clicked.connect(self.browse_save_dir)
        
        save_path_layout.addWidget(self.save_dir_input, 4)
        save_path_layout.addWidget(self.save_dir_browse_btn, 1)

        options_layout.addWidget(self.audio_check)
        options_layout.addWidget(self.awake_check)
        options_layout.addWidget(self.screen_off_check)
        options_layout.addWidget(path_title)
        options_layout.addLayout(save_path_layout)

        controls_layout.addWidget(options_group)

        # Launch Card
        launch_group = QGroupBox("Actions")
        launch_group.setObjectName("settingsGroup")
        launch_layout = QVBoxLayout(launch_group)
        launch_layout.setSpacing(10)
        
        self.launch_btn = QPushButton("LAUNCH MIRROR")
        self.launch_btn.setObjectName("btnLaunch")
        self.launch_btn.setMinimumHeight(60)
        self.launch_btn.setCursor(Qt.PointingHandCursor)
        self.launch_btn.clicked.connect(self.toggle_mirror)
        launch_layout.addWidget(self.launch_btn)

        self.status_label = QLabel("Status: Ready to connect")
        self.status_label.setObjectName("statusText")
        self.status_label.setAlignment(Qt.AlignCenter)
        launch_layout.addWidget(self.status_label)

        controls_layout.addWidget(launch_group)
        controls_layout.addStretch()
        
        # 2. Video Widget (Embedded video screen + Sidebar Toolbar)
        self.video_widget = QWidget()
        video_layout = QHBoxLayout(self.video_widget)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(10)
        
        # Left Part: Video frame container
        display_panel = QWidget()
        display_layout = QVBoxLayout(display_panel)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(10)

        self.video_container = QFrame()
        self.video_container.setFrameShape(QFrame.StyledPanel)
        self.video_container.setObjectName("settingsGroup")
        self.video_container.setStyleSheet("background-color: #0F111A; border: 1px solid #1F2833; border-radius: 8px;")
        
        # Layout inside container to hold embedded window
        container_layout = QVBoxLayout(self.video_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Default placeholder text inside container
        self.video_placeholder = QLabel("Initializing Video Stream...")
        self.video_placeholder.setAlignment(Qt.AlignCenter)
        self.video_placeholder.setStyleSheet("color: #8E9AAF; font-size: 14px; font-weight: bold;")
        container_layout.addWidget(self.video_placeholder)
        
        display_layout.addWidget(self.video_container, 1)
        video_layout.addWidget(display_panel, 8)

        # Right Part: Vertical Gaming Toolbar
        self.toolbar_card = QFrame()
        self.toolbar_card.setObjectName("settingsGroup")
        self.toolbar_card.setFixedWidth(130)
        self.toolbar_card.setStyleSheet("""
            QFrame {
                background-color: #1F2833;
                border: 1px solid #2D3748;
                border-radius: 8px;
            }
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                height: 40px;
                border: none;
                border-radius: 6px;
                text-align: center;
            }
            QLabel#recTimer {
                color: #8E9AAF;
                font-size: 10px;
                font-weight: 800;
                background-color: #12141C;
                border: 1px solid #2D3748;
                border-radius: 4px;
                padding: 6px;
                text-align: center;
            }
        """)
        toolbar_layout = QVBoxLayout(self.toolbar_card)
        toolbar_layout.setContentsMargins(8, 12, 8, 12)
        toolbar_layout.setSpacing(10)

        # Recording Timer HUD
        self.rec_status_label = QLabel("● REC 00:00:00")
        self.rec_status_label.setObjectName("recTimer")
        self.rec_status_label.setAlignment(Qt.AlignCenter)
        toolbar_layout.addWidget(self.rec_status_label)

        # Record Trigger Button
        self.rec_toggle_btn = QPushButton("🔴 Record")
        self.rec_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.rec_toggle_btn.setStyleSheet("background-color: #E74C3C; color: white;")
        self.rec_toggle_btn.clicked.connect(self.toggle_recording_action)
        toolbar_layout.addWidget(self.rec_toggle_btn)

        # Screenshot Button
        self.screenshot_btn = QPushButton("📷 Screenshot")
        self.screenshot_btn.setCursor(Qt.PointingHandCursor)
        self.screenshot_btn.setStyleSheet("background-color: #3498DB; color: white;")
        self.screenshot_btn.clicked.connect(self.take_screenshot_action)
        toolbar_layout.addWidget(self.screenshot_btn)

        # Mute Audio Button
        self.mute_audio_btn = QPushButton("🔊 Audio: ON")
        self.mute_audio_btn.setCursor(Qt.PointingHandCursor)
        self.mute_audio_btn.setStyleSheet("background-color: #2D3748; color: #E2E8F0;")
        self.mute_audio_btn.clicked.connect(self.toggle_audio_action)
        toolbar_layout.addWidget(self.mute_audio_btn)

        # Open Folder Button
        self.open_folder_btn = QPushButton("📂 Save Folder")
        self.open_folder_btn.setCursor(Qt.PointingHandCursor)
        self.open_folder_btn.setStyleSheet("background-color: #16A085; color: white;")
        self.open_folder_btn.clicked.connect(self.open_save_folder_action)
        toolbar_layout.addWidget(self.open_folder_btn)

        # Full Screen Button
        self.fullscreen_btn = QPushButton("🖥️ Full Screen")
        self.fullscreen_btn.setCursor(Qt.PointingHandCursor)
        self.fullscreen_btn.setStyleSheet("background-color: #8E44AD; color: white;")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen_action)
        toolbar_layout.addWidget(self.fullscreen_btn)

        toolbar_layout.addStretch()

        # Stop Mirroring Button at the bottom of the toolbar
        self.stop_btn = QPushButton("🛑 Stop Mirror")
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setStyleSheet("background-color: #C0392B; color: white;")
        self.stop_btn.clicked.connect(self.stop_mirroring_pressed)
        toolbar_layout.addWidget(self.stop_btn)

        video_layout.addWidget(self.toolbar_card, 2)
        
        # Add widgets to stack
        self.right_stack.addWidget(self.controls_widget) # Index 0
        self.right_stack.addWidget(self.video_widget)    # Index 1
        
        main_h_layout.addWidget(self.right_stack, 3) # Stack takes 3/5 width for video space
        
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
        # Scan devices without interrupting layout text
        devices = self.monitor.get_android_devices()
        current_selection = self.device_combo.currentText()
        self.device_combo.clear()
        
        for dev in devices:
            # dev is a dict: {"serial": serial, "model": model_name, "type": conn_type}
            display_name = dev["model"]
            self.device_combo.addItem(display_name, dev["serial"])
            
        # Restore selection if possible
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
            QMessageBox.critical(self, "Connection Failed", f"Failed: {msg}\n\nMake sure the device has wireless debugging turned on.")
        self.status_label.setText("Status: Ready to connect")

    def browse_save_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Save Directory", self.save_dir_input.text())
        if dir_path:
            self.save_dir_input.setText(dir_path)

    def audio_checkbox_toggled(self, state):
        self.mute_audio_btn.setText("🔊 Audio: ON" if state == Qt.Checked else "🔇 Audio: OFF")

    def toggle_mirror(self):
        is_running = any(self.runner.is_running(k) for k in self.runner.active_processes if k.startswith("android"))
        
        if is_running:
            self.stop_mirroring_pressed()
        else:
            # Check engine setup
            if not self.runner.downloader.get_scrcpy_path():
                QMessageBox.warning(self, "Missing Engine", "Android engine is missing. Go to Setup tab to install it first.")
                return

            # Start mirroring
            serial = self.device_combo.currentData()
            if not serial:
                QMessageBox.warning(self, "No Device", "Please connect and select a device from the list.")
                return

            # Extract params
            res_map = {"Native (Original)": "Native", "3840 (4K UHD)": "3840", "2560 (2K QHD)": "2560", "1920 (1080p Limit)": "1920", "1280 (720p Limit)": "1280"}
            res = res_map[self.res_combo.currentText()]

            fps_map = {
                "60 FPS (Super Smooth)": "60",
                "90 FPS (High Refresh)": "90",
                "120 FPS (Pro Gaming)": "120",
                "30 FPS (Standard)": "30"
            }
            fps = fps_map[self.fps_combo.currentText()]

            bit_map = {"16 Mbps (High Quality)": "16M", "32 Mbps (4K Ultra)": "32M", "24 Mbps (Ultra Clean)": "24M", "8 Mbps (Standard)": "8M", "4 Mbps (Low Bandwidth)": "4M"}
            bitrate = bit_map[self.bitrate_combo.currentText()]

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
                self.status_label.setText("Status: Starting Mirror...")
                self.refresh_timer.stop() # Pause auto scanning
                
                # Switch stack view and start embedding polling timer
                self.right_stack.setCurrentIndex(1)
                self.video_placeholder.setText("Connecting to device screen...")
                self.embed_ticks = 0
                self.embed_timer.start(100) # Check every 100ms
            else:
                QMessageBox.critical(self, "Mirroring Error", f"Failed to start mirroring: {msg}")
                self.status_label.setText("Status: Launch failed")

    def stop_mirroring_pressed(self):
        # Stop recording timers if active
        if self.is_recording:
            self.is_recording = False
            self.rec_timer.stop()
            self.rec_status_label.setText("● REC 00:00:00")
            self.rec_toggle_btn.setText("🔴 Record")
        
        # Stop mirroring
        serial = self.device_combo.currentData()
        process_key = f"android_{serial or 'default'}"
        self.runner.stop_process(process_key)
        
        # Reset buttons and views
        self.launch_btn.setText("LAUNCH MIRROR")
        self.launch_btn.setObjectName("btnLaunch")
        self.launch_btn.setStyle(self.launch_btn.style())
        self.status_label.setText("Status: Mirroring stopped")
        self.refresh_timer.start() # Resume auto scanning
        
        # Switch stack back to settings
        self.right_stack.setCurrentIndex(0)
        
        # Clear container layout
        container_layout = self.video_container.layout()
        while container_layout.count():
            child = container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Restore placeholder
        self.video_placeholder = QLabel("Initializing Video Stream...")
        self.video_placeholder.setAlignment(Qt.AlignCenter)
        self.video_placeholder.setStyleSheet("color: #8E9AAF; font-size: 14px; font-weight: bold;")
        container_layout.addWidget(self.video_placeholder)

    def check_and_embed_android(self):
        import win32gui
        import win32con
        
        self.embed_ticks += 1
        hwnd = win32gui.FindWindow(None, "N8 G Tools Android Mirror")
        
        if hwnd:
            self.embed_timer.stop()
            self.status_label.setText("Status: Mirroring Active (Embedded)")
            
            # 1. Remove borders and title bar
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style &= ~win32con.WS_CAPTION
            style &= ~win32con.WS_THICKFRAME
            style &= ~win32con.WS_MINIMIZEBOX
            style &= ~win32con.WS_MAXIMIZEBOX
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
            
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex_style &= ~win32con.WS_EX_DLGMODALFRAME
            ex_style &= ~win32con.WS_EX_CLIENTEDGE
            ex_style &= ~win32con.WS_EX_STATICEDGE
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
            
            win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 
                                  win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | 
                                  win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | 
                                  win32con.SWP_FRAMECHANGED)
            
            # 2. Wrap window in QWindow and QWidget container
            qwin = QWindow.fromWinId(hwnd)
            qwidget = QWidget.createWindowContainer(qwin, self.video_container)
            
            # 3. Add to container layout (clear placeholder first)
            container_layout = self.video_container.layout()
            while container_layout.count():
                child = container_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
            container_layout.addWidget(qwidget)
        else:
            if self.embed_ticks > 60: # 6 seconds timeout
                self.embed_timer.stop()
                self.status_label.setText("Status: Embedding failed (Timeout)")
                QMessageBox.warning(self, "Mirroring Error", "Failed to capture mirror window. Please make sure the device is unlocked and try again.")
                self.stop_mirroring_pressed()

    # --- Live Toolbar Controls Actions ---

    def toggle_recording_action(self):
        serial = self.device_combo.currentData()
        if not serial:
            return
        
        # Toggle recording state
        if not self.is_recording:
            # Start Recording
            self.is_recording = True
            self.rec_seconds = 0
            self.rec_status_label.setText("● REC 00:00:00")
            self.rec_toggle_btn.setText("⏹️ Stop Rec")
            self.rec_toggle_btn.setStyleSheet("background-color: #27AE60; color: white;")
            self.rec_timer.start(1000)
            
            # Silently restart scrcpy with the recording parameter
            self.restart_mirror_silently()
        else:
            # Stop Recording
            self.is_recording = False
            self.rec_timer.stop()
            self.rec_status_label.setText("● REC 00:00:00")
            self.rec_toggle_btn.setText("🔴 Record")
            self.rec_toggle_btn.setStyleSheet("background-color: #E74C3C; color: white;")
            
            # Silently restart scrcpy without recording parameter
            self.restart_mirror_silently()
            QMessageBox.information(self, "Recording Saved", f"Gameplay recording saved successfully to folder:\n{self.save_dir_input.text()}")

    def restart_mirror_silently(self):
        serial = self.device_combo.currentData()
        if not serial:
            return
        
        # Stop process
        process_key = f"android_{serial}"
        self.runner.stop_process(process_key)
        
        # Re-parse parameters
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

        record_path = None
        if self.is_recording:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"N8GTools_Rec_{timestamp}.mp4"
            record_path = os.path.join(self.save_dir_input.text(), filename)

        self.runner.start_android_mirror(
            serial=serial, resolution=res, fps=fps, bitrate=bitrate,
            audio_enabled=self.audio_check.isChecked(), record_path=record_path,
            stay_awake=self.awake_check.isChecked(), turn_screen_off=self.screen_off_check.isChecked()
        )
        self.embed_ticks = 0
        self.embed_timer.start(100)

    def update_recording_timer(self):
        self.rec_seconds += 1
        hours = self.rec_seconds // 3600
        minutes = (self.rec_seconds % 3600) // 60
        seconds = self.rec_seconds % 60
        time_str = f"● REC {hours:02d}:{minutes:02d}:{seconds:02d}"
        self.rec_status_label.setText(time_str)
        if self.rec_seconds % 2 == 0:
            self.rec_status_label.setStyleSheet("color: #E74C3C; background-color: #12141C; padding: 6px; font-weight: bold; border-radius: 4px;")
        else:
            self.rec_status_label.setStyleSheet("color: #8E9AAF; background-color: #12141C; padding: 6px; font-weight: bold; border-radius: 4px;")

    def take_screenshot_action(self):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"N8GTools_Screenshot_{timestamp}.png"
        filepath = os.path.join(self.save_dir_input.text(), filename)
        
        pixmap = self.video_container.grab()
        if pixmap.save(filepath):
            QMessageBox.information(self, "Screenshot Saved", f"Screenshot saved successfully to:\n{filepath}")
        else:
            QMessageBox.critical(self, "Screenshot Error", "Failed to save screenshot.")

    def toggle_audio_action(self):
        current = self.audio_check.isChecked()
        self.audio_check.setChecked(not current)
        self.mute_audio_btn.setText("🔊 Audio: ON" if not current else "🔇 Audio: OFF")
        
        is_running = any(self.runner.is_running(k) for k in self.runner.active_processes if k.startswith("android"))
        if is_running:
            self.restart_mirror_silently()

    def open_save_folder_action(self):
        path = self.save_dir_input.text()
        if os.path.exists(path):
            subprocess.run(f'explorer "{path}"', shell=True)

    def toggle_fullscreen_action(self):
        if self.window():
            self.window().toggle_fullscreen()
