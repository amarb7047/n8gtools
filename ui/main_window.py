from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QStackedWidget, QFrame,
                             QProgressBar, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from ui.android_tab import AndroidTab
from ui.ios_tab import IosTab
from ui.setup_tab import SetupTab
from ui.obs_tab import ObsTab
from ui.hub_tab import HubTab
from ui.booster_tab import BoosterTab
from ui.sys_info_tab import SysInfoTab
from ui.maintenance_tab import MaintenanceTab
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
        logo_layout.setContentsMargins(20, 20, 20, 20)
        
        logo_title = QLabel("N8 G Tools")
        logo_title.setObjectName("logoTitle")
        logo_title.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_title)
        
        logo_subtitle = QLabel("ULTRA MIRROR & REC")
        logo_subtitle.setObjectName("logoSubtitle")
        logo_subtitle.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_subtitle)
        
        sidebar_layout.addWidget(logo_container)

        # Navigation Buttons
        self.btn_android = QPushButton("  Android Console")
        self.btn_android.setObjectName("sidebarBtnActive") # Initial active button
        self.btn_android.setMinimumHeight(50)
        self.btn_android.setCursor(Qt.PointingHandCursor)
        self.btn_android.clicked.connect(lambda: self.switch_tab(0, self.btn_android))
        sidebar_layout.addWidget(self.btn_android)

        self.btn_ios = QPushButton("  iOS AirPlay")
        self.btn_ios.setObjectName("sidebarBtn")
        self.btn_ios.setMinimumHeight(50)
        self.btn_ios.setCursor(Qt.PointingHandCursor)
        self.btn_ios.clicked.connect(lambda: self.switch_tab(1, self.btn_ios))
        sidebar_layout.addWidget(self.btn_ios)

        self.btn_obs = QPushButton("  OBS Stream Guide")
        self.btn_obs.setObjectName("sidebarBtn")
        self.btn_obs.setMinimumHeight(50)
        self.btn_obs.setCursor(Qt.PointingHandCursor)
        self.btn_obs.clicked.connect(lambda: self.switch_tab(2, self.btn_obs))
        sidebar_layout.addWidget(self.btn_obs)

        self.btn_setup = QPushButton("  Setup & Drivers")
        self.btn_setup.setObjectName("sidebarBtn")
        self.btn_setup.setMinimumHeight(50)
        self.btn_setup.setCursor(Qt.PointingHandCursor)
        self.btn_setup.clicked.connect(lambda: self.switch_tab(3, self.btn_setup))
        sidebar_layout.addWidget(self.btn_setup)

        self.btn_hub = QPushButton("  N8 Gamer Hub")
        self.btn_hub.setObjectName("sidebarBtn")
        self.btn_hub.setMinimumHeight(50)
        self.btn_hub.setCursor(Qt.PointingHandCursor)
        self.btn_hub.clicked.connect(lambda: self.switch_tab(4, self.btn_hub))
        sidebar_layout.addWidget(self.btn_hub)

        self.btn_booster = QPushButton("  Game Booster")
        self.btn_booster.setObjectName("sidebarBtn")
        self.btn_booster.setMinimumHeight(50)
        self.btn_booster.setCursor(Qt.PointingHandCursor)
        self.btn_booster.clicked.connect(lambda: self.switch_tab(5, self.btn_booster))
        sidebar_layout.addWidget(self.btn_booster)

        self.btn_sys_info = QPushButton("  System Info")
        self.btn_sys_info.setObjectName("sidebarBtn")
        self.btn_sys_info.setMinimumHeight(50)
        self.btn_sys_info.setCursor(Qt.PointingHandCursor)
        self.btn_sys_info.clicked.connect(lambda: self.switch_tab(6, self.btn_sys_info))
        sidebar_layout.addWidget(self.btn_sys_info)

        # Engine Status Indicators at bottom of Sidebar
        status_panel = QFrame()
        status_panel.setObjectName("statusPanel")
        status_layout = QVBoxLayout(status_panel)
        status_layout.setContentsMargins(15, 15, 15, 15)
        status_layout.setSpacing(8)

        self.android_indicator = QLabel("● Android Engine: Missing")
        self.android_indicator.setObjectName("indMissing")
        self.ios_indicator = QLabel("● iOS Engine: Missing")
        self.ios_indicator.setObjectName("indMissing")
        self.bonjour_indicator = QLabel("● Bonjour Service: Missing")
        self.bonjour_indicator.setObjectName("indMissing")

        status_layout.addWidget(self.android_indicator)
        status_layout.addWidget(self.ios_indicator)
        status_layout.addWidget(self.bonjour_indicator)

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
        
        self.maintenance_tab = MaintenanceTab()
        self.stacked_widget.addWidget(self.maintenance_tab) # Index 7

        main_layout.addWidget(self.stacked_widget, 4)

        # Store button list for handling active state toggling
        self.nav_buttons = [self.btn_android, self.btn_ios, self.btn_obs, self.btn_setup, self.btn_hub, self.btn_booster, self.btn_sys_info]
        
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

    def update_sidebar_indicators(self):
        """Refreshes sidebar indicator badges depending on installation state."""
        # Android
        if self.downloader.get_scrcpy_path():
            self.android_indicator.setText("● Android Engine: Ready")
            self.android_indicator.setObjectName("indReady")
        else:
            self.android_indicator.setText("● Android Engine: Missing")
            self.android_indicator.setObjectName("indMissing")

        # iOS
        if self.downloader.get_uxplay_path():
            self.ios_indicator.setText("● iOS Engine: Ready")
            self.ios_indicator.setObjectName("indReady")
        else:
            self.ios_indicator.setText("● iOS Engine: Missing")
            self.ios_indicator.setObjectName("indMissing")

        # Bonjour
        if self.downloader.is_bonjour_installed():
            self.bonjour_indicator.setText("● Bonjour Service: Active")
            self.bonjour_indicator.setObjectName("indReady")
        else:
            self.bonjour_indicator.setText("● Bonjour Service: Missing")
            self.bonjour_indicator.setObjectName("indMissing")

        # Force stylesheet refreshes
        self.android_indicator.setStyle(self.android_indicator.style())
        self.ios_indicator.setStyle(self.ios_indicator.style())
        self.bonjour_indicator.setStyle(self.bonjour_indicator.style())

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
            self.stacked_widget.setCurrentIndex(7) # Switch to Maintenance locking tab
            self.sidebar.hide() # Lock navigation

    def closeEvent(self, event):
        # Terminate all active mirroring and receiver processes
        self.sys_timer.stop()
        self.runner.stop_all()
        event.accept()
