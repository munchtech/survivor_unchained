# Performance and rendering

Status page. The last lead was agent a4e0c353e61cca6dc on branch `worktree-agent-a4e0c353e61cca6dc` (wound down 2026-10-10; before it a6a04e32348559b6c, a7afb4d33cdd5efba). **A successor starts from `docs/handoff/performance.md`.** Method and older numbers: `docs/PERF_AUDIT.md`.

## Current state (2026-10-10, on the branch, not merged)

- **Her blur while running:** FSR 2 at native (sharpening off, MSAA off) removes TAA's 50-60 px ghost and keeps 22-26% more of her detail (1440 and 1080). Judged shippable as play's default; the flip in `Graphics.Apply` is the next step, then two gates (a 60 fps fight, wolves' fur).
- **Her hair:** drawn "two" by default: an opaque core at cover 0.5 (depth and motion vectors with its sway) and a blended pass over it, FSR 2's reactive mask erased under it from cover 0.5, lashes, brows and paint erased. In play it matches blended hair's detail with no dotted strands.
- **The Look:** always TAA + MSAA 4x (per view), no depth of field (it caused the side-hair mush). Hair 0.00% flicker, face 0.02%. The core's alpha-to-coverage edge in turned views still needs one fix (handoff Next 2).
- **See-through:** `--see-fix back,norim` removes the pale wedge and arc but cuts a hard circle; a v2 design is in the handoff.

## Measured (164 Hz, cycles 10-13)

| | Look hair / face flicker | her detail running (1440) |
|---|---|---|
| TAA + MSAA, hashed (old default) | 0.02% / 0.05% | 9.58 |
| TAA + MSAA, "two" + A2C, no DOF (new Look) | 0.00% / 0.02% | |
| FSR 2, "two" 0.5 + eraser (new play) | 0.25% / 0.22% | 11.69 |

Sheets: scratchpad `181eef02-...\scratchpad\perf9\c10\` to `c13\` (paths in the handoff).

## Key decisions

- Never Godot's default FSR 2 sharpening at native: it over-sharpens (133%) and doubles the flicker.
- The see-through opens a smaller window for a piece partly in the way, never a fainter one.
- Hair draw \"two\" is the default on the branch (judged); the face lead owns the hair's look and mesh.
- Paired flips (`--perf-flip`) for GPU costs; her detail is never traded; only invisible changes unless the owner or the owning lead agrees.

## Next

1. Play to FSR 2 native; gates: a 60 fps fight, a wolves fight.
2. The Look's A2C hair edge (`ALPHA_TEXTURE_COORDINATE = UV`, core cut 0.9 at the Look).
3. Ground fizz under FSR 2 (arena ground and litter).
4. See-through v2 (opaque, irregular world-space radius, roofs lifted whole).

## Notes for other areas

- **Face (hair):** the blended path's lash cover is the paint's own alpha (+25% per mip far off). Hair shadows are cut at half cover. Blended hair gets no SSAO.
- **Creatures:** fur shells (`fur_shell.gdshader`) are alpha-cut and will crawl under FSR 2; check before the AA changes.
- **Arena art:** the see-through notes are in `docs/team/arena_art.md`.
- **Legal:** re-list the pack before every upload: `python tools/godot/pack_listing.py Windows`.
