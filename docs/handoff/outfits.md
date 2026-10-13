# Handoff: the heroine's body and outfits

From outfits lead successor 17 (su-lead-high), 13 October 2026 (coordinator wind-down). **No helper is running and no turn is held.** Start cold: `docs/team/README.md` ("Safety", "Working lean"), then this page. **Never read a whole file.** `heroine_outfits.py` is ~6,400 lines, mixed CRLF/LF: grep it, edit with exact byte replacements (handle `\r\n`), `ast.parse` after each edit.

## Start here (successor 17, 13 Oct)
- **Branch** `worktree-agent-a5ca10091b08dc429` (integration merged at 2053d8f3). Every fin1 FAIL has a fix in code, on by default, **unjudged**. **Next: build fin2, re-judge only the failed items on one face, then `dotnet test` (no timeout) and the merge request.**
- **Uncommitted, unjudged built art in W (keep, don't commit until judged):** godot/art/people/heroine.glb, heroine_outfit_{arcanist,ranger,reaver,warden}.{gltf,bin}, outfit_materials.json, the outfit_tex/ and art/outfit/ diffuse jpgs (bronze, browncloth, gold; new amethyst, bootleather, claspgold, down) and their .import files. The last W builds were by solvers (s17r1, s17sab2, one6w, spike round 2's): fin2 rebuilds it all.
- Scratch M = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\59a43b82-cb5d-4a5a-bb8d-db67086387ea\scratchpad\outfits` (keep). Each item's report and sheets: `M\s17_<item>\DONE.txt`. N = 33ad5b17's `scratchpad\outfits` (builds land in N\<tag>; `N\locked.sh` is the worktree's build lock). Solver rules used this round: `M\s17_RULES.txt`.
- **fin2 command:** `CUFIN=$M/fin/cu_fin2.txt nohup bash $M/fin/fin.sh fin2 > $M/fin/fin2.txt 2>&1 &` (bash paths). Full build + close-ups (cu_fin2 = cu_fin + Ranger leg-line rows r_leo_f/qr/ql), fair and deep tone shots, cb04 hands, posed heel shots (walk_tired and run_warden f5, `M\s17_lin\cu_heel.txt`, with DUMP=1), the legal run over all four outfits and count.py (`M\fin\fin2\legal_count.txt`, must be all zeros), FIN_DONE at the end of fin2.txt. ~1 h 15 min. Hand the wait to a su-runner.
- **After fin2, measured (runner):** leotard `outside_u.py` counts with masks remade by `M\s17_leo3\mkmask3.py` (chain3.sh has the chain); vis5 (`M\s17_leo2\vis5.py`); spikes `M\s17_spike\pspike.py` needs a DRY_SPLIT build: use the spike kit's dry + look on the fin2 snapshot. Glove poke at catch_breath f4 and a sword grip: `M\s17_glove` posetool.py skins the fin2 gltf into dumps e_cb04 / d_sword. Warden tone in a real game scene: from W/godot, `Godot --path . --resolution 2560x1440 -- --quick warden --zone waystation --time day --shot w_town --seconds 7` (and `--zone verge --time night`), output godot/.shots/.
- **Re-judge fin2 (one fresh su-lead-max judge, one face, the failed items only; list in `M\s17_fin2_notes.txt`):** leotard V (blocker), skin-edge spikes, sabaton (b welt, c heel spikes/slit, d lames; streaks polish only), glove tips, Ranger leg line's edge knob, greave lining at the heel.

## What changed this round (all default on, unjudged)
- **Leotard V, route (a) one piece** (`s17_leo2`, `s17_leo3`; 0b4305a1, 2cd2bcfd, af432de2, 228fdc84): LEO_ONE=1, the corset's sheet carried on under her crotch, no gusset, one leg-line binding a side. Dry: gusset px 0/0/0 (was 16882/2506/8684), vis5 game/mid/low 0/0/7 (was 0/27/10), COVER nearest bare 11.8 mm, legal flat all 0; one6w outside_u f 3 / qr 0 / ql 0 / half 1 / full 30. LEO_LIP (a lip trim) stays OFF: it fixed flecks but cost coverage (vis5 0/5/22). Warden/Reaver gussets untouched.
- **EDGE_SKIVE** (756c2854, lead): finish() pares arcanist.corset 3 -> 0.9 mm over its last 6 mm under its binding (the spikes and the V's-foot flecks are the 3 mm sheet out through its own roll). Dry: flecks 280+/315 -> 0/0; plunge roll 271 -> 132 verts >0.3 mm out; left plunge bump 2.58 -> 0.70 mm.
- **Spikes round 2** (`s17_spike2`, a7fa4689; built in W as its last build, legal flat areola/genital 0 over 2180): `sheet_untangled()` in plunge_fold (PLUNGE_UNTANGLE, on) and BIND_AREA_N (arcanist.corset only: the roll faces by area-weighted sheet normals; other outfits' bindings byte-identical). Gone: the tooth and the speck right of the clasp, the shard at a_clasp_hi, the hip spur. Plunge roll posed 132 -> 75 verts >0.3 mm, max 2.77 -> 0.77 mm (not visible). Sheets `M\s17_spike2\ba_*.png`.
- **NEXT, before or with fin2 (not done):** the tab at r_hand_outer_rest and the thorn at a_leo_qr are the square lower end of the boning channel (`arcanist.boninga`): taper its lift and thickness to flush over the last ~8 mm, or end it ~10 mm short (a small lead edit, then a dry look at those two views). Also unchecked: whether any view sees the leg-line roll's back end under the thong's foot (bind1, 6.8-7.1 mm, rest ~(0.002,0.065,0.944)) and 1.8 mm at the back of her hip (rest (-0.113,0.071,1.142)): add a low back and a below view to fin2's close-ups.
- **Ranger** (10f95ed8, RANGER_GUSSET): fin1's legal miss (genital strip 1 px in 2 frames, new clips axes_left/daggers_back) -> 0 over 2180 frames; COVER 7.2 -> 10.0 mm. Judge: a small knob on the edge roll where the leg line turns under the crotch.
- **Sabaton** (`s17_sab`, `s17_sab2`; 2cea158d, 4d8f169a, 5eb10438, 284d5242): SAB17 (3 lames + instep, 4 gold leading edges, 4.7 mm steps, Taubin relax, RIGID_UV), SAB_MATTE (dark matte sole: welt), GREAVE_RIM (greave edge slivers/folds dropped: heel spikes 15/11 -> 0), SAB_CHAMFER and SAB_RIM off. **Greave lining** (6a2cb4a4, lead): GREAVE_LINE, `edge_lining()` / `piece(line=)`, dark leather under the greave's lower edge (the slit over her heel). The coordinator ended the sabaton rounds: tone (e) is physical (greave faces the ground); judge it in a game scene, accept if it differs. Walk/run: 268 sabaton points under the greave at walk_tired f5 (fine if nothing shows outside).
- **Glove** (`s17_glove`, 8defd9a3, glove17a): caps divided once (KEEP_SUB), Taubin-rounded; face angle median 6.0 -> 3.3 deg, folds 0. Speck at (970,850) closed (skin between fingers, correct). +31k tris: note for rendering's LOD. Open: one 44 deg edge near the tips.
- **fin1 legal** (all four, 2180 frames each): Arcanist, Reaver, Warden all 0; Ranger 2 frames (fixed above).

## Lessons
- Max solvers at 250k often finish only diagnosis: give them the cause and a measure up front, "first dry build within 30-40k", and do one-line fixes yourself (the skive and the lining each took the lead ~15k).
- A thick sheet under a thin binding pokes through wherever the edge turns: skive first, before reshaping bindings or trimming edges.
- New clips in the legal run find old near-misses: the full 2180-frame run per outfit, every time.

## Later
Gold by day (roughness 0.2-0.3 + edge wear, reflection probe); Reaver/Ranger/Arcanist boots to AAA; Ranger wrist ring; judge 10's spaulder list; sabaton streaks (export slivers) polish; reaver.cape_bind1 43 verts 2.55 mm past overhang (not looked at).

## The owner's words and bar
"AAA", "never settle", "we are striving for perfection". Edges "perfectly cut and tailored professionally". Sex appeal drives, "tho not at the cost of looking bad"; full cups with "massive cleavage" fine; the Reaver near-naked. Coverage "pixel perfect ... not even a few pixels"; holes and see-through "really distracting and bad". Fit means tighter, not bigger. Nipple poke-through on Arcanist and Ranger, equal both sides (1.5 mm).

## Setup
The build reads `heroine_built.blend` in the 181eef02 session's `scratchpad\outfits\hs` (OSCR): keep it. Older kits: J = 1515c1de's `scratchpad\outfits`, S = ba85aba8's `scratchpad\o`, O2 = 91211d34's `scratchpad\o2`. Keep all.
- `CUF=<list> bash N/b.sh <tag>`: full build + Godot close-ups into N\<tag> under the lock. Dry builds (one outfit, own folder): each `M\s17_*\dry.sh`.
- Godot shots of a dry build: `M\s17_sab\gshoot.sh <list> <out> <clip> OUTFITGLTF=... OUTFITTABLE=...`.

## Gotchas
- Build everything (a single-outfit build skips her body). Never `git commit -a` (built art is tracked). `git add tools/assets/heroine_outfits.py`.
- Before a geometry hunt, shoot the spot with `NORIM=1` and `LIGHTS=side`.
- A killed build keeps running: kill the process tree and give the turns back.

## Collaborators
Face (her shoulder graft line beside the neck corner is theirs), animation (helpers, her body build), rendering (LOD: the glove's +31k tris), the male hero lead (keep the generator parameterisable). Reports go to the main session.
