import math

import pygame

from core.ui import draw_bar, get_font, WHITE, GREY
from core.upgrades import UPGRADES


class PlayerHUD:
    """Top-left HP bar, Chin meter, status, bombs/candy, and owned upgrades."""

    def __init__(self, screen, player, x=50, y=5, bar_width=300):
        self.screen = screen
        self.player = player
        self.font = get_font(22)
        self.small = get_font(14, bold=True)
        self.x, self.y = x, y
        self.bar_width = bar_width
        self.shown_hp = float(player.hp)  # eases toward real HP so the bar slides
        self.shown_meter = float(player.chin_meter)
        self.time = 0

    def update(self, dt):
        self.time += dt
        k = min(1.0, dt / 100)
        self.shown_hp += (self.player.hp - self.shown_hp) * k
        self.shown_meter += (self.player.chin_meter - self.shown_meter) * k

    def draw(self):
        p, x, y = self.player, self.x, self.y
        render = self.font.render

        name = f"{p.name} - Lv {p.level}"
        self.screen.blit(render(name, True, WHITE), (x, y))
        tag_x = x + self.font.size(name)[0] + 12
        for turns, label, color in ((p.infected, "INFECTED", (140, 230, 90)), (p.burning, "BURNING", (255, 150, 50))):
            if turns:
                tag = self.small.render(f"{label} ({turns})", True, color)
                self.screen.blit(tag, (tag_x, y + 5))
                tag_x += tag.get_width() + 10

        hp_color = (230, 130, 40) if p.burning else (110, 190, 60) if p.infected else (0, 200, 0)
        draw_bar(self.screen, x, y + 25, self.bar_width, 20, self.shown_hp, p.max_hp, hp_color)
        self.screen.blit(render(f"HP: {p.hp}/{p.max_hp}", True, WHITE), (x, y + 50))

        # Chin meter: thin gold bar, pulses when the finisher is ready
        mx, my, mw = x + 150, y + 56, self.bar_width - 150
        pygame.draw.rect(self.screen, (40, 35, 25), (mx, my, mw, 12))
        fill = int(mw * max(0.0, min(1.0, self.shown_meter / p.CHIN_METER_MAX)))
        color = (255, 200, 40)
        if p.chin_ready:
            pulse = 0.5 + 0.5 * math.sin(self.time / 120)
            color = (255, int(140 + 100 * pulse), 40)
        pygame.draw.rect(self.screen, color, (mx, my, fill, 12))
        pygame.draw.rect(self.screen, (230, 220, 200), (mx, my, mw, 12), 1)
        label = "CHIN CHECK READY!" if p.chin_ready else "CHIN"
        self.screen.blit(self.small.render(label, True, color), (mx, my + 14))

        self.screen.blit(render(f"Bombs: {p.inventory.get('bomb', 0)}  Candy: {p.candy}", True, GREY),
                         (x, y + 100))
        owned = [u["short"] for u in UPGRADES if p.has(u["key"])]
        if owned:
            self.screen.blit(render("Upgrades: " + ", ".join(owned), True, (255, 215, 100)), (x, y + 130))
