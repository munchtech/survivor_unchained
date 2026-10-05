# Handoff: the gameplay experience director

For a fresh successor. Read `docs/team/README.md` first (the owner's bar, how we work, the roster,
the Godot turn), then this, then `docs/team/experience.md` (the one-page status),
`docs/design/STORY_NIGHTS_AND_TIME.md` (the owner's approved design, decisions at its top) and
`docs/EXPERIENCE_AUDIT.md` (the audit, the night's structure, the music by beat).

## The owner, in their words

- "begin leveling up our whole gameplay experience again"; "AAA standard", "strive for excellent,
  above and beyond", "do we have soul", "I don't want to polish, I want to create perfection",
  "how things are can be limiting"; and now "we are striving for perfection": improved is not
  enough. Before showing anything, ask whether it is the best version of it in any game; root the
  design in how the best games solve it, then make it ours.
- "endless is truly endless"; full pages pause only in arena combat "and are often not the best
  choice"; final voices come from ElevenLabs later.
- Story nights: "much more specialized and fun - smaller arena - and they don't need endless -
  they have proper arpg end bosses right?"
- Time: "time passing should probably happen because some users may not figure out the rest
  mechanic and anotehr way to prompt advancement is worth it, and also just natural."
- Decisions (4 October, in the design doc): losing a story fight wakes her in town a day on
  ("having to die for a time"); Redcowl spared or killed; 12-minute days; a night left alone
  passes; several fights a night if she goes straight on; one rise per story fight in Act 1, none
  later without a rare trait, maps the same ("a balancing nightmare").
- Unconfirmed: what "the Wayfinder's maps are 30" means. Build on neither reading.

## The brief

The whole experience as a player lives it: game feel and juice, pacing and set pieces, onboarding,
the loop and meta-progression, the endgame arenas' shape, anything no lead owns. Brief the leads
in short writing (what's wrong, evidence, target, how it's judged) and check their results in
play. Play with the autopilot and harness, shoot at 1920×1080, read the logs. Commit and push the
branch at milestones (the main session merges; no PRs); `dotnet test` in `godot/tests` before
every commit; British spelling; comments are short prose saying why.

## Done (branch `worktree-agent-ab406cf9ddd22b03b`)

- **The design** for story nights and the day's clock, agreed with story, combat and arena art,
  approved by the owner (`docs/design/STORY_NIGHTS_AND_TIME.md`; combat's half is
  `docs/design/STORY_BOSSES.md`).
- **The day's clock, built and seen** (`World/DayClock.cs`, `Play/Journey.Day.cs`,
  `Game/GameClock.cs`): free play only; light read off the clock; dusk's call and line; nightfall,
  the "Tonight" entry and "Answer the night" (N, pad L3); the Verge's scars and dead at nightfall;
  a night passing; the skips; back into the same night after a fight; story's final words in
  `Journey.DayLines`. Story fights moved to `Play/StoryFights.cs` (called only once the story
  has pointed her at one).
- **Losing a story fight**: the result, Chid's bench at dawn a day on, his waking, the morning
  (`Journey.WakeAfterLoss`, story's `CarriedHome`); no table rematch.
- **The fall in a story night** (`Game/GameFall.cs`, `IZoneHost.StoryFall`): the world darkened
  on its own layer under the HUD, "Get up" or "Let the night go"; a counted rise line.
- **Fixed from frames:** dusk darker than night (now a golden hour), moths drawn a metre across
  (`BillboardKeepScale`), the fall's fade greying its choices, the crowd's status read (rime and
  fire over char, `vat.gdshaderinc`), the struck flare's white capped at four bodies a frame
  (`CrowdView`), the crit's burst (warm gold, three a breath, small at her elbow), the ember
  stones (gems, not popcorn: glow at their colour, not 2.6 times it), every ruler painted with
  the nemesis's orange (now only a true nemesis, `Named.SourceHero`).
- **Evidence** in `docs/experience/`: `dusk_gold_town`, `nightfall_town`, `fall_choices`,
  `frozen_rime`, `burning_char`, `hollow_drive`, `greymuzzle_grey`, `ember_gems`.

## In progress, and next

1. **The Hollow at full resolution** with combat (`afe45df4957917614`). Seen whole on the game's
   autopilot (`scratchpad/experience/merge_runs.sh hollow`): clough 0–2:00, water 2:30–4:50, the
   drive 5:00–11:50, the boss from 11:50; ember about 25 at the boss. The drive was the problem
   ("go through the wolves, never the gap" is against instinct and untaught); combat is fixing it
   (bounded by drives, a first lesson drive, barks). Judge their push at the screen: the drive,
   the deadfalls (no wood or flame yet), the ring, the cold, his lying down and the two prompts,
   the camera at 27 m on the den floor. Frames: `docs/experience/hollow_drive.jpg`.
2. **The screen's noise in the Hollow and late nights:** big salmon hatched hostile discs, the
   warden's white ringed projectiles, damage numbers overlapping in clusters (skills' branch
   `a94ac6b67f1279213@8447124b` has its number fixes, not yet merged here: judge together).
3. **Judge the rest of the landed merges:** combat's maps and the strongbox through the chest
   ceremony (`merge_runs.sh map`; `ChestCeremony.ColourOf/DetailOf` want Gear's rarity colour and
   name); animation's death poses (seen once in the dark, varied; judge in light, 30 bodies).
4. **The run-ups' danger** with combat: 10–20% of runs under half health in 7–10, 17–20, 25–28.
5. **UI design** (`aab47bfdab5955dac`) builds the day dial and the fall's two choices next; judge
   their frames (`--clock 590/710/890/1070`; the fall switches are in the status page).
6. **Still to see on the clock:** a full day on the autopilot for the dawn-to-day turn; Maeca and
   the Verge's day packs change only on re-entry (after a night out in the wood).

## Decisions (with why)

- **The night calls a story fight only once the story has pointed her at it:** the Pack and the
  Roost are the violent roads, open from the start; a clock must never push her down one.
- **Free play is the world with nothing over it;** a slow reader never loses a night.
- **The light is read off the clock, not its turns:** the dark comes before the word "night".
- **One fight a night was overruled:** several, by going straight on (the owner).
- **The Hollow is not padded to 12 minutes:** a tight ten beats a padded twelve.
- **The status read lives at the rim and in patches, under 1:** AgX folds bright hues to white.

## Failures and why

- **Built against the import's stale assembly:** Godot runs `.godot/mono/temp/bin`; building to
  another folder (`-o`) left the game on old code. Always `dotnet build` the game project itself.
- **The disk filled mid-run** and truncated the VAT cache in `%APPDATA%\SurvivorUnchainedExperience\
  vat` (files under 1 MB are broken: delete them and they are rebuilt).
- **Wrong commit ids sent twice** from memory. Quote ids only from command output.

## Gotchas

- **The Godot turn:** `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot
  "experience: <job>"` before any run; `give` straight after. Exit 1 means busy.
- **Merges** abort on untracked `.import`/`.uid` files: list them from the error and delete them
  (`experience/rm_list.py`), never other files.
- **The shell guard** refuses compound git commands, variables in commands and heredoc python
  with computed parts: write scripts to the scratchpad and run them plainly.
- **Shots** by tag: `Shots.Want(tag, s)` only saves while the run lasts (`--every`/`--count`).
- **`--die T1,T2`** fells her at each time; `--choose rise|letgo` answers the fall card.

## Collaborators (roster in `docs/team/README.md` on the integration branch is current)

- **Combat** `afe45df4957917614`: story nights' runtime and bosses; the Roost next.
- **Story** `a7ba8903f4c8261b1`: all the clock's and the fights' words; specs in `StoryFights`.
- **Skills** (successor to `a94ac6b67f1279213`): the crit burst and the struck flare are ours, done;
  Cinderfall's blast, the hostile discs and the projectiles are theirs.
- **UI design** `aab47bfdab5955dac`: the day dial and the fall's choices.
- **Arena art** `a26767f7f9955cb56`: the story places (outline builder).

## Files to read first

1. `docs/design/STORY_NIGHTS_AND_TIME.md`, `docs/team/experience.md`.
2. `godot/src/Game/GameClock.cs`, `GameFall.cs`; `godot/logic/Play/Journey.Day.cs`,
   `StoryFights.cs`; `godot/logic/World/DayClock.cs`.
3. Scratchpad `experience/`: `clock_runs.sh`, `tod.sh`, `status_runs.sh`, `crit_runs.sh`,
   `merge_runs.sh`, `ba.py`, `runlog.py`, `landed.sh`, `play.py`, `tsheet.py`, `crop.py`,
   `keep.py`.
