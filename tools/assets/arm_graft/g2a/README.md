# Body 1 stage 2a (arm root shape and weights): WIP harness, armor 18 g2a, 22 Oct 2026

Unfinished. A measuring harness and two experiments, kept for the next solver. Nothing here has been written into a blend.

- `meas.py`: the stage's acceptance numbers for BOTH arms (the left by mirrored poses: `mirrorG` mirrors bone globals so a
  right-arm clip poses the left arm): pit crease at rest, pit edges past 30 deg at A82, flask_drink and catch_breath pit
  crease, inner-elbow faces losing over half their area, upper-arm sections at idle/A58/A82, outline chords and corners
  at the town close-up, and `outline_top` (the shoulder's upper outline rastered at 4x, its turn per cm, + convex).
  `common.py` is D1's loader and regions. `run_base.py <people dir> <tag>` measures an export.
- `proxy.py`: G1's export in memory with dump-space edits mapped on (positions; weights as a delta through
  helpers.split). A full rebuild from the dump (`g2lib.dbody`) is NOT faithful in the pit (the build eases breast
  weights and mends folds after the blend), so use the mapping proxy and confirm on a real export.
- `edit.py`: heroine_arm_shape.py's field on the dump (to bake it into the blend), Taubin fairing of the pit
  (`pit_mask`), a deltoid cap field. `t4.py` runs shape variants.
- `opt.py`: skin-weight optimisation at the arm root (per vertex: spine_03 share and the clavicle->upperarm blend),
  ARAP strain over a pose set, Levenberg-Marquardt with a numeric Jacobian through helpers.split. `t6.py` runs it.

Paths: written for the armor18 scratch (`g1d.npz` = b_dump of heroine_built_armroot.blend; `..\g1\exp_graft` = G1's raw
export). Set them before reuse.
