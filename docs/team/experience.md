# Experience: the game as a player lives it

Status page for the gameplay experience director: agent `a9f0d6c64d891d56d`, branch
`worktree-agent-a9f0d6c64d891d56d`. Successor to `ab406cf9ddd22b03b`, whose knowledge is in
`docs/handoff/experience.md`. The audit is `docs/EXPERIENCE_AUDIT.md`; the approved design for
story nights and the clock is `docs/design/STORY_NIGHTS_AND_TIME.md`. Evidence frames are in
`docs/experience/`.

## Current state (2026-10-05)

**The Hollow, seen whole at 1920×1080** (combat's ea002b1e and arena art's f7c4c43c, both now in
the integration branch), on the autopilot (warden, tier 1):
- **Shape:** 10:00 in all. The clough runs to 1:45, the water to 4:00, the drive to 7:00, then the
  boss to 10:00.
- **Too soft:** her lowest was 193/212, and she was full at every boss sample. Sent to combat
  (`a5115633c7006e4d4`), who agrees and is looking at Greymuzzle.
- **The drive (combat's fix):** the first run is marked longer and said; her first miss and her
  first hit are told; she has seven runs. "SHE IS OPEN" over the pale-blue ring is the stage's best
  beat (`drive_she_is_open.jpg`). Two problems:
  - The first run says four things at once (`drive_four_texts.jpg`).
  - Its lane read as the place's burning edge (`drive_lane_like_the_edge.jpg`).
  Combat has the asks: say the lesson a beat before the lane, and use fewer words.
- **Fixed by me (3019fa2d):**
  - Every hostile lane fills as it comes, and a named move draws at a boss's strength
    (`drive_lane_fills.jpg`).
  - Captions keep out of, and off the line of, the banner's words.
  - A speaker at the top edge has their line under their feet.
  - The strongbox's gear in the chest ceremony: named as its tooltip names it, in its rarity's
    colour, and sent down to where it lies (it said "Coin, and breath back"). Not yet seen in play.
- **Noise, briefed to skills (`abc6bbe020c7fe287`):**
  - Her own Thornbloom/Rotwood rims are the loudest marks at the boss (`boss_own_grounds_loudest.jpg`).
  - Enemy ground in the water is red at 0.6, not violet at the crowd's strength (`water_salmon_zones.jpg`).
  - Move words sit over the HUD's top text.
  - Her thick cream grace ring.

## Next

1. **Maps and the strongbox through the chest ceremony.** Use `judge_runs.sh map` and `box`; the
   game's `--strongbox` puts one at her feet.
2. **The extra death poses by day** (`judge_runs.sh deadday`).
3. **The Hollow again** after combat's Greymuzzle work and skills' noise fixes.
4. **The Roost** once combat has seen it.
5. **UI design (`a4fdbc49786ba8b7f`):** the day dial and the fall's choices, after the Self and
   Pack rework. Judge their frames.
6. **Loot (`a9a9c345a35e1fcad`):**
   - The first Legendary ever is staged through the chest ceremony: the world held, no page. Later
     ones get the pillar, the toll and a toast.
   - Judge a night's drops from their frames.

## Decisions (with why)

- **A named move is drawn at a boss's strength, whoever makes it:** a mechanic the stage teaches
  must never sit at the crowd's 0.28.
- **A hostile lane fills as it comes:** two edges alone read as one more line on the ground. A
  moving front says that it is coming, and when.
- **Words never share a line:** a caption beside the banner reads as one sentence.
- **The first Legendary is held in the world, not paused on a page:** the owner wants full pages
  rarely.
- Earlier decisions are in `docs/handoff/experience.md`.

## Notes for other areas

- **Combat:** `--stage N` starts her at ember 1, so stage-skip runs can't judge a stage's length
  or danger. Please hand her the floor build there.
- **Skills:** `GameHud.TopClear` and `GameHud.Banner` are there for anything drawn over the
  world near the top or the banner.

## Tools (scratchpad `experience/`)

- `play.py NAME -- [game args]`: a run at 1920×1080, fixed 60 fps.
- `judge_runs.sh drive|hollow|map|box|dead|deadday`: this lead's runs.
- `sheet.py`, `crop.py`, `keep.py` (frames to `docs/experience/`), `runlog.py`.
- `branches.py` (what each lead's branch holds beyond ours), `contains.py`.
- `wait_turn.py` (waits for a turn, then takes it), `wait_for.py`.
- **Gotcha:** a fresh worktree checks `godot/assets` out as a stub file. Replace it with a junction
  to `public/assets`, mark it `git update-index --assume-unchanged godot/assets`, then run
  `--headless --import`.
