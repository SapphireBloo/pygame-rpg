class Player:
    def __init__(self):
        self.name = "Hero"
        self.hp = 100
        self.max_hp = 100
        self.level = 1
        self.xp = 0
        self.xp_to_next = 50
        self.inventory = {
            "potion": 3,
            "bomb": 1
        }
        self.blocking = False

    def attack(self):
        return 10 + self.level * 2

    def block(self):
        self.blocking = True

    def heal(self):
        if self.inventory["potion"] > 0:
            self.inventory["potion"] -= 1
            heal_amt = 25
            self.hp = min(self.max_hp, self.hp + heal_amt)
            return heal_amt
        return 0

    def use_bomb(self):
        if self.inventory["bomb"] > 0:
            self.inventory["bomb"] -= 1
            return 30 + self.level * 3
        return 0

    def gain_xp(self, amount):
        self.xp += amount
        messages = []
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.max_hp += 10
            self.hp = self.max_hp
            self.xp_to_next = int(self.xp_to_next * 1.5)
            messages.append("🆙 You leveled up to Lv " + str(self.level) + "!")
        return messages
