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


Older blocks: history/armor.md (grep by keyword, never read whole).
