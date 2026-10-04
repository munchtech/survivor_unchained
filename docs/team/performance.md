# Performance

Status page for the performance lead (agent a9586a5171413db0b, branch `worktree-agent-a9586a5171413db0b`).
The audit, with every number and how to reproduce it: `docs/PERF_AUDIT.md`.

## Current state (2026-10-03, stopped at the owner's usage limit)

- **Harness:**
  - `--perf NAME` in the game (`godot/src/Perf.cs`), with `--perf-dump`, `--perf-off`, `--quality`, `--scale` and `--prop-cell`;
  - scenarios and A/B by kept builds: `tools/perf/run.py`.
- **Measured:**
  - a baseline in the hub;
  - 3-second samples of the Verge, the arena (open, 20 min), the boss, endless and a horde of 600;
  - a cold first launch;
  - the sim bench.
  - Headline: **the town is draw-call bound** (renderer CPU 9.9 ms, 6091 shadow draws, 48 fps), and **effects are the largest main-thread cost** (0.6–2.0 ms).
- **Changed (compiles, tests green at 470; the crowd and effects checked in one arena picture against the base build, alike; the before/after is NOT yet measured):**
  - the crowd, sparks, batches and gore are sent to the GPU by buffer, only what is in use;
  - a regex cache for the effects' schools;
  - ordinal string tests;
  - no per-frame arrays and sets in the effects;
  - HerPose looks up its bones once.
- **Graphics settings:**
  - `godot/src/Game/Graphics.cs`: high is exactly the game as it was (the default); medium and low give up more;
  - a new "Upscaling (FSR 2)" row (native, quality, balanced, performance);
  - none of it measured or looked at yet.
- Not done: measuring the heroine in-game; merging props and landmarks; messages to other areas.

## Key decisions

- Measure at the owner's screen (2560x1440, RTX 5080, Ryzen 9 5900X), windowed, vsync off. The target is headroom over 164 Hz.
- Measure an optimised C# build (`-p:Optimize=true --no-incremental`). The shipped game is Release.
- Measured runs get their own user folder (`godot/override.cfg`, not committed), so they never touch the owner's saves.
- The GPU is shared, so compare builds A/B, interleaved (`--builds`), and trust CPU-side numbers over GPU times.
- At default settings, change only what draws the same pixels. Anything visible goes to its owner as a proposal.

## Next

Follow `docs/PERF_AUDIT.md`, "Next":
1. Before/after battery.
2. Attribution with `--perf-off`.
3. Prop square size, then landmark merging.
4. Tune and look at each quality tier.
5. Send findings to their owners.

## Notes for other areas

- **Main session (heroine outfits):**
  - warden is 95 pieces and 727k triangles at about 150 px tall in the arena;
  - proposed: merge by material at build time, a gameplay-distance LOD that keeps full detail up close, and fewer fur shells. Not yet costed in-game.
- **Combat (ac4ec5bbd2763a0df):** the sim bench's p95 at 900 is 13.7 ms a tick (mean 3.0 ms). At 300 it is 3.4 ms.
- **UI (a5629aff0f215ea4a):**
  - a new settings row, "Upscaling (FSR 2)", sits under Picture;
  - the HUD costs 0.15–0.3 ms a frame. The globe redraws every frame.
- **Animation (aa4f5fc266b043035):** `HerPose` now finds its bones once per skeleton. Before, it asked every bone's name each frame. Behaviour is the same.
- **Everyone running the game:** other sessions' runs and ComfyUI kept the GPU 60–100% busy all evening. That makes any frame-time number taken now noisy.
