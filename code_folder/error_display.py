import sys
import traceback

def display_error():
    _, _, exc_tb = sys.exc_info()
    tb = traceback.extract_tb(exc_tb)
    for filename, lineno, func, text in tb:
        print(f"    └─File \"{filename}\", line {lineno}, in {func}")
        if text:
            print(f"        {text.strip()}")