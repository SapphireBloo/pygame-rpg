# Chin Check Charlie: Playtest

Thanks for playing! This is an early demo, so expect rough edges. Your honest feedback is the whole point.

## How to start

**Windows**
1. Unzip `ChinCheckCharlie-windows.zip` somewhere (right-click, *Extract All*). Don't run it from inside the zip.
2. Open the `ChinCheckCharlie` folder and double-click **ChinCheckCharlie.exe**.
3. Windows will probably say *"Windows protected your PC"*. That's because the game isn't from a paid,
   registered publisher. Click **More info**, then **Run anyway**.

**Linux**
1. Unzip `ChinCheckCharlie-linux-source.zip`.
2. Open a terminal in the `ChinCheckCharlie` folder and run: `bash run_linux.sh`
3. The first run sets things up (needs Python 3 and the internet once). After that it starts right away.

The game starts fullscreen. **F11** switches to a window. **Esc** pauses (Resume, Settings, Controls, Quit).

## Controls

| | |
|---|---|
| Walk / run | **A / D** or arrows, hold **Shift** to run |
| Jump / slide | **Space** / **S** (slide into a monster to get a free first hit) |
| Talk at camp | **E** next to the Blacksmith or the Crow |
| Bag / quick heal | **I** / **H** |
| Fight | Pick a move with arrows, **1-4**, or the mouse. Then press **Space** (or click) as each ring closes |
| Defend | Press **Space** right as an enemy's hit lands: good timing blocks, perfect timing **parries** |

The full list is under **Controls** on the title screen. Settings has volume, fullscreen, and **difficulty**
(Normal is the intended experience; Easy if you just want the story).

The game saves automatically at each camp. **Continue** on the title screen picks up from there.

## What we'd love to hear

Play as far as you like (the whole demo is four chapters). Then tell us:

1. **Difficulty:** too easy, too hard, or about right? Which fight gave you the most trouble?
2. **Fighting:** did the timing feel fair? Did you end up using Jab, Haymaker, and parries, or spam one thing?
3. **Candy and shopping:** did you have enough candy? Which upgrades did you buy, and why?
4. **Confusing moments:** anything you didn't understand, or had to guess at?
5. **Favorite and least favorite** part.
6. **Bugs:** anything broken, stuck, or weird. What were you doing when it happened?

Include the difficulty you played on and the version shown in the bottom-right of the title screen.

## If something goes wrong

If the game crashes, it writes `crash_log.txt` here. Please send it along:
- **Windows:** `C:\Users\<your name>\.chin_check_charlie\`
- **Linux:** `~/.chin_check_charlie/`

That folder also holds your save (`save.json`) and settings. Delete them to start completely fresh.
