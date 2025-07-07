import pygame
import os
import random
from core.player import Player

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
        self.player = player  # Persistent player from main.py
        self.font = pygame.font.SysFont("consolas", 22)

        # Background setup (must tile seamlessly)
        self.bg_tile = pygame.image.load(os.path.join("assets", "images", "backgrounds", "bg_0.png")).convert()
        self.bg_tile = pygame.transform.scale(self.bg_tile, (800, 600))
        self.bg_width = self.bg_tile.get_width()
        self.camera_offset = 0

        # Hero idle & walk animations
        self.hero_idle_frames = self.load_frames(os.path.join("assets", "images", "hero_idle"))
        self.hero_walk_frames = self.load_frames(os.path.join("assets", "images", "hero_walk"))
        self.hero_index = 0
        self.hero_walk_index = 0
        self.last_update = pygame.time.get_ticks()
        self.hero_speed = 200  # ms per frame

        # Hero position
        self.hero_x = 50
        self.hero_y = 400
        self.velocity = 5

        # Load ghost spawn animation frames once
        spawn_frames = self.load_sprite_sheet(
            os.path.join("assets", "images", "ghost_spawn", "ghost_spawn.png"),
            frame_width=32,
            frame_height=32,
            scale=(150, 150)
        )

        # Load fallback enemy idle image once
        fallback_path = os.path.join("assets", "images", "goblin.png")
        if os.path.exists(fallback_path):
            enemy_img = pygame.image.load(fallback_path).convert_alpha()
            enemy_img = pygame.transform.scale(enemy_img, (150, 150))
        else:
            enemy_img = None

        # Create multiple ghosts with doubled spacing
        ghost_positions = [800 * i for i in range(1, 11)]  # 800, 1600, ..., 8000
        self.ghosts = [
            Ghost(x, 400, spawn_frames, enemy_img)
            for x in ghost_positions
        ]

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

    def handle_event(self, event):
        pass

    def update(self, keys):
        now = pygame.time.get_ticks()
        moving = keys[pygame.K_a] or keys[pygame.K_d]

        if now - self.last_update > self.hero_speed:
            if moving and self.hero_walk_frames:
                self.hero_walk_index = (self.hero_walk_index + 1) % len(self.hero_walk_frames)
            else:
                self.hero_index = (self.hero_index + 1) % len(self.hero_idle_frames)
            self.last_update = now

        if keys[pygame.K_d]:
            self.hero_x += self.velocity
        if keys[pygame.K_a]:
            self.hero_x -= self.velocity
        self.hero_x = max(0, self.hero_x)

        # Update camera offset (centered on hero)
        self.camera_offset = max(0, self.hero_x - 250)

        # Update ghosts: trigger spawn and update animation
        for ghost in self.ghosts:
            if ghost.visible and abs(self.hero_x - ghost.x) < 100:
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

    def check_battle_trigger(self):
        for ghost in self.ghosts:
            if ghost.visible and ghost.trigger_battle:
                return ghost
        return None

    def draw(self):
        # Looping background based on camera offset
        start_x = -self.camera_offset % self.bg_width
        for i in range(3):
            self.screen.blit(self.bg_tile, (start_x + i * self.bg_width - self.bg_width, 0))

        # Hero sprite
        keys = pygame.key.get_pressed()
        moving = keys[pygame.K_a] or keys[pygame.K_d]
        frame = (
            self.hero_walk_frames[self.hero_walk_index] if moving else self.hero_idle_frames[self.hero_index]
        )
        self.screen.blit(frame, (self.hero_x - self.camera_offset, self.hero_y))

        # Draw all ghosts
        for ghost in self.ghosts:
            if ghost.visible:
                if ghost.spawning and ghost.spawn_index < len(ghost.spawn_frames):
                    spawn_frame = ghost.spawn_frames[ghost.spawn_index]
                    self.screen.blit(spawn_frame, (ghost.x - self.camera_offset, ghost.y))
                elif not ghost.spawn_complete and ghost.enemy_img:
                    self.screen.blit(ghost.enemy_img, (ghost.x - self.camera_offset, ghost.y))

        # UI text
        self.screen.blit(self.font.render("Explore with A/D (←/→)", True, (255, 255, 255)), (50, 20))
        self.screen.blit(self.font.render("Walk into a ghost to begin battle!", True, (255, 255, 100)), (50, 50))
