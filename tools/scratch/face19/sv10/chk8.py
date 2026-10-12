"""chk8.py: the original M8 replica against the C# dumps."""
import sys; sys.path[:0] = ["../sv9", "../sv8", "../sv6", "../sv5", "../sv4", "../sv3"]
from g9 import *
for SET, CL in (("hair16", "death_braid"), ("hair16", "getup_ponytail"), ("hair16", "getupback_long"), ("hair18", "death_braid"), ("hair18", "getup_ponytail"), ("hair18", "run_braid"), ("hair16", "run_braid")):
    fr = lg(SET, CL); st = CL.split("_")[1]; xs, _ = sim8(fr, st, **per4(H7, st)); cs = today(fr)
    print(SET, CL, "worst %.3f cm" % max(np.linalg.norm(p - q, axis=1).max() * 100 for p, q in list(zip(xs, cs))[:-1]))
