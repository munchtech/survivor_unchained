import sys, math, numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-59\tools\anim")
from keyed import Rig, grip_of
from rig import Skeleton, DATA, qrot
from clips import flare_long_cut as M
sk = Skeleton.load(DATA / "heroine_skeleton.json"); rig = Rig(sk, body="her")
rig.grip = grip_of("sunder", M.TILT)
L = M.LongCut(rig); S_r, S_l, chest = L.body(); HR = L.right(S_r, chest)
for fr in [int(x) for x in sys.argv[1].split(",")]:
    p = L.pose(fr); p["hand_r"] = HR[fr]
    rig.swivel = {}
    local, pos = rig.solve(p, base=(L.base.rot[fr], L.base.pos[fr]))
    g, gp = sk.fk(local[None], pos[None]); h = rig.I["hand_r"]
    P, d = M._blade_at(fr)[:2]
    dd = qrot(g[0, h], M.DIR); Pp = gp[0, h] + qrot(g[0, h], M.AT)
    print(fr, "spec", {k: np.round(v, 2) if isinstance(v, tuple) else v for k, v in HR[fr].items()})
    print("   err", round(math.degrees(math.acos(min(1, float(dd @ d)))), 1), "pos mm", round(1000 * float(np.linalg.norm(Pp - P)), 1))
print("fresh twists")
for fr in range(0, 5):
    p = L.pose(fr); p["hand_r"] = HR[fr]
    rig.swivel = {}; rig.twist_last = {}; rig.swing_last = {}
    local, pos = rig.solve(p, base=(L.base.rot[fr], L.base.pos[fr]))
    g, gp = sk.fk(local[None], pos[None]); h = rig.I["hand_r"]
    print(fr, "tw", round(rig.twist_last["r"], 1), "spec k", np.round(HR[fr].get("knuckles", (0, 0, 0)), 2), "blade", np.round(HR[fr]["blade"], 2))
