"""Sound effects. Drop audio files into assets/audio/sfx/ named after the
events below (e.g. punch.wav, parry.ogg). Missing files are simply skipped,
so the game runs fine with none, some, or all of them.

Variations: punch_1.wav, punch_2.wav, ... are picked at random each time,
which keeps repeated hits from sounding robotic.
"""
import random

import pygame

from core.settings import AUDIO_DIR

SFX_DIR = AUDIO_DIR / "sfx"
SFX_VOLUME = 0.7
EXTENSIONS = (".wav", ".ogg", ".mp3")

EVENTS = {
    # Charlie
    "whoosh": "Charlie dashes in / swings / throws",
    "punch": "Jab lands",
    "punch_heavy": "Haymaker or Chin Check lands",
    "perfect": "PERFECT timing (a sparkle/ding)",
    "miss": "Haymaker whiffs",
    "parry": "Perfect parry (metal clang)",
    "block": "Timed block",
    "hurt": "Charlie takes a hit",
    "heal": "Eating candy",
    "explosion": "Bomb explodes",
    "jump": "Jump while exploring",
    "slide": "Slide while exploring",
    # Enemies
    "zombie_groan": "Zombie groans while wandering",
    "zombie_bite": "Zombie attacks",
    "ghost_wail": "Ghost attacks / phases through a hit",
    "warlock_cast": "Warlock attacks",
    "warlock_laugh": "Warlock taunts before the boss fight",
    "reaper_laugh": "Bringer of Death taunts / starts the fight",
    "reaper_slash": "Bringer of Death scythe sweep",
    "reaper_grasp": "Death's Grasp (hand from the portal)",
    "worm_roar": "Fire Worm screeches before the fight",
    "worm_spit": "Fire Worm spits fire",
    "demon_roar": "Demon roars before the fight",
    "demon_cleave": "Demon swings its cleaver",
    "burn": "Charlie catches fire",
    "enrage": "Boss enrages at half HP",
    # Results and UI
    "ko": "Knockout blow",
    "victory": "Battle won",
    "defeat": "Charlie goes down",
    "ui_move": "Moving through the battle menu",
    "ui_select": "Choosing a move",
    "portal": "Stepping into the level exit portal",
}

_cache = {}


def _load(name):
    if name in _cache:
        return _cache[name]
    sounds = []
    if SFX_DIR.is_dir():
        candidates = [SFX_DIR / f"{name}{ext}" for ext in EXTENSIONS]
        candidates += sorted(p for p in SFX_DIR.glob(f"{name}_*") if p.suffix.lower() in EXTENSIONS)
        for path in candidates:
            if path.is_file():
                try:
                    sound = pygame.mixer.Sound(str(path))
                    sound.set_volume(SFX_VOLUME)
                    sounds.append(sound)
                except pygame.error as err:
                    print(f"[sfx] Couldn't load {path.name}: {err}")
    _cache[name] = sounds
    return sounds


def play(name, volume=1.0):
    """Play a sound effect by event name if its file exists (no-op otherwise)."""
    if not pygame.mixer.get_init():
        return
    sounds = _load(name)
    if sounds:
        sound = random.choice(sounds)
        channel = sound.play()
        if channel and volume != 1.0:
            channel.set_volume(volume)
