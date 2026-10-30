"""Warm, flickering firelight at camp: a soft glow added over everything near the cooking fire,
the forge, and the torches (characters walking by pick up the warm light too).

A light is (color, radius, strength) on a prop: see Kit.light in core/obstacles.py and the
camp layout in core/level_layouts.py. The glows are pre-drawn at a few brightness levels and
picked each frame by a flicker, so they cost almost nothing to draw.
"""
import math
import random
from functools import lru_cache

import pygame

LEVELS = 10                 # brightness steps the flicker picks between
SQUASH = 0.72               # glows are wider than tall, so they spill along the ground
DARKEN = (212, 202, 216)    # camp gets a touch darker overall so the firelight reads


@lru_cache(maxsize=None)
def _glow(color, radius, strength, level):
    """A radial glow (black at the edge) for additive blending."""
    w, h = radius * 2, int(radius * 2 * SQUASH)
    surf = pygame.Surface((w, h))
    surf.fill((0, 0, 0))
    k = strength * level / LEVELS
    steps = 28
    for i in range(steps, 0, -1):
        t = i / steps                                   # 1 at the rim, small at the center
        fall = (1 - t) ** 1.8
        c = tuple(min(255, int(v * k * fall)) for v in color)
        rect = pygame.Rect(0, 0, int(w * t), int(h * t))
        rect.center = (w // 2, h // 2)
        pygame.draw.ellipse(surf, c, rect)
    return surf


class Flicker:
    """A light's wobble: a couple of slow waves plus a little crackle."""

    def __init__(self):
        self.seed = random.uniform(0, 100)
        self.crackle = 0.0

    def level(self, time_ms):
        t = time_ms / 1000 + self.seed
        if random.random() < 0.08:
            self.crackle = random.uniform(-0.08, 0.06)
        self.crackle *= 0.9
        value = 0.84 + 0.08 * math.sin(t * 7.1) + 0.06 * math.sin(t * 17.3 + 1.7) + self.crackle
        return max(1, min(LEVELS, round(value * LEVELS)))


def darken(screen):
    screen.fill(DARKEN, special_flags=pygame.BLEND_RGB_MULT)


def draw_light(screen, center, light, flicker, time_ms):
    color, radius, strength = light
    glow = _glow(tuple(color), radius, strength, flicker.level(time_ms))
    rect = glow.get_rect(center=(int(center[0]), int(center[1])))
    if rect.right < 0 or rect.left > screen.get_width():
        return
    screen.blit(glow, rect, special_flags=pygame.BLEND_RGB_ADD)
