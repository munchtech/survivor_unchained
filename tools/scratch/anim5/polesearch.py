"""Which elbow pole lays her shield flat in the fall's last pose."""
import itertools
import sys
from pathlib import Path
W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np
from keyed import Rig
from rig import DATA, Skeleton, qrot
from clips import actions
body = sys.argv[1] if len(sys.argv) > 1 else "her"
sk = Skeleton.load(DATA / ("hero_skeleton.json" if body == "hero" else "heroine_skeleton.json"))
rig = Rig(sk, body="him" if body == "hero" else "her")
I = sk.index
res = []
for px, py, pz in itertools.product((1.0, 0.5, 0.0), (-1.0, -0.3, 0.3, 1.0), (-1.0, -0.3, 0.3, 1.0)):
    pose = actions._down_pose()
    pose["hand_l"] = dict(pose["hand_l"], pole=(px, py, pz))
    rig.swivel = {}
    local, pos = rig.solve(pose)
    g, p = sk.fk(local[None], pos[None])
    face = qrot(g[0, I["lowerarm_l"]], [-1.0, 0, 0])
    elbow = p[0, I["lowerarm_l"]]
    res.append((face[1], (px, py, pz), round(float(elbow[1]), 2)))
for r in sorted(res, reverse=True)[:6]:
    print(f"face up {r[0]:+.2f} pole {r[1]} elbow y {r[2]}")
