# Performance and rendering

Status page. The last lead was agent a7afb4d33cdd5efba on branch `worktree-agent-a7afb4d33cdd5efba` (handed off 2026-10-07; before it a20bdef993e00f26b, ad57a6dd0798688d7). **A successor starts from `docs/handoff/performance.md`.** Method and older numbers: `docs/PERF_AUDIT.md`.

## Current state (2026-10-07)

- **Her blur while running: explained, and the cure is measured.** Godot's TAA leaves a ghost of her about 50 px long and keeps 71 to 80% of her detail. FSR 2 at native (sharpening off, MSAA off) keeps 23 to 26% more of her detail in motion with no ghost (cycle 1, 1440 and 1080, 164 Hz).
- **Her hair under FSR 2:** blended cards (`--hair-draw blend`, a switch) replace the hashed speckle with clean strands, and the lashes come out full and soft. They still change 0.4 to 0.7% of hair pixels a frame at the Look, against TAA's 0.02%: FSR 2 treats the blended alpha as reactive. Next: erase the reactive mask there.
- **See-through:** the window works (merged). The pale wedge and arc at the Waystation are pieces in the rim's wide feather (1.45 to 2.5 m), drawn translucent without SSAO. Fixes to try are in the handoff.

## Measured (cycle 1, 164 Hz)

| | her detail running (1440) | ground flicker in motion | Look hair flicker | Look face flicker |
|---|---|---|---|---|
| TAA + MSAA 4x (today) | 9.58 | 0.83 | 0.02% | 0.05% |
| FSR 2 native, hashed hair | 11.80 | 1.22 | 0.83% | 1.22% |
| FSR 2 native, blended hair | 11.73 | 1.22 | 0.43% | 0.68% |

Crops: `docs/team/perf_sheets/c1_run_1440_x2.png`, `c1_look_pony_x2.png`, `c1_look_long_turned.png`, `c1_house_debug.png`.

## Key decisions

- Never Godot's default FSR 2 sharpening at native: it over-sharpens (133%) and doubles the flicker.
- The see-through opens a smaller window for a piece partly in the way, never a fainter one.
- Hair draw is a developer's switch until the face lead and the main session sign it off. The face lead owns the hair's look and mesh (card sort per layer by distance from her scalp, in their hair pass).
- Paired flips (`--perf-flip`) for GPU costs; her detail is never traded; only invisible changes unless the owner or the owning lead agrees.

## Next

1. The reactive mask erased under hair and lashes, then the Look again. Then the AA default (FSR 2 native + blended hair), with the switches retired and the tiers rethought.
2. The pale wedge (narrower feather, back faces cut, or the feather held to its screen width).
3. Alpha-cut surfaces under FSR 2: foliage (`kit.gdshader`), fur (`fur_shell.gdshader`), crowd cut-outs (`vat.gdshaderinc`).
4. FSR 2's sharpening at the lower resolution steps; the draft panel rebuilt at every pick; first bakes; loot beams.

## Notes for other areas

- **Face (hair):** the blended path's lash cover is the paint's own alpha (+25% per mip far off). Hair shadows are cut at half cover. Blended hair gets no SSAO.
- **Creatures:** fur shells (`fur_shell.gdshader`) are alpha-cut and will crawl under FSR 2; check before the AA changes.
- **Arena art:** the see-through notes are in `docs/team/arena_art.md`.
- **Legal:** re-list the pack before every upload: `python tools/godot/pack_listing.py Windows`.
