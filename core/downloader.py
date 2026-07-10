import os
import sys
import zipfile
import subprocess
import requests
import shutil

class EngineDownloader:
    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.base_dir = base_dir
        
        self.engines_dir = os.path.join(self.base_dir, "engines")
        os.makedirs(self.engines_dir, exist_ok=True)
        
        # Fallback hardcoded URLs in case GitHub API fails
        self.scrcpy_fallback_url = "https://github.com/Genymobile/scrcpy/releases/download/v2.4/scrcpy-win64-v2.4.zip"
        self.uxplay_fallback_url = "https://github.com/leapbtw/uxplay-windows/releases/download/1.72.1-3/uxplay-windows-installer-v1.72.1-3.exe"
        self.bonjour_url = "https://github.com/leapbtw/uxplay-windows/releases/download/1.72.1-3/Bonjour64.msi"
        self.usb_driver_url = "https://dl.google.com/android/repository/usb_driver_r13-windows.zip"

    def get_scrcpy_path(self):
        """Returns the path to scrcpy.exe if installed, otherwise None."""
        scrcpy_dir = os.path.join(self.engines_dir, "scrcpy")
        if os.path.exists(scrcpy_dir):
            for root, dirs, files in os.walk(scrcpy_dir):
                if "scrcpy.exe" in files:
                    return os.path.join(root, "scrcpy.exe")
        return None

    def get_uxplay_path(self):
        """Checks first in the engines folder recursively, then typical installation directories."""
        # Check portable folder
        uxplay_dir = os.path.join(self.engines_dir, "uxplay")
        if os.path.exists(uxplay_dir):
            for root, dirs, files in os.walk(uxplay_dir):
                for f in ["uxplay.exe", "uxplay-windows.exe"]:
                    if f in files:
                        return os.path.join(root, f)
        
        # Check system installed paths
        paths = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "uxplay-windows", "uxplay.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "uxplay-windows", "uxplay.exe"),
            os.path.join(os.environ.get("LocalAppData", ""), "Programs", "uxplay-windows", "uxplay.exe")
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None

    def is_bonjour_installed(self):
        """Checks if Bonjour is installed on the system."""
        # Check system directory or registry
        sys_dir = os.environ.get("SystemRoot", "C:\\Windows")
        bonjour_path = os.path.join(sys_dir, "System32", "dnssd.dll")
        if os.path.exists(bonjour_path):
            return True
        # Check Program Files
        prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        bonjour_dir = os.path.join(prog_files, "Bonjour")
        if os.path.exists(bonjour_dir) and len(os.listdir(bonjour_dir)) > 0:
            return True
        return False

    def download_file(self, url, dest_path, progress_callback=None):
        """Downloads a file with progress callback reporting (percent, speed_str)."""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            response = requests.get(url, stream=True, headers=headers, timeout=30)
            response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Failed to initiate download from {url}: {e}")

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        progress_callback(percent)
        return dest_path

    def setup_scrcpy(self, progress_callback=None):
        """Downloads and extracts scrcpy."""
        zip_path = os.path.join(self.engines_dir, "scrcpy.zip")
        scrcpy_dir = os.path.join(self.engines_dir, "scrcpy")
        
        # Try to find latest release URL via GitHub API
        url = self.scrcpy_fallback_url
        try:
            r = requests.get("https://api.github.com/repos/Genymobile/scrcpy/releases/latest", timeout=5)
            if r.status_code == 200:
                assets = r.json().get("assets", [])
                for asset in assets:
                    name = asset.get("name", "")
                    if "win64" in name and name.endswith(".zip"):
                        url = asset.get("browser_download_url")
                        break
        except Exception:
            pass # Fall back to hardcoded URL

        if progress_callback:
            progress_callback(5, "Downloading Android Engine (scrcpy)...")
            
        def sub_cb(percent):
            if progress_callback:
                # Scale 5% to 85%
                scaled = 5 + int(percent * 0.8)
                progress_callback(scaled, f"Downloading: {percent}%")

        try:
            self.download_file(url, zip_path, sub_cb)
            if progress_callback:
                progress_callback(90, "Extracting files...")
            
            # Extract ZIP
            if os.path.exists(scrcpy_dir):
                shutil.rmtree(scrcpy_dir)
            os.makedirs(scrcpy_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(scrcpy_dir)
            
            # Clean up zip
            os.remove(zip_path)
            
            if progress_callback:
                progress_callback(100, "Android Engine ready!")
            return True
        except Exception as e:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise RuntimeError(f"Error setting up scrcpy: {e}")

    def setup_uxplay(self, progress_callback=None):
        """Downloads and sets up uxplay (tries portable zip first, then runs installer silently)."""
        url = None
        is_zip = False
        try:
            r = requests.get("https://api.github.com/repos/leapbtw/uxplay-windows/releases", timeout=5)
            if r.status_code == 200:
                releases = r.json()
                for rel in releases:
                    assets = rel.get("assets", [])
                    # Try to find portable zip asset
                    for asset in assets:
                        name = asset.get("name", "")
                        if name.endswith(".zip") and "arm64" not in name.lower() and "untested" not in name.lower():
                            url = asset.get("browser_download_url")
                            is_zip = True
                            break
                    if url:
                        break
                    
                    # Try to find exe installer
                    for asset in assets:
                        name = asset.get("name", "")
                        if name.endswith(".exe") and "arm64" not in name.lower():
                            url = asset.get("browser_download_url")
                            is_zip = False
                            break
                    if url:
                        break
        except Exception:
            pass

        if not url:
            url = self.uxplay_fallback_url
            is_zip = False

        if progress_callback:
            progress_callback(5, "Downloading iOS Engine (uxplay)...")
            
        temp_file = os.path.join(self.engines_dir, "uxplay_temp.zip" if is_zip else "uxplay_installer.exe")
        uxplay_dir = os.path.join(self.engines_dir, "uxplay")

        def sub_cb(percent):
            if progress_callback:
                scaled = 5 + int(percent * 0.75)
                progress_callback(scaled, f"Downloading: {percent}%")

        try:
            self.download_file(url, temp_file, sub_cb)
            if progress_callback:
                progress_callback(85, "Extracting/Installing iOS Engine...")

            if is_zip:
                # Extract portable zip
                if os.path.exists(uxplay_dir):
                    shutil.rmtree(uxplay_dir)
                os.makedirs(uxplay_dir, exist_ok=True)
                
                with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                    zip_ref.extractall(uxplay_dir)
            else:
                # Run Inno Setup installer silently
                process = subprocess.Popen([temp_file, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"], 
                                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.communicate()

            # Clean up downloaded temp file
            try:
                os.remove(temp_file)
            except Exception:
                pass

            if progress_callback:
                progress_callback(100, "iOS Engine ready!")
            return True
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise RuntimeError(f"Error setting up uxplay: {e}")

    def setup_bonjour(self, progress_callback=None):
        """Downloads and runs the Bonjour service MSI silently."""
        msi_path = os.path.join(self.engines_dir, "Bonjour64.msi")
        
        if progress_callback:
            progress_callback(5, "Downloading Bonjour Service (mDNS Discovery)...")
            
        def sub_cb(percent):
            if progress_callback:
                scaled = 5 + int(percent * 0.75)
                progress_callback(scaled, f"Downloading Bonjour: {percent}%")

        try:
            self.download_file(self.bonjour_url, msi_path, sub_cb)
            if progress_callback:
                progress_callback(85, "Installing Bonjour... (Accept Admin privilege prompt)")

            # Run MSI installer silently
            process = subprocess.Popen(["msiexec", "/i", msi_path, "/quiet", "/qn", "/norestart"], 
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.communicate()

            # Clean up MSI
            try:
                os.remove(msi_path)
            except Exception:
                pass

            if progress_callback:
                progress_callback(100, "Bonjour Service installed!")
            return True
        except Exception as e:
            if os.path.exists(msi_path):
                os.remove(msi_path)
            raise RuntimeError(f"Error setting up Bonjour: {e}")

    def get_bonjour_guid(self):
        """Queries the registry to find Bonjour's Product GUID."""
        try:
            import winreg
        except ImportError:
            return None
        
        paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        for path in paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    sub_key_name = winreg.EnumKey(key, i)
                    try:
                        sub_key = winreg.OpenKey(key, f"{path}\\{sub_key_name}")
                        display_name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                        if "bonjour" in display_name.lower():
                            if sub_key_name.startswith("{") and sub_key_name.endswith("}"):
                                return sub_key_name
                    except Exception:
                        pass
            except Exception:
                pass
        return None

    def uninstall_scrcpy(self, progress_callback=None):
        """Uninstalls Android mirroring engine (deletes the portable folder)."""
        scrcpy_dir = os.path.join(self.engines_dir, "scrcpy")
        if progress_callback:
            progress_callback(20, "Stopping active ADB servers...")
        
        # Kill adb first so files aren't locked
        try:
            adb_exe = self.get_scrcpy_path()
            if adb_exe:
                adb_dir = os.path.dirname(adb_exe)
                subprocess.run([os.path.join(adb_dir, "adb.exe"), "kill-server"], 
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception:
            pass

        if progress_callback:
            progress_callback(50, "Deleting scrcpy engine files...")

        try:
            if os.path.exists(scrcpy_dir):
                shutil.rmtree(scrcpy_dir)
            if progress_callback:
                progress_callback(100, "Android Engine uninstalled!")
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete Android engine: {e}")

    def uninstall_uxplay(self, progress_callback=None):
        """Uninstalls iOS mirroring engine (runs uninstaller silently and cleans directory)."""
        uxplay_exe = self.get_uxplay_path()
        if not uxplay_exe:
            if progress_callback:
                progress_callback(100, "iOS Engine not found.")
            return True

        uxplay_dir = os.path.dirname(uxplay_exe)
        uninstaller = os.path.join(uxplay_dir, "unins000.exe")
        
        try:
            if os.path.exists(uninstaller):
                if progress_callback:
                    progress_callback(30, "Running silent uninstaller... (Accept prompt if shown)")
                # Run Inno uninstaller silently
                process = subprocess.Popen([uninstaller, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"], 
                                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.communicate()
            
            # Additional cleanup if folder remains
            if progress_callback:
                progress_callback(70, "Cleaning up remaining files...")
                
            if os.path.exists(uxplay_dir):
                try:
                    shutil.rmtree(uxplay_dir)
                except Exception:
                    pass

            if progress_callback:
                progress_callback(100, "iOS Engine uninstalled successfully!")
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to uninstall iOS engine: {e}")

    def uninstall_bonjour(self, progress_callback=None):
        """Uninstalls Bonjour Service via registry search and MSIEXEC."""
        guid = self.get_bonjour_guid()
        
        try:
            if progress_callback:
                progress_callback(20, "Stopping Bonjour service...")
            # Direct service stop and delete
            subprocess.run(["sc", "stop", "Bonjour Service"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["sc", "delete", "Bonjour Service"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if guid:
                if progress_callback:
                    progress_callback(50, f"Uninstalling Product GUID {guid} silently...")
                # Run MSIEXEC uninstall silently
                process = subprocess.Popen(["msiexec", "/x", guid, "/quiet", "/qn", "/norestart"], 
                                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.communicate()

            # Clean remaining program folders
            if progress_callback:
                progress_callback(80, "Cleaning remaining files...")
                
            prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            prog_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            
            for base in [prog_files, prog_files_x86]:
                b_dir = os.path.join(base, "Bonjour")
                if os.path.exists(b_dir):
                    try:
                        shutil.rmtree(b_dir)
                    except Exception:
                        pass

            if progress_callback:
                progress_callback(100, "Bonjour Service uninstalled!")
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to uninstall Bonjour: {e}")

    def get_usb_driver_path(self):
        """Checks if the extracted USB driver files are present."""
        driver_dir = os.path.join(self.engines_dir, "usb_driver")
        if os.path.exists(driver_dir):
            for root, dirs, files in os.walk(driver_dir):
                if "android_winusb.inf" in files:
                    return os.path.join(root, "android_winusb.inf")
        return None

    def setup_usb_driver(self, progress_callback=None):
        """Downloads, extracts and registers the Google Universal ADB USB Driver."""
        zip_path = os.path.join(self.engines_dir, "usb_driver.zip")
        driver_dir = os.path.join(self.engines_dir, "usb_driver")
        
        if progress_callback:
            progress_callback(5, "Downloading Google USB Driver...")
            
        def sub_cb(percent):
            if progress_callback:
                scaled = 5 + int(percent * 0.7)
                progress_callback(scaled, f"Downloading: {percent}%")

        try:
            self.download_file(self.usb_driver_url, zip_path, sub_cb)
            if progress_callback:
                progress_callback(80, "Extracting driver packages...")
            
            # Extract ZIP
            if os.path.exists(driver_dir):
                shutil.rmtree(driver_dir)
            os.makedirs(driver_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(driver_dir)
            
            os.remove(zip_path)
            
            if progress_callback:
                progress_callback(90, "Registering driver (Accept Admin UAC prompt)...")
            
            # Use pnputil silently with admin prompt (using runas ShellExecuteW)
            inf_path = os.path.join(driver_dir, "usb_driver", "android_winusb.inf")
            if not os.path.exists(inf_path):
                # Check alternative paths
                for root, dirs, files in os.walk(driver_dir):
                    if "android_winusb.inf" in files:
                        inf_path = os.path.join(root, "android_winusb.inf")
                        break
            
            if os.path.exists(inf_path):
                import ctypes
                res = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", "pnputil.exe", f'/add-driver "{inf_path}" /install', None, 1
                )
                if int(res) <= 32:
                    raise RuntimeError("UAC permission was denied or pnputil failed.")
            else:
                raise FileNotFoundError("Driver INF file not found in extracted package.")

            if progress_callback:
                progress_callback(100, "Universal USB Driver installed!")
            return True
        except Exception as e:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise RuntimeError(f"Error setting up USB driver: {e}")

    def uninstall_usb_driver(self, progress_callback=None):
        """Removes extracted USB driver folders."""
        driver_dir = os.path.join(self.engines_dir, "usb_driver")
        if progress_callback:
            progress_callback(50, "Removing driver files...")
        try:
            if os.path.exists(driver_dir):
                shutil.rmtree(driver_dir)
            if progress_callback:
                progress_callback(100, "USB Driver uninstalled!")
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete USB driver folder: {e}")

    def get_platform_tools_path(self):
        """Returns the path to platform-tools directory if installed, otherwise None."""
        pt_dir = os.path.join(self.engines_dir, "platform-tools")
        if os.path.exists(pt_dir) and os.path.exists(os.path.join(pt_dir, "fastboot.exe")):
            return pt_dir
        return None

    def get_fastboot_path(self):
        """Returns the path to fastboot.exe if platform-tools is installed, otherwise checks system path."""
        pt_path = self.get_platform_tools_path()
        if pt_path:
            return os.path.join(pt_path, "fastboot.exe")
        
        # Check system PATH
        fb_sys = shutil.which("fastboot")
        if fb_sys:
            return fb_sys
        return None

    def setup_platform_tools(self, progress_callback=None):
        """Downloads and extracts Google Platform Tools (adb & fastboot)."""
        zip_path = os.path.join(self.engines_dir, "platform_tools.zip")
        pt_dir = os.path.join(self.engines_dir, "platform-tools")
        url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
        
        if progress_callback:
            progress_callback(5, "Downloading Google Platform Tools...")
            
        def sub_cb(percent):
            if progress_callback:
                scaled = 5 + int(percent * 0.8)
                progress_callback(scaled, f"Downloading Platform Tools: {percent}%")

        try:
            self.download_file(url, zip_path, sub_cb)
            if progress_callback:
                progress_callback(90, "Extracting files...")
            
            # Extract ZIP
            if os.path.exists(pt_dir):
                try:
                    shutil.rmtree(pt_dir)
                except Exception:
                    pass
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.engines_dir)
            
            # Clean up zip
            try:
                os.remove(zip_path)
            except Exception:
                pass
            
            if progress_callback:
                progress_callback(100, "Google Platform Tools ready!")
            return True
        except Exception as e:
            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
            raise RuntimeError(f"Error setting up platform-tools: {e}")

    def uninstall_platform_tools(self, progress_callback=None):
        """Uninstalls Google Platform Tools (deletes the folder)."""
        pt_dir = os.path.join(self.engines_dir, "platform-tools")
        if progress_callback:
            progress_callback(50, "Deleting platform-tools files...")
        try:
            if os.path.exists(pt_dir):
                shutil.rmtree(pt_dir)
            if progress_callback:
                progress_callback(100, "Google Platform Tools uninstalled!")
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete platform-tools folder: {e}")

    def get_samsung_driver_path(self):
        """Returns the Samsung driver directory if setup, otherwise None."""
        drv_dir = os.path.join(self.engines_dir, "samsung_driver")
        if os.path.exists(drv_dir) and len(os.listdir(drv_dir)) > 0:
            return drv_dir
        return None

    def setup_samsung_driver(self, progress_callback=None):
        """Downloads, extracts and runs the Samsung Mobile USB Driver installer silently."""
        zip_path = os.path.join(self.engines_dir, "samsung_driver.zip")
        drv_dir = os.path.join(self.engines_dir, "samsung_driver")
        url = "https://github.com/kdrag0n/fastboot-drivers/releases/download/v1.0/Samsung_Android_USB_Driver.zip"

        if progress_callback:
            progress_callback(5, "Downloading Samsung Mobile USB Driver...")

        def sub_cb(percent):
            if progress_callback:
                scaled = 5 + int(percent * 0.7)
                progress_callback(scaled, f"Downloading Samsung Driver: {percent}%")

        try:
            self.download_file(url, zip_path, sub_cb)
            if progress_callback:
                progress_callback(80, "Extracting installation package...")

            if os.path.exists(drv_dir):
                try: shutil.rmtree(drv_dir)
                except: pass
            os.makedirs(drv_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(drv_dir)

            try: os.remove(zip_path)
            except: pass

            if progress_callback:
                progress_callback(90, "Running Samsung Driver Installer (Accept Admin UAC prompt)...")

            # Look for .exe file inside the extracted directory
            exe_file = None
            for root, dirs, files in os.walk(drv_dir):
                for f in files:
                    if f.endswith(".exe"):
                        exe_file = os.path.join(root, f)
                        break
            
            if exe_file:
                # Run Samsung installer with silent flag /S
                import ctypes
                res = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", exe_file, "/S", None, 1
                )
                if int(res) <= 32:
                    raise RuntimeError("UAC permission denied or installer failed.")
            else:
                raise FileNotFoundError("Samsung driver installer executable (.exe) not found in zip.")

            if progress_callback:
                progress_callback(100, "Samsung Mobile USB Driver installed!")
            return True
        except Exception as e:
            if os.path.exists(zip_path):
                try: os.remove(zip_path)
                except: pass
            raise RuntimeError(f"Error setting up Samsung Driver: {e}")

    def uninstall_samsung_driver(self, progress_callback=None):
        """Removes extracted Samsung Driver folders."""
        drv_dir = os.path.join(self.engines_dir, "samsung_driver")
        if progress_callback:
            progress_callback(50, "Removing driver package...")
        try:
            if os.path.exists(drv_dir):
                shutil.rmtree(drv_dir)
            if progress_callback:
                progress_callback(100, "Samsung Driver package removed!")
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to remove Samsung driver: {e}")

    def get_mtk_driver_path(self):
        """Returns MTK driver directory if setup, otherwise None."""
        drv_dir = os.path.join(self.engines_dir, "mtk_driver")
        if os.path.exists(drv_dir) and len(os.listdir(drv_dir)) > 0:
            return drv_dir
        return None

    def setup_mtk_driver(self, progress_callback=None):
        """Downloads, extracts and registers MediaTek (MTK) USB VCOM drivers."""
        zip_path = os.path.join(self.engines_dir, "mtk_driver.zip")
        drv_dir = os.path.join(self.engines_dir, "mtk_driver")
        url = "https://github.com/MTK-bypass/bypass_utility/releases/download/v1.4.1/mtk_driver.zip"

        if progress_callback:
            progress_callback(5, "Downloading MediaTek (MTK) VCOM Driver...")

        def sub_cb(percent):
            if progress_callback:
                scaled = 5 + int(percent * 0.7)
                progress_callback(scaled, f"Downloading MTK Driver: {percent}%")

        try:
            self.download_file(url, zip_path, sub_cb)
            if progress_callback:
                progress_callback(80, "Extracting drivers package...")

            if os.path.exists(drv_dir):
                try: shutil.rmtree(drv_dir)
                except: pass
            os.makedirs(drv_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(drv_dir)

            try: os.remove(zip_path)
            except: pass

            if progress_callback:
                progress_callback(90, "Installing MTK Drivers (Accept Admin UAC prompts)...")

            # Install all .inf driver files recursively using pnputil
            success = self.install_inf_drivers(drv_dir)
            if not success:
                raise RuntimeError("Failed to install one or more MTK Driver inf packages.")

            if progress_callback:
                progress_callback(100, "MediaTek VCOM USB Driver installed!")
            return True
        except Exception as e:
            if os.path.exists(zip_path):
                try: os.remove(zip_path)
                except: pass
            raise RuntimeError(f"Error setting up MediaTek Driver: {e}")

    def uninstall_mtk_driver(self, progress_callback=None):
        """Removes extracted MTK driver folders."""
        drv_dir = os.path.join(self.engines_dir, "mtk_driver")
        if progress_callback:
            progress_callback(50, "Removing driver package...")
        try:
            if os.path.exists(drv_dir):
                shutil.rmtree(drv_dir)
            if progress_callback:
                progress_callback(100, "MTK Driver package removed!")
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to remove MTK driver: {e}")

    def install_inf_drivers(self, folder_path):
        """Finds all .inf files in folder_path and registers/installs them using pnputil."""
        import ctypes
        success = True
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".inf"):
                    inf_path = os.path.join(root, file)
                    res = ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", "pnputil.exe", f'/add-driver "{inf_path}" /install', None, 1
                    )
                    if int(res) <= 32:
                        success = False
        return success


