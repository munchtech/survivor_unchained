# Handoff: the gameplay experience director

For a fresh successor. Read `docs/team/README.md` first (the owner's bar, how we work, the
roster), then this, then `docs/team/experience.md` (the one-page status) and
`docs/EXPERIENCE_AUDIT.md` (the audit and the plan).

## The owner, in their words

- "begin leveling up our whole gameplay experience again".
- The bar: "AAA standard", "strive for excellent, above and beyond", "do we have soul", "I don't
  want to polish, I want to create perfection", "how things are can be limiting".
- Decisions:
  - "endless is truly endless";
  - full-page screens pause the world only in arena combat;
  - final voices are recorded in ElevenLabs, with placeholders until then.
- Structure (4 October): "story should be 40% of the game early on, end game is two types of
  arenas - permanent and our normal arenas. permanent is our arpg build maps like poe and the
  normal arenas are for mindless survivors fun". Story fights are 20 minutes; the Wayfinder's
  maps are 30.
- Music: "i'll work on music at some point". Leave the score; say what it must do at each beat
  (done: the audit's music table).

## The brief

You are the gameplay experience director: the whole experience as a player lives it, from the
title through a run, the hub, the story and many runs. Find what holds it back from the best
of the genre, and raise it.

- **Yours:**
  - game feel and juice;
  - pacing and set pieces;
  - onboarding;
  - the overall loop and meta-progression;
  - the endgame arenas' shape and loop;
  - anything no lead owns.
- **The leads:** hand them short written briefs (what's wrong, the evidence, the target, how
  it's judged) and check their results in play.
- **How:** play with the game's own autopilot and harness, shoot frames at full resolution,
  read the logs. Don't stop to ask: decide, record the reason, and escalate only what needs
  the owner, with a recommendation.
- **Housekeeping:** tests green, British spelling; commit and push at milestones.

## Done (all merged into the integration branch)

- **The audit,** draft two (`docs/EXPERIENCE_AUDIT.md`): ten ranked findings with evidence
  frames (`docs/experience/*.jpg`), the owner's structure, the music by beat, and the plan by
  owner.
- **The night's shape** (`godot/logic/Play/Zones/ArenaPacing.cs`, wired in `ArenaRun.Step`):
  - a sawtooth into 10, 20 and 28;
  - breathers after turns;
  - a herald's duel on a thinned field, then a flood;
  - the hush (28½–30);
  - no turn twice running;
  - a chest in every three turns from minute 8;
  - each people's own question at 6, 17 and 26 minutes, with a tell, led by a captain with a
    chest (`ArenaRun.Signature`, `Column`, `Line`, `RingRise`);
  - `Building` for combat's charge spikes.

  It scales to any night length.
- **The fall as the night's peak** (`Ev.Victory`):
  - slow motion to a tenth, easing back over 2.2 s (`WorldScene`);
  - the camera turned to it (`Ev.Focus`);
  - layered effects with no filled disc (`BattleFx`, case `Ev.Victory`);
  - a sound-effects duck under its own boom and chord (`Synth.DuckSfx`, `Sfx.Fall`; evolutions
    duck too);
  - the horde made to flee for 3.5 s.
- **Story nights end on their beat:** the spoils are pulled in at 2.4 s and the night ends at
  7 s after the fall (`ArenaRun.Victory`).
- **The breathing camera** (`ArenaRun.CameraDistance`, applied in `Game.cs`): 22 m at the start,
  31 m as the horde grows, 33 m for the boss, up to 34 m in the long night.
- **The night opens with the horde in sight:** three groups at 12–15 m at 1.5 s.
- **The dead read as dead** (`CrowdView.DrawCorpses`): darkened by half within about a second,
  lying 8 s in a horde and 18 s when few. Real bone and skull gibs, back in the ground in 8–12 s
  (`Gore.Bone`, `Gore.Skull`).
- **`arena.last.*` facts** for the town to talk about (`Arenas.Finish`). They are StoryLint
  seeds until story lines read them.
- **The autopilot** opens the watch-post chest from its far side (it used to loop on the
  watchman's book); `Game.Prompted`.
- **Tests:** `PacingTests`, plus these in `ArenaTests`:
  - `The_people_ask_their_own_question_with_a_tell_first`;
  - `The_town_can_talk_about_the_last_night`;
  - `The_fall_is_the_peak_and_a_story_night_ends_on_its_beat`;
  - `The_camera_opens_close_and_stands_back_as_the_horde_grows`.

## In progress, and next, in order

1. **Verify at full resolution.** Never seen on screen:
   - the breathing camera (0:00–5:00 and 25:00);
   - the opening groups;
   - the darker dead and the new gibs. Performance's merge moved `CorpseMax` to a public field
     and batched the gibs; check them in frames;
   - the fall since its filled disc was removed;
   - a story night's end.

   Then tell arena art (`ab03c3c85571e5085`) how the dead read against its ground: it asked.
2. **The chest as a sequence** (feel S-09; taken from UI's backlog): the world held, the chest
   shakes and bursts, the items land one by one with a reel and a sound each (1, 3 or 5 items),
   skippable, the ceremony scaled to what is inside. Today `ArenaRun.OnPickup` →
   `LevelUp.OpenChest` → a single announcement line.
3. **Then:**
   - the evolution ceremony (S-10);
   - the XP ladder (S-02; `Sfx.Xp` climbs microtonally and tops out at 24);
   - the multi-kill swell (S-08);
   - the level-up landing on major (S-04);
   - the dash buffer (S-05);
   - rumble (S-14; none exists).

   The specs are in `docs/feel/SUGGESTIONS.md`.
4. **The ember carpet:** late nights leave thousands of uncollected stones (`boss_18.png`
   showed it). Merge them past a cap, as Vampire Survivors' red gem does.
5. **Onboarding:** the prologue pays character XP per kill (`Journey.Killed`), so "LEVEL 3 – a
   new trait (C)" pops up while the ember drafts. Bank it and pay it at dawn as "what the night
   taught you". Also: prompts that never share a spot (the chest and the watchman).
6. **The 40%, measured:** journey time by mode (day story, story night, table night, map),
   reported by the explorer and the harness. Target: 35–45% of Act 1 in the story.
7. **The endgame's shape:** agree the maps' design (the audit's "The structure") with combat and
   crafting before either builds.
8. **Re-measure the night** with combat's charge director and its new kinds and minibosses. The
   build-ups should finally carry danger: at the start 0% of runs dipped below half health in
   the long push.

## Decisions (with why)

- **Pacing reshapes the night and never re-prices it** (average share about 1). Measured: win
  rate 94% and ember 53 at 30:00, before and after. Danger is combat's: the charge director,
  kinds, minibosses.
- **A climax, then a hush,** not one or the other: the long push peaks at 28, then the people
  draw back for 90 s while the sign burns.
- **The people's own turns are set pieces built from existing kinds.** Their timing and tells are
  mine; what spawns in them is combat's as kinds unlock (the agreed split by file).
- **The fall is the only screen-filling moment.** A champion's death blast is about 3 m, a
  herald's about 5 m (agreed with skills).
- **Story nights end on their beat; table nights have the long night** (the story bible §2
  agrees).
- **The camera starts close and stands back:** she is seen early; the fight is seen late.
- **Pausing:** in arenas and on the prologue's night road only; recommended to UI. The code
  pauses on `zone.Combat`, which also catches the Verge by day.

## Failures and why

- **The autopilot looped on the dead watchman's book.** The prompt picks the nearest
  interactable, and the chest's approach point was nearer the watchman. Fixed by approaching
  from the far side and pressing only when `Prompted == "chest"`.
- **The first fall had a flat pink disc** (a `Nova` on the ground) filling the screen under her.
  Removed. Every big moment must be rings and light, never a filled disc.
- **Frame times taken while the GPU was shared were meaningless** (30–136 ms). Use performance's
  `--perf` harness, and quote nothing measured during ComfyUI or voice jobs.
- **A sweep script hung** on a stray `cat > /dev/null` reading stdin. Keep analysis in the
  scratchpad scripts.

## Gotchas

- **A fresh worktree's `godot/assets`** is a text file. Replace it with a junction to the
  worktree's `public/assets` and set `git update-index --skip-worktree godot/assets`. Copying
  another worktree's `godot/.godot` and running `--import` saves most of the import (it still
  re-imports changed paths, about 15 min).
- **Running a Godot import or a game run updates `.import` files** and leaves untracked ones.
  Never commit them.
- **Shell rules:** the Bash tool refuses complex `mkdir`/`cd` chains in this worktree and
  `powershell -Command` strings. Use the Write tool and plain commands; use PowerShell for
  process and GPU checks (`nvidia-smi`).
- **The GPU is shared** (ComfyUI, the voice placeholders, other agents' game windows). Check
  `nvidia-smi` before quoting frame times.
- **StoryLint fails on a fact that is written and never read.** New facts go in `Seeds` until a
  line reads them, and must leave it when one does.
- **`Event(0)`:** with an `Event(Turn)` overload, the literal 0 still binds to `Event(int)`.
- **Fixed-minute tests:** pacing changed when turns come, so tests that waited a fixed time for a
  champion now loop until its bark (from minute 8 one comes in every three turns).

## Collaborators (the roster in `docs/team/README.md` is current)

- **Combat** `ac4ec5bbd2763a0df`:
  - wired into pacing: the charge director, calm in breathers, the hush and the duel, spikes
    while `Building`;
  - building the 20-minute night clock, story nights skipping the long night, kinds, minibosses
    and Signs;
  - sent: choice deciding survival from tier 3 (random drafting wins as often as greedy at tiers
    1–3), and the endgame design.
- **Story** `a035208561a66c171` (successor to `a7622ae77d19e31dc`): **both briefs done**, at
  `worktree-agent-a035208561a66c171@38d4291`, merged at the coordinator's next round.
  - **The town reacts:** 29 barks across 13 people on `arena.last.*`, said that night and the
    morning after, then dropped. A new fact, `arena.last.ago`, starts at 0 and gains 1 each dawn.
    The test is `CinematicTests.The_town_talks_about_the_night_just_past_and_then_lets_it_go`.
  - **Still seeds:** tier, minutes, day and killer.
  - **The "half hour" strings** are worded by the night.
  - **Offer:** they will write the result screen's words (titles, the night's one-line story,
    the Wayfinder's verdict) once you send the slots. Send them with UI's design.
- **UI design** `ac76f400913a109cd`: one bark at a time, the result as the night's story, the
  table saying what a map pays, the pause rule. Character creation comes first for them.
- **Skills (VFX)** `a8bafe3cd8a229639`: zones with no fill, at most 35% coverage, never red or
  pale grey; ribbons dimmed over her; the blast sizes above.
- **Arena art** `ab03c3c85571e5085`: a place and ground per people; darker ground; landmarks
  at the edges; tall pieces that fade whole or stay out of the play space.
- **Performance** `a9586a5171413db0b`:
  - the `--perf` harness, with herald, boss and dense scenarios;
  - the Waystation is draw-call bound (about 6,000 shadow draws from the kit props);
  - load time of 15 s for the Waystation.

## Files to read first

1. `docs/EXPERIENCE_AUDIT.md`: the findings, the structure, the music, the plan.
2. `docs/team/experience.md`: the one-page status.
3. `godot/logic/Play/Zones/ArenaPacing.cs` and `ArenaRun.cs` (Step, Event, Signature, Victory,
   Frame, CameraDistance).
4. `docs/feel/SUGGESTIONS.md`: the specs for the moments still to build.
5. `godot/src/Game/WorldScene.cs` (slow motion, hit-stop), `src/Fx/BattleFx.cs` (the moments'
   effects), `src/Audio/Sfx.cs` and `Synth.cs` (stingers and ducking), `src/Actors/CrowdView.cs`
   and `src/Fx/Gore.cs` (the dead).
6. **The scratchpad's `experience/`:**
   - `play.py NAME -- [game args]`: a game run at 1920×1080 with a log;
   - `sheet.py`: contact sheets;
   - `arc.py` and `compare.py`: the night's arc from `godot/balance` sweeps, in
     `godot/balance/out/exp/*.jsonl`;
   - examples: `--quick warden --sex female --zone arena --people dead --auto --log 30 --every 30
     --count 110` (a full night), and `--minute 29.9 --give "<build>" --on boss --until 150`
     (the boss, and the fall's frames).
