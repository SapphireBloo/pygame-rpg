"""Game-wide constants. Tweak numbers here instead of hunting through files."""
from pathlib import Path

# Window
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Chin Check Charlie"
FULLSCREEN = True          # start fullscreen; F11 or Alt+Enter toggles while playing

# Paths are built from this file's location, so the game runs no matter
# which folder you launch it from.
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
AUDIO_DIR = ASSETS_DIR / "audio"

MUSIC_FILE = AUDIO_DIR / "background_music.mp3"
MUSIC_VOLUME = 0.4

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
CAMERA_LEAD = 250          # how far from the left edge the hero sits on screen
GHOST_SPACING = 800        # distance between ghost encounters (ghost count is per level)
GHOST_TRIGGER_RANGE = 100  # how close the hero must get to wake a ghost

# Battle
TURN_DELAY_MS = 600        # pause between turns
GRIT = True                # color grading, grain, vignette and fog (set False to turn off)
