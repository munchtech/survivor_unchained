"""Body 23 r1a: her elbow's bend shapes authored IN THE GAME FRAMES that show the bend (left: w_m80 pose 112.5 deg,
look_f 120, rL90 96; right: s_p45 76): a field on the posed elbow chart (z mm along the arm about the elbow joint, -
up the humerus; ang 0 front 90 out 180 back -90 in), along the posed normal; carried to bind space by each vertex's
inverse blended skin matrix; elbow_psd90/135 solved per vertex by least squares over the frames with the weights
ElbowPsd.cs gives there (flex.py); elbow_psd45 left empty (a straight arm is unchanged).
Fields: pt (the olecranon point proud), plate/ulna (the corner's round cut back above and below it: the triceps
tendon's flat plate straight into the point, the ulna's border), sides (the club's sides at the joint), slim (the
upper arm's inner/outer sides above the elbow), bic (the flexed biceps oval), br (the thumb-side wad above and below
the crease), crease (a crisp inner line)."""
import numpy as np
import k
import chart as c

FR = {"l": ["w_m80", "look_f", "rL90_m45"], "r": ["s_p45"]}
C1 = dict(pt=4.0, plate=4.0, ulna=2.5, sides=3.0, slim=2.5, bic=3.5, br=3.5, crease=2.0)


def bw(x):
    x = np.clip(1 - np.asarray(x, float) ** 2, 0, None)
    return x * x


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def ss(x):
    t = np.clip(x, 0, 1)
    return t * t * (3 - 2 * t)


def chart(fr, sd, X):
    FU, FF = c.posed_frame(fr, sd, "U"), c.posed_frame(fr, sd, "F")
    sU, pU, rU = c.coords(X, FU)
    sF, pF, rF = c.coords(X, FF)
    zU = sU - FU["L"]
    bf = ss((sF + 12.0) / 24.0)
    z = (1 - bf) * zU + bf * sF
    a = np.degrees(np.arctan2((1 - bf) * np.sin(np.radians(pU)) + bf * np.sin(np.radians(pF)),
                              (1 - bf) * np.cos(np.radians(pU)) + bf * np.cos(np.radians(pF))))
    r = (1 - bf) * rU + bf * rF
    return z, a, r


def field(z, a, P):
    back = wrap(a - 180)
    d = P["pt"] * bw(z / 11.0) * bw(back / 26.0)
    d -= P["plate"] * bw((z + 36.0) / 26.0) * bw(back / 65.0)
    d -= P["ulna"] * bw((z - 30.0) / 20.0) * bw(back / 60.0)
    d -= P["sides"] * bw(z / 22.0) * (bw((np.abs(back) - 70.0) / 30.0))
    d -= P["slim"] * bw((z + 75.0) / 50.0) * (bw(wrap(a - 90) / 40.0) + bw(wrap(a + 90) / 40.0))
    d += P["bic"] * bw((z + 70.0) / 38.0) * bw(wrap(a) / 55.0)
    d += P["br"] * bw((z - 15.0) / 40.0) * bw(wrap(a - 60) / 45.0)
    d -= P["crease"] * bw(z / 7.0) * bw(wrap(a) / 50.0)
    return d


def solve(P, body=None, log=print, smooth=2):
    bs = k.base()
    body = body or k.Body()
    A, deg = bs.b.A, bs.b.deg
    out = {}
    for sd in "lr":
        sg = 1 if sd == "l" else -1
        mine = (bs.U[:, 0] * sg > 0.05) & (bs.b.arm_w(sd) > 0.3)
        rows = []
        for f in FR[sd]:
            fr = k.frame(f)
            X = k.posed_welded(fr, body)
            ok = np.isfinite(X).all(1) & mine
            Xs = np.where(ok[:, None], X, 0)
            N = k.vn(Xs, bs.F)
            z, a, r = chart(fr, sd, Xs)
            dmm = np.where(ok & (r < 70), field(z, a, P), 0.0)
            dp = N * (dmm * 1e-3)[:, None]
            Bm, _ = k.welded_B(fr)
            Bi = np.linalg.inv(np.where(ok[:, None, None], Bm, np.eye(3)))
            dr = np.einsum("nij,nj->ni", Bi, dp)
            for _ in range(smooth):
                dr = 0.5 * dr + 0.5 * (A @ dr) / deg[:, None]
            w = fr.psdw
            rows.append((w.get("elbow_psd90_" + sd, 0.0), w.get("elbow_psd135_" + sd, 0.0), dr))
        W = np.array([[r[0], r[1]] for r in rows])
        if len(rows) == 1:
            D90 = rows[0][2] / max(rows[0][0] + rows[0][1], 1e-6)
            D135 = D90.copy()
        else:
            Rm = np.stack([r[2] for r in rows], 0)               # (nf, nU, 3)
            Mi = np.linalg.pinv(W)                               # (2, nf)
            D = np.einsum("kf,fnc->knc", Mi, Rm)
            D90, D135 = D[0], D[1]
        for n, D in (("elbow_psd90_" + sd, D90), ("elbow_psd135_" + sd, D135)):
            D = np.where(mine[:, None], D, 0)
            out[n] = D
        log("elbow %s: weights %s, most %.1f / %.1f mm" % (sd, np.round(W, 2).tolist(), np.linalg.norm(D90, axis=1).max() * 1000,
                                                          np.linalg.norm(D135, axis=1).max() * 1000))
    return out
