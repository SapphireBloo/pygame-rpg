import random

import pygame

from core.ui import get_font, WHITE, BLACK

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
        self.name_font = get_font(18, bold=True)
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
    def _wrap(self, text):
        if text not in self._wrapped_cache:
            lines, current = [], ""
            for word in text.split(" "):
                test = f"{current} {word}".strip()
                if self.font.size(test)[0] <= self.max_bubble_width or not current:
                    current = test
                else:
                    lines.append(current)
                    current = word
            if current:
                lines.append(current)
            self._wrapped_cache[text] = lines
        return self._wrapped_cache[text]

    def draw(self, screen, camera_offset=0):
        if not self.active:
            return
        screen_x = self.x - camera_offset
        if self.frames:
            screen.blit(self.frames[self.frame_index], (screen_x, self.y))

        if self.message_index >= len(self.messages):
            return
        lines = self._wrap(self.messages[self.message_index])
        name_surface = self.name_font.render(self.name, True, (20, 20, 20))

        padding = 10
        line_height = self.font.get_height()
        width = max([self.font.size(line)[0] for line in lines] + [name_surface.get_width()]) + padding * 2
        height = line_height * len(lines) + name_surface.get_height() + padding * 3
        bubble = pygame.Rect(max(10, screen_x - width - 20), self.y - height - 30, width, height)

        pygame.draw.rect(screen, WHITE, bubble, border_radius=8)
        pygame.draw.rect(screen, BLACK, bubble, 2, border_radius=8)
        screen.blit(name_surface, (bubble.x + padding, bubble.y + padding))

        text_y = bubble.y + padding + name_surface.get_height() + 5
        for line in lines:
            screen.blit(self.font.render(line, True, BLACK), (bubble.x + padding, text_y))
            text_y += line_height

        if not self.fading_out:
            hint = self.font.render("[Press Space]", True, (100, 100, 100))
            screen.blit(hint, (bubble.x + padding, bubble.bottom))
