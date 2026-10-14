"""hs8.py: solver 8: hs6's M6 (C# at ef8e3971) plus the round carry: once she has been fully down and is rising (spine
up-dot past rlo), drape points in front of her neck and chest (behind-angle past 90 deg about her spine line through the
neck) are swung round her near side about that line, toward the back (at most rto from it), no faster than 180 deg per
rtime; the down weight is held at 1 while any point is being carried. Head-tied chains only (rhead)."""
import sys; sys.path[:0] = ["../sv6", "../sv5", "../sv4", "../sv3"]
from hs6 import *
ROUND = dict(rlo=0.45, rhi=0.85, rto=60.0, rtime=0.25, rmin=0.02, rhold=True, rhead=True, rcarry=True, rh=0.7, rfront=0.015, rtop=0.12)
def rotab(v, ax, ang):
    c, s = math.cos(ang), math.sin(ang)
    return v * c + np.cross(ax, v) * s + ax * (ax @ v) * (1 - c)
class M8(M6):
    def rcollide(s, d, p, upax, sc=1.04):
        for b in range(11):
            r = d["r"][b] * sc; w = d["across"][b]; ww = w @ w; at = d["at"][b]
            c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
            off = p - c
            if off @ off >= r * r: continue
            u = upax * (off @ upax); fl = off - u
            if fl @ fl < 1e-10 or u @ u >= r * r: continue
            p = c + u + nz(fl) * math.sqrt(r * r - u @ u)
        return p
    def dcollide(s, d, p, came, sc=1.04, nb=None, flip=0.0):
        for b in range(len(d["r"]) if nb is None else nb):
            r = d["r"][b] * sc; w = d["across"][b]; ww = w @ w; at = d["at"][b]
            c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
            off = p - c
            if off @ off >= r * r: continue
            bk = d["back"][b]
            if d["behind"][b] and off @ bk < 0 and (not ((came - c) @ bk < 0) or -(off @ bk) < flip): off = off - 2 * (off @ bk) * bk
            n = nz(off) if off @ off > 1e-10 else bk
            p = c + n * r
        return p
    def __init__(s, fr, style, **o):
        M6.__init__(s, fr, style, **o)
        for k, v in ROUND.items(): s.o.setdefault(k, v)
        s.rth = np.zeros(8); s.style = style; s.full = False; s.side = 0; s.rnd = np.zeros(8, bool); s.rlog = []
    def frame(s, d):
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
        if first or s.w <= 0 or s.dr is None: s.dr = x.copy()
        else:
            dr = s.dr + (tg[0] - s.rootT); dr[0] = tg[0]
            upax = nz(neck - at[10])
            armed = o["rcarry"] and s.full and upright > o["rlo"] and d["head"][0][1] - d["ground"] > o["rh"] and (s.style != "long" or not o["rhead"])
            if armed:
                bk = d["back"][1]; bk = nz(bk - (bk @ upax) * upax); ac = np.cross(upax, bk)
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
                    if th <= math.radians(o["rto"]) + 1e-3: s.rnd[i] = False; continue
                    s.rth[i] = th
            for k in range(o["K"]):
                for i in range(1, 8):
                    came = dr[i].copy(); dr[i][1] -= o["step"]
                    dirn = nz(dr[i] - dr[i - 1])
                    dr[i] = dr[i - 1] + dirn * link[i]
                    dr[i] = s.rcollide(d, dr[i], upax) if s.rnd[i] and o.get("rrad") else s.dcollide(d, dr[i], came)
                    dr[i][1] = max(dr[i][1], floor)
                    if armed and s.rnd[i] and o.get("rin"):
                        hg, a, b, rho = polar(dr[i]); th = math.atan2(s.side * a, b)
                        if th < -math.pi / 2: th += 2 * math.pi
                        if th > thmax: dr[i] = neck + rotab(dr[i] - neck, upax, -s.side * min(th - thmax, stepmax / o["K"]))
            s.dr = dr
        s.rootT = tg[0].copy()
        out = x + (s.dr - x) * s.w
        if s.w >= 1 - 1e-4:
            steps = max(1, int(math.ceil(dt * 120 - 1e-3)))
            rs = (tg[0] - s.prevRoot) / steps if hasattr(s, "prevRoot") else 0
            s.x[:] = s.dr; s.xp[:] = s.dr - rs
        s.prevRoot = tg[0].copy()
        s.wlog.append(s.w); s.swing.append(x); s.drape.append(s.dr.copy()); s.rlog.append(s.rnd.copy())
        return out
def sim8(fr, style, **o):
    m = M8(fr, style, **o)
    xs = [m.frame(d).copy() for d in fr]
    return xs, m
