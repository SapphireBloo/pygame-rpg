"""Chin Check Charlie - entry point.

Run with:  python main.py
Controls:  A/D or arrows to walk, Space to jump, S to slide, H to drink a Gourd-Aid,
           I for your bag, E to talk at camp, Esc or P to pause, M to mute.
           Battles: arrows + Space/Enter, or the mouse. Mouse in shops and menus.
           F11 or Alt+Enter for fullscreen.

The game moves between a few modes:
  title    the title screen (New Game, Continue, Settings, Controls, Credits, Quit)
  play     exploring, fighting, and the chapter cards (Esc pauses)
  credits  the rolling credits (from the title screen, or after the ending)
  summary  how the run went (after the ending's credits), then back to the title
Settings, Controls, Pause, and "are you sure?" boxes stack on top as overlays.
"""
import os

import pygame

from core import game_state, options as settings_store, save_game, sfx
from core.music_manager import MusicManager
from core.menu_ui import ConfirmDialog
from core.options import options
from core.player import Player
from core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, MUSIC_TRACKS
from scenes.battle_scene import BattleScene, PLAYER_TURN, ACTION, INTRO
from scenes.credits_scene import CreditsScene, SummaryScene
from scenes.exploration_scene import ExplorationScene
from scenes.level_transition import chapter_card, camp_card, next_transition
from scenes.menus import SettingsMenu, ControlsMenu, PauseMenu
from scenes.title_screen import TitleScreen


def create_screen(fullscreen):
    """The game always draws at 1066x600 (widescreen); SCALED stretches that to fit the
    window or monitor (keeping the shape, with black bars if needed) and maps
    mouse clicks back to game coordinates automatically."""
    os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "1")   # smooth scaling instead of blocky pixels
    size = (SCREEN_WIDTH, SCREEN_HEIGHT)
    flags = pygame.SCALED | pygame.RESIZABLE
    try:
        return pygame.display.set_mode(size, flags | (pygame.FULLSCREEN if fullscreen else 0))
    except pygame.error:
        return pygame.display.set_mode(size)                   # very old drivers: plain window


def is_fullscreen_toggle(event):
    return event.type == pygame.KEYDOWN and (
        event.key == pygame.K_F11 or (event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT))


def is_pause_key(event):
    return event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p)


def pick_music(exploration, battle):
    """Which song fits the game right now: "boss", "camp", or "level"."""
    if battle and battle.enemy.boss and not battle.ready_to_exit:
        return "boss"                 # through the victory screen, until it's closed
    boss = exploration.boss
    if boss and boss.state != "waiting" and not boss.defeated:
        return "boss"                 # Charlie walked into range and the boss started talking
    if exploration.in_camp:
        return "camp"
    return "level"


class Game:
    def __init__(self):
        settings_store.load()
        sfx.set_master(options["sfx_volume"])
        self.screen = create_screen(options["fullscreen"])
        self.fullscreen = options["fullscreen"]
        self.music = MusicManager(volume=options["music_volume"])
        self.running = True

        self.mode = "title"
        self.overlays = []            # menus on top of everything (last one gets the input)
        self.title = TitleScreen(self.screen, save_game.describe(save_game.load()))
        self.credits = None
        self.summary = None
        self.player = None
        self.exploration = None
        self.battle = None
        self.transition = None

    # ---- starting and leaving a run --------------------------------------
    def new_game(self):
        game_state.reset()
        self.player = Player()
        self.exploration = ExplorationScene(self.screen, self.player)
        self.battle = None
        self.transition = chapter_card(self.screen, self.exploration, 0)
        self.mode = "play"

    def continue_game(self):
        data = save_game.load()
        if not data:
            self.title.set_save(None)
            return
        self.player, chapter = save_game.restore(data)
        self.exploration = ExplorationScene(self.screen, self.player, chapter)
        self.battle = None
        self.transition = camp_card(self.screen, self.exploration)   # loads the camp behind the card
        self.mode = "play"

    def to_title(self):
        self.mode = "title"
        self.overlays.clear()
        self.battle = self.transition = None
        self.exploration = self.player = None
        self.title.set_save(save_game.describe(save_game.load()))

    def start_credits(self, after_ending=False):
        self.credits = CreditsScene(self.screen, after_ending)
        self.mode = "credits"

    # ---- settings ----------------------------------------------------------
    def apply_setting(self, key):
        if key == "music_volume":
            self.music.set_volume(options[key])
        elif key == "sfx_volume":
            sfx.set_master(options[key])
        elif key == "fullscreen" and options[key] != self.fullscreen:
            self.toggle_fullscreen()

    def toggle_fullscreen(self):
        try:
            pygame.display.toggle_fullscreen()
            self.fullscreen = not self.fullscreen
            options["fullscreen"] = self.fullscreen
        except pygame.error as err:   # some video drivers can't switch; keep playing
            print(f"[display] Fullscreen toggle not supported here: {err}")
            options["fullscreen"] = self.fullscreen

    # ---- overlays ---------------------------------------------------------
    def open_overlay(self, kind):
        in_game = self.mode == "play"
        overlay = {"settings": lambda: SettingsMenu(self.screen, self.apply_setting, in_game),
                   "controls": lambda: ControlsMenu(self.screen),
                   "pause": lambda: PauseMenu(self.screen)}[kind]()
        overlay.kind = kind
        self.overlays.append(overlay)

    def confirm(self, kind, title, message, yes):
        dialog = ConfirmDialog(self.screen, title, message, yes)
        dialog.kind = kind
        self.overlays.append(dialog)

    def overlay_action(self, overlay, action):
        kind = overlay.kind
        if action in ("back", "resume", "no"):
            self.overlays.pop()
            if kind == "settings":
                settings_store.save()
        elif kind == "pause":
            if action in ("settings", "controls"):
                self.open_overlay(action)
            elif action == "quit":
                self.confirm("quit_run", "Quit to title?", "Anything since your last camp will be lost. "
                             "(The game saves when you reach a camp.)", "Quit")
        elif kind == "new_game" and action == "yes":
            self.overlays.pop()
            self.new_game()
        elif kind == "quit_run" and action == "yes":
            self.to_title()

    def can_pause(self):
        if self.transition:
            return True
        if self.battle:
            return self.battle.state in (PLAYER_TURN, ACTION, INTRO)
        return self.exploration.active_menu is None

    # ---- the loop -----------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif is_fullscreen_toggle(event):
            self.toggle_fullscreen()
            settings_store.save()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            self.music.toggle_mute()
        elif self.overlays:
            overlay = self.overlays[-1]
            action = overlay.handle_event(event)
            if action:
                self.overlay_action(overlay, action)
        elif self.mode == "title":
            self.title_action(self.title.handle_event(event))
        elif self.mode == "play":
            focus_lost = event.type == pygame.WINDOWFOCUSLOST
            if (is_pause_key(event) or focus_lost) and self.can_pause():
                self.open_overlay("pause")
            else:
                (self.transition or self.battle or self.exploration).handle_event(event)
        elif self.mode == "credits":
            self.credits.handle_event(event)
        elif self.mode == "summary":
            self.summary.handle_event(event)

    def title_action(self, action):
        if action == "continue":
            self.continue_game()
        elif action == "new":
            if save_game.load():
                self.confirm("new_game", "Start a new game?", "Your saved game will be replaced when you "
                             "reach the first camp.", "Start")
            else:
                self.new_game()
        elif action in ("settings", "controls"):
            self.open_overlay(action)
        elif action == "credits":
            self.start_credits()
        elif action == "quit":
            self.running = False

    def update(self, dt):
        if self.mode == "play":
            track = pick_music(self.exploration, self.battle)
        else:
            track = "camp"                         # title, credits, and summary: the ominous camp theme
        self.music.play_track(*MUSIC_TRACKS[track])
        self.music.update()

        if self.overlays:
            self.overlays[-1].update(dt)
            if self.mode != "play":                # the title keeps drifting behind its menus
                self._update_mode(dt)
            return
        self._update_mode(dt)

    def _update_mode(self, dt):
        if self.mode == "title":
            self.title.update(dt)
        elif self.mode == "credits":
            self.credits.update(dt)
            if self.credits.done:
                if self.credits.after_ending:
                    self.summary = SummaryScene(self.screen, self.player, options["difficulty"])
                    self.mode = "summary"
                else:
                    self.mode = "title"
        elif self.mode == "summary":
            self.summary.update(dt)
            if self.summary.done:
                self.to_title()
        elif self.mode == "play":
            self._update_play(dt)

    def _update_play(self, dt):
        self.player.stats["play_ms"] += dt
        if self.transition:
            self.transition.update(dt)
            if self.exploration.finished:          # the ending card is over: roll the credits
                self.transition = None
                self.start_credits(after_ending=True)
            elif self.transition.done:
                self.transition = None
        elif self.battle:
            self.battle.update(dt)
            if self.battle.ready_to_exit:
                self.battle = None
        else:
            self.exploration.update(pygame.key.get_pressed(), dt)
            foe = self.exploration.take_battle_trigger()
            if foe:
                self.battle = BattleScene(self.screen, self.player, self.exploration.level, foe)
            elif self.exploration.exit_reached:
                self.transition = next_transition(self.screen, self.exploration)

    def draw(self):
        if self.mode == "title":
            self.title.draw()
        elif self.mode == "credits":
            self.credits.draw()
        elif self.mode == "summary":
            self.summary.draw()
        elif self.mode == "play":
            (self.transition or self.battle or self.exploration).draw()
        for overlay in self.overlays:
            overlay.draw()


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    game = Game()
    clock = pygame.time.Clock()
    while game.running:
        dt = min(clock.tick(FPS), 50)  # ms since last frame; capped so a loading hitch doesn't skip fades
        for event in pygame.event.get():
            game.handle_event(event)
        if not game.running:
            break
        game.update(dt)
        game.draw()
        pygame.display.flip()
    settings_store.save()
    pygame.quit()


if __name__ == "__main__":
    main()
