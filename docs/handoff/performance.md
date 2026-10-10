# Handoff: performance and rendering lead

For a fresh successor. Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md`, this page, then `docs/team/performance.md`. **Never Read a whole big file: grep, then `sed -n` the lines.** Older rounds: git history of this page and `docs/PERF_AUDIT.md`.

Written by agent a4e0c353e61cca6dc, 2026-10-10 (wound down at the owner's word). Before it: a6a04e32348559b6c (cut off by the limit), a7afb4d33cdd5efba, a20bdef993e00f26b, ad57a6dd0798688d7. Branch `worktree-agent-a4e0c353e61cca6dc` @ c4beebaf + this page; 775 tests pass.

## The owner's words

- "we are blurry when moving in active action gameplay." "the filter to see through trees and stuff is also a little pedestrian in its pixelation." "we are striving for perfection." Her detail is never traded for frames.

## Paused here; next:

State (all on this branch, none merged yet):
- **Hair defaults flipped** (c4beebaf, `godot/src/Actors/HairDraw.cs`): `--hair-draw two` (opaque core at cover `--hair-core-cut 0.5`, writing depth and motion vectors incl. sway; blended over pass), FSR 2's reactive mask erased under hair (`--hair-erase 0`, eased in from `--hair-erase-from 0.5` over the 0.25 below), lashes and brows and face paint erased too (`HairDraw.Eraser`, `People.cs` paint chain). Under MSAA the core swaps to `heroine_hair_core_a2c.gdshader` (alpha to coverage; `HairDraw.Msaa`, called from `Graphics.Apply`). `--hair-bias` exists, judged no gain: leave 0.
- **The Look** (creation) is always TAA + MSAA 4x, whatever play uses (`Graphics.AtLook`, set by `GameFront.LookView` on NewJourney/EndCreate), and has **no depth of field** (it caused the side-hair mush and edge flicker; `--look-dof` brings it back). Per-view verified bit-identical.
- **Play's AA is still TAA by default.** The judge (c13) says flip play to FSR 2 native now: in `Graphics.Apply`, at scale 1.0 use FSR 2, `FsrSharpness = 2.0` (sharpening off), MSAA off. Not done: do it first, then the two gates below.
- See-through: no fix is default. `--see-fix back,norim` is the judged stopgap (wedge and arc gone, crisp), but it is a cookie-cutter circle ("pedestrian"). Switches: back, screen, narrow, underao, undercut, norim (`KitLook.Fixed`, `kit.gdshader` SEE_*).

Next, in order:
1. **Flip play to FSR 2 native** (above). Then two gates, FSR 2 vs TAA, deterministic: a fight at a 60 fps cap (`--fixed-fps 60`), and a fight with wolves on screen (fur shells, `fur_shell.gdshader`; c13's "pack" showed only risen).
2. **The Look's hair edge under A2C** (c13: staircase gone, but the edge is darker, 0.3–1 px wider, a dotted double line on the +40 jaw, 3x the shimmer of tt5n). Fix in `heroine_hair.gdshaderinc` CORE_A2C: `ALPHA_TEXTURE_COORDINATE = UV;` (turns off Godot's +25%/mip coverage boost), and at the Look put `core_cut` back to 0.9 (per view, via `HairDraw.Msaa`), the over pass carrying true cover. Alternative (keep 0.5): over pass under MSAA `c = clamp((cover - core_cut)/max(fwidth(cover),1e-4)+0.5,0,1)*step(cut0,cover); ALPHA = max(cover-c,0)/max(1-c,1e-3)`. Pass on llr/llrn: jag ≤ 0.10, rim darkness ≤ tbn + 3, edge within 1 px of tbn, edge share >8/255 ≤ 0.1% (judge scripts `rim3.py`, `tband.py` in scratchpad `judge_c13b\`).
3. **Ground fizz under FSR 2** (arena, low severity, fuses at 164 Hz, test at 60): `arena_ground.gdshader` detail layers sampled 0.25–0.5 mip blurrier (derivatives × 1.19–1.41), specular AA before ROUGHNESS (`k = min(0.5*(|dFdx n|²+|dFdy n|²), 0.18); rough = sqrt(rough²+k)`), `arena_leaves.gdshader` leaves under ~4 px faded to the ground's tone. Pass: lit-litter temporal noise ≤ 1.3 (`tspec.py`).
4. **See-through v2** (cycle 11 judge's design; opaque only, the REVEAL pass deleted): radius fixed to each piece in world space `R = (1.55 + 0.35*fbm(world.xz*1.1 + v_jit*17))*open`; foliage thins along its leaves (`ALPHA_SCISSOR_THRESHOLD = mix(1.02, alpha_scissor, smoothstep(R-0.5, R+0.25, metres))`, alpha sampled at mip +1.5); solids `discard` inside R with a soft darkening at the cut; roofs lifted whole (KitLook tags roofs; CPU line test sets an instance uniform `lift` eased over 0.15 s; world-noise dissolve); the radius eased in and out over 0.2 s.
5. The face judge's items for rendering (main session's scratchpad `judge_hr2\verdict.md`): the hair cut where it crosses the strap at her right ear; DOF softness at the crown (likely gone with the Look's DOF: confirm); hair shadow facets on Highborn's neck (shadows are cut at half cover, `IN_SHADOW_PASS`); card order (c11/c12 judges saw no wrong-order cards).
6. Smaller: Godot never resets FSR 2 history on camera cuts (`reset_accumulation = false; // FIXME`, render_forward_clustered.cpp): check frames after cinematic cuts. Cinematics' DOF (GameCinema) will mush blended hair the same way. A smoke billboard notches the slash VFX with quad edges (`art/fx/sprites.png` frame borders?). Retire `--hair-draw blend|hash`, `--coverage`, `--aa` switches once FSR 2 ships.

For other leads (via the main session): face: the strand atlas darkens as cover drops (dark rim on every card edge; spread the strands' shade into partial texels), card edges end in wide alpha ramps (a 3–5 px see-through band) instead of strand tips, plank-like locks, hairline band, lash comb; the eye shader's hard pupil and sub-pixel iris edge and catchlight flicker under FSR 2 (`heroine_eye.gdshader`: fwidth edges). Combat/creatures: the risen horde moves in lockstep. UI: the Blessing picker hides the world behind a black page.

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

HANDOFF READY: docs/handoff/performance.md on worktree-agent-a4e0c353e61cca6dc
