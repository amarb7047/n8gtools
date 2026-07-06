import os
import time
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QCheckBox, QGroupBox, 
                             QFormLayout, QMessageBox, QStackedWidget, QFrame,
                             QLineEdit, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QWindow, QImage, QPixmap
import cv2
import numpy as np

class IosTab(QWidget):
    def __init__(self, runner, monitor):
        super().__init__()
        self.runner = runner
        self.monitor = monitor
        self.is_embedded = False
        
        # Timer to poll and embed UxPlay window
        self.embed_timer = QTimer()
        self.embed_timer.timeout.connect(self.check_and_embed_ios)
        
        # Timer to track recording seconds
        self.rec_seconds = 0
        self.is_recording = False
        self.rec_timer = QTimer()
        self.rec_timer.timeout.connect(self.update_recording_timer)
        
        self.init_ui()
        
        # Timer to periodically refresh connected iOS devices
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.scan_ios_devices)
        self.refresh_timer.start(3000) # Check every 3 seconds

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title Card
        title_label = QLabel("iOS AirPlay Console")
        title_label.setObjectName("tabTitle")
        layout.addWidget(title_label)

        # Horizontal Split: Configuration (Left) and Connection Guide (Right)
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(20)

        # --- Left Settings Panel ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # Device Connection Status Box (USB)
        status_group = QGroupBox("iOS USB Detection Status")
        status_group.setObjectName("settingsGroup")
        status_group_layout = QVBoxLayout(status_group)
        status_group_layout.setSpacing(10)

        self.usb_status_label = QLabel("Scanning for USB iOS devices...")
        self.usb_status_label.setObjectName("guideText")
        self.usb_status_label.setStyleSheet("font-weight: bold; color: #8E9AAF;")
        status_group_layout.addWidget(self.usb_status_label)

        # Checkbox to block PC internet routing over iPhone USB
        self.optimize_route_check = QCheckBox("Block PC Internet routing over iPhone USB (Recommended)")
        self.optimize_route_check.setChecked(True)
        status_group_layout.addWidget(self.optimize_route_check)

        left_layout.addWidget(status_group)

        # Configuration Box
        config_group = QGroupBox("AirPlay Receiver Settings")
        config_group.setObjectName("settingsGroup")
        config_layout = QFormLayout(config_group)
        config_layout.setSpacing(10)

        self.res_combo = QComboBox()
        self.res_combo.addItems(["1920x1080 (FHD - Recommended)", "1280x720 (HD)", "3840x2160 (4K UHD)", "2560x1440 (2K QHD)"])
        self.res_combo.setMinimumHeight(35)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60 FPS (Super Smooth)", "90 FPS (High Refresh)", "120 FPS (Pro Gaming)", "30 FPS (Standard)"])
        self.fps_combo.setMinimumHeight(35)

        self.audio_delay_combo = QComboBox()
        self.audio_delay_combo.addItems(["0.25 seconds (Default)", "0.15 seconds (Low Latency)", "0.05 seconds (Ultra Low)", "0.00 seconds (No Delay)"])
        self.audio_delay_combo.setMinimumHeight(35)

        self.sync_check = QCheckBox("Enable Audio-Video Sync (V-Sync)")
        self.sync_check.setChecked(False)

        # Captures Folder Selection
        self.save_dir_label = QLabel("Recordings Save Directory:")
        self.save_dir_label.setStyleSheet("font-weight: bold; color: #8E9AAF; margin-top: 5px;")
        
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

        config_layout.addRow("Mirroring Resolution:", self.res_combo)
        config_layout.addRow("Frame Rate Suggestion:", self.fps_combo)
        config_layout.addRow("Audio Buffer Latency:", self.audio_delay_combo)
        config_layout.addRow("", self.sync_check)
        config_layout.addRow(self.save_dir_label)
        config_layout.addRow(save_path_layout)

        left_layout.addWidget(config_group)

        # Actions Box
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
        
        main_h_layout.addWidget(left_panel, 2) # Left takes 2/5 width

        # --- Options & Launch Panel Stack (Right) ---
        self.right_stack = QStackedWidget()

        # 1. Right Connection Guide Box
        self.guide_group = QGroupBox("iOS Connection Setup Guide")
        self.guide_group.setObjectName("settingsGroup")
        guide_layout = QVBoxLayout(self.guide_group)
        guide_layout.setContentsMargins(15, 15, 15, 15)
        guide_layout.setSpacing(15)

        guide_text = (
            "<h3>Option A: USB Cable (Wired - Recommended for Low Latency)</h3>"
            "<ol>"
            "  <li>Disconnect Wi-Fi on your iOS device.</li>"
            "  <li>Go to <b>Settings > Personal Hotspot</b> on iOS and turn it <b>ON</b>.</li>"
            "  <li>Connect the iOS device to your PC using a USB cable.</li>"
            "  <li>Select <b>'Trust this Computer'</b> if prompted on iOS.</li>"
            "  <li>Start the AirPlay Server in this app.</li>"
            "  <li>Open iOS Control Center, tap <b>Screen Mirroring</b>, and select <b>'UxPlay'</b>.</li>"
            "</ol>"
            "<hr/>"
            "<h3>Option B: Wireless (Wi-Fi)</h3>"
            "<ol>"
            "  <li>Connect both your PC and iOS device to the <b>same Wi-Fi router</b>.</li>"
            "  <li>Start the AirPlay Server in this app.</li>"
            "  <li>Open iOS Control Center, tap <b>Screen Mirroring</b>, and select <b>'UxPlay'</b>.</li>"
            "</ol>"
        )

        guide_label = QLabel(guide_text)
        guide_label.setTextFormat(Qt.RichText)
        guide_label.setWordWrap(True)
        guide_label.setObjectName("guideText")
        guide_layout.addWidget(guide_label)
        guide_layout.addStretch()

        # 2. Video Widget (Embedded Video + Toolbar)
        self.video_widget = QWidget()
        video_layout = QHBoxLayout(self.video_widget)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(10)
        
        # Left Side: display pane
        display_panel = QWidget()
        display_layout = QVBoxLayout(display_panel)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(10)

        # Video frame container
        self.video_container = QFrame()
        self.video_container.setFrameShape(QFrame.StyledPanel)
        self.video_container.setObjectName("settingsGroup")
        self.video_container.setStyleSheet("background-color: #0F111A; border: 1px solid #1F2833; border-radius: 8px;")
        
        container_layout = QVBoxLayout(self.video_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_placeholder = QLabel("AirPlay Server running. Please connect your device from Control Center...")
        self.video_placeholder.setAlignment(Qt.AlignCenter)
        self.video_placeholder.setWordWrap(True)
        self.video_placeholder.setStyleSheet("color: #8E9AAF; font-size: 14px; font-weight: bold; padding: 20px;")
        container_layout.addWidget(self.video_placeholder)
        
        display_layout.addWidget(self.video_container, 1)

        self.info_note = QLabel("Wired/Wireless Mirroring Active (Embedded)")
        self.info_note.setAlignment(Qt.AlignCenter)
        self.info_note.setStyleSheet("color: #2ECC71; font-weight: bold; font-size: 12px;")
        display_layout.addWidget(self.info_note)
        video_layout.addWidget(display_panel, 8)

        # Right Side: Vertical Toolbar
        self.toolbar_card = QFrame()
        self.toolbar_card.setObjectName("settingsGroup")
        self.toolbar_card.setFixedWidth(130)
        self.toolbar_card.setStyleSheet("""
            QFrame {
                background-color: #1F2833;
                border: 1px solid #2D3748;
                border-radius: 8px;
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

        # Help Tip Label
        self.help_tip = QLabel("Use OBS guide tab for 60FPS video recording.")
        self.help_tip.setStyleSheet("color: #8E9AAF; font-size: 9px; text-align: center;")
        self.help_tip.setWordWrap(True)
        toolbar_layout.addWidget(self.help_tip)

        toolbar_layout.addStretch()

        # Stop Server Button
        self.stop_btn = QPushButton("🛑 Stop Server")
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setStyleSheet("background-color: #C0392B; color: white;")
        self.stop_btn.clicked.connect(self.stop_server_pressed)
        toolbar_layout.addWidget(self.stop_btn)

        video_layout.addWidget(self.toolbar_card, 2)

        # Add to stack
        self.right_stack.addWidget(self.guide_group)   # Index 0
        self.right_stack.addWidget(self.video_widget)   # Index 1

        main_h_layout.addWidget(self.right_stack, 3)

        layout.addLayout(main_h_layout)
        self.setLayout(layout)

    def scan_ios_devices(self):
        devices = self.monitor.get_ios_devices()
        iphone_devices = [d for d in devices if any(x in d["model"].lower() for x in ["iphone", "ipad", "ipod", "apple mobile device"])]
        
        if iphone_devices:
            dev_name = iphone_devices[0]["model"]
            self.usb_status_label.setText(f"● USB Connected: {dev_name}\n(Personal Hotspot must be active)")
            self.usb_status_label.setStyleSheet("font-weight: bold; color: #2ECC71;")
            
            if self.optimize_route_check.isChecked():
                self.optimize_network_routing()
            
            is_running = self.runner.is_running("ios_airplay")
            if not is_running:
                if self.runner.downloader.get_uxplay_path() and self.runner.downloader.is_bonjour_installed():
                    self.start_server_silent()
        else:
            self.usb_status_label.setText("● USB Status: No USB iPhone Detected\n(Using Wi-Fi Mode. Connect both to same Wi-Fi)")
            self.usb_status_label.setStyleSheet("font-weight: bold; color: #E74C3C;")

    def optimize_network_routing(self):
        try:
            import os
            if os.name == 'nt':
                cmd = ["powershell", "-NoProfile", "-Command", 
                       "Get-NetAdapter | Where-Object InterfaceDescription -like '*Apple*' | Get-NetIPInterface -AddressFamily IPv4 | Set-NetIPInterface -InterfaceMetric 1000"]
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                subprocess.run(cmd, startupinfo=startupinfo, timeout=5)
        except Exception:
            pass

    def start_server_silent(self):
        res = "1920x1080" if "1920" in self.res_combo.currentText() else "1280x720"
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
            "0.00 seconds (No Delay)": "0.00"
        }
        audio_delay = delay_map[self.audio_delay_combo.currentText()]
        vsync = self.sync_check.isChecked()

        self.status_label.setText("Auto-Starting Server (USB)...")
        success, msg = self.runner.start_ios_mirror(
            fps=fps, resolution=res, vsync=vsync, audio_delay=audio_delay
        )

        if success:
            self.launch_btn.setText("STOP AIRPLAY SERVER")
            self.launch_btn.setObjectName("btnStop")
            self.launch_btn.setStyle(self.launch_btn.style())
            self.status_label.setText("Status: Server Online (USB Auto). Ready for connection.")
            
            self.right_stack.setCurrentIndex(1)
            self.video_placeholder.setText("AirPlay Server running. Please connect your device from Control Center...")
            self.embed_timer.start(500) # Check every 500ms
        else:
            self.status_label.setText(f"Status: Auto-Launch failed: {msg}")

    def browse_save_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Save Directory", self.save_dir_input.text())
        if dir_path:
            self.save_dir_input.setText(dir_path)

    def toggle_server(self):
        is_running = self.runner.is_running("ios_airplay")
        
        if is_running:
            self.stop_server_pressed()
        else:
            if not self.runner.downloader.get_uxplay_path():
                QMessageBox.warning(self, "Missing Engine", "iOS engine (uxplay) is not installed. Go to Setup tab first.")
                return
            if not self.runner.downloader.is_bonjour_installed():
                QMessageBox.warning(self, "Missing Driver", "Apple Bonjour Service is missing. Please setup drivers in Setup tab.")
                return

            res = "1920x1080" if "1920" in self.res_combo.currentText() else "1280x720"
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
                "0.00 seconds (No Delay)": "0.00"
            }
            audio_delay = delay_map[self.audio_delay_combo.currentText()]
            vsync = self.sync_check.isChecked()

            self.status_label.setText("Starting Server...")
            success, msg = self.runner.start_ios_mirror(
                fps=fps, resolution=res, vsync=vsync, audio_delay=audio_delay
            )

            if success:
                self.launch_btn.setText("STOP AIRPLAY SERVER")
                self.launch_btn.setObjectName("btnStop")
                self.launch_btn.setStyle(self.launch_btn.style())
                self.status_label.setText("Status: Server Online. Ready for device connection.")
                
                self.right_stack.setCurrentIndex(1)
                self.video_placeholder.setText("AirPlay Server running. Please connect your device from Control Center...")
                self.embed_timer.start(500) # Check every 500ms
            else:
                QMessageBox.critical(self, "Server Error", f"Failed to start server: {msg}")
                self.status_label.setText("Status: Offline (Launch failed)")

    def stop_server_pressed(self):
        self.runner.stop_process("ios_airplay")
        self.launch_btn.setText("START AIRPLAY SERVER")
        self.launch_btn.setObjectName("btnLaunch")
        self.launch_btn.setStyle(self.launch_btn.style())
        self.status_label.setText("Status: Server Offline")
        
        self.embed_timer.stop()
        self.right_stack.setCurrentIndex(0)
        self.clear_container_layout()

    def check_and_embed_ios(self):
        import win32gui
        import win32con
        
        hwnd = win32gui.FindWindow(None, "UxPlay")
        
        if hwnd:
            if not self.is_embedded:
                self.is_embedded = True
                self.status_label.setText("Status: Server Online (Connected)")
                
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
                
                qwin = QWindow.fromWinId(hwnd)
                qwidget = QWidget.createWindowContainer(qwin, self.video_container)
                
                container_layout = self.video_container.layout()
                while container_layout.count():
                    child = container_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                        
                container_layout.addWidget(qwidget)
        else:
            if self.is_embedded:
                self.is_embedded = False
                self.status_label.setText("Status: Server Online. Ready for device connection.")
                self.clear_container_layout()
                
    def clear_container_layout(self):
        container_layout = self.video_container.layout()
        while container_layout.count():
            child = container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.video_placeholder = QLabel("AirPlay Server running. Please connect your device from Control Center...")
        self.video_placeholder.setAlignment(Qt.AlignCenter)
        self.video_placeholder.setWordWrap(True)
        self.video_placeholder.setStyleSheet("color: #8E9AAF; font-size: 14px; font-weight: bold; padding: 20px;")
        container_layout.addWidget(self.video_placeholder)

    def take_screenshot_action(self):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"N8GTools_Screenshot_{timestamp}.png"
        filepath = os.path.join(self.save_dir_input.text(), filename)
        
        pixmap = self.video_container.grab()
        if pixmap.save(filepath):
            QMessageBox.information(self, "Screenshot Saved", f"Screenshot saved successfully to:\n{filepath}")
        else:
            QMessageBox.critical(self, "Screenshot Error", "Failed to save screenshot.")

    def open_save_folder_action(self):
        path = self.save_dir_input.text()
        if os.path.exists(path):
            subprocess.run(f'explorer "{path}"', shell=True)

    def toggle_fullscreen_action(self):
        if self.window():
            self.window().toggle_fullscreen()

    def closeEvent(self, event):
        self.embed_timer.stop()
        if hasattr(self, 'rec_fps_timer'):
            self.rec_fps_timer.stop()
        if hasattr(self, 'video_writer') and self.video_writer:
            self.video_writer.release()
        self.runner.stop_process("ios_airplay")
        event.accept()

    def update_recording_timer(self):
        self.rec_seconds += 1
        hours, remainder = divmod(self.rec_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.rec_status_label.setText(f"● REC {hours:02d}:{minutes:02d}:{seconds:02d}")

    def toggle_recording_action(self):
        if not self.is_recording:
            # Start Recording
            self.is_recording = True
            self.rec_seconds = 0
            self.rec_status_label.setText("● REC 00:00:00")
            self.rec_toggle_btn.setText("⏹️ Stop Rec")
            self.rec_toggle_btn.setStyleSheet("background-color: #27AE60; color: white;")
            
            # Setup VideoWriter
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"N8GTools_iOS_Rec_{timestamp}.mp4"
            self.record_path = os.path.join(self.save_dir_input.text(), filename)
            
            pixmap = self.video_container.grab()
            width = pixmap.width()
            height = pixmap.height()
            
            # Ensure dimensions are even
            width = width - (width % 2)
            height = height - (height % 2)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(self.record_path, fourcc, 30.0, (width, height))
            
            # Start Timers
            self.rec_timer.start(1000)
            self.rec_fps_timer = QTimer()
            self.rec_fps_timer.timeout.connect(self.record_frame_callback)
            self.rec_fps_timer.start(33) # 30 FPS
        else:
            # Stop Recording
            self.is_recording = False
            self.rec_timer.stop()
            if hasattr(self, 'rec_fps_timer'):
                self.rec_fps_timer.stop()
            
            if hasattr(self, 'video_writer') and self.video_writer:
                self.video_writer.release()
                self.video_writer = None
                
            self.rec_status_label.setText("● REC 00:00:00")
            self.rec_toggle_btn.setText("🔴 Record")
            self.rec_toggle_btn.setStyleSheet("background-color: #E74C3C; color: white;")
            
            QMessageBox.information(
                self, "Recording Saved", 
                f"iOS Gameplay recording saved successfully to folder:\n{self.save_dir_input.text()}"
            )

    def record_frame_callback(self):
        if not self.is_recording or not hasattr(self, 'video_writer') or not self.video_writer:
            return
            
        try:
            pixmap = self.video_container.grab()
            image = pixmap.toImage().convertToFormat(QImage.Format_RGB32)
            
            width = image.width() - (image.width() % 2)
            height = image.height() - (image.height() % 2)
            
            ptr = image.bits()
            ptr.setsize(image.height() * image.width() * 4)
            arr = np.frombuffer(ptr, dtype=np.uint8).reshape((image.height(), image.width(), 4))
            frame = arr[0:height, 0:width, 0:3]
            
            self.video_writer.write(frame)
        except Exception:
            pass
