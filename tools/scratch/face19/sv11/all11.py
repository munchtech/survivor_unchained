"""all11.py OPTS [SET]: every clip of SET (hair19): the replica at HEAD vs with OPTS, worst change (cm) over the clip."""
from hs11 import *
o = eval(sys.argv[1]); SET = sys.argv[2] if len(sys.argv) > 2 else "hair19"; out = []
for cl, st in CLIPS:
    fr = lg(SET, cl + "_" + st); a, _ = run(fr, st); b, _ = run(fr, st, **o)
    out.append("%s_%s %.2f" % (cl, st, max(np.linalg.norm(p - q, axis=1).max() * 100 for p, q in zip(a, b))))
print(" | ".join(out))
