"""Chin Check Charlie - entry point.

Run with:  python main.py
Controls:  A/D or arrows to walk, H to eat candy (heal), M to mute,
           arrows + Space/Enter in battle, mouse for the Candy Shop,
           F11 or Alt+Enter for fullscreen.
"""
import os

import pygame

from core.music_manager import MusicManager
from core.player import Player
from core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, MUSIC_FILE, MUSIC_VOLUME, FULLSCREEN
from scenes.battle_scene import BattleScene
from scenes.exploration_scene import ExplorationScene
from scenes.level_transition import chapter_card, next_transition


def create_screen():
    """The game always draws at 800x600; SCALED stretches that to fit the
    window or monitor (keeping the shape, with black bars if needed) and maps
    mouse clicks back to game coordinates automatically."""
    os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "1")   # smooth scaling instead of blocky pixels
    size = (SCREEN_WIDTH, SCREEN_HEIGHT)
    flags = pygame.SCALED | pygame.RESIZABLE
    try:
        return pygame.display.set_mode(size, flags | (pygame.FULLSCREEN if FULLSCREEN else 0))
    except pygame.error:
        return pygame.display.set_mode(size)                   # very old drivers: plain window


def is_fullscreen_toggle(event):
    return event.type == pygame.KEYDOWN and (
        event.key == pygame.K_F11 or (event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT))


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = create_screen()
    clock = pygame.time.Clock()

    music = MusicManager(volume=MUSIC_VOLUME)
    music.load(MUSIC_FILE)
    music.play()

    player = Player()
    exploration = ExplorationScene(screen, player)
    battle = None                                         # a BattleScene while fighting
    transition = chapter_card(screen, exploration, 0)     # opening "Chapter 1" card

    running = True
    while running:
        dt = clock.tick(FPS)  # milliseconds since last frame
        scene = transition or battle or exploration

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif is_fullscreen_toggle(event):
                try:
                    pygame.display.toggle_fullscreen()
                except pygame.error as err:   # some video drivers can't switch; keep playing
                    print(f"[display] Fullscreen toggle not supported here: {err}")
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                music.toggle_mute()
            else:
                scene.handle_event(event)

        if transition:
            transition.update(dt)
            transition.draw()
            if transition.done:
                transition = None
        elif battle:
            battle.update(dt)
            battle.draw()
            if battle.ready_to_exit:
                battle = None
        else:
            exploration.update(pygame.key.get_pressed(), dt)
            exploration.draw()
            foe = exploration.take_battle_trigger()
            if foe:
                battle = BattleScene(screen, player, exploration.level, foe)
            elif exploration.exit_reached:
                transition = next_transition(screen, exploration)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
