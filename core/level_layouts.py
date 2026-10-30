"""Where everything sits in each chapter: monsters, the boss, the Golden Crumb, and the props
(platforms, traps, spots to search, decor).

All x positions are world pixels along the level (Charlie starts with his feet at about 125).
Heights are pixels above the ground. Charlie's jump reaches about 110 px and his double jump
about 195 (floating islands and planks you can jump up through; keep their tops 185+ if Charlie
should be able to walk under them). He stands 138 tall. (k.beam and k.ceiling, low things to slide
under, still exist but the chapters don't use them any more.)

Rough shape of every chapter:  start -> obstacles -> monster -> obstacles -> monster -> ... -> boss -> exit.
Monsters on the ground stay in the open stretch around their spot (clear of the obstacles).
A monster whose spot is over a platform (a crate loft, an earth ridge, a ledge) stands up there
and patrols its top instead.

The props are built by a Kit (core/obstacles.py) that knows each chapter's look. Order doesn't
matter, except that props listed later draw on top of earlier ones.

  "golden_crumb": (x, height) for a floating crumb (height = its center above the ground),
  or put loot="golden_crumb" on a search spot to hide it inside.

Fires are camp-only scenery now. The levels' traps are spikes, toxic pools, and the animated
traps: k.trap for boxing gloves, runes, sandworms (these go off when Charlie steps on them: only a
jump clears them), lightning, and arrows (these keep going on their own), and *k.crusher for a
spiked block hanging under a shelf (or a floating slab outdoors) that keeps slamming down. See
TRAP_ART in core/obstacles.py.
"""
from core.obstacles import Kit

# A boss needs this much empty ground in front of him for his walk-in and taunt.
BOSS_CLEARING = 700


def cabin(k):
    return [
        k.deco("bottles", 250), k.deco("chair", 370),
        k.search("barrel", 540),
        # a spring-loaded boxing glove pops out of the floorboards: jump it
        k.trap("punch", 820),
        # climb: crate, crate stack, then shelves up to the Golden Crumb (hop up from the top shelf)
        k.solid("crate", 1080),
        k.solid("crate_stack", 1160),
        k.ledge(1330, 3, 175),
        k.search("apple_basket", 1400, elev=175),
        k.ledge(1550, 2, 265),
        k.deco("bottles_small", 1500, elev=265),
        # ghost #1 (on the floor)
        k.deco("side_table", 1960), k.deco("apples", 1960, elev=33),
        # a barrel to hop, then a crusher hanging under a shelf: run past while it's up, or hop up onto the shelf
        k.solid("barrels", 2420),
        *k.crusher(2880, phase=0.5),
        k.solid("crate", 3170, search=True),
        # ghost #2 haunts a loft of crates; a high shelf above it
        k.row("crate_stack", 3400, 5),
        k.ledge(3520, 2, 280),
        k.search("basket", 3520, elev=280),
        k.deco("bottles", 3250, elev=96),
        # another glove, a barrel wall, and a shelf to land on
        k.trap("punch", 3880),
        k.solid("barrels", 4170),
        k.solid("crate_stack", 4255),
        k.ledge(4400, 2, 190),
        # ghost #3 (on the floor)
        k.deco("chair", 4950, flip=True), k.deco("jack_o_lantern", 5100),
        k.deco("apple_table", 5300), k.deco("chopping_block", 5450),
    ]


def hollow(k):
    return [
        k.deco("reeds", 240), k.animated("torch", 380), k.deco("reeds_tall", 470),
        # two mossy pillars with a sludge pool between them, and an island to reach from the second
        k.block(720, 1, 75),
        k.pool(890, 2),
        k.block(1060, 1, 75),
        k.island(1260, 2, 200),
        k.search("potion_table", 1260, elev=200),
        k.trap("runes", 1430),                     # the runes flare... then spikes
        # a wide pool with a plank stepping stone in the middle
        k.pool(1680, 3),
        k.ledge(1680, 2, 95),
        k.deco("reeds", 1880, front=True),
        # knight #1 (on the ground)
        k.deco("ore", 2250),
        # another pool
        k.pool(3000, 2),
        k.island(3020, 2, 185),
        k.search("alchemy_desk", 3020, elev=185),
        # knight #2 patrols a mossy ridge
        k.block(3500, 5, 80),
        # the Warlock's lightning pylon: wait for a gap
        k.trap("lightning", 4020, phase=0.6),
        # the climb to the Golden Crumb: pillars, then a high plank over a pool
        k.block(4330, 1, 80),
        k.block(4430, 1, 160),
        k.search("barrel", 4430, elev=160),
        k.pool(4650, 3),
        k.ledge(4600, 2, 235),
        k.deco("reeds", 4830, front=True),
        # knight #3 (on the ground)
        k.deco("ore_pink", 5650), k.deco("grapes", 5800, elev=250),
    ]


def woods(k):
    return [
        k.deco("bush_autumn", 270), k.deco("scarecrow", 470),
        k.spikes(760, 1),
        k.deco("tuft_autumn", 860, front=True),
        k.island(1000, 2, 185),
        k.search("leaf_pile", 1000, elev=185),
        k.trap("worm", 1200),                      # something lives under these leaves
        # a boulder to climb over
        k.solid("boulders_autumn", 1440, inset=22),
        # satyr #1 (on the ground)
        k.deco("pumpkin_small", 1950), k.deco("tall_grass", 2150, front=True),
        # rocks, then spikes
        k.deco("rocks_autumn", 2660),
        k.spikes(2830, 2),
        k.search("bush_autumn", 3050),
        # satyr #2 hops along an earth ridge; an island above with something to search
        k.block(3250, 1, 60),
        k.block(3550, 4, 110),
        k.island(3550, 2, 290),
        k.search("pumpkin_pile", 3550, elev=290),
        k.spikes(3820, 1),
        # pillars over spikes: the Golden Crumb floats high over the gap (double jump for it)
        k.block(4000, 1, 70),
        k.block(4100, 1, 140),
        k.spikes(4290, 1),
        k.block(4400, 1, 140),
        k.trap("arrows", 4560, phase=0.3),         # fires back down the path, over the spikes
        k.island(4700, 2, 200),
        k.search("leaf_pile", 4700, elev=200),
        # satyr #3 (on the ground)
        k.deco("rock_pile_autumn", 5180), k.deco("bush_small_autumn", 5330),
    ]


def graveyard(k):
    return [
        k.deco("grave_small", 230), k.deco("jack_o_lantern", 330),
        k.search("grave", 520),
        k.deco("grave_broken", 640),
        k.spikes(800, 1),
        k.island(1000, 2, 185),
        k.block(1240, 2, 80),
        k.search("grave_mossy", 1220, elev=80),
        # zombie #1 (on the ground)
        k.deco("statue", 1770),
        # the Golden Crumb is in a grave up on a high island (double jump up from the mound beside it)
        k.block(2150, 1, 80),
        k.island(2330, 2, 230),
        k.search("grave_cross", 2330, loot="golden_crumb", glint=True, elev=230),
        k.spikes(2650, 1),
        k.deco("tuft_snow", 2760, front=True),
        # zombie #2 shambles along a frozen ridge, with an island above it
        k.block(3100, 5, 90),
        k.island(3100, 2, 280),
        k.search("snow_pile", 3100, elev=280),
        *k.crusher(3440, phase=0.2),
        k.block(3620, 1, 90),
        k.block(3720, 1, 170),
        k.spikes(3910, 1),
        k.search("snow_pile", 4060),
        # zombie #3 (on the ground)
        k.deco("grave_cross", 4380),
        k.spikes(4750, 1),
        k.trap("lightning", 4990, phase=0.4),
        k.search("pumpkin_pile", 5150),
        # zombie #4 on a burial mound
        k.block(5550, 5, 70),
        k.deco("grave_small", 5440, elev=70), k.deco("grave", 5660, elev=70),
        k.deco("angel", 5950), k.deco("grave_mossy", 6150), k.deco("jack_o_lantern_small", 6250),
    ]


FIRE_LIGHT = ((255, 140, 60), 360, 0.95)       # (color, radius, strength): see core/lighting.py
FORGE_LIGHT = ((255, 115, 45), 260, 0.8)
TORCH_LIGHT = ((255, 155, 75), 170, 0.7)
FAR_FIRE_LIGHT = ((255, 140, 60), 170, 0.55)


def camp(k):
    """The camp has three depths: "far" props back by the treeline (smaller, hazier, slower),
    the characters' plane, and "near" props right in front of the camera (big and dark)."""
    return [
        # far: another little camp back in the trees
        k.deco("lean_to", 470, depth="far"),
        k.animated("campfire", 640, depth="far", light=FAR_FIRE_LIGHT),
        k.deco("log_pile", 760, depth="far"),
        k.deco("small_tent", 1230, depth="far"),
        k.deco("barrels", 1420, depth="far"),
        k.deco("lean_to_patched", 1720, depth="far", flip=True),
        k.deco("crate_stack", 1900, depth="far"),
        # the characters' plane
        k.deco("log_pile", 70),
        k.deco("large_tent", 250),
        k.animated("furnace", 820, light=FORGE_LIGHT),            # the Blacksmith's forge
        k.deco("stool", 1125),
        k.animated("campfire_pot", 1200, light=FIRE_LIGHT),     # (clear of the big rocks in front)
        k.deco("stool", 1275, flip=True),
        k.deco("apple_basket", 1320),
        k.deco("barrels", 1420),
        k.deco("crate_stack", 1495),
        k.deco("small_tent", 1620),
        k.deco("chopping_block", 1715),
        k.animated("torch", 1775, light=TORCH_LIGHT), k.animated("torch", 2030, light=TORCH_LIGHT),
        # near: dark shapes right in front of the camera. They slide left faster than everything
        # else, so each sits left of (or well past) the folks it might otherwise cover.
        k.deco("fern", 250, depth="near"),
        k.deco("bush_small", 1060, depth="near"),
        k.deco("tall_grass", 1560, depth="near"),
        k.deco("bush", 2300, depth="near"),
    ]


# Chapter index -> layout. Monster x positions are their home spots, in order
# (a spot over a platform puts that monster up on it).
LAYOUTS = [
    {"theme": "cabin", "props": cabin, "monsters": [2000, 3400, 5000], "boss": 6150,
     "golden_crumb": (1590, 470)},          # over the top shelf: hop up from it
    {"theme": "hollow", "props": hollow, "monsters": [2200, 3500, 5300], "boss": 6400,
     "golden_crumb": (4740, 380)},          # over the far pool: leap off the high plank
    {"theme": "woods", "props": woods, "monsters": [1990, 3550, 5050], "boss": 6200,
     "golden_crumb": (4290, 420)},          # high over the spikes between the pillars
    {"theme": "graveyard", "props": graveyard, "monsters": [1800, 3100, 4380, 5550], "boss": 6900,
     "golden_crumb": None},                 # inside the cross grave up on the high island
]
CAMP_LAYOUT = {"theme": "camp", "props": camp}
EXIT_PAST_BOSS = 600


def build_props(layout):
    return layout["props"](Kit(layout["theme"]))
