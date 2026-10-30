"""Combat rules: the numbers behind each move. No drawing here; the battle
scene animates whatever these functions decide.

Tuning lives in MOVES and the constants below.
"""
import random
from dataclasses import dataclass

from core import cheats
from core.combat_options import JAB, HAYMAKER, CHIN_CHECK
from core.effects import PERFECT, GOOD, MISS
from core.items import LOOT, POTION_DROP_CHANCE, SNACK_DROP_CHANCE, SNACKS

# ring_ms: how long the timing ring takes to close; perfect/good: timing windows (ms either side)
# Jab numbers are PER HIT: a jab is a combo of up to JAB_CHAIN quick hits.
MOVES = {
    JAB:        {"mult": 0.45, "whiff": 0.0, "ring_ms": 650, "perfect": 90, "good": 190,
                 "meter": {PERFECT: 8, GOOD: 5, MISS: 2}},
    HAYMAKER:   {"mult": 1.7, "whiff": 0.4, "ring_ms": 800, "perfect": 60, "good": 130,
                 "meter": {PERFECT: 25, GOOD: 12, MISS: 0}},
    CHIN_CHECK: {"mult": 3.0, "whiff": 0.0, "ring_ms": 700, "perfect": 70, "good": 150,
                 "meter": {PERFECT: 0, GOOD: 0, MISS: 0}},
}
TIMING_BONUS = {PERFECT: 1.5, GOOD: 1.2, MISS: 1.0}

# Jab combo: the first jab always lands; each Good/Perfect jab brings up another, faster ring
JAB_CHAIN = 3                # hits in a full combo (Quick Hands I: 4, III: 5)
JAB_SPEEDUP = 0.8            # each follow-up ring closes in 80% of the time of the one before
JAB_WINDOW_SHRINK = 0.9      # ...and its timing windows shrink a little
QUICK_HANDS_DAMAGE = 2       # Quick Hands II: extra damage per jab hit

# Daze: landed jabs stack it (max 3). A Haymaker or Chin Check into a dazed enemy can't whiff
# or phase, and hits harder per stack; then the daze is spent. Stacks don't wait around:
# each enemy turn one wears off (except ones added during the turn just before).
DAZE_MAX = 3                 # (bosses: 2, and enraging shakes it off; see core/enemy.py)
DAZE_BONUS = 0.2             # +20% damage per stack (Heavy Hands III: +30%)
HEAVY_HANDS_BONUS = 0.3

# Haymakers are slow: after throwing one, Charlie is off balance and the enemy's next swing
# is harder to parry or block.
OFF_BALANCE_PERFECT_MS = 60
OFF_BALANCE_GOOD_MS = 125
HAYMAKER_WHIFF_STEADY = 0.25  # Heavy Hands I: whiff chance on an untimed Haymaker
HAYMAKER_DAMAGE_UP = 1.15     # Heavy Hands II

DEFENSE_PERFECT_MS = 80      # parry window (either side of impact)
DEFENSE_GOOD_MS = 170        # timed-block window
PARRY_METER = 25
BLOCK_METER = 8
HURT_METER = 4               # getting hit fires Charlie up a little
COUNTER_MULT = 0.7           # slide-kick counter after a parry (Counter Puncher: x1.5, then x2)
IRON_CHIN_METER = (1.0, 1.2, 1.4, 1.4)   # Chin meter gain by Iron Chin tier
IRON_CHIN_FINISHER = 1.25                # Iron Chin III: Chin Check damage
THICK_SKIN_SHRUG = 0.3                   # Thick Skin: chance to shake off infection and burns
# Ailments last until cured (a Remedy or an Elixir), even between fights and while
# walking around, so carrying Remedies matters. Damage is per turn in battle.
INFECTION_DAMAGE = 4         # zombie bites
BURN_DAMAGE = 6              # Satyrs, Fire Worm, Demon
FIRST_STRIKE_DAMAGE = 15
CANDY_SNACK_HEAL = 5         # Gorge heals this much per piece of candy he snatches (and eats)
LOAF_MULT = 2.4              # Loaf Launch (Crumb, once per fight): this many times Charlie's attack
LOAF_METER = 15
FIRST_STRIKE_METER = 20


@dataclass
class StrikeResult:
    damage: int = 0
    timing: str = MISS
    whiffed: bool = False       # haymaker missed
    phased: bool = False        # ghost phased through
    armored: bool = False       # sloppy hit glanced off armor (half damage)
    meter: int = 0
    killed: bool = False
    dazed: int = 0              # Daze stacks on the enemy after this hit (jabs)
    daze_used: int = 0          # Daze stacks this Haymaker/Chin Check cashed in
    combo: int = 1              # which hit of a jab combo this was
    chain: bool = False         # a jab that earned another ring


@dataclass
class DefenseResult:
    damage: int = 0
    timing: str = MISS
    parried: bool = False
    timed_block: bool = False
    counter: int = 0
    infected: bool = False
    burned: bool = False        # set on fire (Fire Worm / Demon)
    drained: int = 0            # Chin meter lost to a Hex Storm / Hellfire Cleave
    stolen: int = 0             # HP the Bringer of Death took for himself
    snatched: int = 0           # candy Gorge grabbed (and ate, healing himself)
    shrugged: str = ""          # Thick Skin shook off an ailment: "infection" or "burn"
    off_balance: bool = False   # Charlie was off balance from a Haymaker
    dazed: int = 0              # Counter Puncher II: Daze stacks after the counter
    killed: bool = False


class BattleManager:
    def __init__(self, player, enemy, timing_scale=1.0):
        self.player = player
        self.enemy = enemy
        self.timing_scale = timing_scale      # difficulty: >1 widens every timing window

    def move_settings(self, move):
        return MOVES[move]

    # ---- upgrade-dependent numbers ---------------------------------------
    def jab_chain(self):
        """Hits in a full jab combo (Quick Hands I adds one, III another)."""
        level = self.player.has("quick_hands")
        return JAB_CHAIN + (level >= 1) + (level >= 3)

    def jab_ring(self, hit):
        """(ring_ms, perfect, good) for jab number `hit` (1-based): each follow-up is quicker."""
        cfg = MOVES[JAB]
        speed, shrink = JAB_SPEEDUP ** (hit - 1), JAB_WINDOW_SHRINK ** (hit - 1) * self.timing_scale
        return round(cfg["ring_ms"] * speed), round(cfg["perfect"] * shrink), round(cfg["good"] * shrink)

    def attack_ring(self, move):
        """(ring_ms, perfect, good) for a Haymaker or Chin Check."""
        cfg = MOVES[move]
        return cfg["ring_ms"], round(cfg["perfect"] * self.timing_scale), round(cfg["good"] * self.timing_scale)

    def daze_bonus(self):
        return HEAVY_HANDS_BONUS if self.player.has("heavy_hands") >= 3 else DAZE_BONUS

    def defense_windows(self):
        """(perfect, good) ms for blocking the enemy's next hit: tighter when off balance."""
        if self.player.off_balance:
            perfect, good = OFF_BALANCE_PERFECT_MS, OFF_BALANCE_GOOD_MS
        else:
            perfect, good = DEFENSE_PERFECT_MS, DEFENSE_GOOD_MS
        return round(perfect * self.timing_scale), round(good * self.timing_scale)

    def roll_feint(self):
        """Does this swing stall mid-way (a feint)?"""
        return random.random() < self.enemy.feint_chance

    def gain_meter(self, amount):
        """Chin meter from fighting (Iron Chin makes it fill faster). Returns what was added."""
        p = self.player
        before = p.chin_meter
        p.add_meter(round(amount * IRON_CHIN_METER[p.has("iron_chin")]))
        return p.chin_meter - before

    # ---- Charlie's attacks ---------------------------------------------
    def strike(self, move, timing, hit=1):
        """Resolve a Jab (hit = which jab of the combo), Haymaker, or Chin Check."""
        p, e, cfg = self.player, self.enemy, MOVES[move]
        result = StrikeResult(timing=timing, combo=hit)
        big = move in (HAYMAKER, CHIN_CHECK)
        if move == CHIN_CHECK:
            p.chin_meter = 0
        daze = e.daze if big else 0
        whiff = cfg["whiff"]
        if move == HAYMAKER and p.has("heavy_hands"):
            whiff = HAYMAKER_WHIFF_STEADY
        sure = daze or cheats.one_shot()          # (the one-hit cheat never whiffs or passes through)
        if timing == MISS and not sure and random.random() < whiff:
            result.whiffed = True
        elif timing == MISS and not sure and random.random() < e.phase_chance:
            result.phased = True
        else:
            damage = p.attack() * cfg["mult"] * TIMING_BONUS[timing]
            if move == JAB and p.has("quick_hands") >= 2:
                damage += QUICK_HANDS_DAMAGE
            if move == HAYMAKER and p.has("heavy_hands") >= 2:
                damage *= HAYMAKER_DAMAGE_UP
            if move == CHIN_CHECK and p.has("iron_chin") >= 3:
                damage *= IRON_CHIN_FINISHER
            if daze:
                damage *= 1 + self.daze_bonus() * daze
                result.daze_used = daze
            if timing == MISS and e.armor < 1.0:
                damage *= e.armor
                result.armored = True
            result.damage = e.take_damage(round(damage))
            if move == JAB:
                e.add_daze()
        if big:
            e.daze = 0                      # spent (or wasted on a whiff)
        if move == HAYMAKER:
            p.off_balance = True
        result.dazed = e.daze
        result.meter = self.gain_meter(cfg["meter"][timing])
        if timing == PERFECT:
            p.stats["perfects"] += 1
        if move == JAB:
            p.stats["best_combo"] = max(p.stats["best_combo"], hit)
        result.killed = not e.is_alive
        result.chain = (move == JAB and timing in (PERFECT, GOOD) and hit < self.jab_chain()
                        and not result.killed and not result.phased)
        return result

    def bomb(self):
        dmg = self.player.use_bomb()
        if dmg:
            self.enemy.take_damage(dmg)
        return dmg

    def loaf_launch(self):
        """Crumb flies into the enemy: a big hit, and it's dazed all the way."""
        e = self.enemy
        e.daze = e.daze_max
        e.daze_fresh = True
        self.gain_meter(LOAF_METER)
        return e.take_damage(round(self.player.attack() * LOAF_MULT))

    def first_strike(self):
        self.gain_meter(FIRST_STRIKE_METER)
        return self.enemy.take_damage(FIRST_STRIKE_DAMAGE)

    # ---- the enemy's attack --------------------------------------------
    def enemy_attack(self, timing, hit=1, hits=1):
        """Resolve one enemy swing given Charlie's defensive timing. In a string of `hits`
        swings, only a parry of the last one earns the slide-kick counter; the last swing
        also ends the enemy's turn (Daze wears off, Charlie gets his balance back)."""
        p, e = self.player, self.enemy
        last = hit >= hits
        result = DefenseResult(timing=timing, off_balance=p.off_balance)
        raw = e.attack(string_hit=hits > 1)
        if timing == PERFECT:
            result.parried = True
            p.stats["parries"] += 1
            counter = p.has("counter_puncher")
            if last:
                mult = COUNTER_MULT * (1.0 if not counter else 1.5 if counter < 3 else 2.0)
                result.counter = e.take_damage(round(p.attack() * mult))
            self.gain_meter(PARRY_METER if last else PARRY_METER // 2)
            if counter >= 2 and e.is_alive and last:
                e.add_daze()
                result.dazed = e.daze
        else:
            if timing == GOOD:
                result.timed_block = True
                raw = raw // 2
                self.gain_meter(BLOCK_METER)
            result.damage = p.take_damage(raw)
            heavy = e.next_heavy
            if result.damage and heavy and e.meter_drain:
                result.drained = min(p.chin_meter, e.meter_drain)
                p.add_meter(-e.meter_drain)
            elif result.damage:
                self.gain_meter(HURT_METER)
                if e.infect_chance and (heavy or random.random() < e.infect_chance):
                    if self._shrug():
                        result.shrugged = "infection"
                    else:
                        result.infected = True
                        p.infected = 1
            if result.damage and e.burns and (heavy or random.random() < e.burn_chance):
                if self._shrug():
                    result.shrugged = "burn"
                else:
                    result.burned = True
                    p.burning = 1
            if result.damage and heavy and e.lifesteal:
                result.stolen = e.heal(round(result.damage * e.lifesteal))
            if heavy and e.candy_steal and timing == MISS and p.candy > 0:   # a clean block saves your candy
                grab = min(p.candy, random.randint(*e.candy_steal))
                p.candy -= grab
                e.stolen += grab
                result.snatched = grab
                result.stolen = e.heal(grab * CANDY_SNACK_HEAL)
        result.killed = not p.is_alive
        if last:
            self.end_enemy_turn()
        return result

    def end_enemy_turn(self):
        p, e = self.player, self.enemy
        p.off_balance = False               # back on his feet
        e.wear_off_daze()
        e.plan_next_attack()

    def _shrug(self):
        """Thick Skin: a chance to shake off an infection or a burn as it lands."""
        return bool(self.player.has("thick_skin")) and random.random() < THICK_SKIN_SHRUG

    def ailment_damage(self, base):
        """Thick Skin II halves what infection and burns do each tick (rounded up)."""
        return -(-base // 2) if self.player.has("thick_skin") >= 2 else base

    def burn_tick(self):
        """Start of Charlie's turn: burning drains HP. Returns damage taken."""
        p = self.player
        if p.burning <= 0:
            return 0
        dmg = min(self.ailment_damage(BURN_DAMAGE), p.hp)
        p.hp -= dmg
        return dmg

    def infection_tick(self):
        """Start of Charlie's turn: infection drains HP. Returns damage taken."""
        p = self.player
        if p.infected <= 0:
            return 0
        dmg = min(self.ailment_damage(INFECTION_DAMAGE), p.hp)
        p.hp -= dmg
        return dmg

    BOSS_BOMB_REWARD = 2

    def award_boss_loot(self):
        """Bosses also drop bombs. Returns how many."""
        self.player.add_item("bomb", self.BOSS_BOMB_REWARD)
        return self.BOSS_BOMB_REWARD

    def award_loot(self):
        """What the enemy dropped: sometimes a trophy to sell to the Crow (bosses always
        drop one), and regular monsters sometimes drop a Gourd-Aid. Returns item keys."""
        dropped = []
        key, chance = LOOT.get(self.enemy.kind, (None, 0))
        if key and random.random() < chance:
            dropped.append(key)
        if not self.enemy.boss and random.random() < POTION_DROP_CHANCE:
            dropped.append("potion")
        if self.enemy.boss and self.enemy.kind != "bread" or random.random() < SNACK_DROP_CHANCE:
            dropped.append(random.choice(SNACKS))           # something for Crumb
        for key in dropped:
            self.player.add_item(key)
        return dropped

    def award_candy(self):
        """Give the victory candy. Returns the amount actually earned."""
        earned = self.player.add_candy(self.enemy.candy_drop() + self.enemy.stolen)   # (Gorge gives it all back)
        self.player.last_candy_reward = earned
        return earned
