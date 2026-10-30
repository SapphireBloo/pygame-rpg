import math

import pygame

from core.player_hud import draw_plate, draw_tag
from core.ui import HealthBar, outlined_text, INK, WHITE

ENEMY_RED = (215, 50, 45)
BOSS_PURPLE = (150, 70, 230)
ENRAGED_PINK = (215, 45, 165)
TRAIL = (235, 200, 160)          # what it just lost (pale, so it shows against the red and purple)


class EnemyHUD:
    """Top-right: the enemy's name, HP bar, and tags (BOSS / ENRAGED, DAZED), mirroring Charlie's."""

    WIDTH = 344

    def __init__(self, screen, enemy, y=8):
        self.screen = screen
        self.enemy = enemy
        self.x = screen.get_width() - self.WIDTH - 16
        self.y = y
        self.hp = HealthBar(enemy.hp)
        self.time = 0

    @property
    def shown_hp(self):
        return self.hp.shown

    def update(self, dt):
        self.time += dt
        self.hp.update(self.enemy.hp, dt)

    def draw(self):
        e, s, x, y = self.enemy, self.screen, self.x, self.y
        boss = getattr(e, "boss", False)
        draw_plate(s, pygame.Rect(x, y, self.WIDTH, 84 if boss or e.daze else 62))

        name_color = (215, 160, 255) if boss else (255, 120, 105)
        name = outlined_text(e.name, 17, name_color, True, 2)
        s.blit(name, name.get_rect(topright=(x + self.WIDTH - 12, y + 6)))

        color = BOSS_PURPLE if boss else ENEMY_RED
        if boss and e.enraged:
            color = ENRAGED_PINK
        bar = pygame.Rect(x + 14, y + 32, self.WIDTH - 28, 20)
        self.hp.draw(s, bar, e.max_hp, color, text=f"{e.hp} / {e.max_hp}", right_to_left=True,
                     trail_color=TRAIL)
        if boss and not e.enraged and e.is_alive:          # where it'll enrage (half HP)
            mid = bar.centerx
            pygame.draw.line(s, INK, (mid, bar.y - 4), (mid, bar.bottom + 3), 4)
            pygame.draw.line(s, WHITE, (mid, bar.y - 3), (mid, bar.bottom + 2), 2)

        tag_x = x + self.WIDTH - 14                        # tags under the bar, from the right
        if boss:
            if e.enraged:
                pulse = 0.6 + 0.4 * math.sin(self.time / 130)
                tag = draw_tag(s, "ENRAGED", (255, int(110 * pulse) + 60, 255), (tag_x, y + 70), "midright")
            else:
                tag = draw_tag(s, "BOSS", (200, 160, 255), (tag_x, y + 70), "midright")
            tag_x = tag.left - 6
        if getattr(e, "daze", 0) and e.is_alive:          # Daze stacks from jabs: cash them in with a Haymaker
            draw_tag(s, f"DAZED x{e.daze}", (255, 225, 90), (tag_x, y + 70), "midright")
