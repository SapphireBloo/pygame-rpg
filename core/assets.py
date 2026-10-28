"""Image loading with caching.

Every scene used to reload (and rescale) every PNG from disk each time it was
created, which meant a fresh load for every single battle. These helpers load
each set once and hand back the cached frames afterwards.
"""
from functools import lru_cache

import pygame

from core.settings import IMAGES_DIR, SPRITE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT


@lru_cache(maxsize=None)
def load_frames(folder, scale=SPRITE_SIZE, flip_x=False):
    """Load every .png in assets/images/<folder>, sorted by name."""
    path = IMAGES_DIR / folder
    if not path.is_dir():
        return ()
    frames = []
    for file in sorted(path.glob("*.png")):
        image = pygame.transform.scale(pygame.image.load(file).convert_alpha(), scale)
        if flip_x:
            image = pygame.transform.flip(image, True, False)
        frames.append(image)
    return tuple(frames)


@lru_cache(maxsize=None)
def load_sprite_sheet(relative_path, frame_width, frame_height, scale=SPRITE_SIZE):
    """Cut a horizontal sprite sheet into scaled frames."""
    path = IMAGES_DIR / relative_path
    if not path.is_file():
        return ()
    sheet = pygame.image.load(path).convert_alpha()
    count = sheet.get_width() // frame_width
    return tuple(
        pygame.transform.scale(
            sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)),
            scale,
        )
        for i in range(count)
    )


@lru_cache(maxsize=None)
def load_background(filename):
    """One background from assets/images/backgrounds, scaled to the window."""
    path = IMAGES_DIR / "backgrounds" / filename
    if not path.is_file():
        return None
    return pygame.transform.scale(pygame.image.load(path).convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))


@lru_cache(maxsize=None)
def tinted(frames, color):
    """Color-tinted copies of a frame tuple (e.g. green ghosts for the witch level).

    `color` multiplies the sprite, so (255, 255, 255) leaves it unchanged.
    """
    if color is None:
        return frames
    result = []
    for frame in frames:
        copy = frame.copy()
        copy.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        result.append(copy)
    return tuple(result)
