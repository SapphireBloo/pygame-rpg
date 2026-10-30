"""Menus that pop up over the title screen or the game.

  SettingsMenu   music and sound volume, fullscreen, difficulty (saved to disk)
  ControlsMenu   every key, in one place
  PauseMenu      Esc / P in game: Resume, Settings, Controls, Cheats, Quit to Title
  CheatMenu      type in a cheat code (for testing; see core/cheats.py)

Each one's handle_event returns an action string (or None), and the caller
(main.py) decides what to do with it.
"""
import math

import pygame

from core import cheats, sfx
from core.difficulty import DIFFICULTIES, DIFFICULTY_NAMES, DIFFICULTY_BLURBS
from core.menu_ui import ButtonMenu, BACK, CONFIRM, NAV_UP, NAV_DOWN, PUMPKIN, BUTTON_FILL, hint_line
from core.options import options
from core.ui import get_font, outlined_text, draw_spooky_panel, dim_screen, draw_candy_button, wrap_text, GOLD, WHITE, INK

TRACK_W = 210
PANEL_TEXT = (215, 205, 220)
DIM_TEXT = (150, 135, 160)


class SettingsMenu:
    ROWS = (("music_volume", "Music"), ("sfx_volume", "Sound Effects"), ("fullscreen", "Fullscreen"),
            ("difficulty", "Difficulty"), ("back", "Back"))

    def __init__(self, screen, on_change, in_game=False):
        """on_change(key) is called whenever a setting changes, so main.py can apply it."""
        self.screen = screen
        self.on_change = on_change
        self.in_game = in_game
        self.rect = pygame.Rect(0, 0, 560, 440)
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2)
        self.index = 0
        self.dragging = None
        self.time = 0

    # ---- layout -------------------------------------------------------
    def _row_y(self, i):
        return self.rect.y + 100 + i * 62

    def _track(self, i):
        return pygame.Rect(self.rect.x + 270, self._row_y(i) - 5, TRACK_W, 10)

    def _toggle(self, i):
        return pygame.Rect(self.rect.x + 270, self._row_y(i) - 16, 96, 32)

    def _arrows(self, i):
        y = self._row_y(i)
        left = pygame.Rect(self.rect.x + 262, y - 16, 32, 32)
        right = pygame.Rect(self.rect.x + 452, y - 16, 32, 32)
        return left, right

    def _back_rect(self):
        r = pygame.Rect(0, 0, 180, 44)
        r.midbottom = (self.rect.centerx, self.rect.bottom - 30)
        return r

    def _row_at(self, pos):
        if self._back_rect().collidepoint(pos):
            return len(self.ROWS) - 1
        for i in range(len(self.ROWS) - 1):
            band = pygame.Rect(self.rect.x + 20, self._row_y(i) - 26, self.rect.width - 40, 52)
            if band.collidepoint(pos):
                return i
        return None

    # ---- changing values ----------------------------------------------
    def _set(self, key, value):
        if options[key] != value:
            options[key] = value
            self.on_change(key)

    def _nudge(self, key, step):
        if key in ("music_volume", "sfx_volume"):
            self._set(key, round(max(0.0, min(1.0, options[key] + 0.1 * step)), 2))
            sfx.play("block", 0.6) if key == "sfx_volume" else sfx.play("ui_move", 0.5)
        elif key == "fullscreen":
            self._set(key, not options[key])
            sfx.play("ui_select", 0.6)
        elif key == "difficulty":
            i = DIFFICULTIES.index(options[key])
            self._set(key, DIFFICULTIES[(i + step) % len(DIFFICULTIES)])
            sfx.play("ui_select", 0.6)

    def _drag_to(self, i, x):
        track = self._track(i)
        value = round(max(0.0, min(1.0, (x - track.x) / track.width)) * 20) / 20
        self._set(self.ROWS[i][0], value)

    # ---- input ----------------------------------------------------------
    def handle_event(self, event):
        key = self.ROWS[self.index][0]
        if event.type == pygame.KEYDOWN:
            if event.key in BACK:
                sfx.play("ui_move", 0.5)
                return "back"
            if event.key in NAV_UP:
                self.index = (self.index - 1) % len(self.ROWS)
                sfx.play("ui_move", 0.5)
            elif event.key in NAV_DOWN:
                self.index = (self.index + 1) % len(self.ROWS)
                sfx.play("ui_move", 0.5)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._nudge(key, -1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._nudge(key, 1)
            elif event.key in CONFIRM:
                if key == "back":
                    sfx.play("ui_select", 0.7)
                    return "back"
                self._nudge(key, 1)
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging is not None:
                self._drag_to(self.dragging, event.pos[0])
            else:
                i = self._row_at(event.pos)
                if i is not None and i != self.index:
                    self.index = i
                    sfx.play("ui_move", 0.4)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging is not None:
                self.dragging = None
                if self.ROWS[self.index][0] == "sfx_volume":
                    sfx.play("block", 0.6)       # hear the new volume
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            i = self._row_at(event.pos)
            if i is None:
                return None
            self.index = i
            key = self.ROWS[i][0]
            if key == "back":
                sfx.play("ui_select", 0.7)
                return "back"
            if key in ("music_volume", "sfx_volume") and self._track(i).inflate(24, 28).collidepoint(event.pos):
                self.dragging = i
                self._drag_to(i, event.pos[0])
            elif key == "fullscreen" and self._toggle(i).inflate(10, 10).collidepoint(event.pos):
                self._nudge(key, 1)
            elif key == "difficulty":
                left, right = self._arrows(i)
                if left.inflate(10, 10).collidepoint(event.pos):
                    self._nudge(key, -1)
                elif right.inflate(10, 10).collidepoint(event.pos) or \
                        pygame.Rect(left.right, left.y, right.x - left.right, left.height).collidepoint(event.pos):
                    self._nudge(key, 1)
        return None

    def update(self, dt):
        self.time += dt

    # ---- drawing ----------------------------------------------------------
    def draw(self):
        s = self.screen
        dim_screen(s, 165)
        draw_spooky_panel(s, self.rect, PUMPKIN)
        title = outlined_text("SETTINGS", 32, PUMPKIN, True, 3)
        s.blit(title, title.get_rect(midtop=(self.rect.centerx, self.rect.y + 22)))

        for i, (key, label) in enumerate(self.ROWS[:-1]):
            y = self._row_y(i)
            selected = i == self.index
            if selected:
                band = pygame.Surface((self.rect.width - 40, 50), pygame.SRCALPHA)
                pygame.draw.rect(band, (255, 160, 60, 34), band.get_rect(), border_radius=10)
                s.blit(band, (self.rect.x + 20, y - 25))
            name = outlined_text(label, 20, GOLD if selected else PANEL_TEXT, True, 2)
            s.blit(name, name.get_rect(midleft=(self.rect.x + 44, y)))
            if key in ("music_volume", "sfx_volume"):
                self._draw_slider(i, options[key], selected)
            elif key == "fullscreen":
                pill = self._toggle(i)
                on = options[key]
                draw_candy_button(s, pill, "ON" if on else "OFF", (70, 160, 80) if on else (110, 70, 80),
                                  hover=selected, size=16)
            elif key == "difficulty":
                left, right = self._arrows(i)
                for rect, flip in ((left, True), (right, False)):
                    self._draw_arrow(rect, flip, selected)
                name = outlined_text(DIFFICULTY_NAMES[options[key]], 20, WHITE, True, 2)
                s.blit(name, name.get_rect(center=((left.right + right.left) // 2, y)))

        blurb = DIFFICULTY_BLURBS[options["difficulty"]]
        if self.in_game:
            blurb += " Applies from the next fight."
        for n, line in enumerate(wrap_text(get_font(14), blurb, self.rect.width - 90)):
            text = get_font(14).render(line, True, DIM_TEXT)
            s.blit(text, text.get_rect(midtop=(self.rect.centerx, self._row_y(3) + 30 + n * 17)))

        back = self._back_rect()
        draw_candy_button(s, back, "Back", BUTTON_FILL, hover=self.index == len(self.ROWS) - 1, size=19)
        hint_line(s, "Arrows or mouse to change   |   Esc to go back", self.rect.bottom + 22)

    def _draw_slider(self, i, value, selected):
        s = self.screen
        track = self._track(i)
        pygame.draw.rect(s, INK, track.inflate(4, 4), border_radius=6)
        pygame.draw.rect(s, (45, 34, 52), track, border_radius=5)
        filled = track.copy()
        filled.width = int(track.width * value)
        if filled.width:
            pygame.draw.rect(s, PUMPKIN if selected else (190, 110, 50), filled, border_radius=5)
        knob = (track.x + int(track.width * value), track.centery)
        pygame.draw.circle(s, INK, knob, 11)
        pygame.draw.circle(s, GOLD if selected else (230, 210, 180), knob, 9)
        pct = get_font(16, bold=True).render(f"{round(value * 100)}%", True, PANEL_TEXT)
        s.blit(pct, pct.get_rect(midleft=(track.right + 18, track.centery)))

    def _draw_arrow(self, rect, flip, selected):
        cx, cy = rect.center
        d = -1 if flip else 1
        pts = [(cx - 7 * d, cy - 10), (cx + 9 * d, cy), (cx - 7 * d, cy + 10)]
        pygame.draw.polygon(self.screen, INK, [(x + d, y + 1) for x, y in pts])
        pygame.draw.polygon(self.screen, GOLD if selected else (200, 180, 160), pts)


CONTROLS = (
    ("EXPLORING", (
        ("A / D  or  Left / Right", "Walk"),
        ("Shift", "Run"),
        ("Space  or  Up", "Jump (again in the air: double jump)"),
        ("S  or  Down", "Slide (into a monster for a First Strike)"),
        ("Land on a monster", "First Strike"),
        ("E", "Search things, talk at camp, or step into a portal"),
        ("I", "Open your bag"),
        ("H", "Drink a Gourd-Aid (a Remedy if you're sick)"),
    )),
    ("FIGHTING", (
        ("Arrows, 1-5, or mouse", "Pick a move"),
        ("Space, Enter, or click", "Throw it, and hit the timing rings"),
        ("Space as a hit lands", "Block (perfect timing = PARRY)"),
        ("Esc", "Back out of the Items menu"),
    )),
    ("ANYWHERE", (
        ("Esc  or  P", "Pause"),
        ("M", "Mute music"),
        ("F11  or  Alt+Enter", "Fullscreen"),
    )),
)


class ControlsMenu:
    def __init__(self, screen):
        self.screen = screen
        self.rect = pygame.Rect(0, 0, 700, 520)
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2 - 6)
        self.back = ButtonMenu([("back", "Back")], self.rect.centerx, self.rect.bottom - 62, width=170, height=42)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in BACK + CONFIRM:
            sfx.play("ui_move", 0.5)
            return "back"
        return self.back.handle_event(event)

    def update(self, dt):
        self.back.update(dt)

    def draw(self):
        s = self.screen
        dim_screen(s, 165)
        draw_spooky_panel(s, self.rect, PUMPKIN)
        title = outlined_text("CONTROLS", 32, PUMPKIN, True, 3)
        s.blit(title, title.get_rect(midtop=(self.rect.centerx, self.rect.y + 18)))
        y = self.rect.y + 70
        key_font, act_font = get_font(15, bold=True), get_font(15)
        for heading, rows in CONTROLS:
            s.blit(outlined_text(heading, 15, (170, 210, 255), True, 1), (self.rect.x + 36, y))
            y += 22
            for keys, action in rows:
                s.blit(key_font.render(keys, True, GOLD), (self.rect.x + 48, y))
                s.blit(act_font.render(action, True, PANEL_TEXT), (self.rect.x + 290, y))
                y += 20
            y += 10
        self.back.draw(s)


class PauseMenu:
    def __init__(self, screen):
        self.screen = screen
        self.rect = pygame.Rect(0, 0, 340, 416)
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2)
        self.menu = ButtonMenu([("resume", "Resume"), ("settings", "Settings"), ("controls", "Controls"),
                                ("cheats", "Cheats"), ("quit", "Quit to Title")], self.rect.centerx,
                               self.rect.y + 92, width=220)
        self.time = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in BACK + (pygame.K_p,):
            sfx.play("ui_move", 0.5)
            return "resume"
        return self.menu.handle_event(event)

    def update(self, dt):
        self.time += dt
        self.menu.update(dt)

    def draw(self):
        s = self.screen
        dim_screen(s, 150)
        draw_spooky_panel(s, self.rect, PUMPKIN)
        bob = 3 * math.sin(self.time / 300)
        title = outlined_text("PAUSED", 34, PUMPKIN, True, 3)
        s.blit(title, title.get_rect(midtop=(self.rect.centerx, self.rect.y + 22 + bob)))
        self.menu.draw(s)
        hint_line(s, "Esc to resume", self.rect.bottom + 22)


class CheatMenu:
    """Type a cheat code and press Enter. A real code flips that cheat on (or back off)."""
    MAX_LEN = 20
    wants_text = True              # (so typing letters here doesn't also trigger M to mute, etc.)

    def __init__(self, screen):
        self.screen = screen
        self.rect = pygame.Rect(0, 0, 480, 330)
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2)
        self.field = pygame.Rect(0, 0, 340, 46)
        self.field.midtop = (self.rect.centerx, self.rect.y + 92)
        self.back = ButtonMenu([("back", "Back")], self.rect.centerx, self.rect.bottom - 64, width=170, height=42)
        self.text = ""
        self.message = None        # (text, color, ms left)
        self.shake = 0
        self.time = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("ui_move", 0.5)
                return "back"
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return None
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._submit()
                return None
            ch = getattr(event, "unicode", "")
            if ch and ch.isalnum() and ch.isascii() and len(self.text) < self.MAX_LEN:
                self.text += ch.lower()
                sfx.play("ui_move", 0.3)
            return None
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return self.back.handle_event(event)
        return None

    def _submit(self):
        if not self.text:
            return
        result = cheats.enter(self.text)
        self.text = ""
        if result is None:
            self.message = ("Nothing happens...", (255, 120, 100), 2200)
            self.shake = 300
            sfx.play("ui_error", 0.7)
        else:
            label, on = result
            self.message = (f"{label}: {'ON' if on else 'OFF'}", (130, 230, 120) if on else (230, 200, 160), 3000)
            sfx.play("ui_select", 0.8)

    def update(self, dt):
        self.time += dt
        self.shake = max(0, self.shake - dt)
        if self.message:
            text, color, left = self.message
            self.message = (text, color, left - dt) if left > dt else None
        self.back.update(dt)

    def draw(self):
        s = self.screen
        dim_screen(s, 165)
        draw_spooky_panel(s, self.rect, PUMPKIN)
        title = outlined_text("CHEAT CODES", 32, PUMPKIN, True, 3)
        s.blit(title, title.get_rect(midtop=(self.rect.centerx, self.rect.y + 22)))
        hint = get_font(14).render("Type a code and press Enter", True, DIM_TEXT)
        s.blit(hint, hint.get_rect(midtop=(self.rect.centerx, self.rect.y + 66)))

        field = self.field.move(int(6 * math.sin(self.time / 25)) if self.shake else 0, 0)
        pygame.draw.rect(s, INK, field.inflate(6, 6), border_radius=10)
        pygame.draw.rect(s, (30, 22, 36), field, border_radius=8)
        pygame.draw.rect(s, PUMPKIN, field, 2, border_radius=8)
        typed = outlined_text(self.text, 22, WHITE, True, 2) if self.text else None
        x = field.x + 14
        if typed:
            s.blit(typed, typed.get_rect(midleft=(x, field.centery)))
            x += typed.get_width() + 2
        if (self.time // 500) % 2 == 0:                     # the blinking caret
            pygame.draw.rect(s, GOLD, (x, field.y + 11, 3, field.height - 22))

        if self.message:
            text, color, _ = self.message
            msg = outlined_text(text, 20, color, True, 2)
            s.blit(msg, msg.get_rect(midtop=(self.rect.centerx, field.bottom + 18)))
        on = cheats.labels()
        status = "On: " + ", ".join(on) if on else "No cheats on"
        line = get_font(14, bold=bool(on)).render(status, True, (150, 220, 140) if on else DIM_TEXT)
        s.blit(line, line.get_rect(midtop=(self.rect.centerx, field.bottom + 52)))
        self.back.draw(s)
        hint_line(s, "Esc to go back   |   Enter a code again to turn it off", self.rect.bottom + 22)
