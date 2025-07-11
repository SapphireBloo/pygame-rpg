import random
from core.combat_text import CombatText

class BattleManager:
    def __init__(self, player, enemy, combat_texts, log_callback):
        self.player = player
        self.enemy = enemy
        self.combat_texts = combat_texts
        self.log = log_callback

    def player_action(self, choice):
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)

        if choice == "Attack":
            dmg = self.player.attack()
            self.enemy.hp -= dmg
            self.log(f"Charlie punches for {dmg}!")
            self.combat_texts.append(CombatText(f"-{dmg}", 575 + offset_x, 380 + offset_y, (255, 80, 80)))

        elif choice == "Heal":
            healed = self.player.heal()
            if healed:
                self.log(f"Charlie drinks a potion (+{healed} HP).")
                self.combat_texts.append(CombatText(f"+{healed}", 125 + offset_x, 380 + offset_y, (100, 255, 100)))
            else:
                self.log("No potions left!")

        elif choice == "Block":
            self.player.block()
            self.log("Charlie braces for impact...")
            self.combat_texts.append(CombatText("Block!", 125 + offset_x, 380 + offset_y, (150, 200, 255)))

        elif choice == "Item":
            dmg = self.player.use_bomb()
            if dmg:
                self.enemy.hp -= dmg
                self.log(f"Charlie hurls a bomb for {dmg}!")
                self.combat_texts.append(CombatText(f"-{dmg}", 575 + offset_x, 380 + offset_y, (255, 100, 100)))
            else:
                self.log("No bombs left!")

        return "enemy_turn"

    def enemy_action(self):
        dmg = self.enemy.attack()
        if self.player.blocking:
            dmg //= 2
            self.player.blocking = False
            self.log("Blocked! Damage halved.")
            self.combat_texts.append(CombatText("Blocked!", 125, 380, (200, 200, 255)))
        self.player.hp -= dmg
        self.log(f"The ghost claws for {dmg}!")
        self.combat_texts.append(CombatText(f"-{dmg}", 125, 380, (255, 80, 80)))

        return "player_turn"
