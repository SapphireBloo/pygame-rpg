"""The results card after a battle: win, boss win, or loss.

    modal.open("VICTORY!", rewards=[Reward("candy", "candy", 7)], quote="Not bad, kid.")

The card pops in over a dimmed screen, rewards tick in one by one (candy
counts up), Whisper Jack gets the last word, and Space/Enter or a click on the
button closes it. Input is ignored for the first moment so mashing Space
through the fight can't skip the results by accident.
"""
import math
import random
from dataclasses import dataclass

import pygame

from core import sfx
from core.effects import Particles, ease_out
from core.icons import draw_icon
from core.ui import (get_font, outlined_text, draw_spooky_panel, dim_screen, draw_candy_button, wrap_text,
                     shade, WHITE, CANDY_PINK, INK)

# Handy colors
CANDY_LINE = CANDY_PINK
JACK_LINE = (190, 190, 255)

MOODS = {
    #           accent           button         embers
    "win":  ((255, 150, 40), (70, 170, 80), [(255, 170, 60), (255, 220, 120)]),
    "boss": ((190, 90, 255), (150, 70, 220), [(190, 90, 255), (255, 140, 230), (255, 220, 120)]),
    "lose": ((210, 50, 50), (170, 60, 50), [(120, 110, 110), (80, 70, 70)]),
}


@dataclass
class Reward:
    icon: str            # name in core/icons.py
    label: str           # "candy", "bombs", ...
    amount: int          # counts up from 0 (negative amounts count down)
    color: tuple = WHITE


class EndCombatModal:
    POP_MS = 280
    INPUT_DELAY_MS = 450
    ROW_DELAY_MS = 260       # time between reward rows appearing
    COUNT_MS = 600           # how long a number takes to count up

    def __init__(self, screen):
        self.screen = screen
        self.rect = pygame.Rect(0, 0, 460, 400)
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2 + 10)
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.button = pygame.Rect(0, 0, 210, 46)
        self.button.midbottom = (self.rect.centerx, self.rect.bottom - 42)
        self.visible = False
        self.title = ""
        self.subtitle = ""
        self.rewards = []
        self.quote_lines = []
        self.button_label = ""
        self.mood = "win"
        self.age = 0
        self.mouse = (-1, -1)
        self.particles = Particles()
        self._ticked = set()

    def open(self, title, rewards=(), quote=None, subtitle="", button_label="Continue", mood="win"):
        self.title = title
        self.subtitle = subtitle
        self.rewards = list(rewards)
        quote = (quote or "").removeprefix("Jack: ")
        self.quote_lines = wrap_text(get_font(17), f"“{quote}”", 300) if quote else []
        self.button_label = button_label
        self.mood = mood
        self.age = 0
        self._ticked = set()
        self.particles = Particles()
        self.visible = True
        if mood != "lose":       # a pop of candy corn as the card lands
            self.particles.candy_corn(self.rect.width // 2, 70, 26 if mood == "boss" else 16)

    @property
    def accent(self):
        return MOODS[self.mood][0]

    # ---- input / update ------------------------------------------------
    def handle_event(self, event):
        """Returns True when the player dismisses the modal."""
        if not self.visible:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.mouse = event.pos
            return False
        if self.age < self.INPUT_DELAY_MS:
            return False
        clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.button.collidepoint(event.pos)
        pressed = event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN)
        if clicked or pressed:
            sfx.play("ui_select")
            self.visible = False
            return True
        return False

    def _row_start(self, i):
        return self.POP_MS + 120 + i * self.ROW_DELAY_MS

    def update(self, dt):
        if not self.visible:
            return
        self.age += dt
        self.particles.update(dt)
        for i in range(len(self.rewards)):
            if i not in self._ticked and self.age >= self._row_start(i):
                self._ticked.add(i)
                sfx.play("ui_move")
        # Ambient embers (or falling ash when Charlie lost)
        colors = MOODS[self.mood][2]
        w, h = self.rect.size
        if random.random() < dt / 70:
            if self.mood == "lose":
                self.particles.burst(random.uniform(20, w - 20), 10, colors, 1, 30, 2600, 3,
                                     gravity=40, direction=math.pi / 2, spread=0.8)
            else:
                self.particles.burst(random.uniform(30, w - 30), h - 20, colors, 1, 50, 2200, 3,
                                     gravity=-60, direction=-math.pi / 2, spread=0.8)

    # ---- drawing -------------------------------------------------------
    def draw(self):
        if not self.visible:
            return
        t = min(1.0, self.age / self.POP_MS)
        dim_screen(self.screen, int(60 + 90 * t))

        surf = self.surface
        surf.fill((0, 0, 0, 0))
        w, h = self.rect.size
        draw_spooky_panel(surf, pygame.Rect(4, 34, w - 14, h - 44), self.accent)
        self.particles.draw(surf)
        self._draw_title(surf, w)
        y = 156 if self.subtitle else 126
        if self.subtitle:
            sub = get_font(17).render(self.subtitle, True, (205, 195, 210))
            surf.blit(sub, sub.get_rect(center=(w // 2, 116 if self.mood == "boss" else 104)))
        for i, reward in enumerate(self.rewards):
            self._draw_reward(surf, i, reward, y)
            y += 44
        self._draw_quote(surf, y + 4)
        self._draw_button(surf)

        # Pop in: scale up from 80% with a little overshoot
        if t < 1:
            k = 0.8 + 0.2 * ease_out_back(t)
            scaled = pygame.transform.smoothscale(surf, (int(w * k), int(h * k)))
            scaled.set_alpha(int(255 * min(1.0, t * 2)))
            self.screen.blit(scaled, scaled.get_rect(center=self.rect.center))
        else:
            self.screen.blit(surf, self.rect)

    def _draw_title(self, surf, w):
        # Ribbon banner across the top edge of the card
        ribbon = pygame.Rect(0, 0, w - 70, 58)
        ribbon.midtop = (w // 2, 8)
        dark = tuple(int(c * 0.45) for c in self.accent)
        top, bottom = ribbon.top + 14, ribbon.bottom + 8
        for side, edge in ((-1, ribbon.left + 10), (1, ribbon.right - 10)):   # notched tails behind the banner
            tail = [(edge, top), (edge + side * 40, top), (edge + side * 26, (top + bottom) // 2),
                    (edge + side * 40, bottom), (edge, bottom)]
            pygame.draw.polygon(surf, dark, tail)
            pygame.draw.polygon(surf, INK, tail, 3)
        pygame.draw.rect(surf, INK, ribbon.inflate(6, 6), border_radius=8)
        pygame.draw.rect(surf, tuple(int(c * 0.75) for c in self.accent), ribbon, border_radius=6)
        pygame.draw.rect(surf, tuple(min(255, int(c * 1.15) + 30) for c in self.accent),
                         (ribbon.x + 6, ribbon.y + 4, ribbon.width - 12, 6), border_radius=3)
        size = 38 if len(self.title) <= 14 else 32
        title = outlined_text(self.title.upper(), size, WHITE, True, 3)
        wobble = math.sin(self.age / 260) * 1.5 if self.mood != "lose" else 0
        surf.blit(title, title.get_rect(center=(w // 2, ribbon.centery + wobble)))
        if self.mood == "boss":
            tag = outlined_text("BOSS LOOT", 14, (255, 220, 120), True, 2)
            surf.blit(tag, tag.get_rect(center=(w // 2, ribbon.bottom + 14)))

    def _draw_reward(self, surf, i, reward, y):
        start = self._row_start(i)
        if self.age < start:
            return
        k = min(1.0, (self.age - start) / 180)
        x_shift = int(30 * (1 - ease_out(k)))
        count_k = min(1.0, (self.age - start) / self.COUNT_MS)
        shown = round(reward.amount * ease_out(count_k))
        w = self.rect.width

        row = pygame.Rect(0, 0, 300, 38)
        row.center = (w // 2 + x_shift, y)
        plate = pygame.Surface(row.size, pygame.SRCALPHA)
        pygame.draw.rect(plate, (0, 0, 0, int(110 * k)), plate.get_rect(), border_radius=10)
        surf.blit(plate, row)
        draw_icon(surf, reward.icon, (row.x + 26, row.centery), 30)
        sign = "+" if reward.amount >= 0 else "-"
        number = outlined_text(f"{sign}{abs(shown)}", 26, reward.color, True, 2)
        surf.blit(number, number.get_rect(midleft=(row.x + 52, row.centery)))
        label = get_font(18).render(reward.label, True, (215, 205, 220))
        surf.blit(label, label.get_rect(midleft=(row.x + 62 + number.get_width(), row.centery + 1)))

    def _draw_quote(self, surf, y):
        if not self.quote_lines:
            return
        appear = self._row_start(len(self.rewards)) + 100
        if self.age < appear:
            return
        alpha = int(255 * min(1.0, (self.age - appear) / 300))
        w = self.rect.width
        line_h = 20
        block_h = line_h * len(self.quote_lines)
        draw_icon(surf, "skull", (68, y + block_h // 2), 34)
        for n, line in enumerate(self.quote_lines):
            text = get_font(17).render(line, True, JACK_LINE)
            text.set_alpha(alpha)
            surf.blit(text, (96, y + n * line_h))
        name = get_font(13, bold=True).render("WHISPER JACK", True, (140, 140, 200))
        name.set_alpha(alpha)
        surf.blit(name, (w - 40 - name.get_width(), y + block_h + 2))

    def _draw_button(self, surf):
        local = self.button.move(-self.rect.x, -self.rect.y)
        ready = self.age >= self.INPUT_DELAY_MS
        hover = ready and self.button.collidepoint(self.mouse)
        pulse = (math.sin(self.age / 220) + 1) / 2 if ready else 0
        fill = shade(MOODS[self.mood][1], 0.15 * pulse)          # gentle "press me" breathing
        draw_candy_button(surf, local, self.button_label, fill, hover=hover, enabled=ready, size=22)
        hint = get_font(12).render("SPACE", True, (150, 140, 160))
        surf.blit(hint, hint.get_rect(midtop=(local.centerx, local.bottom + 6)))


def ease_out_back(t, s=1.6):
    t -= 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2
