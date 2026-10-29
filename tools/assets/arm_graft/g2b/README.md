# Body 1 stage 2b (arm root shape + weights written into the blend): armor 18 g2b, 22 Oct 2026

What is in `heroine_built_armroot.blend` now (written from G1's `heroine_built_armroot_g1.blend`, which stays as the pre-g2b copy):
- **Shape:** `heroine_arm_shape.py`'s field baked in (edit.arm_shape_field), plus Taubin fairing of both pits (edit.pit_mask,
  30 iterations). body_post step 6 (`heroine_arm_shape`) is RETIRED in `heroine_body_post.py` (runs only with `--arm-shape`,
  for a build from the pre-graft blend), so it isn't applied twice. Moved points' corners (and their 1-ring) take the
  skin's own normal; the rest keep their custom normals (w_write.py).
- **Weights:** G2a's optimised pit/shoulder weights (opt.py, VG_opt_a) kept near the root, ramped back to the blend's own
  weights over t 0.1..0.3 of the upper arm (t7.tmix; the optimiser had cost the t .5 section .87 -> .83); a cap hand-off
  (t7.capw: more upperarm, less clavicle over the top of the shoulder, t -0.9..-0.2 ramp, gated to the upper side,
  Laplacian-smoothed; a=0.3 right, 0.2 left). Written = P_v1.npy + VG_v1.npy (scratch g2).
- Tried and NOT kept: t9.elb (inner-elbow upperarm/lowerarm split smoothed, it=10): proxy 14/9% -> 6/3%, the real export
  15/12% (worse). The build re-derives the elbow, so the proxy can't be trusted there.

Run (scratch paths; set them for reuse): `t8.py`/`t9.py` measure variants on the proxy (G2a's proxy.py, ~4 s each);
`wexp.sh <P.npy> <VG.npy> <tag>` writes the blend (w_write.py), exports body + warden (NAPE=0, ~6 min, takes the blender
turn) and restores tools/assets/heroine_neck_graft.npz; `../g2a/run_base.py <export dir> <tag>` measures the real export;
`pose_dump2.py <export dir> out.npz` + `blender -b --python b_render.py -- out.npz out.png P|Pl|P0` renders half size.

Learned: the proxy over-reports flask_drink's pit (proxy 88/79, real export 43/63). Moving the clavicle hand-off medially
makes the cap ride with the arm (the t -0.2..+0.1 collapse turns convex in the proxy) but sharpens the trap/cap junction at
t ~ -0.37, where the outline switches from the back surface (phi -50..-100) to the front-top (phi +35..+60): a silhouette
crossing, not a crease in one surface. Wider ramps don't move it. The dip near t 0.2 (-20..-35 deg/cm) is in G1 too and
doesn't answer a bind-pose swell or DELT=0; near the window's end the outline crosses to the arm's side (phi ~87).
