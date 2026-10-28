"""Body 23 r1a: the front axillary fold as a convex ROLL along the pit's front rim (the loop map's front_fold cuts),
authored in the hanging pose(s): each vertex near the rim moves along its posed normal by a rounded profile across
the rim (H mm at the crest, half-width W mm, the crest shifted `shift` mm toward the opening), carried to rest by
its inverse blended skin matrix, least squares over the side's frames. A roll is convex across and long along the
rim, so its points diverge (no bunching into a knot, as the pit's old vertices pulled into a closing did)."""
import json
import numpy as np
import k
import chart as c
import pitviz

FR_SIDE = {"r": ["w_p45", "look_f"], "l": ["w_m45", "look_f", "rL90_m45"]}
C1 = dict(H=6.0, W=16.0, shift=3.0, ends=12.0)


def bw(x):
    x = np.clip(1 - np.asarray(x, float) ** 2, 0, None)
    return x * x


def seg_dist(Q, P):
    """distance from points Q to the polyline P, and the arc parameter (0..1) of the nearest point"""
    best = np.full(len(Q), np.inf); tt = np.zeros(len(Q))
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        ab = b - a
        u = np.clip(((Q - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        d = np.linalg.norm(Q - (a + u[:, None] * ab), axis=1)
        m = d < best
        best[m] = d[m]; tt[m] = (L[i] + u[m] * np.linalg.norm(ab)) / L[-1]
    return best, tt, L[-1]


def solve(P, body=None, sides="lr", frames=FR_SIDE, smooth=2, log=print):
    bs = k.base()
    body = body or k.Body()
    dU = np.zeros((bs.nU, 3))
    for sd in sides:
        sg = 1 if sd == "l" else -1
        ii0 = pitviz.cut_ids(sd, "front_fold", "+0")
        iin = pitviz.cut_ids(sd, "front_fold", "+4")    # the opening's side
        mine = bs.U[:, 0] * sg > 0.02
        acc = np.zeros((bs.nU, 3)); cnt = np.zeros(bs.nU)
        for f in frames[sd]:
            fr = k.frame(f)
            X = k.posed_welded(fr, body)
            ok = np.isfinite(X).all(1) & mine
            Xs = np.where(ok[:, None], X, 0)
            N = k.vn(Xs, bs.F)
            # the crest: the +0 cut shifted toward the opening (+4 side)
            from scipy.spatial import cKDTree
            _, j = cKDTree(Xs[iin]).query(Xs[ii0])
            tow = Xs[iin][j] - Xs[ii0]
            tow /= np.maximum(np.linalg.norm(tow, axis=1, keepdims=True), 1e-9)
            crest = Xs[ii0] + tow * P["shift"] * 1e-3
            near = ok & (np.linalg.norm(Xs - Xs[ii0].mean(0), axis=1) < 0.12)
            d, t, Ltot = seg_dist(Xs[near], crest)
            dmm = d * 1000
            # fade at the cut's ends (ends mm)
            e = np.minimum(t, 1 - t) * Ltot * 1000
            fe = np.clip(e / P["ends"], 0, 1)
            h = P["H"] * bw(dmm / P["W"]) * (fe * fe * (3 - 2 * fe))
            dp = np.zeros((bs.nU, 3))
            dp[near] = N[near] * (h * 1e-3)[:, None]
            Bm, _ = k.welded_B(fr)
            Bi = np.linalg.inv(np.where(ok[:, None, None], Bm, np.eye(3)))
            dr = np.einsum("nij,nj->ni", Bi, dp)
            acc[ok] += dr[ok]; cnt[ok] += 1
        d = np.where(cnt[:, None] > 0, acc / np.maximum(cnt, 1)[:, None], 0)
        dU[mine] += d[mine]
    A, deg = bs.b.A, bs.b.deg
    for _ in range(smooth):
        dU = 0.5 * dU + 0.5 * (A @ dU) / deg[:, None]
    mv = np.linalg.norm(dU, axis=1) * 1000
    log("fold: %d points > 0.5 mm, max %.1f mm" % ((mv > 0.5).sum(), mv.max()))
    return dU
