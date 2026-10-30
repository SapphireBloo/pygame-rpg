"""Item catalog: what the Crow sells and buys, what monsters drop, and what
each item does when used.

Each item:
  key     id used in the player's inventory
  name    shown in menus
  icon    drawing in core/icons.py
  desc    one line for the shop/bag card
  buy     price at the Crow (None = he doesn't sell it)
  sell    what the Crow pays for one
  battle  can be used from the Items menu in a fight
  field   can be used from the bag (I) while exploring
  plus what it does: heal (HP), cure (burning/infection), meter (Chin meter),
  damage ("bomb": thrown at the enemy)

Monster loot ("trophies") can't be used: it's for selling to the Crow.
"""

ITEMS = [
    {"key": "potion", "name": "Gourd-Aid", "icon": "potion", "desc": "Pumpkin-flavored potion. +40 HP.",
     "buy": 4, "sell": 2, "battle": True, "field": True, "heal": 40},
    {"key": "remedy", "name": "Remedy", "icon": "remedy", "desc": "Puts out burns, cures infection, +10 HP.",
     "buy": 3, "sell": 1, "battle": True, "field": True, "heal": 10, "cure": True},
    {"key": "elixir", "name": "Pumpkin Elixir", "icon": "elixir", "desc": "Full HP, and cures everything.",
     "buy": 12, "sell": 6, "battle": True, "field": True, "heal": 9999, "cure": True},
    {"key": "bomb", "name": "Bomb", "icon": "bomb", "desc": "Throw it for big damage. Battle only.",
     "buy": 5, "sell": 2, "battle": True, "field": False, "damage": "bomb"},
    {"key": "chin_juice", "name": "Chin Juice", "icon": "chin_juice", "desc": "Chin meter +50. Battle only.",
     "buy": 6, "sell": 3, "battle": True, "field": False, "meter": 50},

    # Snacks for Crumb (feed him at camp for a blessing that lasts the next chapter). Monsters
    # sometimes drop them and every boss leaves one. The Crow will buy them, but Crumb is nicer.
    {"key": "butter", "name": "Butter Pat", "icon": "butter", "desc": "Feed Crumb: +15 max HP next chapter.",
     "buy": None, "sell": 2, "snack": "+15 max HP next chapter"},
    {"key": "jam", "name": "Jam Jar", "icon": "jam", "desc": "Feed Crumb: Chin head start next chapter.",
     "buy": None, "sell": 2, "snack": "Fights start with 30 Chin, next chapter"},
    {"key": "sugar", "name": "Sugar Cube", "icon": "sugar", "desc": "Feed Crumb: harder punches next chapter.",
     "buy": None, "sell": 2, "snack": "+3 punch damage next chapter"},
    {"key": "golden_crumb", "name": "Golden Crumb", "icon": "golden_crumb",
     "desc": "It glows. Crumb would REALLY like this.", "buy": None, "sell": None},

    # Trophies: monsters drop them, the Crow buys them
    {"key": "ectoplasm", "name": "Ectoplasm", "icon": "ectoplasm", "desc": "Ghost goo. Still wiggling.",
     "buy": None, "sell": 2},
    {"key": "knight_spur", "name": "Knight's Spur", "icon": "spur", "desc": "Off a Death Knight's boot.",
     "buy": None, "sell": 3},
    {"key": "satyr_antler", "name": "Satyr Antler", "icon": "antler", "desc": "Still warm. Smells smoky.",
     "buy": None, "sell": 3},
    {"key": "zombie_tooth", "name": "Zombie Tooth", "icon": "tooth", "desc": "Gross. The Crow loves these.",
     "buy": None, "sell": 3},
    {"key": "reaper_shard", "name": "Reaper Shard", "icon": "shard", "desc": "A sliver of Mortis's scythe.",
     "buy": None, "sell": 10},
    {"key": "hex_stone", "name": "Hex Stone", "icon": "hex_stone", "desc": "Grimwald's focus. It hums.",
     "buy": None, "sell": 12},
    {"key": "worm_scale", "name": "Worm Scale", "icon": "scale", "desc": "Fireproof. Probably.",
     "buy": None, "sell": 14},
    {"key": "demon_horn", "name": "Demon Horn", "icon": "horn", "desc": "Malgorath's. Still smoldering.",
     "buy": None, "sell": 20},
    {"key": "golden_crust", "name": "Golden Crust", "icon": "golden_crust", "desc": "Proof you beat the Crust Eternal.",
     "buy": None, "sell": 40},
]
ITEMS_BY_KEY = {item["key"]: item for item in ITEMS}
SNACKS = [item["key"] for item in ITEMS if item.get("snack")]
SHOP_STOCK = [item for item in ITEMS if item.get("buy")]          # what the Crow sells
BATTLE_ITEMS = [item for item in ITEMS if item.get("battle")]     # order shown in the battle Items menu

# What each kind of enemy drops: (item key, chance)
LOOT = {
    "ghost": ("ectoplasm", 0.5),
    "knight": ("knight_spur", 0.5),
    "satyr": ("satyr_antler", 0.5),
    "zombie": ("zombie_tooth", 0.5),
    "reaper": ("reaper_shard", 1.0),
    "warlock": ("hex_stone", 1.0),
    "worm": ("worm_scale", 1.0),
    "demon": ("demon_horn", 1.0),
    "bread": ("golden_crust", 1.0),
}
SNACK_DROP_CHANCE = 0.15     # regular monsters; bosses always leave a snack

STARTING_ITEMS = {"bomb": 1, "potion": 2}

# Regular monsters sometimes drop a Gourd-Aid too (bosses always leave a trophy instead)
POTION_DROP_CHANCE = 0.3
