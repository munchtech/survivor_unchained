"""ev10.py OPTS [SET]: per clip, hs10(OPTS) against the C# at HEAD (orig): worst change (cm, cell) and worst 3D joint angle before -> after."""
from hs10 import *
o = eval(sys.argv[1]); SET = sys.argv[2] if len(sys.argv) > 2 else "hair18"; out = []
for cl, st in CLIPS:
    fr = lg(SET, cl + "_" + st); a, _ = sim10(fr, st, orig=1); b, _ = sim10(fr, st, **o)
    dif = [np.linalg.norm(p - q, axis=1).max() * 100 for p, q in zip(a, b)]; j = int(np.argmax(dif))
    out.append("%s_%s %.1f(c%.1f) %d>%d" % (cl, st, dif[j], j / STEP[cl], max(angles(x).max() for x in a), max(angles(x).max() for x in b)))
print(o, SET); print("\n".join(out))
