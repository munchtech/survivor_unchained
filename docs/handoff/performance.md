# Handoff: performance lead

For a fresh successor. Read `docs/team/README.md` first, then this, then
`docs/team/performance.md` (status) and `docs/PERF_AUDIT.md` (method and numbers).

## The owner's words (via the coordinator)

- "look for any optimizations we may be missing to improve performance - do not sacrifice quality at this time but we can consider it - obviously with the graphic settings we should help performance as is, but audit code and performance with a specialized agent".
- The team bar: "AAA standard", "never settle", "Never claim what you haven't seen". British spelling.

## The brief (in full, condensed)

1. **Measure real play** with the game's own tools. Measure:
   - frame time (mean, 1% and 0.1% lows), CPU against GPU;
   - draw calls, overdraw and shader-compile stutter;
   - memory and C# allocations a frame;
   - load and zone-change times, physics and audio voices.

   Cover the hub, a full arena, a boss and the densest endless. Record exact numbers and how to reproduce them.
2. **Audit:**
   - C# hot paths;
   - Godot usage: the horde (MultiMesh/VAT), culling and LOD, visibility ranges, materials, textures, shadows, GI and fog, particles and overdraw, UI redraws;
   - the heroine's outfits (pieces, faces, hair cards and physics, skinning).
3. **Act:**
   - write `docs/PERF_AUDIT.md`;
   - implement the safe wins (no visible change at default settings) with before/after numbers and tests green;
   - make the graphics settings genuinely helpful, each tier measured, defaults at full quality;
   - anything visible at default settings goes to the main session as a proposal with numbers.
4. Tell each area's owner what you find in their area. Fix things yourself only where they agree, or where the fix is purely technical and invisible.
5. Don't stop to ask. Commit and push at milestones. Hand off past about 500k tokens.

## Done (all on `worktree-agent-a9586a5171413db0b`, merged into the integration branch)

- **Harness:** `--perf NAME` (`godot/src/Perf.cs`). It warms up, then records every frame:
  - wall time;
  - main thread, split into sim, player, crowd, fx, HUD, sound and zone, each with its garbage;
  - renderer CPU and GPU time;
  - draws in the picture, shadows and UI;
  - collections, pipeline compiles, memory;
  - hitches, with what came with them.

  It also prints `perf lap ...` for the steps of building a place, and the first frame's time since launch. Options:
  - `--perf-dump` lists what's in the scene;
  - `--perf-off X,...` takes one thing out to cost it (her, crowd, grass, flora, props, pieces, landmarks, fx, hud, lamps, lampshadows, sunshadows, ssao, volfog, fog, glow, taa, msaa, fxaa);
  - `--quality`, `--scale`, `--prop-cell N` and `--merge-landmarks` override for the run.
- **Runners:**
  - `tools/perf/run.py`: scenarios hub, hub_night, verge, arena_open, arena_mid, boss, herald, dense, endless, endless_dead, horde600 and title. `--builds A=dir,B=dir` alternates kept builds; `--engine` passes engine options. It waits for a quiet GPU and records how busy it was.
  - `tools/perf/sweep.py`: one change per run (off, quality, scale, prop-cell, engine).
- **Safe wins**, with A/B numbers on the status page:
  - the crowd (`VatCrowd`), sparks and smoke, the effect batches and gore send one buffer of what's in use (`Uploads` in `Sparks.cs`);
  - `Palette.OfArt` is cached;
  - ordinal string tests;
  - no per-frame arrays and sets in `BattleFx`;
  - `HerPose` caches its bones;
  - the town's markers are worked out on events (`ZoneRuntime.Touched()`, the story lead's spec, tested);
  - `Voices.Plates` sets its words only when they change.
- **Graphics settings** (`godot/src/Game/Graphics.cs`):
  - high reproduces the project's own settings exactly, and stays the default;
  - medium and low give up SSAO, volumetric fog, softer and fewer shadow cascades, lamp shadows, MSAA, skin SSS, grass density, sparks, crowd shadows, corpses and LOD threshold;
  - new: `Settings.Scale`, the "Upscaling (FSR 2)" settings row.
  - **None of it measured or looked at yet.**
- **Landmark merge** (`Landmarks.Merge`): in, but **off unless `--merge-landmarks`**. Not measured or seen.

## Key numbers (2560x1440, vsync off, optimised C#; GPU shared all the time, so trust CPU)

- **Hub:**
  - about 5,900 shadow draws a frame;
  - renderer CPU about 14 ms, which caps the frame rate;
  - without lamp shadows: 1,873 shadow draws, 7.9 ms;
  - without kit props: 3,196 draws, 6.4 ms.

  The town's lamps cast cube-map shadows by day.
- **Waystation load:** about 15 s, of which props 4.0 s and starting play 8.5 s.
- **First launch:** freezes of up to 1.4 s in the first fight (creature bakes, item photographs, pipelines).
- **Sim bench (CPU):** p95 13.7 ms a tick at 900 foes (the game caps at 380).

## In progress and next, in order

1. **Ribbons.** The skills lead (a8bafe3cd8a229639) handed `Ribbons.cs` to you. Their commit db4e375 is merged into the integration branch.
   - Do: each `Buffer` becomes one surface made once at `Capacity` (9,000 verts, indices at Capacity×3), updated with `RenderingServer.MeshSurfaceUpdateVertexRegion`, `AttributeRegion` and `IndexRegion` (they take spans), with a degenerate tail.
   - Keep: the layout (Vertex, Color, UV, UV2) and the look.
   - Today: `Flush` copies five arrays and remakes the GPU buffers every frame.
   - Message them when it's pushed. The skills lead has since handed off (their branch is at 69cb2af, unchanged in `Ribbons.cs`). Their successor knows from `docs/handoff/skills.md` to tell you before touching that file, so message whoever the roster names for skills.
2. **Finish the stopped sweeps.** The commands are in `scratchpad/perf_sweeps.sh`, recreated below. Run them when the GPU is quiet (overnight was best):
   - `sweep.py hub off her,grass,ssao,volfog`
   - `sweep.py hub prop-cell 48,64,1000`
   - `sweep.py hub engine "--render-thread safe|--render-thread separate"`
   - `sweep.py dense off her,crowd,fx,grass,flora,pieces,sunshadows,ssao,volfog,taa,msaa,hud`
   - `sweep.py dense quality low,medium,high`
   - `sweep.py dense scale quality,balanced,performance`
   - `sweep.py hub quality low,medium`

   All with `--build <optimised build dir>`.
3. **Prop batching.** Choose the square size from `--prop-cell` (estimate: 792 draws a pass at 32 m, 357 at 48 m, about 140 whole-town). It's the same pixels, so change the default in `Dressing.PropCell`.
4. **Lamp shadows by day.** Propose to the main session: shadows only at dusk and night. This is visible, so it's their call. Saves about 4,000 draws and 6 ms of renderer CPU in town.
5. **Landmark merge.** Measure with `--merge-landmarks`. Look at the Waystation and the Verge at full resolution with and without it, then make it the default.
6. **Load times.** Read the new laps (props files loaded and placed; play start: fight, survivor, zone begin, bakes). Then attack them, for example by loading kit pieces once and caching, or doing the work behind the fade. First launch: ship the VAT bakes and item icons pre-made, or warm them at the title.
7. **Quality tiers and FSR.** Measure each, look at each at full resolution, then tune.
8. **The heroine's outfits** are now merged per material by the main session (warden 5 meshes, arcanist 6, ranger 8, reaver 8; generated LODs off). It lands after a cup-fit fix; they'll message you. Measure with `--perf-off her` and A/B.

## Decisions (and why)

- **Measure at 2560x1440 windowed, vsync off.** It's the owner's screen (Ryzen 9 5900X, RTX 5080, 164 Hz monitor); the target is headroom over 164 Hz. The window gets 2560x1421.
- **Optimised C#:** `dotnet build -p:Optimize=true --no-incremental -o <dir>`. The editor binary loads `.godot/mono/temp/bin/Debug`, which is unoptimised by default and overstates C# costs.
- **Builds go to scratch folders, never straight to `bin`.** Each run copies the build it wants (`--builds`), so A/B is interleaved and a rebuild never lands mid-battery.
- **Own user folder.** `godot/override.cfg` (not committed) sets `custom_user_dir_name="SurvivorUnchainedPerf"`, so runs never touch the owner's saves or settings. This also gives cold-start measurements.
- **Invisible-only changes at default settings.** Anything visible goes to its owner as a proposal.

## Failures and why

- **The GPU was never ours.** Other sessions' games and ComfyUI kept it 40–100% busy with up to 15 GB of VRAM taken, so GPU times and lows are noise. The runner's "wait for quiet" mostly timed out.
- **A Verge run hung past its timeout.** The runner now kills its own game on timeout.
- **The `endless` scenario is not endless.** `--minute 45` without the boss killed froze the arena (the clock and kills stood still). Use `dense` (27:30, cap 320) for the densest fight. Combat was told.
- **The sandbox refuses** `cd` into another folder followed by `git`, and complex heredocs with git. Run git from the worktree root with plain commands.

## Gotchas

- **`godot/assets` must be a junction:**
  `Remove-Item godot\assets; cmd /c mklink /J godot\assets public\assets; git update-index --skip-worktree godot/assets`
- **Import.** Copying the main checkout's `godot/.godot` (1.7 GB) saves most of the 14-minute first import. Re-import (`--headless --path godot --import`, about 30 s) after merges that bring art.
- **Never commit `.import` changes.** The import rewrites hundreds of them (only CRLF). Add files by path.
- **`Performance.Monitor.TimeProcess` is the maximum over a second,** not per frame. The harness times the main thread itself (`Perf.Start` at `int.MinValue` priority).
- **`multimesh_set_buffer` needs the whole `InstanceCount × stride`.** Hence `Uploads` resizes the MultiMesh by powers of two.
- **The drive was at 99%.** Write no large captures. Delete `godot/.shots/perf/*.csv` if space is short.

## Collaborators (roster in `docs/team/README.md`)

| who | what |
|---|---|
| Coordinator | relays the owner; merges branches |
| Main session | heroine outfits (the merge and LOD are theirs); gets lamp-shadow and other visible proposals |
| Skills (a8bafe3cd8a229639) | Ribbons handed to you; their Spikes and shade batches need measuring |
| Combat (ac4ec5bbd2763a0df) | sim p95, crowd view, the endless freeze |
| UI design (ac76f400913a109cd) | the FSR settings row, the globe redraw |
| Animation (a1e3002b800ee55ac) | told about `HerPose` |
| Story | markers spec agreed; done |
| Experience director (a33f58e68e89e3ccf) | asks: no hitches at heralds, the boss, chests, evolutions and the boss's death; a clean Waystation; time to the title. Scenarios `herald`, `boss` and `dense` were made for them |

## Files to read first

- `godot/src/Perf.cs`
- `tools/perf/run.py`
- `tools/perf/sweep.py`
- `godot/src/Game/Graphics.cs`
- `godot/src/Fx/Sparks.cs` (`Uploads`)
- `godot/src/Actors/Vat.cs` (`VatCrowd`)
- `godot/src/World/Landmarks.cs` (`Merge`)
- `godot/src/World/Dressing.cs` (`Props`)
- `godot/src/Fx/Ribbons.cs`
- `docs/PERF_AUDIT.md`
- `docs/team/performance.md`
