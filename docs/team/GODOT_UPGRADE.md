# Godot 4.5.1 to 4.7.2: the upgrade sessions (22-23 Nov 2026), after the trial (GODOT_UPGRADE_TRIAL.md)

Branch `worktree-agent-a73cef575840655d2` (from integration 873f32817). State file: `survivorsunchained_inputs\scratch_godot47\STATE.md` (top block).
The owner, 21 Nov: "we shouldn't be planning on never upgrading our blender or godot as they will continue to update and we don't want to be trapped not updating".

**Verdict after session 2 (23 Nov): ready to merge on the build, the suite and the movement numbers; two bars of the brief are NOT met and are the main session's and the owner's to rule on, not this lane's to waive.** (1) The look match went to its three judged rounds and none passed: one mark is left, the shape of the glow halo round one light point. By the README's finish line it closes as known at the cap. (2) Uncapped, 4.7.2's den frame time is 2% longer (median 5.21 ms against 5.11). Everything else below is equal or at the baseline. Measured unless marked.

## Session 2 (23 Nov 2026, Fable lead; the owner, 23 Nov: "your picks are good")

Commits on `worktree-agent-a73cef575840655d2`: eb122b6ff (the look match), 915e5199a (`Ui/Aa.cs`), ab9de03ce (glow numbers), b7342051a (Upgrade Project Files), then this page.

**What the engine changed in the picture, and what now undoes it (4.7 only; on 4.5.1 none of this code runs, so the 4.5.1 picture is untouched).**
- AgX is a new curve since 4.6 (read from the 4.7.2 tag: tonemap.glsl and environment_storage.cpp). Its two dials (contrast, white) cannot reproduce the old curve: measured, contrast 1.20 trades a -0.009 mid dip for +0.0065 lifted darks, white 64 changes nothing. Do not retry dials. `Atmosphere.GradeLut` now folds the exact map (new curve undone, old curve applied) into every grade LUT. Glow off, what is left is a flat +0.0013 to +0.0026 display in every tone bin, about half an 8-bit level. Its source is unknown (my reading: a rounding difference in the render or movie-writer path).
- Soft-light glow still blends after the tonemap (session 1's "before" was wrong for soft light), but on linear values where 4.5 used sRGB-encoded ones, which lifted a faint glow about twelvefold. No single number is exact for both the broad bloom and the hot halos. `Atmosphere.SetGlow` scales intensity x3 and bloom x2 on 4.7: whole frame +0.46 levels of 255 against 4.5.1 (was -4.6% to -5.1% luma before any fix), mean absolute difference about 1.5 levels.
- Antialiased 2D lines are drawn wider since 4.6. `Ui/Aa.W(width)` inverts the engine's own formula; 206 calls in 36 files go through it. Two judges found the HUD the same after it. `Fx/Ribbons.cs` has its own line helper and was left alone.
- Dev flag `--look47 map=0,glow=1,bloom=1` shows the engine's raw picture; `glow=` and `bloom=` take other multipliers.

**The judge (three fresh su-lead-max rounds, 1:1 den frames at the play camera, both engines side by side, bar "no visible change in the look").**
- Round 1 FAIL: tone lobes and thicker HUD lines. Round 2 FAIL: every pair passed except the halo round the light point at pixel (361,500) of take s01, clip second 0.5 (wider and redder on 4.7.2, picked blind 10 of 11). Round 3 FAIL, same place only: after glow x3 / x2 the halo is darker 10-16 px out (red -4.6 to -7.0 levels) and pinker 20-36 px out (red +1 to +2.2, blue +1.5 to +2.9); picked blind 19 of 24. Every other checklist line in round 3 reads "same": exposure, hue, darks, fog and shafts, her outline, foes and hit paint by kind, HUD.
- Not supplied to any round, so not judged: a telegraph ring on 4.7.2 (the take with foes, s12d, is not frame-matched across engines; its 4.7.2 hit frames held no ring) and a lit lamp or fire prop near the camera (none found in the den that a take can place). Take s12 never draws its dummy wolf; s11 draws no swing trail.
- Logged, not failing: a soft patch above her, +4 to +9 red levels on 4.7.2, picked at chance.
- Frames: `godot/.shots/godot47up/judge`, `judge2`, `judge3` in the worktree, copied to `survivorsunchained_inputs\scratch_godot47\judged` with the 4.5.1 reference clips (a 4.5.1 editor run from this tree is no longer safe after the Upgrade Project Files commit).
- What the next attempt costs: one solver burst. The round 3 judge proposed scaling the glow levels separately; that was already tried and does almost nothing on 4.7 (levels changed by 30-50% moved the rings by 0.4 levels or less, sweep m1-m4), so start by reading how 4.6+ composes its glow levels (the 4.7.2 glow shaders) before fitting. A try is 65 seconds: `tools/scratch/godot47/look_sweep.sh TAG:glow=..,bloom=..` then `halo.py` (ring by ring against the kept 4.5.1 frame).

**Numbers (pass = equal or better).**
- Movement, `move_baseline.py`, 23 takes on each engine at eb122b6ff: the two tables are identical, 0 differing lines of 43 (`godot/.shots/godot47up/TABLE_g45s2.md`, `TABLE_g47s2.md`). Taken before the scene re-save; my reading is that the re-save cannot change them (one header line per scene changed).
- Den perf legs, exports, uncapped, 15 minutes each, all four CLEAN (`tools/scratch/pacing4/i2.sh next8`, `godot/.shots/pacing4/i2_summary.txt`):

| leg | engine | fps | median ms | mean ms | 1% ms | 0.1% ms | frames over 16.7 ms | hitches | fx warm-up |
|---|---|---|---|---|---|---|---|---|---|
| s2a | 4.5.1 next4 | 193 | 5.11 | 5.19 | 7.7 | 9.8 | 1 of 172453 | 0 | 4.02 s |
| s2b | 4.7.2 next8 | 185 | 5.27 | 5.41 | 15.2 | 82.5 | 5 of 124292 | 4 | 5.21 s |
| s2c | 4.7.2 next8 | 190 | 5.21 | 5.28 | 7.9 | 10.2 | 3 of 169601 | 1 | 6.64 s |
| s2d | 4.5.1 next4 | 193 | 5.11 | 5.18 | 7.8 | 10.1 | 2 of 172576 | 1 | 4.36 s |

  s2b alone reached the den's own load inside its window (one 9.0 s load frame at 685 s, then the leg ends), which is what its 1%, 0.1% and hitch numbers show; s2c is the like-for-like leg. So: median +0.10 ms (+2%), 3 fps of 193, on 4.7.2; under a 60 fps cap nothing separates them (1 to 5 frames over 16.7 ms in about 170,000). NOT "equal or better" uncapped. Where the 0.10 ms goes is unknown (not traced). The warm-up read 5.21 s and 6.64 s against 4.02 s and 4.36 s; the owner accepted 5.5 s on 23 Nov; why s2c read 6.64 s is unknown (one reading).
- Suite on b7342051a: 3147 pass, 1 fail (the known den one, `DungeonFightTests.The_den_clears_inside_the_pages_feel_targets`), 12 skip: the baseline.

**Upgrade Project Files (b7342051a):** engine-written only, 336 files: `project.godot`, `.import` and `.uid` files, and `game.tscn` and `slice.tscn` re-saved by 4.7.2 (`tools/scratch/godot47/resave_scenes.gd`; one header line each).

**Play build:** `release\godot\next8` in the worktree (exe 109 MB, pck 3.69 GB), made with `tools/scratch/godot47/export47.sh next8` (the "Windows Demo (proof)" preset, windowed so the shader baker runs; `tools/godot/export.sh` cannot name a folder), start check passed (`start47.sh next8`: level 9, warm-up done, 1767 pipelines, no error outside the known exit leaks). next5, next6 and next7 are in the Recycle Bin.
`& "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73cef575840655d2\release\godot\next8\SurvivorUnchained.exe" -- --quick warden --sex female --zone map --dungeon hollow --veteran 9 --move-new --move-ab`

## Session 1 (22-23 Nov), as written then

**Session 1's verdict: NOT MERGE-READY in this session.** The build, the suite and a new break are done; the pipeline compile cost is handed to the frame-pacing lead with evidence; the look and the pacing numbers are not finished. Measured unless marked.

## Done
- **Trial merged** (c3e29b259) without its churn commit 1ebd656c3: that commit deleted the tracked `godot/assets` link and copied 1346 asset files under it. The `.uid`/`.import` churn comes back with the upgrade's own project-files commit, written by 4.7.2.
- **Build:** 0 errors, 72 warnings on both engines, the same set (71 was the trial-era count). **Suite on 4.7.2:** 3147 pass, 1 known fail (`DungeonFightTests.The_den_clears_inside_the_pages_feel_targets`, the den re-tune lane's), 12 skip = the baseline.
- **Export templates** 4.7.2.stable.mono from github.com/godotengine/godot 4.7.2-stable, SHA512 checked against SHA512-SUMS.txt; Windows x64 files only.
- **New break, fixed:** 4.7 refuses a shader over 32 varyings. kit.gdshader's roof variant counted 33 and failed to compile (roofs would not draw). 52cff96be packs six scalars into two vec3 (macros keep the names; same maths). The warm-up library `data/fx_warm/warm.scn` keeps copies of shader code: its 9 kit copies are patched (35c456cf5, `tools/scratch/godot47/warm_patch.py`, saved with 4.5.1 so both engines read it). **Lesson:** any shader-file edit leaves warm.scn's copies stale until a re-census or this patch.
- `AnimationNodeBlendSpace2D.SyncModeEnum.Independent` is documented in 4.7.2's API as "equivalent to the previous sync = true" (the trial's fix holds).
- The fx warm-up's report now gives pipelines by kind and its worst frame (a86b898ca).

## Item 2, pipeline compile cost: one attempt, stopped, handed to the frame-pacing lead
Same work on both engines: the den's fx warm-up compiles 1397-1417 pipelines, canvas/mesh/surface/draw/specialization 20/97/620/262/398, on both.

| run | 4.5.1 | 4.7.2 |
|---|---|---|
| export, start check (zone map, den) | 4.06 s (next4) | 19.95-20.55 s first, 15.81-16.09 s second (next5) |
| editor, Debug, cold / warm (`kinds_ab.sh`) | 11.79 / 5.77 s, worst frame 7.5 / 3.4 s | 33.07 / 28.53 s, worst frame 28.5 / 25.0 s |

- Nearly all of it sits in ONE frame (13-17 s in the export). The travel's black caps at 15 s (FxWarm.Busy), so on 4.7.2 the warm-up can run past it.
- 262 Draw-kind compiles happen on BOTH engines; the Godot docs say Draw compiles "should never happen" with ubershaders. That is a lead for both engines.
- Both engines share one pipeline cache file (`user://vulkan/pipelines.forward_plus.nvidia_geforce_rtx_5080.cache`, 125 MB). The second 4.7.2 run did not rewrite it, and still took 15.8 s.
- Shipped games (5 lines in the state file): Godot's docs (draw everything once behind a load: what FxWarm does), Unreal's PSO precache, Unity's variant warm-up, PC ports' first-boot "optimizing shaders" pass on all cores, Steam's Fossilize. The attempt copied "all cores": `threading/worker_pool/low_priority_thread_ratio=1.0` through an override.cfg beside next5's exe. **No change** (20.55 / 16.09 s). It is not verified that the export read the file.
- My reading, not proven: the cost is in the shader compile itself (the trial's row 3: a new ShaderMaterial costs 228 ms on 4.7.2 against 12-29 ms on 4.5.1), not in the pipeline count.
- **Next for that lead:** an engine-level profile of the one long frame (ETW/PerfView, or a Tracy build); which shaders the 262 Draw compiles are; whether 4.7.2's `user://shader_cache` hits; and the in-play den stall legs (`tools/scratch/godot47/leg47.sh`, next4 against next5).

## Not done
- **Item 3, the look: the stage is found; the re-tune and the judge are not done.** These are frame-matched 12-shot take s01 clips on both engines at the current code (`tools/scratch/godot47/look_ab.sh`, clips `godot/.shots/look_<g45|g47>_<base|glow|volfog>/s01/clip.mp4`, sheets `godot/.shots/godot47up/cmp_s01_<set>/sheet.png`, log `godot/.shots/godot47up/look_ab.log`). Mean luma 4.5.1 / 4.7.2 at 0.5 s and 2.5 s:

| set | 0.5 s | 2.5 s | darkest tenth (0.5 s) | brightest tenth (0.5 s) | MAE |
|---|---|---|---|---|---|
| as is | 0.1754 / 0.1673 (-4.6%) | 0.1952 / 0.1853 (-5.1%) | 0.0471 / 0.0473 | 0.4750 / 0.4656 | 0.011-0.013 |
| glow off | 0.1703 / 0.1666 (-2.2%) | 0.1893 / 0.1847 (-2.4%) | 0.0459 / 0.0472 | 0.4620 / 0.4641 | 0.008-0.009 |
| volfog off | 0.1792 / 0.1691 (-5.6%) | 0.1993 / 0.1876 (-5.9%) | 0.0486 / 0.0476 | 0.4804 / 0.4684 | 0.012-0.014 |

  - **Glow is about half of the drop.** On 4.5.1 our Softlight glow adds +0.0051 luma; on 4.7.2 it adds +0.0007, almost nothing. 4.6 moved glow before the tonemapper, and Softlight now works on pre-tonemap values. Our glow settings are set in code, so the new defaults are not the cause.
  - **Volumetric fog is not the cause:** the gap stays with it off.
  - **The rest, about 2%, is the tonemapper** (my reading, from the shape). With glow off, 4.7.2's darks are 3% brighter, its mids 2% darker and its brights equal. That is a different curve, not an exposure. 4.6 rewrote AgX and gave it `TonemapAgxWhite` (default 16.29) and `TonemapAgxContrast` (default 1.25, measured from 4.7.2's defaults).
  - **Next:** in `src/World/Atmosphere.cs:246-262`, on 4.7 only, raise the glow (intensity, or the blend mode) until glow-on minus glow-off is about +0.005 luma again. Then fit `TonemapAgxContrast` (and the white if needed) to the glow-off darks, mids and brights. Re-shoot with look_ab.sh after each step. Then take the one always-seen judge on 1:1 game-camera den frames, both engines side by side.
- Item 4, the card hold: note only. It is the same compile cost as item 2 (the trial measured +1.9 s).
- Item 5, Upgrade Project Files: not committed. 4.7.2 has already rewritten `godot/project.godot` (features 4.7; adds `animation/compatibility/default_parent_skeleton_in_mesh_instance_3d=true`; `boot_splash/fullsize` becomes `stretch_mode=0`; it drops `screen_space_aa=0`, which is checked to be the default), plus 328 untracked .uid/.import files. The project has only 2 text scenes (`scenes/game.tscn`, `slice.tscn`). The editor's menu action has no command line: re-save those 2 with 4.7.2 and commit that with the churn.
- Item 6, pacing numbers on the final code: not taken. The chains are ready: `tools/scratch/godot47/keep_ab2.sh` (editor den perf, interleaved, and the hold's cost), `move_baseline.py` with MOVES_OUT/GODOT, and `leg47.sh` (export legs).
- Item 7: `release\godot\next5` (4.7.2, at a86b898ca) was built and start-checked. It is NOT the final build (the attempt's override.cfg is already removed).
