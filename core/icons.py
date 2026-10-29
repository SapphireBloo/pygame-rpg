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


def _flask(surf, cx, cy, s, liquid, round_body=True, cork=(150, 105, 60)):
    """A little glass bottle with colored liquid (potions, remedy, elixir, chin juice)."""
    body = pygame.Rect(0, 0, s * 0.62, s * 0.56)
    body.midbottom = (cx, cy + s * 0.44)
    neck = pygame.Rect(0, 0, s * 0.24, s * 0.26)
    neck.midbottom = (cx, body.top + 4)
    cork_r = pygame.Rect(0, 0, s * 0.3, s * 0.12)
    cork_r.midbottom = (cx, neck.top + 2)
    glass = (210, 225, 235)
    if round_body:
        pygame.draw.ellipse(surf, INK, body.inflate(4, 4))
        pygame.draw.rect(surf, INK, neck.inflate(4, 2))
        pygame.draw.ellipse(surf, glass, body)
        fill = body.inflate(-6, -6)
        fill.height = int(fill.height * 0.7)
        fill.bottom = body.bottom - 3
        pygame.draw.ellipse(surf, liquid, fill)
    else:
        pygame.draw.rect(surf, INK, body.inflate(4, 4), border_radius=5)
        pygame.draw.rect(surf, INK, neck.inflate(4, 2))
        pygame.draw.rect(surf, glass, body, border_radius=4)
        fill = body.inflate(-6, -6)
        fill.height = int(fill.height * 0.72)
        fill.bottom = body.bottom - 3
        pygame.draw.rect(surf, liquid, fill, border_radius=3)
    pygame.draw.rect(surf, glass, neck)
    pygame.draw.rect(surf, INK, cork_r.inflate(2, 2), border_radius=2)
    pygame.draw.rect(surf, cork, cork_r, border_radius=2)
    pygame.draw.line(surf, (255, 255, 255), (body.left + s * 0.12, body.top + s * 0.12),
                     (body.left + s * 0.12, body.top + s * 0.28), max(2, int(s / 18)))


def _blob(surf, cx, cy, s, color):
    for dx, dy, r in ((0, 0.08, 0.3), (-0.18, 0.15, 0.2), (0.2, 0.14, 0.18), (0.05, -0.15, 0.17)):
        pygame.draw.circle(surf, INK, (cx + dx * s, cy + dy * s), r * s + 2)
    for dx, dy, r in ((0, 0.08, 0.3), (-0.18, 0.15, 0.2), (0.2, 0.14, 0.18), (0.05, -0.15, 0.17)):
        pygame.draw.circle(surf, color, (cx + dx * s, cy + dy * s), r * s)
    for dx in (-0.08, 0.1):
        pygame.draw.circle(surf, INK, (cx + dx * s, cy + 0.02 * s), max(2, s * 0.05))


def _crystal(surf, cx, cy, s, color):
    pts = [(cx, cy - s * 0.45), (cx + s * 0.22, cy - s * 0.1), (cx + s * 0.14, cy + s * 0.42),
           (cx - s * 0.14, cy + s * 0.42), (cx - s * 0.22, cy - s * 0.1)]
    _poly(surf, color, pts, 2)
    pygame.draw.line(surf, tuple(min(255, c + 90) for c in color), (cx - s * 0.06, cy - s * 0.3),
                     (cx - s * 0.08, cy + s * 0.3), 2)


def _horn(surf, cx, cy, s, color):
    """A curved horn: wide at the base (bottom left), curling up to a point."""
    p0, p1, p2 = (cx - s * 0.3, cy + s * 0.36), (cx + s * 0.3, cy + s * 0.32), (cx + s * 0.26, cy - s * 0.42)
    left, right = [], []
    for i in range(13):
        t = i / 12
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
        dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
        n = math.hypot(dx, dy) or 1
        w = s * 0.17 * (1 - t) + 1
        left.append((x - dy / n * w, y + dx / n * w))
        right.append((x + dy / n * w, y - dx / n * w))
    _poly(surf, color, left + right[::-1], 3)
    for t in (0.25, 0.45, 0.65):                      # ridges
        i = int(t * 12)
        pygame.draw.line(surf, tuple(min(255, c + 70) for c in color), left[i], right[i], 2)


def _glove(surf, cx, cy, s, color=(210, 45, 45)):
    """A boxing glove facing right: padded fist, thumb, and a white cuff."""
    fist = pygame.Rect(0, 0, s * 0.56, s * 0.5)
    fist.center = (cx + s * 0.05, cy - s * 0.06)
    thumb = pygame.Rect(0, 0, s * 0.26, s * 0.22)
    thumb.center = (fist.left + s * 0.14, fist.bottom - s * 0.1)
    cuff = pygame.Rect(0, 0, s * 0.36, s * 0.2)
    cuff.midtop = (fist.centerx - s * 0.08, fist.bottom - s * 0.06)
    radius = int(s * 0.2)
    for rect, r in ((fist, radius), (cuff, 3)):
        pygame.draw.rect(surf, INK, rect.inflate(4, 4), border_radius=r + 2)
    pygame.draw.ellipse(surf, INK, thumb.inflate(4, 4))
    pygame.draw.rect(surf, (235, 230, 220), cuff, border_radius=3)
    pygame.draw.rect(surf, color, fist, border_radius=radius)
    pygame.draw.ellipse(surf, tuple(max(0, v - 30) for v in color), thumb)
    pygame.draw.ellipse(surf, INK, thumb, 1)
    shine = tuple(min(255, v + 90) for v in color)
    pygame.draw.line(surf, shine, (fist.left + s * 0.14, fist.top + s * 0.1), (fist.right - s * 0.14, fist.top + s * 0.1),
                     max(2, int(s / 18)))


def _burst(surf, cx, cy, s, color):
    """A spiky impact star."""
    pts = []
    for k in range(16):
        r = s * (0.48 if k % 2 == 0 else 0.26)
        a = k * math.pi / 8
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    _poly(surf, color, pts, 2)


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
    elif name == "potion":
        _flask(surf, c, c, s, (220, 50, 70))
    elif name == "remedy":
        _flask(surf, c, c, s, (90, 200, 110), round_body=False)
    elif name == "elixir":
        _flask(surf, c, c, s, (255, 170, 40), cork=(240, 200, 80))
        for dx, dy in ((-0.32, -0.3), (0.34, -0.12), (0.3, 0.32)):
            pygame.draw.circle(surf, (255, 245, 180), (c + dx * s, c + dy * s), max(2, s * 0.05))
    elif name == "chin_juice":
        _flask(surf, c, c, s, (255, 205, 40), round_body=False, cork=(200, 60, 60))
        bolt = [(c + 0.04 * s, c - 0.02 * s), (c - 0.08 * s, c + 0.18 * s), (c + 0.02 * s, c + 0.18 * s),
                (c - 0.06 * s, c + 0.38 * s), (c + 0.12 * s, c + 0.12 * s), (c + 0.02 * s, c + 0.12 * s)]
        pygame.draw.polygon(surf, (255, 255, 255), bolt)
    elif name == "ectoplasm":
        _blob(surf, c, c, s, (150, 240, 150))
    elif name == "spur":
        pygame.draw.circle(surf, INK, (c, c), s * 0.3 + 2)
        for i in range(8):
            a = i * math.tau / 8
            pygame.draw.line(surf, INK, (c, c), (c + math.cos(a) * s * 0.42, c + math.sin(a) * s * 0.42), 6)
            pygame.draw.line(surf, (200, 205, 220), (c, c), (c + math.cos(a) * s * 0.4, c + math.sin(a) * s * 0.4), 3)
        pygame.draw.circle(surf, (150, 155, 175), (c, c), s * 0.14)
        pygame.draw.circle(surf, INK, (c, c), s * 0.06)
    elif name == "antler":
        col, w = (130, 80, 55), max(3, int(s / 10))
        for color, width in ((INK, w + 4), (col, w)):
            pygame.draw.line(surf, color, (c - s * 0.1, c + s * 0.42), (c + s * 0.05, c - s * 0.4), width)
            pygame.draw.line(surf, color, (c - s * 0.04, c + s * 0.1), (c - s * 0.36, c - s * 0.2), width)
            pygame.draw.line(surf, color, (c + s * 0.0, c - s * 0.12), (c + s * 0.34, c - s * 0.32), width)
            pygame.draw.line(surf, color, (c - s * 0.22, c - s * 0.06), (c - s * 0.3, c - s * 0.4), width)
    elif name == "tooth":
        pts = [(c - s * 0.26, c - s * 0.32), (c + s * 0.26, c - s * 0.32), (c + s * 0.22, c + s * 0.05),
               (c + s * 0.1, c + s * 0.42), (c, c + s * 0.1), (c - s * 0.1, c + s * 0.42), (c - s * 0.22, c + s * 0.05)]
        _poly(surf, (225, 215, 160), pts, 3)
        pygame.draw.circle(surf, (120, 160, 70), (c + s * 0.08, c - s * 0.12), max(2, s * 0.06))
    elif name == "shard":
        _crystal(surf, c, c, s, (150, 110, 230))
    elif name == "hex_stone":
        pygame.draw.circle(surf, INK, (c, c), s * 0.36 + 2)
        pygame.draw.circle(surf, (110, 40, 170), (c, c), s * 0.36)
        pygame.draw.circle(surf, (200, 120, 255), (c, c), s * 0.2, 2)
        pygame.draw.circle(surf, (235, 200, 255), (c - s * 0.12, c - s * 0.12), max(2, s * 0.07))
    elif name == "scale":
        pts = [(c, c - s * 0.42), (c + s * 0.34, c - s * 0.05), (c, c + s * 0.42), (c - s * 0.34, c - s * 0.05)]
        _poly(surf, (240, 120, 40), pts, 3)
        pygame.draw.lines(surf, (255, 210, 90), False, [(c - s * 0.18, c - s * 0.02), (c, c + s * 0.2),
                                                         (c + s * 0.18, c - s * 0.02)], 2)
    elif name == "horn":
        _horn(surf, c, c, s, (190, 40, 30))
    elif name == "bag":                             # a tied-up sack
        sack = [(c - s * 0.3, c - s * 0.08), (c + s * 0.3, c - s * 0.08), (c + s * 0.4, c + s * 0.32),
                (c + s * 0.26, c + s * 0.44), (c - s * 0.26, c + s * 0.44), (c - s * 0.4, c + s * 0.32)]
        neck = [(c - s * 0.16, c - s * 0.3), (c + s * 0.16, c - s * 0.3), (c + s * 0.22, c - s * 0.08),
                (c - s * 0.22, c - s * 0.08)]
        _poly(surf, (170, 120, 70), neck, 2)
        _poly(surf, (190, 140, 85), sack, 3)
        pygame.draw.line(surf, (110, 70, 40), (c - s * 0.24, c - s * 0.1), (c + s * 0.24, c - s * 0.1), max(3, int(s / 10)))
        pygame.draw.line(surf, (225, 185, 125), (c - s * 0.22, c + s * 0.08), (c - s * 0.26, c + s * 0.3), 2)
        _candy_corn(surf, c + s * 0.06, c + s * 0.2, s * 0.3, 12)
    elif name == "quick_hands":                     # small glove with speed lines
        for i, dy in enumerate((-0.18, 0.0, 0.18)):
            x0 = c - s * (0.48 - 0.06 * (i % 2))
            pygame.draw.line(surf, INK, (x0, c + dy * s), (c - s * 0.16, c + dy * s), 6)
            pygame.draw.line(surf, (130, 220, 255), (x0 + 1, c + dy * s), (c - s * 0.17, c + dy * s), 3)
        _glove(surf, c + s * 0.1, c, s * 0.92, (70, 150, 230))
    elif name == "heavy_hands":                     # big glove over an impact burst
        _burst(surf, c + s * 0.12, c - s * 0.04, s * 0.9, (255, 190, 60))
        _glove(surf, c - s * 0.04, c + s * 0.04, s * 0.98)
    elif name == "counter":                         # glove with a curved "comes back" arrow
        w = max(3, int(s / 11))
        arc = pygame.Rect(0, 0, s * 0.8, s * 0.7)
        arc.center = (c, c + s * 0.02)
        for color, width in ((INK, w + 4), ((255, 200, 80), w)):
            pygame.draw.arc(surf, color, arc, math.radians(200), math.radians(340), width)
        tip = (arc.left + s * 0.06, arc.centery + s * 0.18)
        _poly(surf, (255, 200, 80), [(tip[0] - s * 0.12, tip[1] - s * 0.04), (tip[0] + s * 0.1, tip[1] - s * 0.1),
                                     (tip[0] + s * 0.02, tip[1] + s * 0.12)], 2)
        _glove(surf, c + s * 0.06, c - s * 0.1, s * 0.74, (200, 150, 60))
    elif name == "iron_chin":                       # steel jaw plate with a gold bolt
        jaw = [(c - s * 0.36, c - s * 0.3), (c + s * 0.36, c - s * 0.3), (c + s * 0.3, c + s * 0.12),
               (c + s * 0.1, c + s * 0.4), (c - s * 0.1, c + s * 0.4), (c - s * 0.3, c + s * 0.12)]
        _poly(surf, (150, 160, 180), jaw, 3)
        pygame.draw.line(surf, (215, 222, 235), (c - s * 0.26, c - s * 0.22), (c + s * 0.26, c - s * 0.22), 2)
        for dx in (-0.24, 0.24):
            pygame.draw.circle(surf, INK, (c + dx * s, c - s * 0.12), max(2, s * 0.04))
        bolt = [(c + 0.06 * s, c - 0.2 * s), (c - 0.12 * s, c + 0.06 * s), (c, c + 0.06 * s),
                (c - 0.06 * s, c + 0.3 * s), (c + 0.14 * s, c - 0.02 * s), (c + 0.02 * s, c - 0.02 * s)]
        _poly(surf, (255, 205, 40), bolt, 2)
    elif name == "thick_skin":                      # stitched leather hide
        hide = [(c - s * 0.4, c - s * 0.3), (c - s * 0.18, c - s * 0.4), (c + s * 0.18, c - s * 0.36),
                (c + s * 0.42, c - s * 0.22), (c + s * 0.36, c + s * 0.2), (c + s * 0.12, c + s * 0.42),
                (c - s * 0.16, c + s * 0.38), (c - s * 0.4, c + s * 0.16)]
        _poly(surf, (165, 115, 70), hide, 3)
        pygame.draw.line(surf, (205, 160, 110), (c - s * 0.26, c - s * 0.2), (c + s * 0.22, c - s * 0.22), 2)
        for i in range(5):                          # stitches down the middle
            y = c - s * 0.24 + i * s * 0.12
            pygame.draw.line(surf, (240, 225, 190), (c - s * 0.06, y), (c + s * 0.06, y + s * 0.06), 2)
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
