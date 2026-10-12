"""carry15.py OPTS [STYLE]: get_up review dump: frames loaded, per frame k36.. the carried flags, capsules on, drape weight,
upright (her neck axis' y), head height; when the carry ends; HEAD vs OPTS."""
import sys, time; sys.path[:0] = ["../sv14"]
from ev14 import *
o = eval(sys.argv[1]); st = sys.argv[2] if len(sys.argv) > 2 else "ponytail"
for name, oo in (("HEAD", {}), ("OPTS", o)):
    t0 = time.time(); fr, xs, m = run14(st, oo)
    end = max((k for k in range(len(m.rlog)) if m.rlog[k].any()), default=-2) + 1
    print("%s %s: %d frames, carry ends k%d (%.1fs)" % (st, name, len(fr), end, time.time() - t0))
    for k in range(36, len(fr)):
        d = fr[k]; at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10])
        print("  k%d %s c%d w%.2f up%.3f hh%.2f dt%.4f" % (k, "".join("1" if q else "." for q in m.rlog[k]), m.caplog[k], m.wlog[k], up[1], d["head"][0][1] - d["ground"], d["dt"]))
