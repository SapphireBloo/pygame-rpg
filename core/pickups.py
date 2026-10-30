"""Things lying around in the levels for Charlie to pick up.

GoldenCrumb: one hidden in each chapter (see "golden_crumb" in core/level_layouts.py). It floats
somewhere tricky to reach: on a high shelf, or over a trap. Feed it to Crumb at camp.
(The Graveyard's isn't floating: it's inside a grave you have to search.)
"""
import math

import pygame

from core import sfx
from core.icons import icon
from core.settings import FEET_Y

REACH_X = 45          # how close (horizontally) Charlie's feet must be
REACH_TOP = 4         # how far past the top of Charlie's head it can still be grabbed


class GoldenCrumb:
    def __init__(self, x, height):
        self.x = x
        self.height = height         # its center, in pixels above the ground
        self.taken = False
        self.time = 0
        self.burst = 0               # sparkle after pickup

    @property
    def y(self):
        return FEET_Y - self.height + 4 * math.sin(self.time / 400)

    def update(self, dt, hero_feet_x, body_bottom, body_top):
        """Returns True the moment Charlie grabs it. body_bottom/top: Charlie's feet and the top of his
        head, in pixels above the ground."""
        self.time += dt
        self.burst = max(0, self.burst - dt)
        if self.taken:
            return False
        if abs(hero_feet_x - self.x) < REACH_X and body_bottom - 10 <= self.height <= body_top + REACH_TOP:
            self.taken = True
            self.burst = 700
            sfx.play("ui_select")
            sfx.play("heal", 0.6)
            return True
        return False

    def draw(self, screen, camera_offset):
        sx = self.x - camera_offset
        if sx < -60 or sx > screen.get_width() + 60:
            return
        if self.taken:
            if self.burst:                               # a ring of sparkles where it was
                k = 1 - self.burst / 700
                for i in range(8):
                    a = i * math.pi / 4
                    r = 10 + 40 * k
                    pygame.draw.circle(screen, (255, 230, 120), (int(sx + r * math.cos(a)), int(self.y + r * math.sin(a))),
                                       max(1, int(4 * (1 - k))))
            return
        # Subtle on purpose: a soft glow that breathes, and a twinkle every few seconds
        breathe = 0.5 + 0.5 * math.sin(self.time / 650)
        glow = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 220, 120, int(30 + 40 * breathe)), (30, 30), 26)
        pygame.draw.circle(glow, (255, 235, 160, int(40 + 50 * breathe)), (30, 30), 15)
        screen.blit(glow, glow.get_rect(center=(sx, self.y)))
        crumb = icon("golden_crumb", 26).copy()
        crumb.set_alpha(int(170 + 85 * breathe))
        screen.blit(crumb, crumb.get_rect(center=(sx, self.y)))
        if (self.time // 100) % 40 < 3:                 # twinkle
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                pygame.draw.line(screen, (255, 255, 230), (sx + 9, self.y - 9),
                                 (sx + 9 + dx * 7, self.y - 9 + dy * 7), 2)
