import subprocess
import sys
import importlib.util
import os
from pathlib import Path
import requests

RAW_URL = f"https://raw.githubusercontent.com/Heavysaur0/TMNFAutoLogs/main/"

def is_pip_installed():
    return importlib.util.find_spec("pip") is not None

if not is_pip_installed():
    print("pip is not installed. Please install pip before running this script.")
    sys.exit(1)

required_packages = {
    "requests": "requests",
    "bs4": "beautifulsoup4",
    "watchdog": "watchdog",
    "matplotlib": "matplotlib"
}

def install_package(pkg_name):
    print(f"Installing {pkg_name}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])

for module_name, pip_name in required_packages.items():
    if importlib.util.find_spec(module_name) is None:
        install_package(pip_name)
    else:
        print(f"{pip_name} is already installed.")

def update_updater():
    try:
        print("Checking for updater.py updates...")
        remote = requests.get(RAW_URL + "update.py")
        if remote.status_code == 200:
            remote_code = remote.text.strip()

            updater_path = Path(__file__).resolve().parent / "update.py"
            if updater_path.exists():
                with open(updater_path, "r", encoding="utf-8") as f:
                    local_code = f.read().strip()
                if local_code != remote_code:
                    print("Updating updater.py...")
                    with open(updater_path, "w", encoding="utf-8") as f:
                        f.write(remote_code)
                else:
                    print("updater.py is already up to date.")
            else:
                print("Downloading updater.py...")
                with open(updater_path, "w", encoding="utf-8") as f:
                    f.write(remote_code)
        else:
            print(f"Could not fetch updater.py: HTTP {remote.status_code}")
    except Exception as e:
        print(f"Error checking/updating updater.py: {e}")

def run_updater():
    updater_path = Path(__file__).resolve().parent / "update.py"
    if updater_path.exists():
        subprocess.run([sys.executable, str(updater_path)])
    else:
        print("updater.py not found. Running tkinter_app.py directly...")

def run_main_script():
    script_dir = Path(__file__).resolve().parent / "code_folder"
    os.chdir(script_dir)
    print(f"Changed working directory to: {script_dir}")
    main_script = "tkinter_app.py"
    print(f"Running {main_script}...")
    subprocess.run([sys.executable, str(script_dir / main_script)])

if __name__ == "__main__":
    update_updater()
    run_updater()
    run_main_script()