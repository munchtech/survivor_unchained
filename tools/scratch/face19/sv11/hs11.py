"""hs11.py: solver 11's carry push (option s11=1): a carried point above a neck or back ball's centre (along her spine) is
pushed out the nearest way (up onto it), else square to her spine as before; and it is kept out of her shoulder and
upper-arm balls grown by 'pad' (m), the nearest way (over the top when above the joint). ev11 metrics per get_up frame."""
from h11 import *
OLD = M8.rcollide
def rc11(s, d, p, upax, sc=1.04):
    if not s.o.get("s11"): return OLD(s, d, p, upax, sc)
    for b in range(len(d["r"])):
        sh = b >= 11
        r = (d["r"][b] + (s.o.get("pad", 0.025) if sh else 0)) * sc; w = d["across"][b]; ww = w @ w; at = d["at"][b]
        c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
        off = p - c
        if off @ off >= r * r: continue
        if sh or off @ upax > 0: p = c + nz(off) * r; continue
        u = upax * (off @ upax); fl = off - u
        if fl @ fl < 1e-10 or u @ u >= r * r: continue
        p = c + u + nz(fl) * math.sqrt(r * r - u @ u)
    return p
M8.rcollide = rc11
def metrics(fr, xs, m, pad=0.025, sc=1.04):
    """per frame: worst link stretch (cm), worst depth of the chain's segments in the neck balls (1,2) and in the right
    shoulder/upper-arm balls grown by pad (cm), round flags, weight."""
    L0 = np.linalg.norm(np.diff(fr[0]["target"], axis=0), axis=1); out = []
    for i, (d, x) in enumerate(zip(fr, xs)):
        st = (np.linalg.norm(np.diff(x, axis=0), axis=1) - L0).max() * 100; nk = -99; shd = -99
        for j in range(1, 8):
            for t in np.linspace(0, 1, 9):
                q = x[j - 1] + (x[j] - x[j - 1]) * t
                for b in (1, 2): nk = max(nk, (d["r"][b] * sc - np.linalg.norm(q - d["at"][b])) * 100)
                for b in (13, 14): shd = max(shd, ((d["r"][b] + pad) * sc - np.linalg.norm(q - d["at"][b])) * 100)
        out.append((st, nk, shd, "".join("1" if r else "." for r in m.rlog[i]), m.wlog[i]))
    return out
