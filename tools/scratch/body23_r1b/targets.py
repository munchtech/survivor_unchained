"""C3 step 1: TARGET OUTLINES at 1:1 per judged frame, as an offset Delta (px, + out) on A's silhouette (body vs
background, the harness raster at SS 2), authored per region from anatomy (one reason each):
  cap   the deltoid a TEARDROP: the acromion's top flatter and in (the round ball top cut along its normal), the belly
        kept (look_f: in, never out > +3), the taper from the belly to the insertion V (45% down) a smooth convex line
        (the ledge where the ball met the tube filled), a soft break IN at the V.
  pit   the FRONT AXILLARY FOLD: the pec's lower border rolls from the breast's upper-outer edge into the arm's front, a
        web that fills the pinched notch between arm and chest with a round (a closing, R ~14 mm), capped.
  elbow (bent arms) the olecranon a POINT: the triceps' back line flat (straight) into it, the ulna's border straight out
        of it, the corner's round (radius <= 8 mm) at the apex; the club's swell along the flanks cut back to the lines.
"""
import numpy as np, c3lib as c
from scipy.ndimage import binary_erosion, distance_transform_edt, gaussian_filter, binary_closing, binary_opening
from PIL import Image, ImageDraw
SS = 2
VIS = {"w_p45": "r", "w_m45": "l", "look_f": "rl", "w_m80": "l", "rL90_m45": "l", "s_p45": "r"}   # caps/pits seen
P = dict(top_in=11.0, cap_in=2.0, v_in=4.0, pit_R=14.0, pit_cap=16.0, apex_out=8.0, apex_r=7.0, tri_in=6.0, ul_in=3.0, pt=4.0,
         waist_in=5.0, bic_out=3.0, bic_hi=2.0)


def disk(r):
    r = int(round(r)); y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def base(fr, g, box):
    ids = c.h.raster(g["xy"], g["z"], g["I"], g["front"], box, SS)
    fg = ids >= 0
    sdA = (distance_transform_edt(~fg) - distance_transform_edt(fg)) / SS      # 1x px, + outside
    bd = fg & ~binary_erosion(fg)
    sm = gaussian_filter(sdA, 2.0)
    gy, gx = np.gradient(sm)
    yy, xx = np.nonzero(bd)
    nrm = np.c_[gx[yy, xx], gy[yy, xx]]; nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    p = np.c_[(xx + 0.5) / SS + box[0], (yy + 0.5) / SS + box[1]]
    return dict(ids=ids, fg=fg, sdA=sdA, yy=yy, xx=xx, p=p, n=nrm, box=box)


def smooth01(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def cap_region(fr, sd, B, D, W):
    """the deltoid's outer outline: Delta on A's outer-side boundary points of this arm"""
    J, u, n, Lp = c.sh.arm_axes(fr, sd)
    ppm = c.sh.px_per_mm(fr, sd); k = ppm / 0.9
    p = B["p"]; a = (p - J) @ u; d = (p - J) @ n
    side = (d > 8) & (a > -90) & (a < 0.7 * Lp) & (d < 110)
    if side.sum() < 20:
        return None
    bins = np.arange(-60, int(0.7 * Lp))
    prof = np.full(len(bins), np.nan)
    for i, b0 in enumerate(bins):
        m = side & (a >= b0) & (a < b0 + 1)
        if m.any():
            prof[i] = d[m].max()
    ok = np.isfinite(prof)
    prof = np.interp(bins, bins[ok], prof[ok])
    m = (bins >= -10) & (bins <= 50)
    ac_ = bins[m][np.argmax(prof[m])]; dc = prof[m].max()
    aV = 0.45 * Lp
    dV = np.interp(aV, bins, prof)
    outer = side & (d >= np.interp(a, bins, prof) - 2.5)
    lo, hi = ac_ - 85 * k, ac_ + 4
    w_top = smooth01((a - lo) / (35 * k)) * smooth01((hi - a) / (30 * k))
    dl = -P["top_in"] * k * w_top
    dl += -P["cap_in"] * k * np.exp(-((a - ac_) / 18.0) ** 2) * (a > ac_ - 5)
    sV = (np.interp(aV + 8, bins, prof) - np.interp(aV - 8, bins, prof)) / 16 - 0.10
    t = np.clip((a - ac_) / (aV - ac_), 0, 1); L = aV - ac_
    H = (2 * t**3 - 3 * t**2 + 1) * (dc - P["cap_in"] * k) + (-2 * t**3 + 3 * t**2) * (dV - P["v_in"] * k) + (t**3 - t**2) * sV * L
    dA_here = np.interp(a, bins, prof)
    mid = (a > ac_) & (a <= aV)
    dl = np.where(mid, np.maximum(dl, H - dA_here), dl)
    below = (a > aV)
    dl = np.where(below, -P["v_in"] * k * smooth01(1 - (a - aV) / (40 * k)), dl)
    D[outer] = dl[outer]; W[outer] = 1.0
    return dict(ac=float(ac_), dc=float(dc), aV=float(aV))


def pit_region(fr, sd, B, D, W):
    """the notch between this arm and her chest: filled by a closing (R), its fill capped"""
    J, u, n, Lp = c.sh.arm_axes(fr, sd)
    ppm = c.sh.px_per_mm(fr, sd)
    p = B["p"]; a = (p - J) @ u; d = (p - J) @ n
    win = (a > -20) & (a < 0.55 * Lp) & (d < 5) & (d > -110)
    if win.sum() < 10:
        return None
    R = P["pit_R"] * ppm
    fg = B["fg"]
    yy, xx = B["yy"][win], B["xx"][win]
    y0, y1, x0, x1 = max(yy.min() - 80, 0), yy.max() + 80, max(xx.min() - 80, 0), xx.max() + 80
    sub = fg[y0:y1, x0:x1]
    cl = binary_closing(np.pad(sub, 60, constant_values=False), disk(R * SS))[60:-60, 60:-60]
    sdT = (distance_transform_edt(~cl) - distance_transform_edt(cl)) / SS
    v = -sdT[yy - y0, xx - x0]
    v = np.minimum(v, P["pit_cap"] * ppm / 0.9)
    idx = np.nonzero(win)[0]
    ok = v > 0.3
    D[idx[ok]] = v[ok]; W[idx[ok]] = 1.0
    return dict(R=float(R), fill=float(v.max()))


def elbow_region(fr, sd, B, D, W):
    """the bent elbow's outer corner: straight back lines into a pointed apex (fillet apex_r)"""
    if fr.flex[sd] < 55:
        return None
    ppm = c.sh.px_per_mm(fr, sd); k = ppm / 0.9
    Es, Ss, Ws = (c.jscreen(fr, nm + "_" + sd) for nm in ("lowerarm", "upperarm", "hand"))
    u1 = (Ss - Es) / np.linalg.norm(Ss - Es); u2 = (Ws - Es) / np.linalg.norm(Ws - Es)
    bis = u1 + u2; bis /= np.linalg.norm(bis); out = -bis
    p = B["p"]; rel = p - Es; r = np.linalg.norm(rel, axis=1)
    pr = np.array([-out[1], out[0]])
    th = np.degrees(np.arctan2(rel @ pr, rel @ out))

    def backline(uu, d0, d1):
        """A's back contour (outer side of this bone) between d0 and d1 px along it: a fitted line (point, dir)"""
        nn = np.array([-uu[1], uu[0]]); nn = nn if nn @ out > 0 else -nn
        al = rel @ uu; of = rel @ nn
        pts = []
        for x in np.arange(d0, d1, 2.0):
            m = (np.abs(al - x) < 1.5) & (of > 0) & (of < 90)
            if m.any():
                pts.append(Es + uu * x + nn * of[m].max())
        if len(pts) < 5:
            return None
        Q = np.array(pts); ctr = Q.mean(0); dv = np.linalg.svd(Q - ctr)[2][0]
        return ctr, dv, nn
    Lu, Lf = backline(u1, 70 * ppm, 120 * ppm), backline(u2, 50 * ppm, 110 * ppm)
    if Lu is None or Lf is None:
        return None
    # the triceps' line pulled in (a slimmer arm above the elbow: the tendon's flat), the ulna's line as it is
    cu, du, nu = Lu; cf, df, nf = Lf
    cu = cu - nu * P["tri_in"] * ppm
    cf = cf - nf * P["ul_in"] * ppm
    # their intersection
    M_ = np.c_[du, -df]; st = np.linalg.solve(M_, cf - cu); Cl = cu + du * st[0]
    r0 = 20.0
    fg_ = B["fg"]; bx = B["box"]
    for rr_ in np.arange(10.0, 120.0, 0.5):
        q = Es + out * rr_; xi, yi = int((q[0] - bx[0]) * SS), int((q[1] - bx[1]) * SS)
        if 0 <= yi < fg_.shape[0] and 0 <= xi < fg_.shape[1] and fg_[yi, xi]:
            r0 = rr_
    dC = Cl - Es; rC = np.linalg.norm(dC)
    rmax = r0 + P["apex_out"] * ppm
    C = Es + dC / rC * min(rC + P["pt"] * ppm, rmax)      # the olecranon proud of the lines' meeting
    # the flank points on the lines, far enough out that the corner owns the whole round
    Pu = cu + du * ((Es + u1 * 75 * ppm - cu) @ du)
    Pf = cf + df * ((Es + u2 * 75 * ppm - cf) @ df)
    fg = B["fg"]; box = B["box"]
    hh, ww = fg.shape

    def S(q):
        return ((q[0] - box[0]) * SS, (q[1] - box[1]) * SS)
    im = Image.new("L", (ww, hh), 0); ImageDraw.Draw(im).polygon([S(Es), S(Pu), S(C), S(Pf)], fill=1)
    wedge = np.asarray(im).astype(bool)
    thu = np.degrees(np.arctan2((Pu - Es) @ pr, (Pu - Es) @ out)); thf = np.degrees(np.arctan2((Pf - Es) @ pr, (Pf - Es) @ out))
    lo_, hi_ = min(thu, thf), max(thu, thf)
    yy, xx = np.mgrid[0:hh, 0:ww]
    gx = (xx + 0.5) / SS + box[0] - Es[0]; gy = (yy + 0.5) / SS + box[1] - Es[1]
    gth = np.degrees(np.arctan2(gx * pr[0] + gy * pr[1], gx * out[0] + gy * out[1]))
    own = (gth > lo_) & (gth < hi_) & (np.hypot(gx, gy) < 140)
    T = np.where(own, wedge, fg)
    rr = P["apex_r"] * ppm * SS
    T2 = binary_opening(np.pad(T, 40), disk(rr))[40:-40, 40:-40]
    T = np.where(own, T2, T)
    sdT = (distance_transform_edt(~T) - distance_transform_edt(T)) / SS
    win = (th > lo_ + 2) & (th < hi_ - 2) & (r < 130)
    v = -sdT[B["yy"][win], B["xx"][win]]
    idx = np.nonzero(win)[0]
    D[idx] = v; W[idx] = 1.0
    return dict(r0=float(r0), C=C.tolist(), Pu=Pu.tolist(), Pf=Pf.tolist(), th=(float(lo_), float(hi_)), rC=float(rC))


def waist_region(fr, sd, B, D, W):
    """(bent arms) the upper arm's inner (front) contour: in at the waist just above the crease (the biceps' tendon),
    out at the flexed belly ~65% down (the oval), a little in above it (a slimmer upper arm)"""
    if fr.flex[sd] < 55:
        return None
    J, u, n, Lp = c.sh.arm_axes(fr, sd)
    ppm = c.sh.px_per_mm(fr, sd)
    p = B["p"]; a = (p - J) @ u; d = (p - J) @ n
    t = a / Lp
    inner = (d < -8) & (d > -90) & (t > 0.3) & (t < 0.97)
    if inner.sum() < 20:
        return None
    # only the contour that faces the background on the arm's inner side (the outermost per bin)
    bins = np.arange(int(0.3 * Lp), int(0.97 * Lp))
    prof = np.full(len(bins), np.nan)
    for i, b0 in enumerate(bins):
        m = inner & (a >= b0) & (a < b0 + 1)
        if m.any():
            prof[i] = -d[m].min()
    ok = np.isfinite(prof)
    if ok.sum() < 20:
        return None
    sel = inner & (-d >= np.interp(a, bins[ok], prof[ok]) - 2.5)
    g_ = lambda x, c0, w: np.exp(-((x - c0) / w) ** 2)
    v = (-P["waist_in"] * g_(t, 0.90, 0.06) + P["bic_out"] * g_(t, 0.66, 0.08) - P["bic_hi"] * g_(t, 0.42, 0.07)) * ppm
    D[sel] = v[sel]; W[sel] = 1.0
    return dict(n=int(sel.sum()))


def build(fr, g=None, box=None):
    """per A boundary pixel: Delta (px, + out), weight (0: keep at A)"""
    g = g or fr.geom(c.MemBody()); box = box or c.box_of(fr)
    B = base(fr, g, box)
    D = np.zeros(len(B["p"])); W = np.zeros(len(B["p"]))
    info = {}
    for sd in VIS.get(fr.name, ""):
        info["cap_" + sd] = cap_region(fr, sd, B, D, W)
    for sd in VIS.get(fr.name, ""):
        info["pit_" + sd] = pit_region(fr, sd, B, D, W)
    for sd in "lr":
        info["waist_" + sd] = waist_region(fr, sd, B, D, W)
    for sd in "lr":
        info["elbow_" + sd] = elbow_region(fr, sd, B, D, W)
    B["D"], B["W"], B["info"] = D, W, info
    return B
