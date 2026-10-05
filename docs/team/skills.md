# Skills: how every skill looks, sounds and feels

Status page for the skills lead (a94ac6b67f1279213, branch `worktree-agent-a94ac6b67f1279213`).

## Current state (2026-10-04, handed off at the context limit)

Tests green (661). Everything is committed and pushed. No job of mine is running, and ComfyUI is
free of my work. Sheets for the main session are in `scratchpad/vfx/` (listed in the handoff).

- **The main session's three findings, seen at 1920×1080 in a packed crowd:**
  - Damage numbers: **fixed.** Four new a frame, twelve on screen, none laid over one still
    rising (summed per target was not enough: a packed crowd still wore a number on every body).
  - Hoarfrost: **fixed.** The crowd is not white; with the experience director's status look
    (their branch, `a3d42f7d`) frozen bodies read as cold blue.
  - The motes' and the disc's bloom over her: **fixed for what is mine.** Lights lit within
    4 m of her fade (a champion falling at her elbow lit her white); filmed bursts' smoke is
    cleared over her too; a champion's fall is 3 m; the disc is held down as it leaves her
    hand. What is left near her is the experience director's struck flare (a body struck hard
    goes white) and the crit "sparks" burst.
- **The rise is built and seen** (`src/Fx/BattleFx.Rise.cs`, on `Ev.Rise`):
  - the cold: ice at her feet, frost glints on her, the world slowed;
  - Cold, Then Not: a ragged ring of fire runs out as far as it burns (`shaders/fire_ring.gdshader`),
    a band of char with embers behind it, a smouldering ring left (Krea mark `smoulder`);
  - Not Yet: a watch-lamp over her and the watch's hours (Krea, one-frame flipbook `watch_dial`)
    held round her at the waist, turning back;
  - a grace ring at her feet gutters as her untouchable time runs out; its own sound (`Sfx.Rise`).
- **Enemy looks** (batch 10 re-shot as `dig4`, `kerch3`, `dead3`, `pack3`): rallies and summons read.
  Hostile marks were cream rings on the Dig's clay: now held to 0.28 of their old strength (a
  boss's 0.5). Seen at 0.38; 0.28 is not yet seen.
- Her dash is a streak, not a string of pearls (built, not yet seen close). The dry dead's bone
  dust is grey and budgeted (it hung cream clouds over every kill).

## Next step (exact)

1. Shoot `dig5` and the dash (any `--auto` run) to see hostile marks at 0.28 and the dash streak.
2. Gale Chakram: cut `gale_ring_1_1_0.png` (five blades in a ring) and `wind_swirl_2_2_0.png` into
   the sprite array (`fx_sprites.py cut`), import, and draw the chakram as `Body(..., "gale_ring")`.
3. `gpu_horn` when 11 GB of RAM is free (it never was today). ComfyUI's queue had no war horn job.
4. Cinderfall's blast blooms cream round her; Umbral Bolt and Moonbrand read as grey smoke; then
   the rest of the table below.

## Grades (now)

1 (poor) to 5 (at the bar), from frames in play. "Before" is in this page's git history.

| Skill | Soul | Reads in a horde | Impact | School | Polish | Crop/square |
|---|---|---|---|---|---|---|
| Oathblade | 4 | 4 | 4 | 4 | 4 | ok |
| Cleaver | 4 | 4 | 4 | 4 | 4 | ok |
| Axe Gyre | 3 | 4 | 3 | 3 | 3 | ok |
| Judgement Disc | 3 | 3 | 3 | 4 | 3 | ok |
| Seeking Motes | 3 | 4 | 3 | 4 | 3 | ok |
| Cinderfall | 3 | 3 | 4 | 4 | 2 | ok |
| Rimeshard | 3 | 4 | 3 | 4 | 3 | ok |
| Volley | 3 | 4 | 3 | 3 | 3 | ok |
| Knifestorm | 3 | 4 | 3 | 3 | 3 | ok |
| Hoarfrost | 4 | 4 | 4 | 4 | 4 | ok |
| Dawnpulse | 3 | 3 | 4 | 4 | 3 | ok |
| Arcweb | 4 | 4 | 4 | 4 | 3 | ok |
| Verdant Lance | 4 | 4 | 3 | 4 | 3 | ok |
| Reaving Arc | 4 | 4 | 4 | 4 | 3 | ok |
| Thunderhead | 3 | 3 | 3 | 4 | 3 | ok |
| Gale Chakram | 2 | 3 | 2 | 2 | 2 | ok |
| Umbral Bolt | 2 | 2 | 2 | 2 | 2 | ok |
| Moonbrand | 2 | 2 | 2 | 3 | 2 | ok |
| Cold, Then Not (rise) | 4 | 4 | 4 | 4 | 3 | ok |
| Not Yet (rise) | 4 | 3 | 3 | 4 | 3 | ok |

## Key decisions

- **Hues below the tone curve's knee**: AgX turns coloured light over about 2 to cream.
- **A crowd is told by its first few**: deaths, falls, flashes, dust and numbers are budgeted.
- **Nothing lights her but her own moments**: lights fade near her; effects are cleared over her.
- **Danger keeps its language**, hatched and never solid, held near the ground's lit value.
- **Ground marks hide under a packed crowd**: what must be seen is held in the air (the dial).
- **Fire from above is a ragged edge, not torches**: a field shader, not upright sprites.
- **Never a hooked cross**: a four-armed turning blade reads as one. Five blades.

## Notes for other areas

- **Combat** (`a708da2c97bf85c95`): `Ev.Rise` is emitted in `HurtPlayer`'s rise (no mechanics
  changed; `RiseRadius` factored out). Proposal: its fire lands each body as the front reaches it
  (front runs 0.3 s game time) or ~0.15 s after the rise; `Ev.Rise.Delay` is there for it.
- **Experience** (`ab406cf9ddd22b03b`): the status look agrees with my frames. The struck flare
  turns many bodies white at once under one big blow (the rise, Cinderfall): budget its
  whole-body term? `--fall-at T` gives a killing blow for pictures.
- **Arena art** (`a26767f7f9955cb56`): Dig crop sent (`scratchpad/vfx/dig_crop_for_arena.png`).
- **Everyone**: disk C: fell to under 2 GB mid-run today and truncated frames. Old `.shots` folders
  in retired worktrees hold about 15 GB.
