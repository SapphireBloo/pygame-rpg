"""The menus Charlie uses in camp (and his bag, anywhere):

  BlacksmithShop   permanent upgrades in tiers that cost more each time (core/upgrades.py)
  CrowShop         BUY items / SELL items and monster trophies (core/items.py)
  BagMenu          see what you're carrying; drink potions outside of battle (I)
  CrumbMenu        pet Crumb, feed him snacks and Golden Crumbs, and (eventually) fight him
"""
import random

import pygame

from core.items import ITEMS, ITEMS_BY_KEY, SHOP_STOCK, SNACKS
from core.icons import draw_icon
from core.shop_modal import CardShop, Entry, NEED_RED
from core.ui import HEAL_GREEN, WHITE, INK, get_font, outlined_text
from core.upgrades import UPGRADES, UPGRADES_BY_KEY, NUMERALS, tier_name

CANT = (255, 200, 120)


class BlacksmithShop(CardShop):
    title = "BLACKSMITH"
    subtitle = "\"Bring candy. I'll bring the hammer.\""
    accent = (255, 140, 40)
    hint = "Click a price to buy   |   Esc to close"

    def entries(self):
        out = []
        for u in UPGRADES:
            level, total = self.player.has(u["key"]), len(u["tiers"])
            tier = self.player.next_tier(u)
            if tier is None:            # bought every tier
                out.append(Entry(u["key"], tier_name(u, level), u["tiers"][-1]["desc"], u.get("icon", "candy"),
                                 stamp="MAXED", done=True, tier=(level, total)))
                continue
            short = tier["cost"] - self.player.candy
            out.append(Entry(u["key"], tier_name(u, level + 1), tier["desc"], u.get("icon", "candy"),
                             button=str(tier["cost"]), button_icon="candy", enabled=short <= 0,
                             note=f"need {short} more" if short > 0 else None, tier=(level, total)))
        return out

    def activate(self, entry):
        upgrade = UPGRADES_BY_KEY[entry.key]
        tier = self.player.next_tier(upgrade)
        if tier is None:
            return False, "", WHITE
        if self.player.buy_upgrade(upgrade):
            return True, f"Forged: {tier_name(upgrade, self.player.has(upgrade['key']))}!", HEAL_GREEN
        return False, f"Need {tier['cost'] - self.player.candy} more candy!", NEED_RED


class CrowShop(CardShop):
    title = "THE CROW"
    subtitle = "\"Shinies for sweeties. Caw.\""
    accent = (220, 60, 70)
    tabs = ("BUY", "SELL")
    hint = "Tab switches Buy / Sell   |   Esc to close"

    @property
    def empty_text(self):
        return "\"Nothing to sell? Bring me trophies from the things you punch. Caw.\""

    def entries(self):
        p = self.player
        if self.tab == 0:
            out = []
            for item in SHOP_STOCK:
                short = item["buy"] - p.candy
                out.append(Entry(item["key"], item["name"], item["desc"], item["icon"],
                                 button=str(item["buy"]), button_icon="candy", enabled=short <= 0,
                                 count=p.count(item["key"]) or None,
                                 note=f"need {short} more" if short > 0 else None))
            return out
        return [Entry(item["key"], item["name"], item["desc"], item["icon"],
                      button=f"+{item['sell']}", button_icon="candy", count=p.count(item["key"]),
                      note=("snack" if item.get("snack") else "trophy") if not item.get("buy") else None,
                      note_color=(200, 180, 120))
                for item in ITEMS if p.count(item["key"]) and item.get("sell")]

    def activate(self, entry):
        p, item = self.player, ITEMS_BY_KEY[entry.key]
        if self.tab == 0:
            if p.candy < item["buy"]:
                return False, f"Need {item['buy'] - p.candy} more candy!", NEED_RED
            p.candy -= item["buy"]
            p.add_item(item["key"])
            return True, f"Bought a {item['name']}!", HEAL_GREEN
        if not p.remove_item(item["key"]):
            return False, "", WHITE
        p.candy += item["sell"]
        return True, f"Sold {item['name']} for {item['sell']} candy.", HEAL_GREEN


class BagMenu(CardShop):
    """Charlie's inventory: candy (top right), item counts, owned upgrades, and the items themselves."""
    title = "BAG"
    accent = (150, 200, 255)
    hint = "Click Use to drink   |   Esc or I to close"
    empty_text = "Your bag is empty. The Crow sells potions and bombs at camp."

    @property
    def subtitle(self):
        p = self.player
        potions = p.count("potion") + p.count("elixir") + p.count("remedy")
        trophies = sum(p.count(item["key"]) for item in ITEMS
                       if not item.get("buy") and not item.get("snack") and item.get("sell"))
        return f"Potions: {potions}    Bombs: {p.count('bomb')}    Trophies: {trophies}"

    def _draw_header(self, surf):
        super()._draw_header(surf)
        # Owned upgrades as a row of little badges next to the title
        owned = [u for u in UPGRADES if self.player.has(u["key"])]
        x, y = 130, 10
        surf.blit(get_font(12, bold=True).render("UPGRADES", True, (160, 190, 230)), (x, y))
        if not owned:
            surf.blit(get_font(13).render("none yet: visit the Blacksmith", True, (130, 125, 145)), (x, y + 18))
        for i, u in enumerate(owned):
            center = (x + 14 + i * 33, y + 30)
            pygame.draw.circle(surf, INK, center, 15)
            pygame.draw.circle(surf, (18, 12, 22), center, 14)
            pygame.draw.circle(surf, (110, 150, 200), center, 14, 2)
            draw_icon(surf, u.get("icon", "candy"), center, 21)
            level = outlined_text(NUMERALS[self.player.has(u["key"])], 11, WHITE, True, 1)
            surf.blit(level, level.get_rect(center=(center[0] + 11, center[1] + 11)))

    def handle_event(self, event):
        if self.visible and event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            self.close()
            return
        super().handle_event(event)

    def entries(self):
        p, out = self.player, []
        for item in ITEMS:
            n = p.count(item["key"])
            if not n:
                continue
            if item.get("field"):
                useful = p.item_useful(item["key"])
                out.append(Entry(item["key"], item["name"], item["desc"], item["icon"], button="Use",
                                 enabled=useful, count=n, note=None if useful else "full HP",
                                 note_color=CANT))
            elif item.get("battle"):
                out.append(Entry(item["key"], item["name"], item["desc"], item["icon"], count=n,
                                 note="use it in battle", note_color=CANT))
            elif item.get("snack") or item["key"] == "golden_crumb":
                out.append(Entry(item["key"], item["name"], item["desc"], item["icon"], count=n,
                                 note="feed it to Crumb at camp", note_color=(255, 210, 140)))
            else:
                out.append(Entry(item["key"], item["name"], item["desc"], item["icon"], count=n,
                                 note="sell it to the Crow", note_color=(200, 180, 120)))
        return out

    def activate(self, entry):
        result = self.player.use_item(entry.key)
        if not result:
            return False, "You don't need that right now.", CANT
        bits = []
        if result["healed"]:
            bits.append(f"+{result['healed']} HP")
        if result["cured"]:
            bits.append("cured!")
        return True, f"{ITEMS_BY_KEY[entry.key]['name']}: {', '.join(bits) or 'done'}", HEAL_GREEN


GOLD_TEXT = (255, 215, 130)


class CrumbMenu(CardShop):
    """Crumb: pet him, feed him snacks (a blessing for the next chapter) or Golden Crumbs,
    and once he's eaten all four, at the last camp, take him on."""
    title = "CRUMB"
    accent = (255, 200, 110)
    hint = "Click a button   |   Esc to close"

    def __init__(self, screen, player, portrait=None, final_camp=False, on_pet=None, on_fight=None):
        super().__init__(screen, player, portrait)
        self.final_camp = final_camp
        self.on_pet = on_pet          # Crumb hops and hearts pop out
        self.on_fight = on_fight      # start the secret boss fight

    @property
    def subtitle(self):
        p = self.player
        if p.companion:
            return "Your partner: every snack blessing, plus Loaf Launch"
        if p.blessing:
            return f"Blessed: {ITEMS_BY_KEY[p.blessing]['snack']}"
        return f"Golden Crumbs eaten: {min(p.crumbs_fed, 4)} / 4"

    def entries(self):
        p, out = self.player, []
        out.append(Entry("pet", "Pet Crumb", "He wiggles. You both feel a little better.", "crumb", button="Pet"))
        for key in SNACKS:
            if p.count(key) and not p.companion:        # (a partner already gives every blessing)
                item = ITEMS_BY_KEY[key]
                note = "replaces your blessing" if p.blessing else None
                out.append(Entry(key, f"Feed: {item['name']}", item["snack"] + ".", item["icon"], button="Feed",
                                 count=p.count(key), note=note, note_color=CANT))
        if p.count("golden_crumb"):
            out.append(Entry("golden_crumb", "Feed: Golden Crumb", "He's been dreaming about these.", "golden_crumb",
                             button="Feed", count=p.count("golden_crumb"), note=f"{p.crumbs_fed} / 4 eaten",
                             note_color=GOLD_TEXT))
        if p.crumb_beaten:
            out.append(Entry("partner", "Partner in Crust", "All snack buffs, plus Loaf Launch.", "golden_crust",
                             stamp="PARTNER", done=True))
        elif p.crumb_fought:
            out.append(Entry("calm", "Crust Eternal: undefeated", "He won. He's being very gracious about it. "
                             "Mostly.", "golden_crust", done=True))
        elif p.crumbs_fed >= 4:
            out.append(Entry("quiet", "Crumb is... quiet", "He's staring at the portal. Very, very still. "
                             "Probably fine.", "golden_crust"))
        if len(out) == 1:
            out.append(Entry("hungry", "No snacks", "Monsters drop butter, jam, and sugar, and every boss leaves "
                             "a snack. Golden Crumbs hide somewhere tricky in every chapter.", "bag",
                             note="come back with a snack", note_color=CANT))
        return out

    def activate(self, entry):
        p = self.player
        if entry.key == "pet":
            if self.on_pet:
                self.on_pet()
            return True, random.choice(PET_LINES), HEAL_GREEN
        if entry.key == "fight":
            self.close()
            if self.on_fight:
                self.on_fight()
            return True, "", WHITE
        result = p.feed_crumb(entry.key)
        if result is None:
            return False, "", WHITE
        if self.on_pet:
            self.on_pet()
        if result == "golden":
            if p.crumbs_fed >= 4:
                return True, "Crumb glows... he looks at you differently now.", GOLD_TEXT
            return True, f"Crumb munches the Golden Crumb! ({p.crumbs_fed}/4)", GOLD_TEXT
        return True, f"Crumb's blessing: {ITEMS_BY_KEY[entry.key]['snack']}!", HEAL_GREEN


PET_LINES = ("Crumb wiggles happily!", "Crumb does a little hop!", "Crumb: \"Again! Again!\"",
             "Crumb leans into the pets.", "Crumb: \"You smell like candy.\"")
