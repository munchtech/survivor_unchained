"""hs13.py: solver 13: solver 12's ridge capsules with the option renamed 'ridge' (hs12's 'cap' was already the swing's
velocity cap, 2.5: so hs12's HEAD runs had the capsules on, and its cap=1 runs also changed the swing). M8.frame copied
here with: the capsules while carrying (every drape point), a tapered radius (RA at the neck end, RB at the shoulder end),
the link pass (a link that cuts a capsule has its far end swung out over it), and the judge's release order (rel=1: a
carried point is let go only once the next one toward the tip is behind the plane through her shoulders)."""
import sys; sys.path[:0] = ["../sv12", "../sv11", "../sv10", "../sv9", "../sv8", "../sv6", "../sv5", "../sv4", "../sv3"]
from h12 import *
CA, CB = np.array([-0.1069, 1.5404, -0.0536]), np.array([-0.2115, 1.501, -0.0434])
A3 = np.array([0, 1.5240698, -0.0268065])
def caps(d, sc):
    ex = nz(d["across"][3]); ez = -nz(d["back"][3]); ey = np.cross(ez, ex); R = np.c_[ex, ey, ez]; a3 = d["at"][3]
    w = lambda p: a3 + R @ ((p - A3) * sc)
    m = np.array([-1, 1, 1])
    return [(w(CA), w(CB)), (w(CA * m), w(CB * m))]
CYL = [False]
def seg_t(p, a, b):
    """the closest point's place along ab (0-1); with CYL (flat ends), None past either end"""
    ab = b - a; L2 = ab @ ab
    t = 0.0 if L2 < 1e-12 else float((p - a) @ ab / L2)
    if CYL[0] and (t < 0 or t > 1): return None
    return min(1.0, max(0.0, t))
def cap_push(p, cs, rA, rB):
    for e in cs:
        a, b = e[0], e[1]; ra, rb = (e[2], e[3]) if len(e) > 2 else (rA, rB)
        t = seg_t(p, a, b)
        if t is None: continue
        c = a + (b - a) * t; r = ra + (rb - ra) * t; off = p - c; L = np.linalg.norm(off)
        if L < r: p = c + (off / L if L > 1e-9 else np.array([0, 1, 0])) * r
    return p
def cap_over(p, cs, rA, rB, upax, bk, gain=1.0):
    """a carried point run into a capsule from in front of its axis slides up its surface toward the top by as far as it
    went in (deflected, not pushed back the way it came); behind the axis, the nearest way."""
    for a, b in cs:
        t = seg_t(p, a, b)
        if t is None: continue
        c = a + (b - a) * t; r = rA + (rB - rA) * t; off = p - c; L = np.linalg.norm(off)
        if L >= r: continue
        dn = off / L if L > 1e-9 else upax
        if off @ bk < 0:
            ax = nz(b - a); u = nz(upax - ax * (upax @ ax)); cosu = float(np.clip(dn @ u, -1, 1)); ang = math.acos(cosu)
            da = min(ang, (r - L) * gain / r)
            if ang > 1e-6:
                v = nz(u - dn * cosu); dn = dn * math.cos(da) + v * math.sin(da)
        p = c + dn * r
    return p
def cap_lift(p, cs, rA, rB, upax):
    """a carried point inside a capsule above its axis goes straight up (along her spine) onto it, so the carry round her
    spine is never pushed back; below the axis, the nearest way."""
    for a, b in cs:
        t = seg_t(p, a, b)
        if t is None: continue
        c = a + (b - a) * t; r = rA + (rB - rA) * t; off = p - c; L = np.linalg.norm(off)
        if L >= r: continue
        ax = nz(b - a); u = upax - ax * (upax @ ax); oo = off - ax * (off @ ax)
        if off @ upax > 0 and u @ u > 1e-6:
            # |oo + u d| = r, d > 0
            A_ = u @ u; B_ = 2 * (oo @ u); C_ = oo @ oo - r * r; d = (-B_ + math.sqrt(max(0.0, B_ * B_ - 4 * A_ * C_))) / (2 * A_)
            p = p + upax * d
        else: p = c + (off / L if L > 1e-9 else upax) * r
    return p
def cap_touch(p, cs, rA, rB, bk, eps):
    """is p within eps of a capsule's surface (or inside), in front of its axis?"""
    for a, b in cs:
        t = seg_t(p, a, b)
        if t is None: continue
        c = a + (b - a) * t; r = rA + (rB - rA) * t; off = p - c
        if off @ off < (r + eps) ** 2 and off @ bk < 0: return True
    return False
def link_cut(p, q, a, b, n=8):
    """the deepest point of link pq in the capsule ab: (depth-ratio test done by the caller) s on pq, x, its axis point c, t"""
    best = None
    for s in np.linspace(0, 1, n + 1):
        x = p + (q - p) * s; t = seg_t(x, a, b)
        if t is None: continue
        c = a + (b - a) * t; dd = np.linalg.norm(x - c)
        if best is None or dd < best[0]: best = (dd, s, x, c, t)
    return best
def frame13(s, d):
    o = s.o; first = not s.live; dt = d["dt"]; tg = d["target"]
    x = M5.frame(s, d).copy()
    if not o["laid"]: return x
    D, U = measures(d, o)
    at = d["at"]; neck = (at[1] + at[2]) / 2; upax = nz(neck - at[10]); upright = upax[1]
    carrying = s.rnd.any() and o["rhold"]
    if first: s.w = D
    elif D > s.w: s.w = min(D, s.w + dt / o["rise"])
    elif not carrying: s.w = max(0.0, s.w - U * dt / o["fall"])
    if s.w >= 1 - 1e-4: s.full = True
    elif s.w <= 0: s.full = False; s.side = 0; s.rnd[:] = False
    floor = d["ground"] + 0.015
    link = np.r_[0, np.linalg.norm(np.diff(tg, axis=0), axis=1)]
    CYL[0] = bool(o.get("cyl")); sc = 1.04; mg = o.get("marg", 0.035); rA = (o.get("RA", 0.085) + mg) * sc; rB = (o.get("RB", o.get("RA", 0.085)) + mg) * sc
    rdg = bool(o.get("ridge")) and s.style != "long"; cs = caps(d, sc) if rdg else []
    if rdg and o.get("slope"):
        ex = nz(d["across"][3]); ez = -nz(d["back"][3]); ey = np.cross(ez, ex); R = np.c_[ex, ey, ez]; a3 = d["at"][3]
        w = lambda p: a3 + R @ ((p - A3) * sc); S = np.array(o["slope"]); m_ = np.array([-1, 1, 1]); rs = (o.get("RS", 0.035) + mg) * sc
        cs = cs + [(w(S), w(CA), rs, rA), (w(S * m_), w(CA * m_), rs, rA)]
    s.capon = False
    if first or s.w <= 0 or s.dr is None: s.dr = x.copy()
    else:
        dr = s.dr + (tg[0] - s.rootT); dr[0] = tg[0]
        upax = nz(neck - at[10])
        armed = o["rcarry"] and s.full and upright > o["rlo"] and d["head"][0][1] - d["ground"] > o["rh"] and (s.style != "long" or not o["rhead"])
        bk = d["back"][1]; bk = nz(bk - (bk @ upax) * upax); ac = np.cross(upax, bk)
        shm = (at[11] + at[13]) / 2
        if armed:
            def polar(p):
                r = p - neck; hg = r @ upax; a = r @ ac; b = r @ bk
                return hg, a, b, math.hypot(a, b)
            if s.side == 0:
                sa = sum(polar(dr[i])[1] for i in range(1, 8) if polar(dr[i])[2] < -o["rfront"] and polar(dr[i])[0] < o["rtop"])
                s.side = 1 if sa >= 0 else -1
            thmax = math.pi - (math.pi - math.radians(o["rto"])) * float(smooth(o["rlo"], o["rhi"], upright))
            stepmax = math.pi * dt / o["rtime"]
            for i in range(1, 8):
                hg, a, b, rho = polar(dr[i])
                if rho < o["rmin"]: continue
                th = math.atan2(s.side * a, b)
                if not s.rnd[i] and b < -o["rfront"] and hg < o["rtop"]: s.rnd[i] = True
                if not s.rnd[i]: continue
                if th < -math.pi / 2: th += 2 * math.pi
                if th <= math.radians(o["rto"]) + 1e-3:
                    # (rel: not while the next point toward the tip is still in front of the plane through her shoulders)
                    if o.get("rel") and i < 7 and (dr[i + 1] - shm) @ bk < o.get("relb", 0.0): continue
                    s.rnd[i] = False; continue
                s.rth[i] = th
        on = rdg and s.rnd.any()
        s.capon = on
        for k in range(o["K"]):
            for i in range(1, 8):
                came = dr[i].copy()
                if not (on and s.rnd[i] and o.get("nograv") and cap_touch(dr[i], cs, rA, rB, bk, o.get("geps", 0.005))): dr[i][1] -= o["step"]
                dirn = nz(dr[i] - dr[i - 1])
                dr[i] = dr[i - 1] + dirn * link[i]
                dr[i] = s.rcollide(d, dr[i], upax) if s.rnd[i] and o.get("rrad") else s.dcollide(d, dr[i], came)
                if o.get("disp"): pass
                elif on and s.rnd[i] and o.get("lift"): dr[i] = cap_lift(dr[i], cs, rA, rB, upax)
                elif on and s.rnd[i] and o.get("over"): dr[i] = cap_over(dr[i], cs, rA, rB, upax, bk, o.get("gain", 1.0))
                elif on and (s.rnd[i] or not o.get("capr")): dr[i] = cap_push(dr[i], cs, rA, rB)
                dr[i][1] = max(dr[i][1], floor)
                if armed and s.rnd[i] and o.get("rin"):
                    hg, a, b, rho = polar(dr[i]); th = math.atan2(s.side * a, b)
                    if th < -math.pi / 2: th += 2 * math.pi
                    if th > thmax: dr[i] = neck + rotab(dr[i] - neck, upax, -s.side * min(th - thmax, stepmax / o["K"]))
        if on and o.get("links") and s.w >= 1 - 1e-4 and not o.get("disp"):
            balls = [(e[0], e[1], e[2], e[3]) if len(e) > 2 else (e[0], e[1], rA, rB) for e in cs] + ([(at[j], at[j], d["r"][j] * sc, d["r"][j] * sc) for j in (1, 2)] if o.get("lneck") else [])
            for it in range(o.get("lit", 2)):
                for i in range(2, 8):
                    for a, b, ra, rb in balls:
                        lc = link_cut(dr[i - 1], dr[i], a, b, o.get("ln", 40))
                        if lc is None: continue
                        dd, t, xx, c, tt = lc
                        rr = ra + (rb - ra) * tt
                        if dd >= rr or t < 0.05: continue
                        n = nz(xx - c); q = dr[i] + n * (rr - dd) / t
                        dr[i] = dr[i - 1] + nz(q - dr[i - 1]) * link[i]
                        for j in range(i + 1, 8): dr[j] = dr[j - 1] + nz(dr[j] - dr[j - 1]) * link[j]
        s.dr = dr
    s.rootT = tg[0].copy()
    show = s.dr
    if o.get("disp") and s.capon:
        show = s.dr.copy()
        for it in range(o.get("dit", 2)):
            for i in range(2, 8):
                show[i] = cap_push(show[i], cs, rA, rB)
                show[i] = show[i - 1] + nz(show[i] - show[i - 1]) * link[i]
                if o.get("links"):
                    for a, b in cs:
                        lc = link_cut(show[i - 1], show[i], a, b, o.get("ln", 40))
                        if lc is None: continue
                        dd, t, xx, c, tt = lc; rr = rA + (rB - rA) * tt
                        if dd >= rr or t < 0.05: continue
                        n = nz(xx - c); q = show[i] + n * (rr - dd) / t
                        show[i] = show[i - 1] + nz(q - show[i - 1]) * link[i]
    s.show = show
    out = x + (show - x) * s.w
    if s.w >= 1 - 1e-4:
        steps = max(1, int(math.ceil(dt * 120 - 1e-3)))
        rs = (tg[0] - s.prevRoot) / steps if hasattr(s, "prevRoot") else 0
        s.x[:] = show; s.xp[:] = show - rs
    s.prevRoot = tg[0].copy()
    s.wlog.append(s.w); s.swing.append(x); s.drape.append(s.dr.copy()); s.rlog.append(s.rnd.copy())
    if not hasattr(s, "caplog"): s.caplog = []
    s.caplog.append(s.capon)
    return out
M8.frame = frame13
DUMP = dict(ponytail="hc/s11_ponytail_review", braid="hc/s11_braid_review")
def run13(st, log=None, **o):
    fr = lg(*(log or DUMP[st]).split("/")); xs, m = run12(fr, st, **o); return fr, xs, m
def evalc(st, o, K0=40, K1=52, log=None):
    fr, xs, m = run13(st, log, **o); res = {}
    for md in ("mw", "mr"): res[md] = {k: clear(xs[k], "s12/" + md, k) for k in range(K0, K1 + 1)}
    return fr, xs, m, res
