# Handoff: her body (rig, mesh, weights)

Read README ("Working lean", Safety), RESUME's top, then this page. Work runs in `.claude/worktrees/armor-7` (branch armor-7, junction worktree: never git stash / reset --hard / checkout . / merge / pull with `godot\assets` linked; remove the link before merging integration, remake it after). One writer: the body chain and the armor pieces both live there.

## Paused here (Body 2, 23 Oct); next:
**The owner failed the arm graft on sight (23 Oct):** "basically there was just a massive resculpt/remake and I was unhappy with it" / "the arms skin looked twisted and weird. not toned or sexy  the one arm looked goofy" / "the idea was correct. her shoulders were too high and there wasn't sexy feminine definition. it just was executed poorly. research and try again". BJ1's PASS is overruled. Plan (main): research, then diagnosis, then two shape variants built in parallel (A: the graft's topology resculpted; B: her original arm densified and resculpted), then an **OWNER GATE before any chain**: nude original | A | B at `--close-turn` 0.8 / -0.8, the default close-up and the Look, by day, on one 1:1 sheet; one max judge (a su-lead-max SUBAGENT: **no API credits this session**); the owner picks. Only after the owner's yes: the G3 chain (outfits, correctives, wearcheck, LOD), the dressed judge, the MR. Scratch S = `survivorsunchained_inputs\scratch_23290ad1\body2\` (texts and sheets; the live scratch with the exports is the coordinator 23290ad1 scratchpad `body2\`).
**1. Research: DONE** (S `research\spec.md`, `topology.md`, `board.jpg` (unjudged, for us only), `sources.txt`; ANSUR II women, Polycount topology). Key numbers: shoulder slope 22 deg (19-25) side neck point to acromion; trap 4.2-4.7 cm above the acromion at the idle; acromion ~0.39 H below the chin; deltoid cap peak at t .15, V at t .46, ~10 mm proud (6-14); girths upper arm : elbow : forearm : wrist = 1.72 : 1.42 : 1.55 : 1 (front widths about 90/79/69/77/39 mm); a flat wrist 1.4:1. Topology: the hybrid (bendy-straw rings opening into one deltoid loop), the open pit, twist bones never only at the wrist, no shrinkwrap fitting, no re-bake onto slid topology, trap weights to the clavicle. (d_a: don't use "acromion vs the jugular notch"; her notch sits high.)
**2. Diagnosis: DONE, three solvers** (S `d_a`, `d_b`, `d_c` result.md):
- Height: at rest both arms meet spec; the idle rides high from (c) weights (the graft's upperarm weight .71 on the shoulder top / .44 on the outer trap vs the original's .54/.26), (b) the CLIPS' clavicle keys (+0.65 to +5.6 cm in the town idles; mocap shrug via retarget.py), and (a) the mesh about 0.8 cm short of 22 deg plus a dent 12 cm from the midline. The C# (ClavicleLift, ShoulderPsd) contributes nothing below 90 deg.
- Twist: the WEIGHTS at the raise (the upperarm twist share .40 of the pit band vs her .28; shear 5.0/4.5 vs her 2.2/3.0 deg/cm at A 82). The UVs and rings were fine. The re-bake halved the paint's fine detail.
- Goofy and untoned: the posed arm swells (+3.8 mm, 16 mm forearm) from the re-carried weights; the deltoid lost its clavicle weight. The tube shape (elbow wider than the upper arm, a round wrist, no cap) is INHERITED from her original. Forearm : upper arm 0.88 vs 0.78 is the skeleton (not touched; known).
**3. Shape round: BUILT, UNJUDGED, partly measured** (nobody has looked at the sheets yet, the lead included):
- **Clip fix** (`tools/anim/clavhold.py` + `build.pack()`, on by default, `CLAV_HOLD=0` off; packed into scratch `clav\packed\`, NOT into godot/art/anim). Town idles' shoulder lift is now -0.14..+0.22 cm (was up to +5.6), sway kept. Still to check by eye: off-hand grips on the staff (0.7-3 cm), crossbow (1.3-1.8), chain_strike 2.1, throw 1.9; leap landing, lie_side_wake, sit_back_heels contacts; idle_arcanist_staff_town's free left hand 5.5 cm lower. S `clav\result.md`.
- **Variant B (the front-runner):** her own UVs and paint EXACT (no bake), arm densified by split/flip/relax (median edge 1.03 -> 0.48 cm), weights hers plus the trap rules, right arm mirrored. Idle slope 20.4/21.8 deg, trap 3.88/4.24 cm, girths 280/234/246 mm (target 260/215/235; kept at the top of the range by Body 2 on a misreading: the owner's "massive resculpt" words described the failed graft, not a rule against reshaping (the owner, 23 Oct, via main); girth is picked by eye at the gate (B-mid vs B); `SLIM` scales it), cap 9-11 mm proud. Misses: the wrist stays round, 174 mm (the hand ring is fixed). NOT measured: pit crease, twist share, A 82 shear, swell, posed L/R, chords. It moved neck-graft skin beyond 8 cm from the midline (needed to lower the shoulder): accept it, and re-record the neck graft npz in the chain. Blend `armor_src\heroine_built_armB.blend`; rebuild `bash tools/assets/arm_graft/v2b/run.sh <work> b3`; S `s_b\result.md`; export scratch `s_b\heroine.glb`.
- **Variant A:** the graft re-weighted (her weights + the rules), paint re-baked per side into a new `skin_arm` material (26-35 px/cm), right arm mirrored. Misses: idle slope ~16-17 deg (19.6/22.4 only with the clip fix), the LEFT pit crease 77 deg (a new fold), flask pit 58/67, A 82 shear 4.8/4.4, paint high-pass only 67/84% of hers, pores need a per-surface scale (People.cs:1634). Further behind than B. S `s_a\result.md`, `HANDOFF.md`; blend `armor_src\heroine_built_armA.blend`.
**Next, in order:** (1) a runner measures B's missing deformation numbers with d_b/d_c scripts (pit, twist share, shear, swell, L/R posed, chords); (2) the gate shoot: install each glb in turn (original from integration, A, B) plus `clav\packed` into godot/art (never commit heroine.res/heroine_clips.json), then shoot nude at close-turn 0.8/-0.8, the default close-up, reaver_show 0.77, the Look, by day, as original | A | B, one 1:1 sheet; (3) one su-lead-max judge, calibrated on the owner crops in `owner_frames_22oct\` plus the owner's 23 Oct words as FAIL, checklist "toned, sexy, feminine; shoulders not high; both arms match; no twisted skin"; (4) the lead opens the owner-crop regions at 1:1 itself; (5) the sheet path goes to main for the owner. Scrap A if it is far behind at the judge (say so). Grip/IK fixes from the clip pass belong to the chain step.
**Cost (23 Oct):** research 141k; diagnosis 130k + 117k + 104k; variant A 212k + a continuation lead ~255k; B 227k; clip pass 129k; the lead ~115k. About 1.43M tokens, API $0.

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

**State (Armor 18, 22 Oct night).** The pipeline rebuilds from the ORIGINAL blend:
`bash tools/assets/arm_graft/g2c/run.sh <work> <g2/g1d.npz> <g2/VG_v1.npy> <people dir> [tag]`. Its README is `tools/assets/arm_graft/g2c/README.md`; read the "g2d additions" section. Inputs are in the armor18 scratch `g2\`, backed up to `survivorsunchained_inputs\scratch_543ece4a\armor18\g2`. Output: `survivorsunchained_inputs\armor_src\heroine_built_armroot.blend`.

- **G1** (2db153b2): grafted the MakeHuman quad arm from Marionette's base. The fit p95 is under 1 mm. Both arms are done separately; her two sides differ.
- **G2a** (fc7d26b0): built the measuring harness `arm_graft/g2a/meas.py` and the proxy.
- **G2b** (aa04bb19):
  - baked the arm_shape field and the faired pit into the blend;
  - wrote the pit and cap weights;
  - retired body_post step 6. `heroine_arm_shape` now runs only with `--arm-shape`. **The source blend must switch to the armroot blend when this merges.**
- **G2c** (7be25ef3): extended the graft to the wrist, as one pipeline.
- **G2d** (20c1c510): graded the wrist, faired the shoulder top.

Real export (`heroine_outfits --body --only warden`, no post steps), right / left:

| Measure | Now | Before the round |
|---|---|---|
| Pit crease at rest | 33 / 34 deg | 51 / 45 at G1 |
| Pit edges past 30 deg at A82 | 0 / 3 | |
| flask_drink pit crease | 44 / 63 | 129 at G1 |
| Upper-arm sections at A82 (t .15 / .30 / .5) | .79 / .71 / .88 and .81 / .73 / .93 | |
| Deltoid chord | 3.2 / 2.8 px | D1: 10.8 px / 22 deg |
| Bicep chord | 4.1 / 3.1 px | |
| Forearm chord | 4.6-4.7 px | 9-25 |
| Corners | 1-4 deg | |
| Elbow ring step | 1.21 / 1.15x | |
| Wrist ring step | 1.49 / 1.59x | |

Small residues, numbers only, NOT yet seen at 1:1. The judge decides whether they show:
- the shoulder-top junction turns -14/+14 right and -22/+23 left (deg/cm);
- the shoulder-top chord is 4.2 / 4.5 px;
- 12% / 10% of inner-elbow faces lose more than half their area at a 112 deg bend.

**G3** (a80867bc tools, b8a9cacd art) installed the full chain from the armroot blend (four outfits, body_post with the correctives re-authored, freckles, build.py --all, cover, LOD, reimport). It also fixed a wrist fold in heroine_outfits' weight easing (`WRIST_KEEP`). dotnet 1076/0/8; fistfit unchanged. **G4** (18b7ea05):
- reaver.top's own tuck re-run (`wrap_post.py --tuck-only`);
- mar_her_bracers' rigid blend no longer takes the hand (`params.rigid_drop`);
- wearcheck gained area-weighted columns (`table_area.txt`; `WC_ART` measures another revision). The skin vertex count rose with density alone, so judge by AREA.

| Wearcheck | Old art | Now |
|---|---|---|
| Area >2 | 224148 | 207222 (-7.6%) |
| Count | 48417 | 50927 |

Still over baseline by area (combat poses): plate tops and cuirass under the pit (cast_raise), ranger.pauldrons (leap, crossbow_shoot). plate_pauldrons_warden's adornment fails build.py's skin check (399 points in arms_overhead; its base clips there too); etched and gilded fail by 0.1 mm.

**BJ1 (max, API, $2.60): FAIL on 4 of 15 sheets, NONE for the arm.** Verdict: `godot/.shots/body1/j1/verdict_bj1.md`. Sheets: `godot/.shots/body1/j1/sheets/` (index `sheets.txt`). Shot list: `...\armor18\j\j_list.txt` and `cine.json`.
- The arm passes at 1:1 in every frame: all four faults in the owner's crops are gone (deltoid round, no ramp or facets, no pinch or fold line, no lumps, the tattoo flat, the inner elbow soft). The armpit is a soft hollow where it shows (warden_show, idle_arcanist_break).
- Residue: a faint trapezius-to-cap step on her LEFT shoulder, in outline (s02, s03-s04).
- The FAILs are not the arm:
  - flask_drink 1.0 s: the forearm runs through her torso (the pose; R1 changed only 3-4.4 s, so check whether it was always so);
  - the arcanist hat brim underside renders black (a known item, out of scope);
  - C01 s8's face close-up (glassy, misaligned eyes) and C01 s10's braid fishnet at night: face and hair leads.
- **Not yet certified:** the armpit at the owner's angle. The owner's crops were from a closer, turned camera.

**Next (for the successor):**
1. Reshoot reaver_show 0.77 and warden_show 0.63 at `--close-turn` 0.8, -0.8 and 1.57, nude and dressed, plus the character-creation Look camera. Add catch_breath 3.3 at a turn that shows the left armpit. Use the worker brief `...\armor18\j_shots_brief.md` with run.sh `import`.
2. One API re-judge (max), the same brief `...\armor18\bj1.md`, on those sheets only.
3. If the left trap step shows there, give it one fix in `arm_graft/g2c/post.py` (a directed fill on graft-owned vertices, TOP_*). Re-run the pipeline and the G3 chain.
4. flask_drink 0.8-1.2 s: scrub it; if the forearm-through-torso is old, it belongs to the clip (story_c04.py), not the arm.
5. Then the MR: dotnet, wearcheck by area, MR READY with the sheet list.

**For the merge:** the source blend changes to `survivorsunchained_inputs\armor_src\heroine_built_armroot.blend` (build.py's default already points there), and body_post step 6 is off. armor-7 also carries the armor R1/R2 clip work, which is unjudged (armor.md top). Temp scratch armor18 holds about 3.6 GB of exports. Texts and pipeline inputs are backed up to `survivorsunchained_inputs\scratch_543ece4a\armor18`; bin the Temp copy once this round closes.

Cost this round: D1 100k, G1 212k, G2a 183k, G2b 114k, G2c 170k, G2d 145k, G2e 184k, G3 207k, G4 208k, J-shots 68k (about 1.6M tokens); API $2.61.
