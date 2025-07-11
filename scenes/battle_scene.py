import pygame
import os
import random
from core.enemy import Enemy
from core.combat_text import CombatText
from core.combat_options import CombatOptions
from core.skeleton_animation import SkeletonAnimation
from core.player_hud import PlayerHUD
from core.enemy_hud import EnemyHUD
from core.end_combat_modal import EndCombatModal
from core import game_state

class BattleScene:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.enemy = Enemy()

        self.enemy.name = "Ghost"
        self.enemy.hp = self.enemy.max_hp

        self.font = pygame.font.SysFont("consolas", 22)
        self.battle_over = False
        self.ready_to_exit = False  # Flag for main.py to exit battle

        self.auto_block_used = False
        self.resurrect_used = False

        if self.player.upgrades.get("auto_block"):
            self.player.blocking = True
            self.auto_block_used = True

        self.show_whisper_jack_intro = not game_state.whisper_jack_combat_intro_done
        self.turn_state = "intro" if self.show_whisper_jack_intro else "player_turn"

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
        self.end_modal = EndCombatModal(self.screen, 0)

        if self.show_whisper_jack_intro:
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
        else:
            self.whisper_jack = None

        self.intro_done = not self.show_whisper_jack_intro

        self.player_hud = PlayerHUD(screen, self.font, self.player)
        self.enemy_hud = EnemyHUD(screen, self.font, self.enemy)

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

    def handle_event(self, event):
        if self.end_modal.visible:
            if self.end_modal.handle_event(event):
                self.ready_to_exit = True
            return

        if self.show_whisper_jack_intro and self.turn_state == "intro":
            self.whisper_jack.handle_event(event)
            return

        if event.type == pygame.KEYDOWN and not self.battle_over and self.turn_state == "player_turn":
            if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                self.combat_options.handle_event(event)
            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                self.combat_options.handle_event(event)
                choice = self.combat_options.get_selected()
                if choice is not None:
                    offset_x = random.randint(-10, 10)
                    offset_y = random.randint(-10, 10)

                    if choice == "Attack":
                        dmg = self.player.attack()
                        self.enemy.hp -= dmg
                        self.combat_texts.append(CombatText(f"-{dmg}", 575 + offset_x, 380 + offset_y, (255, 80, 80)))
                        self.start_delay("enemy_turn")

                    elif choice == "Heal":
                        heal_amount = self.player.heal()
                        if heal_amount > 0:
                            self.combat_texts.append(CombatText(f"+{heal_amount}", 125 + offset_x, 380 + offset_y, (100, 255, 100)))
                            self.start_delay("enemy_turn")


                    elif choice == "Block":
                        self.player.block()
                        self.combat_texts.append(CombatText("Block!", 125 + offset_x, 380 + offset_y, (150, 200, 255)))
                        self.start_delay("enemy_turn")

                    elif choice == "Item":
                        dmg = self.player.use_bomb()
                        if dmg:
                            if self.player.upgrades.get("bomb_power_plus_10"):
                                dmg += 10
                            self.enemy.hp -= dmg
                            self.combat_texts.append(CombatText(f"-{dmg}", 575 + offset_x, 380 + offset_y, (255, 100, 100)))
                        self.start_delay("enemy_turn")

                    self.combat_options.reset_selection()

    def start_delay(self, next_state):
        self.turn_state = "delay"
        self.delay_start = pygame.time.get_ticks()
        self.next_turn = next_state

    def update(self, dt):
        now = pygame.time.get_ticks()

        if self.show_whisper_jack_intro and not self.intro_done:
            self.whisper_jack.update(dt)
            if self.whisper_jack.message_done and not self.whisper_jack.fading_out:
                self.whisper_jack.fading_out = True
            elif not self.whisper_jack.active:
                self.intro_done = True
                self.turn_state = "player_turn"
                game_state.whisper_jack_combat_intro_done = True
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
            base_candy = random.randint(1, 3)
            if self.player.upgrades.get("double_candy"):
                base_candy *= 2
            self.player.candy += base_candy
            self.player.last_candy_reward = base_candy
            self.ghost_death_animating = True
            self.ghost_death_index = 0
            return

        if self.ghost_death_animating:
            if self.ghost_death_index >= len(self.ghost_spawn_frames):
                self.enemies_defeated += 1
                if self.enemies_defeated % self.switch_every == 0:
                    self.bg_index = (self.bg_index + 1) % len(self.backgrounds)
                game_state.first_battle_done = True
                if not self.end_modal.visible:
                    self.end_modal.open(self.player.last_candy_reward)
                self.battle_over = True
                self.ghost_death_animating = False
            return

        if self.player.hp <= 0 and not self.battle_over:
            if self.player.upgrades.get("resurrect_once") and not self.resurrect_used:
                self.player.hp = self.player.max_hp // 2
                self.resurrect_used = True
                self.combat_texts.append(CombatText("Resurrected!", 125, 340, (255, 255, 100)))
            else:
                self.battle_over = True

        if self.turn_state == "enemy_turn" and not self.battle_over and not self.ghost_death_animating:
            dmg = self.enemy.attack()
            if self.player.blocking:
                dmg //= 2
                self.player.blocking = False
                self.combat_texts.append(CombatText("Blocked!", 125, 380, (200, 200, 255)))
            self.player.hp -= dmg
            self.combat_texts.append(CombatText(f"-{dmg}", 125, 380, (255, 80, 80)))
            self.start_delay("player_turn")

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

        self.player_hud.draw()
        self.enemy_hud.draw()

        for text in self.combat_texts:
            text.draw(self.screen)

        if self.show_whisper_jack_intro and not self.intro_done:
            self.whisper_jack.draw(self.screen, camera_offset=0)

        if self.turn_state == "player_turn" and not self.battle_over and not self.end_modal.visible:
            self.combat_options.draw()

        self.end_modal.draw()
