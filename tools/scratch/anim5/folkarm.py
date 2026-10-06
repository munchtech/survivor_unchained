"""A folk clip's arm per frame: python folkarm.py m_die_front_armed l f0 f1"""
import math
import sys
from pathlib import Path
W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np
import audit
from rig import DATA, Skeleton, qrot
name, side, f0, f1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sk = Skeleton.load(DATA / ("folk_male_skeleton.json" if name.startswith("m_") else "folk_female_skeleton.json"))
d, rot, pos = audit.load(W / "out" / "folk" / f"{name}.json", sk)
g, p = sk.fk(rot, pos)
I = sk.index
for f in range(f0, f1):
    fa = g[f, I[f"lowerarm_{side}"]]
    h = g[f, I[f"hand_{side}"]]
    S, E, Wr = p[f, I[f"upperarm_{side}"]], p[f, I[f"lowerarm_{side}"]], p[f, I[f"hand_{side}"]]
    u, v = E - S, Wr - E
    bend = math.degrees(math.acos(max(-1, min(1, float(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v))))))
    sh = qrot(fa, [-1.0, 0, 0])
    print(f"f{f} bend {bend:3.0f} shield face ({sh[0]:+.2f},{sh[1]:+.2f},{sh[2]:+.2f}) knuckles {np.round(qrot(h, [0, 1.0, 0]), 2)} blade {np.round(qrot(h, [0, 0, 1.0]), 2)}")
