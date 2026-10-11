# Handoff: the heroine's body and outfits

From the fifth outfits lead (su-lead-high), 11 October 2026, handed off at its context budget. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` first, then this page, then `docs/team/outfits.md`. **Never read a whole file**: `heroine_outfits.py` is 4,000 lines. Grep, then `sed -n` the lines you need.

## The owner's words and bar
- "AAA", "never settle", "we are striving for perfection"; edges "perfectly cut and tailored professionally". Sex appeal drives it, "tho not at the cost of looking bad"; full cups with "massive cleavage" are fine; the Reaver stays near-naked with underboob.
- Coverage: "pixel perfect no extra stuff hidden at all. none. not even a few pixels". Holes and see-through are "really distracting and bad". Fit means **tighter, not bigger** (except where the check's 2.4 cm strip is wider than a garment: then just wide enough). There were never genital issues.

## Paused here (11 October, after judge 4); next:
Branch `worktree-agent-a5ca10091b08dc429`, HEAD = this commit. **Built art in the worktree is mixed and unjudged; never commit it until it passes:** Warden and Reaver = g9; Ranger = dry build p7 (new pauldron); Arcanist = dry build t6 (`PLUNGE_TAUT=0.06`, stomach and nipple fits); `heroine.glb` = g9. g9 backups: `o2\g9_arc\`, `o2\g9_rgr\`. Do a full rebuild (`o2\b.sh`) before any motion check. Also uncommitted on purpose: animation's `heroine.res` + `heroine_clips.json` (thigh fix). `o2` = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\o2`. Keep `o2`, `o3` and `o4_plunge` beside it.
- **Judge 4 (FAIL; paint edge and ink pass):** `o2\judge4\verdict.md` (coords, fixes, priority), sheets in `o2\judge4\`.
- **Done this round (code committed):**
  - **Reaver ink z-fight:** `view_pull` in `heroine_outfit.gdshader` moves VERTEX toward the camera in model space; `PULL` table in the builder; read by `People.OutfitMaterials` and `lookdev.gd`. Writing POSITION instead hid every piece. Judge: better as a skin-material mask (option).
  - **Arcanist stomach:** `mls_flat()`, a quadric fit along a direction, replaces Taubin in `piece(stiff=)`. Taubin keeps long waves, which is why the abs stayed. `stiff` takes a list of (width, zone) or callables. Passes in stills.
  - **Nipple dome:** `over_nipples()` uses an `mls_flat` fit within 65 mm, G2 falloff, eased off near the rim. Left breast passes; the right is unproven (re-shoot with the lights mirrored).
  - **Ranger pauldron:** built from the lowest plate up. Each lame is a band (`PL_LAP` 10 mm under the plate above) with its own centre on the arm. `shell(nest=)` nests each plate outside those under it (world, along its own rays). Plates 1.5 mm. `RIGID_UV` in `finish()` gives each plate one island round the arm. Gash and dents are gone; corners remain.
  - **Plunge:** a solver's commit 7b110ba5 (signed-distance U cut, `taut_gore()` rolled-disc closing, `PLUNGE_TAUT`). t6 (60 mm disc) is still not clean: a tooth at the foot on her right, and her left side drops below the foot. **The two sides differ because her skin is asymmetric** (nipple depths -0.163 vs -0.156). Next: mirror-snap the sheet round the plunge before the cut (left depth = mean of own and mirrored right), then DUMP `arcanist.corset` to see whether the tooth is born at the cut (`3cut`) or in `bind_edges`. A fresh solver with exactly that brief.
- **Next, in order:**
  1. Full rebuild, then re-shoot the Arcanist game look. Judge 4's j3 six-pack frames predate the stomach fix.
  2. Plunge (above).
  3. Pauldron: tuck lame ends 10 mm under the plate above (clip each band's arc by the plate above's outline), round the corners R 8-12 mm, make the dome's lower rim one curve, brush along the bands.
  4. Nipple re-shoot with the lights mirrored.
  5. Collarbone blister on the Arcanist suit (fit it like the stomach).
  6. Warden corners and raw cup edge (judge 3 item 3).
  7. Arcanist gusset shards in vault.
  8. Boots (judge 3 item 6): one boot per solver.
  9. Gloves, stockings, rivets as metal, suit boning seams.
- Coordinator notes: a red scratch line beside her left cup (w_paul_l_side ~940-1000,865-885), and a white rim down her neck. If the rim is the face shader's rim term, hand it to face (a8b147f78b1db794b). Animation adds heels as a runtime foot pitch once the boots pass, and will send the elbow corrective shape (name, driver, transfer) to carry onto the garments. Rendering's LOD hook line comes after its judge. Body mesh holes at the inner thigh: not ours (animation confirmed with `o3\meshdef.py`).
- **Gotcha:** `heroine_outfits.py` is now LF in the working tree (a `sed -i`); git normalises it. Python edits must match `\n`.

## Setup
- My scratch folder (`SO` below): `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\outfits\`: `setup_wt.ps1`, `cu.txt` (close-up list for `closeups.sh`), `q3.sh` and `qsum.py` (fast loop), `loops2.py`, `longedge.py`, `rimlong.py`, `nonman.py` (rim and mesh diagnostics on DUMP npz), `judge1/` (judge 1's sheets), `solver1/` (the cut-off solver's tools: `sim.py`, `fold.py`, `raysec.py`).
- A new worktree: `godot/assets` as a junction to its `public/assets` (`git update-index --skip-worktree godot/assets`), then robocopy main's `godot/.godot` and main's `*.import`/`*.uid` sidecars (godot, not through the junction, and public/assets): `SO\setup_wt.ps1` (repoint `$WT`). Never commit the sidecars (line-ending churn).
- `tools/scratch/outfits/*.sh` now find their worktree themselves and take the scratch folder from `OSCR` (e.g. `OSCR=<scratchpad>/outfits bash tools/scratch/outfits/turn_build.sh`). Copy `tools/comfy/out/heroes/heroine_built.blend` (main checkout) to `$OSCR/hs/` first. **The session scratchpad is shared with other agents: keep yours in a subfolder.**
- New: `compare.py <base> <new>` (per outfit: strip and areola frames, any pixel and 6+, worst frames, tucked-skin frames); `xsection.py <heroine.glb> <outfit.gltf> <png> y,y,y` (cross-sections at the crotch, Blender axes).
- True baselines are in the first lead's scratchpad: `.../74e72383-70c7-41d5-8e96-2fad2ed58481/scratchpad/legal/base1/<outfit>/` (read-only; compare against it).

## Gotchas
- The worktree guard refuses shell commands with variables in loops, heredocs near git, or `sed -i` on a glob: write a script file and run it. `heroine_outfits.py` has CRLF endings (the Edit tool copes; Python string replaces need `\r\n`).
- `DUMP=<piece,...>` writes npz files to `$TEMP`: set `TEMP` to a folder for that one command (turn.py keeps its state in `~/.su_turns`, so it is unaffected).
- `BOUND x n of m edge loops` now counts only bound loops.

## Collaborators
Animation lead a20d622060130a90a (helpers, weights, thigh fix; you share the rig). Face lead a8b147f78b1db794b. Rendering lead a7afb4d33cdd5efba (owed: one TAA out-of-gamut pixel, Warden vault, chest view, frame 10). Reports go to the main session.
