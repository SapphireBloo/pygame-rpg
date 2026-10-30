"""Card-grid menus: the Blacksmith's upgrades, the Crow's shop (Buy / Sell), and
Charlie's bag (I). They share one look:

    title + subtitle (+ the shopkeeper's portrait), candy wallet, close button,
    optional tabs, a scrollable grid of cards, and a footer for messages.

A menu subclass only says what cards to show (entries) and what happens when a
card's button is clicked (activate). Mouse to click, wheel to scroll,
Tab or Left/Right to switch tabs, Esc or E to close.
"""
from dataclasses import dataclass

import pygame

from core import sfx
from core.effects import Particles, ease_out
from core.icons import draw_icon
from core.ui import (get_font, wrap_text, outlined_text, draw_spooky_panel, dim_screen, draw_candy_button,
                     WHITE, GOLD, HEAL_GREEN, INK)

CARD_BG = (30, 22, 36)
CARD_BG_HOVER = (40, 30, 48)
CARD_BORDER = (78, 60, 88)
BUY_GREEN = (70, 170, 80)
NEED_RED = (255, 110, 100)
DONE_GREEN = (80, 170, 90)


@dataclass
class Entry:
    key: str
    name: str
    desc: str
    icon: str
    button: str = None          # button label, or None for no button
    button_icon: str = None     # e.g. "candy" in front of a price
    enabled: bool = True        # greyed-out button when False (still clickable, to explain why)
    stamp: str = None           # big rotated word instead of a button, e.g. "OWNED"
    count: int = None           # "x3" badge in the corner
    note: str = None            # small line under the description, e.g. "need 2 more"
    note_color: tuple = NEED_RED
    done: bool = False          # green "already have it" styling
    tier: tuple = None          # (owned, total): a row of pips in the corner for tiered upgrades


class CardShop:
    COLUMNS = 2
    CARD_W, CARD_H = 292, 106
    GAP = 12
    GRID_TOP = 98            # from the top of the panel
    GRID_BOTTOM = 52         # space left under the grid for the footer
    OPEN_MS = 200

    title = "SHOP"
    subtitle = ""
    accent = (255, 140, 40)
    tabs = ()                # e.g. ("BUY", "SELL")
    hint = "Click a button   |   Esc to close"
    empty_text = "Nothing here."

    def __init__(self, screen, player, portrait=None):
        self.screen = screen
        self.player = player
        self.portrait = portrait  # small surface drawn left of the title (the shopkeeper)
        self.visible = False
        self.tab = 0

        self.rect = pygame.Rect(0, 0, 640, 496)
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2 + 4)
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.close_button = pygame.Rect(self.rect.right - 44, self.rect.top + 14, 30, 30)   # screen coords
        side = (self.rect.width - self.COLUMNS * self.CARD_W - (self.COLUMNS - 1) * self.GAP) // 2
        self.grid = pygame.Rect(side, self.GRID_TOP, self.rect.width - side * 2,
                                self.rect.height - self.GRID_TOP - self.GRID_BOTTOM)          # panel coords
        self.content_rect = self.grid.move(self.rect.topleft)                                # screen coords

        self.scroll = 0.0
        self.scroll_target = 0.0
        self.scroll_step = 40
        self.mouse = (-1, -1)
        self.hovered = None          # index of the button under the mouse
        self.hovered_card = None
        self.flash_text = ""
        self.flash_color = WHITE
        self.flash_timer = 0
        self.card_flash = {}         # idx -> ms of "it worked" glow
        self.card_shake = {}         # idx -> ms of "can't do that" wobble
        self.wallet_pulse = 0
        self.open_timer = 0
        self.particles = Particles()
        self._wrapped = {}
        self._entries = []

    # ---- what subclasses fill in ------------------------------------------
    def entries(self):
        """The cards to show right now (for the current tab)."""
        return []

    def activate(self, entry):
        """The card's button was clicked. Returns (worked, message, color)."""
        return False, "", WHITE

    # ---- open / close -----------------------------------------------------
    def open(self, tab=0):
        self.visible = True
        self.tab = tab
        self.scroll = self.scroll_target = 0.0
        self.open_timer = self.OPEN_MS
        self.flash_timer = 0
        self.mouse = pygame.mouse.get_pos() if pygame.display.get_init() else (-1, -1)
        self._entries = self.entries()

    def close(self):
        self.visible = False
        self.hovered = self.hovered_card = None

    # ---- layout helpers (panel coordinates) ------------------------------
    @property
    def max_scroll(self):
        rows = -(-len(self._entries) // self.COLUMNS)
        content_h = rows * self.CARD_H + max(0, rows - 1) * self.GAP
        return max(0, content_h - self.grid.height)

    def _card_rect(self, idx):
        col, row = idx % self.COLUMNS, idx // self.COLUMNS
        return pygame.Rect(self.grid.x + col * (self.CARD_W + self.GAP),
                           self.grid.y + row * (self.CARD_H + self.GAP) - int(self.scroll),
                           self.CARD_W, self.CARD_H)

    def _button_rect(self, idx):
        card = self._card_rect(idx)
        return pygame.Rect(card.right - 104, card.bottom - 36, 92, 28)

    def _tab_rect(self, i):
        return pygame.Rect(self.rect.width - 66 - (len(self.tabs) - i) * 92, 66, 84, 26)

    def _local(self, pos):
        return pos[0] - self.rect.x, pos[1] - self.rect.y

    def _card_at(self, pos):
        if not self.content_rect.collidepoint(pos):
            return None
        local = self._local(pos)
        for idx in range(len(self._entries)):
            if self._card_rect(idx).collidepoint(local):
                return idx
        return None

    def _button_at(self, pos):
        """Index of the card button under the mouse, if any."""
        idx = self._card_at(pos)
        if idx is None or self._entries[idx].button is None:
            return None
        return idx if self._button_rect(idx).collidepoint(self._local(pos)) else None

    # ---- input / update ------------------------------------------------
    def handle_event(self, event):
        if not self.visible:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_e):
                self.close()
            elif self.tabs and event.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                step = -1 if event.key in (pygame.K_LEFT, pygame.K_a) else 1
                self._switch_tab((self.tab + step) % len(self.tabs))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_button.collidepoint(event.pos):
                self.close()
                return
            local = self._local(event.pos)
            for i in range(len(self.tabs)):
                if self._tab_rect(i).collidepoint(local):
                    self._switch_tab(i)
                    return
            idx = self._button_at(event.pos)
            if idx is not None:
                self._click(idx)
        elif event.type == pygame.MOUSEMOTION:
            self.mouse = event.pos
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_target = max(0, min(self.scroll_target - event.y * self.scroll_step, self.max_scroll))

    def _switch_tab(self, i):
        if i != self.tab:
            sfx.play("ui_move", 0.6)
            self.tab = i
            self.scroll = self.scroll_target = 0.0
            self.card_flash.clear()
            self.card_shake.clear()
            self._entries = self.entries()

    def _click(self, idx):
        entry = self._entries[idx]
        button = self._button_rect(idx)
        worked, message, color = self.activate(entry)
        if worked:
            sfx.play("ui_select")
            self.card_flash[idx] = 450
            self.wallet_pulse = 350
            self.particles.candy_corn(button.centerx, button.centery, 14)
        else:
            sfx.play("ui_error")
            self.card_shake[idx] = 320
        if message:
            self._flash(message, color)
        self._entries = self.entries()
        self.scroll_target = min(self.scroll_target, self.max_scroll)

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
        draw_spooky_panel(surf, surf.get_rect().inflate(-10, -12).move(-3, -4), self.accent)
        self._draw_header(surf)

        surf.set_clip(self.grid.inflate(8, 0))
        for idx, entry in enumerate(self._entries):
            card = self._card_rect(idx)
            if card.bottom >= self.grid.top - 4 and card.top <= self.grid.bottom + 4:
                self._draw_card(surf, idx, entry, card)
        if not self._entries:
            for n, line in enumerate(wrap_text(get_font(18), self.empty_text, self.grid.width - 80)):
                text = get_font(18).render(line, True, (170, 155, 180))
                surf.blit(text, text.get_rect(center=(self.rect.width // 2, self.grid.centery - 20 + n * 24)))
        self.particles.draw(surf)
        surf.set_clip(None)
        self._draw_scrollbar(surf)
        self._draw_footer(surf)

        t = 1 - self.open_timer / self.OPEN_MS
        if t < 1:
            surf.set_alpha(int(255 * t))
            self.screen.blit(surf, (self.rect.x, self.rect.y + int(24 * (1 - ease_out(t)))))
            surf.set_alpha(None)
        else:
            self.screen.blit(surf, self.rect)

    def _draw_header(self, surf):
        x = 30
        if self.portrait:
            badge = pygame.Rect(22, 14, 72, 72)
            pygame.draw.rect(surf, INK, badge.inflate(4, 4), border_radius=12)
            pygame.draw.rect(surf, (18, 12, 22), badge, border_radius=10)
            pygame.draw.rect(surf, self.accent, badge, 2, border_radius=10)
            surf.set_clip(badge.inflate(-4, -4))
            surf.blit(self.portrait, self.portrait.get_rect(midbottom=(badge.centerx, badge.bottom + 4)))
            surf.set_clip(None)
            x = 106
        title = outlined_text(self.title, 34 if len(self.title) < 12 else 30, self.accent, True, 3)
        surf.blit(title, (x, 20))
        surf.blit(get_font(15).render(self.subtitle, True, (190, 170, 200)), (x + 4, 62))

        for i, name in enumerate(self.tabs):
            rect = self._tab_rect(i)
            active = i == self.tab
            pygame.draw.rect(surf, INK, rect.inflate(4, 4), border_radius=9)
            pygame.draw.rect(surf, self.accent if active else (45, 34, 52), rect, border_radius=8)
            label = outlined_text(name, 15, WHITE if active else (170, 160, 180), True, 1)
            surf.blit(label, label.get_rect(center=rect.center))

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

    def _desc_lines(self, text):
        if text not in self._wrapped:
            self._wrapped[text] = wrap_text(get_font(15), text, self.CARD_W - 100)
        return self._wrapped[text]

    def _fit_lines(self, entry):
        """The description, cut to what fits: two lines over a button, note, or stamp, four otherwise.
        (Anything longer ends in "..." instead of running under the button.)"""
        lines = self._desc_lines(entry.desc)
        room = 2 if (entry.stamp or entry.note or entry.button is not None) else 4
        if len(lines) <= room:
            return lines
        font, width = get_font(15), self.CARD_W - 100
        last = " ".join(lines[room - 1:])
        while last and font.size(last + "...")[0] > width:
            last = last[:-1]
        return lines[:room - 1] + [last.rstrip(" ,.;:") + "..."]

    def _draw_card(self, surf, idx, entry, card):
        wobble = self.card_shake.get(idx, 0)
        if wobble:
            card = card.move(int(5 * ((wobble // 40) % 2 * 2 - 1)), 0)
        hovered = idx == self.hovered_card and not entry.done

        fill = (26, 40, 30) if entry.done else (CARD_BG_HOVER if hovered else CARD_BG)
        border = DONE_GREEN if entry.done else (self.accent if hovered else CARD_BORDER)
        pygame.draw.rect(surf, INK, card.inflate(4, 4), border_radius=12)
        pygame.draw.rect(surf, fill, card, border_radius=10)
        pygame.draw.rect(surf, border, card, 2, border_radius=10)
        if idx in self.card_flash:
            glow = pygame.Surface(card.size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (180, 255, 170, int(120 * self.card_flash[idx] / 450)), glow.get_rect(),
                             border_radius=10)
            surf.blit(glow, card)

        # Icon badge (nudged up on tiered cards to make room for the tier pips underneath)
        badge = (card.x + 44, card.centery - (8 if entry.tier else 0))
        pygame.draw.circle(surf, INK, badge, 35)
        pygame.draw.circle(surf, (18, 12, 22), badge, 33)
        pygame.draw.circle(surf, border if (entry.done or hovered) else (95, 70, 50), badge, 33, 2)
        draw_icon(surf, entry.icon, badge, 46)
        if entry.count is not None:
            tag = outlined_text(f"x{entry.count}", 16, WHITE, True, 2)
            surf.blit(tag, tag.get_rect(bottomright=(badge[0] + 36, badge[1] + 36)))

        x = card.x + 88
        surf.blit(outlined_text(entry.name, 18, HEAL_GREEN if entry.done else GOLD, True, 1), (x, card.y + 9))
        if entry.tier:
            self._draw_pips(surf, entry.tier, (badge[0], card.bottom - 10), entry.done)
        y = card.y + 33
        for line in self._fit_lines(entry):
            surf.blit(get_font(15).render(line, True, (196, 186, 204)), (x, y))
            y += 17

        if entry.stamp:
            stamp = pygame.transform.rotate(outlined_text(entry.stamp, 20, HEAL_GREEN, True, 2), 8)
            surf.blit(stamp, stamp.get_rect(center=(card.right - 62, card.bottom - 24)))
            return
        if entry.note:
            surf.blit(get_font(14, bold=True).render(entry.note, True, entry.note_color), (x, card.bottom - 27))
        if entry.button is not None:
            draw_candy_button(surf, self._button_rect(idx), entry.button, BUY_GREEN,
                              hover=idx == self.hovered, enabled=entry.enabled, size=18,
                              icon_name=entry.button_icon, press=1.0 if idx in self.card_flash else 0.0)

    def _draw_pips(self, surf, tier, center, done):
        """A centered row of little diamonds: filled for tiers owned, hollow for the ones still to buy."""
        owned, total = tier
        for i in range(total):
            cx, cy = center[0] + (i - (total - 1) / 2) * 14, center[1]
            cx = round(cx)
            points = [(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)]
            pygame.draw.polygon(surf, INK, [(px + (1 if px > cx else -1 if px < cx else 0),
                                             py + (1 if py > cy else -1 if py < cy else 0)) for px, py in points])
            if i < owned:
                pygame.draw.polygon(surf, HEAL_GREEN if done else self.accent, points)
            else:
                pygame.draw.polygon(surf, (40, 30, 46), points)
                pygame.draw.polygon(surf, (110, 90, 120), points, 1)

    def _draw_scrollbar(self, surf):
        if not self.max_scroll:
            return
        track = pygame.Rect(self.rect.width - 22, self.grid.top, 5, self.grid.height)
        thumb_h = max(40, track.height * self.grid.height // (self.grid.height + self.max_scroll))
        ratio = min(1.0, self.scroll / self.max_scroll)
        thumb = pygame.Rect(track.x, track.y + int(ratio * (track.height - thumb_h)), 5, thumb_h)
        pygame.draw.rect(surf, (45, 35, 50), track, border_radius=3)
        pygame.draw.rect(surf, self.accent, thumb, border_radius=3)

    def _draw_footer(self, surf):
        y = self.rect.height - 34
        if self.flash_timer:
            text = outlined_text(self.flash_text, 18, self.flash_color, True, 2)
            rise = int(6 * max(0, self.flash_timer - 1400) / 200)
            surf.blit(text, text.get_rect(center=(self.rect.width // 2, y - rise)))
        else:
            hint = self.hint + ("   |   Wheel to scroll" if self.max_scroll else "")
            text = get_font(14).render(hint, True, (140, 125, 150))
            surf.blit(text, text.get_rect(center=(self.rect.width // 2, y)))
