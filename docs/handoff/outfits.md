# Handoff: the heroine's body and outfits

From outfits lead successor 26 (su-lead-high), 14 October 2026. Start cold: `docs/team/README.md` ("Safety", "Working lean"), then this page. **Never read a whole file.** `heroine_outfits.py` is ~6,500 lines, mixed CRLF/LF: grep it, edit with exact byte replacements (handle `\r\n`), `ast.parse` after each edit. `heroine_rig.py` is CRLF.

## Paused here; next: (successor 26, 14 Oct, evening)
M = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\1847d1a6-6513-4947-9408-126dd43ed5f8\scratchpad\outfits` (this round's work). N = the 1cc516bc session's `scratchpad\outfits` (older tools: `N\gs2\gl.py`, `pd.sh`, `pd_F0` pose dumps). Builds are in `M\prop\<tag>\art`; `bash M\vb.sh <tag> K=V` builds all four plus the body (~9 min, its own blender turn). Run ONE build at a time: each writes `godot/art/outfit/outfit_glovesatin_diff.jpg`, so restore it after with `git checkout --`.

**Done this round**
- **Chest (CHEST_SMOOTH on by default, 5dba90b6).** The CT2 build was 2 vertices short of F0 because the chest's custom normals were set twice. `heroine_chest.chest_smooth` now hands them to `mend_folds` as `CN_OVERRIDE`, applied to `cn` before the fold check (a0686d94, 22c07116).
  - Max judge PASS on CT2's sheets (`M\chj\*.jpg` plus `N\s25\chest2\wedge_game_CT2.jpg`).
  - Poke-through on all four outfits: no new pokes (`M\poke\chest_poke_ct4.txt`).
  - UVs: the flips change interpolation in a few skewed quads, at most 0.0031 UV on her left upper-inner breast (`M\uvchk.py`). The coordinator asked for one textured close-up of that spot (F0 vs final) on the glove judge's checklist.
  - Later (judge): a hairline light tear at the cleavage bottom under Blender's single hard light only; the fold band; a red paint tick on the outer left breast and the areola ticks. These go to the "close-up skin detail" pass.
- **Body committed: d268fe8a** (heroine.glb = build B1c = CT4). `M\ident.py <F0 glb> <glb>` shows 31536 vertices; bones, inverse binds and every shape-key delta identical; weights identical except 258 chest points (at most 2e-4); elbow_point keys present. Animation and face are rebuilding on it.
- **Glove crook fixed** (e055270f, c678500f, 76b952d9): GLOVE_WFIT (top band weights fitted to her skin over 180 poses) and GLOVE_CROOK_WX ("0.4,12,32,20,35"). B1c and G1e have 0 A / 0 Ao on every frame of the six Arcanist clips, and the rest gap is unchanged. The judge needs `M\gs4\m3.py` (each arm against its own glove). The cast_raise "drift" was her forearms meeting (relayed to animation).
- **G2 dropped**: its V edge isn't clean (break L 1.0, R 0.46 mm). It stays off the sheet.
- **Legal on B1c's outfits** (all four): areola 0, strip 0, FLAT stray/binding/lone 0. Closest margins are below. Output and `count.txt` are in `M\legal`.

  | Outfit | L (cm) | R (cm) |
  |---|---|---|
  | warden | +0.69 | +0.48 |
  | arcanist | +2.10 | +0.48 |
  | ranger | +2.05 | +1.15 |
  | reaver | +0.88 | +0.21 |

  Arcanist leap_below_05 shows tucked skin as a cyan arm close to the camera (near-clip; not a legal area).
- **Tests:** dotnet 917 passed, 0 failed.

**In flight: the thumb web** (animation's white corner below the B1 thumb hole, hand on hip)
- 2afc9aec glove_hand_final (GLOVE_HAND_EXACT "0.5,0.9"): the glove's hand part takes her final skin blend. In the hip pose, the L thumb-hole edge is 4.57 -> 0.44 mm and the web edge 6.53 -> 0.71.
- 05e037f7 TUCK_WELD (arcanist) and GLOVE_EDGE_IN (10 mm): her skin's split copies (one point, 2-4 vertices) each took their own tuck and parted when tucked, giving a 5.5 mm crack, the dark slit and the white flap. Now there's one tuck mark per point, eased to none at the glove's open edges. The crack is 5.54 -> 1.16 mm at the L thumb hole (1.74 worst).
  - **This changes heroine.glb's COLOR_0 channel 1 at 216 vertices; every other accessor is byte-equal (`M\gs6\cmp0.py`). Tell the coordinator before committing B1j's heroine.glb.**
- Builds: B1j (default, all fixes) and G1j (GLOVE_STYLE=G1), in `M\prop`. Nobody has looked at them.
- `M\gs6\thumb_after_half.jpg` came out as full-figure frames (the l6.txt cameras don't close in), so it's useless. Shoot closes with `M\gs6\l_hip.txt` or `M\gs5\shoot.sh` (LOOKOFF on the thumb web), B1c vs B1j, and look at half size: is the flap and slit gone?
- Open:
  - The R staff-fist thumb stands 2.0 mm off her skin. The glove's weights already equal hers; it's her coarse thumb joint. Fit per-point weights over the clip poses, or leave it for the judge.
  - The knuckle edge bridges the finger webs 1.5-2.3 mm (old).
  - `TUCK_WELD=all` would weld the other three outfits' split marks (103/76/334 points): a later legal-scope change.
  - An m3 that ignores the staff grip (`M\gs6\m3e.py` is polluted).

**Next, in order**
1. Judge-ready check of B1j at the thumb, as above. If the flap is gone, B1j/G1j are the final outfits; if not, one high solver on the crack.
2. Commit the final art: B1j's four outfits, outfit_materials.json and outfit_tex.
   - The worktree's `godot/art/people` currently holds B1c's outfits, uncommitted, swapped in for legal.
   - Run legal only for what the diff touches: the tuck colours changed only near the glove edges (arcanist channel), so arcanist alone, unless `TUCK_WELD` widens.
   - heroine.glb goes to B1j only after the coordinator says yes (colour-only).
3. **The glove sheet:** G1 vs plain B1 on the final art.
   - `bash M\gshoot.sh B1:B1j G1:G1j` runs anim_review closes from `M\gsheet.txt` (incl. elbow_back) and the game shots from `M\ggame.txt` (art swapped in, then restored to HEAD and re-imported). Commit the final art first, so the restore doesn't undo it.
   - Then `python M\gsheet.py M\shots M\gl_sheet B1="B1: plain white satin" G1="G1: styled (amethyst-piped point, finger loop)"` makes `_play.jpg` and `_detail.jpg`. Look at every cut edge at 2x yourself first.
   - Then a max judge (budget 150k): rank the styles, pass F0's hands (open hand, fist on the staff, brim, elbow-back), and check the chest UV spot.
   - Note for the pick: G1's finger ring sits where the middle finger closes on the staff.
   - Then to the coordinator with the verdict path.
4. MERGE REQUEST `worktree-agent-a5ca10091b08dc429@<commit>`, with the tests and the legal counts above.
5. Then: the Reaver belt (`N\hip\need.py`), the Arcanist chest, stockings in the winning glove's trim, the nude groin fold, and the neck graft corner (Godot game shots only).

Other leads' scripts in `M` (anim, face subfolders) aren't ours.

## What changed this round (all default on)
- **The owner's leg band ("legs stuck together by fabric", every clip):** `heroine_rig._as_skin` shared a piece's whole limb weight out as the nearest skin's, so pieces at the inner thigh took the other thigh's bones: Arcanist stocking lace 0.98, Ranger cloth/leather 0.97, Reaver knee fur 1.00. **AS_SKIN_SIDES** (d0f5851f, eased in 0121f13f): per side only where the skin's share of the piece's own leg is under 30% (fully under 10%); elsewhere as before, since done everywhere it parted the crotch pieces from her (fin3: strip 11/6/4 frames). After: one-leg pieces 0 (Arcanist, Reaver); Ranger browncloth 0.41 and brownleather 0.12 at z 0.89-0.92, at her crotch (judged fine).
- **Arcanist:** BONING_CLIP (3362f1c3; boning a/d dived 10 cm into her past the leg line: the qr thorn and r_hand tab); BONING_TAPER (3385b11b); BIND_SLIM (slim leg-line roll under the crotch) with BIND_SLIM_STITCH (stitch row restored, 439ba9ae); LEO_ROOF_FIX (five bad roof samples, c3b33183). Off: LEO_SLOT_CAP, LEO_BRIDGE (vis5 cost).
- **Ranger** (439ba9ae): RING_ONE (each leg-line ring on one blend after the helpers' split: the speck), BIND_CLAMP 0.3 mm, BIND_REACH 8 mm (an edge pinch the loop finder drops; it is in the general finder and may touch other pieces).
- **Warden:** sabaton tone judged in game: one armour (PASS).

## Polish list (judge r2, none blocking)
Leotard foot: binding ends square at a_leo_f (955-961,705-711), taper into the thigh crease over ~3 mm; bottom stitch run ~1 mm onto the binding's front face; qr left end 3x4 px bluish fleck and 5 px step (turn-under radius, lining albedo); left leg-line pale rim (roughness on the roll's crest); under-crotch back: pointed binding ends and a creased pouch from below-hip cameras (one continuous binding into the strap, shrink-wrap <= 1 mm); sit_log front-low leg lines ragged when legs spread (Arcanist, Ranger); Ranger knob's dark tick (blend the binding corner). From judge fin2: sabaton heel crescent (lining value or rim in 2 mm), instep streaks and run_warden heel_bq2 crumple (rigid-weight the shell), sole corner ticks; glove middle-finger cap-seam kink (blend the subdivision boundary ring). The l_hand_outer_rest skin speck is her hip seen between fingers (ray-cast; correct).

## Lessons
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
