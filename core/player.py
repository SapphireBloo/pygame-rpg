class Player:
    def __init__(self):
        self.name = "Charlie"  # Rename as you want
        self.hp = 100
        self.max_hp = 100
        self.level = 1
        self.last_candy_reward = 0  # Track how much candy was earned last battle

        self.candy = 0  # Candy as currency and healing resource
        
        self.inventory = {
            "bomb": 1
        }
        self.blocking = False

        # Position (used by ExplorationScene)
        self.x = 50
        self.y = 400

        # --- NEW: Upgrade System ---
        self.upgrades = {
            "max_hp_plus_25": False,
            "bomb_power_plus_10": False,
            "auto_block": False,
            "double_candy": False,
            "heal_boost": False,
            "resurrect_once": False
        }
        self.used_resurrect = False  # tracks if resurrect was already used

    def attack(self):
        return 10 + self.level * 2

    def block(self):
        self.blocking = True

    def heal(self):
        candy_needed = 1
        base_heal = 25

        if self.upgrades.get("heal_boost"):
            base_heal = 35  # heal more if upgrade bought

        if self.candy >= candy_needed:
            self.candy -= candy_needed
            self.hp = min(self.max_hp, self.hp + base_heal)
            return base_heal
        return 0

    def use_bomb(self):
        if self.inventory["bomb"] > 0:
            self.inventory["bomb"] -= 1
            base_damage = 30 + self.level * 3

            if self.upgrades.get("bomb_power_plus_10"):
                base_damage += 10

            return base_damage
        return 0

    def add_candy(self, amount):
        if self.upgrades.get("double_candy"):
            amount *= 2
        self.candy += amount
