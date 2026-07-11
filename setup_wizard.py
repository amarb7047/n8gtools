import os
import sys
import shutil
import winreg
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QProgressBar, 
                             QLineEdit, QFileDialog, QStackedWidget, QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont

# Modern premium style matching the main app
QSS_STYLESHEET = """
QWidget {
    background-color: #12141C;
    font-family: 'Segoe UI', -apple-system, sans-serif;
    color: #E2E8F0;
}
QLabel#title {
    color: #66FCF1;
    font-size: 24px;
    font-weight: 800;
    margin-bottom: 5px;
}
QLabel#subtitle {
    color: #8E9AAF;
    font-size: 13px;
    margin-bottom: 20px;
}
QLabel#bodyText {
    font-size: 13px;
    line-height: 1.5;
}
QPushButton {
    background-color: #1F2833;
    border: 1px solid #2D3748;
    color: #E2E8F0;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: bold;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #2D3748;
    border-color: #4A5568;
}
QPushButton#btnPrimary {
    background-color: #6366F1;
    color: #FFFFFF;
    border: none;
}
QPushButton#btnPrimary:hover {
    background-color: #4F46E5;
}
QLineEdit {
    background-color: #1F2833;
    border: 1px solid #2D3748;
    border-radius: 6px;
    padding: 8px;
    color: #E2E8F0;
    font-size: 13px;
}
QLineEdit:focus {
    border-color: #66FCF1;
}
QProgressBar {
    border: 1px solid #2D3748;
    border-radius: 6px;
    background-color: #1F2833;
    text-align: center;
    color: #E2E8F0;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #66FCF1;
    border-radius: 5px;
}
QCheckBox {
    font-size: 13px;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #2D3748;
    border-radius: 4px;
    background-color: #1F2833;
}
QCheckBox::indicator:checked {
    background-color: #6366F1;
    image: url(logo.png); /* Fallback to styled check */
}
"""

class InstallThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, dest_dir, copy_engines=True):
        super().__init__()
        self.dest_dir = dest_dir
        self.copy_engines = copy_engines

    def run(self):
        try:
            # 0. Close active instances to prevent locks
            self.progress.emit(5, "Closing running application instances...")
            import subprocess
            try:
                subprocess.run(["taskkill", "/F", "/T", "/IM", "N8GTools.exe"], 
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["taskkill", "/F", "/T", "/IM", "uxplay.exe"], 
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["taskkill", "/F", "/T", "/IM", "scrcpy.exe"], 
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["taskkill", "/F", "/T", "/IM", "adb.exe"], 
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception:
                pass
            import time
            time.sleep(1)

            # 1. Create target directory
            self.progress.emit(10, "Creating installation directory...")
            os.makedirs(self.dest_dir, exist_ok=True)

            # Get resource folder from PyInstaller
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            
            # Paths to bundled resources
            exe_src = os.path.join(base_path, "N8GTools.exe")
            logo_src = os.path.join(base_path, "logo.png")
            ico_src = os.path.join(base_path, "logo.ico")
            avatar_src = os.path.join(base_path, "N8Gamer.jpeg")

            # Validate sources
            if not os.path.exists(exe_src):
                # Fallback to local dist directory if run during development
                exe_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "N8GTools.exe")
                logo_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
                ico_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
                avatar_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "N8Gamer.jpeg")

            if not os.path.exists(exe_src):
                self.finished.emit(False, "Error: Compiled N8GTools.exe not found in installer package.")
                return

            # 2. Copy main application files
            self.progress.emit(30, "Copying core application files...")
            shutil.copy2(exe_src, os.path.join(self.dest_dir, "N8GTools.exe"))
            if os.path.exists(logo_src):
                shutil.copy2(logo_src, os.path.join(self.dest_dir, "logo.png"))
            if os.path.exists(ico_src):
                shutil.copy2(ico_src, os.path.join(self.dest_dir, "logo.ico"))
            if os.path.exists(avatar_src):
                shutil.copy2(avatar_src, os.path.join(self.dest_dir, "N8Gamer.jpeg"))

            # 3. Optionally copy local engines to prevent re-downloading
            if self.copy_engines:
                self.progress.emit(50, "Migrating pre-downloaded scrcpy/uxplay engines...")
                local_engines = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engines")
                if os.path.exists(local_engines):
                    dest_engines = os.path.join(self.dest_dir, "engines")
                    if os.path.exists(dest_engines):
                        shutil.rmtree(dest_engines)
                    shutil.copytree(local_engines, dest_engines)

            # 4. Create Desktop Shortcut
            self.progress.emit(70, "Creating shortcuts...")
            self.create_desktop_shortcut()

            # 5. Register in Windows Add/Remove Programs (Registry)
            self.progress.emit(85, "Configuring Windows registry entries...")
            self.register_uninstaller()

            self.progress.emit(100, "Installation completed successfully!")
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))

    def create_desktop_shortcut(self):
        try:
            from win32com.client import Dispatch
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            shortcut_path = os.path.join(desktop, "N8 G Tools.lnk")
            target = os.path.join(self.dest_dir, "N8GTools.exe")
            icon = os.path.join(self.dest_dir, "logo.ico")

            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = self.dest_dir
            if os.path.exists(icon):
                shortcut.IconLocation = icon
            shortcut.save()
        except Exception:
            pass

    def register_uninstaller(self):
        try:
            # We create an entry in Current User Uninstall registry
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\N8GTools"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
            
            exe_path = os.path.join(self.dest_dir, "N8GTools.exe")
            ico_path = os.path.join(self.dest_dir, "logo.ico")
            
            # Set values
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "N8 G Tools")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.6")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "N8 G Tools Team")
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, ico_path)
            
            # Simple uninstall command (cmd to remove the directory)
            # For a proper uninstall, we could write an uninstaller executable, 
            # but cmd command deleting the folder is extremely clean.
            uninstall_cmd = f'cmd.exe /c rmdir /s /q "{self.dest_dir}"'
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
            
            winreg.CloseKey(key)
        except Exception:
            pass


def get_resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class SetupWizard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("N8 G Tools - Installation Setup Wizard")
        self.resize(550, 360)
        self.setMinimumSize(550, 360)

        # Set setup icon
        icon_path = get_resource_path("logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Default path in User Programs (no admin rights needed)
        self.default_dest = os.path.join(os.environ['LOCALAPPDATA'], "Programs", "N8GTools")

        self.init_ui()

    def init_ui(self):
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        # Create pages
        self.create_welcome_page()
        self.create_install_page()
        self.create_progress_page()
        self.create_finish_page()

    def create_welcome_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left Logo
        logo_label = QLabel()
        logo_label.setFixedSize(150, 150)
        logo_path = get_resource_path("logo.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            logo_label.setStyleSheet("background-color: #1F2833; border-radius: 12px;")
        layout.addWidget(logo_label)

        # Right Text and Action
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Welcome to N8 G Tools")
        title.setObjectName("title")
        right_layout.addWidget(title)

        subtitle = QLabel("Next-Generation Ultra Mirroring & Recording")
        subtitle.setObjectName("subtitle")
        right_layout.addWidget(subtitle)

        body = QLabel("This wizard will guide you through the quick installation of N8 G Tools on your computer.<br><br>Click <b>Next</b> to continue.")
        body.setObjectName("bodyText")
        body.setWordWrap(True)
        right_layout.addWidget(body)
        right_layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        next_btn = QPushButton("Next >")
        next_btn.setObjectName("btnPrimary")
        next_btn.clicked.connect(self.go_next)
        btn_layout.addWidget(next_btn)
        right_layout.addLayout(btn_layout)

        layout.addWidget(right_widget, 1)
        self.central_widget.addWidget(page)

    def create_install_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("Select Installation Destination")
        title.setObjectName("title")
        layout.addWidget(title)

        body = QLabel("Setup will install N8 G Tools into the following directory. To select a different folder, click Browse.")
        body.setObjectName("bodyText")
        body.setWordWrap(True)
        layout.addWidget(body)

        # Path picker
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self.default_dest)
        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # Extra options
        self.migrate_engines_check = QCheckBox("Migrate downloaded scrcpy/uxplay engines (Recommended)")
        self.migrate_engines_check.setChecked(True)
        layout.addWidget(self.migrate_engines_check)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        back_btn = QPushButton("< Back")
        back_btn.clicked.connect(self.go_back)
        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        
        install_btn = QPushButton("Install")
        install_btn.setObjectName("btnPrimary")
        install_btn.clicked.connect(self.start_installation)
        btn_layout.addWidget(install_btn)
        layout.addLayout(btn_layout)

        self.central_widget.addWidget(page)

    def create_progress_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 40, 25, 25)
        layout.setSpacing(20)

        title = QLabel("Installing N8 G Tools...")
        title.setObjectName("title")
        layout.addWidget(title)

        self.status_label = QLabel("Extracting application packages...")
        self.status_label.setObjectName("bodyText")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(25)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        self.central_widget.addWidget(page)

    def create_finish_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left Logo
        logo_label = QLabel()
        logo_label.setFixedSize(150, 150)
        logo_path = get_resource_path("logo.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            logo_label.setStyleSheet("background-color: #1F2833; border-radius: 12px;")
        layout.addWidget(logo_label)

        # Right Side
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Installation Complete!")
        title.setObjectName("title")
        right_layout.addWidget(title)

        body = QLabel("N8 G Tools has been successfully installed on your computer.<br><br>A shortcut has been created on your desktop.")
        body.setObjectName("bodyText")
        body.setWordWrap(True)
        right_layout.addWidget(body)
        right_layout.addStretch()

        self.run_app_check = QCheckBox("Launch N8 G Tools now")
        self.run_app_check.setChecked(True)
        right_layout.addWidget(self.run_app_check)
        right_layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        finish_btn = QPushButton("Finish")
        finish_btn.setObjectName("btnPrimary")
        finish_btn.clicked.connect(self.finish_installation)
        btn_layout.addWidget(finish_btn)
        right_layout.addLayout(btn_layout)

        layout.addWidget(right_widget, 1)
        self.central_widget.addWidget(page)

    def go_next(self):
        self.central_widget.setCurrentIndex(self.central_widget.currentIndex() + 1)

    def go_back(self):
        self.central_widget.setCurrentIndex(self.central_widget.currentIndex() - 1)

    def browse_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Installation Folder", self.path_input.text())
        if dir_path:
            self.path_input.setText(os.path.join(dir_path, "N8GTools"))

    def start_installation(self):
        dest = self.path_input.text().strip()
        if not dest:
            QMessageBox.warning(self, "Invalid Path", "Please enter a valid path.")
            return

        self.go_next() # Move to progress page
        
        # Start installation thread
        self.thread = InstallThread(dest, self.migrate_engines_check.isChecked())
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.install_finished)
        self.thread.start()

    def update_progress(self, val, status):
        self.progress_bar.setValue(val)
        self.status_label.setText(status)

    def install_finished(self, success, err_msg):
        if success:
            self.go_next() # Go to finish page
        else:
            QMessageBox.critical(self, "Installation Failed", f"Setup encountered an error:\n\n{err_msg}")
            self.central_widget.setCurrentIndex(1) # Return to install path screen

    def finish_installation(self):
        if self.run_app_check.isChecked():
            dest = self.path_input.text().strip()
            exe_path = os.path.join(dest, "N8GTools.exe")
            if os.path.exists(exe_path):
                import subprocess
                subprocess.Popen([exe_path], cwd=dest)
        
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS_STYLESHEET)
    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec_())
