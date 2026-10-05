# Experience: the game as a player lives it

Status page for the gameplay experience director (agent `ab406cf9ddd22b03b`, branch
`worktree-agent-ab406cf9ddd22b03b`; successor to `ad1f5623590e09883`). The audit is
`docs/EXPERIENCE_AUDIT.md`; evidence frames are in `docs/experience/`.

## Current state (2026-10-04)

Took over from `ad1f5623590e09883`. Tests green (661). The owner approved the story nights and the
day's clock (`docs/design/STORY_NIGHTS_AND_TIME.md`, decisions at its top). Godot allowed again.

**The day's clock, built and seen at 1920×1080** (`World/DayClock.cs`, `Play/Journey.Day.cs`,
`Game/GameClock.cs`, `Game/GameFall.cs`; frames in `docs/experience/`):
- 12 minutes of free play from dawn to night (dawn 1, day 9, dusk 2), then 6 of night; still in
  talk, pages, the draft and chest, cinematics, travel, pause, arenas and the prologue (seen: the
  pack, journal, map and rest page hold it); day 1 waits for `beasts` or `caravan`.
- **The light is read off the clock:** dawn warms into day, day goes gold over dusk's first
  minute, the dark comes in over dusk's last half minute and night's first, so "Night" lands in
  the dark (`dusk_gold_town.jpg`, `nightfall_town.jpg`).
- **Dusk:** the gate guard's call in town, then the night's line; **nightfall:** "Night" with the
  called fight, a "Tonight" entry (with "Also out tonight"), and hold N (pad L3) to answer. Seen:
  answered from town, pulled into the Hollow.
- **The Verge at nightfall:** scars open and the dead rise away from her; they go out at dawn.
- **A night left alone:** nudge at 3 minutes, the fade at 6, "Dawn · Day N", the story's line,
  then the morning's news.
- **A story fight lost:** the result, then Chid's bench at dawn a day on, his waking for that
  fight, then the morning lines. No table rematch: it waits at its place (story's line: "It will
  be there again tomorrow night").
- **The fall** (`fall_choices.jpg`): the world darkens under the HUD; "Get up" or "Let the night
  go"; getting up fades to the checkpoint with the counted words.
- **The crowd's status read** (`frozen_rime.jpg`, `burning_char.jpg`): ice in rime, glossy blue,
  never white; fire as thin orange tongues over char. Sheets sent to skills (`a94ac6b67f1279213`).

**Fixed from the frames:** dusk was darker than night (the Verge went black and red: the sun at
18° grazing the ground at half the light) and is now a golden hour at 34°; the lamps' moths were
drawn a metre across (Godot's particle billboard drops particle scale unless it keeps it), cream
puffballs round every lamp from dusk on; the fall's fade greyed its own choices.

**Next:**
1. With combat (`afe45df4957917614` now): the Hollow measured 5 minutes, not 12, and 50–63% dip
   under half on the way in (target 20–35%); combat lengthens the stages. The 40% sums wait.
2. Judge the waiting merges in play: skills' grounds, marks and numbers, animation's death
   poses, combat's maps and strongbox through the chest ceremony.
3. The run-ups' danger with combat: 10–20% of runs under half health in 7–10, 17–20, 25–28.
4. Still to see: a full day on the autopilot for the dawn-to-day turn and the HUD's corner;
   Maeca and the Verge's day packs still change only on re-entry (dawn after a night out).

**Harness** (`scratchpad/experience/`): `clock_runs.sh dusk|answer|verge|nightout|nudge|fall|
letgo|pauses`, `tod.sh TAG TIME` (the Verge and the town side by side), `status_runs.sh TAG`
(skills' worst case), `ba.py` (before and after crops), `runlog.py NAME` (a run's gist). Game
switches: `--clock S`, `--night ID`, `--answer T`, `--die T1,T2`, `--choose rise|letgo`. After a
code change, `dotnet build` the game project itself (Godot runs `.godot/mono/temp/bin`), not to
another folder.

## Notes for other areas

- **Story** (`a7ba8903f4c8261b1`): the story fights' specs live in `Play/StoryFights.cs`; the
  rematch line change pairs with mine (`8290bfda`).
- **Combat**: `StoryFall` stages the fall; `ClockRuns` is false by default, so the story-night
  runtime needs nothing for the clock.
- **Skills**: `vat.gdshaderinc`'s frozen and burning lines are mine; Cinderfall's own blast
  still blooms cream mid-crowd (theirs).

## Decisions (with why)

- **The night calls a story fight only once the story has pointed her at it:** the Pack and the
  Roost stand open from the start, and they are the violent roads; a clock must never push her
  down one unasked.
- **Free play is the world with nothing over it:** the clock never eats talk, reading or menus,
  so a slow reader never loses a night.
- **The light is read off the clock, not its turns; lamps and the corner turn at once:** a pop
  reads as a bug, a slow change as the world, and the dark must come before the word "night".
- **The chest is staged in the world;** a chest is worth 1.4 things on average, as before.
- **The fall is the only screen-filling moment;** a boss's kill adds light and a ring, no blast.
- **One levelling system at a time:** the ember by night, the character's lessons at dawn.
- **Unconfirmed: "the Wayfinder's maps are 30" read as the table's nights,** making the atlas's
  build maps about ten minutes. The owner is being asked; build on neither reading until then.
- **What came before** (the chest ceremony, the evolution, the ember ladder, the swell, rumble,
  the hoard stone, the night's lessons) is in `docs/handoff/experience.md`.

## Tools (scratchpad `experience/`)

- `play.py NAME -- [game args]`: a run at 1920×1080, fixed 60 fps (`--real` for wall time).
- `sheet.py`, `tsheet.py`, `crop.py`, `keep.py` (to `docs/experience/`), `spec.py` (a `--wav`
  spectrogram), `words.py` (dialogue words), `pending.sh` (what each lead's branch holds).
- The game: `--story` (a story night), `--chest 1,3,5!` (chests at her feet), `--log` (with stones,
  hoard and the story's share).
