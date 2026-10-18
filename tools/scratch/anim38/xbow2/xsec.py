"""The crossbow in hand_r's local frame: extents and cross-sections along the stock (+Y), and the idle's left-hand
relation (rel_p, its palm axes). python xsec.py"""
import sys; from pathlib import Path
W = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(W / "tools/anim"))
import numpy as np
import armscheck as A
from rig import qrot
ck = A.Checker()
Q = ck.pts["crossbow@hand_r"]
print("pts", Q.shape, "min", Q.min(0).round(3), "max", Q.max(0).round(3))
for y0 in np.arange(-0.10, 0.45, 0.03):
    s = Q[(Q[:, 1] > y0) & (Q[:, 1] < y0 + 0.03)]
    if len(s):
        print(f"y {y0:+.2f}: n {len(s):5d} x {s[:,0].min():+.3f}..{s[:,0].max():+.3f}  z {s[:,2].min():+.3f}..{s[:,2].max():+.3f}")
from keyed import Rig
from rig import DATA, Skeleton
import clips.idle as I
for hero in (False, True):
    sk = Skeleton.load(DATA / ("hero_skeleton.json" if hero else "heroine_skeleton.json"))
    rig = Rig(sk, body="him" if hero else "her")
    rp, rq = I._stock_rel(rig)
    print("hero" if hero else "her", "rel_p", np.round(rp, 3), "x", np.round(qrot(rq, [1, 0, 0]), 2), "y", np.round(qrot(rq, [0, 1, 0]), 2), "z", np.round(qrot(rq, [0, 0, 1]), 2))
