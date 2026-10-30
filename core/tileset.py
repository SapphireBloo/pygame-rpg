"""Art from the GandalfHardcore tileset (assets/images/tileset): props, platforms, traps.

Everything is cut from the sheets here, trimmed to its visible pixels, scaled up with
crisp pixels, and tinted to sit in each chapter's colors. Results are cached.

  prop(name, theme)        one still image from ART
  frames(name, theme)      the frames of an animated prop from ANIMATED
  earth_block(...)         a grassy dirt block (built from tiles) that reaches the bottom of the screen
  planks(...)              a thin wooden plank platform
  spike_strip(...)         bone spikes poking up out of the ground
  ceiling_slab(...)        a floating earth slab with spikes hanging under it (slide beneath)
  hanging_beam(...)        a heavy beam hung on ropes (slide beneath)
  pool_frames(...)         an animated pool of (toxic) water

The sheet coordinates below are in the sheets' own pixels: (x, y, width, height).
"""
from functools import lru_cache

import pygame

from core.settings import IMAGES_DIR, SCREEN_HEIGHT, FEET_Y

TILESET_DIR = IMAGES_DIR / "tileset"
SCALE = 3                       # every sheet pixel becomes a 3x3 block on screen
GROUND_DEPTH = SCREEN_HEIGHT - FEET_Y   # how far the ground band reaches below the feet line

# Chapter looks: a multiply tint so the props sit in each background's colors,
# and which grass the earth tiles wear.
THEMES = {
    "cabin": {"tint": (255, 222, 196), "grass": "green"},
    "hollow": {"tint": (196, 236, 186), "grass": "green", "pool": (120, 255, 70)},
    "woods": {"tint": (240, 186, 188), "grass": "autumn"},
    "graveyard": {"tint": (176, 200, 240), "grass": "snow", "fire": (90, 230, 255)},
    "camp": {"tint": (240, 232, 220), "grass": "green"},
}
GRASS_ROW = {"green": 0, "autumn": 192, "snow": 384}     # y offset of each grass variant in the floor sheets

DECOR = "Decor.png"
# name: (sheet, (x, y, w, h), scale)
ART = {
    # crates, barrels, furniture
    "crate": (DECOR, (0, 0, 32, 32), 3),
    "crate_stack": (DECOR, (32, 0, 32, 32), 3),
    "barrel": (DECOR, (64, 0, 32, 32), 3),
    "barrels": (DECOR, (96, 0, 32, 32), 3),
    "stool": (DECOR, (128, 0, 32, 32), 3),
    "cauldron": (DECOR, (160, 0, 32, 32), 3),
    "chopping_block": (DECOR, (192, 0, 32, 32), 3),
    "stump_axe": (DECOR, (224, 0, 32, 32), 3),
    "side_table": (DECOR, (256, 0, 32, 32), 3),
    "chair": (DECOR, (288, 0, 32, 32), 3),
    "apples": (DECOR, (320, 0, 32, 32), 3),
    "apple_pile": (DECOR, (352, 0, 32, 32), 3),
    "bottles": (DECOR, (384, 0, 32, 32), 3),
    "apple_table": (DECOR, (256, 32, 64, 32), 3),
    "apple_basket": (DECOR, (352, 32, 32, 32), 3),
    "bottles_small": (DECOR, (384, 32, 32, 32), 3),
    "lean_to": (DECOR, (0, 56, 96, 40), 2),
    "lean_to_patched": (DECOR, (96, 56, 96, 40), 2),
    "log_pile": (DECOR, (192, 64, 64, 32), 3),
    "table": (DECOR, (256, 64, 64, 32), 3),
    "basket": (DECOR, (320, 64, 32, 32), 3),
    "basket_lid": (DECOR, (352, 64, 32, 32), 3),
    "bottle": (DECOR, (384, 64, 32, 32), 3),
    "dirt_pile": (DECOR, (0, 96, 32, 32), 3),
    "pot_frame": (DECOR, (32, 96, 32, 32), 3),
    "tub": (DECOR, (64, 96, 32, 32), 3),
    "bucket": (DECOR, (96, 96, 32, 32), 3),
    "pail": (DECOR, (128, 96, 32, 32), 3),
    # graveyard
    "grave": (DECOR, (192, 96, 32, 32), 3),
    "grave_mossy": (DECOR, (224, 96, 32, 32), 3),
    "grave_small": (DECOR, (256, 96, 32, 32), 3),
    "grave_cross": (DECOR, (288, 96, 32, 32), 3),
    "grave_broken": (DECOR, (320, 96, 32, 32), 3),
    "jack_o_lantern": (DECOR, (352, 96, 32, 32), 3),
    "jack_o_lantern_small": (DECOR, (384, 96, 32, 32), 3),
    "statue": (DECOR, (384, 256, 32, 64), 3),
    "angel": ("Angel Statue.png", (0, 0, 64, 64), 3),
    # nature (green / autumn / snow versions)
    "rock_small": (DECOR, (32, 160, 32, 32), 3),
    "rock_small_autumn": (DECOR, (128, 160, 32, 32), 3),
    "rock_small_snow": (DECOR, (224, 160, 32, 32), 3),
    "rocks": (DECOR, (32, 192, 64, 32), 3),
    "rocks_autumn": (DECOR, (128, 192, 64, 32), 3),
    "rocks_snow": (DECOR, (224, 192, 64, 32), 3),
    "rock_pile": (DECOR, (32, 224, 64, 32), 3),
    "rock_pile_autumn": (DECOR, (128, 224, 64, 32), 3),
    "rock_pile_snow": (DECOR, (224, 224, 64, 32), 3),
    "boulders": (DECOR, (0, 256, 96, 64), 3),
    "boulders_autumn": (DECOR, (192, 256, 96, 64), 3),
    "boulders_snow": (DECOR, (288, 256, 96, 64), 3),
    "tuft": (DECOR, (0, 208, 32, 16), 3),
    "tuft_autumn": (DECOR, (96, 208, 32, 16), 3),
    "tuft_snow": (DECOR, (192, 208, 32, 16), 3),
    "bush": (DECOR, (0, 416, 64, 32), 3),
    "bush_small": (DECOR, (64, 416, 32, 32), 3),
    "fern": (DECOR, (96, 416, 32, 32), 3),
    "bush_autumn": (DECOR, (0, 448, 64, 32), 3),
    "bush_small_autumn": (DECOR, (64, 448, 32, 32), 3),
    "fern_autumn": (DECOR, (96, 448, 32, 32), 3),
    "bush_snow": (DECOR, (0, 480, 64, 32), 3),
    "bush_small_snow": (DECOR, (64, 480, 32, 32), 3),
    "fern_snow": (DECOR, (96, 480, 32, 32), 3),
    "leaf_mound": (DECOR, (160, 328, 96, 24), 3),
    "snow_mound": (DECOR, (256, 328, 96, 24), 3),
    "leaf_pile": (DECOR, (160, 364, 64, 20), 3),
    "snow_pile": (DECOR, (224, 364, 64, 20), 3),
    "reeds": (DECOR, (288, 160, 32, 32), 3),
    "reeds_tall": (DECOR, (320, 136, 32, 56), 3),
    "tall_grass": ("Tall Grass.png", (0, 0, 96, 32), 3),
    "brick_wall": (DECOR, (352, 136, 64, 56), 3),
    "scarecrow": (DECOR, (296, 192, 48, 64), 3),
    "pumpkin": (DECOR, (352, 200, 32, 24), 3),
    "pumpkin_small": (DECOR, (384, 200, 32, 24), 3),
    "pumpkin_pile": (DECOR, (352, 224, 64, 32), 3),
    "laundry": (DECOR, (24, 350, 112, 68), 3),
    # alchemy and ores
    "grapes": ("Alchemy Decor.png", (0, 0, 64, 28), 3),
    "potion_table": ("Alchemy Decor.png", (32, 32, 32, 32), 3),
    "alchemy_desk": ("Alchemy Decor.png", (64, 16, 64, 48), 3),
    "crystal_stand": ("Alchemy Decor.png", (128, 32, 32, 32), 3),
    "sunflowers": ("Alchemy Decor.png", (160, 16, 32, 48), 3),
    "ore": ("Ores.png", (0, 16, 64, 48), 3),
    "ore_pink": ("Ores.png", (64, 16, 64, 48), 3),
    "ore_gold": ("Ores.png", (0, 80, 64, 48), 3),
    "ore_crystal": ("Ores.png", (64, 80, 64, 48), 3),
    # garden
    "flower_pot": ("Garden Decorations.png", (0, 0, 32, 32), 3),
    "urn": ("Garden Decorations.png", (64, 0, 32, 32), 3),
    "urn_pedestal": ("Garden Decorations.png", (32, 64, 32, 64), 3),
    "garden_statue": ("Garden Decorations.png", (0, 64, 32, 64), 3),
    # camp
    "large_tent": ("Large Tent.png", (0, 0, 96, 128), 2),
    "small_tent": ("Small Tent.png", (0, 0, 64, 64), 3),
}

# name: (sheet, (x, y) of the first frame, (frame w, h), columns, count, ms per frame, scale)
ANIMATED = {
    "campfire": ("Animated Sprites/Campfire sheet.png", (0, 0), (32, 32), 5, 40, 80, 3),
    "campfire_pot": ("Animated Sprites/Campfire with food sheet.png", (0, 0), (32, 32), 5, 40, 80, 3),
    "cooking": ("Cooking area.png", (0, 0), (64, 64), 12, 12, 110, 3),
    "torch": ("Torch.png", (0, 32), (32, 32), 6, 6, 100, 3),
    "torch_wall": ("Torch.png", (0, 96), (32, 32), 6, 6, 100, 3),
    "furnace": ("Furnace and Sawmill.png", (0, 0), (64, 64), 6, 6, 130, 3),
    "sawmill": ("Furnace and Sawmill.png", (0, 64), (64, 64), 6, 6, 130, 3),
    "water": ("Animated Sprites/GandalfHardcore Animated Water Tiles.png", (0, 64), (32, 32), 20, 20, 90, 3),
}


@lru_cache(maxsize=None)
def _sheet(name):
    return pygame.image.load(str(TILESET_DIR / name)).convert_alpha()


def _cut(sheet, rect):
    return _sheet(sheet).subsurface(pygame.Rect(rect)).copy()


def _scaled(surface, scale=SCALE):
    return pygame.transform.scale(surface, (surface.get_width() * scale, surface.get_height() * scale))


def _tint(surface, color):
    if not color or color == (255, 255, 255):
        return surface
    out = surface.copy()
    out.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def tint_for(theme):
    return THEMES.get(theme, THEMES["camp"])["tint"]


@lru_cache(maxsize=None)
def prop(name, theme="camp", flip=False, scale=None):
    """One still prop, trimmed to its pixels, scaled, and tinted for the chapter.
    scale: pixels per sheet pixel, if not the prop's usual size (smaller far away, bigger up close)."""
    sheet, rect, usual = ART[name]
    scale = scale or usual
    image = _cut(sheet, rect)
    image = image.subsurface(image.get_bounding_rect()).copy()
    image = _scaled(image, scale)
    if flip:
        image = pygame.transform.flip(image, True, False)
    return _tint(image, tint_for(theme))


@lru_cache(maxsize=None)
def frames(name, theme="camp", color=None, scale=None):
    """The frames of an animated prop (all trimmed to the same box, so they don't jitter).
    color: an extra multiply tint (ghostly blue fire in the graveyard)."""
    sheet, (x0, y0), (fw, fh), cols, count, _, usual = ANIMATED[name]
    scale = scale or usual
    raw = [_cut(sheet, (x0 + (i % cols) * fw, y0 + (i // cols) * fh, fw, fh)) for i in range(count)]
    box = raw[0].get_bounding_rect()
    for f in raw[1:]:
        box.union_ip(f.get_bounding_rect())
    out = []
    for f in raw:
        f = _scaled(f.subsurface(box).copy(), scale)
        f = _tint(f, tint_for(theme))
        out.append(_brighten(f, color) if color else f)
    return tuple(out)


def shade(surface, darken, haze=None, amount=0.0):
    """Push a prop into the distance (or the shadowy foreground): darken it by a multiply color,
    then blend `amount` of the way toward a haze color."""
    out = surface.copy()
    keep = tuple(round(c * (1 - amount)) for c in darken)
    out.fill((*keep, 255), special_flags=pygame.BLEND_RGBA_MULT)
    if haze and amount:
        out.fill(tuple(round(c * amount) for c in haze), special_flags=pygame.BLEND_RGB_ADD)
    return out


def frame_ms(name):
    return ANIMATED[name][5]


def _brighten(surface, color):
    """Recolor something bright (flames) toward a color, keeping its shading."""
    gray = pygame.transform.grayscale(surface)
    gray.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    glow = gray.copy()
    glow.fill((60, 60, 60, 0), special_flags=pygame.BLEND_RGB_ADD)
    return glow


# ---- built from tiles ---------------------------------------------------
FLOOR = "Floor Tiles2.png"      # the darker floor tiles: they match the silhouette backgrounds
T = 32                          # tile size on the sheet


def _tile(x, y, w=T, h=T, sheet=FLOOR):
    return _cut(sheet, (x, y, w, h))


@lru_cache(maxsize=None)
def earth_block(theme, tiles, top_height):
    """A grassy dirt block `tiles` wide whose walkable top is `top_height` pixels above the
    ground line. The surface reaches down to the bottom of the screen.
    Returns (surface, lip): lip = how far the grass pokes up above the walkable top."""
    g = GRASS_ROW[THEMES[theme]["grass"]]
    lip = 4 * SCALE                                     # grass blades above the dirt
    height = top_height + GROUND_DEPTH + lip
    width = tiles * T * SCALE
    surf = pygame.Surface((tiles * T, height // SCALE + T), pygame.SRCALPHA)
    if tiles == 1:
        top_tiles, mid_tiles = [(192, 96 + g)], [(192, 128 + g)]
    else:
        top_tiles = [(0, g)] + [(32, g)] * (tiles - 2) + [(64, g)]
        mid_tiles = [(0, 32 + g)] + [(32, 32 + g)] * (tiles - 2) + [(64, 32 + g)]
    for i, (tx, ty) in enumerate(top_tiles):
        surf.blit(_tile(tx, ty), (i * T, 0))
    y = T
    while y < surf.get_height():
        for i, (tx, ty) in enumerate(mid_tiles):
            surf.blit(_tile(tx, ty), (i * T, y))
        y += T
    surf = _scaled(surf).subsurface((0, 0, width, height)).copy()
    return _tint(surf, tint_for(theme)), lip


@lru_cache(maxsize=None)
def planks(theme, tiles):
    """A thin plank platform, `tiles` boards wide."""
    board = _tile(0, 200, 32, 8, "Other Tiles1.png")
    surf = pygame.Surface((tiles * T, 8), pygame.SRCALPHA)
    for i in range(tiles):
        surf.blit(board, (i * T, 0))
    return _tint(_scaled(surf), tint_for(theme))


@lru_cache(maxsize=None)
def spike_strip(theme, tiles):
    """Bone-colored spikes pointing up, `tiles` wide. Their base sits a little under the ground line.
    Returns (surface, sink): sink = how far the image reaches below the ground line."""
    strip = pygame.Surface((tiles * T, 26), pygame.SRCALPHA)
    for i in range(tiles):
        strip.blit(_tile(224 + 32 * (i % 2), 110, 32, 26, "Floor Tiles1.png"), (i * T, 0))   # (lighter: easier to spot)
    strip = pygame.transform.flip(strip, False, True)
    return _tint(_scaled(strip), tint_for(theme)), 6 * SCALE


@lru_cache(maxsize=None)
def ceiling_slab(theme, tiles, spiked=True):
    """A floating earth slab with stalactite spikes under it.
    Returns (surface, spike_depth): how far the spikes hang below the slab's dirt."""
    g = GRASS_ROW[THEMES[theme]["grass"]]
    tiles = max(2, tiles)
    row = [(192, 160 + g)] + [(224, 160 + g)] * (tiles - 2) + [(256, 160 + g)]
    spike_h = 20 if spiked else 0
    surf = pygame.Surface((tiles * T, T + spike_h), pygame.SRCALPHA)
    if spiked:
        for i in range(tiles):
            spikes = _tile(224 + 32 * (i % 2), 116, 32, 20)
            surf.blit(spikes, (i * T, T - 4))
    for i, (tx, ty) in enumerate(row):
        surf.blit(_tile(tx, ty), (i * T, 0))
    return _tint(_scaled(surf), tint_for(theme)), (spike_h - 4) * SCALE if spiked else 0


@lru_cache(maxsize=None)
def island_slab(theme, tiles):
    """A thin floating earth platform: the grassy top of the floating-ledge tiles joined to their
    rounded underside, so it's thin enough to walk under when it floats above head height."""
    g = GRASS_ROW[THEMES[theme]["grass"]]
    tiles = max(2, tiles)
    row = [(192, 160 + g)] + [(224, 160 + g)] * (tiles - 2) + [(256, 160 + g)]
    strip = pygame.Surface((tiles * T, T), pygame.SRCALPHA)
    for i, (tx, ty) in enumerate(row):
        strip.blit(_tile(tx, ty), (i * T, 0))
    top_rows, bottom_rows = 11, 9
    surf = pygame.Surface((tiles * T, top_rows + bottom_rows), pygame.SRCALPHA)
    surf.blit(strip, (0, 0), (0, 0, tiles * T, top_rows))
    surf.blit(strip, (0, top_rows), (0, T - bottom_rows, tiles * T, bottom_rows))
    surf = surf.subsurface(surf.get_bounding_rect()).copy()
    return _tint(_scaled(surf), tint_for(theme))


@lru_cache(maxsize=None)
def hanging_beam(theme, tiles, rope_height):
    """A thick plank beam (two boards) hung from ropes that run up off the top of the screen."""
    board = planks(theme, tiles)
    w, bh = board.get_width(), board.get_height()
    surf = pygame.Surface((w, rope_height + bh * 2), pygame.SRCALPHA)
    for rx in (int(w * 0.18), int(w * 0.82)):
        pygame.draw.line(surf, (40, 28, 20), (rx, 0), (rx, rope_height + 6), 7)
        pygame.draw.line(surf, (128, 98, 66), (rx, 0), (rx, rope_height + 6), 3)
        for ky in range(8, rope_height, 18):                 # twisted-rope ticks
            pygame.draw.line(surf, (82, 60, 40), (rx - 2, ky), (rx + 2, ky + 4), 2)
        pygame.draw.rect(surf, (40, 28, 20), (rx - 6, rope_height - 4, 12, 10), border_radius=3)
    surf.blit(board, (0, rope_height))
    surf.blit(board, (0, rope_height + bh - 3))
    return surf


@lru_cache(maxsize=None)
def pool_frames(theme, tiles):
    """An animated pool `tiles` wide, tinted for the chapter (sickly green in the Hollow)."""
    color = THEMES.get(theme, {}).get("pool")
    water = frames("water", "camp")
    out = []
    for f in water:
        strip = pygame.Surface((f.get_width() * tiles, f.get_height() + GROUND_DEPTH), pygame.SRCALPHA)
        for i in range(tiles):
            strip.blit(f, (i * f.get_width(), 0))
        deep = strip.get_rect(top=f.get_height() - 2)
        strip.fill((10, 30, 22), deep)
        if color:
            strip.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        out.append(strip)
    return tuple(out)


# ---- the Pixel Trap Pack (assets/images/trap) ---------------------------
TRAP_DIR = IMAGES_DIR / "trap"


@lru_cache(maxsize=None)
def trap_frames(file, fw, fh, theme, flip=False, skip_bottom=0, thin=0):
    """An animated trap's frames (scaled, tinted for the chapter), plus where it can hurt on each
    frame: (left, bottom, right, top) in screen pixels from the frame's bottom-left corner, or
    None for an empty frame. skip_bottom ignores the base plate rows; thin ignores rows with only
    a few pixels (the crusher's chains)."""
    sheet = pygame.image.load(str(TRAP_DIR / file)).convert_alpha()
    frames, boxes = [], []
    for i in range(sheet.get_width() // fw):
        raw = sheet.subsurface((i * fw, 0, fw, fh)).copy()
        if flip:
            raw = pygame.transform.flip(raw, True, False)
        rows = []
        for y in range(fh - skip_bottom):
            xs = [x for x in range(fw) if raw.get_at((x, y)).a > 40]
            if len(xs) > thin:
                rows.append((y, min(xs), max(xs)))
        if rows and thin:                       # only the lowest solid run (the block, not its anchor)
            run = [rows[-1]]
            for r in reversed(rows[:-1]):
                if run[-1][0] - r[0] > 1:
                    break
                run.append(r)
            rows = run[::-1]
        if rows:
            y0, y1 = rows[0][0], rows[-1][0]
            x0, x1 = min(r[1] for r in rows), max(r[2] for r in rows)
            boxes.append((x0 * SCALE, (fh - y1 - 1) * SCALE, (x1 + 1) * SCALE, (fh - y0) * SCALE))
        else:
            boxes.append(None)
        frames.append(_tint(_scaled(raw), tint_for(theme)))
    return tuple(frames), tuple(boxes)


@lru_cache(maxsize=None)
def trap_arrow(theme):
    """The arrow the totem fires, pointing left."""
    arrow = pygame.image.load(str(TRAP_DIR / "Arrow Trap/PNGs/Arrow.png")).convert_alpha()
    return _tint(_scaled(arrow), tint_for(theme))
