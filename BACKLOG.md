# Backlog

Things we've talked about adding but put off for later, so they don't get lost in chat.
Move items to "Done" when they ship. Newest ideas go at the bottom of each section.

## Waiting on assets

- **Sounds for the silent moments.** The Deadly Kombat pack covers punches, blocks, and impacts, but these still have no sound:
  boss laughs and roars, the Crow's caw, zombie groans, ghost wails, a victory jingle, menu clicks (move/select),
  the portal, and drinking potions.

- **A real ending.** There's an ending idea that needs its own art. Until then, beating Gorge rolls the credits.
- **Gorge's artist.** We don't know where the bully sprite sheets came from yet; the credits say "coming soon".

## Gameplay and balance

- **Economy pass.** Tune item prices, drops, and candy rewards after playtesting the tiered upgrades and jab combos.
- **Overall difficulty.** In the simulation, a decent player with a few upgrades almost never loses. If fights still feel
  easy after playtesting the combos, bump enemy HP or damage in `core/levels.py`.
- **Graveyard difficulty.** The simulation says weaker players lose most of their fights in the Graveyard (Chapter 4) now
  that ailments stick around. Watch this in playtests; zombie infection chance or Remedy price are the easy knobs.
- **Click the ring itself (idea, later).** Make mouse players click on the moving timing ring instead of anywhere,
  for a real hand-eye test. Space on the keyboard would stay as it is.
- **Trap and search tuning.** Trap damage is `TRAP_DAMAGE` in `scenes/exploration_scene.py` (6/8/10/12 by chapter,
  never a knockout); search finds are `SEARCH_LOOT` in `core/obstacles.py`. Searched spots reset if you die and come back.
  Fires are camp-only scenery now (they didn't fit the levels).
- **Depth in the levels (later).** The camp has far/near decor bands and firelight now; do the same in the chapters
  when we come back to it. Their backgrounds are single flat images, so real parallax there would need layered art,
  but far/near decor bands (and light around the torches) would still work.
- **More level ideas (later).** Moving platforms, crumbling planks, swinging blades, drop-through ledges (Down to drop),
  puzzles (a lever that opens a gate). The tileset also has trees, a house, a boat, wheat, and waterfalls we haven't used yet.
- **Death Knight guard (idea, not decided).** Knights raise a guard that Haymakers bounce off but jabs break through.
- **Crumb's difficulty.** He has a tell when he stalls and forgives one too-early press per stalled swing, and was eased
  after the first playthrough (a simulated decent player on Normal now wins about 9 in 10, up from about half).
  The knobs: his HP and damage (`SECRET_BOSS` in `core/levels.py`), the `CRUMB_*` and `BUTTER_SLICK_CHANCE` numbers at
  the top of `scenes/battle_scene.py`, and `forgive_early` on `TimingRing` in `core/effects.py`.
- **The Void's pacing.** Jack's lines stay up `LINE_MS` (3.4 s) each and Charlie walks at `WALK_SCALE` (60%) speed
  (`scenes/void_walk.py`); his lines only count down while Charlie walks forward. Watch whether the walk drags or
  rushes in playtests.

## Release

- **Web demo for friends.** Build with pygbag and host it on itch.io once the game is more polished.
  Saving and settings write to a folder on the PC, which a browser build can't do, so they'll need a web-friendly version.
- **Smaller download.** The Windows zip is about 90 MB, mostly audio: `ominous.wav` (20 MB) and the sound effects
  (32-bit WAVs). Converting them to OGG would shrink it a lot (needed for the web build anyway).
- **Credits and licenses.** Add credits for the satyr, Death Knight, crow, blacksmith, camp background (safe), and demon art packs,
  and the composers of the three music tracks. The credits screen text is in `core/credits.py`; the README has its own list.
  Confirm Daniel Barros's license terms for the Deadly Kombat sound pack (the PDF didn't include any).
  AshDeal's horror pack (the Void creatures) and the GandalfHardcore tileset both say the raw files may not be
  redistributed, so check that before making the repo (or a source zip) public.

## From the README's planned features

- Inventory & equipment
- More interactions with Whisper Jack

## Setup

- **Home PC.** To work on it from home, start a new task from the Claude desktop app on that PC
  (project at C:\Users\Dustin\Documents\GitHub\pygame-rpg).

## Done

- Whisper Jack talks from his narration panel everywhere (chapters, camp, the first fight), like in the Void;
  outside the Void he still holds Charlie in place until his lines are read

- Third pass: cabin crushers hang from shelves and always cycle; step traps can't be outrun (only jumped);
  Crumb trots behind Charlie and has no menu once he's a partner (fixes E at the portal); Whisper Jack's portrait
  and more frightened lines in the Void, no floor line; new HP bars (damage trail, numbers in the bar, low-HP pulse)

- Cheats menu (title screen and pause menu) for testing: `candyrulez` gives one-hit knockouts

- Second pass after a full playthrough: no more low beams or overhangs to slide under (the graveyard's Golden Crumb grave
  moved up onto a high island); crushers hang under floating slabs instead of ropes; boxing gloves, runes, sandworms,
  and crushers wait until Charlie steps on (or under) them; Gorge arrives in a spotlight and dies back into it;
  Whisper Jack only talks in the Void while Charlie walks forward; Crumb eased

- Chapter 5, The Void: a slow walk through a nebula and starfield while Whisper Jack talks (no platforms or traps);
  Catto, the Mad Ghost, the Void Mage, and the Abomination step out one after each speech, then Gorge, Taker of Worlds
  (the candy bully; his Candy Snatch steals candy on a missed ring and you get it back if you win); credits roll after
- Crumb's fight is now a surprise: feed him the 4th crumb, shop as usual, and at the portal he stops you. Go back to the
  red, steaming Crumb and press E. One shot only: win and he joins Charlie (follows him, all snack blessings for good,
  Loaf Launch once per fight); lose and he calms down and lets you go. His feints forgive one early press and have a tell
- Portal: the tileset's dark portal as it is, the label in the chapter's color; press E and Charlie walks in
- Swinging cauldrons replaced by the Pixel Trap Pack: boxing gloves, crushers, runes, lightning, sandworms, an arrow totem
- Dying puts you back at camp fully healed and cured, with exactly what you left that camp with
- Crumb's speech bubbles wrap and stay on screen (one at a time) instead of stretching over everything

- Camp depth: far props back by the treeline (smaller, hazier, scrolling slower), near ones in front of the camera
  (big, dark, see-through when Charlie's behind them), and flickering firelight from the cooking fire, the forge,
  the torches, and a little far-off campfire

- Double jump; stomp a monster's head for a First Strike; monsters up on platforms (crate loft, earth ridges) that can't
  grab Charlie from above or below; monsters hang back past their reach where you land, so you can slide in; more
  height in every chapter (thin floating islands you can jump up through, higher shelves); fires out of the levels
  (swinging cauldrons in the Cabin and Hollow instead); the tileset's portal replaces the old drawn one

- Obstacles, traps, and searching in every chapter (GandalfHardcore tileset): crates/blocks/shelves to climb, slide-under
  beams and spiky overhangs (crawl while stuck under them), fires, toxic pools, bone spikes, search spots; the levels got
  longer with room around each monster; Golden Crumbs moved to a top shelf (Cabin), over a toxic pool (Hollow), over
  spikes (Woods), and inside a grave under an overhang (Graveyard). Camp decor: tents, cooking fire, forge, torches

- Dying sends you back to the last camp (or the start of Chapter 1); no more half-candy drop
- Crumb at camp (pet, feed snacks for a blessing), hidden Golden Crumbs, and the secret boss: Crumb, the Crust Eternal
  (all four crumbs fed, at the last camp; three phases, Crouton Barrage, Butter Slick)
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
