import pygame


class MusicManager:
    """Background music with mute. If there's no audio device or the file is
    missing, it prints a warning and the game keeps running silently."""

    def __init__(self, volume=0.5):
        self.volume = volume
        self.muted = False
        self.current_track = None
        try:
            pygame.mixer.init()
            self.enabled = True
        except pygame.error as err:
            print(f"[music] Audio unavailable, continuing without sound: {err}")
            self.enabled = False

    def load(self, filepath):
        if not self.enabled or str(filepath) == self.current_track:
            return
        try:
            pygame.mixer.music.load(str(filepath))
            self.current_track = str(filepath)
        except pygame.error as err:
            print(f"[music] Couldn't load {filepath}: {err}")

    def play(self, loops=-1):
        if self.enabled and self.current_track:
            pygame.mixer.music.set_volume(0 if self.muted else self.volume)
            pygame.mixer.music.play(loops)

    def stop(self):
        if self.enabled:
            pygame.mixer.music.stop()

    def set_volume(self, volume):
        self.volume = max(0.0, min(volume, 1.0))
        if self.enabled and not self.muted:
            pygame.mixer.music.set_volume(self.volume)

    def toggle_mute(self):
        self.muted = not self.muted
        if self.enabled:
            pygame.mixer.music.set_volume(0 if self.muted else self.volume)
