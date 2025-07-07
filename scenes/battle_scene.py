import pygame
import os
from core.enemy import Enemy

class BattleScene:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player  # persistent player instance
        self.enemy = Enemy()

        # Force enemy to be a Ghost for this battle scene
        self.enemy.name = "Ghost"
        self.enemy.hp = self.enemy.max_hp
        self.enemy.xp = 50  # XP awarded for defeating ghost

        self.font = pygame.font.SysFont("consolas", 22)
        self.messages = ["👻 A ghostly presence appears!"]
        self.turn = "player"
        self.battle_over = False

        # Backgrounds
        self.backgrounds = self.load_backgrounds(os.path.join("assets", "images", "backgrounds"))
        self.bg_index = 0
        self.enemies_defeated = 0
        self.switch_every = 2  # Change background every 2 kills

        # Hero idle animation setup
        self.hero_idle_frames = self.load_idle_frames(os.path.join("assets", "images", "hero_idle"))
        self.hero_idle_index = 0

        # Ghost idle animation
        ghost_idle_path = os.path.join("assets", "images", "ghost_idle", "ghost_idle.png")
        if os.path.exists(ghost_idle_path):
            self.ghost_idle_frames = self.load_sprite_sheet(ghost_idle_path, frame_width=32, frame_height=32, scale=(150, 150))
        else:
            self.ghost_idle_frames = []
        self.ghost_idle_index = 0

        self.idle_speed = 200
        self.last_update_time = pygame.time.get_ticks()

    def load_idle_frames(self, folder_path, scale=(150, 150)):
        frames = []
        if not os.path.exists(folder_path):
            return frames
        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith(".png"):
                full_path = os.path.join(folder_path, filename)
                image = pygame.image.load(full_path).convert_alpha()
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

    def load_backgrounds(self, folder_path):
        backgrounds = []
        if not os.path.exists(folder_path):
            return backgrounds
        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith(".png"):
                path = os.path.join(folder_path, filename)
                image = pygame.image.load(path).convert()
                image = pygame.transform.scale(image, (800, 600))
                backgrounds.append(image)
        return backgrounds

    def log(self, text):
        self.messages.append(text)
        if len(self.messages) > 6:
            self.messages.pop(0)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and not self.battle_over:
            if self.turn == "player":
                if event.key == pygame.K_a:
                    dmg = self.player.attack()
                    self.enemy.hp -= dmg
                    self.log(f"You slash for {dmg}!")
                    self.turn = "enemy"
                elif event.key == pygame.K_h:
                    healed = self.player.heal()
                    if healed:
                        self.log(f"You healed {healed} HP.")
                    else:
                        self.log("No potions left!")
                    self.turn = "enemy"
                elif event.key == pygame.K_b:
                    self.player.block()
                    self.log("You brace for impact...")
                    self.turn = "enemy"
                elif event.key == pygame.K_i:
                    dmg = self.player.use_bomb()
                    if dmg:
                        self.enemy.hp -= dmg
                        self.log(f"You throw a bomb for {dmg}!")
                    else:
                        self.log("No bombs left!")
                    self.turn = "enemy"

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update_time > self.idle_speed:
            self.hero_idle_index = (self.hero_idle_index + 1) % len(self.hero_idle_frames)
            if self.ghost_idle_frames:
                self.ghost_idle_index = (self.ghost_idle_index + 1) % len(self.ghost_idle_frames)
            self.last_update_time = now

        # Battle outcome
        if self.enemy.hp <= 0 and not self.battle_over:
            self.log("🎉 The ghost vanishes!")
            xp_msgs = self.player.gain_xp(self.enemy.xp)
            for msg in xp_msgs:
                self.log(msg)

            self.enemies_defeated += 1
            if self.enemies_defeated % self.switch_every == 0:
                self.bg_index = (self.bg_index + 1) % len(self.backgrounds)
                self.log("🌄 The scenery changes...")

            self.battle_over = True

        if self.player.hp <= 0 and not self.battle_over:
            self.log("💀 You died...")
            self.battle_over = True

        if self.turn == "enemy" and not self.battle_over:
            dmg = self.enemy.attack()
            if self.player.blocking:
                dmg = dmg // 2
                self.player.blocking = False
                self.log("Blocked! Damage halved.")
            self.player.hp -= dmg
            self.log(f"The ghost hits for {dmg}!")
            self.turn = "player"

    def draw_bar(self, x, y, width, height, value, max_value, color):
        pygame.draw.rect(self.screen, (80, 80, 80), (x, y, width, height))
        fill = int(width * (value / max_value))
        pygame.draw.rect(self.screen, color, (x, y, fill, height))
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, width, height), 2)

    def draw(self):
        # Background
        if self.backgrounds:
            self.screen.blit(self.backgrounds[self.bg_index], (0, 0))
        else:
            self.screen.fill((20, 20, 20))

        # Health bars
        self.draw_bar(50, 30, 300, 20, self.player.hp, self.player.max_hp, (0, 200, 0))
        self.draw_bar(450, 30, 300, 20, self.enemy.hp, self.enemy.max_hp, (200, 0, 0))

        # Labels
        self.screen.blit(self.font.render(f"{self.player.name} - Lv {self.player.level}", True, (255, 255, 255)), (50, 5))
        self.screen.blit(self.font.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, (255, 255, 255)), (50, 55))
        self.screen.blit(self.font.render(f"XP: {self.player.xp}/{self.player.xp_to_next}", True, (255, 255, 255)), (50, 80))
        self.screen.blit(self.font.render(f"Potions: {self.player.inventory['potion']}, Bombs: {self.player.inventory['bomb']}", True, (200, 200, 200)), (50, 105))

        self.screen.blit(self.font.render(f"{self.enemy.name}", True, (255, 100, 100)), (450, 5))
        self.screen.blit(self.font.render(f"HP: {self.enemy.hp}/{self.enemy.max_hp}", True, (255, 255, 255)), (450, 55))

        # Hero
        current_hero_frame = self.hero_idle_frames[self.hero_idle_index]
        self.screen.blit(current_hero_frame, (100, 400))

        # Ghost
        if self.ghost_idle_frames:
            current_ghost_frame = self.ghost_idle_frames[self.ghost_idle_index]
            self.screen.blit(current_ghost_frame, (550, 400))

        # Log
        for i, msg in enumerate(self.messages):
            self.screen.blit(self.font.render(msg, True, (255, 255, 100)), (50, 160 + i * 30))

        if self.battle_over:
            self.screen.blit(self.font.render("Press Esc to quit", True, (180, 180, 180)), (50, 500))
        else:
            self.screen.blit(self.font.render("[A]ttack  [H]eal  [B]lock  [I]tem", True, (180, 180, 180)), (50, 550))
