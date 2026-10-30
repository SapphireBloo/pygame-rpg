import random

from core import cheats
from core.difficulty import STRING_HIT_DAMAGE

# What makes each enemy type play differently
KINDS = {
    # Ghosts sometimes phase through sloppy (untimed) hits
    "ghost": {"phase_chance": 0.2, "infect_chance": 0.0, "heavy_name": "a bone-chilling WAIL",
              "attack_verb": "claws"},
    # Zombie bites can infect: Charlie loses HP every turn (and while walking) until he drinks a Remedy or Elixir
    "zombie": {"phase_chance": 0.0, "infect_chance": 0.25, "heavy_name": "a BIG BITE",
               "attack_verb": "bites"},
    # Death Knights are armored: untimed (sloppy) punches only do half damage
    "knight": {"phase_chance": 0.0, "infect_chance": 0.0, "heavy_name": "a CAVALRY CHARGE",
               "attack_verb": "slashes", "armor": 0.5, "heavy_chance": 0.3},
    # Satyrs play with fire: their antler beam (heavy) always burns, scratches sometimes do
    "satyr": {"phase_chance": 0.0, "infect_chance": 0.0, "heavy_name": "an ANTLER BEAM",
              "attack_verb": "scratches", "burn_chance": 0.15, "heavy_chance": 0.3},
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
    # Crumb, the secret boss: no enrage. He RISES through three phases instead (bread, toast,
    # burnt toast), and his heavy attack is a 5-hit Crouton Barrage.
    "bread": {"phase_chance": 0.0, "infect_chance": 0.0, "heavy_name": "a CROUTON BARRAGE",
              "attack_verb": "bonks", "heavy_chance": 0.3, "heavy_hits": 5, "phases": 3},
    # --- The Void ---
    # Catto: a little black cat... until its mouth opens. Quick, and its heavy bite drains the Chin meter.
    "catto": {"phase_chance": 0.0, "infect_chance": 0.0, "heavy_name": "a VOID MAW",
              "attack_verb": "bites", "meter_drain": 20, "heavy_chance": 0.3},
    # The Mad Ghost: a ghost (sloppy hits pass through) with blades
    "madghost": {"phase_chance": 0.15, "infect_chance": 0.0, "heavy_name": "a TRIPLE SLASH",
                 "attack_verb": "slashes", "heavy_chance": 0.3, "heavy_hits": 3},
    # The Mage: its vortex drains the Chin meter and burns
    "mage": {"phase_chance": 0.0, "infect_chance": 0.0, "heavy_name": "a VOID VORTEX",
             "attack_verb": "hexes", "meter_drain": 30, "burn_chance": 0.0, "heavy_chance": 0.35},
    # The Abomination: armored like a knight (untimed hits do half), tentacle barrage
    "abomination": {"phase_chance": 0.0, "infect_chance": 0.2, "heavy_name": "a TENTACLE LASH",
                    "attack_verb": "lashes", "armor": 0.5, "heavy_chance": 0.3, "heavy_hits": 3},
    # Gorge, Taker of Worlds: the bully. His Candy Snatch steals candy (and he eats it to heal)
    # unless Charlie blocks it. Beat him and you get every piece back.
    "bully": {"phase_chance": 0.0, "infect_chance": 0.0, "heavy_name": "a CANDY SNATCH",
              "attack_verb": "pounds", "heavy_chance": 0.35, "candy_steal": (3, 6)},
}
BARRAGE_HIT = 0.7          # each hit of a multi-hit heavy attack (Crouton Barrage)

ENRAGED_HEAVY_CHANCE = 0.55
ENRAGED_DAMAGE = 1.2

HEAVY_MULTIPLIER = 1.8
HEAVY_CHANCE = 0.3


class Enemy:
    def __init__(self, name="Ghost", hp=50, damage=(5, 15), candy=(1, 3), kind="ghost", boss=False, mods=None, **_):
        """mods: chapter/difficulty adjustments from core.difficulty.enemy_mods (None = as written)."""
        mods = mods or {}
        self.name = name
        self.max_hp = round(hp * mods.get("hp", 1.0))
        self.hp = self.max_hp
        self.damage_mult = mods.get("damage", 1.0)
        self.damage_range = damage
        self.string_chance = mods.get("string_chance", 0.0)   # chance a regular attack is a 2-3 hit string
        self.string_max = mods.get("string_max", 1)
        self.feint_chance = mods.get("feint_chance", 0.0)     # chance each swing stalls mid-swing
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
        self.armor = traits.get("armor", 1.0)               # damage multiplier for untimed hits
        self.heavy_chance = traits.get("heavy_chance", HEAVY_CHANCE)
        self.heavy_hits = traits.get("heavy_hits", 1)        # swings in its heavy attack
        self.phases = traits.get("phases", 0)                # >1: rises through phases instead of enraging
        self.candy_steal = traits.get("candy_steal")         # (min, max) candy his heavy hit snatches
        self.stolen = 0                                      # candy he's taken this fight (you win it back)
        self.phase = 1
        self.boss = boss
        self.enraged = False
        self.next_heavy = False    # telegraphed intent for its next attack
        self.next_hits = 1         # how many swings its next attack has (a string if more than 1)
        self._last_heavy = False
        self.daze = 0              # stacks from Charlie's jabs (spent by a Haymaker or Chin Check)
        self.daze_fresh = False    # dazed during the turn that just happened (doesn't wear off yet)

    @property
    def daze_max(self):
        return 2 if self.boss else 3

    def add_daze(self):
        self.daze = min(self.daze_max, self.daze + 1)
        self.daze_fresh = True

    def wear_off_daze(self):
        """End of the enemy's turn: an old Daze stack wears off (a fresh one waits a turn)."""
        if self.daze and not self.daze_fresh:
            self.daze -= 1
        self.daze_fresh = False

    @property
    def is_alive(self):
        return self.hp > 0

    def plan_next_attack(self):
        """Decide (and reveal) whether the next attack is a heavy one. Never two in a row."""
        chance = ENRAGED_HEAVY_CHANCE if self.enraged else self.heavy_chance
        self.next_heavy = (not self._last_heavy) and random.random() < chance
        self._last_heavy = self.next_heavy
        self.next_hits = 1
        if not self.next_heavy and self.string_max > 1 and random.random() < self.string_chance:
            self.next_hits = random.randint(2, self.string_max)
        return self.next_heavy

    def attack(self, string_hit=False):
        dmg = random.randint(*self.damage_range) * self.damage_mult
        if self.enraged:
            dmg *= ENRAGED_DAMAGE
        if self.next_heavy and string_hit:
            dmg *= BARRAGE_HIT
        elif self.next_heavy:
            dmg *= HEAVY_MULTIPLIER
        elif string_hit:
            dmg *= STRING_HIT_DAMAGE
        return max(1, round(dmg))

    def check_enrage(self):
        """Bosses enrage once at half HP. Returns True on the turn it happens."""
        if self.boss and not self.phases and not self.enraged and self.is_alive and self.hp <= self.max_hp // 2:
            self.enraged = True
            self.daze = 0             # the rage shakes off any Daze
            return True
        return False

    def check_phase(self):
        """Phase bosses (Crumb) move to the next phase at each third of their HP.
        Returns True on the turn a new phase starts."""
        if self.phases < 2 or not self.is_alive:
            return False
        lost = 1 - self.hp / self.max_hp
        target = min(self.phases, 1 + int(lost * self.phases + 1e-9))
        if target > self.phase:
            self.phase = target
            self.daze = 0
            return True
        return False

    def heal(self, amount):
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def take_damage(self, amount):
        if amount > 0 and cheats.one_shot():      # (cheat code: anything that lands knocks it out)
            amount = self.hp
        self.hp = max(0, self.hp - amount)
        return amount

    def candy_drop(self):
        return random.randint(*self.candy_range)
