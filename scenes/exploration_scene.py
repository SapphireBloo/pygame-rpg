import math

import pygame

from core import game_state
from core.animation import AnimatedSprite, load_gameart2d_character
from core.assets import load_frames, load_sprite_sheet, load_background, tinted
from core.candy_shop_modal import CandyShopModal
from core.combat_text import CombatText
from core.grit import Grit
from core.levels import LEVELS
from core.player_hud import PlayerHUD
from core.portal import Portal
from core import sfx
from core.boss_encounter import BossEncounter
from core.roaming_zombie import RoamingZombie, GRAB_RANGE
from core.settings import (
    SCREEN_WIDTH, GROUND_Y, FEET_Y, WALK_SPEED, RUN_SPEED, SLIDE_SPEED, CAMERA_LEAD,
    GHOST_SPACING, GHOST_TRIGGER_RANGE, HERO_HEIGHT, CHARACTER_INK,
)
from core.skeleton_animation import SkeletonAnimation
from core.ui import get_font, draw_button, HEAL_GREEN, WHITE

GHOST_SPAWN_FRAME_MS = 80
JUMP_HEIGHT = 85           # pixels
BOSS_SCREEN_X = 590    # where a talking boss's feet sit on screen
HERO_HALF_WIDTH = 75       # player.x is the left edge of Charlie's old 150px box; feet are 75px in
CHARLIE = "Chin Check Charlie"

JACK_INTRO = [
    f"Well, well, well... look who we have here, {CHARLIE}.",
    "The shadows whisper my name... I'm Whisper Jack.",
    "I'm here to guide you, and maybe keep you on your toes.",
    "Use A and D to walk. Hold Shift to run, W to jump, S to slide.",
    "Slide right into a monster and you'll get the first punch in.",
    "And watch out for the candy... if you want me around.",
]

JACK_AFTER_FIRST_BATTLE = [
    f"Well, well... look who finally got some candy, {CHARLIE}!",
    "But you look beat up. Hitting 'H' might sweeten the deal.",
    "Don't make me come back just to patch you up again...",
    "Don't eat too much candy though... you'll need it for the Candy Shop.",
]


class Ghost:
    """A hidden ghost that materializes when the hero walks close, then starts a battle."""

    def __init__(self, x, spec):
        self.x = x
        self.y = GROUND_Y
        self.spec = spec          # enemy stats handed to the battle
        self.first_strike = False # Charlie slid into it
        self.spawning = False
        self.spawn_index = 0
        self.spawn_timer = 0
        self.defeated = False
        self.ready_for_battle = False

    def update(self, dt, hero_x, frame_count, sliding=False):
        if self.defeated or self.ready_for_battle:
            return
        if not self.spawning and abs(hero_x - self.x) < GHOST_TRIGGER_RANGE:
            self.spawning = True
            self.first_strike = sliding
        if self.spawning:
            self.spawn_timer += dt
            if self.spawn_timer >= GHOST_SPAWN_FRAME_MS:
                self.spawn_timer = 0
                self.spawn_index += 1
                if self.spawn_index >= frame_count:
                    self.spawning = False
                    self.ready_for_battle = True


class ExplorationScene:
    def __init__(self, screen, player, level_index=0):
        self.screen = screen
        self.player = player
        self.font = get_font(22)
        self.small_font = get_font(16)

        self.hero = AnimatedSprite(load_gameart2d_character("charlie", HERO_HEIGHT, ink=CHARACTER_INK))
        self.is_walking = False
        self.facing_right = True
        self.action = None         # "jump" or "slide" while one is playing
        self.action_time = 0
        self.grit = Grit(screen.get_size())

        self.skeleton_frames = load_frames("Skeleton", flip_x=True)
        self.floating_texts = []   # screen-positioned (heal numbers over Charlie)
        self.world_texts = []      # world-positioned (zombie groans), scroll with the camera
        self.player_hud = PlayerHUD(screen, player)
        self.shop = CandyShopModal(screen, player)
        self.shop_button = pygame.Rect(650, 10, 145, 40)

        self.finished = False   # True after the last level's exit (free roam)
        self.load_level(level_index)

    # ---- levels --------------------------------------------------------
    @property
    def is_last_level(self):
        return self.level_index == len(LEVELS) - 1

    def load_level(self, index):
        """Reset the world for LEVELS[index]. Charlie keeps HP, candy, and upgrades."""
        self.level_index = index
        self.level = LEVELS[index]
        self.background = load_background(self.level["background"])
        self.grit.set_level(self.level)
        self.ghost_spawn_frames = tinted(load_sprite_sheet("ghost_spawn/ghost_spawn.png", 32, 32),
                                         self.level.get("ghost_tint"))

        count = self.level["ghosts"]
        ghost_spec = {"sprite": "ghost", **self.level["enemy"]}
        self.ghosts = [Ghost(GHOST_SPACING * i, ghost_spec) for i in range(1, count + 1)]
        zombie_specs = self.level.get("zombies", [])
        self.zombies = [RoamingZombie(GHOST_SPACING * (count + i), spec)
                        for i, spec in enumerate(zombie_specs, start=1)]
        boss_spec = self.level.get("boss")
        boss_x = GHOST_SPACING * (count + len(zombie_specs) + 1)
        self.boss = BossEncounter(boss_x, boss_spec) if boss_spec else None
        self.exit_x = boss_x + 600 if self.boss else boss_x
        next_name = "???" if self.is_last_level else LEVELS[index + 1]["name"]
        self.portal = Portal(self.exit_x, GROUND_Y, self.level["accent"], f"{next_name} >")
        self.exit_reached = False   # main.py starts the transition when this flips

        self.player.x = 50.0
        self.camera_offset = 0
        self.boss_pan = 0.0        # extra camera slide so a talking boss is fully on screen
        self.floating_texts.clear()
        self.world_texts.clear()
        self.facing_right = True
        self.action = None
        self.hero.lift = 0
        self.whisper_jack = None    # the active cutscene, if any
        self.on_jack_done = None    # callback run when he finishes talking
        if self.level["arrival"]:
            self._start_jack(self.level["arrival"], None)

    def finish(self):
        """Called after the ending card: the portal goes away and you can roam."""
        self.finished = True
        self.portal = None
        self.exit_reached = False

    # ---- Whisper Jack cutscenes ----------------------------------------
    @property
    def movement_locked(self):
        jack_talking = self.whisper_jack is not None and not self.whisper_jack.message_done
        grabbed = any(z.grabbing for z in self.zombies) or bool(self.boss and self.boss.grabbing)
        return jack_talking or grabbed

    def _start_jack(self, messages, on_done):
        spawn_x = self.camera_offset + SCREEN_WIDTH - 200
        self.whisper_jack = SkeletonAnimation(spawn_x, GROUND_Y, self.skeleton_frames, messages)
        self.on_jack_done = on_done

    def _check_cutscenes(self, trying_to_move):
        # A Jack who's finished talking (even if still sinking) can be replaced
        if not trying_to_move or (self.whisper_jack and not self.whisper_jack.message_done):
            return
        if not game_state.whisper_jack_exploration_intro_done:
            self._start_jack(JACK_INTRO, self._intro_finished)
        elif game_state.first_battle_done and not game_state.whisper_jack_second_intro_done:
            self._start_jack(JACK_AFTER_FIRST_BATTLE, self._second_intro_finished)

    @staticmethod
    def _intro_finished():
        game_state.whisper_jack_exploration_intro_done = True

    @staticmethod
    def _second_intro_finished():
        game_state.whisper_jack_second_intro_done = True

    # ---- input ---------------------------------------------------------
    def handle_event(self, event):
        if self.shop.visible:
            self.shop.handle_event(event)
            return

        if self.whisper_jack:
            self.whisper_jack.handle_event(event)
        if self.boss:
            self.boss.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.shop_button.collidepoint(event.pos):
            self.shop.open()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:
                self._eat_candy()
            elif event.key in (pygame.K_w, pygame.K_UP):
                self._start_action("jump")
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self._start_action("slide")

    def _start_action(self, name):
        if self.action or self.movement_locked or not self.hero.has(name):
            return
        self.action = name
        self.action_time = 0
        self.hero.play(name, restart=True)
        sfx.play(name)

    @property
    def sliding(self):
        return self.action == "slide"

    @property
    def hero_feet_x(self):
        return self.player.x + HERO_HALF_WIDTH

    def _eat_candy(self):
        hero_x = self.hero_feet_x - self.camera_offset - 35
        if self.player.hp >= self.player.max_hp:
            text, color = "Already full HP", (255, 230, 120)
        else:
            healed = self.player.heal()
            text, color = (f"+{healed} HP", HEAL_GREEN) if healed else ("No candy!", (255, 230, 120))
        self.floating_texts.append(CombatText(text, hero_x, self.player.y - 20, color))

    # ---- update --------------------------------------------------------
    def update(self, keys, dt):
        self.player_hud.update(dt)
        for text in self.floating_texts + self.world_texts:
            text.update(dt)
        self.floating_texts = [t for t in self.floating_texts if t.is_alive()]
        self.world_texts = [t for t in self.world_texts if t.is_alive()]

        self.grit.update(dt)
        if self.shop.visible:
            self.shop.update(dt)
            self.is_walking = False
            return

        # Update Jack first so a finished talk marks its story flag before we
        # decide whether another cutscene should start.
        if self.whisper_jack:
            self.whisper_jack.update(dt)
            if self.whisper_jack.message_done and self.on_jack_done:
                self.on_jack_done()
                self.on_jack_done = None
            if not self.whisper_jack.active:
                self.whisper_jack = None

        direction = int(bool(keys[pygame.K_d] or keys[pygame.K_RIGHT])) - int(bool(keys[pygame.K_a] or keys[pygame.K_LEFT]))
        self._check_cutscenes(direction != 0)

        running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        self.is_walking = direction != 0 and not self.movement_locked
        if self.sliding:
            # Slides carry Charlie forward fast, slowing toward the end
            t = min(1.0, self.action_time / self.hero.current.duration)
            step = (1 if self.facing_right else -1) * SLIDE_SPEED * (1 - 0.6 * t) * dt / 1000
            self.player.x = max(0.0, self.player.x + step)
        elif self.is_walking:
            self.facing_right = direction > 0
            speed = RUN_SPEED if running else WALK_SPEED
            self.player.x = max(0.0, self.player.x + direction * speed * dt / 1000)
        self.camera_offset = max(0, int(self.player.x) - CAMERA_LEAD)
        self._frame_boss(dt)

        self._animate_hero(dt, running)

        for ghost in self.ghosts:
            ghost.update(dt, self.player.x, len(self.ghost_spawn_frames), self.sliding)

        hero_center = self.hero_feet_x
        if self.boss:
            self.boss.update(dt, hero_center)
            if not self.boss.defeated:      # can't walk through the boss
                self.player.x = min(self.player.x, self.boss.x - HERO_HALF_WIDTH - 140)
        for zombie in self.zombies:
            if self.sliding and not zombie.defeated and not zombie.grabbing and \
                    abs(zombie.x - hero_center) < GRAB_RANGE:
                zombie.first_strike = True            # slid right into it: Charlie hits first
                zombie.ready_for_battle = True
            groan = zombie.update(dt, hero_center)
            on_screen = 0 < zombie.x - self.camera_offset < SCREEN_WIDTH
            if groan and on_screen:
                sfx.play("zombie_groan", 0.5)
                self.world_texts.append(CombatText(groan, zombie.x - 45, FEET_Y - 170, (150, 210, 150),
                                                   lifespan=2200, size=18))

        if self.portal:
            self.portal.update(dt)
            self.player.x = min(self.player.x, self.exit_x)   # can't walk past the portal
            cleared = all(f.defeated for f in self._foes())
            if cleared and self.player.x >= self.exit_x - 40 and not self.movement_locked:
                if not self.exit_reached:
                    sfx.play("portal")
                self.exit_reached = True

    def _animate_hero(self, dt, running):
        if self.action:
            self.action_time += dt
            duration = self.hero.current.duration
            if self.action == "jump":
                self.hero.lift = JUMP_HEIGHT * math.sin(math.pi * min(1.0, self.action_time / duration))
            if self.action_time >= duration:
                self.action = None
                self.hero.lift = 0
        if not self.action:
            if self.is_walking:
                self.hero.play("run" if running and self.hero.has("run") else "walk")
            else:
                self.hero.play("idle")
        self.hero.update(dt)

    def take_battle_trigger(self):
        """Return the enemy spec of a ghost/zombie that's ready to fight (and
        mark it used), else None. Adds "first_strike" if Charlie slid into it."""
        for foe in self._foes():
            if foe.ready_for_battle and not foe.defeated:
                foe.defeated = True
                foe.ready_for_battle = False
                self.action = None
                self.hero.lift = 0
                spec = dict(foe.spec)
                if getattr(foe, "first_strike", False):
                    spec["first_strike"] = True
                return spec
        return None

    def _frame_boss(self, dt):
        """While the boss talks, glide the camera so he stands fully on screen."""
        want = 0.0
        if self.boss and self.boss.grabbing:
            want = max(0.0, self.boss.x - BOSS_SCREEN_X - self.camera_offset)
        self.boss_pan += (want - self.boss_pan) * min(1.0, dt / 180)
        self.camera_offset += int(self.boss_pan)

    def _foes(self):
        return self.ghosts + self.zombies + ([self.boss] if self.boss else [])

    # ---- drawing -------------------------------------------------------
    def draw(self):
        self._draw_background()
        if self.portal:
            self.portal.draw(self.screen, self.camera_offset)

        for zombie in self.zombies:
            if not zombie.defeated:
                self.grit.draw_shadow(self.screen, zombie.x - self.camera_offset, FEET_Y)
            zombie.draw(self.screen, self.camera_offset, FEET_Y)
        if self.boss and not self.boss.defeated:
            self.grit.draw_shadow(self.screen, self.boss.x - self.camera_offset, FEET_Y, self.boss.shadow_size)
            self.boss.draw(self.screen, self.camera_offset, FEET_Y)

        hero_x = self.hero_feet_x - self.camera_offset
        self.grit.draw_shadow(self.screen, hero_x, FEET_Y, 0.9 - min(0.4, self.hero.lift / 250))
        self.hero.draw(self.screen, hero_x, FEET_Y, self.facing_right)

        for ghost in self.ghosts:
            if ghost.spawning and ghost.spawn_index < len(self.ghost_spawn_frames):
                self.screen.blit(self.ghost_spawn_frames[ghost.spawn_index],
                                 (ghost.x - self.camera_offset, ghost.y))

        self.grit.draw_fog(self.screen, self.camera_offset)
        self.grit.apply(self.screen)   # everything above is "world"; below stays crisp

        if self.whisper_jack:
            self.whisper_jack.draw(self.screen, self.camera_offset)
        if self.boss:
            self.boss.draw_bubble(self.screen, self.camera_offset, FEET_Y)

        for text in self.floating_texts:
            text.draw(self.screen)
        for text in self.world_texts:
            text.draw(self.screen, self.camera_offset)

        self.player_hud.draw()
        label = self.small_font.render(f"Ch. {self.level_index + 1}: {self.level['name']}", True, (230, 230, 230))
        self.screen.blit(label, (self.shop_button.right - label.get_width(), self.shop_button.bottom + 8))
        if not self.shop.visible:
            draw_button(self.screen, self.shop_button, "Candy Shop", self.font, (80, 80, 200), text_color=WHITE)
        self.shop.draw()

    def _draw_background(self):
        if not self.background:
            self.screen.fill((15, 10, 25))
            return
        width = self.background.get_width()
        x = -(self.camera_offset % width)
        self.screen.blit(self.background, (x, 0))
        self.screen.blit(self.background, (x + width, 0))
