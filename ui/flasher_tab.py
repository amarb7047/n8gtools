import os
import re
import sys
import time
import subprocess
import threading
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QLineEdit, QGroupBox, 
                             QFormLayout, QFileDialog, QPlainTextEdit, QMessageBox, QTabWidget, QTextBrowser, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from core.mi_unlock import MiUnlockSession

class FlasherThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, action_type, params):
        super().__init__()
        self.action_type = action_type
        self.params = params

    def run(self):
        try:
            if self.action_type == "mi_login":
                session = self.params["session"]
                user = self.params["user"]
                pwd = self.params["pwd"]
                pasted_url = self.params["pasted_url"]
                
                self.log_signal.emit("Logging into Xiaomi Account API...")
                success, msg = session.authenticate(user, pwd, pasted_url)
                self.finished_signal.emit(success, msg)

            elif self.action_type == "mi_check_notice":
                session = self.params["session"]
                product = self.params["product"]
                self.log_signal.emit(f"Checking clear device notice for product: {product}...")
                success, clean_or_not, notice = session.get_confirm_notice(product)
                if success:
                    res_msg = f"Clean User Data: {'Yes' if clean_or_not == 1 else 'No'}\nNotice: {notice}"
                    self.finished_signal.emit(True, res_msg)
                else:
                    self.finished_signal.emit(False, notice)

            elif self.action_type == "mi_unlock":
                session = self.params["session"]
                fastboot_path = self.params["fastboot_path"]
                product = self.params["product"]
                token = self.params["token"]
                serial = self.params["serial"]
                
                self.log_signal.emit("Contacting Xiaomi server for unlock signature...")
                success, msg = session.unlock_device(fastboot_path, product, token, serial)
                self.finished_signal.emit(success, msg)

            elif self.action_type == "adb_command":
                cmd = self.params["cmd"]
                self.log_signal.emit(f"Running ADB command: {' '.join(cmd[1:])}")
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, startupinfo=startupinfo)
                for line in iter(process.stdout.readline, ''):
                    self.log_signal.emit(line.strip())
                process.stdout.close()
                process.wait()
                
                if process.returncode == 0:
                    self.finished_signal.emit(True, "ADB Command completed successfully.")
                else:
                    self.finished_signal.emit(False, f"ADB Command exited with code {process.returncode}.")

            elif self.action_type == "fastboot_command":
                cmd = self.params["cmd"]
                self.log_signal.emit(f"Running Fastboot command: {' '.join(cmd[1:])}")
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, startupinfo=startupinfo)
                for line in iter(process.stdout.readline, ''):
                    self.log_signal.emit(line.strip())
                process.stdout.close()
                process.wait()
                
                if process.returncode == 0:
                    self.finished_signal.emit(True, "Fastboot Command completed successfully.")
                else:
                    self.finished_signal.emit(False, f"Fastboot Command exited with code {process.returncode}.")

            elif self.action_type == "flash_rom":
                script_path = self.params["script_path"]
                rom_dir = self.params["rom_dir"]
                fastboot_dir = self.params["fastboot_dir"]
                
                self.log_signal.emit(f"Executing Fastboot ROM Flash Script: {os.path.basename(script_path)}")
                
                # Add fastboot dir to environment PATH so the ROM script can find fastboot.exe
                env = os.environ.copy()
                if fastboot_dir:
                    env["PATH"] = fastboot_dir + os.pathsep + env.get("PATH", "")
                
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                process = subprocess.Popen([script_path], cwd=rom_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, startupinfo=startupinfo)
                for line in iter(process.stdout.readline, ''):
                    self.log_signal.emit(line.strip())
                process.stdout.close()
                process.wait()
                
                if process.returncode == 0:
                    self.finished_signal.emit(True, "ROM flashing completed successfully! Device should reboot.")
                else:
                    self.finished_signal.emit(False, f"ROM script exited with code {process.returncode}.")

            elif self.action_type == "backup_partitions":
                adb_path = self.params["adb_path"]
                serial = self.params["serial"]
                partitions = self.params["partitions"]
                backup_dir = self.params["backup_dir"]
                
                os.makedirs(backup_dir, exist_ok=True)
                self.log_signal.emit(f"Starting IMEI/Baseband Backup to: {backup_dir}")
                
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                # Check root access
                self.log_signal.emit("Checking device root privileges...")
                chk_res = subprocess.run([adb_path, "-s", serial, "shell", "id"], capture_output=True, text=True, startupinfo=startupinfo, timeout=5)
                uid_str = chk_res.stdout.lower()
                
                is_root = "uid=0(root)" in uid_str or "root" in uid_str
                su_prefix = ""
                if not is_root:
                    su_res = subprocess.run([adb_path, "-s", serial, "shell", "su -c id"], capture_output=True, text=True, startupinfo=startupinfo, timeout=5)
                    if "uid=0" in su_res.stdout.lower() or "root" in su_res.stdout.lower():
                        su_prefix = "su -c "
                        is_root = True
                
                if not is_root:
                    self.finished_signal.emit(False, "Root access denied. To back up raw partitions, your device must be Rooted or booted into TWRP Recovery mode.")
                    return

                # Locate by-name directory
                self.log_signal.emit("Locating partition by-name folder on phone...")
                locate_cmd = 'for d in /dev/block/bootdevice/by-name /dev/block/by-name /dev/block/platform/*/by-name /dev/block/platform/*/*/by-name; do if [ -d "$d" ]; then echo "$d"; exit 0; fi; done'
                if su_prefix:
                    run_cmd = [adb_path, "-s", serial, "shell", f"su -c '{locate_cmd}'"]
                else:
                    run_cmd = [adb_path, "-s", serial, "shell", locate_cmd]
                
                loc_res = subprocess.run(run_cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=5)
                by_name_dir = loc_res.stdout.strip()
                
                if not by_name_dir:
                    self.finished_signal.emit(False, "Could not locate block by-name directory on this device.")
                    return
                
                self.log_signal.emit(f"Found block directory: {by_name_dir}")
                
                backed_up = []
                for part in partitions:
                    self.log_signal.emit(f"Backing up partition: {part}...")
                    target_img = f"/data/local/tmp/{part}.img"
                    dd_cmd = f"dd if={by_name_dir}/{part} of={target_img}"
                    
                    if su_prefix:
                        sh_cmd = [adb_path, "-s", serial, "shell", f"su -c '{dd_cmd}'"]
                    else:
                        sh_cmd = [adb_path, "-s", serial, "shell", dd_cmd]
                        
                    dd_res = subprocess.run(sh_cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=15)
                    if "no such file" in dd_res.stdout.lower() or "no such file" in dd_res.stderr.lower() or dd_res.returncode != 0:
                        self.log_signal.emit(f"Notice: Partition '{part}' not found or could not be read. Skipping.")
                        continue
                    
                    # Pull image
                    self.log_signal.emit(f"Pulling {part}.img to PC...")
                    pull_res = subprocess.run([adb_path, "-s", serial, "pull", target_img, os.path.join(backup_dir, f"{part}.img")], capture_output=True, text=True, startupinfo=startupinfo, timeout=30)
                    
                    # Delete temp image on phone
                    del_cmd = f"rm {target_img}"
                    if su_prefix:
                        subprocess.run([adb_path, "-s", serial, "shell", f"su -c '{del_cmd}'"], startupinfo=startupinfo)
                    else:
                        subprocess.run([adb_path, "-s", serial, "shell", del_cmd], startupinfo=startupinfo)
                        
                    if pull_res.returncode == 0:
                        backed_up.append(part)
                        self.log_signal.emit(f"Success: {part} backup finished.")
                    else:
                        self.log_signal.emit(f"Error: Failed to pull {part}.img")
                
                if backed_up:
                    self.finished_signal.emit(True, f"Backup completed successfully for: {', '.join(backed_up)}. Files saved in: {backup_dir}")
                else:
                    self.finished_signal.emit(False, "Failed to back up any partition. Check if the device is connected properly in TWRP/ADB root.")

            elif self.action_type == "restore_partitions":
                mode = self.params["mode"]
                serial = self.params["serial"]
                backup_dir = self.params["backup_dir"]
                partitions = self.params["partitions"] # list of (partition_name, file_name)
                
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                self.log_signal.emit(f"Starting IMEI/Baseband Restore from: {backup_dir}")
                
                restored = []
                if mode == "fastboot":
                    fastboot_path = self.params["fastboot_path"]
                    for part, file_name in partitions:
                        img_path = os.path.join(backup_dir, file_name)
                        if not os.path.exists(img_path):
                            self.log_signal.emit(f"Warning: Backup file {file_name} not found. Skipping.")
                            continue
                            
                        self.log_signal.emit(f"Flashing partition '{part}' via Fastboot...")
                        res = subprocess.run([fastboot_path, "-s", serial, "flash", part, img_path], capture_output=True, text=True, startupinfo=startupinfo, timeout=30)
                        if res.returncode == 0:
                            restored.append(part)
                            self.log_signal.emit(f"Success: Flashed {part}")
                        else:
                            self.log_signal.emit(f"Failed: Error flashing {part}\n{res.stderr}")
                
                elif mode == "adb":
                    adb_path = self.params["adb_path"]
                    # Check root
                    chk_res = subprocess.run([adb_path, "-s", serial, "shell", "id"], capture_output=True, text=True, startupinfo=startupinfo, timeout=5)
                    uid_str = chk_res.stdout.lower()
                    is_root = "uid=0(root)" in uid_str or "root" in uid_str
                    su_prefix = ""
                    if not is_root:
                        su_res = subprocess.run([adb_path, "-s", serial, "shell", "su -c id"], capture_output=True, text=True, startupinfo=startupinfo, timeout=5)
                        if "uid=0" in su_res.stdout.lower() or "root" in su_res.stdout.lower():
                            su_prefix = "su -c "
                            is_root = True
                    
                    if not is_root:
                        self.finished_signal.emit(False, "Root access denied. Boot into TWRP Recovery to restore via ADB.")
                        return

                    # Locate by-name
                    locate_cmd = 'for d in /dev/block/bootdevice/by-name /dev/block/by-name /dev/block/platform/*/by-name /dev/block/platform/*/*/by-name; do if [ -d "$d" ]; then echo "$d"; exit 0; fi; done'
                    if su_prefix:
                        run_cmd = [adb_path, "-s", serial, "shell", f"su -c '{locate_cmd}'"]
                    else:
                        run_cmd = [adb_path, "-s", serial, "shell", locate_cmd]
                    
                    loc_res = subprocess.run(run_cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=5)
                    by_name_dir = loc_res.stdout.strip()
                    if not by_name_dir:
                        self.finished_signal.emit(False, "Could not locate block by-name directory on device.")
                        return
                    
                    for part, file_name in partitions:
                        img_path = os.path.join(backup_dir, file_name)
                        if not os.path.exists(img_path):
                            self.log_signal.emit(f"Warning: {file_name} not found. Skipping.")
                            continue
                            
                        # Push to temp
                        temp_dest = f"/data/local/tmp/restore_{part}.img"
                        self.log_signal.emit(f"Pushing {file_name} to phone...")
                        push_res = subprocess.run([adb_path, "-s", serial, "push", img_path, temp_dest], capture_output=True, text=True, startupinfo=startupinfo, timeout=30)
                        if push_res.returncode != 0:
                            self.log_signal.emit(f"Failed to push {file_name}")
                            continue
                            
                        # Write back using dd
                        self.log_signal.emit(f"Restoring partition '{part}' via dd...")
                        dd_cmd = f"dd if={temp_dest} of={by_name_dir}/{part}"
                        if su_prefix:
                            run_dd = [adb_path, "-s", serial, "shell", f"su -c '{dd_cmd}'"]
                        else:
                            run_dd = [adb_path, "-s", serial, "shell", dd_cmd]
                            
                        dd_res = subprocess.run(run_dd, capture_output=True, text=True, startupinfo=startupinfo, timeout=20)
                        
                        # Clean up temp
                        del_cmd = f"rm {temp_dest}"
                        if su_prefix:
                            subprocess.run([adb_path, "-s", serial, "shell", f"su -c '{del_cmd}'"], startupinfo=startupinfo)
                        else:
                            subprocess.run([adb_path, "-s", serial, "shell", del_cmd], startupinfo=startupinfo)
                            
                        if dd_res.returncode == 0:
                            restored.append(part)
                            self.log_signal.emit(f"Success: Restored {part}")
                        else:
                            self.log_signal.emit(f"Failed: dd write error for {part}")
                            
                if restored:
                    self.finished_signal.emit(True, f"Restored partitions: {', '.join(restored)} successfully.")
                else:
                    self.finished_signal.emit(False, "Failed to restore any partition. Ensure backup files are present.")

            elif self.action_type == "wipe_efs":
                fastboot_path = self.params["fastboot_path"]
                serial = self.params["serial"]
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                self.log_signal.emit("Erasing modemst1 partition...")
                r1 = subprocess.run([fastboot_path, "-s", serial, "erase", "modemst1"], capture_output=True, text=True, startupinfo=startupinfo)
                self.log_signal.emit(r1.stdout + r1.stderr)
                
                self.log_signal.emit("Erasing modemst2 partition...")
                r2 = subprocess.run([fastboot_path, "-s", serial, "erase", "modemst2"], capture_output=True, text=True, startupinfo=startupinfo)
                self.log_signal.emit(r2.stdout + r2.stderr)
                
                self.log_signal.emit("Erasing fsg partition...")
                r3 = subprocess.run([fastboot_path, "-s", serial, "erase", "fsg"], capture_output=True, text=True, startupinfo=startupinfo)
                self.log_signal.emit(r3.stdout + r3.stderr)
                
                if r1.returncode == 0 or r2.returncode == 0:
                    self.finished_signal.emit(True, "EFS Wiped successfully. Please reboot your device to rebuild EFS.")
                else:
                    self.finished_signal.emit(False, "Failed to erase EFS partitions.")

            elif self.action_type == "erase_frp":
                fastboot_path = self.params["fastboot_path"]
                serial = self.params["serial"]
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                self.log_signal.emit("Attempting standard Fastboot FRP erase...")
                r1 = subprocess.run([fastboot_path, "-s", serial, "erase", "frp"], capture_output=True, text=True, startupinfo=startupinfo)
                self.log_signal.emit(r1.stdout + r1.stderr)
                
                self.log_signal.emit("Attempting alternative config partition erase (Oppo/Realme/MTK)...")
                r2 = subprocess.run([fastboot_path, "-s", serial, "erase", "config"], capture_output=True, text=True, startupinfo=startupinfo)
                self.log_signal.emit(r2.stdout + r2.stderr)
                
                if r1.returncode == 0 or r2.returncode == 0:
                    self.finished_signal.emit(True, "FRP Partition Erased successfully. Reboot device to verify.")
                else:
                    self.finished_signal.emit(False, "FRP Erase failed. Ensure your device is connected in Fastboot mode with an unlocked bootloader.")

        except Exception as e:
            self.finished_signal.emit(False, f"Error during execution: {str(e)}")

class FlasherTab(QWidget):
    def __init__(self, runner, monitor):
        super().__init__()
        self.runner = runner
        self.monitor = monitor
        self.downloader = runner.downloader
        
        self.mi_session = MiUnlockSession()
        self.detected_serial = None
        self.detected_mode = None # "adb", "fastboot", "sideload", "recovery", None
        self.detected_codename = "Unknown"
        self.detected_model = "Unknown"
        self.detected_unlocked = "Unknown"
        self.detected_token = None
        self.detected_manufacturer = "Unknown"
        
        self.init_ui()
        
        # Periodic scanner for connected devices
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.scan_device_status)
        self.scan_timer.start(2000) # Scan every 2 seconds
        self.scan_device_status()

    def init_ui(self):
        # Create an outer main layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        # Create a container widget for scroll area
        container = QWidget()
        container.setObjectName("tabContainer")
        container.setStyleSheet("background-color: transparent;")
        
        # All our actual layouts go inside this container
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        # Tab Title
        title = QLabel("All-in-One Flash & Unlock Console")
        title.setObjectName("tabTitle")
        main_layout.addWidget(title)

        # Top Device Status Indicator Card
        self.status_card = QGroupBox("Connected Device Monitor")
        self.status_card.setObjectName("settingsGroup")
        status_layout = QHBoxLayout(self.status_card)
        status_layout.setContentsMargins(15, 12, 15, 12)
        
        self.lbl_device_mode = QLabel("● Device Status: Scanning...")
        self.lbl_device_mode.setStyleSheet("font-weight: bold; font-size: 14px; color: #8E9AAF;")
        status_layout.addWidget(self.lbl_device_mode)
        
        self.lbl_device_info = QLabel("Details: No device detected")
        self.lbl_device_info.setStyleSheet("font-size: 13px; color: #CBD5E1;")
        status_layout.addWidget(self.lbl_device_info)
        
        # Quick Reboot Actions
        reboot_layout = QHBoxLayout()
        reboot_layout.setSpacing(5)
        
        self.btn_reboot_sys = QPushButton("Reboot System")
        self.btn_reboot_sys.setObjectName("btnSecondary")
        self.btn_reboot_sys.clicked.connect(self.reboot_system)
        
        self.btn_reboot_bl = QPushButton("Reboot Bootloader")
        self.btn_reboot_bl.setObjectName("btnSecondary")
        self.btn_reboot_bl.clicked.connect(self.reboot_bootloader)
        
        self.btn_reboot_rec = QPushButton("Reboot Recovery")
        self.btn_reboot_rec.setObjectName("btnSecondary")
        self.btn_reboot_rec.clicked.connect(self.reboot_recovery)

        self.btn_reboot_edl = QPushButton("Reboot EDL")
        self.btn_reboot_edl.setObjectName("btnSecondary")
        self.btn_reboot_edl.clicked.connect(self.reboot_edl)

        self.btn_reboot_dl = QPushButton("Reboot Download")
        self.btn_reboot_dl.setObjectName("btnSecondary")
        self.btn_reboot_dl.clicked.connect(self.reboot_download)
        
        reboot_layout.addWidget(self.btn_reboot_sys)
        reboot_layout.addWidget(self.btn_reboot_bl)
        reboot_layout.addWidget(self.btn_reboot_rec)
        reboot_layout.addWidget(self.btn_reboot_edl)
        reboot_layout.addWidget(self.btn_reboot_dl)
        
        status_layout.addStretch()
        status_layout.addLayout(reboot_layout)
        
        # Driver Recommendation Banner Alert (Hidden by default)
        self.lbl_driver_alert = QLabel("")
        self.lbl_driver_alert.setWordWrap(True)
        self.lbl_driver_alert.setStyleSheet("background-color: #2D2214; border: 1px solid #D68910; color: #F5B041; padding: 10px; border-radius: 6px; font-weight: 500; font-size: 13px; margin-bottom: 5px;")
        self.lbl_driver_alert.setVisible(False)
        main_layout.addWidget(self.lbl_driver_alert)

        main_layout.addWidget(self.status_card)

        # Main Sub-sections tabs
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #1F2833; background: #12141C; }")
        
        self.create_xiaomi_tab()
        self.create_fastboot_tab()
        self.create_recovery_tab()
        self.create_repair_tab()
        self.create_guides_tab()
        
        main_layout.addWidget(self.sub_tabs)

        # Bottom Live Output Console
        console_group = QGroupBox("Live Operations Console Log")
        console_group.setObjectName("settingsGroup")
        console_layout = QVBoxLayout(console_group)
        console_layout.setContentsMargins(10, 10, 10, 10)
        
        self.txt_console = QPlainTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setMinimumHeight(150)
        self.txt_console.setStyleSheet("background-color: #0F111A; color: #66FCF1; font-family: 'Consolas', monospace; font-size: 12px; border: 1px solid #2D3748;")
        console_layout.addWidget(self.txt_console)
        
        clear_console_btn = QPushButton("Clear Log")
        clear_console_btn.setObjectName("btnSecondary")
        clear_console_btn.clicked.connect(self.txt_console.clear)
        clear_console_btn.setFixedWidth(100)
        console_layout.addWidget(clear_console_btn, 0, Qt.AlignRight)
        
        main_layout.addWidget(console_group)
        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def create_xiaomi_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_lbl = QLabel("Xiaomi/Mi Official Bootloader Unlocker")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #66FCF1;")
        layout.addWidget(title_lbl)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.txt_mi_user = QLineEdit()
        self.txt_mi_user.setPlaceholderText("Xiaomi ID, Email or Phone")
        
        self.txt_mi_pwd = QLineEdit()
        self.txt_mi_pwd.setEchoMode(QLineEdit.Password)
        self.txt_mi_pwd.setPlaceholderText("Password")
        
        self.txt_mi_redirect = QLineEdit()
        self.txt_mi_redirect.setPlaceholderText("Paste URL containing 'd=' parameter here after logging in")

        form_layout.addRow("Xiaomi Account Info:", self.txt_mi_user)
        form_layout.addRow("Account Password:", self.txt_mi_pwd)
        
        # Link generator row
        link_btn = QPushButton("Open Official Login Page (Get Link)")
        link_btn.setObjectName("btnAction")
        link_btn.clicked.connect(self.open_mi_login_page)
        
        form_layout.addRow("1. Login Action:", link_btn)
        form_layout.addRow("2. Paste Redirected URL:", self.txt_mi_redirect)

        layout.addLayout(form_layout)

        # Login and Status Info
        action_layout = QHBoxLayout()
        
        self.btn_mi_login = QPushButton("Verify and Login API")
        self.btn_mi_login.setObjectName("btnSetup")
        self.btn_mi_login.clicked.connect(self.run_mi_login)
        action_layout.addWidget(self.btn_mi_login)

        self.btn_mi_logout = QPushButton("Logout Account")
        self.btn_mi_logout.setObjectName("btnStop")
        self.btn_mi_logout.clicked.connect(self.run_mi_logout)
        action_layout.addWidget(self.btn_mi_logout)
        
        self.lbl_mi_status = QLabel("API Account Status: Logged Out")
        self.lbl_mi_status.setStyleSheet("font-weight: bold; color: #E74C3C;")
        action_layout.addWidget(self.lbl_mi_status, 1, Qt.AlignLeft | Qt.AlignVCenter)
        
        layout.addLayout(action_layout)

        # Clear Notice and Unlock Actions
        unlock_box = QGroupBox("Unlock Commands Execution")
        unlock_box.setObjectName("settingsGroup")
        unlock_layout = QVBoxLayout(unlock_box)
        unlock_layout.setSpacing(10)
        
        self.btn_mi_clear_notice = QPushButton("Check Wipe Data Notice")
        self.btn_mi_clear_notice.setObjectName("btnSecondary")
        self.btn_mi_clear_notice.clicked.connect(self.check_mi_notice)
        unlock_layout.addWidget(self.btn_mi_clear_notice)
        
        self.btn_mi_unlock = QPushButton("UNLOCK BOOTLOADER (Stage & Execute)")
        self.btn_mi_unlock.setObjectName("btnLaunch")
        self.btn_mi_unlock.setMinimumHeight(45)
        self.btn_mi_unlock.clicked.connect(self.execute_mi_unlock)
        unlock_layout.addWidget(self.btn_mi_unlock)

        layout.addWidget(unlock_box)
        layout.addStretch()

        # Update login fields if session cached
        if self.mi_session.uid:
            self.lbl_mi_status.setText(f"API Account Status: Logged in (UID: {self.mi_session.uid})")
            self.lbl_mi_status.setStyleSheet("font-weight: bold; color: #2ECC71;")
            self.txt_mi_user.setText(self.mi_session.user)
            self.txt_mi_pwd.setText(self.mi_session.pwd)
            self.txt_mi_redirect.setText("Session Cached - Paste new URL only if login expires")

        self.sub_tabs.addTab(tab, "Xiaomi Bootloader Unlock")

    def create_fastboot_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Fastboot ROM flasher card
        rom_box = QGroupBox("Fastboot ROM Flashing (Full Firmware Update)")
        rom_box.setObjectName("settingsGroup")
        rom_layout = QVBoxLayout(rom_box)
        rom_layout.setSpacing(10)
        
        rom_picker_layout = QHBoxLayout()
        self.txt_rom_path = QLineEdit()
        self.txt_rom_path.setPlaceholderText("Select folder containing extracted Fastboot ROM firmware...")
        
        btn_rom_browse = QPushButton("Browse Folder")
        btn_rom_browse.setObjectName("btnSecondary")
        btn_rom_browse.clicked.connect(self.browse_rom_dir)
        
        rom_picker_layout.addWidget(self.txt_rom_path)
        rom_picker_layout.addWidget(btn_rom_browse)
        rom_layout.addLayout(rom_picker_layout)

        form_layout = QFormLayout()
        self.combo_scripts = QComboBox()
        self.combo_scripts.setMinimumHeight(35)
        form_layout.addRow("Select Flash Script:", self.combo_scripts)
        rom_layout.addLayout(form_layout)

        self.btn_flash_rom = QPushButton("FLASH FASTBOOT ROM")
        self.btn_flash_rom.setObjectName("btnLaunch")
        self.btn_flash_rom.setMinimumHeight(45)
        self.btn_flash_rom.clicked.connect(self.flash_fastboot_rom)
        rom_layout.addWidget(self.btn_flash_rom)
        
        layout.addWidget(rom_box)

        # Single partition image flash card
        img_box = QGroupBox("Flash Individual Partition Images (recovery, boot, vbmeta etc.)")
        img_box.setObjectName("settingsGroup")
        img_layout = QVBoxLayout(img_box)
        img_layout.setSpacing(10)
        
        img_picker_layout = QHBoxLayout()
        self.txt_img_path = QLineEdit()
        self.txt_img_path.setPlaceholderText("Select partition image file (.img)...")
        
        btn_img_browse = QPushButton("Browse Image")
        btn_img_browse.setObjectName("btnSecondary")
        btn_img_browse.clicked.connect(self.browse_img_file)
        
        img_picker_layout.addWidget(self.txt_img_path)
        img_picker_layout.addWidget(btn_img_browse)
        img_layout.addLayout(img_picker_layout)

        part_layout = QHBoxLayout()
        self.combo_part = QComboBox()
        self.combo_part.addItems(["boot", "recovery", "vbmeta", "system", "vendor", "super", "userdata", "cache", "logo"])
        self.combo_part.setEditable(True) # Allow user to type custom partitions
        self.combo_part.setMinimumHeight(35)
        
        self.btn_flash_part = QPushButton("Flash Image to Partition")
        self.btn_flash_part.setObjectName("btnAction")
        self.btn_flash_part.clicked.connect(self.flash_partition_image)
        
        self.btn_boot_img = QPushButton("Boot Image Temporarily")
        self.btn_boot_img.setObjectName("btnSecondary")
        self.btn_boot_img.clicked.connect(self.boot_partition_image)

        part_layout.addWidget(QLabel("Partition Target:"))
        part_layout.addWidget(self.combo_part, 1)
        part_layout.addWidget(self.btn_flash_part)
        part_layout.addWidget(self.btn_boot_img)
        img_layout.addLayout(part_layout)

        layout.addWidget(img_box)
        layout.addStretch()

        self.sub_tabs.addTab(tab, "Fastboot Flasher")

    def create_recovery_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Custom recovery flasher
        rec_box = QGroupBox("Custom Recovery Flasher (TWRP / OrangeFox)")
        rec_box.setObjectName("settingsGroup")
        rec_layout = QVBoxLayout(rec_box)
        rec_layout.setSpacing(10)
        
        rec_picker_layout = QHBoxLayout()
        self.txt_rec_path = QLineEdit()
        self.txt_rec_path.setPlaceholderText("Select Custom Recovery Image (.img file)...")
        
        btn_rec_browse = QPushButton("Browse Image")
        btn_rec_browse.setObjectName("btnSecondary")
        btn_rec_browse.clicked.connect(self.browse_rec_file)
        
        rec_picker_layout.addWidget(self.txt_rec_path)
        rec_picker_layout.addWidget(btn_rec_browse)
        rec_layout.addLayout(rec_picker_layout)

        action_layout = QHBoxLayout()
        self.btn_flash_rec = QPushButton("Flash Custom Recovery")
        self.btn_flash_rec.setObjectName("btnAction")
        self.btn_flash_rec.setMinimumHeight(40)
        self.btn_flash_rec.clicked.connect(self.flash_recovery_image)
        
        self.btn_boot_rec_img = QPushButton("Boot Custom Recovery (Test Mode)")
        self.btn_boot_rec_img.setObjectName("btnSecondary")
        self.btn_boot_rec_img.setMinimumHeight(40)
        self.btn_boot_rec_img.clicked.connect(self.boot_recovery_image)

        action_layout.addWidget(self.btn_flash_rec)
        action_layout.addWidget(self.btn_boot_rec_img)
        rec_layout.addLayout(action_layout)

        layout.addWidget(rec_box)

        # ADB Sideload card
        sideload_box = QGroupBox("ADB Sideload Custom ROM / Flash Zip package")
        sideload_box.setObjectName("settingsGroup")
        sideload_layout = QVBoxLayout(sideload_box)
        sideload_layout.setSpacing(10)

        sideload_guide = QLabel("Guide: Reboot device into Recovery mode, select <b>'Apply update from ADB'</b> / <b>'ADB Sideload'</b>, then select zip package below.")
        sideload_guide.setStyleSheet("color: #94A3B8; font-size: 12px;")
        sideload_layout.addWidget(sideload_guide)

        zip_picker_layout = QHBoxLayout()
        self.txt_zip_path = QLineEdit()
        self.txt_zip_path.setPlaceholderText("Select firmware or flashable zip package (.zip file)...")
        
        btn_zip_browse = QPushButton("Browse Zip")
        btn_zip_browse.setObjectName("btnSecondary")
        btn_zip_browse.clicked.connect(self.browse_zip_file)
        
        zip_picker_layout.addWidget(self.txt_zip_path)
        zip_picker_layout.addWidget(btn_zip_browse)
        sideload_layout.addLayout(zip_picker_layout)

        self.btn_sideload = QPushButton("START ADB SIDELOAD FLASH")
        self.btn_sideload.setObjectName("btnLaunch")
        self.btn_sideload.setMinimumHeight(45)
        self.btn_sideload.clicked.connect(self.execute_sideload)
        sideload_layout.addWidget(self.btn_sideload)

        layout.addWidget(sideload_box)
        layout.addStretch()

        self.sub_tabs.addTab(tab, "Recovery & Sideload")

    def create_repair_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Format and Wipe Box
        wipe_box = QGroupBox("Metadata Repair & Partition Formatting")
        wipe_box.setObjectName("settingsGroup")
        wipe_layout = QVBoxLayout(wipe_box)
        wipe_layout.setSpacing(12)

        warning_lbl = QLabel("WARNING: All operations here will permanently wipe files and user configurations.")
        warning_lbl.setStyleSheet("color: #E74C3C; font-weight: bold; font-size: 12px;")
        wipe_layout.addWidget(warning_lbl)

        btn_grid_1 = QHBoxLayout()
        btn_format_ud = QPushButton("Format Userdata (Wipe All)")
        btn_format_ud.setObjectName("btnStop")
        btn_format_ud.clicked.connect(self.format_userdata)
        
        btn_erase_ud = QPushButton("Erase Userdata")
        btn_erase_ud.setObjectName("btnSecondary")
        btn_erase_ud.clicked.connect(self.erase_userdata)
        
        btn_erase_cache = QPushButton("Erase Cache")
        btn_erase_cache.setObjectName("btnSecondary")
        btn_erase_cache.clicked.connect(self.erase_cache)
        
        btn_erase_frp = QPushButton("Erase FRP Lock (Google Lock)")
        btn_erase_frp.setObjectName("btnStop")
        btn_erase_frp.clicked.connect(self.erase_frp_lock)

        btn_grid_1.addWidget(btn_format_ud)
        btn_grid_1.addWidget(btn_erase_ud)
        btn_grid_1.addWidget(btn_erase_cache)
        btn_grid_1.addWidget(btn_erase_frp)
        wipe_layout.addLayout(btn_grid_1)
        
        layout.addWidget(wipe_box)

        # OEM Unlock/Lock box
        oem_box = QGroupBox("Standard Android OEM Bootloader Unlock & Lock (Generic)")
        oem_box.setObjectName("settingsGroup")
        oem_layout = QVBoxLayout(oem_box)
        oem_layout.setSpacing(12)

        lbl_oem_desc = QLabel("Standard commands for Google, OnePlus, Motorola, etc. Xiaomi models MUST use the Xiaomi tab.")
        lbl_oem_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        oem_layout.addWidget(lbl_oem_desc)

        btn_grid_2 = QHBoxLayout()
        btn_unlock_std = QPushButton("OEM Unlock (oem unlock)")
        btn_unlock_std.setObjectName("btnSecondary")
        btn_unlock_std.clicked.connect(self.generic_oem_unlock)
        
        btn_unlock_flashing = QPushButton("OEM Unlock (flashing unlock)")
        btn_unlock_flashing.setObjectName("btnSecondary")
        btn_unlock_flashing.clicked.connect(self.generic_flashing_unlock)
        
        btn_lock_flashing = QPushButton("OEM Lock (flashing lock)")
        btn_lock_flashing.setObjectName("btnStop")
        btn_lock_flashing.clicked.connect(self.generic_flashing_lock)

        btn_grid_2.addWidget(btn_unlock_std)
        btn_grid_2.addWidget(btn_unlock_flashing)
        btn_grid_2.addWidget(btn_lock_flashing)
        oem_layout.addLayout(btn_grid_2)

        layout.addWidget(oem_box)

        # Baseband / IMEI Partition repair box
        imei_box = QGroupBox("Baseband & IMEI Recovery Suite (EFS & NVRAM)")
        imei_box.setObjectName("settingsGroup")
        imei_layout = QVBoxLayout(imei_box)
        imei_layout.setSpacing(10)
        
        imei_desc = QLabel("Backup, restore or erase EFS/NVRAM partitions. Root or TWRP Recovery is required for Backup/Restore in ADB mode.")
        imei_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        imei_layout.addWidget(imei_desc)

        # File picker for restore
        picker_layout = QHBoxLayout()
        self.txt_backup_dir = QLineEdit()
        self.txt_backup_dir.setPlaceholderText("Select folder containing IMEI backup (.img files) to restore...")
        btn_browse_backup = QPushButton("Browse Backup Folder")
        btn_browse_backup.setObjectName("btnSecondary")
        btn_browse_backup.clicked.connect(self.browse_backup_folder)
        picker_layout.addWidget(self.txt_backup_dir)
        picker_layout.addWidget(btn_browse_backup)
        imei_layout.addLayout(picker_layout)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()
        self.btn_backup_imei = QPushButton("Backup IMEI / EFS")
        self.btn_backup_imei.setObjectName("btnSetup")
        self.btn_backup_imei.clicked.connect(self.run_imei_backup)
        
        self.btn_restore_imei = QPushButton("Restore IMEI / EFS")
        self.btn_restore_imei.setObjectName("btnAction")
        self.btn_restore_imei.clicked.connect(self.run_imei_restore)

        self.btn_wipe_efs = QPushButton("Wipe EFS (Fix No Network)")
        self.btn_wipe_efs.setObjectName("btnStop")
        self.btn_wipe_efs.clicked.connect(self.run_efs_wipe)

        btn_layout.addWidget(self.btn_backup_imei)
        btn_layout.addWidget(self.btn_restore_imei)
        btn_layout.addWidget(self.btn_wipe_efs)
        imei_layout.addLayout(btn_layout)

        layout.addWidget(imei_box)
        layout.addStretch()

        self.sub_tabs.addTab(tab, "Advanced Repairs")

    # File dialog pickers
    def browse_rom_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Fastboot ROM Folder")
        if dir_path:
            self.txt_rom_path.setText(dir_path)
            self.scan_rom_scripts(dir_path)

    def scan_rom_scripts(self, path):
        self.combo_scripts.clear()
        # Scan folder for batch scripts (.bat) or shell scripts (.sh)
        scripts = [f for f in os.listdir(path) if f.endswith(('.bat', '.sh')) and 'flash' in f.lower()]
        if not scripts:
            # Fallback to listing all .bat or .sh
            scripts = [f for f in os.listdir(path) if f.endswith(('.bat', '.sh'))]
            
        self.combo_scripts.addItems(scripts)

    def browse_img_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Partition Image File", "", "Image Files (*.img)")
        if file_path:
            self.txt_img_path.setText(file_path)

    def browse_rec_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Custom Recovery Image", "", "Recovery Images (*.img)")
        if file_path:
            self.txt_rec_path.setText(file_path)

    def browse_zip_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select ROM or Patch Zip Package", "", "Zip Files (*.zip)")
        if file_path:
            self.txt_zip_path.setText(file_path)

    # Console logging helpers
    def log(self, text):
        self.txt_console.appendPlainText(text)
        # Auto scroll to bottom
        self.txt_console.verticalScrollBar().setValue(self.txt_console.verticalScrollBar().maximum())

    # Device Monitor logic
    def scan_device_status(self):
        # 1. Run adb devices
        adb_path = self.runner.get_adb_path()
        fastboot_path = self.downloader.get_fastboot_path()
        
        adb_connected = []
        fastboot_connected = []

        # Find ADB Devices
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            res = subprocess.run([adb_path, "devices", "-l"], capture_output=True, text=True, startupinfo=startupinfo, timeout=3)
            for line in res.stdout.splitlines():
                if not line.strip() or line.startswith("List of devices"):
                    continue
                match = re.match(r"^([^\s]+)\s+([^\s]+)\s+(.*)$", line)
                if match:
                    serial = match.group(1)
                    state = match.group(2) # "device", "recovery", "sideload", "unauthorized", etc.
                    info_str = match.group(3)
                    
                    # Extract model
                    model = "Android Device"
                    model_match = re.search(r"model:([^\s]+)", info_str)
                    if model_match:
                        model = model_match.group(1).replace("_", " ")
                    
                    adb_connected.append({"serial": serial, "state": state, "model": model})
        except Exception:
            pass

        # Find Fastboot Devices
        if fastboot_path:
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                res = subprocess.run([fastboot_path, "devices"], capture_output=True, text=True, startupinfo=startupinfo, timeout=3)
                for line in res.stdout.splitlines():
                    if not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        serial = parts[0]
                        state = parts[1] # "fastboot"
                        fastboot_connected.append({"serial": serial, "state": state})
            except Exception:
                pass

        # Update UI according to scanner results
        if adb_connected:
            dev = adb_connected[0]
            self.detected_serial = dev["serial"]
            self.detected_mode = dev["state"]
            self.detected_model = dev["model"]
            
            # Fetch manufacturer & codename
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                res_man = subprocess.run([adb_path, "-s", self.detected_serial, "shell", "getprop", "ro.product.manufacturer"], capture_output=True, text=True, startupinfo=startupinfo, timeout=2)
                self.detected_manufacturer = res_man.stdout.strip().lower()
            except Exception:
                self.detected_manufacturer = "unknown"

            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                res_code = subprocess.run([adb_path, "-s", self.detected_serial, "shell", "getprop", "ro.product.name"], capture_output=True, text=True, startupinfo=startupinfo, timeout=2)
                self.detected_codename = res_code.stdout.strip()
                if not self.detected_codename:
                    res_code2 = subprocess.run([adb_path, "-s", self.detected_serial, "shell", "getprop", "ro.product.device"], capture_output=True, text=True, startupinfo=startupinfo, timeout=2)
                    self.detected_codename = res_code2.stdout.strip()
            except Exception:
                self.detected_codename = "Unknown"
            
            self.detected_unlocked = "Unknown"
            self.detected_token = None

            # Fetch additional stats: Android version and Security patch level
            android_ver = "Unknown"
            patch_date = "Unknown"
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                res_ver = subprocess.run([adb_path, "-s", self.detected_serial, "shell", "getprop", "ro.build.version.release"], capture_output=True, text=True, startupinfo=startupinfo, timeout=2)
                android_ver = res_ver.stdout.strip()
                
                res_patch = subprocess.run([adb_path, "-s", self.detected_serial, "shell", "getprop", "ro.build.version.security_patch"], capture_output=True, text=True, startupinfo=startupinfo, timeout=2)
                patch_date = res_patch.stdout.strip()
            except Exception:
                pass

            # Render UI
            state_colored = f"<font color='#2ECC71'>ADB Mode ({self.detected_mode.upper()})</font>"
            self.lbl_device_mode.setText(f"● Device Status: {state_colored}")
            self.lbl_device_info.setText(f"Model: {self.detected_model} | Codename: {self.detected_codename} | Android: {android_ver} | Patch: {patch_date} | Serial: {self.detected_serial}")

        elif fastboot_connected:
            dev = fastboot_connected[0]
            self.detected_serial = dev["serial"]
            self.detected_mode = "fastboot"
            self.detected_model = "Bootloader Device"
            
            # Query fastboot variables
            product_val = "Unknown"
            unlocked_val = "Unknown"
            token_val = None
            
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                # Get product codename
                res_prod = subprocess.run([fastboot_path, "-s", self.detected_serial, "getvar", "product"], capture_output=True, text=True, startupinfo=startupinfo, timeout=2)
                for line in (res_prod.stdout + res_prod.stderr).splitlines():
                    if "product:" in line:
                        product_val = line.split("product:")[1].strip()
                
                # Get unlocked status
                res_unlock = subprocess.run([fastboot_path, "-s", self.detected_serial, "getvar", "unlocked"], capture_output=True, text=True, startupinfo=startupinfo, timeout=2)
                for line in (res_unlock.stdout + res_unlock.stderr).splitlines():
                    if "unlocked:" in line:
                        unlocked_val = line.split("unlocked:")[1].strip()

                # Get Xiaomi token
                res_tok1 = subprocess.run([fastboot_path, "-s", self.detected_serial, "oem", "get_token"], capture_output=True, text=True, startupinfo=startupinfo, timeout=2)
                tok_out = res_tok1.stdout + res_tok1.stderr
                token_match = re.search(r"token:(.*)", tok_out)
                if token_match:
                    token_val = token_match.group(1).strip()
                else:
                    res_tok2 = subprocess.run([fastboot_path, "-s", self.detected_serial, "getvar", "token"], capture_output=True, text=True, startupinfo=startupinfo, timeout=2)
                    for line in (res_tok2.stdout + res_tok2.stderr).splitlines():
                        if "token:" in line:
                            token_val = line.split("token:")[1].strip()

            except Exception:
                pass
            
            self.detected_codename = product_val
            self.detected_unlocked = unlocked_val
            self.detected_token = token_val

            # Render UI
            state_colored = f"<font color='#FFA500'>Fastboot Mode (Unlocked: {self.detected_unlocked})</font>"
            self.lbl_device_mode.setText(f"● Device Status: {state_colored}")
            self.lbl_device_info.setText(f"Codename: {self.detected_codename} | Token: {self.detected_token or 'None'} | Serial: {self.detected_serial}")

        else:
            self.detected_serial = None
            self.detected_mode = None
            self.detected_model = "Unknown"
            self.detected_codename = "Unknown"
            self.detected_unlocked = "Unknown"
            self.detected_token = None
            self.detected_manufacturer = "Unknown"

            self.lbl_device_mode.setText("● Device Status: Disconnected")
            self.lbl_device_mode.setStyleSheet("font-weight: bold; font-size: 14px; color: #E74C3C;")
            self.lbl_device_info.setText("Details: Plug in a device in ADB, Recovery, Sideload, or Fastboot mode.")

        # Check and display driver recommendation warnings dynamically
        if self.detected_mode:
            if "samsung" in self.detected_manufacturer and not self.downloader.get_samsung_driver_path():
                self.lbl_driver_alert.setText("⚠️ <b>Samsung device connected:</b> The Samsung USB Driver is not installed. Go to the <i>Setup & Drivers</i> tab and install it to ensure stable flashing and Odin compatibility.")
                self.lbl_driver_alert.setVisible(True)
            elif any(brand in self.detected_manufacturer for brand in ["realme", "oppo", "oneplus", "xiaomi"]) and not self.downloader.get_mtk_driver_path():
                self.lbl_driver_alert.setText(f"⚠️ <b>{self.detected_manufacturer.capitalize()} device detected:</b> If flashing fails or device is not recognized in Fastboot, go to the <i>Setup & Drivers</i> tab and install the <b>MediaTek VCOM</b> or <b>Google USB Driver</b>.")
                self.lbl_driver_alert.setVisible(True)
            else:
                self.lbl_driver_alert.setVisible(False)
        else:
            self.lbl_driver_alert.setVisible(False)

    # Execution launcher helper
    def launch_worker(self, action_type, params):
        self.txt_console.appendPlainText(f"\n--- Operation Started: {action_type.upper()} ---")
        worker = FlasherThread(action_type, params)
        worker.log_signal.connect(self.log)
        worker.finished_signal.connect(self.on_worker_finished)
        
        # Save reference
        self.active_worker = worker
        worker.start()

    def on_worker_finished(self, success, msg):
        self.log(msg)
        if success:
            self.log("OPERATION COMPLETED SUCCESSFULLY.")
        else:
            self.log("OPERATION FAILED.")
            QMessageBox.critical(self, "Execution Error", msg)
        self.log("-----------------------------------------")
        self.active_worker = None
        # Trigger an immediate scan update
        self.scan_device_status()

    # Xiaomi Login & Unlocking Action trigger handlers
    def open_mi_login_page(self):
        url = self.mi_session.get_login_url()
        import webbrowser
        webbrowser.open(url)
        self.log("Opening official Xiaomi Account Login page in your browser...")
        self.log("Log in, and when you see a blank page showing '\"R\":\"\",\"S\":\"OK\"', COPY the full URL from the browser's address bar and paste it below.")

    def run_mi_login(self):
        user = self.txt_mi_user.text().strip()
        pwd = self.txt_mi_pwd.text().strip()
        redirect_url = self.txt_mi_redirect.text().strip()
        
        if not user or not pwd or not redirect_url:
            QMessageBox.warning(self, "Input Error", "Please fill in Username, Password and Pasteur login Redirect URL.")
            return

        params = {
            "session": self.mi_session,
            "user": user,
            "pwd": pwd,
            "pasted_url": redirect_url
        }
        self.launch_worker("mi_login", params)

    def run_mi_logout(self):
        self.mi_session.logout()
        self.lbl_mi_status.setText("API Account Status: Logged Out")
        self.lbl_mi_status.setStyleSheet("font-weight: bold; color: #E74C3C;")
        self.txt_mi_redirect.clear()
        self.log("Logged out from Xiaomi Unlock Session.")

    def check_mi_notice(self):
        if not self.mi_session.uid:
            QMessageBox.warning(self, "Authentication Required", "Please log in to your Xiaomi account first.")
            return
        if self.detected_mode != "fastboot" or not self.detected_codename:
            QMessageBox.warning(self, "Device Required", "Xiaomi device must be connected in Fastboot mode.")
            return
            
        params = {
            "session": self.mi_session,
            "product": self.detected_codename
        }
        self.launch_worker("mi_check_notice", params)

    def execute_mi_unlock(self):
        if not self.mi_session.uid:
            QMessageBox.warning(self, "Authentication Required", "Please log in to your Xiaomi account first.")
            return
        if self.detected_mode != "fastboot":
            QMessageBox.warning(self, "Device Required", "Xiaomi device must be connected in Fastboot mode.")
            return
        if not self.detected_codename or not self.detected_token:
            QMessageBox.warning(self, "Device Variables Missing", "Could not fetch product codename or fastboot token. Ensure device drivers are installed.")
            return

        fastboot_path = self.downloader.get_fastboot_path()
        if not fastboot_path:
            QMessageBox.critical(self, "Platform Tools Missing", "Fastboot engine is not installed. Go to Setup tab and setup Platform Tools first.")
            return

        # Double confirmation dialog
        reply = QMessageBox.critical(
            self, 
            "PERMANENT DATA WIPE WARNING", 
            "WARNING: Unlocking the Bootloader will WIPE ALL USER DATA. Are you absolutely sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        params = {
            "session": self.mi_session,
            "fastboot_path": fastboot_path,
            "product": self.detected_codename,
            "token": self.detected_token,
            "serial": self.detected_serial
        }
        self.launch_worker("mi_unlock", params)

    # Fastboot flashing handlers
    def flash_fastboot_rom(self):
        rom_dir = self.txt_rom_path.text().strip()
        script = self.combo_scripts.currentText()
        if not rom_dir or not script:
            QMessageBox.warning(self, "Input Error", "Please select a valid ROM folder and flash script.")
            return

        fastboot_path = self.downloader.get_fastboot_path()
        if not fastboot_path:
            QMessageBox.critical(self, "Platform Tools Missing", "Fastboot engine is missing. Install Google Platform Tools from Setup.")
            return

        if self.detected_mode != "fastboot":
            QMessageBox.warning(self, "Device Required", "Device must be connected in Fastboot mode.")
            return

        reply = QMessageBox.question(
            self, 
            "ROM Flash Confirmation", 
            f"Are you sure you want to run {script} on this device? This will overwrite the firmware.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        script_path = os.path.join(rom_dir, script)
        params = {
            "script_path": script_path,
            "rom_dir": rom_dir,
            "fastboot_dir": os.path.dirname(fastboot_path)
        }
        self.launch_worker("flash_rom", params)

    def flash_partition_image(self):
        img_path = self.txt_img_path.text().strip()
        part = self.combo_part.currentText().strip()
        
        if not img_path or not part:
            QMessageBox.warning(self, "Input Error", "Please select an image file and target partition name.")
            return

        fastboot_path = self.downloader.get_fastboot_path()
        if not fastboot_path:
            QMessageBox.critical(self, "Platform Tools Missing", "Fastboot engine is missing. Install Google Platform Tools from Setup.")
            return

        if self.detected_mode != "fastboot":
            QMessageBox.warning(self, "Device Required", "Device must be connected in Fastboot mode.")
            return

        params = {
            "cmd": [fastboot_path, "-s", self.detected_serial, "flash", part, img_path]
        }
        self.launch_worker("fastboot_command", params)

    def boot_partition_image(self):
        img_path = self.txt_img_path.text().strip()
        if not img_path:
            QMessageBox.warning(self, "Input Error", "Please select an image file first.")
            return

        fastboot_path = self.downloader.get_fastboot_path()
        if not fastboot_path:
            QMessageBox.critical(self, "Platform Tools Missing", "Fastboot engine is missing.")
            return

        if self.detected_mode != "fastboot":
            QMessageBox.warning(self, "Device Required", "Device must be connected in Fastboot mode.")
            return

        params = {
            "cmd": [fastboot_path, "-s", self.detected_serial, "boot", img_path]
        }
        self.launch_worker("fastboot_command", params)

    # Custom Recovery handlers
    def flash_recovery_image(self):
        rec_path = self.txt_rec_path.text().strip()
        if not rec_path:
            QMessageBox.warning(self, "Input Error", "Please select a custom recovery image file.")
            return

        fastboot_path = self.downloader.get_fastboot_path()
        if not fastboot_path:
            QMessageBox.critical(self, "Platform Tools Missing", "Fastboot engine is missing.")
            return

        if self.detected_mode != "fastboot":
            QMessageBox.warning(self, "Device Required", "Device must be connected in Fastboot mode.")
            return

        params = {
            "cmd": [fastboot_path, "-s", self.detected_serial, "flash", "recovery", rec_path]
        }
        self.launch_worker("fastboot_command", params)

    def boot_recovery_image(self):
        rec_path = self.txt_rec_path.text().strip()
        if not rec_path:
            QMessageBox.warning(self, "Input Error", "Please select a custom recovery image file.")
            return

        fastboot_path = self.downloader.get_fastboot_path()
        if not fastboot_path:
            QMessageBox.critical(self, "Platform Tools Missing", "Fastboot engine is missing.")
            return

        if self.detected_mode != "fastboot":
            QMessageBox.warning(self, "Device Required", "Device must be connected in Fastboot mode.")
            return

        params = {
            "cmd": [fastboot_path, "-s", self.detected_serial, "boot", rec_path]
        }
        self.launch_worker("fastboot_command", params)

    # ADB Sideload custom ROM handler
    def execute_sideload(self):
        zip_path = self.txt_zip_path.text().strip()
        if not zip_path:
            QMessageBox.warning(self, "Input Error", "Please select a flashable ROM zip package.")
            return

        adb_path = self.runner.get_adb_path()
        if self.detected_mode != "sideload":
            QMessageBox.warning(self, "Device Sideload Required", "Please put your device in Sideload Mode in custom recovery first.")
            return

        params = {
            "cmd": [adb_path, "-s", self.detected_serial, "sideload", zip_path]
        }
        self.launch_worker("adb_command", params)

    # Advanced actions & format handlers
    def format_userdata(self):
        fastboot_path = self.downloader.get_fastboot_path()
        if self.detected_mode != "fastboot" or not fastboot_path:
            QMessageBox.warning(self, "Fastboot Required", "Connect device in Fastboot mode and set up Platform Tools.")
            return
            
        reply = QMessageBox.critical(self, "Data Wipe Alert", "This will WIPE all your phone photos, apps and files. Proceed?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No: return

        self.launch_worker("fastboot_command", {"cmd": [fastboot_path, "-s", self.detected_serial, "format", "userdata"]})

    def erase_userdata(self):
        fastboot_path = self.downloader.get_fastboot_path()
        if self.detected_mode != "fastboot" or not fastboot_path:
            QMessageBox.warning(self, "Fastboot Required", "Connect device in Fastboot mode.")
            return
        self.launch_worker("fastboot_command", {"cmd": [fastboot_path, "-s", self.detected_serial, "erase", "userdata"]})

    def erase_cache(self):
        fastboot_path = self.downloader.get_fastboot_path()
        if self.detected_mode != "fastboot" or not fastboot_path:
            QMessageBox.warning(self, "Fastboot Required", "Connect device in Fastboot mode.")
            return
        self.launch_worker("fastboot_command", {"cmd": [fastboot_path, "-s", self.detected_serial, "erase", "cache"]})

    def generic_oem_unlock(self):
        fastboot_path = self.downloader.get_fastboot_path()
        if self.detected_mode != "fastboot" or not fastboot_path:
            QMessageBox.warning(self, "Fastboot Required", "Connect device in Fastboot mode.")
            return
        self.launch_worker("fastboot_command", {"cmd": [fastboot_path, "-s", self.detected_serial, "oem", "unlock"]})

    def generic_flashing_unlock(self):
        fastboot_path = self.downloader.get_fastboot_path()
        if self.detected_mode != "fastboot" or not fastboot_path:
            QMessageBox.warning(self, "Fastboot Required", "Connect device in Fastboot mode.")
            return
        self.launch_worker("fastboot_command", {"cmd": [fastboot_path, "-s", self.detected_serial, "flashing", "unlock"]})

    def generic_flashing_lock(self):
        fastboot_path = self.downloader.get_fastboot_path()
        if self.detected_mode != "fastboot" or not fastboot_path:
            QMessageBox.warning(self, "Fastboot Required", "Connect device in Fastboot mode.")
            return
        self.launch_worker("fastboot_command", {"cmd": [fastboot_path, "-s", self.detected_serial, "flashing", "lock"]})

    def ensure_authorized_and_run(self, action_callback):
        if self.detected_mode == "unauthorized":
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("USB Debugging Unauthorized")
            msg_box.setText("⚠️ <b>Device Unauthorized</b><br><br>"
                             "Please check your phone's screen. A popup dialog asking to <b>'Allow USB debugging?'</b> should appear.<br><br>"
                             "1. Check the box <i>'Always allow from this computer'</i>.<br>"
                             "2. Tap <b>'Allow'</b> or <b>'OK'</b>.<br><br>"
                             "<i>This tool will automatically execute your reboot request as soon as you authorize it...</i>")
            msg_box.setStandardButtons(QMessageBox.Cancel)
            
            self.auth_attempts = 0
            self.auth_timer = QTimer(self)
            
            def check_status():
                self.auth_attempts += 1
                self.scan_device_status()
                if self.detected_mode == "device":
                    self.auth_timer.stop()
                    msg_box.accept()
                    action_callback()
                elif self.auth_attempts >= 20: # 20 seconds timeout
                    self.auth_timer.stop()
                    msg_box.reject()
                    QMessageBox.warning(self, "Authorization Timeout", "Failed to authorize USB debugging in time. Please try again.")
            
            self.auth_timer.timeout.connect(check_status)
            self.auth_timer.start(1000)
            
            res = msg_box.exec_()
            if res == QMessageBox.Cancel:
                self.auth_timer.stop()
        else:
            action_callback()

    # Reboot commands
    def reboot_system(self):
        def do_reboot():
            adb_path = self.runner.get_adb_path()
            fastboot_path = self.downloader.get_fastboot_path()
            if self.detected_mode == "fastboot" and fastboot_path:
                self.launch_worker("fastboot_command", {"cmd": [fastboot_path, "-s", self.detected_serial, "reboot"]})
            elif self.detected_mode and self.detected_mode != "fastboot":
                self.launch_worker("adb_command", {"cmd": [adb_path, "-s", self.detected_serial, "reboot"]})
            else:
                QMessageBox.warning(self, "No Device Connected", "Connect a device first.")
        self.ensure_authorized_and_run(do_reboot)

    def reboot_bootloader(self):
        def do_reboot():
            adb_path = self.runner.get_adb_path()
            fastboot_path = self.downloader.get_fastboot_path()
            if self.detected_mode == "fastboot" and fastboot_path:
                self.launch_worker("fastboot_command", {"cmd": [fastboot_path, "-s", self.detected_serial, "reboot-bootloader"]})
            elif self.detected_mode and self.detected_mode != "fastboot":
                self.launch_worker("adb_command", {"cmd": [adb_path, "-s", self.detected_serial, "reboot", "bootloader"]})
            else:
                QMessageBox.warning(self, "No Device Connected", "Connect a device first.")
        self.ensure_authorized_and_run(do_reboot)

    def reboot_recovery(self):
        def do_reboot():
            adb_path = self.runner.get_adb_path()
            fastboot_path = self.downloader.get_fastboot_path()
            if self.detected_mode == "fastboot" and fastboot_path:
                self.launch_worker("fastboot_command", {"cmd": [fastboot_path, "-s", self.detected_serial, "reboot", "recovery"]})
            elif self.detected_mode and self.detected_mode != "fastboot":
                self.launch_worker("adb_command", {"cmd": [adb_path, "-s", self.detected_serial, "reboot", "recovery"]})
            else:
                QMessageBox.warning(self, "No Device Connected", "Connect a device first.")
        self.ensure_authorized_and_run(do_reboot)

    def reboot_edl(self):
        def do_reboot():
            adb_path = self.runner.get_adb_path()
            fastboot_path = self.downloader.get_fastboot_path()
            if self.detected_mode == "fastboot" and fastboot_path:
                self.launch_worker("fastboot_command", {"cmd": [fastboot_path, "-s", self.detected_serial, "oem", "edl"]})
            elif self.detected_mode and self.detected_mode != "fastboot":
                self.launch_worker("adb_command", {"cmd": [adb_path, "-s", self.detected_serial, "reboot", "edl"]})
            else:
                QMessageBox.warning(self, "No Device Connected", "Connect a device first.")
        self.ensure_authorized_and_run(do_reboot)

    def reboot_download(self):
        def do_reboot():
            adb_path = self.runner.get_adb_path()
            if self.detected_mode and self.detected_mode != "fastboot":
                self.launch_worker("adb_command", {"cmd": [adb_path, "-s", self.detected_serial, "reboot", "download"]})
            else:
                QMessageBox.warning(self, "ADB Device Required", "Reboot to Download (Odin) mode requires an active ADB connection.")
        self.ensure_authorized_and_run(do_reboot)

    def erase_frp_lock(self):
        if self.detected_mode != "fastboot":
            QMessageBox.warning(self, "Fastboot Required", "FRP Lock erase must be performed in Fastboot Mode. Please reboot your device to bootloader.")
            return

        fastboot_path = self.downloader.get_fastboot_path()
        if not fastboot_path:
            QMessageBox.critical(self, "Platform Tools Missing", "Fastboot engine is missing. Install Google Platform Tools from Setup.")
            return

        reply = QMessageBox.critical(
            self,
            "Erase FRP Lock",
            "WARNING: You are about to erase the FRP/Google lock partitions on this device. Proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        params = {
            "fastboot_path": fastboot_path,
            "serial": self.detected_serial
        }
        self.launch_worker("erase_frp", params)

    def browse_backup_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select IMEI Backup Folder")
        if dir_path:
            self.txt_backup_dir.setText(dir_path)

    def run_imei_backup(self):
        if not self.detected_mode or self.detected_mode == "fastboot":
            QMessageBox.warning(self, "ADB Root/TWRP Required", "Please connect your device in ADB Mode (Rooted) or booted into TWRP Recovery mode first.")
            return
            
        adb_path = self.runner.get_adb_path()
        backup_dir = os.path.join(self.downloader.base_dir, "backups", f"imei_{self.detected_serial or 'device'}_{int(time.time())}")
        
        # We try to back up both Qualcomm and MTK EFS/NVRAM partitions. The worker will automatically skip any partitions that aren't present.
        partitions = ["modemst1", "modemst2", "fsg", "fsc", "nvram", "nvdata", "proinfo"]
        
        params = {
            "adb_path": adb_path,
            "serial": self.detected_serial,
            "partitions": partitions,
            "backup_dir": backup_dir
        }
        self.launch_worker("backup_partitions", params)

    def run_imei_restore(self):
        backup_dir = self.txt_backup_dir.text().strip()
        if not backup_dir or not os.path.exists(backup_dir):
            QMessageBox.warning(self, "Invalid Backup Folder", "Please select a valid folder containing the backup image files.")
            return

        if not self.detected_mode:
            QMessageBox.warning(self, "Device Required", "Please connect your device in Fastboot or TWRP Recovery mode.")
            return

        # Scan folder for available images
        available_files = os.listdir(backup_dir)
        partitions_to_restore = []
        for file in available_files:
            if file.endswith(".img"):
                part_name = file[:-4] # strip '.img'
                partitions_to_restore.append((part_name, file))

        if not partitions_to_restore:
            QMessageBox.warning(self, "No Backups Found", "No partition image files (.img) found in the selected folder.")
            return

        reply = QMessageBox.question(
            self, 
            "Restore Partitions", 
            f"Are you sure you want to restore partitions: {', '.join([p[0] for p in partitions_to_restore])} to your device? This will overwrite existing radio/IMEI partition data.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        params = {
            "backup_dir": backup_dir,
            "serial": self.detected_serial,
            "partitions": partitions_to_restore
        }

        if self.detected_mode == "fastboot":
            fastboot_path = self.downloader.get_fastboot_path()
            if not fastboot_path:
                QMessageBox.critical(self, "Platform Tools Missing", "Fastboot engine is missing. Install Google Platform Tools from Setup.")
                return
            params["mode"] = "fastboot"
            params["fastboot_path"] = fastboot_path
        else:
            params["mode"] = "adb"
            params["adb_path"] = self.runner.get_adb_path()

        self.launch_worker("restore_partitions", params)

    def run_efs_wipe(self):
        if self.detected_mode != "fastboot":
            QMessageBox.warning(self, "Fastboot Required", "Erase EFS can only be performed in Fastboot Mode. Please reboot your device to bootloader.")
            return

        fastboot_path = self.downloader.get_fastboot_path()
        if not fastboot_path:
            QMessageBox.critical(self, "Platform Tools Missing", "Fastboot engine is missing. Install Google Platform Tools from Setup.")
            return

        reply = QMessageBox.critical(
            self,
            "Erase EFS (Fix No Network)",
            "WARNING: Erasing EFS partitions (modemst1, modemst2) will temporarily clear your baseband calibration. Unlocked devices will rebuild this on next boot. Proceed at your own risk?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        params = {
            "fastboot_path": fastboot_path,
            "serial": self.detected_serial
        }
        self.launch_worker("wipe_efs", params)

    def create_guides_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_lbl = QLabel("Step-by-Step Flashing & Unlocking Guides")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #66FCF1;")
        layout.addWidget(title_lbl)

        # Dropdown selection for guides
        hdr_layout = QHBoxLayout()
        hdr_layout.addWidget(QLabel("Select Topic Guide:"))
        
        self.combo_guides = QComboBox()
        self.combo_guides.addItems([
            "Xiaomi/Mi Bootloader Unlock",
            "Realme/Oppo Bootloader Unlock",
            "Samsung Bootloader Unlock",
            "Generic Bootloader Unlock (OnePlus, Pixel, Moto etc.)",
            "How to Flash Fastboot ROM (Stock Firmware)",
            "How to Install Custom Recovery (TWRP/OrangeFox)",
            "How to Sideload Custom ROM (adb sideload)",
            "Baseband & IMEI Backup/Restore (EFS & NVRAM)"
        ])
        self.combo_guides.setMinimumHeight(35)
        self.combo_guides.currentIndexChanged.connect(self.display_guide_content)
        hdr_layout.addWidget(self.combo_guides, 1)
        layout.addLayout(hdr_layout)

        # Guide Content Area
        self.txt_guide_content = QTextBrowser()
        self.txt_guide_content.setStyleSheet("background-color: #171B26; color: #E2E8F0; border: 1px solid #1F2833; padding: 15px; font-size: 13px; line-height: 1.6;")
        self.txt_guide_content.setOpenExternalLinks(True)
        layout.addWidget(self.txt_guide_content)

        self.display_guide_content(0) # Show first guide by default
        self.sub_tabs.addTab(tab, "Guides & Help")

    def display_guide_content(self, index):
        guides = [
            # Xiaomi
            "<h2>Xiaomi/Mi Bootloader Unlock Guide</h2>"
            "<p>Xiaomi devices require account verification and authorization to unlock the bootloader. Unlocking will <b>WIPE ALL USER DATA</b>.</p>"
            "<h3>Steps:</h3>"
            "<ol>"
            "  <li>On your phone: Go to <b>Settings -> About Phone</b> and tap <b>'MIUI/OS Version'</b> 7 times to enable Developer Options.</li>"
            "  <li>Go to <b>Settings -> Additional Settings -> Developer Options</b>. Enable <b>OEM Unlocking</b> and <b>USB Debugging</b>.</li>"
            "  <li>Tap <b>Mi Unlock Status</b> and click <b>'Add account and device'</b> (requires mobile data, turn off Wi-Fi).</li>"
            "  <li>Turn off your phone, then hold <b>Volume Down + Power</b> keys until you see the 'FASTBOOT' screen, and connect it to PC.</li>"
            "  <li>On the <b>Xiaomi Bootloader Unlock</b> tab: Click <i>'Open Official Login Page'</i> to authenticate, login, and copy/paste the redirected blank URL back to log into the API.</li>"
            "  <li>Click <b>'UNLOCK BOOTLOADER'</b> to flash signature and unlock. If Xiaomi returns a wait timer (e.g. 168 hours), you must repeat this step after that duration.</li>"
            "</ol>",

            # Realme
            "<h2>Realme/Oppo Bootloader Unlock Guide</h2>"
            "<p>Realme/Oppo devices require a deep testing authorization tool (APK) before allowing fastboot unlock. Unlocking will <b>WIPE ALL DATA</b>.</p>"
            "<h3>Steps:</h3>"
            "<ol>"
            "  <li>Download the official <b>'In-Depth Test APK'</b> (Deep Testing Tool) matching your device model and Realme UI version.</li>"
            "  <li>Install the app, open it, and tap <b>'Apply for In-depth test'</b>. It will take from 1 to 24 hours for Realme servers to approve your application.</li>"
            "  <li>Once approved, open the app, tap <b>'Start In-depth test'</b>. The device will reboot automatically into Fastboot mode.</li>"
            "  <li>Connect the phone to PC. The status bar at the top of our tool should change to <b>'Fastboot Mode'</b>.</li>"
            "  <li>If drivers are missing, download the <b>MediaTek</b> or <b>Google USB Driver</b> from the Setup tab.</li>"
            "  <li>Go to the <b>Advanced Repairs</b> tab of our tool, and click <b>'OEM Unlock (flashing unlock)'</b>.</li>"
            "  <li>On your phone screen, use Volume keys to select <b>'UNLOCK THE BOOTLOADER'</b> and press the Power key to confirm.</li>"
            "</ol>",

            # Samsung
            "<h2>Samsung Bootloader Unlock Guide</h2>"
            "<p>Samsung devices do not use standard fastboot. Bootloader unlocking is done via the Download Mode. Unlocking will <b>WIPE ALL DATA</b>.</p>"
            "<h3>Steps:</h3>"
            "<ol>"
            "  <li>On the phone: Go to <b>Settings -> About Phone -> Software Info</b> and tap <b>Build Number</b> 7 times.</li>"
            "  <li>Go back to settings, open <b>Developer Options</b>, and toggle <b>OEM Unlocking</b> to ON. (If you don't see it, connect to internet and wait a few minutes).</li>"
            "  <li>Power off your device completely.</li>"
            "  <li>Hold <b>Volume Up + Volume Down</b> keys together, and plug in the USB cable connected to PC. The screen will turn turquoise (Warning screen).</li>"
            "  <li>Long-press <b>Volume Up</b> to enter the Bootloader Unlock mode.</li>"
            "  <li>Press <b>Volume Up</b> once to confirm the unlock. The phone will format and reboot.</li>"
            "  <li><i>Note: To check if unlocked, boot to Download mode again: it should show 'OEM LOCK: OFF' or 'U' (Unlocked) in the text header.</i></li>"
            "</ol>",

            # Generic
            "<h2>Generic Bootloader Unlock Guide (Pixel, OnePlus, Motorola etc.)</h2>"
            "<p>Most stock/standard Android devices can be unlocked using standard fastboot protocol commands. Unlocking will <b>WIPE ALL DATA</b>.</p>"
            "<h3>Steps:</h3>"
            "<ol>"
            "  <li>Enable <b>Developer Options</b> by tapping Build Number 7 times.</li>"
            "  <li>Enable <b>USB Debugging</b> and <b>OEM Unlocking</b> inside Developer Options.</li>"
            "  <li>Run `adb reboot bootloader` or click <b>Reboot Bootloader</b> in our tool status panel.</li>"
            "  <li>Once in Fastboot mode, go to the <b>Advanced Repairs</b> tab of our tool.</li>"
            "  <li>Try clicking <b>'OEM Unlock (flashing unlock)'</b> first. If your device is older, try <b>'OEM Unlock (oem unlock)'</b>.</li>"
            "  <li>Confirm the prompt on the device screen using the Volume and Power keys if prompted.</li>"
            "</ol>",

            # Fastboot ROM
            "<h2>How to Flash Fastboot ROM (Stock Firmware)</h2>"
            "<p>Fastboot ROMs are official stock firmware packages used to restore devices from bootloops or software bricking.</p>"
            "<h3>Steps:</h3>"
            "<ol>"
            "  <li>Download the official Fastboot ROM for your specific device model and extract the package (.tgz/.zip) to a folder on your PC.</li>"
            "  <li>Put your phone in Fastboot mode and connect it. Ensure the status bar shows <b>'Fastboot Mode'</b>.</li>"
            "  <li>On the <b>Fastboot Flasher</b> tab of our tool, click <b>'Browse Folder'</b> and select the extracted ROM directory.</li>"
            "  <li>Our tool will scan the directory and list available script files (e.g., <i>'flash_all.bat'</i>, <i>'flash_all_except_storage.bat'</i>).</li>"
            "  <li>Select the script. (Choose <i>'flash_all.bat'</i> for a clean restore. Avoid lock scripts unless you want to re-lock the bootloader).</li>"
            "  <li>Click <b>'FLASH FASTBOOT ROM'</b>. Do not disconnect the phone until the logs console says operation completed.</li>"
            "</ol>",

            # TWRP
            "<h2>How to Install Custom Recovery (TWRP / OrangeFox)</h2>"
            "<p>A custom recovery is required to flash custom ROMs (like LineageOS) and root packages.</p>"
            "<h3>Steps:</h3>"
            "<ol>"
            "  <li>Download the correct custom recovery `.img` file matching your specific device codename.</li>"
            "  <li>Put the phone in Fastboot mode and connect to PC.</li>"
            "  <li>On the <b>Recovery & Sideload</b> tab of our tool, click <b>'Browse Image'</b> and select the recovery `.img` file.</li>"
            "  <li>Click <b>'Flash Custom Recovery'</b> to flash it permanently (for devices with a dedicated recovery partition).</li>"
            "  <li>If your device does not have a recovery partition (A/B layout devices), click <b>'Boot Custom Recovery (Test Mode)'</b> to temporarily boot into recovery, and then install it permanently from TWRP menus.</li>"
            "</ol>",

            # Sideload
            "<h2>How to Flash Custom ROM via ADB Sideload</h2>"
            "<p>ADB Sideload is the safest and cleanest method to install custom firmware zips directly from recovery mode.</p>"
            "<h3>Steps:</h3>"
            "<ol>"
            "  <li>Reboot your phone into your custom recovery (TWRP/OrangeFox).</li>"
            "  <li>Perform a data format: Go to <b>Wipe -> Format Data</b>, type 'yes' and confirm. (Required if coming from Stock ROM to avoid encryption issues).</li>"
            "  <li>Enable Sideload: Go to <b>Advanced -> ADB Sideload</b> (or <b>Wipe -> Advanced Wipe -> Sideload</b>) and swipe to start.</li>"
            "  <li>Connect the phone to PC. The status bar at the top of our tool should detect <b>'Sideload'</b> mode.</li>"
            "  <li>In the <b>Recovery & Sideload</b> tab of our tool, click <b>'Browse Zip'</b> and select your custom ROM `.zip` file.</li>"
            "  <li>Click <b>'START ADB SIDELOAD FLASH'</b>. The tool will stream the zip file to your device, and the recovery will flash it automatically.</li>"
            "  <li>Once done, reboot the device in TWRP menu.</li>"
            "</ol>",

            # EFS / IMEI
            "<h2>Baseband & IMEI Backup / Restore Guide (EFS & NVRAM)</h2>"
            "<p>Your IMEI, MAC addresses, and network calibration values are stored in specific partitions. Qualcomm chips use <b>EFS (modemst1, modemst2, fsg, fsc)</b>, while MediaTek chips use <b>NVRAM, NVDATA, PROINFO</b>. If these partitions are corrupted or wiped, you will see 'No Service' or 'Null IMEI'. This guide explains how to back up and restore them.</p>"
            "<h3>To Back Up (Root/TWRP Required):</h3>"
            "<ol>"
            "  <li>You must connect your device with root privileges. The easiest way is booting your phone into a <b>Custom Recovery (TWRP/OrangeFox)</b>, which runs ADB as root automatically.</li>"
            "  <li>Alternatively, connect your phone in normal Android mode with <b>USB Debugging</b> enabled and ensure it has <b>Root access</b> (Magisk/KernelSU).</li>"
            "  <li>Under the <b>Advanced Repairs</b> tab -> click <b>'Backup IMEI / EFS'</b>.</li>"
            "  <li>The tool will dump the partition images, transfer them to your PC, and store them in: <i>[BaseDir]/backups/imei_[device_serial]_[timestamp]/</i>.</li>"
            "</ol>"
            "<h3>To Restore (Fastboot or Recovery Mode):</h3>"
            "<ol>"
            "  <li>Under the <b>Advanced Repairs</b> tab, click <b>'Browse Backup Folder'</b> and select the folder containing your `.img` backup files.</li>"
            "  <li><b>Option A (Fastboot Mode - Recommended):</b> Put your phone in Fastboot mode, connect it, and click <b>'Restore IMEI / EFS'</b>. The tool will flash each image back to its partition.</li>"
            "  <li><b>Option B (TWRP Recovery Mode):</b> Connect your phone in TWRP mode and click <b>'Restore IMEI / EFS'</b>. The tool will write the files back directly using `dd`.</li>"
            "</ol>"
            "<h3>Fix 'No Service' (Erase EFS):</h3>"
            "<ol>"
            "  <li>If your baseband/signal is lost but the hardware is intact, put your phone in Fastboot mode and click <b>'Wipe EFS (Fix No Network)'</b>.</li>"
            "  <li>This erases the temporary modem cache. Upon reboot, the modem will automatically rebuild its parameters from the golden backup (fsg/proinfo) to restore service.</li>"
            "</ol>"
        ]
        if 0 <= index < len(guides):
            self.txt_guide_content.setHtml(guides[index])

