# Experience: the game as a player lives it

Status page for the gameplay experience director (agent `ab406cf9ddd22b03b`, branch
`worktree-agent-ab406cf9ddd22b03b`; successor to `ad1f5623590e09883`). The audit is
`docs/EXPERIENCE_AUDIT.md`; evidence frames are in `docs/experience/`.

## Paused for the owner (2026-10-04)

Took over from `ad1f5623590e09883`; merged the integration branch and its last commit
(`4abe07d8`). Tests green (567). No code changed yet. Paused at the owner's request.

- **Worktree setup:** `godot/assets` is a junction to `public/assets` (skip-worktree set);
  `godot/.godot` copied from the old worktree; `override.cfg` in place. The `--import` was stopped
  at about 1%: rerun `--headless --path godot --import` (about 15 min) before any picture.
- **Tools:** the scratchpad's `experience/` scripts now point at this worktree;
  `experience/pending.sh` lists what each lead's branch holds that this one doesn't.
- **Waiting on merges** (not yet on the integration branch): skills `0d2e4a0b` (numbers that sum,
  grounds, marks), animation `d7b091ea` (die2/die3), combat `1b0f8bf1` (maps, strongbox),
  performance `29b5ae5b`. Combat's branch has no run-up danger work yet.
- **Story nights and the day's clock** (the owner's new direction): proposal in
  `docs/design/STORY_NIGHTS_AND_TIME.md` (`1d8e5d92`), waiting on the owner's four choices. Combat
  (`a708da2c97bf85c95`) writes the bosses in `docs/design/STORY_BOSSES.md` to the same frame
  (10–14 min, beats then a 3–4 min boss, ember ×2.5, 50–60 m places). Story and arena art asked
  to agree. Build nothing until the owner approves.
- **Exact next step:** the crowd's status read (skills is waiting). In `shaders/vat.gdshaderinc`,
  burning and frozen still add emission over the knee (burn: rim² 1.2 plus an `up` term, which
  from the 56° camera lights most of a body; glow threshold 1.1), so a crowd blooms cream/white.
  Plan: no full-body tint; fire as flickering tongues and soot only where they lick, ice as rime
  patches darker than a pale body, a thin rim, all emission under about 1.0 so it stays
  saturated. Shoot it first: `play.py frost -- --zone arena --people dead --time night --lab
  --give hoarfrost:6 --horde 70 --dist 5 --spread 7` (and `cinderfall:6`), then change and reshoot.
- **Then:** ask combat (`a1d4562f44c7f6feb`) where the run-ups' danger stands (targets 10–20%
  under half in 7–10, 17–20, 25–28; wins within two points of 93%), and judge each merge as it lands.
- **Do not build on the maps' length** until the owner confirms what "the Wayfinder's maps are
  30" means (the main session is asking).

## Before the pause (predecessor, 2026-10-04)

Merged the integration branch at `f56ee42`. Tests green (567). Pushed. **Handed off:**
`docs/handoff/experience.md` is the successor's brief. Since the list below: S-17 (her blows
lean the camera, arts' hit-stop, a bigger flinch); the chest judged in a real night (its mouth's
light, a softer column, the fan clear of the bars); the night re-measured (the run-ups carry no
danger: briefed to combat, taken).

**Done since the handoff (all seen at 1920×1080):**
- **Verified:** the opening groups (in sight by 6 s), the camera (22 m early, about 31 m at minute
  25), the dead (half value, 8–18 s), the fall, a story night's end. Fixed what the frames showed:
  the boss's own 14 m death blast under the fall, the way out's prompt over her at the peak, the
  title over the flash, chalk-white bones (now old bone, flat, skulls face up), a story night's
  pointless way out and "comes again", the autopilot stranding her after a result, the hit flash
  blooming pale bodies.
- **The chest** (S-09, `ChestCeremony`): staged in the world, not on a page. The world held, the
  edges dark, the camera in; the chest shakes and bursts; reels spin out and stop one by one on
  the D minor ladder; an evolution first in gold; plates, a plaque, home to the bar. 1/3/5 at
  84/12/4% (mean 1.4, as before). Skippable; quicker from the third chest.
- **The evolution** (S-10): the slot crowned, a breath of slow motion, gold light and rings (no
  pink disc). Discoveries are a side toast, not a title across the fight.
- **Sound:** the ember ladder on D minor pentatonic, merged per frame (S-02); the lodestone's
  breath; the level-up landing on major (S-04); the crowd's fall and the swell at 15/40/80/150
  kills in 1.5 s with a camera kick (S-08).
- **Feel:** a 120 ms dash and art buffer (S-05); rumble with a setting (S-14, `Haptics`).
- **The ember carpet:** 240 stones at most; the rest goes into one red hoard stone under a beam.
  Stones keep saturated colours (no cream popcorn).
- **Onboarding:** the prologue's character levels are banked and paid at dawn ("What the night
  taught you").
- **Death poses:** `die`/`die2`/`die3` picked per body, never the nearest body's pose (animation's
  v11 bake is on its branch, not merged yet).
- **The 40%:** `WorldState.TimeIn` books play time by kind; `--log` prints the share a minute.
- **The maps' shape:** decided in the audit's structure section; briefs sent (below).

## The 40%, estimated from the content

Act 1 holds about three hours of story: 15,000 words of dialogue (85 minutes if every branch is
read; about 45 on one path), the Verge's walking and packs (about 50), the prologue (about 8), and
four story nights (80). At 40%, that is about 4.5 hours of table nights and maps: some nine table
nights, about two after each story night. Playtests now measure it (`TimeIn`).

## Next steps, in order

1. **Judge in play once merged:** skills' fixes (the pyre square, the Hallowed Ground, hostile
   marks), animation's death poses, arena art's new grounds and crypt-free places, combat's maps.
2. **Re-run the stretch table** when combat's run-ups land (measured: 7–10 5%, 17–20 3%,
   25–28 2% under half health; target 10–20% each, wins within two points of 93%).
3. **A full night at full resolution** with the autopilot, judging the swell and evolution in
   context (the chest was judged in a real night).
4. **The map's staging** when combat's maps land: the ruler's fall smaller than the night's, the
   strongbox through the chest ceremony (`ChestItemKind.Gear`, combat's).

## Decisions

- **The chest is staged in the world;** a chest is worth 1.4 things on average, as before.
- **The fall is the only screen-filling moment;** a boss's kill adds light and a ring, no blast.
- **A story night needs no way out:** it lets her go by itself.
- **Unconfirmed: "the Wayfinder's maps are 30" read as the table's nights,** making the atlas's
  build maps about ten minutes. The owner is being asked; build on neither reading until then.
- **One levelling system at a time:** the ember by night, the character's lessons at dawn.

## Briefs sent (4 October)

- **Skills** (`a63cd93fc73d5ed79`): items 1–3 done on its branch; damage numbers (S-13) are its to
  build, to my rule (merge per target per 0.25 s, 8 new a frame, crits always).
- **Arena art** (`ab03c3c85571e5085`, handed off): crypt fixed by its new places.
- **Animation** (`a435f4dd0ac80df75`): death poses wired.
- **Combat** (`a1d4562f44c7f6feb`): the maps' numbers (length, the breath before the ruler, the
  event's strongbox, the atlas's first biases).
- **UI design** (`a69858664f1d3dd29`): a map's result page and the atlas.
- **Crafting** (`a97e32948c5bf419d`): chart verbs as choices of risk, against the loop.

## Tools (scratchpad `experience/`)

- `play.py NAME -- [game args]`: a run at 1920×1080, fixed 60 fps (`--real` for wall time).
- `sheet.py`, `tsheet.py`, `crop.py`, `keep.py` (to `docs/experience/`), `spec.py` (a `--wav`
  spectrogram), `words.py` (dialogue words).
- The game: `--story` (a story night), `--chest 1,3,5!` (chests at her feet), `--log` (with stones,
  hoard and the story's share).
