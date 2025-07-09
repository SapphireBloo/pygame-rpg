import pygame
from core.player import Player
from scenes.battle_scene import BattleScene
from scenes.exploration_scene import ExplorationScene
from core.music_manager import MusicManager

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Pygame RPG")

clock = pygame.time.Clock()

# Initialize MusicManager and play background music
music_manager = MusicManager(volume=0.4)
music_manager.load("assets/audio/background_music.mp3")
music_manager.play()

# Create a persistent player instance (includes position now)
player = Player()

# Initial scene
exploration = ExplorationScene(screen, player)
exploration.last_battle_x = -1000  # Allow the first battle to trigger
battle = None
current_scene = "exploration"

running = True
while running:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Music mute toggle on M key
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                music_manager.toggle_mute()

        if current_scene == "exploration":
            exploration.handle_event(event)
        elif current_scene == "battle":
            battle.handle_event(event)

    dt = clock.tick(60)  # Calculate delta time (seconds)

    if current_scene == "exploration":
        exploration.update(keys)
        exploration.draw()

        triggered_ghost = exploration.check_battle_trigger()

        if triggered_ghost:
            battle = BattleScene(screen, player)  # Pass player with retained x/y
            current_scene = "battle"
            triggered_ghost.visible = False
            triggered_ghost.trigger_battle = False
            exploration.last_battle_x = player.x  # Now uses player.x instead of hero_x

    elif current_scene == "battle":
        battle.update(dt)  # Pass dt here
        battle.draw()

        if battle.battle_over:
            if keys[pygame.K_ESCAPE]:
                current_scene = "exploration"

    pygame.display.flip()

pygame.quit()
