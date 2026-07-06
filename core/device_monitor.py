import os
import subprocess
import re

class DeviceMonitor:
    def __init__(self, runner):
        self.runner = runner

    def get_android_devices(self):
        """Uses ADB to list connected Android devices (USB and Wi-Fi)."""
        stdout, _ = self.runner.run_adb_command(["devices", "-l"])
        devices = []
        for line in stdout.splitlines():
            if not line.strip() or line.startswith("List of devices"):
                continue
            
            # Match serial and model information
            # Format: serial   device product:xxx model:xxx device:xxx
            match = re.match(r"^([^\s]+)\s+device\s+(.*)$", line)
            if match:
                serial = match.group(1)
                info_str = match.group(2)
                
                # Extract model
                model = "Android Device"
                model_match = re.search(r"model:([^\s]+)", info_str)
                if model_match:
                    model = model_match.group(1).replace("_", " ")
                
                # Check connection type (Wi-Fi vs USB)
                # If serial contains an IP and port (e.g. 192.168.1.100:5555), connection is Wi-Fi
                conn_type = "Wi-Fi" if ":" in serial else "USB"
                
                devices.append({
                    "serial": serial,
                    "model": f"{model} ({serial})",
                    "type": conn_type,
                    "platform": "Android"
                })
        return devices

    def get_ios_devices(self):
        """Uses Windows PowerShell to detect connected Apple devices via Vendor ID (05AC)."""
        devices = []
        try:
            # Query using PowerShell (much more modern and reliable than deprecated wmic)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            cmd = ["powershell", "-NoProfile", "-Command", 
                   "Get-PnpDevice -PresentOnly | Where-Object InstanceId -like '*VID_05AC*' | Select-Object FriendlyName, InstanceId | ConvertTo-Json -Compress"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=8)
            output = result.stdout.strip()
            
            if output:
                import json
                data = json.loads(output)
                # Convert to list if it's a single dictionary
                if isinstance(data, dict):
                    data = [data]
                
                for item in data:
                    name = item.get("FriendlyName", "")
                    device_id = item.get("InstanceId", "")
                    
                    if name and device_id:
                        # Filter out Apple devices that aren't iPhones/iPads/Mobile devices
                        if any(x in name.lower() for x in ["iphone", "ipad", "ipod", "apple mobile device"]):
                            # Avoid duplicates
                            if not any(d["serial"] == device_id for d in devices):
                                devices.append({
                                    "serial": device_id,
                                    "model": name,
                                    "type": "USB",
                                    "platform": "iOS"
                                })
        except Exception:
            pass
        return devices

    def get_all_devices(self):
        """Combines Android and iOS lists."""
        return self.get_android_devices() + self.get_ios_devices()
