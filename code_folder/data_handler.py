import pickle
from pathlib import Path


def save(data: dict, file_path: Path | str) -> None:
    with open(file_path, "wb") as file:
        pickle.dump(data, file)


def load(file_path: Path | str) -> dict:
    with open(file_path, "rb") as file:
        data = pickle.load(file)
    return data

def recur_display(key, value, level = 0, ignore_key=False):
    prefix = "  " * level
    if not value:
        if ignore_key:
            print(value)
        else:
            print(f"{prefix}{key} - {value}")
    elif isinstance(value, dict):
        if ignore_key:
            print(f"{prefix}{'{'}")
        else:
            print(f"{prefix}{key} - {'{'}")
        for k2, v2 in value.items():
            recur_display(k2, v2, level + 1, False)
        print(f"{prefix}{'}'}")
    elif isinstance(value, (tuple, list)):
        if ignore_key:
            print('[')
        else:
            print(f"{prefix}{key} - [")
        for v2 in value:
            recur_display("", v2, level + 1, True)
        print(f"{prefix}]")
    else:
        if ignore_key:
            print(value)
        else:
            print(f"{prefix}{key} - {value}")