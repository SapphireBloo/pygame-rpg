"""The title screen: the camp forest drifting by, Charlie and Whisper Jack, and the main menu.

handle_event returns "new", "continue", "settings", "controls", "cheats", "credits", "quit", or None.
"""
import math

import pygame

from core.animation import AnimatedSprite, load_gameart2d_character
from core.assets import load_frames
from core.camp import ParallaxBackground
from core.menu_ui import ButtonMenu, PUMPKIN, hint_line
from core.settings import FEET_Y, HERO_HEIGHT, CHARACTER_INK
from core.ui import get_font, outlined_text, dim_screen

VERSION = "Playtest demo v0.2"     # bump this for each build you send out


def _glow(color, w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(12, 0, -1):
        k = i / 12
        rect = pygame.Rect(0, 0, int(w * k), int(h * k))
        rect.center = (w // 2, h // 2)
        pygame.draw.ellipse(surf, (*color, int(16 * (1 - k) + 4)), rect)
    return surf


class TitleScreen:
    def __init__(self, screen, save_info=None):
        """save_info: a short label for Continue (e.g. "Camp after Chapter 2"), or None if no save."""
        self.screen = screen
        self.parallax = ParallaxBackground()
        self.hero = AnimatedSprite(load_gameart2d_character("charlie", HERO_HEIGHT, ink=CHARACTER_INK))
        self.jack_frames = load_frames("Skeleton", flip_x=True)
        self.glow = _glow(PUMPKIN, 620, 200)
        self.time = 0
        self.save_info = None
        self.menu = ButtonMenu([], screen.get_width() // 2, 232, width=250, height=38, gap=9)
        self.set_save(save_info)

    def set_save(self, save_info):
        self.save_info = save_info
        self.menu.set_items([
            ("continue", "Continue", bool(save_info)),
            ("new", "New Game"),
            ("settings", "Settings"),
            ("controls", "Controls"),
            ("cheats", "Cheats"),
            ("credits", "Credits"),
            ("quit", "Quit"),
        ])

    def handle_event(self, event):
        return self.menu.handle_event(event)

    def update(self, dt):
        self.time += dt
        self.hero.update(dt)
        self.menu.update(dt)

    def draw(self):
        s = self.screen
        w = s.get_width()
        self.parallax.draw(s, self.time * 0.04)
        dim_screen(s, 70)

        # Charlie on the left, Whisper Jack bobbing on the right
        self.hero.draw(s, 150, FEET_Y, True)
        frame = self.jack_frames[int(self.time / 250) % len(self.jack_frames)]
        bob = 8 * math.sin(self.time / 520)
        s.blit(frame, frame.get_rect(midbottom=(w - 140, FEET_Y - 30 + bob)))

        # Title
        pulse = 0.85 + 0.15 * math.sin(self.time / 700)
        self.glow.set_alpha(int(255 * pulse))
        s.blit(self.glow, self.glow.get_rect(center=(w // 2, 120)))
        for text, size, y in (("CHIN CHECK", 58, 92), ("CHARLIE", 70, 158)):
            shadow = outlined_text(text, size, (60, 20, 10), True, 3)
            s.blit(shadow, shadow.get_rect(center=(w // 2 + 4, y + 5)))
            title = outlined_text(text, size, PUMPKIN, True, 4)
            s.blit(title, title.get_rect(center=(w // 2, y)))
        tag = get_font(15, bold=True).render("A HALLOWEEN BRAWL", True, (230, 200, 160))
        s.blit(tag, tag.get_rect(center=(w // 2, 208)))

        self.menu.draw(s)
        if self.save_info:
            note = get_font(13).render(self.save_info, True, (200, 185, 160))
            r = self.menu.rect(0)
            s.blit(note, note.get_rect(midleft=(r.right + 14, r.centery)))
        hint_line(s, "Arrows + Enter, or the mouse   |   M mutes music", s.get_height() - 18, (170, 155, 175))
        ver = get_font(12).render(VERSION, True, (130, 120, 140))
        s.blit(ver, ver.get_rect(bottomright=(w - 10, s.get_height() - 8)))
