import math

import pygame

from core.ui import HealthBar, get_font, outlined_text, shade, INK, GOLD, WHITE

PLATE = (12, 9, 16, 165)        # the dark plate behind the HUD
HP_COLOR = (70, 200, 80)
BURNING_COLOR = (240, 130, 40)
INFECTED_COLOR = (150, 200, 60)
LOW_HP = 0.25                   # below this share of HP the frame pulses red
STATUSES = (("infected", "INFECTED", (140, 230, 90)), ("burning", "BURNING", (255, 150, 50)),
            ("blessing", "WELL-FED", (255, 210, 120)))


def draw_plate(screen, rect):
    plate = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(plate, PLATE, plate.get_rect(), border_radius=12)
    pygame.draw.rect(plate, (90, 70, 100, 120), plate.get_rect(), 1, border_radius=12)
    screen.blit(plate, rect)


def draw_tag(screen, text, color, pos, anchor="midleft"):
    """A little rounded label (status effects, BOSS, DAZED...). Returns its rect."""
    label = outlined_text(text, 12, color, True, 1)
    rect = label.get_rect().inflate(12, 4)
    setattr(rect, anchor, pos)
    pygame.draw.rect(screen, INK, rect, border_radius=8)
    pygame.draw.rect(screen, shade(color, -0.45), rect, 1, border_radius=8)
    screen.blit(label, label.get_rect(center=rect.center))
    return rect


class PlayerHUD:
    """Top-left: Charlie's name and level, status effects, HP bar, and Chin meter, on a dark plate.
    (Candy, items, and upgrades are in the bag.)"""

    WIDTH = 344

    def __init__(self, screen, player, x=16, y=8):
        self.screen = screen
        self.player = player
        self.x, self.y = x, y
        self.hp = HealthBar(player.hp)
        self.shown_meter = float(player.chin_meter)
        self.time = 0

    @property
    def shown_hp(self):
        return self.hp.shown

    def update(self, dt):
        self.time += dt
        self.hp.update(self.player.hp, dt)
        self.shown_meter += (self.player.chin_meter - self.shown_meter) * min(1.0, dt / 100)

    def draw(self):
        p, s, x, y = self.player, self.screen, self.x, self.y
        draw_plate(s, pygame.Rect(x, y, self.WIDTH, 84))

        name = outlined_text(p.name.upper(), 17, GOLD, True, 2)
        s.blit(name, (x + 12, y + 6))
        level = outlined_text(f"LV {p.level}", 13, (210, 200, 220), True, 2)
        s.blit(level, (x + 18 + name.get_width(), y + 10))
        tag_x = x + 26 + name.get_width() + level.get_width()
        for attr, label, color in STATUSES:
            if getattr(p, attr):   # ailments last until a Remedy or Elixir; WELL-FED (a blessing) until the next camp
                tag_x = draw_tag(s, label, color, (tag_x, y + 16)).right + 6

        color = BURNING_COLOR if p.burning else INFECTED_COLOR if p.infected else HP_COLOR
        low = p.hp > 0 and p.hp / max(1, p.max_hp) < LOW_HP
        pulse = 0.5 + 0.5 * math.sin(self.time / 140) if low else 0.0
        self.hp.draw(s, (x + 14, y + 32, self.WIDTH - 28, 20), p.max_hp, color,
                     text=f"{p.hp} / {p.max_hp}", low_pulse=pulse)

        # Chin meter: a slim gold bar that pulses when the finisher is ready
        ready = p.chin_ready
        glow = 0.5 + 0.5 * math.sin(self.time / 120)
        gold = (255, int(150 + 90 * glow), 40) if ready else (255, 200, 40)
        label = outlined_text("CHIN", 12, gold, True, 2)
        s.blit(label, (x + 12, y + 61))
        bar = pygame.Rect(x + 56, y + 63, self.WIDTH - 70, 9)
        pygame.draw.rect(s, INK, bar.inflate(4, 4), border_radius=5)
        pygame.draw.rect(s, (40, 32, 24), bar, border_radius=4)
        fill = bar.copy()
        fill.width = int(bar.width * max(0.0, min(1.0, self.shown_meter / p.CHIN_METER_MAX)))
        if fill.width:
            pygame.draw.rect(s, shade(gold, -0.2), fill, border_radius=4)
            shine = fill.inflate(-2, 0)
            shine.height = 3
            shine.y = bar.y + 1
            pygame.draw.rect(s, shade(gold, 0.5), shine, border_radius=2)
        if ready:
            text = outlined_text("CHIN CHECK READY!", 12, gold, True, 2)
            s.blit(text, text.get_rect(midright=(bar.right, y + 16)))
