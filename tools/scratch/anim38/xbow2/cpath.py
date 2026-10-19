"""Both arms' joints in the chest's frame (spine_03, rest-aligned; cm: x her left, y up, z ahead?) per frame:
python cpath.py clip a:b [--hero] [--tag=]"""
import sys; from pathlib import Path
W = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(W / "tools/anim"))
import numpy as np
from rig import DATA, Skeleton, qrot, qinv, qmul
from skin import Body
hero = "--hero" in sys.argv
a = [x for x in sys.argv[1:] if not x.startswith("--")]
sk = Skeleton.load(DATA / ("hero_skeleton.json" if hero else "heroine_skeleton.json")); I = sk.index
b = Body.hero() if hero else Body.heroine(jiggle=False)
c = b.clip(a[0], W / "tools/anim/out" / (("anim38_hero" if hero else "anim38_her") + next((x[6:] for x in sys.argv if x.startswith("--tag=")), "")))
g, p = sk.fk(c.rot, c.pos)
rg, rp = sk.rest_globals()
s3 = I["spine_03"]
r = range(*map(int, a[1].split(":"))) if len(a) > 1 else range(len(p))
for f in r:
    ch = qmul(g[f, s3], qinv(rg[0, s3] if rg.ndim == 3 else rg[s3]))
    s = lambda j: " ".join(f"{100*v:5.1f}" for v in qrot(qinv(ch), p[f, I[j]] - p[f, s3]))
    def flare(sd):
        u = qrot(qinv(ch), p[f, I[f"lowerarm_{sd}"]] - p[f, I[f"upperarm_{sd}"]])
        return np.degrees(np.arctan2(u[0] * (1 if sd == "l" else -1), np.hypot(u[1], u[2])))
    print(f"f{f:3d} flare L {flare('l'):4.0f} R {flare('r'):4.0f}", end="  ")
    print(f"shL {s('upperarm_l')} elL {s('lowerarm_l')} hdL {s('hand_l')} | shR {s('upperarm_r')} elR {s('lowerarm_r')} hdR {s('hand_r')}")
