# 🎃 Chin Check Charlie 🥊
**A Halloween RPG of Ghosts, Candy, and Chin Checks**

**Chin Check Charlie** is a quirky, Halloween-themed 2D RPG where you play as **Chin Check Charlie**, a tough-as-nails hero wandering through haunted lands in search of candy, answers, and a fight.

Battle spooky enemies, collect candy to unlock upgrades, and survive the whispers of **Whisper Jack**, the ghostly voice in your head who's got advice... and maybe an agenda.

## ⚠️ Status: Still Under Construction!

This project is an active **work in progress**. Core gameplay systems are playable:

- **Four chapters**: The Cabin, Witch's Hollow, The Bleeding Woods, and The Graveyard, each with tougher ghosts, joined by a glowing exit portal, a chapter title card, and Whisper Jack waiting on the other side
- **Exploration mode** (side-scrolling adventure)
- **Action-command battles**: time SPACE as the ring closes for PERFECT hits, time it on enemy swings to block or PARRY (and slide-kick counter); blocking is all timing, no menu button. Jab, Haymaker, and the Chin Check finisher, a Chin meter, telegraphed heavy attacks, zombie infection, ghosts that phase through sloppy hits
- **Heavy-hitting effects**: hit-stop, screen shake, sparks/goo/candy-corn particles, white hit flashes, knockback, slow-motion K.O. zoom
- **Gritty look**: per-level color grading, film grain, vignette, ground fog, inked outlines, and shadows
- **Candy Shop upgrades** (spend your hard-earned candy on buffs)
- **Roaming zombies** in The Graveyard that shamble, idle, notice Charlie, and lunge to start a fight, with full attack and death animations in battle
- **Animated characters** (Charlie, ghosts, zombies, Whisper Jack)

Expect some missing features, placeholder art, and candy wrappers on the floor while we build this haunted house.

## 🕹️ Controls

| Where | Keys |
|---|---|
| Exploring | **A / D** or **← / →** to walk, **Shift** to run, **W** jump, **S** slide (slide into a monster for a First Strike), **H** to eat candy (heal), click **Candy Shop** |
| Battle | **← / →** to pick a move, **Space / Enter** to confirm; **Space** again on the timing rings (attacking and defending) |
| Whisper Jack | **Space** to continue |
| Candy Shop | Mouse to buy, wheel to scroll, **Esc** or **X** to close |
| Anywhere | **M** to mute music, **F11** or **Alt+Enter** to toggle fullscreen (set `FULLSCREEN` in `core/settings.py` to choose how it starts), **Alt+F4** to quit |

## 💻 How to Run

1. Install **Python 3.10+**
2. Install the dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
   This installs **pygame-ce** (Community Edition), a drop-in replacement for pygame that has
   prebuilt wheels for the newest Python versions. The code still says `import pygame`.
3. Run the game (from any folder):
   ```bash
   python main.py
   ```

## 📂 Project Structure

```
main.py                  Game loop and scene switching
core/
  settings.py            Screen size, speeds, paths, and other tunable numbers
  levels.py              The chapters: names, backgrounds, ghost stats, Whisper Jack's lines
  portal.py              Glowing exit portal at the end of each level
  animation.py           Frame animation for GameArt2D-style characters (feet-anchored, flippable, posable)
  effects.py             Combat juice: shake, particles, timing rings, swooshes, animation scripts
  grit.py                Color grading, grain, vignette, fog, ground shadows (toggle GRIT in settings)
  roaming_zombie.py      Zombie wandering/chase/grab behavior in exploration
  assets.py              Cached image loading
  ui.py                  Fonts, colors, and shared drawing helpers
  player.py              Charlie's stats, healing, bombs, candy, upgrades
  enemy.py               Enemy stats and per-type traits (ghost phasing, zombie infection, heavy attacks)
  upgrades.py            Candy Shop catalog
  battle_manager.py      Combat rules: move damage, timing bonuses, parries, infection (tuning in MOVES)
  combat_options.py      Battle menu
  combat_text.py         Floating damage/heal numbers
  player_hud.py          Player HP bar and stats
  enemy_hud.py           Enemy HP bar
  end_combat_modal.py    Win/lose popup
  candy_shop_modal.py    Candy Shop window
  skeleton_animation.py  Whisper Jack
  music_manager.py       Background music
  game_state.py          Story flags (which Whisper Jack scenes have played)
scenes/
  exploration_scene.py   Side-scrolling world
  battle_scene.py        Turn-based fights
  level_transition.py    Fade-out, chapter title card, fade-in between levels
assets/
  images/                Sprites and backgrounds
  audio/                 Music
```

## 🚧 Planned Features

- Save / load system
- Inventory & equipment
- Boss battles
- Boss at the end of The Graveyard
- New enemy types per chapter
- More unique enemies & ghost variants
- More interactions with Whisper Jack

## ✨ Why "Chin Check Charlie"?

Because when ghosts show up, someone's gotta throw hands. And it's Halloween, so candy is serious business.

## 👻 Credits

- Design & Code: SapphireBloo
- Skeleton Advisor: Whisper Jack (fictional)
- Charlie (Jack-o'-Lantern) and Zombies: GameArt2D / pzUH (CC0)
- Font: Consolas
- Made with: Python + pygame-ce

## 🦴 License

MIT License. Free to play with, remix, or adapt. Just don't forget to leave some candy behind. 🍬
