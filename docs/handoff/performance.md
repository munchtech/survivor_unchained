# Handoff: performance lead

For a fresh successor. Read these first:
- `docs/team/README.md`
- `docs/team/RESUME.md`
- `docs/team/OWNER_NOTES.md`
- then this page;
- then `docs/team/performance.md` (status);
- the method and older numbers are in `docs/PERF_AUDIT.md`.

Written by agent a0eb8c612c94d4aa5 at its context limit, 2026-10-06. Before it: a56abaf3a104be675, then a7145e18b3eb78294.

## The owner's words

- On her in motion: "the pixel blur while running is that intentional or something we can fix?", "we are blurry when moving in active action gameplay." Earlier: "We don't look very smooth while running, a little blurry pixelated." The owner sent zoomed crops of her head while running: smeared and blocky.
- On the trees: "the filter to see through trees and stuff is also a little pedestrian in its pixelation."
- "we still want sex appeal so don't lose that". Her outfits and her detail are never traded for frames. "If a tier must trade, it trades the world, not her."
- "we are striving for perfection." "do not sacrifice quality at this time but we can consider it."
- Medium stays without MSAA: the owner took the main session's recommendation. That question is closed.

## Your brief (from the main session, 2026-10-06), top priority first

1. **Her motion blur.** Find the true cause, then make her crisp in motion at the game camera, without bringing back aliasing on grass and specular.
   - Check:
     - whether her skinned meshes, hair cards, outfit pieces and the crowd write motion vectors;
     - TAA's jitter and history weights;
     - the follow camera's sub-pixel judder;
     - any render scale or FSR.
   - Compare in one A/B batch:
     - motion vectors fixed;
     - TAA off with MSAA 4x and a light post AA;
     - FSR2 at native as the AA.
   - Show the main session before and after crops of her sprinting, at 1080 and 1440, with frame times. Run a strict self-critique at 1:1 first.
2. **The see-through-trees effect.** Replace the pixel dither with something that looks designed: a soft, smooth, round cut-out around her, feathered, stable in motion, no screen-door. Arena art owns the trees; they're paused, so note the change on the status page. It is noted already: show it to them when they're back.
3. Then the status page's "Next".

Working rules:
- Heavy work takes turns: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "performance: <job>" --wait 30`. There are three Godot slots, each needing 5 GB of RAM free, served in a fair queue. Profile only while you hold a turn, and give it back the moment the run ends.
- The GPU is shared: use `--perf-flip` for A/B within one run.
- Batch your shots and look once.
- Run `dotnet test` in `godot/tests` before every commit (762 green at hand-off).
- Commit and push your branch; the main session merges it. Open no PRs.
- Use British spelling.
- Hand off at about 500k tokens of context.

## What I found for the top priority (light reading only; nothing run yet)

- **AA as set:**
  - `project.godot` has `msaa_3d=2` (4x in Godot's count) and `use_taa=true`.
  - `Graphics.Apply` (`src/Game/Graphics.cs`) does `UseTaa = !fsr` and `Msaa3D = fsr ? off : tier.Msaa`. High is MSAA 4x + TAA; Medium is TAA only. FSR2 is opt-in.
- **Prime suspect: TAA ghosting on things whose motion is made in a vertex shader.** Godot's motion vectors come from the previous model matrix and the previous skinning, not from a vertex shader's own displacement. So these will smear under TAA:
  - her hair sway, done in the shader (`HairSway` sets `sway`/`head`/`chain`);
  - her fur shells;
  - (her jiggle is a skeleton modifier, on bones, so its vectors should be right);
  - the VAT crowd: a MultiMesh posed in the vertex shader;
  - grass wind.

  Her skinned body should have correct vectors; verify that. Then check her blend shapes (the face, the figure) and the outfits.
  - Ways to test: `--perf-off taa` exists (Game.cs `--perf-off`), and `--perf-flip` can be extended to flip TAA in one run.
  - Shoot her sprinting with `--auto` and `--shot NAME --every 0.0333 --count 8 --cam 23`. `scratchpad/perf3/her_crop.py` and `her_flicker.py` crop her and map the shimmer.
  - The handoff before this measured TAA/MSAA/FSR shimmer round her when still: High 2, Medium 8, FSR doubles it.
- **The see-through dither** is in `shaders/kit.gdshader`, at the fragment's start:
  - a tunnel from the camera to the survivor;
  - `bayer(FRAGCOORD)` with a 4x4 ordered dither and `discard`, "a fade the temporal AA resolves to translucency".

  So the dither *relies on* TAA: turning TAA off without replacing it shows a bare screen-door. The two tasks are linked; do the cut-out so it needs no TAA.
  - Options:
    - a feathered alpha-blended cut in a depth pre-pass;
    - a screen-space round mask around her projected position, smoothstepped, with a dissolve edge in world space;
    - per-instance fade over time, so it doesn't pop.

    Mind the trees' shadows: a cut tree must still cast its shadow.
  - `shaders/hero_clear.gdshaderinc` (`hero_clear(...)`) clears effects round her. It's another place the same look should match.
  - The global `survivor` vec4 is set each frame in `WorldScene.Draw`.

## Done (this round, on `worktree-agent-a0eb8c612c94d4aa5`)

| commit | what | numbers (optimised C#, 2560x1440) |
|---|---|---|
| 0f81f988 | perf-loads-wip landed: the photoscans' mipmaps and BC7/BC5 (arena art agreed); effects' meshes and Gore's splat made once a session; VAT sweep; `--travel` chains | arena VRAM 2,226 to 1,998 MB; flora 1.5-2.2 to 0.9-1.0 s; second entry's stage 0.5-0.84 to 0.15-0.18 s; 903 MB of old bakes swept |
| 1e824956 | VAT frames skinned with Parallel.For, posed on the main thread; Perf parts events/draft/auto/later and each hitch's GC pause | wolf and boar 1.8-1.9 to 0.44-0.49 s; bytes identical (7 kinds, Debug and optimised) |
| 14ade2e4 | her (and the hero's) body PackedScene held; `Prefetch.Scenes` before the people's first bakes; synth mixes into kept 128-frame buffers; `--perf-allocs`; `--perf-flip fires,lamps,lampshadows,pieces` | her re-entry 0.3-0.5 s to 0; the Risen's bakes 5.1-5.4 to 2.7-2.8 s; garbage 19-30 to 12-16 KB a frame; quit check 0 crashes in 10 |
| 9b9d19d9 | per-frame StringNames made once (hair sway, gaze, reflections, hits, beams, globals, HUD, minimap); `UiArt.Warm()` at start; `--perf-flip labels` | 22-23 to 17-18 KB a frame; GCs 7-8 to 5; GC pause 105 to 67 ms in 40 s; no draft hitch since |
| 018bdbb2 | merged the integration branch (toasts redesigned by UI; my HUD names kept where they still apply) | |

## Measured, worth keeping

- **Her (warden, dense):** 0.71 ms GPU, 0.96M primitives, 32 shadow draws.
- **Loot labels:** about zero.
- **Hollow by Night:**
  - pieces 1.15 ms GPU (1.48M primitives);
  - its fires are unlit at stage 0 and cost nothing measurable;
  - its lamps' shadows are within noise.
- **Arena dumps** (`--perf-dump`):
  - lamplings: 26 shadowed omni lights and 1,340 shadow draws, yet 3.3 ms GPU;
  - pack: 15.4M vertices in the zone.
- **Dense hitches** (now 22-50 ms, rarer):
  - a queued draft rebuilt whole at each pick (`GameMenus.Present`), 15-20 ms;
  - gen-1 GCs, 15-40 ms;
  - the shared GPU (spikes with gpu at 15-65 ms are other sessions).
- **Debug vs optimised C#:**
  - The editor's DLL is `/optimize-`.
  - Dense main thread is about the same (2.6-3.4 ms).
  - Bake skinning gains little: Godot's math structs dominate.

## Decisions (and why)

- **Paired flips for GPU costs:** the GPU is shared, and plain A/B runs swing 2x.
- **No Godot threaded loader:** it crashed on quit. We decode KTX2 on .NET threads (`Prefetch`).
- **Her detail is never traded,** and her textures stay lossless (the face lead's rule).
- **Invisible changes only,** unless the owning lead agrees. Visible ones (the photoscans) are shown to the owner of the look first.
- **Bakes must stay byte-identical** when sped up; compare `user://vat/*.bin` across builds.

## Failures and why

- **`DOTNET_GCgen0size=128 MB`:** one run had a 172 ms pause. It isn't consistent, so it was dropped.
- **Holding the kit's people's PackedScenes:** no gain on a first entry; repeat entries weren't measured, so it was dropped.
- **A `Select-String` filter hid the "done" lines** of some runs. Read the `.json` in `godot/.shots/perf` to be sure.
- **Weekly limit:** I was cut off mid-batch once. Commit at milestones.

## Gotchas

- **The worktree's setup:**
  - `godot/assets` is a junction to `public/assets`, with `git update-index --skip-worktree godot/assets`.
  - `godot/override.cfg` (excluded) sets the perf user folder `SurvivorUnchainedPerf`.
  - Copy `.godot` and the generated `public/assets` `.import` files from an imported worktree (`scratchpad/perf4/copy_imports.py`).
  - Any `--import` takes 1.5-9 min, inside a turn.
- **Merging:** untracked `*.uid` files that Godot generates block merges. Delete the ones git names. Never commit them.
- **Builds:**
  - Keep A/B builds out of the bin: `dotnet build -p:Optimize=true --no-incremental -o <dir>`, then copy `SurvivorUnchained.*` into `godot/.godot/mono/temp/bin/Debug` (or use `run.py --builds a=DIR,b=DIR`).
  - Plain `-p:Optimize=true` without `--no-incremental` silently keeps the old DLL.
- **PowerShell:** variables are case-insensitive. Use long, distinct names in batch scripts.
- **Shots:** `--shot NAME --seconds S --every 0.0333 --count 8 --perf x --perf-warm 1000 --perf-off crowd,fx,hud` takes clean stills.
- **Bakes:** `--vat-fresh --vat-probe --log` re-bakes and prints per-kind times.

## Collaborators

- **Main session / coordinator:** merges; relays the owner; owns her outfits.
- **Arena art** (aba487928a1515c93, paused): owns the trees' look and Hollow by Night. They agreed the photoscan fix.
- **Creatures** (af551cacc6292152f): the boar. 7k VAT vertices, 2K albedo and normal, `VAT_NORMAL` compile-time variant agreed. They will send flips.
- **Skills** (abc6bbe020c7fe287): told about the `BattleFx.Kept` meshes.
- **UI design:** owns the draft panel (it is rebuilt at each pick).
- **The face lead:** her import settings stay (lossless, mipmaps).

## Files to read first

- `godot/src/Game/Graphics.cs` (tiers, AA)
- `godot/project.godot` (rendering)
- `godot/shaders/kit.gdshader` (the see-through dither)
- `godot/shaders/hero_clear.gdshaderinc`
- `godot/src/Actors/HairSway.cs`, `HerJiggle.cs`, `PlayerView.cs`
- `godot/src/Game/Game.cs` (`MeasureWith`: `--perf-flip`, `--perf-off`; `--travel`)
- `godot/src/Perf.cs`
- `tools/perf/run.py`, `tools/perf/flip.py`
- Scratch scripts in `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf4`:
  - `batch1-9.ps1` (turn-wrapped);
  - `gshot.py`, `scan_flicker.py`;
  - `loadprof.ps1`, `prof2.py` (`--from/--to`), `longcalls.py` (the long main-thread calls in a dotnet-trace);
  - `herload.gd`, `stringnames.py`;
  - perf3's `her_crop.py` and `her_flicker.py`.
