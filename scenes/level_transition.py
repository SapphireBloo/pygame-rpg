"""Cinematic transition between levels.

  1. Fade the last frame of the old level to black
  2. Show a chapter title card (auto-advances; Space skips)
  3. Load the new level behind the black
  4. Fade in on the new level (Whisper Jack is already rising to greet you)

main.py runs this like any other scene until `done` is True.
"""
from collections import defaultdict

import pygame

from core.levels import LEVELS, ENDING
from core.ui import get_font, blit_centered

FADE_MS = 700
CARD_TEXT_FADE_MS = 500
CARD_HOLD_MS = 2600
MIN_CARD_MS = 400          # ignore Space for a moment so a held key doesn't skip the card

FADE_OUT, CARD, CARD_OUT, FADE_IN = "fade_out", "card", "card_out", "fade_in"
NO_KEYS = defaultdict(bool)  # stands in for the keyboard so the hero stays still while fading in


def _radial_glow(color, radius=320):
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -8):
        alpha = int(70 * (1 - r / radius) ** 2)
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    return surf


class LevelTransition:
    def __init__(self, screen, exploration, title, subtitle, accent, kicker="",
                 on_load=None, snapshot=None, auto_advance=True):
        self.screen = screen
        self.exploration = exploration
        self.title, self.subtitle, self.kicker = title, subtitle, kicker
        self.on_load = on_load
        self.snapshot = snapshot
        self.auto_advance = auto_advance
        self.glow = _radial_glow(accent)
        self.accent = accent
        self.black = pygame.Surface(screen.get_size())
        self.black.fill((0, 0, 0))

        self.title_font = get_font(52, bold=True)
        self.sub_font = get_font(22)
        self.kicker_font = get_font(20, bold=True)
        self.hint_font = get_font(16)

        self.phase = FADE_OUT if snapshot else CARD
        self.timer = 0
        self.done = False

    # ---- flow ----------------------------------------------------------
    def _go(self, phase):
        self.phase = phase
        self.timer = 0
        if phase == FADE_IN and self.on_load:
            self.on_load()
            self.on_load = None

    def handle_event(self, event):
        pressed = event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN)
        if pressed and self.phase == CARD and self.timer >= MIN_CARD_MS:
            self._go(CARD_OUT)

    def update(self, dt):
        self.timer += dt
        if self.phase == FADE_OUT and self.timer >= FADE_MS:
            self._go(CARD)
        elif self.phase == CARD and self.auto_advance and self.timer >= CARD_HOLD_MS:
            self._go(CARD_OUT)
        elif self.phase == CARD_OUT and self.timer >= CARD_TEXT_FADE_MS:
            self._go(FADE_IN)
        elif self.phase == FADE_IN:
            self.exploration.update(NO_KEYS, dt)
            if self.timer >= FADE_MS:
                self.done = True

    # ---- drawing -------------------------------------------------------
    def draw(self):
        if self.phase == FADE_OUT:
            self.screen.blit(self.snapshot, (0, 0))
            self._overlay(self.timer / FADE_MS)
        elif self.phase in (CARD, CARD_OUT):
            self.screen.fill((0, 0, 0))
            if self.phase == CARD:
                alpha = min(1.0, self.timer / CARD_TEXT_FADE_MS)
            else:
                alpha = max(0.0, 1 - self.timer / CARD_TEXT_FADE_MS)
            self._draw_card(alpha)
        elif self.phase == FADE_IN:
            self.exploration.draw()
            self._overlay(1 - self.timer / FADE_MS)

    def _overlay(self, amount):
        self.black.set_alpha(int(255 * max(0.0, min(1.0, amount))))
        self.screen.blit(self.black, (0, 0))

    def _draw_card(self, alpha):
        a = int(255 * alpha)
        cx, cy = self.screen.get_width() // 2, self.screen.get_height() // 2

        self.glow.set_alpha(a)
        self.screen.blit(self.glow, self.glow.get_rect(center=(cx, cy)))

        pieces = []
        if self.kicker:
            pieces.append((self.kicker_font.render(self.kicker, True, self.accent), cy - 70))
        pieces.append((self.title_font.render(self.title, True, (245, 240, 230)), cy - 15))
        pieces.append((self.sub_font.render(self.subtitle, True, (190, 190, 200)), cy + 40))
        hint = "[Space]" if self.auto_advance else "[Press Space]"
        pieces.append((self.hint_font.render(hint, True, (110, 110, 120)), cy + 200))

        line_w = 260
        line = pygame.Surface((line_w, 2), pygame.SRCALPHA)
        line.fill((*self.accent, 255))
        line.set_alpha(a)
        self.screen.blit(line, (cx - line_w // 2, cy + 18))

        for surf, y in pieces:
            surf.set_alpha(a)
            blit_centered(self.screen, surf, (cx, y))


# ---- factories used by main.py -----------------------------------------
def chapter_card(screen, exploration, index, snapshot=None):
    """Title card for LEVELS[index]; loads that level behind the black."""
    level = LEVELS[index]
    on_load = None if index == exploration.level_index else (lambda: exploration.load_level(index))
    return LevelTransition(screen, exploration, level["name"], level["subtitle"], level["accent"],
                           kicker=f"CHAPTER {index + 1}", on_load=on_load, snapshot=snapshot)


def next_transition(screen, exploration):
    """Whatever comes after the current level: the next chapter, or the ending."""
    snapshot = screen.copy()
    if not exploration.is_last_level:
        return chapter_card(screen, exploration, exploration.level_index + 1, snapshot)
    return LevelTransition(screen, exploration, ENDING["title"], ENDING["subtitle"],
                           exploration.level["accent"], on_load=exploration.finish,
                           snapshot=snapshot, auto_advance=False)
