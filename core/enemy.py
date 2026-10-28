import random

# What makes each enemy type play differently
KINDS = {
    # Ghosts sometimes phase through sloppy (untimed) hits
    "ghost": {"phase_chance": 0.2, "infect_chance": 0.0, "heavy_name": "a bone-chilling WAIL",
              "attack_verb": "claws"},
    # Zombie bites can infect: Charlie loses HP every turn until he eats candy
    "zombie": {"phase_chance": 0.0, "infect_chance": 0.25, "heavy_name": "a BIG BITE",
               "attack_verb": "bites"},
}

HEAVY_MULTIPLIER = 1.8
HEAVY_CHANCE = 0.3


class Enemy:
    def __init__(self, name="Ghost", hp=50, damage=(5, 15), candy=(1, 3), kind="ghost", **_):
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
        self.next_heavy = False    # telegraphed intent for its next attack
        self._last_heavy = False

    @property
    def is_alive(self):
        return self.hp > 0

    def plan_next_attack(self):
        """Decide (and reveal) whether the next attack is a heavy one. Never two in a row."""
        self.next_heavy = (not self._last_heavy) and random.random() < HEAVY_CHANCE
        self._last_heavy = self.next_heavy
        return self.next_heavy

    def attack(self):
        dmg = random.randint(*self.damage_range)
        return round(dmg * HEAVY_MULTIPLIER) if self.next_heavy else dmg

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        return amount

    def candy_drop(self):
        return random.randint(*self.candy_range)
