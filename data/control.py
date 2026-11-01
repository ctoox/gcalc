"""
Shared control interface for collector rate management.
Both web server and collector process read/write control.json.
"""

import os, json, time
from datetime import datetime

DATA_DIR = os.path.dirname(__file__)
CONTROL_FILE = os.path.join(DATA_DIR, "control.json")

DEFAULT_CONTROL = {
    "paused": False,
    "delay_seconds": 12.0,
    "target_total": 0,
    "max_offset": 0,
    "updated": None,
}

def read_control():
    if os.path.exists(CONTROL_FILE):
        try:
            with open(CONTROL_FILE, "r") as f:
                return {**DEFAULT_CONTROL, **json.load(f)}
        except Exception:
            pass
    return dict(DEFAULT_CONTROL)

def write_control(updates):
    current = read_control()
    current.update(updates)
    current["updated"] = str(datetime.now())
    with open(CONTROL_FILE, "w") as f:
        json.dump(current, f, indent=2)
    return current

def get_rate_label(delay):
    if delay <= 5:
        return "fast"
    elif delay <= 15:
        return "normal"
    elif delay <= 30:
        return "slow"
    else:
        return "glacial"

def set_pause(paused=True):
    return write_control({"paused": paused})

def set_delay(seconds):
    return write_control({"delay_seconds": max(1.0, float(seconds))})

def set_target(total):
    return write_control({"target_total": int(total)})

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pause", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--delay", type=float)
    parser.add_argument("--target", type=int)
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if args.pause:
        set_pause(True)
        print("Paused")
    elif args.resume:
        set_pause(False)
        print("Resumed")
    elif args.delay:
        set_delay(args.delay)
        print(f"Delay set to {args.delay}s")
    elif args.target:
        set_target(args.target)
        print(f"Target set to {args.target}")
    else:
        c = read_control()
        print(json.dumps(c, indent=2))
