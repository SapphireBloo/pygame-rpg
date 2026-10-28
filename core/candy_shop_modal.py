import pygame

from core import sfx
from core.effects import Particles, ease_out
from core.icons import draw_icon
from core.upgrades import UPGRADES
from core.ui import (get_font, wrap_text, outlined_text, draw_spooky_panel, dim_screen, draw_candy_button,
                     WHITE, GOLD, PUMPKIN, HEAL_GREEN, INK)

ACCENT = PUMPKIN
CARD_BG = (30, 22, 36)
CARD_BORDER = (78, 60, 88)
BUY_GREEN = (70, 170, 80)
NEED_RED = (255, 110, 100)


class CandyShopModal:
    """Candy Shop: a grid of upgrade cards. Mouse to buy, wheel to scroll,
    X or Esc to close.

    Everything is drawn onto one panel surface in panel coordinates, then the
    panel is blitted at self.rect (with a short slide-in when it opens)."""

    COLUMNS = 2
    CARD_W, CARD_H = 292, 106
    GAP = 12
    GRID_TOP = 98            # from the top of the panel
    GRID_BOTTOM = 52         # space left under the grid for the footer
    OPEN_MS = 200

    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.visible = False

        self.rect = pygame.Rect(0, 0, 640, 496)
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2 + 4)
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.close_button = pygame.Rect(self.rect.right - 44, self.rect.top + 14, 30, 30)   # screen coords
        side = (self.rect.width - self.COLUMNS * self.CARD_W - (self.COLUMNS - 1) * self.GAP) // 2
        self.grid = pygame.Rect(side, self.GRID_TOP, self.rect.width - side * 2,
                                self.rect.height - self.GRID_TOP - self.GRID_BOTTOM)          # panel coords
        self.content_rect = self.grid.move(self.rect.topleft)                                # screen coords

        rows = -(-len(UPGRADES) // self.COLUMNS)
        content_h = rows * self.CARD_H + (rows - 1) * self.GAP
        self.max_scroll = max(0, content_h - self.grid.height)
        self.scroll = 0.0
        self.scroll_target = 0.0
        self.scroll_step = 40

        self.mouse = (-1, -1)
        self.hovered = None          # index of the Buy button under the mouse
        self.hovered_card = None
        self.flash_text = ""
        self.flash_color = WHITE
        self.flash_timer = 0
        self.card_flash = {}         # idx -> ms of "just bought" glow
        self.card_shake = {}         # idx -> ms of "can't afford" wobble
        self.wallet_pulse = 0
        self.open_timer = 0
        self.particles = Particles()
        self._desc = {u["key"]: wrap_text(get_font(15), u["desc"], self.CARD_W - 100) for u in UPGRADES}

    def open(self):
        self.visible = True
        self.open_timer = self.OPEN_MS
        self.mouse = pygame.mouse.get_pos() if pygame.display.get_init() else (-1, -1)

    def close(self):
        self.visible = False
        self.hovered = self.hovered_card = None

    # ---- layout helpers (panel coordinates) ------------------------------
    def _card_rect(self, idx):
        col, row = idx % self.COLUMNS, idx // self.COLUMNS
        return pygame.Rect(self.grid.x + col * (self.CARD_W + self.GAP),
                           self.grid.y + row * (self.CARD_H + self.GAP) - int(self.scroll),
                           self.CARD_W, self.CARD_H)

    def _buy_rect(self, idx):
        card = self._card_rect(idx)
        return pygame.Rect(card.right - 104, card.bottom - 36, 92, 28)

    def _local(self, pos):
        return pos[0] - self.rect.x, pos[1] - self.rect.y

    def _card_at(self, pos):
        if not self.content_rect.collidepoint(pos):
            return None
        local = self._local(pos)
        for idx in range(len(UPGRADES)):
            if self._card_rect(idx).collidepoint(local):
                return idx
        return None

    def _button_at(self, pos):
        """Index of the Buy button under the mouse, if any (and visible)."""
        idx = self._card_at(pos)
        if idx is None or self.player.has(UPGRADES[idx]["key"]):
            return None
        return idx if self._buy_rect(idx).collidepoint(self._local(pos)) else None

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
                self._buy(idx)
        elif event.type == pygame.MOUSEMOTION:
            self.mouse = event.pos
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_target = max(0, min(self.scroll_target - event.y * self.scroll_step, self.max_scroll))

    def _buy(self, idx):
        upgrade = UPGRADES[idx]
        if self.player.buy_upgrade(upgrade):
            sfx.play("ui_select")
            self._flash(f"Bought {upgrade['name']}!", HEAL_GREEN)
            self.card_flash[idx] = 450
            self.wallet_pulse = 350
            button = self._buy_rect(idx)
            self.particles.candy_corn(button.centerx, button.centery, 18)
        else:
            sfx.play("miss")
            short = upgrade["cost"] - self.player.candy
            self._flash(f"Need {short} more candy!", NEED_RED)
            self.card_shake[idx] = 320

    def _flash(self, text, color=WHITE):
        self.flash_text = text
        self.flash_color = color
        self.flash_timer = 1600

    def update(self, dt):
        if not self.visible:
            return
        self.scroll += (self.scroll_target - self.scroll) * 0.2
        self.flash_timer = max(0, self.flash_timer - dt)
        self.wallet_pulse = max(0, self.wallet_pulse - dt)
        self.open_timer = max(0, self.open_timer - dt)
        for timers in (self.card_flash, self.card_shake):
            for idx in list(timers):
                timers[idx] -= dt
                if timers[idx] <= 0:
                    del timers[idx]
        self.particles.update(dt)
        hovered = self._button_at(self.mouse)
        if hovered is not None and hovered != self.hovered:
            sfx.play("ui_move", 0.5)
        self.hovered = hovered
        self.hovered_card = self._card_at(self.mouse)

    # ---- drawing -------------------------------------------------------
    def draw(self):
        if not self.visible:
            return
        dim_screen(self.screen, 150)
        surf = self.surface
        surf.fill((0, 0, 0, 0))
        local = surf.get_rect()
        draw_spooky_panel(surf, local.inflate(-10, -12).move(-3, -4), ACCENT)
        self._draw_header(surf)

        surf.set_clip(self.grid.inflate(8, 0))
        for idx, upgrade in enumerate(UPGRADES):
            card = self._card_rect(idx)
            if card.bottom >= self.grid.top - 4 and card.top <= self.grid.bottom + 4:
                self._draw_card(surf, idx, upgrade, card)
        self.particles.draw(surf)
        surf.set_clip(None)
        self._draw_scroll_hints(surf)
        self._draw_footer(surf)

        t = 1 - self.open_timer / self.OPEN_MS
        if t < 1:
            surf.set_alpha(int(255 * t))
            self.screen.blit(surf, (self.rect.x, self.rect.y + int(24 * (1 - ease_out(t)))))
            surf.set_alpha(None)
        else:
            self.screen.blit(surf, self.rect)

    def _draw_header(self, surf):
        title = outlined_text("CANDY SHOP", 34, ACCENT, True, 3)
        surf.blit(title, (30, 22))
        surf.blit(get_font(15).render("Trade your sugar for strength.", True, (190, 170, 200)), (34, 64))

        # Candy wallet
        pulse = self.wallet_pulse / 350
        count = outlined_text(str(self.player.candy), 24 + int(6 * pulse), GOLD if not pulse else WHITE, True, 2)
        pill = pygame.Rect(0, 0, count.get_width() + 62, 40)
        pill.topright = (self.rect.width - 66, 18)
        pygame.draw.rect(surf, INK, pill.inflate(4, 4), border_radius=20)
        pygame.draw.rect(surf, (52, 36, 30), pill, border_radius=20)
        pygame.draw.rect(surf, (120, 80, 40), pill, 2, border_radius=20)
        draw_icon(surf, "candy", (pill.x + 22, pill.centery), 30)
        surf.blit(count, count.get_rect(midleft=(pill.x + 42, pill.centery)))

        # Close button (circle with an X)
        close = self.close_button.move(-self.rect.x, -self.rect.y)
        hover = self.close_button.collidepoint(self.mouse)
        pygame.draw.circle(surf, INK, close.center, 17)
        pygame.draw.circle(surf, (210, 70, 60) if hover else (160, 45, 45), close.center, 15)
        for dx in (-1, 1):
            pygame.draw.line(surf, WHITE, (close.centerx - 6, close.centery - 6 * dx),
                             (close.centerx + 6, close.centery + 6 * dx), 3)

    def _draw_card(self, surf, idx, upgrade, card):
        owned = self.player.has(upgrade["key"])
        affordable = self.player.candy >= upgrade["cost"]
        wobble = self.card_shake.get(idx, 0)
        if wobble:
            card = card.move(int(5 * ((wobble // 40) % 2 * 2 - 1)), 0)
        hovered = idx == self.hovered_card and not owned

        fill = (26, 40, 30) if owned else (CARD_BG if not hovered else (40, 30, 48))
        border = (80, 170, 90) if owned else (ACCENT if hovered else CARD_BORDER)
        pygame.draw.rect(surf, INK, card.inflate(4, 4), border_radius=12)
        pygame.draw.rect(surf, fill, card, border_radius=10)
        pygame.draw.rect(surf, border, card, 2, border_radius=10)
        if idx in self.card_flash:
            glow = pygame.Surface(card.size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (180, 255, 170, int(120 * self.card_flash[idx] / 450)), glow.get_rect(),
                             border_radius=10)
            surf.blit(glow, card)

        # Icon badge
        badge = (card.x + 44, card.centery)
        pygame.draw.circle(surf, INK, badge, 35)
        pygame.draw.circle(surf, (18, 12, 22), badge, 33)
        pygame.draw.circle(surf, border if (owned or hovered) else (95, 70, 50), badge, 33, 2)
        draw_icon(surf, upgrade.get("icon", "candy"), badge, 46)

        x = card.x + 88
        name_color = HEAL_GREEN if owned else GOLD
        surf.blit(outlined_text(upgrade["name"], 18, name_color, True, 1), (x, card.y + 9))
        y = card.y + 33
        for line in self._desc[upgrade["key"]]:
            surf.blit(get_font(15).render(line, True, (196, 186, 204)), (x, y))
            y += 17

        if owned:
            stamp = outlined_text("OWNED", 20, HEAL_GREEN, True, 2)
            stamp = pygame.transform.rotate(stamp, 8)
            surf.blit(stamp, stamp.get_rect(center=(card.right - 62, card.bottom - 24)))
            return
        if not affordable:
            short = upgrade["cost"] - self.player.candy
            surf.blit(get_font(14, bold=True).render(f"need {short} more", True, NEED_RED),
                      (x, card.bottom - 27))
        draw_candy_button(surf, self._buy_rect(idx), str(upgrade["cost"]), BUY_GREEN,
                          hover=idx == self.hovered, enabled=affordable, size=18, icon_name="candy",
                          press=1.0 if idx in self.card_flash else 0.0)

    def _draw_scroll_hints(self, surf):
        if not self.max_scroll:
            return
        # Track on the right edge, plus fades at the top/bottom when there's more to see
        track = pygame.Rect(self.rect.width - 22, self.grid.top, 5, self.grid.height)
        thumb_h = max(40, track.height * self.grid.height // (self.grid.height + self.max_scroll))
        ratio = self.scroll / self.max_scroll
        thumb = pygame.Rect(track.x, track.y + int(ratio * (track.height - thumb_h)), 5, thumb_h)
        pygame.draw.rect(surf, (45, 35, 50), track, border_radius=3)
        pygame.draw.rect(surf, ACCENT, thumb, border_radius=3)

    def _draw_footer(self, surf):
        y = self.rect.height - 34
        if self.flash_timer:
            text = outlined_text(self.flash_text, 18, self.flash_color, True, 2)
            rise = int(6 * max(0, self.flash_timer - 1400) / 200)
            surf.blit(text, text.get_rect(center=(self.rect.width // 2, y - rise)))
        else:
            hint = "Click a price to buy   |   Wheel to scroll   |   Esc to close"
            if not self.max_scroll:
                hint = "Click a price to buy   |   Esc to close"
            surf.blit(text := get_font(14).render(hint, True, (140, 125, 150)),
                      text.get_rect(center=(self.rect.width // 2, y)))
