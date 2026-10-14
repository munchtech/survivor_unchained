# Handoff: the heroine's body and outfits

From outfits lead successor 23 (su-lead-high), 14 October 2026. Start cold: `docs/team/README.md` ("Safety", "Working lean"), then this page. **Never read a whole file.** `heroine_outfits.py` is ~6,500 lines, mixed CRLF/LF: grep it, edit with exact byte replacements (handle `\r\n`), `ast.parse` after each edit. `heroine_rig.py` is CRLF.

## Paused here; next: (successor 23, 14 Oct)
S = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\d7e64ca2-6832-41bd-8851-2fc0175ecc1b\scratchpad\outfits` (mine; keep). X = successor 22's scratch (34daaf5d; keep; tools in `X\h22`, `X\fin`, `X\chest`). Integration is merged at 64eb9b62 (lips B3-15; Godot re-imported). The worktree's art is still F1's (080103ba): no new heroine.glb is committed.
- **The owner's glove pick is PENDING.** The sheets went to the owner after judge gl2 passed them (SEND): `survivorsunchained_inputs\scratch_d7e64ca2\outfits_s23\gloves_options_play.jpg` and `gloves_options_detail.jpg`. Both judges lean to the white or black glove: gl1 (NOT YET on the first sheet: jagged knuckle cut, B1 matte) leaned B2 60%; gl2 leans B1 60/40 over B2.
  - Builds: A = `ARC_HANDS=glove` in `S\prop\As3`; B1 = default white satin fingerless in `S\prop\B1y`; B2 = `ARC_GLOVE_MAT=gloveblack` in `S\prop\B2y`; C = `ARC_HANDS=bare` in `S\prop\C`.
  - After the pick, set the defaults (`ARC_HANDS`, `ARC_GLOVE_MAT` in arcanist(), ~line 5440). The pick rides the next body build.
  - **gl2's notes:**
    - A has two pale slivers at its knuckle creases in the fist close-up (a mesh split in the full glove; the `glove_shape`/`glove_tip_k` branch, ~line 5765). Fix them ONLY if A is picked.
    - A faint level line across her throat (body, every option): the face lead's; the coordinator has it.
  - Polish, not blocking: the inner-elbow notch at the glove top seen from below; the hem end ~1 mm proud at the index side in the open hand.
- **Code this round** (`tools/assets/heroine_outfits.py`, WIP until the pick):
  - 2de8efb4 (solver):
    - `glove_top_weights(objs)` refits the glove's weights in its top 20-35 mm after `rig_helpers.apply` (knobs `GLOVE_WSMOOTH`, `GLOVE_WSMOOTH_BAND`).
    - A's branch now takes `glove_top_cut`, `glove_a_lift` and the tuck; `GLOVE_FIELD_OVER` is 0.04; `piece()` accepts a callable lift.
    - Left over: the rim wiggle max is 0.43-1.6 mm (an unexplained rest-pose notch on B1's right arm), and skin still pokes through by 0.3-2.4 mm in the elbow fold in the brim pose (the lever: a steeper first 10 mm of `GLOVE_TUCK_*`). The solver's tools are in `S\gs` (`sum.sh <tag>`, `dd.sh <tag>`).
  - 6482281e:
    - `knuckle_exact(sd)` (knobs FL_EXACT, FL_WEB_GAP 2 mm, FL_V 8 mm, FL_P1 = F1's right-hand first-bone lengths). The line is set from her 02 joints less FL_P1, so it stays at her webs when the 01 pivots move. After the body build, check the printed "GLOVE l/r knuckle line" mm.
    - Satin roughness: glovesatin 0.3, gloveblack 0.46.
- **The next body build** (ONE build, after the pick):
  1. **Hand pivots:** `...\d7e64ca2-...\scratchpad\anim\handpivots.json` and `handpivots.md`, in hand_r rest space.
     - MCP at 0.48 of the hand, P2 = 0.65 P1: index 105.9, middle 101.5, ring 96.9, pinky 96.7 mm from the wrist.
     - The palm skin from the new knuckle line to the webs goes onto each 01 bone in 14 mm smoothstep lanes; the DIP skin ramps over 5 mm.
     - The thumb MCP moves 12.4 mm back; the thumb_01 skin past it goes to thumb_02 by a +-10 mm smoothstep.
  2. **The left hand is NOT made a mirror** (the coordinator's call). Her body is asymmetric (the sculpt: 3.6 mm median; the left hand 1.2-2.4 mm per finger, the max at the wrist). Place the left pivots by the same rule on the left's own skin, and write `handpivots_left.json` beside the right table for animation. Tools: `S\knk\web.py`, `land2.py`, `sym.py`, `symmax.py`.
  3. **Back-of-hand reshape** (approved; a su-lead-high numeric solver). The back-of-hand drop sits at the webs (middle 117-129 mm from the wrist).
     - Move it 15-20 mm toward the wrist so it centres within 3 mm of each hand's new MCP, with a soft metacarpal-head rise.
     - Only back-of-hand vertices in the 100-130 mm band move; the vertex diff must show nothing else moves.
  4. **The Reaver front panel's top band weights:** `...\anim\panelweights.json/.md` (panel3; the coordinator says when it's in).
  5. **The pick's defaults.** Then run legal on what `git diff --stat` of the built files shows (README "Scope checks"): the Arcanist at least (`ONLY=arcanist bash X\fin\legal_only.sh <tag>`), plus any outfit the build re-tessellated.
     - motioncheck plays clips in real time, so the panel's lag is handled.
     - lookdev CLIPFRAME and anim_review START seeks catch the panel mid-fall.
  6. **Before committing heroine.glb:** rebuild on the current integration, and tell the coordinator first (face rebases its mouth build m11 onto it). F1 merges with animation's re-fits, through the coordinator. Tell the coordinator when the body build is final, so animation fits the final hand.
- **Then:**
  - The Arcanist chest fix, as the owner ordered it (unchanged from successor 22): on the cap-sleeve top, zone edges over 3-4 cm, blur the clearance push over 3-5 cm, ease the binding 1-2 cm, cup grain 3-4x finer at half strength (`taut_gore`, `plunge_fold`, `mls_flat` in arcanist()). First show the weights as vertex colours at rest. The before sheet is `X\chest\sheet_chest.jpg`. Judged before and after.
  - Then the stockings (`SHEER_UNTANGLE`, `X\h22\stk`), then polish.
- **Answered for the coordinator:**
  - The Ranger thigh "black line" is `ranger.pant_seam` (designed; the light brown pant reads near skin in warm light).
  - The flare wrist band is the fingerless design on F1's art.
- **Tools:**
  - `S\vb.sh <tag> K=V..`: a full build into `S\prop\<tag>\art`.
  - `S\ar.sh <out> <list> BODYDIR=.. LIGHTS=town W=1920 H=1080`: anim_review frames; the list `S\gloves2.txt` includes open_hand.
  - `S\swapshoot.sh <tag>`: game shots, which read only the worktree's art. It copies the build into godot/art/people, imports, and shoots `S\gl.txt` (Waystation, `--close 1` and `0.6`, `--time day|night`). Afterwards restore with `git checkout --` on the named art files and re-import: see `S\opts4.sh`. `--close` works only in a town zone.
  - `S\sheet_opts.py <shots dir> <out prefix>`: the options sheets.

## What changed this round (all default on)
- **The owner's leg band ("legs stuck together by fabric", every clip):** `heroine_rig._as_skin` shared a piece's whole limb weight out as the nearest skin's, so pieces at the inner thigh took the other thigh's bones: Arcanist stocking lace 0.98, Ranger cloth/leather 0.97, Reaver knee fur 1.00. **AS_SKIN_SIDES** (d0f5851f, eased in 0121f13f): per side only where the skin's share of the piece's own leg is under 30% (fully under 10%); elsewhere as before, since done everywhere it parted the crotch pieces from her (fin3: strip 11/6/4 frames). After: one-leg pieces 0 (Arcanist, Reaver); Ranger browncloth 0.41 and brownleather 0.12 at z 0.89-0.92, at her crotch (judged fine).
- **Arcanist:** BONING_CLIP (3362f1c3; boning a/d dived 10 cm into her past the leg line: the qr thorn and r_hand tab); BONING_TAPER (3385b11b); BIND_SLIM (slim leg-line roll under the crotch) with BIND_SLIM_STITCH (stitch row restored, 439ba9ae); LEO_ROOF_FIX (five bad roof samples, c3b33183). Off: LEO_SLOT_CAP, LEO_BRIDGE (vis5 cost).
- **Ranger** (439ba9ae): RING_ONE (each leg-line ring on one blend after the helpers' split: the speck), BIND_CLAMP 0.3 mm, BIND_REACH 8 mm (an edge pinch the loop finder drops; it is in the general finder and may touch other pieces).
- **Warden:** sabaton tone judged in game: one armour (PASS).

## Polish list (judge r2, none blocking)
Leotard foot: binding ends square at a_leo_f (955-961,705-711), taper into the thigh crease over ~3 mm; bottom stitch run ~1 mm onto the binding's front face; qr left end 3x4 px bluish fleck and 5 px step (turn-under radius, lining albedo); left leg-line pale rim (roughness on the roll's crest); under-crotch back: pointed binding ends and a creased pouch from below-hip cameras (one continuous binding into the strap, shrink-wrap <= 1 mm); sit_log front-low leg lines ragged when legs spread (Arcanist, Ranger); Ranger knob's dark tick (blend the binding corner). From judge fin2: sabaton heel crescent (lining value or rim in 2 mm), instep streaks and run_warden heel_bq2 crumple (rigid-weight the shell), sole corner ticks; glove middle-finger cap-seam kink (blend the subdivision boundary ring). The l_hand_outer_rest skin speck is her hip seen between fingers (ray-cast; correct).

## Lessons
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
