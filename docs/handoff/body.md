# Handoff: her body (rig, mesh, weights)

Read README ("Working lean", Safety), RESUME's top, then this page. Work runs in `.claude/worktrees/armor-7` (branch armor-7, junction worktree: never git stash / reset --hard / checkout . / merge / pull with `godot\assets` linked; remove the link before merging integration, remake it after). One writer: the body chain and the armor pieces both live there.

## Arm root (Body 1, 22 Oct): the ONE source-fix round, approved by the owner and main
**Why.** Her arm root fails at the town close-up at game size (the owner's crops, all FAIL, in `survivorsunchained_inputs\owner_frames_22oct\`: reaver_show_armpit.png, reaver_show_armpit_notch_r1.png, reaver_show_shoulder_r1_1to1.png, reaver_show_shoulder_top_facets_r1.png, reaver_show_upper_arm.png). Two corrective rounds (C1, C2) and a restage below level (armor.md, Armor 18) didn't fix it.

**D1 diagnosis (numbers; scripts in the armor18 scratch, `d1\m1-m4.py`): the mesh first, then the weights. FAR.**
- The arm is the coarsest skin on her: a decimated triangle mesh with no loops (16-25% valence 6). Median edge: upper arm 1.27 cm (slivers to 6.2 cm along the bicep), deltoid 0.96, breast 0.74, face 0.18. Vertices per cm2: 1.2 / 1.5 / 2.3 / 27.
- At the close-up (2.80 m, 24 deg, 9.4 px/cm; LOD0, since HerLod switches past 18 m; smooth normals), outline chords are: deltoid 10.8 px with 22 deg corners; arm underside 12.6 px / 14 deg; breast 1.9 px / 8 deg.
- The bicep crease is the twist hand-off across one 6.2 cm sliver (upperarm 0.91 to 0.39). The pit sits at the 4-bone cap everywhere and is already pinched in the bind pose.
- Upper-arm section kept, at t 0.15 / 0.30: idle 1.00 / 0.94, A 58 0.87 / 0.76, A 82 0.79 / 0.70. The inner elbow collapses at any A once the elbow is bent.
- Blast radius at close range:
  - warden_show (A 104), stalker_show (83), reaver_show (82), flask_drink (88), catch_breath, idle_arcanist_break (80);
  - C01 s8 reach_coals (33 px/cm), C01 s10 kneel_to_stand_snap, C03 s8 cup_hands;
  - the town idles, in profile only.

**The round (main's route, 22 Oct):**
1. **Graft first:** take Marionette's shared base arm patch (MakeHuman CC0 quad skin with loops, `C:\Users\munch\Desktop\Marionette\public\base\base.json/.bin`, HANDOFF "Base topology kept"), from mid-clavicle and the pit to the elbow crease. Fit it to her lightly smoothed sculpt and stitch it to her torso ring. Fall back to an isotropic remesh (about 0.4 cm) only if the graft can't match her shape within about 2 mm.
2. Open the bind-pose pit and add a small deltoid cap. Transfer the weights and smooth the twist band over t 0.15-0.6. Project the UVs and re-bake the skin and tattoo. Rebuild the shoulder correctives (shoulder_psd_post) and the elbow shape.
3. Run the chain: a full build with NAPE=0, then `tools/assets/heroine_body_post.py`, with the neck graft restore checked index-safe. Then build.py --all, cover.py, heroine_lod.py, reimport. Never `--body hero`.
4. Measure before the judge:
   - deltoid and underside chords and corners within 2x the breast's (1.9 px / 8 deg);
   - section ratios at idle, A 58, A 82 and with the elbow bent;
   - wearcheck per outfit against the baseline below;
   - neck graft indices;
   - fistfit unchanged.
5. ONE max judge with the whole-frame gate, calibrated on the owner's crops. Arms-down frames are RE-JUDGED, not frozen.

**Baseline wearcheck** (22 clips, today's art, correctives on): `armor18\wc_on\table.txt` (off: `wc_off`). The sum of OUT>2 counts is 48417 on and 47537 off. The C2 correctives made the plate pauldrons worse at flask_drink (skin under plate_pauldrons 29-37 to 155-173).

**State:** stage 1 (graft fit study) starting.
