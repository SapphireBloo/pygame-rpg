import random

import pygame

from core.ui import get_font, wrap_text, draw_speech_bubble

FAREWELL_LINES = [
    "Got candy? No? Then I'm ghostin'...",
    "The sweetest treats vanish first... so do I.",
    "Remember, Jack's always watching... especially for candy.",
    "No candy, no company. I'm haunting off.",
    "Sugar's the price for my company... and you're broke.",
    "Catch me if you can... but first, find some candy.",
    "Candy or chaos. Choose wisely, or I'll be back.",
    "Trick or treat? Looks like you're all treat... for now.",
]


class SkeletonAnimation:
    """Whisper Jack: rises out of the ground, talks, then sinks away.

    Space advances his lines. After the scripted lines he adds a random
    farewell; `message_done` turns True at that point, and the next Space
    (or the owning scene) sends him back underground.
    """

    RISE_SPEED = 72    # pixels per second
    SINK_SPEED = 90

    def __init__(self, x, y, frames, messages, frame_delay=250, max_bubble_width=250):
        self.x = x
        self.target_y = y
        self.y = float(y + 100)  # start below ground
        self.frames = frames
        self.frame_delay = frame_delay
        self.frame_index = 0
        self.frame_timer = 0

        self.active = True
        self.fading_out = False
        self.message_done = False

        self.name = "Whisper Jack"
        self.font = get_font(20)
        self.max_bubble_width = max_bubble_width

        self.messages = list(messages) + [random.choice(FAREWELL_LINES)]
        self.message_index = 0
        self.message_done = len(self.messages) == 1  # no scripted lines, straight to farewell
        self._wrapped_cache = {}

    # ---- input / update ------------------------------------------------
    def handle_event(self, event):
        if not self.active or self.fading_out:
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self.message_done:
                self.fading_out = True
            else:
                self.message_index += 1
                if self.message_index == len(self.messages) - 1:
                    self.message_done = True  # now showing the farewell line

    def update(self, dt):
        if not self.active:
            return
        step = dt / 1000
        if self.fading_out:
            self.y += self.SINK_SPEED * step
            if self.y > pygame.display.get_surface().get_height() + 100:
                self.active = False
        elif self.y > self.target_y:
            self.y = max(self.target_y, self.y - self.RISE_SPEED * step)

        if self.frames:
            self.frame_timer += dt
            if self.frame_timer >= self.frame_delay:
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                self.frame_timer = 0

    # ---- drawing -------------------------------------------------------
    def draw(self, screen, camera_offset=0):
        if not self.active:
            return
        screen_x = self.x - camera_offset
        if self.frames:
            screen.blit(self.frames[self.frame_index], (screen_x, self.y))
        if self.message_index >= len(self.messages):
            return
        text = self.messages[self.message_index]
        if text not in self._wrapped_cache:
            self._wrapped_cache[text] = wrap_text(self.font, text, self.max_bubble_width)
        # Bubble sits up and to the left of Jack, never off the left edge
        draw_speech_bubble(screen, self.name, self._wrapped_cache[text],
                           lambda w, h: (max(10, screen_x - w - 20), self.y - h - 30),
                           hint=not self.fading_out)
