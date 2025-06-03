import time
import json
from pathlib import Path


def start_timer(stop_flag):
    """
    Starts a live timer until stop_flag[0] becomes True.
    Prints time in-place like ⏱️  00:12
    """
    start_time = time.time()

    while not stop_flag[0]:
        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)
        timer_str = f"\r⏱️ {mins:02}:{secs:02}"
        print(timer_str, end='', flush=True)
        time.sleep(1)

    print()  # move to new line after stop


def save_json(data, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)