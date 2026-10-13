# Handoff: the heroine's body and outfits

From outfits lead successor 16 (su-lead-high), 13 October 2026. **No helper is running and no turn is held.** Start cold: `docs/team/README.md` ("Safety", "Working lean"), then this page. **Never read a whole file.** `heroine_outfits.py` is ~6,300 lines, mixed CRLF/LF: grep it, edit with exact byte replacements (handle `\r\n`), `ast.parse` after each edit.

## Start here (successor 16, 13 Oct)
- **Branch** `worktree-agent-a5ca10091b08dc429` (integration merged at ca6e9d97). All judge-h failures fixed by solvers, built, each legal-clean on its own outfit. **Next: one set re-judge**, then the legal run over all four, `dotnet test`, push, merge request. Built art stays uncommitted until the judge passes it.
- Scratch M = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\59a43b82-cb5d-4a5a-bb8d-db67086387ea\scratchpad\outfits` (keep). Each item's report and sheets: `M\s16_<item>\DONE.txt`. N = 33ad5b17's `scratchpad\outfits` (builds land in N\<tag>).
- **Final run:** `M\fin\fin.sh <tag>`: full build + close-ups (`fin\cu_fin.txt`: leotard, clasp, cups, feet, hands), skin-edge shots at the lightest and darkest tones (`TONE=#FFEDDE` fair, `#6E4F3F` deep; lookdev's new TONE knob, 8ba84808), cb04 hand shots, then the legal run over ALL four outfits and count.py (`fin\<tag>\legal_count.txt`). FIN_DONE ends `fin\<tag>.txt`. fin1 started 06:21.
- **Changed (defaults on):**
  - Leotard V (`s16_leo2`): one U (LEO_U 16 mm, 4 mm before the bridge cut), gusset 5 mm wider in front (LEO_GW), the U's edge held onto the gusset (LEO_UH, LEO_UG). Rest strip at game cameras 10 -> 0. For the judge: a thin dark sliver of the gusset's right side on the slot wall (a_leo_f, a_leo_qr); route if called: gusset off the walls behind GAP_F (0.96 -> 0.9) or its side edge held at 0.5 mm. Not done: chain_haul hip frame, yaw-46 margin.
  - Warden sabaton (`s16_sab2`; heroine_boots.py `sabaton()`, SABATON): 4 lames ~22 mm, 3.2 mm steps, domed toe cap, thin sole, steel, gold edges, rivets. Open: unevenness under the greave's edge, specks at the gold trim, a white sliver inside the sole (w_feet35lo).
  - Clasp D2 (`s16_clasp`): back laid on the corset (CLASP_D_LIE), inner rim 0.8 mm onto the binding (CLASP_D_RIN), jewel tilted 13 deg (CLASP_D_TILT), shallow bezel cup (CLASP_D_CUPOUT), half-round section (CLASP_D_ROUND). Ball gaps 0.80/0.66. Open: a low band behind the bezel from above.
  - Glove (`s16_glove`): fingertip caps relaxed over their hull (glove_tips, GLOVE_TIP_*), folds 39 -> 0; caps kept whole by the thinning (KEEP_FINE, e5d6afa0, first built in fin1); top sunk 1 mm (GLOVE_SINK).
  - Warden cups (`s16_areola`): dark leather lining under each cup's top edge (CUP_LINE): chain_haul's left view saw in under the plunge to her right areola (6 of 2080 frames -> 0). Judge question: leather or steel?
- **Judge fin1 (13 Oct): clasp PASS, cups + lining PASS (keep leather). FAIL: leotard V (blocker: the gusset shows below/beside the U as lobes, a flap and a 2nd stitch row), skin-edge binding spikes (plunge tooth by the clasp, a thorn and two spurs on the leg line), sabaton (instep lumps and nicks, white welt at the sole, spikes at the heel cup, lames read as stripes, greave vs sabaton material), glove (polygonal tips at 2x, a ragged patch where the index meets the thumb). Every fix route with pixel coordinates: `Minerdict_fin1.txt`; sheets `Min\q1..q6*.jpg`; judge crops `scratchpad\judge_fin\`.** Next: one solver per FAIL (leotard first: blocker), with that file's text as the brief; then fin2 via `fin.sh`, a re-judge of the failed items only, the merge request.
- **Legal fin1 (all four outfits)** was still running at handoff (nohup `Minin.sh fin1`): result in `Minin1\legal_count.txt` (FIN_DONE in `Minin1.txt`). Per-outfit runs on the same code were clean (arcanist, warden). `dotnet test`: 870 passed, 0 failed (the run then printed "Test Run Aborted", likely my 15-min timeout at teardown: rerun without one).
- **Lessons:** solvers at 200k ran out before building, twice: give 240-260k and "build within your first 60k". The legal run now covers 2080 frames per outfit (old runs 500); the new clips found the cup gap.
- **Later:** gold by day (roughness 0.2-0.3 + edge wear, waystation reflection probe); Reaver/Ranger/Arcanist boots to AAA; Ranger wrist ring; judge 10's spaulder list.

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
