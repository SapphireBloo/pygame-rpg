"""Speech bubbles over characters in the world (the camp folk's greetings, Crumb's outbursts).

A bubble wraps its text, draws it outlined on a dark rounded panel with a little tail pointing
at whoever's talking, follows them around, and fades out when its time is up.
"""
import pygame

from core.ui import get_font, outlined_text

MAX_WIDTH = 270
PAD = 9
FADE_MS = 300


def _wrap(text, font, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if font.size(trial)[0] <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


class SpeechBubble:
    def __init__(self, text, speaker, color, life=2800, size=16, height=None):
        """speaker: anything with an .x (world x of its feet). height: how far above the ground the
        tail points (defaults to the top of the speaker's sprite)."""
        self.speaker = speaker
        self.color = color
        self.life = self.total = life
        self.height = height
        font = get_font(size, True)
        lines = _wrap(text, font, MAX_WIDTH)
        rendered = [outlined_text(line, size, (250, 240, 225), True, 2) for line in lines]
        w = max(r.get_width() for r in rendered) + PAD * 2
        h = sum(r.get_height() for r in rendered) + PAD * 2 - 4
        self.surface = pygame.Surface((w, h + 10), pygame.SRCALPHA)
        body = pygame.Rect(0, 0, w, h)
        pygame.draw.rect(self.surface, (14, 10, 18, 225), body, border_radius=10)
        pygame.draw.rect(self.surface, (*color, 240), body, 2, border_radius=10)
        tail = [(w // 2 - 8, h - 2), (w // 2 + 8, h - 2), (w // 2, h + 9)]
        pygame.draw.polygon(self.surface, (14, 10, 18, 225), tail)
        pygame.draw.lines(self.surface, (*color, 240), False, [tail[0], tail[2], tail[1]], 2)
        y = PAD - 2
        for r in rendered:
            self.surface.blit(r, ((w - r.get_width()) // 2, y))
            y += r.get_height()

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt):
        self.life -= dt

    def draw(self, screen, camera_offset, feet_y):
        if self.height is not None:
            top = self.height
        else:
            frames = self.speaker.sprite.current.frames
            top = frames[0].get_height() + 30
        x = self.speaker.x - camera_offset
        rect = self.surface.get_rect(midbottom=(x, feet_y - top))
        rect.clamp_ip(screen.get_rect().inflate(-8, -8))
        age = self.total - self.life
        alpha = min(1.0, age / FADE_MS, self.life / FADE_MS)
        self.surface.set_alpha(int(255 * max(0.0, alpha)))
        screen.blit(self.surface, rect)
