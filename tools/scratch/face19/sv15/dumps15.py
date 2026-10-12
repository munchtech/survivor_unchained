import sys; sys.path[:0] = ["../sv14"]
from ev14 import *
for n in ("hc/s11_ponytail_review", "hair19/getup_ponytail", "hair19/getupback_ponytail", "hair19/death_ponytail"):
    fr = lg(*n.split("/")); dts = sorted(set(round(d["dt"], 4) for d in fr))
    print(n, len(fr), "dt", dts[:5], "ground", round(fr[0]["ground"], 3))
