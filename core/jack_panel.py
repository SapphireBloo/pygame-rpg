"""Whisper Jack's narration panel: a dark box near the top of the screen with a small, animated
Jack in the corner and his line next to him. Every chapter, the camp, and the first fight use it
(JackPanel, below); the Void draws the same panel for his walk-and-talk (scenes/void_walk.py).

JackPanel works like a little cutscene: Space (or a click) moves to his next line, Charlie can't
move until the last real line has been read, then a farewell quip stays up until Space (or until
Charlie walks off) and the panel fades away.
"""
import random
from functools import lru_cache

import pygame

from core.assets import load_frames
from core.skeleton_animation import FAREWELL_LINES
from core.ui import get_font, outlined_text, wrap_text

PANEL_W = 600
PANEL_TOP = 92               # just under the HUD
PANEL_SHIFT = 60             # nudged right of center, clear of Charlie's HUD
PORTRAIT_H = 84
FRAME_MS = 220               # his portrait's animation speed
FADE_MS = 250
BORDER = (180, 120, 255)
NAME_COLOR = (200, 170, 255)
TEXT_COLOR = (245, 238, 255)
HINT_COLOR = (170, 150, 200)


@lru_cache(maxsize=None)
def jack_portrait():
    """Whisper Jack's frames, cropped to him and shrunk down for the panel."""
    frames = load_frames("Skeleton")
    if not frames:
        return ()
    box = frames[0].get_bounding_rect()
    for f in frames[1:]:
        box.union_ip(f.get_bounding_rect())
    scale = PORTRAIT_H / box.height
    size = (max(1, round(box.width * scale)), PORTRAIT_H)
    return tuple(pygame.transform.smoothscale(f.subsurface(box), size) for f in frames)


def panel_rect(screen, text):
    lines = wrap_text(get_font(18, True), text, PANEL_W - 130)
    rect = pygame.Rect(0, 0, PANEL_W, max(PORTRAIT_H + 12, 44 + 24 * len(lines)))
    rect.midtop = (screen.get_width() // 2 + PANEL_SHIFT, PANEL_TOP)
    return rect, lines


def draw_jack_panel(screen, text, alpha, time, hint="[Space] next", hint_bright=False, shiver=False):
    """Draw the panel with one of Jack's lines. alpha 0-1 fades it; shiver makes him tremble (the Void)."""
    rect, lines = panel_rect(screen, text)
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (14, 8, 24, int(215 * alpha)), panel.get_rect(), border_radius=12)
    pygame.draw.rect(panel, (*BORDER, int(200 * alpha)), panel.get_rect(), 2, border_radius=12)
    screen.blit(panel, rect)
    frames = jack_portrait()
    if frames:
        jack = frames[int(time // FRAME_MS) % len(frames)].copy()
        dx = dy = 0
        if shiver and int(time // 70) % 3 == 0:
            dx, dy = random.choice((-1, 0, 0, 1)), random.choice((-1, 0, 0, 1))
        jack.set_alpha(int(255 * min(1.0, alpha + 0.2)))
        screen.blit(jack, jack.get_rect(midbottom=(rect.x + 52 + dx, rect.bottom - 4 + dy)))
    fade = int(255 * alpha)
    name = outlined_text("WHISPER JACK", 13, NAME_COLOR, True, 2)
    if fade < 255:
        name = name.copy()
        name.set_alpha(fade)
    screen.blit(name, (rect.x + 100, rect.y + 10))
    y = rect.y + 30
    for line in lines:
        surf = outlined_text(line, 18, TEXT_COLOR, True, 2)
        if fade < 255:
            surf = surf.copy()
            surf.set_alpha(fade)
        screen.blit(surf, (rect.x + 100, y))
        y += 24
    if hint:
        label = get_font(12, hint_bright).render(hint, True, (225, 200, 255) if hint_bright else HINT_COLOR)
        label.set_alpha(fade)
        screen.blit(label, label.get_rect(bottomright=(rect.right - 10, rect.bottom - 6)))
    return rect


class JackPanel:
    """Whisper Jack talking, in the panel. Same handles as the old rise-out-of-the-ground Jack:
    handle_event / update / draw, and active, message_done, fading_out, x."""

    def __init__(self, messages, x=0):
        self.x = x                       # where Charlie was when Jack started (walk far enough and he leaves)
        self.messages = list(messages) + [random.choice(FAREWELL_LINES)]
        self.message_index = 0
        self.message_done = len(self.messages) == 1      # (no scripted lines: straight to the farewell)
        self.active = True
        self.fading_out = False
        self.alpha = 0.0
        self.time = 0
        self.line_age = 0

    def handle_event(self, event):
        if not self.active or self.fading_out:
            return
        advance = (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or \
                  (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
        if not advance:
            return
        if self.message_done:
            self.fading_out = True
        else:
            self.message_index += 1
            self.line_age = 0
            if self.message_index == len(self.messages) - 1:
                self.message_done = True               # now showing the farewell line

    def update(self, dt):
        if not self.active:
            return
        self.time += dt
        self.line_age += dt
        if self.fading_out:
            self.alpha -= dt / FADE_MS
            if self.alpha <= 0:
                self.active = False
        else:
            self.alpha = min(1.0, self.alpha + dt / FADE_MS)

    def draw(self, screen, camera_offset=0):
        if not self.active or self.alpha <= 0:
            return
        text = self.messages[min(self.message_index, len(self.messages) - 1)]
        hint = "[Space] close" if self.message_done else "[Space] next"
        draw_jack_panel(screen, text, max(0.0, self.alpha), self.time, hint)
