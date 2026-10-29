"""Monsters that wander a level until Charlie gets too close, then attack.

Every regular monster (ghosts, death knights, satyrs, zombies) uses this. They:
  * wander back and forth around their spot, pausing now and then
  * notice Charlie when he's near, turn, and come after him
  * attack when close enough (or swoop, for ghosts), and the battle starts
  * mutter to themselves now and then (floating text, and a sound if one exists)

How each kind moves and what it says lives in PROFILES below.
"""
import math
import random

from core.animation import AnimatedSprite
from core.enemy_art import enemy_animations, art_faces_left

# speeds are pixels per second; ranges are pixels from Charlie
PROFILES = {
    # Shambles, lurching on every step like it's dragging a leg
    "zombie": {"walk": 40, "chase": 62, "notice": 330, "grab": 115, "patrol": 170, "gait": "lurch",
               "chatter": ["Braaains...", "Uuurgh...", "Mmmrrh...", "Caaandy..."],
               "color": (150, 210, 150), "sound": "zombie_groan"},
    # Drifts and bobs, shimmering in and out; swoops at Charlie instead of attacking
    "ghost": {"walk": 55, "chase": 95, "notice": 350, "grab": 125, "patrol": 210, "gait": "float",
              "chatter": ["Ooooooo...", "Whooo's there?", "Boo.", "Caaandy..."],
              "color": (200, 230, 255), "sound": "ghost_wail"},
    # Trots its horse on patrol, gallops when it spots Charlie
    "knight": {"walk": 75, "chase": 170, "notice": 430, "grab": 150, "patrol": 250, "gait": "trot",
               "chatter": ["*clop clop clop*", "Halt, gourd!", "None shall pass.", "For the Warlock!"],
               "color": (180, 195, 255), "sound": "knight_charge"},
    # Skitters with little hops
    "satyr": {"walk": 55, "chase": 115, "notice": 340, "grab": 120, "patrol": 160, "gait": "hop",
              "chatter": ["Hee hee hee!", "*crackle*", "Burn, pumpkin, burn!", "These woods are ours!"],
              "color": (255, 170, 130), "sound": None},
}
SWOOP_MS = 520           # ghosts have no attack animation: they swoop for this long instead


def profile_for(spec):
    return PROFILES.get(spec.get("kind") or ("ghost" if spec["sprite"] == "ghost" else "zombie"),
                        PROFILES["zombie"])


class RoamingEnemy:
    def __init__(self, home_x, spec, tint=None):
        self.spec = spec                  # enemy stats + "sprite", handed to the battle
        self.p = profile_for(spec)
        self.home_x = home_x
        self.x = home_x + random.uniform(-60, 60)   # world x of its feet
        self.facing_right = random.random() < 0.5
        self.flip_art = art_faces_left(spec["sprite"])
        self.sprite = AnimatedSprite(enemy_animations(spec["sprite"], tint))
        self.sprite.index = random.randrange(len(self.sprite.current))  # don't all move in sync
        self.walk_anim = "walk" if self.sprite.has("walk") else "idle"
        self.time = random.uniform(0, 5000)

        self.state = "idle"
        self.state_timer = random.uniform(400, 2200)
        self.lunge_timer = 0
        self.chatter_timer = random.uniform(3000, 9000)
        self.defeated = False
        self.ready_for_battle = False
        self.first_strike = False        # Charlie slid into it before it could attack

    @property
    def grab_range(self):
        return self.p["grab"]

    @property
    def grabbing(self):
        """True while it's attacking Charlie (he can't walk away mid-attack)."""
        return self.state == "lunge" and not self.defeated

    # ---- behavior ------------------------------------------------------
    def update(self, dt, hero_center_x, calm=False):
        """Returns a chatter line occasionally (for floating text), else None.
        calm=True (e.g. while Whisper Jack is talking) keeps it from attacking."""
        if self.defeated or self.ready_for_battle:
            return None
        self.time += dt
        self.sprite.update(dt)
        self._animate_gait()
        dist = hero_center_x - self.x

        if self.state == "lunge":
            self.lunge_timer -= dt
            if not self.sprite.has("attack"):          # ghost swoop: rush in and flare up
                self.x += (1 if self.facing_right else -1) * 260 * dt / 1000
                self.sprite.scale_x = self.sprite.scale_y = 1 + 0.25 * math.sin(math.pi * (1 - self.lunge_timer / SWOOP_MS))
            if self.lunge_timer <= 0:
                self.sprite.reset_pose()
                self.ready_for_battle = True
            return None

        if not calm and abs(dist) < self.p["grab"]:
            self._lunge(dist)
        elif not calm and abs(dist) < self.p["notice"]:
            self.facing_right = dist > 0
            self.state = "chase"
            self.sprite.play(self.walk_anim, speed=1.4 if self.p["gait"] == "trot" else 1.0)
            self._step(dt, self.p["chase"])
        else:
            self._wander(dt)
        return self._maybe_chatter(dt)

    def _lunge(self, dist):
        self.facing_right = dist > 0
        self.state = "lunge"
        if self.sprite.has("attack"):
            self.sprite.play("attack", restart=True)
            attack = self.sprite.current
            self.lunge_timer = len(attack) * attack.frame_ms
        else:
            self.lunge_timer = SWOOP_MS

    def _wander(self, dt):
        if self.state == "chase":           # lost interest
            self._set_idle()
        self.state_timer -= dt
        patrol = self.p["patrol"]
        if self.state == "walk":
            self._step(dt, self.p["walk"])
            past_edge = (self.x > self.home_x + patrol and self.facing_right) or \
                        (self.x < self.home_x - patrol and not self.facing_right)
            if past_edge:
                self._set_idle()
                self.facing_right = not self.facing_right   # turn around after a pause
            elif self.state_timer <= 0:
                self._set_idle()
        elif self.state_timer <= 0:          # idle finished: start moving
            self.state = "walk"
            self.sprite.play(self.walk_anim)
            self.state_timer = random.uniform(2000, 5000)
            if random.random() < 0.35:
                self.facing_right = not self.facing_right

    def _set_idle(self):
        self.state = "idle"
        self.sprite.play("idle")
        self.state_timer = random.uniform(1200, 3500)
        if random.random() < 0.25:           # sometimes a turn on the spot
            self.facing_right = not self.facing_right

    def _step(self, dt, speed):
        gait = self.p["gait"]
        if gait == "lurch":
            # Speed swells and drops twice per walk cycle, like dragging a leg
            walk = self.sprite.current
            phase = (self.sprite.index + self.sprite.timer / walk.frame_ms) / len(walk)
            speed *= 0.35 + 0.65 * abs(math.sin(phase * math.tau))
        direction = 1 if self.facing_right else -1
        self.x += direction * speed * dt / 1000

    def _animate_gait(self):
        """Little bits of motion on top of the frames, per kind."""
        gait, t = self.p["gait"], self.time / 1000
        if gait == "float":                  # bob up and down and shimmer
            self.sprite.lift = 10 + 8 * math.sin(t * 2.4)
            self.sprite.alpha = int(200 + 45 * math.sin(t * 3.1))
        elif gait == "hop" and self.state in ("walk", "chase"):
            self.sprite.lift = 10 * abs(math.sin(t * (9 if self.state == "chase" else 6)))
        elif gait == "hop":
            self.sprite.lift = 0

    def _maybe_chatter(self, dt):
        self.chatter_timer -= dt
        if self.chatter_timer <= 0:
            self.chatter_timer = random.uniform(5000, 11000)
            return random.choice(self.p["chatter"])
        return None

    # ---- drawing -------------------------------------------------------
    @property
    def shadow_size(self):
        return {"knight": 1.5, "ghost": 0.6}.get(self.spec.get("kind"), 1.0)

    def draw(self, screen, camera_offset, feet_y):
        if not self.defeated:
            facing = self.facing_right != self.flip_art
            self.sprite.draw(screen, self.x - camera_offset, feet_y, facing)
