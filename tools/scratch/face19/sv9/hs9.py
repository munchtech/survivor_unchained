"""hs9.py: solver 9: M8 (C# at 7f2968ce) with the back capsules' stretch fading toward each ball's top (tlo..thi of its
radius up its bone): her shoulders slope down from her neck, and the flat-topped capsule held a flung braid on a ridge
beside her neck (throw braid c3-c10 Z)."""
from g9 import *
TAPER = dict(tlo=0.5, thi=0.9, taper=True)
def near(d, b, p, sc, o):
    """The nearest point of ball b's line to p, and the ball's half-width line used (tapered toward its top)."""
    w = d["across"][b]; ww = w @ w; at = d["at"][b]
    if ww <= 0: return at, w
    if o.get("taper"):
        up = np.cross(w / math.sqrt(ww), d["back"][b])
        w = w * (1 - float(smooth(o["tlo"], o["thi"], (p - at) @ up / (d["r"][b] * sc))))
        ww = w @ w
        if ww <= 1e-12: return at, w
    return at + w * np.clip((p - at) @ w / ww, -1, 1), w
class M9(M8):
    def __init__(s, fr, style, **o):
        M8.__init__(s, fr, style, **o)
        for k, v in TAPER.items(): s.o.setdefault(k, v)
    def collide(s, d, p, i=None, sc=1.0):
        for b in range(len(d["r"])):
            r = d["r"][b] * sc
            if r <= 0: continue
            c, w = near(d, b, p, sc, s.o); off = p - c
            if off @ off >= r * r: continue
            bk = d["back"][b]
            if d["behind"][b] and off @ bk < 0:
                came = s.o["mirror"] == "came" or (s.o["mirror"] == "came_free" and i is not None and s.free[i] > 0.5)
                if i is None or not came or (s.prev[i] - c) @ bk >= 0: off = off - 2 * (off @ bk) * bk
            n = nz(off) if off @ off > 1e-10 else bk
            p = c + n * r
            if i is not None:
                s.touch[i] = n; s.grip[i] = max(s.grip[i], s.o["grip_ball"])
                if s.pd is not None:
                    ww = w @ w; tt = np.clip((p - d["at"][b]) @ w / ww, -1, 1) if ww > 0 else 0
                    f = math.sqrt(ww / (d["across"][b] @ d["across"][b])) if ww > 0 else 0
                    s.surf[i] = (c - (s.pd["at"][b] + s.pd["across"][b] * f * tt)) / s.nsteps
                else: s.surf[i] = 0
        return p
    def dcollide(s, d, p, came, sc=1.04, nb=None, flip=0.0):
        for b in range(len(d["r"]) if nb is None else nb):
            r = d["r"][b] * sc; c, w = near(d, b, p, sc, s.o); off = p - c
            if off @ off >= r * r: continue
            bk = d["back"][b]
            if d["behind"][b] and off @ bk < 0 and not ((came - c) @ bk < 0): off = off - 2 * (off @ bk) * bk
            n = nz(off) if off @ off > 1e-10 else bk
            p = c + n * r
        return p
    def rcollide(s, d, p, upax, sc=1.04):
        for b in range(11):
            r = d["r"][b] * sc; c, w = near(d, b, p, sc, s.o); off = p - c
            if off @ off >= r * r: continue
            u = upax * (off @ upax); fl = off - u
            if fl @ fl < 1e-10 or u @ u >= r * r: continue
            p = c + u + nz(fl) * math.sqrt(r * r - u @ u)
        return p
def sim9(fr, style, **o):
    m = M9(fr, style, **o)
    return [m.frame(d).copy() for d in fr], m
