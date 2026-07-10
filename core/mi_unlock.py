import os
import re
import sys
import json
import hmac
import random
import binascii
import urllib.parse
import hashlib
import time
import requests
import subprocess
from urllib3.util.url import Url
from base64 import b64encode, b64decode
from Cryptodome.Cipher import AES

class MiUnlockSession:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {"User-Agent": "XiaomiPCSuite"}
        
        config_dir = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
        self.data_dir = os.path.join(config_dir, "miunlocktool")
        os.makedirs(self.data_dir, exist_ok=True)
        self.datafile = os.path.join(self.data_dir, "miunlockdata.json")
        
        self.user = ""
        self.pwd = ""
        self.wb_id = ""
        self.ssecurity = ""
        self.nonce = ""
        self.location = ""
        self.cookies = {}
        self.region = "global"
        self.url = "unlock.update.intl.miui.com"
        self.uid = ""
        
        self.load_saved_session()

    def load_saved_session(self):
        if os.path.isfile(self.datafile):
            try:
                with open(self.datafile, "r") as file:
                    data = json.load(file)
                if data and data.get("login") == "ok":
                    self.user = data.get("user", "")
                    self.pwd = data.get("pwd", "")
                    self.wb_id = data.get("wb_id", "")
                    self.uid = data.get("uid", "")
            except Exception:
                pass

    def save_session(self):
        data = {
            "login": "ok" if self.uid else "failed",
            "user": self.user,
            "pwd": self.pwd,
            "wb_id": self.wb_id,
            "uid": self.uid
        }
        try:
            with open(self.datafile, "w") as file:
                json.dump(data, file, indent=2)
        except Exception:
            pass

    def logout(self):
        self.user = ""
        self.pwd = ""
        self.wb_id = ""
        self.uid = ""
        if os.path.isfile(self.datafile):
            try:
                os.remove(self.datafile)
            except Exception:
                pass

    def get_login_url(self):
        return 'https://account.xiaomi.com/pass/serviceLogin?sid=unlockApi&checkSafeAddress=true&passive=false&hidden=false'

    def postv(self, sid):
        url = f"https://account.xiaomi.com/pass/serviceLoginAuth2?sid={sid}&_json=true&passive=true&hidden=true"
        data = {
            "user": self.user, 
            "hash": hashlib.md5(self.pwd.encode()).hexdigest().upper()
        }
        res = self.session.post(url, data=data, headers=self.headers, cookies={"deviceId": str(self.wb_id)})
        return json.loads(res.text.replace("&&&START&&&", ""))

    def authenticate(self, user, pwd, pasted_url):
        self.user = user
        self.pwd = pwd
        
        # Extract wb_id
        try:
            parsed = urllib.parse.urlparse(pasted_url)
            params = urllib.parse.parse_qs(parsed.query)
            self.wb_id = params.get('d', [None])[0]
        except Exception:
            return False, "Invalid confirmation link format. Please copy and paste the entire URL."
            
        if not self.wb_id:
            return False, "Could not extract device ID (wb_id) from the URL."

        try:
            data = self.postv("unlockApi")
            if data.get("code") == 70016:
                return False, "Invalid account ID or password."

            if data.get("securityStatus") == 4 and "notificationUrl" in data and "bizType=SetEmail" in data["notificationUrl"]:
                return False, f"Email verification required. Please link an email to your account: {data['notificationUrl']}"

            if data.get("securityStatus") == 16:
                p = self.postv("passport")
                if p.get("securityStatus") == 4 and "notificationUrl" in p and "bizType=SetEmail" in p["notificationUrl"]:
                    return False, f"Email verification required. Please link an email to your account: {p['notificationUrl']}"
                elif "passToken" not in p:
                     return False, "Failed to fetch passToken (Email required)."
                
                # Fetch unlock location config
                cookies_init = {
                    'passToken': p['passToken'], 
                    'userId': str(p['userId']), 
                    'deviceId': urllib.parse.parse_qs(urllib.parse.urlparse(p['location']).query)['d'][0]
                }
                res = requests.get(
                    "https://account.xiaomi.com/pass/serviceLogin?sid=unlockApi&_json=true&passive=true&hidden=true", 
                    headers=self.headers, 
                    cookies=cookies_init
                )
                data = json.loads(res.text.replace("&&&START&&&", ""))

            if "notificationUrl" in data:
                return False, f"Security check required. Open this URL in browser: {data['notificationUrl']}"

            self.ssecurity = data.get("ssecurity")
            self.nonce = data.get("nonce")
            self.location = data.get("location")
            self.uid = data.get("userId")

            if not self.ssecurity or not self.location:
                return False, "Failed to authenticate with Xiaomi Server (Missing security context)."

            # Perform client token exchange
            client_sign = b64encode(hashlib.sha1(f"nonce={self.nonce}".encode("utf-8") + b"&" + self.ssecurity.encode("utf-8")).digest())
            url_with_sign = self.location + "&clientSign=" + urllib.parse.quote_plus(client_sign)
            
            res_cookies = self.session.get(url_with_sign, headers=self.headers)
            self.cookies = {cookie.name: cookie.value for cookie in res_cookies.cookies}

            if 'serviceToken' not in self.cookies:
                return False, "Failed to acquire Service Token from Xiaomi redirect."

            # Fetch User Region
            region_res = requests.get(
                "https://account.xiaomi.com/pass/user/login/region?", 
                headers=self.headers, 
                cookies={
                    'passToken': data['passToken'], 
                    'userId': str(data['userId']), 
                    'deviceId': urllib.parse.parse_qs(urllib.parse.urlparse(data['location']).query)['d'][0]
                }
            )
            self.region = json.loads(region_res.text.replace("&&&START&&&", ""))['data']['region']

            # Match region config
            reg_config_res = requests.get("https://account.xiaomi.com/pass2/config?key=register").text
            region_config = json.loads(reg_config_res.replace("&&&START&&&", ""))['regionConfig']
            for key, value in region_config.items():
                if 'region.codes' in value and self.region in value['region.codes']:
                    self.region = value['name'].lower()
                    break

            # Set correct base endpoint URL based on region
            g_host = "unlock.update.intl.miui.com"
            if self.region == "china":
                self.url = g_host.replace("intl.", "")
            elif self.region == "india":
                self.url = f"in-{g_host}"
            elif self.region == "russia":
                self.url = f"ru-{g_host}"
            elif self.region == "europe":
                self.url = f"eu-{g_host}"
            else:
                self.url = g_host

            # Save state
            self.save_session()
            return True, f"Login successful! Account UID: {self.uid}"

        except Exception as e:
            return False, f"Exception during authentication: {str(e)}"

    def get_confirm_notice(self, product):
        """Checks if unlocking will format user data."""
        try:
            res_data = self.RetrieveEncryptData("/api/v2/unlock/device/clear", {"data":{"product":product}}).add_nonce(self).run(self)
            cleanOrNot = res_data.get('cleanOrNot')
            notice = res_data.get('notice', 'Unlocking device clears user data.')
            return True, cleanOrNot, notice
        except Exception as e:
            return False, 0, f"Error checking clearing notice: {str(e)}"

    def unlock_device(self, fastboot_path, product, token, serialno):
        """Performs the unlock sequence by calling Xiaomi api and flashing the staged signature."""
        try:
            # Step 1: Request unlock signature from api
            payload = {
                "appId": "1", 
                "data": {
                    "clientId": "2", 
                    "clientVersion": "7.6.727.43", 
                    "language": "en", 
                    "operate": "unlock", 
                    "pcId": hashlib.md5(self.wb_id.encode("utf-8")).hexdigest(), 
                    "product": product, 
                    "region": "",
                    "deviceInfo": {
                        "boardVersion": "",
                        "product": product, 
                        "socId": "",
                        "deviceName": ""
                    }, 
                    "deviceToken": token
                }
            }
            res_data = self.RetrieveEncryptData("/api/v3/ahaUnlock", payload).add_nonce(self).run(self)
            
            if "code" in res_data and res_data["code"] == 0:
                encrypt_hex = res_data.get("encryptData")
                if not encrypt_hex:
                    return False, "Failed: Xiaomi API returned code 0 but no encryptData."
                
                # Write encryptData file locally
                stages_bytes = bytes.fromhex(encrypt_hex)
                stage_file = os.path.join(self.data_dir, "encryptData")
                with open(stage_file, "wb") as f:
                    f.write(stages_bytes)
                
                # Step 2: Flash staged file
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                # Run fastboot stage
                p1 = subprocess.run([fastboot_path, "stage", stage_file], capture_output=True, text=True, startupinfo=startupinfo, timeout=15)
                if p1.returncode != 0:
                    try: os.remove(stage_file)
                    except: pass
                    return False, f"Failed fastboot stage:\nSTDOUT: {p1.stdout}\nSTDERR: {p1.stderr}"
                
                # Run fastboot oem unlock
                p2 = subprocess.run([fastboot_path, "oem", "unlock"], capture_output=True, text=True, startupinfo=startupinfo, timeout=15)
                
                # Cleanup
                try: os.remove(stage_file)
                except: pass
                
                if p2.returncode == 0:
                    return True, "Unlock Successful! Your device will now reboot."
                else:
                    return False, f"Failed fastboot oem unlock:\nSTDOUT: {p2.stdout}\nSTDERR: {p2.stderr}"
            
            elif "descEN" in res_data:
                err_msg = res_data["descEN"]
                if res_data["code"] == 20036:
                    wait_hours = res_data.get("data", {}).get("waitHour", 168)
                    wait_time = (time.time() + wait_hours * 3600)
                    formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(wait_time))
                    return False, f"Unlock Cooldown active: Please wait {wait_hours} hours. You can unlock on: {formatted_time}."
                return False, f"Xiaomi server error (code {res_data['code']}): {err_msg}"
            else:
                return False, f"Unlock failed. Xiaomi Server Response: {json.dumps(res_data)}"
                
        except Exception as e:
            return False, f"Exception during unlock execution: {str(e)}"

    class RetrieveEncryptData:
        def __init__(self, path, params):
            self.path = path
            self.params = {}
            for k, v in params.items():
                k_b = k.encode("utf-8")
                if isinstance(v, str):
                    v_b = v.encode("utf-8")
                elif isinstance(v, bytes):
                    v_b = v
                else:
                    v_b = b64encode(json.dumps(v).encode("utf-8"))
                self.params[k_b] = v_b

        def add_nonce(self, session_obj):
            random_r = ''.join(random.choices(list("abcdefghijklmnopqrstuvwxyz"), k=16))
            self.params[b"nonce"] = session_obj.nonce.encode("utf-8")
            self.params[b"r"] = random_r.encode("utf-8")
            self.params[b"sid"] = b"miui_unlocktool_client"
            return self

        def getp(self, sep):
            return b'POST' + sep + self.path.encode("utf-8") + sep + b"&".join([k + b"=" + v for k, v in self.params.items()])

        def run(self, session_obj):
            # Signature hash
            signature_base = self.getp(b"\n")
            sign = binascii.hexlify(hmac.digest(b'2tBeoEyJTunmWUGq7bQH2Abn0k2NhhurOaqBfyxCuLVgn4AVj7swcawe53uDUno', signature_base, "sha1"))
            self.params[b"sign"] = sign
            
            # AES encryption of values
            aes_key = b64decode(session_obj.ssecurity)
            for k, v in self.params.items():
                pad_len = 16 - len(v) % 16
                padded = v + bytes([pad_len] * pad_len)
                cipher = AES.new(aes_key, AES.MODE_CBC, b"0102030405060708")
                self.params[k] = b64encode(cipher.encrypt(padded))
                
            # Final signature
            final_sig = b64encode(hashlib.sha1(self.getp(b"&") + b"&" + session_obj.ssecurity.encode("utf-8")).digest())
            self.params[b"signature"] = final_sig
            
            # Post request
            post_url = Url(scheme="https", host=session_obj.url, path=self.path).url
            res = session_obj.session.post(post_url, data=self.params, headers=session_obj.headers, cookies=session_obj.cookies)
            
            # Decrypt response
            raw_dec = b64decode(res.text)
            dec_cipher = AES.new(aes_key, AES.MODE_CBC, b"0102030405060708")
            decrypted = dec_cipher.decrypt(raw_dec)
            unpadded = decrypted[:-decrypted[-1]]
            
            return json.loads(unpadded.decode("utf-8"))
