# Experience: the game as a player lives it

Status page for the gameplay experience director (agent `a33f58e68e89e3ccf`, branch
`worktree-agent-a33f58e68e89e3ccf`). The audit is `docs/EXPERIENCE_AUDIT.md` (draft two, with the
owner's structure, the music by beat and the plan by owner); evidence frames are in
`docs/experience/`.

## Current state (2026-10-04, handed off past 500k context)

Merged the integration branch at `535bb60`. Tests green (539). Pushed. **Handed off:**
`docs/handoff/experience.md` is the successor's brief.

**Done and in the game:**
- **The night's shape** (`ArenaPacing.cs`): a sawtooth into each landmark, breathers, a herald's
  duel and flood, the hush, and the people's own questions. Combat's charge director follows it.
- **The fall, as the night's peak** (`Ev.Victory`):
  - the world slows to a tenth and eases back over 2.2 s (`WorldScene`);
  - the camera turns to the fall;
  - a layered flash, a pillar and three shockwaves, with no filled disc (`BattleFx`);
  - the fight's sounds duck while the fall's own boom and chord play (`Sfx.Fall`,
    `Synth.DuckSfx`; evolutions duck too);
  - the horde breaks and runs for 3.5 s.

  Seen in frames (`--on boss` now shoots the fall); the filled disc was removed after that, so
  re-shoot it.
- **A story night ends on its beat:** the spoils fly to her at 2.4 s and the night ends at 7 s,
  with its own victory line. Table nights go on into the long night. Combat is making story
  nights 20 minutes on one night clock.
- **The camera breathes:** it opens at 22 m on the survivor and stands back to 31 m as the horde
  grows (5 s smoothing), 33 m for the boss, and up to 34 m in the long night
  (`ArenaRun.CameraDistance`).
- **The night opens with the horde in sight:** three groups at 12–15 m at 1.5 s.
- **The dead:** they darken by half within about a second and cool slightly, and lie 8 s in a
  horde (18 s when few) (`CrowdView`).
- **Gibs:** real bone and skull meshes (knuckled shafts; a cranium with a jaw and dark sockets)
  in old bone, back in the ground after 8–12 s (`Gore.cs`).
- **The town can talk about your nights:** `arena.last.*` facts are listed as StoryLint seeds
  until the story reads them.
- **Not yet seen on screen:** the camera's breathing, the opening groups, the darker dead, the
  new gibs.

**Briefs sent and taken:**
- **combat** (`ac4ec5bbd2763a0df`): 20-minute story nights, story nights skip the long night,
  choice from tier 3, the endgame's two arena kinds;
- **skills** (`a8bafe3cd8a229639`): death blasts 2.9 m, a herald's about 5 m; zones with no fill,
  35% at most, never red or pale grey; ribbons dim over her;
- **arena art** (`ab03c3c85571e5085`): a place and ground per people, darker ground, landmarks
  only at the edges. It asks to be told when the darker dead land, to judge the corpse-against-
  ground value with me;
- **UI** (`ac76f400913a109cd`): one bark at a time, the result as the night's story, the table
  saying what a map pays, pausing only in arenas;
- **story** (now `a035208561a66c171`): reactions to `arena.last.*`, and the wording of the "half
  hour" strings;
- **performance** (`a9586a5171413db0b`): my frame times. It has a `--perf` harness with
  herald, boss and dense scenarios, and finds the Waystation limited by draw calls (about
  6,000 shadow draws, the kit props).

## Next steps, in order

1. **Shoot and judge at full resolution:**
   - the fall again;
   - the camera from 0:00 to 5:00 and at 25:00;
   - the opening groups;
   - the darker dead and the new gibs;
   - a story night's end (`--zone arena` with a story spec, or the Verge's story fight).

   Then tell arena art about the dead.
2. **The chest as a sequence** (S-09; I took UI's backlog item): pause, shake, burst, a reel per
   item landing in turn, 1/3/5 items, skippable. Then the evolution ceremony (S-10), the XP
   ladder (S-02), the multi-kill swell (S-08), the level-up landing on major (S-04), the dash
   buffer (S-05) and rumble (S-14).
3. **The ember carpet:** thousands of uncollected stones litter late nights. Merge them past a
   cap (Vampire Survivors' red gem).
4. **Onboarding:** bank the prologue's character XP and pay it at dawn; prompts that never share a
   spot.
5. **The 40% measured:** journey time by mode (day story, story night, table night, map), and a
   report.
6. **The endgame's shape:** agree the maps' design with combat and crafting.

## Decisions

- **Pacing reshapes the night and never re-prices it.** Danger is combat's.
- **A climax, then a hush.** The long push peaks at 28, then the people draw back for 90 s.
- **The fall is the only screen-filling moment.** A champion's blast is about 3 m, a herald's
  about 5 m.
- **Story nights end on their beat; table nights have the long night.**
- **The camera starts close and stands back.** She is seen early; the fight is seen late.

## Tools (scratchpad `experience/`)

- `play.py NAME -- [game args]`: a run at 1920×1080 with a log.
- `sheet.py`: contact sheets.
- `arc.py` and `compare.py`: the night's arc from balance sweeps.
- `--on boss` takes frames of the fall: `fall_N.png`, 0.25 s apart.
