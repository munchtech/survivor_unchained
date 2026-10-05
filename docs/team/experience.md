# Experience: the game as a player lives it

Status page for the gameplay experience director (agent `ab406cf9ddd22b03b`, branch
`worktree-agent-ab406cf9ddd22b03b`; successor to `ad1f5623590e09883`). The audit is
`docs/EXPERIENCE_AUDIT.md`; evidence frames are in `docs/experience/`.

## Current state (2026-10-04)

Took over from `ad1f5623590e09883`. Tests green (661). The owner approved the story nights and the
day's clock (`docs/design/STORY_NIGHTS_AND_TIME.md`, decisions at its top). **Limit for now: no
Godot or GPU**, code and `dotnet test` only.

**Built (`d95946c5` and after), not yet seen in a run:**
- **The day's clock** (`World/DayClock.cs`, `Play/Journey.Day.cs`, `Game/GameClock.cs`):
  - 12 minutes of free play from dawn to night (dawn 1, day 9, dusk 2), then 6 of night;
  - free play is the town or the Verge with nothing over it: no page, talk, draft, chest,
    cinematic, travel, pause or captured controls; never in arenas or the prologue;
  - day 1 waits until `beasts` or `caravan` is in the journal (story's call).
- **Dusk:** the light blends over a minute; in town the gate guard's evening call; anywhere, the
  night's line (`Journey.DayLines`, story's drafts).
- **Nightfall:** "Night" with the called fight's place; a "Tonight" entry above the objectives;
  hold Answer (N, pad L3, rebindable) to be pulled to the called story fight, else the nearest
  scar in the Verge, else the Wayfinder's table. A fight is called only once the story has pointed
  her at it (`StoryFights.Called`: the bounty, the Roost found; the Dig and the vault always).
- **A night left alone** passes at 6 minutes (nudge at 3): fade, a day on, no inn's rest.
- **The skips:** the inn's sleep (next morning, healed) and "wait for nightfall" set the clock.
- **Back from a fight:** the same night with at least 3 minutes left (several fights by intent).
- **A story fight lost** (`ArenaResult.WakesInTown`): she wakes on Chid's bench in the shrine a
  day on, healed (`Journey.WakeAfterLoss` calls story's `CarriedHome`); Chid's conversation tells
  the waking for that fight, then the town's morning lines.
- **Story's final words** in `Journey.DayLines`; a rise counted (`RiseLine`, story.rises); a
  second fight answered the same night says "straight on" (`FoughtTonight`); the night's card
  lists "Also out tonight".
- **StoryFights** (`Play/StoryFights.cs`): the four fights out of the Verge so the night can call
  them from anywhere; the Verge builds its interactables from it.
- **The fall in a story night, staged** (`Game/GameFall.cs`, on combat's `StoryNight`, merged at
  `aa68f38e`): the picture darkens and the world holds; with a rise left, "Get up" (confirm or the
  use key) or "Let the night go" (back), no page; getting up is a short fade to the checkpoint and
  the counted words (`RiseLine`); with none left, the night is lost and its result follows.

**In-game checks owed (when Godot is allowed), all at 1920×1080:**
1. A day run through on the autopilot at `--fixed-fps 60`: the light's blends at 1, 10 and 12
   minutes (no pop, no grade stutter), lamps and shadows at dusk, the HUD's corner.
2. Dusk in town (the call, then the line) and in the Verge (the line only); the night's
   announcement and the "Tonight" entry; Answer from town and from the wood.
3. The night passing: the fade, "Dawn · Day N", the lines, the scars going out in the Verge.
4. A story fight lost: the result, the shrine at dawn, Chid's waking, then the morning lines.
5. Pausing: the clock still in talk, the pack, the map, the shop, the rest page and cutscenes.
7. A fall in the Hollow (`--stage 3` for the boss): the darkening, the two choices (keys and pad),
   the fade to the checkpoint and "You get up."; then a second fall with none left.
6. The Verge at a turn: Maeca and the night packs only change on re-entry (judge if it jars).

**Next:**
1. With combat: the Hollow measures 5 minutes, not 12, and 50–63% dip under half on the way in
   (target 20–35%); combat lengthens the stages (more to do, not more health). The 40% sums wait.
2. The crowd's status read for skills: drafted, unseen, on the side branch
   `experience-status-read@9d5d30e6` (rime in patches, fire in tongues, all status light under 1).
   Today (the predecessor's tint, skills' `scratchpad/vfx/ba_a9_1.png` rows 2 and 5): no longer
   white, but frozen reads as grey bodies and burning as tan ones: the status barely reads. When
   Godot is allowed: import first, then skills' worst case, before and after: `--quick arcanist
   --zone arena --people dead --time night --tier 2 --lab --give hoarfrost:4 --horde 70,8:risen!
   --dist 3 --spread 9 --seconds 2.5 --every 0.08 --count 24` (frames 13–14; `cinderfall:4`,
   frames 21–23). Sheets to whoever holds the skills row (its lead handed off), then merge.
3. Judge the waiting merges in play once Godot is allowed: skills' grounds, marks and numbers,
   animation's death poses, combat's maps and strongbox through the chest ceremony.
4. The run-ups' danger with combat (`a708da2c97bf85c95`): 10–20% of runs under half health in
   7–10, 17–20, 25–28; wins within two points of 93%.

**Worktree:** `godot/assets` is a junction to `public/assets`; `godot/.godot` copied; the import
was stopped at about 1% (rerun `--headless --path godot --import`, about 15 min, before any
picture). Scratchpad tools in `experience/` point here.

## Notes for other areas

- **Story** (`a54dc034ed29f2e02`): its spare choices and lost lines are ported into
  `StoryFights.Spec` (`415e16f3`); edit the story fights' specs there, not in the Verge.
- **Combat** (`a708da2c97bf85c95`): `StoryFall` and `StoryFights` are pushed; `ClockRuns` is
  false by default, so the story-night runtime needs nothing for the clock.

## Decisions (with why)

- **The night calls a story fight only once the story has pointed her at it:** the Pack and the
  Roost stand open from the start, and they are the violent roads; a clock must never push her
  down one unasked.
- **Free play is the world with nothing over it:** the clock never eats talk, reading or menus,
  so a slow reader never loses a night.
- **The light turns over a minute; lamps and the corner turn at once:** a pop reads as a bug, a
  slow change as the world.
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
