"""Cheat codes, for testing. Type one in under Cheats (on the title screen or the pause menu).

  candyrulez   One-hit knockouts: anything Charlie lands (a punch, a counter, a bomb, a First
               Strike, Loaf Launch) knocks the enemy out, bosses included. Sloppy punches can't
               whiff or pass through ghosts while it's on.

Entering a code again turns it back off. Cheats that are on are remembered (in settings.json,
next to the other settings), and a CHEAT tag shows in fights while any are on so one is never
left on by accident.

To add a code: put it in CODES as  "code": ("name", "What it does"),  and check
cheats.active("name") wherever it should change something.
"""
from core.options import options, save

CODES = {
    "candyrulez": ("one_shot", "One-hit knockouts"),
}
NAMES = {name: label for name, label in CODES.values()}


def active(name):
    return name in options.get("cheats", ())


def one_shot():
    return active("one_shot")


def labels():
    """What's switched on right now, as display names."""
    return [NAMES[name] for name in options.get("cheats", ()) if name in NAMES]


def enter(code):
    """Try a code. Returns (label, now_on) if it's a real code (and flips it), or None."""
    code = "".join(code.split()).lower()
    if code not in CODES:
        return None
    name, label = CODES[code]
    on = list(options.get("cheats", ()))
    if name in on:
        on.remove(name)
    else:
        on.append(name)
    options["cheats"] = on
    save()
    return label, name in on
