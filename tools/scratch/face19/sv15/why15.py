"""why15.py OPTS K1,K2,.. [MD]: for frames K, segments 4-7: mesh clearance (cm) and the deepest each link goes into the
colliders (cm, >0 inside): arm balls grown by pad (11-14), the ridge/slope capsules (as hs14 makes them), neck/back balls."""
from ev15 import *
o = eval(sys.argv[1]); ks = [int(v) for v in sys.argv[2].split(",")]; md = sys.argv[3] if len(sys.argv) > 3 else "mw"
fr, xs, m = run14("ponytail", o); oo = dict(o); sc = 1.04
for k in ks:
    d = fr[k]; x = xs[k]; c = clear(x, "s12/" + md, k); cs = capsules(d, dict(RA=0.045, RB=0.085, marg=o.get("marg", 0.035), slope=o.get("slope"), RS=o.get("RS", 0.035)))
    print("k%d carried %s" % (k, "".join("1" if q else "." for q in m.rlog[k])))
    for i in range(4, 8):
        S = [x[i - 1] + (x[i] - x[i - 1]) * t for t in np.linspace(0, 1, 21)]
        arm = []
        for b in range(11, len(d["r"])):
            r = (d["r"][b] + 0.025) * sc; w = d["across"][b]; ww = w @ w; at = d["at"][b]
            dep = max(r - np.linalg.norm(p - (at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else p - at)) if False else r - np.linalg.norm(p - ((at + w * np.clip((p - at) @ w / ww, -1, 1)) if ww > 0 else at)) for p in S)
            arm.append(dep * 100)
        cap = []
        for a, b, ra, rb in cs:
            ab = b - a; dd = []
            for p in S:
                t = min(1.0, max(0.0, float((p - a) @ ab / (ab @ ab)))); dd.append(ra + (rb - ra) * t - np.linalg.norm(p - (a + ab * t)))
            cap.append(max(dd) * 100)
        bod = []
        for b in range(0, 11):
            r = d["r"][b] * sc; w = d["across"][b]; ww = w @ w; at = d["at"][b]
            bod.append(max(r - np.linalg.norm(p - ((at + w * np.clip((p - at) @ w / ww, -1, 1)) if ww > 0 else at)) for p in S) * 100)
        print("  s%d mesh %5.1f | arm %s | caps %s | body max %5.1f (ball %d)" % (i, c[i - 1], " ".join("%5.1f" % v for v in arm),
              " ".join("%5.1f" % v for v in cap), max(bod), int(np.argmax(bod))))
