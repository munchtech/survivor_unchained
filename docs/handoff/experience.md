# Handoff: the gameplay experience director

For a fresh successor. Read `docs/team/README.md` first (the owner's bar, how we work, the
roster), then this, then `docs/team/experience.md` (the one-page status) and
`docs/EXPERIENCE_AUDIT.md` (the audit, the structure, the maps' shape, the music by beat).

## The owner, in their words

- "begin leveling up our whole gameplay experience again".
- The bar: "AAA standard", "strive for excellent, above and beyond", "do we have soul", "I don't
  want to polish, I want to create perfection", "how things are can be limiting".
- Decisions:
  - "endless is truly endless";
  - full-page screens pause the world only in arena combat, "and are often not the best choice";
  - final voices are recorded in ElevenLabs later (the voice lead is paused: no placeholders).
- Structure (4 October): "story should be 40% of the game early on, end game is two types of
  arenas - permanent and our normal arenas. permanent is our arpg build maps like poe and the
  normal arenas are for mindless survivors fun". Story nights are 20 minutes; "the Wayfinder's
  maps are 30" (the table's people-named nights, as the story lead uses the words; the atlas's
  build maps are another thing and run about ten minutes).
- Music: "i'll work on music at some point". Leave the score; the audit says what it must do.

## The brief

You are the gameplay experience director: the whole experience as a player lives it, from the
title through a run, the hub, the story and many runs. Raise it to the best of the genre.
- **Yours:** game feel and juice; pacing and set pieces; onboarding; the loop and
  meta-progression; the endgame arenas' shape and loop; anything no lead owns.
- **The leads:** short written briefs (what's wrong, the evidence, the target, how it's judged);
  check their results in play.
- **How:** play with the autopilot and harness, shoot frames at 1920×1080, read the logs. Decide,
  record why, escalate only what needs the owner. Commit and push your branch at milestones
  (the main session merges it; no PRs); `dotnet test` in `godot/tests` before every commit;
  British spelling; comments are short prose saying why.

## Done (all on `worktree-agent-ad1f5623590e09883`, pushed; last `8a56eb43`)

Merged with the integration branch at `f56ee42`. 567 tests green.

- **Verified at full resolution** since performance's merge: the opening groups, the camera, the
  dead, the fall, a story night's end. Fixed from the frames: the boss's own 14 m flat death blast
  under the fall (`BattleFx`, Ev.Kill), the way out's prompt over her at the peak (now 2.6 s
  later), the victory words over the flash (0.8 s later), a story night's pointless way out and
  "comes again" (`ArenaRun.Victory`, `Objectives`), chalk-white bones (old bone, laid flat, skulls
  face up: `Gore`), the hit flash blooming pale bodies (rim, `vat.gdshaderinc`), the field flashing
  between the result and the road (`Game.LeaveArena`), the autopilot stranding her after a result.
- **The chest as a sequence** (S-09): `godot/src/Game/ChestCeremony.cs`. Staged in the world, not
  on a page. `LevelUp.OpenChest` returns `ChestItem`s; `IZoneHost.Chest(ChestOpened)` (default:
  the old one-line announcement for headless hosts); `GameMenus.UpdateChest` queues and shows it
  (`hudMode "chest"`, the fight paused, `WorldScene.Hold` freezes the living's clock while effects
  keep real time). 1/3/5 at 84/12/4% (mean 1.4, unchanged). The chest model has a hinged `Lid`
  (`ItemModels.Chest`). Sounds: `Sfx.ChestShake/ChestBurst/ChestLand/ChestTick`.
- **The evolution** (S-10): the slot crowned (`WeaponSlot.Crown`), 0.6 s slow motion
  (`WorldScene.Slow`), gold light and rings instead of the 9 m pink disc. A chest's evolution waits
  for the chest to close (`Ev.Evolve.Chest`). Discoveries are a side toast, not a centre title.
- **Sound:** the ember ladder (S-02) on D minor pentatonic, merged per frame, a lodestone's breath;
  the level-up landing on major (S-04); the crowd's fall and the swell at 15/40/80/150 kills in
  1.5 s (S-08, `SoundBridge`), with a camera kick.
- **Feel:** a 120 ms dash and art buffer (S-05, `WorldScene`); rumble (S-14, `Haptics.cs`, a
  "Pad rumble" option); her blows lean the camera (S-17, `FollowCamera.Kick`), arts' hit-stop,
  a bigger flinch. S-06 (bars that flow) was already built.
- **The ember carpet:** 240 stones lie at most (`Battle.EmberCap`); the rest go into one red hoard
  stone under a beam (`Battle.Hoard`). Stone colours kept saturated (no cream popcorn).
- **Onboarding:** the prologue's character levels are banked (`WorldState.NightLessons`) and paid
  at dawn as "What the night taught you" (`Journey.Douse`, `Prologue.Douse`).
- **Death poses:** `CrowdView.DeathOf` picks die/die2/die3 by seed, never the nearest body's pose;
  animation's v11 bake (`worktree-agent-a435f4dd0ac80df75@8b2b54f`) is not merged yet.
- **Frozen and burning** keep the body's value; ice and fire live at the rim and top (agreed with
  skills; theirs to judge on its Hoarfrost ring).
- **The 40%:** `WorldState.TimeIn` books play time by prologue/town/wild/story night/table
  night/map; `Journey.StoryShare`; the `--log` run prints it each minute. Estimate from content in
  the status page.
- **The maps' shape:** decided in the audit's structure section; combat has taken the numbers.
- **The night re-measured** (96 nights): danger peaks at the landmarks but the run-ups are the
  calmest stretches (7–10: 5%, 17–20: 3%, 25–28: 2% of runs under half health). Combat has taken
  the brief (signed champions twice, pincer charges, ranged and aura kinds while Building).

## Next, in order

1. **Judge in play once merged:** skills' fixes (the pyre square, the Hallowed Ground's glow,
   hostile marks as hatch and edge, damage numbers S-13 at most about 12 up), animation's death
   poses (30 bodies, no neighbours alike), arena art's places (the barrow near-black: its successor
   is briefed), combat's run-ups (re-run the stretch table: target 10–20% under half in each
   run-up, wins within two points of 93%) and maps (median clear 9–10 min at tiers 1–2).
2. **Stage the map's strongbox and ruler's fall:** combat appends `ChestItemKind.Gear`; give it a
   colour and detail in `ChestCeremony.ColourOf/DetailOf`, and a smaller fall for maps.
3. **A whole night at full resolution** on the autopilot (it now watches chests and leaves
   results): judge the swell, the evolution, the chest in context. The chest's frames are tagged
   (`NAME_chest_N`, `NAME_evolve_N`).
4. **The table and the result as the hub loop** (audit finding 5): with UI design, what a night
   pays, said before and after.
5. **The rest of the feel list:** S-15 (loot by rarity), S-16 (the end screen's story, UI),
   S-18 (a score that follows success), S-19 (a readability layer).

## Decisions (with why)

- **The chest is staged in the world:** the owner says full pages are often not the best choice;
  the world held round her keeps the night's place and stakes.
- **A chest is worth 1.4 things on average, as before:** the jackpot changes, not the night's price.
- **The fall is the only screen-filling moment;** a boss's kill adds light and a ring, no blast.
- **A story night needs no way out:** it lets her go by itself.
- **One levelling system at a time:** the ember by night, the character's lessons at dawn.
- **Maps run about ten minutes and dense** (a pack every 13–15 s); length is set by the way.
- **The run-ups' danger is combat's to add:** pacing reshapes the night, never re-prices it.

## Failures and why

- **The ceremony's camera never came in:** the follow camera eases its distance over about two
  seconds, so the ceremony sets `cam.Distance` itself for the first half second.
- **The chest's open mouth read black twice:** first a burnt ground decal printed over it (the
  chest now sits on render layer 2, which decals don't paint), then the seam's iron band, a solid
  slab across the whole top, covered the light (the glow now sits above it).
- **Story nights "never ended":** the autopilot closed the result as a screen. Fixed in the
  autopilot; the game was right.
- **Runs while the GPU was shared crawled** (frames of 250–600 ms; game time slowed). `play.py`
  now runs at `--fixed-fps 60` by default.
- **I woke two handed-off agents** (story, crafting) by messaging old ids. Read the roster from the
  integration branch before messaging.

## Gotchas

- **Worktree setup:** `godot/assets` must be a junction to `public/assets` (skip-worktree set);
  copy another worktree's `godot/.godot` and run `--import` (about 15 min of kit reimports).
- **Never commit the `.import` churn** or stray `.uid` files from imports; add files by name.
- **`godot/override.cfg`** (untracked) gives runs their own user folder
  (`SurvivorUnchainedExperience`), so they never touch the owner's saves.
- **The shell guard** refuses heredocs and `cd` chains in some forms: write scripts with the Write
  tool into the scratchpad, and edit with the Edit tool.
- **`G.After` runs in real seconds and waits while the fight is paused**; tests' hosts pass time.
- **Godot `Color * float` scales alpha too.**
- **The log line prints only the zone's first six debug entries.**

## Collaborators (roster in `docs/team/README.md` on the integration branch is current)

- **Combat** `a1d4562f44c7f6feb`: maps (length, breath, event strongbox, atlas biases) and the
  run-ups' danger, both taken; tier 3 at 87/71 (greedy/random).
- **Skills** `a63cd93fc73d5ed79`: marks, grounds and S-13 built on its branch; frozen and burning
  lines in `vat.gdshaderinc` are ours.
- **Animation** `a435f4dd0ac80df75`: die2/die3 baked (v11), our pick wired.
- **Arena art** `a26767f7f9955cb56`: briefed on the barrow's near-black ground.
- **UI design** `a69858664f1d3dd29`: a map's result page and the atlas.
- **Crafting** (successor to `a97e32948c5bf419d`): chart verbs as choices of risk.
- **Story** `a73ca9d35d0c487a9`: the strings used ("The night lets you go", "What the night taught
  you") fit the canon.

## Files to read first

1. `docs/EXPERIENCE_AUDIT.md` (the structure and the maps' shape) and `docs/feel/SUGGESTIONS.md`.
2. `godot/src/Game/ChestCeremony.cs`, `GameMenus.cs` (UpdateChest), `WorldScene.cs` (Hold, Slow,
   the buffers, Weigh), `FollowCamera.cs` (Kick), `Haptics.cs`.
3. `godot/logic/Play/Zones/ArenaRun.cs` (Victory, OnPickup, Frame) and `ArenaPacing.cs`.
4. `godot/src/Audio/Sfx.cs` (the chest's sounds, the ladder, the swell) and `SoundBridge.cs`.
5. The scratchpad's `experience/`: `play.py` (fixed fps), `sheet.py`, `tsheet.py`, `crop.py`,
   `keep.py`, `spec.py` (a `--wav` spectrogram), `arc.py`/`compare.py` (balance sweeps),
   `words.py`. Examples: `--zone arena --people dead --chest 1,3,5! --auto idle` (the chest);
   `--story --minute 19.95 --give "<late build>" --on boss --until 150` (a story night's end);
   balance: `arena --callings all --policies greedy,random --seeds 4 --tiers 1,2,3 --people all
   --oaths table --level tier --bot deft --cap 34 --par 8`.
