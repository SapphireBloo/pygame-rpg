import pygame

from core.ui import get_font, draw_panel, draw_button, blit_centered, WHITE, CANDY_PINK


class EndCombatModal:
    """Result popup shown after a battle (win or loss).

    Close it by clicking the button or pressing Space/Enter.
    """

    def __init__(self, screen):
        self.screen = screen
        self.font = get_font(22)
        self.rect = pygame.Rect(200, 150, 400, 300)
        self.button = pygame.Rect(0, 0, 170, 40)
        self.button.midbottom = (self.rect.centerx, self.rect.bottom - 30)
        self.visible = False
        self.title = ""
        self.lines = []
        self.button_label = ""
        self.border_color = (255, 165, 0)

    def open(self, title, lines, button_label="Continue", border_color=(255, 165, 0)):
        self.title = title
        self.lines = lines
        self.button_label = button_label
        self.border_color = border_color
        self.visible = True

    def handle_event(self, event):
        """Returns True when the player dismisses the modal."""
        if not self.visible:
            return False
        clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.button.collidepoint(event.pos)
        pressed = event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN)
        if clicked or pressed:
            self.visible = False
            return True
        return False

    def draw(self):
        if not self.visible:
            return
        draw_panel(self.screen, self.rect, self.border_color)
        blit_centered(self.screen, self.font.render(self.title, True, WHITE), (self.rect.centerx, self.rect.top + 30))

        y = self.rect.top + 90
        for text, color in self.lines:
            blit_centered(self.screen, self.font.render(text, True, color), (self.rect.centerx, y))
            y += 40

        draw_button(self.screen, self.button, self.button_label, self.font, (100, 200, 100))


# Handy colors for modal lines
CANDY_LINE = CANDY_PINK
JACK_LINE = (180, 180, 255)
