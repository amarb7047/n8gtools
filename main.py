import sys
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.downloader import EngineDownloader
from core.runner import MirrorRunner
from core.device_monitor import DeviceMonitor

QSS_STYLESHEET = """
/* Core Application Theme */
QWidget#centralWidget {
    background-color: #12141C;
    font-family: 'Segoe UI', -apple-system, sans-serif;
    color: #E2E8F0;
}

/* Sidebar Styling */
QFrame#sidebar {
    background-color: #0B0C10;
    border-right: 1px solid #1F2430;
}

QWidget#logoContainer {
    background-color: transparent;
    border: none;
    margin-bottom: 0px;
}

QLabel#logoTitle {
    color: #66FCF1;
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 1.5px;
}

QLabel#logoSubtitle {
    color: #8E9AAF;
    font-size: 8px;
    font-weight: bold;
    letter-spacing: 2px;
}

QPushButton#sidebarBtn, QPushButton#sidebarBtnActive {
    border: none;
    text-align: left;
    padding-left: 15px;
    font-size: 13px;
    font-weight: 500;
    margin: 1px 10px;
    border-radius: 6px;
}

QPushButton#sidebarBtn {
    color: #C5C6C7;
    background-color: transparent;
}

QPushButton#sidebarBtn:hover {
    color: #FFFFFF;
    background-color: #1F2833;
}

QPushButton#sidebarBtnActive {
    color: #FFFFFF;
    background-color: #4F46E5;
    border-left: 4px solid #66FCF1;
}

/* Indicators */
QFrame#statusPanel {
    background-color: #0B0C10;
    border-top: none;
    border-radius: 0px;
}

QPushButton#btnSystemStatusChecking {
    background-color: #1A1F2C;
    border: 1px solid #94A3B8;
    color: #94A3B8;
    font-weight: 600;
    font-size: 10px;
    border-radius: 12px;
    padding: 4px 10px;
    margin: 5px 20px;
}

QPushButton#btnSystemStatusReady {
    background-color: #122215;
    border: 1px solid #2ECC71;
    color: #2ECC71;
    font-weight: 600;
    font-size: 10px;
    border-radius: 12px;
    padding: 4px 10px;
    margin: 5px 20px;
}

QPushButton#btnSystemStatusMissing {
    background-color: #2D1A1A;
    border: 1px solid #E74C3C;
    color: #E74C3C;
    font-weight: 600;
    font-size: 10px;
    border-radius: 12px;
    padding: 4px 10px;
    margin: 5px 20px;
}

/* Tab Content Styling */
QStackedWidget#stackedWidget {
    background-color: #12141C;
}

/* Sub-Tab Bar Custom Theme Styling */
QTabWidget::pane {
    border: 1px solid #1F2833;
    background-color: #12141C;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #171B26;
    color: #8E9AAF;
    border: 1px solid #1F2833;
    border-bottom: none;
    padding: 6px 20px;
    min-height: 30px;
    min-width: 120px;
    font-size: 11px;
    font-weight: 600;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 6px;
}

QTabBar::tab:hover {
    background-color: #1F2833;
    color: #E2E8F0;
}

QTabBar::tab:selected {
    background-color: #12141C;
    color: #66FCF1;
    border-top: 2px solid #66FCF1;
    font-weight: bold;
}

QLabel#tabTitle {
    color: #FFFFFF;
    font-size: 24px;
    font-weight: bold;
}

QLabel#tabSubtitle {
    color: #94A3B8;
    font-size: 13px;
}

QGroupBox#settingsGroup {
    color: #66FCF1;
    font-size: 14px;
    font-weight: bold;
    border: 1px solid #1F2833;
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 15px;
    background-color: #171B26;
}

QGroupBox#settingsGroup::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 0px 5px;
}

QLabel {
    color: #E2E8F0;
    font-size: 13px;
}

QLabel#guideText {
    color: #CBD5E1;
    font-size: 13px;
    line-height: 1.5;
}

/* Inputs and Combos */
QComboBox, QLineEdit {
    background-color: #0F111A;
    border: 1px solid #2D3748;
    border-radius: 5px;
    color: #FFFFFF;
    padding: 5px 10px;
    font-size: 13px;
}

QComboBox:hover, QLineEdit:hover {
    border: 1px solid #4F46E5;
}

QComboBox:focus, QLineEdit:focus {
    border: 1px solid #66FCF1;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #171B26;
    color: #E2E8F0;
    selection-background-color: #4F46E5;
    selection-color: #FFFFFF;
    border: 1px solid #1F2833;
}

QCheckBox {
    color: #E2E8F0;
    font-size: 13px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #2D3748;
    border-radius: 4px;
    background: #0F111A;
}

QCheckBox::indicator:checked {
    background: #4F46E5;
    border: 1px solid #66FCF1;
}

/* Buttons */
QPushButton#btnAction {
    background-color: #4F46E5;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 15px;
    font-weight: bold;
    font-size: 12px;
}

QPushButton#btnAction:hover {
    background-color: #6366F1;
}

QPushButton#btnSecondary {
    background-color: #1F2833;
    color: #E2E8F0;
    border: 1px solid #2D3748;
    border-radius: 5px;
    padding: 8px 15px;
    font-weight: 500;
    font-size: 12px;
}

QPushButton#btnSecondary:hover {
    background-color: #2D3748;
}

QPushButton#btnLaunch {
    background-color: #008080;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 1px;
}

QPushButton#btnLaunch:hover {
    background-color: #00A6A6;
}

QPushButton#btnStop {
    background-color: #C0392B;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 1px;
}

QPushButton#btnStop:hover {
    background-color: #E74C3C;
}

QPushButton#btnSetup {
    background-color: #2ECC71;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 15px;
    font-weight: bold;
}

QPushButton#btnSetup:hover {
    background-color: #27AE60;
}

QPushButton#btnReinstall {
    background-color: #7F8C8D;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 15px;
    font-weight: bold;
}

QPushButton#btnReinstall:hover {
    background-color: #95A5A6;
}

QLabel#statusText {
    font-size: 12px;
    color: #94A3B8;
    font-weight: 500;
}

/* Engine Card inside Setup tab */
QWidget#engineCard {
    background-color: #171B26;
    border: 1px solid #1F2833;
    border-radius: 8px;
}

QLabel#engineTitle {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: bold;
}

QLabel#engineDesc {
    color: #94A3B8;
    font-size: 12px;
}

QProgressBar {
    background-color: #0F111A;
    border: 1px solid #2D3748;
    border-radius: 4px;
    text-align: center;
    color: white;
    font-weight: bold;
    font-size: 11px;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #4F46E5;
    border-radius: 3px;
}

/* Scroll areas */
QScrollArea#guideScroll {
    border: none;
    background-color: transparent;
}

/* Dialogs / QMessageBox */
QDialog, QMessageBox {
    background-color: #12141C;
    border: 1px solid #2D3748;
    color: #E2E8F0;
}

QMessageBox QLabel {
    color: #E2E8F0;
    font-size: 13px;
}

QMessageBox QPushButton {
    background-color: #4F46E5;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 15px;
    font-weight: bold;
    min-width: 75px;
}

QMessageBox QPushButton:hover {
    background-color: #6366F1;
}
"""

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def main():
    # Set app scaling for high DPI displays
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS_STYLESHEET)
    
    # Initialize Core engines and systems with dynamic base dir for pyinstaller
    base_dir = get_base_dir()
    downloader = EngineDownloader(base_dir=base_dir)
    runner = MirrorRunner(downloader)
    monitor = DeviceMonitor(runner)
    
    # Create and show window
    window = MainWindow(runner, monitor, downloader, base_dir)
    window.show()
    
    # Run loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
