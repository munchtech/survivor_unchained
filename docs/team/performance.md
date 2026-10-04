# Performance

Status page for the performance lead (agent a9586a5171413db0b, branch `worktree-agent-a9586a5171413db0b`).
The audit, with every number and how to reproduce it: `docs/PERF_AUDIT.md`.

## Current state (2026-10-04, stopped at the owner's usage limit)

- **Harness:**
  - in the game: `--perf NAME` (`godot/src/Perf.cs`), with time and garbage per part of the frame, load-time laps (`perf lap ...`) and first frame since launch;
  - runners: `tools/perf/run.py` (scenarios; A/B with kept builds via `--builds`; engine options via `--engine`) and `tools/perf/sweep.py` (one thing changed per run: `off`, `quality`, `scale`, `prop-cell`, `engine`);
  - new scenarios: `dense` (tier 3, 27:30, the 320 cap), `herald` (20:00 arrival) and `boss` (its arrival inside the recording).
- **A/B, base vs optimised effects and crowd** (same merged code otherwise; main thread):

  | scenario | main thread | parts | garbage |
  |---|---|---|---|
  | hub | 5.94 → 4.37 ms | fx 1.08 → 0.13 | |
  | Verge | 1.86 → 0.97 ms | fx 0.79 → 0.09 | |
  | arena at 20 min | 4.01 → 2.91 ms | crowd 1.17 → 0.51, fx 1.73 → 1.40 | 51 → 30 KB/frame |
  | horde 600 | 2.67 → 2.58 ms | | 45 → 23 KB/frame |
  | boss | 2.80 → 2.84 ms | (unchanged) | |

  GPU numbers were swamped by other sessions all night (GPU 40–100% busy, up to 15 GB of VRAM taken); only the CPU side is trustworthy.
- **Hub attribution** (one thing taken out per run; hub ref: renderer CPU 14.1 ms, shadow draws 5893):

  | taken out | shadow draws | renderer CPU |
  |---|---|---|
  | lamp shadows | 1873 | 7.9 ms |
  | props | 3196 | 6.4 ms |
  | sun shadows | 3985 | — |
  | landmarks | 5718 | — |
  | flora, pieces | about the same | — |

  **The town's lamps cast cube-map shadows by day, and that is most of the hub's shadow draws.** The rest of the sweep (her, grass, SSAO, volumetric fog, prop squares, render thread) was stopped part way.
- **Waystation load: about 15 s.**
  - props: 4.0 s
  - play: 8.5 s (the survivor, the folk, bakes)
  - lights and fires: 1.3 s
  - landmarks: 0.6 s
  - flora: 0.5 s
  - Finer laps are now in the code, not yet run.
- **Committed this round:**
  - the town's markers are worked out on events (the story lead's spec, agreed). A conversation ending, something used and a screen closing call `ZoneRuntime.Touched()`; a change in the time of day and a 2 s safety tick also trigger it. The plates set their words only when they change;
  - a new test, `A_marker_clears_the_frame_its_conversation_ends`;
  - the landmark merge (`Landmarks.Merge`) is in, but **off unless `--merge-landmarks`**: not yet measured or looked at. Kit-shader pieces are never merged, because their sway, jitter and foot come from their own model space.

## Key decisions

- Measure at the owner's screen (2560x1440), windowed, vsync off, with an optimised C# build (`-p:Optimize=true --no-incremental`), in a user folder of its own (`godot/override.cfg`, not committed).
- Compare builds A/B, interleaved, and trust CPU-side numbers while the GPU is shared.
- At default settings, change only what draws the same pixels. Anything visible goes to its owner.

## Next

1. **Ribbons `Buffer.Flush`.** The skills lead pushed `worktree-agent-a8bafe3cd8a229639@db4e375` and is keeping out of `Ribbons.cs` for me. Merge that branch, then make each Buffer a single surface at `Capacity` with region updates and a degenerate tail. Keep the layout (Vertex, Color, UV, UV2) and the look.
2. **Finish the sweeps** (`scratchpad/perf_sweeps.sh`: hub off, prop-cell, engine; dense off, quality, scale; hub quality), ideally when the GPU is quiet.
3. **Props.** Choose the square size from `--prop-cell`.
4. **Lamp shadows by day.** Propose to the main session: shadows only at dusk and night, or lamps off by day. That's a visible choice, with a saving of about 4,000 shadow draws and 6 ms of renderer CPU in the town.
5. **Landmark merge.** Measure it with `--merge-landmarks`, look at it at full resolution, then make it default.
6. **Load times.** Run the finer laps, then attack the 4 s props load and the 8.5 s play start.
7. **Quality tiers and FSR.** Measure them and look at each.
8. **Outfit merge and LOD.** Measure the main session's work when it says it's in.

## Notes for other areas

- **Main session:** lamp shadows by day (above). For the heroine, measure with `--perf-off her` once the outfit merge and LOD are in.
- **Skills (a8bafe3cd8a229639):** Ribbons is next for me. Your Spikes and shade batches will go through the harness.
- **Combat (ac4ec5bbd2763a0df):** the crowd view now costs 0.5 ms at 212 foes, down from 1.2. The endless scenario (`--minute 45` without the boss killed) froze: kills and the clock stood still for 30 s. Worth a look.
- **UI (ac76f400913a109cd):** the new "Upscaling (FSR 2)" row is under Picture. `Voices.Plates` no longer rebuilds text each frame. The HUD costs 0.2–0.4 ms and 3 KB of garbage a frame (the globe redraws every frame).
- **Animation (a1e3002b800ee55ac):** `HerPose` caches its bones (told).
