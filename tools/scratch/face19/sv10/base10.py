"""base10.py [SET]: hs10 with no options against the original loop (orig=1) on all 18 clips (worst cm)."""
from hs10 import *
SET = sys.argv[1] if len(sys.argv) > 1 else "hair18"
for cl, st in CLIPS:
    fr = lg(SET, cl + "_" + st); a, _ = sim10(fr, st, orig=1); b, _ = sim10(fr, st)
    print(cl, st, "%.4f" % max(np.linalg.norm(p - q, axis=1).max() * 100 for p, q in zip(a, b)))
