"""Frame-by-frame character animation (Charlie, zombies, and future monsters).

Characters are positioned by their FEET: you tell a sprite "stand here" and
every animation lines up on that spot, even when one animation's art (like
GameArt2D's Dead or Slide frames) is drawn on a different-size canvas.

Art is assumed to face RIGHT; facing left is a mirrored copy.
"""
import math
from functools import lru_cache

import pygame

from core.settings import IMAGES_DIR

INK_COLOR = (12, 8, 14)


class Animation:
    """One animation's frames plus where the feet are inside each frame."""

    def __init__(self, frames, anchor, frame_ms, loop=True):
        self.frames = frames                     # facing right
        self.flipped = tuple(pygame.transform.flip(f, True, False) for f in frames)
        self.anchor = anchor                     # (x, y) of the feet inside a frame
        self.frame_ms = frame_ms
        self.loop = loop
        self._white = {}

    def __len__(self):
        return len(self.frames)

    @property
    def duration(self):
        return len(self.frames) * self.frame_ms

    def frame(self, index, facing_right):
        """Returns (surface, anchor) for drawing."""
        if facing_right:
            return self.frames[index], self.anchor
        surface = self.flipped[index]
        return surface, (surface.get_width() - self.anchor[0], self.anchor[1])

    def white(self, index, facing_right):
        """All-white silhouette of a frame, for hit flashes (cached)."""
        key = (index, facing_right)
        if key not in self._white:
            surface, _ = self.frame(index, facing_right)
            flash = surface.copy()
            flash.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            self._white[key] = flash
        return self._white[key]


class AnimatedSprite:
    """Plays a character's animations. Call update(dt) each frame, draw(...) to show.

    Optional transforms for juicy motion: angle (degrees, + leans back),
    scale_x/scale_y (squash and stretch around the feet), lift (pixels up),
    flash (ms of white hit-flash remaining), alpha.
    """

    def __init__(self, animations, start="idle"):
        self.animations = animations
        self.name = None
        self.index = 0
        self.timer = 0
        self.finished = False
        self.speed = 1.0
        self.angle = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.lift = 0.0
        self.flash = 0
        self.alpha = 255
        self.play(start)

    def play(self, name, restart=False, speed=1.0):
        self.speed = speed
        if name == self.name and not restart:
            return
        self.name = name
        self.index = 0
        self.timer = 0
        self.finished = False

    def has(self, name):
        return name in self.animations

    @property
    def current(self):
        return self.animations[self.name]

    def reset_pose(self):
        self.angle, self.scale_x, self.scale_y, self.lift = 0.0, 1.0, 1.0, 0.0

    def update(self, dt):
        self.flash = max(0, self.flash - dt)
        anim = self.current
        if self.finished:
            return
        self.timer += dt * self.speed
        while self.timer >= anim.frame_ms:
            self.timer -= anim.frame_ms
            if self.index + 1 < len(anim):
                self.index += 1
            elif anim.loop:
                self.index = 0
            else:
                self.finished = True     # hold the last frame (e.g. lying dead)
                break

    def _surface(self, facing_right):
        anim = self.current
        surface, anchor = anim.frame(self.index, facing_right)
        if self.flash:
            surface = anim.white(self.index, facing_right)
        return surface, anchor

    def draw(self, screen, feet_x, feet_y, facing_right=True):
        surface, (ax, ay) = self._surface(facing_right)
        feet_y -= self.lift
        posed = self.angle or self.scale_x != 1.0 or self.scale_y != 1.0
        if posed:
            surface, (ax, ay) = _pose(surface, (ax, ay), self.angle if facing_right else -self.angle,
                                      self.scale_x, self.scale_y)
        if self.alpha < 255:
            surface = surface.copy()
            surface.set_alpha(self.alpha)
        screen.blit(surface, (round(feet_x - ax), round(feet_y - ay)))


def _pose(surface, anchor, angle, sx, sy):
    """Scale and rotate a frame around its feet anchor. Returns (surface, new_anchor)."""
    if sx != 1.0 or sy != 1.0:
        w, h = surface.get_size()
        surface = pygame.transform.smoothscale(surface, (max(1, round(w * sx)), max(1, round(h * sy))))
        anchor = (anchor[0] * sx, anchor[1] * sy)
    if angle:
        w, h = surface.get_size()
        cx, cy = w / 2, h / 2
        vx, vy = anchor[0] - cx, anchor[1] - cy
        rotated = pygame.transform.rotate(surface, angle)
        rad = math.radians(angle)
        # pygame rotates counter-clockwise; rotate the anchor vector to match
        rx = vx * math.cos(rad) + vy * math.sin(rad)
        ry = -vx * math.sin(rad) + vy * math.cos(rad)
        rw, rh = rotated.get_size()
        anchor = (rw / 2 + rx, rh / 2 + ry)
        surface = rotated
    return surface, anchor


# ---- loading GameArt2D-style folders ("Idle (1).png", "Walk (1).png", ...) ----

def _feet_center_x(image, bbox):
    """Middle of the lowest strip of visible pixels: roughly between the feet."""
    strip_h = max(4, bbox.height // 12)
    strip = pygame.Rect(bbox.left, bbox.bottom - strip_h, bbox.width, strip_h)
    feet = image.subsurface(strip).get_bounding_rect()
    return strip.left + feet.centerx


def _ink(image, thickness):
    """Return the frame on a slightly bigger canvas with a thick dark outline."""
    silhouette = image.copy()
    silhouette.fill((*INK_COLOR, 255), special_flags=pygame.BLEND_RGBA_MIN)
    silhouette.fill((*INK_COLOR, 0), special_flags=pygame.BLEND_RGBA_MAX)
    w, h = image.get_size()
    out = pygame.Surface((w + thickness * 2, h + thickness * 2), pygame.SRCALPHA)
    steps = 12
    for i in range(steps):
        a = math.tau * i / steps
        out.blit(silhouette, (thickness + round(math.cos(a) * thickness), thickness + round(math.sin(a) * thickness)))
    out.blit(image, (thickness, thickness))
    return out


def _sequences(folder):
    """{"idle": [surfaces], "walk": [...], ...} for every "<Name> (1).png" series in a folder."""
    path = IMAGES_DIR / folder
    names = sorted({p.name.split(" (")[0] for p in path.glob("* (1).png")})
    result = {}
    for name in names:
        frames, n = [], 1
        while (path / f"{name} ({n}).png").is_file():
            frames.append(pygame.image.load(path / f"{name} ({n}).png").convert_alpha())
            n += 1
        result[name.lower()] = frames
    return result


DEFAULT_FRAME_MS = {"idle": 90, "walk": 110, "run": 70, "attack": 70, "dead": 80, "jump": 60, "slide": 50}
NON_LOOPING = {"dead", "jump", "slide"}


@lru_cache(maxsize=None)
def load_gameart2d_character(folder, height, speeds=None, ink=0):
    """Load every animation in assets/images/<folder> (Idle, Walk, Run, Attack, Dead...).

    height  how tall the character should stand on screen, in pixels
    speeds  optional ((name, frame_ms), ...) overrides
    ink     outline thickness in pixels (0 = none) for a grittier, inked look
    Returns {"idle": Animation, "walk": Animation, ...} (lowercase names).
    """
    frame_ms = dict(DEFAULT_FRAME_MS)
    frame_ms.update(dict(speeds or ()))
    raw = _sequences(folder)
    if "idle" not in raw:
        raise FileNotFoundError(f"No 'Idle (1).png' found in assets/images/{folder}")

    # Measure the standing pose once; every animation uses the same scale
    idle0 = raw["idle"][0]
    idle_box = idle0.get_bounding_rect()
    scale = height / idle_box.height
    stand_anchor = (_feet_center_x(idle0, idle_box), idle_box.bottom)

    def prepare(images):
        out = []
        for img in images:
            img = pygame.transform.smoothscale(img, (round(img.get_width() * scale), round(img.get_height() * scale)))
            out.append(_ink(img, ink) if ink else img)
        return tuple(out)

    animations = {}
    for name, images in raw.items():
        if images[0].get_size() == idle0.get_size():
            ax, ay = stand_anchor            # same canvas as Idle: same feet point
        else:
            # Different canvas (Dead, Slide): line up this animation's first frame
            # feet with the standing feet; ground line from its final frame.
            ax = _feet_center_x(images[0], images[0].get_bounding_rect())
            ay = images[-1].get_bounding_rect().bottom
        anchor = (ax * scale + ink, ay * scale + ink)
        animations[name] = Animation(prepare(images), anchor, frame_ms.get(name, 80),
                                     loop=name not in NON_LOOPING)
    return animations


def frames_animation(frames, frame_ms, loop=True, feet_y_in_frame=None):
    """Wrap an existing frame tuple (like the ghost sprite sheet) as an Animation
    anchored at bottom-center (or at feet_y_in_frame)."""
    w, h = frames[0].get_size()
    return Animation(tuple(frames), (w / 2, h if feet_y_in_frame is None else feet_y_in_frame), frame_ms, loop)
