import random

import pygame

from core.ui import get_font, WHITE, BLACK


class CombatText:
    """Floating number/label that rises and fades out (damage, heals, etc.)."""

    POP_MS = 140   # big hits "pop" in large and settle to normal size

    def __init__(self, text, x, y, color=WHITE, lifespan=1500, rise_speed=24, size=22, bold=False, pop=False):
        self.x = x + random.randint(-5, 5)      # small jitter so stacked texts don't overlap
        self.y = float(y)
        self.lifespan = lifespan                 # milliseconds
        self.age = 0
        self.rise_speed = rise_speed + random.uniform(-6, 6)  # pixels per second
        self.pop = pop

        font = get_font(size, bold)
        self.surface = font.render(text, True, color)
        self.outline_surface = self._make_outline(font, text)

    @staticmethod
    def _make_outline(font, text):
        base = font.render(text, True, BLACK)
        outline = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    outline.blit(base, (dx + 1, dy + 1))
        return outline

    def update(self, dt):
        self.age += dt
        self.y -= self.rise_speed * dt / 1000
        alpha = int(255 * max(0.0, 1 - self.age / self.lifespan))
        self.surface.set_alpha(alpha)
        self.outline_surface.set_alpha(alpha)

    def draw(self, screen, offset_x=0):
        """offset_x lets world-positioned text scroll with the camera."""
        if not self.is_alive():
            return
        x = self.x - offset_x
        if self.pop and self.age < self.POP_MS:
            k = 1 + 0.8 * (1 - self.age / self.POP_MS)
            for surf, dx in ((self.outline_surface, -1), (self.surface, 0)):
                big = pygame.transform.rotozoom(surf, 0, k)
                w, h = surf.get_size()
                screen.blit(big, (x + dx - (big.get_width() - w) / 2, self.y + dx - (big.get_height() - h) / 2))
            return
        screen.blit(self.outline_surface, (x - 1, self.y - 1))
        screen.blit(self.surface, (x, self.y))

    def is_alive(self):
        return self.age < self.lifespan
