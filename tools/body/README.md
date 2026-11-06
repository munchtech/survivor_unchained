# tools/body: the body's check

> **`tools/body/out/` is a git-ignored CACHE: never delete it by hand; if it is lost, restore it in this order
> (5 Nov restore: every output matched byte for byte or to 0.0 mm).**
> 1. The MakeHuman reference `out/run_a` (needs the pre-22494f355 placement, which HEAD's `skeleton.place_skeleton`
>    now refuses), from the last code that built it, in a scratch tree, output pointed at this checkout:
>    `git archive d48cf240c tools/body tools/anim tools/assets/heroine_face/targets godot/art/people/heroine.glb | tar -x -C <scratch>/oldtree`,
>    then in `<scratch>/oldtree`: `python tools/body/build.py tools/body/specs/base_woman.json <repo>/tools/body/out/run_a`
>    (takes and gives back the Blender turn itself; ~2 min).
> 2. `python tools/body/topo_build.py --check-determinism` -> `out/topo/{close,play}.npz` (topo_sha close
>    2f3fff29b655fbfb, play a7f5aacfdd6e4cea = the `topology` stored in `base/uv_*.npz` and `forms/her_topo_*.npz`).
>    Proof: `topo_corr.Reference().close(None)` vs run_a close.npz 0.0 mm; `topo_corr.evaluate(base/topo_corr_<tier>, ref)`
>    and `base/sliders_<tier>.npz` V0 vs out/topo V 0.0 mm.
> 3. Her build: `python tools/body/build_topo.py tools/body/specs/her_topo.json tools/body/out/her_ek2_final` (no
>    slider_bake cache needed) -> body.glb/play.glb/rig.json/play_rig.json byte-identical to `godot/art/people/body_p1/`.
>    CAUTION: the spec's `"maps"` IS `godot/art/people/body_p1`, so the bake rewrites the published maps in place
>    (they came back equal to git HEAD; only bake.json's timing `"s"` changed: restore it from HEAD).

`check.py` is the CHECK command for her body (docs/team/PIPELINE.md P1): numbers first, a judge only on what they
cannot say. Pure Python (numpy, scipy, embreex, Pillow); no Blender or Godot.

    python tools/body/check.py <body.glb> [--ref A.glb] [--rig rig.json] [--play play.glb] [--far far.glb]
                               [--poser game|lbs] [--same-head] [--topo NPZ] [--only contract,tris,weights,bends,silhouette,topology] --out DIR

Baseline (the shipped body A against itself, the game poser), about a minute:

    python tools/body/check.py godot/art/people/heroine.glb --ref godot/art/people/heroine.glb --same-head --out <dir>

Out: `check.json` (every number), `summary.txt` (one screen), `strip_<joint>.png` (the bend sheets), `sil_<view>.png`
(the silhouette XOR, red). Exit 1 only on a hard fail (`check_spec.json` "hard": the same head, NaN or negative
weights, sums off 1, more than 8 influences). Everything else reports against `targets` until the lead tightens it.
Tests: `python -m pytest tools/body` (or `python tools/body/test_check.py`).

## The numbers

- **contract** (with --ref): node, mesh, material and skinned-mesh names only in one file; blend-shape names per
  mesh; the skeletons' bone lists (reported, never failed: B's skeleton is meant to differ). `--same-head` (P1 B2a: the
  head compared IN THE WORLD AT REST, since our build bakes A's +7% Head rest scale into the meshes): the five head
  meshes' rest world positions (each file's own rest @ inverse bind, skinned) within 1e-5 m of the ref's
  (`world_rest_max_diff_m`); normals, UVs and triangles equal as stored; blend-shape names equal, their POSITION moves
  equal in the world (times each vertex's blended rest scale) within 1e-5 m and their NORMAL moves as stored;
  `P_bytes_equal` reported only. And the body's boundary ring at the neck within 1e-5 m of the head's open boundary,
  both at rest in the world (`boundary_ring.max_gap_m`). (The old byte test passed the hm08 build corr_a, whose head
  is 2.6 cm off A's in the world: its Head bound at our joint with A's scale. The world test fails it.)
- **tris**: triangles per mesh, body-only (the largest skinned mesh that is not a head part) and whole, per tier.
- **weights**: per skinned mesh, influences per vertex (max, histogram), the worst |1 - sum|, NaN and negative
  counts. On the body (welded by position): L/R mirror (each vertex against its mirror within `mirror_tol_m`, bone
  names swapped `_l/_r`, `.L/.R`, Left/Right; the per-vertex worst bone difference, p95 and max; `matched_share` says
  how symmetric the mesh is), far weights (> 0.05 on a bone whose head-to-tail segment is over `far_m` away), islands
  (a bone's weight above `island_weight` in more than one connected patch; stray points beyond the biggest), the
  biggest weight step across one edge per bone.
- **bends**: elbow and knee flexion, shoulder abduction and flexion, hip flexion, at 0, 90 and 135 degrees, both
  sides (`bends.py` docstring: how each axis is found from the skeleton). Angles are ABSOLUTE anatomical, from the
  posed bone directions: elbow/knee flexion between the bones (0 = straight), shoulder abduction / flexion and hip
  flexion from the torso's down axis in the frontal / sagittal plane (0 = hanging, 90 = horizontal). The 0 strip is
  the rest pose as built; each strip prints `rest_angle_deg`, and each angle `target_deg` and `achieved_deg` (within
  0.5 deg). Per angle:
  - `girth_mm` / `girth_ratio`: the cross-section's convex-hull perimeter at stations `p<s>` / `d<s>` (s of the
    proximal / distal segment's length from the joint), against rest;
  - `area_ratio`: the cut's enclosed area (oriented, Green's sum) against rest; `null` when the cut is open;
  - `penetration`: posed body points within `near_m` of the joint that lie inside the posed surface (3-ray parity
    against body and head), and their depth (mm: to the nearest posed point that was over 20 mm away at rest). The
    0 row is the open mesh's leak floor; compare against it;
  - `outline_vs_ref`: the side view's outline (the posed mask at 18.8 px/cm) against the reference profile
    `ref/<joint>_<angle>.json` built for this body: per curve, reference-to-outline mean and max, outline-to-reference
    max (mm), and the same in px at the close-up (9.4 px/cm). A reference curve the model hides (a limb folded over
    it in the view) reads as a large deviation: look at the sheet;
  - `outline_mm`: the outline itself, per segment and side, (s, mm out from the bone line);
  - `poser`: the shapes the poser drove and, for the game poser, the game's own bend/flexion readings.
  Sheets: clay at 9.4 px/cm, orange the model's outline, cyan the reference; both sides when under 700 px tall.
- **silhouette** (with --ref): rest-pose front, side, back masks of every mesh at the close-up (9.4 px/cm) and the
  Look (`look_px_per_cm`, 30 by the brief's fallback): XOR pixels and the max outline distance (px, both ways).
- **topology** (any body built on our topology; `topo_check.py`, limits imported from `topo_gates.py`): the build's topology
  gates measured on the glb's rest body mesh, close and `--play`. The quads come from the npz the glb names
  (`extras.body_base.topology`; `--topo` / `--play-topo` override; the glb body mesh is that npz's vertices, same order). Per tier:
  folds over 60 deg (templates and the cleft's midline floor loop apart; the play crotch's thigh-gap edges up to 65 deg counted
  as `fold_over_60_crotch_exception`), quads over aspect 4, edges under 2 mm, non-designed poles (valence != 4, interior,
  not template) within 40 mm of a bend zone, and the elbow / knee crease loop's plane against the rest bisector plane (deg).
  Zones are the body's own vertices in slabs set by the glb's skeleton joints (elbow 40 mm, knee 50 mm, wrist 25, ankle 30,
  shoulder, hip, neck base as in topo_gates.zone_points). Targets 0 (report-only). `topo_b2a`: close 19 folds, 2 aspect, 6 short edges, all at the neck ring.

## Posers (posers.py)

- `game`: her body as the game poses it (tools/anim/skin.py Body, helpers and correctives), on her current skeleton.
  Chosen by default when the body's bones are all in tools/anim/data/heroine_skeleton.json and no --rig is given.
- `lbs`: linear blend skinning from the glb's own skin, shapes driven by the rig.json `"poser"` module
  (`tools.body.rig_drive` by default: the `"correctives"` table). A rig build plugs in its own module with
  `drive(poser, G, rig) -> (G, {shape: weight})`.

rig.json keys: `poser`, `body_mesh`, `close_meshes` (pieces posed with the body to close it: the head), `roles`
(`{"upperarm": "upperarm_{s}", "lowerarm", "hand", "thigh", "calf", "foot"}`; common MakeHuman/Blender names are
tried too), `hinge` (`{"elbow": "front"|"plane"|"local_x"}`), `near_m` per joint, `correctives`.

## Reference profiles (ref/)

Parametric, scaled to the body's own rest half-widths, so away from the joint the reference is the limb held rigid
and only the joint's anatomy is authored (each file's `why` and `grammar`). Not yet authored: the armpit and front
axillary fold at shoulder abduction (the A-pose hides the trunk side), the trunk under the arm.

## Skeleton: joint derivation (skeleton.json, skeleton.py ANAT_RULES)

Most joints are placed by MakeHuman CC0 landmarks fitted onto our vertices (landmarks_fit.py, (c) inherited). Where
that put a joint off its anatomy, the landmark is undone (inherited from MakeHuman) and a rule runs on OUR body (and
her approved head) at placement time:
- **Hip (thigh head, its twists/share/glute, the pelvis's tail): (b) Harrington et al. 2007** (J Biomech 40:595, the
  pelvic width/depth regression) from our skin ASIS (the trunk's front-left support point 35 deg off the front) and
  PSIS (back skin at x 45 mm, its height by a 12 deg standing pelvic tilt: women's neutral ~12 deg, palpation-meter
  studies), skin -> bone 15 mm (ASIS) / 10 mm (PSIS): (a) estimates, no measured source found; sensitivity: the joint's
  depth moves 0.76 mm per mm of ASIS tissue, 0.24 per mm of PSIS. The height is kept (the inherited one; Harrington's
  own vertical term agrees within 5 mm). Was 19 mm too far back.
- **neck_01 (C7/T1): (b) surface anatomy**: the cervicale = the knee of the back midline profile (a degree-6 fit
  from the upper back's furthest-back point to the head ring: the nape's corner), the joint 0.40 of the neck's depth
  forward of it. ANSUR II women's cervicale/stature 0.857 would put it 11 mm higher: her proportions are stylized (8
  heads tall, long legs, the +7% head), so a stature ratio does not transfer; the rule reads her own neck.
- **Head (occipital condyles): (b) surface anatomy** on her head mesh: midline, at the earlobe's lowest point, at the
  ear's mean depth (below and just in front of the mastoid). Was 1867 mm, above the head's top (1849): the head turned
  from the crown. neck_02 halfway (C4); Head's tail = the crown.
- Head weights: unchanged by rule (weights_topo.head: the ring's points copy the body ring, Head 3.5 cm past it,
  harmonic between); the spine/neck chain's weights re-derive from the joints' heights (weights_topo T).
- **Spine depth (spine_02..05's heads, joint-spine-4..1): (b) Grünwald et al. 2024** (BMC Med Imaging, doi
  10.1186/s12880-024-01293-6, Table 1 "mild" group: the vertebral body centre -> spinous tip, the distance the paper
  finds similar across patients of one sex) + 8 mm over the spinous tips ((a) estimate for a lean young woman, 1:1),
  in front of the midline back skin at the joint's (inherited, (c)) height. Level by **(b) Gray's Anatomy's** column
  lengths (thoracic ~28 cm, lumbar ~18 cm) between the pelvis joint (s 0) and C7/T1 (s 1). Was z -65, -46, +23, -31
  (13% / 49% of the depth from the back); now -9, +21, +8, -47: her back's own lordosis/kyphosis, no zigzag. The
  pelvis joint (spine_01's head) and the pec/lat muscle helpers keep the inherited cube (c).
- **Knee (thigh's tail, calf's head and its helpers): (b) Hollister et al. 1993** (Clin Orthop 290:259: the flexion
  axis passes through the posterior femoral condyles' circle centres, near the epicondyles; ISB knee centre = the
  epicondyles' midpoint, Wu et al. 2002). On our skin: the left leg's section (quad edges, either tier) by the plane
  through the inherited joint (its height kept, (c)) normal to hip -> ankle; medial/lateral: the section's middle;
  depth: `back_frac` 0.41 of the knee's depth from the back skin ((a) from typical dimensions: condyle radius ~21 of
  ~60 mm femoral AP, ~26 mm behind / ~30 mm in front of the bone; 0.5 = the section's centre). Was z 0 (16 mm from
  the back skin; and play's inherited knee 13 mm off close's), now 31 mm, both tiers within 1 mm.
- **Shoulder (glenohumeral centre): kept (c)**, checked: her shoulder cap's skin is 67-71 mm from the joint in every
  up-lateral direction (63-66 front/back): the joint sits at the cap's centre, so her shoulder is uniformly thick
  (stylized), and the acromion rule (skin top ~45 mm above the GH centre: humeral head radius ~22-24 mm, Iannotti
  1992; acromiohumeral gap 7-14 mm, Petersson & Redlund-Johnell 1984; acromion ~7 mm, skin ~5) does not hold on her
  skin: raising it 25 mm would put the hinge at the top of the arm's mass.
- **Clavicle's head: (b) the game-rig convention** (A's rig and UE-style rigs: near the spine), not the
  sternoclavicular joint.

## Base topology (topo.py, WIP)

`topo.py` builds OUR base topology from `loopplan.json` (rows, rings and junction patterns placed by our skeleton on
run_a's close surface, which is only the shape reference). `base/hand_l.obj` and `base/foot_l.obj` are **(b) converted
from MakeHuman** (hm08 CC0 base mesh, cut once at a clean 22-point wrist / ankle loop by `topo.py --make-templates`);
they are our source files from here on, mirrored for the right. `python tools/body/topo.py --probe` checks the plan's
count ties and part 1 on the reference. Assembly, relaxation, UVs, landmarks, measures and the sheet are not built yet.

## Bake (topo_bake.py, build_topo stage 7)

Her maps on OUR topology's UVs (`topo_uv.py`; close and play share one texture set), baked from A (the shipped
`godot/art/people/heroine.glb`: its albedo, normal, roughness factors, the graft's freckles) by numpy + embree rays,
no Blender. A stage of the build, not a separate command: the spec's `"bake": {"maps", "size", "pose"}` block turns it
on (`specs/her_topo.json`), so a rebuild that moves her surface, UVs or frames rebakes in the same command
(`python tools/body/build_topo.py tools/body/specs/her_topo.json <out>`, about 95 s of the build). It bakes into
`<out>/maps/` (with `bake.json`), writes `<out>/uv_sheet.png` (the maps over the UV layout), and publishes to the
spec's `maps` (`godot/art/people/body_p1/`) only when its gates pass. Alone: `python tools/body/topo_bake.py <out>
<maps_dir>` on a built `<out>`.

- Source: A posed by the fit's own bones (`forms/her_topo_target_bones.json`, from wrap_topo's target.npz), the surface
  our points were wrapped onto; each texel's point takes A's point along our normal (30 mm, facing faces only), else the
  closest point. Posing A to the built body's skeleton instead missed by up to 4 cm (half the texels fell back).
- Normal: A's shading normal in our tangent frame where A's form is a correction of ours (under 8 deg), A's map detail
  alone on our shape where it is another shape (over 16 deg: the loose arms, the template hands and feet).
- Areolas: A's shipped maps have them painted out (the apex's 15 mm disk matches the ring around it within 0.3 L*,
  the normal map flat there); the bake carries only the shipped maps, so the rule is inherited, never re-derived.
- Gates (`topo_bake.GATES`, in bake.json): albedo dE00 p95 <= 3 away from seams (ours at the point's UV vs A at the
  point), seam step dE00 p95 <= 4 (the two sides of every UV seam), 0 inverted tangent frames.
- The triangulation mirrors: a right quad splits on its left mirror's diagonal (`topo_uv.mirror_diag`), checked in
  build.json `uv.tri_mirror.share` (1.0, asserted).

## B native: the rig and the clip bridge (P1 R2)

Behind `--body p1` B is the actor: `art/people/body_p1/body.glb` is her root (`Armature/Skeleton3D`, A's path, so every
track and filter path holds), its skeleton plays clips baked onto it offline, and B's laws are its only deformation.
A (`heroine.glb`) is not loaded; A without the flag is untouched.

- **B's bones.** Keyed by clips: `root`, `pelvis` (the only position tracks), `spine_01..05`, `neck_01..02`, `Head`,
  the limbs, hands, fingers and face bones by A's names. Law-driven, never keyed: `clavicle_{s}`, `scap_{s}` (the
  girdle law, from the arm) and the helpers in rig.json `helpers` (twists, shares, points, delt/trap/pec/lat/glute,
  breast tips: `P1Rig.Helpers`). B's own metacarpals ride their parent. No scale tracks.
- **The clip format the game plays.** Godot `AnimationLibrary` resources: `body_p1/clips.res` (the library clips,
  `People.Clips()` names, played as `Name`) and `body_p1/her_clips.res` (her own, `heroine_clips.json` names, played as
  `her/Name`; their meta stays heroine_clips.json). Rotation tracks `Armature/Skeleton3D:<bone>` (local, B's rest
  frames), 30 fps, keys from 0 to the length inclusive, loop modes as the sources; blend-shape and method tracks copied.
  A clip keys only the bones its source keys (partial clips stay partial for the game's filtered blends). A new clip
  made directly on B (MotionBricks, Kimodo) just has to follow this: local rotations on the keyed bones, never the
  girdle or helpers, pelvis/root positions in B's rest space; drop it into a library under the same name.
- **The bake.** `bash tools/body/bake_clips.sh` (takes and gives back the godot turn; log in `tools/body/out/
  bake_clips.log`): A plays each clip under HerPose alone (her library carriage baked: Native 0 for library clips, 1
  for hers), each frame goes through `P1Retarget.Map`, the girdle hold (clavicle/scap at B's rest local, the upper arm
  keeps its world turn) and the clean, then is keyed. Deterministic (identical bytes on a rerun); prints frames, keyed
  bones and the idles' shoulder height against B's rest; writes `a_skeleton.json` (A's names, parents, rests).
  `--p1-bake-only TEXT` bakes matching clips without writing. Re-run after any B skeleton change.
- **p1_clips.json** (`tools/body/`): per clip `{"why", "turns": {bone: [x, y, z] deg rotation vector in the bone's own
  frame, laid after the baked local}, "hold": [bones set to B's rest local]}`; applied after the girdle hold.
- **The role map.** Systems keyed to A's names ask `P1Body.Bone(skel, "spine_03")` (identity on A): by name off the
  chain; on the chain the B parent of A's next chain bone (A's chest `spine_03` -> B `spine_05`; B's `spine_03` is
  mid-back); `panel_front` -> its ancestor's. `P1Body.Spread` spreads chain turn shares over B's chain, the total
  kept. Hair and head pieces skinned to A are rebound once (`P1Body.Rebind`, meta `p1_rebound`).
- **B's layer order** (children of her skeleton): HerPose (Baked: only LookArms, CineCurl, neck sliders, chin, head
  tries), Gestures, whatever PlayerView adds (HerCarriage, HerArmHold, HeadTurn, GazeCarry...), **P1Laws** (helpers at
  rest, `P1Rig.Drive` with rig.json, correctives; the play body's by play_rig.json; it re-sorts itself last on every
  added modifier), HerJiggle, HerFaceLife. Not on B: HerShrug, HerRaise, HerScap, HerJoints, HerShoulder.
  `--p1-probe` prints the shoulder/clavicle/scap/trap numbers every 120 frames.
