"""File to sanitise replay files in case of problems
Also used if I change data formats in a new version"""

import sys
from pathlib import Path

from code_folder.treat_files import sanitise_replays
from code_folder.data_handler import save, load
from code_folder.error_display import display_error

data_file = Path(__file__).resolve().parent / "code/data.pkl"
if not data_file.exists():
    print("Couldn't sanitise, data file is not created yet.")
    sys.exit(1)

print("Sanitising files...")
try:
    source, destination, data = load(data_file)
    sanitise_replays(destination, data)
    save((source, destination, data), data_file)
except Exception as e:
    display_error()
    print(f"[!] The sanitisation failed, data could be a mess please contact Heavysaur0 if problems occur - {e}")
    
    