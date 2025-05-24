import re

from php_like import GBXReplayFetcher
from error_display import display_error

from track_name import get_tmnf_map_info

def is_gbx_file(file_data: str) -> bool:
    return file_data[:3] == "GBX"

def is_validable(file_data: str) -> bool:
    match = re.search(r' validable="([01])"/>', file_data)
    if match:
        return bool(int(match.group(1)))
    return False

def get_times_match(file_data: str):
    return re.search(r'<times best="(\d+)" respawns="(\d+)" stuntscore="(\d+)"', file_data)

def get_time(file_data: str) -> int:
    match = get_times_match(file_data)
    if match:
        return match.group(1)
    raise Exception("Map best time not found")

def get_map_uid(file_data: str) -> int:
    match = re.search(r'<challenge uid="([^"]+)"/>', file_data)
    if match:
        return match.group(1)
    raise Exception("Map uid not found")


def parse_trackmania_replay(file_path: str) -> dict:
    with open(file_path, "rb") as f:
        data = f.read()
    file_data = data.decode(errors="ignore")
    
    if not is_gbx_file(file_data):
        print("The file is not a GBX replay file.")
    
    validable = is_validable(file_data)
    if not validable:
        print("Replay file is not validable, not displayed in logs.")
        return None

    result = {
        "environment": None,
        "author": None,
        "user_name": None,
        "user_login": None,
        "map_uid": None,
        "replay_time_ms": None,
        "respawns": None,
        "stunt_score": None,
        "validable": True,
    }

    # --- USER + MAP INFO ---
    replay_fetcher = GBXReplayFetcher(debug=True)
    replay_fetcher.processFile(file_path)
    result["environment"] = replay_fetcher.envir
    result["author"] = replay_fetcher.author
    result["user_name"] = replay_fetcher.nickname
    result["user_login"] = replay_fetcher.login
    result["map_uid"] = replay_fetcher.uid

    # --- USER STATS ---
    try:
        # print(xml_text[:400])
        times_match = get_times_match(file_data)
        if times_match:
            result["replay_time_ms"] = int(times_match.group(1))
            result["respawns"] = int(times_match.group(2))
            result["stunt_score"] = int(times_match.group(3))
        else:
            print("[!] User stats not found")
            
        result["map_uid"] = get_map_uid(file_data)
    except Exception as e:
        print(f"[!] Could not parse XML info: {e}")
        display_error()
    return result



if __name__ == '__main__':
    replay_file = r"C:\Users\Cosmo\Documents\TrackMania\Tracks\Replays\A - 1_Heavysaur(00'08''25).Replay.Gbx"
    
    info = parse_trackmania_replay(replay_file)
    for key, value in info.items():
        print(f"{key} - {value}")
    print()
    
    map_info = get_tmnf_map_info(info["map_uid"])
    for key, value in map_info.items():
        print(f"{key} - {value}")
    print()
