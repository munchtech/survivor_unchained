"""e2.py: which change takes the throw braid's fold away? Variants of the frames (spine balls as spheres, no 1.04 scale on
the balls) run through M8; joint angles at points 1-3 per cell."""
import copy
from g9 import *
fr0 = lg("hair17d", "throw_braid"); st = "braid"
def run(fr, **o):
    xs, m = sim8(fr, st, **per4(dict(H7, **o), st)); return xs
def show(name, xs, fr):
    a = np.array([angles(x) for x in xs])
    print("%-22s p1 %s" % (name, " ".join("%3.0f" % v for v in a[::2, 0])))
    print("%-22s p2 %s" % ("", " ".join("%3.0f" % v for v in a[::2, 1])))
    print("%-22s p3 %s" % ("", " ".join("%3.0f" % v for v in a[::2, 2])))
show("C# model", run(fr0), fr0)
sph = copy.deepcopy(fr0)
for d in sph: d["across"][3:11] = 0
show("spine spheres", run(sph), sph)
for W in (0.03, 0.045):
    f2 = copy.deepcopy(fr0)
    for d in f2: d["across"][3:11] *= W / 0.06
    show("W=%.3f" % W, run(f2), f2)
nb = copy.deepcopy(fr0)
for d in nb: d["r"][11:] = 0
show("no arm balls", run(nb), nb)
