"""Which animations each enemy type uses, how big the bosses are, and how each
one sits in a battle. Battles and the exploration scene both ask here, so
adding a new monster is done in one place.

Boss art folders (assets/images):
  death/      Mortis, Bringer of Death  - The Cabin
  warlock/    Grimwald the Warlock      - Warlock's Hollow
  fire worm/  Scorchmaw the Fire Worm   - The Bleeding Woods
  demon/      Malgorath the Demon       - The Graveyard (final boss)

Regular monsters (they roam the levels, see core/roaming_enemy.py):
  ghost_idle/     Ghosts        - The Cabin
  death knight/   Death Knights - Warlock's Hollow
  satyr/          Satyrs        - The Bleeding Woods
  male/ female/   Zombies       - The Graveyard
"""
import json
from functools import lru_cache

import pygame

from core.animation import (Animation, frames_animation, load_gameart2d_character, load_strip_character,
                            load_pixel_character, slice_grid, slice_strip, effect_animation)
from core.assets import load_sprite_sheet, tinted
from core.settings import ZOMBIE_HEIGHT, CHARACTER_INK, IMAGES_DIR

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
    # regular monsters
    "knight": {"mid": 95, "gap": 165, "home_x": 635, "shadow": 1.7, "hit_point": 0.41,
               "sparks": [(220, 225, 240), (140, 150, 180), (255, 255, 255)],
               "sounds": {"attack": "knight_slash", "heavy": "knight_charge"}},
    "satyr": {"mid": 65, "gap": 120, "hit_point": 0.5,
              "sparks": [(200, 60, 90), (255, 150, 60), (90, 30, 50)],
              "sounds": {"attack": "satyr_attack", "heavy": "satyr_beam"}},
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

# ---- regular monsters ----------------------------------------------------
SATYR_HEIGHT = 140
SATYR_SHEET = "satyr/SPRITE_SHEET.png"      # 32x32 pixel-art frames, 10 per row
SATYR_FRAMES = (("idle", 0, 6), ("walk", 10, 8), ("attack", 30, 7), ("dead", 60, 10), ("hit", 70, 4),
                ("attack2", 90, 20))        # attack2 = the antler beam (its heavy attack)
SATYR_BRIGHTEN = (45, 30, 40)               # added to its colors so it reads against the Bleeding Woods
SATYR_SPEEDS = (("idle", 130), ("walk", 90), ("attack", 85), ("attack2", 55), ("dead", 100), ("hit", 90))

KNIGHT_HEIGHT = 185                          # mounted, so a bit taller than a zombie
KNIGHT_FOLDER = "death knight"               # hi-res 448x448 frames with timings in animations.json
KNIGHT_TICK_MS = 42                          # frames are repeated to match their listed durations


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


@lru_cache(maxsize=None)
def _satyr_animations():
    raw = {name: slice_grid(SATYR_SHEET, 32, 32, start, n) for name, start, n in SATYR_FRAMES}
    for frames in raw.values():           # its dark reds vanish in the red woods: lift them a little
        for i, frame in enumerate(frames):
            frames[i] = frame.copy()
            frames[i].fill(SATYR_BRIGHTEN, special_flags=pygame.BLEND_RGB_ADD)
    return load_pixel_character(raw, SATYR_HEIGHT, SATYR_SPEEDS, CHARACTER_INK)


@lru_cache(maxsize=None)
def _knight_animations():
    """The Death Knight is smooth (not pixel) art, so it's scaled with smoothing.
    The pack only has walk and attack: idle is his standing pose, and his death
    (rearing back, then crumbling into the ground) is built here from that pose."""
    meta = json.loads((IMAGES_DIR / KNIGHT_FOLDER / "animations.json").read_text(encoding="utf-8"))
    ax, ay = meta["anchor"]["pixel"]
    raw = {name: [(pygame.image.load(IMAGES_DIR / KNIGHT_FOLDER / f["file"]).convert_alpha(), f["durationMs"])
                  for f in action["frames"]]
           for name, action in meta["actions"].items()}
    scale = KNIGHT_HEIGHT / raw["walk"][0][0].get_bounding_rect().height

    def build(frames, loop):
        used = None
        for image, _ in frames:
            box = image.get_bounding_rect()
            used = box if used is None else used.union(box)
        used = used.inflate(4, 4).clip(frames[0][0].get_rect())
        size = (round(used.width * scale), round(used.height * scale))
        sequence = []
        for image, ms in frames:
            scaled = pygame.transform.smoothscale(image.subsurface(used), size)
            sequence += [scaled] * max(1, round(ms / KNIGHT_TICK_MS))   # same surface, no extra memory
        anchor = ((ax - used.left) * scale, (ay - used.top) * scale)
        return Animation(tuple(sequence), anchor, KNIGHT_TICK_MS, loop)

    walk = build(raw["walk"], True)
    attack = build(raw["attack"], False)
    stand = raw["walk"][0][0]
    idle = build([(stand, 400)], True)
    dying = []
    for k in range(14):
        t = k / 13
        frame = stand.copy()
        frame.fill((int(255 - 150 * t),) * 3 + (255,), special_flags=pygame.BLEND_RGBA_MULT)   # darken
        frame.fill((255, 255, 255, int(255 * (1 - t) ** 0.7)), special_flags=pygame.BLEND_RGBA_MULT)  # fade
        w, h = frame.get_size()
        sink = pygame.Surface((w, h), pygame.SRCALPHA)
        squash = max(1, round(h * (1 - 0.35 * t)))
        sink.blit(pygame.transform.smoothscale(frame, (w, squash)), (0, h - squash + round(18 * t)))
        dying.append((sink, 70))
    dead = build(dying, False)
    return {"idle": idle, "walk": walk, "attack": attack, "dead": dead}


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
    if sprite == "satyr":
        return _satyr_animations()
    if sprite == "knight":
        return _knight_animations()
    return load_gameart2d_character(sprite, ZOMBIE_HEIGHT, ink=CHARACTER_INK)   # male / female zombies


def battle_layout(sprite):
    return {**DEFAULT_LAYOUT, **BATTLE_LAYOUT.get(sprite, {})}


def faces_right_in_battle(sprite):
    """Most art faces right and gets mirrored to face Charlie; the ghost sheet already faces him."""
    return sprite == "ghost"


def art_faces_left(sprite):
    """The ghost sheet is drawn facing left (everything else faces right)."""
    return sprite == "ghost"
