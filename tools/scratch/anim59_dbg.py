import sys, math, numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-59\tools\anim")
from rig import Skeleton, DATA, qrot
from folkhold import load_clip
import build as B
from clips import flare_long_cut as M
sk = Skeleton.load(DATA / "heroine_skeleton.json")
rot, pos = load_clip(B.OUT / "flare_long_cut.json", sk)
g, p = sk.fk(rot, pos)
hr = sk.i("hand_r"); la = sk.i("lowerarm_r")
for f in [int(x) for x in sys.argv[1].split(",")]:
    _, dk, _ = M._blade_at(f)
    z = qrot(g[f, hr], np.array([0, 0, 1.0])); y = qrot(g[f, hr], np.array([0, 1.0, 0]))
    fa = p[f, hr] - p[f, la]; fa /= np.linalg.norm(fa)
    ang = lambda a, b: math.degrees(math.acos(max(-1, min(1, float(a @ b)))))
    print(f, "dk", np.round(dk, 2), "handZ", np.round(z, 2), "handY", np.round(y, 2), "fore", np.round(fa, 2),
          "Z-dk", round(ang(z, dk)), "Z-fore", round(ang(z, fa)), "Y-fore", round(ang(y, fa)))
