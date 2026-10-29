import math

import pygame

from core import game_state
from core.animation import AnimatedSprite, load_gameart2d_character
from core.assets import load_frames, load_background
from core.camp import ParallaxBackground, Blacksmith, Crow, CAMP_LENGTH, BLACKSMITH_X, CROW_HOME_X
from core.camp_shops import BlacksmithShop, CrowShop, BagMenu
from core.combat_text import CombatText
from core import save_game
from core.icons import icon
from core.grit import Grit
from core.levels import LEVELS
from core.player_hud import PlayerHUD
from core.portal import Portal
from core import sfx
from core.boss_encounter import BossEncounter
from core.roaming_enemy import RoamingEnemy
from core.settings import (
    SCREEN_WIDTH, GROUND_Y, FEET_Y, WALK_SPEED, RUN_SPEED, SLIDE_SPEED, CAMERA_LEAD,
    MONSTER_SPACING, HERO_HEIGHT, CHARACTER_INK,
)
from core.skeleton_animation import SkeletonAnimation
from core.ui import get_font, HEAL_GREEN

JUMP_HEIGHT = 85           # pixels
BOSS_SCREEN_X = SCREEN_WIDTH - 230    # where a talking boss's feet sit on screen
SAVE_TOAST_MS = 2500       # how long "Game saved" shows after reaching camp
AILMENT_TICK_MS = 5000     # out in the levels, infection/burning nibble HP this often (never below 1)
JACK_WANDER_OFF = 450      # walk this far from a finished Whisper Jack and he leaves
HERO_HALF_WIDTH = 75       # player.x is the left edge of Charlie's old 150px box; feet are 75px in
CHARLIE = "Chin Check Charlie"

JACK_INTRO = [
    f"Well, well, well... look who we have here, {CHARLIE}.",
    "The shadows whisper my name... I'm Whisper Jack.",
    "I'm here to guide you, and maybe keep you on your toes.",
    "Use A and D to walk. Hold Shift to run, Space to jump, S to slide.",
    "Slide right into a monster and you'll get the first punch in.",
    "And watch out for the candy... if you want me around.",
]

JACK_FIRST_CAMP = [
    "Phew. A camp. Nothing out here is trying to bite you. For once.",
    "Camp's safe, but it won't patch you up. Need HP? The Crow sells Gourd-Aid.",
    "Still infected or on fire? That doesn't wear off. Grab a Remedy.",
    "That's the Blacksmith. Bring him candy and he'll make you tougher. For good.",
    "And the beaky fella is the Crow. Potions, bombs... and he BUYS the junk monsters drop.",
    "Don't ask what he does with zombie teeth. I didn't.",
    "Walk up and press E to talk to 'em. Press I any time to check your bag.",
]

JACK_LAST_CAMP = [
    "You actually did it, kid. Malgorath's done. The graveyard's quiet.",
    "Rest up. Spend that candy. Then... well. Let's see what's past that portal.",
]

JACK_AFTER_FIRST_BATTLE = [
    f"Well, well... look who finally got some candy, {CHARLIE}!",
    "But you look beat up. Press 'H' to chug a Gourd-Aid. Pumpkin-flavored. Obviously.",
    "Don't make me come back just to patch you up again...",
    "Save that candy, though. You'll want it at camp after the big fight.",
]


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
        self.world_texts = []      # world-positioned (monster chatter), scroll with the camera
        self.player_hud = PlayerHUD(screen, player)
        self.bag = BagMenu(screen, player)        # I: what Charlie's carrying (works anywhere)
        self.blacksmith_shop = None               # camp menus, made when a camp loads
        self.crow_shop = None
        self.parallax = None                      # camp background (loaded the first time)
        self.in_camp = False
        self.npcs = []

        self.finished = False   # True after the last level's exit (the ending plays)
        self.save_toast = 0     # ms left on the "Game saved" note
        self.load_level(level_index)

    # ---- levels --------------------------------------------------------
    @property
    def is_last_level(self):
        return self.level_index == len(LEVELS) - 1

    def load_level(self, index):
        """Reset the world for LEVELS[index]. Charlie keeps HP, candy, and upgrades."""
        self.level_index = index
        self.level = LEVELS[index]
        self.in_camp = False
        self.player.new_chapter()        # Second Wind II recharges each chapter
        self.npcs = []
        self.background = load_background(self.level["background"])
        self.grit.set_level(self.level)

        # Monsters roam spots spread along the level, then the boss waits at the end
        specs = self.level.get("monsters", [])
        self.monsters = [RoamingEnemy(MONSTER_SPACING * i, spec, self.level.get("ghost_tint"))
                         for i, spec in enumerate(specs, start=1)]
        boss_spec = self.level.get("boss")
        boss_x = MONSTER_SPACING * (len(specs) + 1)
        self.boss = BossEncounter(boss_x, boss_spec) if boss_spec else None
        self.exit_x = boss_x + 600 if self.boss else boss_x
        self.portal = Portal(self.exit_x, GROUND_Y, self.level["accent"], "Camp >")
        self._reset_world()
        if self.level["arrival"]:
            self._start_jack(self.level["arrival"], None)

    def load_camp(self):
        """The safe camp after this chapter's boss: shops, no monsters."""
        self.in_camp = True
        self.background = None
        if self.parallax is None:
            self.parallax = ParallaxBackground()
        self.grit.set_level({"background": "camp", "accent": (255, 170, 90)})
        self.monsters = []
        self.boss = None
        self.blacksmith = Blacksmith(BLACKSMITH_X)
        self.crow = Crow(CROW_HOME_X)
        self.npcs = [self.blacksmith, self.crow]
        self.blacksmith_shop = BlacksmithShop(self.screen, self.player, self.blacksmith.portrait())
        self.crow_shop = CrowShop(self.screen, self.player, self.crow.portrait())
        self.exit_x = CAMP_LENGTH
        label = "The End >" if self.is_last_level else f"{LEVELS[self.level_index + 1]['name']} >"
        self.portal = Portal(self.exit_x, GROUND_Y, (255, 170, 90), label)
        self._reset_world()
        if self.is_last_level:
            self._start_jack(JACK_LAST_CAMP, None)
        elif not game_state.first_camp_done:
            self._start_jack(JACK_FIRST_CAMP, None)
            game_state.first_camp_done = True     # (counted as heard, so Continue doesn't replay it)
        if save_game.save(self.player, self.level_index):   # Continue picks up here
            self.save_toast = SAVE_TOAST_MS

    def _reset_world(self):
        self.ailment_timer = 0
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

    def finish(self):
        """Called after the ending card: the portal goes away and you can roam."""
        self.finished = True
        self.portal = None
        self.exit_reached = False

    # ---- Whisper Jack cutscenes ----------------------------------------
    @property
    def movement_locked(self):
        jack_talking = self.whisper_jack is not None and not self.whisper_jack.message_done
        grabbed = any(m.grabbing for m in self.monsters) or bool(self.boss and self.boss.grabbing)
        return jack_talking or grabbed

    def _start_jack(self, messages, on_done):
        # In camp he pops up between Charlie and the Blacksmith instead of on top of him
        spawn_x = 330 if self.in_camp else self.camera_offset + SCREEN_WIDTH - 200
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
    @property
    def active_menu(self):
        """The shop/bag window that's open, if any (it gets all the input)."""
        for menu in (self.bag, self.blacksmith_shop, self.crow_shop):
            if menu and menu.visible:
                return menu
        return None

    def _nearby_npc(self):
        hero = self.hero_feet_x
        close = [npc for npc in self.npcs if npc.near(hero)]
        return min(close, key=lambda npc: abs(npc.x - hero)) if close else None

    def _interact(self):
        npc = self._nearby_npc()
        if npc is None or self.movement_locked:
            return
        sfx.play("crow_caw" if npc is self.crow else "anvil", 0.6)
        (self.crow_shop if npc is self.crow else self.blacksmith_shop).open()

    def handle_event(self, event):
        menu = self.active_menu
        if menu:
            menu.handle_event(event)
            return

        # Space talks to Whisper Jack / a taunting boss when one is on screen; otherwise it jumps
        space = event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
        space_for_talk = space and ((self.whisper_jack and not self.whisper_jack.fading_out) or
                                    (self.boss and self.boss.state == "taunting"))
        if self.whisper_jack:
            self.whisper_jack.handle_event(event)
        if self.boss:
            self.boss.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                self._interact()
            elif event.key == pygame.K_i:
                self.bag.open()
            elif event.key == pygame.K_h:
                self._quick_potion()
            elif (space and not space_for_talk) or event.key == pygame.K_UP:
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

    def _ailment_tick(self, dt):
        """Infection and burns keep hurting between fights until cured. Camp is safe."""
        p = self.player
        if self.in_camp or self.movement_locked or not (p.infected or p.burning):
            self.ailment_timer = 0
            return
        self.ailment_timer += dt
        if self.ailment_timer < AILMENT_TICK_MS:
            return
        self.ailment_timer = 0
        dmg = 2 * bool(p.infected) + 3 * bool(p.burning)
        if p.has("thick_skin") >= 2:          # Thick Skin II: ailments hurt half as much
            dmg = -(-dmg // 2)
        dmg = min(p.hp - 1, dmg)
        if dmg > 0:
            p.hp -= dmg
            word = "burn" if p.burning else "infection"
            self.floating_texts.append(CombatText(f"-{dmg} {word}", self.hero_feet_x - self.camera_offset - 40,
                                                  p.y - 20, (255, 160, 60) if p.burning else (140, 230, 90)))

    def _quick_potion(self):
        """H: drink a Gourd-Aid (or a Remedy if that's all there is) without opening the bag."""
        hero_x = self.hero_feet_x - self.camera_offset - 35
        p = self.player
        order = ("remedy", "potion", "elixir") if (p.infected or p.burning) else ("potion", "remedy", "elixir")
        key = next((k for k in order if p.item_useful(k)), None)
        if key:
            result = p.use_item(key)
            text = f"+{result['healed']} HP" + (", cured!" if result["cured"] else "")
            color = HEAL_GREEN
            sfx.play("heal")
        elif p.hp >= p.max_hp:
            text, color = "Already full HP", (255, 230, 120)
        else:
            text, color = "No Gourd-Aid! (Crow sells it)", (255, 230, 120)
        self.floating_texts.append(CombatText(text, hero_x, p.y - 20, color))

    # ---- update --------------------------------------------------------
    def update(self, keys, dt):
        self.save_toast = max(0, self.save_toast - dt)
        self.player_hud.update(dt)
        for text in self.floating_texts + self.world_texts:
            text.update(dt)
        self.floating_texts = [t for t in self.floating_texts if t.is_alive()]
        self.world_texts = [t for t in self.world_texts if t.is_alive()]

        self.grit.update(dt)
        menu = self.active_menu
        if menu:
            menu.update(dt)
            self.is_walking = False
            return

        # Update Jack first so a finished talk marks its story flag before we
        # decide whether another cutscene should start.
        if self.whisper_jack:
            self.whisper_jack.update(dt)
            if self.whisper_jack.message_done and self.on_jack_done:
                self.on_jack_done()
                self.on_jack_done = None
            jack = self.whisper_jack
            if jack.message_done and not jack.fading_out and abs(jack.x - self.hero_feet_x) > JACK_WANDER_OFF:
                jack.fading_out = True          # Charlie walked off mid-goodbye: Jack sinks away on his own
            if not jack.active:
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
        self._ailment_tick(dt)

        hero_center = self.hero_feet_x
        for npc in self.npcs:
            npc.update(dt, hero_center)
            line = npc.greeting(hero_center)
            if line:
                width = get_font(17).size(line)[0]
                top = FEET_Y - npc.sprite.current.frames[0].get_height() - 70
                self.world_texts.append(CombatText(line, npc.x - width / 2, top, npc.color, lifespan=2600, size=17))
        if self.boss:
            self.boss.update(dt, hero_center)
            if not self.boss.defeated:      # can't walk through the boss
                self.player.x = min(self.player.x, self.boss.x - HERO_HALF_WIDTH - 140)
        jack_talking = self.whisper_jack is not None and not self.whisper_jack.message_done
        for monster in self.monsters:
            if self.sliding and not monster.defeated and not monster.grabbing and \
                    abs(monster.x - hero_center) < monster.grab_range:
                monster.first_strike = True            # slid right into it: Charlie hits first
                monster.ready_for_battle = True
            line = monster.update(dt, hero_center, calm=jack_talking)
            on_screen = 0 < monster.x - self.camera_offset < SCREEN_WIDTH
            if line and on_screen:
                if monster.p["sound"]:
                    sfx.play(monster.p["sound"], 0.5)
                self.world_texts.append(CombatText(line, monster.x - 45, FEET_Y - 200, monster.p["color"],
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
        """Return the enemy spec of a monster or boss that's ready to fight (and
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
        return self.monsters + ([self.boss] if self.boss else [])

    # ---- drawing -------------------------------------------------------
    def draw(self):
        if self.in_camp:
            self.parallax.draw(self.screen, self.camera_offset, with_front=False)   # foreground comes later
        else:
            self._draw_background()
        if self.portal:
            self.portal.draw(self.screen, self.camera_offset)
        for npc in self.npcs:
            self.grit.draw_shadow(self.screen, npc.x - self.camera_offset, FEET_Y, 1.1)
            npc.draw(self.screen, self.camera_offset, FEET_Y)

        for monster in self.monsters:
            if not monster.defeated:
                self.grit.draw_shadow(self.screen, monster.x - self.camera_offset, FEET_Y, monster.shadow_size)
            monster.draw(self.screen, self.camera_offset, FEET_Y)
        if self.boss and not self.boss.defeated:
            self.grit.draw_shadow(self.screen, self.boss.x - self.camera_offset, FEET_Y, self.boss.shadow_size)
            self.boss.draw(self.screen, self.camera_offset, FEET_Y)

        hero_x = self.hero_feet_x - self.camera_offset
        self.grit.draw_shadow(self.screen, hero_x, FEET_Y, 0.9 - min(0.4, self.hero.lift / 250))
        self.hero.draw(self.screen, hero_x, FEET_Y, self.facing_right)
        if self.in_camp:           # stumps and trees in front of everyone, for depth
            hero_box = pygame.Rect(0, 0, 70, 125)
            hero_box.midbottom = (hero_x, FEET_Y - self.hero.lift)
            self.parallax.draw_front(self.screen, self.camera_offset, hero_box)

        self.grit.draw_fog(self.screen, self.camera_offset)
        self.grit.apply(self.screen)   # everything above is "world"; below stays crisp

        if self.whisper_jack:
            self.whisper_jack.draw(self.screen, self.camera_offset)
        if self.boss:
            self.boss.draw_bubble(self.screen, self.camera_offset, FEET_Y)
        npc = self._nearby_npc()
        if npc and not self.active_menu:
            npc.draw_prompt(self.screen, self.camera_offset, FEET_Y)

        for text in self.floating_texts:
            text.draw(self.screen)
        for text in self.world_texts:
            text.draw(self.screen, self.camera_offset)

        self.player_hud.draw()
        where = "Camp" if self.in_camp else f"Ch. {self.level_index + 1}: {self.level['name']}"
        label = self.small_font.render(where, True, (230, 230, 230))
        right = self.screen.get_width() - 10
        self.screen.blit(label, (right - label.get_width(), 12))
        if self.save_toast > 0:
            alpha = int(255 * min(1.0, self.save_toast / 500))
            note = self.small_font.render("Game saved", True, (255, 220, 160))
            note.set_alpha(alpha)
            icon_surf = icon("candy", 22).copy()     # (the cached icon is shared: fade a copy)
            icon_surf.set_alpha(alpha)
            y = self.screen.get_height() - 34
            self.screen.blit(icon_surf, (right - note.get_width() - 28, y - 2))
            self.screen.blit(note, (right - note.get_width(), y))
        menu = self.active_menu
        if menu:
            menu.draw()

    def _draw_background(self):
        if not self.background:
            self.screen.fill((15, 10, 25))
            return
        width = self.background.get_width()
        x = -(self.camera_offset % width)
        self.screen.blit(self.background, (x, 0))
        self.screen.blit(self.background, (x + width, 0))
