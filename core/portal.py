"""The glowing exit portal at the end of each level. Drawn in code (no art
needed), colored by the level's accent so it hints at what's next."""
import math
import random

import pygame

from core.ui import get_font, blit_centered, WHITE

WIDTH, HEIGHT = 110, 190


def _make_glow(color):
    """Soft glowing oval built from stacked translucent ellipses."""
    surf = pygame.Surface((WIDTH + 80, HEIGHT + 80), pygame.SRCALPHA)
    center = surf.get_rect().center
    bright = tuple(min(255, c + 90) for c in color)
    steps = 16
    for i in range(steps, 0, -1):          # outer halo, fading toward the edge
        t = i / steps
        rect = pygame.Rect(0, 0, int(WIDTH * (0.6 + 0.75 * t)), int(HEIGHT * (0.7 + 0.5 * t)))
        rect.center = center
        pygame.draw.ellipse(surf, (*color, int(28 + 22 * (1 - t))), rect)
    core = pygame.Rect(0, 0, int(WIDTH * 0.6), int(HEIGHT * 0.8))
    core.center = center
    dark = tuple(c // 6 for c in color)
    pygame.draw.ellipse(surf, (*dark, 240), core)                     # tinted dark center
    inner = core.inflate(-core.width // 3, -core.height // 4)
    pygame.draw.ellipse(surf, (*color, 70), inner)                    # inner shimmer
    pygame.draw.ellipse(surf, (*bright, 255), core, 4)                # bright rim
    return surf


class Portal:
    def __init__(self, x, ground_y, color, label):
        self.x = x                       # world x of the portal's center
        self.bottom = ground_y + 150     # sit on the same ground line as the hero's feet
        self.color = color
        self.label = label
        self.glow = _make_glow(color)
        self.time = 0
        self.sparks = []                 # [x_offset, y_offset, speed, life]
        self.font = get_font(18, bold=True)

    def update(self, dt):
        self.time += dt
        if random.random() < dt / 60:   # about one spark every 60 ms
            self.sparks.append([random.uniform(-WIDTH / 3, WIDTH / 3), 0, random.uniform(30, 70), 1.0])
        for spark in self.sparks:
            spark[1] -= spark[2] * dt / 1000
            spark[3] -= dt / 1400
        self.sparks = [s for s in self.sparks if s[3] > 0]

    def draw(self, screen, camera_offset):
        cx = self.x - camera_offset
        if cx < -200 or cx > screen.get_width() + 200:
            return
        cy = self.bottom - HEIGHT // 2

        pulse = 0.85 + 0.15 * math.sin(self.time / 300)
        self.glow.set_alpha(int(255 * pulse))
        screen.blit(self.glow, self.glow.get_rect(center=(cx, cy)))

        # Swirl: a few bright dots orbiting inside the portal
        for i in range(6):
            angle = self.time / 500 + i * math.tau / 6
            px = cx + math.cos(angle) * WIDTH * 0.18
            py = cy + math.sin(angle) * HEIGHT * 0.27
            pygame.draw.circle(screen, self.color, (int(px), int(py)), 3)

        for sx, sy, _, life in self.sparks:
            pygame.draw.circle(screen, (*self.color,), (int(cx + sx), int(self.bottom - 20 + sy)), max(1, int(3 * life)))

        bob = math.sin(self.time / 400) * 4
        blit_centered(screen, self.font.render(self.label, True, WHITE), (cx, self.bottom - HEIGHT - 25 + bob))
