# Skills: how every skill looks, sounds and feels

Status page for the skills lead (a63cd93fc73d5ed79, branch `worktree-agent-a63cd93fc73d5ed79`).

## Current state (2026-10-04, paused for the owner)

Tests green (567). Everything is committed and pushed. No job of mine is running, and ComfyUI is freed.
Sheets sent to the main session: `scratchpad/vfx/ba_nine_*.png`, `ba_a7_*.png`. Newer and not sent
yet: `ba_a9_1.png` (numbers summed, frozen tint), `ba_s6_*.png` (Arcweb, Thunderhead, Verdant Lance,
Reaving Arc, Gale Chakram, Umbral Bolt, Moonbrand).

- **Batch 1 (the nine starting weapons, Hoarfrost, Dawnpulse): remade and seen at full resolution**
  in a packed crowd and in the 9–14 m showcase.
  - Blades: a crescent shader (`shaders/blade.gdshader`, `src/Fx/Blades.cs`). The smear is held low
    (0.55) and saturated; it read as cream on the dark Dig. Not yet seen since that change.
  - Crowd restraint:
    - kill budget of six a frame;
    - flashes share their light;
    - champions falling together are told by the first;
    - sparks and filmed bursts keep her clear (`hero_clear`).
  - Damage numbers (S-13, `src/Fx/Hits.Numbers.cs`):
    - sum per target per 0.25 s beat;
    - at most 8 new a frame;
    - none within 1.5 m of her;
    - damage over time in its school's colour.
- **Batch 2, remade and seen once**:
  - Arcweb is a forking blue bolt;
  - Verdant Lance is a heart with twisting vines and a leaf gather;
  - Reaving Arc is a crimson crescent;
  - Thunderhead has a glow round the bolt, the filmed burst only for the clap, and quiet marks.
  - Trails shortened, not yet seen since: Gale Chakram, Umbral Bolt; Moonbrand's dust made violet.
- **Grounds and telegraphs**:
  - fills premultiplied, so the pyre square is gone;
  - Hallowed's edge thinner;
  - hostile discs and lanes hatched (front edge plus about 30%);
  - "blocked" said once per 0.35 s.
- **Enemy looks** (`src/Fx/BattleFx.Enemies.cs`), built and compiling, **not yet seen**:
  - a rally in the people's colour (it was a white-gold band: the arena lead's "lampling discs");
  - summoning circles (the painted rune ring);
  - slams that throw stone and roll dust;
  - haste lines and ward glints;
  - bolt_bone and frost_orb in flight.
- **GPU done**:
  - 10 Krea sprites;
  - 12 LTX clips, of which 7 are in use: holy_ring, moon_burst, gold_flare, shadow_wisps, bramble_burst,
    leaf_burst and (earlier) the school bursts. The other five were refused by the edge check or set aside
    as poor; see commit 0d2e4a0b.
  - tell_whistle ×2 and tell_fuse ×2. The owner should listen.
  - **tell_horn** (the dead's new tell) is in `sfx_clips.py`, not made: it was interrupted for the pause.

## Next step (exact)

1. Run `bash scratchpad/vfx/batch10.sh` with no other game open. It shoots the Dig, the Kerchiefs, the
   dead and the Pack at minute 25, plus `s7`. Judge the rallies, summons, slams, bolts and orbs, and the
   lamplings on the Dig's clay. Send the arena lead (a26767f7f9955cb56) the Dig crop.
2. Run `bash scratchpad/vfx/gpu_horn.sh` (tell_horn, LTX; it waits for 11 GB of free RAM), then free ComfyUI.
3. Send the main session `ba_a9_1.png` and `ba_s6_*.png` with the batch-10 results.
4. Then: champion Sign marks; Firepot, Iron Palms, Grave Tether, Gravecall, Spirit Herd, Thornbloom and
   Blightfield seen and judged; the evolutions and unions; the arts.

## Grades (now)

1 (poor) to 5 (at the bar), from frames in play. "Before" is in this page's git history.

| Skill | Soul | Reads in a horde | Impact | School | Polish | Crop/square |
|---|---|---|---|---|---|---|
| Oathblade | 4 | 4 | 4 | 4 | 4 | ok |
| Cleaver | 4 | 4 | 4 | 4 | 4 | ok |
| Axe Gyre | 3 | 4 | 3 | 3 | 3 | ok |
| Judgement Disc | 3 | 3 | 3 | 4 | 3 | ok |
| Seeking Motes | 3 | 4 | 3 | 4 | 3 | ok |
| Cinderfall | 3 | 4 | 4 | 4 | 3 | ok |
| Rimeshard | 3 | 4 | 3 | 4 | 3 | ok |
| Volley | 3 | 4 | 3 | 3 | 3 | ok |
| Knifestorm | 3 | 4 | 3 | 3 | 3 | ok |
| Hoarfrost | 4 | 4 | 4 | 4 | 4 | ok |
| Dawnpulse | 3 | 3 | 4 | 4 | 3 | ok |
| Arcweb | 4 | 4 | 4 | 4 | 3 | ok |
| Verdant Lance | 4 | 4 | 3 | 4 | 3 | ok |
| Reaving Arc | 4 | 4 | 4 | 4 | 3 | ok |
| Thunderhead | 3 | 3 | 3 | 4 | 3 | ok |

## Key decisions

- **Hues below the tone curve's knee**: AgX turns coloured light over about 2 to cream. Only thin edges
  and cores are white. Dark grounds raise exposure, so smears are held lower still.
- **A crowd is told by its first few**: deaths, champion falls, flashes and numbers are all budgeted.
- **Dark beds**, in the same pass where possible (premultiplied).
- **Danger keeps its language**, hatched and never solid. A people's colour is for what is theirs.
- **Per skill, not per school**; real shapes where a flat picture fails; painted sprites and filmed clips,
  always through the edge checks.

## Notes for other areas

- **Experience director** (ad1f5623590e09883): frozen and burning are theirs, merged here (3c67542).
  S-13 is built to their rule.
- **Arena art** (a26767f7f9955cb56): the "white-gold lampling discs" were rallies drawn as holy bands;
  now a people-coloured front. Their Dig crop is owed once batch 10 runs.
- **Performance** (a7145e18b3eb78294): Blades is one MultiMesh, at most 48 instances. Ribbons gained only
  the head cap.
- **Anyone running a game in a worktree after a merge**: run `--headless --import` first. A plain run
  does not import new textures, and the ground came out as banded gradients.
