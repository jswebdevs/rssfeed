# log.py

import datetime

def log_step(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("steps.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
