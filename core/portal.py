"""The exit portal at the end of each level (and each camp): the dark, animated portal from the
GandalfHardcore tileset. Its label (and a few sparks) wear the level's accent color.
Charlie steps through it with E (see ExplorationScene)."""
import math
import random
from functools import lru_cache

import pygame

from core.settings import FEET_Y
from core.tileset import TILESET_DIR
from core.ui import get_font, outlined_text

SHEET = "Animated Sprites/GandalfHardcore Portal sheet.png"
FRAMES, FRAME_SIZE, SCALE = 10, 64, 3
FRAME_MS = 110


@lru_cache(maxsize=None)
def _frames():
    """The portal frames, as drawn: a dark doorway with a few sparks."""
    sheet = pygame.image.load(str(TILESET_DIR / SHEET)).convert_alpha()
    raw = [sheet.subsurface((i * FRAME_SIZE, 0, FRAME_SIZE, FRAME_SIZE)).copy() for i in range(FRAMES)]
    box = raw[0].get_bounding_rect()
    for f in raw[1:]:
        box.union_ip(f.get_bounding_rect())
    return tuple(pygame.transform.scale(f.subsurface(box).copy(), (box.width * SCALE, box.height * SCALE))
                 for f in raw)


class Portal:
    def __init__(self, x, ground_y, color, label):
        self.x = x                       # world x of the portal's center
        self.bottom = FEET_Y + 6         # sits on the ground line, like everyone's feet
        self.color = tuple(color)        # the label (and the sparks) wear the chapter's accent color
        self.label = label
        self.frames = _frames()
        self.time = 0
        self.sparks = []                 # [x_offset, y_offset, speed, life]
        self.font = get_font(18, bold=True)

    @property
    def height(self):
        return self.frames[0].get_height()

    def update(self, dt):
        self.time += dt
        if random.random() < dt / 90:   # a few drifting sparks in the accent color
            half = self.frames[0].get_width() / 4
            self.sparks.append([random.uniform(-half, half), 0, random.uniform(30, 70), 1.0])
        for spark in self.sparks:
            spark[1] -= spark[2] * dt / 1000
            spark[3] -= dt / 1500
        self.sparks = [s for s in self.sparks if s[3] > 0]

    def draw(self, screen, camera_offset):
        cx = self.x - camera_offset
        if cx < -250 or cx > screen.get_width() + 250:
            return
        frame = self.frames[int(self.time // FRAME_MS) % len(self.frames)]
        screen.blit(frame, frame.get_rect(midbottom=(cx, self.bottom)))
        for sx, sy, _, life in self.sparks:
            pygame.draw.circle(screen, self.color, (int(cx + sx), int(self.bottom - 30 + sy)), max(1, int(2.5 * life)))
        bob = math.sin(self.time / 400) * 4
        label = outlined_text(self.label, 18, self.color, True, 2)
        screen.blit(label, label.get_rect(center=(cx, self.bottom - self.height - 25 + bob)))
