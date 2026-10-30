from core.items import ITEMS_BY_KEY, STARTING_ITEMS
from core.settings import GROUND_Y
from core.upgrades import UPGRADES

SUGAR_PUNCH = 3


class Player:
    BASE_MAX_HP = 100
    BUTTER_HP = 15         # Crumb's blessings, for the chapter after you feed him (see feed_crumb)
    JAM_METER = 30
    # What each Blacksmith tier is worth (see core/upgrades.py for the costs)
    MAX_HP_PER_TIER = 20       # Tough Hide
    POTION_BOOST = 10          # extra HP per healing potion, per Potion Boost tier
    BOMB_POWER = 10            # extra bomb damage per Bomb Power tier

    def __init__(self):
        self.name = "Charlie"
        self.max_hp = self.BASE_MAX_HP
        self.hp = self.max_hp
        self.level = 1

        self.candy = 0                # currency (spend it at camp)
        self.last_candy_reward = 0    # candy earned in the most recent battle
        self.battles_won = 0

        self.inventory = dict(STARTING_ITEMS)   # item key -> how many (see core/items.py)
        self.off_balance = False      # just threw a Haymaker: the next enemy hit is harder to block

        # Position in the exploration world
        self.x = 50.0
        self.y = GROUND_Y

        self.upgrades = {u["key"]: 0 for u in UPGRADES}   # upgrade key -> tier owned (0 = none)
        self.used_resurrect = False   # Second Wind: once per game (tier II: refreshed every chapter)

        # Crumb, the bread at camp
        self.crumbs_found = []        # chapters whose hidden Golden Crumb Charlie picked up
        self.crumbs_fed = 0           # Golden Crumbs Crumb has eaten (4 = he's ready for a fight)
        self.crumb_beaten = False     # beat the secret boss: now he's Charlie's companion (see `companion`)
        self.crumb_angry = False      # fed all four crumbs, then tried to leave camp: he's FURIOUS
        self.crumb_fought = False     # the secret fight is a one-shot: True once it's been tried
        self.blessing = None          # snack Crumb ate at the last camp: helps until the next camp

        # For the end-of-run summary
        self.stats = {"losses": 0, "perfects": 0, "best_combo": 0, "parries": 0, "candy_earned": 0, "play_ms": 0}

        self.chin_meter = 0           # 0-100; full unlocks the Chin Check finisher
        self.infected = 0             # zombie infection (1 = infected): hurts every turn until cured
        self.burning = 0              # on fire (1 = burning): hurts every turn until cured

    # ---- status --------------------------------------------------------
    @property
    def is_alive(self):
        return self.hp > 0

    def has(self, upgrade_key):
        """Tier owned of an upgrade (0 if none), so `if player.has(...)` still works."""
        return self.upgrades.get(upgrade_key, 0)

    def next_tier(self, upgrade):
        """The next tier the Blacksmith can sell, or None when it's maxed out."""
        level = self.has(upgrade["key"])
        return upgrade["tiers"][level] if level < len(upgrade["tiers"]) else None

    CHIN_METER_MAX = 100

    @property
    def chin_ready(self):
        return self.chin_meter >= self.CHIN_METER_MAX

    def add_meter(self, amount):
        self.chin_meter = max(0, min(self.CHIN_METER_MAX, self.chin_meter + amount))

    # ---- combat --------------------------------------------------------
    def attack(self):
        sugar = self.blessing == "sugar" or self.companion
        return 10 + self.level * 2 + (SUGAR_PUNCH if sugar else 0)

    @property
    def companion(self):
        """Crumb travels with Charlie (after Charlie beat him): every snack blessing, for good,
        and the Loaf Launch move in battle."""
        return self.crumb_beaten

    @property
    def jam_start(self):
        return self.blessing == "jam" or self.companion

    def join_crumb(self):
        """Charlie beat Crumb, the Crust Eternal, and Crumb's coming along: his butter blessing
        becomes permanent (the sugar and jam ones follow from `companion`)."""
        self.clear_blessing()
        if not self.crumb_beaten:
            self.crumb_beaten = True
            self.max_hp += self.BUTTER_HP
        self.hp = self.max_hp

    def take_damage(self, amount):
        """Apply a hit. Returns the damage taken. (Blocking is all timing: see battle_manager.)"""
        self.hp = max(0, self.hp - amount)
        return amount

    # ---- items -------------------------------------------------------
    def count(self, key):
        return self.inventory.get(key, 0)

    def add_item(self, key, amount=1):
        self.inventory[key] = self.count(key) + amount

    def remove_item(self, key, amount=1):
        """Take items out of the bag. Returns False if there weren't enough."""
        if self.count(key) < amount:
            return False
        self.inventory[key] -= amount
        if not self.inventory[key]:
            del self.inventory[key]
        return True

    def item_useful(self, key):
        """Would using this item do anything right now? (No drinking potions at full HP.)"""
        item = ITEMS_BY_KEY[key]
        if not self.count(key):
            return False
        hurt = self.hp < self.max_hp
        sick = self.infected > 0 or self.burning > 0
        if item.get("heal") or item.get("cure"):
            return (item.get("heal") and hurt) or (item.get("cure") and sick)
        if item.get("meter"):
            return not self.chin_ready
        return bool(item.get("damage"))

    def use_item(self, key):
        """Use a healing/cure/meter item. Returns what happened:
        {"healed": hp, "cured": bool, "meter": gained}, or None if it couldn't be used.
        (Bombs are thrown through the battle rules instead.)"""
        if not self.item_useful(key) or ITEMS_BY_KEY[key].get("damage"):
            return None
        item = ITEMS_BY_KEY[key]
        self.remove_item(key)
        result = {"healed": 0, "cured": False, "meter": 0}
        if item.get("cure"):
            result["cured"] = self.infected > 0 or self.burning > 0
            self.infected = self.burning = 0
        if item.get("heal"):
            before = self.hp
            boost = self.POTION_BOOST * self.has("heal_boost")
            self.hp = min(self.max_hp, self.hp + item["heal"] + boost)
            result["healed"] = self.hp - before
        if item.get("meter"):
            before = self.chin_meter
            self.add_meter(item["meter"])
            result["meter"] = self.chin_meter - before
        return result

    def use_bomb(self):
        """Throw a bomb. Returns damage dealt (0 if out of bombs)."""
        if not self.remove_item("bomb"):
            return 0
        return 30 + self.level * 3 + self.BOMB_POWER * self.has("bomb_power")

    def try_resurrect(self):
        """Use Second Wind if it's ready. Returns True if revived.
        Tier I: half HP, once per game. Tier II: full HP and cured, once per chapter."""
        level = self.has("resurrect")
        if not level or self.used_resurrect:
            return False
        self.used_resurrect = True
        if level >= 2:
            self.hp = self.max_hp
            self.infected = self.burning = 0
        else:
            self.hp = self.max_hp // 2
        return True

    def new_chapter(self):
        """Leaving camp for the next chapter: Second Wind II comes back."""
        if self.has("resurrect") >= 2:
            self.used_resurrect = False

    # ---- economy -------------------------------------------------------
    def add_candy(self, amount):
        """Add candy. Returns the amount added."""
        self.candy += amount
        self.stats["candy_earned"] += amount
        return amount

    def buy_upgrade(self, upgrade):
        """Buy the next tier of an upgrade. Returns True on success."""
        tier = self.next_tier(upgrade)
        if tier is None or self.candy < tier["cost"]:
            return False
        self.candy -= tier["cost"]
        self.upgrades[upgrade["key"]] += 1
        if upgrade["key"] == "max_hp":
            self.max_hp += self.MAX_HP_PER_TIER
            self.hp += self.MAX_HP_PER_TIER
        return True

    # ---- Crumb ---------------------------------------------------------
    def feed_crumb(self, key):
        """Feed Crumb a snack (a blessing for the next chapter) or a Golden Crumb.
        Returns what happened: "golden", "blessed", or None if Charlie doesn't have one."""
        if not self.remove_item(key):
            return None
        if key == "golden_crumb":
            self.crumbs_fed += 1
            return "golden"
        self.clear_blessing()                 # one blessing at a time: the new snack replaces it
        self.blessing = key
        if key == "butter":
            self.max_hp += self.BUTTER_HP
            self.hp += self.BUTTER_HP
        return "blessed"

    def clear_blessing(self):
        """Reached the next camp: the blessing wears off."""
        if self.blessing == "butter":
            self.max_hp -= self.BUTTER_HP
            self.hp = max(1, min(self.hp, self.max_hp))
        self.blessing = None

    # ---- saving --------------------------------------------------------
    SAVED = ("max_hp", "hp", "candy", "battles_won", "used_resurrect", "infected", "burning",
             "crumbs_fed", "crumb_beaten", "crumb_angry", "crumb_fought", "blessing")

    def to_save(self):
        data = {name: getattr(self, name) for name in self.SAVED}
        data.update(inventory=dict(self.inventory), upgrades=dict(self.upgrades), stats=dict(self.stats),
                    crumbs_found=list(self.crumbs_found))
        return data

    @classmethod
    def from_save(cls, data):
        p = cls()
        for name in cls.SAVED:
            if name in data:
                setattr(p, name, data[name])
        p.inventory = {k: int(v) for k, v in data.get("inventory", {}).items() if k in ITEMS_BY_KEY and v > 0}
        for key, level in data.get("upgrades", {}).items():
            if key in p.upgrades:                  # skip upgrades that no longer exist
                p.upgrades[key] = int(level)
        p.stats.update({k: v for k, v in data.get("stats", {}).items() if k in p.stats})
        p.crumbs_found = [int(c) for c in data.get("crumbs_found", [])]
        p.hp = max(1, min(p.hp, p.max_hp))
        return p
