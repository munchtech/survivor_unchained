"""sum.py: Godot HAIRCLEAR/HAIRMOVE from the pt1 logs (on vs off), per outfit and view: segs 4-7 worst k40-52, k28-52,
k53-60; the largest HAIRMOVE k40-60 and k28-60; k0-27 on-off; and per frame (v) the worst segs 4-7 on/off."""
import re, sys, os
D = os.path.dirname(os.path.abspath(__file__))
def rd(f):
    seg, mv = {}, {}
    if not os.path.exists(f): return None, None
    for l in open(f, errors="ignore"):
        m = re.match(r"HAIRCLEAR k=(\d+) segs (.*)", l)
        if m: seg[int(m.group(1))] = [float(v) for v in m.group(2).split()]
        m = re.match(r"HAIRMOVE k=(\d+) max=([\d.]+) point=(\d+)", l)
        if m: mv[int(m.group(1))] = (float(m.group(2)), int(m.group(3)))
    return seg, mv
w = lambda s, a, b: min((min(s[k][3:]), k) for k in range(a, b + 1) if k in s)
mm = lambda m, a, b: max((m[k][0], k, m[k][1]) for k in range(a, b + 1) if k in m)
V = "v" in sys.argv
for od in ("warden", "reaver"):
    for vw in ("bk", "rv", "r3"):
        n = "%s_%s" % (vw, od); a, ma = rd(os.path.join(D, n + "_on.log")); b, mb = rd(os.path.join(D, n + "_off.log"))
        if not a or not b: print(n, "missing"); continue
        d = max(max(abs(x - y) for x, y in zip(a[k], b[k])) for k in range(0, 28) if k in a and k in b)
        f = lambda s, m: "k40-52 %5.1f (k%d) k28-52 %5.1f (k%d) k53-60 %5.1f (k%d) | move k40-60 %4.1f (k%d p%d) k28-60 %4.1f (k%d p%d)" % (
            *w(s, 40, 52), *w(s, 28, 52), *w(s, 53, 60), *mm(m, 40, 60), *mm(m, 28, 60))
        print("%-10s ON  %s | k0-27 on-off %.2f" % (n, f(a, ma), d)); print("%-10s OFF %s" % (n, f(b, mb)))
        if V and vw == "bk":
            for k in range(28, 61):
                print("   k%d on %s | off %s | mv %.1f/%.1f" % (k, " ".join("%5.1f" % v for v in a[k]), " ".join("%5.1f" % v for v in b[k]), ma.get(k, (0,))[0], mb.get(k, (0,))[0]))
