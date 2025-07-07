import pygame
from core.player import Player
from scenes.battle_scene import BattleScene
from scenes.exploration_scene import ExplorationScene

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Pygame RPG")

clock = pygame.time.Clock()

# Create a persistent player instance
player = Player()

# Initial scene
exploration = ExplorationScene(screen, player)
exploration.last_battle_x = -1000  # Allow the first battle to trigger
battle = None  # Will be initialized when needed
current_scene = "exploration"

running = True
while running:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if current_scene == "exploration":
            exploration.handle_event(event)
        elif current_scene == "battle":
            battle.handle_event(event)

    if current_scene == "exploration":
        exploration.update(keys)
        exploration.draw()

        triggered_ghost = exploration.check_battle_trigger()

        if triggered_ghost:
            battle = BattleScene(screen, player)  # Pass the persistent player
            current_scene = "battle"
            triggered_ghost.visible = False
            triggered_ghost.trigger_battle = False
            exploration.last_battle_x = exploration.hero_x

    elif current_scene == "battle":
        battle.update()
        battle.draw()

        if battle.battle_over:
            if keys[pygame.K_ESCAPE]:
                current_scene = "exploration"

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
