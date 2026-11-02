"""Build flare_long_cut (no pack), write it, and print per-frame geometry."""
import sys, time, math, pickle
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-59\tools\anim")
import numpy as np
from keyed import Rig
from rig import Skeleton, DATA, qrot, write_clip
import build as B
from clips import flare_long_cut as M
sk = Skeleton.load(DATA / "heroine_skeleton.json"); rig = Rig(sk, body="her")
t0 = time.time()
clip = M.flare_long_cut(rig)
print("built", round(time.time() - t0, 1), "s")
write_clip(clip, sk, B.OUT)
g, p = sk.fk(clip.rot, clip.pos)
I = rig.I
hr, hl = I["hand_r"], I["hand_l"]
fr_list = sys.argv[1:] and [int(x) for x in sys.argv[1].split(",")] or range(clip.frames)
print("fr  P(x y z)              dErr  tip(x y z)            Lline Lang  kneeR(y z)   ballL(y)  ballR(y)  pel_y")
for f in fr_list:
    P = p[f, hr] + qrot(g[f, hr], M.AT); d = qrot(g[f, hr], M.DIR)
    Pk, dk = M._blade_at(f)[:2]
    tip = P + d * M.BLADE_LEN
    Q = p[f, hl] + qrot(g[f, hl], M.AT_L); dl = qrot(g[f, hl], M.DIR_L)
    v = Q - P; off = v - d * float(v @ d)
    ang = math.degrees(math.acos(max(-1, min(1, float(dl @ d)))))
    kn = p[f, I["calf_r"]]
    print(f"{f:2d} {P[0]:6.3f} {P[1]:5.3f} {P[2]:6.3f}  {math.degrees(math.acos(max(-1,min(1,float(d@dk))))):5.1f}  "
          f"{tip[0]:6.3f} {tip[1]:6.3f} {tip[2]:6.3f}  {np.linalg.norm(off)*1000:5.1f} {ang:5.1f}  "
          f"{kn[1]:5.3f} {kn[2]:6.3f}  {p[f, I['ball_l']][1]:6.3f} {p[f, I['ball_r']][1]:6.3f}  {p[f, I['pelvis']][1]:5.3f}")
