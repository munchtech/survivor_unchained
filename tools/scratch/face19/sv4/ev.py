"""ev.py CFG...: solver 4's acceptance numbers offline (hair9 inputs).
death long: lift off her back (cm, points 2-7) at c8 (f23-25) and c7-c11, worst of 6 seeds;
death braid/ponytail: lift at c3-c5 (the c4 rod), worst joint (deg) and worst cap deviation (deg, past its rest bend), highest point over the tie (cm) c11-14;
run/stop/throw: worst point distance from today's (G2) chain (cm)."""
import sys
from hs4 import *
sys.path.insert(0, "../sv3")
from lift import lifts, perturb
def capdev(tg, x):
    rest = [None] + [nz(tg[i] - tg[i - 1]) for i in range(1, 8)]; out = []
    R = np.eye(3)
    for i in range(1, 8):
        cur = nz(x[i] - x[i - 1])
        if i > 1: out.append(math.degrees(math.acos(np.clip(cur @ (R @ rest[i]), -1, 1))))
        R = rot_between(rest[i], cur)
    return np.array(out)
def run(name, o, quick=False):
    res = {}
    fr = lg("hair9", "death_long"); L8 = []; L = []
    for sd in (range(1) if quick else range(6)):
        f = perturb(fr, sd); xs = sim4(f, "long", **per4(o, "long"))
        L8.append(max(lifts(f[j], xs[j])[2:].max() for j in (23, 24, 25)) * 100)
        L.append(max(lifts(f[j], xs[j])[2:].max() for j in range(21, 34)) * 100)
    res["long"] = "lift c8 %.1f c7-11 %.1f" % (max(L8), max(L))
    for st in ("braid", "ponytail"):
        fr = lg("hair9", "death_" + st); xs = sim4(fr, st, **per4(o, st))
        rod = max(lifts(fr[j], xs[j])[2:].max() for j in range(9, 16)) * 100
        ang = max(angles(xs[j]).max() for j in range(len(xs)))
        cd = [capdev(fr[j]["target"], xs[j]).max() for j in range(len(xs))]
        up = max(max(xs[j][k][1] - xs[j][0][1] for k in range(1, 8)) for j in range(33, 44)) * 100
        fl = min(min(xs[j][k][1] - fr[j]["ground"] for k in range(4, 8)) for j in range(36, 44)) * 100
        res[st] = "rod c3-5 %4.1f ang %3.0f capdev %3.0f@f%d up c11-14 %+5.1f lowest end c12-14 %4.1f" % (rod, ang, max(cd), int(np.argmax(cd)), up, fl)
    if not quick:
        worst = []
        for st in ("braid", "ponytail", "long"):
            for cl in ("run", "stop", "throw"):
                fr = lg("hair9", cl + "_" + st); a = sim4(fr, st, **per4(C2, st)); b = sim4(fr, st, **per4(o, st))
                worst.append("%s/%s %.1f" % (cl[:2], st[:2], max(np.linalg.norm(p - q, axis=1).max() for p, q in zip(a, b)) * 100))
        res["rst"] = " ".join(worst)
    print("== %s\n  %s" % (name, "\n  ".join("%s: %s" % kv for kv in res.items())))
if __name__ == "__main__":
    q = "-q" in sys.argv
    for n in [a for a in sys.argv[1:] if a != "-q"]:
        run(n, eval(n), q)
