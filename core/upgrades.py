"""Upgrade catalog (sold by the Blacksmith at camp).

Every upgrade has tiers. Charlie buys them in order, and each tier costs more
than the last, so there's always something to save candy for. A tier's "desc"
says what that tier does (shown on the Blacksmith's card before you buy it).

The effect numbers live in core/player.py (look for the upgrade's key).
"icon" names a drawing in core/icons.py.
"""

UPGRADES = [
    {"key": "max_hp", "icon": "heart_plus", "name": "Tough Hide", "tiers": [
        {"cost": 4,  "desc": "Max HP +20"},
        {"cost": 8,  "desc": "Max HP +20 more (+40 total)"},
        {"cost": 14, "desc": "Max HP +20 more (+60 total)"},
        {"cost": 22, "desc": "Max HP +20 more (+80 total)"},
    ]},
    {"key": "heal_boost", "icon": "heal", "name": "Potion Boost", "tiers": [
        {"cost": 3,  "desc": "Healing potions restore 10 more HP"},
        {"cost": 7,  "desc": "Healing potions restore 20 more HP"},
        {"cost": 12, "desc": "Healing potions restore 30 more HP"},
    ]},
    {"key": "bomb_power", "icon": "bomb_power", "name": "Bomb Power", "tiers": [
        {"cost": 3,  "desc": "Bombs deal +10 damage"},
        {"cost": 7,  "desc": "Bombs deal +20 damage"},
        {"cost": 12, "desc": "Bombs deal +30 damage"},
    ]},
    {"key": "resurrect", "icon": "revive", "name": "Second Wind", "tiers": [
        {"cost": 10, "desc": "Revive once per game, at half HP"},
        {"cost": 22, "desc": "Revive once per chapter, at full HP"},
    ]},

    # Fighting-style upgrades: each rewards a different skill
    {"key": "quick_hands", "icon": "quick_hands", "name": "Quick Hands", "tiers": [
        {"cost": 5,  "desc": "Jab combos go up to 4 hits"},
        {"cost": 10, "desc": "Every jab hits for +2 damage"},
        {"cost": 16, "desc": "Jab combos go up to 5 hits"},
    ]},
    {"key": "heavy_hands", "icon": "heavy_hands", "name": "Heavy Hands", "tiers": [
        {"cost": 5,  "desc": "Sloppy Haymakers whiff less often"},
        {"cost": 10, "desc": "Haymakers hit 15% harder"},
        {"cost": 16, "desc": "Daze stacks add 30% each (was 20%)"},
    ]},
    {"key": "counter_puncher", "icon": "counter", "name": "Counter Puncher", "tiers": [
        {"cost": 4,  "desc": "Parry counters hit 50% harder"},
        {"cost": 9,  "desc": "Parry counters also daze the enemy"},
        {"cost": 15, "desc": "Parry counters hit twice as hard"},
    ]},
    {"key": "iron_chin", "icon": "iron_chin", "name": "Iron Chin", "tiers": [
        {"cost": 5,  "desc": "Chin meter fills 20% faster"},
        {"cost": 10, "desc": "Chin meter fills 40% faster"},
        {"cost": 16, "desc": "Chin Check hits 25% harder"},
    ]},
    {"key": "thick_skin", "icon": "thick_skin", "name": "Thick Skin", "tiers": [
        {"cost": 6,  "desc": "30% chance to shrug off infection and burns"},
        {"cost": 12, "desc": "Infection and burns hurt half as much"},
    ]},
]

UPGRADES_BY_KEY = {u["key"]: u for u in UPGRADES}

NUMERALS = ("", "I", "II", "III", "IV", "V")


def tier_name(upgrade, level):
    """'Tough Hide II' for level 2. Level 0 is just the name."""
    return f"{upgrade['name']} {NUMERALS[level]}".strip()
