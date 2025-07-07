import random

class Enemy:
    def __init__(self, name="Ghost", hp=50, xp=30):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.xp = xp

    def attack(self):
        return random.randint(5, 15)
