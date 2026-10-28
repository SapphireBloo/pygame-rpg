import pygame

from core.ui import get_font, GOLD, GREY, blit_centered

JAB, HAYMAKER, CHIN_CHECK, HEAL, BOMB = "Jab", "Haymaker", "Chin Check", "Heal", "Bomb"
# Blocking isn't a menu choice: press SPACE as an enemy hit lands to block (or parry).

HINTS = {
    JAB: "Quick and reliable. Hit SPACE as the ring closes for bonus damage.",
    HAYMAKER: "Huge damage, but whiffs a lot unless you time it.",
    CHIN_CHECK: "Finisher! Spends a full Chin meter. Time it for a massive uppercut.",
    HEAL: "Eat 1 candy: restore HP and cure infection.",
    BOMB: "Throw a bomb for heavy damage.",
}


class CombatOptions:
    """The move menu along the bottom of the battle screen."""

    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.options = [JAB, HAYMAKER, CHIN_CHECK, HEAL, BOMB]
        self.selected_index = 0
        self.font = get_font(22, bold=True)
        self.hint_font = get_font(15)
        self.y = 562

    def available(self, option):
        p = self.player
        if option == CHIN_CHECK:
            return p.chin_ready
        if option == HEAL:
            return p.can_heal()
        if option == BOMB:
            return p.inventory.get("bomb", 0) > 0
        return True

    def handle_event(self, event):
        """Returns the chosen option when confirmed, otherwise None."""
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.selected_index = (self.selected_index - 1) % len(self.options)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.selected_index = (self.selected_index + 1) % len(self.options)
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
            return self.options[self.selected_index]
        return None

    def draw(self):
        texts = []
        for i, option in enumerate(self.options):
            selected = i == self.selected_index
            if option == CHIN_CHECK and self.player.chin_ready:
                color = (255, 120, 60) if not selected else GOLD
            else:
                color = GOLD if selected else GREY
            if not self.available(option):
                color = (95, 95, 95) if not selected else (170, 150, 80)
            texts.append(self.font.render(option, True, color))

        # Spread the options evenly across the bottom strip
        total = sum(t.get_width() for t in texts)
        gap = (self.screen.get_width() - 40 - total) / (len(texts) - 1)
        x = 20
        bar = pygame.Surface((self.screen.get_width(), self.screen.get_height() - self.y + 14), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 160))
        self.screen.blit(bar, (0, self.y - 14))
        for i, text in enumerate(texts):
            rect = text.get_rect(topleft=(x, self.y))
            if i == self.selected_index:
                box = rect.inflate(16, 12)
                pygame.draw.rect(self.screen, (40, 35, 30), box, border_radius=6)
                pygame.draw.rect(self.screen, GOLD, box, 2, border_radius=6)
            self.screen.blit(text, rect)
            x += text.get_width() + gap

        hint = self.hint_font.render(HINTS[self.options[self.selected_index]], True, (225, 215, 195))
        pill = hint.get_rect(center=(self.screen.get_width() // 2, self.y - 64)).inflate(18, 8)
        back = pygame.Surface(pill.size, pygame.SRCALPHA)
        back.fill((0, 0, 0, 150))
        self.screen.blit(back, pill)
        blit_centered(self.screen, hint, pill.center)
