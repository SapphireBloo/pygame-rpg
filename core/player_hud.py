# player_hud.py
import pygame

class PlayerHUD:
    def __init__(self, screen, font, player):
        self.screen = screen
        self.font = font
        self.player = player

        self.bar_pos = (50, 30)
        self.bar_width = 300
        self.bar_height = 20

        self.name_pos = (50, 5)
        self.hp_pos = (50, 55)
        self.inventory_pos = (50, 105)
        self.upgrades_pos = (50, 135)

    def draw_bar(self, x, y, width, height, value, max_value, color):
        pygame.draw.rect(self.screen, (60, 60, 60), (x, y, width, height))
        fill = int(width * (value / max_value)) if max_value > 0 else 0
        pygame.draw.rect(self.screen, color, (x, y, fill, height))
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, width, height), 2)

    def draw(self):
        self.draw_bar(*self.bar_pos, self.bar_width, self.bar_height, self.player.hp, self.player.max_hp, (0, 200, 0))
        self.screen.blit(self.font.render(f"{self.player.name} - Lv {self.player.level}", True, (255, 255, 255)), self.name_pos)
        self.screen.blit(self.font.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, (255, 255, 255)), self.hp_pos)

        inventory_text = f"Bombs: {self.player.inventory.get('bomb', 0)}  Candy: {self.player.candy}"
        self.screen.blit(self.font.render(inventory_text, True, (200, 200, 200)), self.inventory_pos)

        # Display upgrades if active
        active_upgrades = []
        if getattr(self.player, 'auto_block', False):
            active_upgrades.append("Auto-Block")
        if getattr(self.player, 'heal_boost', False):
            active_upgrades.append("Heal+")
        if getattr(self.player, 'resurrect_once', False):
            active_upgrades.append("Revive")
        if getattr(self.player, 'bomb_power_plus_10', False):
            active_upgrades.append("Bomb++")
        if getattr(self.player, 'double_candy', False):
            active_upgrades.append("Double Candy")

        if active_upgrades:
            upgrades_text = "Upgrades: " + ", ".join(active_upgrades)
            self.screen.blit(self.font.render(upgrades_text, True, (255, 215, 100)), self.upgrades_pos)
