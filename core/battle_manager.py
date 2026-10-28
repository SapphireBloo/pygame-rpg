"""Combat rules: the numbers behind each move. No drawing here; the battle
scene animates whatever these functions decide.

Tuning lives in MOVES and the constants below.
"""
import random
from dataclasses import dataclass

from core.combat_options import JAB, HAYMAKER, CHIN_CHECK
from core.effects import PERFECT, GOOD, MISS

# ring_ms: how long the timing ring takes to close; perfect/good: timing windows (ms either side)
MOVES = {
    JAB:        {"mult": 0.85, "whiff": 0.0, "ring_ms": 650, "perfect": 90, "good": 190,
                 "meter": {PERFECT: 18, GOOD: 10, MISS: 4}},
    HAYMAKER:   {"mult": 1.7, "whiff": 0.4, "ring_ms": 800, "perfect": 60, "good": 130,
                 "meter": {PERFECT: 25, GOOD: 12, MISS: 0}},
    CHIN_CHECK: {"mult": 3.0, "whiff": 0.0, "ring_ms": 700, "perfect": 70, "good": 150,
                 "meter": {PERFECT: 0, GOOD: 0, MISS: 0}},
}
TIMING_BONUS = {PERFECT: 1.5, GOOD: 1.2, MISS: 1.0}

DEFENSE_PERFECT_MS = 80      # parry window (either side of impact)
DEFENSE_GOOD_MS = 170        # timed-block window
PARRY_METER = 25
BLOCK_METER = 8
HURT_METER = 4               # getting hit fires Charlie up a little
COUNTER_MULT = 0.7           # slide-kick counter after a parry
INFECTION_TURNS = 3
INFECTION_DAMAGE = 4
BURN_TURNS = 3               # Fire Worm / Demon burns: hurts more than infection
BURN_DAMAGE = 6
FIRST_STRIKE_DAMAGE = 15
FIRST_STRIKE_METER = 20


@dataclass
class StrikeResult:
    damage: int = 0
    timing: str = MISS
    whiffed: bool = False       # haymaker missed
    phased: bool = False        # ghost phased through
    meter: int = 0
    killed: bool = False


@dataclass
class DefenseResult:
    damage: int = 0
    timing: str = MISS
    parried: bool = False
    timed_block: bool = False
    stance_block: bool = False
    counter: int = 0
    infected: bool = False
    burned: bool = False        # set on fire (Fire Worm / Demon)
    drained: int = 0            # Chin meter lost to a Hex Storm / Hellfire Cleave
    stolen: int = 0             # HP the Bringer of Death took for himself
    killed: bool = False


class BattleManager:
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy

    def move_settings(self, move):
        return MOVES[move]

    # ---- Charlie's attacks ---------------------------------------------
    def strike(self, move, timing):
        """Resolve Jab / Haymaker / Chin Check with the timing the player hit."""
        p, e, cfg = self.player, self.enemy, MOVES[move]
        result = StrikeResult(timing=timing)
        if move == CHIN_CHECK:
            p.chin_meter = 0
        if timing == MISS and random.random() < cfg["whiff"]:
            result.whiffed = True
        elif timing == MISS and random.random() < e.phase_chance:
            result.phased = True
        else:
            result.damage = e.take_damage(round(p.attack() * cfg["mult"] * TIMING_BONUS[timing]))
        result.meter = cfg["meter"][timing]
        p.add_meter(result.meter)
        result.killed = not e.is_alive
        return result

    def bomb(self):
        dmg = self.player.use_bomb()
        if dmg:
            self.enemy.take_damage(dmg)
        return dmg

    def heal(self):
        return self.player.heal()

    def first_strike(self):
        self.player.add_meter(FIRST_STRIKE_METER)
        return self.enemy.take_damage(FIRST_STRIKE_DAMAGE)

    # ---- the enemy's attack --------------------------------------------
    def enemy_attack(self, timing):
        """Resolve the enemy's hit given Charlie's defensive timing."""
        p, e = self.player, self.enemy
        result = DefenseResult(timing=timing)
        raw = e.attack()
        if timing == PERFECT:
            result.parried = True
            p.blocking = False
            result.counter = e.take_damage(round(p.attack() * COUNTER_MULT))
            p.add_meter(PARRY_METER)
        else:
            if timing == GOOD:
                result.timed_block = True
                raw = raw // 2
                p.add_meter(BLOCK_METER)
            result.stance_block = p.blocking
            result.damage, _ = p.take_damage(raw)
            heavy = e.next_heavy
            if result.damage and heavy and e.meter_drain:
                result.drained = min(p.chin_meter, e.meter_drain)
                p.add_meter(-e.meter_drain)
            elif result.damage:
                p.add_meter(HURT_METER)
                if e.infect_chance and (heavy or random.random() < e.infect_chance):
                    result.infected = True
                    p.infected = INFECTION_TURNS
            if result.damage and e.burns and (heavy or random.random() < e.burn_chance):
                result.burned = True
                p.burning = BURN_TURNS
            if result.damage and heavy and e.lifesteal:
                result.stolen = e.heal(round(result.damage * e.lifesteal))
        result.killed = not p.is_alive
        e.plan_next_attack()
        return result

    def burn_tick(self):
        """Start of Charlie's turn: burning drains HP. Returns damage taken."""
        p = self.player
        if p.burning <= 0:
            return 0
        p.burning -= 1
        dmg = min(BURN_DAMAGE, p.hp)
        p.hp -= dmg
        return dmg

    def infection_tick(self):
        """Start of Charlie's turn: infection drains HP. Returns damage taken."""
        p = self.player
        if p.infected <= 0:
            return 0
        p.infected -= 1
        dmg = min(INFECTION_DAMAGE, p.hp)
        p.hp -= dmg
        return dmg

    BOSS_BOMB_REWARD = 2

    def award_boss_loot(self):
        """Bosses also drop bombs. Returns how many."""
        self.player.inventory["bomb"] = self.player.inventory.get("bomb", 0) + self.BOSS_BOMB_REWARD
        return self.BOSS_BOMB_REWARD

    def award_candy(self):
        """Give the victory candy. Returns the amount actually earned."""
        earned = self.player.add_candy(self.enemy.candy_drop())
        self.player.last_candy_reward = earned
        return earned
