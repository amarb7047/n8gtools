from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QStackedWidget, QFrame,
                             QProgressBar, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from ui.android_tab import AndroidTab
from ui.ios_tab import IosTab
from ui.setup_tab import SetupTab
from ui.obs_tab import ObsTab
from ui.hub_tab import HubTab
from ui.booster_tab import BoosterTab
from ui.sys_info_tab import SysInfoTab
from ui.maintenance_tab import MaintenanceTab
from ui.flasher_tab import FlasherTab
from PyQt5.QtCore import QThread, pyqtSignal

class MainWindow(QMainWindow):
    def __init__(self, runner, monitor, downloader, base_dir):
        super().__init__()
        self.runner = runner
        self.monitor = monitor
        self.downloader = downloader
        self.base_dir = base_dir
        
        self.setWindowTitle("N8 G Tools - Next Gen Ultra Mirror")
        self.resize(1000, 650)
        self.setMinimumSize(950, 600)
        
        # Load Application Window Icon
        import os
        from PyQt5.QtGui import QIcon
        icon_path = os.path.join(self.base_dir, "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.init_ui()

        # Timer to update system stats
        self.sys_timer = QTimer()
        self.sys_timer.timeout.connect(self.update_system_status)
        self.sys_timer.start(2000) # Update every 2 seconds
        self.update_system_status()

        # Check maintenance configuration on startup
        self.check_server_configurations()

    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar Panel ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(10)

        # Sidebar Title Logo
        logo_container = QWidget()
        logo_container.setObjectName("logoContainer")
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(15, 10, 15, 10)
        
        logo_title = QLabel("N8 G Tools")
        logo_title.setObjectName("logoTitle")
        logo_title.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_title)
        
        logo_subtitle = QLabel("ULTRA MIRROR & REC")
        logo_subtitle.setObjectName("logoSubtitle")
        logo_subtitle.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_subtitle)
        
        sidebar_layout.addWidget(logo_container)

        # Navigation Buttons (height reduced to 38px for a compact premium look)
        self.btn_android = QPushButton("  Android Console")
        self.btn_android.setObjectName("sidebarBtnActive") # Initial active button
        self.btn_android.setMinimumHeight(38)
        self.btn_android.setCursor(Qt.PointingHandCursor)
        self.btn_android.clicked.connect(lambda: self.switch_tab(0, self.btn_android))
        sidebar_layout.addWidget(self.btn_android)

        self.btn_ios = QPushButton("  iOS AirPlay")
        self.btn_ios.setObjectName("sidebarBtn")
        self.btn_ios.setMinimumHeight(38)
        self.btn_ios.setCursor(Qt.PointingHandCursor)
        self.btn_ios.clicked.connect(lambda: self.switch_tab(1, self.btn_ios))
        sidebar_layout.addWidget(self.btn_ios)

        self.btn_obs = QPushButton("  OBS Stream Guide")
        self.btn_obs.setObjectName("sidebarBtn")
        self.btn_obs.setMinimumHeight(38)
        self.btn_obs.setCursor(Qt.PointingHandCursor)
        self.btn_obs.clicked.connect(lambda: self.switch_tab(2, self.btn_obs))
        sidebar_layout.addWidget(self.btn_obs)

        self.btn_setup = QPushButton("  Setup & Drivers")
        self.btn_setup.setObjectName("sidebarBtn")
        self.btn_setup.setMinimumHeight(38)
        self.btn_setup.setCursor(Qt.PointingHandCursor)
        self.btn_setup.clicked.connect(lambda: self.switch_tab(3, self.btn_setup))
        sidebar_layout.addWidget(self.btn_setup)

        self.btn_hub = QPushButton("  N8 Gamer Hub")
        self.btn_hub.setObjectName("sidebarBtn")
        self.btn_hub.setMinimumHeight(38)
        self.btn_hub.setCursor(Qt.PointingHandCursor)
        self.btn_hub.clicked.connect(lambda: self.switch_tab(4, self.btn_hub))
        sidebar_layout.addWidget(self.btn_hub)

        self.btn_booster = QPushButton("  Game Booster")
        self.btn_booster.setObjectName("sidebarBtn")
        self.btn_booster.setMinimumHeight(38)
        self.btn_booster.setCursor(Qt.PointingHandCursor)
        self.btn_booster.clicked.connect(lambda: self.switch_tab(5, self.btn_booster))
        sidebar_layout.addWidget(self.btn_booster)

        self.btn_sys_info = QPushButton("  System Info")
        self.btn_sys_info.setObjectName("sidebarBtn")
        self.btn_sys_info.setMinimumHeight(38)
        self.btn_sys_info.setCursor(Qt.PointingHandCursor)
        self.btn_sys_info.clicked.connect(lambda: self.switch_tab(6, self.btn_sys_info))
        sidebar_layout.addWidget(self.btn_sys_info)

        self.btn_flasher = QPushButton("  All-in-One Flasher")
        self.btn_flasher.setObjectName("sidebarBtn")
        self.btn_flasher.setMinimumHeight(38)
        self.btn_flasher.setCursor(Qt.PointingHandCursor)
        self.btn_flasher.clicked.connect(lambda: self.switch_tab(7, self.btn_flasher))
        sidebar_layout.addWidget(self.btn_flasher)

        # Compact Status Indicator Button at bottom of Sidebar
        status_panel = QFrame()
        status_panel.setObjectName("statusPanel")
        status_layout = QVBoxLayout(status_panel)
        status_layout.setContentsMargins(10, 10, 10, 10)
        status_layout.setSpacing(5)

        self.btn_system_status = QPushButton("● System Status: Checking...")
        self.btn_system_status.setObjectName("btnSystemStatusChecking")
        self.btn_system_status.setCursor(Qt.PointingHandCursor)
        self.btn_system_status.setMinimumHeight(32)
        self.btn_system_status.clicked.connect(self.show_engine_status_details)
        status_layout.addWidget(self.btn_system_status)

        sidebar_layout.addWidget(status_panel)
        main_layout.addWidget(self.sidebar, 1)

        # --- Stacked Content Panels ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("stackedWidget")

        # Create Tab Instances
        self.android_tab = AndroidTab(self.runner, self.monitor)
        self.ios_tab = IosTab(self.runner, self.monitor)
        self.obs_tab = ObsTab()
        self.setup_tab = SetupTab(self.downloader)
        self.hub_tab = HubTab(self.base_dir)
        self.booster_tab = BoosterTab()
        self.sys_info_tab = SysInfoTab()
        self.flasher_tab = FlasherTab(self.runner, self.monitor)
        
        # Connect signal to update indicators when setup changes
        self.setup_tab.engines_updated.connect(self.update_sidebar_indicators)

        # Add to stack
        self.stacked_widget.addWidget(self.android_tab) # Index 0
        self.stacked_widget.addWidget(self.ios_tab)     # Index 1
        self.stacked_widget.addWidget(self.obs_tab)     # Index 2
        self.stacked_widget.addWidget(self.setup_tab)   # Index 3
        self.stacked_widget.addWidget(self.hub_tab)     # Index 4
        self.stacked_widget.addWidget(self.booster_tab) # Index 5
        self.stacked_widget.addWidget(self.sys_info_tab) # Index 6
        self.stacked_widget.addWidget(self.flasher_tab)  # Index 7
        
        self.maintenance_tab = MaintenanceTab()
        self.stacked_widget.addWidget(self.maintenance_tab) # Index 8

        main_layout.addWidget(self.stacked_widget, 4)

        # Store button list for handling active state toggling
        self.nav_buttons = [self.btn_android, self.btn_ios, self.btn_obs, self.btn_setup, self.btn_hub, self.btn_booster, self.btn_sys_info, self.btn_flasher]
        
        # Initial indicators refresh
        self.update_sidebar_indicators()

    def switch_tab(self, index, active_btn):
        # Update active stylesheet IDs
        for btn in self.nav_buttons:
            if btn == active_btn:
                btn.setObjectName("sidebarBtnActive")
            else:
                btn.setObjectName("sidebarBtn")
            btn.setStyle(btn.style()) # Force style refresh
            
        self.stacked_widget.setCurrentIndex(index)

    def show_engine_status_details(self):
        android_ok = bool(self.downloader.get_scrcpy_path())
        ios_ok = bool(self.downloader.get_uxplay_path())
        bonjour_ok = self.downloader.is_bonjour_installed()
        fastboot_ok = bool(self.downloader.get_platform_tools_path())
        
        status_msg = "<h3>System Engine & Driver Installation Status:</h3><br>"
        
        status_msg += f"● <b>Android Mirroring Engine:</b> {'<font color=#2ECC71><b>Ready</b></font>' if android_ok else '<font color=#E74C3C><b>Missing</b></font>'}<br>"
        status_msg += f"● <b>iOS AirPlay Engine:</b> {'<font color=#2ECC71><b>Ready</b></font>' if ios_ok else '<font color=#E74C3C><b>Missing</b></font>'}<br>"
        status_msg += f"● <b>Apple Bonjour Service:</b> {'<font color=#2ECC71><b>Active</b></font>' if bonjour_ok else '<font color=#E74C3C><b>Missing</b></font>'}<br>"
        status_msg += f"● <b>Fastboot Engine (Platform Tools):</b> {'<font color=#2ECC71><b>Ready</b></font>' if fastboot_ok else '<font color=#E74C3C><b>Missing</b></font>'}<br><br>"
        
        status_msg += "<i>If any engine or service is listed as missing, go to the <b>Setup & Drivers</b> tab to download and configure it automatically with a single click.</i>"
        
        QMessageBox.information(self, "System Engines Status Monitor", status_msg)

    def update_sidebar_indicators(self):
        """Refreshes sidebar indicator button depending on installation state."""
        android_ok = bool(self.downloader.get_scrcpy_path())
        ios_ok = bool(self.downloader.get_uxplay_path())
        bonjour_ok = self.downloader.is_bonjour_installed()
        fastboot_ok = bool(self.downloader.get_platform_tools_path())
        
        if android_ok and ios_ok and bonjour_ok and fastboot_ok:
            self.btn_system_status.setText("● System Status: Ready")
            self.btn_system_status.setObjectName("btnSystemStatusReady")
        else:
            self.btn_system_status.setText("● System Status: Setup Needed")
            self.btn_system_status.setObjectName("btnSystemStatusMissing")
            
        self.btn_system_status.setStyle(self.btn_system_status.style())

    def update_system_status(self):
        import psutil
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('C:\\')
            disk_free_gb = disk.free / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            disk_used_percent = disk.percent
            
            if hasattr(self, 'sys_info_tab'):
                self.sys_info_tab.update_stats(cpu, ram, disk_free_gb, disk_used_percent, disk_total_gb)
        except Exception:
            pass

        # Update the taskbar and titlebar icons of running scrcpy and uxplay windows at runtime
        try:
            import win32gui
            import win32con
            import os
            icon_path = os.path.join(self.base_dir, "logo.ico")
            if os.path.exists(icon_path):
                hicon = win32gui.LoadImage(
                    None, icon_path, win32con.IMAGE_ICON,
                    0, 0, win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                )
                
                def callback(hwnd, extra):
                    title = win32gui.GetWindowText(hwnd)
                    if any(term in title for term in ["N8 G Tools Android Mirror", "AirPlay Video Stream", "UxPlay"]):
                        win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
                        win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)
                    return True
                
                win32gui.EnumWindows(callback, None)
        except Exception:
            pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.sidebar.show()
        else:
            self.sidebar.hide()
            self.showFullScreen()

    def check_server_configurations(self):
        class ConfigChecker(QThread):
            config_checked = pyqtSignal(dict)
            def run(self):
                import requests
                # Mock Firebase URL or custom server endpoint.
                # When developers set their custom Firebase Default RTDB config.json url here, it updates instantly!
                url = "https://n8-g-tools-default-rtdb.asia-southeast1.firebasedatabase.app/config.json"
                try:
                    r = requests.get(url, timeout=2.0)
                    if r.status_code == 200:
                        self.config_checked.emit(r.json())
                        return
                except Exception:
                    pass
                self.config_checked.emit({"maintenance": False})

        self.checker = ConfigChecker(self)
        self.checker.config_checked.connect(self.on_config_checked)
        self.checker.start()

    def on_config_checked(self, config):
        if config and config.get("maintenance", False):
            msg = config.get("maintenance_msg", "System upgrades in progress. Please check back later.")
            if hasattr(self, 'maintenance_tab'):
                self.maintenance_tab.set_message(msg)
            self.stacked_widget.setCurrentIndex(8) # Switch to Maintenance locking tab (shifted index)
            self.sidebar.hide() # Lock navigation

    def closeEvent(self, event):
        # Terminate all active mirroring and receiver processes
        self.sys_timer.stop()
        self.runner.stop_all()
        event.accept()
