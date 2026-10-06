"""Her shield's facing (the left forearm's -X) per frame of a built clip, and
in rest terms of the left hand: python shield.py clip [her|hero] [step]"""
import sys
from pathlib import Path
W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np
import audit
from rig import DATA, Skeleton, qinv, qmul, qrot
name = sys.argv[1]
body = sys.argv[2] if len(sys.argv) > 2 else "her"
step = int(sys.argv[3]) if len(sys.argv) > 3 else 4
sk = Skeleton.load(DATA / ("hero_skeleton.json" if body == "hero" else "heroine_skeleton.json"))
g0, _ = sk.rest_globals()
I = sk.index
la, ha = I["lowerarm_l"], I["hand_l"]
# The shield's face in the hand's own frame at rest.
face_in_hand = qrot(qinv(g0[0, ha]), qrot(g0[0, la], [-1.0, 0, 0]))
print("shield face in the left hand's frame at rest:", np.round(face_in_hand, 2))
d, rot, pos = audit.load(W / "out" / ("hero" if body == "hero" else "clips") / f"{name}.json", sk)
g, p = sk.fk(rot, pos)
n = rot.shape[0]
for f in list(range(0, n, step)) + [n - 1]:
    face = qrot(g[f, la], [-1.0, 0, 0])
    c = p[f, la] + qrot(g[f, la], [0, 0.14, 0])
    print(f"f{f:3d} shield face ({face[0]:+.2f},{face[1]:+.2f},{face[2]:+.2f})  centre y {c[1]:.2f}  (lowest rim {c[1] - 0.30 * np.sqrt(max(0, 1 - face[1] ** 2)):+.2f})")
