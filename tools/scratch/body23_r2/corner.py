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


def metrics(P, S, E, W, ppm, outer=True):
    """the corner measures of a closed 2D contour P (px) round the joint E, S up the upper arm, W down the forearm"""
    u = (S - E) / np.linalg.norm(S - E); v = (W - E) / np.linalg.norm(W - E)
    o = -(u + v); o /= np.linalg.norm(o)
    if not outer:
        o = -o
    rel = P - E
    side = rel @ o
    nu = np.array([-u[1], u[0]]); nu = nu if nu @ o > 0 else -nu
    nv = np.array([-v[1], v[0]]); nv = nv if nv @ o > 0 else -nv
    au, av = rel @ u, rel @ v
    du, dv = rel @ nu, rel @ nv
    R = 90 * ppm
    sel = (((au > -5) & (au < R) & (du > 4)) | ((av > -5) & (av < R) & (dv > 4)) | ((side > 0) & (np.linalg.norm(rel, axis=1) < 60 * ppm)))
    if sel.sum() < 10:
        return None
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
    if (Q[0] - E) @ u < (Q[-1] - E) @ u:
        Q = Q[::-1]
    d = np.diff(Q, axis=0)
    sl = np.linalg.norm(d, axis=1)
    s = np.r_[0, np.cumsum(sl)]
    ang = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
    rq = Q - E
    i0 = np.nonzero(rq @ u >= 25 * ppm)[0]; i0 = i0[-1] if len(i0) else 0
    i1 = np.nonzero(rq @ v >= 25 * ppm)[0]; i1 = i1[0] if len(i1) else len(Q) - 1
    if i1 <= i0 + 3:
        return None
    a = ang[i0:i1]; ss_ = s[i0:i1]
    turn = a - a[0]
    tot = turn[-1]
    if abs(tot) < 1e-3:
        return None
    q = np.maximum.accumulate(np.clip(turn / tot, 0, 1)) + np.arange(len(turn)) * 1e-9
    s05, s10, s50, s90 = np.interp([0.05, 0.1, 0.5, 0.9], q, ss_)
    r_eff = (s90 - s10) / (0.8 * abs(tot))
    apex = Q[i0 + int(np.argmin(np.abs(ss_ - s50)))]
    j5 = i0 + int(np.argmin(np.abs(ss_ - s05)))
    best = 0.0
    up = Q[:j5 + 1][::-1]
    for k in range(5, len(up)):
        seg = up[:k + 1]
        cen = seg.mean(0)
        _, _, vt = np.linalg.svd(seg - cen)
        if np.abs((seg - cen) @ vt[1]).max() > 0.6:
            break
        best = np.linalg.norm(seg[-1] - seg[0])
    return dict(r_eff=float(r_eff), turn=float(np.degrees(abs(tot))), flat_mm=float(best / ppm), flat_px=float(best),
                apex=apex, Q=Q, ppm=float(ppm), s_core=float(s90 - s10))


def corner(fr, g, sd, half=120, ss=SSC, outer=True, sm_px=1.5):
    S, E, W = (c.jscreen(fr, n + "_" + sd) for n in ("upperarm", "lowerarm", "hand"))
    box = (int(E[0] - half), int(E[1] - half), int(E[0] + half), int(E[1] + half))
    m, ids = arm_mask(fr, g, sd, box, ss)
    P = contour(m)
    if P is None:
        return None
    P = (P + 0.5) / ss + [box[0], box[1]]
    P = _smooth_closed(P, max(1, int(round(sm_px * ss))))
    k = metrics(P, S, E, W, c.sh.px_per_mm(fr, sd), outer)
    if k:
        k["box"] = box
    return k


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
