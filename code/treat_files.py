import shutil
import os
from pathlib import Path
from datetime import datetime, timezone
import matplotlib.pyplot as plt

from track_name import get_tmnf_map_info
from error_display import display_error
from php_like import GBXReplayFetcher
from file_uid import get_file_hash

from data_handler import save, load
from parse_replay import is_gbx_file, is_validable, get_map_uid, get_times_match


def treat_new_file(file: Path, destination: Path, data_dict: dict):
    with open(file, "rb") as f:
        data = f.read()
    file_data = data.decode(errors="ignore")
    pos = file_data.find("</header>")
    if pos != -1:
        file_data = file_data[:pos + 10]
    
    if not is_gbx_file(file_data):
        print("The file is not a GBX replay file.")
        return
    
    validable = is_validable(file_data)
    if not validable:
        print("Replay file is not validable, not displayed in logs.")
        return
        
    map_uid = get_map_uid(file_data)
    if map_uid in data_dict["map_uids"]:
        map_data = data_dict["map_uids"][map_uid]
    else:
        map_data = get_tmnf_map_info(map_uid)
        data_dict["map_uids"][map_uid] = map_data

    map_folder_path = destination / map_data["name"]
    data_file_path = map_folder_path / "data.pkl"
    if not os.path.exists(map_folder_path):
        os.mkdir(map_folder_path)
        # No need to create the file, already does it by itself
        data = {"name": map_data["name"], "runs": {}}
        save(data, data_file_path)
    else:
        data = load(data_file_path)
    
    file_hash = get_file_hash(file)
    if file_hash in data["runs"]:
        print("Replay file ignored due to duplicate")
        return
    data["runs"][file_hash] = replay_info
    save(data, data_file_path)

    replay_info = {}
    
    replay_fetcher = GBXReplayFetcher(debug=True)
    replay_fetcher.processFile(file)
    replay_info["user_name"] = replay_fetcher.nickname
    replay_info["user_login"] = replay_fetcher.login
    
    times_match = get_times_match(file_data)
    if times_match:
        replay_info["replay_time_ms"] = int(times_match.group(1))
        replay_info["respawns"] = int(times_match.group(2))
        replay_info["stunt_score"] = int(times_match.group(3))
    else:
        print("[!] User stats not found")
        return

    utc_date = datetime.now(timezone.utc)
    replay_info["utc_date"] = utc_date
    
    try:
        dst = map_folder_path / file
        file_name = Path(file.stem).stem # Remove the Replay Gbx
        index = 0
        while os.path.exists(dst):
            dst = map_folder_path / f"{file_name}-({index}).Replay.Gbx"
            index += 1
        try:
            shutil.move(str(file), str(dst))
            print(f"Moved: {file.name} to {dst}")
            file.unlink(True)
        except Exception as e:
            print(f"Error moving the file {dst} - {e}")
            display_error()
    except Exception as e:
        print(f"Error moving {file.name}: {e}")
        display_error()
        return

def get_map_stats(map_folder: Path | str):
    """
    return of layout:
    map_stats = {
        "names": {..., ..., ...},
        "login1": {
            time.1: {
                "times": ...,
                "dates": {..., ..., ...},
                "respawns": ...,
                "stunt_score": ...,
            },
            time.2: {...},
            ...,
        }
        "login2": {...},
        ...
    }
    """
    if not os.path.exists(map_folder):
        raise Exception(f"The map folder {map_folder} doesn't exist yet.")
    data_file = map_folder / "data.pkl" if isinstance(map_folder, Path) else os.path.join(map_folder, "data.pkl")
    data = load(data_file)["runs"]
    
    map_stats = {}
    
    for value in data.values():
        name = value["user_name"]
        login = value["user_login"]
        time_ms = value["replay_time_ms"]
        respawns = value["respawns"]
        stunt_score = value["stunt_score"]
        date = value["utc_date"]
        
        if login not in map_stats:
            map_stats[login] = {"names": set([name])}
        else:
            map_stats[login]["names"].add(name)
        
        if time_ms not in map_stats[login]:
            map_stats[login][time_ms] = {
                "times": 1, 
                "dates": set([date]), 
                "respawns": respawns,
                "stunt_score": stunt_score,
            }
        else:
            map_stats[login][time_ms]["times"] += 1
            map_stats[login][time_ms]["dates"].add(date)
            map_stats[login][time_ms]["respawns"] += respawns
            map_stats[login][time_ms]["stunt_score"] += stunt_score
    
    return map_stats

def plot_times(map_folder: Path | str):
    if not os.path.exists(map_folder):
        raise Exception(f"The map folder {map_folder} doesn't exist yet.")
    data_file = map_folder / "data.pkl" if isinstance(map_folder, Path) else os.path.join(map_folder, "data.pkl")
    data = load(data_file)["runs"]
    if not data:
        print("The map folder data is empty.")
        return
    
    x_dict = {}
    y_dict = {}
    
    min_date_int = None
    max_date_int = None
    min_date = None
    max_date = None
    
    for value in data.values():
        login = value["user_login"]
        time_ms = value["replay_time_ms"]
        date = value["utc_date"]
        
        timestamp_float = date.timestamp()
        date_int = int(timestamp_float)
        
        if min_date is None:
            min_date = max_date = date
            min_date_int = max_date_int = date_int
        
        if date_int < min_date_int:
            min_date_int = date_int
            min_date = date
        if date_int > max_date_int:
            max_date_int = date_int
            max_date = date
        
        if login not in x_dict:
            x_dict[login] = [date_int]
            y_dict[login] = [time_ms / 1000]
        else:
            x_dict[login].append(date_int)
            y_dict[login].append(time_ms / 1000)
    
    
    colors = [
        'red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'olive', 'cyan', 'magenta', 'gold',
        'darkgreen', 'navy', 'crimson', 'teal', 'coral', 'indigo', 'turquoise', 'darkorange',  'slateblue'
    ]
    
    for i, login in enumerate(x_dict.keys()):
        color = colors[i % len(colors)]
        plt.scatter(x_dict[login], y_dict[login], 
                    color=color, marker='o', label=login)
    
    plt.xlabel('Date')
    plt.ylabel('Time in seconds')
    plt.title('Plot of times by date')
    plt.legend()
    
    plt.show()

def move_whole_directory(source: Path, destination: Path):
    if source is None: 
        return
    
    shutil.move(str(source / "data.pkl"), str(destination))
    map_folders = [map_folder for map_folder in source.iterdir() if map_folder.is_dir()]
    for map_folder in map_folders:
        shutil.move(str(map_folder), str(destination))

