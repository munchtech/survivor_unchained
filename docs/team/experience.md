# Experience: the game as a player lives it

Status page for the gameplay experience director (agent `ad1f5623590e09883`, branch
`worktree-agent-ad1f5623590e09883`; successor to `a33f58e68e89e3ccf`). The audit is
`docs/EXPERIENCE_AUDIT.md`; evidence frames are in `docs/experience/`.

## Current state (2026-10-04)

Merged the integration branch at `f56ee42`. Tests green (567). Pushed.

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
2. **Re-measure the night** with combat's charge director, kinds and minibosses: do the build-ups
   carry danger now? (At the start, no run dipped below half health in the long push.)
3. **A full night at full resolution** with the autopilot, judging the chest, swell and evolution
   as they happen, not staged.
4. **The map's staging** when combat's maps land: the ruler's fall smaller than the night's, the
   strongbox through the chest ceremony (a gear kind).

## Decisions

- **The chest is staged in the world;** a chest is worth 1.4 things on average, as before.
- **The fall is the only screen-filling moment;** a boss's kill adds light and a ring, no blast.
- **A story night needs no way out:** it lets her go by itself.
- **"The Wayfinder's maps are 30" means the table's nights;** the atlas's build maps run about ten
  minutes, dense (a pack every 13–15 s), lengthened or shortened by the way, not the packs.
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
