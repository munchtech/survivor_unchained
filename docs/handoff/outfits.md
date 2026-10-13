# Handoff: the heroine's body and outfits

From outfits lead successor 13 (su-lead-high), 12 October 2026 night. **Stopped clean for a new session; no helper running, no turn held.** Start cold from here: `docs/team/README.md` ("Safety", "Working lean"), RESUME's "Coverage", then this page. **Never read a whole file**: `heroine_outfits.py` is ~5,900 lines with mixed CRLF/LF, so edit it with exact replacements (`S\ed.py <file> <pairs.py>`, pairs.py defines `PAIRS=[(old,new),...]` in raw strings `r"""..."""`).

## Start here (successor 13 stopped, 12 Oct night; no helper running, no turn held)
- Branch `worktree-agent-a5ca10091b08dc429`. Worktree art = build **glove_g3** (the glove fix + the rigid clasp as in g0). It is **unjudged and uncommitted on purpose**. N = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\33ad5b17-6735-4f1b-843e-85f16b19e648\scratchpad\outfits` (keep it).
- **Tools (in N):**
  - `CUF=<list> bash N/b.sh <tag>`: a locked full build plus close-ups into `N/<tag>` (B_DONE in run.txt; about 15 min).
  - `bash N/locked.sh <cmd>`: use it for any render of the worktree's art (parallel solvers share one worktree).
  - `N/solver_common.md`: the brief every solver reads first (rules, the lock, the motion check).
  - lookdev's ORBIT takes `,x,z` target offsets (camera lists take two extra columns).
  - lookdev's `CLIPFRAME=k` poses her at the motion check's picture k (167d2c1d). Pass the clip as `her/<clip>`. closeups.sh's POSE is a bone pose, so use `N/glove3/shoot.sh` for clip frames.
- **The close-ups are not her rest pose.** `Idle` isn't in her rig, so lookdev shows her rest pose plus the HerPose posture, which spreads her breasts about 9 mm against her spine at the plunge.
- **The checker (`tools/legal/motioncheck/count.py`):**
  - It flags from 1 px now. It was 6 px, silent below that, so older qsum bases read lower.
  - Pixels dropped by stray(), the binding filter and the lone filter are counted, logged in `stray.txt` and cropped.
  - Judges 12 and 13 still want the root fix: draw garments flat grey in the test-colour mode, then assert 0 stray and 0 binding.

## Done this session
- **Nipple rise: REVERTED to e2 exactly** (judge 11, `N/j11/verdict11.md`). The 3 mm plateau read as a rivet with chips, and the owner said it was "kinda ok before". The owner's call: closed, don't reopen.
- **The Warden's "areola pixel" is not skin.** It is a skirt-plate highlight that matches a code colour; judge 12 passed that. It is fixed in the checker (76c823b5).
  - Watch: the right cup's margin is +0.27 cm at warden_show_left_10.
  - Judge 12: resample frames 9-11 at 4-8x density; widen the cup about 3 mm, mirrored, if the margin falls under 0.1 cm.
- **The Arcanist glove see-through is fixed but not yet passed** (e11b2991, 6d38e296). A hide mark of exactly 1.0 now discards in heroine_skin.gdshader; every other mark is capped at 0.98. catch_breath went from 25 px to 0 at the hand.
  - Judge 14 FAIL (`N/j14/verdict14.md`), worst first:
    1. A skin wedge in the notch where the sleeve's front seam meets its hem (l_cuff_outer_rest ~797-815,517-567). Fix: run the glove's cuff 1.5-2 cm higher under the sleeve, or pin the flap. Not more discard.
    2. The welded glove's open-edge fragments (73 left, 18 right) near the knuckles and palm: list them, close the ones on the outer surface, ring each at 4x.
    3. Reshoot the palms at rest from about 25 cm, with her body, bodice and skirt hidden.
    4. Minor: a 5 px spike at the left thumb tip (l_hand_inner_cb04 1250-1267,849-862).
  - Then one sheet to a judge. Kit: `N/glove3` (lists, shoot.sh, report.txt) and `N/glove`.
- **Clasp tips: not fixed.** The solver's kit is in `N/clasp/` (dump_idle.sh, balls.py, ortho2.py, sheet.py).
  - At rest the tips sit on the bindings. Posed (HerPose), the rigid clasp and the breast-weighted bindings part by 9.5 mm (left) and 8.6 mm (right).
  - Riding weights (`CLASP_RIDE=1`, default off) seat the balls (0.66/0.52 mm), but the crescent kinks (c1) or flattens (c2).
  - Next route: keep the crescent rigid and put only its last ~6 mm and the ball on the roll's weights, pre-shaped so it reads as a crescent in her carriage. Then bend the tips onto the roll's crown and round the taper (N2: the drawn-down back rim is the chisel facet).
  - Or ask the owner whether HerPose should move her breasts 9 mm at the plunge.
- **Gold reads olive; likely cause: a double tint.** The `claspgold` texture is already tint x grain (~line 1201), and the shader's metal branch multiplies its mean by `tint` again (~line 144). Check `outfit_materials.json`.

## Next, in order
1. The glove: judge 14's items 1-4, then one judge.
2. The clasp (route above) and the gold's double tint.
3. Two new 1 px flags: catch_breath side_02 (544,330, the bodice's hip edge) and vault_back over_04 (the chest clasp).
4. Two side notes:
   - The purple cup's edge stair-steps where it overlaps the gold clasp (a_bust_r ~1120-1140,800-845; judge 11, sent by the coordinator). Cause: aliasing or z-fighting. Check it at the play camera too (an idle/town close-up camera is coming).
   - A dark flap at the bodice's leg opening by the hip (judge 13): a stray polygon or a tab?
5. Judge 10's spaulder list (`J\j10\verdict10.md`): the A5 neck-corner crease, the A4 rivet halo, the A6 armpit cusp, the 3.9 mm neck fit (fix FOLLOW in make_motioncheck.py first), the N5 roll knuckle and step, the cap rivets' spacing and fleck.
6. The boots.

**Cost lessons:**
- Parallel solvers in one worktree work with `locked.sh`.
- Each judge round widened the scope. Give the judge the previous verdict, and ask for the blocking items only.
- Successor 12's notes (spaulder, binding, clasp) are in this page's git history at 9b0536cc.

## The owner's words and bar
"AAA", "never settle", "we are striving for perfection". Edges "perfectly cut and tailored professionally". Sex appeal drives, "tho not at the cost of looking bad"; full cups with "massive cleavage" fine; the Reaver near-naked. Coverage "pixel perfect ... not even a few pixels"; holes and see-through "really distracting and bad". Fit means tighter, not bigger. Nipple poke-through on Arcanist and Ranger, equal both sides (the owner once chose 1.5 mm over 3).


## Setup
J = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\1515c1de-1208-43e2-b6eb-5133e0d07e1c\scratchpad\outfits`. The build reads `heroine_built.blend` in the 181eef02 session's `scratchpad\outfits\hs` (OSCR): keep it. S = `...\ba85aba8-36f4-4cf9-99c5-4c5ef9e4a65c\scratchpad\o` (ed.py, sheet.py); O2 = `...\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\o2` (b.sh motion check). Keep all.
- `CUF=<list> bash J/b.sh <tag>`: full build + Godot close-ups into `J\<tag>\` (B_DONE in run.txt; key.txt). Lists: `J\cu.txt` (all), `cu_e.txt` (Ranger binding/spaulder), `svC\cuC.txt` (Arcanist clasp).
- `EXTRA=... bash J/j.sh <tag>`: build + close-ups + posed dumps of six Ranger clips + `mdump.txt` (cap/band numbers).
- `J\svC\p1.py <arcanist gltf> <heroine.glb> <out.png>`: clasp parts, balls vs binding, gold over skin.
- Motion check: `NOBUILD=1 bash O2/b.sh <tag> <base> "<outfits>"` then `O2\<tag>_qsum.txt`; last base `n1`.
- Sheets: `J\j10\mk.py`, `J\j9\mk3.py` (two builds side by side).
- Solvers' kits: `J\sv` (sim.py offline skinning), `sv2` (row search), `sv3` (evalb.py), `svD` (xsec2.py, walk.py), `svE` (pix/pmap/prof/dih3).

## Gotchas
- Build everything (a single-outfit build skips her body). Never `git commit -a` (built art is tracked). `git add tools/assets/heroine_outfits.py`.
- Before a geometry hunt, shoot the spot with `NORIM=1` and `LIGHTS=side`.
- A killed build keeps running: kill the process tree and give the turns back.

## Collaborators
Face (her shoulder graft line beside the neck corner is theirs), animation (helpers, her body build), the male hero lead (keep the generator parameterisable). Reports go to the main session.
