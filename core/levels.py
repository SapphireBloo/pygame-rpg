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
        # Level 1 uses the original intro, which plays when you first start walking
        "arrival": [],
    },
    {
        "name": "Witch's Hollow",
        "subtitle": "Something's bubbling, and it isn't soup",
        "background": "bg_1.png",
        "accent": (120, 255, 80),
        "ghost_tint": (170, 255, 150),
        "ghosts": 3,
        "enemy": {"name": "Slime Ghost", "hp": 65, "damage": (7, 16), "candy": (2, 4)},
        "arrival": [
            "Smell that? Eye of newt and bad decisions.",
            "The witch who lives here doesn't like visitors. Or anyone.",
            "Her ghosts hit harder. Stock up on candy before you push on.",
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
        "arrival": [
            "Ugh. I hate this place. Too many legs.",
            "Those red berries? Don't eat 'em. Trust me.",
            "The ghosts here have been snacking on spiders. They're tougher.",
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
        "arrival": [
            "Well, kid... welcome to my neighborhood.",
            "Careful. The locals don't stay buried around here.",
            "Somewhere past those gates is the one who started all this.",
            "Keep your chin up. You're gonna need it.",
        ],
    },
]

# Shown after the last level's exit
ENDING = {
    "title": "To Be Continued...",
    "subtitle": "Thanks for playing Chin Check Charlie",
}
