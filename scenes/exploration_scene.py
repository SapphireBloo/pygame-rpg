import math
import random

import pygame

from core import game_state
from core.animation import AnimatedSprite, load_gameart2d_character
from core.assets import load_background
from core.camp import ParallaxBackground, Blacksmith, Crow, Crumb, CAMP_LENGTH, BLACKSMITH_X, CROW_HOME_X, CRUMB_HOME_X
from core.camp_shops import BlacksmithShop, CrowShop, BagMenu, CrumbMenu
from core.combat_text import CombatText
from core import save_game
from core.icons import icon
from core.grit import Grit
from core.difficulty import settings as difficulty_settings
from core.level_layouts import LAYOUTS, CAMP_LAYOUT, EXIT_PAST_BOSS, BOSS_CLEARING, build_props
from core.levels import LEVELS, SECRET_BOSS
from core.options import options
from core.player_hud import PlayerHUD
from core.pickups import GoldenCrumb
from core.portal import Portal
from core import lighting, sfx
from core.boss_encounter import BossEncounter
from core.roaming_enemy import RoamingEnemy
from core.settings import (
    SCREEN_WIDTH, GROUND_Y, FEET_Y, WALK_SPEED, RUN_SPEED, SLIDE_SPEED, CAMERA_LEAD,
    MONSTER_SPACING, HERO_HEIGHT, CHARACTER_INK,
)
from core.jack_panel import JackPanel
from core.speech import SpeechBubble
from scenes.void_walk import VoidWalk, WALK_SCALE as VOID_WALK_SCALE
from core.ui import get_font, outlined_text, HEAL_GREEN

# Movement. Jumps use real gravity now (so Charlie can land on platforms): a jump from the ground
# rises JUMP_HEIGHT and lands JUMP_TIME later, which matches the length of the jump animation.
JUMP_HEIGHT = 110          # pixels
JUMP_TIME = 0.6            # seconds in the air for a jump from flat ground
GRAVITY = 8 * JUMP_HEIGHT / JUMP_TIME ** 2
JUMP_SPEED = 4 * JUMP_HEIGHT / JUMP_TIME
COYOTE_MS = 90             # a jump still works this long after walking off an edge
DOUBLE_JUMP_HEIGHT = 95    # the second jump, in mid-air (one per trip off the ground)
DOUBLE_JUMP_SPEED = (2 * GRAVITY * DOUBLE_JUMP_HEIGHT) ** 0.5
BODY_HALF = 22             # half of Charlie's width, for bumping into things
FOOT_HALF = 14             # how much of him has to be over a platform to stand on it
STAND_HEIGHT = 134         # his height for bumping his head (the art is ~138 tall)
SLIDE_HEIGHT = 108         # ...and while sliding or crawling (fits under 122-high ceilings)
CRAWL_SPEED = 170          # moving while stuck down under a low ceiling
# Traps
TRAP_DAMAGE = (6, 8, 10, 12)   # by chapter, before difficulty. Traps never knock Charlie out (1 HP minimum).
HURT_GRACE_MS = 1200       # blinking, can't be hurt again
KNOCK_MS = 260             # knocked back this long
KNOCK_SPEED = 320
KNOCK_HOP = 380
PORTAL_REACH = 90          # how close (to its middle) Charlie must be to step into the portal with E
PORTAL_WALK_SPEED = 160    # he walks into the middle of it...
PORTAL_FADE_MS = 650       # ...then shrinks and fades away into it
STOMP_REACH = 60           # land within this of a monster's middle (and on its head) for a stomp First Strike
MONSTER_STANDOFF = 110     # monsters keep this far back from the obstacles around their ground...
LANDING_ROOM = 70          # ...and on the side Charlie comes from, this much past their grab range,
                           # so he can land, then slide in (or they don't pounce the moment he lands)
TRAP_WORDS = {"fire": "hot!", "spikes": "ouch!", "toxic": "sludge!", "punch": "pow!", "crusher": "smash!",
              "runes": "zap!", "lightning": "zap!", "worm": "chomp!", "arrows": "thwip!"}
TRAP_SOUNDS = {"fire": "burn", "spikes": "hurt", "toxic": "bite", "crusher": "hurt_heavy", "punch": "punch_heavy"}
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
    "Press Space again in mid-air for a double jump. Handy for reaching high places.",
    "Slide right into a monster, or land on its head, and you'll get the first punch in.",
    "Spikes, gunk, swinging pots... jump 'em. Something hanging low? Slide under it.",
    "And if something looks worth rummaging through, walk up and press E to search it.",
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
        self.lift = 0.0            # Charlie's feet, in pixels above the ground line
        self.vy = 0.0              # upward speed (pixels per second)
        self.on_ground = True      # standing on the ground or a platform
        self.coyote = 0
        self.air_jumps = 1         # double jumps left before landing
        self.puffs = []            # little dust rings from double jumps: [world x, elevation, age ms]
        self.crawling = False      # stuck low under a ceiling after a slide
        self.hurt_timer = 0
        self.knock_timer = 0
        self.knock_dir = 0
        self.props = []            # platforms, traps, things to search, decor (core/level_layouts.py)
        self.entering = None       # stepping into the portal: ms spent fading in it (None = not entering)
        self.grit = Grit(screen.get_size())

        self.floating_texts = []   # screen-positioned (heal numbers over Charlie)
        self.world_texts = []      # world-positioned (monster chatter), scroll with the camera
        self.bubble = None         # the camp folk's speech bubble showing now (one at a time)
        self.bubble_queue = []     # ...and the lines waiting their turn: (npc, text)
        self.talk = []             # a little scene of lines (Crumb's outbursts): (npc, text, ms); locks movement
        self.talking = False
        self.talk_timer = 0
        self.talk_done = None      # called after the last line
        self.banner = None         # [text, color, ms left]: a big line across the middle of the screen
        self.shake = 0             # ms of screen shake left
        self.buddy = None          # Crumb tagging along in a chapter (after he joined Charlie)
        self.void = None           # the final chapter's slow, narrated walk (scenes/void_walk.py)
        self.player_hud = PlayerHUD(screen, player)
        self.bag = BagMenu(screen, player)        # I: what Charlie's carrying (works anywhere)
        self.blacksmith_shop = None               # camp menus, made when a camp loads
        self.crow_shop = None
        self.crumb_menu = None
        self.pending_battle = None                # a fight started from a menu (Crumb's challenge)
        self.parallax = None                      # camp background (loaded the first time)
        self.in_camp = False
        self.npcs = []

        self.finished = False   # True after the last level's exit (the ending plays)
        self.save_toast = 0     # ms left on the "Game saved" note
        self._menu_was_open = False
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
        self.void = None
        if self.level.get("void"):            # the final chapter is its own thing: see scenes/void_walk.py
            self._load_void()
            return

        # Monsters roam their spots along the level, then the boss waits at the end.
        # Where they stand, and the obstacles in between, come from core/level_layouts.py.
        layout = LAYOUTS[index] if index < len(LAYOUTS) else None
        specs = self.level.get("monsters", [])
        if layout:
            self.theme = layout["theme"]
            self.props = build_props(layout)
            homes, boss_x = layout["monsters"], layout["boss"]
        else:                                   # a chapter with no layout yet: evenly spaced, no props
            self.theme, self.props = "camp", []
            homes = [MONSTER_SPACING * i for i in range(1, len(specs) + 1)]
            boss_x = MONSTER_SPACING * (len(specs) + 1)
        self.monsters = []
        for home, spec in zip(homes, specs):
            monster = RoamingEnemy(home, spec, self.level.get("ghost_tint"))
            perch = self._perch(home)
            if perch:                           # its spot is up on a platform: it patrols the top
                monster.elev = perch.top
                lo = perch.left + monster.grab_range + 30     # (room to climb up before it reaches you)
                hi = perch.right - 60
                monster.bounds = (lo, hi) if lo < hi else (perch.x, perch.x)
                monster.x = home
            else:
                lo, hi = self._open_ground(home, monster.grab_range + LANDING_ROOM)
                monster.bounds = (lo, min(hi, boss_x - BOSS_CLEARING))   # (and out of the boss's clearing)
            monster.x = max(monster.bounds[0], min(monster.bounds[1], monster.x))
            self.monsters.append(monster)
        boss_spec = self.level.get("boss")
        self.boss = BossEncounter(boss_x, boss_spec) if boss_spec else None
        spot = layout.get("golden_crumb") if layout else None
        self.pickups = [GoldenCrumb(*spot)] if spot and index not in self.player.crumbs_found else []
        self.exit_x = boss_x + EXIT_PAST_BOSS if self.boss else boss_x
        self.portal = Portal(self.exit_x, GROUND_Y, self.level["accent"], "Camp >")
        self._reset_world()
        self.buddy = Crumb(self.hero_feet_x - 70, self.player, follow=True) if self.player.companion else None
        if self.level["arrival"] and index not in game_state.arrivals_seen:   # not again after a retry
            game_state.arrivals_seen.add(index)
            self._start_jack(self.level["arrival"], None)

    def _load_void(self):
        self.theme, self.props = "camp", []
        self.monsters, self.boss, self.pickups = [], None, []
        self.exit_x = 10 ** 7                  # (no portal: the walk ends when Gorge does)
        self.portal = None
        self._reset_world()
        self.void = VoidWalk(self, self.level)
        self.buddy = Crumb(self.hero_feet_x - 70, self.player, follow=True) if self.player.companion else None

    def load_camp(self, arriving=True):
        """The safe camp after this chapter's boss: shops, no monsters. arriving=False when
        coming back to it (dying, or Continue), so Crumb's blessing from this camp stays."""
        self.in_camp = True
        self.void = None
        self.background = None
        if self.parallax is None:
            self.parallax = ParallaxBackground()
        self.grit.set_level({"background": "camp", "accent": (255, 170, 90)})
        self.monsters = []
        self.boss = None
        self.pickups = []
        self.theme = CAMP_LAYOUT["theme"]
        self.props = build_props(CAMP_LAYOUT)
        self.blacksmith = Blacksmith(BLACKSMITH_X)
        self.crow = Crow(CROW_HOME_X)
        self.crumb = Crumb(CRUMB_HOME_X, self.player, follow=self.player.companion)
        self.buddy = None
        self.npcs = [self.blacksmith, self.crumb, self.crow]      # (drawn in this order: Crumb in front of the anvil)
        self.blacksmith_shop = BlacksmithShop(self.screen, self.player, self.blacksmith.portrait())
        self.crow_shop = CrowShop(self.screen, self.player, self.crow.portrait())
        self.crumb_menu = CrumbMenu(self.screen, self.player, self.crumb.portrait(), on_pet=self.crumb.petted)
        self.exit_x = CAMP_LENGTH
        label = "The End >" if self.is_last_level else f"{LEVELS[self.level_index + 1]['name']} >"
        self.portal = Portal(self.exit_x, GROUND_Y, (255, 170, 90), label)
        self._reset_world()
        if self.level_index == len(LEVELS) - 2:          # the camp before the final chapter
            self._start_jack(JACK_LAST_CAMP, None)
        elif not game_state.first_camp_done:
            self._start_jack(JACK_FIRST_CAMP, None)
            game_state.first_camp_done = True     # (counted as heard, so Continue doesn't replay it)
        if arriving:
            self.player.clear_blessing()        # Crumb's blessing lasted the chapter; it wears off here
        self.checkpoint()                       # dying (or Continue) brings you back here

    def _reset_world(self):
        self.ailment_timer = 0
        self.exit_reached = False   # main.py starts the transition when this flips
        self.player.x = 50.0
        self.camera_offset = 0
        self.boss_pan = 0.0        # extra camera slide so a talking boss is fully on screen
        self.floating_texts.clear()
        self.world_texts.clear()
        self.bubble = None
        self.bubble_queue.clear()
        self.talk, self.talking, self.talk_done = [], False, None
        self.banner = None
        self.shake = 0
        self.facing_right = True
        self.action = None
        self.lift = self.vy = 0.0
        self.on_ground = True
        self.air_jumps = 1
        self.puffs.clear()
        self.crawling = False
        self.hurt_timer = self.knock_timer = 0
        self.hero.reset_pose()
        self.hero.alpha = 255
        self.entering = None
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
        return jack_talking or grabbed or self.entering is not None or self.talking

    def _start_jack(self, messages, on_done):
        """Whisper Jack talks in his panel at the top. Charlie waits until the lines have been read."""
        self.whisper_jack = JackPanel(messages, self.hero_feet_x)
        self.on_jack_done = on_done

    # ---- speech bubbles -------------------------------------------------
    def say(self, npc, text, life=3000, now=False):
        """A speech bubble over a camp character. One at a time: others wait their turn
        (now=True cuts in front, for outbursts)."""
        if now:
            self.bubble = SpeechBubble(text, npc, npc.color, life, height=self._bubble_height(npc))
        else:
            self.bubble_queue.append((npc, text, life))

    @staticmethod
    def _bubble_height(npc):
        return npc.sprite.current.frames[0].get_height() + 64   # (above the [E] prompt)

    def _update_bubbles(self, dt):
        if self.bubble:
            self.bubble.update(dt)
            if not self.bubble.alive:
                self.bubble = None
        while self.bubble is None and self.bubble_queue:
            npc, text, life = self.bubble_queue.pop(0)
            if abs(npc.x - self.hero_feet_x) < 500:            # (skip it if Charlie's wandered off)
                self.bubble = SpeechBubble(text, npc, npc.color, life, height=self._bubble_height(npc))

    def _check_cutscenes(self, trying_to_move):
        # A Jack who's finished talking (even if still sinking) can be replaced
        if not trying_to_move or (self.whisper_jack and not self.whisper_jack.message_done):
            return
        if not game_state.whisper_jack_exploration_intro_done:
            self._start_jack(JACK_INTRO, self._intro_finished)
        elif game_state.first_battle_done and not game_state.whisper_jack_second_intro_done:
            self._start_jack(JACK_AFTER_FIRST_BATTLE, self._second_intro_finished)

    def checkpoint(self, toast=True):
        """Save the game at this camp. Dying, or Continue on the title screen, comes back here."""
        if save_game.save(self.player, self.level_index) and toast:
            self.save_toast = SAVE_TOAST_MS

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
        for menu in (self.bag, self.blacksmith_shop, self.crow_shop, self.crumb_menu):
            if menu and menu.visible:
                return menu
        return None

    def _nearby_npc(self):
        hero = self.hero_feet_x
        close = [npc for npc in self.npcs if npc.near(hero)]
        return min(close, key=lambda npc: abs(npc.x - hero)) if close else None

    def _nearby_prop(self):
        """A spot Charlie could search right now, if any."""
        if self.in_camp or not self.on_ground:
            return None
        feet = self.hero_feet_x
        close = [p for p in self.props if p.near(feet, self.lift)]
        return min(close, key=lambda p: abs(p.x - feet)) if close else None

    def _search(self, spot):
        text, color, _ = spot.roll_loot(self.player, self.level_index, self.theme)
        width = get_font(18).size(text)[0]
        self.world_texts.append(CombatText(text, spot.x - width / 2, FEET_Y - spot.elev - spot.size[1] - 30,
                                           color, lifespan=2200, size=18))

    def _interact(self):
        if self.movement_locked:
            return
        npc = self._nearby_npc()
        if npc is None and self.near_portal:
            self._enter_portal()
            return
        if npc is None:
            spot = self._nearby_prop()
            if spot:
                self._search(spot)
            return
        if npc is self.crumb:
            if self.crumb.angry and not self.player.crumb_fought:
                self._crumb_confront()
                return
            sfx.play("ui_select", 0.6)
            self.crumb_menu.open()
            return
        sfx.play("crow_caw" if npc is self.crow else "anvil", 0.6)
        (self.crow_shop if npc is self.crow else self.blacksmith_shop).open()

    @property
    def near_portal(self):
        return bool(self.portal) and self.on_ground and abs(self.hero_feet_x - self.exit_x) < PORTAL_REACH

    def _enter_portal(self):
        """E at the portal: Charlie walks into it and vanishes, then the next chapter (or camp) loads."""
        if not all(f.defeated for f in self._foes()):
            self._note("Something's still lurking out there...", (255, 200, 150))
            return
        p = self.player
        if self.in_camp and p.crumbs_fed >= 4 and not p.crumb_fought and not p.crumb_beaten:
            if not p.crumb_angry:
                self._crumb_outburst()
            else:
                self.say(self.crumb, "CRUMB: Oh no you DON'T. Get back here.", 2000, now=True)
                self._note("Crumb wants a word...", (255, 140, 120))
            return
        self.entering = 0
        self.action = None
        sfx.play("portal")
        if self.in_camp:                 # leaving camp: the checkpoint includes what you bought
            self.checkpoint()

    def _note(self, text, color):
        """A short line floating over Charlie's head."""
        width = get_font(18).size(text)[0]
        self.floating_texts.append(CombatText(text, self.hero_feet_x - self.camera_offset - width / 2,
                                              FEET_Y - self.lift - 190, color, size=18))

    def _walk_into_portal(self, dt):
        feet = self.hero_feet_x
        if abs(feet - self.exit_x) > 4:                       # walk to the middle
            self.facing_right = self.exit_x > feet
            step = PORTAL_WALK_SPEED * dt / 1000
            self.player.x += max(-step, min(step, self.exit_x - feet))
            self.hero.play("walk")
            return
        self.hero.play("idle")
        self.entering += dt
        k = min(1.0, self.entering / PORTAL_FADE_MS)
        self.hero.scale_x = self.hero.scale_y = 1 - 0.75 * k   # shrink into the dark
        self.hero.alpha = int(255 * (1 - k))
        if k >= 1:
            self.exit_reached = True

    # ---- Crumb's secret fight --------------------------------------------
    def play_talk(self, lines, done=None):
        """A little scene: each (npc, text, ms) line shows in a bubble in turn. Charlie can't move
        while it plays (Space or E skips ahead)."""
        self.talk = list(lines)
        self.talk_done = done
        self.talking = True
        self._next_talk()

    def _next_talk(self):
        if self.talk:
            npc, text, ms = self.talk.pop(0)
            self.say(npc, text, ms, now=True)
            self.talk_timer = ms
            return
        self.talking = False
        if self.bubble:
            self.bubble.life = min(self.bubble.life, 300)
        done, self.talk_done = self.talk_done, None
        if done:
            done()

    def _update_talk(self, dt):
        if self.talking:
            self.talk_timer -= dt
            if self.talk_timer <= 0:
                self._next_talk()
        if self.banner:
            self.banner[2] -= dt
            if self.banner[2] <= 0:
                self.banner = None
        self.shake = max(0, self.shake - dt)

    def _crumb_outburst(self):
        """Crumb ate all four Golden Crumbs... and Charlie's about to leave without him. BOOM."""
        c, p = self.crumb, self.player
        p.crumb_angry = True
        sfx.play("explosion")
        sfx.play("enrage")
        self.shake = 700
        self.play_talk([(c, "CRUMB: HEY!! WHERE do you think YOU'RE going?!", 2200),
                        (c, "CRUMB: FOUR golden crumbs. FOUR. And you just... LEAVE?!", 2600),
                        (c, "CRUMB: Get back here, pumpkin. We need to TALK.", 2300)],
                       done=lambda: self._show_banner("Go back and check on Crumb...", (255, 130, 110), 3500))
        self.checkpoint(toast=False)

    def _crumb_confront(self):
        """Charlie faces the furious Crumb: his speech, then the fight. It's a one-shot."""
        c = self.crumb
        sfx.play("enrage")
        self.banner = None                          # (he's been found)

        def fight():
            self.player.crumb_fought = True
            self.checkpoint(toast=False)            # (win or lose, there's no second try)
            self.pending_battle = dict(SECRET_BOSS)

        self.play_talk([(c, "You fed me. You FED me. Four golden crumbs.", 2300),
                        (c, "And then you tried to sneak off to the Void. Without. ME.", 2500),
                        (c, "Do you know what happens to bread that eats gold, pumpkin?", 2500),
                        (c, "It. RISES.", 1800)], done=fight)

    def _crumb_after_fight(self):
        """Back at camp after the secret fight: he joins Charlie (a win), or calms down (a loss)."""
        c, p = getattr(self, "crumb", None), self.player
        if not (self.in_camp and c and p.crumb_angry and p.crumb_fought) or self.talking or self.pending_battle:
            return                                  # (the fight itself hasn't started yet)

        def settled():
            p.crumb_angry = False
            if p.crumb_beaten:
                c.follow = True
                self._show_banner("Crumb joined you!", (255, 215, 130), 3000)
                sfx.play("heal")
            self.checkpoint(toast=False)

        if p.crumb_beaten:
            lines = [(c, "...ow. Okay. OKAY. You win.", 2000),
                     (c, "That's the hardest anyone's ever punched a loaf.", 2300),
                     (c, "Take me with you? Into the Void? I'm crusty, I'm loyal, and I can FLY. Kinda.", 3000),
                     (c, "I'll launch myself at the bad guys. Just say the word: LOAF LAUNCH.", 2800)]
        else:
            lines = [(c, "HA! The Crust Eternal stays ETERNAL!", 2000),
                     (c, "...sorry. That was a lot. I get crumby when I'm hungry.", 2500),
                     (c, "Go on, pumpkin. Save the world. I'll keep the fire warm.", 2600)]
        c.facing_right = self.hero_feet_x > c.x
        self.play_talk(lines, done=settled)

    def _show_banner(self, text, color, ms):
        self.banner = [text, color, ms]

    def handle_event(self, event):
        menu = self.active_menu
        if menu:
            menu.handle_event(event)
            return
        if self.void and self.void.talking and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE \
                and not (self.boss and self.boss.state == "taunting"):
            self.void.skip_line()                          # Space: Jack's next line (no jumping mid-speech)
            return
        if self.talking:                                   # Space or E hurries a scene along
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_e, pygame.K_RETURN):
                self.talk_timer = min(self.talk_timer, 0)
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
        if self.movement_locked or self.crawling or self.knock_timer > 0 or not self.hero.has(name):
            return
        if name == "jump":
            if (self.on_ground or self.coyote > 0) and not self.action:
                self.vy = JUMP_SPEED
            elif not self.on_ground and self.air_jumps > 0 and self.action in (None, "jump"):
                self.vy = DOUBLE_JUMP_SPEED       # double jump: a second kick in mid-air
                self.air_jumps -= 1
                self.puffs.append([self.hero_feet_x, self.lift, 0])
            else:
                return
            self.on_ground = False
            self.coyote = 0
        elif self.action or not self.on_ground:
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
        self._update_talk(dt)
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
            self._menu_was_open = True
            return
        if self._menu_was_open:
            self._menu_was_open = False
            if self.in_camp:                    # closed a shop (or fed Crumb) at camp: update the checkpoint
                self.checkpoint(toast=False)

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

        if self.entering is not None:            # stepping through the portal: nothing else happens
            if self.portal:
                self.portal.update(dt)
            self._walk_into_portal(dt)
            self.hero.update(dt)
            return
        direction = int(bool(keys[pygame.K_d] or keys[pygame.K_RIGHT])) - int(bool(keys[pygame.K_a] or keys[pygame.K_LEFT]))
        self._check_cutscenes(direction != 0)

        running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        locked = self.movement_locked
        self.is_walking = direction != 0 and not locked
        self.hurt_timer = max(0, self.hurt_timer - dt)
        step = 0.0
        if self.knock_timer > 0:
            self.knock_timer -= dt
            step = self.knock_dir * KNOCK_SPEED * dt / 1000
            self.is_walking = False
        elif self.sliding:
            # Slides carry Charlie forward fast, slowing toward the end
            t = min(1.0, self.action_time / self.hero.current.duration)
            step = (1 if self.facing_right else -1) * SLIDE_SPEED * (1 - 0.6 * t) * dt / 1000
        elif self.crawling:
            if self.is_walking:
                self.facing_right = direction > 0
                step = direction * CRAWL_SPEED * dt / 1000
        elif self.is_walking:
            self.facing_right = direction > 0
            speed = RUN_SPEED if running else WALK_SPEED
            if self.void:                                 # the Void: a slow walk, no running
                speed = WALK_SPEED * VOID_WALK_SCALE
            step = direction * speed * dt / 1000
        self._move_x(step)
        self._move_y(dt)
        if self.crawling and not self._under_ceiling():
            self.crawling = False                     # out from under it: stand back up
        self._check_traps()
        self.hero.alpha = 120 if self.hurt_timer and (self.hurt_timer // 90) % 2 else 255
        for prop in self.props:
            prop.update(dt)
        for puff in self.puffs:
            puff[2] += dt
        self.puffs = [puff for puff in self.puffs if puff[2] < 350]
        self.camera_offset = max(0, int(self.player.x) - CAMERA_LEAD)
        self._frame_boss(dt)

        self._animate_hero(dt, running)
        self._ailment_tick(dt)

        hero_center = self.hero_feet_x
        for npc in self.npcs:
            npc.update(dt, hero_center)
            line = npc.greeting(hero_center)
            if line and not self.talking:
                self.say(npc, line)
        if self.buddy:
            self.buddy.update(dt, hero_center)
        self._crumb_after_fight()
        if self.void:
            self.void.update(dt)
        self._update_bubbles(dt)
        if self.boss:
            self.boss.update(dt, hero_center)
            if not self.boss.defeated:      # can't walk through the boss
                self.player.x = min(self.player.x, self.boss.x - HERO_HALF_WIDTH - 140)
        jack_talking = self.whisper_jack is not None and not self.whisper_jack.message_done
        for monster in self.monsters:
            self._check_stomp(monster)
            if self.sliding and not monster.defeated and not monster.grabbing and \
                    abs(monster.x - hero_center) < monster.grab_range:
                monster.first_strike = True            # slid right into it: Charlie hits first
                monster.ready_for_battle = True
            line = monster.update(dt, hero_center, calm=jack_talking, hero_elev=self.lift)
            if monster.bounds:                         # monsters keep to their open stretch of ground
                monster.x = max(monster.bounds[0], min(monster.bounds[1], monster.x))
            on_screen = 0 < monster.x - self.camera_offset < SCREEN_WIDTH
            if line and on_screen:
                if monster.p["sound"]:
                    sfx.play(monster.p["sound"], 0.5)
                self.world_texts.append(CombatText(line, monster.x - 45, FEET_Y - 200 - monster.elev, monster.p["color"],
                                                   lifespan=2200, size=18))

        for pickup in self.pickups:
            if pickup.update(dt, self.hero_feet_x, self.lift, self.lift + self.body_height):
                self.player.add_item("golden_crumb")
                self.player.crumbs_found.append(self.level_index)
                self.floating_texts.append(CombatText("Golden Crumb!", self.hero_feet_x - self.camera_offset - 60,
                                                      self.player.y - 40, (255, 220, 120)))
        if self.portal:
            self.portal.update(dt)
            self.player.x = min(self.player.x, self.exit_x)   # can't walk past the portal

    def _animate_hero(self, dt, running):
        if self.action:
            self.action_time += dt
            if self.action == "slide" and self.action_time >= self.hero.current.duration:
                self.action = None
                if self._under_ceiling():         # can't stand up under here: keep low and crawl
                    self.crawling = True
            # (a jump ends when he lands: see _move_y)
        self.hero.lift = self.lift
        if self.crawling:
            self.hero.play("slide")               # holds the last slide frame
        elif not self.action and not self.on_ground:
            self.hero.play("jump")                # falling off a ledge (the pose holds at the end)
        elif not self.action:
            if self.is_walking:
                self.hero.play("run" if running and self.hero.has("run") else "walk")
            else:
                self.hero.play("idle")
        self.hero.update(dt)

    # ---- platforms, ceilings, traps ---------------------------------------
    @property
    def body_height(self):
        return SLIDE_HEIGHT if (self.sliding or self.crawling) else STAND_HEIGHT

    def _body_x(self, player_x=None):
        feet = (self.player.x if player_x is None else player_x) + HERO_HALF_WIDTH
        return feet - BODY_HALF, feet + BODY_HALF

    def _support(self, feet_x, below):
        """The highest thing to stand on under Charlie's feet that's no higher than `below`."""
        best = 0.0
        for p in self.props:
            if (p.solid or p.ledge) and p.top <= below and p.left - FOOT_HALF < feet_x < p.right + FOOT_HALF:
                best = max(best, p.top)
        return best

    def _under_ceiling(self):
        a, b = self._body_x()
        return any(p.ceiling is not None and p.overlaps_x(a, b) and p.ceiling < self.lift + STAND_HEIGHT
                   for p in self.props)

    def _move_x(self, step):
        """Walk/slide sideways, stopping at walls and low ceilings."""
        if not step:
            return
        old = self._body_x()
        new_x = max(0.0, self.player.x + step)
        a, b = self._body_x(new_x)
        low, high = self.lift, self.lift + self.body_height
        for p in self.props:
            if not p.blocks or p.body_hits(*old, low, high) or not p.body_hits(a, b, low, high):
                continue                     # (already overlapping it: don't yank him out sideways)
            if step > 0:
                new_x = min(new_x, p.left - BODY_HALF - HERO_HALF_WIDTH - 0.01)
            else:
                new_x = max(new_x, p.right + BODY_HALF - HERO_HALF_WIDTH + 0.01)
            if p.spiked:
                self._hurt(p)
            if self.sliding:
                self.action = None           # slid into a wall
        self.player.x = max(0.0, new_x)

    def _move_y(self, dt):
        """Gravity: fall, land on platforms, bump into ceilings."""
        feet = self.hero_feet_x
        support = self._support(feet, self.lift + 0.5)
        if self.on_ground:
            if support >= self.lift - 0.5:
                self.lift = support
                return
            self.on_ground = False            # walked off an edge
            self.vy = 0.0
            self.coyote = COYOTE_MS
            if self.sliding:
                self.action = None
        self.coyote = max(0, self.coyote - dt)
        s = dt / 1000
        self.vy -= GRAVITY * s
        new = self.lift + self.vy * s
        if self.vy > 0:
            a, b = self._body_x()
            height = self.body_height
            for p in self.props:
                under = p.underside
                if under is not None and p.overlaps_x(a, b) and \
                        self.lift + height <= under + 0.5 < new + height:
                    new = under - height          # bonk
                    self.vy = 0.0
                    if p.spiked:
                        self._hurt(p)
        elif new <= support:
            new = support                         # landed
            self.vy = 0.0
            self.on_ground = True
            self.air_jumps = 1
            if self.action == "jump":
                self.action = None
        self.lift = max(0.0, new)

    def _check_stomp(self, monster):
        """Coming down on a monster's head starts the fight with a First Strike."""
        if monster.defeated or self.on_ground or self.vy >= 0 or self.movement_locked and not monster.grabbing:
            return
        if monster.ready_for_battle and monster.first_strike:
            return
        if abs(monster.x - self.hero_feet_x) < STOMP_REACH and \
                monster.elev + 30 < self.lift <= monster.elev + monster.head_height:
            monster.first_strike = True
            monster.ready_for_battle = True
            sfx.play("punch_heavy", 0.7)
            text = "STOMP! First Strike!"
            width = get_font(20).size(text)[0]
            self.world_texts.append(CombatText(text, monster.x - width / 2, FEET_Y - monster.elev - 230,
                                               (255, 230, 120), lifespan=1600, size=20))

    def _check_traps(self):
        a, b = self._body_x()
        if self.on_ground:                               # stepping on a trap sets it off (a click, then...)
            for p in self.props:
                if hasattr(p, "step_on") and p.step_on(a, b, self.lift):
                    sfx.play("metal_clang", 0.35)
        if self.hurt_timer:
            return
        low, high = self.lift, self.lift + self.body_height
        for p in self.props:
            if p.trap_hits(a, b, low, high):
                self._hurt(p)
                return

    def _hurt(self, prop):
        """A trap got Charlie: some damage (never a knockout) and a hop back the way he came."""
        if self.hurt_timer:
            return
        p = self.player
        chapter = min(self.level_index, len(TRAP_DAMAGE) - 1)
        amount = round(TRAP_DAMAGE[chapter] * difficulty_settings(options["difficulty"])["damage"])
        amount = max(0, min(p.hp - 1, amount))
        p.hp -= amount
        kind = prop.trap or "spikes"
        sfx.play(TRAP_SOUNDS.get(kind, "hurt"), 0.7)
        text = f"-{amount} {TRAP_WORDS.get(kind, 'ouch!')}" if amount else "Ouch!"
        self.floating_texts.append(CombatText(text, self.hero_feet_x - self.camera_offset - 40,
                                              FEET_Y - self.lift - 170, (255, 120, 90)))
        self.hurt_timer = HURT_GRACE_MS
        self.knock_timer = KNOCK_MS
        self.knock_dir = -1 if prop.hit_x > self.hero_feet_x else 1
        self.crawling = False
        if not self._under_ceiling():
            self.vy = KNOCK_HOP
            self.on_ground = False
            self.action = "jump"
            self.action_time = 0
            self.hero.play("jump", restart=True)

    def _perch(self, x):
        """The platform a monster spot at x stands on, if any (the lowest one covering x, so a
        monster on a ridge stays on the ridge even with an island floating over it)."""
        tops = [p for p in self.props if (p.solid or p.ledge) and p.left < x < p.right]
        return min(tops, key=lambda p: p.top) if tops else None

    def _open_ground(self, home, left_gap=MONSTER_STANDOFF):
        """The stretch of open ground around a monster's spot (between the obstacles on either side).
        left_gap: how far it stays from the obstacle Charlie comes over (he walks left to right)."""
        lo, hi = 0.0, float("inf")
        for p in self.props:
            if not (p.blocks or p.ledge or p.trap):
                continue
            if p.right <= home:
                lo = max(lo, p.right + left_gap)
            elif p.left >= home:
                hi = min(hi, p.left - MONSTER_STANDOFF)
        return lo, hi

    def take_battle_trigger(self):
        """Return the enemy spec of a monster or boss that's ready to fight (and
        mark it used), else None. Adds "first_strike" if Charlie slid into it."""
        if self.pending_battle:
            spec, self.pending_battle = self.pending_battle, None
            return spec
        for foe in self._foes():
            if foe.ready_for_battle and not foe.defeated:
                foe.defeated = True
                foe.ready_for_battle = False
                if self.action == "slide":
                    self.action = None
                self.vy = min(self.vy, 0.0)        # (if he was mid-jump, he drops when the fight's over)
                self.knock_timer = 0
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
        for depth in ("far", "mid"):              # back by the trees first, then the characters' plane
            for prop in self.props:
                if not prop.front and prop.depth == depth:
                    prop.draw(self.screen, self.camera_offset)
        if self.portal:
            self.portal.draw(self.screen, self.camera_offset)
        for npc in self.npcs:
            self.grit.draw_shadow(self.screen, npc.x - self.camera_offset, FEET_Y, 1.1)
            npc.draw(self.screen, self.camera_offset, FEET_Y)
        if self.buddy:                                   # Crumb, tagging along
            self.grit.draw_shadow(self.screen, self.buddy.x - self.camera_offset, FEET_Y, 0.6)
            self.buddy.draw(self.screen, self.camera_offset, FEET_Y)

        for monster in self.monsters:
            if not monster.defeated:
                self.grit.draw_shadow(self.screen, monster.x - self.camera_offset, FEET_Y - monster.elev,
                                      monster.shadow_size)
            monster.draw(self.screen, self.camera_offset, FEET_Y)
        if self.boss and not self.boss.defeated:
            self.grit.draw_shadow(self.screen, self.boss.x - self.camera_offset, FEET_Y, self.boss.shadow_size)
            self.boss.draw(self.screen, self.camera_offset, FEET_Y)

        for pickup in self.pickups:
            pickup.draw(self.screen, self.camera_offset)
        if self.void:
            self.void.draw_world(self.screen, self.camera_offset)

        hero_x = self.hero_feet_x - self.camera_offset
        ground = self._support(self.hero_feet_x, self.lift + 0.5)
        self.grit.draw_shadow(self.screen, hero_x, FEET_Y - ground, 0.9 - min(0.4, (self.lift - ground) / 250))
        for px, pe, age in self.puffs:              # double-jump dust ring
            k = age / 350
            ring = pygame.Surface((90, 30), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (235, 225, 210, int(170 * (1 - k))),
                                pygame.Rect(0, 0, 40 + 50 * k, 10 + 14 * k).move(25 - 25 * k, 10 - 7 * k), 3)
            self.screen.blit(ring, (px - self.camera_offset - 45, FEET_Y - pe - 12))
        self.hero.draw(self.screen, hero_x, FEET_Y, self.facing_right)
        lights = [prop for prop in self.props if prop.light]
        if lights:                 # firelight: everything nearby (Charlie included) catches the glow
            lighting.darken(self.screen)
            for prop in lights:
                lighting.draw_light(self.screen, prop.light_center(self.camera_offset), prop.light,
                                    prop.flicker, prop.time)
        hero_box = pygame.Rect(0, 0, 70, 125)
        hero_box.midbottom = (hero_x, FEET_Y - self.hero.lift)
        for prop in self.props:
            if prop.front and prop.depth != "near":
                prop.draw(self.screen, self.camera_offset)
        if self.in_camp:           # stumps and trees in front of everyone, for depth
            self.parallax.draw_front(self.screen, self.camera_offset, hero_box)
        for prop in self.props:    # the closest things of all (big, dark, see-through when he's behind them)
            if prop.depth == "near":
                prop.fade_behind(hero_box)
                prop.draw(self.screen, self.camera_offset)

        self.grit.draw_fog(self.screen, self.camera_offset)
        self.grit.apply(self.screen)   # everything above is "world"; below stays crisp

        if self.whisper_jack:
            self.whisper_jack.draw(self.screen, self.camera_offset)
        if self.boss:
            self.boss.draw_bubble(self.screen, self.camera_offset, FEET_Y)
        npc = self._nearby_npc()
        if npc and not self.active_menu:
            npc.draw_prompt(self.screen, self.camera_offset, FEET_Y)
        elif not self.active_menu and not self.movement_locked:
            spot = self._nearby_prop()
            if self.near_portal:
                self._draw_portal_prompt()
            elif spot:
                spot.draw_prompt(self.screen, self.camera_offset)

        for text in self.floating_texts:
            text.draw(self.screen)
        for text in self.world_texts:
            text.draw(self.screen, self.camera_offset)
        if self.bubble and not self.active_menu:
            self.bubble.draw(self.screen, self.camera_offset, FEET_Y)

        self.player_hud.draw()
        if self.void:
            self.void.draw_overlay(self.screen)
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
        if self.banner:
            text, color, left = self.banner
            surf = outlined_text(text, 30, color, True, 3)
            surf.set_alpha(int(255 * min(1.0, left / 500)))
            self.screen.blit(surf, surf.get_rect(center=(self.screen.get_width() // 2, 170)))
        if self.shake:
            k = self.shake / 700
            self.screen.scroll(int(random.uniform(-9, 9) * k), int(random.uniform(-7, 7) * k))
        menu = self.active_menu
        if menu:
            menu.draw()

    def _draw_portal_prompt(self):
        label = outlined_text("[E] Enter", 16, (255, 240, 200), True, 2)
        bob = 3 * math.sin(pygame.time.get_ticks() / 200)
        top = FEET_Y - self.portal.height - 80 + bob
        pill = label.get_rect(midtop=(self.exit_x - self.camera_offset, top)).inflate(14, 8)
        back = pygame.Surface(pill.size, pygame.SRCALPHA)
        pygame.draw.rect(back, (12, 8, 14, 200), back.get_rect(), border_radius=10)
        pygame.draw.rect(back, (*self.portal.color, 230), back.get_rect(), 2, border_radius=10)
        self.screen.blit(back, pill)
        self.screen.blit(label, label.get_rect(center=pill.center))

    def _draw_background(self):
        if self.void:
            self.void.draw_background(self.screen, self.camera_offset)
            return
        if not self.background:
            self.screen.fill((15, 10, 25))
            return
        width = self.background.get_width()
        x = -(self.camera_offset % width)
        self.screen.blit(self.background, (x, 0))
        self.screen.blit(self.background, (x + width, 0))
