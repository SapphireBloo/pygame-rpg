"""Which animations each enemy type uses, how big the bosses are, and how each
one sits in a battle. Battles and the exploration scene both ask here, so
adding a new monster is done in one place.

Boss art folders (assets/images):
  death/      Mortis, Bringer of Death  - The Cabin
  warlock/    Grimwald the Warlock      - Warlock's Hollow
  fire worm/  Scorchmaw the Fire Worm   - The Bleeding Woods
  demon/      Malgorath the Demon       - The Graveyard (final boss)
"""
from functools import lru_cache

from core.animation import (frames_animation, load_gameart2d_character, load_strip_character,
                            load_pixel_character, slice_grid, slice_strip, effect_animation)
from core.assets import load_sprite_sheet, tinted
from core.settings import ZOMBIE_HEIGHT, CHARACTER_INK

# How tall each boss's idle pose stands, in pixels (Charlie is about 138).
# Bigger number = bigger boss. The art scales with crisp nearest-neighbor pixels.
BOSS_HEIGHTS = {
    "death": 330,
    "warlock": 340,
    "fireworm": 290,     # long and low: this is about where its head flame reaches
    "demon": 400,        # the final boss gets to be the biggest
}

# How a monster sits in a battle.
#   mid        pixels above the feet where hits land (body center)
#   gap        how far in front of the monster's feet Charlie stands to punch
#   aura       (width, height) of the glow behind a boss, or None
#   home_x     where the monster's feet rest
#   shadow     ground-shadow width (1.0 = Charlie-sized)
#   hit_point  how far through its attack animation the blow lands (0-1)
#   glow       boss color: aura, enrage, intro burst
#   sparks     particle colors when it gets hit
#   intro      animation it shows off when the fight starts / after its taunt
#   sounds     sound events (see core/sfx.py): taunt laugh, attack, heavy attack
DEFAULT_LAYOUT = {"mid": 80, "gap": 125, "aura": None, "home_x": 625, "shadow": 1.0, "hit_point": 0.55,
                  "glow": (190, 90, 255), "sparks": None, "intro": "attack", "sounds": {}}
BATTLE_LAYOUT = {
    "death": {"mid": 160, "gap": 190, "aura": (380, 480), "home_x": 640, "shadow": 1.7, "hit_point": 0.45,
              "glow": (150, 110, 230), "sparks": [(150, 110, 230), (70, 55, 90), (220, 210, 240)],
              "intro": "attack2",
              "sounds": {"laugh": "reaper_laugh", "attack": "reaper_slash", "heavy": "reaper_grasp"}},
    "warlock": {"mid": 170, "gap": 200, "aura": (420, 530), "home_x": 640, "shadow": 2.0,
                "glow": (190, 90, 255), "sparks": [(190, 90, 255), (90, 30, 140)], "intro": "attack2",
                "sounds": {"laugh": "warlock_laugh", "attack": "warlock_cast", "heavy": "warlock_cast"}},
    "fireworm": {"mid": 120, "gap": 220, "aura": (460, 400), "home_x": 630, "shadow": 2.8, "hit_point": 0.66,
                 "glow": (255, 120, 40), "sparks": [(255, 150, 40), (255, 220, 90), (140, 30, 20)],
                 "intro": "attack",
                 "sounds": {"laugh": "worm_roar", "attack": "worm_spit", "heavy": "worm_spit"}},
    "demon": {"mid": 190, "gap": 215, "aura": (480, 600), "home_x": 650, "shadow": 2.4, "hit_point": 0.62,
              "glow": (255, 80, 30), "sparks": [(255, 120, 30), (255, 210, 80), (120, 20, 10)],
              "intro": "attack",
              "sounds": {"laugh": "demon_roar", "attack": "demon_cleave", "heavy": "demon_cleave"}},
}

WARLOCK_STRIPS = (
    ("idle", "Idle.png"), ("attack", "Attack1.png"), ("attack2", "Attack2.png"),
    ("hit", "Take hit.png"), ("dead", "Death.png"),
)
WARLOCK_SPEEDS = (("idle", 110), ("attack", 85), ("attack2", 95), ("dead", 130), ("hit", 90))

DEATH_SHEET = "death/SpriteSheet/Bringer-of-Death-SpritSheet.png"     # 140x93 frames, 8 per row
DEATH_FRAMES = (("idle", 0, 8), ("attack", 16, 10), ("hit", 26, 3), ("dead", 29, 10), ("attack2", 39, 9))
DEATH_SPELL = (48, 16)                                                 # the hand from the portal
DEATH_SPEEDS = (("idle", 110), ("attack", 80), ("attack2", 95), ("dead", 120), ("hit", 90))

WORM_STRIPS = (("idle", "Idle.png"), ("attack", "Attack.png"), ("hit", "Get Hit.png"), ("dead", "Death.png"))
WORM_SPEEDS = (("idle", 100), ("attack", 70), ("hit", 90), ("dead", 120))

DEMON_SHEET = "demon/spritesheets/demon_slime_FREE_v1.0_288x160_spritesheet.png"   # 288x160, 22 per row
DEMON_FRAMES = (("idle", 0, 6), ("attack", 44, 15), ("hit", 66, 5), ("dead", 88, 22))
DEMON_SPEEDS = (("idle", 120), ("attack", 70), ("hit", 80), ("dead", 75))


def boss_scale(sprite):
    """Pixel-art scale factor a boss is drawn at (effects use the same)."""
    raw_idle_height = {"death": 54, "warlock": 95, "fireworm": 41, "demon": 105}[sprite]
    return BOSS_HEIGHTS[sprite] / raw_idle_height


@lru_cache(maxsize=2)   # bosses are big: keep only the most recent couple in memory
def _boss_animations(sprite):
    h, ink = BOSS_HEIGHTS[sprite], CHARACTER_INK
    if sprite == "warlock":
        return load_strip_character("warlock/Sprites", h, WARLOCK_STRIPS, WARLOCK_SPEEDS, ink)
    if sprite == "death":
        raw = {name: slice_grid(DEATH_SHEET, 140, 93, start, n) for name, start, n in DEATH_FRAMES}
        return load_pixel_character(raw, h, DEATH_SPEEDS, ink, faces="left")
    if sprite == "fireworm":
        return load_strip_character("fire worm/Sprites/Worm", h, WORM_STRIPS, WORM_SPEEDS, ink)
    if sprite == "demon":
        raw = {name: slice_grid(DEMON_SHEET, 288, 160, start, n) for name, start, n in DEMON_FRAMES}
        return load_pixel_character(raw, h, DEMON_SPEEDS, ink, faces="left")
    raise KeyError(sprite)


@lru_cache(maxsize=4)
def boss_effects(sprite):
    """Extra one-shot effect animations a boss uses for its heavy attack."""
    if sprite == "death":
        frames = slice_grid(DEATH_SHEET, 140, 93, *DEATH_SPELL)
        return {"spell": effect_animation(frames, boss_scale("death") * 0.85, 70, faces="left")}
    if sprite == "fireworm":
        scale = boss_scale("fireworm") * 0.6
        return {"fireball": effect_animation(slice_strip("fire worm/Sprites/Fire Ball/Move.png"), scale, 70,
                                             anchor="center"),
                "explosion": effect_animation(slice_strip("fire worm/Sprites/Fire Ball/Explosion.png"),
                                              scale * 1.3, 60, anchor="center")}
    return {}


def is_boss_sprite(sprite):
    return sprite in BOSS_HEIGHTS


def enemy_animations(sprite, tint=None):
    """{"idle": Animation, ...} for an enemy spec's "sprite" value."""
    if sprite == "ghost":
        idle = tinted(load_sprite_sheet("ghost_idle/ghost_idle.png", 32, 32), tint)
        death = tuple(reversed(tinted(load_sprite_sheet("ghost_spawn/ghost_spawn.png", 32, 32), tint)))
        return {
            "idle": frames_animation(idle, 250, feet_y_in_frame=144),
            "dead": frames_animation(death, 200, loop=False, feet_y_in_frame=144),
        }
    if is_boss_sprite(sprite):
        return _boss_animations(sprite)
    return load_gameart2d_character(sprite, ZOMBIE_HEIGHT, ink=CHARACTER_INK)   # male / female zombies


def battle_layout(sprite):
    return {**DEFAULT_LAYOUT, **BATTLE_LAYOUT.get(sprite, {})}


def faces_right_in_battle(sprite):
    """Most art faces right and gets mirrored to face Charlie; the ghost sheet already faces him."""
    return sprite == "ghost"
