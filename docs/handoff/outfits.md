# Handoff: the heroine's body and outfits

From outfits lead successor 12 (su-lead-high), 12 October 2026. **Stopped clean for a new session; no helper running, no turn held.** Start cold from here: `docs/team/README.md` ("Safety", "Working lean"), RESUME's "Coverage", then this page. **Never read a whole file**: `heroine_outfits.py` is ~5,900 lines with mixed CRLF/LF, so edit it with exact replacements (`S\ed.py <file> <pairs.py>`, pairs.py defines `PAIRS=[(old,new),...]` in raw strings `r"""..."""`).

## Start here
- Branch `worktree-agent-a5ca10091b08dc429` (head at the end of this page's commit). Worktree art = build **e2** (code 96795831, all defaults), **unjudged, uncommitted on purpose**.
- Latest verdict: **judge 10**, `J\j10\verdict10.md` (its fix list, worst first, with boxes and acceptance, is the to-do list). Sheets: `J\j10\q*.jpg`. Judge 9: `J\j9\verdict9.md`.
- Passed by judge 10: the Ranger cup binding (judge 9's worst), the slot above the clasp, the 17th cap rivet slot, the clasp's rim lines. Judge 9 ruled the clasp span: keep the default (100 degrees; now 44 mm across).

## The owner's words and bar
"AAA", "never settle", "we are striving for perfection". Edges "perfectly cut and tailored professionally". Sex appeal drives, "tho not at the cost of looking bad"; full cups with "massive cleavage" fine; the Reaver near-naked. Coverage "pixel perfect ... not even a few pixels"; holes and see-through "really distracting and bad". Fit means tighter, not bigger. Nipple poke-through on Arcanist and Ranger, equal both sides (the owner once chose 1.5 mm over 3).

## What changed this session (all WIP, unjudged unless said)
- **Spaulder plates** (`rigid_again`): all three plates on one row, `SP_ROW` (collarbone .47, upper arm .26, twist .27). Godot dumps: cap vs band 1, 0 crossings, least gap 2.18 mm (was 11 crossing frames). Two solvers proved no per-plate row can keep j3's idle placement and pass; the shared row moves the plates 6-12 mm at idle, and judge 9 found they still nest well. `SP_SHARE` (share bone) exists, default off (it slid the cap 25 mm).
- **Neck end:** a soft 0-1 weight `nkw()` (`SP_NECKW` 12 mm) instead of hard masks in conform/weigh/clear_; `SP_NECKCUT` (reach; 0.032 changed nothing). Fit unchanged: idle worst 3.9 mm, median 0.9 (true underside metric `J\sv3\evalb.py <dumpdir>`; mdump's cell number reads high, ignore it). A5's crease and kink remain.
- **Ranger corset binding:** `BIND_FIT` (roll facing from a fitted plane), `BIND_FLAT` 4/8 mm with `BIND_FLATMAX` 0.8 mm (unbounded it folded the cup), `CORSET_ROLL` 1.0 mm proud. PASSED judge 10.
- **Clasp:** tips found on the cups' `_bind<k>` (they were looked for as `_trim`), 1.8 mm balls, `CLASP_PULL` 6 mm, new `claspgold` material. Judge 10: tips still FAIL (horns stand near vertical while the bindings run out at ~45 deg: the last 5-6 mm must follow the roll's V and the ball rest on it); the gold body still reads olive.
- **Rivets:** `pl_border_spots` widens a slot with no point (cap 17 rivets).
- **Nipple rise:** `NIP_RISE` 1.5 mm (was 0.7). Judge 10: still unreadable; tighten its shape (3 mm plateau to 0 at 7 mm, a normal imprint), and judge from a 90-degree profile.
- **Motion check:** `FOLLOW=<bone>` (make_motioncheck.py) rides cameras on a bone. **Broken:** with FOLLOW=clavicle_l the d2d frames miss her even at idle. Suspect `follow_skel` = the first Skeleton3D found (maybe an outfit's or hair's), or the t<0.5 reference. Fix it before any "spaulder in motion" sheet (judge 10 wants the idle worst frame shoulder-locked, plus the tinted tuck check on those frames).
- A leftover `dump(name, "3pre", ...)  # SOLVER1 TEMP` line in `piece()` writes only when `DUMP` names the piece; remove it when convenient.

## Next, in order (judge 10's list)
1. Clasp horns (above). 2. The Warden's 1 areola px (`warden_hit_chest_01`, legal check). 3. See-through: the Arcanist's hand through the glove at the wrist in catch_breath (left_04, over_05), and a skin sliver at a_clasp_hi 1155-1170,488-505. 4. A5 crease at the spaulder's neck corner. 5. Poke-through shape. 6. Gold colour (hue 30-40 deg, B <= 0.55 R). 7. Neck fit and hem in motion (after FOLLOW works). 8. A4 rivet halo (r_paul_back 813-847,172-200). 9. A6 armpit cusp. 10. The clasp's chisel facet, a knuckle in the Ranger's roll, the step where the two rolls meet. 11. Rivet spacing in 3D, the grey cap fleck. 12. New views: a_clasp_40 and a_clasp_side don't frame the clasp (fix in `J\cu.txt`), 90-degree bust profiles. Then the boots (the Ranger's by `heroine_boots.py`; the Arcanist's and Reaver's still `piece(limb(...))`).
**Lesson on cost:** four max solvers each spent 130-190k and three fixed nothing (diagnosis only). Better: give a solver one item and a named route; do small decided edits yourself; a runner builds (~20k tokens per build).

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
