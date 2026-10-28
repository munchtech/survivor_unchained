"""Body 23 r2: the bent elbow's outer corner in a game frame (harness posing, sub-pixel contour of her arm's region).
r_eff: the corner's effective radius (px at 1:1) = arc length over which the middle 80% of the outline's turn happens /
that turn (rad): a circular fillet gives its radius, a point between flat planes a small number.
flat_mm: the upper arm's back outline, straight within 0.6 px from the corner's start (5% of the turn) up the arm (mm).
crease: the inner side's turn (same measure, px) for reference."""
import numpy as np, cv2
import r2lib as c

SSC = 4


def arm_mask(fr, g, sd, box, ss=SSC):
    ids = c.h.raster(g["xy"], g["z"], g["I"], g["front"], box, ss)
    tsd, tt, _ = fr.tri_attr(g["I"])
    want = 1 if sd == "l" else 2
    ok = np.zeros(len(g["I"]) + 1, bool)
    ok[:-1] = (tsd == want) & (tt > 0.45) & (tt < 1.7)
    m = ok[np.where(ids >= 0, ids, len(g["I"]))]
    return m, ids


def contour(mask):
    m = mask.astype(np.uint8)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return None
    cc = max(cs, key=len)[:, 0, :].astype(float)
    return cc


def _smooth_closed(P, k):
    n = len(P)
    if k <= 0:
        return P
    ker = np.ones(2 * k + 1) / (2 * k + 1)
    Q = np.vstack([P[-k:], P, P[:k]])
    return np.c_[np.convolve(Q[:, 0], ker, "valid"), np.convolve(Q[:, 1], ker, "valid")]


def corner(fr, g, sd, half=120, ss=SSC, outer=True, sm_px=1.5):
    S, E, W = (c.jscreen(fr, n + "_" + sd) for n in ("upperarm", "lowerarm", "hand"))
    box = (int(E[0] - half), int(E[1] - half), int(E[0] + half), int(E[1] + half))
    m, ids = arm_mask(fr, g, sd, box, ss)
    P = contour(m)
    if P is None:
        return None
    P = (P + 0.5) / ss + [box[0], box[1]]                 # screen px
    P = _smooth_closed(P, max(1, int(round(sm_px * ss))))
    u = (S - E) / np.linalg.norm(S - E); v = (W - E) / np.linalg.norm(W - E)
    o = -(u + v); o /= np.linalg.norm(o)
    if not outer:
        o = -o
    # the outer side's run: contour points within 75 px of E on o's side of the line through E across the bend
    rel = P - E
    side = rel @ o
    nu = np.array([-u[1], u[0]]); nu = nu if nu @ o > 0 else -nu
    nv = np.array([-v[1], v[0]]); nv = nv if nv @ o > 0 else -nv
    au, av = rel @ u, rel @ v
    du, dv = rel @ nu, rel @ nv
    # points on the upper arm's outer flank (au in 0..90, du > 0) or the forearm's (av in 0..90, dv > 0), or the corner
    sel = (((au > -5) & (au < 90) & (du > 4)) | ((av > -5) & (av < 90) & (dv > 4)) | ((side > 0) & (np.linalg.norm(rel, axis=1) < 60)))
    if sel.sum() < 10:
        return None
    # the longest consecutive run of selected contour points (closed contour)
    idx = np.nonzero(sel)[0]
    n = len(P)
    runs, cur = [], [idx[0]]
    for a, b in zip(idx[:-1], idx[1:]):
        if b == a + 1:
            cur.append(b)
        else:
            runs.append(cur); cur = [b]
    runs.append(cur)
    if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] == n - 1:
        runs[0] = runs[-1] + runs[0]; runs.pop()
    run = max(runs, key=len)
    Q = P[run]
    # orient: from the upper arm to the forearm
    if (Q[0] - E) @ u < (Q[-1] - E) @ u:
        Q = Q[::-1]
    d = np.diff(Q, axis=0)
    sl = np.linalg.norm(d, axis=1)
    s = np.r_[0, np.cumsum(sl)]
    ang = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
    # restrict to the stretch between the upper arm's flank (au >= 25) and the forearm's (av >= 25)
    rq = Q - E
    i0 = np.nonzero(rq @ u >= 25)[0]; i0 = i0[-1] if len(i0) else 0
    i1 = np.nonzero(rq @ v >= 25)[0]; i1 = i1[0] if len(i1) else len(Q) - 1
    if i1 <= i0 + 3:
        return None
    a = ang[i0:i1]; ss_ = s[i0:i1]
    turn = a - a[0]
    tot = turn[-1]
    if abs(tot) < 1e-3:
        return None
    fr_ = turn / tot
    # monotone envelope for the quantiles
    q = np.maximum.accumulate(np.clip(fr_, 0, 1))
    s10, s50, s90 = np.interp([0.1, 0.5, 0.9], q + np.arange(len(q)) * 1e-9, ss_)
    s05 = np.interp(0.05, q + np.arange(len(q)) * 1e-9, ss_)
    r_eff = (s90 - s10) / (0.8 * abs(tot))
    apex = Q[i0 + int(np.argmin(np.abs(ss_ - s50)))]
    # the flat: from the 5% point up the upper arm, the longest stretch straight within 0.6 px
    j5 = i0 + int(np.argmin(np.abs(ss_ - s05)))
    best = 0.0
    up = Q[:j5 + 1][::-1]                                   # from the corner's start up the arm
    for k in range(5, len(up)):
        seg = up[:k + 1]
        cen = seg.mean(0)
        _, _, vt = np.linalg.svd(seg - cen)
        dev = np.abs((seg - cen) @ vt[1]).max()
        if dev > 0.6:
            break
        best = np.linalg.norm(seg[-1] - seg[0])
    ppm = c.sh.px_per_mm(fr, sd)
    return dict(r_eff=float(r_eff), turn=float(np.degrees(abs(tot))), flat_mm=float(best / ppm), flat_px=float(best),
                apex=apex, Q=Q, box=box, ppm=float(ppm), s_core=float(s90 - s10))


if __name__ == "__main__":
    import sys
    bodies = sys.argv[1:] or [c.A_GLB]
    for f, sd in (("w_m80", "l"), ("rL90_m45", "l"), ("s_p45", "r"), ("w_m45", "l"), ("look_f", "l")):
        fr = c.frame(f)
        row = []
        for bp in bodies:
            g = fr.geom(c.h.GlbBody(bp) if bp != "A" else c.MemBody())
            k = corner(fr, g, sd)
            kin = corner(fr, g, sd, outer=False)
            row.append("r_eff %5.1f px turn %5.1f flat %4.1f mm | inner r %5.1f" % (k["r_eff"], k["turn"], k["flat_mm"], kin["r_eff"] if kin else np.nan) if k else "none")
        print("%-9s %s" % (f, " || ".join(row)))
