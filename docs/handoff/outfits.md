# Handoff: the heroine's body and outfits

From outfits lead successor 15 (su-lead-high), 13 October 2026, early. **No helper is running and no turn is held.** Start cold: `docs/team/README.md` ("Safety", "Working lean"), then this page. **Never read a whole file.** `heroine_outfits.py` is ~6,300 lines, mixed CRLF/LF: grep it, edit with exact byte replacements (handle `\r\n`), `ast.parse` after each edit.

## Start here (successor 15, 13 Oct early)
- **Branch** `worktree-agent-a5ca10091b08dc429` (integration merged at 5e482697). **Not merge-ready yet.** Worktree art = build **ls1** (code at da4e554f), uncommitted on purpose (unjudged as a set).
- **Coordinator rules (13 Oct):** fix a failing piece; don't gate it to save time. Gate only what can't be reached within reason, and say why. A judge sees only what varies the thing judged: garments on ONE face; skin tone only at tuck edges (lightest and darkest). Measured checks cover every clip; the judge looks at the worst cases.
- **Scratch.** M = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\59a43b82-cb5d-4a5a-bb8d-db67086387ea\scratchpad\outfits` (this session's runners, sheets, solver kit `leo_s`; keep). N = the 33ad5b17 `scratchpad\outfits` (builds land in N\<tag>; `N\solver_common.md` = every solver's brief; keep).
- **Build + measure loop (works, cheap: run it in the background, no runner needed):** `CUF=$M/cu_h.txt bash $N/b.sh <tag>` (full build + close-ups incl. Warden and Ranger feet, ~15 min), then a copy of `$M/h3_runner.sh` with `T=<tag>` (notch views, targeted motion check vs base n1 via O2/b.sh, close-up-camera coverage `$M/cuv_go.sh <tag> <outfits>`, game shots from `$M/game.txt`; ~20 min). Notch counts: `python $M/cnt3.py <dirs...>`. Clasp ball gaps: `N/clasp/dump_idle.sh <dir>` then `balls.py <dir>/arc_01_posed`.

### Judge round h (13 Oct): results
1. **PASS, ship:** Ranger heel (her foot inside the boot not drawn from 5 mm under the ankle, `RBOOT_GONE`; run_stalker tucked 44 px -> 0). Warden cups: no orange spot in our art (judge 49's spot was the campfire highlight; optional: slightly lower cup roughness). Glove items 2 (no open edges) and 3 (palms). Gold floor 0.08 is now the default (judge g4: warm gold at night, no change by day). By day the gold is still matte mustard: it needs lower roughness (0.2-0.3) with an edge-wear map, plus a waystation reflection probe (later, separate).
2. **FAIL, fix next (one solver or lead pass each, then ONE re-judge of all):**
   - **Leotard, bottom of the V** (`a_leo_f`, `a_leo_qr`, and the Look at 1x): the two leg-line bindings meet in a crumpled knot (stitch lines cross, the binding folds, dark tatters below). It already shows in h3 (hold off), so it is the old cut, not the solver's. Fix: one U curve (radius >= 10 mm) across the foot, one unbroken binding left to right with its stitch following, the front/gusset seam >= 5 mm underneath, no loose flap. Keep the solver's legal fix (da4e554f: `LEO_HOLD` on, `LEO_HOLD_Z`, `LEO_FOOT` 4 mm, `LEO_GUSSET_F` 0.026, `HOLD_CAP`): genital strip in the close-up views 40-48 frames -> 0, notch 202 px -> 0. Still open: chain_haul tucked 0/3 -> 7/80 (the judge: tint can't settle it; render the worst chain_haul frame in the real look; if a jagged line shows at the hip, start the full tuck 2 mm inside the edge there). 10 strip sample points still visible at rest near yaw 46 (her left): a thin margin. Solver kit `M\leo_s` (`dry.sh` arcanist-only ~4 min, `vis5.py` rest-pose strip count).
   - **Warden sabaton:** now `BOOTS.boot(... ANKLE_S - 0.06, 0.035, BOOTS.RANGER, "darksteel")` (~line 3668). The toes are gone, with no ankle gap and no poke-through at rest, but it reads as a patent-leather loafer. Fix: the greave's own steel material; 3-4 overlapping gold-edged lames over the instep with a rivet each side; a rounded toe cap and heel cup; a thin dark sole with no welt stitch and no heel block (a sabaton style in `tools/assets/heroine_boots.py`, which has only RANGER). Check the heel gap over a walk. (Laid on her foot it showed every toe; on her foot's hull it kept toe creases.)
   - **Clasp D2** (sits well: ball gaps 0.71/0.61 mm, fine in game): the cut-down U foot's flat top face reads as a pale ledge, a "top hat" from above (`a_clasp_hi`, `plunge_top`). Fix: a half-round foot section level with the bar (or a 45 deg bevel, ~1.5 mm deep). Keep the ball ends (the judge: the smooth-U fallback is worse). Code: grep `CLASP_D_`. The judge allows D2 as a stopgap in a merge (the fault is <= 3 px in play) if the coordinator wants.
   - **Glove item 4:** the thumb tip copies the nail edge (an overhang with a dark wedge, l_hand_inner_cb04; a pale lip on the thumb and index tips). Fix: smooth the last 6-8 mm of each finger (fill under the nail edge, >= 0.5 mm off her). New, macro only: dark flecks at the sleeve hem over the glove top, and a pale facet below at cb04: sink the glove's top 15 mm ~1 mm deeper under the sleeve (`GLOVE_TOP`).
3. **Then:** the legal flat run on the final art (`tools/legal/motioncheck/run.sh all`, all four outfits, threshold 1; each summary `FLAT: stray 0, binding 0, lone 0`, areola 0, genital 0), `dotnet test`, push, and a merge request to the coordinator with branch@commit and the sheet paths. Close-up coverage now: Warden and Ranger FLAT 0/0/0, areola and genital 0; Arcanist genital 0 at ls1.
4. **Later:** the Reaver, Ranger and Arcanist boots to AAA (owner), the Ranger's tucked ring at the wrist cuff, judge 10's spaulder list (`J\j10\verdict10.md`).

**Lessons:** easing a tuck over 10 mm changed nothing (her rows there are 4-20 mm apart): ease over >= 30 mm, or cap the standard rule too (`HOLD_CAP`). Run a "hold off" diagnostic build before blaming a new change: the strip leak and the V knot both predated it. `vault_opened` and `dig_boils` render black via `--zone`, so there is no dark-interior check of the gold floor yet.

## Done (successors 14 and 15)
Successor 15: Ranger foot hide (652f6f2e), gold floor 0.08 default and Warden sabaton as a lofted shoe (e16e7add, 8617fabc, 259f8677), leotard leg-line legal fix by solver (da4e554f); builds h1-h3, ls1; judges g4 (gold) and h (five items).
Glove weld and cuff (cd1db038); legal flat mode (181e4033, f1b6b04c, 45c94538); main merged (de8cef63); gold knobs (e9b9667f, 26887c69, 1967199d); clasp routes S, A, D, D2 (596a02a6, 467da49f, 87571429, f8f59d2b); leotard hold and tuck (419ede90).

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
