import os, sys
import requests
import zipfile
import io
import subprocess
from pathlib import Path

from code_folder.error_display import display_error

VERSION_FILE_URL = f"https://raw.githubusercontent.com/Heavysaur0/TMNFAutoLogs/main/version.txt"
ZIP_URL = f"https://github.com/Heavysaur0/TMNFAutoLogs/archive/refs/heads/main.zip"

def get_local_version():
    if not os.path.exists("version.txt"):
        return None
    with open("version.txt", "r") as f:
        return f.read().strip()

def get_remote_version():
    try:
        response = requests.get(VERSION_FILE_URL)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print("Error fetching remote version:", e)
        display_error()
    return None

def download_and_extract_zip():
    print("Downloading new version...")
    response = requests.get(ZIP_URL)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        zip_ref.extractall("update_temp")

    extracted_folder = os.path.join("update_temp", f"TMNFAutoLogs-main")
    for item in os.listdir(extracted_folder):
        src = os.path.join(extracted_folder, item)
        dst = os.path.join(".", item)
        if os.path.isdir(src):
            os.system(f'cp -r "{src}" "{dst}"')
        else:
            os.system(f'cp "{src}" "{dst}"')

    print("Update complete.")
    os.system("rm -rf update_temp")

def check_for_update():
    local_version = get_local_version()
    remote_version = get_remote_version()

    print(f"Local version: {local_version}")
    print(f"Remote version: {remote_version}")

    if remote_version and remote_version != local_version:
        print("New version available!")
        download_and_extract_zip()
        with open("version.txt", "w") as f:
            f.write(remote_version)
        subprocess.run([sys.executable, Path(__file__).resolve().parent / "sanitise.py"])
    else:
        print("You already have the latest version.")

if __name__ == "__main__":
    check_for_update()
