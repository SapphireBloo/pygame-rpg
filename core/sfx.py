"""Sound effects, played by event name: sfx.play("punch").

SOUNDS (below) says which files in assets/audio/sfx/ each event uses, and how
loud. When an event lists several files, one is picked at random each time so
repeated hits don't sound robotic. To change a sound, edit its line in SOUNDS.

You can also drop in a file named after an event (e.g. portal.wav, or
portal_1.wav / portal_2.wav for variations) and it's picked up automatically.
Events with no sound are silently skipped.
"""
import random

import pygame

from core.settings import AUDIO_DIR

SFX_DIR = AUDIO_DIR / "sfx"
SFX_VOLUME = 0.7
EXTENSIONS = (".wav", ".ogg", ".mp3")
CHANNELS = 24          # enough for layered hits + effects without cutting each other off

# event: ((files...), volume). Files are from the Deadly Kombat Free Library.
SOUNDS = {
    # Charlie's swings and hits
    "whoosh": (("punch_short_whoosh_16.wav", "punch_short_whoosh_30.wav"), 0.55),     # jab swing, bomb toss
    "swing_heavy": (("punch_long_whoosh_21.wav", "punch_long_whoosh_30.wav"), 0.6),   # haymaker / uppercut
    "punch": (("face_hit_small_01.wav", "face_hit_small_13.wav", "face_hit_small_23.wav",
               "body_hit_small_20.wav"), 0.8),                                         # jab lands
    "punch_heavy": (("face_hit_Large_20.wav", "face_hit_Large_29.wav", "face_hit_Large_78.wav",
                     "body_hit_large_44.wav"), 0.85),                                  # haymaker lands
    "crit": (("face_hit_finisher_19.wav", "face_hit_finisher_40.wav", "face_hit_finisher_61.wav",
              "face_hit_finisher_73.wav"), 0.9),                                       # PERFECT-timed hit
    "super": (("body_hit_finisher_23.wav", "body_hit_finisher_27.wav", "body_hit_finisher_52.wav"), 1.0),
    "super_crack": (("wood_bat_finisher_01.wav", "wood_bat_finisher_05.wav"), 0.7),    # layered on the Chin Check
    "miss": (("punch_long_whoosh_30.wav",), 0.6),                                      # haymaker whiffs
    "phase": (("punch_long_whoosh_21.wav",), 0.5),                                     # punch sails through a ghost
    "dodge": (("somersault_01.wav", "somersault_10.wav"), 0.8),                        # slide out of a parry
    "counter": (("body_hit_large_32.wav", "body_hit_large_76.wav"), 0.85),             # slide-kick counter lands
    "ko": (("bone_breaking_03.wav", "bone_breaking_53.wav"), 0.9),                     # knockout crunch
    # Defense
    "parry": (("metal_punch_06.wav", "block_large_59.wav", "block_large_71.wav"), 0.9),
    "block": (("block_medium_09.wav", "block_medium_25.wav", "block_small_69.wav", "block_small_73.wav"), 0.8),
    "hurt": (("body_hit_small_11.wav", "body_hit_small_23.wav", "body_hit_small_79.wav",
              "face_hit_small_78.wav"), 0.75),                                         # Charlie takes a hit
    "hurt_heavy": (("body_hit_large_32.wav", "body_hit_large_76.wav", "face_hit_Large_78.wav"), 0.85),
    # What enemy attacks feel like when they land (layered on "hurt")
    "bite": (("guts_and_gore_59.wav", "guts_and_gore_68.wav"), 0.9),                   # zombies
    "slash": (("blade_hit_07.wav", "blade_hit_08.wav"), 0.7),                          # knights, reaper, demon
    "burn": (("fire_punch_02.wav",), 0.7),                                             # fire, and catching fire
    "explosion": (("fire_punch_finisher_06.wav",), 0.9),                               # bombs, fireballs
    "metal_clang": (("metal_punch_finisher_07.wav",), 0.6),                            # sloppy hit off armor
    "gore": (("guts_and_gore_19.wav",), 0.6),                                          # zombie goes down
    # Enemy swings (wind-up)
    "zombie_bite": (("kick_short_whoosh_12.wav",), 0.5),
    "knight_slash": (("punch_long_whoosh_21.wav",), 0.6),
    "knight_charge": (("kick_short_whoosh_23.wav",), 0.6),
    "reaper_slash": (("punch_long_whoosh_30.wav",), 0.6),
    "demon_cleave": (("punch_long_whoosh_21.wav",), 0.75),
    "satyr_attack": (("kick_short_whoosh_12.wav",), 0.5),
    "worm_spit": (("fire_punch_02.wav",), 0.45),
    "satyr_beam": (("fire_punch_02.wav",), 0.4),
    "warlock_cast": (("punch_long_whoosh_30.wav",), 0.5),
    "reaper_grasp": (("punch_long_whoosh_21.wav",), 0.5),
    "enrage": (("kick_long_whoosh_19.wav",), 0.6),                                     # boss powers up
    "defeat": (("body_hit_finisher_42.wav",), 0.9),                                    # Charlie goes down
    "anvil": (("metal_punch_06.wav",), 0.3),                                           # Blacksmith's hammer (camp)
    # Movement
    "jump": (("kick_short_whoosh_12.wav",), 0.35),
    "slide": (("kick_short_whoosh_23.wav",), 0.5),
    # Menus
    "ui_error": (("block_small_69.wav",), 0.35),                                       # can't buy / can't use
}

EVENTS = {
    # Charlie
    "whoosh": "Charlie dashes in / swings / throws",
    "punch": "Jab lands",
    "punch_heavy": "Haymaker or Chin Check lands",
    "swing_heavy": "Haymaker / Chin Check wind-up",
    "crit": "A PERFECT-timed hit lands",
    "super": "The Chin Check lands (layered with super_crack)",
    "super_crack": "Extra crack on the Chin Check",
    "phase": "A punch sails through a ghost",
    "dodge": "Charlie slides out of a parry",
    "counter": "The slide-kick counter lands",
    "hurt_heavy": "Charlie takes a heavy hit",
    "bite": "A zombie bite lands",
    "slash": "A blade lands (knights, Mortis, Malgorath)",
    "metal_clang": "A sloppy punch glances off armor",
    "gore": "A zombie goes down",
    "ui_error": "Can't buy / can't use that",
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
    "knight_slash": "Death Knight swings its sword",
    "knight_charge": "Death Knight's horse charges / neighs while patrolling",
    "anvil": "Blacksmith's hammer hits the anvil in camp",
    "crow_caw": "The Crow greets Charlie in camp",
    "satyr_attack": "Satyr's fiery scratch",
    "satyr_beam": "Satyr's antler beam",
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
        files, volume = SOUNDS.get(name, ((), 1.0))
        candidates = [SFX_DIR / f for f in files]
        candidates += [SFX_DIR / f"{name}{ext}" for ext in EXTENSIONS]
        candidates += sorted(p for p in SFX_DIR.glob(f"{name}_*") if p.suffix.lower() in EXTENSIONS)
        for path in candidates:
            if path.is_file():
                try:
                    sound = pygame.mixer.Sound(str(path))
                    sound.set_volume(SFX_VOLUME * (volume if path.name in files else 1.0))
                    sounds.append(sound)
                except pygame.error as err:
                    print(f"[sfx] Couldn't load {path.name}: {err}")
    _cache[name] = sounds
    return sounds


master = 1.0     # the Settings menu's sound-effect volume (0-1)


def set_master(volume):
    global master
    master = max(0.0, min(1.0, volume))


def play(name, volume=1.0):
    """Play a sound effect by event name if its file exists (no-op otherwise)."""
    if not pygame.mixer.get_init() or master <= 0:
        return
    if pygame.mixer.get_num_channels() < CHANNELS:
        pygame.mixer.set_num_channels(CHANNELS)
    sounds = _load(name)
    if sounds:
        sound = random.choice(sounds)
        channel = sound.play()
        if channel:
            channel.set_volume(volume * master)
