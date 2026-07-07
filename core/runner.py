import os
import subprocess
import signal

class MirrorRunner:
    def __init__(self, downloader):
        self.downloader = downloader
        self.active_processes = {}

    def get_adb_path(self):
        """Locates adb.exe inside the scrcpy engine folder."""
        scrcpy_exe = self.downloader.get_scrcpy_path()
        if scrcpy_exe:
            scrcpy_dir = os.path.dirname(scrcpy_exe)
            adb_path = os.path.join(scrcpy_dir, "adb.exe")
            if os.path.exists(adb_path):
                return adb_path
        return "adb"

    def run_adb_command(self, args):
        """Runs an ADB command and returns output."""
        adb_path = self.get_adb_path()
        try:
            # Use startupinfo to prevent terminal flash on older Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run([adb_path] + args, capture_output=True, text=True, startupinfo=startupinfo, timeout=10)
            return result.stdout, result.stderr
        except Exception as e:
            return "", str(e)

    def connect_wifi_device(self, ip_address, port=5555):
        """Tries to connect to an Android device over Wi-Fi."""
        target = f"{ip_address}:{port}"
        stdout, stderr = self.run_adb_command(["connect", target])
        if "connected" in stdout.lower():
            return True, stdout.strip()
        return False, stderr.strip() if stderr else stdout.strip()

    def disconnect_wifi_device(self, ip_address, port=5555):
        """Disconnects a Wi-Fi device."""
        target = f"{ip_address}:{port}"
        self.run_adb_command(["disconnect", target])

    def start_android_mirror(self, serial=None, resolution="1920", fps="60", bitrate="8M", 
                             audio_enabled=True, record_path=None, stay_awake=True, connection_type="USB",
                             turn_screen_off=False):
        """Launches scrcpy mirroring session."""
        scrcpy_exe = self.downloader.get_scrcpy_path()
        if not scrcpy_exe:
            return False, "Android engine (scrcpy) is not set up."

        # Build command list
        cmd = [scrcpy_exe, "--window-title", "N8 G Tools Android Mirror"]
        
        # Optimize performance: force hardware-accelerated H.264 and disable buffering
        cmd += ["--video-codec=h264", "--video-buffer=0"]
        
        if serial:
            cmd += ["--serial", serial]
            
        if resolution != "Native":
            cmd += ["-m", resolution]
            
        if fps:
            cmd += ["--max-fps", fps]
            
        if bitrate:
            cmd += ["-b", bitrate]
            
        if not audio_enabled:
            cmd += ["--no-audio"]
            
        if stay_awake:
            cmd += ["--stay-awake"]

        if turn_screen_off:
            cmd += ["--turn-screen-off"]
            
        if record_path:
            cmd += ["--record", record_path]

        # Hide terminal window on execution on Windows without hiding the GUI window
        creationflags = 0
        if os.name == 'nt':
            creationflags = 0x08000000  # subprocess.CREATE_NO_WINDOW

        try:
            process_key = f"android_{serial or 'default'}"
            self.stop_process(process_key)

            # Start process with CREATE_NO_WINDOW, redirecting output to DEVNULL to avoid buffer fill-up
            p = subprocess.Popen(cmd, creationflags=creationflags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.active_processes[process_key] = p
            return True, "Android Mirror started."
        except Exception as e:
            return False, f"Failed to launch scrcpy: {e}"

    def start_ios_mirror(self, fps="60", resolution="1920x1080", vsync=True, audio_delay="0.25", audio_enabled=True):
        """Launches uxplay AirPlay server."""
        uxplay_exe = self.downloader.get_uxplay_path()
        if not uxplay_exe:
            return False, "iOS engine (uxplay) is not installed."
        
        if not self.downloader.is_bonjour_installed():
            return False, "Apple Bonjour Service is required for AirPlay discovery."

        # Build command list - Set network name to N8 G Tools
        cmd = [uxplay_exe, "-n", "N8 G Tools", "-nh"]
        
        # On Windows, use Direct3D 11 hardware-accelerated video rendering for maximum smoothness
        if os.name == 'nt':
            cmd += ["-vs", "d3d11videosink"]
        
        if fps:
            cmd += ["-fps", fps]
            
        if resolution:
            cmd += ["-s", resolution]
            
        if not vsync:
            cmd += ["-vsync", "no"]
            
        if audio_delay:
            cmd += ["-al", audio_delay]

        if not audio_enabled:
            cmd += ["-a"]

        # Run process on Windows hiding the console window but keeping the GUI window visible
        creationflags = 0
        if os.name == 'nt':
            creationflags = 0x08000000  # subprocess.CREATE_NO_WINDOW

        try:
            process_key = "ios_airplay"
            self.stop_process(process_key)

            p = subprocess.Popen(cmd, creationflags=creationflags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.active_processes[process_key] = p
            return True, "iOS AirPlay Server started. Open Control Center on iPhone/iPad and select Mirroring."
        except Exception as e:
            return False, f"Failed to launch uxplay: {e}"

    def stop_process(self, key):
        """Stops an active process."""
        p = self.active_processes.get(key)
        if p:
            try:
                # Use taskkill on Windows to ensure child processes die
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], 
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception:
                p.terminate()
            del self.active_processes[key]

    def stop_all(self):
        """Stops all running mirrors."""
        for key in list(self.active_processes.keys()):
            self.stop_process(key)

    def is_running(self, key):
        """Checks if a process is still active."""
        p = self.active_processes.get(key)
        if p:
            return p.poll() is None
        return False
