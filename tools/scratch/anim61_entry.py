"""anim61: the right hand's blade way d and knuckles kn (as flare_long_cut keys them) per frame of the written clip."""
import sys, math
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-61\tools\anim")
import numpy as np
from rig import Skeleton, DATA, qrot, qaxis, qmul, qinv
import build as B, audit
from clips import flare_long_cut as M
sk = Skeleton.load(DATA / "heroine_skeleton.json")
d, rot, pos = audit.load(B.OUT / "flare_long_cut.json", sk, stage=True)
g, p = sk.fk(rot, pos)
hr = sk.index["hand_r"]; la = sk.index["lowerarm_r"]
lq = qaxis([1.0, 0, 0], -M.GRIP_LEAN)
for f in [int(x) for x in sys.argv[1].split(",")]:
    Rk = qmul(g[f, hr], lq)
    dd, kn = qrot(Rk, np.array([0, 0, 1.0])), qrot(Rk, np.array([0, 1.0, 0]))
    print(f, np.round(dd, 3), np.round(kn, 3), "fore", np.round(qrot(qmul(g[f, la], qinv(sk.rest_rot[la]) if False else g[f, la]), np.array([0, 1.0, 0])), 3))
