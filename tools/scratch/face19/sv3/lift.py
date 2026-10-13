"""lift.py: lift off her back (cm) of a death chain over frames, robust over small perturbations."""
import sys, copy
from cfg3 import *
def lifts(d, x, sc=1.04):
    out = []
    for p in x:
        best = 1e9; bb = -1; cc = None
        for b in range(len(d["r"])):
            w = d["across"][b]; ww = w @ w; at = d["at"][b]
            c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
            g = np.linalg.norm(p - c) - d["r"][b] * sc
            if g < best: best, bb, cc = g, b, c
        q = nz(p - cc); out.append(best if (d["behind"][bb] and q @ d["back"][bb] > 0.5) else 0)
    return np.array(out)
def perturb(fr, seed, amp=2e-4):
    if seed == 0: return fr
    rng = np.random.default_rng(seed); out = []
    for d in fr:
        e = dict(d); e["target"] = d["target"] + rng.normal(0, amp, d["target"].shape); out.append(e)
    return out
def measure(st, o, f0=21, f1=33, seeds=range(6), clip="death"):
    fr = lg("hair9", clip + "_" + st); res = []
    for sd in seeds:
        f = perturb(fr, sd); xs = sim(f, st, **per(o, st))
        res.append(max(lifts(f[j], xs[j])[2:].max() for j in range(f0, f1 + 1)) * 100)
    return np.array(res)
if __name__ == "__main__":
    st = sys.argv[1]
    for n in sys.argv[2:]:
        r = measure(st, eval(n)); print("%-30s lift cm: %s  max %.1f" % (n, " ".join("%.1f" % v for v in r), r.max()))
