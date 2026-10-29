import pygame


class MusicManager:
    """Background music with mute and crossfades. If there's no audio device or a
    file is missing, it prints a warning and the game keeps running silently.

    Call play_track(path, gain) whenever the scene decides what should be playing
    (it's fine to call it every frame), and update() once per frame. When the track
    changes, the old one fades out and the new one fades in.
    """

    FADE_MS = 800

    def __init__(self, volume=0.5):
        self.volume = volume          # master music volume (0-1)
        self.gain = 1.0               # per-track loudness adjustment
        self.muted = False
        self.current_track = None
        self.wanted = None            # (path, gain) waiting for the old track to fade out
        try:
            pygame.mixer.init()
            self.enabled = True
        except pygame.error as err:
            print(f"[music] Audio unavailable, continuing without sound: {err}")
            self.enabled = False

    # ---- track switching ---------------------------------------------------
    def play_track(self, filepath, gain=1.0):
        """Make this the playing track (fading from the old one). No-op if it already is."""
        if not self.enabled:
            return
        target = (str(filepath), gain)
        if target[0] == self.current_track and self.wanted is None:
            return
        if self.wanted and self.wanted[0] == target[0]:
            return
        self.wanted = target
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(self.FADE_MS)
        else:
            self._start_wanted()

    def update(self):
        """Start the next track once the old one has faded out."""
        if self.enabled and self.wanted and not pygame.mixer.music.get_busy():
            self._start_wanted()

    def _start_wanted(self):
        path, gain = self.wanted
        self.wanted = None
        try:
            pygame.mixer.music.load(path)
        except pygame.error as err:
            print(f"[music] Couldn't load {path}: {err}")
            self.current_track = path       # don't retry every frame
            return
        self.current_track = path
        self.gain = gain
        self._apply_volume()
        pygame.mixer.music.play(-1, fade_ms=self.FADE_MS)

    # ---- simple controls -----------------------------------------------------
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
            self._apply_volume()
            pygame.mixer.music.play(loops)

    def stop(self):
        if self.enabled:
            pygame.mixer.music.stop()

    def set_volume(self, volume):
        self.volume = max(0.0, min(volume, 1.0))
        self._apply_volume()

    def toggle_mute(self):
        self.muted = not self.muted
        self._apply_volume()

    def _apply_volume(self):
        if self.enabled:
            pygame.mixer.music.set_volume(0 if self.muted else min(1.0, self.volume * self.gain))
