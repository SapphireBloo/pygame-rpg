import pygame
class EndCombatModal:
    def __init__(self, screen, candy_reward=0):
        self.screen = screen
        self.font = pygame.font.SysFont("consolas", 22)
        self.modal_rect = pygame.Rect(200, 150, 400, 300)
        self.end_button_rect = pygame.Rect(325, 370, 150, 40)
        self.candy_reward = candy_reward
        self.visible = False
        self.comment = "Whisper Jack: Not bad, kid."
        self.done = False  # Track when modal is closed

    def open(self, candy_reward, comment=None):
        self.candy_reward = candy_reward
        self.comment = comment or self.comment
        self.visible = True
        self.done = False  # Reset done flag on open

    def close(self):
        self.visible = False
        self.done = True  # Mark as done when closed

    def handle_event(self, event):
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.end_button_rect.collidepoint(event.pos):
                self.close()
                return True
        return False

    def draw(self):
        if not self.visible:
            return

        pygame.draw.rect(self.screen, (30, 30, 30), self.modal_rect)
        pygame.draw.rect(self.screen, (255, 165, 0), self.modal_rect, 4)

        title_surf = self.font.render("Battle Won!", True, (255, 255, 255))
        self.screen.blit(title_surf, (self.modal_rect.centerx - title_surf.get_width() // 2, 170))

        candy_text = self.font.render(f"Candy earned: {self.candy_reward}", True, (255, 200, 255))
        self.screen.blit(candy_text, (self.modal_rect.left + 50, 230))

        comment = self.font.render(self.comment, True, (180, 180, 255))
        self.screen.blit(comment, (self.modal_rect.left + 50, 270))

        pygame.draw.rect(self.screen, (100, 200, 100), self.end_button_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), self.end_button_rect, 2)
        button_text = self.font.render("End Combat", True, (0, 0, 0))
        self.screen.blit(button_text, (
            self.end_button_rect.centerx - button_text.get_width() // 2,
            self.end_button_rect.centery - button_text.get_height() // 2
        ))
