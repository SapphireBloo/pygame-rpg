"""The scrolling credits (Credits on the title screen, and after the ending).

Edit freely: each entry is (style, text). Styles:
  "title"    big orange title          "heading"  a section name
  "line"     a normal line             "small"    a quieter note
  "gap"      blank space (text ignored)
"""

CREDITS = [
    ("title", "CHIN CHECK CHARLIE"),
    ("small", "A Halloween brawl"),
    ("gap", ""),

    ("heading", "CREATED BY"),
    ("line", "SapphireBloo"),
    ("small", "Design, code, and an unreasonable amount of candy"),
    ("gap", ""),

    ("heading", "STARRING"),
    ("line", "Chin Check Charlie"),
    ("line", "Whisper Jack, skeleton advisor"),
    ("line", "The Blacksmith and the Crow"),
    ("gap", ""),

    ("heading", "THE BOSSES"),
    ("line", "Mortis, Bringer of Death"),
    ("small", "Bringer of Death by Clembod"),
    ("line", "Grimwald the Warlock"),
    ("small", "Evil Wizard 2 asset pack (CC0)"),
    ("line", "Scorchmaw the Fire Worm"),
    ("small", "Fire Worm asset pack (CC0)"),
    ("line", "Malgorath the Demon"),
    ("small", "Demon Slime (free version)"),
    ("gap", ""),

    ("heading", "THE MONSTERS AND FRIENDS"),
    ("line", "Charlie and the zombies"),
    ("small", "GameArt2D / pzUH (CC0)"),
    ("line", "Ghosts, Death Knights, and Satyrs"),
    ("line", "The Blacksmith, the Crow, and the camp forest"),
    ("small", "Free asset packs; artist credits coming soon"),
    ("gap", ""),

    ("heading", "SOUND AND MUSIC"),
    ("line", "Sound effects"),
    ("small", "Deadly Kombat Free Library by Daniel Barros"),
    ("line", "Level, camp, and boss music"),
    ("small", "Composer credits coming soon"),
    ("gap", ""),

    ("heading", "MADE WITH"),
    ("line", "Python and pygame-ce"),
    ("gap", ""),

    ("heading", "SPECIAL THANKS"),
    ("line", "Everyone who played the demo"),
    ("line", "and told us what to fix"),
    ("gap", ""),
    ("gap", ""),
    ("title", "Thanks for playing!"),
]
