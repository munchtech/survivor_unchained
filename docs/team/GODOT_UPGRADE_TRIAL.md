# Godot 4.5.1 to 4.7.2: the upgrade trial (GAME_PLAN decision 16, package P1), 22 Nov 2026

Branch `godot47-trial` (cut from the integration head 731c2510b). State file: `survivorsunchained_inputs\scratch_godot47\STATE.md`.
The owner, 21 Nov: "we shouldn't be planning on never upgrading our blender or godot as they will continue to update and we don't want to be trapped not updating".

## Verdict

VERDICT_PLACEHOLDER

## What broke, file and line

| # | What | Where | State on the branch |
|---|---|---|---|
| 1 | C# build: no errors. One new warning: `AnimationNodeBlendSpace2D.Sync` has been obsolete since 4.6 | `godot/src/Actors/PlayerView.cs:483` | Fixed: `SyncMode = SyncModeEnum.Independent` (the same thing). Warnings are back to 4.5.1's 71 (998106632) |
| 2 | SDK pin | `godot/SurvivorUnchained.csproj:1` | `Godot.NET.Sdk/4.7.2`. The packages restore from the editor's own `GodotSharp\Tools\nupkgs` folder through `godot/NuGet.Config` (no download; the path is this machine's) (2cc2767d3) |
| 3 | Making a new material from a shader costs about 10x more: `new ShaderMaterial { Shader = sh }` takes ~228 ms on 4.7.2 against 12-29 ms on 4.5.1 | `godot/src/Fx/BattleFx.P7.cs:144` (and any shader's first material) | The opening's `ShaderKeep` (`src/View/ShaderKeep.cs`, `GameFront.cs:65,70`) holds and readies every shader behind the card, so a player's start pays it there, not in play. Quick starts (`--quick`, every tool and harness) skip the opening and paid it at every dash: a 465 ms + 240 ms frame pair. `--keep-shaders` (911edebca) runs the hold in a quick start. The card's extra time on 4.7.2 is LOAD_PLACEHOLDER |
| 4 | Look: the frame is about 5% darker in the mid and bright tones; darks and near-whites are unchanged | the grade (`src/World/Atmosphere.cs:246-262`: AgX, Softlight glow, volumetric fog) | LOOK_PLACEHOLDER |

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

PERF_PLACEHOLDER

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

REC_PLACEHOLDER
