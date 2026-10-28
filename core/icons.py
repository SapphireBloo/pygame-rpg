"""Little hand-drawn icons for the menus (candy, bombs, upgrades, Jack's skull).

Everything is drawn with shapes, so there are no extra image files to manage.
Use icon("candy", 32) to get a cached surface, or draw_icon(screen, "bomb", center, 40).
"""
import math
from functools import lru_cache

import pygame

INK = (12, 8, 14)


def _poly(surf, color, pts, outline=2):
    pygame.draw.polygon(surf, color, pts)
    if outline:
        pygame.draw.polygon(surf, INK, pts, outline)


def _candy_corn(surf, cx, cy, s, angle=0.0):
    """Candy corn: yellow base, orange middle, white tip (tip points up)."""
    def rot(x, y):
        a = math.radians(angle)
        return (cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))
    half, top, bottom = s * 0.42, -s * 0.5, s * 0.45

    def edge(t):  # point on the left/right edge at height fraction t (0 = tip, 1 = base)
        y = top + (bottom - top) * t
        return half * t, y
    bands = ((0.0, 0.38, (250, 246, 232)), (0.38, 0.72, (255, 140, 30)), (0.72, 1.0, (255, 214, 60)))
    for t0, t1, color in bands:
        (x0, y0), (x1, y1) = edge(t0), edge(t1)
        pygame.draw.polygon(surf, color, [rot(-x0, y0), rot(x0, y0), rot(x1, y1), rot(-x1, y1)])
    outline = [rot(0, top), rot(half, bottom), rot(-half, bottom)]
    pygame.draw.polygon(surf, INK, outline, max(2, int(s / 14)))


def _bomb(surf, cx, cy, s, spark=True):
    r = s * 0.34
    by = cy + s * 0.08
    pygame.draw.circle(surf, INK, (cx, by), r + 2)
    pygame.draw.circle(surf, (40, 38, 50), (cx, by), r)
    pygame.draw.circle(surf, (120, 120, 140), (cx - r * 0.35, by - r * 0.35), max(2, r * 0.22))
    cap = pygame.Rect(0, 0, r * 0.7, r * 0.45)
    cap.midbottom = (cx + r * 0.45, by - r * 0.75)
    pygame.draw.rect(surf, (70, 68, 80), cap)
    pygame.draw.rect(surf, INK, cap, 1)
    fuse_end = (cx + s * 0.38, cy - s * 0.42)
    pygame.draw.line(surf, (210, 170, 100), cap.midtop, fuse_end, max(2, int(s / 16)))
    if spark:
        for i in range(6):
            a = i * math.tau / 6
            pygame.draw.line(surf, (255, 220, 90), fuse_end,
                             (fuse_end[0] + math.cos(a) * s * 0.12, fuse_end[1] + math.sin(a) * s * 0.12), 2)
        pygame.draw.circle(surf, (255, 250, 200), fuse_end, max(2, s * 0.05))


def _heart(surf, cx, cy, s, color=(230, 50, 70)):
    r = s * 0.22
    pts = [(cx - s * 0.42, cy - s * 0.05), (cx, cy + s * 0.4), (cx + s * 0.42, cy - s * 0.05)]
    for c, grow in ((INK, 2), (color, 0)):
        pygame.draw.circle(surf, c, (cx - r * 0.95, cy - s * 0.12), r + grow)
        pygame.draw.circle(surf, c, (cx + r * 0.95, cy - s * 0.12), r + grow)
        if grow:
            pygame.draw.polygon(surf, c, [(pts[0][0] - 2, pts[0][1]), (pts[1][0], pts[1][1] + 3), (pts[2][0] + 2, pts[2][1])])
        else:
            pygame.draw.polygon(surf, c, pts)
    pygame.draw.circle(surf, (255, 170, 180), (cx - r * 1.2, cy - s * 0.2), max(2, r * 0.3))


def _plus(surf, cx, cy, s, color, thick=0.3):
    t = s * thick
    for rect in (pygame.Rect(cx - s / 2, cy - t / 2, s, t), pygame.Rect(cx - t / 2, cy - s / 2, t, s)):
        pygame.draw.rect(surf, INK, rect.inflate(4, 4), border_radius=3)
    for rect in (pygame.Rect(cx - s / 2, cy - t / 2, s, t), pygame.Rect(cx - t / 2, cy - s / 2, t, s)):
        pygame.draw.rect(surf, color, rect, border_radius=2)


def _shield(surf, cx, cy, s):
    w, h = s * 0.8, s * 0.9
    top = cy - h / 2
    pts = [(cx - w / 2, top), (cx + w / 2, top), (cx + w / 2, top + h * 0.45), (cx, top + h), (cx - w / 2, top + h * 0.45)]
    _poly(surf, (90, 150, 230), pts, 3)
    inner = [(cx - w / 4, top + h * 0.12), (cx, top + h * 0.12), (cx, top + h * 0.82), (cx - w / 2 + 6, top + h * 0.42)]
    pygame.draw.polygon(surf, (150, 200, 255), inner)


def _ankh(surf, cx, cy, s, color=(255, 205, 80)):
    width = max(3, int(s / 8))
    loop = pygame.Rect(0, 0, s * 0.42, s * 0.46)
    loop.midbottom = (cx, cy - s * 0.04)
    for c, extra in ((INK, 3), (color, 0)):
        pygame.draw.ellipse(surf, c, loop.inflate(extra, extra), width + extra)
        pygame.draw.line(surf, c, (cx, loop.bottom - 2), (cx, cy + s * 0.48), width + extra)
        pygame.draw.line(surf, c, (cx - s * 0.32, cy + s * 0.06), (cx + s * 0.32, cy + s * 0.06), width + extra)


def _skull(surf, cx, cy, s):
    bone = (236, 230, 214)
    head = pygame.Rect(0, 0, s * 0.8, s * 0.66)
    head.midtop = (cx, cy - s * 0.45)
    jaw = pygame.Rect(0, 0, s * 0.5, s * 0.3)
    jaw.midtop = (cx, head.bottom - s * 0.12)
    pygame.draw.ellipse(surf, INK, head.inflate(4, 4))
    pygame.draw.rect(surf, INK, jaw.inflate(4, 4), border_radius=4)
    pygame.draw.ellipse(surf, bone, head)
    pygame.draw.rect(surf, bone, jaw, border_radius=3)
    for dx in (-1, 1):
        pygame.draw.circle(surf, INK, (cx + dx * s * 0.17, head.centery + s * 0.04), s * 0.12)
    pygame.draw.polygon(surf, INK, [(cx, head.bottom - s * 0.2), (cx - s * 0.05, head.bottom - s * 0.1),
                                    (cx + s * 0.05, head.bottom - s * 0.1)])
    for i in (-1, 0, 1):
        pygame.draw.line(surf, INK, (cx + i * s * 0.1, jaw.top + 3), (cx + i * s * 0.1, jaw.bottom - 2), 1)


def _draw(surf, name, s):
    c = s / 2
    if name == "candy":
        _candy_corn(surf, c, c, s * 0.95)
    elif name == "double_candy":
        _candy_corn(surf, c - s * 0.16, c + s * 0.04, s * 0.72, -18)
        _candy_corn(surf, c + s * 0.18, c - s * 0.02, s * 0.72, 16)
    elif name == "bomb":
        _bomb(surf, c, c, s * 0.95)
    elif name == "bomb_power":
        _bomb(surf, c - s * 0.06, c + s * 0.04, s * 0.85)
        _plus(surf, c + s * 0.3, c + s * 0.28, s * 0.34, (255, 190, 70))
    elif name == "heart_plus":
        _heart(surf, c - s * 0.04, c, s * 0.9)
        _plus(surf, c + s * 0.3, c + s * 0.28, s * 0.34, (255, 255, 255))
    elif name == "heal":
        _plus(surf, c, c, s * 0.78, (110, 235, 120), 0.32)
    elif name == "shield":
        _shield(surf, c, c, s)
    elif name == "revive":
        _ankh(surf, c, c, s * 0.95)
    elif name == "skull":
        _skull(surf, c, c, s)
    else:
        pygame.draw.circle(surf, (200, 200, 200), (c, c), s * 0.4)


@lru_cache(maxsize=None)
def icon(name, size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    _draw(surf, name, size)
    return surf


def draw_icon(screen, name, center, size):
    surf = icon(name, int(size))
    screen.blit(surf, surf.get_rect(center=(int(center[0]), int(center[1]))))
