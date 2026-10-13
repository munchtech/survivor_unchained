from ev5 import *
import ev5
def braid_only(o):
    def runb(name):
        out = []
        for cl in ("throw", "run", "stop", "death", "getup"):
            fr = lg("hair12", cl + "_braid"); a = sim5(fr, "braid", **per4(H7, "braid")); b = sim5(fr, "braid", **per4(o, "braid"))
            out.append("%s %.1f" % (cl, max(np.linalg.norm(p - q, axis=1).max() for p, q in zip(a, b)) * 100))
        print(name, "throw joint f15-21 %.0f" % max(angles(b[j]).max() for j in range(15, 21)) if False else "", end="")
        fr = lg("hair12", "throw_braid"); xs = sim5(fr, "braid", **per4(o, "braid"))
        print(name, "throw joint f15-21 %.0f |" % max(angles(xs[j]).max() for j in range(15, 21)), " ".join(out))
    return runb
for k in (45, 55):
    braid_only(dict(H7, kink=k))("K%d" % k)
run("F15v2", dict(H7, facc=1.5, fvmin=2.0))
