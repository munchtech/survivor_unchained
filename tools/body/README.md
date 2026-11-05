# tools/body: the body's check

`check.py` is the CHECK command for her body (docs/team/PIPELINE.md P1): numbers first, a judge only on what they
cannot say. Pure Python (numpy, scipy, embreex, Pillow); no Blender or Godot.

    python tools/body/check.py <body.glb> [--ref A.glb] [--rig rig.json] [--play play.glb] [--far far.glb]
                               [--poser game|lbs] [--same-head] [--only contract,tris,weights,bends,silhouette] --out DIR

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

## Base topology (topo.py, WIP)

`topo.py` builds OUR base topology from `loopplan.json` (rows, rings and junction patterns placed by our skeleton on
run_a's close surface, which is only the shape reference). `base/hand_l.obj` and `base/foot_l.obj` are **(b) converted
from MakeHuman** (hm08 CC0 base mesh, cut once at a clean 22-point wrist / ankle loop by `topo.py --make-templates`);
they are our source files from here on, mirrored for the right. `python tools/body/topo.py --probe` checks the plan's
count ties and part 1 on the reference. Assembly, relaxation, UVs, landmarks, measures and the sheet are not built yet.
