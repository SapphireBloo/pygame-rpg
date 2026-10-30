"""Level definitions. Edit this file to rename levels, rebalance them, or
change what Whisper Jack says. Add a level by adding a dict to LEVELS.

Each level:
  name        Shown on the chapter title card and the HUD
  subtitle    Small line under the title on the card
  background  File name in assets/images/backgrounds/
  accent      (R, G, B) color for the exit portal and title card glow
  ghost_tint  (R, G, B) tint for ghost sprites in this level, or None for normal
  monsters    The roaming monsters you meet, in order. Each one is a dict of stats
              (passed to Enemy) plus "sprite" (its art: ghost, knight, satyr, male,
              female) and "kind" (how it fights and moves: ghost, knight, satyr,
              zombie). See core/enemy.py and core/roaming_enemy.py.
  boss        Optional boss waiting before the exit portal: stats plus "taunt"
              (what he says before the fight), "lunge" (how far he surges in), and
              optionally "defeat_quote" (Whisper Jack's line when he goes down).
              "sprite" picks the art (see core/enemy_art.py, where boss sizes live)
              and "kind" picks how he fights (see core/enemy.py).
  arrival     Whisper Jack's lines when you arrive (empty list = he stays quiet)

Where the monsters stand, the boss's spot, the obstacles, and the hidden Golden Crumbs
are in core/level_layouts.py.
"""

LEVELS = [
    {
        "name": "The Cabin",
        "subtitle": "Where every bad night starts",
        "background": "bg_0.png",
        "accent": (255, 140, 40),
        "ghost_tint": None,
        "monsters": [{"sprite": "ghost", "kind": "ghost", "name": "Ghost", "hp": 50, "damage": (5, 15), "candy": (1, 3)}] * 3,
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
        "ghost_tint": None,
        "monsters": [
            {"sprite": "knight", "kind": "knight", "name": "Death Knight", "hp": 70, "damage": (7, 16), "candy": (2, 4)},
        ] * 3,
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
            "His Death Knights patrol the swamp. Sloppy punches just bounce off that armor, so TIME your hits.",
            "And he's worse. Watch for the HEX STORM: it drains your Chin meter.",
            "Stock up on candy before you face him.",
        ],
    },
    {
        "name": "The Bleeding Woods",
        "subtitle": "Mind the webs",
        "background": "bg_2.png",
        "accent": (230, 50, 60),
        "ghost_tint": None,
        "monsters": [
            {"sprite": "satyr", "kind": "satyr", "name": "Satyr", "hp": 80, "damage": (8, 18), "candy": (2, 5)},
        ] * 3,
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
            "Satyrs run these woods. Little fire-starters. Their antler beam will set you BURNING.",
            "And something BIG nests at the end of these woods. A fire worm.",
            "If it spits a fireball, time your block. Burns keep hurting every turn until you drink a Remedy.",
        ],
    },
    {
        "name": "The Graveyard",
        "subtitle": "Home sweet home",
        "background": "bg_3.png",
        "accent": (90, 220, 255),
        "ghost_tint": None,
        "monsters": [
            {"sprite": "male", "name": "Rotting Rick", "hp": 100, "damage": (10, 20), "candy": (3, 6)},
            {"sprite": "female", "name": "Ghoulish Gwen", "hp": 90, "damage": (12, 22), "candy": (3, 6)},
            {"sprite": "male", "name": "Rotting Rick", "hp": 110, "damage": (10, 20), "candy": (3, 6)},
            {"sprite": "female", "name": "Ghoulish Gwen", "hp": 100, "damage": (12, 22), "candy": (4, 7)},
        ],
        "boss": {
            "sprite": "demon", "kind": "demon", "boss": True,
            "name": "Malgorath the Demon", "hp": 240, "damage": (11, 18), "candy": (15, 20),
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
            "And their bites INFECT. It won't wear off on its own. Keep Remedies handy.",
            "Somewhere past those gates is the one who started all this. A demon.",
            "His Hellfire Cleave burns you AND drains your Chin meter. Parry it if you can.",
            "Keep your chin up. You're gonna need it.",
        ],
    },
]

VOID_BACKGROUND = "final/Purple Nebula/Purple_Nebula_04-1024x1024.png"

LEVELS.append({
    # The final chapter: no platforms or traps. Charlie walks slowly through the Void while
    # Whisper Jack explains it (he doesn't stop Charlie). After each speech one of the Void's
    # creatures appears, in order, and then Gorge waits at the end. See scenes/void_walk.py.
    "name": "The Void",
    "subtitle": "Where all the candy goes",
    "background": VOID_BACKGROUND,
    "accent": (200, 90, 255),
    "ghost_tint": None,
    "final": True,          # after Gorge: the ending and credits (no camp)
    "void": True,           # the slow walk, narrated
    "monsters": [
        {"sprite": "catto", "kind": "catto", "name": "Catto", "hp": 120, "damage": (11, 20), "candy": (5, 8)},
        {"sprite": "madghost", "kind": "madghost", "name": "The Mad Ghost", "hp": 135, "damage": (12, 21),
         "candy": (5, 8)},
        {"sprite": "mage", "kind": "mage", "name": "The Void Mage", "hp": 145, "damage": (12, 22), "candy": (6, 9)},
        {"sprite": "abomination", "kind": "abomination", "name": "The Abomination", "hp": 175, "damage": (13, 23),
         "candy": (6, 10)},
    ],
    "boss": {
        "sprite": "gorge", "kind": "bully", "boss": True,
        "name": "Gorge, Taker of Worlds", "hp": 320, "damage": (13, 21), "candy": (25, 30),
        "lunge": 40,
        "taunt": [
            "Well, well. If it isn't Pumpkin-Head.",
            "Every Halloween you trick-or-treat. Every Halloween I TAKE it. That's how it works.",
            "Your candy? MINE. Your world? A SNACK. Hand over the bag, kid.",
        ],
        "defeat_quote": "Gorge shrinks back down... just a kid with an empty bag. All that candy's going home.",
    },
    "arrival": [],
    # Whisper Jack, as Charlie walks. One of the Void's creatures appears after each speech
    # (Catto, the Mad Ghost, the Mage, the Abomination), and Gorge after the last.
    "speeches": [
        ["...Oh. Oh, no. So this is the Void.",
         "Kid, I've haunted a lot of places. Nothing like this. Nothing.",
         "No up. No down. Just lights that aren't stars... and I think they're looking at us.",
         "This is where all the lost candy goes. Every wrapper. Every last piece. Forever.",
         "Don't stop walking. Whatever happens, keep moving. ...Is that a cat?"],
        ["That was NOT a kitty. Out here, things wear whatever face fools you longest.",
         "Can you feel that? The whole place is... breathing. Slow and deep, like it's asleep.",
         "Let's not wake it up.",
         "Wait. Hear that? Something out there is... sharpening."],
        ["A ghost with knives. And I thought I was scary.",
         "Look up, Charlie. Every one of those lights is somebody's stolen candy. Millions of them.",
         "It's beautiful. It's horrible. I can't stop looking at it.",
         "Bullies made this. Every time one takes something that isn't theirs, the hole gets bigger.",
         "...Somebody's casting. Get ready!"],
        ["I'm a skeleton, kid, and my bones are rattling. Real talk.",
         "The one at the end of this? He's the one who took your candy. Every single Halloween.",
         "He got so big on it, he started swallowing whole worlds.",
         "And something's crawling out of his leftovers right now. Oh, that's horrible..."],
        ["That was his last guard. He's right up ahead. I can feel him from here.",
         "Gorge. The Taker of Worlds. Eater of all candy.",
         "I've never been this scared in my whole afterlife. But he's only as big as you let him be.",
         "Chin up, Charlie. I'm right here."],
    ],
    "farewell": ["You did it, kid. Look at him... just a mean little kid with an empty bag.",
                 "The lights are going out. No... they're going HOME. All that candy's going home.",
                 "Come on, Charlie. Let's go home too. Before this place remembers we're here."],
})

# Shown after the last level's exit
ENDING = {
    "title": "To Be Continued...",
    "subtitle": "Thanks for playing Chin Check Charlie",
}


# The secret boss: Crumb, once he's eaten all four Golden Crumbs, at the last camp.
# He fights at camp ("arena"), as hard as a Chapter 4 boss and then some ("chapter").
SECRET_BOSS = {
    "sprite": "bread", "kind": "bread", "name": "Crumb, the Crust Eternal", "boss": True,
    "hp": 520, "damage": (12, 20), "candy": (40, 50), "lunge": 150, "arena": "camp", "chapter": 3,
    "defeat_quote": "Crumb shrinks back to snack size. \"Best. Fight. EVER. Hug?\"",
}
