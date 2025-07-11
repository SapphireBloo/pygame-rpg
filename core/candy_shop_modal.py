import pygame

class CandyShopModal:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.font = pygame.font.SysFont("consolas", 20)
        self.title_font = pygame.font.SysFont("consolas", 28, bold=True)
        self.visible = False
        self.scroll_offset = 0
        self.scroll_speed = 20
        self.modal_rect = pygame.Rect(150, 80, 500, 440)
        self.close_button = pygame.Rect(self.modal_rect.right - 40, self.modal_rect.top + 10, 30, 30)

        self.options = [
            {"name": "Max HP +25", "key": "max_hp_plus_25", "desc": "Increase max HP by 25", "cost": 3},
            {"name": "Bomb Power +10", "key": "bomb_power_plus_10", "desc": "Bombs deal +10 damage", "cost": 3},
            {"name": "Heal Boost", "key": "heal_boost", "desc": "Heals restore 35 HP instead of 25", "cost": 2},
            {"name": "Double Candy", "key": "double_candy", "desc": "Get 2x candy from battles", "cost": 4},
            {"name": "Auto Block", "key": "auto_block", "desc": "Auto-block first hit every battle", "cost": 5},
            {"name": "Resurrect Once", "key": "resurrect_once", "desc": "Survive death once", "cost": 6},
        ]

        self.hovered_button_index = None

    def open(self):
        self.visible = True

    def close(self):
        self.visible = False
        self.hovered_button_index = None

    def handle_event(self, event):
        if not self.visible:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.close_button.collidepoint(event.pos):
                self.close()
                return

            for idx, opt in enumerate(self.options):
                key = opt["key"]
                owned = self.player.upgrades.get(key, False)
                if owned:
                    continue  # Skip owned upgrades

                y = self.modal_rect.top + 100 + idx * 80 - self.scroll_offset
                buy_button = pygame.Rect(self.modal_rect.left + 30, y + 45, 200, 30)

                if buy_button.collidepoint(event.pos):
                    self.try_purchase(opt)
                    break

        elif event.type == pygame.MOUSEMOTION:
            self.hovered_button_index = None
            for idx, opt in enumerate(self.options):
                key = opt["key"]
                owned = self.player.upgrades.get(key, False)
                if owned:
                    continue

                y = self.modal_rect.top + 100 + idx * 80 - self.scroll_offset
                buy_button = pygame.Rect(self.modal_rect.left + 30, y + 45, 200, 30)
                if buy_button.collidepoint(event.pos):
                    self.hovered_button_index = idx
                    break

        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_offset -= event.y * self.scroll_speed
            self.scroll_offset = max(0, min(self.scroll_offset, max(0, len(self.options) * 80 - 300)))

    def try_purchase(self, opt):
        key = opt["key"]
        cost = opt["cost"]
        if not self.player.upgrades.get(key, False) and self.player.candy >= cost:
            self.player.candy -= cost
            self.player.upgrades[key] = True

            # Apply instant effects
            if key == "max_hp_plus_25":
                self.player.max_hp += 25
                self.player.hp += 25

    def draw(self):
        if not self.visible:
            return

        # Modal background
        pygame.draw.rect(self.screen, (30, 30, 30), self.modal_rect)
        pygame.draw.rect(self.screen, (200, 100, 200), self.modal_rect, 4)

        # Close button
        pygame.draw.rect(self.screen, (200, 50, 50), self.close_button)
        x_font = self.font.render("X", True, (255, 255, 255))
        self.screen.blit(x_font, (
            self.close_button.centerx - x_font.get_width() // 2,
            self.close_button.centery - x_font.get_height() // 2
        ))

        # Title
        title = self.title_font.render("Candy Shop", True, (255, 200, 255))
        self.screen.blit(title, (self.modal_rect.centerx - title.get_width() // 2, self.modal_rect.top + 20))

        # Current candy
        candy_text = self.font.render(f"Your Candy: {self.player.candy}", True, (255, 255, 255))
        self.screen.blit(candy_text, (self.modal_rect.left + 30, self.modal_rect.top + 60))

        # Upgrades list
        for idx, opt in enumerate(self.options):
            y = self.modal_rect.top + 100 + idx * 80 - self.scroll_offset
            if self.modal_rect.top + 80 <= y <= self.modal_rect.bottom - 40:
                name = opt["name"]
                desc = opt["desc"]
                cost = opt["cost"]
                key = opt["key"]
                owned = self.player.upgrades.get(key, False)

                name_text = self.font.render(name, True, (255, 255, 0) if not owned else (100, 255, 100))
                desc_text = self.font.render(desc, True, (200, 200, 200))
                cost_text = self.font.render(f"{cost} 🍬", True, (255, 200, 255))

                self.screen.blit(name_text, (self.modal_rect.left + 30, y))
                self.screen.blit(desc_text, (self.modal_rect.left + 30, y + 20))
                self.screen.blit(cost_text, (self.modal_rect.left + 250, y))

                if not owned:
                    buy_button = pygame.Rect(self.modal_rect.left + 30, y + 45, 200, 30)
                    # Change button color if hovered
                    if idx == self.hovered_button_index:
                        button_color = (140, 255, 140)  # lighter green on hover
                    else:
                        button_color = (100, 200, 100)
                    pygame.draw.rect(self.screen, button_color, buy_button)
                    pygame.draw.rect(self.screen, (255, 255, 255), buy_button, 2)
                    btn_text = self.font.render("Buy", True, (0, 0, 0))
                    self.screen.blit(btn_text, (
                        buy_button.centerx - btn_text.get_width() // 2,
                        buy_button.centery - btn_text.get_height() // 2
                    ))
                else:
                    owned_text = self.font.render("Owned", True, (100, 255, 100))
                    self.screen.blit(owned_text, (self.modal_rect.left + 250, y + 45))
