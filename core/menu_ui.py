"""Shared pieces for the title screen, pause menu, and other full-screen menus.

  ButtonMenu     a column of candy buttons: arrows/W/S + Enter/Space, or the mouse
  ConfirmDialog  a small "are you sure?" box with two buttons
"""
import math

import pygame

from core import sfx
from core.icons import draw_icon
from core.ui import get_font, outlined_text, draw_candy_button, draw_spooky_panel, dim_screen, wrap_text

PUMPKIN = (255, 140, 40)
BUTTON_FILL = (150, 70, 30)
NAV_UP = (pygame.K_UP, pygame.K_w)
NAV_DOWN = (pygame.K_DOWN, pygame.K_s)
CONFIRM = (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)
BACK = (pygame.K_ESCAPE, pygame.K_BACKSPACE)


class ButtonMenu:
    """items: list of (key, label) or (key, label, enabled). handle_event returns the key
    of the button that was chosen, or None."""

    def __init__(self, items, center_x, top, width=250, height=44, gap=12, fill=BUTTON_FILL, size=20):
        self.center_x, self.top = center_x, top
        self.width, self.height, self.gap = width, height, gap
        self.fill, self.size = fill, size
        self.time = 0
        self.press = {}
        self.set_items(items)

    def set_items(self, items):
        self.items = [(it[0], it[1], it[2] if len(it) > 2 else True) for it in items]
        self.index = next((i for i, it in enumerate(self.items) if it[2]), 0)

    def rect(self, i):
        r = pygame.Rect(0, 0, self.width, self.height)
        r.midtop = (self.center_x, self.top + i * (self.height + self.gap))
        return r

    def _at(self, pos):
        for i in range(len(self.items)):
            if self.rect(i).collidepoint(pos):
                return i
        return None

    def _step(self, direction):
        for _ in range(len(self.items)):
            self.index = (self.index + direction) % len(self.items)
            if self.items[self.index][2]:
                break
        sfx.play("ui_move", 0.5)

    def _choose(self, i):
        key, _, enabled = self.items[i]
        if not enabled:
            sfx.play("ui_error", 0.6)
            return None
        sfx.play("ui_select", 0.7)
        self.press[i] = 160
        return key

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in NAV_UP:
                self._step(-1)
            elif event.key in NAV_DOWN:
                self._step(1)
            elif event.key in CONFIRM:
                return self._choose(self.index)
        elif event.type == pygame.MOUSEMOTION:
            i = self._at(event.pos)
            if i is not None and i != self.index and self.items[i][2]:
                self.index = i
                sfx.play("ui_move", 0.4)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            i = self._at(event.pos)
            if i is not None:
                self.index = i
                return self._choose(i)
        return None

    def update(self, dt):
        self.time += dt
        for i in list(self.press):
            self.press[i] -= dt
            if self.press[i] <= 0:
                del self.press[i]

    def draw(self, screen):
        for i, (key, label, enabled) in enumerate(self.items):
            r = self.rect(i)
            selected = i == self.index
            draw_candy_button(screen, r, label, self.fill, hover=selected, enabled=enabled, size=self.size,
                              press=1.0 if i in self.press else 0.0)
            if selected and enabled:          # a little bobbing candy corn points at the choice
                bob = 4 * math.sin(self.time / 160)
                draw_icon(screen, "candy", (r.left - 24 + bob, r.centery), 26)


class ConfirmDialog:
    """A yes/no question over whatever is behind it. handle_event returns "yes", "no", or None."""

    def __init__(self, screen, title, message, yes="Yes", no="Cancel", accent=PUMPKIN):
        self.screen = screen
        self.title, self.accent = title, accent
        self.rect = pygame.Rect(0, 0, 460, 230)
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2)
        self.lines = wrap_text(get_font(17), message, self.rect.width - 60)
        y = self.rect.bottom - 64
        self.menu = ButtonMenu([("yes", yes), ("no", no)], self.rect.centerx, y, width=150, height=42)
        # side by side instead of stacked
        self.menu.rect = self._button_rect
        self.menu.index = 1                   # default to the safe choice

    def _button_rect(self, i):
        r = pygame.Rect(0, 0, 150, 42)
        r.center = (self.rect.centerx + (-90 if i == 0 else 90), self.rect.bottom - 44)
        return r

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in BACK:
            sfx.play("ui_move", 0.5)
            return "no"
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            self.menu._step(1)
            return None
        return self.menu.handle_event(event)

    def update(self, dt):
        self.menu.update(dt)

    def draw(self):
        dim_screen(self.screen, 160)
        draw_spooky_panel(self.screen, self.rect, self.accent)
        title = outlined_text(self.title, 26, self.accent, True, 2)
        self.screen.blit(title, title.get_rect(midtop=(self.rect.centerx, self.rect.y + 20)))
        for n, line in enumerate(self.lines):
            text = get_font(17).render(line, True, (215, 205, 220))
            self.screen.blit(text, text.get_rect(midtop=(self.rect.centerx, self.rect.y + 66 + n * 22)))
        for i, (key, label, enabled) in enumerate(self.menu.items):
            draw_candy_button(self.screen, self._button_rect(i), label, BUTTON_FILL, hover=i == self.menu.index,
                              size=18, press=1.0 if i in self.menu.press else 0.0)


def draw_title_text(screen, text, size, center, color=PUMPKIN, outline=3):
    surf = outlined_text(text, size, color, True, outline)
    screen.blit(surf, surf.get_rect(center=center))
    return surf


def hint_line(screen, text, y, color=(150, 135, 160)):
    surf = get_font(14).render(text, True, color)
    screen.blit(surf, surf.get_rect(center=(screen.get_width() // 2, y)))

