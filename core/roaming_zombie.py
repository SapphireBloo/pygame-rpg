"""A zombie that wanders the Graveyard until Charlie gets too close.

Behavior, in proper zombie fashion:
  * Shambles slowly back and forth around its spot, lurching with each step
  * Stops now and then to sway in place (idle), sometimes turning around
  * Notices Charlie when he's near, turns, and shuffles toward him
  * Close enough to grab: plays its attack lunge, then the battle starts
"""
import math
import random

from core.animation import AnimatedSprite, load_gameart2d_character
from core.settings import ZOMBIE_HEIGHT, CHARACTER_INK

PATROL_RANGE = 170       # how far from home it wanders, each way
WALK_SPEED = 40          # pixels per second while wandering
CHASE_SPEED = 62         # pixels per second once it has spotted Charlie
NOTICE_RANGE = 330       # distance at which it notices Charlie
GRAB_RANGE = 115         # distance at which it lunges and the fight starts
GROANS = ["Braaains...", "Uuurgh...", "Mmmrrh...", "Caaandy..."]


class RoamingZombie:
    def __init__(self, home_x, spec):
        self.spec = spec                  # enemy stats + "sprite" folder, handed to the battle
        self.home_x = home_x
        self.x = home_x + random.uniform(-60, 60)   # world x of its feet
        self.facing_right = random.random() < 0.5
        self.sprite = AnimatedSprite(load_gameart2d_character(spec["sprite"], ZOMBIE_HEIGHT, ink=CHARACTER_INK))
        self.sprite.index = random.randrange(len(self.sprite.current))  # don't all sway in sync

        self.state = "idle"
        self.state_timer = random.uniform(400, 2200)
        self.lunge_timer = 0
        self.groan_timer = random.uniform(3000, 9000)
        self.defeated = False
        self.ready_for_battle = False
        self.first_strike = False        # Charlie slid into it before it could grab him

    @property
    def grabbing(self):
        """True while it's lunging at Charlie (he can't walk away mid-grab)."""
        return self.state == "lunge" and not self.defeated

    # ---- behavior ------------------------------------------------------
    def update(self, dt, hero_center_x):
        """Returns a groan string occasionally (for a floating speech line), else None."""
        if self.defeated or self.ready_for_battle:
            return None
        self.sprite.update(dt)
        dist = hero_center_x - self.x

        if self.state == "lunge":
            self.lunge_timer -= dt
            if self.lunge_timer <= 0:
                self.ready_for_battle = True
            return None

        if abs(dist) < GRAB_RANGE:
            self._lunge(dist)
        elif abs(dist) < NOTICE_RANGE:
            self.facing_right = dist > 0
            self.state = "chase"
            self.sprite.play("walk")
            self._step(dt, CHASE_SPEED)
        else:
            self._wander(dt)
        return self._maybe_groan(dt)

    def _lunge(self, dist):
        self.facing_right = dist > 0
        self.state = "lunge"
        self.sprite.play("attack", restart=True)
        attack = self.sprite.current
        self.lunge_timer = len(attack) * attack.frame_ms

    def _wander(self, dt):
        if self.state == "chase":           # lost interest
            self._set_idle()
        self.state_timer -= dt
        if self.state == "walk":
            self._step(dt, WALK_SPEED)
            past_edge = (self.x > self.home_x + PATROL_RANGE and self.facing_right) or \
                        (self.x < self.home_x - PATROL_RANGE and not self.facing_right)
            if past_edge:
                self._set_idle()
                self.facing_right = not self.facing_right   # turn around after a pause
            elif self.state_timer <= 0:
                self._set_idle()
        elif self.state_timer <= 0:          # idle finished: start shambling
            self.state = "walk"
            self.sprite.play("walk")
            self.state_timer = random.uniform(2000, 5000)
            if random.random() < 0.35:
                self.facing_right = not self.facing_right

    def _set_idle(self):
        self.state = "idle"
        self.sprite.play("idle")
        self.state_timer = random.uniform(1200, 3500)
        if random.random() < 0.25:           # sometimes a confused turn on the spot
            self.facing_right = not self.facing_right

    def _step(self, dt, speed):
        # Lurch: speed swells and drops twice per walk cycle, like dragging a leg
        walk = self.sprite.current
        phase = (self.sprite.index + self.sprite.timer / walk.frame_ms) / len(walk)
        lurch = 0.35 + 0.65 * abs(math.sin(phase * math.tau))
        direction = 1 if self.facing_right else -1
        self.x += direction * speed * lurch * dt / 1000

    def _maybe_groan(self, dt):
        self.groan_timer -= dt
        if self.groan_timer <= 0:
            self.groan_timer = random.uniform(5000, 11000)
            return random.choice(GROANS)
        return None

    # ---- drawing -------------------------------------------------------
    def draw(self, screen, camera_offset, feet_y):
        if not self.defeated:
            self.sprite.draw(screen, self.x - camera_offset, feet_y, self.facing_right)
