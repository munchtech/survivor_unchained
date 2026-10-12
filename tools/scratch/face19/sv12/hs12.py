"""hs12.py: solver 12's ridge capsules (option cap=1): while the round carry runs, every drape point is kept out of a
capsule per side along the ridge from her neck's base to the top of her shoulder (on spine_03, ends A-B in its rest
space, radius R + marg), and (links=1) each link too: if it cuts the capsule, its far end is swung out over it."""
from ridge import rest_of, A3
from h12 import *
CA, CB = np.array([-0.1069, 1.5404, -0.0536]), np.array([-0.2115, 1.501, -0.0434])
def caps(d, sc, fa=0.0):
    ca = CA + (CB - CA) * fa
    ex = nz(d["across"][3]); ez = -nz(d["back"][3]); ey = np.cross(ez, ex); R = np.c_[ex, ey, ez]; a3 = d["at"][3]
    w = lambda p: a3 + R @ ((p - A3) * sc)
    m = np.array([-1, 1, 1])
    return [(w(ca), w(CB)), (w(ca * m), w(CB * m))]
def seg_closest(p, a, b):
    ab = b - a; L2 = ab @ ab
    if L2 < 1e-12: return a.copy()
    t = np.clip((p - a) @ ab / L2, 0, 1); return a + ab * t
def cap_push(p, cs, r):
    for a, b in cs:
        c = seg_closest(p, a, b); off = p - c; L = np.linalg.norm(off)
        if L < r: p = c + (off / L if L > 1e-9 else np.array([0, 1, 0])) * r
    return p
def seg_seg(p, q, a, b):
    """closest points of segments pq and ab (s on pq, t on ab), by sampling pq finely (offline only)."""
    best = None
    for s in np.linspace(0, 1, 41):
        x = p + (q - p) * s; c = seg_closest(x, a, b); dd = np.linalg.norm(x - c)
        if best is None or dd < best[0]: best = (dd, s, x, c)
    return best
OLDF = M8.frame
def frame12(s, d):
    o = s.o
    if not o.get("cap"): return OLDF(s, d)
    # (the HEAD drape step, with the capsules added while carrying)
    sc = 1.04; r = (o.get("R", 0.085) + o.get("marg", 0.035)) * sc; cs = caps(d, sc, o.get("fa", 0.0))
    orc, odc = M8.rcollide, M8.dcollide
    def rc(self, d_, p, upax, sc_=1.04): return cap_push(orc(self, d_, p, upax, sc_), cs, r) if self.rnd.any() else orc(self, d_, p, upax, sc_)
    def dc(self, d_, p, came, sc_=1.04, nb=None, flip=0.0):
        q = odc(self, d_, p, came, sc_, nb, flip); return cap_push(q, cs, r) if self.rnd.any() and not o.get("capr") else q
    s.rcollide = rc.__get__(s); s.dcollide = dc.__get__(s)
    out = OLDF(s, d)
    if o.get("links") and s.rnd.any() and s.w >= 1 - 1e-4:
        dr = s.dr; link = np.r_[0, np.linalg.norm(np.diff(d["target"], axis=0), axis=1)]
        for it in range(o.get("lit", 2)):
            for i in range(2, 8):
                for a, b, rr in [(a, b, r) for a, b in cs] + ([(d["at"][j], d["at"][j], d["r"][j] * sc) for j in (1, 2)] if o.get("lneck") else []):
                    dd, t, x, c = seg_seg(dr[i - 1], dr[i], a, b)
                    if dd >= rr or t < 0.05: continue
                    n = nz(x - c); q = dr[i] + n * (rr - dd) / t
                    dr[i] = dr[i - 1] + nz(q - dr[i - 1]) * link[i]
                    for j in range(i + 1, 8): dr[j] = dr[j - 1] + nz(dr[j] - dr[j - 1]) * link[j]
        s.x[:] = dr; out = dr.copy(); s.drape[-1] = dr.copy()
    return out
M8.frame = frame12
