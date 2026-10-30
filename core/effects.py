"""Combat "juice": everything that makes hits feel heavy.

  Shake        camera shake that decays over time
  Particles    sparks, candy corn, zombie goo, ghost wisps, smoke, healing plus signs
  TimingRing   the shrinking ring for timed hits and timed blocks
  Swoosh       a fading arc that trails a punch
  Script       runs an attack/animation "script" written as a Python generator

Scripts read top-to-bottom like a storyboard:

    def punch(self):
        yield from tween(300, lambda t: move_hero(t))   # dash in over 300 ms
        yield from wait(100)                             # hold
        ...

`yield` hands control back to the game for one frame; the frame's dt comes
back as the value of the yield.
"""
import math
import random

import pygame

from core.ui import get_font, blit_centered


# ---- scripting -------------------------------------------------------------

def wait(ms):
    elapsed = 0
    while elapsed < ms:
        elapsed += (yield)


def tween(ms, fn, ease=None):
    """Call fn(progress) every frame for `ms`, with progress going 0 -> 1."""
    ease = ease or (lambda t: t)
    elapsed = 0
    while True:
        t = min(1.0, elapsed / ms) if ms else 1.0
        fn(ease(t))
        if t >= 1.0:
            return
        elapsed += (yield)


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in(t):
    return t ** 3


def ease_in_out(t):
    return 3 * t * t - 2 * t * t * t


def lerp(a, b, t):
    return a + (b - a) * t


class Script:
    """Runs a generator one frame at a time. `done` turns True when it ends."""

    def __init__(self, generator):
        self.gen = generator
        self.done = False
        try:
            next(self.gen)
        except StopIteration:
            self.done = True

    def update(self, dt):
        if self.done:
            return
        try:
            self.gen.send(dt)
        except StopIteration:
            self.done = True


# ---- screen shake ----------------------------------------------------------

class Shake:
    def __init__(self):
        self.strength = 0.0
        self.offset = (0, 0)

    def add(self, strength):
        self.strength = min(30.0, max(self.strength, strength))

    def update(self, dt):
        self.strength *= 0.5 ** (dt / 70)       # halves every 70 ms
        if self.strength < 0.4:
            self.strength = 0.0
            self.offset = (0, 0)
        else:
            s = self.strength
            self.offset = (random.uniform(-s, s), random.uniform(-s, s))


# ---- particles -------------------------------------------------------------

class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color", "gravity", "shape", "spin", "angle", "drag")

    def __init__(self, x, y, vx, vy, life, size, color, gravity=0.0, shape="circle", drag=0.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.size, self.color, self.gravity, self.shape = size, color, gravity, shape
        self.spin = random.uniform(-8, 8)
        self.angle = random.uniform(0, math.tau)
        self.drag = drag


class Particles:
    def __init__(self):
        self.items = []

    def update(self, dt):
        s = dt / 1000
        for p in self.items:
            p.life -= dt
            p.vy += p.gravity * s
            if p.drag:
                f = max(0.0, 1 - p.drag * s)
                p.vx *= f
                p.vy *= f
            p.x += p.vx * s
            p.y += p.vy * s
            p.angle += p.spin * s
        self.items = [p for p in self.items if p.life > 0]

    def draw(self, screen, offset=(0, 0)):
        ox, oy = offset
        for p in self.items:
            k = p.life / p.max_life
            size = max(1, p.size * (0.4 + 0.6 * k))
            x, y = p.x + ox, p.y + oy
            if p.shape == "circle":
                pygame.draw.circle(screen, p.color, (int(x), int(y)), int(size))
            elif p.shape == "ring":
                pygame.draw.circle(screen, p.color, (int(x), int(y)), int(size), 2)
            elif p.shape == "plus":
                w = max(2, int(size / 2.5))
                pygame.draw.rect(screen, p.color, (x - size, y - w / 2, size * 2, w))
                pygame.draw.rect(screen, p.color, (x - w / 2, y - size, w, size * 2))
            elif p.shape == "streak":
                length = size * 3
                ang = math.atan2(p.vy, p.vx)
                pygame.draw.line(screen, p.color, (x, y),
                                 (x - math.cos(ang) * length, y - math.sin(ang) * length), max(2, int(size / 2)))
            else:  # "candy": a little candy-corn triangle
                pts = [(x + math.cos(p.angle + i * math.tau / 3) * size,
                        y + math.sin(p.angle + i * math.tau / 3) * size) for i in range(3)]
                pygame.draw.polygon(screen, p.color, pts)

    # Presets ---------------------------------------------------------------
    def burst(self, x, y, colors, count, speed, life, size, gravity=0.0, shape="circle", spread=math.tau,
              direction=0.0, drag=0.0):
        for _ in range(count):
            a = direction + random.uniform(-spread / 2, spread / 2)
            v = random.uniform(speed * 0.4, speed)
            self.items.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v, random.uniform(life * 0.6, life),
                                       random.uniform(size * 0.6, size), random.choice(colors), gravity, shape, drag))

    def hit_sparks(self, x, y, direction, big=False):
        n = 26 if big else 14
        self.burst(x, y, [(255, 255, 255), (255, 230, 150), (255, 200, 80)], n, 650 if big else 480, 260, 5,
                   shape="streak", spread=1.6, direction=direction, drag=3)

    def candy_corn(self, x, y, count=16):
        self.burst(x, y, [(255, 150, 30), (255, 220, 60), (250, 250, 240)], count, 420, 900, 7,
                   gravity=1200, shape="candy", direction=-math.pi / 2, spread=2.4)

    def goo(self, x, y, count=16):
        self.burst(x, y, [(90, 200, 70), (60, 160, 50), (140, 230, 90)], count, 380, 700, 6,
                   gravity=1300, direction=-math.pi / 2, spread=2.6)

    def wisps(self, x, y, color=(200, 230, 255), count=14):
        self.burst(x, y, [color, (255, 255, 255)], count, 160, 800, 6, gravity=-120, drag=1.5)

    def heal(self, x, y):
        self.burst(x, y, [(100, 255, 120), (180, 255, 190)], 12, 90, 900, 7, gravity=-150, shape="plus", drag=1)

    def explosion(self, x, y):
        self.burst(x, y, [(255, 240, 160), (255, 170, 40), (255, 100, 20)], 30, 520, 450, 10, drag=3)
        self.burst(x, y, [(60, 55, 55), (90, 85, 80), (40, 38, 40)], 16, 160, 1100, 14, gravity=-90, drag=1.5)
        self.burst(x, y, [(255, 210, 120)], 1, 0, 300, 70, shape="ring")

    def dust(self, x, y, direction=0.0):
        self.burst(x, y, [(120, 110, 100), (90, 85, 80)], 8, 140, 500, 5, gravity=-60, direction=direction,
                   spread=1.2, drag=2)


# ---- timing ring -----------------------------------------------------------

PERFECT, GOOD, MISS = "perfect", "good", "miss"


class TimingRing:
    """A ring that shrinks onto a target circle. Press Space as they line up.

    duration   ms the ring takes to close (not counting a feint's stall)
    perfect/good   half-width of the timing windows in ms
    drift      (dx, dy) px the whole ring slides by while it closes (an arc, eased)
    hold       feint: ms the ring freezes about two-thirds of the way in. The real
               sweet spot comes that much later, so pressing on rhythm is early.
    forgive_early  a feint's first too-early press (before the stall's over) is ignored,
               so pressing on rhythm doesn't cost the block (a second early press counts).
    The first press is the only one that counts (no mashing).
    """

    HOLD_AT = 0.68               # a feint stalls once the ring is this far closed

    def __init__(self, center, duration, perfect=70, good=160, color=(255, 215, 0), label="SPACE",
                 drift=(0, 0), hold=0, forgive_early=False):
        self.start_center = center
        self.drift = drift
        self.closing_ms = duration                # visual closing time
        self.hold = hold
        self.hold_at = duration * self.HOLD_AT
        self.duration = duration + hold           # when the hit actually lands
        self.perfect = perfect
        self.good = good
        self.color = color
        self.label = label
        self.elapsed = 0
        self.result = None           # set on first press: PERFECT / GOOD / MISS
        self.forgive_early = forgive_early and bool(hold)
        self.forgiven = False        # (the one free early press has been used)
        self.flash = 0
        self.font = get_font(14, bold=True)

    @property
    def progress(self):
        """How far the ring has closed, 0-1 (it pauses during a feint)."""
        t = self.elapsed
        if self.hold and t > self.hold_at:
            t = self.hold_at if t < self.hold_at + self.hold else t - self.hold
        return min(1.0, t / self.closing_ms) if self.closing_ms else 1.0

    @property
    def stalled(self):
        return bool(self.hold) and self.hold_at < self.elapsed < self.hold_at + self.hold

    @property
    def center(self):
        """Where the ring is right now (it slides along a gentle curve as it closes)."""
        k = self.progress
        dx, dy = self.drift
        bend = math.sin(math.pi * k) * 0.35       # bow the path a little so it isn't a straight line
        return (self.start_center[0] + dx * k - dy * bend, self.start_center[1] + dy * k + dx * bend)

    def press(self):
        if self.result is not None:
            return
        error = abs(self.elapsed - self.duration)
        early = self.elapsed < self.hold_at + self.hold and error > self.good
        if early and self.forgive_early and not self.forgiven:
            self.forgiven = True          # the feint fooled you once: no harm done, press again
            self.flash = 120
            return
        self.result = PERFECT if error <= self.perfect else GOOD if error <= self.good else MISS
        self.flash = 200

    def final(self):
        return self.result or MISS

    def update(self, dt):
        self.elapsed += dt
        self.flash = max(0, self.flash - dt)

    @property
    def expired(self):
        return self.elapsed > self.duration + self.good

    def draw(self, screen):
        if self.result is not None and not self.flash:
            return
        cx, cy = self.center
        target_r = 34
        r = target_r + 110 * (1 - self.progress)
        in_window = abs(self.elapsed - self.duration) <= self.good
        pygame.draw.circle(screen, (255, 255, 255), (int(cx), int(cy)), target_r, 3)
        color = self.color if in_window else (230, 230, 230)
        if self.result == PERFECT:
            color = (255, 255, 120)
        pygame.draw.circle(screen, color, (int(cx), int(cy)), int(r), 4 if in_window else 3)
        blit_centered(screen, self.font.render(self.label, True, (255, 255, 255)), (cx, cy))


# ---- swoosh arc --------------------------------------------------------------

class Swoosh:
    """A crescent that flashes in front of a punch and fades."""

    def __init__(self, center, radius, start_deg, end_deg, color=(255, 255, 255), width=10, life=180):
        self.center, self.radius = center, radius
        self.start, self.end = math.radians(start_deg), math.radians(end_deg)
        self.color, self.width = color, width
        self.life = self.max_life = life

    def update(self, dt):
        self.life -= dt

    @property
    def alive(self):
        return self.life > 0

    def draw(self, screen, offset=(0, 0)):
        k = max(0.0, self.life / self.max_life)
        cx, cy = self.center[0] + offset[0], self.center[1] + offset[1]
        steps = 14
        outer, inner = [], []
        for i in range(steps + 1):
            a = self.start + (self.end - self.start) * i / steps
            thick = self.width * math.sin(math.pi * i / steps) * k
            outer.append((cx + math.cos(a) * (self.radius + thick), cy + math.sin(a) * (self.radius + thick)))
            inner.append((cx + math.cos(a) * (self.radius - thick), cy + math.sin(a) * (self.radius - thick)))
        surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (*self.color, int(220 * k)), outer + inner[::-1])
        screen.blit(surf, (0, 0))


_aura_cache = {}


def aura(color, size=(240, 280)):
    """Soft glowing oval to put behind a boss so it pops off dark backgrounds (cached)."""
    key = (color, size)
    if key not in _aura_cache:
        w, h = size
        surf = pygame.Surface(size, pygame.SRCALPHA)
        for i in range(12, 0, -1):
            t = i / 12
            rect = pygame.Rect(0, 0, int(w * t), int(h * t))
            rect.center = (w // 2, h // 2)
            pygame.draw.ellipse(surf, (*color, int(16 + 20 * (1 - t))), rect)
        _aura_cache[key] = surf
    return _aura_cache[key]
