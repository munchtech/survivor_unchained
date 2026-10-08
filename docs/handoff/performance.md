# Handoff: performance and rendering lead

For a fresh successor. Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md`, this page, then `docs/team/performance.md`. **Never Read a whole big file: grep, then `sed -n` the lines.** Older rounds: git history of this page and `docs/PERF_AUDIT.md`.

Written by agent a7afb4d33cdd5efba, 2026-10-07 (handed off at the main session's context check). Before it: a20bdef993e00f26b, ad57a6dd0798688d7.

## The owner's words

- "the pixel blur while running is that intentional or something we can fix?", "we are blurry when moving in active action gameplay."
- "the filter to see through trees and stuff is also a little pedestrian in its pixelation."
- "we are striving for perfection." Her detail is never traded for frames.

## The brief (this wave)

Clarity in motion first. The blur is Godot's TAA (a 50 px ghost). Choose the AA (leaning FSR 2 native, sharpening off, no MSAA), but hashed hair crawls under it, so blended hair cards with a depth prepass come first, designed with the face lead (who owns the hair). Fix the pale wedge in the see-through behind the Waystation. Judge at 1:1 in motion at 2560x1440 and 1920x1080. `perf-seethrough-wip` was already merged (33e5df80 is in the integration branch); the batch re-tests it.

## Done (3adef6a8 code; docs and crops in the commit after it; 775 tests pass)

- **`--hair-draw hash|blend|two`** (`godot/src/Actors/HairDraw.cs`; default unchanged, hashed). blend = `heroine_hair_blend.gdshader` (`blend_mix, depth_prepass_alpha`); two = `heroine_hair_core.gdshader` (opaque, scissor 0.9, writes her depth and motion) with `heroine_hair_over.gdshader` as its next pass (blended). Both add BLEND/CORE/OVER branches at the end of `heroine_hair.gdshaderinc`; shading untouched. Hair shadows are cut at half cover (`IN_SHADOW_PASS`). Lashes are blended to their paint's alpha (`heroine_cards_blend.gdshader`, +25% per mip far off). Priorities: cap 0, hair 1, fine hairs 2. HairSway and the dye set every pass (`HairDraw.Passes`).
- **`--see-debug`** (`KitLook.SeeDebug`, `KitLook.Dump`, called once from `Game.cs`): kit pieces tinted per copy, the window's rim drawn opaque and coloured by how much is kept (blue 0 to red 1), and every mesh in the window printed.

## Cycle 1 (the AA A/B batch, 27 runs, 164 Hz; `tools/scratch/perf7/runs_c1.txt`)

Frames: this worktree's `godot/.shots/c1_*`. Sheets: scratchpad `...\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad\c1\`; the key crops are committed in `docs/team/perf_sheets/c1_*.png`.

| | her detail running 1440 / 1080 | ground flicker in motion (hot %) | still shimmer (>12) | Look hair >8/255 pony / long / pony 1440 | Look face >8 |
|---|---|---|---|---|---|
| TAA + MSAA 4x (today) | 9.58 / 9.07 | 0.83 (0.000) | 0.16 (0.00%) | 0.02% / 0.03% / 0.03% | 0.05% |
| FSR 2 native, hashed hair | 11.80 / | 1.22 (0.054) | | 0.83% | 1.22% |
| FSR 2 native, blend | 11.73 / 11.42 | 1.22 (0.054) | 0.34 (0.04%) | 0.43% / 0.68% / 0.40% | 0.68% |
| FSR 2 native, two | 11.76 / | 1.22 (0.054) | | 0.42% / 0.50% | 0.68% |

Turned 40 degrees, blended hair: 0.15 to 1.44% (long +40 is worst). TAA turned: 0.03 to 0.05%.

- **In motion, FSR 2 wins clearly**: her detail +23% (1440) and +26% (1080), and no ghost. TAA's pale smear trails her in `c1_run_1440_x2.png`. The hair draw doesn't matter in play.
- **At the Look, blended hair is cleaner than hashed**: no speckle, crisp strands, and the hair-to-cheek edge clean where TAA's is dotted (`c1_look_long_turned.png`). Lashes are full and soft, where FSR 2 broke the A2C lashes into dots (`c1_look_pony_x2.png`). No card-order errors I could see at plus or minus 40. "two" is no better than "blend", so drop it.
- **But it still moves frame to frame**: hair 0.4 to 0.7% against TAA's 0.02%. Why: Godot hands FSR 2 the blended alpha as its reactive mask (clamped to 0.9), so FSR 2 shows the hair as the near-raw jittered frame. The side hair against the dark background also reads soft (many faint layers averaged).
- Next idea, untested: **erase the reactive mask where hair and lashes are drawn**, so FSR 2 accumulates them on the velocity of the head behind. One way is a `blend_mul` pass (white, ALPHA 0) after them; check Godot's BLEND_MODE_MUL alpha factors first (not in the fetched files). The other is a POST_TRANSPARENT CompositorEffect scaling the colour alpha, but that would hit VFX too.
- The ground flicker under FSR 2 (0.054% hot) is the alpha-cut foliage and grass (Next 3).

## The pale wedge: diagnosed, not yet fixed

- `--see-debug` (`c1_house_debug.png`: left is the debug, right the final). Every piece in the window is a kit piece (Dump listed nothing else). The window is mostly rim: its feather runs from 1.45 to 2.5 m (42% of the radius), drawn by the blended rim pass (no SSAO, `depth_draw_never`). The wedge (bottom) and arc (top) are pieces inside that band, kept at about 0.6 to 0.95, so nearly opaque but shaded as translucent: pale and flat, maybe an underside or a gable seen from inside. Straight edges in the band mark pieces with a different `open`.
- Fixes to try, each judged with `--see-debug` and then the trees (`c1_trees_fb`): (1) a narrower feather (about 0.35 m, keeping the clear radius); (2) faces seen from behind (`!FRONT_FACING`) cut whole inside the window, with no rim; (3) the feather kept at its nominal width on the screen where `open` varies (`kept = smoothstep(-band, 0, s * min(fwidth(metres) / max(fwidth(s), 1e-5), 8))` with `s = metres - 2.5*open`, computed in fragment).

## Next

1. The reactive eraser for hair and lashes (cycle 1, last bullet), then the Look's numbers again. If they near TAA's: FSR 2 native (sharpening off, MSAA off) plus blended hair becomes the default, the `--aa`, `--fsr-sharpness`, `--coverage` and "two" switches are retired, and the tiers are rethought (Medium's saving was mostly MSAA). Fallback if it can't be held: FSR 2 in play and in cinematics, TAA at the Look's still close-up, applied per view in `Graphics.Apply` (main and owner's call).
2. The wedge fix above.
3. Alpha-cut surfaces left under FSR 2: foliage (`kit.gdshader` scissor), creature fur (`fur_shell.gdshader` discards, the creatures lead's), crowd cut-outs (`vat.gdshaderinc`). Shoot each under FSR 2 at 1:1 in motion.
4. FSR 2's sharpening at the lower resolution steps; status page "Next" 4 (draft panel, first bakes, loot beams).

## Engine facts (Godot 4.5.1 source in the scratchpad's `godot_src/`; fetch with `tools/scratch/perf6/fetch_src.py` and `perf7/fetch_src2.py`)

- FSR 2's reactive mask is the internal colour's alpha, clamped to 0.9. The opaque pass writes alpha 0 and the transparent pass writes the blended alpha, so blended hair is about 0.9 reactive: little history, little ghost.
- The transparent pass writes no motion vectors. `depth_prepass_alpha` writes depth (and normal-roughness) for alpha 0.99 and up in the prepass, and casts shadows for alpha 0.1 and up. Motion vectors of (-1,-1) or below are derived from depth.

## Gotchas

- Worktree setup: `godot/assets` as a junction (PowerShell `New-Item -ItemType Junction`) to the worktree's `public/assets`, then `git update-index --skip-worktree godot/assets`; `godot/override.cfg` (perf user folder, in .gitignore); robocopy `.godot` from the main checkout (2.6 GB, 35 s); `perf7/copy_imports.py`; the first import takes about 4 minutes. Never commit `.import` or others' `.uid` churn.
- Scripts: `tools/scratch/perf7` (batch.ps1 takes the godot turn itself; shoot.py; runs files; sheets_c1.py; box.py). The measures are perf6's (crops, flick, look_noise, look_where, mres), repointed by `perf7/repoint.py`. Use plain `python` (numpy is in the user site, not under `-I`).
- Don't edit shaders or build while a batch runs. Worktree-isolated git: plain commands, no `cd` chains, no loops.

## Collaborators

Main session (reports, owner decisions). Face lead abe65bc929823a791: owns the hair; agreed the switch; won't touch `heroine_hair.gdshaderinc`, `heroine_hair.py` or `People.Hair()` this wave; is changing the lash paint and the "lashes" case (keep the blend in `HairDraw.Cards`); will sort cards per layer by distance from her scalp (inner first) in the hair pass. Animation ae2a9884e3e51609c; outfits a1f120018d8749c97.

HANDOFF READY: docs/handoff/performance.md on worktree-agent-a7afb4d33cdd5efba (code 3adef6a8; this page is in the branch head)
