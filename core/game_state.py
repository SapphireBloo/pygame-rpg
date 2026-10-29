"""Story flags shared between scenes (which Whisper Jack scenes have played)."""

whisper_jack_exploration_intro_done = False  # first talk when you start walking
whisper_jack_combat_intro_done = False       # tutorial at the start of the first battle
whisper_jack_second_intro_done = False       # talk after the first battle is won
first_battle_done = False
first_camp_done = False                      # Whisper Jack explained the camp

FLAGS = ("whisper_jack_exploration_intro_done", "whisper_jack_combat_intro_done",
         "whisper_jack_second_intro_done", "first_battle_done", "first_camp_done")


def reset():
    """A new game: every Whisper Jack scene plays again."""
    for name in FLAGS:
        globals()[name] = False


def to_dict():
    return {name: globals()[name] for name in FLAGS}


def from_dict(data):
    for name in FLAGS:
        globals()[name] = bool(data.get(name, False))
