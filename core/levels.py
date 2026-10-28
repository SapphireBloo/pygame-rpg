"""Level definitions. Edit this file to rename levels, rebalance them, or
change what Whisper Jack says. Add a level by adding a dict to LEVELS.

Each level:
  name        Shown on the chapter title card and the HUD
  subtitle    Small line under the title on the card
  background  File name in assets/images/backgrounds/
  accent      (R, G, B) color for the exit portal and title card glow
  ghost_tint  (R, G, B) tint for this level's ghost sprite, or None for normal
  ghosts      How many ghost fights stand between you and the exit
  enemy       Stats for this level's ghosts (passed to Enemy)
  zombies     Optional list of roaming zombies, in the order you meet them after
              the ghosts. "sprite" is the folder in assets/images (male/female).
  boss        Optional boss waiting before the exit portal: stats plus "taunt"
              (what he says before the fight), "lunge" (how far he surges in), and
              optionally "defeat_quote" (Whisper Jack's line when he goes down).
              "sprite" picks the art (see core/enemy_art.py, where boss sizes live)
              and "kind" picks how he fights (see core/enemy.py).
  arrival     Whisper Jack's lines when you arrive (empty list = he stays quiet)
"""

LEVELS = [
    {
        "name": "The Cabin",
        "subtitle": "Where every bad night starts",
        "background": "bg_0.png",
        "accent": (255, 140, 40),
        "ghost_tint": None,
        "ghosts": 3,
        "enemy": {"name": "Ghost", "hp": 50, "damage": (5, 15), "candy": (1, 3)},
        "boss": {
            "sprite": "death", "kind": "reaper", "boss": True,
            "name": "Mortis, Bringer of Death", "hp": 170, "damage": (8, 14), "candy": (5, 8),
            "lunge": 0,      # his scythe wave crosses the whole clearing
            "taunt": [
                "Another lost soul wanders into my cabin...",
                "I have reaped kings, little gourd. You are barely a side dish.",
                "Hold still. This will only hurt... forever.",
            ],
            "defeat_quote": "Even Death takes a nap, I guess. Nice hands, kid.",
        },
        # Level 1 uses the original intro, which plays when you first start walking
        "arrival": [],
    },
    {
        "name": "Warlock's Hollow",
        "subtitle": "Something's bubbling, and it isn't soup",
        "background": "bg_1.png",
        "accent": (120, 255, 80),
        "ghost_tint": (170, 255, 150),
        "ghosts": 3,
        "enemy": {"name": "Slime Ghost", "hp": 65, "damage": (7, 16), "candy": (2, 4)},
        "boss": {
            "sprite": "warlock", "kind": "warlock", "boss": True,
            "name": "Grimwald the Warlock", "hp": 180, "damage": (9, 16), "candy": (8, 12),
            "lunge": 10,    # short: his spells reach a long way
            "taunt": [
                "A pumpkin? In MY hollow? How... seasonal.",
                "My spirits will scatter your seeds across this swamp.",
                "Come then, little gourd. Let's see how hard that chin really is.",
            ],
        },
        "arrival": [
            "Smell that? Eye of newt and bad decisions.",
            "A warlock named Grimwald runs this swamp. He doesn't like visitors. Or anyone.",
            "His ghosts hit harder, and he's worse. Watch for the HEX STORM: it drains your Chin meter.",
            "Stock up on candy before you face him.",
        ],
    },
    {
        "name": "The Bleeding Woods",
        "subtitle": "Mind the webs",
        "background": "bg_2.png",
        "accent": (230, 50, 60),
        "ghost_tint": (255, 150, 160),
        "ghosts": 3,
        "enemy": {"name": "Web Wraith", "hp": 80, "damage": (8, 18), "candy": (2, 5)},
        "boss": {
            "sprite": "fireworm", "kind": "worm", "boss": True,
            "name": "Scorchmaw the Fire Worm", "hp": 220, "damage": (10, 17), "candy": (9, 13),
            "lunge": 170,    # it rears up and strikes; its FIREBALL is spat from where it stands
            "taunt": [
                "*skitter skitter* ...smells like pumpkin.",
                "These woods are MY nest. Every web. Every bone.",
                "Roasted pumpkin seeds are my favorite snack. Hold still!",
            ],
            "defeat_quote": "Barbecued bug. Smells awful. Good work.",
        },
        "arrival": [
            "Ugh. I hate this place. Too many legs.",
            "Those red berries? Don't eat 'em. Trust me.",
            "The ghosts here have been snacking on spiders. They're tougher.",
            "And something BIG nests at the end of these woods. A fire worm.",
            "If it spits a fireball, time your block. Burns keep hurting every turn until you eat candy.",
        ],
    },
    {
        "name": "The Graveyard",
        "subtitle": "Home sweet home",
        "background": "bg_3.png",
        "accent": (90, 220, 255),
        "ghost_tint": (160, 230, 255),
        "ghosts": 0,
        "enemy": {"name": "Grave Spirit", "hp": 100, "damage": (10, 20), "candy": (3, 6)},
        "zombies": [
            {"sprite": "male", "name": "Rotting Rick", "hp": 100, "damage": (10, 20), "candy": (3, 6)},
            {"sprite": "female", "name": "Ghoulish Gwen", "hp": 90, "damage": (12, 22), "candy": (3, 6)},
            {"sprite": "male", "name": "Rotting Rick", "hp": 110, "damage": (10, 20), "candy": (3, 6)},
            {"sprite": "female", "name": "Ghoulish Gwen", "hp": 100, "damage": (12, 22), "candy": (4, 7)},
        ],
        "boss": {
            "sprite": "demon", "kind": "demon", "boss": True,
            "name": "Malgorath the Demon", "hp": 260, "damage": (11, 18), "candy": (15, 20),
            "lunge": 20,     # that cleaver reaches across the graveyard
            "taunt": [
                "So. The little pumpkin made it to my graveyard.",
                "The ghosts. The hexes. The dead that won't stay buried. All MINE.",
                "Come then, Charlie. Show me this famous chin.",
            ],
            "defeat_quote": "You did it, kid. You actually did it. ...Got any candy?",
        },
        "arrival": [
            "Well, kid... welcome to my neighborhood.",
            "Careful. The locals don't stay buried around here.",
            "Somewhere past those gates is the one who started all this. A demon.",
            "His Hellfire Cleave burns you AND drains your Chin meter. Parry it if you can.",
            "Keep your chin up. You're gonna need it.",
        ],
    },
]

# Shown after the last level's exit
ENDING = {
    "title": "To Be Continued...",
    "subtitle": "Thanks for playing Chin Check Charlie",
}
