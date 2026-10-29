"""How hard the fights are: the chosen difficulty (Settings) plus how far into
the game Charlie is. Every tuning number for that lives here.

  enemy_mods(chapter, boss, difficulty)  -> what an enemy gets for this fight
  timing_scale(difficulty)                -> multiplier on every timing window
  ring_motion(chapter, boss, difficulty)  -> how far timing rings jump and drift
"""

DIFFICULTIES = ("easy", "normal", "hard")
DIFFICULTY_NAMES = {"easy": "Easy", "normal": "Normal", "hard": "Hard"}
DIFFICULTY_BLURBS = {
    "easy": "Softer hits, wider timing, no feints. For friends who just want the story.",
    "normal": "The way it's meant to be played.",
    "hard": "Tougher monsters, tighter timing, more combos and feints.",
}

# Per difficulty: enemy HP and damage, timing-window size, and how often enemies string
# hits together or feint (added to the chapter's chance), and how much the rings move.
SETTINGS = {
    "easy":   {"hp": 0.8,  "damage": 0.75, "windows": 1.25, "strings": 0.5, "feint_bonus": None, "motion": 0.6},
    "normal": {"hp": 1.0,  "damage": 1.0,  "windows": 1.0,  "strings": 1.0, "feint_bonus": 0.0,  "motion": 1.0},
    "hard":   {"hp": 1.1,  "damage": 1.1,  "windows": 0.9,  "strings": 1.2, "feint_bonus": 0.05, "motion": 1.2},
}

# Per chapter (0 = Chapter 1): monsters get tougher as Charlie goes deeper.
CHAPTER_HP = (1.0, 1.15, 1.25, 1.3)
CHAPTER_DAMAGE = (1.0, 1.05, 1.1, 1.15)
BOSS_CHAPTER_SHARE = 0.4     # bosses already get tougher by design, so they take less of the chapter bump

# Attack strings: a regular (not heavy) attack can be 2-3 quick hits, each with its own ring.
STRING_CHANCE = (0.0, 0.25, 0.3, 0.35)    # by chapter
STRING_MAX_HITS = (1, 2, 3, 3)
STRING_BOSS_BONUS = 0.05
STRING_HIT_DAMAGE = 0.6                   # each hit of a string does 60% of a normal hit

# Feints: the enemy hitches mid-swing, so the ring stalls before it closes.
FEINT_CHANCE = (0.0, 0.12, 0.2, 0.25)     # by chapter, per swing
FEINT_BOSS_BONUS = 0.1
FEINT_HOLD_MS = (260, 420)                # how long the stall lasts

# Timing rings: how far from the target they can appear (px), and how far they drift while closing
RING_JUMP = (30, 50, 70, 80)              # by chapter
RING_DRIFT = (0, 16, 26, 32)
RING_BOSS_EXTRA = 10


def _chapter(chapter):
    return max(0, min(3, chapter))


def settings(difficulty):
    return SETTINGS.get(difficulty, SETTINGS["normal"])


def enemy_mods(chapter, boss, difficulty):
    """Multipliers and chances for one enemy in this chapter at this difficulty."""
    c, d = _chapter(chapter), settings(difficulty)
    string = 0.0
    if STRING_MAX_HITS[c] > 1:
        string = min(0.8, (STRING_CHANCE[c] + (STRING_BOSS_BONUS if boss else 0)) * d["strings"])
    if d["feint_bonus"] is None:
        feint = 0.0
    else:
        feint = FEINT_CHANCE[c] + (FEINT_BOSS_BONUS if boss and c else 0) + (d["feint_bonus"] if c else 0)
    share = BOSS_CHAPTER_SHARE if boss else 1.0
    return {
        "hp": (1 + (CHAPTER_HP[c] - 1) * share) * d["hp"],
        "damage": (1 + (CHAPTER_DAMAGE[c] - 1) * share) * d["damage"],
        "string_chance": string,
        "string_max": STRING_MAX_HITS[c],
        "feint_chance": feint,
    }


def timing_scale(difficulty):
    return settings(difficulty)["windows"]


def ring_motion(chapter, boss, difficulty):
    """(jump, drift) in pixels for timing rings in this fight."""
    c, k = _chapter(chapter), settings(difficulty)["motion"]
    extra = RING_BOSS_EXTRA if boss else 0
    return (RING_JUMP[c] + extra) * k, (RING_DRIFT[c] + (extra if c else 0)) * k
