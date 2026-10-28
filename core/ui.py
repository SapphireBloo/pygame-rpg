"""Small drawing helpers shared by the HUDs, modals, and menus."""
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
