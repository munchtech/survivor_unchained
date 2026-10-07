# Performance and rendering

Status page. The last lead was agent a20bdef993e00f26b on branch `worktree-agent-a20bdef993e00f26b` (wound down 2026-10-06; before it ad57a6dd0798688d7). **A successor starts from `docs/handoff/performance.md`.** Method and older numbers: `docs/PERF_AUDIT.md`.

## Current state (2026-10-06)

- **Her blur while running: found and explained.** The 60 Hz stepping was fixed (bb86717b). What remains is Godot's TAA itself: a ghost of her ~50 px long behind her at a run and her detail at 71% of the unsmoothed picture. Its thresholds are in the engine, not fixable from the game.
- **The AA leaning: FSR 2 at native, sharpening off, MSAA off.** Her detail +23% in motion, no ghost, the Look's skin detail kept whole, VFX and crowd crisp, 0.72 ms GPU cheaper in the dense fight. Not the default yet: her hashed hair crawls under it (0.8% of hair pixels a frame at the Look; TAA 0.02%), and so do alpha-tested leaves. Switches: `--aa fsr2 --fsr-sharpness 2.0 [--coverage]`.
- **Done this round** (33e5df80): her hair's exact motion vectors (verified); the see-through window fixed twice; the crowd's first frames; a prototype cut moved every frame (`--coverage`) that fixes her lashes under FSR 2 but not her hair.

## Measured (1440, 164 Hz)

| | her detail running | flicker in motion | Look hair flicker | dense GPU |
|---|---|---|---|---|
| TAA + MSAA 4x (today) | 9.55 | 0.83 | 0.02% | |
| FSR 2, sharpening off | 11.78 | 1.22 | 0.8% | -0.72 ms |
| none (MSAA alone) | 13.53 | 1.91 | 1.7% | |

Also: the Hollow's soft moon (PCSS 1.2) 0.43 ms GPU; MSAA 4x alone 1.1 ms in the dense fight.

## Key decisions

- Never Godot's default FSR 2 sharpening at native: it over-sharpens (133%) and doubles the flicker.
- The see-through opens a smaller window for a piece partly in the way, never a fainter one (the translucent pass has no SSAO: faint pieces stood pale).
- Paired flips (`--perf-flip`) for GPU costs; her detail never traded; invisible changes only unless the owner or the owning lead agrees.

## Next

1. Her hair under FSR 2 with the face lead (blended cards with a depth prepass), then FSR 2 as the default and the switches gone.
2. Leaves under FSR 2; the pale wedge left inside the see-through window at the Waystation house.
3. Quality tiers without MSAA; FSR 2's sharpening at the lower resolution steps.
4. The draft panel rebuilt at every pick (15-20 ms, UI design's); first bakes (`skeleton_rogue`); loot beams.

## Notes for other areas

- **Face (hair):** the base AA will be temporal and probably FSR 2; Godot's hashed alpha does not hold still under it. Bob and pixie have UV2 (0,1) everywhere, so they never move.
- **Arena art:** see-through and Hollow notes are in `docs/team/arena_art.md`.
- **UI design:** the draft panel is rebuilt whole at every queued pick (`GameMenus.Present`).
- **Legal:** re-list the pack before every upload: `python tools/godot/pack_listing.py Windows`.
