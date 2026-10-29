# Backlog

Things we've talked about adding but put off for later, so they don't get lost in chat.
Move items to "Done" when they ship. Newest ideas go at the bottom of each section.

## Waiting on assets

- **Campfire for the camp.** The old drawn campfire was removed; Dustin is finding a sprite for it.
- **Sounds for the silent moments.** The Deadly Kombat pack covers punches, blocks, and impacts, but these still have no sound:
  boss laughs and roars, the Crow's caw, zombie groans, ghost wails, a victory jingle, menu clicks (move/select),
  the portal, and drinking potions.

## Gameplay and balance

- **Economy pass.** Tune item prices, drops, and candy rewards after playtesting the tiered upgrades and jab combos.
- **Overall difficulty.** In the simulation, a decent player with a few upgrades almost never loses. If fights still feel
  easy after playtesting the combos, bump enemy HP or damage in `core/levels.py`.
- **Graveyard difficulty.** The simulation says weaker players lose most of their fights in the Graveyard (Chapter 4) now
  that ailments stick around. Watch this in playtests; zombie infection chance or Remedy price are the easy knobs.
- **Click the ring itself (idea, later).** Make mouse players click on the moving timing ring instead of anywhere,
  for a real hand-eye test. Space on the keyboard would stay as it is.
- **Death Knight guard (idea, not decided).** Knights raise a guard that Haymakers bounce off but jabs break through.
- **More chapters past the Demon.** Malgorath is the final showdown "until we decide to go further."

## Release

- **Web demo for friends.** Build with pygbag and host it on itch.io once the game is more polished.
  Saving and settings write to a folder on the PC, which a browser build can't do, so they'll need a web-friendly version.
- **Smaller download.** The Windows zip is about 90 MB, mostly audio: `ominous.wav` (20 MB) and the sound effects
  (32-bit WAVs). Converting them to OGG would shrink it a lot (needed for the web build anyway).
- **Credits and licenses.** Add credits for the satyr, Death Knight, crow, blacksmith, camp background (safe), and demon art packs,
  and the composers of the three music tracks. The credits screen text is in `core/credits.py`; the README has its own list.
  Confirm Daniel Barros's license terms for the Deadly Kombat sound pack (the PDF didn't include any).

## From the README's planned features

- Inventory & equipment
- More interactions with Whisper Jack

## Setup

- **Home PC.** To work on it from home, start a new task from the Claude desktop app on that PC
  (project at C:\Users\Dustin\Documents\GitHub\pygame-rpg).

## Done

- Camp depth (foreground stumps and trees in front, fading when Charlie is behind them); move cards in battle
- Widescreen (1066x600): no black bars in fullscreen, backgrounds no longer squashed
- Title screen, Settings (volumes, fullscreen, difficulty), Controls, pause menu, autosave at camp + Continue,
  skippable credits, and a run summary after the ending
- Harder fights: Daze wears off, enemy flurries and feints, chapter scaling, Easy/Normal/Hard; timing rings move around
- Music: ominous track at camp, boss music from the taunt through the victory screen
- Tiered Blacksmith upgrades with rising prices; Double Candy removed
- Jab combos, Daze, off-balance Haymakers; Auto Block removed; five new upgrades
  (Quick Hands, Heavy Hands, Counter Puncher, Iron Chin, Thick Skin)
- Camp no longer heals; ailments last until cured
- Sound effects from the Deadly Kombat pack
- Camp with the Blacksmith and the Crow; Items menu replaces the Bomb option
- Roaming monsters in every chapter; bosses for all four chapters
