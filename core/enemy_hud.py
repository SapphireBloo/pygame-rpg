from core.ui import draw_bar, get_font, WHITE


class EnemyHUD:
    """Top-right enemy name and HP bar."""

    def __init__(self, screen, enemy, x=450, y=5, bar_width=300):
        self.screen = screen
        self.enemy = enemy
        self.font = get_font(22)
        self.x, self.y = x, y
        self.bar_width = bar_width
        self.shown_hp = float(enemy.hp)

    def update(self, dt):
        self.shown_hp += (self.enemy.hp - self.shown_hp) * min(1.0, dt / 100)

    def draw(self):
        e, x, y = self.enemy, self.x, self.y
        self.screen.blit(self.font.render(e.name, True, (255, 100, 100)), (x, y))
        draw_bar(self.screen, x, y + 25, self.bar_width, 20, self.shown_hp, e.max_hp, (200, 0, 0))
        self.screen.blit(self.font.render(f"HP: {e.hp}/{e.max_hp}", True, WHITE), (x, y + 50))
