"""Gritty look, applied in code over the whole world (not the HUD):

  * per-level color grade + partial desaturation
  * drifting ground fog tinted to the level
  * soft vignette around the edges
  * animated film grain
  * soft ground shadows under characters

Scenes call: grit.draw_fog(...) after characters, then grit.apply(screen)
before drawing HUD/menus so text stays crisp. Toggle with GRIT in settings.
"""
import math
import random
from functools import lru_cache

import pygame

from core.settings import GRIT

DESATURATE = 70          # 0-255: how much color to drain
GRAIN_ALPHA = 26         # strength of the film grain
VIGNETTE_STRENGTH = 150  # edge darkness

# Multiply tint per level background (darker, moodier versions of each place)
GRADES = {
    "bg_0.png": (240, 218, 196),   # The Cabin: warm, smoky
    "bg_1.png": (212, 232, 202),   # Witch's Hollow: sickly green
    "bg_2.png": (232, 200, 198),   # Bleeding Woods: dried-blood red
    "bg_3.png": (200, 218, 238),   # Graveyard: cold moonlight
    "camp": (245, 225, 200),       # Camp: warm firelight
}
DEFAULT_GRADE = (215, 205, 200)


@lru_cache(maxsize=None)
def _vignette(size):
    w, h = size
    small = pygame.Surface((w // 4, h // 4), pygame.SRCALPHA)
    sw, sh = small.get_size()
    for y in range(sh):
        for x in range(sw):
            dx = (x - sw / 2) / (sw / 2)
            dy = (y - sh / 2) / (sh / 2)
            d = min(1.0, math.sqrt(dx * dx * 0.85 + dy * dy))
            small.set_at((x, y), (0, 0, 0, int(VIGNETTE_STRENGTH * max(0.0, d - 0.45) / 0.55)))
    return pygame.transform.smoothscale(small, size)


@lru_cache(maxsize=None)
def _grain_tile(variant, size=192):
    data = bytearray()
    rand = random.getrandbits
    for _ in range(size * size):
        v = rand(8)
        data += bytes((v, v, v, rand(8) * GRAIN_ALPHA // 255))
    return pygame.image.frombuffer(bytes(data), (size, size), "RGBA").convert_alpha()


def _puff(radius, color):
    surf = pygame.Surface((radius * 2, radius), pygame.SRCALPHA)
    for i in range(10, 0, -1):
        t = i / 10
        rect = pygame.Rect(0, 0, int(radius * 2 * t), int(radius * t))
        rect.center = (radius, radius // 2)
        pygame.draw.ellipse(surf, (*color, int(14 * (1 - t) + 4)), rect)
    return surf


class Grit:
    def __init__(self, size):
        self.enabled = GRIT
        self.size = size
        self.grade = DEFAULT_GRADE
        self.time = 0
        if not self.enabled:
            return
        self.vignette = _vignette(tuple(size))
        self.grain = [_grain_tile(i) for i in range(3)]   # built once, shared by every scene
        self.grain_index = 0
        self.grain_timer = 0
        self.fog_puffs = []
        self.set_level(None)
        self.shadow = pygame.Surface((110, 22), pygame.SRCALPHA)
        for i in range(8, 0, -1):
            t = i / 8
            r = pygame.Rect(0, 0, int(110 * t), int(22 * t))
            r.center = (55, 11)
            pygame.draw.ellipse(self.shadow, (0, 0, 0, int(26 * (1 - t) + 10)), r)

    def set_level(self, level):
        if not self.enabled:
            return
        bg = level["background"] if level else None
        self.grade = GRADES.get(bg, DEFAULT_GRADE)
        accent = level["accent"] if level else (180, 180, 200)
        fog_color = tuple(int(0.55 * c + 0.45 * 200) for c in accent)
        puff = _puff(170, fog_color)
        rng = random.Random(bg)
        self.fog_puffs = [(puff, rng.uniform(0, 1600), rng.uniform(470, 560), rng.uniform(8, 22))
                          for _ in range(9)]

    def update(self, dt):
        self.time += dt
        if self.enabled:
            self.grain_timer += dt
            if self.grain_timer > 45:
                self.grain_timer = 0
                self.grain_index = (self.grain_index + 1) % len(self.grain)

    # ---- world layer ---------------------------------------------------
    def draw_shadow(self, screen, feet_x, feet_y, width=1.0):
        if not self.enabled:
            return
        shadow = self.shadow if width == 1.0 else pygame.transform.smoothscale(
            self.shadow, (int(110 * width), 22))
        screen.blit(shadow, shadow.get_rect(center=(feet_x, feet_y - 2)))

    def draw_fog(self, screen, camera_offset=0):
        if not self.enabled:
            return
        span = 1600
        for puff, x, y, speed in self.fog_puffs:
            px = (x + self.time * speed / 1000 - camera_offset * 0.6) % span - 200
            screen.blit(puff, (px, y + math.sin(self.time / 2000 + x) * 6))

    # ---- post-process --------------------------------------------------
    def apply(self, screen):
        if not self.enabled:
            return
        if hasattr(pygame.transform, "grayscale"):
            gray = pygame.transform.grayscale(screen)
            gray.set_alpha(DESATURATE)
            screen.blit(gray, (0, 0))
        screen.fill(self.grade, special_flags=pygame.BLEND_MULT)
        screen.blit(self.vignette, (0, 0))
        tile = self.grain[self.grain_index]
        tw, th = tile.get_size()
        ox, oy = random.randrange(tw), random.randrange(th)
        w, h = self.size
        for y in range(-oy, h, th):
            for x in range(-ox, w, tw):
                screen.blit(tile, (x, y))
