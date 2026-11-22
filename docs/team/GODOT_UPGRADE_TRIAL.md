# Godot 4.5.1 to 4.7.2: the upgrade trial (GAME_PLAN decision 16, package P1), 22 Nov 2026

Branch `godot47-trial` (cut from the integration head 731c2510b). State file: `survivorsunchained_inputs\scratch_godot47\STATE.md`.
The owner, 21 Nov: "we shouldn't be planning on never upgrading our blender or godot as they will continue to update and we don't want to be trapped not updating".

## Verdict

**NOT IN ONE SESSION.** Movement, the build and the tests pass. On a clean, interleaved A/B the den's average frame is 3% faster on 4.7.2, but two things keep the pass test from being met:
1. **Stalls:** 2 of 3 runs on 4.7.2 had a 1.2-1.3 s stall. In both, the renderer's draw phase blocked while new pipelines were compiled. No warm 4.5.1 run had a frame over 74 ms.
2. **Look:** the frame is about 5% darker in the mid tones. It has not been re-tuned.

The upgrade becomes the **first task after the slice**: one lead session of about 150-200k tokens, plus one always-seen judge. Staying on 4.5.1 is not the recommendation. The branch already builds and runs on 4.7.2.

## What broke, file and line

| # | What | Where | State on the branch |
|---|---|---|---|
| 1 | C# build: no errors. One new warning: `AnimationNodeBlendSpace2D.Sync` has been obsolete since 4.6 | `godot/src/Actors/PlayerView.cs:483` | Fixed: `SyncMode = SyncModeEnum.Independent` (the same thing). Warnings are back to 4.5.1's 71 (998106632) |
| 2 | SDK pin | `godot/SurvivorUnchained.csproj:1` | `Godot.NET.Sdk/4.7.2`. The packages restore from the editor's own `GodotSharp\Tools\nupkgs` folder through `godot/NuGet.Config` (no download; the path is this machine's) (2cc2767d3) |
| 3 | Making a new material from a shader costs about 10x more: `new ShaderMaterial { Shader = sh }` takes ~228 ms on 4.7.2 against 12-29 ms on 4.5.1 | `godot/src/Fx/BattleFx.P7.cs:144` (and any shader's first material) | The opening's `ShaderKeep` (`src/View/ShaderKeep.cs`, `GameFront.cs:65,70`) holds and readies every shader behind the card, so a player's start pays it there, not in play. Quick starts (`--quick`, every tool and harness) skip the opening and paid it at every dash: a 465 ms + 240 ms frame pair. `--keep-shaders` (911edebca) runs the hold in a quick start. The card's extra time on 4.7.2 is measured: the hold readies the 165 shaders in **3201 ms on 4.7.2 against 1317 ms on 4.5.1** (+1.9 s, warm disk cache). That cost falls on the opening card. Loading them is 438 against 360 ms. The most costly each, 4.7.2: vat 80 ms, terrain 77 ms, fx_p7 72-74 ms. On 4.5.1: vat 42 ms, terrain 42 ms |
| 4 | Look: the frame is about 5% darker in the mid and bright tones; darks and near-whites are unchanged | the grade (`src/World/Atmosphere.cs:246-262`: AgX, Softlight glow, volumetric fog) | **Not re-tuned (open).** The cause is not isolated. Glow brighter than 4.5.1, as the pages warn, is not what we see: the near-white share is unchanged. Next: frame-matched harness clips with `--perf-off glow` and then `volfog` on both engines (4 takes) to find the stage. Then match it in `Atmosphere.cs` and take one always-seen judge on 1:1 game-camera frames |
| 5 | Render-thread stalls of 1236 and 1341 ms in 2 of 3 warm 4.7.2 den legs, with the shaders held. Main thread ~3 ms; the renderer's draw phase waits while 2 and 24 new pipelines appear. 4.5.1's worst warm frame: 73 ms | the engine's pipeline compile path (no game line found yet; `GameFront.cs` readying frames and `ShaderKeep.Ready` are where a pre-warm would go) | **Open.** Cause not proven (see the perf note under the A/B table). This is the one perf fail |

Checked and not hit:
- The scene format change (no `load_steps`, unique node ids). The headless `--import` on 4.7.2 rewrote no file: no .import, .uid, .tscn or project.godot change. The first editor save will rewrite them. Run Project > Tools > Upgrade Project Files once, in its own commit, when the upgrade merges.
- AnimationPlayer `CurrentAnimation`/`AssignedAnimation` now take StringName (21 and 2 uses) and `Animation.Length` is now a double (about 18 files): all compiled unchanged.
- Input device ids (4.7): no code reads `InputEvent.Device`. The 12-shot harness injects real input events and measured the same on both engines.
- Jolt `WorldBoundaryShape3D`, `SoftBody3D` and the audio area mask: none in the project. The project runs Jolt (`project.godot` `3d/physics_engine`).
- Glow defaults (4.6): `Atmosphere.cs` sets the blend mode, intensity and levels itself, so the new defaults don't reach us.
- The 4.6 default renderer on Windows is D3D12, but both engines ran Vulkan 1.4.351 (the log's first lines).
- `LinearToSRGB` (visual shaders only): there are no visual shaders.
- The pages' warning that canvas lines lose their antialiasing feather: the HUD at 1:1 in the frame-matched clips shows no visible thinning (my own look, half size).
- The runtime is .NET 10.0.10 on both engines (the csproj targets net8.0). The engine logs show the same exit leaks on both: 12 errors and 13 warnings.

## Numbers, both engines (same worktree, same takes, same seed)

Tests (`dotnet test godot/tests`): 3081 passed, 11 skipped on both. The suite is plain logic and references no Godot types, so it cannot catch an engine break.

12-shot movement harness (`--moves12`, all 17 takes, `tools/motion/move_baseline.py`): every number in the table is identical on both engines (`godot/.shots/godot47/TABLE_g45.md` and `TABLE_g47.md`). These are also task 1's numbers. Each frame is a fixed 1/60 s step here, so the harness measures the game's own movement and camera, not the engine's frame pacing.

Den perf trace (`tools/perf/run.py den`: the hollow den, seed 1, from its mouth with its foes, autopilot, 2560x1440 high, vsync off, 15 s warm-up and 40 s recorded, Debug C#). Each set is 4 runs; run 0 is dropped as the shader-cache warm-up. Other Godot runs on the machine: none during the 4.5.1 and 4.7.2 perf blocks.

**Clean A/B with the shader hold (`--keep-shaders`, as a player's start), legs interleaved 4.7.2 / 4.5.1, no other Godot or Blender running before or after any leg** (`tools/scratch/godot47/keep_ab2.sh`, log `godot/.shots/godot47/keep_ab2.log`, 02:36-02:47):

| leg | ms mean | p50 | 1% | 0.1% | max | main | render CPU | GPU | shadow draws | KB/frame |
|---|---|---|---|---|---|---|---|---|---|---|
| 4.7.2 r1 | 9.78 | 9.17 | 52.0 | 310.8 | **1235.9** | 1.84 | 1.91 | 4.45 | 116 | 347 |
| 4.5.1 r1 | 10.01 | 9.89 | 19.2 | 41.1 | 73.4 | 2.06 | 1.71 | 4.37 | 165 | 364 |
| 4.7.2 r2 | 9.79 | 9.19 | 53.0 | 315.4 | **1341.3** | 1.77 | 1.90 | 4.20 | 122 | 345 |
| 4.5.1 r2 | 9.89 | 9.72 | 17.4 | 25.1 | 27.8 | 1.97 | 1.68 | 4.43 | 162 | 360 |
| 4.7.2 r3 | 9.77 | 9.57 | 21.3 | 55.2 | 79.3 | 1.93 | 1.68 | 4.29 | 120 | 355 |
| 4.5.1 r3 | 10.36 | 10.06 | 18.3 | 24.4 | 27.3 | 2.09 | 1.83 | 4.63 | 165 | 372 |
| **mean 4.7.2 / 4.5.1** | **9.78 / 10.09** | 9.31 / 9.89 | 42.1 / 18.3 | 227 / 30 | 886 / 43 | 1.85 / 2.04 | 1.83 / 1.74 | 4.31 / 4.48 | 119 / 164 | 349 / 365 |

My reading of the stalls, not proven: the 1236 and 1341 ms frames are the renderer's draw phase waiting on 2 and 24 new pipelines. That points to pipeline compiles that 4.5.1 hides and 4.7.2 doesn't. A pipeline cache that is still warming on 4.7.2 (fewer runs on it) would also explain it. 4.5.1's own cold first run had a 1031 ms frame. The 4.7.2 r3 leg had none. Both engines' exports bake shaders (`export_presets.cfg` shader_baker). Next: 5 more 4.7.2 legs, then a baked export on each engine.

Earlier runs without the shader hold (quick start, as every tool runs today; nothing else running; `takes_g45.log`, `takes_g47.log`), runs 1-3: 4.5.1 ms 11.29/11.03/10.71, max 81/110/106. 4.7.2 ms 11.13/10.40/9.51, max 2354/480/474. On 4.7.2 every dash made the fx_p7 materials afresh at ~228 ms each (row 3 of the breaks): a 465 + 240 ms frame pair. A first `keep_ab.sh` run (`keep_ab_contaminated.log`) is discarded: other sessions' Godot games were running.

Frame pacing: see the 1% and 0.1% columns. Input latency: not measured. The movie-maker harness has no real-time input, and measuring input-to-photon needs a camera or a latency tool. 4.6 and 4.7 list no change to the input or present path.

## Films (1:1, 1920x1080, 60 fps, the game camera)

- Den with foes, 45 s: `godot/.shots/godot47/film_g45.mp4` (4.5.1), `film_g47.mp4` (4.7.2). The autopilot's play diverges between engines, so these two can't be compared frame for frame.
- Frame-matched (the harness takes are deterministic): `godot/.shots/moves12_g45/<take>/clip.mp4` against `moves12_g47/<take>/clip.mp4`. Side-by-side sheets: `godot/.shots/godot47/cmp_s01/sheet.png` and `cmp_s10a/sheet.png` (`tools/scratch/godot47/compare.py`).

| clip, second | mean luma 4.5.1 / 4.7.2 | brightest tenth | darkest tenth | near-white % | mean abs diff |
|---|---|---|---|---|---|
| s01 0.5 s | 0.1758 / 0.1676 | 0.476 / 0.467 | 0.0478 / 0.0480 | 0.79 / 0.79 | 0.011 |
| s01 2.5 s | 0.1956 / 0.1856 | 0.471 / 0.459 | 0.0429 / 0.0433 | 0.78 / 0.77 | 0.013 |
| s10a 1.6 s (dash) | 0.1847 / 0.1758 | 0.472 / 0.462 | 0.0432 / 0.0434 | 0.89 / 0.89 | 0.012 |

## Recommendation and cost

- **When:** the first task after the slice, before tasks 3 and 5 start (so movement is measured and fixed on one engine), with the breaks above as its list. Merge this branch then; it is not merged now.
- **Cost:** one lead session, about 150-200k tokens:
  - (a) Stalls: more warm 4.7.2 legs, then baked exports on both engines. If the stall persists, a solver on the pipeline compile path: the ubershader setting, `rendering/shader_compiler`, the readying frames in `GameFront.cs`. About 60-80k.
  - (b) Look: find the stage, re-tune `Atmosphere.cs`, one always-seen judge. About 60-80k plus the judge.
  - (c) The opening card's +1.9 s: accept it, or spread `ShaderKeep.Ready` over more frames. Small.
  - (d) Upgrade Project Files once, in its own commit.
- **Kept on the branch for that task:** `--keep-shaders` (tools' quick starts should hold shaders like the real opening). The trial scripts are in `tools/scratch/godot47/`. `move_baseline.py` and its table script now read `MOVES_OUT` and `TURN_LABEL`. The 4.5.1 import churn commit (1ebd656c3: .uid files and filled .import headers) is engine-written: drop it or keep it at merge.
