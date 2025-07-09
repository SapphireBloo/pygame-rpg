import pygame
import os
import random
from core.enemy import Enemy
from core.combat_text import CombatText
from core.combat_options import CombatOptions
from core.skeleton_animation import SkeletonAnimation

class BattleScene:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.enemy = Enemy()

        self.enemy.name = "Ghost"
        self.enemy.hp = self.enemy.max_hp
        self.enemy.xp = 50

        self.font = pygame.font.SysFont("consolas", 22)
        self.messages = ["A ghostly presence materializes..."]
        self.battle_over = False

        self.turn_state = "intro"  # Start with intro
        self.delay_start = 0
        self.delay_duration = 600

        self.backgrounds = self.load_backgrounds(os.path.join("assets", "images", "backgrounds"))
        self.bg_index = 0
        self.enemies_defeated = 0
        self.switch_every = 2

        self.hero_idle_frames = self.load_idle_frames(os.path.join("assets", "images", "hero_idle"))
        self.hero_idle_index = 0

        ghost_idle_path = os.path.join("assets", "images", "ghost_idle", "ghost_idle.png")
        self.ghost_idle_frames = self.load_sprite_sheet(ghost_idle_path, 32, 32, (150, 150)) if os.path.exists(ghost_idle_path) else []
        self.ghost_idle_index = 0

        self.ghost_spawn_frames = self.load_sprite_sheet(
            os.path.join("assets", "images", "ghost_spawn", "ghost_spawn.png"),
            32, 32, (150, 150))
        self.ghost_death_index = 0
        self.ghost_death_animating = False

        self.idle_speed = 250
        self.last_update_time = pygame.time.get_ticks()

        self.displayed_player_hp = self.player.hp
        self.displayed_enemy_hp = self.enemy.hp
        self.hp_change_speed = 1.5

        self.combat_texts = []
        self.combat_options = CombatOptions(self.screen)

        # Whisper Jack intro
        jack_frames_path = os.path.join("assets", "images", "Skeleton")
        jack_frames = self.load_idle_frames(jack_frames_path)
        jack_frames = [pygame.transform.flip(frame, True, False) for frame in jack_frames]
        jack_msgs = [
            "Combat time!",
            "Use ← and → to choose.",
            "Press Space or Enter to select.",
            "Think fast. The dead don't wait."
        ]
        self.whisper_jack = SkeletonAnimation(330, 400, jack_frames, jack_msgs)
        self.intro_done = False

    def load_idle_frames(self, folder_path, scale=(150, 150)):
        return [
            pygame.transform.scale(
                pygame.image.load(os.path.join(folder_path, filename)).convert_alpha(), scale
            ) for filename in sorted(os.listdir(folder_path)) if filename.endswith(".png")
        ]

    def load_sprite_sheet(self, path, frame_width, frame_height, scale=(150, 150)):
        sheet = pygame.image.load(path).convert_alpha()
        sheet_width, _ = sheet.get_size()
        return [
            pygame.transform.scale(
                sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)),
                scale
            ) for i in range(sheet_width // frame_width)
        ]

    def load_backgrounds(self, folder_path):
        return [
            pygame.transform.scale(pygame.image.load(os.path.join(folder_path, filename)).convert(), (800, 600))
            for filename in sorted(os.listdir(folder_path)) if filename.endswith(".png")
        ] if os.path.exists(folder_path) else []

    def log(self, message):
        self.messages.append(message)
        if len(self.messages) > 6:
            self.messages.pop(0)

    def handle_event(self, event):
        if self.turn_state == "intro":
            self.whisper_jack.handle_event(event)
            return

        if event.type == pygame.KEYDOWN and not self.battle_over and self.turn_state == "player_turn":
            if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                self.combat_options.handle_event(event)
            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                self.combat_options.handle_event(event)  # Marks selection made

                choice = self.combat_options.get_selected()
                if choice is not None:
                    offset_x = random.randint(-10, 10)
                    offset_y = random.randint(-10, 10)

                    if choice == "Attack":
                        dmg = self.player.attack()
                        self.enemy.hp -= dmg
                        self.log(f"Charlie punches for {dmg}!")
                        self.combat_texts.append(CombatText(f"-{dmg}", 575 + offset_x, 380 + offset_y, (255, 80, 80)))
                        self.start_delay("enemy_turn")

                    elif choice == "Heal":
                        healed = self.player.heal()
                        if healed:
                            self.log(f"Charlie drinks a potion (+{healed} HP).")
                            self.combat_texts.append(CombatText(f"+{healed}", 125 + offset_x, 380 + offset_y, (100, 255, 100)))
                        else:
                            self.log("No potions left!")
                        self.start_delay("enemy_turn")

                    elif choice == "Block":
                        self.player.block()
                        self.log("Charlie braces for impact...")
                        self.combat_texts.append(CombatText("Block!", 125 + offset_x, 380 + offset_y, (150, 200, 255)))
                        self.start_delay("enemy_turn")

                    elif choice == "Item":
                        dmg = self.player.use_bomb()
                        if dmg:
                            self.enemy.hp -= dmg
                            self.log(f"Charlie hurls a bomb for {dmg}!")
                            self.combat_texts.append(CombatText(f"-{dmg}", 575 + offset_x, 380 + offset_y, (255, 100, 100)))
                        else:
                            self.log("No bombs left!")
                        self.start_delay("enemy_turn")

                    # Reset selection for next turn
                    self.combat_options.reset_selection()

    def start_delay(self, next_state):
        self.turn_state = "delay"
        self.delay_start = pygame.time.get_ticks()
        self.next_turn = next_state

    def update(self, dt):
        now = pygame.time.get_ticks()

        if not self.intro_done:
            self.whisper_jack.update(dt)
            if self.whisper_jack.message_done and not self.whisper_jack.fading_out:
                self.whisper_jack.fading_out = True
            elif not self.whisper_jack.active:
                self.intro_done = True
                self.turn_state = "player_turn"
            return

        if now - self.last_update_time > self.idle_speed:
            self.hero_idle_index = (self.hero_idle_index + 1) % len(self.hero_idle_frames)
            if self.ghost_idle_frames:
                self.ghost_idle_index = (self.ghost_idle_index + 1) % len(self.ghost_idle_frames)
            if self.ghost_death_animating:
                self.ghost_death_index += 1
            self.last_update_time = now

        self.displayed_player_hp += (self.player.hp - self.displayed_player_hp) * self.hp_change_speed * 0.1
        self.displayed_enemy_hp += (self.enemy.hp - self.displayed_enemy_hp) * self.hp_change_speed * 0.1

        for text in self.combat_texts:
            text.update(dt)
        self.combat_texts = [t for t in self.combat_texts if t.is_alive()]

        if self.turn_state == "delay" and now - self.delay_start > self.delay_duration:
            self.turn_state = self.next_turn

        if self.enemy.hp <= 0 and not self.battle_over and not self.ghost_death_animating:
            self.log("The ghost dissipates into mist...")
            for msg in self.player.gain_xp(self.enemy.xp):
                self.log(msg)
            self.ghost_death_animating = True
            self.ghost_death_index = 0
            return

        if self.ghost_death_animating:
            if self.ghost_death_index >= len(self.ghost_spawn_frames):
                self.enemies_defeated += 1
                if self.enemies_defeated % self.switch_every == 0:
                    self.bg_index = (self.bg_index + 1) % len(self.backgrounds)
                    self.log("The scene darkens...")
                self.battle_over = True
                self.ghost_death_animating = False

        if self.player.hp <= 0 and not self.battle_over:
            self.log("Charlie collapses... Game over.")
            self.battle_over = True

        if self.turn_state == "enemy_turn" and not self.battle_over and not self.ghost_death_animating:
            dmg = self.enemy.attack()
            if self.player.blocking:
                dmg //= 2
                self.player.blocking = False
                self.log("Blocked! Damage halved.")
                self.combat_texts.append(CombatText("Blocked!", 125, 380, (200, 200, 255)))
            self.player.hp -= dmg
            self.log(f"The ghost claws for {dmg}!")
            self.combat_texts.append(CombatText(f"-{dmg}", 125, 380, (255, 80, 80)))
            self.start_delay("player_turn")

    def draw_bar(self, x, y, width, height, value, max_value, color):
        pygame.draw.rect(self.screen, (60, 60, 60), (x, y, width, height))
        fill = int(width * (value / max_value))
        pygame.draw.rect(self.screen, color, (x, y, fill, height))
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, width, height), 2)

    def draw(self):
        if self.backgrounds:
            self.screen.blit(self.backgrounds[self.bg_index], (0, 0))
        else:
            self.screen.fill((10, 10, 10))

        self.screen.blit(self.hero_idle_frames[self.hero_idle_index], (100, 400))

        if self.ghost_death_animating and self.ghost_death_index < len(self.ghost_spawn_frames):
            frame = self.ghost_spawn_frames[::-1][self.ghost_death_index]
            self.screen.blit(frame, (550, 400))
        elif self.ghost_idle_frames and not self.battle_over:
            self.screen.blit(self.ghost_idle_frames[self.ghost_idle_index], (550, 400))

        self.draw_bar(50, 30, 300, 20, int(self.displayed_player_hp), self.player.max_hp, (0, 200, 0))
        self.draw_bar(450, 30, 300, 20, int(self.displayed_enemy_hp), self.enemy.max_hp, (200, 0, 0))

        self.screen.blit(self.font.render(f"{self.player.name} - Lv {self.player.level}", True, (255, 255, 255)), (50, 5))
        self.screen.blit(self.font.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, (255, 255, 255)), (50, 55))
        self.screen.blit(self.font.render(f"XP: {self.player.xp}/{self.player.xp_to_next}", True, (200, 200, 200)), (50, 80))
        self.screen.blit(self.font.render(f"Potions: {self.player.inventory['potion']}  Bombs: {self.player.inventory['bomb']}", True, (200, 200, 200)), (50, 105))

        self.screen.blit(self.font.render(self.enemy.name, True, (255, 100, 100)), (450, 5))
        self.screen.blit(self.font.render(f"HP: {self.enemy.hp}/{self.enemy.max_hp}", True, (255, 255, 255)), (450, 55))

        for text in self.combat_texts:
            text.draw(self.screen)

        if not self.intro_done:
            self.whisper_jack.draw(self.screen, camera_offset=0)

        if self.battle_over:
            self.screen.blit(self.font.render("Press Esc to return", True, (180, 180, 180)), (50, 500))
        elif self.turn_state == "player_turn":
            self.combat_options.draw()
