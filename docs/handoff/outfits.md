# Handoff: the heroine's body and outfits

From outfits lead successor 8 (su-lead-high), 11 October 2026. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` first, then this page, then `docs/team/outfits.md`. **Never read a whole file**: `heroine_outfits.py` is 5,500 lines. Grep, then `sed -n` the lines you need. Pictures cost context: crop, look once, and send sheets to judges.

## The owner's words and bar
- "AAA", "never settle", "we are striving for perfection"; edges "perfectly cut and tailored professionally". Sex appeal drives it, "tho not at the cost of looking bad"; full cups with "massive cleavage" are fine; the Reaver stays near-naked with underboob.
- Coverage: "pixel perfect no extra stuff hidden at all. none. not even a few pixels". Holes and see-through are "really distracting and bad". Fit means **tighter, not bigger**.

## The coordinator's rulings for this round
1. Pauldron: the leather spaulder (`PAULDRON=leather`) becomes the default **once it passes**.
2. Plunge: h3's bound plunge (feathery trim dropped). One try at a fair U at the foot, else a small arcane clasp. **Done: the try failed (below), so the clasp is in.**
3. B1 and B2 (Arcanist, arm_side cell 6). Keep `MEND_PRECUT` off.
4. Then a full h5 build and a fresh su-lead-max judge on the h3 checklist plus judge 7's items (`O2\h4\verdict7.md`). A pass goes to the owner as a sheet: the leather pauldron beside h3's lames, and the plunge (with its clasp). Then SendMessage the main session the commit and sheet paths.

## Paused here (branch `worktree-agent-a5ca10091b08dc429`, pushed; integration merged in at 59ee7a24)
Built art in godot/art/people is **integration's** now (animation's helper build). The judged-FAIL h4 art is backed up in `O5\h4art_bak\`. Nothing built is committed.
- **Spaulder, plate clearance (done, ebe1facf):** over all 1,607 poses of the new clips (`O5\poses.json`, re-dumped after the merge with `O2\paul_v\dump_pose.gd`), plates crossed in a third of her poses at 7 mm gaps and shares 0.45/0.6/0.7. Now `SP_BAND` 0.011,0.0245 and `SP_W` 0.5,0.55,0.6: bands 1-2 never cross; cap and band 1 cross in 11 poses (death_back 7 of 14 frames, cast_raise 3, cast_bolt 1, get_up_back 1); where band 1 slides under the cap the clearance is >= 1.17 mm (5 poses < 1.5). Shares 0.5/0.5/0.55 would leave one pose (likely a measuring artefact: identical rows can't cross) but more skin through band 1; a judge call. Skin through the bands > 10 mm (past the tuck) in about 355 poses for band 1 and 255 for band 2 (the old design: 284/240): show the judge cast_raise, death_back and get_up_back in Godot. Workbench at idle: `O5\c_w01.png` (top old, bottom 12 mm gaps).
- **Rivets:** they sat right (0.3 mm proud, `m_riv.py`); the "hole" and halos were the 1.3 r flange catching light round a dark head. Flange now 1.12 r (all rivets, all outfits). Unseen in Godot.
- **Bracers:** the satin flag reached them (vertex alpha 0.5 checked in the gltf); the hot streak was the 0.32 roughness floor on a round. Floor now 0.38 for plates and bracers (shader). Unseen in Godot.
- **Look number for the face lead:** the spaulder is in their frame. 0.02% of their region [760:1080, 600:1320] at >= 250; a crop round the spaulder (cols 1150-1350): 0.10% (63 px). `O5\g1\look.png`.
- **B1: solved, it was the review tool.** anim_review.gd drew outfits in StandardMaterials and never tucked her skin; the speck was untucked skin. With `OUTFITSHADER=1` (new, 5bfc734b: the game's outfit shader and tuck) it is gone (`O5\b12\cmp_tk2.png`). The solver's folded-sleeve theory and its discard shader were tested and reverted (not needed). Animation told. **Shoot every arm sheet with OUTFITSHADER=1** (`O5\b12\b12.sh` passes it through).
- **B2:** with the game's shader the pinch reads as a soft contact crease where her wrist presses (same crop). Let the judge rule on it from the OUTFITSHADER sheets.
- **Plunge:** the try (`PLUNGE_BAND`/`STRING` 45 mm, h3's `PLUNGE_TAUT=0.06`) broke the stitch line and kept the left step (`O5\pl\cmp1.png`). So `plunge_clasp()` (in `arcanist()`, before `down_tube`): a gold crescent on the binding round the foot (horns 78 deg round it, 8.5 mm wide at the foot, `CLASP=deg,width`), an oval amethyst cabochon (new `amethyst` gloss material) in a gold bezel, each point skinned as the corset point nearest it. **Built and shot (clasp2), NOT good yet** (`O5\pl\cl2.png`, crop of `O5\pl\clasp2_cu_chest_f.png`): the crescent sinks into the binding in a ragged line and its horns are buried in the cloth (the 30-pass easing of its back depth `Y` pulled it behind them: keep `Y0 = Y.copy()` before the easing and use `Y = np.minimum(Y, Y0) - 0.0006`; my scripted edit failed on line endings, not applied), and the stone renders near-white, not violet (check how kind "gloss" takes the `amethyst` tint in heroine_outfit.gdshader; maybe a metal-free deep violet with its own albedo). Every Arcanist build: `PLUNGE_TAUT=0.06 bash O5/pl/bld.sh <tag> arcanist`. Judge 7 asked for silver; I used the corset's gold to match her set: a judge call.

## Next, in order
1. Look at the clasp crops; fix what's off (one honest try, then a solver).
2. h5: copy `O2\h4\run.sh` to `O2\h5\run.sh`: tag h5 against h3, drop `PLUNGE_TRIM`, keep `PAULDRON=leather` and `PLUNGE_TAUT=0.06`, shoot the arm sheets with `OUTFITSHADER=1`, add Godot frames of cast_raise, death_back and get_up_back for the Ranger. Check the build log for `--helpers`: animation says helpers are now built by default (their abcbb3d3, not yet merged); our build calls `rig_helpers.apply` already. Disk is fine (325 GB). Hand the ~45 min wait to a su-runner.
3. The judge (ruling 4), with pair sheets (`O2\h4\pairs.py`) h3 lames vs h5 spaulder, the clasp, the numbers above, and hair clipping through the outfits (integration's hair swing b716ea2a). Then the owner sheet and SendMessage to the main session.
4. Later: Arcanist crotch flap, channels' bar tacks and ridge, vault's 2 frames / 3 px; the Warden's corners and raw cup edge; gusset shards; boots, gloves, stockings (owner: Reaver, Ranger and Arcanist boots); nipple show-through equal both sides (OWNER_NOTES).

## Setup (O5 = `...\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\o5`, O2 = `...\o2`; keep both)
- **Spaulder sweeps (Blender turn, one session, several variants):** `bash O5/vary.sh <dir> "K=V K=V;K=V"` (VM5=1 adds plate-into-skin and SKIN10 counts; ~3 min a variant with VM5). Measures: `m_pp2.py` (plate crossings by clip), `m5.py`, `m_riv.py` (rivet seats). Single variant with renders at idle: `MPOSES=g0 bash O5/run2.sh <dir>`; sheet `python O5/crops.py <dir> out.png 0.4`.
- **One outfit build:** `bash O5/pl/bld.sh <tag> <outfit>` (env knobs pass through) into `O5\pl\<tag>\tx`. Godot close-ups: `PRE="cp <files> <worktree>/godot/art/people/" bash O5/shoot.sh <dir> <cu.txt>`. **`O5\LOCK`** guards godot/art/people between helpers: shoot.sh and b12.sh take it; never leave it behind.
- `O5/ed.py <file> <pairs.py>`: exact-match edits keeping each spot's line endings (`heroine_outfits.py` mixes CRLF and LF).

## Gotchas
- The arm sheets (anim_review) lie without `OUTFITSHADER=1`: no tuck, wrong materials.
- `PLUNGE_TAUT=0.06` is h3's setting, not the default (0.03): pass it to every Arcanist build.
- Workbench renders show no skin tuck. Judge geometry in workbench, looks in Godot.
- A helper's completion notice goes to the main session: brief helpers to write a result file last.

## Collaborators
Face a4ed04ec4c86f67bd, animation a1d7dac29f821a87f (successor 9). Reports go to the main session.
