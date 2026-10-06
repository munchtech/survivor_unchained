import math
import sys
from pathlib import Path
W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np
from rig import DATA, Skeleton, qrot
for skel in ("heroine_skeleton.json", "hero_skeleton.json", "folk_female_skeleton.json"):
    sk = Skeleton.load(DATA / skel)
    g, p = sk.rest_globals()
    I = sk.index
    for s in "lr":
        la, h, mid, th, ix, pk = (I[f"lowerarm_{s}"], I[f"hand_{s}"], I[f"middle_01_{s}"], I[f"thumb_01_{s}"], I[f"index_01_{s}"], I[f"pinky_01_{s}"])
        fa = p[0, h] - p[0, la]; fa /= np.linalg.norm(fa)
        fing = p[0, mid] - p[0, h]; fing /= np.linalg.norm(fing)
        hy = qrot(g[0, h], [0, 1.0, 0]); hz = qrot(g[0, h], [0, 0, 1.0]); hx = qrot(g[0, h], [1.0, 0, 0])
        fy = qrot(g[0, la], [0, 1.0, 0])
        thumbdir = p[0, ix] - p[0, pk]; thumbdir /= np.linalg.norm(thumbdir)
        ang = lambda a, b: math.degrees(math.acos(max(-1, min(1, float(np.dot(a, b))))))
        print(skel[:6], s, "forearm->fingers", round(ang(fa, fing)), "handY vs fingers", round(ang(hy, fing)),
              "handZ vs pinky->index", round(ang(hz, thumbdir)), "forearmY vs forearm", round(ang(fy, fa)),
              "handY", np.round(hy, 2), "handZ", np.round(hz, 2), "fa", np.round(fa, 2))
