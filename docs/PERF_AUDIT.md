# Performance audit (first pass, 2026-10-03)

Stopped at the owner's usage limit, part way through. What is below is measured
unless it says otherwise. The before/after for the changes made is still to
be taken (see "Next").

## How it was measured

- **The harness**: `--perf NAME` (`godot/src/Perf.cs`). It warms up, then
  records every frame. For each frame it keeps:
  - wall time;
  - main-thread work, and timed parts of it (sim, player, crowd, fx, HUD, sound, zone);
  - renderer CPU and GPU time (Godot's timestamps);
  - draw calls and objects, split into picture, shadows and UI;
  - C# allocations, GC collections and pipeline compiles.

  It writes `godot/.shots/perf/NAME.json` and `.csv`. Other options:
  - `--perf-dump` lists what is in the scene, by branch;
  - `--perf-off her,crowd,grass,flora,props,pieces,landmarks,fx,hud,lamps,lampshadows,sunshadows,ssao,volfog,fog,glow,taa,msaa,fxaa`
    takes one thing out at a time, to cost it by the difference;
  - `--quality`, `--scale` and `--prop-cell N` override settings for the run.
- **The scenarios**: `python tools/perf/run.py SCENARIO... [--tag T] [--builds A=dir,B=dir]`.
  - The scenarios are hub, hub_night, verge, arena_open, arena_mid (20 min, mid build), boss (29.9 min), endless (45 min, tier 3, late build), endless_dead, horde600 and title.
  - `--builds` runs kept C# builds in turn, so a busy GPU weighs on both alike.
  - It waits for a quiet GPU and records how busy it was.
- **The setup**:
  - the owner's screen size, 2560x1440 (the window gets 2560x1421);
  - vsync off;
  - an optimised C# build: `dotnet build -p:Optimize=true --no-incremental`. Debug JIT overstates C# costs;
  - its own user folder (`godot/override.cfg`, not committed);
  - the editor binary. The export template would be a little faster on the CPU, and no templates are installed.
- **Caveat: the GPU was never ours.** Two or three other sessions' games and a ComfyUI job ran throughout (GPU 60–100% busy before each run, 15 GB of 16 GB VRAM in use). GPU times and wall times are inflated and noisy. CPU-side numbers (main thread, renderer CPU, draw calls, allocations) are reliable.

## Measured

| run | fps | mean ms | 1% / 0.1% low ms | main ms | render CPU ms | GPU ms | draws (picture+shadow+UI) | KB/frame |
|---|---|---|---|---|---|---|---|---|
| hub (Waystation by day), 30 s | 48 | 20.9 | 62 / 128 | 3.29 | **9.88** | 8.0 | 343 + **6091** + 48 | 39 |
| verge (day), 3 s sample | 111 | 9.0 | 13 / 13 | 1.20 | 1.94 | 6.0 | 333 + 1220 + 100 | 38 |
| arena open, 3 s | 140 | 7.2 | 30 / 54 | 1.63 | 1.95 | 3.8 | 237 + 495 + 94 | 27 |
| arena 20 min (212 foes), 3 s | 41 | 24.5 | 50 / 51 | 3.51 | 3.70 | 12.4 | 294 + 440 + 124 | 37 |
| boss, 3 s | 76 | 13.2 | 48 / 66 | 3.66 | 4.29 | 5.8 | 277 + 499 + 136 | 28 |
| endless 45 min, 3 s | 57 | 17.5 | 36 / 37 | 3.10 | 3.66 | 4.1 | 343 + 466 + 143 | 29 |

- **Main thread, by part.** The effects are the largest part everywhere:
  - fx 0.55–2.0 ms (0.67 ms in the hub with nothing happening);
  - crowd 0.3–0.7 ms;
  - sim 0.05–0.3 ms;
  - player 0.2–0.3 ms;
  - HUD 0.15–0.3 ms;
  - zone 0.4 ms in the hub (the Waystation's plates and dialogue markers, each frame).
- **Loading:**
  - Waystation 7.9–9.6 s;
  - Verge 11.1 s;
  - arena 4.2–6.8 s warm, 9.0 s cold;
  - 350–520 pipelines are compiled while each place warms.
- **First launch (an empty user folder), arena:**
  - the 1% low is 317 ms and the 0.1% low 1387 ms over the first 10 s;
  - dozens of 50–250 ms frames, each allocating about 2 MB;
  - the cause is the first-run VAT bakes (307 MB in `user://vat`), the item photographs (`user://icons`) and pipeline compiles. A new player meets all of this.
- **The simulation alone** (`HORDE_BENCH=1`, CPU):

  | horde | ms/tick | p95 |
  |---|---|---|
  | 300 | 0.90 | 3.4 |
  | 600 | 1.29 | 3.7 |
  | 900 | 2.97 | **13.7** |

  It allocates 0.5 KB a tick. The game's own cap is 380 alive, but the p95 spikes are worth finding.
- **The heroine**, from the files:

  | part | pieces (draws per pass) | triangles |
  |---|---|---|
  | warden outfit | 95 | 727k |
  | ranger outfit | 116 | 622k |
  | arcanist outfit | 45 | 442k |
  | reaver outfit | 51 | 381k |
  | body | 7 surfaces (87 blend shapes) | 92k |
  | long hair | 2 | 173k |

  At the arena camera she is about 150 px tall, so about 1M triangles land in about 9,000 pixels, drawn in the depth prepass, the picture and up to 4 shadow cascades. Not yet costed in-game (`--perf-off her` is ready).

## Findings, ranked by gain and risk

1. **The town is draw-call bound (hub: renderer CPU 9.9 ms, 6091 shadow draws).**
   - Kit props are one MultiMesh per (piece, 32 m square, surface). The Waystation has 2283 props of 67 pieces, giving 792 draws per pass. 48 m squares give 357; a whole-town batch about 140.
   - Landmarks add 223 separate meshes (13.7k triangles in all); the Verge's add 788.
   - Each is drawn again in every one of the sun's 4 cascades.
   - Gain: several ms of renderer CPU in the town. Risk: none visible (same pixels).
   - `--prop-cell` is in place to measure 32/48/64/whole; landmark merging by material (leaving the nodes the runtime toggles) is next.
2. **Effects sent their whole capacity to the GPU every frame.**
   - Sparks (6000), smoke (2500) and 14 batches (6580 places): about 1.1 MB copied three times and uploaded each frame, used or not.
   - The crowd made 3 engine calls per creature per frame.
   - Changed (not yet measured): only the places in use are sent, nothing when empty, and one call per kind of creature.
3. **Per-frame garbage and slow lookups in the effects** (changed, not yet measured):
   - an array made per ember on the ground per frame;
   - up to 7 regex matches per projectile per frame (`Palette.OfArt`, now cached);
   - culture-aware `StartsWith` per projectile and per creature;
   - new sets and lists per frame in the ground marks;
   - one engine call per gib per frame (now one buffer per kind);
   - her `HerPose` asking every bone's name each frame (now cached once).
4. **The heroine.** For the main session; quality-safe proposals:
   - **(a) Merge each outfit's pieces by material at build time:** 95 draws become about 5, per pass.
   - **(b) A gameplay-distance LOD** (decimated to about 20–25%). Use visibility ranges or a LOD bias that holds full detail up close, at the title, in creation and in conversations. Godot's own LOD picks by a 1-pixel error, so at the arena camera it would not show.
   - **(c) The fur:** 21 shells as `next_pass` is 21 draws per fur surface per pass.

   Measure (a) to (c) with `--perf-off her` before and after.
5. **First launch.** Ship the VAT bakes and item photographs pre-made in the export (or bake them behind the first load), and warm the pipelines at the title. Gain: no 1.4 s freezes in a new player's first fight.
6. **The simulation's p95 at 900** (13.7 ms ticks). This is for the combat lead (ac4ec5bbd2763a0df). It is beyond the game's cap, but the spikes probably come from area weapons over a dense crowd.
7. **The HUD** redraws its health globe every frame (`Globe._Draw` builds polygons and parses colours). 0.15–0.3 ms; low priority, for the UI lead.

## The graphics settings (built, not yet measured)

- `Settings.Quality` (low/medium/high) is now applied by `godot/src/Game/Graphics.cs`.
- High reproduces the game exactly as it was and stays the default. Each of these values matches the project's setting:
  - SSAO medium;
  - soft shadows medium (sun) and low (lamps);
  - 4 cascades, 4096 shadow atlas;
  - MSAA 2x with TAA;
  - skin SSS low;
  - LOD threshold 1;
  - grass every 0.3 m.
- Medium and low give up, step by step:

  | setting | medium | low |
  |---|---|---|
  | SSAO | low quality | off |
  | volumetric fog | off | off |
  | sun shadow filter | soft low | soft very low, 2 cascades, 2048 atlas |
  | lamp shadows | on | off |
  | MSAA | off | off |
  | skin SSS | low | off |
  | grass cell | 0.36 m | 0.45 m |
  | sparks and smoke | 75% | 50% |
  | crowd shadows | on | off |
  | corpses kept | 110 | 60 |
  | LOD threshold | 1.5 | 2.5 |

- New: `Settings.Scale`, the "Upscaling (FSR 2)" row (native, quality, balanced, performance). It renders the world at 67%, 59% or 50% width and uses FSR 2.2, which replaces TAA and MSAA. The UI stays native.
- Each step still needs measuring and a look at full resolution before it is tuned.

## Next

1. Re-run the baseline battery: `run.py hub verge arena_open arena_mid boss endless horde600 --builds base=...,new=...`. Keep the base build at `scratchpad/dll_base`; rebuild "new" from this branch. The Verge run hung once past its timeout under contention, so check it.
2. Attribution with `--perf-off`, one item at a time, in the hub and arena_mid (her, crowd, grass, flora, props, pieces, landmarks, fx, sunshadows, lampshadows, ssao, volfog, taa, msaa).
3. Pick the prop square size from `--prop-cell` 32/48/64/1000, then merge landmarks by material.
4. Measure and tune each quality tier and scale step, and look at each at 2560x1440.
5. Send the findings to their owners: combat (ac4ec5bbd2763a0df: sim p95, crowd), UI (a5629aff0f215ea4a: globe redraw, settings rows), animation (aa4f5fc266b043035: HerPose change), and the main session (heroine proposals).
