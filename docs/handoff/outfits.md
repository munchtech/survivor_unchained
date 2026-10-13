# Handoff: the heroine's body and outfits

From outfits lead successor 14 (su-lead-high), 12 October 2026, late night. **Paused clean for a fresh coordinator. No helper is running and no turn is held.** Start cold from here: `docs/team/README.md` ("Safety", "Working lean"), then this page. **Never read a whole file.** `heroine_outfits.py` is about 6,000 lines with mixed CRLF and LF line endings: grep it and edit with exact replacements.

## Start here (successor 14 paused, 12 Oct late night)
- **Branch** `worktree-agent-a5ca10091b08dc429`. Main was merged in at de8cef63 (the close-up camera, animation's clips); dotnet test passed 844, failed 0.
- **Nothing is judged and nothing is merge-ready.** Several unjudged changes are now code defaults: the glove weld and cuff, the leotard edge hold and tuck, clasp D2. Judge each before any merge request, or gate it off.
- **Worktree art = build `clasp5/D1`.** That is the glove fix, the leotard hold (419ede90) and clasp D1 (50 deg horns, pulled in 4.5 mm), which is superseded by D2 in code. It is unjudged and uncommitted on purpose. Rebuild before any judge.
- **Scratch.** N = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\33ad5b17-6735-4f1b-843e-85f16b19e648\scratchpad\outfits` (keep it).
  - `N/solver_common.md` is every solver's brief: the build lock, `b.sh`, `locked.sh`, the motion check.
  - Parallel solvers in one worktree work, because the lock serializes builds.

### Open items: exact state and next step
1. **Arcanist glove** (judge 14's items, `N/j14/verdict14.md`).
   - Done (cd1db038): the gloves weld only along their own edges (`weld(joined=)`, `FOLD_SAFE`); open edges went from 73/18 to 0/0; the thumb spike was one of those zips. The cuff (`GLOVE_TOP` 0.10) sits 4 cm under the sleeve. Palms were reshot with the body hidden.
   - Sheet: `N/glove4/sheet.jpg` (20 tiles, listed in the glove solver's report in `N/glove4`).
   - Judge 14's notch wedge (item 1) was NOT the glove: it was her belly seen under the leotard's lifted leg-line edge (`N/notch/sheet.jpg`, `N/hem/sheet.jpg`). Item 5 below fixes it.
   - Next: one judge on `N/glove4/sheet.jpg` plus the notch tiles of `N/leo/sheet.jpg`, against verdict 14, blocking items only. Also: edges on 3+ faces 17/72 (no open boundary), and the sleeve binding 1-2 mm inside the glove at 355-357 deg, 5-7 mm above the hem (`N/hem`; fix it only if it shows at 1x).
2. **Clasp D2** (f8f59d2b, unjudged, NOT built). What failed, and why:
   - Measured cause: her spine bend, not her breasts. In her carriage the binding's U flattens.
   - Routes that failed: riding weights (c1/c2), two halves, S (`CLASP_SHEAR`: squashed to 40%), A (`CLASP_A`: the foot drops 14 mm under the cloth), D1 (pulled in, floating horns). The coordinator ruled out floating horns.
   - D2: the horns end at 25 deg (`CLASP_D_TH`), `CLASP_D_IN`=0, each tip `CLASP_D_ON`=3.7 mm onto the binding from its inner edge, the ball `CLASP_D_SEAT`=0.2 mm off it, lay-down on.
   - Why it should hold: the binding slides against the clasp almost only sideways (+1.3 to +3.1 mm out, up to 3.7 mm along), not in depth. Spare room inside the binding's width: 0.96 mm at 20 deg, 1.34 at 25, 0.62 at 30, 0.12 at 35; 40 doesn't fit.
   - Offline: rest gap 0.24 mm, posed 0.28; cloth 0.09-0.55 mm clear; skin 5-8 mm clear.
   - Unchecked: the laid horn tips against the cloth when posed, jiggle, the look (the tip runs ~3.7 mm across the binding). Fallback: 20 deg. If both fail: a smooth U foot with only the stone and bezel (the coordinator's call).
   - Next, in order:
     1. `bash N/clasp6/dry.sh d2` then `meas.py`.
     2. `CUF=N/cu_g.txt bash N/b.sh clasp6/D2`.
     3. Ball gaps: `N/clasp/dump_idle.sh`, then `balls.py`.
     4. Clips with jiggle on: `N/clasp3/clips.sh`.
     5. The Arcanist motion check.
     6. The sheet, g0 vs D2: a_clasp_* views, the Look, the close-up camera, the clips, 4x tips and stone.
     7. A judge.
   - Kits: `N/clasp2-6`.
3. **Gold** (game light is the reference; `N/gold2/sheet.jpg`, `N/gold4/sheet.jpg`). It isn't olive in game and has the right hue. It is dull by day (no pixels at 245+) and brown or black at night. The play camera barely sees it; it matters at the Look and the close-up.
   - Shader knobs, all default 0 (no change):
     - `debug_view` 4 is a gold mask (e9b9667f).
     - `gold_gloss`/`gold_rough` (26887c69) is the wrong lever: at night it goes black.
     - `gold_floor` (1967199d) adds emission of the gold's own mean x floor x mix(0.4,1,sky). At night it lifts brown toward brass (Arcanist night close-up 77,34,3 -> 118,75,35 at 0.15); by day the Warden gains 4-11 R. The Arcanist day numbers are unreliable: they fell, undiagnosed, maybe the pose or the 138-295 px mask.
     - Env trial knobs `GOLD_GLOSS`/`GOLD_ROUGH`/`GOLD_FLOOR` in People.cs and lookdev.gd.
   - Next: a judge on `N/gold4/sheet.jpg` (unviewed). If a floor of about 0.08-0.15 clearly helps at night without flattening the day, make it the default. Otherwise the gold stays as it is and goes to the owner as a note. The other option is a fill reflection probe in town (not tried). Separately, match lookdev's exposure and sky to the game, so judges see what players see (lookdev's gold is about 2.5x darker).
4. **Legal flat mode.**
   - Done: 181e4033 (garments flat grey), f1b6b04c (uncoded skin flat warm grey), 45c94538 (the assert counts lone pixels and exits 1; `FLAT: off`; run.sh threshold 1).
   - The judge FAILED the sign-off only for the run's scope.
   - Next: on the final art, `run.sh all` for all four outfits (~44-46 clips each) at HEAD, threshold 1. Each summary must show `FLAT: stray 0, binding 0, lone 0`, frames above 0, and 0 areola and 0 genital frames. Confirm that no `stocking` surface overlaps the genital strip or the 6 cm zones (sheer counts as cover). Then a judge signs off.
   - Margins now: Warden +0.27 cm, Arcanist +0.45, Ranger +1.23, Reaver +1.65.
5. **Arcanist leotard edges** (419ede90, unjudged, in the D1 art). The leg-line edge is held 1 mm off her over its last 12 mm (`held_edges`, `piece(hold=)`, `HOLD`), and her skin is tucked out to 5 cm (`HOLD_TUCK`).
   - Result: the notch wedge went from 202 px to 0, edge standoff median 1.9 -> 1.0 mm, coverage unchanged, FLAT 0/0/0.
   - **But tucked skin seen rose** (frames/px): chain_haul 0/3 -> 6/83, daggers_fore 0/5 -> 7/114, vault 0/0 -> 1/21, vault_back 0/0 -> 4/66. The crops (`181eef02 ...\legal\leo1\arcanist\crops\tuck_arcanist_0..5.png`) show cyan slivers and a sawtooth of tucked edge along the leg line in side views, so the deeper edge tuck shows as the cloth lifts in motion.
   - Next: a softer falloff, e.g. a full tuck only from ~10 mm in, and a gentler edge row. Check the real look of those frames at 1x and 3x, then a judge. Sheet `N/leo/sheet.jpg`; kit `N/leo` (edge.py, dry.sh, shoot_all.sh).
6. **Close-up camera coverage.** Kit `N/cuv` (views.sh, go.sh). Camera views: wheel 1.0 (pitch 9 deg, 2.77 m, FOV 24); idle 0.92 (3.02 m, FOV 26.6); moving cap 0.6 (4.91 m, FOV 34); she turns so the camera sits at -34.4 deg; idle drift ±17 deg.
   - Warden, Reaver, Ranger: FLAT 0/0/0, areola and genital 0.
   - Next: the Arcanist on the final art.
7. **Ranger boot heel** (diagnosed, not fixed; `N/rboot/sheet.jpg`, before only). In run_stalker her heel skin comes out through the boot's heel counter: up to 44 px, visible in the real look at 1x. The heel skin carries calf weight; the boot below the ankle is rigid on the foot, so the heel swings 43-51 mm against the boot.
   - Recommended fix: mark her foot skin inside each Ranger boot "not drawn" (mark 1), as for the Arcanist's hands in the gloves (the BODY_OUT block, ~line 5935), below where the boot turns rigid (~ankle - 5 mm). First check the upper limit over all 10 frames with `N/rboot/out1.py`.
   - Acceptance: tucked px 0 over the whole run in `N/cuv/go.sh`, no new flags.
8. Later: catch_breath side_02 (1 px of genuine tucked skin at the bodice's hip edge; the leotard work may change it); the Ranger's tucked-ring at the wrist cuff (chain_haul_over_08, a look item); judge 10's spaulder list (`J\j10\verdict10.md`); the boots.

**Cost lessons (this session):**
- Three of the solvers' premises were wrong: "breasts spread", "sleeve seam flap", "sleeve hem off the glove". Brief a solver to measure the cause first, and to build only after.
- Solvers ran out right after their build. Hand the post-build shoot, measure and sheet to a worker.
- Old handoff note fixed: HerPose does NOT spread her breasts; her spine bends.

## Done this session (successor 14)
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
