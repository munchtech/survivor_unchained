# Body 1 stage 2c: the arm graft to the wrist, one chain from the original blend (armor 18 g2c, 22 Oct 2026)

    bash tools/assets/arm_graft/g2c/run.sh <work dir> <g1d.npz> <VG_v1.npy> <people dir> [tag]

Takes the blender turn yourself around it (it runs Blender 3-4 times and the body+warden export, ~10 min; the graft's python
steps take ~20 min, so run them first with ARM_GRAFT_WORK set and then `SKIP_GRAFT=1`). Chain:
1. graft (`heroine_arm_graft.py`, env ARM_TO=wrist WRIST_TF=0.98 WRIST_HW=0.6 TRAP=0.5 TRAP_CL=0.3 FA_CUT=0.5): the base's
   whole arm, mid-clavicle and pit to the wrist; the base forearm turned about its elbow onto hers (46 deg) and rigid-ICP'd;
   loop cuts where the base's forearm loops are > 0.5 cm apart (0.75-0.8 cm -> ~0.4); the ring traced on welded ids.
2. b_write onto heroine_built.blend -> <work>/graft.blend; b_dump -> gd.npz.
3. `post.py`: G2b's weights carried from G1's geometry (g1d.npz = dump of heroine_built_armroot_g1.blend, with VG_v1.npy) by
   surface interpolation; the arm_shape field + pit fairing (30 it) re-run on the new mesh (g2a edit.py).
4. g2b/w_write.py -> heroine_built_armroot.blend; export (NAPE=0, --only warden); neck graft npz restored.
`extra.py <people dir>`: forearm outline chords, inner-elbow collapse by faces and by area, edge-length bands across the elbow
and wrist. g2a/meas.py now also prints the top outline cut where it crosses onto the arm's front (phi > 65 past t 0.1).
TRAP=0.3 TRAP_CL=0.15 (strip moved medially off the trap) gave shoulder_top chords 3.6/4.2 px but left the t -0.37 junction
as it was and moves 215 more neck-graft field points (|x| 0.094-0.128), so it is not the default.

## g2d additions (armor 18 g2d, 22 Oct 2026), all defaults in run.sh
- `WRIST_TC=0.85` (fit.py `wrist_coarsen`): the patch's wrist end halved round the arm (along-arm rows kept) from the base
  quad ring nearest tf 0.85 to the wrist, the ring before it a 4:2 all-quad transition (6 quads per base quad); quads past
  tf 1.08 dropped; the loop cuts seed only in the fine quads. Base forearm rings are 20 quads (80 -> 40 round the arm).
- `WRIST_CORNER=1` (build.py): the wrist loop's staircase (her wrist ring runs 4-6 cm along the arm) cut on the diagonal,
  one triangle per convex corner. Wrist loop 106/126 -> 58/73 against her 39/46.
- `GAP=0.008 UNT=30`: the wider gap and the seam untangle clear the folds the coarse rows made at the top of the left wrist.
- `ELBOW_IT` (post.py, default 0: 20 made the inner elbow worse, 15/13%): x = W_low/(W_up+W_low) Laplacian-smoothed on the elbow's front (t .7-1.3), sum kept.
- `TOP_IT=80 TOP_PHI1=60` (post.py, `TOP_T`): Taubin fairing of the shoulder top/back (t -.6..0, phi -130..40) on
  graft-moved vertices only, so no neck-graft npz point on the original blend moves.
