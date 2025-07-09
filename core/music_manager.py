import pygame

class MusicManager:
    def __init__(self, volume=0.5):
        pygame.mixer.init()
        self.volume = volume
        self.current_track = None
        self.is_playing = False

    def load(self, filepath):
        if filepath != self.current_track:
            pygame.mixer.music.load(filepath)
            self.current_track = filepath

    def play(self, loops=-1):
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.play(loops)
        self.is_playing = True

    def pause(self):
        pygame.mixer.music.pause()
        self.is_playing = False

    def unpause(self):
        pygame.mixer.music.unpause()
        self.is_playing = True

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False

    def set_volume(self, volume):
        self.volume = max(0, min(volume, 1))  # Clamp between 0 and 1
        pygame.mixer.music.set_volume(self.volume)

    def toggle_mute(self):
        if pygame.mixer.music.get_volume() > 0:
            pygame.mixer.music.set_volume(0)
        else:
            pygame.mixer.music.set_volume(self.volume)
