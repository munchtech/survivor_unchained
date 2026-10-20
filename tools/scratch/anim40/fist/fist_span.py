"""Where her fist (WRAP[w]) lies along a pocket's line: each finger's and the palm's skin t range (mm from the pocket point)."""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "anim"))
import fistfit as F, keyed
w, outfit, clip, fr, pocket = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
F.PIECES["_p"] = dict(arms="x", at=pocket + "AtR", dir=pocket + "DirR", outfit=outfit)
A, D = F._pocket("_p"); D = D / np.linalg.norm(D)
_, rot, pos = F.load(F.CLIPS / f"{clip}.json")
h = F.Hand(rot[fr], pos[fr], outfit)
a, o, r, sp, ti = F.wrap_args(keyed.WRAP[w]); rf = h.rotf(a, o, r, sp, ti)
X = h.pose(rf); t = (X - A) @ D * 1000
for fn in F.ALLF:
    s = h.fing[fn]; print(f"{fn:7s} t {t[s].min():6.1f}..{t[s].max():6.1f}")
print(f"palm    t {t[h.palm].min():6.1f}..{t[h.palm].max():6.1f}")
