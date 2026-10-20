import sys, math, numpy as np
from pathlib import Path
W = Path(r"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40")
sys.path.insert(0, str(W / "tools/anim"))
from keyed import Rig
from rig import Skeleton, DATA, qfrom_matrix, qrot
from clips import idle
sk = Skeleton.load(DATA / "heroine_skeleton.json"); rig = Rig(sk)
base = idle.base_of(rig, "arcanist_town")
idle.staff_walk(rig, base)
rows, arm, hand = idle.staff_walk.seen
ha = rig.I["hand_r"]
for f in (0, 60):
    G, d = rows[f]; d_la, fa = arm[f]
    print("frame", f, "G", np.round(G, 3), "d", np.round(d, 2), "fa", np.round(fa, 2))
    for psi in range(-180, 180, 20):
        R, Wr = hand(G, d, math.radians(psi))
        tw, sw, _, _, phi, dev = rig._strain(d_la, qfrom_matrix(R), ha, fa, "r")
        print(f"  psi {psi:4d} tw {tw:6.0f} sw {sw:5.0f} phi {phi:5.0f} dev {dev:5.0f} over {rig._wrist_over(phi, dev):.2f} thumb {np.round(R[:, 2], 2)} fing {np.round(R[:, 1], 2)}")
