"""Which animations each enemy type uses, how big the bosses are, and how each
one sits in a battle. Battles and the exploration scene both ask here, so
adding a new monster is done in one place.

Boss art folders (assets/images):
  death/      Mortis, Bringer of Death  - The Cabin
  warlock/    Grimwald the Warlock      - Warlock's Hollow
  fire worm/  Scorchmaw the Fire Worm   - The Bleeding Woods
  demon/      Malgorath the Demon       - The Graveyard
  bully/      Gorge, Taker of Worlds    - The Void (the true final boss)

Regular monsters (they roam the levels, see core/roaming_enemy.py):
  ghost_idle/     Ghosts        - The Cabin
  death knight/   Death Knights - Warlock's Hollow
  satyr/          Satyrs        - The Bleeding Woods
  male/ female/   Zombies       - The Graveyard
  void/           Catto, the Mad Ghost, the Mage, the Abomination - The Void
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
    "bread": 300,        # Crumb, the secret boss (he RISES taller each phase: see CRUMB_PHASES)
    "gorge": 420,        # Gorge, Taker of Worlds: the true final boss is the biggest of all
}

# Crumb's three phases: (height on screen, color tint): bread, toast, burnt toast
CRUMB_PHASES = {1: (300, None), 2: (330, (230, 170, 115)), 3: (360, (135, 88, 68))}

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
    "bread": {"mid": 150, "gap": 205, "aura": (440, 440), "home_x": 640, "shadow": 2.6, "hit_point": 0.62,
              "glow": (255, 190, 90), "sparks": [(255, 225, 150), (225, 165, 95), (255, 250, 225)],
              "intro": "attack", "sounds": {"laugh": "enrage", "attack": "swing_heavy", "heavy": "swing_heavy"}},
    "gorge": {"mid": 200, "gap": 210, "aura": (470, 560), "home_x": 650, "shadow": 2.6, "hit_point": 0.6,
              "glow": (255, 90, 160), "sparks": [(255, 120, 180), (255, 220, 120), (120, 60, 140)],
              "intro": "attack2", "sounds": {"laugh": "enrage", "attack": "swing_heavy", "heavy": "swing_heavy"}},
    "catto": {"mid": 45, "gap": 110, "hit_point": 0.5, "shadow": 0.8,
              "sparks": [(255, 40, 90), (40, 30, 50)]},
    "madghost": {"mid": 95, "gap": 140, "hit_point": 0.7, "shadow": 1.2,
                 "sparks": [(255, 40, 90), (230, 230, 240)]},
    "mage": {"mid": 85, "gap": 130, "hit_point": 0.6, "shadow": 1.1,
             "sparks": [(255, 40, 90), (230, 230, 240)]},
    "abomination": {"mid": 90, "gap": 150, "hit_point": 0.55, "shadow": 1.8,
                    "sparks": [(255, 40, 90), (40, 30, 50)]},
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


# ---- The Void ------------------------------------------------------------
# The four Void creatures (AshDeal's horror pack): (sheet, frame w, h, rows as (name, frames)),
# and how tall each stands on screen. They're near-black, so they get a pale outline to read
# against the dark nebula.
VOID_SHEETS = {
    "catto": ("void/Catto/Cat monster-Sheet Separated tags.png", 48, 32,
              (("stare", 1), ("stand", 2), ("walk", 4), ("turn", 5), ("sit", 2), ("idle", 4), ("attack", 6),
               ("hit", 2), ("dead", 9))),
    "madghost": ("void/Mad Ghost/Mad Ghost-Sheet Separated tags.png", 64, 64,
                 (("idle", 4), ("walk", 4), ("draw", 5), ("slash", 3), ("sheathe", 4), ("hit", 2), ("dead", 9))),
    "mage": ("void/Mage/Mage-Sheet Separated Tags.png", 112, 48,
             (("idle", 4), ("walk", 4), ("attack", 10), ("hit", 2), ("dead", 9))),
    "abomination": ("void/Abomination/Abomination-Sheet Separated Tags.png", 112, 48,
                    (("idle", 4), ("walk", 4), ("attack", 9), ("hit", 2), ("dead", 9))),
}
VOID_HEIGHTS = {"catto": 72, "madghost": 190, "mage": 170, "abomination": 175}
VOID_SPEEDS = (("idle", 150), ("walk", 120), ("attack", 85), ("hit", 100), ("dead", 95))
VOID_RIM = (205, 175, 255)        # the pale outline

# Gorge: 40x40 walk/transform frames and 50x50 punch frames, lined up on one 50x50 canvas.
GORGE_WALK = "bully/RageWalk.png"
GORGE_TRANSFORM = "bully/RageTransformation.png"
GORGE_HIT = "bully/RageHitRightFront.png"
GORGE_SPEEDS = (("idle", 160), ("walk", 120), ("attack", 80), ("attack2", 90), ("hit", 100),
                ("transform", 105), ("dead", 95), ("arrive", 130), ("spotlight", 160))
# His spotlight: the kid steps into a pool of light (entry), and when he's beaten he shrinks back into it,
# slumps, and is squeezed down to nothing (death). The sheets' FIRED / NEW EMPLOYEE frames aren't used.
GORGE_SPOT = "bully/rageDeathOutro.png"          # 7 x 7 grid of 40x40 frames
GORGE_SLUMP = "bully/rageDeathIntro.png"         # 3 x 3 grid; frame 0 is him slumped in the light
SPOT_ARRIVE = range(24, 29)      # a sliver of light opens into a spotlight with the kid standing in it
SPOT_WAIT = range(28, 33)        # standing in the light
SPOT_FADE = range(6, 21)         # slumped in the light, squeezed down to a sliver, gone
# The spotlight art sits on solid black with a gray cone (a dim yellow one when he's beaten). The black
# goes, and the cone and the pool on the floor become see-through light drawn behind him.
SPOT_LIGHT = {(64, 64, 64): (215, 225, 255, 55), (122, 122, 122): (215, 225, 255, 105),
              (68, 63, 46): (255, 210, 140, 50), (124, 109, 55): (255, 210, 140, 95)}


def _rim(frame, color):
    """A 1-pixel outline (at the art's own scale) in a light color, so dark art stands out."""
    silhouette = frame.copy()
    silhouette.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MIN)
    silhouette.fill((*color, 0), special_flags=pygame.BLEND_RGBA_MAX)
    out = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        out.blit(silhouette, (dx, dy))
    out.blit(frame, (0, 0))
    return out


@lru_cache(maxsize=None)
def _void_animations(sprite):
    sheet_file, fw, fh, rows = VOID_SHEETS[sprite]
    sheet = pygame.image.load(IMAGES_DIR / sheet_file).convert_alpha()
    raw = {}
    for r, (name, n) in enumerate(rows):
        raw[name] = [_rim(sheet.subsurface((c * fw, r * fh, fw, fh)).copy(), VOID_RIM) for c in range(n)]
    if sprite == "madghost":                   # draws its blades, slashes, sheathes them
        raw["attack"] = raw.pop("draw") + raw.pop("slash") + raw.pop("sheathe")
    return load_pixel_character(raw, VOID_HEIGHTS[sprite], VOID_SPEEDS, 0)


def _gorge_raw():
    return _gorge_split()[0]


@lru_cache(maxsize=1)
def _gorge_split():
    """Gorge's frames ({name: [frames]}), and the spotlight that goes behind some of them
    ({name: [frames]}, one light frame per character frame)."""
    canvas = 50

    def cells(path, size, count):
        sheet = pygame.image.load(IMAGES_DIR / path).convert_alpha()
        cols = sheet.get_width() // size
        out = []
        for i in range(count):
            frame = sheet.subsurface(((i % cols) * size, (i // cols) * size, size, size))
            pad = pygame.Surface((canvas, canvas), pygame.SRCALPHA)
            pad.blit(frame, ((canvas - size) // 2, (canvas - size) // 2))   # (feet land on the same spot)
            out.append(pad)
        return out

    def spot(path, i, cols, drop):
        """One spotlight frame split into (kid, light), moved down `drop` px so his feet match the other sheets."""
        sheet = pygame.image.load(IMAGES_DIR / path).convert_alpha()
        x0, y0 = (i % cols) * 40, (i // cols) * 40
        kid = pygame.Surface((canvas, canvas), pygame.SRCALPHA)
        light = pygame.Surface((canvas, canvas), pygame.SRCALPHA)
        off = (canvas - 40) // 2
        for y in range(40):
            for x in range(40):
                c = sheet.get_at((x0 + x, y0 + y))
                rgb = (c.r, c.g, c.b)
                if c.a == 0 or rgb == (0, 0, 0):
                    continue
                if rgb in SPOT_LIGHT:
                    light.set_at((x + off, y + off + drop), SPOT_LIGHT[rgb])
                else:
                    kid.set_at((x + off, y + off + drop), c)
        return kid, _beam(light)

    def faded(light, k):
        out = light.copy()
        out.fill((255, 255, 255, int(255 * k)), special_flags=pygame.BLEND_RGBA_MULT)
        return out

    walk = cells(GORGE_WALK, 40, 20)
    grow = cells(GORGE_TRANSFORM, 40, 17)
    hits = cells(GORGE_HIT, 50, 11)
    arrive = [spot(GORGE_SPOT, i, 7, 3) for i in SPOT_ARRIVE]
    wait = [spot(GORGE_SPOT, i, 7, 3) for i in SPOT_WAIT]
    slump = spot(GORGE_SLUMP, 0, 3, 1)
    fade = [spot(GORGE_SPOT, i, 7, 1) for i in SPOT_FADE]
    cone = wait[0][1]
    nothing = pygame.Surface((canvas, canvas), pygame.SRCALPHA)
    # dead: he shrinks back into the kid as the light comes up, stands there a moment, slumps, and fades out
    shrink = list(reversed(grow))
    dead = shrink + [wait[0][0]] * 3 + [slump[0]] * 4 + [f[0] for f in fade]
    dead_light = ([nothing] * (len(shrink) - 5) + [faded(cone, k / 5) for k in range(1, 6)] + [cone] * 3
                  + [slump[1]] * 4 + [f[1] for f in fade])
    frames = {"idle": walk[0:4], "walk": walk[4:8], "attack": hits[0:6], "attack2": hits[6:11],
              "hit": [walk[0], walk[2]], "transform": grow, "dead": dead,
              "arrive": [f[0] for f in arrive], "spotlight": [f[0] for f in wait]}
    lights = {"idle": walk[0:1],               # (only there so the light lines up with him: never drawn)
              "arrive": [f[1] for f in arrive], "spotlight": [f[1] for f in wait],
              "transform": [faded(cone, 1 - k / 5) for k in range(5)] + [nothing] * (len(grow) - 5),
              "dead": dead_light}
    return frames, lights


def _beam(light):
    """Tidy a spotlight layer: fill the art's dithered (checkerboard) edges in at half strength, so they
    read as a soft edge over the starfield instead of a grid, and carry the beam up off the top of the frame."""
    w, h = light.get_size()
    src = light.copy()
    for y in range(h):
        for x in range(w):
            if src.get_at((x, y)).a:
                continue
            near = [src.get_at((nx, ny)) for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
                    if 0 <= nx < w and 0 <= ny < h and src.get_at((nx, ny)).a]
            if len(near) >= 3:
                c = near[0]
                light.set_at((x, y), (c.r, c.g, c.b, c.a // 2))
    for top in range(h):                        # the beam's first solid row in the art (no gaps across it)...
        lit = [x for x in range(w) if src.get_at((x, top)).a]
        if len(lit) >= 3 and len(lit) == lit[-1] - lit[0] + 1:
            break
    else:
        return light
    for y in range(top):                        # ...carried straight up: the light comes from somewhere above
        for x in lit:
            light.set_at((x, y), src.get_at((x, top)))
    return light


@lru_cache(maxsize=1)
def _gorge_lights():
    return load_pixel_character(_gorge_split()[1], BOSS_HEIGHTS["gorge"], GORGE_SPEEDS, 0)


def draw_spotlight(screen, sprite_name, sprite, feet_x, feet_y, facing_right):
    """The light behind a boss (only Gorge has one), matched to whatever he's doing.
    Returns True if there was any light to draw."""
    if sprite_name != "gorge":
        return False
    anim = _gorge_lights().get(sprite.name)
    if anim is None or sprite.name == "idle":
        return False
    surface, (ax, ay) = anim.frame(min(sprite.index, len(anim) - 1), facing_right)
    screen.blit(surface, (round(feet_x - ax), round(feet_y - sprite.lift - ay)))
    return True


def boss_scale(sprite):
    """Pixel-art scale factor a boss is drawn at (effects use the same)."""
    raw_idle_height = {"death": 54, "warlock": 95, "fireworm": 41, "demon": 105, "bread": 27, "gorge": 30}[sprite]
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
    if sprite == "bread":
        return crumb_boss_animations(1)
    if sprite == "gorge":
        return load_pixel_character(_gorge_raw(), h, GORGE_SPEEDS, ink)
    raise KeyError(sprite)


@lru_cache(maxsize=3)
def crumb_boss_animations(phase):
    """Crumb as a towering boss: bigger and toastier each phase. His attack is a jump and a
    body slam; when he's beaten he shrinks back down to snack size."""
    from core.camp import bread_frames
    height, tint = CRUMB_PHASES[phase]
    raw = bread_frames()
    idle0 = raw["idle"][0]
    raw["attack"] = [raw["jump"][0], raw["jump"][0], raw["jump"][2], raw["jump"][2], idle0]
    raw["dead"] = [_shrunk(idle0, k) for k in (1.0, 0.82, 0.64, 0.48, 0.36, 0.28, 0.28)]
    if tint:
        raw = {name: [_tint(f, tint) for f in frames] for name, frames in raw.items()}
    speeds = (("idle", 170), ("walk", 110), ("jump", 120), ("attack", 95), ("dead", 140))
    return load_pixel_character(raw, height, speeds, CHARACTER_INK)


def _shrunk(frame, k):
    """The frame scaled down by k, standing on the same spot (for shrinking back to normal)."""
    box = frame.get_bounding_rect()
    art = frame.subsurface(box)
    small = pygame.transform.scale(art, (max(1, round(box.width * k)), max(1, round(box.height * k))))
    out = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
    out.blit(small, small.get_rect(midbottom=(box.centerx, box.bottom)))
    return out


def _tint(frame, tint):
    out = frame.copy()
    out.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
    return out


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
    if sprite in VOID_SHEETS:
        return _void_animations(sprite)
    return load_gameart2d_character(sprite, ZOMBIE_HEIGHT, ink=CHARACTER_INK)   # male / female zombies


def battle_layout(sprite):
    return {**DEFAULT_LAYOUT, **BATTLE_LAYOUT.get(sprite, {})}


def faces_right_in_battle(sprite):
    """Most art faces right and gets mirrored to face Charlie; the ghost sheet already faces him."""
    return sprite == "ghost"


def art_faces_left(sprite):
    """The ghost sheet is drawn facing left (everything else faces right)."""
    return sprite == "ghost"
