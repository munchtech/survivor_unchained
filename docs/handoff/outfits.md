# Handoff: the heroine's body and outfits

From outfits lead successor 27 (su-lead-high), 14 October 2026. Start cold: `docs/team/README.md` ("Safety", "Working lean"), then this page. **Never read a whole file.** `heroine_outfits.py` is ~6,500 lines, mixed CRLF/LF: grep it, edit with exact byte replacements (handle `\r\n`), `ast.parse` after each edit. `heroine_rig.py` is CRLF.

## Paused here; next: (successor 27, 14 Oct, night)
M = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\1847d1a6-6513-4947-9408-126dd43ed5f8\scratchpad\outfits` (this round: `M\s27`). N = the 1cc516bc session's `scratchpad\outfits` (pose dumps `N\gs2\pd_F0` for `M\gs6\hr.py`). Builds: `bash M\vb.sh <tag> K=V` (all four plus body, ~9 min, into `M\prop\<tag>\art`); after each, `git checkout --` `godot/art/outfit/outfit_glove{satin,pipe,thread}_diff.jpg`. Arcanist only, with dumps: `M\s27\cut\ob.sh` (~2 min).

**Committed (on this branch)**
- **Final art d1be5c2a (+ dfe686ed, the glove texture .import with mipmaps).** heroine.glb = B1j: d268fe8a's body plus COLOR_0 ch1 at 216 hand vertices (tuck). Arcanist = B1j. Warden, Ranger and Reaver = B1c, because B1j only added UV float noise there and a 42-triangle reorder on warden gold.
  - Legal: Arcanist on B1j has areola 0, strip 0, FLAT 0, closest L +2.10 / R +0.48 cm (`M\s27\legal\count.txt`). Tests: 917 passed, 0 failed.
  - **MERGE REQUEST dfe686ed is sent and on hold.** It merges with animation's repack (integration's clips are built for the old rig). If the head changes before that merge, tell the coordinator.
- **The L thumb flap in the hand-on-hip clip is animation's.** thumb_01_l is turned 71° into the back of her hand; bare skin does it too (`M\s27\solve\e34.jpg`, `pen.py`). It went to animation as a gate.
- **Glove round 2 code, all default off** (210cc759, f1c238b9, 4fc84278, b4e3e865):
  - `GLOVE_IVORY`, `GLOVE_PIPE_MAT`, `GLOVE_THREAD_MAT` (materials, defined before `SPEC`);
  - `FL_DORS`, `FL_THUMB_BLEND` (`knuckle_exact`);
  - `GLOVE_EDGE_EASE` and `GLOVE_EDGE_EASE_IDX` (`glove_edge_delta` / `glove_hand_final`): the glove edge's blend averaged along each hand opening, wide only where it carries the index finger;
  - the satin rim 0.3 -> 0.4 (shader kind 5, shared, so B1 has it too).
  - Satin anisotropy was tried and removed: Godot's anisotropic path (even at 0, even written for every kind) flattened the leotard's grain from 8.68 to 3.58 (`M\s27\leo.py`). If it's reopened, use a glove-only shader.

**The glove pick (waiting on the owner)**
- Max judge round 3 PASSES G3 at the game cameras (`M\s27\gl3_verdict.md`; rounds 1-2 in `gl_verdict.md`, `gl2_verdict.md`).
- The owner's sheets: `M\s27\gl3_play_owner.jpg` and `gl3_detail_owner.jpg` (B1 vs G3), sent through the coordinator.
- G3 = build `M\prop\G3d`, env:
  `GLOVE_STYLE=G1 GLOVE_LOOP=0,0,0,0 GLOVE_POINTS=0,0,0,0,0 FL_DORS=0.006,0.014 FL_THUMB_BLEND=0.3,0.7 GLOVE_IVORY=1.789,1.470,1.142,223 GLOVE_PIPE_MAT=0.75,0.44,0.72,70,0.25 GLOVE_EDGE_EASE=0.010,0.005,0.003,0.010 GLOVE_EDGE_EASE_IDX=0.005,0.1,0.4`
- Measures: the posed knuckle loop turns at most 86-91° in 6 mm (as at rest; the hairpin was 162°); the thumb hole's tightest turn is 6.6-7.5 mm; hr.py's L knuckle in cast_raise is 2.49 mm (B1j 2.32, accepted). Output in `M\s27\cut\hr_e3.txt`.
- **If the owner picks G3:**
  1. Make that env the default for `ARC_GLOVE` (grep `GLOVE_STYLE = os.environ`) and rebuild, or commit G3d's files:
     - the Arcanist gltf and bin;
     - outfit_materials.json;
     - `outfit_tex` glove textures: `outfit_glovepipe_diff.jpg` (and its .import) is new;
     - heroine.glb: G3d's differs from the committed one only in COLOR_0 ch1 at 413 hand vertices (`M\gs6\cmp0.py`). Tell the coordinator before committing it: face and animation build on it.
  2. Keep Warden, Ranger and Reaver as committed (G3d's differ by float noise only).
  3. Run Arcanist legal (`M\s27\legal.sh`, ~5 min), then the tests.
- If the owner picks B1, the edge fix alone (`GLOVE_EDGE_EASE*`) fixes B1's index tooth and thumb flaps: build and check them.

**Then, in order:**
1. The R thumb in the staff fist stands 2.0 mm off her skin (her coarse thumb joint; R:thumb in hr.py).
2. The Reaver belt (`N\hip\need.py`).
3. The Arcanist chest.
4. Stockings in the winning trim (match their white to the glove's ivory: judge r3).
5. The nude groin fold.
6. The neck graft corner (Godot game shots only).
7. The close-up skin detail pass: knuckles, the cleavage hairline, the fold band, paint ticks, and the old dark tick and pale wedge at the L areola.

Logged and not fixed (beyond game zoom): the satin weave reads sandy in the closes; the satin sheen doesn't show on the forearm in play by day.
Judging rule (the owner, README "The finish line"): judges rule at the game's own cameras, critically; marks beyond that are logged; 2-3 rounds per item, then it closes as known.

## What changed this round (all default on)
- **The owner's leg band ("legs stuck together by fabric", every clip):** `heroine_rig._as_skin` shared a piece's whole limb weight out as the nearest skin's, so pieces at the inner thigh took the other thigh's bones: Arcanist stocking lace 0.98, Ranger cloth/leather 0.97, Reaver knee fur 1.00. **AS_SKIN_SIDES** (d0f5851f, eased in 0121f13f): per side only where the skin's share of the piece's own leg is under 30% (fully under 10%); elsewhere as before, since done everywhere it parted the crotch pieces from her (fin3: strip 11/6/4 frames). After: one-leg pieces 0 (Arcanist, Reaver); Ranger browncloth 0.41 and brownleather 0.12 at z 0.89-0.92, at her crotch (judged fine).
- **Arcanist:** BONING_CLIP (3362f1c3; boning a/d dived 10 cm into her past the leg line: the qr thorn and r_hand tab); BONING_TAPER (3385b11b); BIND_SLIM (slim leg-line roll under the crotch) with BIND_SLIM_STITCH (stitch row restored, 439ba9ae); LEO_ROOF_FIX (five bad roof samples, c3b33183). Off: LEO_SLOT_CAP, LEO_BRIDGE (vis5 cost).
- **Ranger** (439ba9ae): RING_ONE (each leg-line ring on one blend after the helpers' split: the speck), BIND_CLAMP 0.3 mm, BIND_REACH 8 mm (an edge pinch the loop finder drops; it is in the general finder and may touch other pieces).
- **Warden:** sabaton tone judged in game: one armour (PASS).

## Polish list (judge r2, none blocking)
Leotard foot: binding ends square at a_leo_f (955-961,705-711), taper into the thigh crease over ~3 mm; bottom stitch run ~1 mm onto the binding's front face; qr left end 3x4 px bluish fleck and 5 px step (turn-under radius, lining albedo); left leg-line pale rim (roughness on the roll's crest); under-crotch back: pointed binding ends and a creased pouch from below-hip cameras (one continuous binding into the strap, shrink-wrap <= 1 mm); sit_log front-low leg lines ragged when legs spread (Arcanist, Ranger); Ranger knob's dark tick (blend the binding corner). From judge fin2: sabaton heel crescent (lining value or rim in 2 mm), instep streaks and run_warden heel_bq2 crumple (rigid-weight the shell), sole corner ticks; glove middle-finger cap-seam kink (blend the subdivision boundary ring). The l_hand_outer_rest skin speck is her hip seen between fingers (ray-cast; correct).

## Lessons
- `M\gshoot.sh <col>:<tag>` removes the shots when col == tag (`rm -rf shots/$c` after shooting): name the column differently (s27 lost a 20-minute run).
- A shared-shader change reaches every outfit material: measure one untouched material (the leotard's high-pass std at brim_close, `M\s27\leo.py`) before and after. Godot's ANISOTROPY, even at 0, flattened the leotard.
- Stray `python -` at the start of a pasted command started the REPL twice this round (lead and solver): a reminder to check the first line of every bash command; stop it at once by task ID.
- Never run `python -` in any form (heredoc or `< /dev/null`): Python 3.14's REPL here loops and wrote ~200 MB each time (three times this round). Scripts go to files.
- A Haiku runner polling a long Godot batch burns its budget in minutes: run legal and shot batches as one background bash script (`M\legal_rest.sh`, `M\gshoot.sh`) and wait with `timeout 590 bash -c 'until ...'`.
- Blender custom normals are quantised on every `normals_split_custom_set`: set them once (mend_folds), or the export welds co-located copies and the vertex count changes.
- Never pipe an empty heredoc to python (`python - <<'EOF'` then `EOF`): on this machine it opens a REPL that spammed 775 MB of errors. Run scripts from files with `< /dev/null`.
- ICP on a finger slides along it: use a fixed vertex region (F1's weights) and multi-start along the axis, or the answer depends on the pivots you started from.
- Before a judge, look at every cut edge at 2x yourself: judge gl1 failed the sheet on teeth in the finger webs and a matte white, costing a second judge.
- Game shots read only the worktree's art (no BODYDIR): swap the build in, import, shoot, then restore the named files with `git checkout --` and re-import (`S\swapshoot.sh`, `S\opts4.sh`).
- Before fixing an outfit fault another lead found, check their render setup: three of judge j4/j5's outfit faults were a review tool without OUTFITSHADER=1 and a Godot import cache older than the merged assets (`.godot/imported/<file>-*.md5` source_md5 against the file). Re-shoot their camera on our assets (BODYDIR) first; it takes minutes.
- Measure the weights, not only the shapes: one export helper (`_as_skin`) put three outfits' leg pieces on the wrong leg, unseen by every close-up judge; `S\legs\xleg.py` catches it in seconds. A fix to shared export code needs the full legal run on all four (it moved the crotch pieces).
- Give solvers the cause and the gate numbers; three rounds on the knob ended in a judge ruling it correct: ask the judge "defect or correct?" before a third round.
- Helpers report to the coordinator unless told "do not SendMessage; your final message is your report".

## Later
Gold by day (roughness 0.2-0.3 + edge wear, reflection probe); Reaver/Ranger/Arcanist boots to AAA; Ranger wrist ring; judge 10's spaulder list; reaver.cape_bind1 43 verts 2.55 mm past overhang; the face judges' "faceted chest in the cinematic close" (needs the shot from the face lead; not looked at).

## The owner's words and bar
"AAA", "never settle", "we are striving for perfection". Edges "perfectly cut and tailored professionally". Sex appeal drives, "tho not at the cost of looking bad"; full cups with "massive cleavage" fine; the Reaver near-naked. Coverage "pixel perfect ... not even a few pixels"; holes and see-through "really distracting and bad". Fit means tighter, not bigger. Nipple poke-through on Arcanist and Ranger, equal both sides (1.5 mm).

## Setup and gotchas
The build reads `heroine_built.blend` in the 181eef02 session's `scratchpad\outfits\hs` (OSCR): keep it. Older kits J (1515c1de), S (ba85aba8), O2 (91211d34): keep. `CUF=<list> bash N/b.sh <tag>`: full build + close-ups under the lock. Build everything (a single-outfit build skips her body). Never `git commit -a`; add named files. Before a geometry hunt shoot with `NORIM=1 LIGHTS=side`. A killed build keeps running: kill the tree, give turns back. Game shots of the heroine need `--sex female`.

## Collaborators
Face (her shoulder graft line), animation (helpers, her body build; `heroine_rig.py` changed: AS_SKIN_SIDES affects only pieces, not her body), rendering (LOD: the glove's +31k tris), the male hero lead (keep the generator parameterisable). Reports go to the main session.
