import random

# What makes each enemy type play differently
KINDS = {
    # Ghosts sometimes phase through sloppy (untimed) hits
    "ghost": {"phase_chance": 0.2, "infect_chance": 0.0, "heavy_name": "a bone-chilling WAIL",
              "attack_verb": "claws"},
    # Zombie bites can infect: Charlie loses HP every turn until he eats candy
    "zombie": {"phase_chance": 0.0, "infect_chance": 0.25, "heavy_name": "a BIG BITE",
               "attack_verb": "bites"},
    # --- bosses (all enrage at half HP) ---
    # Mortis, Bringer of Death: a ghost too, so sloppy hits can pass through him.
    # Death's Grasp steals half the damage it deals as HP for him.
    "reaper": {"phase_chance": 0.15, "infect_chance": 0.0, "heavy_name": "DEATH'S GRASP",
               "attack_verb": "reaps", "lifesteal": 0.5, "heavy_chance": 0.3},
    # The Warlock's Hex Storm drains Charlie's Chin meter
    "warlock": {"phase_chance": 0.0, "infect_chance": 0.0, "heavy_name": "a HEX STORM",
                "attack_verb": "hexes", "meter_drain": 35, "heavy_chance": 0.35},
    # The Fire Worm's fireball sets Charlie BURNING (its regular bites sometimes do too)
    "worm": {"phase_chance": 0.0, "infect_chance": 0.0, "heavy_name": "a FIREBALL",
             "attack_verb": "scorches", "burn_chance": 0.2, "heavy_chance": 0.35},
    # The Demon's Hellfire Cleave does both: burns AND drains the Chin meter
    "demon": {"phase_chance": 0.0, "infect_chance": 0.0, "heavy_name": "a HELLFIRE CLEAVE",
              "attack_verb": "cleaves", "burn_chance": 0.0, "meter_drain": 25, "heavy_chance": 0.35},
}

ENRAGED_HEAVY_CHANCE = 0.55
ENRAGED_DAMAGE = 1.2

HEAVY_MULTIPLIER = 1.8
HEAVY_CHANCE = 0.3


class Enemy:
    def __init__(self, name="Ghost", hp=50, damage=(5, 15), candy=(1, 3), kind="ghost", boss=False, **_):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.damage_range = damage
        self.candy_range = candy
        self.kind = kind
        traits = KINDS[kind]
        self.phase_chance = traits["phase_chance"]
        self.infect_chance = traits["infect_chance"]
        self.heavy_name = traits["heavy_name"]
        self.attack_verb = traits["attack_verb"]
        self.meter_drain = traits.get("meter_drain", 0)     # heavy hits drain the Chin meter
        self.lifesteal = traits.get("lifesteal", 0.0)       # heavy hits heal it by this share of the damage
        self.burn_chance = traits.get("burn_chance", 0.0)   # chance a regular hit burns (heavy hits always do)
        self.burns = "burn_chance" in traits
        self.heavy_chance = traits.get("heavy_chance", HEAVY_CHANCE)
        self.boss = boss
        self.enraged = False
        self.next_heavy = False    # telegraphed intent for its next attack
        self._last_heavy = False

    @property
    def is_alive(self):
        return self.hp > 0

    def plan_next_attack(self):
        """Decide (and reveal) whether the next attack is a heavy one. Never two in a row."""
        chance = ENRAGED_HEAVY_CHANCE if self.enraged else self.heavy_chance
        self.next_heavy = (not self._last_heavy) and random.random() < chance
        self._last_heavy = self.next_heavy
        return self.next_heavy

    def attack(self):
        dmg = random.randint(*self.damage_range)
        if self.enraged:
            dmg *= ENRAGED_DAMAGE
        return round(dmg * HEAVY_MULTIPLIER) if self.next_heavy else round(dmg)

    def check_enrage(self):
        """Bosses enrage once at half HP. Returns True on the turn it happens."""
        if self.boss and not self.enraged and self.is_alive and self.hp <= self.max_hp // 2:
            self.enraged = True
            return True
        return False

    def heal(self, amount):
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        return amount

    def candy_drop(self):
        return random.randint(*self.candy_range)
