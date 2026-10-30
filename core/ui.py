"""Small drawing helpers shared by the HUDs, modals, and menus."""
import math
import random
from functools import lru_cache

import pygame

from core.settings import FONT_NAME

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
DARK_GREY = (60, 60, 60)
PANEL_BG = (30, 30, 30)
GOLD = (255, 215, 0)
CANDY_PINK = (255, 200, 255)
HEAL_GREEN = (100, 255, 100)
DAMAGE_RED = (255, 80, 80)
BLOCK_BLUE = (150, 200, 255)
INK = (12, 8, 14)
PUMPKIN = (255, 140, 40)


@lru_cache(maxsize=None)
def get_font(size, bold=False):
    """SysFont lookups are slow, so each size is created once and reused."""
    return pygame.font.SysFont(FONT_NAME, size, bold=bold)


def draw_bar(surface, x, y, width, height, value, max_value, color):
    """A health-style bar with a dark background and white outline."""
    pygame.draw.rect(surface, DARK_GREY, (x, y, width, height))
    if max_value > 0:
        ratio = max(0.0, min(1.0, value / max_value))
        pygame.draw.rect(surface, color, (x, y, int(width * ratio), height))
    pygame.draw.rect(surface, WHITE, (x, y, width, height), 2)


def blit_centered(surface, text_surface, center):
    surface.blit(text_surface, text_surface.get_rect(center=center))


def draw_button(surface, rect, label, font, fill, text_color=BLACK, border=WHITE):
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, border, rect, 2)
    blit_centered(surface, font.render(label, True, text_color), rect.center)


def draw_panel(surface, rect, border_color, fill=PANEL_BG, border_width=4):
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, border_color, rect, border_width)


def wrap_text(font, text, max_width):
    """Split text into lines that fit max_width pixels."""
    lines, current = [], ""
    for word in text.split(" "):
        test = f"{current} {word}".strip()
        if font.size(test)[0] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_speech_bubble(screen, name, lines, place, hint=True, name_color=(20, 20, 20), padding=10):
    """White speech bubble with a speaker name. `place(width, height)` returns
    the bubble's top-left, so callers decide where it sits. Returns its rect."""
    font, name_font = get_font(20), get_font(18, bold=True)
    name_surface = name_font.render(name, True, name_color)
    line_h = font.get_height()
    width = max([font.size(line)[0] for line in lines] + [name_surface.get_width()]) + padding * 2
    height = line_h * len(lines) + name_surface.get_height() + padding * 3
    rect = pygame.Rect(*place(width, height), width, height)

    pygame.draw.rect(screen, WHITE, rect, border_radius=8)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=8)
    screen.blit(name_surface, (rect.x + padding, rect.y + padding))
    y = rect.y + padding + name_surface.get_height() + 5
    for line in lines:
        screen.blit(font.render(line, True, BLACK), (rect.x + padding, y))
        y += line_h
    if hint:
        screen.blit(font.render("[Space or click]", True, (100, 100, 100)), (rect.x + padding, rect.bottom))
    return rect


# ---- spooky menu kit (shops, bag, battle results) ------------------------------

def shade(color, amount):
    """Lighten (amount > 0) or darken (amount < 0) a color."""
    if amount >= 0:
        return tuple(int(c + (255 - c) * amount) for c in color[:3])
    return tuple(int(c * (1 + amount)) for c in color[:3])


@lru_cache(maxsize=None)
def outlined_text(text, size, color, bold=True, outline=2, outline_color=INK):
    """Text with a solid dark outline so it reads on anything (cached)."""
    font = get_font(size, bold)
    base = font.render(text, True, outline_color)
    out = pygame.Surface((base.get_width() + outline * 2, base.get_height() + outline * 2), pygame.SRCALPHA)
    for dx in range(-outline, outline + 1):
        for dy in range(-outline, outline + 1):
            if dx * dx + dy * dy <= outline * outline + 1:
                out.blit(base, (dx + outline, dy + outline))
    out.blit(font.render(text, True, color), (outline, outline))
    return out


def _cobweb(surf, corner, size, color):
    """A little corner cobweb: spokes fanning out of a corner, joined by sagging threads."""
    cx, cy, sx, sy = corner
    spokes = [math.radians(a) for a in (0, 22, 45, 68, 90)]
    rings = (0.35, 0.65, 1.0)
    pts = [[(cx + sx * math.cos(a) * size * r, cy + sy * math.sin(a) * size * r) for a in spokes] for r in rings]
    for a in spokes:
        pygame.draw.aaline(surf, color, (cx, cy), (cx + sx * math.cos(a) * size * 1.08, cy + sy * math.sin(a) * size * 1.08))
    for ring in pts:
        for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
            mid = ((x0 + x1) / 2 - sx * 3, (y0 + y1) / 2 - sy * 3)    # threads sag toward the corner
            pygame.draw.aalines(surf, color, False, [(x0, y0), mid, (x1, y1)])


@lru_cache(maxsize=32)
def spooky_panel(size, accent, top=(40, 28, 48), bottom=(13, 10, 17), radius=16, webs=True):
    """A dark, slightly grainy panel with an inked frame, an accent trim line,
    a soft accent glow at the top, and cobwebs in two corners (cached)."""
    w, h = size
    surf = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(h):
        t = y / max(1, h - 1)
        pygame.draw.line(surf, [int(a + (b - a) * t) for a, b in zip(top, bottom)], (0, y), (w, y))
    glow = pygame.Surface(size, pygame.SRCALPHA)
    for i in range(8, 0, -1):
        r = pygame.Rect(0, 0, int(w * 0.95 * i / 8), int(h * 0.55 * i / 8))
        r.center = (w // 2, 0)
        pygame.draw.ellipse(glow, (*accent, 7), r)
    surf.blit(glow, (0, 0))
    rng = random.Random(w * 31 + h)
    for _ in range(w * h // 45):            # grain
        x, y = rng.randrange(w), rng.randrange(h)
        c = surf.get_at((x, y))
        k = rng.uniform(-0.35, 0.25)
        surf.set_at((x, y), shade(c, k) + (255,))
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    rect = surf.get_rect()
    pygame.draw.rect(surf, INK, rect, 4, border_radius=radius)
    pygame.draw.rect(surf, shade(accent, -0.25), rect.inflate(-10, -10), 2, border_radius=max(2, radius - 5))
    pygame.draw.rect(surf, (*shade(accent, 0.3), 90), rect.inflate(-14, -14), 1, border_radius=max(2, radius - 7))
    if webs:
        web = (*shade(accent, 0.55), 70)
        _cobweb(surf, (8, 8, 1, 1), 46, web)
        _cobweb(surf, (w - 8, h - 8, -1, -1), 40, web)
    return surf


@lru_cache(maxsize=8)
def _panel_shadow(size, radius):
    shadow = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 120), shadow.get_rect(), border_radius=radius)
    return shadow


def draw_spooky_panel(screen, rect, accent, **kw):
    """Panel with a drop shadow, drawn at rect."""
    screen.blit(_panel_shadow(rect.size, kw.get("radius", 16)), (rect.x + 6, rect.y + 9))
    screen.blit(spooky_panel(rect.size, accent, **kw), rect)


_dim_cache = {}


def dim_screen(screen, alpha=150):
    """Darken everything already drawn (behind a menu), with darker edges."""
    key = (screen.get_size(), alpha)
    if key not in _dim_cache:
        small = pygame.Surface((40, 30), pygame.SRCALPHA)
        for y in range(30):
            for x in range(40):
                d = ((x - 19.5) / 20) ** 2 + ((y - 14.5) / 15) ** 2     # 0 center .. ~2 corners
                small.set_at((x, y), (6, 3, 10, min(255, int(alpha + 70 * d))))
        surf = pygame.transform.smoothscale(small, screen.get_size())
        _dim_cache[key] = surf
    screen.blit(_dim_cache[key], (0, 0))


def draw_candy_button(screen, rect, label, fill, hover=False, enabled=True, size=20, icon_name=None, press=0.0):
    """Chunky rounded button with a darker lip underneath, like a hard candy.
    `press` (0-1) pushes it down for a click flash."""
    if not enabled:
        fill = (70, 64, 74)
    elif hover:
        fill = shade(fill, 0.18)
    lip = 4
    r = min(rect.height // 2, 12)
    down = int(lip * press)
    body = pygame.Rect(rect.x, rect.y + down, rect.width, rect.height - lip)
    pygame.draw.rect(screen, INK, rect.inflate(4, 4), border_radius=r + 2)
    pygame.draw.rect(screen, shade(fill, -0.45), rect, border_radius=r)
    pygame.draw.rect(screen, fill, body, border_radius=r)
    shine = pygame.Rect(body.x + 6, body.y + 3, body.width - 12, max(2, body.height // 4))
    pygame.draw.rect(screen, shade(fill, 0.35), shine, border_radius=r)
    text = outlined_text(label, size, WHITE if enabled else (170, 165, 175), True, 2)
    if icon_name:
        from core.icons import icon
        ic = icon(icon_name, int(body.height * 0.75))
        total = ic.get_width() + 4 + text.get_width()
        x = body.centerx - total // 2
        screen.blit(ic, ic.get_rect(midleft=(x, body.centery)))
        screen.blit(text, text.get_rect(midleft=(x + ic.get_width() + 4, body.centery)))
    else:
        screen.blit(text, text.get_rect(center=body.center))


# ---- health bars (the HUDs) -------------------------------------------------
TRAIL_HOLD_MS = 380          # after a hit, the lost chunk lingers this long (pale) before draining away
TRAIL_COLOR = (225, 105, 95)    # the chunk just lost: a muted red


class HealthBar:
    """A framed HP bar: glossy fill that slides to the new value, a red "damage trail" that hangs
    on for a moment after a hit and then drains, notches every 10%, and the numbers inside."""

    def __init__(self, value):
        self.shown = float(value)        # the fill (slides toward the real value)
        self.trail = float(value)        # the chunk you just lost
        self.hold = 0
        self.last = value

    def update(self, value, dt):
        if value < self.last:
            self.hold = TRAIL_HOLD_MS    # just got hit: the trail stays put for a moment
        self.last = value
        k = min(1.0, dt / 90)
        self.shown += (value - self.shown) * k
        if value >= self.trail:
            self.trail = max(self.shown, value)
        elif self.hold > 0:
            self.hold -= dt
        else:
            self.trail += (value - self.trail) * min(1.0, dt / 140)

    def draw(self, screen, rect, max_value, color, text=None, right_to_left=False, low_pulse=0.0,
             trail_color=TRAIL_COLOR):
        """low_pulse (0-1) flashes the frame red, for when HP is low."""
        rect = pygame.Rect(rect)
        frame = rect.inflate(6, 6)
        pygame.draw.rect(screen, INK, frame, border_radius=7)
        rim = shade((150, 40, 40), 0.4 + 0.6 * low_pulse) if low_pulse else (78, 64, 84)
        pygame.draw.rect(screen, rim, frame.inflate(-2, -2), 2, border_radius=6)
        pygame.draw.rect(screen, (26, 20, 30), rect, border_radius=4)
        top = max(1, max_value)

        def part(value):
            w = int(rect.width * max(0.0, min(1.0, value / top)))
            r = pygame.Rect(rect.x, rect.y, w, rect.height)
            if right_to_left:
                r.right = rect.right
            return r

        trail = part(self.trail)
        if trail.width:
            pygame.draw.rect(screen, trail_color, trail, border_radius=4)
        fill = part(self.shown)
        if fill.width:
            pygame.draw.rect(screen, shade(color, -0.25), fill, border_radius=4)            # body
            pygame.draw.rect(screen, color, fill.inflate(0, -rect.height // 3).move(0, -rect.height // 6),
                             border_radius=3)
            gloss = fill.inflate(-4, 0)
            gloss.height = max(2, rect.height // 4)
            gloss.y = rect.y + 2
            pygame.draw.rect(screen, shade(color, 0.45), gloss, border_radius=2)
        for i in range(1, 10):                                                           # notches every 10%
            x = rect.x + rect.width * i // 10
            pygame.draw.line(screen, (0, 0, 0), (x, rect.bottom - rect.height // 3), (x, rect.bottom - 1), 1)
        if text:
            label = outlined_text(text, max(12, rect.height - 4), WHITE, True, 2)
            screen.blit(label, label.get_rect(center=(rect.centerx, rect.centery + 1)))
