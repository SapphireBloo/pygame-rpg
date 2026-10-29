"""The battle Items menu: a row of item slots above the move bar.

Left/Right (or hover) to choose, Space/Enter (or click) to use,
Esc/Backspace (or right-click) to go back.
Only items that can be used in battle are listed (see core/items.py).
"""
import math

import pygame

from core import sfx
from core.icons import draw_icon
from core.items import BATTLE_ITEMS
from core.ui import get_font, outlined_text, GOLD, WHITE, INK

BACK = "back"
SLOT = 74
GAP = 12


class ItemPicker:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.items = []
        self.index = 0
        self.time = 0
        self.message = ""
        self.message_timer = 0

    def open(self):
        self.items = [item for item in BATTLE_ITEMS if self.player.count(item["key"])]
        # Start on the first item that would actually do something
        self.index = next((i for i, it in enumerate(self.items) if self.player.item_useful(it["key"])), 0)
        self.message_timer = 0

    # ---- layout ----------------------------------------------------------
    def _panel(self):
        n = max(1, len(self.items))
        row_w = n * SLOT + (n - 1) * GAP
        panel = pygame.Rect(0, 0, max(row_w + 40, 560), SLOT + 74)
        panel.midbottom = (self.screen.get_width() // 2, 530)       # just above the move cards
        return panel, row_w

    def _slots(self):
        panel, row_w = self._panel()
        x = panel.centerx - row_w // 2
        return [pygame.Rect(x + i * (SLOT + GAP), panel.y + 30, SLOT, SLOT) for i in range(len(self.items))]

    def _slot_at(self, pos):
        for i, slot in enumerate(self._slots()):
            if slot.collidepoint(pos):
                return i
        return None

    def _try_use(self):
        item = self.items[self.index]
        if self.player.item_useful(item["key"]):
            sfx.play("ui_select", 0.7)
            return item["key"]
        sfx.play("ui_error", 0.6)
        self.message = "Chin meter's already full!" if item.get("meter") else "You don't need that right now."
        self.message_timer = 1400
        return None

    # ---- input -----------------------------------------------------------
    def handle_event(self, event):
        """Returns an item key to use, BACK, or None."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            sfx.play("ui_move", 0.5)
            return BACK
        if event.type == pygame.MOUSEMOTION and self.items:
            i = self._slot_at(event.pos)
            if i is not None and i != self.index:
                self.index = i
                sfx.play("ui_move", 0.4)
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            i = self._slot_at(event.pos) if self.items else None
            if i is not None:
                self.index = i
                return self._try_use()
            if not self._panel()[0].collidepoint(event.pos) and event.pos[1] < 530:
                return BACK          # clicked out on the battlefield: close the bag
            return None
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_q):
            sfx.play("ui_move", 0.5)
            return BACK
        if not self.items:
            return BACK if event.key in (pygame.K_SPACE, pygame.K_RETURN) else None
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.index = (self.index - 1) % len(self.items)
            sfx.play("ui_move", 0.5)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.index = (self.index + 1) % len(self.items)
            sfx.play("ui_move", 0.5)
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
            return self._try_use()
        return None

    def update(self, dt):
        self.time += dt
        self.message_timer = max(0, self.message_timer - dt)

    def draw(self):
        panel, _ = self._panel()
        back = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(back, (10, 6, 14, 215), back.get_rect(), border_radius=14)
        pygame.draw.rect(back, (150, 200, 255, 200), back.get_rect(), 2, border_radius=14)
        self.screen.blit(back, panel)
        title = outlined_text("ITEMS", 16, (170, 210, 255), True, 2)
        self.screen.blit(title, (panel.x + 14, panel.y + 6))
        hint = get_font(13).render("Click or Space to use  |  Right-click or Esc: back", True, (150, 140, 160))
        self.screen.blit(hint, hint.get_rect(topright=(panel.right - 14, panel.y + 9)))

        if not self.items:
            text = get_font(17).render("Your bag is empty. The Crow sells items at camp.", True, (200, 190, 210))
            self.screen.blit(text, text.get_rect(center=(panel.centerx, panel.centery + 8)))
            return

        for i, (item, slot) in enumerate(zip(self.items, self._slots())):
            selected = i == self.index
            useful = self.player.item_useful(item["key"])
            lift = int(3 * math.sin(self.time / 140)) if selected else 0
            slot.y -= lift
            pygame.draw.rect(self.screen, INK, slot.inflate(4, 4), border_radius=12)
            pygame.draw.rect(self.screen, (44, 34, 52) if selected else (28, 20, 34), slot, border_radius=10)
            pygame.draw.rect(self.screen, GOLD if selected else (80, 64, 92), slot, 2 if not selected else 3,
                             border_radius=10)
            draw_icon(self.screen, item["icon"], slot.center, 48)
            if not useful:
                dim = pygame.Surface(slot.size, pygame.SRCALPHA)
                pygame.draw.rect(dim, (0, 0, 0, 140), dim.get_rect(), border_radius=10)
                self.screen.blit(dim, slot)
            count = outlined_text(f"x{self.player.count(item['key'])}", 15, WHITE, True, 2)
            self.screen.blit(count, count.get_rect(bottomright=(slot.right - 3, slot.bottom - 1)))

        item = self.items[self.index]
        label = self.message if self.message_timer else f"{item['name']}: {item['desc']}"
        color = (255, 200, 120) if self.message_timer else (230, 220, 200)
        text = get_font(15, bold=bool(self.message_timer)).render(label, True, color)
        self.screen.blit(text, text.get_rect(midbottom=(panel.centerx, panel.bottom - 6)))
