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
