"""Turn-based fights, played out as animated sequences.

Each round is a "script" (see core/effects.py): Charlie's move, the enemy's
attack, then back to the menu. Timing rings appear during attacks and enemy
swings; Space presses are routed to whichever ring is active.
"""
import math
import random

import pygame

from core import cheats, game_state, save_game
from core import sfx
from core.animation import AnimatedSprite, load_gameart2d_character
from core.assets import load_background
from core.battle_manager import BattleManager, MOVES
from core.difficulty import enemy_mods, timing_scale, ring_motion, FEINT_HOLD_MS
from core.options import options
from core.combat_options import CombatOptions, JAB, HAYMAKER, CHIN_CHECK, ITEMS, LOAF
from core.item_picker import ItemPicker, BACK
from core.items import ITEMS_BY_KEY
from core.camp import camp_backdrop, crumb_animations, CRUMB_TINTS
from core.combat_text import CombatText
from core.effects import (Script, Shake, Particles, Swoosh, TimingRing, wait, tween, lerp, aura,
                          ease_out, ease_in, ease_in_out, PERFECT, GOOD, MISS)
from core.end_combat_modal import EndCombatModal, Reward
from core.enemy import Enemy
from core.enemy_art import (enemy_animations, faces_right_in_battle, battle_layout, boss_effects, draw_spotlight,
                            crumb_boss_animations, CRUMB_PHASES)
from core.enemy_hud import EnemyHUD
from core.grit import Grit
from core.levels import LEVELS
from core.player_hud import PlayerHUD
from core.settings import FEET_Y, HERO_HEIGHT, CHARACTER_INK, SCREEN_WIDTH
from core.jack_panel import JackPanel
from core.ui import get_font, outlined_text, BLOCK_BLUE, WHITE, DAMAGE_RED, HEAL_GREEN, GOLD, INK

# Turn states
INTRO = "intro"
PLAYER_TURN = "player_turn"
ACTION = "action"          # a scripted sequence is playing
RESULT = "result"          # win/loss modal is showing
ITEM_MENU = "item_menu"    # choosing an item from the bag

# The fight was laid out for an 800-wide screen; STAGE_X slides it to the middle of the real one
STAGE_X = (SCREEN_WIDTH - 800) // 2
HERO_HOME_X = 175 + STAGE_X  # Charlie's feet when waiting
DEFAULT_LUNGE = {"ghost": 300, "zombie": 70, "knight": 310, "satyr": 300}   # how far each surges at Charlie
                                                                           # (bosses set their own "lunge")
# Extra sound layered on "hurt" when an enemy's hit lands, by enemy kind
IMPACT_SOUNDS = {"zombie": "bite", "knight": "slash", "reaper": "slash", "demon": "slash",
                 "worm": "burn", "satyr": "burn"}
FIREBALL_MS = 380            # Fire Worm fireball travel time
FIREBALL_MOUTH = (215, 165)  # where the fireball leaves the worm: (in front of its feet, above them)
SPELL_GRAB_FRAME = 7.5       # Death's Grasp: the hand closes on Charlie at this frame of its spell
NOTICE = (255, 230, 120)
RING_TOP, RING_BOTTOM = 135, 505   # keep timing rings clear of the HUD and the move bar
COMBO_BLUE = (120, 220, 255)   # follow-up jab rings and combo counter
DAZE_GOLD = (255, 225, 90)
OFF_BALANCE = (255, 150, 80)
FLURRY_RED = (255, 130, 110)

# Crumb, the secret boss (core/levels.py SECRET_BOSS)
CRUMB_STRING_CHANCE = 0.5     # how often his regular attacks are flurries
CRUMB_FEINT_BONUS = 0.1      # on top of the chapter 4 boss feint chance
CRUMB_RISE_HEAL = 0.06        # share of max HP he heals each time he rises
CRUMB_RISE_DAMAGE = 1.12      # and how much harder he hits
BUTTER_SLICK_CHANCE = 0.3     # after his turn, from phase 2: the next turn's rings slide around
SLICK_MOTION = 2.2            # how much more the rings jump and drift while it's slick
BATTLE_LAYOUT_CRUMB_MID = 150
CAMP_ARENA = {"name": "The Camp", "background": "camp", "camp": True, "accent": (255, 170, 90), "monsters": []}   # the enemy's ring after a Haymaker (tighter windows)

WIN_COMMENTS = [
    "Not bad, kid.",
    "Sweet. Literally.",
    "That one's gonna feel it in the morning.",
    "Chin checked. Next!",
]

JACK_COMBAT_INTRO = [
    "Combat time!",
    "When you swing, hit SPACE as the ring closes. Nail it for a PERFECT.",
    "When they swing at you, hit SPACE right as it lands. Perfect timing is a PARRY.",
    "Jabs are quick. Keep hitting the rings to chain a combo and daze 'em... then land the Haymaker.",
    "Clean hits fill your Chin meter. Fill it up... then CHIN CHECK 'em.",
    "Hurting? Items has your Gourd-Aid. Chug one.",
]


class BattleScene:
    def __init__(self, screen, player, level=None, enemy_spec=None, first_strike=False):
        self.screen = screen
        self.player = player
        level = level or LEVELS[0]
        spec = enemy_spec or level["monsters"][0]
        if spec.get("arena") == "camp":       # Crumb's secret fight happens at camp
            level = CAMP_ARENA
        self.is_ghost = spec["sprite"] == "ghost"
        kind = spec.get("kind") or ("ghost" if self.is_ghost else "zombie")
        # Monsters get tougher deeper in, and with the difficulty setting (core/difficulty.py)
        self.chapter = spec.get("chapter", LEVELS.index(level) if level in LEVELS else 0)
        self.difficulty = options["difficulty"]
        boss = spec.get("boss", False)
        self.enemy = Enemy(kind=kind, mods=enemy_mods(self.chapter, boss, self.difficulty),
                           **{k: v for k, v in spec.items()
                              if k not in ("sprite", "first_strike", "kind", "lunge", "taunt", "defeat_quote")})
        self.ring_jump, self.ring_drift = ring_motion(self.chapter, boss, self.difficulty)
        self.slick = False                    # Crumb's Butter Slick: the rings slide much more for a turn
        if kind == "bread":                   # the secret boss strings hits and feints more than anyone
            self.enemy.string_chance = max(self.enemy.string_chance, CRUMB_STRING_CHANCE)
            self.enemy.feint_chance += CRUMB_FEINT_BONUS
        self.spec = spec
        self.lunge = spec.get("lunge", DEFAULT_LUNGE.get(kind, 70))
        self.foe_faces_right = faces_right_in_battle(spec["sprite"])
        layout = battle_layout(spec["sprite"])
        self.home_x = layout["home_x"] + STAGE_X   # enemy's feet when waiting
        self.strike_gap = layout["gap"]      # how close Charlie stands to punch
        self.foe_mid = layout["mid"]         # height of the enemy's body center
        self.aura_size = layout["aura"]
        self.shadow_size = layout["shadow"]
        self.hit_point = layout["hit_point"]  # damage lands this far through its attack animation
        self.glow = layout["glow"]            # boss color (aura, enrage, intro)
        self.glow_hot = tuple(min(255, c + 80) for c in self.glow)
        self.sparks = layout["sparks"]        # particle colors when it gets hit
        self.intro_anim = layout["intro"]
        self.sounds = layout["sounds"]
        self.boss_fx = boss_effects(spec["sprite"]) if self.enemy.boss else {}
        self.effects = []                     # one-shot boss effects: [Animation, x, y, elapsed, frame_ms]
        self.projectile = None                # the Fire Worm's fireball in flight

        self.rules = BattleManager(player, self.enemy, timing_scale(self.difficulty))
        if player.jam_start:                  # Crumb's Jam blessing (or Crumb himself): fights start with some Chin meter
            player.chin_meter = max(player.chin_meter, player.JAM_METER)
        self.options = CombatOptions(screen, player)
        self.item_picker = ItemPicker(screen, player)
        self.end_modal = EndCombatModal(screen)
        self.player_hud = PlayerHUD(screen, player)
        self.enemy_hud = EnemyHUD(screen, self.enemy)
        self.big_font = get_font(20, bold=True)

        # World
        self.background = load_background(level["background"])
        if self.background is None and level.get("camp"):
            self.background = camp_backdrop(screen.get_size())
        self.canvas = pygame.Surface(screen.get_size())
        self.grit = Grit(screen.get_size())
        self.grit.set_level(level)

        # Fighters
        self.hero = AnimatedSprite(load_gameart2d_character("charlie", HERO_HEIGHT, ink=CHARACTER_INK))
        self.hero_x = HERO_HOME_X
        # Crumb fights alongside Charlie once he's joined (Loaf Launch)
        self.crumb = AnimatedSprite(crumb_animations(CRUMB_TINTS[4])) if player.companion else None
        self.crumb_x, self.crumb_lift = HERO_HOME_X - 95, 0.0
        self.hero_facing = True
        self.hero_knock = 0.0
        self.foe = AnimatedSprite(enemy_animations(spec["sprite"], level.get("ghost_tint")))
        self.foe_sprite = spec["sprite"]
        self.foe_x = self.home_x
        self.foe_knock = 0.0

        # Juice
        self.shake = Shake()
        self.particles = Particles()
        self.swooshes = []
        self.afterimages = []
        self.texts = []
        self.ring = None
        self.feinting = False        # the enemy's current swing is a feint (it freezes mid-swing)
        self.hitstop = 0
        self.time_scale = 1.0
        self.slowmo_timer = 0
        self.zoom = 1.0
        self.zoom_target = 1.0
        self.zoom_focus = (self.home_x, FEET_Y - self.foe_mid)
        self.bomb_pos = None
        self.banner = None
        self.time = 0

        self.state = PLAYER_TURN
        self.script = None
        self.outcome = None          # "won" or "lost" once decided
        self.ready_to_exit = False   # main.py switches scenes when this is True
        self.first_strike = first_strike or spec.get("first_strike", False)

        self.enemy.plan_next_attack()
        player.off_balance = False

        self.whisper_jack = None
        if not game_state.whisper_jack_combat_intro_done:
            self.whisper_jack = JackPanel(JACK_COMBAT_INTRO)
            self.state = INTRO
        else:
            self._run(self._opening())

    # ---- helpers -----------------------------------------------------------
    def _run(self, generator):
        self.state = ACTION
        self.script = Script(generator)

    @property
    def hero_center(self):
        return (self.hero_x - self.hero_knock, FEET_Y - 75)

    @property
    def foe_center(self):
        return (self.foe_x + self.foe_knock, FEET_Y - self.foe_mid)

    def _say(self, text, pos, color=WHITE, size=22, bold=False, pop=False, life=1300):
        w = get_font(size, bold).size(text)[0]
        self.texts.append(CombatText(text, pos[0] - w / 2, pos[1], color, lifespan=life, size=size,
                                     bold=bold, pop=pop))

    def _shout(self, text, color=GOLD, size=46, y=200):
        self._say(text, (self.screen.get_width() / 2, y), color, size, bold=True, pop=True, life=1100)

    def _afterimage(self):
        surface, (ax, ay) = self.hero.current.frame(self.hero.index, self.hero_facing)
        self.afterimages.append([surface.copy(), self.hero_x - ax, FEET_Y - self.hero.lift - ay, 200])

    # ---- input -------------------------------------------------------------
    def handle_event(self, event):
        if self.state == RESULT:
            if self.end_modal.handle_event(event):
                self._finish()
        elif self.state == INTRO:
            self.whisper_jack.handle_event(event)
        elif self.state == PLAYER_TURN:
            choice = self.options.handle_event(event)
            if choice == ITEMS:                    # always opens, even just to look
                self.item_picker.open()
                self.state = ITEM_MENU
            elif choice:
                if self.options.available(choice):
                    self._run(self._round(choice))
                else:
                    reason = {CHIN_CHECK: "Chin meter not full!"}.get(choice, "Can't do that!")
                    self._say(reason, (self.hero_x, FEET_Y - 175), NOTICE)
        elif self.state == ITEM_MENU:
            picked = self.item_picker.handle_event(event)
            if picked == BACK:
                self.state = PLAYER_TURN
            elif picked:
                self._run(self._round(("item", picked)))
        elif self.state == ACTION and self.ring:
            pressed = event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN)
            clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            if pressed or clicked:
                self.ring.press()

    # ---- update ------------------------------------------------------------
    def update(self, dt):
        self.time += dt
        self.player_hud.update(dt)
        self.enemy_hud.update(dt)
        self.end_modal.update(dt)
        self.shake.update(dt)
        self.grit.update(dt)
        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.is_alive()]

        if self.hitstop > 0:          # freeze-frame on big hits
            self.hitstop -= dt
            return
        if self.slowmo_timer > 0:
            self.slowmo_timer -= dt
            if self.slowmo_timer <= 0:
                self.time_scale = 1.0
                self.zoom_target = 1.0
        self.zoom += (self.zoom_target - self.zoom) * min(1.0, dt / 120)

        wdt = dt * self.time_scale
        self.hero.update(wdt)
        if self.crumb:
            self.crumb.update(wdt)
        if not (self.ring and self.ring.stalled and self.state == ACTION and self.feinting):
            self.foe.update(wdt)                 # (a feint freezes the enemy mid-swing)
        if self.foe.name == "hit" and self.foe.finished:
            self.foe.play("idle")
        if self.enemy.enraged and self.enemy.is_alive and random.random() < wdt / 60:
            self.particles.burst(self.foe_x + self.foe_knock + random.uniform(-40, 40), FEET_Y - 10,
                                 [self.glow, self.glow_hot], 1, 50, 900, 5, gravity=-160)
        if self.player.burning and random.random() < wdt / 45:      # Charlie's on fire
            self.particles.burst(self.hero_x + random.uniform(-30, 30), FEET_Y - random.uniform(20, 120),
                                 [(255, 150, 40), (255, 220, 90), (230, 70, 20)], 1, 40, 600, 5, gravity=-220)
        self._update_effects(wdt)
        self.particles.update(wdt)
        for s in self.swooshes:
            s.update(wdt)
        self.swooshes = [s for s in self.swooshes if s.alive]
        for a in self.afterimages:
            a[3] -= wdt
        self.afterimages = [a for a in self.afterimages if a[3] > 0]
        self.foe_knock *= 0.5 ** (wdt / 70)
        self.hero_knock *= 0.5 ** (wdt / 70)
        if self.ring:
            self.ring.update(wdt)
        if self.state == ITEM_MENU:
            self.item_picker.update(dt)

        if self.state == INTRO:
            jack = self.whisper_jack
            jack.update(dt)
            if jack.message_done and not jack.fading_out:
                jack.fading_out = True
            if not jack.active:
                game_state.whisper_jack_combat_intro_done = True
                self._run(self._opening())
        elif self.script:
            self.script.update(wdt)
            if self.script.done:
                self.script = None

    # ---- round flow --------------------------------------------------------
    def _opening(self):
        if self.enemy.boss:
            sfx.play(self.sounds.get("laugh", "enrage"))
            self._shout(self.enemy.name.upper(), self.glow_hot, 40, y=200)
            self._say("BOSS BATTLE", (self.screen.get_width() / 2, 250), (230, 200, 255), 22, bold=True, life=1300)
            self.shake.add(12)
            cx, cy = self.foe_center
            self.particles.burst(cx, cy, [self.glow, self.glow_hot] + (self.sparks or []), 36, 520, 900, 8, drag=2.5)
            self.particles.dust(self.foe_x - 60, FEET_Y, math.pi)
            self.particles.dust(self.foe_x + 60, FEET_Y, 0.0)
            if self.foe.has(self.intro_anim):               # show off as the fight starts
                self.foe.play(self.intro_anim, restart=True)
            yield from wait(max(900, self.foe.current.duration if self.foe.has(self.intro_anim) else 0))
            self.foe.play("idle")
        if self.first_strike:
            yield from self._first_strike()
            if not self.enemy.is_alive:                     # (only with the one-hit cheat)
                yield from self._knockout()
                return
        yield from self._begin_player_turn(tick=False)

    def _round(self, choice):
        self.banner = None
        if choice in (JAB, HAYMAKER, CHIN_CHECK):
            yield from self._attack(choice)
        elif choice == LOAF:
            yield from self._loaf_launch()
        elif isinstance(choice, tuple) and choice[0] == "item":
            yield from self._use_item(choice[1])

        if not self.enemy.is_alive:
            yield from self._knockout()
            return
        if self.enemy.check_enrage():
            yield from self._enrage()
        if self.enemy.check_phase():
            yield from self._rise()
        yield from self._enemy_turn()
        if not self.enemy.is_alive:          # parry counter finished it
            yield from self._knockout()
            return
        if self.enemy.check_enrage():
            yield from self._enrage()
        if self.enemy.check_phase():
            yield from self._rise()
        if not self.player.is_alive and not (yield from self._survive()):
            return
        yield from self._begin_player_turn()

    def _begin_player_turn(self, tick=True):
        if tick:
            dmg = self.rules.infection_tick()
            if dmg:
                self.hero.flash = 120
                self.particles.goo(self.hero_x, FEET_Y - 90, 8)
                self._say(f"-{dmg} infection", (self.hero_x, FEET_Y - 175), (140, 230, 90))
                yield from wait(350)
                if not self.player.is_alive and not (yield from self._survive()):
                    return
            dmg = self.rules.burn_tick()
            if dmg:
                self.hero.flash = 120
                self.particles.burst(self.hero_x, FEET_Y - 80, [(255, 150, 40), (255, 220, 90)], 14, 220, 500, 6,
                                     gravity=-300)
                self._say(f"-{dmg} burn", (self.hero_x, FEET_Y - 175), (255, 160, 60))
                yield from wait(350)
                if not self.player.is_alive and not (yield from self._survive()):
                    return
        self.banner = None
        if self.enemy.next_heavy:
            self.banner = f"{self.enemy.name} is winding up {self.enemy.heavy_name}!"
        self.state = PLAYER_TURN

    def _survive(self):
        """Charlie hit 0 HP: use Resurrect Once if owned, otherwise lose. Returns True if alive."""
        if self.player.try_resurrect():
            self.hero.flash = 300
            self.particles.candy_corn(self.hero_x, FEET_Y - 80, 24)
            self._shout("RESURRECTED!", (255, 255, 120))
            yield from wait(600)
            return True
        yield from self._defeat()
        return False

    def _foe_flinch(self):
        """Enemies with a 'Take hit' animation flinch when struck (but not mid-attack or dying)."""
        if self.enemy.is_alive and self.foe.has("hit") and self.foe.name in ("idle", "hit"):
            self.foe.play("hit", restart=True)

    def _enrage(self):
        sfx.play("enrage")
        self._shout(f"{self.enemy.name.split()[0].strip(',').upper()} IS ENRAGED!", self.glow_hot, 38, y=210)
        self.shake.add(14)
        self.foe.flash = 250
        for _ in range(3):
            self.particles.burst(*self.foe_center, [self.glow, self.glow_hot, (255, 255, 255)], 18, 380, 700, 7,
                                 drag=2)
            yield from wait(180)
        yield from wait(300)

    def _rise(self):
        """Crumb reaches his next phase: he grows, toasts darker, heals a little, and hits harder."""
        phase = self.enemy.phase
        sfx.play("enrage")
        word = {2: "CRUMB IS TOASTED!", 3: "CRUMB IS BURNT!"}.get(phase, "CRUMB RISES!")
        self._shout("CRUMB RISES!", self.glow_hot, 46, y=200)
        self.shake.add(14)
        cx, cy = self.foe_center
        for _ in range(3):
            self.particles.burst(cx, cy, [self.glow, self.glow_hot, (255, 255, 230)], 20, 420, 800, 7, drag=2)
            yield from wait(160)
        self.foe.animations = crumb_boss_animations(phase)
        self.foe.play("idle", restart=True)
        self.foe_mid = round(BATTLE_LAYOUT_CRUMB_MID * CRUMB_PHASES[phase][0] / CRUMB_PHASES[1][0])
        healed = self.enemy.heal(round(self.enemy.max_hp * CRUMB_RISE_HEAL))
        self.enemy.damage_mult *= CRUMB_RISE_DAMAGE
        self.enemy.string_chance = min(0.8, self.enemy.string_chance + 0.1)
        self.foe.flash = 300
        self._say(word, (cx, cy - 210), (255, 200, 120), 26, bold=True, pop=True, life=1400)
        if healed:
            self._say(f"+{healed} HP", (cx, cy - 170), HEAL_GREEN, 26, bold=True, pop=True)
            self.particles.heal(cx, cy)
        yield from wait(700)

    def _butter_slick(self):
        """Crumb butters the floor: next turn the timing rings slide around much more."""
        self.slick = True
        self._shout("BUTTER SLICK!", (255, 225, 110), 40, y=210)
        self._say("The rings are slippery!", (self.screen.get_width() / 2, 255), (255, 240, 180), 20, bold=True,
                  life=1300)
        self.particles.burst(self.hero_x, FEET_Y - 10, [(255, 230, 120), (255, 245, 190)], 26, 300, 700, 6,
                             gravity=-120, drag=1.5)
        yield from wait(500)

    # ---- Charlie's moves ---------------------------------------------------
    def _dash(self, target_x, ms=260, facing=True):
        self.hero_facing = facing
        self.hero.play("run", restart=True, speed=1.4)
        if facing:
            sfx.play("whoosh", 0.5)
        self.particles.dust(self.hero_x, FEET_Y, math.pi if facing else 0)
        start = self.hero_x
        frame = [0]

        def step(t):
            self.hero_x = lerp(start, target_x, t)
            frame[0] += 1
            if frame[0] % 3 == 0:
                self._afterimage()
        yield from tween(ms, step, ease_in_out)
        self.hero.play("idle")
        self.hero_facing = True

    def _dash_back(self):
        yield from self._dash(HERO_HOME_X, 300, facing=False)

    def _attack(self, move):
        cfg = MOVES[move]
        yield from self._dash(self.foe_x - self.strike_gap)
        if move == JAB:
            yield from self._jab_combo()
        else:
            # Wind-up pose while the timing ring closes
            if move == CHIN_CHECK:
                self.hero.scale_x, self.hero.scale_y = 1.12, 0.82          # deep crouch
            else:
                self.hero.angle, self.hero.scale_y = 12, 0.94              # rear back
            timing = yield from self._ring(*self.rules.attack_ring(move), gather=move == CHIN_CHECK)
            result = self.rules.strike(move, timing)
            if move == CHIN_CHECK:
                yield from self._uppercut(result)
            else:
                yield from self._punch(move, result)
        self.hero.reset_pose()
        yield from wait(160)
        yield from self._dash_back()

    def _ring_spot(self, target, side=0):
        """Where a timing ring appears near `target`, and how it drifts while closing.
        side: 0 = anywhere, 1 = upper half, -1 = lower half (combo jabs alternate)."""
        angle = random.uniform(0, 2 * math.pi)
        if side:
            angle = random.uniform(math.pi * 1.1, math.pi * 1.9) if side > 0 else random.uniform(0.1, 0.9) * math.pi
        slick = SLICK_MOTION if self.slick else 1.0
        reach = self.ring_jump * slick * random.uniform(0.45, 1.0)
        x = target[0] + reach * math.cos(angle)
        y = target[1] + reach * math.sin(angle) * 0.8
        x = max(70, min(self.screen.get_width() - 70, x))
        y = max(RING_TOP, min(RING_BOTTOM, y))
        drift = (0, 0)
        if self.ring_drift:
            heading = random.uniform(0, 2 * math.pi)
            drift = (self.ring_drift * slick * math.cos(heading), self.ring_drift * slick * math.sin(heading))
        return (x, y), drift

    def _ring(self, ring_ms, perfect, good, color=(255, 215, 0), label="SPACE", gather=False, side=0):
        """Show a timing ring near the enemy and wait for Charlie's press. Returns the timing."""
        center, drift = self._ring_spot(self.foe_center, side)
        self.ring = TimingRing(center, ring_ms, perfect, good, color, label, drift=drift)
        while self.ring.result is None and not self.ring.expired:
            if gather and random.random() < 0.3:                      # Chin Check gathering power
                self.particles.burst(self.hero_x + random.uniform(-30, 30), FEET_Y - 10,
                                     [(255, 200, 60)], 1, 60, 500, 4, gravity=-200)
            yield
        timing = self.ring.final()
        self.ring = None
        return timing

    def _jab_combo(self):
        """Jab: a quick hit, and every Good/Perfect one brings up another, faster ring."""
        hit = 1
        while True:
            self.hero.angle = 5
            ring_ms, perfect, good = self.rules.jab_ring(hit)
            follow_up = hit > 1
            timing = yield from self._ring(ring_ms, perfect, good, COMBO_BLUE if follow_up else (255, 215, 0),
                                           f"x{hit}" if follow_up else "SPACE", side=1 if hit % 2 else -1)
            result = self.rules.strike(JAB, timing, hit)
            yield from self._punch(JAB, result)
            if not result.chain:
                return
            hit += 1
            self.hero.reset_pose()
            yield from wait(50)

    def _punch(self, move, result):
        big = move == HAYMAKER
        combo = result.combo if not big else 1
        self.hero.angle = -22 if big else -13
        self.hero.scale_x, self.hero.scale_y = (1.3, 0.9) if big else (1.16, 0.94)
        self.hero_x += 18 if big else (10 if combo == 1 else 4)       # follow-up jabs barely step in
        cx, cy = self.foe_center
        rise = (combo - 1) % 2 * 30                                     # alternate high and low jabs
        self.swooshes.append(Swoosh((self.hero_x + 20, cy - rise), 75 if big else 55,
                                    -70 if big else -40, 60 if big else 35, width=14 if big else 9))
        yield from self._show_strike(result, power=2 if big else 1)
        if big and self.enemy.is_alive:
            self._say("Off balance!", (self.hero_x, FEET_Y - 190), OFF_BALANCE, 18, bold=True, life=900)
        yield from wait(60 if not big else 90)

    def _uppercut(self, result):
        self.hero.reset_pose()
        self.hero.play("jump", restart=True, speed=1.6)
        cx, cy = self.foe_center
        self.swooshes.append(Swoosh((self.hero_x + 10, cy + 10), 80, 100, -60, color=(255, 210, 90),
                                    width=18, life=260))
        yield from tween(140, lambda t: setattr(self.hero, "lift", 95 * ease_out(t)))
        yield from self._show_strike(result, power=3)
        if result.damage and self.enemy.is_alive:
            # Launch the enemy, then let it drop
            yield from tween(220, lambda t: setattr(self.foe, "lift", 70 * ease_out(t)))
            yield from tween(200, lambda t: setattr(self.foe, "lift", 70 * (1 - ease_in(t))))
            self.shake.add(10)
            self.particles.dust(self.foe_x, FEET_Y)
        yield from tween(180, lambda t: setattr(self.hero, "lift", 95 * (1 - ease_in(t))))
        self.particles.dust(self.hero_x, FEET_Y)
        self.hero.play("idle")

    def _show_strike(self, result, power):
        """Shared impact for Jab/Haymaker/Chin Check."""
        cx, cy = self.foe_center
        head = (cx, cy - 95)
        if result.timing == PERFECT:
            self._say("PERFECT!", (cx, cy - 150), GOLD, 30, bold=True, pop=True)
        elif result.timing == GOOD:
            self._say("GOOD", (cx, cy - 150), WHITE, 24, bold=True, pop=True)
        if result.combo > 1:
            self._say(f"{result.combo} HIT COMBO!", (cx, cy - 185), COMBO_BLUE, 22 + 2 * result.combo,
                      bold=True, pop=True, life=900)

        if result.whiffed:
            sfx.play("miss")
            yield from tween(120, lambda t: setattr(self, "foe_knock", 45 * ease_out(t)))
            self._say("WHIFF!", head, (190, 190, 190), 26, bold=True)
            self.hero.angle = -30                                  # stumble forward
            yield from wait(200)
            return
        if result.phased:
            sfx.play("phase")
            self.foe.alpha = 90
            self.particles.wisps(cx, cy)
            self._say("PHASED THROUGH!", head, (200, 230, 255), 22, bold=True)
            yield from wait(300)
            self.foe.alpha = 255
            return

        perfect = result.timing == PERFECT
        # Impact sound: the Chin Check gets its own layered "super", a PERFECT hit a "crit"
        if power == 3:
            sfx.play("super")
            sfx.play("super_crack")
        elif perfect:
            sfx.play("crit")
        else:
            sfx.play("punch_heavy" if power > 1 else "punch")
        if power == 2:
            sfx.play("swing_heavy", 0.6)
        if result.armored:
            sfx.play("metal_clang")
            self._say("CLANG! Time it!", (cx, cy - 150), (200, 210, 235), 22, bold=True, pop=True)
        self._foe_flinch()
        self.foe.flash = 130
        self.foe_knock = 18 * power + (15 if perfect else 0)
        self.hitstop = 50 + 30 * power + (50 if perfect else 0)
        self.shake.add(4 * power + (6 if perfect else 0) + result.damage / 6)
        self.particles.hit_sparks(cx - 25, cy, 0.0, big=power > 1 or perfect)
        if self.is_ghost:
            self.particles.wisps(cx, cy, count=10)
        elif self.sparks:
            self.particles.burst(cx, cy - 10, self.sparks, 10 + 4 * power, 300, 600, 6, drag=2)
        else:
            self.particles.goo(cx, cy - 10, 10 + 4 * power)
        if perfect or power == 3:
            self.particles.candy_corn(cx, cy - 20, 14)
        size = min(48, 26 + result.damage // 2)
        self._say(f"-{result.damage}", head, DAMAGE_RED, size, bold=True, pop=True)
        if result.daze_used:                       # cashed in the Daze from the jabs
            self._say(f"DAZED SMASH +{round(self.rules.daze_bonus() * result.daze_used * 100)}%",
                      (cx, cy - 215), DAZE_GOLD, 22, bold=True, pop=True)
            self.particles.burst(cx, cy - 60, [DAZE_GOLD, (255, 255, 255)], 16, 320, 600, 5, drag=2)
        elif power == 1 and result.dazed and self.enemy.is_alive:
            self._say(f"DAZED x{result.dazed}", (cx + 70, cy - 120), DAZE_GOLD, 18, bold=True, life=800)
        if power == 3:
            self._shout("CHIN CHECK!!", GOLD if perfect else (255, 160, 40), 54)
        yield

    def _use_item(self, key):
        """Use an item from the bag: bombs get thrown, everything else gets drunk."""
        if ITEMS_BY_KEY[key].get("damage") == "bomb":
            yield from self._bomb()
            return
        result = self.player.use_item(key)
        sfx.play("heal")
        self.hero.play("jump", restart=True, speed=1.2)
        yield from tween(300, lambda t: setattr(self.hero, "lift", 26 * math.sin(math.pi * t)))
        self.hero.play("idle")
        hx = self.hero_x
        self._say(ITEMS_BY_KEY[key]["name"], (hx, FEET_Y - 230), (200, 225, 255), 20, bold=True)
        if result and result["healed"]:
            self.particles.heal(hx, FEET_Y - 80)
            self._say(f"+{result['healed']}", (hx, FEET_Y - 175), HEAL_GREEN, 30, bold=True, pop=True)
        if result and result["cured"]:
            self.particles.burst(hx, FEET_Y - 80, [(180, 255, 200), (255, 255, 255)], 16, 220, 600, 5, drag=2)
            self._say("Cured!", (hx, FEET_Y - 205), (180, 255, 160), 20, bold=True)
        if result and result["meter"]:
            self.particles.burst(hx, FEET_Y - 70, [GOLD, (255, 240, 160)], 22, 300, 700, 6, gravity=-200, drag=1.5)
            self._say(f"+{result['meter']} CHIN", (hx, FEET_Y - 175), GOLD, 28, bold=True, pop=True)
        yield from wait(380)

    def _bomb(self):
        self.hero.angle = 14
        yield from wait(140)
        self.hero.angle = -16
        sfx.play("whoosh", 0.7)
        start = (self.hero_x + 40, FEET_Y - 110)
        end = self.foe_center

        def fly(t):
            x = lerp(start[0], end[0], t)
            y = lerp(start[1], end[1], t) - 120 * math.sin(math.pi * t)
            self.bomb_pos = (x, y)
        yield from tween(430, fly)
        self.bomb_pos = None
        self.hero.reset_pose()
        dmg = self.rules.bomb()
        sfx.play("explosion")
        self._foe_flinch()
        cx, cy = end
        self.particles.explosion(cx, cy)
        self.foe.flash = 160
        self.foe_knock = 50
        self.hitstop = 110
        self.shake.add(18)
        self._say(f"-{dmg}", (cx, cy - 95), (255, 140, 60), 40, bold=True, pop=True)
        yield from wait(400)

    def _loaf_launch(self):
        """Crumb hurls himself at the enemy, spinning: a big hit that dazes it all the way."""
        self.options.loaf_used = True
        self._shout("LOAF LAUNCH!", (255, 205, 120), 42, y=180)
        sfx.play("swing_heavy")
        home = self.crumb_x
        cx, cy = self.foe_center
        rise = FEET_Y - cy                                  # how high the enemy's middle is
        self.crumb.play("jump", restart=True)

        def fly(k):
            self.crumb_x = lerp(home, cx - 30, k)
            self.crumb_lift = rise * k + 180 * 4 * k * (1 - k)
            self.crumb.angle = -720 * k

        yield from tween(400, fly, ease_in)
        dmg = self.rules.loaf_launch()
        sfx.play("crit")
        sfx.play("super_crack", 0.6)
        self._foe_flinch()
        self.foe.flash, self.foe_knock, self.hitstop = 140, 55, 120
        self.shake.add(16)
        self.particles.hit_sparks(cx - 25, cy, 0.0, big=True)
        self.particles.burst(cx - 20, cy, [(255, 215, 130), (230, 170, 80), (255, 240, 200)], 30, 420, 700, 6, drag=2.5)
        self._say(f"-{dmg}", (cx, cy - 95), DAMAGE_RED, 40, bold=True, pop=True)
        self._say(f"DAZED x{self.enemy.daze}", (cx + 70, cy - 135), DAZE_GOLD, 20, bold=True, life=1100)
        yield from wait(180)

        def back(k):
            self.crumb_x = lerp(cx - 30, home, k)
            self.crumb_lift = rise * (1 - k) + 120 * 4 * k * (1 - k)
            self.crumb.angle = -720 + 720 * k

        yield from tween(460, back, ease_out)
        self.crumb.angle, self.crumb_lift = 0, 0.0
        self.crumb.play("idle")
        yield from wait(150)

    def _first_strike(self):
        self._shout("FIRST STRIKE!", (255, 200, 80), 40, y=180)
        yield from self._dash(self.foe_x - self.strike_gap, 220)
        self.hero.angle, self.hero.scale_x = -18, 1.2
        dmg = self.rules.first_strike()
        sfx.play("crit")
        self._foe_flinch()
        cx, cy = self.foe_center
        self.foe.flash, self.foe_knock, self.hitstop = 120, 40, 90
        self.shake.add(10)
        self.particles.hit_sparks(cx - 25, cy, 0.0, big=True)
        self._say(f"-{dmg}", (cx, cy - 95), DAMAGE_RED, 34, bold=True, pop=True)
        yield from wait(160)
        self.hero.reset_pose()
        yield from self._dash_back()

    # ---- the enemy's turn --------------------------------------------------
    def _enemy_turn(self):
        """The enemy attacks: one swing, or from Chapter 2 on sometimes a flurry of 2-3."""
        heavy = self.enemy.next_heavy
        hits = (self.enemy.heavy_hits if heavy else self.enemy.next_hits)
        has_attack_anim = self.foe.has("attack")
        if hits > 1:
            fx, fy = self.foe_center
            label = f"{self.enemy.heavy_name.removeprefix('a ')}!" if heavy else f"{hits}-HIT FLURRY!"
            self._say(label, (fx, fy - 175), FLURRY_RED, 24, bold=True, pop=True, life=1200)
        was_slick = self.slick
        for hit in range(1, hits + 1):
            result = yield from self._enemy_swing(heavy, hit, hits, has_attack_anim)
            if result.killed and hit < hits:              # Charlie went down mid-flurry
                self.rules.end_enemy_turn()
                yield from self._retreat_foe(has_attack_anim)
                return
        if was_slick:
            self.slick = False
        elif self.enemy.kind == "bread" and self.enemy.phase >= 2 and self.enemy.is_alive \
                and random.random() < BUTTER_SLICK_CHANCE:
            yield from self._butter_slick()

    def _enemy_swing(self, heavy, hit, hits, has_attack_anim):
        """One enemy swing with its defense ring. Returns the DefenseResult."""
        kind = self.enemy.kind
        last = hit == hits
        if heavy and hit == 1:                        # wind-up tell
            yield from tween(320, lambda t: setattr(self.foe, "angle", 10 * math.sin(math.pi * t)))
        sound = self.sounds.get("heavy" if heavy else "attack") or \
            {"zombie": "zombie_bite", "ghost": "ghost_wail"}.get(kind, "whoosh")
        sfx.play(sound)
        if has_attack_anim:
            # Heavy attacks use a second attack animation when there is one (Hex Storm, Death's Grasp)
            move = "attack2" if heavy and self.foe.has("attack2") else "attack"
            speed = 1.0
            if heavy and move == "attack":   # bosses slow down to put their weight in; zombies lunge faster
                speed = 0.85 if self.enemy.boss else 1.25
            if hit > 1:                      # follow-up swings in a flurry come faster
                speed *= 1.3
            if self.enemy.enraged:
                speed *= 1.2
            self.foe.play(move, restart=True, speed=speed)
            impact_ms = self.foe.current.duration * self.hit_point / self.foe.speed
        else:
            impact_ms = 340 if hit == 1 else 260
        lunge = self.lunge
        launch_ms = None
        special = False
        if heavy and "fireball" in self.boss_fx:       # Fire Worm: spit a fireball from where it stands
            launch_ms = impact_ms
            impact_ms += FIREBALL_MS
            lunge = 0
            special = True
        if heavy and "spell" in self.boss_fx:          # Death's Grasp: a hand reaches out of a portal over Charlie
            self.effects.append([self.boss_fx["spell"], self.hero_x, FEET_Y + 8, 0.0, impact_ms / SPELL_GRAB_FRAME])
            lunge = 0
            special = True
        hold = random.randint(*FEINT_HOLD_MS) if not special and self.rules.roll_feint() else 0
        self.feinting = bool(hold)

        ring_color = (255, 90, 70) if heavy else (255, 215, 0)
        perfect, good = self.rules.defense_windows()       # tighter right after a Haymaker
        if self.player.off_balance:
            ring_color = OFF_BALANCE
            self.hero.angle = 8                             # still leaning from that swing
        center, drift = self._ring_spot(self.hero_center)
        label = f"{hit}/{hits}" if hits > 1 else "SPACE"
        crumb = kind == "bread"          # Crumb's feints are readable: a tell, and an early press is forgiven
        self.ring = TimingRing(center, impact_ms, perfect, good, ring_color, label, drift=drift, hold=hold,
                               forgive_early=crumb)
        start_x, target_x = self.foe_x, self.home_x - lunge
        elapsed = 0
        told = False
        while elapsed < self.ring.duration:
            elapsed += (yield)
            self.foe_x = lerp(start_x, target_x, ease_in(self.ring.progress))
            self.foe.angle = 3 * math.sin(self.time / 22) if self.ring.stalled else 0   # the feint's hitch
            if crumb and self.ring.stalled and not told:   # the tell: he flashes and goes "...!"
                told = True
                self.foe.flash = 110
                sfx.play("whoosh", 0.35)
                fx, fy = self.foe_center
                self._say("...!", (fx, fy - 150), (255, 230, 160), 24, bold=True, life=600)
            if launch_ms is not None and elapsed >= launch_ms and self.projectile is None:
                self._launch_fireball(impact_ms - elapsed)
        self.foe.angle = 0
        self.feinting = False
        timing = self.ring.result or MISS
        self.ring = None
        self.hero.reset_pose()

        result = self.rules.enemy_attack(timing, hit, hits)
        if self.projectile:                           # the fireball arrives
            self.projectile = None
            hx, hy = self.hero_center
            self._play_effect("explosion", hx + 20, hy - 10)
            self.particles.explosion(hx + 20, hy - 10)
            self.shake.add(10)
            sfx.play("explosion")
        if heavy and kind == "demon" and not result.parried:   # hellfire erupts under Charlie
            self.particles.explosion(self.hero_x, FEET_Y - 30)
            self.particles.burst(self.hero_x, FEET_Y, [(255, 120, 30), (255, 210, 80), (200, 40, 20)], 40, 600, 700,
                                 8, gravity=-500, direction=-math.pi / 2, spread=0.9, drag=1.5)
            self.shake.add(14)
        hx, hy = self.hero_center
        if hold and timing == MISS and result.damage:
            self._say("Feint!", (hx + 60, hy - 60), (255, 200, 150), 18, bold=True, life=800)
        if result.parried:
            sfx.play("parry")
            self.particles.hit_sparks(hx + 40, hy, math.pi, big=last)
            self.shake.add(9 if last else 5)
            self.foe_knock = 30 if last else 16
            if not last:                              # mid-flurry: deflect it and get ready for the next
                self._say("PARRY!", (hx, hy - 125), GOLD, 26, bold=True, pop=True)
                self.hitstop = 80
                yield from wait(110)
                return result
            self._shout("PARRY!", GOLD, 44, y=230)
            self.hitstop = 130
            yield from self._retreat_foe(has_attack_anim)
            yield from self._counter(result)
            return result
        if result.timed_block:
            sfx.play("block")
            self._say("BLOCKED!", (hx, hy - 125), BLOCK_BLUE, 26, bold=True, pop=True)
            self.particles.hit_sparks(hx + 40, hy, math.pi)
        sfx.play("hurt_heavy" if heavy else "hurt")
        impact = IMPACT_SOUNDS.get(kind)            # what the hit feels like: a bite, a blade, fire...
        if impact and result.damage:
            sfx.play(impact)
        self.hero.flash = 120
        self.hero_knock = 12 + result.damage
        self.hitstop = 90 if heavy else 60
        self.shake.add(4 + result.damage / 2.5)
        if self.enemy.kind == "zombie":
            self.particles.goo(hx + 20, hy - 20, 6)
        elif self.sparks:
            self.particles.burst(hx + 10, hy - 20, self.sparks, 14, 260, 600, 6, drag=2)
        self._say(f"-{result.damage}", (hx, hy - 95), DAMAGE_RED, min(46, 24 + result.damage), bold=True, pop=True)
        if result.infected:
            self._say("INFECTED!", (hx, hy - 150), (140, 230, 90), 24, bold=True, pop=True)
        if result.shrugged:
            self._say("Thick Skin! Shrugged it off", (hx, hy - 180), (200, 220, 160), 20, bold=True, pop=True)
        if result.off_balance and result.damage and hit == 1:
            self._say("Caught off balance!", (hx, hy - 210), OFF_BALANCE, 18, bold=True, life=900)
        if result.drained:
            word = "HEXED" if self.enemy.kind == "warlock" else "SCORCHED"
            self._say(f"{word}! Chin -{result.drained}", (hx, hy - 150), self.glow_hot, 24, bold=True, pop=True)
        if result.burned:
            sfx.play("burn")
            self._say("BURNING!", (hx, hy - 180), (255, 150, 50), 24, bold=True, pop=True)
            self.particles.burst(hx, hy, [(255, 150, 40), (255, 220, 90), (230, 70, 20)], 24, 320, 700, 7,
                                 gravity=-250, drag=1.5)
        if result.snatched:                          # Gorge grabs a fistful of candy and gulps it down
            fx, fy = self.foe_center
            sfx.play("bite", 0.8)
            self.particles.burst(self.hero_x, FEET_Y - 90, [(255, 200, 90), (255, 120, 60), (255, 240, 200)],
                                 18, 380, 700, 6, drag=2.0)
            self._say(f"-{result.snatched} candy!", (self.hero_x, FEET_Y - 220), (255, 200, 90), 26, bold=True,
                      pop=True, life=1500)
        if result.stolen:
            fx, fy = self.foe_center
            self._say(f"+{result.stolen} HP stolen", (fx, fy - 170), (150, 255, 160), 24, bold=True, pop=True)
            self.particles.burst(hx, hy - 20, [self.glow, (40, 30, 60)], 16, 200, 700, 6, gravity=-120, drag=1)
            self.particles.heal(fx, fy)
        if last:
            yield from self._retreat_foe(has_attack_anim)
        else:
            yield from wait(140)
        return result

    def _retreat_foe(self, has_attack_anim):
        if has_attack_anim:
            while self.foe.index < len(self.foe.current) - 1:
                yield
            self.foe.play("idle")
        self.foe.angle = 0
        start = self.foe_x
        yield from tween(240, lambda t: setattr(self, "foe_x", lerp(start, self.home_x, ease_out(t))))
        yield from wait(150)

    def _counter(self, result):
        """Perfect parry: Charlie slide-kicks the enemy."""
        self.hero.play("slide", restart=True)
        sfx.play("dodge")
        start = self.hero_x
        target = self.foe_x - self.strike_gap + 15
        yield from tween(230, lambda t: setattr(self, "hero_x", lerp(start, target, ease_out(t))))
        cx, cy = self.foe_center
        sfx.play("counter")
        self._foe_flinch()
        self.foe.flash, self.foe_knock, self.hitstop = 120, 35, 80
        self.shake.add(8)
        self.particles.hit_sparks(cx - 25, cy + 30, 0.0, big=True)
        self._say(f"-{result.counter}", (cx, cy - 95), DAMAGE_RED, 32, bold=True, pop=True)
        self._say("COUNTER!", (cx, cy - 135), (255, 200, 80), 22, bold=True)
        if result.dazed:
            self._say(f"DAZED x{result.dazed}", (cx + 70, cy - 120), DAZE_GOLD, 18, bold=True, life=800)
        yield from wait(280)
        self.hero.play("idle")
        yield from self._dash_back()

    def _draw_daze(self, surface, fx):
        """Little stars circling over a dazed enemy's head, one per stack."""
        head_y = FEET_Y - min(2 * self.foe_mid, 330) - 6
        n = self.enemy.daze
        for i in range(n):
            a = self.time / 260 + i * 2 * math.pi / n
            x, y = fx + 34 * math.cos(a), head_y + 9 * math.sin(a)
            r = 7 + 2 * math.sin(a)                       # bigger when in front
            points = [(x + (r if k % 2 == 0 else r * 0.45) * math.cos(k * math.pi / 5 - math.pi / 2),
                       y + (r if k % 2 == 0 else r * 0.45) * math.sin(k * math.pi / 5 - math.pi / 2))
                      for k in range(10)]
            pygame.draw.polygon(surface, INK, [(px + 1, py + 1) for px, py in points])
            pygame.draw.polygon(surface, DAZE_GOLD, points)

    # ---- boss effects ------------------------------------------------------
    def _play_effect(self, name, x, y):
        anim = self.boss_fx.get(name)
        if anim:
            self.effects.append([anim, x, y, 0.0, anim.frame_ms])

    def _launch_fireball(self, travel_ms):
        start = (self.foe_x - FIREBALL_MOUTH[0], FEET_Y - FIREBALL_MOUTH[1])
        end = (self.hero_x + 20, FEET_Y - 85)
        self.projectile = {"start": start, "end": end, "t": 0.0, "ms": max(1.0, travel_ms), "pos": start}
        self.particles.burst(*start, [(255, 150, 40), (255, 220, 90)], 12, 260, 400, 6, direction=math.pi, spread=1.2)

    def _update_effects(self, dt):
        for fx in self.effects:
            fx[3] += dt
        self.effects = [fx for fx in self.effects if fx[3] / fx[4] < len(fx[0])]
        p = self.projectile
        if p:
            p["t"] = min(1.0, p["t"] + dt / p["ms"])
            t = p["t"]
            (x0, y0), (x1, y1) = p["start"], p["end"]
            p["pos"] = (lerp(x0, x1, t), lerp(y0, y1, t) - 60 * math.sin(math.pi * t))   # a little arc
            if random.random() < dt / 25:                                                    # fiery trail
                self.particles.burst(*p["pos"], [(255, 150, 40), (255, 220, 90), (120, 60, 40)], 1, 60, 400, 6,
                                     gravity=-80)

    def _draw_effects(self, surface):
        for anim, x, y, elapsed, frame_ms in self.effects:
            index = min(len(anim) - 1, int(elapsed / frame_ms))
            image, (ax, ay) = anim.frame(index, True)
            surface.blit(image, (x - ax, y - ay))
        p = self.projectile
        if p and "fireball" in self.boss_fx:
            anim = self.boss_fx["fireball"]
            image, (ax, ay) = anim.frame(int(self.time / anim.frame_ms) % len(anim), False)   # flying left
            surface.blit(image, (p["pos"][0] - ax, p["pos"][1] - ay))

    # ---- endings -----------------------------------------------------------
    def _knockout(self):
        self.ring = None
        self.time_scale = 0.25
        self.slowmo_timer = 750
        self.zoom_target = 1.18
        self.zoom_focus = self.foe_center
        sfx.play("ko")
        if self.enemy.kind == "zombie":
            sfx.play("gore")
        self._shout("K.O.!", (255, 70, 50), 72, y=105)
        self.foe.reset_pose()
        self.foe.play("dead", restart=True)
        if self.hero_x != HERO_HOME_X:
            yield from self._dash_back()
        while not self.foe.finished:
            yield
        if self.is_ghost:
            self.particles.wisps(*self.foe_center, count=20)
        # Victory hop
        self.hero.play("jump", restart=True)
        yield from tween(420, lambda t: setattr(self.hero, "lift", 45 * math.sin(math.pi * t)))
        self.hero.play("idle")
        self._win()

    def _defeat(self):
        self.ring = None
        self.hero.reset_pose()
        self.hero.play("dead", restart=True)
        sfx.play("defeat")
        self.shake.add(12)
        while not self.hero.finished:
            yield
        yield from wait(500)
        self._lose()

    def _win(self):
        sfx.play("victory")
        earned = self.rules.award_candy()
        self.player.battles_won += 1
        if self.enemy.kind == "bread":          # Crumb, beaten: he joins Charlie (the camp plays his speech)
            self.player.join_crumb()
        game_state.first_battle_done = True
        self.outcome = "won"
        self.state = RESULT
        rewards = [Reward("candy", "candy", earned, (255, 200, 90))]
        if self.enemy.boss:
            rewards.append(Reward("bomb", "bombs", self.rules.award_boss_loot(), (255, 170, 90)))
        for key in self.rules.award_loot():     # trophies to sell to the Crow, and sometimes a Gourd-Aid
            item = ITEMS_BY_KEY[key]
            rewards.append(Reward(item["icon"], item["name"], 1, (200, 225, 255)))
        if self.enemy.boss:
            self.end_modal.open("Boss Defeated!", rewards, subtitle=f"{self.enemy.name} has fallen.", mood="boss",
                                quote=self.spec.get("defeat_quote", "Now THAT'S a chin check."))
            return
        self.end_modal.open("Victory!", rewards, quote=random.choice(WIN_COMMENTS),
                            subtitle=f"{self.enemy.name} got chin checked.")

    def _lose(self):
        """Charlie's down. main.py sends him back to the last camp (or the start of Chapter 1)."""
        self.player.stats["losses"] += 1
        self.outcome = "lost"
        self.state = RESULT
        at_camp = save_game.latest is not None
        self.end_modal.open("Chin Checked!", [],
                            quote="Get up, kid. Pumpkins bounce.",
                            subtitle="Back to your last camp." if at_camp else "Back to the start of the chapter.",
                            button_label="Back to Camp" if at_camp else "Try Again", mood="lose")

    def _finish(self):
        self.player.off_balance = False
        if self.outcome == "lost":    # Charlie gets back up fresh (ailments carry over after a win)
            self.player.hp = self.player.max_hp
            self.player.infected = self.player.burning = 0
        self.ready_to_exit = True

    # ---- drawing -----------------------------------------------------------
    def draw(self):
        c = self.canvas
        if self.background:
            c.blit(self.background, (0, 0))
        else:
            c.fill((10, 10, 10))

        hx = self.hero_x - self.hero_knock
        fx = self.foe_x + self.foe_knock
        self.grit.draw_shadow(c, hx, FEET_Y, 0.9 - min(0.4, self.hero.lift / 250))
        show_foe = self.enemy.is_alive or not (self.is_ghost and self.foe.finished)
        if show_foe:
            if self.enemy.boss and self.enemy.is_alive:
                glow = aura(self.glow_hot if self.enemy.enraged else self.glow, self.aura_size or (240, 280))
                glow.set_alpha(int(200 + 55 * math.sin(self.time / 300)))
                c.blit(glow, glow.get_rect(midbottom=(fx, FEET_Y + 30)))
            shadow = self.shadow_size if self.enemy.is_alive or self.foe_sprite != "gorge" else 0.8   # (he shrinks)
            self.grit.draw_shadow(c, fx, FEET_Y, shadow * (1.0 - min(0.4, self.foe.lift / 250)))
            draw_spotlight(c, self.foe_sprite, self.foe, fx, FEET_Y, self.foe_faces_right)   # (Gorge's, as he falls)
            self.foe.draw(c, fx, FEET_Y, facing_right=self.foe_faces_right)
        for surf, x, y, life in self.afterimages:
            surf.set_alpha(int(110 * life / 200))
            c.blit(surf, (x, y))
        if self.crumb:                                   # Crumb, right behind Charlie
            self.grit.draw_shadow(c, self.crumb_x, FEET_Y, 0.55)
            self.crumb.draw(c, self.crumb_x, FEET_Y - self.crumb_lift, True)
        self.hero.draw(c, hx, FEET_Y, self.hero_facing)
        self._draw_effects(c)
        if self.enemy.daze and self.enemy.is_alive:
            self._draw_daze(c, fx)
        if self.bomb_pos:
            bx, by = self.bomb_pos
            pygame.draw.circle(c, (230, 220, 200), (int(bx), int(by)), 13)          # light rim so it reads on dark levels
            pygame.draw.circle(c, (20, 20, 25), (int(bx), int(by)), 11)
            pygame.draw.circle(c, (110, 110, 125), (int(bx - 4), int(by - 4)), 3)
            pygame.draw.line(c, (200, 160, 90), (bx + 5, by - 9), (bx + 10, by - 16), 3)
            pygame.draw.circle(c, (255, 220, 120), (int(bx + 11), int(by - 17)), 3 + int(self.time / 40) % 3)
        for s in self.swooshes:
            s.draw(c)
        self.particles.draw(c)
        self.grit.draw_fog(c)

        # Camera: zoom (on knockouts) and shake
        ox, oy = self.shake.offset
        if self.zoom > 1.005:
            w, h = c.get_size()
            view = pygame.Rect(0, 0, int(w / self.zoom), int(h / self.zoom))
            view.center = self.zoom_focus
            view.clamp_ip(c.get_rect())
            self.screen.blit(pygame.transform.smoothscale(c.subsurface(view), (w, h)), (ox, oy))
        else:
            self.screen.blit(c, (ox, oy))
        self.grit.apply(self.screen)

        # UI layer (crisp, not color graded)
        if self.ring:
            self.ring.draw(self.screen)
        self.player_hud.draw()
        self.enemy_hud.draw()
        if cheats.one_shot():                          # a reminder that the one-hit cheat is on
            tag = outlined_text("CHEAT: ONE-HIT KO", 14, (255, 120, 200), True, 2)
            self.screen.blit(tag, tag.get_rect(midtop=(self.screen.get_width() // 2, 8)))
        if self.banner and self.state == PLAYER_TURN:
            pulse = int(200 + 55 * math.sin(self.time / 140))
            text = outlined_text("!! " + self.banner, 19, (255, pulse // 2, 60), True, 2)
            self.screen.blit(text, text.get_rect(topright=(self.screen.get_width() - 18, 100)))
        for t in self.texts:
            t.draw(self.screen)
        if self.state == INTRO:
            self.whisper_jack.draw(self.screen)
        elif self.state == PLAYER_TURN:
            self.options.draw()
        elif self.state == ITEM_MENU:
            self.options.draw(show_hint=False)
            self.item_picker.draw()
        self.end_modal.draw()
