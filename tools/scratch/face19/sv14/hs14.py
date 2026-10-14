"""hs14.py: solver 14 (get_up shoulder cut, last attempt). hs13's frame with the ridge capsules in the chain solve
restructured as the C# port will run them:
  ridge=1      the tapered capsules per side on spine_03 (RA neck end, RB shoulder end, marg added; slope=S adds the
               ponytail's slope capsule from S to the ridge's neck end, RS tapering to RA)
  cpts         'all' (every drape point while carrying, hs13) or 'car' (carried points only)
  links        'far' (hs13: a link cutting a capsule has its far end swung out over it, the rest re-laid) or
               'both' (hj6 fix 2: the link's nearest point pushed out, both ends moved by their weights) or 0
  lwhen        'end' (after the passes, hs13) or 'last' (inside the last pass, after each point's length step)
  rel=1        tip-last release (a carried point stays carried while the next one toward the tip is in front of the
               plane through her shoulders; relb moves that plane, m, + behind)
Everything is gated on the carry (any point carried), so nothing else can change."""
import sys; sys.path[:0] = ["../sv13", "../sv12", "../sv11", "../sv10", "../sv9", "../sv8", "../sv6", "../sv5", "../sv4", "../sv3"]
from hs13 import *
import hs13


def capsules(d, o, sc=1.04):
    """[(a, b, ra, rb)] in the world, as the C# makes them (ends rest-space on spine_03, radii + margin, x scale)."""
    mg = o.get("marg", 0.035)
    rA = (o.get("RA", 0.045) + mg) * sc; rB = (o.get("RB", 0.085) + mg) * sc
    (a1, b1), (a2, b2) = caps(d, sc)
    cs = [(a1, b1, rA, rB), (a2, b2, rA, rB)]
    if o.get("slope") is not None:
        ex = nz(d["across"][3]); ez = -nz(d["back"][3]); ey = np.cross(ez, ex); R = np.c_[ex, ey, ez]; a3 = d["at"][3]
        w = lambda p: a3 + R @ ((p - A3) * sc); S = np.array(o["slope"]); m_ = np.array([-1, 1, 1]); rs = (o.get("RS", 0.035) + mg) * sc
        cs += [(w(S), w(CA), rs, rA), (w(S * m_), w(CA * m_), rs, rA)]
    return cs


def cpush(p, cs):
    """out of each tapered capsule the nearest way (the axis point by plain projection, clamped; its radius there)"""
    for a, b, ra, rb in cs:
        ab = b - a; L2 = ab @ ab; t = min(1.0, max(0.0, float((p - a) @ ab / L2))) if L2 > 1e-12 else 0.0
        c = a + ab * t; r = ra + (rb - ra) * t; off = p - c; L = math.sqrt(off @ off)
        if L < r: p = c + (off / L if L > 1e-9 else np.array([0.0, 1.0, 0.0])) * r
    return p


def seg_seg(p, q, a, b):
    """closest points of segments pq and ab: (s on pq, t on ab), clamped (Ericson 5.1.9)"""
    d1 = q - p; d2 = b - a; r = p - a; A = d1 @ d1; E = d2 @ d2; F = d2 @ r
    if A <= 1e-12 and E <= 1e-12: return 0.0, 0.0
    if A <= 1e-12: return 0.0, min(1.0, max(0.0, F / E))
    C = d1 @ r
    if E <= 1e-12: return min(1.0, max(0.0, -C / A)), 0.0
    B = d1 @ d2; den = A * E - B * B
    s = min(1.0, max(0.0, (B * F - C * E) / den)) if den > 1e-12 else 0.0
    t = (B * s + F) / E
    if t < 0: t = 0.0; s = min(1.0, max(0.0, -C / A))
    elif t > 1: t = 1.0; s = min(1.0, max(0.0, (B - C) / A))
    return s, t


def link_far(dr, link, cs, n=40, lit=2):
    """hs13's link pass: the deepest of n+1 samples of each link (2..7) in a capsule; the far end swung out over it."""
    for it in range(lit):
        for i in range(2, 8):
            for a, b, ra, rb in cs:
                ab = b - a; L2 = ab @ ab; best = None
                for s_ in np.linspace(0, 1, n + 1):
                    x = dr[i - 1] + (dr[i] - dr[i - 1]) * s_
                    t = min(1.0, max(0.0, float((x - a) @ ab / L2)))
                    c = a + ab * t; dd = np.linalg.norm(x - c)
                    if best is None or dd < best[0]: best = (dd, s_, x, c, t)
                dd, s_, x, c, t = best; rr = ra + (rb - ra) * t
                if dd >= rr or s_ < 0.05: continue
                q = dr[i] + nz(x - c) * (rr - dd) / s_
                dr[i] = dr[i - 1] + nz(q - dr[i - 1]) * link[i]
                for j in range(i + 1, 8): dr[j] = dr[j - 1] + nz(dr[j] - dr[j - 1]) * link[j]
    return dr


def link_both(dr, cs, lit=2, i0=1):
    """hj6 fix 2: each link's nearest point to each capsule's axis pushed out; both ends move by their weights (the root
    is pinned)."""
    for it in range(lit):
        for i in range(i0, 8):
            for a, b, ra, rb in cs:
                s_, t = seg_seg(dr[i - 1], dr[i], a, b)
                x = dr[i - 1] + (dr[i] - dr[i - 1]) * s_; c = a + (b - a) * t; r = ra + (rb - ra) * t
                off = x - c; L = math.sqrt(off @ off)
                if L >= r: continue
                n = off / L if L > 1e-9 else np.array([0.0, 1.0, 0.0]); dep = r - L
                w0 = 0.0 if i == 1 else (1 - s_); w1 = s_; den = w0 * w0 + w1 * w1
                if den < 1e-9: continue
                dr[i - 1] = dr[i - 1] + n * dep * w0 / den; dr[i] = dr[i] + n * dep * w1 / den
    return dr


def frame14(s, d):
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
    rdg = bool(o.get("ridge")) and s.style != "long"
    cs = capsules(d, o) if rdg else []
    s.capon = False
    if first or s.w <= 0 or s.dr is None: s.dr = x.copy()
    else:
        dr = s.dr + (tg[0] - s.rootT); dr[0] = tg[0]
        armed = o["rcarry"] and s.full and upright > o["rlo"] and d["head"][0][1] - d["ground"] > o["rh"] and (s.style != "long" or not o["rhead"])
        bk = d["back"][1]; bk = nz(bk - (bk @ upax) * upax); ac = np.cross(upax, bk)
        shm = (at[11] + at[13]) / 2
        def polar(p):
            r = p - neck; return r @ upax, r @ ac, r @ bk, math.hypot(r @ ac, r @ bk)
        thmax = math.pi - (math.pi - math.radians(o["rto"])) * float(smooth(o["rlo"], o["rhi"], upright))
        stepmax = math.pi * dt / o["rtime"]
        if armed:
            if s.side == 0:
                sa = sum(polar(dr[i])[1] for i in range(1, 8) if polar(dr[i])[2] < -o["rfront"] and polar(dr[i])[0] < o["rtop"])
                s.side = 1 if sa >= 0 else -1
            for i in range(1, 8):
                hg, a, b, rho = polar(dr[i])
                if rho < o["rmin"]: continue
                th = math.atan2(s.side * a, b)
                if not s.rnd[i] and b < -o["rfront"] and hg < o["rtop"]: s.rnd[i] = True
                if not s.rnd[i]: continue
                if th < -math.pi / 2: th += 2 * math.pi
                if th <= math.radians(o["rto"]) + 1e-3:
                    if o.get("rel") and i < 7 and (dr[i + 1] - shm) @ bk < o.get("relb", 0.0): continue
                    s.rnd[i] = False
        on = rdg and s.rnd.any()
        s.capon = on
        K = o["K"]
        for k in range(K):
            for i in range(1, 8):
                came = dr[i].copy(); dr[i][1] -= o["step"]
                dr[i] = dr[i - 1] + nz(dr[i] - dr[i - 1]) * link[i]
                dr[i] = s.rcollide(d, dr[i], upax) if s.rnd[i] and o.get("rrad") else s.dcollide(d, dr[i], came)
                if on and (s.rnd[i] or o.get("cpts", "all") == "all"): dr[i] = cpush(dr[i], cs)
                dr[i][1] = max(dr[i][1], floor)
                if armed and s.rnd[i] and o.get("rin"):
                    hg, a, b, rho = polar(dr[i]); th = math.atan2(s.side * a, b)
                    if th < -math.pi / 2: th += 2 * math.pi
                    if th > thmax: dr[i] = neck + rotab(dr[i] - neck, upax, -s.side * min(th - thmax, stepmax / K))
            if on and o.get("links") and o.get("lwhen", "end") == "each":
                dr = link_far(dr, link, cs, o.get("ln", 40), o.get("lit", 2)) if o["links"] == "far" else link_both(dr, cs, o.get("lit", 2))
        if on and o.get("links") and o.get("lwhen", "end") == "end" and s.w >= 1 - 1e-4:
            dr = link_far(dr, link, cs, o.get("ln", 40), o.get("lit", 2)) if o["links"] == "far" else link_both(dr, cs, o.get("lit", 2))
        if on and o.get("vcap"):
            # (vcap: each drape point moves at most this far a frame against its root's carry while carrying)
            prev = s.dr + (tg[0] - s.rootT)
            for i in range(1, 8):
                dv = dr[i] - prev[i]; L = np.linalg.norm(dv)
                if L > o["vcap"]: dr[i] = prev[i] + dv * (o["vcap"] / L)
        s.dr = dr
    s.rootT = tg[0].copy()
    show = s.dr
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


M8.frame = frame14
