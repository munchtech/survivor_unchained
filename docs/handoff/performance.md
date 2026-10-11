# Handoff: performance and rendering lead

For a fresh successor. Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md`, this page, then `docs/team/performance.md`. **Never Read a whole big file: grep, then `sed -n` the lines.** Older rounds: git history of this page and `docs/PERF_AUDIT.md`.

Written by agent a4e0c353e61cca6dc, 2026-10-10 (wound down at the owner's word). Before it: a6a04e32348559b6c (cut off by the limit), a7afb4d33cdd5efba, a20bdef993e00f26b, ad57a6dd0798688d7. Branch `worktree-agent-a4e0c353e61cca6dc` @ c4beebaf + this page; 775 tests pass.

## The owner's words

- "we are blurry when moving in active action gameplay." "the filter to see through trees and stuff is also a little pedestrian in its pixelation." "we are striving for perfection." Her detail is never traded for frames.

## Paused here; next:

Written by a3123dd8bb0182789 (10 October, at the context budget). Branch @ the commit after 0a85d850, integration merged, 775 tests green (before 0a85d850; rerun).

Done and judged (judge c14, verdict `S\judge_c14\verdict.md`; S = the 181eef02 scratchpad):
- **Play is FSR 2 native by default** (`Graphics.Apply`: FSR 2 at every scale, sharpening off; `--aa old` = the former TAA + MSAA, also smaa/fxaa/msaa/taa). Gates PASS WITH FIXES: at 60 fps FSR 2 keeps her and the foes crisp, TAA ghosts the slashes; owner sheet `S\perf9\c16\fight60_x1.png` rows 1 and 4.
- **The Look's hair edge PASS:** A2C core at its own `a2c_cut` 0.9 (`--hair-a2c-cut`), `ALPHA_TEXTURE_COORDINATE = UV`; matches TAA blended hair. Bar from now: jag <= 1.1x the reference (0.10 was wrong).
- **Arena ground:** `detail_blur` 2.0 (one mip softer: detail equal to TAA's) + specular AA. Fizz ~2x TAA, accepted as low. Leaf fade tried and dropped (it dimmed every leaf).
- **Pictures repeat frame for frame:** `Game.Rng` seeded in shot mode, camera kicks on game time. Gates now compare the same moment.

Next, in order:
1. **Wolf fur sparkle** (required before the wolf arena signs off). Root cause found by solver: the crowd's glTF textures had no mips (fixed, 0a85d850, unjudged) and FSR 2 keeps ~1 frame of history on fast-moving foes, so each frame must be smooth on its own. Sparkle (nearest wolf, `S\perf9\furbox.py`, frames 3-5): TAA 36, FSR 2 607, with mips 362; crowd share 298 vs target ~70 (ground alone ~70 in the box). Measured, unbuilt: crowd textures one mip blurrier 148, two 111; one mip + rim and specular off 95. Next: crowd textures sampled one mip softer + specular/rim AA on bodies (vat.gdshaderinc), check fur still reads as fur at 3x, judge. Runs `S\perf9\runs_c20.txt` (wolves at 2.2 s, title on screen; `--nohud` doesn't hide it). Solver notes: `split.py` and `sheet_c21.png` in scratchpad 91211d34-...\scratchpad.
2. **Night grade for face** (promised to face lead a411e6c81f22f5c18, waiting on it): `Atmosphere.GradeLut` adds the shadow tint in gamma (`p += (lin(#2f5a86) - 0.5) * sh * 0.24`), taking ~0.11 R off dark pixels: dark browns go purple/black (lashes, pupils, irises, brows) at the Look (Night). Fix: hue-preserving shadow tint (chroma toward the tint at constant luma), lift neutral in darks, for every grade. Message face with the commit so they recalibrate iris swatches.
3. Ground: try `detail_blur` 2.4 only if detail stays >= TAA's and box 700 900 900 1050 <= 1.3 (judge c14 fix 2).
4. **See-through v2** (unchanged design): radius fixed in world space `R = (1.55 + 0.35*fbm(world.xz*1.1 + v_jit*17))*open`; foliage thins along its leaves (`ALPHA_SCISSOR_THRESHOLD = mix(1.02, alpha_scissor, smoothstep(R-0.5, R+0.25, metres))`, alpha at mip +1.5); solids discard inside R with a soft darkening at the cut; roofs lifted whole (KitLook tags roofs; CPU line test, instance uniform `lift` eased 0.15 s; world-noise dissolve); radius eased 0.2 s. `--see-fix back,norim` is today's stopgap ("pedestrian").
5. Face judge's items (main scratchpad `judge_hr2\verdict.md`): hair cut over the strap at her right ear; DOF at the crown (likely gone with the Look's DOF: confirm); hair shadow facets on Highborn's neck (`IN_SHADOW_PASS` half-cover cut).
6. Smaller: FSR 2 history never reset on camera cuts (`reset_accumulation = false`): check frames after cinematic cuts; GameCinema DOF mushes blended hair; smoke billboard notches the slash VFX; retire `--hair-draw blend|hash`, `--coverage` once FSR 2 ships; bush alpha-cut edges show 1 px steps under FSR 2 (low).

Tools: `S\perf9\batch.ps1` needs `powershell -ExecutionPolicy Bypass`; `edge_nums.sh` (Look edge numbers), `flick.py`, `sheets_c14.py`/`sheets_c15.py`, `judge_c13b	spec.py`, `furbox.py`. Judge and solver briefs need the line "Context budget: NNk".

## Measured (164 Hz; share of pixels changing >8/255 between consecutive frames, hair / face)

| | Look pony 1080 | Look long +40 | her detail running 1440 / 1080 |
|---|---|---|---|
| TAA + MSAA, hashed (old default) | 0.02 / 0.05 | 0.03 / 0.51 | 9.58 / 9.07 (50–60 px ghost) |
| TAA + MSAA, blended, no DOF | 0.00 / 0.02 | 0.00 / 0.13 | |
| TAA + MSAA, "two" 0.5 + A2C, no DOF (new Look) | 0.00 / 0.02 | 0.00 / 0.18 | |
| FSR 2, blended, no eraser | 0.43 / 0.68 | | 11.73 / 11.42 |
| FSR 2, blended, whole hair erased (c10; dotted strands running) | 0.24 / 0.23 | 0.78 / 0.97 | 11.77 / 11.44 |
| FSR 2, "two" 0.5, eraser from 0.5 (new play) | 0.25 / 0.22 | 0.74 / 0.65 | 11.69 / 11.40 |
| same + bias 0.5 | 0.08 / 0.17 | 0.13 / 0.59 | (no gain in play) |

Fight (arena, 60 horde, 1440): ground flicker TAA 1.09–1.13 (0% hot) vs FSR 2 2.21–3.54 (1–2.8% hot): fine fizz on ground and litter, judged low severity.

## Where things are

- Scripts: my scratchpad `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\perf9\` (batch.ps1 takes the godot turn; shoot.py; `runs_c10`–`c13.txt`; `mk_c1x.py` write runs and `sheets_c1x.py`; look_noise, crops sharp, mres, flick, look_where). Sheets in `perf9\c10\`–`c13\`. Judges' crops and measuring scripts: `judge_c10\`, `judge_c11\`, `judge_c12\`, `judge_c13b\` beside it. Frames: this worktree's `godot/.shots`.
- Repoint the scripts to a new worktree with a copy of `setup9.py` (same scratchpad).

## Gotchas

- Worktree setup: delete the `godot/assets` placeholder file, make it a junction (`New-Item -ItemType Junction`) to the worktree's `public/assets`, `git update-index --skip-worktree godot/assets`; copy `godot/override.cfg` (perf user folder); robocopy `godot/.godot` from a worktree that has imported; copy `.import`/`.uid` (setup9.py); `dotnet build` in `godot/` after every C# change (the game runs the built assembly). The editor import crashed (access violation) at 94 s once; the game ran fine on the cache; use `-NoImport`. Never commit `.import`/`.uid` churn.
- **Never merge a WIP branch whole**: a6a04's WIP commit had replaced the `godot/assets` symlink with 850 copied asset files. Apply its code with `git diff A^ A -- paths | git apply -3`.
- batch.ps1's give-back sometimes leaves the godot entry listed; check `turn.py show` and give it back by its exact listed name.
- `--auto` is needed for fights (else the Blessing picker pauses); the autopilot's 1440 run path is not repeatable (two bias runs went off course).
- Engine facts (Godot 4.5.1 source in scratchpad `0b33992d-...\scratchpad\godot_src\`): FSR 2's reactive mask is the colour's alpha (clamped 0.9); the transparent pass writes no motion vectors; `blend_mul` alpha = src × dst (so the eraser works); alpha antialiasing cuts at the scissor first, then ramps at scissor + edge with a +25%/mip boost.

## Collaborators

Main session (reports, owner decisions; relays to the face lead, who owns the hair's look and mesh, eyes and lashes). Outfits and animation leads share the godot turn.

HANDOFF READY: docs/handoff/performance.md on worktree-agent-a4e0c353e61cca6dc (a3123dd8bb0182789)
