"""A boss waiting at the end of a level. When Charlie gets close the boss turns,
taunts him in a speech bubble (Space advances), shows off its big move, and the
fight starts. Movement is locked during the taunt so you can't walk past."""
import pygame

from core import sfx
from core.animation import AnimatedSprite
from core.effects import aura
from core.enemy_art import enemy_animations, battle_layout
from core.ui import draw_speech_bubble, wrap_text, get_font

NOTICE_RANGE = 430
BUBBLE_WIDTH = 300
BUBBLE_MIN_Y = 86      # keep the bubble below the HUD and Candy Shop button, even for the tallest bosses


class BossEncounter:
    def __init__(self, x, spec):
        self.x = x                        # world x of the boss's feet
        self.spec = spec                  # handed to the battle
        self.sprite = AnimatedSprite(enemy_animations(spec["sprite"]))
        layout = battle_layout(spec["sprite"])
        self.aura_size = layout["aura"] or (240, 280)
        self.glow = layout["glow"]
        self.intro_anim = layout["intro"] if self.sprite.has(layout["intro"]) else "attack"
        self.sounds = layout["sounds"]
        self.shadow_size = layout["shadow"]
        self.height = self.sprite.current.frames[0].get_height()   # for placing the speech bubble
        self.facing_right = False         # art faces right; mirror to face Charlie coming from the left
        self.lines = list(spec.get("taunt", ["..."]))
        self.line_index = 0
        self.state = "waiting"            # waiting -> taunting -> casting -> (battle)
        self.cast_timer = 0
        self.defeated = False
        self.ready_for_battle = False
        self.first_strike = False
        self._wrapped = {}

    @property
    def grabbing(self):
        """Locks Charlie in place while the boss is talking/casting."""
        return self.state in ("taunting", "casting") and not self.defeated

    def handle_event(self, event):
        if self.state != "taunting":
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.line_index += 1
            if self.line_index >= len(self.lines):
                self.state = "casting"
                self.sprite.play(self.intro_anim, restart=True)
                self.cast_timer = self.sprite.current.duration
                sfx.play(self.sounds.get("attack", "whoosh"))

    def update(self, dt, hero_center_x):
        if self.defeated or self.ready_for_battle:
            return
        self.sprite.update(dt)
        if self.state == "waiting" and abs(hero_center_x - self.x) < NOTICE_RANGE:
            self.state = "taunting"
            self.facing_right = hero_center_x > self.x
            sfx.play(self.sounds.get("laugh", "enrage"))
        elif self.state == "casting":
            self.cast_timer -= dt
            if self.cast_timer <= 0:
                self.sprite.play("idle")
                self.ready_for_battle = True

    def draw(self, screen, camera_offset, feet_y):
        if self.defeated:
            return
        sx = self.x - camera_offset
        glow = aura(self.glow, self.aura_size)
        screen.blit(glow, glow.get_rect(midbottom=(sx, feet_y + 30)))
        self.sprite.draw(screen, sx, feet_y, self.facing_right)

    def draw_bubble(self, screen, camera_offset, feet_y):
        """Drawn after the grit pass so the text stays crisp."""
        if self.state != "taunting" or self.defeated:
            return
        text = self.lines[self.line_index]
        if text not in self._wrapped:
            self._wrapped[text] = wrap_text(get_font(20), text, BUBBLE_WIDTH)
        sx = self.x - camera_offset
        draw_speech_bubble(screen, self.spec["name"], self._wrapped[text],
                           lambda w, h: (min(screen.get_width() - w - 10, max(10, sx - w // 2)),
                                        max(BUBBLE_MIN_Y, feet_y - self.height - 15 - h)),
                           name_color=tuple(int(c * 0.6) for c in self.glow))
