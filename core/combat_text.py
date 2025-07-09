import pygame
import random

class CombatText:
    def __init__(self, text, x, y, color=(255, 255, 255), lifespan=1500, base_rise_speed=0.4):
        self.text = text
        # Add a small random horizontal offset for liveliness
        self.x = x + random.randint(-5, 5)
        self.y = y
        self.color = color
        self.lifespan = lifespan  # milliseconds
        self.age = 0
        self.alpha = 255
        # Slight random variation on rise speed
        self.rise_speed = base_rise_speed + random.uniform(-0.1, 0.1)
        self.font = pygame.font.SysFont("consolas", 22)
        self.surface = self.font.render(self.text, True, self.color).convert_alpha()
        # Pre-render outline surface
        self.outline_surface = self.create_outline_surface()

    def create_outline_surface(self):
        outline_color = (0, 0, 0)
        base = self.font.render(self.text, True, outline_color).convert_alpha()
        size = (base.get_width() + 2, base.get_height() + 2)
        outline_surf = pygame.Surface(size, pygame.SRCALPHA)

        # Draw outline by rendering text shifted by 1 px in all directions
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx != 0 or dy != 0:
                    outline_surf.blit(base, (dx + 1, dy + 1))
        return outline_surf

    def update(self, dt):
        self.age += dt
        self.y -= self.rise_speed
        fade_ratio = max(0, 1 - (self.age / self.lifespan))
        self.alpha = int(255 * fade_ratio)
        self.surface.set_alpha(self.alpha)
        self.outline_surface.set_alpha(self.alpha)

    def draw(self, screen):
        if self.alpha > 0:
            # Draw outline first, offset by (1,1) to center with main text
            screen.blit(self.outline_surface, (self.x - 1, self.y - 1))
            screen.blit(self.surface, (self.x, self.y))

    def is_alive(self):
        return self.age < self.lifespan
