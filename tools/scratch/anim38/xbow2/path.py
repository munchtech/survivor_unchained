"""Left arm joints per frame (char space, cm) of a built clip in out/anim38_<body>: python path.py clip [a:b] [--hero]"""
import sys; from pathlib import Path
W = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(W / "tools/anim"))
import numpy as np
from rig import DATA, Skeleton
from skin import Body
hero = "--hero" in sys.argv
a = [x for x in sys.argv[1:] if not x.startswith("--")]
sk = Skeleton.load(DATA / ("hero_skeleton.json" if hero else "heroine_skeleton.json")); I = sk.index
b = Body.hero() if hero else Body.heroine(jiggle=False)
c = b.clip(a[0], W / "tools/anim/out" / ("anim38_hero" if hero else "anim38_her"))
g, p = sk.fk(c.rot, c.pos)
r = range(*map(int, a[1].split(":"))) if len(a) > 1 else range(len(p))
for f in r:
    s = lambda j: " ".join(f"{100*v:5.1f}" for v in p[f, I[j]])
    print(f"f{f:3d} sh {s('upperarm_l')} | el {s('lowerarm_l')} | hd {s('hand_l')} | chest {s('spine_03')} | knee {s('calf_l')} | thigh {s('thigh_l')}")
