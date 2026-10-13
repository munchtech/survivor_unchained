"""hs6.py: solver 6: hs5's M5 (as C# at c3958e1a: H7) plus the laid shape: a down weight from her skeleton (held until she
is up), a drape (inertia-free chain carried with the root's move, settled under gravity, kept out of her and the floor), the
output blended swing -> drape by the weight, and the swing reset to the drape while fully down."""
import sys; sys.path[:0] = ["../sv5", "../sv4", "../sv3"]
from hs5 import *
SS = lambda a, b, x: float(smooth(a, b, x))
def measures(d, o):
    g = d["ground"]; at = d["at"]
    neck = (at[1] + at[2]) / 2; low = at[10]; back = at[3:8].mean(0); head = d["head"][0]
    up = nz(neck - low)[1]
    D = (1 - SS(o["blo"], o["bhi"], back[1] - g)) * (1 - SS(o["flo"], o["fhi"], up))
    U = SS(o["hlo"], o["hhi"], head[1] - g) * SS(o["ulo"], o["uhi"], up)
    return D, U
LAID = dict(blo=0.45, bhi=0.95, flo=0.3, fhi=0.7, hlo=1.1, hhi=1.35, ulo=0.8, uhi=0.95, rise=0.7, fall=0.5, K=4, step=0.02, kst=0.0, laid=True)
class M6(M5):
    def __init__(s, fr, style, **o):
        M5.__init__(s, fr, style, **o)
        for k, v in LAID.items(): s.o.setdefault(k, v)
        s.w = 0.0; s.dr = None; s.wlog = []; s.swing = []; s.drape = []
    def dcollide(s, d, p, came, sc=1.04):
        for b in range(len(d["r"])):
            r = d["r"][b] * sc; w = d["across"][b]; ww = w @ w; at = d["at"][b]
            c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
            off = p - c
            if off @ off >= r * r: continue
            bk = d["back"][b]
            if d["behind"][b] and off @ bk < 0 and not ((came - c) @ bk < 0): off = off - 2 * (off @ bk) * bk
            n = nz(off) if off @ off > 1e-10 else bk
            p = c + n * r
        return p
    def frame(s, d):
        o = s.o; first = not s.live; dt = d["dt"]; tg = d["target"]
        x = M5.frame(s, d).copy()
        if not o["laid"]: return x
        D, U = measures(d, o)
        if first: s.w = D
        elif D > s.w: s.w = min(D, s.w + dt / o["rise"])
        else: s.w = max(0.0, s.w - U * dt / o["fall"])
        floor = d["ground"] + 0.015
        link = np.r_[0, np.linalg.norm(np.diff(tg, axis=0), axis=1)]
        if first or s.w <= 0 or s.dr is None: s.dr = x.copy()
        else:
            dr = s.dr + (tg[0] - s.rootT); dr[0] = tg[0]
            for k in range(o["K"]):
                for i in range(1, 8):
                    came = dr[i].copy(); dr[i][1] -= o["step"]
                    dirn = nz(dr[i] - dr[i - 1])
                    if o["kst"] and i >= 2: dirn = nz(dirn + o["kst"] * nz(dr[i - 1] - dr[i - 2]))
                    dr[i] = dr[i - 1] + dirn * link[i]
                    dr[i] = s.dcollide(d, dr[i], came)
                    dr[i][1] = max(dr[i][1], floor)
            s.dr = dr
        s.rootT = tg[0].copy()
        out = x + (s.dr - x) * s.w
        if s.w >= 1 - 1e-4:
            steps = max(1, int(math.ceil(dt * 120 - 1e-3)))
            rs = (tg[0] - s.prevRoot) / steps if hasattr(s, "prevRoot") else 0
            s.x[:] = s.dr; s.xp[:] = s.dr - rs
        s.prevRoot = tg[0].copy()
        s.wlog.append(s.w); s.swing.append(x); s.drape.append(s.dr.copy())
        return out
def sim6(fr, style, **o):
    m = M6(fr, style, **o)
    xs = [m.frame(d).copy() for d in fr]
    return xs, m
