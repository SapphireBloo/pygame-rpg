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
