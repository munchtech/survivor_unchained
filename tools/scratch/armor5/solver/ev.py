"""ev.py <socket> <x;x;...> [--vox v]: worst body/arm/snug per trial (dx,dy,dz,rx,ry,rz in m and degrees, skeleton axes)."""
import sys, numpy as np, score as S, opt
SP = opt.SP
so = sys.argv[1]; xs = [np.array([float(v) for v in t.split(",")]) for t in sys.argv[2].split(";")]
vox = float(sys.argv[3]) if len(sys.argv) > 3 else 0.012
row0 = S.ROWS[so]
s = S.Scorer({row0[0]: SP + ("pelvis.npz" if row0[0] == "pelvis" else "spine.npz")}, [so])
for k, q in list(s.pts.items()):
    _, first = np.unique(np.floor(q / vox).astype(np.int64), axis=0, return_index=True); s.pts[k] = q[np.sort(first)]
for x in xs:
    row = opt.trial(row0, x, False)
    res, clr = s.score(so, row)
    sa, ta = opt.angles(row0, row)
    print(f"x {x.tolist()} shaft {sa:.0f} thick {ta:.0f}")
    for k, v in res.items():
        b = max(v.values(), key=lambda t: t[0]); a = max(v.values(), key=lambda t: t[1])
        g = min(t[4] - clr[o] * 1000 for o, t in v.items())
        print(f"   {k:24} body {b[0]:5.1f} @{b[3]:22} arm {a[1]:5.1f} @{a[2]:22} snug {g:5.1f}")
