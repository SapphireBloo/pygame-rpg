"""The safe camp Charlie reaches after every boss: a parallax forest, the
Blacksmith (upgrades), and the Crow (items, buys trophies).

    ParallaxBackground   the 6 layers in assets/images/safe, scrolling at different speeds
    Blacksmith           stands at his anvil hammering; sparks fly on each strike
    Crow                 wanders around near the Blacksmith, hops now and then, turns to face Charlie
"""
import math
import random
from functools import lru_cache

import pygame

from core import sfx
from core.animation import AnimatedSprite, load_strip_character, load_pixel_character, slice_strip
from core.settings import IMAGES_DIR, CHARACTER_INK
from core.ui import outlined_text

# Back to front: (file in assets/images/safe, how fast it scrolls compared to the ground)
# 0.png is the same scene pre-combined into one picture, so it isn't needed here.
PARALLAX_LAYERS = (("6.png", 0.06), ("5.png", 0.18), ("4.png", 0.32), ("3.png", 0.5), ("2.png", 1.0))
# The rocks, stumps, and broken tree closest to the camera: drawn in FRONT of Charlie and the
# camp folk, and scrolling a little faster than the ground so the depth reads.
FOREGROUND_LAYER = ("1.png", 1.15)
FOREGROUND_FADE = 120       # how see-through it gets while Charlie is behind something big (0-255)
FADE_OVERLAP = 0.22         # ...meaning more than this share of him is covered
PARALLAX_SCALE = 3          # the art is 384x216 pixel art: 3x fills the screen height
PARALLAX_Y = -48            # shift up so the dirt path lines up with Charlie's feet

CAMP_LENGTH = 1900          # world x of the exit portal
BLACKSMITH_X = 700
CROW_HOME_X = 1180
CRUMB_HOME_X = 548          # Crumb potters around in front of the Blacksmith's anvil (clear of the stumps)
INTERACT_RANGE = 120        # how close Charlie must be to press E


def _load_layer(name):
    image = pygame.image.load(IMAGES_DIR / "safe" / name).convert_alpha()
    w, h = image.get_size()
    return pygame.transform.scale(image, (w * PARALLAX_SCALE, h * PARALLAX_SCALE))


def _tiles(screen, image, camera_offset, speed):
    """x positions to blit a repeating layer at."""
    width = image.get_width()
    x = -((camera_offset * speed) % width)
    while x < screen.get_width():
        yield x
        x += width


class ParallaxBackground:
    def __init__(self):
        self.layers = [(_load_layer(name), speed) for name, speed in PARALLAX_LAYERS]
        self.front = _load_layer(FOREGROUND_LAYER[0])
        self.front_speed = FOREGROUND_LAYER[1]
        self.front_mask = pygame.mask.from_surface(self.front)
        self.front_alpha = 255.0

    def draw(self, screen, camera_offset, with_front=True):
        """The whole scene. In camp, pass with_front=False and call draw_front after the characters."""
        screen.fill((24, 20, 18))
        for image, speed in self.layers:
            for x in _tiles(screen, image, camera_offset, speed):
                screen.blit(image, (x, PARALLAX_Y))
        if with_front:
            self.draw_front(screen, camera_offset)

    def covered(self, screen, camera_offset, rect):
        """How much of `rect` (screen coords) the foreground hides, 0-1."""
        box = pygame.Mask(rect.size, fill=True)
        hidden = 0
        for x in _tiles(screen, self.front, camera_offset, self.front_speed):
            hidden += self.front_mask.overlap_area(box, (int(rect.x - x), int(rect.y - PARALLAX_Y)))
        return hidden / max(1, rect.width * rect.height)

    def draw_front(self, screen, camera_offset, hero_rect=None):
        """The foreground, over the characters. Goes see-through while Charlie is behind it."""
        target = 255
        if hero_rect is not None and self.covered(screen, camera_offset, hero_rect) > FADE_OVERLAP:
            target = FOREGROUND_FADE
        self.front_alpha += (target - self.front_alpha) * 0.18
        self.front.set_alpha(min(255, round(self.front_alpha)))   # (not None: that would drop its see-through pixels)
        for x in _tiles(screen, self.front, camera_offset, self.front_speed):
            screen.blit(self.front, (x, PARALLAX_Y))


def camp_backdrop(size):
    """The camp forest as one still picture (the arena for Crumb's secret fight)."""
    surface = pygame.Surface(size)
    ParallaxBackground().draw(surface, 260, with_front=False)
    return surface


@lru_cache(maxsize=None)
def blacksmith_animations():
    return load_strip_character("blacksmith/Sprites", 165, (("idle", "BLACKSMITH.png"),), (("idle", 120),),
                                CHARACTER_INK, faces="left")


CROW_BRIGHTEN = (52, 46, 58)   # his black cloak vanishes in the dark woods: lift it to a dusky grey


@lru_cache(maxsize=None)
def crow_animations():
    strips = (("idle", "crow_idle.png"), ("walk", "crow_walk.png"), ("jump", "crow_jump.png"))
    raw = {}
    for name, filename in strips:
        frames = [f.copy() for f in slice_strip(f"crow/{filename}")]
        for f in frames:
            f.fill(CROW_BRIGHTEN, special_flags=pygame.BLEND_RGB_ADD)
        raw[name] = frames
    return load_pixel_character(raw, 130, (("idle", 160), ("walk", 120), ("jump", 90)), CHARACTER_INK)


class Npc:
    name = ""
    prompt = "[E] Talk"
    greetings = ()
    color = (255, 255, 255)

    def __init__(self, x):
        self.x = x
        self.facing_right = False
        self.greeted = False

    def near(self, hero_x):
        return abs(hero_x - self.x) < INTERACT_RANGE

    def greeting(self, hero_x):
        """A one-time line when Charlie first walks up."""
        if not self.greeted and abs(hero_x - self.x) < INTERACT_RANGE + 80:
            self.greeted = True
            return random.choice(self.greetings)
        return None

    def portrait(self):
        """A frame of the NPC for the shop window header."""
        image, _ = self.sprite.animations["idle"].frame(0, True)
        h = 92
        scale = h / image.get_height()
        return pygame.transform.scale(image, (int(image.get_width() * scale), h))

    def draw_prompt(self, screen, camera_offset, feet_y):
        label = outlined_text(self.prompt, 16, (255, 240, 200), True, 2)
        bob = 3 * math.sin(pygame.time.get_ticks() / 200)
        top = feet_y - self.sprite.current.frames[0].get_height() - 34 + bob
        pill = label.get_rect(midtop=(self.x - camera_offset, top)).inflate(14, 8)
        back = pygame.Surface(pill.size, pygame.SRCALPHA)
        pygame.draw.rect(back, (12, 8, 14, 200), back.get_rect(), border_radius=10)
        pygame.draw.rect(back, (*self.color, 230), back.get_rect(), 2, border_radius=10)
        screen.blit(back, pill)
        screen.blit(label, label.get_rect(center=pill.center))


class Blacksmith(Npc):
    name = "Blacksmith"
    prompt = "[E] Upgrades"
    color = (255, 190, 120)
    greetings = ("Hrm. You look like you punch things.", "Mind the sparks, pumpkin.",
                 "Candy for steel. Fair trade.")
    STRIKE_FRAME = 3            # the frame where the hammer hits the anvil

    def __init__(self, x):
        super().__init__(x)
        self.sprite = AnimatedSprite(blacksmith_animations())
        self._last_index = 0

    def update(self, dt, hero_x):
        self.sprite.update(dt)
        if self.sprite.index == self.STRIKE_FRAME and self._last_index != self.STRIKE_FRAME:
            sfx.play("anvil", 0.5)          # the sparks are already drawn in his animation
        self._last_index = self.sprite.index

    def draw(self, screen, camera_offset, feet_y):
        self.sprite.draw(screen, self.x - camera_offset, feet_y, self.facing_right)


class Crow(Npc):
    name = "The Crow"
    prompt = "[E] Trade"
    color = (255, 140, 150)
    greetings = ("Caw! Shiny things for sweet things.", "Got trophies? I'm buying. Caw.",
                 "Potions. Bombs. Secrets. Two of those are for sale.")
    ROAM = 240                  # how far he wanders from home, each way
    SPEED = 55

    def __init__(self, home_x):
        super().__init__(home_x)
        self.home_x = home_x
        self.sprite = AnimatedSprite(crow_animations())
        self.state = "idle"
        self.timer = random.uniform(800, 2000)
        self.facing_right = False

    def update(self, dt, hero_x):
        self.sprite.update(dt)
        if self.near(hero_x):                  # stop and pay attention to the customer
            self.facing_right = hero_x > self.x
            if self.state != "idle":
                self.state = "idle"
                self.sprite.play("idle")
            return
        self.timer -= dt
        if self.state == "walk":
            step = (1 if self.facing_right else -1) * self.SPEED * dt / 1000
            self.x += step
            if abs(self.x - self.home_x) > self.ROAM:
                self.x = self.home_x + math.copysign(self.ROAM, self.x - self.home_x)
                self.timer = 0
        elif self.state == "hop" and self.sprite.finished:   # hops play once, then he moves on
            self.timer = 0
        if self.timer <= 0:
            self._next_state()

    def _next_state(self):
        """idle -> (mostly) walk somewhere, sometimes hop; walking or hopping -> a short pause."""
        if self.state != "idle":
            self.state, self.timer = "idle", random.uniform(900, 2200)
            self.sprite.play("idle")
            if random.random() < 0.3:
                self.facing_right = not self.facing_right
        elif random.random() < 0.2:
            self.state, self.timer = "hop", 99999
            self.sprite.play("jump", restart=True)
        else:
            self.state, self.timer = "walk", random.uniform(1500, 3500)
            # Head back toward home if he's wandered off to one side
            self.facing_right = self.x < self.home_x if abs(self.x - self.home_x) > 60 else random.random() < 0.5
            self.sprite.play("walk")

    def draw(self, screen, camera_offset, feet_y):
        self.sprite.draw(screen, self.x - camera_offset, feet_y, self.facing_right)


# ---- Crumb, the bread ----------------------------------------------------------
BREAD_SHEET = "bread/bread_spritesheet.png"     # 32x32 frames, one animation per row
CRUMB_HEIGHT = 58
CRUMB_FRAME_MS = (("idle", 170), ("walk", 110), ("jump", 120))
# He gets a little more golden (toasty) with every Golden Crumb he eats
CRUMB_TINTS = (None, (255, 240, 215), (250, 222, 175), (245, 205, 140), (255, 200, 100))
CRUMB_ANGRY_TINT = (255, 110, 90)     # red with rage


def bread_frames():
    """Raw 32x32 frames: idle (row 1), walk (row 2), jump and fall (rows 3 and 4)."""
    sheet = pygame.image.load(IMAGES_DIR / BREAD_SHEET).convert_alpha()
    frame = lambda col, row: sheet.subsurface((col * 32, row * 32, 32, 32))
    return {
        "idle": [frame(c, 0) for c in range(3)],
        "walk": [frame(c, 1) for c in range(4)],
        "jump": [frame(0, 2), frame(0, 2), frame(0, 3), frame(0, 3)],
    }


@lru_cache(maxsize=None)
def crumb_animations(tint=None):
    raw = bread_frames()
    if tint:
        raw = {name: [_tinted(f, tint) for f in frames] for name, frames in raw.items()}
    return load_pixel_character(raw, CRUMB_HEIGHT, CRUMB_FRAME_MS, CHARACTER_INK)


def _tinted(frame, tint):
    out = frame.copy()
    out.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
    return out


CRUMB_LINES = {
    0: ("Hi! I'm Crumb. I'm bread.", "Got any snacks? I like snacks.",
        "I heard golden crumbs fall from the sky out there. Look UP!"),
    1: ("Mmm... golden. I feel... toasty.", "More golden crumbs are out there. Somewhere sneaky. Up high? Down low?"),
    2: ("Two crumbs! I feel... crispier.", "Something's waking up inside me. Probably yeast.",
        "My cousin says one fell into a GRAVE. Spooky. Search everything!"),
    3: ("Just one more... crumb...", "I'm SO close to... something. Find the last one!"),
    4: ("Mmm. Thank you, friend. I feel... FULL.", "Go on. Shop. Don't mind me. I'll just... sit here.",
        "Everything's fine. Totally fine. Why do you ask?"),
    "angry": ("Oh, NOW you come back.", "You know what you did.", "Don't 'hi Crumb' me."),
    "calm": ("Crust Eternal: still undefeated. Just saying.", "Go on, pumpkin. Save the world. I'll keep the fire warm."),
    "beaten": ("Best. Fight. EVER.", "Partners! Where are we going? The VOID? Cool. Cool cool cool."),
}


FOLLOW_GAP = 75           # (as Charlie's partner) how far behind him Crumb trots
FOLLOW_SPEED = 330        # his trot (Charlie walks at 300)...
FOLLOW_HOP_SPEED = 560    # ...and how fast he bounds to catch up (Charlie runs at 480)
HOP_MS = 320


class Crumb(Npc):
    """The bread who lives at camp. Pet him, feed him snacks, and... maybe more."""
    name = "Crumb"
    color = (255, 215, 140)
    ROAM = 55
    SPEED = 40
    HOP_HEIGHT = 22

    def __init__(self, home_x, player, follow=False):
        super().__init__(home_x)
        self.home_x = home_x
        self.player = player
        self.follow = follow             # tagging along behind Charlie (he joined the quest)
        self.steam = []                  # [x offset, rise, life] angry puffs
        self.tint_level = -1
        self.sprite = AnimatedSprite(crumb_animations())
        self._refresh_tint()
        self.state = "idle"
        self.timer = random.uniform(600, 1600)
        self.lift = 0.0
        self.hop_time = 0
        self.hearts = []                 # [x offset, rise, life] little hearts after a pet
        self.time = 0
        self.hero_dir = 1                # (following) which way Charlie's heading: 1 right, -1 left
        self.last_hero_x = None

    @property
    def angry(self):
        return self.player.crumb_angry and not self.player.crumb_beaten

    @property
    def prompt(self):
        return "[E] Face Crumb" if self.angry and not self.player.crumb_fought else "[E] Crumb"

    def near(self, hero_x):
        """Once he's Charlie's partner there's nothing to press E for (and E is free for the portal)."""
        return not self.follow and super().near(hero_x)

    @property
    def greetings(self):
        p = self.player
        if p.crumb_beaten:
            key = "beaten"
        elif self.angry:
            key = "angry"
        elif p.crumb_fought:
            key = "calm"
        else:
            key = min(4, p.crumbs_fed)
        return CRUMB_LINES[key]

    def _refresh_tint(self):
        level = "angry" if self.angry else min(4, self.player.crumbs_fed)
        if level != self.tint_level:
            self.tint_level = level
            name, index = self.sprite.name, self.sprite.index
            tint = CRUMB_ANGRY_TINT if level == "angry" else CRUMB_TINTS[level]
            self.sprite.animations = crumb_animations(tint)
            self.sprite.play(name)
            self.sprite.index = min(index, len(self.sprite.current) - 1)

    def petted(self):
        """Wiggle, hop, and hearts."""
        self.state, self.timer = "hop", 99999
        self.hop_time = 0
        self.sprite.play("jump", restart=True)
        for i in range(5):
            self.hearts.append([random.uniform(-26, 26), random.uniform(0, 12), 900 + i * 120])

    def update(self, dt, hero_x):
        self.time += dt
        self._refresh_tint()
        self.sprite.update(dt)
        for heart in self.hearts:
            heart[1] += dt * 0.05
            heart[2] -= dt
        self.hearts = [h for h in self.hearts if h[2] > 0]
        for puff in self.steam:
            puff[1] += dt * 0.06
            puff[2] -= dt
        self.steam = [p for p in self.steam if p[2] > 0]
        if self.angry and random.random() < dt / 160:          # fuming
            self.steam.append([random.choice((-14, 14)) + random.uniform(-4, 4), 0, 700])
        if self.follow:
            self._follow(dt, hero_x)
            return
        if self.angry and self.state != "hop":                  # stomping mad: little angry hops in place
            self.facing_right = hero_x > self.x
            self.timer -= dt
            if self.timer <= 0:
                self.state, self.timer, self.hop_time = "hop", 99999, 0
                self.sprite.play("jump", restart=True)
            return
        if self.state == "hop":
            self.hop_time += dt
            self.lift = self.HOP_HEIGHT * math.sin(math.pi * min(1.0, self.hop_time / 420))
            if self.hop_time >= 420:
                self.lift = 0
                self.state, self.timer = "idle", random.uniform(700, 1500)
                self.sprite.play("idle")
            return
        if self.near(hero_x):                  # stop and look up at Charlie
            self.facing_right = hero_x > self.x
            if self.state != "idle":
                self.state = "idle"
                self.sprite.play("idle")
            return
        self.timer -= dt
        if self.state == "walk":
            self.x += (1 if self.facing_right else -1) * self.SPEED * dt / 1000
            if abs(self.x - self.home_x) > self.ROAM:
                self.x = self.home_x + math.copysign(self.ROAM, self.x - self.home_x)
                self.timer = 0
        if self.timer <= 0:
            if self.state != "idle":
                self.state, self.timer = "idle", random.uniform(900, 2000)
                self.sprite.play("idle")
            elif random.random() < 0.3:        # a happy little hop
                self.state, self.timer, self.hop_time = "hop", 99999, 0
                self.sprite.play("jump", restart=True)
            else:
                self.state, self.timer = "walk", random.uniform(1200, 2600)
                self.facing_right = self.x < self.home_x if abs(self.x - self.home_x) > 40 else random.random() < 0.5
                self.sprite.play("walk")

    def _follow(self, dt, hero_x):
        """Trot along behind Charlie (on the side he's coming from), hopping to keep up. If he ends up
        level with Charlie or in front of him, he hops back around behind."""
        if self.last_hero_x is not None and abs(hero_x - self.last_hero_x) > 0.3:
            self.hero_dir = 1 if hero_x > self.last_hero_x else -1
        self.last_hero_x = hero_x
        behind = hero_x - self.hero_dir * FOLLOW_GAP
        gap = behind - self.x
        in_the_way = (self.x - hero_x) * self.hero_dir > -FOLLOW_GAP / 2      # beside or in front of him
        if self.state == "hop":
            self.hop_time += dt
            k = min(1.0, self.hop_time / HOP_MS)
            self.lift = self.HOP_HEIGHT * 1.6 * math.sin(math.pi * k)
            self.x += max(-1, min(1, gap / 30)) * FOLLOW_HOP_SPEED * dt / 1000
            self.facing_right = gap > 0
            if k >= 1.0:
                self.lift, self.state = 0, "idle"
            return
        if (in_the_way and abs(gap) > 30) or abs(gap) > 220:   # hop back behind him / bound to catch up
            self.state, self.hop_time = "hop", 0
            self.sprite.play("jump", restart=True)
        elif abs(gap) > 12:
            speed = FOLLOW_SPEED if abs(gap) < 120 else FOLLOW_HOP_SPEED
            self.x += max(-1, min(1, gap / 40)) * speed * dt / 1000
            self.facing_right = gap > 0
            if self.sprite.name != "walk":
                self.sprite.play("walk")
        else:
            self.facing_right = hero_x > self.x                  # waiting: looking at Charlie
            if self.sprite.name != "idle":
                self.sprite.play("idle")

    def draw(self, screen, camera_offset, feet_y):
        x = self.x - camera_offset
        if self.angry:                                       # fuming red
            glow = pygame.Surface((140, 140), pygame.SRCALPHA)
            pulse = 0.5 + 0.5 * math.sin(self.time / 120)
            for r in range(60, 10, -10):
                pygame.draw.circle(glow, (255, 70, 50, int((25 + 35 * pulse) * (1 - r / 70))), (70, 70), r)
            screen.blit(glow, glow.get_rect(center=(x, feet_y - CRUMB_HEIGHT // 2 - self.lift)))
            x += random.uniform(-1.5, 1.5)                   # shaking with rage
        elif self.player.crumbs_fed >= 4 and not self.player.crumb_beaten and not self.player.crumb_fought:
            glow = pygame.Surface((140, 140), pygame.SRCALPHA)
            pulse = 0.5 + 0.5 * math.sin(self.time / 300)
            for r in range(60, 10, -10):
                pygame.draw.circle(glow, (255, 210, 110, int((20 + 25 * pulse) * (1 - r / 70))), (70, 70), r)
            screen.blit(glow, glow.get_rect(center=(x, feet_y - CRUMB_HEIGHT // 2 - self.lift)))
        self.sprite.draw(screen, x, feet_y - self.lift, self.facing_right)
        for dx, rise, life in self.steam:
            k = life / 700
            pygame.draw.circle(screen, (230, 225, 225), (int(x + dx * (1 + rise / 40)), int(feet_y - CRUMB_HEIGHT - rise)),
                               max(2, int(9 * (1 - k) + 3)), 0 if k > 0.3 else 2)
        for dx, rise, life in self.hearts:
            alpha = min(255, int(255 * life / 500))
            hx, hy = int(x + dx), int(feet_y - CRUMB_HEIGHT - 10 - rise)
            heart = pygame.Surface((14, 13), pygame.SRCALPHA)
            for cx in (4, 10):
                pygame.draw.circle(heart, (235, 70, 100, alpha), (cx, 4), 4)
            pygame.draw.polygon(heart, (235, 70, 100, alpha), [(0, 5), (14, 5), (7, 13)])
            screen.blit(heart, (hx - 7, hy))
