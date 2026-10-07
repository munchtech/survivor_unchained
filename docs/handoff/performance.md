# Handoff: performance and rendering lead

For a fresh successor. Read `docs/team/README.md`, `RESUME.md`, `OWNER_NOTES.md`, this page, then `docs/team/performance.md`. Older rounds: git history of this page (4b95fa43, 680f2a0d) and `docs/PERF_AUDIT.md`.

Written by agent a20bdef993e00f26b, 2026-10-06, wound down by the coordinator (usage low). Before it: ad57a6dd0798688d7.

## The owner's words

- "the pixel blur while running is that intentional or something we can fix?", "we are blurry when moving in active action gameplay."
- "the filter to see through trees and stuff is also a little pedestrian in its pixelation."
- "we are striving for perfection." Her detail is never traded for frames.

## The brief

Choose the AA: her crisp at 164 Hz and 1440, no shimmer return, a foundation for the hair pass. Exact motion vectors for her hair. Land the see-through and the crowd's slots.

## What ran (three batches, all at 2560x1440 and 1920x1080, 164 Hz)

Scripts: `tools/scratch/perf6/` (repoint the paths). Pictures (while the scratchpad lasts): `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\` `final/`, `b1/`, `b2/`; the frames themselves are in this worktree's `godot/.shots` (`b3_*`, `b2_*`, `run_*`). Measures: `crops.py sharp|shimmer`, `flick.py` (flicker in motion: |a-2b+c| over aligned ground tiles, medians), `look_noise.py`, `look_where.py`, the face lead's `fair_grain.py` (their venv: `%LOCALAPPDATA%\facefit\.venv`).

| 1440, 164 Hz | her detail running | still: change >12/255 | flicker in motion (hot %) | Look grain s0.8 (1080) | Look hair flicker >8 | dense GPU vs today |
|---|---|---|---|---|---|---|
| TAA + MSAA 4x (today) | 9.55 | 0.00% | 0.83 (0.000) | 0.0126 | 0.02% | 0 |
| none (MSAA alone) | 13.53 | 0.06% | 1.91 (0.065) | 0.0178 | 1.68% | |
| FSR 2 native, sharpening off | 11.78 | 0.04% | 1.22 (0.054) | 0.0174 | 0.83% (0.75% with --coverage) | -0.72 ms |
| FSR 2, Godot's default sharpening 0.2 | 17.99 | 0.27% | 2.40 (0.543) | 0.0252 | 1.40% | -0.6 ms |

- **Godot's TAA is the blur**: a ~50 px ghost of her behind her at a run (crops `final/run_1440_x2.png`), her detail 71% of the unsmoothed render, the Look's finest grain -29%. Its thresholds are fixed in the engine (`taa_resolve.glsl`: 2.5-sigma box at any speed a 164 Hz frame has, 2.5 px velocity test at 1%, an anti-flicker term that slows the blend on her edge). Not fixable from the game.
- **FSR 2 at native, sharpening off** keeps the unsmoothed detail when still, no ghost, crisp VFX and crowd at 1:1, 0.72 ms GPU cheaper. Godot's default sharpening over-sharpens (133% of unsmoothed) and doubles the flicker: never use it at native.
- **But alpha-cut detail crawls under FSR 2**: her hashed hair (0.83% of hair pixels per frame at the Look vs TAA 0.02%), her lashes (alpha to coverage needs MSAA), alpha-tested foliage. A cut moved every frame (`--coverage`: `coverage.gdshaderinc`, `heroine_hair_coverage.gdshader`, `heroine_cards.gdshader`, `Coverage.cs`) fixes the lashes (face flicker 1.22% to 0.42%) but not the hair (0.75%): FSR 2 damps accumulation wherever brightness oscillates.
- Face lead's finding: her skin's scattering, not the AA, was the bigger blur at the Look (they're fixing it on her material, `scatter` ~0.1). Batch 3 shot the Look with `--skinparam scatter=0.1`: `b3_look_*_sc`.

## The AA leaning

FSR 2 at native with sharpening off, at every tier (MSAA off), as the base, once her hair has a technique that holds still under it. Not yet the default: the switches are `--aa fsr2 --fsr-sharpness 2.0 [--coverage]`.

## Done (33e5df80)

- **Hair motion vectors exact**: last frame's swing beside this frame's, chosen in Godot's motion-vector run by its TIME (`MotionClock`, `motion.gdshaderinc`). Verified: with a debug offset only the look-back run moved (`b2/hairmv.png`).
- **See-through**: the dither is gone; a soft round window (merged from `perf-seethrough-wip`). Fixed: Vulkan's flipped projection opened everything in front of her; a piece partly in the way now gets a smaller window, not a fainter one. `--see-through old` removed. Arena art's notes written.
- **Crowd**: each body keeps its slot (merged); a new body's first frame is placed unseen, so its vectors are exact from its first seen frame.
- **Hollow's soft moon** (PCSS 1.2): 0.43 ms GPU at 1440 (`--perf-flip softshadow`).

## Next

1. **Her hair under FSR 2** (with the face lead): try blended cards with a depth prepass (`blend_mix, depth_prepass_alpha`) instead of any cut; measure with `look_noise.py` and `fair_grain.py`. If it holds, make FSR 2 native (sharpening off) plus `--coverage` for brows and lashes the default, and remove the switches.
2. **Foliage under FSR 2**: alpha-tested leaves flicker; test the moving cut or blended edges in `kit.gdshader` (arena art's look).
3. **See-through**: a pale wedge (bottom) and arc (top) still show inside the window behind the Waystation house (`final/see_house.png`): find which pieces (not the kit shader, or the rim pass on a two-sided piece).
4. Rethink the quality tiers once MSAA is gone (Medium's saving was mostly MSAA); measure FSR 2's sharpening for the lower resolution steps.
5. Status page "Next" 2-4 (the draft panel, first bakes, loot beams).

## Gotchas

- Worktree setup: `godot/assets` junction to `public/assets` (skip-worktree), `override.cfg` (perf user folder), `.godot` copied from the main checkout (robocopy), generated `.import`/`.uid` via `copy_imports.py`. Never commit `.import` or `.uid` churn (new files' `.uid` are tracked).
- Shots' `her` place is in the viewport's 1920x1080 units: scale to the picture (`crops.her_at`).
- Phase correlation: the peak sits at minus the shift (numpy's inverse FFT).
- Batch 1's TAA/MSAA references were shot with the see-through bug (trees before her removed); use batch 3's.
- Don't edit shaders while a batch runs (they load from source); don't build either.
- Worktree isolation: no `cd` before git, no heredocs into python, no xargs.

## Collaborators

Main session; face lead aed215ba3ca60cc29 (hair, the Look's grain; told about `--coverage` and the bob and pixie: their UV2 is (0,1) everywhere, so those styles never move); body and outfits afb34c385770877d3; arena art (paused: the see-through and the Hollow's moon are in their notes).

HANDOFF READY: docs/handoff/performance.md on worktree-agent-a20bdef993e00f26b (see the commit below)
