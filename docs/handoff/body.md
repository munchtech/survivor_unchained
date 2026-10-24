# Handoff: her body (rig, mesh, weights)

Read README ("Working lean", Safety), RESUME's top, then this page. Work runs in `.claude/worktrees/armor-7` (branch armor-7, junction worktree: never git stash / reset --hard / checkout . / merge / pull with `godot\assets` linked; remove the link before merging integration, remake it after). One writer: the body chain and the armor pieces both live there.

## Body 6, 24 Oct: nude OWNER GATE sent; WAITING for the owner's ruling
Scratch B6 = coordinator b8322a60's scratchpad `body6\` (B5 = `body5\`, keep both). Sheet `B6\gate_owner.png` (half `gate_owner_half.jpg`), built by `B6\sheet.py`; TODAY frames `B6\today\` shot by `B6\shoot.sh` (body of record `B5\lift\post\heroine.glb`; overhead = git res, everything else = `B52\pack`); BEFORE = Body 3 gate7 column 1. Row 7, the worst case: warden cast_raise@0.10 `--sheathed` (A 148-160), front (`B6\shoot1.sh`).
Full test on armor-7@d37180c6 (repo heroine.glb, lift code in): 1082 passed, 0 failed, 8 skipped (1090).
No new judge (judge 13 stands). Next on the owner's ruling: a raised-arm round on judge 13's fixes (or not), overhead vs lowered, then the G3 chain (see Body 5 below), the dressed judge, the full test, the MR.

## Body 5 HANDOFF, 24 Oct: (c) closed; (a) twist rig built, raised arm at NO-medium (judge 13)
No helpers running. B5 = coordinator b8322a60's scratchpad `body5\` (keep it; texts not yet backed up). S4 = 2ea92279's `body4\`.
**Body of record now (unmerged; nothing installed in the repo):** cl3 + UNFOLD + twist chain + new lift + delta-mush correctives = `B5\lift\post\heroine.glb` (stripped base without the shoulder/axilla morphs: `B5\fold\base\heroine.glb`; blend `armor_src\heroine_built_armScl3uf.blend`; pack with the chain bones' rest tracks: `B5\a2\pack\`; skeleton JSON `B5\a2\skel_new\`; axilla pose dump at the new lift `B5\lift\dump\axpose.json`). Rebuild the correctives on a base: `B5\lift\post_lift.py <dir>` (= post2 with PSD_MODE=dm and the new dump). Shots: `B5\cor\shoot.sh` pattern (overhead = git res, everything else = `B5\a2\pack`).
**Commits (armor-7):** dd35c121/6d9be397 the twist chain (helpers.py + HerJoints/ArmTwist.cs, gated on upperarm_twist_02: hero/NPCs byte-identical; ArmTwistTests parity); 1ccd5ef3 post_run.py in v2b; 4207a083 shoulder_psd per-side authoring; e4b84727 shape.py step 10 UNFOLD (the left-arm needle-triangle fold; nick gone at 1:1, judge 13); dc656017 PSD_MODE=dm (NOT yet the default: make it so when this body ships); 10e36f22 clavicle lift curve 34*smoothstep((A-60)/120) (C# + helpers twin; the Look gets <=0.28 deg, invisible, accepted).
**Judges:** 11: the towel twist is GONE (shear 10.8 -> 6.5 deg/cm, girth kept); overhead preferred over the lowered restage (stubby at 3/4). 12 (procedural correctives): NO-medium -> scrap rule -> rebuilt from delta mush (main approved). 13 (`B5\lift\sheet_r7.png`): NO-medium. Fixed: the 3/4 shelf/V mostly, the trap fine at A 115, the left nick, no regressions at the Look/idle. Still failing at the overhead FRONT: (1) a ball-joint hump on the shoulder top, grown with the lift: the clavicle-to-upperarm weight step; spread that blend over 50-60 mm, then fill the notch ~5 mm and lower the hump 6-8 mm in the A 90-140 samples; (2) the raised arm a smooth tube: a 1.5-2 mm deltoid-insertion V groove at ~45% down, a 2 mm biceps/triceps groove on the underside, the belly 4-5 mm slimmer (on the rest mesh at half depth if delta mush can't carry it); (3) the front pit a tucked crease: chest-edge ridge 3 -> 1.5 mm, falloff 60 -> 90 mm, drop the 1.5 mm hollow, one broad 3-4 mm hollow ~40 mm across. Also needed before the gate: a frame at A >= 140 (the trap crease counts rose there).
**DECISION PENDING (main/owner):** raised-arm definition is at medium twice. Lead's recommendation: take the nude owner gate NOW (the twist the owner failed is fixed; show overhead C vs restaged, with judge 13's three marks named) rather than spend ~0.5-0.8M more before the owner sees it; the owner decides whether the overhead definition round runs. Alternative: one more round on judge 13's fixes (weights + correctives + rest-mesh grooves; a medium solver ~250k, a shot turn, a judge).
**Then:** the nude gate sheet (reuse BEFORE/today cells from `S3\gate7`; the coordinator opens it first), the G3 outfit chain once with TWIST_CHAIN=1 (heroine_outfits.py; pauldron SP_ROW moves to twist_02; ranger wear's 493/603 stale tuck points re-recorded), commit the new axilla pose dump, dressed judge, full test, MR. A note for animation: clips roll the upper arm 137-174 deg (axe, throw, cast_bolt, death_back), probably retarget leftovers.
Cost of Body 5: (c) r2-r3 ~0.95M; (a) design 164k, code 180k, build 136k, correctives 176k, dm 146k, fold 152k, lift 141k, judges 120+90+83k, lead ~250k. API $0.

## Body 5, 24 Oct: (c) CLOSED after round 3; next (a) the twist rig
Scratch B5 = the coordinator b8322a60's scratchpad `body5\` (pose, mesh, collar, hand, shots). S4 = 2ea92279's `body4\`. Don't clear either.
**Body of record (unmerged, not yet in the repo's heroine.glb): cl3** = `VEE=6 VT=0.26 VPHI=30 NOTCH=0 CAPTOP=6 BELLY=6 DOME=0.5 NARROW=14 SLIM=0.5 COLLAR=3 BLN=Scl3 bash S4/shape/run_v.sh S4/bnb/w cl3`, then `post_run.py ... --reaver`. Post-stepped glb: `B5\collar\post\cl3\people\heroine.glb`. Blend: `armor_src\heroine_built_armScl3.blend`. The (a) rig work builds on THIS blend.
**Code (armor-7):**
- 7fa02100, bbe3413c: shape.py step 8 VEE/NOTCH/VT (a teardrop cap: a front-lateral fill into the deltoid V).
- 9cd70cad: step 9 COLLAR (clavicle ridge, hollow and notch; zero near the neck graft's seams).
- 2f437d9a, 0960dd5a: HerPose Look-only arm fields (LookArmsDown/Roll/Swivel L/R, plus left-hand Fan/Curl/Thumb), eased with the crossfade, set in GameFront.FigureArms; `--look-*` try flags.
- 05594101: the Look defaults: right down 10, left swivel 31, left hand on her hip (roll/fan/curl/thumb 0), framing pan 0.04 m, and body light B (`--body-key-at`, default 0.55,3.0: the broad body cone only; the face cone is unchanged).
**Judges:** 9 (r2) NO-close; 10 (r3, last on the cap): town +/-0.8 day and night SHIP, the Look turn 40 with the hand on her hip SHIP. Look front NO-close on one item: the inner two-thirds of the collarbones and the sternal notch stay blank under the Look key. CLOSED AS KNOWN (main's call at the cap). Measured: even a 9 mm ridge (x3 preview) gains about 0 luma on the inner yoke under light B (`B5\collar\cols.py`); geometry can't reach it. The real route is a soft painted clavicle cavity in the neck-graft paint/AO (Face's asset, its next session).
Clavicle shortening: closed (breadth 2.82-2.86 head widths at the Look).
Known: a folded face pair on the front of the LEFT upper arm (t 0.21, phi 93; absent on the right, likely from the mirror step). Best guess for the reaver_show "arm tick". Look at it inside (a).
**Next: (a) the twist rig** (twist_02/03, ramped weights, share ~0.4; helpers.py, HerJoints.cs, skeleton JSON, every outfit re-split; regress raised/rolled clips; measure the towel at reaver_show@0.77 and at the Look arm). Then the nude owner gate, the G3 chain, the dressed judge and the MR.
Cost of (c) r2+r3: solvers 144+151+172+98k, judges 114+122k, lead ~150k; API $0.

## Paused after (c), Body 4, 23-24 Oct night
Scope this session (the owner, via main): step 1 only, which is the B-narrow-on-B-mid build and the (c) measure and shape. Nothing below is merged.
Scratch S4 = the coordinator 2ea92279's scratchpad `body4\`. It keeps the exports. Texts and scripts are backed up to `survivorsunchained_inputs\scratch_2ea92279\body4\`.
**Built:**
- Bnb, the owner's pick: `SLIM=0.5 NARROW=14 DOME=0.3`, recipe `S4\bnb\run_bnb.sh`. Post-stepped: `S4\post\Bnb\heroine.glb`.
- c6b6, the chosen variant: `SLIM=0.5 NARROW=14 DOME=0.5 CAPTOP=6 BELLY=6` (ELLO -25, ELHI 60). Post-stepped: `S4\post\c6b6\heroine.glb`. Blend: `armor_src\heroine_built_armSc6b6.blend`.
- Post-steps use `S3\post\tools\post_run.py <glb> <out> --reaver`.
**Code:**
- 5f62eb02: creation's Look loops her town idle, sheathed (GameFront.FigureArms). Before, the guard idle leaned her 5.6 deg forward and sank her head.
- 1bc8db67: shape.py step 8 gains the CAPTOP and BELLY knobs (0 = Bnb unchanged). The Look's ChinUp goes to 0 (head level; it was 5.8 deg down).
**Measures** (`S4\look\bnb.txt`, `S4\shape\look_c6b6.txt`; scripts in `S4\look\` look.py, top.py, cap3d.py, neck.py):
- The Look camera adds nothing (26.7 deg at 2.14 m, against the town's 24 deg at 2.69 m: within 1%).
- Breadth over head width: rest 3.27 (Bnb) -> 3.23 (c6b6). Straight on 3.10 -> 3.07. Body 2's research spec puts typical women at about 2.9 (bideltoid about 1.96 head heights).
- The mesh has about 4 mm per side left. Anything more is skeletal: 12-16 mm per side off the clavicles, a rig change.
- The arm tick is NOT in the paint (no mark in any base color). It's likely a crease or normal fault; skipped.
**Judge 8 (max, `S4\shape\sheet_r1.png`; columns BEFORE | today | Bnb with the new pose | NEW c6b6; crops in `S4\shape\jcrops\`):** the shoulders at the Look are CLOSE.
- The town close-up at +/-0.8 SHIPs.
- The Look front and turn 40 are NO but close. The football read is far better than BEFORE and today: 85-90% of that is the pose, 10-15% the shape.
- Still left at the Look: her left cap reads as a separate knob (an outline notch and a crease at the arm). At turn 40 the near deltoid is a round dome on a narrower arm. Not deflated.
- Her face is better with the head level: keep ChinUp 0 (-1 at most).
- A staging regression: the town idle's right forearm runs under the UI panel at the Look front.
- The clavicle cut is not worth it now.
**Next, round 2 of (c):**
1. Pose: a Look-only arm offset, like ChinUp. Upper arms down from 20-30 deg to 10-15 deg, the left arm turned less inward. Check arm/breast contact, and that the forearm clears the panel; if not, move her about 50 px right.
2. Mesh: a teardrop cap. Raise the deltoid V to about 8 mm proud, fill the back-of-cap notch 2-3 mm, and don't flatten the dome further.
3. Optional: a light A/B with more fill from camera right at the Look.
Reshoot only the NEW Look cells, plus the close-ups after any mesh change, then re-judge. A night shot is needed before (c) closes. Estimate: about 0.3-0.4M tokens, 2-3 h.
**Then (a), the rig fix:** about 1.5-2.5M tokens, 8-12 h. After it, the nude owner gate (about 0.2-0.3M), and after the owner's yes the G3 chain, the dressed judge, the full test and the MR (about 0.6-0.9M).
**Owner decision, held:** clavicles 12-16 mm shorter per side, only if the owner still calls her too broad after round 2. It's a skeleton change that touches every clip and every armor fit, so it would ride with (a).
**Notes for others (judge 8):**
- Face: the purple patch at the neck base shows in the guard and combat idles, hidden by the new Look pose. Also a dusky shadow at the throat base at the Look front, her face a step paler than her torso, and dark specks on her left forearm at the Look front.
- Ranger wear: 493 of 603 tuck points are stale.
Cost: measuring solver 150k, worker 42k, shape solver about 140k, judge 115k, lead about 75k. API $0.

## At the owner gate (Body 3, 23 Oct night); superseded by Body 4 above
Scratch S3 = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\2ea92279-b96d-4eee-9202-d8d2ca78739a\scratchpad\body3` (the coordinator 2ea92279's scratchpad, `body3\` only). Text backups go to `survivorsunchained_inputs\scratch_2ea92279\body3\` at the end.
**Final gate sheet:** `S3\gate7\gate_final.png` (1:1; columns BEFORE eb667858 | today (integration 3559d1dd) | B-mid | B | B-narrow; rows: idle close-up +/-0.8, reaver_show 0.77 at 3/4 (`--facing 45`; `--close-turn` does nothing during `--hold`) and front, the Look front and turn 40 at `--zoom 0.45`). Max judge 7 (`S3\judge7\`): **B-narrow is the pick, medium overall.** The town close-up SHIPs in all three new columns. The Look camera's football shoulders remain in every column (B-narrow cuts them by about a quarter). Rows 3-4 FAIL in every column: the owner's "wrung out towel".
**Diagnosis (`S3\twist\`):** (1) The towel is the RIG. There is ONE upper-arm twist bone, driven at half the roll; the pit band is about 75% on zero-roll bones; the roll lands at z 2-14 cm (9.5 deg/cm); the pit section goes 1.16 -> 1.83. (2) The football shoulders are the REST shape: breadth 525/530/508 mm vs a 162 mm head (3.1-3.3 head widths, target about 2.7), and B's cap is 1.25x the mid-arm radius. Options sent to main: (a) rig: twist_02/03 plus ramped weights, share 0.4 (1.5-2.5M tokens, 8-12 h); (b) a reaver_show restage (0.2-0.3M; prototype `S3\twist\proto\reaver_show.json`); (c) the shoulder rest shape: NARROW about 22 mm on B-mid's girth plus a smaller cap (0.3-0.5M). Nothing started.
**Built (all post-stepped; positions keyed, verified against integration):** `S3\post\{B,Bmid,Bnarrow}\heroine.glb`.
- Rebuild with `tools/assets/arm_graft/v2b/run.sh`. B-mid = `SLIM=0.5` (`S3\bmid\run_bmid.sh`). B-narrow = `NARROW=14 DOME=0.3 ELLO=-25 ELHI=60` (`S3\narrow\run_bn.sh`). Then post: `S3\post\tools\post_run.py <src> <outdir> --reaver` (nape, breast_sym, neck_shape, neck_relief, worn_reaver; NOT arm_shape, axilla_fold, shoulder_psd, LOD).
- shape.py now runs on the welded topology (9da45ee0): the forearm slits are closed, open edges are 94 = orig.
- Blends: `armor_src\heroine_built_arm{B,Bmid,Bnarrow}.blend`.
- A is scrapped.
**Gotchas:**
- armor-7 HEAD's `head_tex/heroine_freckles_graft.png` belongs to the arm-root graft. Any old-UV body (orig, B*) needs integration's map (blob 9cfca4db), or a false brown shoulder blotch appears (sky-share alpha).
- `tools/anim/out/clips` holds Armor 18's RESTAGED reaver_show (d2eb0c5c, arm at/below level). Body 2's `clav\packed` is built from it. Integration's reaver_show is overhead. The owner decides which ships.
- The worktree's stale heroine.res (22 Oct) is in `S3\stale\`.
**Measures:** `S3\meas\table4.md`. The grip eye-check found no grip broken by the clav hold.
**Next, after the owner's pick:** the fix(es) the owner picks, then the G3 chain on the chosen variant (outfits, correctives, wearcheck, LOD; the install fills the outfit tuck channels, which the raw exports lack), the dressed judge, the full test, and the MR.

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
