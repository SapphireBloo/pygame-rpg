"""The rolling credits and the end-of-run summary.

  CreditsScene   scrolls core/credits.py over the camp forest. Esc, Space, Enter, or a
                 click skips it. `done` turns True when it ends.
  SummaryScene   after the ending: how the run went. Enter or a click to continue.
"""
import pygame

from core import sfx
from core.camp import ParallaxBackground
from core.credits import CREDITS
from core.difficulty import DIFFICULTY_NAMES
from core.icons import draw_icon
from core.menu_ui import PUMPKIN, ButtonMenu, CONFIRM, BACK, hint_line
from core.ui import get_font, outlined_text, draw_spooky_panel, dim_screen, GOLD, WHITE

SCROLL_SPEED = 42        # pixels per second
STYLES = {               # style: (size, color, bold, outline, height)
    "title": (40, PUMPKIN, True, 3, 64),
    "heading": (18, (170, 210, 255), True, 2, 34),
    "line": (21, WHITE, True, 2, 30),
    "small": (15, (180, 165, 190), False, 0, 24),
    "gap": (0, None, False, 0, 36),
}


def _render(style, text):
    size, color, bold, outline, height = STYLES[style]
    if style == "gap":
        return None, height
    if outline:
        return outlined_text(text, size, color, bold, outline), height
    return get_font(size, bold).render(text, True, color), height


class CreditsScene:
    def __init__(self, screen, after_ending=False):
        self.screen = screen
        self.after_ending = after_ending
        self.parallax = ParallaxBackground()
        self.lines = [_render(style, text) for style, text in CREDITS]
        self.total_h = sum(h for _, h in self.lines)
        self.scroll = 0.0
        self.time = 0
        self.done = False
        self.fade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

    def handle_event(self, event):
        skip = (event.type == pygame.KEYDOWN and event.key in BACK + CONFIRM) or \
               (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
        if skip and self.time > 300:
            sfx.play("ui_select", 0.6)
            self.done = True

    def update(self, dt):
        self.time += dt
        self.scroll += SCROLL_SPEED * dt / 1000
        if self.scroll > self.total_h + self.screen.get_height() * 0.55:
            self.done = True

    def draw(self):
        s = self.screen
        self.parallax.draw(s, self.time * 0.03)
        dim_screen(s, 120)
        h = s.get_height()
        y = h - self.scroll
        cx = s.get_width() // 2
        for surf, height in self.lines:
            if surf is not None and -60 < y < h + 60:
                alpha = 255
                if y < 110:                              # fade out near the top
                    alpha = max(0, int(255 * (y + 20) / 130))
                surf.set_alpha(alpha)
                s.blit(surf, surf.get_rect(midtop=(cx, y)))
            y += height
        if self.time < 900:                              # fade in from black
            self.fade.fill((0, 0, 0, int(255 * (1 - self.time / 900))))
            s.blit(self.fade, (0, 0))
        skip = get_font(14).render("[Esc] Skip", True, (170, 160, 180))
        s.blit(skip, skip.get_rect(bottomright=(s.get_width() - 18, h - 14)))


def _clock(ms):
    seconds = int(ms // 1000)
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


class SummaryScene:
    """How the run went, shown once after the ending credits."""

    def __init__(self, screen, player, difficulty):
        self.screen = screen
        self.player = player
        self.difficulty = difficulty
        self.parallax = ParallaxBackground()
        self.rect = pygame.Rect(0, 0, 520, 470)
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2)
        self.menu = ButtonMenu([("title", "Back to Title")], self.rect.centerx, self.rect.bottom - 64, width=220)
        self.time = 0
        self.done = False
        st = player.stats
        self.rows = [
            ("candy", "Fights won", str(player.battles_won)),
            ("skull", "Times knocked out", str(st["losses"])),
            ("chin_juice", "PERFECT hits", str(st["perfects"])),
            ("quick_hands", "Best jab combo", f"{st['best_combo']} hits"),
            ("counter", "Parries", str(st["parries"])),
            ("candy", "Candy earned", str(st["candy_earned"])),
            ("heavy_hands", "Upgrades forged", str(sum(player.upgrades.values()))),
            ("revive", "Play time", _clock(st["play_ms"])),
        ]

    def handle_event(self, event):
        if self.time < 600:
            return
        if self.menu.handle_event(event) or (event.type == pygame.KEYDOWN and event.key in BACK):
            self.done = True

    def update(self, dt):
        self.time += dt
        self.menu.update(dt)

    def draw(self):
        s = self.screen
        self.parallax.draw(s, self.time * 0.03)
        dim_screen(s, 140)
        draw_spooky_panel(s, self.rect, PUMPKIN)
        title = outlined_text("THE END... FOR NOW", 30, PUMPKIN, True, 3)
        s.blit(title, title.get_rect(midtop=(self.rect.centerx, self.rect.y + 20)))
        sub = get_font(15).render(f"Your run on {DIFFICULTY_NAMES.get(self.difficulty, 'Normal')}", True,
                                  (180, 165, 190))
        s.blit(sub, sub.get_rect(midtop=(self.rect.centerx, self.rect.y + 62)))
        y = self.rect.y + 100
        shown = min(len(self.rows), int(self.time / 140))      # rows tick in one by one
        for icon_name, label, value in self.rows[:shown]:
            draw_icon(s, icon_name, (self.rect.x + 62, y + 12), 26)
            s.blit(get_font(18).render(label, True, (215, 205, 220)), (self.rect.x + 90, y + 2))
            val = outlined_text(value, 20, GOLD, True, 2)
            s.blit(val, val.get_rect(topright=(self.rect.right - 50, y)))
            y += 36
        if shown == len(self.rows):
            self.menu.draw(s)
        hint_line(s, "Enter to continue", self.rect.bottom + 22)
