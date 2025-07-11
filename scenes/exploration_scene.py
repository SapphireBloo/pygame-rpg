import pygame
import os
import random
from core.player import Player
from core.player_hud import PlayerHUD
from core.skeleton_animation import SkeletonAnimation
from core import game_state  # import game_state here
from core.candy_shop_modal import CandyShopModal  # NEW IMPORT

class Ghost:
    def __init__(self, x, y, spawn_frames, enemy_img):
        self.x = x
        self.y = y
        self.spawn_frames = spawn_frames
        self.enemy_img = enemy_img
        self.spawning = False
        self.spawn_index = 0
        self.spawn_timer = 0
        self.spawn_speed = 80
        self.spawn_complete = False
        self.visible = True
        self.trigger_battle = False

class ExplorationScene:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.font = pygame.font.SysFont("consolas", 22)

        self.bg_tile = pygame.image.load(os.path.join("assets", "images", "backgrounds", "bg_0.png")).convert()
        self.bg_tile = pygame.transform.scale(self.bg_tile, (800, 600))
        self.bg_width = self.bg_tile.get_width()
        self.camera_offset = 0

        self.hero_idle_frames = self.load_frames(os.path.join("assets", "images", "hero_idle"))
        self.hero_walk_frames = self.load_frames(os.path.join("assets", "images", "hero_walk"))
        self.hero_index = 0
        self.hero_walk_index = 0
        self.last_update = pygame.time.get_ticks()
        self.hero_speed = 200

        self.player.y = 400
        self.velocity = 5

        spawn_frames = self.load_sprite_sheet(
            os.path.join("assets", "images", "ghost_spawn", "ghost_spawn.png"),
            frame_width=32,
            frame_height=32,
            scale=(150, 150)
        )

        fallback_path = os.path.join("assets", "images", "goblin.png")
        if os.path.exists(fallback_path):
            enemy_img = pygame.image.load(fallback_path).convert_alpha()
            enemy_img = pygame.transform.scale(enemy_img, (150, 150))
        else:
            enemy_img = None

        ghost_positions = [800 * i for i in range(1, 11)]
        self.ghosts = [
            Ghost(x, 400, spawn_frames, enemy_img)
            for x in ghost_positions
        ]

        self.skeleton_frames = self.load_frames(os.path.join("assets", "images", "Skeleton"))
        self.skeleton_frames = [pygame.transform.flip(frame, True, False) for frame in self.skeleton_frames]
        self.skeleton_animations = []
        self.skeleton_intro_triggered = False
        self.skeleton_intro_done = False
        self.movement_locked = False
        self.skeleton_second_intro_triggered = False
        self.skeleton_second_intro_done = False

        self.player_hud = PlayerHUD(self.screen, self.font, self.player)

        self.shop_modal = CandyShopModal(screen, player)
        self.show_shop_button = True
        self.shop_button_rect = pygame.Rect(680, 10, 110, 35)

    def load_frames(self, folder_path, scale=(150, 150)):
        frames = []
        if not os.path.exists(folder_path):
            return frames
        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith(".png"):
                path = os.path.join(folder_path, filename)
                image = pygame.image.load(path).convert_alpha()
                image = pygame.transform.scale(image, scale)
                frames.append(image)
        return frames

    def load_sprite_sheet(self, sheet_path, frame_width, frame_height, scale=(150, 150)):
        sheet = pygame.image.load(sheet_path).convert_alpha()
        sheet_width, _ = sheet.get_size()
        frames = []
        for i in range(sheet_width // frame_width):
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), (i * frame_width, 0, frame_width, frame_height))
            frame = pygame.transform.scale(frame, scale)
            frames.append(frame)
        return frames

    def spawn_skeleton_intro(self, x, y):
        charlie_name = "Chin Check Charlie"
        intro_messages = [
            f"Well, well, well... look who we have here, {charlie_name}.",
            "The shadows whisper my name... I'm Whisper Jack.",
            "I’m here to guide you — and maybe keep you on your toes.",
            "Use A and D to walk. And watch out for the candy... if you want me around."
        ]
        anim = SkeletonAnimation(x, y, self.skeleton_frames, messages=intro_messages, frame_delay=250)
        self.skeleton_animations.append(anim)

    def spawn_skeleton_second_intro(self, x, y):
        charlie_name = "Chin Check Charlie"
        second_intro_messages = [
            f"Well, well... look who finally got some candy, {charlie_name}!",
            "But you look beat up. Hitting 'H' might sweeten the deal.",
            "Don't make me come back just to patch you up again...",
            "Don't eat too much candy though... you'll need it for the Candy Shop ."
        ]
        anim = SkeletonAnimation(x, y, self.skeleton_frames, messages=second_intro_messages, frame_delay=250)
        self.skeleton_animations.append(anim)

    def handle_event(self, event):
        if self.shop_modal.visible:
            self.shop_modal.handle_event(event)
            return

        for anim in self.skeleton_animations:
            anim.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and self.shop_button_rect.collidepoint(event.pos):
            self.shop_modal.open()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            heal_amount = self.player.heal()
            if heal_amount > 0:
                print(f"Healed {heal_amount} HP by eating candy. Candy left: {self.player.candy}")


    def update(self, keys):
        if self.shop_modal.visible:
            return

        now = pygame.time.get_ticks()
        moving = keys[pygame.K_a] or keys[pygame.K_d]

        if not self.skeleton_intro_triggered and moving and not game_state.whisper_jack_exploration_intro_done:
            screen_width = self.screen.get_width()
            spawn_x = self.camera_offset + screen_width - 200
            self.spawn_skeleton_intro(spawn_x, 400)
            self.skeleton_intro_triggered = True
            self.movement_locked = True

        if (game_state.first_battle_done
            and not self.skeleton_second_intro_triggered
            and moving
            and game_state.whisper_jack_exploration_intro_done):
            screen_width = self.screen.get_width()
            spawn_x = self.camera_offset + screen_width - 200
            self.spawn_skeleton_second_intro(spawn_x, 400)
            self.skeleton_second_intro_triggered = True
            self.movement_locked = True

        if now - self.last_update > self.hero_speed:
            if moving and self.hero_walk_frames:
                self.hero_walk_index = (self.hero_walk_index + 1) % len(self.hero_walk_frames)
            else:
                self.hero_index = (self.hero_index + 1) % len(self.hero_idle_frames)
            self.last_update = now

        if not self.movement_locked:
            if keys[pygame.K_d]:
                self.player.x += self.velocity
            if keys[pygame.K_a]:
                self.player.x -= self.velocity
            self.player.x = max(0, self.player.x)

        self.camera_offset = max(0, self.player.x - 250)

        for ghost in self.ghosts:
            if ghost.visible and abs(self.player.x - ghost.x) < 100:
                if not ghost.spawning and not ghost.spawn_complete:
                    ghost.spawning = True

            if ghost.spawning:
                if now - ghost.spawn_timer > ghost.spawn_speed:
                    ghost.spawn_index += 1
                    ghost.spawn_timer = now
                    if ghost.spawn_index >= len(ghost.spawn_frames):
                        ghost.spawning = False
                        ghost.spawn_complete = True
                        ghost.trigger_battle = True

        dt = now - self.last_update
        for anim in self.skeleton_animations:
            anim.update(dt)
        self.skeleton_animations = [a for a in self.skeleton_animations if a.active or not a.message_done]

        if self.skeleton_intro_triggered and not self.skeleton_intro_done:
            if all(a.message_done for a in self.skeleton_animations):
                self.skeleton_intro_done = True
                self.movement_locked = False
                game_state.whisper_jack_exploration_intro_done = True

        if self.skeleton_second_intro_triggered and not self.skeleton_second_intro_done:
            if all(a.message_done for a in self.skeleton_animations):
                self.skeleton_second_intro_done = True
                self.movement_locked = False
                game_state.whisper_jack_second_intro_done = True

    def check_battle_trigger(self):
        for ghost in self.ghosts:
            if ghost.visible and ghost.trigger_battle:
                return ghost
        return None

    def draw(self):
        start_x = -self.camera_offset % self.bg_width
        for i in range(3):
            self.screen.blit(self.bg_tile, (start_x + i * self.bg_width - self.bg_width, 0))

        keys = pygame.key.get_pressed()
        moving = keys[pygame.K_a] or keys[pygame.K_d]
        frame = (
            self.hero_walk_frames[self.hero_walk_index] if moving else self.hero_idle_frames[self.hero_index]
        )
        self.screen.blit(frame, (self.player.x - self.camera_offset, self.player.y))

        for ghost in self.ghosts:
            if ghost.visible:
                if ghost.spawning and ghost.spawn_index < len(ghost.spawn_frames):
                    spawn_frame = ghost.spawn_frames[ghost.spawn_index]
                    self.screen.blit(spawn_frame, (ghost.x - self.camera_offset, ghost.y))
                elif not ghost.spawn_complete and ghost.enemy_img:
                    self.screen.blit(ghost.enemy_img, (ghost.x - self.camera_offset, ghost.y))

        for anim in self.skeleton_animations:
            anim.draw(self.screen, self.camera_offset)

        self.player_hud.draw()

        if self.show_shop_button and not self.shop_modal.visible:
            pygame.draw.rect(self.screen, (80, 80, 200), self.shop_button_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), self.shop_button_rect, 2)
            label = self.font.render("Candy Shop", True, (255, 255, 255))
            self.screen.blit(label, (
                self.shop_button_rect.centerx - label.get_width() // 2,
                self.shop_button_rect.centery - label.get_height() // 2
            ))

        self.shop_modal.draw()
