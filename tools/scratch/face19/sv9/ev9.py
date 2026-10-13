"""ev9.py OPTS [SET] [clips]: per clip, M9(OPTS) against the C# model (M8): worst change (cm, cell), first cell >1 cm, and the
worst 3D joint angle over the clip before -> after (deg)."""
from hs9 import *
STEP = dict(death=3, getup=4, getupback=4, throw=2, run=2, stop=2)
CLIPS = [(c, s) for c in ("run", "stop", "throw", "death", "getup", "getupback") for s in ("ponytail", "braid", "long")]
o = eval(sys.argv[1]); SET = sys.argv[2] if len(sys.argv) > 2 else "hair16"
clips = CLIPS if len(sys.argv) < 4 else [tuple(c.split("_")) for c in sys.argv[3].split(",")]
for cl, st in clips:
    fr = lg(SET, cl + "_" + st)
    a, _ = sim8(fr, st, **per4(H7, st)); b, _ = sim9(fr, st, **per4(dict(H7, **o), st))
    dif = [np.linalg.norm(p - q, axis=1).max() * 100 for p, q in zip(a, b)]
    j = int(np.argmax(dif)); first = next((k for k, v in enumerate(dif) if v > 1), -1)
    A0 = max(angles(x).max() for x in a); A1 = max(angles(x).max() for x in b)
    print("%-9s %-8s chg %5.1f (c%.1f, >1cm from %s) maxang %3.0f -> %3.0f" % (cl, st, dif[j], j / STEP[cl], "c%.1f" % (first / STEP[cl]) if first >= 0 else "-", A0, A1))
