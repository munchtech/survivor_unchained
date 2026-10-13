from hs9 import *
fr = lg("hair18", "throw_braid"); xs, _ = sim9(fr, "braid", **per4(dict(H7, taper=False, kink=45), "braid")); cs = today(fr)
print("per frame:", " ".join("%.2f" % (np.linalg.norm(p - q, axis=1).max() * 100) for p, q in zip(xs, cs)))
for st in ("ponytail", "braid", "long"):
    a, b = lg("hair17d", "throw_" + st), lg("hair18", "throw_" + st); n = min(len(a), len(b))
    print("throw", st, "hair17d vs hair18 C#: %.2f cm" % (max(np.linalg.norm(a[j]["x"] - b[j]["x"], axis=1).max() for j in range(n)) * 100), "inputs same: %.4f" % max(np.abs(a[j]["target"] - b[j]["target"]).max() for j in range(n)))
