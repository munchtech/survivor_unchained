"""all14.py OPTS: every hair19 clip and style, the replica at HEAD vs with OPTS (the C# gates: braid only): worst change (cm)."""
from hs14 import *
o = eval(sys.argv[1]); out = []
for cl, st in CLIPS:
    fr = lg("hair19", cl + "_" + st); a, _ = run12(fr, st); b, _ = run12(fr, st, **(o if st in sys.argv[2].split(",") else {}))
    out.append("%s_%s %.2f" % (cl, st, max(np.linalg.norm(p - q, axis=1).max() * 100 for p, q in zip(a, b))))
print(" | ".join(out))
