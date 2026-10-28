import pygame

from core.upgrades import UPGRADES
from core.ui import get_font, draw_panel, draw_button, blit_centered, WHITE, GREY, CANDY_PINK, HEAL_GREEN


class CandyShopModal:
    """Scrollable shop for spending candy on permanent upgrades.

    Mouse to buy, wheel to scroll, X or Esc to close.
    """

    ROW_HEIGHT = 80
    LIST_TOP = 100        # first row's offset from the top of the modal
    VISIBLE_HEIGHT = 340

    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.font = get_font(20)
        self.title_font = get_font(28, bold=True)
        self.visible = False

        self.rect = pygame.Rect(150, 80, 500, 440)
        self.close_button = pygame.Rect(self.rect.right - 40, self.rect.top + 10, 30, 30)
        self.content_rect = pygame.Rect(self.rect.left + 10, self.rect.top + 80,
                                        self.rect.width - 20, self.VISIBLE_HEIGHT)

        self.scroll = 0.0
        self.scroll_target = 0.0
        self.scroll_step = 40
        self.max_scroll = max(0, len(UPGRADES) * self.ROW_HEIGHT - 300)
        self.hovered = None
        self.flash_text = ""
        self.flash_timer = 0

    def open(self):
        self.visible = True

    def close(self):
        self.visible = False
        self.hovered = None

    # ---- layout helpers ------------------------------------------------
    def _row_y(self, idx):
        return self.rect.top + self.LIST_TOP + idx * self.ROW_HEIGHT - int(self.scroll)

    def _buy_rect(self, idx):
        return pygame.Rect(self.rect.left + 30, self._row_y(idx) + 45, 200, 30)

    def _button_at(self, pos):
        """Index of the Buy button under the mouse, if any (and visible)."""
        if not self.content_rect.collidepoint(pos):
            return None
        for idx, upgrade in enumerate(UPGRADES):
            if not self.player.has(upgrade["key"]) and self._buy_rect(idx).collidepoint(pos):
                return idx
        return None

    # ---- input / update ------------------------------------------------
    def handle_event(self, event):
        if not self.visible:
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_button.collidepoint(event.pos):
                self.close()
                return
            idx = self._button_at(event.pos)
            if idx is not None:
                upgrade = UPGRADES[idx]
                if self.player.buy_upgrade(upgrade):
                    self._flash(f"Bought {upgrade['name']}!")
                else:
                    self._flash("Not enough candy!")
        elif event.type == pygame.MOUSEMOTION:
            self.hovered = self._button_at(event.pos)
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_target = max(0, min(self.scroll_target - event.y * self.scroll_step, self.max_scroll))

    def _flash(self, text):
        self.flash_text = text
        self.flash_timer = 1500

    def update(self, dt):
        if not self.visible:
            return
        self.scroll += (self.scroll_target - self.scroll) * 0.2
        self.flash_timer = max(0, self.flash_timer - dt)

    # ---- drawing -------------------------------------------------------
    def draw(self):
        if not self.visible:
            return
        draw_panel(self.screen, self.rect, (200, 100, 200))
        draw_button(self.screen, self.close_button, "X", self.font, (200, 50, 50), text_color=WHITE, border=(200, 50, 50))
        blit_centered(self.screen, self.title_font.render("Candy Shop", True, CANDY_PINK),
                      (self.rect.centerx, self.rect.top + 35))
        self.screen.blit(self.font.render(f"Your Candy: {self.player.candy}", True, WHITE),
                         (self.rect.left + 30, self.rect.top + 60))
        old_clip = self.screen.get_clip()
        self.screen.set_clip(self.content_rect)
        for idx, upgrade in enumerate(UPGRADES):
            self._draw_row(idx, upgrade)
        self.screen.set_clip(old_clip)

        if self.flash_timer:  # "Bought X!" / "Not enough candy!" along the bottom edge
            blit_centered(self.screen, self.font.render(self.flash_text, True, (255, 230, 120)),
                          (self.rect.centerx, self.rect.bottom - 12))

        self._draw_scrollbar()

    def _draw_row(self, idx, upgrade):
        y = self._row_y(idx)
        left = self.rect.left + 30
        owned = self.player.has(upgrade["key"])
        affordable = self.player.candy >= upgrade["cost"]

        self.screen.blit(self.font.render(upgrade["name"], True, HEAL_GREEN if owned else (255, 255, 0)), (left, y))
        self.screen.blit(self.font.render(upgrade["desc"], True, GREY), (left, y + 20))
        self.screen.blit(self.font.render(f"{upgrade['cost']} candy", True, CANDY_PINK), (left + 220, y))

        if owned:
            self.screen.blit(self.font.render("Owned", True, HEAL_GREEN), (left + 220, y + 45))
            return
        if not affordable:
            color = (90, 90, 90)
        elif idx == self.hovered:
            color = (140, 255, 140)
        else:
            color = (100, 200, 100)
        draw_button(self.screen, self._buy_rect(idx), "Buy", self.font, color)

    def _draw_scrollbar(self):
        total = len(UPGRADES) * self.ROW_HEIGHT
        if total <= self.VISIBLE_HEIGHT:
            return
        track = pygame.Rect(self.rect.right - 15, self.content_rect.top, 5, self.VISIBLE_HEIGHT)
        thumb_h = max(40, self.VISIBLE_HEIGHT * self.VISIBLE_HEIGHT // total)
        ratio = self.scroll / max(1, self.max_scroll)
        thumb = pygame.Rect(track.left, track.top + int(ratio * (self.VISIBLE_HEIGHT - thumb_h)), 5, thumb_h)
        pygame.draw.rect(self.screen, (50, 50, 50), track)
        pygame.draw.rect(self.screen, GREY, thumb)
