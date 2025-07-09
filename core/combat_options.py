import pygame

class CombatOptions:
    def __init__(self, screen):
        self.screen = screen
        self.options = ["Attack", "Heal", "Block", "Item"]
        self.selected_index = 0
        self.font = pygame.font.SysFont("consolas", 28, bold=True)
        self.option_spacing = 180
        self.base_x = 50
        self.y = 550
        self.highlight_color = (255, 215, 0)
        self.text_color = (200, 200, 200)
        self.selection_made = False

    def handle_event(self, event):
        if self.selection_made:
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key == pygame.K_RIGHT:
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):  # Accept Space or Enter to confirm
                self.selection_made = True

    def reset_selection(self):
        self.selection_made = False

    def get_selected(self):
        if self.selection_made:
            return self.options[self.selected_index]
        else:
            return None

    def draw(self):
        for i, option in enumerate(self.options):
            x = self.base_x + i * self.option_spacing
            color = self.highlight_color if i == self.selected_index else self.text_color

            # Draw background rect for selected option
            if i == self.selected_index:
                text_surface = self.font.render(option, True, color)
                padding = 10
                rect = pygame.Rect(
                    x - padding,
                    self.y - padding,
                    text_surface.get_width() + padding * 2,
                    text_surface.get_height() + padding * 2
                )
                pygame.draw.rect(self.screen, (50, 50, 50), rect, border_radius=6)
                pygame.draw.rect(self.screen, self.highlight_color, rect, 3, border_radius=6)

            # Draw option text
            text_surface = self.font.render(option, True, color)
            self.screen.blit(text_surface, (x, self.y))
