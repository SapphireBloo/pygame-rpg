"""Turn-based fights, played out as animated sequences.

Each round is a "script" (see core/effects.py): Charlie's move, the enemy's
attack, then back to the menu. Timing rings appear during attacks and enemy
swings; Space presses are routed to whichever ring is active.
"""
import math
import random

import pygame

from core import game_state
from core import sfx
from core.animation import AnimatedSprite, load_gameart2d_character
from core.assets import load_frames, load_background
from core.battle_manager import BattleManager, MOVES, DEFENSE_PERFECT_MS, DEFENSE_GOOD_MS
from core.combat_options import CombatOptions, JAB, HAYMAKER, CHIN_CHECK, HEAL, BOMB
from core.combat_text import CombatText
from core.effects import (Script, Shake, Particles, Swoosh, TimingRing, wait, tween, lerp, aura,
                          ease_out, ease_in, ease_in_out, PERFECT, GOOD, MISS)
from core.end_combat_modal import EndCombatModal, Reward
from core.enemy import Enemy
from core.enemy_art import enemy_animations, faces_right_in_battle, battle_layout, boss_effects
from core.enemy_hud import EnemyHUD
from core.grit import Grit
from core.levels import LEVELS
from core.player_hud import PlayerHUD
from core.settings import GROUND_Y, FEET_Y, HERO_HEIGHT, CHARACTER_INK
from core.skeleton_animation import SkeletonAnimation
from core.ui import get_font, BLOCK_BLUE, WHITE, DAMAGE_RED, HEAL_GREEN, GOLD

# Turn states
INTRO = "intro"
PLAYER_TURN = "player_turn"
ACTION = "action"          # a scripted sequence is playing
RESULT = "result"          # win/loss modal is showing

HERO_HOME_X = 175          # Charlie's feet when waiting
DEFAULT_LUNGE = {"ghost": 300, "zombie": 70}   # how far each type surges at Charlie (bosses set "lunge")
FIREBALL_MS = 380            # Fire Worm fireball travel time
FIREBALL_MOUTH = (215, 165)  # where the fireball leaves the worm: (in front of its feet, above them)
SPELL_GRAB_FRAME = 7.5       # Death's Grasp: the hand closes on Charlie at this frame of its spell
NOTICE = (255, 230, 120)

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
    "Clean hits fill your Chin meter. Fill it up... then CHIN CHECK 'em.",
]


class BattleScene:
    def __init__(self, screen, player, level=None, enemy_spec=None, first_strike=False):
        self.screen = screen
        self.player = player
        level = level or LEVELS[0]
        spec = enemy_spec or {"sprite": "ghost", **level["enemy"]}
        self.is_ghost = spec["sprite"] == "ghost"
        kind = spec.get("kind") or ("ghost" if self.is_ghost else "zombie")
        self.enemy = Enemy(kind=kind, **{k: v for k, v in spec.items()
                                         if k not in ("sprite", "first_strike", "kind", "lunge", "taunt", "defeat_quote")})
        self.spec = spec
        self.lunge = spec.get("lunge", DEFAULT_LUNGE.get(kind, 70))
        self.foe_faces_right = faces_right_in_battle(spec["sprite"])
        layout = battle_layout(spec["sprite"])
        self.home_x = layout["home_x"]       # enemy's feet when waiting
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

        self.rules = BattleManager(player, self.enemy)
        self.options = CombatOptions(screen, player)
        self.end_modal = EndCombatModal(screen)
        self.player_hud = PlayerHUD(screen, player)
        self.enemy_hud = EnemyHUD(screen, self.enemy)
        self.big_font = get_font(20, bold=True)

        # World
        self.background = load_background(level["background"])
        self.canvas = pygame.Surface(screen.get_size())
        self.grit = Grit(screen.get_size())
        self.grit.set_level(level)

        # Fighters
        self.hero = AnimatedSprite(load_gameart2d_character("charlie", HERO_HEIGHT, ink=CHARACTER_INK))
        self.hero_x = HERO_HOME_X
        self.hero_facing = True
        self.hero_knock = 0.0
        self.foe = AnimatedSprite(enemy_animations(spec["sprite"], level.get("ghost_tint")))
        self.foe_x = self.home_x
        self.foe_knock = 0.0

        # Juice
        self.shake = Shake()
        self.particles = Particles()
        self.swooshes = []
        self.afterimages = []
        self.texts = []
        self.ring = None
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
        if player.has("auto_block"):
            player.block()

        self.whisper_jack = None
        if not game_state.whisper_jack_combat_intro_done:
            frames = load_frames("Skeleton", flip_x=True)
            self.whisper_jack = SkeletonAnimation(330, GROUND_Y, frames, JACK_COMBAT_INTRO)
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
            if choice:
                if self.options.available(choice):
                    self._run(self._round(choice))
                else:
                    reason = {CHIN_CHECK: "Chin meter not full!", HEAL: "Can't eat candy now!",
                              BOMB: "No bombs!"}.get(choice, "Can't do that!")
                    self._say(reason, (self.hero_x, FEET_Y - 175), NOTICE)
        elif self.state == ACTION:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN) and self.ring:
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
        self.foe.update(wdt)
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
        yield from self._begin_player_turn(tick=False)

    def _round(self, choice):
        self.banner = None
        if choice in (JAB, HAYMAKER, CHIN_CHECK):
            yield from self._attack(choice)
        elif choice == HEAL:
            yield from self._heal()
        elif choice == BOMB:
            yield from self._bomb()

        if not self.enemy.is_alive:
            yield from self._knockout()
            return
        if self.enemy.check_enrage():
            yield from self._enrage()
        yield from self._enemy_turn()
        if not self.enemy.is_alive:          # parry counter finished it
            yield from self._knockout()
            return
        if self.enemy.check_enrage():
            yield from self._enrage()
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

    # ---- Charlie's moves ---------------------------------------------------
    def _dash(self, target_x, ms=260, facing=True):
        self.hero_facing = facing
        self.hero.play("run", restart=True, speed=1.4)
        if facing:
            sfx.play("whoosh", 0.6)
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

        # Wind-up pose while the timing ring closes
        if move == CHIN_CHECK:
            self.hero.scale_x, self.hero.scale_y = 1.12, 0.82          # deep crouch
        elif move == HAYMAKER:
            self.hero.angle, self.hero.scale_y = 12, 0.94              # rear back
        else:
            self.hero.angle = 5
        self.ring = TimingRing(self.foe_center, cfg["ring_ms"], cfg["perfect"], cfg["good"])
        while self.ring.result is None and not self.ring.expired:
            if move == CHIN_CHECK and random.random() < 0.3:          # gathering power
                self.particles.burst(self.hero_x + random.uniform(-30, 30), FEET_Y - 10,
                                     [(255, 200, 60)], 1, 60, 500, 4, gravity=-200)
            yield
        timing = self.ring.final()
        self.ring = None

        result = self.rules.strike(move, timing)
        if move == CHIN_CHECK:
            yield from self._uppercut(result)
        else:
            yield from self._punch(move, result)
        self.hero.reset_pose()
        yield from wait(160)
        yield from self._dash_back()

    def _punch(self, move, result):
        big = move == HAYMAKER
        self.hero.angle = -22 if big else -13
        self.hero.scale_x, self.hero.scale_y = (1.3, 0.9) if big else (1.16, 0.94)
        self.hero_x += 18 if big else 10
        cx, cy = self.foe_center
        self.swooshes.append(Swoosh((self.hero_x + 20, cy), 75 if big else 55,
                                    -70 if big else -40, 60 if big else 35, width=14 if big else 9))
        yield from self._show_strike(result, power=2 if big else 1)
        yield from wait(90)

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

        if result.timing == PERFECT:
            sfx.play("perfect")
        if result.whiffed:
            sfx.play("miss")
            yield from tween(120, lambda t: setattr(self, "foe_knock", 45 * ease_out(t)))
            self._say("WHIFF!", head, (190, 190, 190), 26, bold=True)
            self.hero.angle = -30                                  # stumble forward
            yield from wait(200)
            return
        if result.phased:
            sfx.play("ghost_wail", 0.6)
            self.foe.alpha = 90
            self.particles.wisps(cx, cy)
            self._say("PHASED THROUGH!", head, (200, 230, 255), 22, bold=True)
            yield from wait(300)
            self.foe.alpha = 255
            return

        perfect = result.timing == PERFECT
        sfx.play("punch_heavy" if power > 1 else "punch")
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
        if power == 3:
            self._shout("CHIN CHECK!!", GOLD if perfect else (255, 160, 40), 54)
        yield

    def _heal(self):
        cured = self.player.infected > 0
        healed = self.rules.heal()
        sfx.play("heal")
        yield from tween(260, lambda t: setattr(self.hero, "lift", 22 * math.sin(math.pi * t)))
        self.particles.heal(self.hero_x, FEET_Y - 80)
        if healed:
            self._say(f"+{healed}", (self.hero_x, FEET_Y - 175), HEAL_GREEN, 30, bold=True, pop=True)
        if cured:
            self._say("Cured!", (self.hero_x, FEET_Y - 205), (180, 255, 160), 20, bold=True)
        yield from wait(350)

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

    def _first_strike(self):
        self._shout("FIRST STRIKE!", (255, 200, 80), 40, y=180)
        yield from self._dash(self.foe_x - self.strike_gap, 220)
        self.hero.angle, self.hero.scale_x = -18, 1.2
        dmg = self.rules.first_strike()
        sfx.play("punch_heavy")
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
        heavy = self.enemy.next_heavy
        kind = self.enemy.kind
        if heavy:                                     # wind-up tell
            yield from tween(320, lambda t: setattr(self.foe, "angle", 10 * math.sin(math.pi * t)))
        has_attack_anim = self.foe.has("attack")
        sound = self.sounds.get("heavy" if heavy else "attack") or \
            {"zombie": "zombie_bite", "ghost": "ghost_wail"}.get(kind, "whoosh")
        sfx.play(sound)
        if has_attack_anim:
            # Heavy attacks use a second attack animation when there is one (Hex Storm, Death's Grasp)
            move = "attack2" if heavy and self.foe.has("attack2") else "attack"
            speed = 1.0
            if heavy and move == "attack":   # bosses slow down to put their weight in; zombies lunge faster
                speed = 0.85 if self.enemy.boss else 1.25
            if self.enemy.enraged:
                speed *= 1.2
            self.foe.play(move, restart=True, speed=speed)
            impact_ms = self.foe.current.duration * self.hit_point / self.foe.speed
        else:
            impact_ms = 340
        lunge = self.lunge
        launch_ms = None
        if heavy and "fireball" in self.boss_fx:       # Fire Worm: spit a fireball from where it stands
            launch_ms = impact_ms
            impact_ms += FIREBALL_MS
            lunge = 0
        if heavy and "spell" in self.boss_fx:          # Death's Grasp: a hand reaches out of a portal over Charlie
            self.effects.append([self.boss_fx["spell"], self.hero_x, FEET_Y + 8, 0.0, impact_ms / SPELL_GRAB_FRAME])
            lunge = 0
        ring_color = (255, 90, 70) if heavy else (255, 215, 0)
        self.ring = TimingRing(self.hero_center, impact_ms, DEFENSE_PERFECT_MS, DEFENSE_GOOD_MS, ring_color)
        elapsed = 0
        while elapsed < impact_ms:
            elapsed += (yield)
            self.foe_x = self.home_x - lunge * ease_in(min(1.0, elapsed / impact_ms))
            if launch_ms is not None and elapsed >= launch_ms and self.projectile is None:
                self._launch_fireball(impact_ms - elapsed)
        timing = self.ring.result or MISS
        self.ring = None

        result = self.rules.enemy_attack(timing)
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
        if result.parried:
            sfx.play("parry")
            self._shout("PARRY!", GOLD, 44, y=230)
            self.particles.hit_sparks(hx + 40, hy, math.pi, big=True)
            self.hitstop = 130
            self.shake.add(9)
            self.foe_knock = 30
            yield from self._retreat_foe(has_attack_anim)
            yield from self._counter(result)
            return
        if result.timed_block or result.stance_block:
            sfx.play("block")
            self._say("BLOCKED!", (hx, hy - 125), BLOCK_BLUE, 26, bold=True, pop=True)
            self.particles.hit_sparks(hx + 40, hy, math.pi)
        sfx.play("hurt")
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
        if result.drained:
            word = "HEXED" if self.enemy.kind == "warlock" else "SCORCHED"
            self._say(f"{word}! Chin -{result.drained}", (hx, hy - 150), self.glow_hot, 24, bold=True, pop=True)
        if result.burned:
            sfx.play("burn")
            self._say("BURNING!", (hx, hy - 180), (255, 150, 50), 24, bold=True, pop=True)
            self.particles.burst(hx, hy, [(255, 150, 40), (255, 220, 90), (230, 70, 20)], 24, 320, 700, 7,
                                 gravity=-250, drag=1.5)
        if result.stolen:
            fx, fy = self.foe_center
            self._say(f"+{result.stolen} HP stolen", (fx, fy - 170), (150, 255, 160), 24, bold=True, pop=True)
            self.particles.burst(hx, hy - 20, [self.glow, (40, 30, 60)], 16, 200, 700, 6, gravity=-120, drag=1)
            self.particles.heal(fx, fy)
        yield from self._retreat_foe(has_attack_anim)

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
        start = self.hero_x
        target = self.foe_x - self.strike_gap + 15
        yield from tween(230, lambda t: setattr(self, "hero_x", lerp(start, target, ease_out(t))))
        cx, cy = self.foe_center
        sfx.play("punch")
        self._foe_flinch()
        self.foe.flash, self.foe_knock, self.hitstop = 120, 35, 80
        self.shake.add(8)
        self.particles.hit_sparks(cx - 25, cy + 30, 0.0, big=True)
        self._say(f"-{result.counter}", (cx, cy - 95), DAMAGE_RED, 32, bold=True, pop=True)
        self._say("COUNTER!", (cx, cy - 135), (255, 200, 80), 22, bold=True)
        yield from wait(280)
        self.hero.play("idle")
        yield from self._dash_back()

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
        game_state.first_battle_done = True
        self.outcome = "won"
        self.state = RESULT
        if self.enemy.boss:
            bombs = self.rules.award_boss_loot()
            self.end_modal.open("Boss Defeated!", [
                Reward("candy", "candy", earned, (255, 200, 90)),
                Reward("bomb", "bombs", bombs, (255, 170, 90)),
            ], quote=self.spec.get("defeat_quote", "Now THAT'S a chin check."), subtitle=f"{self.enemy.name} has fallen.", mood="boss")
            return
        self.end_modal.open("Victory!", [Reward("candy", "candy", earned, (255, 200, 90))],
                            quote=random.choice(WIN_COMMENTS), subtitle=f"{self.enemy.name} got chin checked.")

    def _lose(self):
        dropped = self.player.candy // 2
        self.player.candy -= dropped
        self.outcome = "lost"
        self.state = RESULT
        lost = [Reward("candy", "candy dropped", -dropped, (255, 110, 100))] if dropped else []
        self.end_modal.open("Chin Checked!", lost,
                            quote="Get up, kid. Pumpkins bounce.", subtitle="Charlie hits the dirt...",
                            button_label="Get Up", mood="lose")

    def _finish(self):
        self.player.blocking = False  # don't carry a block into the next fight
        self.player.infected = 0
        self.player.burning = 0
        if self.outcome == "lost":
            self.player.hp = self.player.max_hp
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
            self.grit.draw_shadow(c, fx, FEET_Y, self.shadow_size * (1.0 - min(0.4, self.foe.lift / 250)))
            self.foe.draw(c, fx, FEET_Y, facing_right=self.foe_faces_right)
        for surf, x, y, life in self.afterimages:
            surf.set_alpha(int(110 * life / 200))
            c.blit(surf, (x, y))
        self.hero.draw(c, hx, FEET_Y, self.hero_facing)
        self._draw_effects(c)
        if self.player.blocking and self.state in (PLAYER_TURN, ACTION):
            pulse = 0.6 + 0.4 * math.sin(self.time / 150)
            pygame.draw.arc(c, (120, 180, 255), (hx + 5, FEET_Y - 150, 70, 140), -1.2, 1.2, max(2, int(5 * pulse)))
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
        if self.banner and self.state == PLAYER_TURN:
            pulse = int(200 + 55 * math.sin(self.time / 140))
            text = self.big_font.render("!! " + self.banner, True, (255, pulse // 2, 60))
            self.screen.blit(text, (self.screen.get_width() - text.get_width() - 20, 88))
        for t in self.texts:
            t.draw(self.screen)
        if self.state == INTRO:
            self.whisper_jack.draw(self.screen)
        elif self.state == PLAYER_TURN:
            self.options.draw()
        self.end_modal.draw()
