import subprocess
import sys
import importlib.util
import os
from pathlib import Path

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

script_dir = Path(__file__).resolve().parent / "code"
os.chdir(script_dir)
print(f"Changed working directory to: {script_dir}")

main_script = "tkinter_app.py"

print(f"Running {main_script}...")
subprocess.run([sys.executable, str(script_dir / main_script)])
