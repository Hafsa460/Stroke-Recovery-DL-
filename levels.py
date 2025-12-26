import json
import os

LEVEL_FILE = "levels.json"

def load_levels():
    if os.path.exists(LEVEL_FILE):
        with open(LEVEL_FILE, "r") as f:
            return json.load(f)
    else:
        levels = {str(i): i == 1 for i in range(1, 11)}  # Only level 1 unlocked
        save_levels(levels)
        return levels

def save_levels(levels):
    with open(LEVEL_FILE, "w") as f:
        json.dump(levels, f)

def is_level_unlocked(level, levels):
    return levels.get(str(level), False)
