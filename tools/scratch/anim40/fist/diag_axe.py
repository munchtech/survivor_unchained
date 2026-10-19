"""anim-40: where along the haft each finger sits after a modelled fit, and the section there (R toward -u)."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model_axe as MA
import fistfit as F
gc = MA.gc
glb = sys.argv[1]
old = gc.load("viking_axe"); pc = gc.load("viking_axe", path=Path(glb))
O, d, _, _ = MA.haft_frame(old)
Vn = MA.new_hand(pc, O, d, old.k)
P = F.PIECES["axe"]; P.update(at="BladeAtR", dir="BladeDirR"); P.pop("dump", None); P.pop("axis", None)
F._arms_v = lambda piece, _V=Vn: _V if piece == "axe" else None
wrap, A, prof = F.fit("axe")
A0, D = F.read_seat("axe"); D = D / np.linalg.norm(D)
gr = F.Grip(A, D, prof)
_, rot, pos = F.load(F.CLIPS / f"{P['rest'][0]}.json")
h = F.Hand(rot[P["rest"][1]], pos[P["rest"][1]], P["outfit"])
a, o, r, sp, ti = F.wrap_args(wrap); rf = h.rotf(a, o, r, sp, ti)
J = h.joints(rf); u = F.palm_dir(h, rf, gr); X = h.pose(rf)
for fn in F.FINGERS:
    sub = h.fing[fn]; B = h.bone[sub]
    e = F.end_point(X[sub][B == f"{fn}_03_r"], J, fn); v = e - gr.A
    ts = [float((J[f"{fn}_0{q}_r"] - gr.A) @ D * 1000) for q in (1, 2, 3)]
    te = float(v @ D * 1000)
    print(fn, "t joints", np.round(ts, 1), "tip t", round(te, 1), "R(-u) at tip", round(float(gr.R(v @ D, -u)) * 1000, 2),
          "tip depth", round(float(-(v @ u)) * 1000, 2))
for t in range(-50, 60, 10):
    print(t, "R(-u)", round(float(gr.R(t / 1000, -u)) * 1000, 2), "R(u)", round(float(gr.R(t / 1000, u)) * 1000, 2))
