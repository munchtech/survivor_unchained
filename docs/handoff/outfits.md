# Handoff: the heroine's body and outfits

From outfits lead successor 25 (su-lead-high), 14 October 2026. Start cold: `docs/team/README.md` ("Safety", "Working lean"), then this page. **Never read a whole file.** `heroine_outfits.py` is ~6,500 lines, mixed CRLF/LF: grep it, edit with exact byte replacements (handle `\r\n`), `ast.parse` after each edit. `heroine_rig.py` is CRLF.

## Paused here; next: (successor 25, 14 Oct, late)
N = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\1cc516bc-727d-4e77-9f0e-4ed15fbf8ea6\scratchpad\outfits`; my work is in `N\s25`. Scripts there:
- `vb.sh <tag> K=V` (full build into `N\prop\<tag>\art`, takes its own turn)
- `vbs.sh` (the same, `SCRIPT=` another build script)
- `ar.sh <out> <list> K=V` (anim_review shots)
- `acc.sh <tag>` (the build swapped in, then the waystation close-ups own/sbd/ownn/sbn, then restored and re-imported)
- `dump.sh <art> <json>` (game skeleton dump from a build)
- `gcmp.py <artA> <artB>` (outfits vertex compare)
- `throat_geo.py <before glb> <after glb>`
- `hp4.py <acc dir>` (face's throat high-pass vs prototype ta3)
- `wedge\geo.py`, `wedge\bl.py` (chest dihedral stats; Blender light-azimuth renders)

Lists: `chest_nude.txt`, `jig.txt`, `neck.txt`, `bh\list*.txt`.

- **Rig-final trial body F0** (`N\prop\F0\art`, code = HEAD with CHEST_SMOOTH off): hand pivots plus the left PIPs and DIPs, throat_fill on, back_of_hand OFF (bcac177d), and correctives rebuilt.
  - **Correctives:** F1 had none, because the skeleton dump was stale. The fresh dump (810d51bf, `tools/anim/data/heroine_skeleton.json`, from P6's armature) makes the log read "RIG correctives: 25 pieces keyed", with elbow_point_l/_r on the body and pieces, as integration has them.
  - **Final-build gates:** the log has no "no game skeleton matches", and the GLB carries elbow_point_l/_r.
  - `N\handpivots_left.json` was rewritten from F0 (right vs handpivots.json 0.05 mm).
  - **Coordinator: GO.** F0 is rig-final. Animation copies `N\prop\F0rt` into its own worktree (uncommitted) and refits now. No heroine.glb or outfit binaries until the final commit. Every later heroine.glb keeps bones, weights and every shape-key delta identical to F0; report that check with the final build.
- **Back of hand: judge bh1 FAILED back_of_hand** (faceting: a ~7 mm mesh can't hold per-knuckle shapes); it's off. P5 = P1 at the hand shots (`N\s25\bh\p156.jpg`). F0's hands still need a judge's pass: fold it into the glove sheet's judge (hand closes).
  - Post-F1 item "close-up skin detail" (coordinator): one max solver picks between a broad knuckle cap (<= 1.5 mm, half-width >= 20 mm) with the detail baked into the skin normal map, or denser skin at the hands (and the chest if chest_smooth falls short).
- **Throat: PASS** (judge on F0, plus a fill-off check; `N\s25\acc\F0\throat_cmp.jpg`, `N\s25\neck\fill_onoff.jpg`). 208 points moved, at most 8.48 mm, band only; the normal profile equals the prototype.
  - Log for a later neck pass, after confirming them in a game shot (the coordinator says judge rim issues only in Godot game shots): a silhouette step at the neck's side, a glint on the left trapezius, a faint line on the back of the neck. All three are identical with the fill off, so they're the old graft corner; the fix is widening the fill around the sides.
- **Chest wedge = body faceting** (light-azimuth test; the sculpt's slivers).
  - Round 1, `tools/assets/heroine_chest.py` (UNCOMMITTED) with its hook in heroine_outfits.py's BODY_OUT block (UNCOMMITTED, knob CHEST_SMOOTH default 0), was FAILED by its judge: a new dent low on the right breast inside, a glint and pit at the left armpit, the wedge only softened.
  - Round 2 is a **su-lead-max solver RUNNING** (tags CT*, sheets to `N\s25\chest2`). It reports by SendMessage to the s25 agent id; ask the coordinator to relay. Gates: dihedral p90 <= 9 / p99 <= 18 per breast, normal move <= 1 mm, no new crease, poke-through no worse, nothing that can't be undone. Then a max judge on the four sheets, as in `N\s25\chestj` (wedge_game, nude_front/tq, jiggle) plus Blender `chest_sheet`.
  - If it passes: CHEST_SMOOTH default 1, commit heroine_chest.py + the hook, and legal on all four (the coordinator asked, since it's under every garment).
- **Gloves:** the builder's WIP is committed (bd9ab30d). GLOVE_STYLE="" is vertex-identical on all four (F0 vs F0h).
  - A **su-lead-high solver is RUNNING** (`N\gs2`; tags B1a/G1x/G2x), reporting by SendMessage to s25. Its jobs: (1) the elbow-fold poke-through at the crook in the brim pose, for every style including the B1 default (gate: 0 skin outside the glove at the brim frame and the worst flexion of six Arcanist clips); (2) G1's points onto the glove's own weights, plus an elbow-back shot; (3) G2's lace >= 0.3 mm over the built binding tubes, the knot seated within 0.5-1 mm, the V placement. G2 drops if it isn't clean in one round.
  - Then **the one glove sheet** on the final body: G1, G2 (if clean), plain B1. Reuse `S\sheet_opts.py` (cols G1/G2/B1) with `S\gloves2.txt` via ar.sh (BODYDIR, LIGHTS=town, 1920x1080) and the game shots `S\gl.txt` (as `S\swapshoot.sh`), plus the elbow-back shot. A max judge ranks them, and also passes F0's hands. Then to the coordinator for the owner. Note for the pick: G1's finger ring sits where the middle finger closes on the staff, and animation checks that grip with whichever glove wins.
- **Then the final build:** F0's code + CHEST_SMOOTH (if passed) + the glove fixes. Gates as above, plus bones/weights/keys identical to F0. Legal (tools/legal/motioncheck, docs/handoff/legal.md) on all four. Tell the coordinator before committing heroine.glb; then `MERGE REQUEST` with animation's refits, tests (`cd godot && dotnet test tests/Tests.csproj`) and legal counts.
- **Reaver belt (the coordinator's call):** garment-side, Reaver-only, AFTER the body build and the glove sheet. The belt's front band and buckle ride up the thigh like panel_front, or the belt sits higher. True gap per `N\hip\need.py`: belt/buckle/panel need sit 48/23/30, run 62/41/28, sprint 84/69/52 mm. The groin-crease corrective was dropped (patch kept in `N\s25\crease_solver.patch`).
- **Backlog:** the nude groin fold is crumpled at deep flexion even in P1 (98-172 creases sharper than 90 deg); a judge looks at nude sit_log first.

## What changed this round (all default on)
- **The owner's leg band ("legs stuck together by fabric", every clip):** `heroine_rig._as_skin` shared a piece's whole limb weight out as the nearest skin's, so pieces at the inner thigh took the other thigh's bones: Arcanist stocking lace 0.98, Ranger cloth/leather 0.97, Reaver knee fur 1.00. **AS_SKIN_SIDES** (d0f5851f, eased in 0121f13f): per side only where the skin's share of the piece's own leg is under 30% (fully under 10%); elsewhere as before, since done everywhere it parted the crotch pieces from her (fin3: strip 11/6/4 frames). After: one-leg pieces 0 (Arcanist, Reaver); Ranger browncloth 0.41 and brownleather 0.12 at z 0.89-0.92, at her crotch (judged fine).
- **Arcanist:** BONING_CLIP (3362f1c3; boning a/d dived 10 cm into her past the leg line: the qr thorn and r_hand tab); BONING_TAPER (3385b11b); BIND_SLIM (slim leg-line roll under the crotch) with BIND_SLIM_STITCH (stitch row restored, 439ba9ae); LEO_ROOF_FIX (five bad roof samples, c3b33183). Off: LEO_SLOT_CAP, LEO_BRIDGE (vis5 cost).
- **Ranger** (439ba9ae): RING_ONE (each leg-line ring on one blend after the helpers' split: the speck), BIND_CLAMP 0.3 mm, BIND_REACH 8 mm (an edge pinch the loop finder drops; it is in the general finder and may touch other pieces).
- **Warden:** sabaton tone judged in game: one armour (PASS).

## Polish list (judge r2, none blocking)
Leotard foot: binding ends square at a_leo_f (955-961,705-711), taper into the thigh crease over ~3 mm; bottom stitch run ~1 mm onto the binding's front face; qr left end 3x4 px bluish fleck and 5 px step (turn-under radius, lining albedo); left leg-line pale rim (roughness on the roll's crest); under-crotch back: pointed binding ends and a creased pouch from below-hip cameras (one continuous binding into the strap, shrink-wrap <= 1 mm); sit_log front-low leg lines ragged when legs spread (Arcanist, Ranger); Ranger knob's dark tick (blend the binding corner). From judge fin2: sabaton heel crescent (lining value or rim in 2 mm), instep streaks and run_warden heel_bq2 crumple (rigid-weight the shell), sole corner ticks; glove middle-finger cap-seam kink (blend the subdivision boundary ring). The l_hand_outer_rest skin speck is her hip seen between fingers (ray-cast; correct).

## Lessons
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
