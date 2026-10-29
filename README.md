# 🎃 Chin Check Charlie 🥊
**A Halloween RPG of Ghosts, Candy, and Chin Checks**

**Chin Check Charlie** is a quirky, Halloween-themed 2D RPG where you play as **Chin Check Charlie**, a tough-as-nails hero wandering through haunted lands in search of candy, answers, and a fight.

Battle spooky enemies, collect candy to unlock upgrades, and survive the whispers of **Whisper Jack**, the ghostly voice in your head who's got advice... and maybe an agenda.

## ⚠️ Status: Still Under Construction!

This project is an active **work in progress**. Core gameplay systems are playable:

- **Title screen** with New Game, Continue, Settings (music and sound volume, fullscreen, difficulty), Controls, and Credits; **Esc** pauses the game
- **Autosave at every camp**: Continue picks up at the last camp you reached
- **Three difficulties** (Easy, Normal, Hard) that change enemy toughness, timing windows, and how often enemies combo and feint
- **An ending**: after the final camp, the credits roll (skippable) and a run summary shows your fights, PERFECTs, best combo, parries, candy, and play time
- **Four chapters**: The Cabin, Warlock's Hollow, The Bleeding Woods, and The Graveyard, each with its own roaming monsters and a boss at the end, joined by a glowing exit portal, a chapter title card, and Whisper Jack waiting on the other side
- **Exploration mode** (side-scrolling adventure)
- **Action-command battles**: time SPACE as the ring closes for PERFECT hits, time it on enemy swings to block or PARRY (and slide-kick counter); blocking is all timing, no menu button. Jab combos (nail each ring to chain more jabs; every jab dazes the enemy), the Haymaker (cashes in the Daze for a big hit, but leaves you off balance), and the Chin Check finisher, a Chin meter, telegraphed heavy attacks, zombie infection and burning (they last until a Remedy cures them, even between fights), ghosts that phase through sloppy hits, armored knights that shrug off untimed punches. Monsters get tougher every chapter: from Chapter 2 on they string 2-3 hits together (each with its own ring) and sometimes **feint**, stalling mid-swing so a press on rhythm comes too early. Timing rings pop up in different spots and drift more the deeper you go. Daze wears off if you don't cash it in, bosses can only be dazed twice, and enraging shakes it off
- **Heavy-hitting effects**: hit-stop, screen shake, sparks/goo/candy-corn particles, white hit flashes, knockback, slow-motion K.O. zoom
- **Gritty look**: per-level color grading, film grain, vignette, ground fog, inked outlines, and shadows
- **Candy is money**: spend it at camp. Healing comes from potions (**Gourd-Aid**, Remedies, Elixirs)
- **A camp after every boss** (including the last): a safe parallax forest to shop in, with stumps and trees in front of Charlie for depth (they fade when he walks behind them) (it doesn't heal you: that's what potions are for)
  - **The Blacksmith** hammers at his anvil and sells permanent upgrades for candy. Each upgrade has tiers that cost more every time, and there's far more to buy than one run earns, so you pick a build: Tough Hide, Potion Boost, Bomb Power, Second Wind, Quick Hands (jabs), Heavy Hands (Haymakers), Counter Puncher (parries), Iron Chin (the Chin meter), and Thick Skin (ailments)
  - **The Crow** wanders the camp, sells items (Gourd-Aid, Remedies, Elixirs, bombs, Chin Juice) and buys them back, along with the trophies monsters drop
- **Items**: a bag (**I**) you can drink potions from anywhere, and an **Items** menu in battle (Gourd-Aid, bombs, Chin Juice); monsters sometimes drop trophies or a Gourd-Aid, and bosses always drop a trophy
- **Animated results cards** after every fight showing candy, bombs, and trophies
- **Four towering bosses**, each with a taunt, a signature heavy attack (telegraphed a turn ahead), hit flinches, and an enrage at half HP:
  - **Mortis, Bringer of Death** (The Cabin): a ghost, so sloppy hits can pass right through him. *Death's Grasp* reaches out of a portal and steals HP
  - **Grimwald the Warlock** (Warlock's Hollow): his *Hex Storm* drains your Chin meter
  - **Scorchmaw the Fire Worm** (The Bleeding Woods): spits a *Fireball* that leaves Charlie BURNING (hurts every turn until he drinks a Remedy)
  - **Malgorath the Demon** (The Graveyard, final boss): his *Hellfire Cleave* burns you AND drains your Chin meter
- **Roaming monsters** in every chapter that wander, pause, notice Charlie, give chase, and attack to start a fight (or slide into them first for a First Strike):
  - **Ghosts** (The Cabin) drift and shimmer, then swoop
  - **Death Knights** (Warlock's Hollow) trot on patrol and gallop in for a Cavalry Charge; their armor halves untimed hits
  - **Satyrs** (The Bleeding Woods) skitter and hop; their Antler Beam sets Charlie burning
  - **Zombies** (The Graveyard) shamble and lurch, and their bites can infect
- **Animated characters** (Charlie, every monster and boss, Whisper Jack)

Expect some missing features, placeholder art, and candy wrappers on the floor while we build this haunted house.

## 🕹️ Controls

| Where | Keys |
|---|---|
| Exploring | **A / D** or **← / →** to walk, **Shift** to run, **Space** jump, **S** slide (slide into a monster for a First Strike), **H** to chug a Gourd-Aid (heal), **I** to open your bag |
| Camp | **E** to talk to the Blacksmith (upgrades) or the Crow (buy and sell items) when you're next to them |
| Battle | **← / →** to pick a move card, **Space / Enter** to confirm, **1-4** to pick one straight away, or just **click** a card; **Space** or **click** on the timing rings (attacking and defending). **Items** opens your bag: **← / →** or hover to choose, **Space** or click to use, **Esc** or right-click to go back |
| Whisper Jack | **Space** or **click** to continue |
| Shops and bag | Mouse to buy, sell, or use, wheel to scroll, **Tab** switches the Crow's Buy/Sell, **Esc** or **X** to close |
| Anywhere | **Esc** or **P** to pause, **M** to mute music, **F11** or **Alt+Enter** to toggle fullscreen |
| Menus | **↑ / ↓** and **Enter**, or the mouse; **← / →** changes a setting; **Esc** goes back |

Settings and the save game are kept in a `.chin_check_charlie` folder in your user folder (on Windows, `C:\Users\<you>\.chin_check_charlie`), so they never end up in git. Delete `save.json` there to wipe your save.

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

## 🧪 Making a Playtest Build

- **Windows:** double-click `build_windows.bat`. It sets up its own build environment, bundles the game with
  PyInstaller, and opens `%USERPROFILE%\ChinCheckCharlie-build`, which has:
  - `ChinCheckCharlie-windows.zip`: testers unzip it and run `ChinCheckCharlie.exe` (no Python needed)
  - `ChinCheckCharlie-linux-source.zip`: the game's source from your last commit, for Linux testers
- **Linux:** testers unzip the source and run `bash run_linux.sh` (it sets up Python packages the first time).
- `PLAYTEST.md` is the note for testers (how to run it, controls, what feedback we want). It's copied into the Windows zip.
- Bump `VERSION` in `scenes/title_screen.py` for each build you send, so feedback says which one they played.
- If the game crashes, it writes `crash_log.txt` to the `.chin_check_charlie` folder in the user's home folder.

## 🎵 Music

Three tracks in `assets/audio/`, crossfaded automatically:

- `background_music.mp3` while exploring the chapters (and in regular fights)
- `ominous.wav` at The Camp
- `boss.ogg` from the moment a boss starts taunting Charlie until the victory screen is closed

Which file plays where, and a loudness adjustment per track, is `MUSIC_TRACKS` in `core/settings.py`. **M** mutes.

## 🔊 Sound Effects

Hits, crits, the Chin Check, blocks, parries, dodges, enemy blades and bites, fire, and bombs all have sounds from the Deadly Kombat Free Library (in `assets/audio/sfx/`). Which file plays for which moment, and how loud, is the `SOUNDS` table at the top of `core/sfx.py`; several files per moment are picked at random so hits don't repeat.

Still silent (no matching sound yet): boss laughs and roars, the Crow's caw, zombie groans, ghost wails, the victory jingle, menu clicks, the portal, and drinking a potion. Add a file to the table, or drop in a file named after the event (e.g. `victory.wav`).

## 📂 Project Structure

```
main.py                  Game loop and scene switching
core/
  settings.py            Screen size, speeds, paths, and other tunable numbers
  levels.py              The chapters: names, backgrounds, monsters and bosses, Whisper Jack's lines
  portal.py              Glowing exit portal at the end of each level
  animation.py           Frame animation for GameArt2D-style characters (feet-anchored, flippable, posable)
  effects.py             Combat juice: shake, particles, timing rings, swooshes, animation scripts
  grit.py                Color grading, grain, vignette, fog, ground shadows (toggle GRIT in settings)
  roaming_enemy.py       How monsters wander, chase, and attack in exploration (per-kind PROFILES)
  boss_encounter.py      Boss waiting at a level's end: taunt, then fight
  enemy_art.py           Which animations each enemy uses, boss sizes (BOSS_HEIGHTS), and battle layout per enemy
  sfx.py                 Sound effects by event name (files in assets/audio/sfx)
  assets.py              Cached image loading
  ui.py                  Fonts, colors, and shared drawing helpers (spooky panels, candy buttons)
  icons.py               Hand-drawn menu icons (candy corn, bombs, upgrade badges, Jack's skull)
  player.py              Charlie's stats, healing, candy, inventory, upgrades
  enemy.py               Enemy stats and per-type traits (phasing, infection, burning, lifesteal, meter drain)
  upgrades.py            The Blacksmith's upgrades and their tier prices
  items.py               Every item: what it does, what the Crow charges and pays, and monster trophy drops
  battle_manager.py      Combat rules: move damage, timing bonuses, parries, infection (tuning in MOVES)
  combat_options.py      Battle menu
  item_picker.py         The battle Items menu
  combat_text.py         Floating damage/heal numbers
  player_hud.py          Player HP bar and stats
  enemy_hud.py           Enemy HP bar
  end_combat_modal.py    Results card after a fight (win, boss win, loss)
  shop_modal.py          The card-grid window shared by every shop and the bag
  camp_shops.py          The Blacksmith's shop, the Crow's shop (Buy/Sell), and the bag
  camp.py                The camp: parallax forest, Blacksmith, Crow
  skeleton_animation.py  Whisper Jack
  music_manager.py       Music: crossfades between the level, camp, and boss tracks
  difficulty.py          Difficulty settings and chapter scaling (all the tuning numbers)
  options.py             Player settings, saved between runs
  save_game.py           Autosave at camp / Continue
  credits.py             The credits text (edit freely)
  menu_ui.py             Buttons and dialogs shared by the menus
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

The full running list of ideas we've put off is in [BACKLOG.md](BACKLOG.md).

- Inventory & equipment
- More interactions with Whisper Jack

## ✨ Why "Chin Check Charlie"?

Because when ghosts show up, someone's gotta throw hands. And it's Halloween, so candy is serious business.

## 👻 Credits

- Design & Code: SapphireBloo
- Skeleton Advisor: Whisper Jack (fictional)
- Charlie (Jack-o'-Lantern) and Zombies: GameArt2D / pzUH (CC0)
- Grimwald the Warlock: Evil Wizard 2 asset pack (CC0)
- Mortis, Bringer of Death: Bringer of Death by Clembod (clembod.itch.io)
- Scorchmaw the Fire Worm: Fire Worm asset pack (CC0)
- Malgorath the Demon: Demon Slime (free version)
- Sound effects: Deadly Kombat Free Library by Daniel Barros (linktr.ee/danielsoundsgood)
- Font: Consolas
- Made with: Python + pygame-ce

## 🦴 License

MIT License. Free to play with, remix, or adapt. Just don't forget to leave some candy behind. 🍬
