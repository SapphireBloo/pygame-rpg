from core.settings import GROUND_Y
from core.upgrades import UPGRADES


class Player:
    BASE_MAX_HP = 100
    HEAL_COST = 1          # candy per heal
    HEAL_AMOUNT = 25
    HEAL_BOOST_AMOUNT = 35
    STARTING_BOMBS = 1

    def __init__(self):
        self.name = "Charlie"
        self.max_hp = self.BASE_MAX_HP
        self.hp = self.max_hp
        self.level = 1

        self.candy = 0                # currency and healing resource
        self.last_candy_reward = 0    # candy earned in the most recent battle
        self.battles_won = 0

        self.inventory = {"bomb": self.STARTING_BOMBS}
        self.blocking = False

        # Position in the exploration world
        self.x = 50.0
        self.y = GROUND_Y

        self.upgrades = {u["key"]: False for u in UPGRADES}
        self.used_resurrect = False   # "Resurrect Once" is once per game, not per battle

        self.chin_meter = 0           # 0-100; full unlocks the Chin Check finisher
        self.infected = 0             # turns of zombie infection left (loses HP each turn)
        self.burning = 0              # turns of fire left (Fire Worm / Demon; loses HP each turn)

    # ---- status --------------------------------------------------------
    @property
    def is_alive(self):
        return self.hp > 0

    def has(self, upgrade_key):
        return self.upgrades.get(upgrade_key, False)

    CHIN_METER_MAX = 100

    @property
    def chin_ready(self):
        return self.chin_meter >= self.CHIN_METER_MAX

    def add_meter(self, amount):
        self.chin_meter = max(0, min(self.CHIN_METER_MAX, self.chin_meter + amount))

    # ---- combat --------------------------------------------------------
    def attack(self):
        return 10 + self.level * 2

    def block(self):
        self.blocking = True

    def take_damage(self, amount):
        """Apply a hit. Returns (damage_taken, was_blocked)."""
        blocked = self.blocking
        if blocked:
            amount //= 2
            self.blocking = False
        self.hp = max(0, self.hp - amount)
        return amount, blocked

    def can_heal(self):
        return self.candy >= self.HEAL_COST and (self.hp < self.max_hp or self.infected > 0 or self.burning > 0)

    def heal(self):
        """Eat candy to heal. Returns HP restored (0 if nothing happened).

        Won't spend candy at full HP (unless it's to cure an infection or put out a fire).
        """
        if not self.can_heal():
            return 0
        amount = self.HEAL_BOOST_AMOUNT if self.has("heal_boost") else self.HEAL_AMOUNT
        self.candy -= self.HEAL_COST
        self.infected = 0              # candy cures zombie infection
        self.burning = 0               # ...and puts out fires
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def use_bomb(self):
        """Throw a bomb. Returns damage dealt (0 if out of bombs)."""
        if self.inventory.get("bomb", 0) <= 0:
            return 0
        self.inventory["bomb"] -= 1
        damage = 30 + self.level * 3
        if self.has("bomb_power_plus_10"):
            damage += 10
        return damage

    def try_resurrect(self):
        """Use the Resurrect Once upgrade if available. Returns True if revived."""
        if self.has("resurrect_once") and not self.used_resurrect:
            self.used_resurrect = True
            self.hp = self.max_hp // 2
            return True
        return False

    # ---- economy -------------------------------------------------------
    def add_candy(self, amount):
        """Add candy (doubled by the upgrade). Returns the amount actually added."""
        if self.has("double_candy"):
            amount *= 2
        self.candy += amount
        return amount

    def buy_upgrade(self, upgrade):
        """Buy an upgrade from the catalog. Returns True on success."""
        key, cost = upgrade["key"], upgrade["cost"]
        if self.has(key) or self.candy < cost:
            return False
        self.candy -= cost
        self.upgrades[key] = True
        if key == "max_hp_plus_25":
            self.max_hp += 25
            self.hp += 25
        return True
