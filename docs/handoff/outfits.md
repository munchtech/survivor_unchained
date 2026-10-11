# Handoff: the heroine's body and outfits

From outfits lead successor 7 (su-lead-high), 11 October 2026. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` first, then this page, then `docs/team/outfits.md`. **Never read a whole file**: `heroine_outfits.py` is 5,400 lines. Grep, then `sed -n` the lines you need. Pictures cost context: crop, look once, and send sheets to judges.

## The owner's words and bar
- "AAA", "never settle", "we are striving for perfection"; edges "perfectly cut and tailored professionally". Sex appeal drives it, "tho not at the cost of looking bad"; full cups with "massive cleavage" are fine; the Reaver stays near-naked with underboob.
- Coverage: "pixel perfect no extra stuff hidden at all. none. not even a few pixels". Holes and see-through are "really distracting and bad". Fit means **tighter, not bigger**.
- Trim option (11 October): leather trim on the Ranger, white feathery trim on the Arcanist "if it makes it easier to clean them up nicely". **The coordinator dropped the feathery trim (judge 7)**: keep h3's bound plunge.

## The coordinator's rulings for this round (still open except 1)
1. Pauldron: the leather spaulder (`PAULDRON=leather`), made the default **once it passes**. Fix judge 7's defects. Report the bright-pixel % at the Look for the face lead.
2. Plunge: h3's bound plunge. **One** focused try by you (no solver) at making its foot one smooth U (judge 7: pale tooth at a_chest_f 957-965,885-890, kinks 870-895,870-890 and 995-1010,860-895, crumple vault_over_05 ~430-500,395-420). If not clean at 1:1: a small arcane clasp at the foot (silver, about 25 mm, violet stone, suited to the Arcanist). No second solver.
3. B1 (skin speck, arcanist_arm_side cell 6, 2202-2206,156-161) still fails. B2 (pinched notch, 2093-2103,98-105) needs a different fix; keep `MEND_PRECUT` off (it broke the Warden's cups). Idea: relax the Arcanist suit there or raise its offset at the arm contact.
4. Then a full h5 build (leather pauldron + h3 plunge with the fixed foot or clasp), then a fresh su-lead-max judge on the h3 checklist plus verdict7's items (`O2\h4\verdict7.md`). A pass goes to the owner as a sheet: the leather pauldron beside h3's lames, and the plunge. Then SendMessage the main session the commit and sheet paths.

## Paused here (branch `worktree-agent-a5ca10091b08dc429` @ db4e78eb, pushed)
**Spaulder: geometry and materials reworked, not yet judged** (commits 626297e6, db4e78eb). Built art in the worktree: the h4 build (judged FAIL) with **this round's Ranger copied over it** (`heroine_outfit_ranger.gltf/.bin`, `outfit_materials.json` with the new `rivetbronze`, `outfit_tex/` and `art/outfit/outfit_rivetbronze_diff.jpg`). All uncommitted on purpose, as are animation's `heroine.res` + `heroine_clips.json`.
What changed in `ranger_spaulder()` and why (judge 7's numbers in brackets):
- (2 crumple) The leather under the plates is held to each plate's underside (`owned()`), held to her skin past `FAR` (16 mm) from any plate, and **eased harmonically between** (`fill()`, a graph Laplacian solve). Weights the same way (`weigh`): cap's bones reach `FAR_W[0]` 16 mm past its rim, bands' 6 mm. Blending tangent planes by distance made the facets and shards.
- (5 hem flare) The leather's hem, past the plates, is pinned `LIFT` off her skin (BVH) before the fill: hem off skin now at most 4.6 mm over the sampled poses (was 22-24).
- (1, 3 neck end, buried rim) The cap is trimmed 20 mm at the neck (`SP_MED` -0.055), lifted 4 mm more (`SP_CAP_UP`), and stops 90 deg round her arm behind and **65 deg in front** (`SP_TH` "90,115,65"): her front deltoid swells 6-8 mm through any rigid plate at her idle, so the leather alone covers it. The leather runs `SP_MARGIN` 8 mm past the cap all round. Measured at idle (g0): no leather over the cap; leather 4 mm past the cap's rim sits 2.1 mm below its inner face (front and back thirds clean; 4 of 70 points in the middle third, the neck end where the leather climbs her trapezius); her skin no longer passes through the cap in most poses (median -4.8 mm).
- (6 torn notch) The side limits were step functions (`side * 0.05`): the cut followed her triangles and tore the binding. Now distance fields with `ANDR`.
- (4 blocky brushing) `brushed()` in `heroine_outfit.gdshader`: hairline rows 0.4 mm apart, each with its own phase, faded to the mean by `fwidth`. (7 rivets) the spaulder's rivets use a new `rivetbronze` (dark bronze, value 100). (8 bracers) flag 0.5 (satin, brushed) and a ring UV round the forearm (`RIGID_UV["ranger.bracer_l/r"]`).
- Look (face lead's ask): Ranger at the Look (`--archetype stalker`), face lead's region [760:1080, 600:1320], max channel >= 250: **0.02%** (was 5.7%). Picture `o5\g1\look.png`; I didn't look at it, so check that the spaulder is in that frame before quoting it.
- Godot close-ups of this state: `o5\g1\` (r_paul, _neck, _top, _back, _rear, r_chest_f). My 1:1 read: rims, gaps and neck end are clean. **Still to check:** one rivet at the cap's outer edge reads as a hole (r_paul ~1740,235); the bracers still show a hot specular streak along their top (r_paul_top 330-420,780-830): the flag may not have reached them (check the vertex alpha) or they need more roughness; the band ends and their rivets from behind (r_paul_rear).

## Next, in order
1. Check the three items above at 1:1; measure plate-to-plate clearance (>= 1.5 mm, `m_sp2.py` has it) and the full sweep (`MPOSES=all`).
2. Plunge foot (ruling 2), then B1/B2 (ruling 3).
3. h5: copy `O2\h4\run.sh` to `O2\h5\run.sh` with tag h5, drop `PLUNGE_TRIM`, keep `PAULDRON=leather`, `bash b.sh h5 h4` (about 45 min with clips; hand the wait to a su-runner). Then the judge (ruling 4), with the pair sheets (`O2\h4\pairs.py`) h3 lames vs h5 spaulder.
4. Later: the Arcanist crotch flap, channels' bar tacks and ridge, vault's 2 frames / 3 px; the Warden's corners and raw cup edge; gusset shards; boots, gloves, stockings. Merge integration (b716ea2a, hair swing) and check her ponytail and braid against the outfits.

## Setup (O5 = `...\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\o5`, O2 = `...\o2`; keep both)
- **Spaulder fast loop (2 min, Blender turn):** `bash O5/run.sh <dir>` (env `SP_*` knobs pass through; `MPOSES=rest,g0,every:8 DUMP=g0`). It builds only `ranger_spaulder()` from the worktree's code (`O5/harness.py`; the old `O2/sp` harness overrode it with a stale `spaulder.py`), prints `M5` numbers (m5.py) and shoots five workbench views at the game's Idle. Analysis on the dump: `python above.py <dir>/pose_g0.npz` (leather over plates, cap rim burial), `hem.py` (hem off skin by place), `an.py` (skin through plates). Sheets: `crops.py <dir> out.png 0.6`.
- **Godot check without a full build:** `PAULDRON=leather bash O2/t.sh ranger` (into O2/tx, about 15 min), copy the gltf/bin (and any new texture and `outfit_materials.json`) into `godot/art/people/`, then `bash O5/shoot.sh <dir> cu5.txt [look]` (Godot turn, import, close-ups, the Look).
- `O5/ed.py <file> <pairs.py>`: exact-match edits that keep each spot's line endings (`heroine_outfits.py` mixes CRLF and LF).

## Gotchas
- Workbench renders show no skin tuck: skin through leather there is hidden in the game (10 mm tuck). Judge geometry in workbench, looks in Godot.
- Killing a run's bash leaves its children and their turns: stop them by command line and `turn.py give` the names in `turn.py show`.
- A helper's completion notice goes to the main session: run judges in the foreground, or brief them to SendMessage you and write a report file.

## Collaborators
Face a4ed04ec4c86f67bd, animation a521f0caab2e91579. Reports go to the main session.
