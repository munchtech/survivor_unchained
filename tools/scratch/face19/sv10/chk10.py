"""chk10.py: hs10 with no options against the C# dumps (should match as M8 did)."""
from hs10 import *
for SET, CL in (("hair17d", "throw_braid"), ("hair17d", "throw_ponytail"), ("hair16", "death_braid"), ("hair16", "getup_ponytail"), ("hair16", "getupback_long")):
    fr = lg(SET, CL); xs, _ = sim10(fr, CL.split("_")[1]); cs = today(fr)
    print(SET, CL, "worst %.3f cm" % max(np.linalg.norm(p - q, axis=1).max() * 100 for p, q in list(zip(xs, cs))[:-1]))
