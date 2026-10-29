"""The save game: written automatically whenever Charlie reaches a camp, so
Continue on the title screen picks up at the last camp.

It lives next to the settings (see core/options.py), not in the project folder.
"""
import json

from core import game_state
from core.levels import LEVELS
from core.options import DATA_DIR, options
from core.player import Player

SAVE_FILE = DATA_DIR / "save.json"
VERSION = 1


def save(player, chapter_index):
    """Charlie made it to the camp after LEVELS[chapter_index]."""
    data = {"version": VERSION, "chapter": chapter_index, "player": player.to_save(),
            "flags": game_state.to_dict(), "difficulty": options["difficulty"]}
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SAVE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except OSError as err:
        print(f"[save] Couldn't save the game: {err}")
        return False


def load():
    """The saved game as a dict, or None if there isn't a usable one."""
    try:
        data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not 0 <= data.get("chapter", -1) < len(LEVELS) or "player" not in data:
        return None
    return data


def describe(data):
    """A short label for the title screen's Continue button."""
    if not data:
        return None
    return f"Camp after Chapter {data['chapter'] + 1}"


def restore(data):
    """Rebuild the Player and story flags from a save. Returns (player, chapter_index)."""
    game_state.from_dict(data.get("flags", {}))
    return Player.from_save(data["player"]), data["chapter"]
