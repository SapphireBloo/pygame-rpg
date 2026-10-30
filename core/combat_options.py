import math

import pygame

from core import sfx
from core.icons import draw_icon
from core.items import BATTLE_ITEMS
from core.ui import get_font, outlined_text, blit_centered, GOLD, WHITE, INK

JAB, HAYMAKER, CHIN_CHECK, ITEMS = "Jab", "Haymaker", "Chin Check", "Items"
LOAF = "Loaf Launch"           # Crumb's move, once he's joined Charlie: once per fight
# Blocking isn't a menu choice: press SPACE as an enemy hit lands to block (or parry).

HINTS = {
    JAB: "Quick combo: nail each ring to chain more jabs. Every jab dazes the enemy.",
    HAYMAKER: "Huge hit. Never whiffs on a dazed enemy, but leaves you off balance.",
    CHIN_CHECK: "Finisher! Spends a full Chin meter. Time it for a massive uppercut.",
    ITEMS: "Open your bag: Gourd-Aid, remedies, bombs, Chin Juice. Using one takes your turn.",
    LOAF: "Crumb launches himself at the enemy: a huge hit that dazes it all the way. Once per fight.",
}

# Each move card: icon (core/icons.py), the little tag under its name, and its color
CARDS = {
    JAB: ("quick_hands", "Combo + Daze", (70, 140, 220)),
    HAYMAKER: ("heavy_hands", "Big hit, risky", (210, 70, 50)),
    CHIN_CHECK: ("iron_chin", "Finisher", (255, 150, 40)),
    ITEMS: ("bag", "Potions + bombs", (110, 170, 90)),
    LOAF: ("crumb", "Once per fight", (235, 175, 80)),
}
CARD_W, CARD_H, CARD_GAP = 200, 52, 14
CARD_BOTTOM = 596          # cards sit along the bottom edge of the battle screen
LIFT = 7                   # how far the selected card rises
NUMBER_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5)


class CombatOptions:
    """The move menu along the bottom of the battle screen."""

    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.options = [JAB, HAYMAKER, CHIN_CHECK, ITEMS]
        if player.companion:                     # Crumb's fighting with Charlie
            self.options.insert(3, LOAF)
        self.loaf_used = False                   # (the battle sets this once Crumb's flown)
        self.selected_index = 0
        self.name_font = get_font(18, bold=True)
        self.tag_font = get_font(12)
        self.hint_font = get_font(15)
        self.time = 0
        self.lift = [0.0] * len(self.options)     # eased lift per card
        self.last_draw = None

    def available(self, option):
        p = self.player
        if option == CHIN_CHECK:
            return p.chin_ready
        if option == ITEMS:
            return any(p.item_useful(item["key"]) for item in BATTLE_ITEMS)
        if option == LOAF:
            return not self.loaf_used
        return True

    def _usable_items(self):
        return sum(self.player.count(item["key"]) for item in BATTLE_ITEMS if self.player.item_useful(item["key"]))

    # ---- layout --------------------------------------------------------
    @property
    def card_w(self):
        """Cards shrink a little when there are five of them."""
        n = len(self.options)
        return min(CARD_W, (self.screen.get_width() - 24 - (n - 1) * CARD_GAP) // n)

    def card_rect(self, i):
        w = self.card_w
        total = len(self.options) * w + (len(self.options) - 1) * CARD_GAP
        x = (self.screen.get_width() - total) // 2 + i * (w + CARD_GAP)
        return pygame.Rect(x, CARD_BOTTOM - CARD_H, w, CARD_H)

    def _labels(self):
        """(option, None, rect) for each card (kept for older callers)."""
        return [(option, None, self.card_rect(i)) for i, option in enumerate(self.options)]

    def _option_at(self, pos):
        for i in range(len(self.options)):
            if self.card_rect(i).inflate(0, 2 * LIFT).move(0, -LIFT).collidepoint(pos):
                return i
        return None

    # ---- input -------------------------------------------------------------
    def handle_event(self, event):
        """Returns the chosen option when confirmed (key, number, or click), otherwise None."""
        if event.type == pygame.MOUSEMOTION:
            i = self._option_at(event.pos)
            if i is not None and i != self.selected_index:
                self.selected_index = i
                sfx.play("ui_move", 0.4)
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            i = self._option_at(event.pos)
            if i is None:
                return None
            self.selected_index = i
            sfx.play("ui_select", 0.7)
            return self.options[i]
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in NUMBER_KEYS[:len(self.options)]:   # 1-4 (or 5) picks a move straight away
            self.selected_index = NUMBER_KEYS.index(event.key)
            sfx.play("ui_select", 0.7)
            return self.options[self.selected_index]
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.selected_index = (self.selected_index - 1) % len(self.options)
            sfx.play("ui_move", 0.5)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.selected_index = (self.selected_index + 1) % len(self.options)
            sfx.play("ui_move", 0.5)
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
            sfx.play("ui_select", 0.7)
            return self.options[self.selected_index]
        return None

    def hint_text(self, option):
        if option == CHIN_CHECK and not self.player.chin_ready:
            return f"Fill the Chin meter first ({self.player.chin_meter}/{self.player.CHIN_METER_MAX}). Clean hits and parries fill it."
        if option == LOAF and self.loaf_used:
            return "Crumb's catching his breath. One Loaf Launch per fight."
        if option == ITEMS and not self.available(ITEMS):
            return "Nothing in your bag would help right now. The Crow sells potions at camp."
        return HINTS[option]

    # ---- drawing -------------------------------------------------------------
    def draw(self, show_hint=True):
        now = pygame.time.get_ticks()
        dt = 16 if self.last_draw is None else min(50, now - self.last_draw)
        self.last_draw = now
        self.time += dt

        # a soft dark band behind the cards
        band = pygame.Surface((self.screen.get_width(), 74), pygame.SRCALPHA)
        for y in range(74):
            band.fill((0, 0, 0, int(175 * min(1.0, y / 30))), (0, y, band.get_width(), 1))
        self.screen.blit(band, (0, self.screen.get_height() - 74))

        for i, option in enumerate(self.options):
            target = LIFT if i == self.selected_index else 0
            self.lift[i] += (target - self.lift[i]) * min(1.0, dt / 70)
            self._draw_card(i, option)

        if not show_hint:
            return
        hint = self.hint_font.render(self.hint_text(self.options[self.selected_index]), True, (230, 220, 200))
        pill = hint.get_rect(center=(self.screen.get_width() // 2, CARD_BOTTOM - CARD_H - 30)).inflate(22, 10)
        back = pygame.Surface(pill.size, pygame.SRCALPHA)
        pygame.draw.rect(back, (10, 6, 14, 190), back.get_rect(), border_radius=pill.height // 2)
        pygame.draw.rect(back, (*GOLD, 90), back.get_rect(), 1, border_radius=pill.height // 2)
        self.screen.blit(back, pill)
        blit_centered(self.screen, hint, pill.center)

    def _draw_card(self, i, option):
        s = self.screen
        icon_name, tag, color = CARDS[option]
        selected = i == self.selected_index
        ready = self.available(option)
        rect = self.card_rect(i).move(0, -round(self.lift[i]))
        chin_full = option == CHIN_CHECK and ready
        pulse = 0.5 + 0.5 * math.sin(self.time / 160)

        # glow behind the selected (or a ready Chin Check) card
        if selected or chin_full:
            glow_color = GOLD if selected else color
            strength = 120 if selected else int(60 + 70 * pulse)
            glow = pygame.Surface(rect.inflate(24, 24).size, pygame.SRCALPHA)
            for k in range(6):
                pygame.draw.rect(glow, (*glow_color, strength // (k + 2)), glow.get_rect().inflate(-k * 4, -k * 4),
                                 border_radius=16)
            s.blit(glow, rect.inflate(24, 24))

        # body: dark card with a colored strip on the left
        pygame.draw.rect(s, INK, rect.inflate(4, 4), border_radius=12)
        body = (44, 34, 52) if selected else (28, 21, 34)
        pygame.draw.rect(s, body, rect, border_radius=10)
        if option == CHIN_CHECK:                      # the card fills up with the Chin meter
            frac = self.player.chin_meter / self.player.CHIN_METER_MAX
            if frac > 0:
                fill = rect.inflate(-4, -4)
                fill.width = max(6, int(fill.width * frac))
                tint = pygame.Surface(fill.size, pygame.SRCALPHA)
                alpha = int(110 + 60 * pulse) if chin_full else 70
                pygame.draw.rect(tint, (*color, alpha), tint.get_rect(), border_radius=8)
                s.blit(tint, fill)
        strip = pygame.Rect(rect.x, rect.y, 8, rect.height)
        pygame.draw.rect(s, color if ready else (80, 74, 86), strip, border_top_left_radius=10,
                         border_bottom_left_radius=10)
        border = GOLD if selected else (color if chin_full else (78, 60, 88))
        pygame.draw.rect(s, border, rect, 3 if selected else 2, border_radius=10)

        # icon, name, tag
        icon_center = (rect.x + 34, rect.centery)
        pygame.draw.circle(s, INK, icon_center, 20)
        pygame.draw.circle(s, (18, 12, 22), icon_center, 19)
        draw_icon(s, icon_name, icon_center, 32)
        name_color = GOLD if selected else (WHITE if ready else (130, 122, 138))
        name = outlined_text(option, 18, name_color, True, 2)
        s.blit(name, (rect.x + 60, rect.y + 7))
        if option == CHIN_CHECK and not ready:
            tag = f"Meter {self.player.chin_meter}%"
        elif option == CHIN_CHECK:
            tag = "READY!"
        elif option == ITEMS and not ready:
            tag = "Nothing useful"
        elif option == LOAF and not ready:
            tag = "Used"
        tag_color = (255, 210, 120) if (chin_full or (selected and ready)) else (165, 155, 175)
        s.blit(self.tag_font.render(tag, True, tag_color), (rect.x + 61, rect.y + 31))

        # number key, and the item count badge
        key = self.tag_font.render(str(i + 1), True, (150, 140, 160))
        s.blit(key, key.get_rect(topright=(rect.right - 8, rect.y + 5)))
        if option == ITEMS:
            count = self._usable_items()
            if count:
                badge = outlined_text(str(count), 14, WHITE, True, 2)
                center = (rect.x + 50, rect.y + 12)
                pygame.draw.circle(s, INK, center, 10)
                pygame.draw.circle(s, (200, 60, 60), center, 9)
                s.blit(badge, badge.get_rect(center=center))
        if not ready:                                  # dim what can't be used right now
            dim = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(dim, (0, 0, 0, 90), dim.get_rect(), border_radius=10)
            s.blit(dim, rect)
