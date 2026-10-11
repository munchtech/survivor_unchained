# Handoff: the heroine's body and outfits

From outfits lead successor 9 (su-lead-high), 11 October 2026. **Outfits are PAUSED by the owner, with no successor running** (the coordinator: pause at the h5 build plus its judge). A future lead picks it up cold from here. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` first, then this page, then `docs/team/outfits.md`. **Never read a whole file**: `heroine_outfits.py` is 5,500 lines, and it mixes CRLF and LF line endings, so edit it with exact byte replacements that keep each line's ending (`O5\ed.py`). Pictures cost context: crop, look once, and send sheets to judges.

## The owner's words and bar
- "AAA", "never settle", "we are striving for perfection". Edges "perfectly cut and tailored professionally". Sex appeal drives the heroine's look, "tho not at the cost of looking bad"; full cups with "massive cleavage" are fine; the Reaver stays near-naked with underboob.
- Coverage: "pixel perfect no extra stuff hidden at all. none. not even a few pixels". Holes and see-through are "really distracting and bad". Fit means **tighter, not bigger**.

## The coordinator's rulings (still open)
1. The leather spaulder (`PAULDRON=leather`) becomes the Ranger's default **once it passes**. Judge 8 passed the design over h3's lames, but not the build.
2. The Arcanist's plunge is h3's bound plunge (the feathery trim is dropped) with an arcane clasp at its foot. Judge 8: **gold, not silver**.
3. When both pass, the owner gets a sheet: the leather pauldron beside h3's lames, and the plunge with its clasp. Then SendMessage the main session the commit and the sheet path.

## State (branch `worktree-agent-a5ca10091b08dc429`, pushed; see the last line for the head)
- **h5** (code c54721ff: leather spaulder, plunge with a 3 mm stand-off clasp, `PLUNGE_TAUT=0.06`, arm sheets with `OUTFITSHADER=1`) was built and judged. **Judge 8: FAIL as rendered, both designs pass.** The verdict is `O2\h5\verdict8.md`, the sheets are in `O2\h5\` (`pairs\`, `sheet_*.png`, `a_clasp_*.png`, arm sheets).
  - **B1 PASS, B2 PASS** with the game's shader: the speck came from the old review tool, and the pinch reads as a contact shadow.
  - Warden and Reaver: no visual regression. The small count rises on them (warden hit areola 0 to 2 px, throw tucked6 10 to 18) date from animation's rig merges (09:23 and 10:04) after h3 was built (06:19), not from our code.
- **After h5 (all unjudged):**
  - **Clasp, judge 8's fixes 6-9 applied** (e213d4e9, aa46cb4a): the horns follow the binding's inner edge on each side, found by walking out from the foot until the front layer's cloth begins. There is a boss under the stone that tapers to 2.5 mm tips. It is seated 1 mm off the cloth (`CLASP_OFF`), and the 456 cloth, binding and stitch faces under it are cut away 1 mm inside its edge. The gold is warmer (tint 1.0/0.88/0.7) and the stone lighter (mean 100). Built as `O5\pl\clasp8\tx`; crops `O5\pl\cl8.png` (front at 1:1 is clean, with symmetric horns). Its span is now 38 mm, but judge 8 asked to keep 58 mm: to widen it, raise `CLASP` (horn angle, default 78) so the horns climb further up the U.
  - **Spaulder, judge 8's fixes 1-5, partial** (two solvers, 7f1f11ba and 3c6c74f0, WIP). Fixed: the hem hole spot and the rivet halo (band rivets on each band's middle). Better: the neck corner (16 mm radius) is rounder but still lifts slightly. Not fixed: the rear-lower corner still hangs as a binding loop, and the pale line at r_paul_neck isn't a UV seam (the leather is now one island; likely a crease at the held-to-eased boundary in `conform()`). **Regressions:** the binding parts from the leather by up to 6.2 mm at idle (311 points over 1 mm), and the cap-to-band-1 minimum clearance fell from 1.17 mm to 0.01 mm (`SP_CAP_UP` 0.0045, raised 0.5 mm; cause not found). Crossings are unchanged: 11 inside and 12 over (death_back 7, cast_raise 3, cast_bolt 1, get_up_back 1). If the next lead prefers h5's spaulder, `git diff c54721ff 3c6c74f0` shows exactly these changes. Details: `O5\sp8\result.md`, `O5\sp9\result.md`, sheet `O5\sp9\sheet.png`; final art `O5\pl\sp9b\tx`.
- **Built art in the worktree is uncommitted on purpose (never commit it unjudged):** godot/art/people holds h5's full build, except the Arcanist, which is clasp8. `outfit_tex` has sp9b's and clasp8's textures. h4's art is backed up in `O5\h4art_bak\`.

## Next, in order (judge 8's fixes; none started beyond what is listed above)
1. **Spaulder hem:** rebuild both lower hem corners as one continuous roll 0.5-1.5 mm off the arm, with the skin hidden to within 3 mm of the hem (r_paul_back 900-995,500-560; r_paul 1855-1890,660-765). sp9's next step: move band 2's weights toward her skin's (for example 0.5/0.6/0.75 for cap, band 1 and band 2) so the hem folds less, checked against plate crossings; fix the binding's 6.2 mm parting (the switch along the edge between skin weights and band 2's row). The lead's first call (skin weights on the last 12 mm, the change hidden under band 2) put the leather 4.8 mm through band 2 at idle.
2. **Neck corner:** round it and pin it to the skin (r_paul_top 1272-1290,105-125).
3. **Rivet** off band 1's rim: done in sp9. Check the cap's border rivets (7.8 mm from the edge, only 1.6 mm inside the rim; the judge wants 2 mm).
4. **Pale seam line** across the leather (r_paul_neck 1365-1450,160-170): plot the sheet's dihedral angles there, then smooth the crease or ease its normals.
5. **Cap-to-band clearance** at least 1.5 mm over the sweep (h5 1.17, now 0.01: find why it fell; put the cap back if the raise caused it).
6-9. **Clasp:** done (above), but unjudged; decide its span (58 mm) and re-shoot at 35-45 degrees.
10. Then h6: copy `O2\h5\run.sh` (it already holds the clasp close-ups `a_clasp_hi`, and `plain_low.sh` shoots the lying clips). **Add shoulder close-ups of the crossing poses**: judge 8 couldn't judge crossings from the far sheets, where the spaulder is about 30 px across. Then a fresh su-lead-max judge with verdict8 as the checklist. A pass goes to the owner as the sheet above.
11. Later: Arcanist crotch flap, channels' bar tacks and ridge, vault's 2 frames / 3 px; the Warden's corners and raw cup edge; gusset shards; boots (Reaver, Ranger, Arcanist) and gloves, stockings; nipple show-through equal on both sides (OWNER_NOTES). Then Marionette's armour workshop (RESUME).

## Setup (O5 = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\o5`, O2 = the same scratchpad's `o2`; keep both)
- **Full build plus everything for a judge:** `bash O2/h5/run.sh` (about 25 min: Blender, close-ups, motion check and qsum against h3, plain frames, arm sheets). Run it in the background and wait on its `run.txt` for `H5DONE`.
- **One outfit:** `PLUNGE_TAUT=0.06 bash O5/pl/bld.sh <tag> arcanist` (or `PAULDRON=leather ... ranger`) writes to `O5\pl\<tag>\tx`. **Godot close-ups:** `PRE="cp <tx>/<gltf> <tx>/<bin> <wt>/godot/art/people/ && cp <tx>/outfit_tex/*.jpg <wt>/godot/art/people/outfit_tex/" bash O5/shoot.sh <dir> <cu.txt>`. **Copy the textures too:** the stone read white in Godot only because its texture was never copied. `O5\LOCK` guards godot/art/people; never leave it behind.
- **No-turn checks:** `O5\pl\dbg\shade.py <gltf> <png>` ray-casts the rest pose; sp8's tools in `O5\sp8\` (gl.py, scene.py, shots.py, part.py, umap.py) skin the exported gltf as Godot does, with the skin tucked; `O5\sp9\b2.py` checks leather against band 2 over the sweep.
- **Spaulder sweeps:** `bash O5/vary.sh <dir> "K=V;..."` (VM5=1), measured with `m_pp2.py` and `m5.py`.

## Gotchas
- **A clean rest pose can still break in her idle.** The clasp was clean at rest, but at 0.4 mm the cloth's lumps came through it in Godot. Check every close-fitting rigid piece in Godot.
- `closeups.sh` with `POSE=<clip>` breaks: lookdev reads the POSE env as bone rotations. Use `plain.sh` or `plain_low.sh` for clips.
- The arm sheets lie without `OUTFITSHADER=1`. Workbench renders show no skin tuck.
- Ray casts through the plunge opening hit her back's cloth: keep only the front layer (`y_ft`).
- Never `git commit -a` here: built art is tracked and modified. Use `git add tools/assets/heroine_outfits.py`.
- A killed build script keeps going: TaskStop killed the bash, but its Blender and Godot children ran on and took turns. Kill the process tree and give the turns back.
- A helper's completion notice goes to the main session. Brief helpers to write a result file last.

## Collaborators
Face add62b85abe9e6b4b, animation a1d7dac29f821a87f. Reports go to the main session.
