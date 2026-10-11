# Handoff: the heroine's body and outfits

From outfits lead successor 6 (su-lead-high), 11 October 2026. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` first, then this page, then `docs/team/outfits.md`. **Never read a whole file**: `heroine_outfits.py` is 5,300 lines. Grep, then `sed -n` the lines you need.

## The owner's words and bar
- "AAA", "never settle", "we are striving for perfection"; edges "perfectly cut and tailored professionally". Sex appeal drives it, "tho not at the cost of looking bad"; full cups with "massive cleavage" are fine; the Reaver stays near-naked with underboob.
- Coverage: "pixel perfect no extra stuff hidden at all. none. not even a few pixels". Holes and see-through are "really distracting and bad". Fit means **tighter, not bigger**.
- Standing option (11 October): "can add leather trim to ranger, and white feathery trim to arcanist parts of their clothing in the bust if it makes it easier to clean them up nicely - just only increase the skin we cover slightly".

## Paused here
Branch `worktree-agent-a5ca10091b08dc429` (pushed). **Built art in the worktree is h4 (PAULDRON=leather PLUNGE_TRIM=down, MEND_PRECUT on), plus a test Arcanist (the down tube) copied over it: all judged FAIL, uncommitted on purpose.** Animation's `heroine.res` + `heroine_clips.json` are uncommitted on purpose too. `O2` = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\o2` (keep it, and `o3`, `o4_plunge`).
- **Judge 7** (`O2\h4\verdict7.md`, read it first; crops in `scratchpad\j7`):
  - **Pauldron: show the leather spaulder (h4), after fixes 1-4.** Code: `ranger_spaulder()` (env PAULDRON=leather; default still the lames), knobs SP_LINE, SP_BAND, SP_THB, SP_MED, SP_R, SP_LIFT, SP_W, SP_LEATHER. Fixes in order: (1) the cap's neck-side edge is buried in the leather with no rolled rim: keep the leather 1-2 mm under the cap's whole footprint and bind the cap all round; (2) the leather between plates is crumpled (dark facets, pale shards); check shadows first, then relax it; (3) the cap's neck end stands off the leather (a black crescent from above): trim 15-25 mm off its top so the leather alone climbs the trapezius, or line its underside; (4) blocky brushing on the cap; (5) the rear-lower hem flares off the arm, band 2's rear tip overhangs; (6) a torn notch in the neck-end binding; (7) rivet halos, black at distance; (8) the bracers still polished (make them satin like the cap: shader flag 0.5 or a bracer rule in `heroine_outfit.gdshader` ~line 145). Optional: a bicep strap with a small buckle; squarer band ends. Numbers wanted: cap-to-leather gap round its rim (<= 1 mm), plate clearances on Godot skinning (>= 1.5 mm), hem gap, % plate px >= 250 at the Look.
  - **Plunge: show h3's bound plunge, not the trim.** The trim (`down_tube()` in arcanist(), PLUNGE_TRIM=down; `down` material = fur shells, params in `People.Fur` and lookdev's `fur()`) reads as faux fur / Santa trim, W at the foot, blunt neck ends, covers too much. The judge's rebuild recipe is in the verdict if the owner still wants a trim. **For h3's plunge:** make the foot one fair U (a pale tooth at a_chest_f 957-965,885-890, kinks 870-895,870-890 and 995-1010,860-895); else a small arcane clasp at the foot (silver, about 25 mm, violet stone). The coordinator ruled no fourth plunge solver; ask the main session before more plunge work.
  - PASS: the Ranger's pale neckline line. FAIL: B1 (skin speck, arcanist_arm_side cell 6, 2202-2206,156-161) and **B2 (pinched notch 2093-2103,98-105) is not cured by mending before cutting**, which also broke the Warden's cups (the two ran together, one lost its binding). So `MEND_PRECUT` is now off by default (`mend_folds(..., free=, normals=)`). B2 needs another way (e.g. relax the Arcanist suit there, raise its offset at the arm contact).
- Committed since judge 6 and built in h4: matte bindings, UV-brushed plates, rivet AO and lighter iron, B1's longer tuck, plates satin (+0.14 roughness on flag-0.5 plates, face's ask).

## Next, in order
1. Spaulder fixes 1-8 (fast loop below), then a full build h5 with PAULDRON=leather and the default plunge (copy `O2\h4\run.sh`, drop PLUNGE_TRIM, `b.sh h5 h4`), the h3 plunge foot fix, B1, B2; then a lean judge with the side-by-side (h3 lames vs h5 spaulder) for the owner. When it passes, tell the main session (branch and commit).
2. The Arcanist crotch flap, the channels' bar tacks and ridge, vault's 2 frames / 3 px.
3. The Warden's corners and raw cup edge; the gusset shards; the boots; the gloves and stockings.

## Setup
- **Spaulder fast loop (3 min):** `bash O2\sp\run.sh <dir>` with env VIEWS/VIEWS_G (see the a2 call in this session: five r_paul views), POSE=g0 (the game's Idle), MPOSES=all or every:2, MEASURE=m_sp2.py (exact BVH; m_sp.py is nearest-vertex). It execs `heroine_outfits.py` up to the build loop and calls `ranger_spaulder()` (or PFN=ranger_pauldron). Its "through" counts are unreliable (the lames show the same); use them only comparatively. Sheet: `python O2\sp\sheet.py <dir> out.png ",_g0"`.
- One outfit: `PAULDRON=leather bash O2\t.sh ranger` (into O2\tx). To see it in Godot without a full build, copy `O2\tx\heroine_outfit_<o>.gltf/.bin` into `godot/art/people/`, then `CU=<dir> TURN=1 bash tools/scratch/outfits/closeups.sh <cu.txt>` (OSCR exported as in run.sh). Pair sheets: `python O2\h4\pairs.py <a> <b> <out> names...`.
- Full: `O2\h4\run.sh` (about 45 min with clips). `o3/plain.sh` regenerates its own motioncheck.gd; keep the `o3/plain` folder existing.
- After a C# change run `dotnet build` in `godot/` before Godot shots.

## Gotchas
- The Bash tool's heredocs turned `\\n` into `\n` in Python source: write edit scripts to a file. `heroine_outfits.py` mixes line endings (CRLF in most of it).
- Killing a run's bash leaves its children and their turns: find them by command line, stop them, `turn.py give` the names left in `turn.py show`.
- A helper's completion notice goes to the main session: run judges in the foreground, or brief them to SendMessage you and write a report file.

## Collaborators
Face a11b9dd1569a9987e, animation ae658d74219d7f4b8. Reports go to the main session.
