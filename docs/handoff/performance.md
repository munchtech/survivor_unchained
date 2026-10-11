# Handoff: performance and rendering lead

For a fresh successor. Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md`, this page, then `docs/team/performance.md`. **Never Read a whole big file: grep, then `sed -n` the lines.** Older rounds: git history of this page and `docs/PERF_AUDIT.md`.

Written by agent a4e0c353e61cca6dc, 2026-10-10 (wound down at the owner's word). Before it: a6a04e32348559b6c (cut off by the limit), a7afb4d33cdd5efba, a20bdef993e00f26b, ad57a6dd0798688d7. Branch `worktree-agent-a4e0c353e61cca6dc` @ c4beebaf + this page; 775 tests pass.

## The owner's words

- "we are blurry when moving in active action gameplay." "the filter to see through trees and stuff is also a little pedestrian in its pixelation." "we are striving for perfection." Her detail is never traded for frames.

## Paused here; next:

Written by lead a3 (11 October, at the context budget). Branch @ e06744f4 + this page. 775 tests passed before e06744f4's last grade tweaks; rerun them. N = scratchpad `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad` (`lod\` LOD tools, `ng\` grade and portrait tools).

Done this round (426cea72, e06744f4):
- **Night grade toe** (face's ask: dark irises and hair crushed to black). Atmosphere.GradeLut holds the shadow tint's darkening in the toe (`GradeSettings.Toe`; the hold fades in over 0-0.14 gamma luma and out by 0.35). Then `ToeColour` keeps a dark's own hue (neutral share `--toe-own` 0.45, chroma ramp `--toe-chroma` 0.04).
  - Strengths: Night (wilds) 0.75; NightTown and ArenaPlaces 0.5; `Atmospheres.Front` (title and Look, GameFront) 1.0.
  - Doe's iris 56,22,12 now stays 56,22,12 at the Look (was 25,6,4). Neutral, brown and navy ramps are smooth.
  - Judge aad08911f5aa24415: round 1 PASS WITH FIXES; round 2 verdict: VERDICT2.
  - Flags: `--grade-toe X`, `--toe-foot/-own/-chroma`, `--grade off`. Check a `--grade-dump` with `N\ng\lutcheck.py LUT.bin`; sheets with `N\ng\nt_sheet2.py OUT PREFIX`.
- **Portrait light** (GameFront.PortraitLight, face's ask): fill 1.0/0.95/0.9, a warm bounce of 0.18 from below, rim specular 0.25. Face's `--bounce`, `--key-shadow` and `--ssao` switches are brought in; `--rig-old` gives the before.
  - Judge a57930a5a677ca5ce: PASS WITH FIXES, ship as built once its checks pass. Measured with `N\ng\pl_meas.py pl1`:
    - Under-jaw shade hue 42-48 to 46-51 (cheek 53-58).
    - Shade C/L against the cheek's: 0.76-0.90 to 0.89-1.07.
    - Catchlights kept, no second catchlight.
    - Cheek spread shrinks 9%, order unchanged.
    - Sclera chroma +0.011-0.013 (target under 0.01; the box may catch lashes).
    - The jaw-step and collar-lilac boxes missed (the right shade box lands on hair).
  - For face: the judge saw ears paler and greyer than the face, and a pale scalp wedge at the temple. Face's HerBackSpec (c3f549ec, back_spec 0.3) isn't on this branch; with it, the rim's skin sheen is 0.25 x 0.3, so check the two together.
- **LOD:**
  - The Reaver's ink and her skin within 2 cm of it are kept as built (`DECALS`). Outfits also fixed the ink z-fight in their shader (view_pull 1.5 mm, 2560896e/4c757428), which the LOD shares through HerLod's material copy.
  - Close tiers loosened to 0.1/0.5/1 mm: Warden 400k to 323k, Arcanist 247k to 209k, Ranger 302k to 245k, Reaver 181k to 156k. The play-size sweep is as clean as tight: s5 blobs Warden 22, Arcanist 7, Ranger 10, Reaver 25 (skipping gib frames 7, 8 and 11).
  - The built art in godot/art/people is this version, uncommitted and unjudged. The tight build is in `N\lod\art_tight\`.

Next:
1. **LOD: one blob left at the 18 m switch.** In s6, Reaver frame 0 has a 206 px blob: a dark leather flap at her hip reads darker and wider in the LOD.
   - Bisected with `N\lod\rtest.sh TAG` and the env switches `LOD_EXACT_MATS=a,b` and `LOD_EXACT=1` in heroine_lod.py. It isn't removal, the shadow mesh, the fur shells or the body. It clears with all three leathers exact and stays with blackleather or darkleather alone exact, so it's **oldleather** (168k triangles).
   - Next: try a tighter error on oldleather near that flap, or a heavier normals weight. Confirm with rtest.
   - Then the re-judge: per-outfit worst6 (`sweep.py` with `SKIP="reaver:7 reaver:8 reaver:11"`), the strips, and the s6 18 m frames. Shoot everything with `--grade-toe 0`, because the arena grade changed under the old off frames.
   - After the pass: commit the art, including the `*_lod.gltf.import` files. Send outfits lead **a8f5db2bb06ceb5c5** the hook line for `heroine_outfits.py`, after the outfits export: `import heroine_lod; heroine_lod.main([os.path.dirname(OUT)])`. Tell the coordinator the commits.
2. **The moonlight pass** (the toe judge's fix 1): give the town and arenas a dim cool moon fill, so unlit ground is blue before the grade (dark hue 230-270 at low chroma, lamp pools still amber). Then re-judge the town and arenas at toe 0.5.
3. **Fur, round 2** (judge fur1's fixes 1, 3 and 5). State: crowd sparkle went from 299 to about 90 (target about 70, TAA 7); fb3adb43 (bias by pace) is unjudged. The detail is in lead a1's block in this page's git history (99cb2f8c).
   - View the motion vectors on a running wolf.
   - Fade only cards under 1 px on screen, if that keeps the outline.
   - Limit the rim at grazing angles on the thin legs and the tail.
   - Then re-judge, adding a lit-arena crop where the foes are dense, at bias 0 against 1.5.
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
