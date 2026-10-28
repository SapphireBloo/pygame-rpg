import math

from core.ui import draw_bar, get_font, WHITE


class EnemyHUD:
    """Top-right enemy name and HP bar (purple, with a BOSS tag, for bosses)."""

    def __init__(self, screen, enemy, x=450, y=5, bar_width=300):
        self.screen = screen
        self.enemy = enemy
        self.font = get_font(22)
        self.tag_font = get_font(14, bold=True)
        self.x, self.y = x, y
        self.bar_width = bar_width
        self.shown_hp = float(enemy.hp)
        self.time = 0

    def update(self, dt):
        self.time += dt
        self.shown_hp += (self.enemy.hp - self.shown_hp) * min(1.0, dt / 100)

    def draw(self):
        e, x, y = self.enemy, self.x, self.y
        boss = getattr(e, "boss", False)
        name_color = (215, 150, 255) if boss else (255, 100, 100)
        name = self.font.render(e.name, True, name_color)
        self.screen.blit(name, (x, y))
        if boss:
            label = "ENRAGED" if e.enraged else "BOSS"
            pulse = 0.6 + 0.4 * math.sin(self.time / 130) if e.enraged else 1.0
            tag = self.tag_font.render(label, True, (255, int(110 * pulse) + 60, 255) if e.enraged else (200, 160, 255))
            self.screen.blit(tag, (x + self.bar_width - tag.get_width(), y + 54))   # under the bar, right side
        bar_color = (150, 60, 220) if boss else (200, 0, 0)
        if boss and e.enraged:
            bar_color = (200, 40, 160)
        draw_bar(self.screen, x, y + 25, self.bar_width, 20, self.shown_hp, e.max_hp, bar_color)
        if boss:   # half-HP marker shows when it'll enrage
            mid = x + self.bar_width // 2
            self.screen.fill((255, 255, 255), (mid, y + 25, 2, 20))
        self.screen.blit(self.font.render(f"HP: {e.hp}/{e.max_hp}", True, WHITE), (x, y + 50))
