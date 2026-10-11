# Handoff: performance and rendering lead

For a fresh successor. Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md`, this page, then `docs/team/performance.md`. **Never Read a whole big file: grep, then `sed -n` the lines.** Older rounds: git history of this page and `docs/PERF_AUDIT.md`.

Written by agent a4e0c353e61cca6dc, 2026-10-10 (wound down at the owner's word). Before it: a6a04e32348559b6c (cut off by the limit), a7afb4d33cdd5efba, a20bdef993e00f26b, ad57a6dd0798688d7. Branch `worktree-agent-a4e0c353e61cca6dc` @ c4beebaf + this page; 775 tests pass.

## The owner's words

- "we are blurry when moving in active action gameplay." "the filter to see through trees and stuff is also a little pedestrian in its pixelation." "we are striving for perfection." Her detail is never traded for frames.

## Paused here; next:

Written by the successor lead a1 (11 October, at the context budget). The branch is at the commit after fb3adb43, and 775 tests pass. N = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad` (this lead's scratch: `ng\` for the grade, `fur\` for the fur; the tools are there).
Spelling: the owner is American, and the British-spelling rule is dropped.

Done:
- **The Night grade (judged PASS, ng3):** `Atmosphere.KeepHue` (Atmosphere.cs), baked into the grade LUT.
  - Dark browns no longer go purple: in the eye region, magenta among dark pixels went from 29% to 5%.
  - Greys, cool colours and greens keep the old blue and teal.
  - Warm near-greys lose their violet toward navy.
  - Commits: 13d87d5a, 075824d4, 39ac8e4d. The face lead asked for 39ac8e4d: skin in shade keeps its hue, with mid-tones held from saturation 0.025-0.06. Face's neck judge n1 passed it at 1:1 on all ten faces (under-jaw hue 15-37 went to 41-48; portraits 46-52); keep the hue hold as is. Face has cherry-picked them.
  - Flags: `--grade-old`; `--grade-dump FILE` (check the dump with `N\ng\lut.py` and `f1.py`); `--grade-sat-lo` and `--grade-sat-hi`; `--hair-colour ID`.
- **The wolf fur sparkle.** Judge fur1 gave PASS WITH FIXES and said "merge as a step". The wolf arena doesn't sign off yet.
  - 0a85d850: the crowd's textures get mips.
  - 8ac7d1f9: the paint is read 1.5 mips softer, and shine and rim fade where the normal turns fast (vat.gdshaderinc).
  - 2d9b6922: the edge-on card fade is dropped. It thinned the outline and gained nothing.
  - fb3adb43 (unjudged): the bias scales with each body's pace (cm moved per frame), so still foes stay crisp.
  - Results: crowd sparkle went from 299 to about 90, against a target of about 70 (TAA scores 7). Split it with `N\split.py TAG`: paint alone scores 103, and adding the shine fade brings it to 89.
  - Ruled out: the frozen-only glint, and the engine's mip bias (0 at native).
  - Motion vectors: Godot reruns the vertex shader with the previous frame's custom data and time, so the VAT limbs should get motion vectors. If the sparkle stays, confirm this on a motion-vector view.

Next, in the coordinator's order:
1. **The heroine's gameplay LOD.** The owner approved all five pieces, then said "we can skip measuring and move to implementing":
   - a gameplay-distance LOD that keeps the silhouette dense at the bust, hips, gear effects and weapon;
   - the body triangles hidden under each outfit removed in the gameplay LOD;
   - the lowest LOD for shadows;
   - her pieces merged by material;
   - fewer fur shells at range.

   How to build it:
   - Make it its own post-export step that runs after heroine.glb is written, like `tools/assets/heroine_seam.py`.
   - Don't edit `heroine_outfits.py`: the outfits lead (ace45ae43386569ed) owns it. Tell them the step and its hook line.
   - Hold full detail at the title, in creation, in conversations, and on every cinematic or close-up camera.
   - Bake the fine detail into normals so she looks the same at play size.
   - Judge the full model against the LOD at the play camera, at 1:1 and 3x, plus the shadows. They must look the same.
   - Include before and after ms only if a runner gets them nearly free.
   - PERF_AUDIT §4 puts her at about 1M triangles (Warden 727k, body 92k, hair 173k) and 95+ draws per pass, landing in about 9,000 px.
2. **Fur, round 2** (judge fur1's fixes 1, 3 and 5):
   - View the motion vectors on a running wolf.
   - Fade only cards under 1 px on screen, if that keeps the outline.
   - Limit the rim at grazing angles on the thin legs and the tail.
   - Then re-judge, adding a lit-arena crop where the foes are dense, at bias 0 against 1.5.
3. **The night moonlight pass** (judges ng1 and ng2): night arenas and the town read black and amber instead of moonlit blue, because unlit ground falls into the grade's toe.
   - Try a moon fill or a toe floor. Warm darks should reach navy through grey.
   - Pale wood looks lilac in the Verge, with the old grade too. Sample its colour before the grade first.
4. **Ground:** `detail_blur` 2.4, but only if detail stays at or above TAA's (judge c14, fix 2).
5. **See-through v2:** the design is unchanged; see this page's git history, the 10 October block.
6. **The face judge's hair items** (main scratchpad `judge_hr2\verdict.md`):
   - the hair cut over the strap at her right ear;
   - DOF at the crown;
   - hair shadow facets on Highborn's neck.
7. **Smaller items:**
   - FSR 2 history is never reset on camera cuts.
   - GameCinema DOF mushes blended hair.
   - The smoke billboard notches the slash VFX.
   - Retire `--hair-draw` and `--coverage`.
   - Bush alpha-cut steps.

Tools:
- Runs go through `181eef02 scratchpad\perf9\batch.ps1 RUNS "rendering: X" -NoImport`, which takes the godot turn and gives it back. The runs file has one line per run: "NAME | RES | FPS | args".
- Measuring: `perf9\furbox.py`; `N\split.py` (needs `c23_wolf60_mask_*.png` in .shots); `N\ng\sheets.py` and `sheets2.py`.
- Judge and solver briefs need "Context budget: NNk". Lean judges cost 85-140k.
- Python in bash heredocs: Windows paths break the string escapes, so write files with the Write tool.

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

HANDOFF READY: docs/handoff/performance.md on worktree-agent-a4e0c353e61cca6dc (successor of a3123dd8bb0182789)
