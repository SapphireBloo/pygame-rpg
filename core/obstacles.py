"""Things placed along a level: platforms to climb, ceilings to slide under, traps, spots to search, decor.

Every Prop sits at a world x (its CENTER) and works in "elevations": pixels above the ground
line (FEET_Y). The level layouts in core/level_layouts.py place them with the Kit helpers.

What a prop can be (any mix):
  solid     blocks Charlie from the sides, and he can stand on its top (crates, earth blocks)
  ledge     he can stand on its top, but jumps up through it and walks under it (thin planks)
  ceiling   its underside is low: standing Charlie bumps into it, sliding Charlie fits under
  trap      touching it hurts (spikes, toxic water, and the animated traps: boxing gloves, crushers,
            runes, lightning, sandworms, arrows; fire at camp is just decor).
            Spiked ceilings hurt too.
  search    press E next to it to rummage through it, once
"""
import math
import random

import pygame

from core import sfx, tileset
from core.items import ITEMS_BY_KEY, SNACKS
from core.lighting import Flicker
from core.settings import FEET_Y
from core.ui import outlined_text

CEILING_BOTTOM = 122       # underside of slide-under ceilings: Charlie stands ~138 tall, slides ~113
SEARCH_REACH = 70          # how close (from the prop's edge) Charlie must be to search it

# What searching turns up: (weight, what). Candy amounts grow a little each chapter.
SEARCH_LOOT = [
    (40, "candy"),
    (14, "potion"),
    (10, "snack"),
    (6, "remedy"),
    (30, None),
]
NOTHING_LINES = {
    "cabin": ("Just dust bunnies.", "Cobwebs. Lots of cobwebs.", "An old sock. No thanks."),
    "hollow": ("Swamp goo. Ew.", "Empty. Someone beat you to it.", "Just a sad frog."),
    "woods": ("Leaves. And a spider. Nope.", "Nothing but twigs.", "Empty."),
    "graveyard": ("Bones. Not yours. Leave 'em.", "Cold dirt.", "Nothing but worms."),
}


class Prop:
    def __init__(self, x, image=None, *, frames=None, frame_ms=100, elev=0, sink=0, front=False,
                 width=None, solid=False, ledge=False, top=None, ceiling=None, spiked=False,
                 trap=None, trap_height=None, search=False, loot=None, glint=False, label=None,
                 depth="mid", light=None):
        self.x = x
        self.image = image
        self.frames = frames
        self.frame_ms = frame_ms
        self.time = random.uniform(0, 5000)
        first = image if image is not None else frames[0]
        self.size = first.get_size()
        self.elev = elev                 # where its bottom sits (above the ground line)
        self.sink = sink                 # how far the image reaches below its bottom
        self.front = front               # drawn in front of the characters
        self.w = width if width is not None else self.size[0]
        self.solid = solid
        self.ledge = ledge
        # walkable top (elevation)
        self.top = top if top is not None else elev + self.size[1] - sink
        self.ceiling = ceiling           # elevation of the underside, or None
        self.spiked = spiked
        self.trap = trap                 # None, "fire", "spikes", "toxic"
        self.trap_height = trap_height if trap_height is not None else self.size[1] - sink
        self.search = search
        self.loot = loot                 # forced find ("golden_crumb"), else random
        self.searched = False
        self._dim = None
        self._camera = 0
        self.shake = 0                   # wobble after a search
        self.glint = glint               # an occasional sparkle (a hint something's inside)
        # depth: "mid" is the characters' plane. "far" props sit back toward the trees (smaller,
        # hazier, scrolling slower); "near" ones are right in front of the camera (big, dark,
        # scrolling faster, drawn over the characters and fading when Charlie walks behind them).
        self.depth = depth
        self.parallax, self.shift = DEPTHS[depth]["parallax"], DEPTHS[depth]["shift"]
        self.front = front or depth == "near"
        self.alpha = 255.0
        self.light = light               # (color, radius, strength) firelight, or None
        self.flicker = Flicker() if light else None
        self.label = label

    # ---- geometry --------------------------------------------------------
    @property
    def left(self):
        return self.x - self.w / 2

    @property
    def right(self):
        return self.x + self.w / 2

    @property
    def hit_x(self):
        """Where a trap hit came from (Charlie gets knocked away from it)."""
        return self.x

    @property
    def underside(self):
        """Where Charlie bumps his head jumping up into it (None: nothing to bump)."""
        if self.ceiling is not None:
            return self.ceiling
        if self.solid and self.elev > 0:      # a floating island
            return self.elev
        return None

    @property
    def blocks(self):
        """Stops sideways movement (and keeps monsters out)."""
        return self.solid or self.ceiling is not None

    def overlaps_x(self, a, b):
        return a < self.right and b > self.left

    def body_hits(self, a, b, low, high):
        """Does a body spanning x a..b, elevation low..high, run into this prop's solid part?"""
        if not self.overlaps_x(a, b):
            return False
        if self.solid:
            return low < self.top - 0.5 and high > self.elev + 0.5
        if self.ceiling is not None:
            return high > self.ceiling + 0.5
        return False

    def trap_hits(self, a, b, low, high):
        if self.trap is None or not self.overlaps_x(a + 10, b - 10):
            return False
        return low < self.elev + self.trap_height - 8 and high > self.elev

    def near(self, feet_x, feet_elev):
        if not self.search or self.searched:
            return False
        dx = max(self.left - feet_x, feet_x - self.right, 0)
        return dx < SEARCH_REACH and abs(feet_elev - self.elev) < 60

    # ---- searching -------------------------------------------------------
    def roll_loot(self, player, chapter, theme):
        """Search it. Gives the find to the player and returns (text, color, icon)."""
        self.searched = True
        self.shake = 450
        sfx.play("ui_select", 0.6)
        if self.loot == "golden_crumb" and chapter not in player.crumbs_found:
            player.add_item("golden_crumb")
            player.crumbs_found.append(chapter)
            sfx.play("heal", 0.6)
            return "Golden Crumb!", (255, 220, 120), "golden_crumb"
        roll = random.uniform(0, sum(w for w, _ in SEARCH_LOOT))
        for weight, find in SEARCH_LOOT:
            roll -= weight
            if roll <= 0:
                break
        if find == "candy":
            amount = random.randint(1, 2) + (chapter >= 2)
            player.add_candy(amount)
            return f"+{amount} candy", (255, 200, 90), "candy"
        if find == "snack":
            find = random.choice(SNACKS)
        if find:
            player.add_item(find)
            return f"Found a {ITEMS_BY_KEY[find]['name']}!", (180, 255, 170), find
        return random.choice(NOTHING_LINES.get(theme, NOTHING_LINES["cabin"])), (200, 195, 210), None

    # ---- drawing ---------------------------------------------------------
    def update(self, dt):
        self.time += dt
        self.shake = max(0, self.shake - dt)

    def surface(self):
        if self.frames:
            return self.frames[int(self.time // self.frame_ms) % len(self.frames)]
        return self.image

    def screen_rect(self, camera_offset):
        rect = pygame.Rect((0, 0), self.size)
        rect.midbottom = (self.x - camera_offset * self.parallax, FEET_Y - self.elev + self.sink + self.shift)
        return rect

    def light_center(self, camera_offset):
        rect = self.screen_rect(camera_offset)
        return rect.centerx, rect.top + rect.height * 0.45

    def fade_behind(self, hero_rect):
        """Near props go see-through while they cover Charlie."""
        rect = self.screen_rect(self._camera)
        clip = rect.clip(hero_rect)
        covered = clip.width * clip.height / max(1, hero_rect.width * hero_rect.height)
        target = 110 if covered > 0.18 else 255
        self.alpha += (target - self.alpha) * 0.18

    def draw(self, screen, camera_offset):
        self._camera = camera_offset
        rect = self.screen_rect(camera_offset)
        if rect.right < -20 or rect.left > screen.get_width() + 20:
            return
        if self.shake:
            rect.x += 4 * math.sin(self.shake / 25) * self.shake / 450
        image = self.surface()
        if self.alpha < 254:
            image = image.copy()
            image.set_alpha(int(self.alpha))
        screen.blit(image, rect)
        if self.search and self.searched:
            if self._dim is None:                        # searched: a shade darker
                self._dim = image.copy()
                self._dim.fill((0, 0, 0, 90), special_flags=pygame.BLEND_RGBA_MULT)
                self._dim.fill((0, 0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(self._dim, rect)
        elif self.glint and (self.time // 100) % 45 < 3:
            gx, gy = rect.right - 14, rect.top + 12
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                pygame.draw.line(screen, (255, 245, 200), (gx, gy), (gx + dx * 8, gy + dy * 8), 2)

    def draw_prompt(self, screen, camera_offset):
        label = outlined_text("[E] Search", 16, (255, 240, 200), True, 2)
        bob = 3 * math.sin(pygame.time.get_ticks() / 200)
        top = FEET_Y - self.elev - self.size[1] + self.sink - 40 + bob
        pill = label.get_rect(midtop=(self.x - camera_offset, top)).inflate(14, 8)
        back = pygame.Surface(pill.size, pygame.SRCALPHA)
        pygame.draw.rect(back, (12, 8, 14, 200), back.get_rect(), border_radius=10)
        pygame.draw.rect(back, (255, 210, 120, 230), back.get_rect(), 2, border_radius=10)
        screen.blit(back, pill)
        screen.blit(label, label.get_rect(center=pill.center))


# How each depth looks: scale (sheet pixels -> screen pixels), scroll speed relative to the
# ground, how far up (-) or down (+) its feet sit, and how it's shaded.
DEPTHS = {
    "far": {"scale": 2, "parallax": 0.9, "shift": -44, "darken": (175, 160, 150), "haze": (70, 60, 52), "amount": 0.3},
    "mid": {"scale": None, "parallax": 1.0, "shift": 0},
    "near": {"scale": 4, "parallax": 1.15, "shift": 34, "darken": (78, 66, 60), "haze": None, "amount": 0.0},
}


# Animated traps from the Pixel Trap Pack (assets/images/trap). Each one loops: it plays its
# frames, then rests for pause_ms. It only hurts during its `danger` frames, and only where its
# pixels are on that frame (hitboxes are worked out from the art).
#   name: (png, frame w, h, ms per frame, danger frames, pause ms, flip, skip rows below / thin rows)
TRAP_ART = {
    # a spring-loaded boxing glove that pops out of the floor and punches low: jump it
    "punch": ("Punch Trap/PNGs/Punch Trap - Level 1.png", 96, 32, 90, range(3, 12), 1300, False, 4, 0),
    # a spiked block hanging under a shelf (or a slab) that slams down and winches back up, over and over
    "crusher": ("Ceiling Trap/PNGs/Ceiling Trap - Level 1.png", 64, 64, 100, range(1, 9), 1500, False, 0, 12),
    # magic runes glow... then spikes shoot up
    "runes": ("Magic trap/PNGs/Magic trap - Level 1.png", 32, 32, 90, range(12, 17), 900, False, 0, 0),
    # two orbs with lightning crackling between them: wait for a gap
    "lightning": ("Lightning Trap/PNGs/Lightning Trap - Level 2.png", 96, 96, 100, range(3, 11), 1400, False, 0, 0),
    # a sandworm bursts out of the ground and arcs over
    "worm": ("Sandworm Trap/PNGs/Sandworm trap - Level 1.png", 32, 32, 100, range(5, 10), 1500, False, 3, 0),
    # an arrow totem pops up and fires an arrow down the path (the arrows do the hurting)
    "arrows": ("Arrow Trap/PNGs/Arrow Trap - Level 1.png", 96, 32, 100, (), 1600, False, 0, 0),
}
# These sit still until Charlie steps on them, then go off once and reset after their pause. The
# crusher, the lightning pylon, and the arrow totem keep going on their own.
STEP_TRAPS = {"punch", "runes", "worm"}
PLATE_INSET = 6          # px trimmed off each side of a trap's pressure plate
# A step trap strikes the moment it's stepped on (no wind-up to outrun, even at a sprint), and the
# strike covers its plate plus this much either side. Only jumping over it gets you past.
STRIKE_REACH = 30
STEP_REARM_MS = 350      # after it's gone off and settled, it's live again this quickly
ARROW_FRAME = 9          # the totem's firing frame
ARROW_SPEED = 430        # pixels per second
ARROW_RANGE = 650        # how far an arrow flies
ARROW_HEIGHT = 50        # its height above the ground


class AnimTrap(Prop):
    """An animated trap that hurts during part of its animation. Most wait for Charlie to step on
    them (STEP_TRAPS); the rest loop on their own."""

    def __init__(self, name, x, theme, phase=0.0, elev=0):
        file, fw, fh, ms, danger, pause, flip, skip_bottom, thin = TRAP_ART[name]
        frames, boxes = tileset.trap_frames(file, fw, fh, theme, flip, skip_bottom, thin)
        super().__init__(x, frames=frames, frame_ms=ms, elev=elev, trap=name,
                         width=max((b[2] - b[0] for b in boxes if b), default=fw * tileset.SCALE * 0.6))
        self.name = name
        self.boxes = boxes                       # per frame: (left, bottom, right, top) in screen px from the
        self.danger = set(danger)                # frame's bottom-left, or None where nothing's there
        self.pause = pause
        self.cycle = len(frames) * ms + pause
        self.time = phase * self.cycle
        self.trap_height = max((b[3] for b in boxes if b), default=0)
        self.on_step = name in STEP_TRAPS
        self.fire_time = None                    # (step traps) ms since it went off, or None while it waits
        self.cooldown = 0                        # (step traps) ms before it can go off again
        strike = [boxes[i] for i in self.danger if boxes[i]]     # stepping where it strikes sets it off
        self.plate = ((min(bx[0] for bx in strike) + PLATE_INSET, max(bx[2] for bx in strike) - PLATE_INSET)
                      if strike else (0, 0))
        self.strike_top = max((bx[3] for bx in strike), default=0)
        self.strike_at = min(self.danger, default=0) * ms

    @property
    def frame_index(self):
        if self.on_step:
            return 0 if self.fire_time is None else min(len(self.frames) - 1, int(self.fire_time // self.frame_ms))
        t = self.time % self.cycle
        return 0 if t >= len(self.frames) * self.frame_ms else int(t // self.frame_ms)

    @property
    def armed(self):
        return self.on_step and self.fire_time is None and self.cooldown <= 0

    def update(self, dt):
        super().update(dt)
        if not self.on_step:
            return
        if self.fire_time is not None:
            self.fire_time += dt
            if self.fire_time >= len(self.frames) * self.frame_ms:
                self.fire_time = None
                self.cooldown = STEP_REARM_MS
        else:
            self.cooldown = max(0, self.cooldown - dt)

    def step_on(self, a, b, feet_elev):
        """Charlie's feet are at [a, b] (world x), feet_elev above the ground. Returns True if
        that set the trap off: his feet have to be down on its level, over its plate."""
        if not self.armed or feet_elev > self.elev + 4:
            return False
        left = self.x - self.size[0] / 2
        if a < left + self.plate[1] and b > left + self.plate[0]:
            self.fire_time = self.strike_at          # straight to the strike
            return True
        return False

    def surface(self):
        return self.frames[self.frame_index]

    def _box(self):
        i = self.frame_index
        if i not in self.danger or not self.boxes[i]:
            return None
        l, b, r, t = self.boxes[i]
        left = self.x - self.size[0] / 2
        return left + l, self.elev + b, left + r, self.elev + t

    @property
    def hit_x(self):
        box = self._box()
        return (box[0] + box[2]) / 2 if box else self.x

    def trap_hits(self, a, b, low, high):
        if self.on_step:                             # while it's striking: its whole plate, and a bit more
            if self.frame_index not in self.danger or self.fire_time is None:
                return False
            left = self.x - self.size[0] / 2
            x0, x1 = left + self.plate[0] - STRIKE_REACH, left + self.plate[1] + STRIKE_REACH
            return a < x1 and b > x0 and low < self.elev + self.strike_top - 4
        box = self._box()
        if not box:
            return False
        x0, e0, x1, e1 = box
        return a + 6 < x1 and b - 6 > x0 and low < e1 - 4 and high > e0 + 4


class ArrowTrap(AnimTrap):
    """A totem that pops up and fires arrows back down the path (toward where Charlie comes from)."""

    def __init__(self, x, theme, phase=0.0):
        super().__init__("arrows", x, theme, phase)
        self.arrow = tileset.trap_arrow(theme)
        self.arrows = []                         # world x of each arrow's tip
        self._fired = False

    def update(self, dt):
        super().update(dt)
        firing = self.frame_index == ARROW_FRAME
        if firing and not self._fired:
            self.arrows.append(self.x - self.size[0] * 0.18)
        self._fired = firing
        for i in range(len(self.arrows)):
            self.arrows[i] -= ARROW_SPEED * dt / 1000
        self.arrows = [a for a in self.arrows if self.x - a < ARROW_RANGE]

    @property
    def hit_x(self):
        return self.arrows[0] if self.arrows else self.x

    def trap_hits(self, a, b, low, high):
        w = self.arrow.get_width()
        return any(a + 6 < tip + w * 0.6 and b - 6 > tip and low < ARROW_HEIGHT + 6 and high > ARROW_HEIGHT - 6
                   for tip in self.arrows)

    def draw(self, screen, camera_offset):
        super().draw(screen, camera_offset)
        for tip in self.arrows:
            fade = min(1.0, (ARROW_RANGE - (self.x - tip)) / 120)
            img = self.arrow
            if fade < 1:
                img = img.copy()
                img.set_alpha(int(255 * fade))
            screen.blit(img, img.get_rect(midleft=(tip - camera_offset, FEET_Y - ARROW_HEIGHT)))


class Kit:
    """Builds props for one chapter's look. Used by core/level_layouts.py, e.g.
        k.solid("crate", 900)            a crate Charlie can stand on
        k.block(1300, 2, 90)             a 2-tile earth block, 90 px tall
        k.ledge(1500, 3, 170)            a plank shelf 170 px up
        k.ceiling(2000, 3)               a spiked slab to slide under
        k.beam(2000, 3)                  a hanging beam to slide under
        k.trap("punch", 2300)  k.spikes(2500, 2)  k.pool(2700, 3)
        k.search("barrel", 2900)         a spot to search
        k.deco("pumpkin", 3100)          scenery
    """

    def __init__(self, theme):
        self.theme = theme

    def deco(self, name, x, elev=0, front=False, flip=False, sink=0, depth="mid", light=None):
        """Scenery. depth "far" (back by the trees) or "near" (in front of the camera) for parallax."""
        d = DEPTHS[depth]
        image = tileset.prop(name, self.theme, flip, d["scale"])
        if depth != "mid":
            image = tileset.shade(image, d["darken"], d["haze"], d["amount"])
        return Prop(x, image, elev=elev, front=front, sink=sink, depth=depth, light=light)

    def animated(self, name, x, elev=0, color=None, front=False, depth="mid", light=None):
        d = DEPTHS[depth]
        frames = tileset.frames(name, self.theme, color, d["scale"])
        if depth != "mid":
            frames = tuple(tileset.shade(f, d["darken"], d["haze"], d["amount"] * 0.5) for f in frames)
        return Prop(x, frames=frames, frame_ms=tileset.frame_ms(name), elev=elev, front=front, depth=depth,
                    light=light)

    def solid(self, name, x, elev=0, search=False, loot=None, flip=False, inset=0, glint=False):
        """A prop you can stand on and can't walk through. inset trims the walkable top."""
        image = tileset.prop(name, self.theme, flip)
        return Prop(x, image, elev=elev, solid=True, top=elev + image.get_height() - inset,
                    width=image.get_width() - 12, search=search, loot=loot, glint=glint)

    def search(self, name, x, elev=0, loot=None, flip=False, glint=False):
        """A spot to search that you walk past (not solid)."""
        return Prop(x, tileset.prop(name, self.theme, flip), elev=elev, search=True, loot=loot, glint=glint)

    def block(self, x, tiles, height):
        image, lip = tileset.earth_block(self.theme, tiles, height)
        return Prop(x, image, solid=True, top=height, sink=tileset.GROUND_DEPTH, width=image.get_width() - 6)

    def island(self, x, tiles, top):
        """A thin floating earth platform. Like the plank shelves, you can jump up through it
        from below and land on top (and walk under it if it's above head height)."""
        image = tileset.island_slab(self.theme, tiles)
        lip = 3 * tileset.SCALE                        # grass blades above the walkable top
        return Prop(x, image, elev=top + lip - image.get_height(), ledge=True, top=top,
                    width=image.get_width() - 24)

    def row(self, name, x, count, step=None):
        """Several of the same prop side by side, as one wide platform (a loft of crate stacks)."""
        one = tileset.prop(name, self.theme)
        step = step or one.get_width() - 3
        image = pygame.Surface((step * (count - 1) + one.get_width(), one.get_height()), pygame.SRCALPHA)
        for i in range(count):
            image.blit(one, (i * step, 0))
        return Prop(x, image, solid=True, width=image.get_width() - 12)

    def ledge(self, x, tiles, top):
        image = tileset.planks(self.theme, tiles)
        return Prop(x, image, elev=top - image.get_height(), ledge=True, top=top, width=image.get_width() - 8)

    def ceiling(self, x, tiles, bottom=CEILING_BOTTOM, spiked=True):
        image, spikes = tileset.ceiling_slab(self.theme, tiles, spiked)
        return Prop(x, image, elev=bottom, ceiling=bottom, spiked=spiked, width=image.get_width() - 24)

    def beam(self, x, tiles, bottom=CEILING_BOTTOM):
        rope = FEET_Y - bottom                          # ropes run up off the top of the screen
        image = tileset.hanging_beam(self.theme, tiles, rope)
        return Prop(x, image, elev=bottom, ceiling=bottom, width=image.get_width() - 10)

    def trap(self, name, x, phase=0.0):
        """An animated trap from TRAP_ART: punch, runes, lightning, worm, arrows (the crusher has its
        own helper, below). phase (0-1) staggers the ones that loop so neighbours don't fire together."""
        if name == "arrows":
            return ArrowTrap(x, self.theme, phase)
        return AnimTrap(name, x, self.theme, phase)

    def crusher(self, x, phase=0.0):
        """A spiked block that hangs under a shelf (indoors) or a floating slab (outside) and keeps
        slamming down and winching back up: pass while it's up. Returns [shelf, crusher] (use
        *k.crusher(x) in a layout). You can stand on the shelf."""
        trap = AnimTrap("crusher", x, self.theme, phase)
        nudge = 2 * tileset.SCALE                       # (tuck it up so the chains meet the underside)
        if self.theme == "cabin":
            board = tileset.planks(self.theme, 2)
            return [self.ledge(x, 2, trap.size[1] + board.get_height() - nudge), trap]
        image = tileset.island_slab(self.theme, 1)
        lip = 3 * tileset.SCALE
        return [self.island(x, 1, trap.size[1] + image.get_height() - lip - nudge), trap]

    def fire(self, x, name="campfire", color=None):
        color = color or tileset.THEMES[self.theme].get("fire")
        frames = tileset.frames(name, self.theme, color)
        return Prop(x, frames=frames, frame_ms=tileset.frame_ms(name), trap="fire",
                    width=frames[0].get_width() - 30, trap_height=frames[0].get_height() * 0.45)

    def spikes(self, x, tiles):
        image, sink = tileset.spike_strip(self.theme, tiles)
        return Prop(x, image, sink=sink, trap="spikes", width=image.get_width() - 12,
                    trap_height=(image.get_height() - sink) * 0.7)   # (the tips are forgiving)

    def pool(self, x, tiles):
        frames = tileset.pool_frames(self.theme, tiles)
        sink = frames[0].get_height() - 6               # the surface sits just above the ground line
        return Prop(x, frames=frames, frame_ms=110, sink=sink, trap="toxic", width=frames[0].get_width() - 20,
                    trap_height=20)
