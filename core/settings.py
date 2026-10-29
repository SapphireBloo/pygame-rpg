"""Game-wide constants. Tweak numbers here instead of hunting through files."""
from pathlib import Path

# Window
SCREEN_WIDTH = 1066        # widescreen 16:9 (fills a normal monitor without black bars)
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Chin Check Charlie"
# Fullscreen, volumes, and difficulty are player settings now: see core/options.py (Settings menu)

# Paths are built from this file's location, so the game runs no matter
# which folder you launch it from.
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
AUDIO_DIR = ASSETS_DIR / "audio"

MUSIC_FILE = AUDIO_DIR / "background_music.mp3"
MUSIC_VOLUME = 0.4
# Which song plays where: (file, loudness adjustment). The game crossfades between them.
MUSIC_TRACKS = {
    "level": (MUSIC_FILE, 1.0),                    # walking around the chapters (and regular fights)
    "camp": (AUDIO_DIR / "ominous.wav", 1.6),      # The Camp (this track is mixed quieter, so it's boosted)
    "boss": (AUDIO_DIR / "boss.ogg", 1.0),         # from a boss's taunt until the victory screen is closed
}

# Art
FONT_NAME = "consolas"
SPRITE_SIZE = (150, 150)
GROUND_Y = 400  # top of the 150px hero sprite
FEET_Y = GROUND_Y + 144  # where everyone's feet touch the ground
ZOMBIE_HEIGHT = 145      # on-screen height of a standing zombie
HERO_HEIGHT = 138        # on-screen height of Charlie standing
CHARACTER_INK = 3        # thickness of the dark outline drawn around characters (0 = off)

# Exploration
WALK_SPEED = 300           # pixels per second
RUN_SPEED = 480            # holding Shift
SLIDE_SPEED = 620          # during a slide (S / Down)
CAMERA_LEAD = 330          # how far from the left edge the hero sits on screen
MONSTER_SPACING = 800      # distance between each roaming monster's home spot (and the boss)

# Battle
TURN_DELAY_MS = 600        # pause between turns
GRIT = True                # color grading, grain, vignette and fog (set False to turn off)
