# enemy_hud.py
import pygame

class EnemyHUD:
    def __init__(self, screen, font, enemy):
        self.screen = screen
        self.font = font
        self.enemy = enemy

        self.bar_pos = (450, 30)
        self.bar_width = 300
        self.bar_height = 20

        self.name_pos = (450, 5)
        self.hp_pos = (450, 55)

    def draw_bar(self, x, y, width, height, value, max_value, color):
        pygame.draw.rect(self.screen, (60, 60, 60), (x, y, width, height))
        fill = int(width * (value / max_value)) if max_value > 0 else 0
        pygame.draw.rect(self.screen, color, (x, y, fill, height))
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, width, height), 2)

    def draw(self):
        self.draw_bar(*self.bar_pos, self.bar_width, self.bar_height, self.enemy.hp, self.enemy.max_hp, (200, 0, 0))
        self.screen.blit(self.font.render(self.enemy.name, True, (255, 100, 100)), self.name_pos)
        self.screen.blit(self.font.render(f"HP: {self.enemy.hp}/{self.enemy.max_hp}", True, (255, 255, 255)), self.hp_pos)
