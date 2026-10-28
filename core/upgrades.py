"""Candy Shop upgrade catalog.

The shop and the HUD both read from this one list, so adding an upgrade is a
one-line change here (plus whatever code makes it do something). "icon" names a
drawing in core/icons.py.
"""

UPGRADES = [
    {"key": "max_hp_plus_25", "icon": "heart_plus", "name": "Max HP +25", "short": "HP+25",
     "desc": "Increase max HP by 25", "cost": 3},
    {"key": "bomb_power_plus_10", "icon": "bomb_power", "name": "Bomb Power +10", "short": "Bomb++",
     "desc": "Bombs deal +10 damage", "cost": 3},
    {"key": "heal_boost", "icon": "heal", "name": "Heal Boost", "short": "Heal+",
     "desc": "Heals restore 35 HP instead of 25", "cost": 2},
    {"key": "double_candy", "icon": "double_candy", "name": "Double Candy", "short": "2x Candy",
     "desc": "Get 2x candy from battles", "cost": 4},
    {"key": "auto_block", "icon": "shield", "name": "Auto Block", "short": "Auto-Block",
     "desc": "Auto-block first hit every battle", "cost": 5},
    {"key": "resurrect_once", "icon": "revive", "name": "Resurrect Once", "short": "Revive",
     "desc": "Survive death once", "cost": 6},
]

UPGRADES_BY_KEY = {u["key"]: u for u in UPGRADES}
