"""Player settings (Settings menu) and where the game keeps its files.

Settings and the save game live in a ".chin_check_charlie" folder in the user's
home folder (C:\\Users\\<you>\\.chin_check_charlie on Windows), not in the project,
so they never end up in git. If that folder can't be written (a locked-down PC,
or a web build), the game still runs; it just won't remember anything.
"""
import json
import os
from pathlib import Path

from core.difficulty import DIFFICULTIES

DATA_DIR = Path(os.environ.get("CHIN_CHECK_DATA_DIR") or Path(os.path.expanduser("~")) / ".chin_check_charlie")
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULTS = {
    "music_volume": 0.4,
    "sfx_volume": 1.0,
    "fullscreen": True,
    "difficulty": "normal",
}

options = dict(DEFAULTS)      # the live settings; read these anywhere


def load():
    """Read saved settings over the defaults (missing or broken file = defaults)."""
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return options
    for key, default in DEFAULTS.items():
        value = data.get(key, default)
        if isinstance(default, bool):
            value = bool(value)
        elif isinstance(default, float):
            try:
                value = max(0.0, min(1.0, float(value)))
            except (TypeError, ValueError):
                value = default
        elif key == "difficulty" and value not in DIFFICULTIES:
            value = default
        options[key] = value
    return options


def save():
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(options, indent=2), encoding="utf-8")
    except OSError as err:
        print(f"[settings] Couldn't save settings: {err}")
