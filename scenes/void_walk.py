"""The Void (the final chapter): Charlie walks slowly through nothing at all while Whisper
Jack talks. Jack doesn't stop him, but he only keeps talking while Charlie keeps walking (stand
still and Jack waits for you). At the end of each of Jack's speeches one of the Void's
creatures appears ahead (Catto, the Mad Ghost, the Mage, the Abomination, in that order) and
comes for him. After the last speech Gorge is waiting. Beat him, Jack says goodbye, and the
credits roll.

The level itself (speeches, monsters, Gorge) is the "The Void" entry in core/levels.py.
ExplorationScene hands off to this for the background, the narration, and the spawns.
"""
import math
import random
from functools import lru_cache

import pygame

from core import sfx
from core.boss_encounter import BossEncounter
from core.jack_panel import draw_jack_panel
from core.roaming_enemy import RoamingEnemy
from core.settings import IMAGES_DIR, SCREEN_WIDTH, SCREEN_HEIGHT, FEET_Y

WALK_SCALE = 0.6          # Charlie walks at 60% speed in the Void (and can't run)
LINE_MS = 3400            # how long each of Jack's lines stays up (Space skips ahead)
FIRST_SPEECH_MS = 900     # a moment after arriving before Jack starts
NEXT_SPEECH_MS = 1400     # after a fight, before Jack picks up again
# (all three only count down while Charlie is walking forward)
NUDGE_MS = 1200           # stand still this long mid-speech and the panel says to keep walking
SPAWN_AHEAD = 520         # creatures appear this far in front of Charlie
BOSS_AHEAD = 760
SPAWN_MS = 700            # the ripple when something steps out of the Void
STAR_LAYERS = (("final/Starfields/Starfield_03-1024x1024.png", 0.45),
               ("final/Starfields/Starfield_08-1024x1024.png", 0.8))
NEBULA_SPEED = 0.15


@lru_cache(maxsize=None)
def _layer(path):
    """A square space image, scaled to the window's width and cropped to its height."""
    image = pygame.image.load(str(IMAGES_DIR / "backgrounds" / path)).convert()
    image = pygame.transform.smoothscale(image, (SCREEN_WIDTH, SCREEN_WIDTH))
    top = (SCREEN_WIDTH - SCREEN_HEIGHT) // 2
    return image.subsurface((0, top, SCREEN_WIDTH, SCREEN_HEIGHT)).copy()


@lru_cache(maxsize=None)
def _floor():
    """A faint violet haze down low, so the characters don't float in nothing. No edge, no line:
    just an endless plane fading into the dark."""
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - FEET_Y + 90), pygame.SRCALPHA)
    for y in range(surf.get_height()):
        k = y / surf.get_height()
        surf.fill((50, 16, 80, int(120 * k ** 1.6)), (0, y, SCREEN_WIDTH, 1))
    return surf


class VoidWalk:
    def __init__(self, scene, level):
        self.scene = scene
        self.level = level
        self.speeches = level.get("speeches", [])
        self.specs = list(level.get("monsters", []))
        self.boss_spec = level.get("boss")
        self.farewell = level.get("farewell", [])
        self.step = 0              # which speech (and which creature after it) is next
        self.lines = []            # Jack's current speech, lines left to say
        self.line = None
        self.line_timer = 0
        self.wait = FIRST_SPEECH_MS
        self.after = None          # what to do when the current speech ends: "spawn" or "finish"
        self.creature = None       # the creature out hunting Charlie right now
        self.ripples = []          # [world x, ms left] where something stepped out of the Void
        self.motes = [[random.uniform(0, SCREEN_WIDTH), random.uniform(60, FEET_Y), random.uniform(6, 18),
                       random.uniform(0, math.tau)] for _ in range(26)]
        self.time = 0
        self.done = False
        self.last_x = scene.hero_feet_x
        self.still = 0             # ms Charlie has been standing still (or backing up)
        self.line_age = 0          # ms the current line has been up (for the panel's fade-in)

    # ---- the walk ------------------------------------------------------------
    @property
    def talking(self):
        return self.line is not None

    def skip_line(self):
        """Space: on to Jack's next line."""
        if self.line is not None:
            self.line_timer = 0

    def update(self, dt):
        self.time += dt
        for ripple in self.ripples:
            ripple[1] -= dt
        self.ripples = [r for r in self.ripples if r[1] > 0]
        for mote in self.motes:
            mote[1] -= mote[2] * dt / 1000
            if mote[1] < 50:
                mote[0], mote[1] = random.uniform(0, SCREEN_WIDTH), FEET_Y + 20
        x = self.scene.hero_feet_x
        walking = x > self.last_x + 0.05            # Jack's story only moves along while Charlie does
        self.last_x = x
        self.still = 0 if walking else self.still + dt
        self.line_age += dt
        dt = dt if walking else 0
        if self.line is not None:
            self.line_timer -= dt
            if self.line_timer <= 0:
                self._next_line()
            return
        if self.creature is not None:              # wait for that fight to be over
            if not self.creature.defeated:
                return
            self.creature = None
            self.wait = NEXT_SPEECH_MS
        boss = self.scene.boss
        if boss is not None:
            if boss.defeated and not self.done and self.after != "finish":
                self.after = "finish"
                self._say(self.farewell)
            return
        if self.wait > 0:
            self.wait -= dt
            if self.wait <= 0 and self.step < len(self.speeches):
                self.after = "spawn"
                self._say(self.speeches[self.step])

    def _say(self, lines):
        self.lines = list(lines)
        self._next_line()

    def _next_line(self):
        if self.lines:
            self.line = self.lines.pop(0)
            self.line_age = 0
            self.line_timer = max(LINE_MS, 45 * len(self.line))
            return
        self.line = None
        if self.after == "spawn":
            self._spawn()
        elif self.after == "finish":
            self.done = True
            self.scene.exit_reached = True        # on to the ending
        self.after = None

    def _spawn(self):
        """The next creature steps out of the Void ahead of Charlie (or Gorge, after the last speech)."""
        x = self.scene.hero_feet_x + (SPAWN_AHEAD if self.step < len(self.specs) else BOSS_AHEAD)
        self.ripples.append([x, SPAWN_MS])
        sfx.play("phase", 0.8)
        if self.step < len(self.specs):
            creature = RoamingEnemy(x, self.specs[self.step])
            creature.facing_right = False
            creature.state = "chase"
            self.scene.monsters.append(creature)
            self.creature = creature
        elif self.boss_spec:
            self.scene.boss = BossEncounter(x, self.boss_spec)
        self.step += 1

    # ---- drawing -------------------------------------------------------------
    def draw_background(self, screen, camera_offset):
        nebula = _layer(self.level["background"])
        x = -((camera_offset * NEBULA_SPEED) % SCREEN_WIDTH)
        screen.blit(nebula, (x, 0))
        screen.blit(nebula, (x + SCREEN_WIDTH, 0))
        for path, speed in STAR_LAYERS:                 # nearer stars slide past faster
            stars = _layer(path)
            x = -((camera_offset * speed) % SCREEN_WIDTH)
            screen.blit(stars, (x, 0), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(stars, (x + SCREEN_WIDTH, 0), special_flags=pygame.BLEND_RGB_ADD)
        for mx, my, _, phase in self.motes:             # drifting specks of light
            a = 0.5 + 0.5 * math.sin(self.time / 500 + phase)
            pygame.draw.circle(screen, (int(140 + 80 * a), int(90 + 50 * a), 255), (int(mx), int(my)), 1 + int(a * 1.5))
        screen.blit(_floor(), (0, FEET_Y - 90))

    def draw_world(self, screen, camera_offset):
        """Ripples where things step out of the Void (drawn with the characters)."""
        for x, left in self.ripples:
            k = 1 - left / SPAWN_MS
            sx = x - camera_offset
            for i in range(3):
                r = 20 + 160 * k + i * 22
                ring = pygame.Rect(0, 0, int(r * 2), int(r * 0.5))
                ring.center = (int(sx), FEET_Y - 6)
                pygame.draw.ellipse(screen, (200, 110, 255), ring, max(1, int(4 * (1 - k))))
            glow = pygame.Surface((240, 300), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (40, 0, 60, int(200 * (1 - k))), glow.get_rect())
            screen.blit(glow, glow.get_rect(midbottom=(sx, FEET_Y + 20)))

    def draw_overlay(self, screen):
        """Jack's narration: his panel near the top (he's shaking a little out here)."""
        if self.line is None:
            return
        alpha = min(1.0, self.line_age / 250, self.line_timer / 250 + 0.4)
        nudge = self.still > NUDGE_MS
        draw_jack_panel(screen, self.line, alpha, self.time, "Keep walking  >" if nudge else "[Space] next",
                        hint_bright=nudge, shiver=True)
