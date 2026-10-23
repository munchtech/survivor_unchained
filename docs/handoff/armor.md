# Handoff: armor and weapons (smart slot parts)

Read README ("Working lean", Safety), RESUME's top, then this page. Worktree (lead 6) `.claude/worktrees/armor-5`; earlier `.claude/worktrees/armor-1`, branch `armor-1` (godot/assets is a junction to its own public/assets: never stash, reset --hard or checkout .). Marionette work: `C:\Users\munch\Desktop\Marionette`, branch `armor-1` (main's uncommitted edits there are not ours: never commit them).

## Paused here (Armor 18, 22 Oct, shoulder-only session); the arm root became a BODY item
**Update 23 Oct:** the owner approved the arm-root source fix and it ran on armor-7. Its state and next steps are in `docs/handoff/body.md` ("Arm root (Body 1)"). BJ1 passed the arm at 1:1; an owner-angle reshoot is still due. The armor items below still stand: the R1/R2 clips are unjudged, and nothing is merged.
Worktree `.claude/worktrees/armor-7`, branch armor-7 (junction worktree). Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\543ece4a-9bcd-4cea-b6df-915822bec5eb\scratchpad\armor18` (texts backed up to `survivorsunchained_inputs\scratch_543ece4a\armor18`): cj2.md and rj1.md (judge briefs), r1/r2/d1 briefs and their scripts (r1\araise.py torso A per frame; r2\hl.py, axe.py, wpn.py; d1\m1-m4.py mesh, weights, collapse), run.sh with list1-3.txt (shoots), sheet2.py.
- **CJ2 (max) on C2: FAIL, far** (`godot/.shots/armor17/c2/verdict_cj2.md`). Correctives can't make the shape.
- **R1 (d2eb0c5c, a34f735f): reaver_show, catch_breath and flask_drink restaged to A <= 90** (117/117/99 -> 83/89/88). RJ1 (max) passed the shoulder; **the owner and main overturned it on reaver_show's peak.** These crops in `owner_frames_22oct\` are all FAIL; calibrate every judge on them: reaver_show_shoulder_top_facets_r1.png, reaver_show_armpit_notch_r1.png, reaver_show_shoulder_r1_1to1.png, reaver_show_upper_arm.png.
- **R2 (e65deb17), unjudged and unshot:**
  - catch_breath plays only with both hands free (`logic/Play/FreeHand.cs` Both, FreeHandTests); held pieces had gone 60-90 mm into her thigh. Its hair push is polished.
  - reaver_show's axe head stays in frame.
  - New `--sheathed` shot arg (PlayerView's hold line).
  - Judge list `list3.txt`. dotnet 1076/0/8.
- **D1 diagnosis (numbers): the ARM ROOT is the mesh first, then the weights. FAR.**
  - The arm is the coarsest skin on her (decimated triangles, no loops). Median edge: upper arm 1.27 cm (slivers to 6.2 cm), deltoid 0.96, breast 0.74, face 0.18.
  - At the close-up (2.80 m, 24 deg, 9.4 px/cm, LOD0, smooth normals) the outline chords are 11-13 px with 14-22 deg corners.
  - The bicep crease is the twist hand-off across one 6.2 cm sliver.
  - The pit is at the 4-bone cap and already pinched in the bind pose.
  - Upper-arm section keeps 0.79/0.70 of rest at A 82.
- **Proposed source-fix round (NOT started; the owner decides):**
  - Remesh a patch from mid-clavicle and the pit to the elbow crease at about 0.4 cm, with a deltoid cap and an opened pit.
  - Transfer the weights and smooth the twist band; project the UVs and re-bake; rebuild the correctives.
  - Then the lead-8 chain: NAPE=0, nape_post, neck graft restore (check it), build.py --all, cover.py, heroine_lod.py, reimport. Re-judge the arms-down frames too.
  - Cost 300-400k, 8-12 h; risk high.
  - The lead suggests it become a body item with its own lead, and asks whether a clean MakeHuman/Marionette arm could be grafted instead.
- **MR state: nothing to merge.**
  - armor-7 holds the earlier judged pieces, the C1/C2 art and the R1/R2 clips, unjudged as a whole.
  - heroine.res and heroine_clips.json are packed locally, not committed.
- Wearcheck over 22 clips, correctives off vs on: `armor18\wc_off` and `armor18\wc_on` tables.

## Paused here (Armor 17, 22 Oct, coordinator wind-down); history
Worktree `.claude/worktrees/armor-7`, branch armor-7 (junction worktree: remove `godot\assets` before merging integration, remake after). Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\67a4f142-1816-491a-be2f-c6d6488eb39a\scratchpad\armor`. Subfolders: a1 = leak audit and AJ1; c1, c2 = corrective briefs and frames; n3, n5, s1 = solver briefs; `shoot2.sh` and `run.sh` = shoot with a turn (run.sh's 4th arg `import` reimports first). API judges are blocked until 1 Nov (usage limit): every judge is a su-lead-max subagent.

**1. TOP: her raised shoulder and armpit** (the owner on reaver_show's armpit: "oof thats bad").
- Calibration frame: `survivorsunchained_inputs\owner_frames_22oct\reaver_show_armpit.png`. It shows a flat shoulder top breaking into a hard corner, no armpit hollow (a single crease line), and no deltoid.
- It is NOT parked: it leaks into close-range poses. The torso-axis sweep is `godot/tools_scenes/arm_raise_scan.gd`; A = upper arm vs the torso's down axis, 90 = level. Close-range clips above level: reaver_show (A 117), catch_breath (117), flask_drink (115, C04's cinematic), warden_show (104). lie_side_wake (157) is in no cinematic. Combat clips are play camera only.
- Diagnosis: the skinning, not the r2 fold morphs.
- r1 (C1, 40ad9164): delta-mush pose-space shapes (`tools/assets/shoulder_psd_post.py`, body post step 7c; `Play/ShoulderPsd.cs`, driven by HerRaise). Max CJ1: FAIL, medium. "Smoothed targets can't add shape." Keepable: zero effect up to level.
- r2, the approved REBUILD (C2: afc69dfd code, aefb019e art), installed and **UNJUDGED**:
  - a clavicle lift of 0.36*(A-90), the larger of the clip's own and the target, with the hands kept (`Play/ClavicleLift.cs`, `Actors/HerShrug.cs`, `helpers.shrug`);
  - sculpted targets: deltoid cap ellipsoid, pec/lat 30 mm webs, a 16 mm hollow, an untangle pass; samples at A 117/140/175;
  - the neck partly in the region;
  - the shoulder fill follows under the pauldrons; wearcheck is back below pre-C1, apart from two slight regressions (warden.top 47 to 51, the reaver collar's worst point 13.9 to 20.1 mm).
  - Fix 3 (armpit weights) is NOT done: changing weights moves arms-down poses.
  - C2's own read: rv medium-close, cb close if the fleck is gone, fd medium (no lift added), cr and lp medium.
  - Sheets: `godot/.shots/armor17/c2/sheet_*.png` (17). BEFORE = C1's build.
- Next: ONE max judge, CJ2, brief modelled on `c1\judge.md`. Calibrate on the owner's reaver_show_armpit.png. Include fix 5 (warden and stalker frames: no skin through the pauldrons) in the judge set.
  - **If CJ2 isn't "close": restage the three close-range clips** (reaver_show, catch_breath, flask_drink) so the upper arm stays at or below level, stop, and report the cost.
  - If close: one fix round on its notes (armpit weights with arms-down measured), then the MR.
- Cost so far: C1 213k, CJ1 116k, C2 231k, AJ1 94k.

**2. Arcanist caps become wide flat straps** (the owner: "straps are fine if you think they are better!"): 4-5 cm, flat along the neck-to-shoulder slope, deltoid bare, armhole inside the shoulder point.
- N3's source re-cut (aabe7f2b, 34969907; CAP_MAX etc. in heroine_outfits.py; arc_fit_post retired) failed OJ2 (medium): any cap over the deltoid reads as a pad.
- The neckline mirror from N3 PASSED: keep it.
- Rebuild `--only arcanist` plus the post chain after item 1 settles (both touch the chain).

**3. Small items:**
- **Warden top strap sawtooth at the Look** (look_f, screen-right strap inner edge; NJ3 whole-frame fail). S1 (nothing committed) ruled out alpha, tuck, AA mode, normal map, sheen and stitches. Likely cause: a 0.4 mm gap between the gold piping tube and the band. Next: a post-step closing the gap row by row (`extras.strap_rows`), before heroine_lod.
- **Arcanist hat brim underside:** a flat black disc when the camera looks up (OJ1, OJ2). No rendering lead is staffed; main is putting it in RESUME.
- **fan_fill:** wired into build.py (42a71ab3). Installed pieces with fans left: plate_pauldrons_plain (43; the fill about doubles its steel mesh), and lod1 meshes (1-4 each). Fill them on their next rebuild.

**Closed this session:**
- Steel-cup bug (6468b40f: HerRaise read "../HerJiggle", a sibling; HerJiggle is the skeleton's child).
- OJ2: plate night cup PASS, neckline PASS, reaver fur PASS, satin gloves PASS-WITH-NOTES (the night tint knob left open as optional).
- NJ3: Look pauldrons PASS-WITH-NOTES, closed (fan_fill.py, 82393b1d).

**MR state:** nothing merged yet.
- The judged-PASS pieces (the cup fix 6468b40f; OJ2's passes from N4 2822c6bb; the N3 collar; the NJ3 pauldrons 82393b1d) sit on armor-7 with the unjudged C1/C2 art (heroine.glb plus the four outfits).
- So the MR waits for CJ2, or cherry-picks the code-only pieces (6468b40f, 82393b1d, 42a71ab3, 68a80250).

**4. B2** (the cuirass passed K5; the g-string is WIP), its own MR later.

## Paused here (Armor 16, 22 Oct, coordinator wind-down); history
Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\a36cc4dd-fb3f-4250-b59c-d2116ef79a9a\scratchpad\armor`. Subfolders:
- a2: the arm judge.
- r16: the raise corrective's briefs, judge and verdict1, plus the pristine pre-morph glb and outfits.
- o1: the outfit-notes shoot and the OJ1 verdict.
- n1, n2, n4: the solver briefs.
- common16.md: the shared solver rules.

**Done:** the arms are MERGED (arms-16 = integration 3582c9d8, max A2 PASS-WITH-NOTES). The coordinator said to skip the shoulder-cap trim. armor-7 has merged integration (cc4b0c77).

**1. TOP: the owner's "really really bad" arms-overhead frame** (nude, town, shield and weapon over her head). It's one of R1's forced holds: `godot/.shots/armor16/r1|r2/r16*_cast_raise_nude_*.png` (or `_leap_`).
- `cast_raise` is the ARCANIST's cast clip (wand/staff, Loadout.cs Spell_Simple_Enter). We forced it onto the warden loadout (`--quick warden --hold cast_raise@0.10`), so the shield and sword through her head never happen in play.
- What she really does with her arms overhead:
  - `leap`: Crashing Leap, 78 deg (PlayerView.cs:557, any calling), and the reaver's Butcher's Bill flare;
  - `bull_rush`: warden, 69 deg;
  - `cast_raise`: arcanist, 63 deg;
  - `chain_strike`: 41 deg.
- The buckled traps and shoulders, pinched armpits and flattened breasts are the rig's skinning at 60-80 deg. They are in BEFORE (corrective off) too. The arm sculpt was on in both, and this pose was never shot pre-sculpt: shoot one from a 9922c080 copy to confirm.
- Next: reshoot each overhead clip with its OWN calling's loadout (arcanist for cast_raise; leap with each). Then fix the shoulder, trap and armpit deformation at high raise (corrective bones or morphs; HerRaise already computes the per-side raise weight) together with item 2.

**2. The bust corrective for raised arms.**
- Built: HerRaise.cs + RaiseRamp.cs, and the morphs axilla_fold_l/r and raise_crease_l/r from `tools/assets/axilla_fold_post.py` (body_post step 7b). The arcanist, ranger and reaver tops carry the morphs.
- Round 1: max RJ1 PASS-WITH-NOTES. Keep it. The lift was timid, there was no pec fold, and a tick showed at cast_raise.
- Round 2 (3802a7ab + e12e8890 WIP): the fold morphs plus the knobs (up 3.4 cm, yaw 12, stretch 0.22, pitch 20). Built and shot (`.shots/armor16/r2/sheet_*.png`), UNJUDGED.
- **Open bug:** under plate_top_plain and the warden top, `HerJiggle.Squash` reads 1 (HerWear.cs:289 `ix.Find(top)?.Hold` is null). So the steel cups still lift and splay with a gap at the centre. Fix that lookup first.
- N1's arc_fit_post caps let skin through at the hem with her arms raised (up to 10 mm at cast). Revisit them with item 3's cap re-cut.
- Then one max judge on the raised poses, nude + tops (round 2 of 2), then its MR: plumbing off integration. heroine.glb changed, so whoever merges second re-runs the chain.

**3. Outfit notes, round 2 of 2** (max OJ1 verdict: `o1\verdict1.md`).
- N4, 2822c6bb (UNJUDGED; sheets `.shots/armor16/n4/sheet_*.png`, BEFORE = round 1):
  - plate night cup: the pink muted to steel (metal_spec_mute 0.85, roughness back to 0.22);
  - gloves: ivory body 0.64, a wider sheen, and a wrinkle bump drawn in the shader;
  - Look pauldrons: a cool softbox off the dome's pole;
  - reaver fur polish (OJ1 passed it with notes).
- NOT STARTED: solver N3, the arcanist REBUILD (`heroine_outfits.py --only arcanist` + the post chain). Run it after item 2, because both touch the body post chain.
  - Re-cut the caps (OJ1: "linebacker shoulders"): end each cap above the deltoid's widest bulge, about 3-4 cm below the shoulder point on the outside, tapering to nothing at the armpit, with a flush bound edge and no lip. Dropping the caps for wide straps is the alternative, a design change: ask main.
  - Mirror the neckline cut to fix the visible notch: asymmetric head weights cut her right collar 2.5 cm lower.
- Then ONE max judge on items 1-6 (the coordinator).
- Also routed by OJ1 (rendering): the arcanist hat brim's underside is a flat black disc when the camera looks up.

**4. B2** (the cuirass passed K5 on armor-7; the g-string is WIP), its own MR later.

**Tooling notes:**
- `tools/freshness.py --root X` ignores --root and checks the cwd checkout; turn.py passes the root correctly.
- Merging integration with `-X ours` still takes NON-conflicting text hunks from integration. That put one of integration's accessor bounds into a built .gltf (fixed in d80574b1). After such a merge, diff your built files against your own last commit.
- `material_table()` now keeps hand-set material keys across a rebuild (a887d4b3).

## Handed off (Armor 15, 22 Oct, at ~255k): bust MERGED (integration 9922c080); reaver-dent-15 MR READY; next: the arm judge and MR
**Done:**
- bust-15 merged.
- **reaver-dent-15@48a529bf: MR READY,** waiting for main. The band was sinking 10-11.6 mm into the hollow beside each cup. `WRAP_TAUT` in wrap() now bridges every hollow except the cleavage.
  - Judges: max J5 PASS-WITH-NOTES; max J6 on the REAL eye-level camera, all six tops, no FAIL.
  - The fix is also on armor-7 as b32bc326, built on the arm body.
  - If main asks for changes, the integration-body build recipe is in the D3 brief (`scratchpad\armor\d3\brief.md` step 3b; built files in `d3\int\`).

**Arms: built on armor-7, UNJUDGED.**
- Commits: 5a1c7088 (code) and b15e3041 (art, 64 files).
- `tools/assets/heroine_arm_shape.py` is heroine_body_post step 6, mark `heroine_arm_shape`.
- Girth at 25-40%: 32.1-32.5 -> 28.7-28.8 cm. Deltoid swell 4.5 mm. Armpit web slimmed (knobs WEB / WEB_TORSO / WEB_T). Seam gap 0. L/R within 1.56 mm.
- Wearcheck: no outfit worse.
- Solver report: the A1 agent's numbers above. Shots in `godot/.shots/armor15/a1` were taken on the OLD camera DLL, so RESHOOT them.

**Next:**
1. `dotnet build`, then shoot the arms set:
   - nude: Look front and 40, close-up day / night / q;
   - each top: close-up day;
   - one arms-up frame: find a cast_raise shot arg, or `--hold`.
   For the before frames use integration: shoot from a clean copy with `scratchpad\armor\dmshot.sh` (edit its branch and list).
2. One max judge, A2: Look + close-up, nude and each top. Ask about:
   - the armpit fold;
   - the deltoid;
   - the taper;
   - "does she look like a real, attractive, athletic woman";
   - arms-up deformation.
   Cap 2. Scrap rule after the first fail.
3. Arms MR, a plumbing build off integration as bust-15 was (`scratchpad\armor\mr\brief.md` is the worker template). It needs heroine.glb plus every follower file, so whoever merges second re-runs the chain (Face 39 may add a brow step).
4. Then the outside notes, cheapest first:
   - the plate's night cup highlight (J6: roughness +0.05);
   - the arcanist neckline notch screen-left of her throat (turned frames);
   - the arcanist puff sleeves reading inflated;
   - flat white satin gloves;
   - the reaver fur cape reading as plush (J5).
   Then B2.

**SHOOT RULE (Armor 15):** run `dotnet build SurvivorUnchained.csproj` in godot/ BEFORE shooting, after any merge or C# edit. Godot console runs don't rebuild C#. J4's "new camera" frames really used the old camera DLL. Copies of a branch for verify shoots: `scratchpad\armor\dmshot.sh` (archive, `dotnet build`, `--import`, shoot, remove the copy after a link check).

## Armor 15 (22 Oct): bust MR READY (bust-15@eb667858); next: the upper-arm sculpt once it merges, then B2
Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\a36cc4dd-fb3f-4250-b59c-d2116ef79a9a\scratchpad\armor`:
- r1-r3: the reaver wrap solvers
- w1: the worn shape
- b1: the night blot
- j2/j3/j4: the judge briefs and verdicts
- mr: the MR worker's brief
- j4.sh: the 20-frame shoot
- j4\crops.py: box 740,420,1300,940 on the new eye-level close-up

**The reaver:**
- `wrap()` in heroine_outfits (`WRAP=0` gives the old bandeau), plus `tools/assets/wrap_post.py`. It transplants the `--only reaver` build into the installed outfit, then does `skin_union()` (body + skin_graft), tuck, cover, LOD and `compact()`.
- Shape:
  - High and narrow (nz-0.040 to +0.024), underboob bare (the owner: "reaver needs underboob").
  - It dips 28 of 54 mm into the cleavage, and its edges press in 2-5 mm.
  - The sides drop 15 mm (`WRAP_SIDE`).
  - Its weights are re-copied from her final skin (`WRAP_SKINW`).
- Wearcheck: worst 5.6, p99 3.1 (old band 19.7 / 10.1).
- `worn_reaver_post.py` (heroine_body_post step 6) rebuilds the reaver channel from armor_tuck/reaver.*.bin and adds the morph `worn_reaver`:
  - about 1.3 mm of roll under the band;
  - the lower pole about 3 mm lower and fuller;
  - the outer side 1.8 mm in.
  `People.WornShape` sets it, from HerOutfit and HerWear.Apply.

**Warden/plate night blot:** metal_finishes pieces `warden.cups` and `plate.cups` at metal_rough 0.22. Their metal_blot 0.2 only acts with B2's shader.

**Arcanist plumleather:** floor 0.50, spread 0.85, clear coat 0.05 at 0.45 (J3 picked c1).

**Max judges, on usage:**
- J2 (old camera): nude, warden, plate and ranger PASS; reaver PASS-WITH-NOTES; arcanist FAIL, near (PVC).
- J3: the arcanist PASS-WITH-NOTES.
- J4, on the new eye-level close-up: all six PASS or PASS-WITH-NOTES. Its notes:
  - the reaver band's top edge runs almost straight;
  - the arcanist's night glow is the glossiest; if the owner says latex, drop the clear coat to 0.02.
- Sheets: `godot/.shots/armor15/j4/bust_*_half.jpg`.

**Open, outside the bust:**
- The arcanist's puff sleeves read as inflated pads.
- A small notch in the arcanist neckline, screen-left of her throat, in the turned frames.
- The white satin gloves look flat.

**The MR:** bust-15, off integration ededfdad, built with plumbing; tests 1046/0/8. It merges clean onto 9252a790. A verify shoot on a bust-15 copy matches the judged frames (mean abs diff 0.25-1.45 out of 765).

**Next: the upper-arm sculpt** (approved). Face 38's numbers are in `...\scratchpad\face38\arms\report.md`:
- the inner side 1.5-2 cm slimmer at 15-50%;
- the armpit join lower;
- a small deltoid swell at 10-25%.
It is a mirrored heroine_body_post step, with sleeves and arm pieces re-fitted. One max judge on the Look and the close-up, nude and each top; cap 2; its own MR.

## Handed off (Armor 14, 22 Oct, at ~245k): PERFECT-BUST pass at judge round 2 of 2; next: the four steps below, then MR
Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\a36cc4dd-fb3f-4250-b59c-d2116ef79a9a\scratchpad\armor` (s1-s3 = solver briefs + reports, j1\brief.md + verdict.md = the bust judge, j1.txt/j1.sh = its 20-frame shoot, shoot2.sh, setmat.py = plumleather knobs for trials, bustmeas.py/wts.py = measures). **Judges and solvers now run on USAGE (su-lead-max subagents), not the API (owner, via main, 22 Oct).**
**Done on armor-7 (unmerged; integration merged at e33d611a incl. Face 38's soft neck relief):**
- 9399a994: the root of the bodysuit dent. breast_sym_post had run `--no-follow`, so the outfits kept the old 3 mm hollow. Now `follow_outfits` carries the four outfits over the moved skin, normals turned with it, done-mark `breast_sym_follow`. It's wired in heroine_body_post and the outfits are rebuilt.
- 2ba8445f / bedcf4ee / 76a8ab25 (S1-S3): `tools/assets/bust_shell_post.py` (arcanist only; marks bust_shell, bust_dome, bust_detail). The leather over the cups is a smooth, full shell, and the convexity bake is redone from the new shape. Measured smooth at rest and posed. The shape alone (debug_view 5) is clean.
- 155f2cf6: the arcanist top/collar tuck and cover records at her nape are snapped to her current points (143 records; `tools/scratch/armor4/tuck_snap.py`); tuckcheck is clean.
- c8ef136e + 4ea04dfe: the "nipple pokes" and the crease were the key light's highlight on glossy leather, not shape: the flat-albedo and flat-roughness tests in .shots/armor14/a3-a5 cleared them. New outfit_materials.json keys feed the outfit shader: `rough_floor`, `rough_var`, `clearcoat`, `clearcoat_rough`. Plumleather is set to 0.52 / 0.6 / 0.2 / 0.25 (trial v3, `.shots/armor14/a7`). Debug views 7-11 each flatten one channel; set them with the `OUTFIT_DEBUG_VIEW=n` env var.
- **Judge J1 (API max, $1.57) FAILED, medium overall** (verdict: scratch j1\verdict.md):
  - PASS: nude, ranger and Look; no dent anywhere, no pokes. Warden and plate pass by day.
  - Arcanist at 0.58: suede and dusty by day, see-through at night (near). Fixed since by v3, unjudged.
  - Warden and plate, night front: a cloudy pink blot on the screen-left cup (near).
  - Reaver: rigid half-spheres below a straight bandeau (medium).
**Next:**
1. **Reaver (medium = scrap rule):** don't patch the shading. Rebuild the bandeau as a fitted wrap: it follows the breasts, dips at the cleavage and gives a slight soft flesh roll at its lower edge (tuck), so the breasts below read as soft and supported. Tell main first; it's a garment rebuild (heroine_outfits / a post-step like bust_shell_post).
2. **Warden/plate night blot:** it's the close-up NIGHT KEY's specular (gone with `--close-key-night 0`; `.shots/armor14/a8`). A gear-layer twin key at spec 0.12 changed nothing, so the cups are not on HerGearLayer: find the cup material's layer and kind first. Fix per material (a crisp single highlight via lower roughness, or less specular), not the key, which her face uses.
3. Re-shoot j1.sh (20 frames, ~15 min), rebuild the crops (box 700,400,1260,920; see j1 folder), and run ONE final max judge (round 2 = the cap; reuse j1\brief.md, adding J1's must-fixes). Pass -> small MR as dent-12 was built (step d of the Armor 13 notes below), tests once.
4. Then the owner's upper-arm sculpt (main's 22 Oct message: inner arm 1.5-2 cm slimmer, lower armpit join, small deltoid; Face 38's numbers in `...\a36cc4dd...\scratchpad\face38\arms\report.md`). It's a mirrored heroine_body_post step, with sleeves and arm pieces re-fitted, one max judge (Look + close-up, nude and each top), cap 2, its own MR. Then B2.
Cost so far: S1 $3.66, S2 $2.37, S3 (~$3), J1 $1.57 on the API.

## Paused here (Armor 13, 21 Oct night, coordinator wind-down); next: the PERFECT-BUST PASS first, then B2
Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\9cf2b0ed-abf7-430e-b71e-d9b5f9dd3bd3\scratchpad\armor` (texts backed up to survivorsunchained_inputs\scratch_armor13). Briefs there are templates: j4_brief.md (strict bust-area judge), d7\brief.md (shader/mask solver), g1\brief.md, c6\brief.md (worker rebuild).
**1. PERFECT-BUST PASS (owner, top priority; NOT STARTED: nothing diagnosed or welded yet).** Owner: "yep do it, mostly smooth, busty, full cups without dents like see the dent in the left one here but that could just be the bodysuit"; "but if you see more great fix em". Crops: survivorsunchained_inputs\owner_frames_21oct\bodysuit_dent_closeup.png and bodysuit_dent_screenright_zoom.png: the arcanist bodysuit (open zip, close-up), a dip on her LEFT breast (SCREEN RIGHT, the same breast as the first dent), lower/inner slope by the cleavage; the other cup's upper-inner edge looks lumpy. Steps:
  a. Diagnose the layer: nude vs bodysuit at the same close-up (`--hide-slots all` vs `--quick arcanist`, args in scratch d6.txt), debug gate 14 (world normal) on both; `--dump-her` / `--geom-normals` (Shots.cs) for her stored vs recomputed normals; the bodysuit's own normals and tuck (wearcheck --dump; armor_tuck/arcanist.top.bin: the g1 solver saw "289 of 10243 tuck points match none of her vertices" on the arcanist = stale after Face 36's neck; the arcanist collar/top stale tucks were already ours in B2) and its gloss (routed earlier: "bodysuit gloss over the bust plasticky").
  b. Weld hard normal seams over her WHOLE bust/cleavage/underbust, mirrored (the dent's weld covered only the left inner box; the whole-body 10 deg survey found 158 places), on her body AND each top outfit over it. Every heroine.glb change must be a post-step in tools/assets/heroine_body_post.py (like breast_sym_post). Message Face 37 (face-37 worktree: her hair, upper arms, deep-skin eyes; may re-run neck geometry) BEFORE writing heroine.glb, and tell main. Don't change her bust's size or shape beyond removing defects without telling main.
  c. One strict max judge on her bust ONLY: nude + warden cups, plate top, ranger, reaver bandeau, arcanist bodysuit; close-up at closest zoom and the Look front and 40; day and night. Gate per frame: "is this a perfect, beautiful, smooth, full bust with no dent, crease, lump or seam at 1:1?" Brief it to FAIL anything short of perfect (the owner called neck frames three max judges passed "awful").
  d. Fix, cap 2 rounds, then a small MR branch off integration, built as dent-12 was (temp index: `GIT_INDEX_FILE=<f> git read-tree <integration>`, `git format-patch -1 --binary --stdout <c> -- <paths> | git apply --cached -3`, `git update-index --cacheinfo` for binaries, `git commit-tree`, `git update-ref`); test on a full-tree `git archive <branch> godot tools public | tar -x` copy under release/ (git-ignored; delete after). Send "MR READY <branch>@<commit>". Estimate 2-4 h.
**2. B2 state (paused):**
- Breast dent MERGED (integration eda25b01). Cuirass PASSED (K5, below) and rebuilt on Face 36's new-neck body (baacc554: same params; town worst 4.8 at idle_warden_break clavicle_l, arcanist idle 5.5, combat 4.6, p99 9.25, cov 0.4%, 19,948 tris; frames godot/.shots/armor13/c6, unlooked).
- G-string (g1, item `forged_gstring`, 2f0eae6b; `hip_line(sd, ...)` shared helper in piece_blender; 4,954 tris) FAILS skin->bottom: 19.2 town / 15.8 other / 2.1 combat (29 with --confirm) at the FRONT LEG LINE (|x| 0.03, 16-20 mm above the crotch: the thigh crease folds over the panel edge in run/sprint) and the cleft (run_arcanist_town). warden.bottom on the same clips: 8.6 (2.7 --confirm). Next round g2 (fresh medium solver from g1\brief.md + this): copy warden.thong's leg line and tuck (ours writes only 294 tuck records), check the panel edge's thigh weights, write its armor_cover bin, envelope p99 6.42 -> <= 6; the left ASIS crossing is only 25.6 mm. Back frames need the shield off. The arcanist `under` now points to plate_gstring_plain (test A_displaced_arcanist_top_leaves_the_forged_gstring_under_it).
- Then cuisses (4 rounds, on hip_line), the arcanist collar/top stale-tuck rekey, B2 final max judge (add a short play-camera clip for the cuirass rim tube's motion), MR B2; then B3 (helm 3, brim 1, tiers 2).

## Armor 13 (21 Oct): the dent MERGED; B2 cuirass steel round 4
Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\9cf2b0ed-abf7-430e-b71e-d9b5f9dd3bd3\scratchpad\armor` (j3/j4 = dent judges, d7 = mask solver, c4 = cuirass r3, k3_brief.md, c5 = steel r4).
- **Breast dent MERGED** (dent-12 d7d35321 -> integration eda25b01, 1046/0/8). Max D3 FAILED sky_body on a deltoid tone line (old mask = freckles blue, bind height only); fixed with its own mask in the graft freckles map's ALPHA (neck column only, 0 at the graft edge; 603a0fa2); D4 PASS, no must-fix. Face 36 wires breast_sym_post into the body build.
- **Cuirass PASSED: K5 (max) PASS-WITH-NOTES** (godot/.shots/armor13/k5; eddf6f0c). Root cause of K3's fail: the cuirass's per-piece id 0.227 bakes as 57/255 (truncated), outside piece_is's 0.0025, so NO per-piece setting ever reached it; piece_is() now also matches the truncated value (side effect: warden.greave's finish applies for the first time; K5: indistinguishable at the town camera). Rims = bare steel tube (rim_metal 0.85, rim_floor 0.10), shape-driven wear, night lift. Notes closed as known: night left-cup gloss dome; lavender cup highlights in q (crown metal 20-30% toward neutral if reopened); rim 10-15% brighter than the gold trim in q; a ~10 px kink at the window's bottom tip (locked mesh). Motion of the 4.5 mm rim tube at the play camera: check in B2's final judge (a short clip).
- Open: wearcheck's arcanist idle worst 8.0 mm after the 19:31 repack (was 2.3): re-measure on the merged clip at B2's final check.
- Then: g-string (2), cuisses (4), arcanist rekey, final judge, MR B2; B3.

## Paused here (Armor 12, 21 Oct, coordinator wind-down); next:
Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\c4134bd3-ebec-4f59-ad97-c6010364bcd4\scratchpad\armor` (dent\ = briefs d1-d5, j1-j2, scripts; c3\ = cuirass r2; k2_brief.md).
- **THE BREAST DENT (owner, team top priority; ships as its own small MR BEFORE B2).** Her LEFT breast (screen right), the inner slope above-right of the warden gore boss, in every outfit (owner crops survivorsunchained_inputs\owner_frames_21oct\warden_cup_dent_closeup.png, dent_other_outfit_closeup.png, dent_tiny_crop.png). Three layers stacked; two fixed on armor-7:
  1. Normal data: a UV-seam split of 34-42 deg on her left lower inner breast drew the fold line. Welded (left inner-breast box only; the whole-body 10 deg survey hits 158 places, so the weld is restricted to that box).
  2. Geometry: her left inner wall sat about 3 mm inside the mirrored right. Pushed out; asymmetry is now 0.3 mm bind, 0.4 mm posed. `tools/assets/breast_sym_post.py --art godot/art/people --no-follow` (c6882ddd) mirrors about x = 0 (FIT_PLANE False; round 1's fitted plane had the sign backwards). It changes heroine.glb Mesh_0 POSITION/NORMAL only (520 vertices, at most 2.75 mm) and re-keys 18 armor_tuck/armor_cover records. NO outfit or piece file changed (the owner: "It shouldn't need to refit any outfits"). It is a post-step on heroine.glb after any body build, like nape_post: Face 35 must rerun it if they rebuild her body.
  3. Lighting: the wedge faces away from the day close-up key and sky. Face 34 (8b9b57e0) cut her sky share to 0.45. Judge D2 (max): PASS-WITH-LIGHTING. The mesh is clean and matched, but the wedge still reads as a dent until her BODY's sky share returns to 1 in the day close-up (1.25 looked pale and flat). Done as `sky_body` (2de0893f, 82cb654b, fe5d26e4, ce7882e3): heroine_skin.gdshader `sky_body`, masked by the freckles blue channel (8 cm feather, 1.47-1.55 m); People.HerSkyShare(p, w, body); GameCloseUp `--close-sky-body` (default 1, DAY only; night untouched; Face 35 owns the night rim lamp). Debug gates are 14 (world normal) and 15 (sky share); 12 and 13 are Face 35's. The coordinator approved it, with a tone-line check. Numbers: pocket 51.4 -> 72.6/255; face unchanged (0.01); the largest step added on the jaw-to-sternum line is 2.4/10 px; Look and night unchanged.
  **NEXT:** (a) merge integration (13 commits behind; junction dance), reimport, then reshoot godot/.shots/armor12/dent_d5 (it was shot --stale-ok). (b) One quick max judge on dent_d5: warden_f_00-02, arcanist_f, nude_f, night, against the _off frames. Ask explicitly: "is there any tone line or band?" on crop_warden_f, crop_warden_s, crop_look_f (+_off). Also: does any dent still read? (c) The ranger top: her skin sits 1.03 mm through its dark leather at the top of the cleavage at bind (bind point (10.3, 1415.1, 120.8) mm), with no tuck record; not visible at idle. Check one arms-up or bend frame; if it shows, stop the move short at the valley top. (d) dotnet test, then the MR. armor-7 also carries B2's cuirass, so build the MR branch `dent-12` from integration with only: tools/assets/breast_sym_post.py, heroine.glb, people/armor_tuck|armor_cover *.top.bin, armor/armor_tuck|armor_cover plate_top_*.bin (rerun the script on integration's files; it is deterministic), the sky_body commits, HerWear --hide-slots (a1757af0), Shots.cs --dump-her/--geom-normals (d6cd3fab). The cuirass records (plate_cuirass_plain.bin) re-keyed on armor-7 stay with B2.
- **Then B2:** cuirass round 3 of 3 (K2 notes below: brighter, glossier rolled edges on the collar, armhole and side; finer wear; the ridge 4x20 mm or dropped; cap_density 54000), g-string (2), cuisses (4), the arcanist collar/top stale-tuck rekey pass (one pass, judged at B2's final judge), MR B2; then B3.

## Armor 12 (21 Oct): B2 under way
- **Cuirass round 2 (solver, c3 installed, b0820806/1fa872b2): judge K2 (max) PASS-WITH-NOTES** (godot/.shots/armor12/k2, brief scratch armor\k2_brief.md). Sides closed (params.wrap az 66; band at the lower outer corner), breast skin outside the window 5.8% -> 0.4%; town worst 4.9 (one back-strap point; plate 3.9 at the armhole), combat 4.6, p99 9.05, 20,128 tris (cap_density 55000; 54000 next). Steel per-piece: metal_finishes.json "plate.plate" (rough 0.38, blot 0.5) via the new `piece_blot` uniform (heroine_outfit.gdshaderinc, People.cs); pauldrons unchanged (k2_paul). K2 notes: front 3/4 reads as dark leather/latex: brighter, glossier rolled edges on collar/armhole/side (rough ~0.22-0.25, +15%, body >= 0.33); finer wear instead of blotches; ridge invisible (4x20 mm lit, or drop). Round 3 of 3 takes these.
- Coordinator: arcanist collar/top stale tucks are ours inside B2 (one rekey pass, judged at B2's final judge, else log). Arcanist white gloves: not ours.
- Process note: TaskStop on a background Bash job leaves its bash loop and Blender/Godot children running on Windows: kill them by PID (`taskkill /PID n /T`) and give the turn back.

## Paused here (Armor 11, 21 Oct, coordinator wind-down); next:
- **Step 0 DONE in code, unjudged (30f19483):** the cause was that arcanist.top is a leotard down to her groin (y 0.914), and arcanist.bottom is only a 2 cm back tab, so any equipped top left her bare from the navel to the groin (only the arcanist has this). New row field `under` (ArmorPiece.Under; Wear.Look: a displaced calling fill puts its `under` pieces in their own slots unless those are equipped, hidden or `hide`). Data: arcanist.top `"under": ["warden.bottom","warden.belt"]` in tools/armor/slot_map.json, which heroine_outfits.py now copies into the row, plus a hand edit to people/armor_index.json. Test A_displaced_arcanist_top_...; dotnet 1042/0/8. Previews: godot/.shots/armor11/c0 (c0_sheet.jpg: a = bare, b = warden.bottom alone reads as a floating dark patch (rejected), c = bottom + belt (chosen interim), d = reaver.bottom (same patch)). **Plan:** once B2's g-string exists, repoint `under` to `plate_gstring_plain` (the set's designed bottom). Keep arcanist frames out of K2 and judge cross-calling once, at B2's final judge, with the g-string on.
- **Next:** item 1, the cuirass solver round (round 2 of 3). Brief a `su-lead-high` solver at medium effort with the K1 MUST/SHOULD from the section below. It should reuse scratch armor\c2\run.sh and wc.sh (wearcheck `--confirm`). Crisper steel: check first whether the steel material is shared with the pauldrons (J3-passed). If so, add a pauldron frame to K2. K2 re-judge frames: k1_q, k1_s, a FRONT town frame, and close-up stills at the worst frames of idle_warden_break and run_reaver_town (scratch k1_brief.md is the template; it is a max judge). Then the g-string (2), cuisses (4), MR B2; B3 as listed.

## Armor 10 (21 Oct, handed off at ~250k): B1 MERGED (integration 72e1c575, CINE OK); B2 cuirass at judge K1 FAIL (open sides); next:
- **Cuirass state** (armor-7 @ HEAD; style ("top","cuirass"), piece plate_cuirass_plain, item forged_cuirass, installed build "b4"): rigid, plate blend spine_03 (a spine_02 share pulls the plate off her chest: dead end), graft on leather only (`graft: "leather"`, heroine_neck.match_pieces `only=`), band_seam 0.6 (band 28 mm on the plate), lower-rim flare 5 mm, neckline corner flare 3 mm, strap_lift 3.5 mm, tuck_rekey_shipped (its tuck rekeyed to the shipped body). Numbers: town clips worst 4.8 mm (idle_warden_break, run_reaver_town; target 2), combat 4.6 (closed: < 1 px), envelope p99 9.08 (the flares; b2 had 6.08 but town 6.9), window 30.6 px, 19.6k tris, plate_top_plain bit-identical. **wearcheck `--confirm`** (new, opt-in) drops false hits where her skin normal runs along the plate (round 1's 19.9 mm was that): use it for the cuirass and say so.
- **Judge K1 (max, godot/.shots/armor10/k1, brief scratch armor\k1_brief.md): FAIL.** Window approved (keep 101x161 mm, reads as a breastplate). Flare reads fitted. **MUST:** close the lower outer sides: carry the lower rim round under each breast back to her chest wall (~70-100 mm further back at band height), bring the side edge down from the armpit to meet it, band attached at that lower outer corner on the underbust line (~60 mm lower than now); acceptance: no breast skin outside the window in k1_q, k1_s, k1_arc_f. SHOULD: crisper steel (roughness one step down, cloudy blotches halved, sharper ridge on bar and gore); the lower rim one clean curve with the lit rolled rim. Re-judge frames: k1_q, k1_s, k1_arc_f, a FRONT town frame (k1_town faced away: use `--facing` or the close-up off), and close-up stills at the worst frames of idle_warden_break (front 3/4) and the reaver town run (back 3/4).
- **CHECK first:** k1_arc_f shows her bare from the navel down: equipping the cuirass may drop the arcanist's own bottom (its leotard is the top). If so, the cuirass's `covers`/Wear fill must leave her a bottom (fallback order) before any arcanist frame is judged.
- Stale tucks not ours: arcanist.collar (30/30), arcanist.top (28/5959): outfits' (route via main).
- Cuirass rounds used: 2 solver rounds (8 builds) + 1 judge. Then g-string (2), cuisses (4), helm (3), brim (1), tiers (2).

## Armor 10, B1 record (MERGED)
Worktree armor-7 (junction rules below). Scratch `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\6a6cb394-317c-45d7-aa08-3523481011e7\scratchpad\armor` (j1-j3 briefs and lists, run_j*.sh = shoot via shoot2.sh, run_perf.sh = perf ABAB; b1/b2r2/b2r3/w1/w2 = helper scratch).
- **B1 contents:** piece_blender machinery for non-top styles (POSES per slot, top-only code guarded, pl_limb_frame/pl_row/pl_lame any side; plate_top_plain rebuilt bit-identical). Style ("pauldrons","lamed"): `plate_pauldrons_plain` (item lamed_pauldrons) and `plate_pauldrons_warden` (base plain + gold bead trims, `"replaces": "warden.pauldrons"`, the warden_pauldrons item). New data fields: `cover_grow` (a piece's cover spreads over her skin, so a puffed sleeve under it lies flat: the arcanist top) and `replaces` (ArmorIndex.Calling stands the piece in for a calling row; HerWear.LookFor sends such a calling down the piece path even with nothing worn; `--standin 0` = old outfit file). push_apply caps each SHELL vertex's total push (was per skin point: 8 mm lifts). tools/armor/paul_check.py (standoff on her drawn skin, lame order); wearcheck --dump/--file/--tuck-file.
- **Judged (max, 1:1):** J1 FAIL narrow (arcanist puff; tab fin) -> J2 FAIL small (tab knob, pale brass) -> J3 PASS 6/6 (godot/.shots/armor10/j3). Known, logged: the tab rivet reads dark at look_q (a gold rivet if reopened); 2-3 px edge shade at the left cop's inner tip; the comb is invisible at 1:1.
- **Numbers left as known (closed by J1 as invisible at 1:1):** cop standoff p99 ~8.7 mm (target 7); neck rim 6.9-7.5 mm untucked (5); skin through lame1's back end 9-10 mm in the axe run's back swing (11 pts / 16 clips); lame-order near-crossings (worst 1.5 mm); adorn.py "through her skin 331" in the extreme test poses (arms overhead, hug) makes build.py print ADORN FAILED for the warden variant (files are written; the plain base has the same poses). Plain gameplay LOD 25.05% (budget 25%). axe_heavy frame 0 is a one-frame arm pop (animation's).
- **Perf ABAB (2560x1440, 2 pairs):** warden on the piece path vs her outfit file: hub 11.5 vs 12.4 ms, arena_mid 9.4 vs 9.7 ms: no cost (godot/.shots/perf/*_sa*/_sb*).
- dotnet 1041/0/8 (one run had 1 flaky failure that passed on rerun; not identified).
- **NEXT (B2):** cuirass (spec section 2, 6 rounds; "rigid": true with >= 3 mm designed clearance), g-string (2), cuisses (4); then B3 helm (3), hat brim (1), tiers (2). Run wearcheck/paul_check inside a blender turn, at most 6 clips a process (the coordinator: 13.8 GB without a turn). Combat frames: the arena play camera shows her ~20 px under dark canopy; judge armor at the close-up (`--close-turn` R sets her turn: 1.57 side, 2.5 back 3/4) and the Look.

## Armor 9 (21 Oct, handed off at ~250k): MR A MERGED (integration 7bdd7689); B started; next:
Worktree armor-7 (junction rules below). Scratch `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\6a6cb394-317c-45d7-aa08-3523481011e7\scratchpad\armor` (B spec copied there: b_design_spec.md, b_design_brief.md; judge briefs p9_judge*.md; shoot2.sh = multi-frame shoots `NAME|WxH|FLAGS|ARGS`, `--count N --every T` keeps every frame; im1_brief.md; im\ = import numbers).
- **Done since MR A:** `tools/armor/import_mesh.py <piece dir> [--check|--install [--item "Name"]] [--refit]` (e694b851; the PIECE_SCHEMA import contract: refusals, body sha1, weights from her skin, `_rigid` parts on one blend, push to band, tuck, LODs with LOD_FLOOR=1800, cover, index row `"source": "mesh"`). **Rigid rule:** a row with `"rigid": true` is never laid by the garment tuck (GarmentTuck.Over, HerWear, wearcheck; test Rigid_inner_piece_is_never_laid; dotnet 1034/0/8). Set only by piece.json `"rigid": true` or an all-`_rigid` free mesh (b7f3878d: NOT every plate style; the plate tops' straps must keep lying under the pauldrons). B's cuirass and cuisses set `"rigid": true` and carry >= 3 mm designed clearance instead.
- **Marionette's mar_her_pauldrons/cuirass/bracers are installed** (godot/art/armor/src/mar_her_*), unjudged. Smoke `godot/.shots/armor9/im/all3.png` (her left pauldron may stand off). Motion is poor: skin through each by 25-28 mm in cast_flick/sword_heavy (one blend per big plate over a twisting arm/torso); the rigid cuirass crosses warden.belt by 30 mm (254 pts). That's Marionette's authoring (split plates into more `_rigid` parts, bending straps), plus barrel faulds, saw-tooth lames, neckline 41 mm: routed to Marionette via main; don't spend B rounds on it.
- **NEXT (B, per b_design_spec.md "Build order"):** (1) shared machinery in piece_blender (POSES per slot, guards on strap_sets/gore_in_pose/BAND, pl_* for any limb and side): 1 round; (2) pauldrons "lamed" (spec section 1 and its proof numbers): 5 rounds; then cuirass 6, g-string 2, cuisses 4, helm 3, hat brim 1 (+ judge 4's hat notes: crown slump, thick wavy brim, band and buckle, finer grain), tiers 2, judge 1-2. Brief a medium solver (su-lead-high, effort medium, ~250k, it builds) per 1-2 items with the spec section pasted and its proof numbers as acceptance; a max judge on 1:1 frames after the pauldrons.
- MR A record: judged 4 rounds (max), all PASS; fixes: the blued finish hid metal dyes (shader), the arcanist choker fragment cut, swap hitch 1.5-1.8 s -> worker lay (worst frame 46-78 ms; P9: redress in place + shader precompile). heroine.glb on a conflict: graft COLOR_0 (scratch glb\graft.py, cmp.py), then heroine_lod.py.

## Paused here (armor lead 8, 21 Oct, coordinator wind-down); next:
Worktree `.claude/worktrees/armor-7`, branch `armor-7` @ 8c4ebc3b (pushed; integration ec27099b + env df377545 merged). Junction rules as below. Scratch: C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\489a0bd2-e3b7-44cc-9b4a-68d66b041337\scratchpad\armor (texts backed up to survivorsunchained_inputs\scratch_armor8\). Briefs there: r1-r4_brief.md (the rebuild solvers), p8_judge.md + p8_list.txt + shoot.sh (judge shoot), b_design_spec.md (B design, DONE).
- **THE ONE REBUILD: DONE** on the new neck (24cdc909, then 1a157d99, then 8c4ebc3b). The recipe that matches integration is a full build with `NAPE=0`, then `rebuild
ape_post.py`, then install. A plain full build gets the neck weights wrong (Face 31 ran nape on the built body). Restore tools/assets/heroine_neck_graft.npz from git after every build. Then build.py --all, cover.py for changed pieces, heroine_lod.py, reimport. Scripts: `rebuild
4b.sh` (needs `--body`) and `pp.sh`. dotnet 1032/0/8 (DyeHelm test now lists thread as trim).
- **Dimple (bounded tuck): proven on numbers and in the art.** Step off full tucks 5.95 -> 1.50 mm; L-R rim 0.19 -> 0.13 (warden.top) and 0.41 -> 0.21 (plate_top_plain); push-out unchanged. Judge r1: not visible at 1:1, CLOSED.
- **Motion clipping (P3):** laid pieces take the outer piece's bone weights in game (93a5760b, GarmentTuck.BlendWeights + HerWear.OuterWeights). A skirt only hangs from its own set's belt (Wear.Hangs). wearcheck mixed OUT>2 total: 5819 -> 4044 -> 3308 on the rebuilt art (`scratch armor\wc	w2`). Worst left: reaver.boots/warden.greaves (thigh, runs), warden/reaver.bottom under ranger.top (pelvis, stalker run). No clipping showed at 1:1 in any town or close-up frame.
- **PERF, must fix before MR A:** the garment tuck takes 1.1-2.2 s per Apply (log "garment tuck: N meshes laid in ... ms"; it was 356 ms before the weights step). That's a hitch on every live swap. Profile with `--tuck-prof 1` and optimize (cache, a grid build per Apply). A medium code solver.
- **Judge round 1 (max, 15 frames + creation Look):** PASS: all 3 sets in town; revealing and leather close-ups; the live swap; helm toggle; leather dye; r2_wq (the pauldron hoop at -40 is GONE). FAIL:
  (a) **The warden shoulder straps/pauldron at the creation Look front** (r2_wf, a8_warden_close): ragged/serrated. Round 3 found the cause was the top's STRAP, not the pauldron: it was laid on the build skin, up to 8 mm high. Now laid on her final skin (STRAP_FINAL), with the pauldron rim 19 mm beside the strap (PAUL_BESIDE). Round 4: the gold piping is laid from the strap's centerline (RIB_TRIM), and strap rows share weights (tools/assets/strap_rows.py). Idle lateral noise is now <= 0.10 mm RMS and posed width 17.8-18.2 mm (was 14.3-21.2). **Still open:** the crest where the strap crosses her shoulder top. Posed in idle_warden, the neck-side edge sinks 2.7 mm into her and the outer edge lifts 8.2 mm. Next: lower the lift over the crest, or ease the shared row weights back to per-edge weights only over the crest. Then **judge round 2** on r4_* frames (godot/.shots/armor8/r4_wf, r4_wq, r4_warden_close, r4_pla_close, r4_wf_shoulders_1to1). This item is at solver round 3 of its cap.
  (b) **The plate top strap flick** by her neck (a8_pla_close): same cause and fixes (STRAP_EXACT, PLATE_STRAP_ROWS). Rejudge it in r4_pla_close.
  (c) **Combat frames unusable:** --close is ignored in combat zones (CloseUp: only safe places), and verge's play camera sits under canopy with rainbow rocks (seen in armor-7 after the env merge; check on main and tell env if it shows there too). Reshoot combat at the play camera in an arena: `--zone arena --theme ruts --seed N --auto toward` (Game.cs ~277). Do the 3 sets + oathbrand + a8_mix_legs (reaver_furboots,warden_legplate,ranger_corset; NOT with reaver_gstring, which replaces the legplate).
  (d) **Dye proof:** reshoot with a metal color that contrasts the navy (steel or bronze) and a non-gold trim. The judge read the gold trim dye as flat yellow paint.
  Note: `--quick stalker` is the ranger calling.
- **Then MR A:** the full 16-clip wearcheck once, dotnet, MR READY to the coordinator.
- **B:** the design spec is done (`b_design_spec.md`): lamed pauldrons, a lozenge-window cuirass, high-rise g-string + cuisses, open-face helm, no gauntlets, the arcanist brim. Its four calls: (1) never lay a RIGID piece with the garment tuck (it bends plates), (2) the g-string legs cover belt+skirt (lead's call: agree), (3) tiers stay adornment-only, (4) the cuirass waits on the tuck rule (done). Its estimate is 25-27 rounds.
- **Marionette's armor workshop for HER** is built against PIECE_SCHEMA@03a0029f (npc-1 merged ce68ff22). Its pieces `Marionette/generated/to_game/armor/mar_her_*` pass drop.py but show in game only through **tools/armor/import_mesh.py (not built)**. Slot it right after MR A, as B's import path, then one 1:1 judge on her. Known issues: barrel faulds, saw-tooth pauldron lames, neckline 41 mm off.

## Paused here (armor lead 7, 20 Oct night); next:
Worktree `.claude/worktrees/armor-7`, branch `armor-7` (pushed). godot/assets is a junction to its OWN public/assets (remove it with `cmd /c rmdir` before merging integration, remake it after, then `git update-index --assume-unchanged godot/assets`). .godot was seeded from main and imported. Scope: OWNER_NOTES 20 Oct "Player gear". Approved split: **MR A** = the engine on existing shells (revealing = reaver, leather = ranger, plate = warden + plate tops); **MR B** = the true sexy full plate. The owner's proof counts as done only with B. After B: tools/armor/import_mesh.py (one import for Marionette and artist meshes). Contracts for Marionette: **CONTRACTS docs/armor/PIECE_SCHEMA.md@03a0029f** ("Dye zones", "Free meshes: the import contract").
- P1 DONE 31ae4238: 21 set items in items.json (`wear` lists: reaver_*, ranger_*, warden_*, *_plate_top, arcanist_hat); shot args `--equip a,b` (Game.Begin, before her first figure) and `--swap-at T:ids;T:ids` (the live Gear path).
- P2 DONE 38a7c780: `tools/armor/wearcheck.py` (garment-vs-garment and skin clipping through her core clips, 31 min for the full matrix; "OUT" = A showing past B's outer face). Read: most big numbers are her own outfits in motion. The warden pauldrons swing ~30 mm into her torso in the overhead attacks, in her own set too, which is B's pauldron shell. The mixed failures are same-band collisions at rest (boots vs greaves, belt vs skirt), waist/leg pieces pressing in runs, and reversed stacking (ranger pauldrons under the warden top's strap). Matrix and table: scratch `armor7\wearcheck\`.
- P3 IN PROGRESS, WIP 75a28ffb + 37afc583: the garment tuck (godot/logic/Rpg/GarmentTuck.cs + tests, HerWear lay step, tools/armor/cover.py writes armor_cover/<id>.bin, the footprint where tuck records are missing: rerun it whenever a piece is rebuilt). Order bottom, top, legwear, gloves, boots, skirt, collar, bracers, greaves, belt, pauldrons, cloak, head (slot_map.json, with a copy in GarmentTuck.Order pinned by a test). r = 20 mm, offset 0.3 mm. Mixed OUT >2 mm went from 46,516 to 3,006. Reversed stacking is solved, and rest overlap is down to 0-85 a pair. What remains is MOTION: each piece moves with its own weights, e.g. warden.skirt/ranger.belt 955, reaver.boots/greaves 660, arcanist.boots/greaves 377, ranger.boots/greaves 146, pelvis pairs 70-78. Next (the solver proposed it, and I agree): blend a laid piece's bone weights toward the outer piece's by the same t. The prototype is `wearcheck --tuck-weights` (a bug was fixed, but it has not been run). If it brings the motion pairs under ~10, put it into LaidMesh in the game. Then the full 16-clip run with --same and skin, gt shots (godot/.shots/gt_close.png is pre-tuning), the --wear path, the calling-set check, a clean Apply cost (356 ms under load; `--tuck-prof 1`), and the full dotnet test. Comparisons: scratch `armor7\gt_*`, gt_cmp.py.
- P4 DONE (measured): the live swap works (`--swap-at` fired in town and rebuilt her figure). Perf ABAB, verge combat, 1080p: a mixed look costs +0.17 ms (3.90 -> 4.07 ms; GPU 3.49 -> 3.66), her shadow primitives 0.78M -> 2.46M (pieces have no gameplay LOD). **P9 after B:** a per-slot gameplay/shadow LOD for outfit pieces (the calling LOD files are merged by material, so they can't be split per slot).
- P5 DONE 4e329d33: show-helm = CharacterData.Headgear (`--helm 0|1`; Wear.Look `hide`), row `"hair": "hide"` drops her hair mesh. Checked: the piece path matches her calling outfit exactly (`ar_ref` vs `sm_helm0`). There's no in-game UI toggle yet (routed to the paper-doll UI).
- P6 DONE 4e329d33 + 4ade4e8b: dye zones as data (outfit_materials `zone`; thread is in trim), ItemInstance.Dye, `--dye zone=#hex`, a recolor that keeps luminance (bit-identical when off). Not yet seen in a judged frame (smoke `sm_dye` only).
- **The dimple (owner crop, first mark in A's judge brief):** a small pinch on her LEFT breast (screen right), just outside that cup's inner rim, 1-2 boss-heights above the gore boss, on the warden's own cups. Cause, measured: `tuck_of` (heroine_outfits.py ~8919) maps the skin-to-piece gap straight to depth (t = 0.8 x clamp((4.5 mm - gap) / 4 mm)). Rim tuck values jump 0.25-0.77 between neighbours and differ up to 0.5 left/right, in warden.top AND plate_top_plain. **Rule APPROVED (coordinator):** smooth the tuck over her surface with a bounded step (~0.15 t between neighbours, falloff >= 8-10 mm from the rim), never less coverage, ~0 at and outside the visible rim, mirrored. WIP 9a7d68b5 (`tuck_bound()` in tuck_of, TUCK_SMOOTH=1 default: graze reject |cos|<0.5, 4 smoothing rounds, slope <= 30/m and <= 0.15 per neighbour, edge ramp; piece_blender `ARMOR_SCRATCH_ONLY=1`; tools/armor/tuck_probe.py, tuck_measure.py). UNPROVEN: the last version was never run. Early numbers (warden, before the step cap): the rim pair went from 0.19/0.39 to 0.37/0.45, slot p99 step 5.56 -> 5.02 mm, grazing points tucked 3 -> 0, pose skin-through unchanged. Next: one Blender turn, `bash <scratch>/armor7/tuck_rule/run.sh warden ptp1 ptp0`, then `tuck_measure.py probe` and `tuck_measure.py piece`. Accept: step <= ~1.5 mm, pose and PUSH counts not up. The p99 is still ~5 mm, so the cap must bite: a fresh medium solver (brief in this bullet).
- **ONE rebuild** (tuck rule + Face 31's nape weight fix, `heroine_neck.nape()`, landing as its own early MR, neck-31): when the coordinator says the neck is on integration, merge integration, then rebuild the four outfits slot-split (her body's tuck vertex colours), `python tools/armor/build.py --all`, `python tools/assets/heroine_lod.py godot/art/people`, reimport. armor lead 4's recipe is below; it took about 2-3 h.
- P8 NOT STARTED: the judge shoot after the rebuild. 1:1 frames: each set in its own calling (town play + close-up), cross-calling (plate on arcanist, leather on warden, revealing on stalker; close-up in combat, `--close 1 --auto toward`), a live swap before/after, Oathbrand via `--swap-at`, dye, helm off/on, the worst mixed pairs after P3. ONE max judge, whole-frame gate first, the dimple named first. Shoot script `armor7\shoot.sh <abs list>` (frames to godot/.shots/armor7/).
- P7 (MR B): design brief written, `armor7\b_design_brief.md` (pauldron shell first, which also fixes the creation judge's ragged right-pauldron edge, the balloon and the attack swing; then cuirass with a boob window, cuisses + high-rise g-string, open-face helm). Spawn it while A's judge runs. **The Arcanist hat brim** reads as a flat black disc at the creation Look (geometry: a flat circle at dusk) and goes with B's head work (heroine_outfits.py witch_hat brim/droop).
- Seen, not mine: a Godot GC-handle exception ("Handle is not initialized", SwapGCHandleForType) in one close-up log (sm_pla_close). Harmless to the frame; check whether integration shows it.
- Scratch: the coordinator's scratchpad `armor7\` (texts backed up to survivorsunchained_inputs\scratch_armor7\). Smoke frames: godot/.shots/armor7/sm_*.png. Perf: godot/.shots/perf/armor7_*.json.
Not committed: ~1128 godot .import files rewritten by this worktree's import (generated; leave them, or restore named files only).
Estimate left: A about 8-12 h (P3 finish, the rebuild, P8 with 1-2 judge rounds, the MR); B about 12-18 h.

## Armor lead 6 (19 Oct): MR READY, the hilt carry (warden town run and sprint), judge r2 PASS 8/8
Worktree `.claude/worktrees/armor-5`, branch `armor-5` (junction: never stash, reset --hard or checkout .). Integration merged in.
- **What:** `run.hilt_carry` post-pass (tools/anim/clips/run.py `HILT`, `POST`; `sprint_stop.sprint` applies it too). Her left hand rests on the sheathed sword's throat at her left hip in run_warden_town and sprint_warden_town. idle and the stops are byte-identical. The free right hand is a loose fist (`fingers_r="fist"`, the town run only).
- **Fixes over lead 5's WIP:** the elbow's pole follows her chest (`pole_chest`), because the shield rides spine_03 and the chest's twist swung its rim into the elbow (23.6 mm, now 6.1). After judge r1 (front views: elbow flared, a gunslinger's wrist, a limp right hand): the hand sits 3.3 cm lower on the throat, the elbow swings 30 degrees in, and `clav` 0.3 lets the held shoulder move with the stride.
- **Measured** (all frames, scratch `tools/scratch/armor5/hilt/chk2`): warden sword vs arm 0 (was 28 run, 38-40 sprint); left forearm vs shield 6.1 (right arm 5.3 before); crossbow 0; elbow 123-138; wrist 18-20; warden palm 8-10 mm off; reaver outfit 4.4-6.0 (thumb, not her shipped kit); motion --against base_town and audit clean. dotnet test 993/0/8.
- **Judges:** r1 11/13 (both front views failed), r2 8/8 PASS (`hilt/judge_h1_r1.md`, `judge_h2_r2.md`; frames `hilt/shots_h1`, `shots_h2`). Closed as known (polish, at the cap): seen head-on, the palm sits 8-10 mm off the scabbard (the judge's ideal is 2-3 mm with the thumb over its front edge; the reaver outfit's sword sits 14 mm further out, so one hand can't touch both).
- **Not committed:** godot/art/anim/heroine.res and heroine_clips.json. This worktree's tools/anim/out/clips lacks 3 of integration's clips (cup_hands, flask_drink, ...), so its pack is partial. **The coordinator packs her library in the main checkout after the merge** (`build.py`, her clips; never `--body hero`).
- **Route:** (face or animation) in the closest front frames her eyes drift down and to her right, not along the run. (Animation, from lead 5) the axe and wand fists, the open hand in run_arcanist_wand.
- Tools: `hilt/h.py` (base cache), `full.py <hilt json|x> [overrides]` + `summ.sh` (all frames), `scan3.py`/`scan4.py` (swivel, hand-down scans), `cand.py` (s, swivel, clav -> HILT).

## Armor lead 5 (19 Oct): MR READY at armor-5@975cd32e (steps 5/5b, the socket retune); the hilt carry is PAUSED on armor-5 HEAD
Worktree `.claude/worktrees/armor-5`, branch `armor-5` (junction: never stash, reset --hard or checkout .). **Merge 975cd32e, not HEAD.** The commits after it hold the unfinished hilt carry in tools/anim/clips/run.py; take this page from HEAD.
**In the MR (975cd32e):**
- (5) Oathbrand passes fistfit 13/13, equal to the sword. fistfit.py merges `tools/anim/data/fistfit_pieces.json` (the read hook, offered to animation); `weapon_drop.py fit_row` writes a dropped piece's row from its kind's (FIT_BASE). ArmsDump re-run on anim-39.
- (5b) Plain mount, measured (`tools/scratch/armor5/plaincheck.py`):
  - Axe FAILS: fingers 17-27 mm into the 40x58 haft.
  - Wand FAILS: cast_flick pads 10 mm off and 14 into; the wand runs show an open hand 38-86 mm off.
  - Blade2H, Blunt and Axe2H: NPC-only. She has no clips of them and no Loadouts template.
- Sheath sockets (Arms.cs `Sockets`: back, sling, hip_loop, hip_belt, back_diag). hip_blade is unchanged. socket_clearance.json refit. Measured by `tools/scratch/armor5/sockdeep.py` on the warden town clips (the only sheathed clips in the game), all five outfits; before `deep1_before.txt`, after `deep2_after.txt`, body/arm mm:
  - shield: 2.3/9.2 -> 0/5.4
  - crossbow: 5-15 -> 0 (none: 1.5/2.3)
  - axes: 26-74 -> 0.6
  - wand: body 21-36 -> 0, but its crystal is now 20-27 into her right upper arm in the borrowed sprint (the arcanist doesn't sheathe yet)
  - 2H back: 16-63 -> 0
  - mace: 82 -> 58, closed (NPC-only)
  - The warden's shipped kit moved only 4 mm (the shield), so no judge: it isn't visible at 1:1.
  - Tests: Sheath and WeaponSocket 42/0 (full suite 977/0/8). Nothing in piece.json or armor_index.json changed.
**For animation (route):** the axe fist and the wand fist (above). The wand's open hand in run_arcanist_wand. The sword hilt: her left forearm goes 38-40 mm through it in sprint_warden_town f0-3 and f19-21, and about 28 in the run (the one hit the player sees today; no socket clears it, the best was 30).
**The hilt carry** was paused here; armor lead 6 finished it (above).

## MR READY (armor lead 4, 19 Oct): steps 1-2; next: steps 5/5b as their own small MR
State: armor-1, integration fdebb878 merged in, pushed. dotnet test 974/0/8.
Done:
- (1) The merge REBUILD. heroine.glb is byte-identical to integration's. The four outfits are rebuilt slot-split; every slot mesh's vertices and sorted positions+weights equal integration's (compare.py; the build varies a few triangle diagonals run to run). Plate tops and her gameplay LOD are rebuilt.
- Fixed: the per-slot tucks were keyed before the body post-steps (throat soften, neck cut...) moved her points, so 719 records sat on no vertex. Fixed by heroine_outfits.armor_tuck_rekey; tools/scratch/armor4/tuckcheck.py checks it.
- (2) Three max judge rounds (round cap). Briefs and verdicts in tools/scratch/armor4/ (judge_brief*.md, verdict_r1-3.md). PASS: gilded tier (gilt rim and gore, 12 mm bead, 13.8 mm sapphire in a bezel), etched (steel vine film, blacksteel ground), the mixed look's gore (rigid, skin tucked 3 mm under it: idle clearance 2.96-3.04 mm, tools/armor/gore_idle.py), skin edges, LOD in all four callings, and metal at the close camera. The round-3 strap hide under pauldrons was a regression and is REMOVED. Straps run continuously into the pauldron opening again (lead check at 1:1, r4 frames).
- Numbers. Pieces at LOD0: plain 20,528 tris and 2 draws, etched 29,874 and 3, gilded 29,615 and 4. Her play LOD: warden 991k -> 385k outfit tris, arcanist 533k -> 224k, ranger 701k -> 243k, reaver 468k -> 178k. Draws merged by material (HerLod.Merge).
Open, closed at the cap (route):
- The steel reads blue at the creation camp (Calling camera): the fire puts no warm highlight on metal. This goes to the Marionette armor pipeline and lighting (fire light specular, a desaturated night-sky reflection on metal).
- In the heavy swing (raised arm, close camera) the top's strap can cross the warden's pauldron. That goes to the next armor list: the pauldron slot shell, plus sinking the strap to ~0.5 mm over the pauldron's sweep zone.
- At the Calling camera, etched can't be told from plain (the band is 2-3 px). It's a size limit; an 8 mm band if wanted.
- Animation: the warden's heavy swing and forehand hold the shield tray-flat; in the runs her shoulders shrug the pauldrons to her jaw.
Next: steps 5/5b (weapons) after anim-39 merges (the coordinator names the sockets), as their own small MR.

## Paused here (armor lead 3, coordinator wind-down, 19 Oct); next:
State: armor-1@(this commit), pushed; NOT merged with integration (see 1). Since 000 below: her gameplay LOD built and committed for the four outfits (d5c917d7, heroine_lod.py, CPU, 7 min: warden 991k -> 385k tris, arcanist 533k -> 224k, ranger 701k -> 243k, reaver 469k -> 180k; her play share e.g. warden 1.39M -> 774k visible, reaver 169+149 -> 53+15 draws; 86-322 px differ in her box at 1:1, unjudged: metal speckle, shadow-edge flecks, reaver fur and loincloth edges; frames godot/.shots/lod/), teeth and tongue hidden with the gameplay model, `--her-draws` reports primitives (0719083a). A mixed look still has no outfit LOD (1.24M at play): a per-slot LOD of the calling's other pieces is backlog.
1. **Merge integration (ba7c26ed+, touch-up 4 merged).** It conflicts on all four outfit files (gltf+bin): touch-up rebuilt them on a NEW heroine.glb (throat r2, Reaver cord) with the old naming, ours are slot-split (item 1) on the old body. heroine_outfits.py and the outfit shaders auto-merge. Resolve by REBUILDING, not by picking a side: take integration's heroine.glb, hair and shaders; rebuild the four outfits with the merged heroine_outfits.py (slot mode, as item 1 did; the source scene survivorsunchained_inputs/armor_src/heroine_built.blend must be refreshed to the new body: ask touch-up's handoff, docs/handoff/face.md top, for its build recipe), check the four outfit hashes/looks against integration's (only the slot split may differ), then `python tools/armor/build.py --all` (the body hash guard refuses pieces on the old body), then `python tools/assets/heroine_lod.py godot/art/people`, reimport. ~2-3 h.
2. The 17-frame shoot (tools/scratch/armor3/judge1.txt via tools/scratch/armor3/shoot.sh <abs list>) + the LOD before/after play frames, then ONE max judge (whole-frame gate first; tiers at close-up and calling, fit and look at play; the coordinator accepted that).
3. Steps 5/5b when anim-38 merges (coordinator messages).
4. The MR: name heroine_outfits.py's TUCK DEFICIT block, outfit_materials armor entries, the four outfit LOD files and the teeth/tongue hide (HerLod) for a careful merge.
Helpers: none running.
Estimate left: ~4-6 h plus 1-2 max judge rounds.

## 000. Armor lead 3 (aea63365, 19 October 2026): state
Steps 1-4 of "Paused here" below DONE: (1) the old tier frames showed her BACK (default facing; the close-up sits behind her): front shots are `--facing 0` (play) and `--close 1 --idle-after 1 --seconds 9` (the idle view turns her to the camera). Tiers can't tell apart at the play camera on a top (cups ~6 px): judged at the close-up and calling cameras; play = fit and look. (2) cup sockets mirrored from her right cup's outer face (f1162577); etched redesigned as `etch_band_vine` (027edbb7: blackened band in darkleather at sky 0, bright vine as gaps, fine lines; 28.2k/5.4k/1.8k, 2 draws). (3) Marionette armor-1@9ea110b: gem_mat, base_adorn; kit re-pulled. (4) HerLod.Merge (4e89f13e): play draws merged by material at equip; `--her-draws`, `--merge off`.
Found: no heroine_outfit_*_lod.gltf was ever committed (her full model draws at play); offered to the coordinator. Judge shoot list: tools/scratch/armor3/judge1.txt (17 frames; tools/scratch/armor3/shoot.sh <abs list>; frames godot/.shots/armor3/).
Next: on touch-up's metal landing, merge integration, `build.py plate_top_plain plate_top_etched plate_top_gilded`, reimport, shoot judge1, ONE max judge (whole-frame gate first); on anim-38's merge, steps 5/5b; then the MR (step 7 below).

## 00. Armor lead 2 (18 October 2026, evening): state and next
Item 1 DONE (8a965bd1; tuck reconciled 0373a43f + tools/armor/tuck_fix.py; `ink` accepted as calling skin). Item 2 DONE (2932408e, a3b3d2cf: Wear.Look with calling fill, equipped beats fill (Wear.FallbackOrder), HerWear, tuck map by VERTEX_ID (`tuck_channel == -2`), `--wear`; full sets equal HerOutfit at both cameras; mixed look costs nothing measurable; 971 tests green). Schema: docs/armor/PIECE_SCHEMA.md (00bbcacc), the Marionette/game contract. Source blend: survivorsunchained_inputs/armor_src/heroine_built.blend (85cb2d6f).
Item 3 (unjudged, WIP): tools/armor/build.py + piece_blender.py + piece_lod.py + adorn.py (variants in ~2 s; plain rebuilds byte-identical). plate_top_plain r3 067d2bf0: cups from her breast surface, gore plate, leather back band buckled at the spine, 0 skin through in 7-8 poses (local push-out; side height 7.7 max / 6.4 p99 mm, over the 6 mm rule), LOD0 20.5k / gameplay 4.7k / shadow 1.8k, 2 draws; HerWear+HerLod show the gameplay LOD at the play camera. Tiers 19aa362f, c746b75f: plate_top_etched (24.7k, 2 draws; the etch is a 0.25 mm film layer in the steel mesh, since the metal shader draws only its texture's mean colour), plate_top_gilded (30.5k, 4 draws: gilt rivets, 5 mm gold band, sapphire at the gore). Library tools/armor/lib.py -> godot/art/armor/lib/ (2c9103d1; files Z-up raw = socket frame). Drop tool tools/armor/drop.py (5ac77f3f). Solver reports: lastmsg.py from the f56a8f65 session's subagents folder (3b: a794b2481ce0de3b1; r3: a314ed6064ed3c58c).
Item 6: Marionette armor-1 fe599d2 + 59e9995 (kit pull, Armor workshop panel, export to schema, lab).
Budgets (look bible page 11, 11_budgets.md): large 30k cap, 20k typical (top, bottom, skirt, cloak); pairs 15-20k (shoulders, bracers, greaves, legwear); head 15k; small 8k (belt, trinkets); gameplay LOD <=25%, shadow <=10%; <=2 draws a piece. Dressed: heaviest built style per slot, per hair, after culling, <=350k (300k typical). Her play draws: 40 until an equip-time merge by material lands (ours if cheap, one item before the MR, else backlog), then 20.
**Paused here (armor lead 2, coordinator wind-down); next:**
1. Reshoot the tiers before any judge: plain vs gilded play frames differ by only 2 px, so the piece likely isn't showing at the play camera (camera, timing or the LOD swap in HerWear/HerLod). Fixed crop, same seed/time; confirm the gameplay LOD keeps the gold band. Frames godot/.shots/armor2/tier_*; strip tools/scratch/armor2/tier_strip.py.
2. Etched: the scroll motif reads as a glyph: a design pass (taste: a max solver if one honest try fails). Plain's cup_l socket sits 12 mm off the plate (fix the socket writer). Check the gold band at the sharp cup corners.
3. Marionette follow-up (worker): gem_mat field, base_adorn toggle, material list incl. gems from outfit_materials.json; re-pull the kit (node tools/armor_kit_pull.mjs) after the builds.
4. Equip-time merge by material in HerWear (draws 40 -> 20) if one medium code run, else backlog.
5. Item 5/5b after anim-38 merges (coordinator messages): ArmsDump, fistfit (tools/scratch/armor1/fistfit_drop.py; oathbrand row weapon=("sword",), wrap="sword"), plain-mount check of Axe/Blade2H/Blunt/Axe2H/Wand.
6. Item 4 (mixed look: a tier top + an outfit's bottom/skirt/boots via --wear) and item 7: one 1:1 shoot (play, close-up at its closest, Look; idle, run, an attack) + ONE max judge, whole-frame gate first, after touch-up 3's metal lands on integration (coordinator messages). Judge also rules on the side push and the band sinking with arms overhead.
7. MR (item 8): name heroine_outfits.py's TUCK DEFICIT block and its outfit_materials armor-entries change for a careful merge (touch-up builds from it).
Estimate left: ~6-9 h of agent time plus 1-2 max judge rounds.

## 0. Start here (armor lead 1, 18 October 2026)
The owner: "build and just drag over armor and weapons without having to rebuild hopefully anything animation wise or character wise"; "smart bras and bikinis, smart all parts really ... making new armor shouldnt cost us hours of animation and body edits - it should just work".
State: design settled (section 1); fixed list with state = section 2.

## 1. The design (decided; why in brackets)
1. **Visual slots, by layer** (from what the four outfits already are). L1 next to skin: `top` (bra, cups, bandeau), `bottom` (bikini, briefs), `legwear` (stockings), `gloves`. L2 over: `skirt` (tassets, loincloth), `belt`, `collar`, `bracers`, `greaves`, `boots`. L3 outer: `pauldrons`, `cloak`, `head`. Paired slots are one piece with both sides (mirrored, or `sides: "l"` for one).
   **Item slots (the owner, 18 Oct: "Armor drops piece by piece ... like Diablo or PoE").** Nine armor item slots, each one wearable region the player reads at the play camera, each naming a fixed group of visual slots: Head (head), Shoulders (pauldrons), Body = chest (top, collar), Bracers (bracers), Hands (gloves), Belt (belt, skirt), Legs (bottom, legwear, greaves), Feet (boots), Cloak (cloak). [Collar, skirt and legwear rarely read alone at 22-34 m, so they ride the item whose silhouette they extend (D3's split, which has the same nine plus jewelry). `Body` keeps its name and number, so saves and every existing Body item stand; the six new slots are appended to the enums.] An item names its pieces (`ItemDef.Wear`, piece ids); each must be in its item slot's group. An empty item slot shows the calling's own pieces for that group, never bare skin. A piece that covers more (a suit: top and bottom) hides what it covers whatever else is worn.
2. **One smart shell per slot style, cut from her surface** in `tools/assets/heroine_outfits.py`'s own machinery (`piece()`, `plate_cups`, `bandeau`, `girdle`, `limb`, `finish`, her weights, `clear_of_skin`), run as a new mode of that script (`--slots`) after its body prep. [It already builds every outfit from her body with her weights and passes judges; a second fitter (Marionette's 4 mm barycentric bind) fails them. A body rebuild = one re-run, no hand work.] Every existing outfit piece is tagged with its slot and becomes a style of that slot: four outfits are the first catalogue, mixable. The four outfit files build exactly as now (checked by hash).
3. **Clipping between pieces: the garment tuck** (armor 7, 20 Oct): see docs/armor/PIECE_SCHEMA.md "Garment tuck".
4. **Skin tuck per piece, not per outfit.** The four RGBA channels allow four outfits only. Each built piece carries its own tuck (sparse: her body's bind-pose points, quantized, and the tuck value, from the same tuck rule as now); the game takes the max over what she wears into one tuck map that `heroine_skin.gdshader` reads (by VERTEX_ID; fallback, rewrite COLOR.r). The four channels stay for the callings until they are wear sets.
5. **Sockets and adornment = tiers.** Each shell's build emits named sockets: points with a frame (gore, cup_l/r, strap_l/r, shoulder, knee...), rims (its named edge loops), and its UV surface. Adornment kinds: `mesh` at a point (gem, filigree plate, rune plate, buckle), `row` along a rim (studs, rivets, domes, grommets: the script's own generators), `trim` along a rim (a swept profile: gold edge, piping, fur), `paint` (material, tint, decal, emissive runes). Each mesh or row element rides ONE blend of bones taken from the shell at its foot (as the rivets and clasps do now), so it never bends; trims take the rim's weights. [Sockets are recomputed from the shell on every build, so a body rebuild re-places every adornment.] A tier adds adornment only: no shell, weight or clip change.
   **Form that reads at 1:1 (look bible `docs/art/look_bible/01_armor_metal.md` item 5, ours; items 1-4 and 6, the metal shader, are touch-up's and we consume them):** every metal shell gets a rolled edge (a 3-6 mm bevel that catches a line of light) as part of the shell, not adornment. Trims are raised 1-2 mm with a dark gap, UV-mapped along the rim into ONE shared trim-strip atlas (rolled edge, rivet row, rope, filigree band). Rivets are real geometry that casts a shadow; straps carry buckles; lames sit at the joints. The tier ladder: **plain forged** (rolled edge, rivets), **etched** (+ an etched pattern in the plate's normal/roughness), **gilded** (+ a raised gold trim band, gems, runes). DONE: the three tell apart from the play camera.
6. **Piece data.** Source: `godot/art/armor/src/<id>/piece.json` (+ its adornment meshes): `{id, slot, style, params, material, tint, adorn: [{kind, socket|rim, mesh, scale, roll, mat}], tier}`. Built by `tools/armor/build.py <id|--all>` (Blender, the `--slots` mode) to `godot/art/armor/<id>.gltf` (skinned on her skeleton), `<id>.tuck.bin`, and a row in `godot/art/armor/armor_index.json` (slot, layer, covers for sheath clearance, how rigid it holds her: HerJiggle). Every built piece is stamped with the body build's hash; `--all` after a body build re-fits everything.
7. **Game.** Logic: `Wear.Of(character)` -> visual slot -> piece id from the equipped items (logic/Rpg, no Godot). View: `HerWear` puts those pieces on her (drop that slot's meshes, add the piece's onto her skeleton, `OutfitMaterials`, recompute the tuck map and jiggle), filling empty groups from her calling's outfit. Sheath clearance comes from the worn pieces' covers. LOD: measure the mixed look's play-camera fps in item 2; if it costs, a per-slot LOD generated from the shell (heroine_lod.py's method, per piece).
8. **Weapons** (animation's convention: `docs/anim/GRIP_STANDARD.md` on anim-38, 6418bbfc; read, never edit; grips, pockets, WRAP and fistfit are animation's). A new weapon = a life-size glb with `anchor_grip`, `anchor_sheath`, `kind` (Marionette's sendPiece writes them). `tools/armor/weapon_drop.py`: conform the grip to the kind's section (`grip_conform.py conform --seat`, `--cylinder` for round kinds) and `check` it, measure the length, copy to `public/assets/weapons/`, and write two DATA rows instead of code: `godot/art/weapons/weapons.json` (file, length, kind, node, pistol), which `Arms.All` merges at load (no C# Spec row), and `tools/anim/data/fistfit_pieces.json` (copied from its kind's row), which fistfit.py merges into PIECES (a small read hook in fistfit.py, added after anim-38 merges and offered to animation). Then the arms dump, `fistfit.py <piece>` (the numeric pass) and `armscheck.py --sockets`. A grip that passes needs no animation judge.
   **The unfitted kinds** (Axe, Blade2H, Blunt, Axe2H, Wand: plain mount, never checked in her hand): first a measured check (fistfit on the plain mount, per kind, on the shipped piece: fingers into it, pads off it); the numbers go to the coordinator. A kind that fails gets a fitted fist (a grip_spec type, a pocket, a WRAP pose: animation work, once per kind, then every piece of that kind is data). Until a kind is fitted, the drop tool accepts its weapons only if the plain-mount check passes.
9. **Marionette: the armor workshop** (Build from Parts > Pieces > Armor). Loads the game's armor kit (her body, each slot style's shell, its sockets and rims, written by `build.py --kit`), pick per slot, recolor, place adornments from its pieces library or the forge, export `piece.json` + meshes to `generated/to_game/armor/<id>/`. Game side: `tools/armor/drop.py` pulls from there, builds, registers. [Marionette never writes into the game repo, by its own rule.]
10. **The hero later:** the same slot builders on his body build; a piece.json builds once per body; adornment meshes are shared.

Known limits: her play-camera model (HerLod, one LOD file per outfit) doesn't cover mixed looks; until per-piece LODs exist a mixed look draws the full model in play (perf to measure in the slice).

## 2. Fixed list
1. Slot-granular outfits: slot map, per-(outfit, slot) meshes and tuck, armor_index (sockets and rims come with item 3). RUNNING (a65daa3772cf94af4)
2. Game: Wear, equip by slot, tuck map in the skin shader, armor_index; tests; mixed-look fps early. NOT STARTED
3. The smart top shell (style `plate`, from the warden's cups code) with the rolled edge, the shared trim strip, and the three tiers (plain forged, etched, gilded) as three pieces. NOT STARTED
4. Mixed look: the new top + an existing outfit's bottom/skirt/boots. NOT STARTED
5. A new blade1h weapon through Marionette, dropped in by weapon_drop.py, fistfit pass. PARTLY DONE: Oathbrand made in Marionette's weapon workshop (Marionette armor-1 47e22c8, fdd3fbe; grip 13.672 mm mean vs 13.70); dropped as data (8f6ab7cc: weapons.json, WeaponsData.cs/ArmsData.cs, tools/armor/weapon_drop.py, public/assets/weapons/oathbrand.glb). fistfit (scratch copy tools/scratch/armor1/fistfit_drop.py; its row needs weapon=("sword",), wrap="sword"): oathbrand and the shipped sword fail alike within 0.1 mm on the main checkout's stale clips. Re-run on anim-38's clips after it merges, and re-run ArmsDump then (arms_local.json kept at integration's, d393552c). In progress: ItemDef.Art + per-kind Held template + HerClips.Kind from the Arms kind (no C# per weapon); an `oathbrand` item.
5b. Measured plain-mount check of Axe, Blade2H, Blunt, Axe2H, Wand; failing kinds listed for animation. NOT STARTED
6. Marionette workshop panel + export; the slice's top made through it. NOT STARTED
7. 1:1 shoot (idle, run, an attack; play, close-up at its closest, Look) + ONE max judge with the whole-frame gate. NOT STARTED
2b. RPG item slots: Shoulders, Bracers, Hands, Belt, Legs, Feet added (ItemKind, EquipSlot, Equipment), ItemDef.Wear, equip/unequip, save migration, tests. DONE 88f620fc (Wear.cs Group/SlotOf/Of/Validate; Inventory.Reslot in Saves.Migrate, save Version stays 5; 6 tests in WearTests.cs; 955 tests, 0 failed; the suite takes ~5 min, run it in the background)
8. MR + Marionette branch report; then the remaining slots as data.

Note (18 Oct): Oathbrand's orange gilt was weaponforge.js's own bug (its `hexRGB` took THREE.Color's linear values into an sRGB canvas; fixed in Marionette fdd3fbe). The shared export path is not affected: pieces.js `recolor` converts sRGB in and out explicitly, `mat.color.set` is managed by three.js, and toGame/sendPiece don't touch colours. So no earlier export needs re-checking.

## 3. Follow-ups for the coordinator to route (not mine)
- **Next armor list, item 1: the pauldron slot shell** (cinematics cut close-ups partly for "balloon pauldrons" and a black gap at the pauldron top; armor 3, 19 Oct: backlog, not this MR). Build `pauldrons` as a smart slot shell like plate_top (from her shoulder surface, rolled edge, sockets), which fixes both marks for every set that uses the slot.
- Loot: drop tables, affixes and itemization for the six new item slots.
- UI: the inventory paper doll for the new slots (PackScreen shows only the old ones).
- Crafting: `Crafting.Workable` and the affix Gear list don't include the six new kinds yet (they can't be reforged and take no affixes).
- Kits: OtherKit (the night kit) isn't re-slotted for the new kinds.
- Animation: fitted fists for the kinds that fail the plain-mount check (5b).
- Merge touch-up's armor metal only from integration, when the coordinator says it landed.
