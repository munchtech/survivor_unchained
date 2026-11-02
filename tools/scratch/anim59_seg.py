import sys, math, numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-59\tools\anim")
import keyed
from keyed import Rig, grip_of, Track
from rig import Skeleton, DATA, qrot
from clips import flare_long_cut as M
sk = Skeleton.load(DATA / "heroine_skeleton.json"); rig = Rig(sk, body="her")
rig.grip = grip_of("sunder", M.TILT)
L = M.LongCut(rig); S_r, S_l, chest = L.body(); HR = L.right(S_r, chest)
a, b = int(sys.argv[1]), int(sys.argv[2])
poses = []
for fr in range(a, b):
    p = L.pose(fr); p["hand_r"] = HR[fr]; poses.append(p)
bases = [(L.base.rot[fr], L.base.pos[fr]) for fr in range(a, b)]
rot, pos = keyed.solve_frames(rig, poses, bases, weapon="sunder")
g, gp = sk.fk(rot, pos); h = rig.I["hand_r"]
for i, fr in enumerate(range(a, b)):
    P, d = M._blade_at(fr)[:2]
    dd = qrot(g[i, h], M.DIR)
    print(fr, round(math.degrees(math.acos(min(1, float(dd @ d)))), 1), "tw", round(rig.twist_last.get("r", 0), 1) if i == b - a - 1 else "")
