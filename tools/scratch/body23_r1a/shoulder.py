"""Body 23 r1a: her shoulder's form authored IN THE POSES that show it (the hanging right arm at w_p45/look_f, the
akimbo left at w_m45/look_f/rL90): anatomical fields on the POSED upper-arm chart (s mm down the humerus line from
the shoulder joint, phi 0 front 90 out 180 back -90 in, left-canonical), each a move along the posed normal; carried
to rest by each vertex's inverse blended skin matrix; least squares over the side's frames.

Fields (mm, + out), windows (1 - x^2)^2:
  top    the cap's top and back-top flattened (the ball): s -50..35, phi 20..220
  belly  the mass lower and forward (anterior/middle heads' belly): s 10..75, phi -5..105
  step   the posterior head's lower border eased into the triceps (no ledge at the back): s 35..115, phi 140..215
  vtap   the outer face tapering into the V (~45% down) and the flat just below it: s 85..150, phi 65..155
  slim   the upper arm slimmer above the elbow (outer and inner sides): s 130..225
"""
import numpy as np
import k
import chart as c

FR_SIDE = {"r": ["w_p45", "look_f"], "l": ["w_m45", "look_f", "rL90_m45"]}

C1 = dict(top=7.0, top_s=(-8.0, 42.0), top_phi=(125.0, 105.0),
          belly=3.0, belly_s=(42.0, 32.0), belly_phi=(50.0, 55.0),
          step=4.0, step_s=(72.0, 38.0), step_phi=(175.0, 40.0),
          vtap=4.0, vtap_s=(118.0, 32.0), vtap_phi=(110.0, 45.0),
          slim=2.5, slim_s=(180.0, 45.0), slim_phi=((90.0, 60.0), (-90.0, 50.0)),
          rmax=(62.0, 80.0))


def bw(x):
    x = np.clip(1 - np.asarray(x, float) ** 2, 0, None)
    return x * x


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def ss(x):
    t = np.clip(x, 0, 1)
    return t * t * (3 - 2 * t)


def field(s, phi, r, P):
    """the move (mm along the posed normal) on the posed chart"""
    d = -P["top"] * bw((s - P["top_s"][0]) / P["top_s"][1]) * bw(wrap(phi - P["top_phi"][0]) / P["top_phi"][1])
    d += P["belly"] * bw((s - P["belly_s"][0]) / P["belly_s"][1]) * bw(wrap(phi - P["belly_phi"][0]) / P["belly_phi"][1])
    d += P["step"] * bw((s - P["step_s"][0]) / P["step_s"][1]) * bw(wrap(phi - P["step_phi"][0]) / P["step_phi"][1])
    d -= P["vtap"] * bw((s - P["vtap_s"][0]) / P["vtap_s"][1]) * bw(wrap(phi - P["vtap_phi"][0]) / P["vtap_phi"][1])
    for ph0, hw in P["slim_phi"]:
        d -= P["slim"] * bw((s - P["slim_s"][0]) / P["slim_s"][1]) * bw(wrap(phi - ph0) / hw)
    # only the arm and the shoulder's top: off the torso (the radial distance from the humerus line)
    d *= 1 - ss((r - P["rmax"][0]) / (P["rmax"][1] - P["rmax"][0]))
    return d


def posed_normals_u(X, F):
    return k.vn(X, F)


def solve(P, body=None, sides="lr", frames=FR_SIDE, smooth=3, log=print):
    """rest move (nU, 3) m: per side, the field at each frame along the posed normal, to rest by B^-1, averaged"""
    bs = k.base()
    body = body or k.Body()
    dU = np.zeros((bs.nU, 3))
    for sd in sides:
        sg = 1 if sd == "l" else -1
        mine = bs.U[:, 0] * sg > 0.02
        acc = np.zeros((bs.nU, 3)); cnt = np.zeros(bs.nU)
        for f in frames[sd]:
            fr = k.frame(f)
            X = k.posed_welded(fr, body)
            ok = np.isfinite(X).all(1) & mine
            Xs = np.where(ok[:, None], X, 0)
            N = posed_normals_u(Xs, bs.F)
            F = c.posed_frame(fr, sd)
            s, phi, r = c.coords(Xs, F)
            dmm = np.where(ok, field(s, phi, r, P), 0.0)
            dp = N * (dmm * 1e-3)[:, None]
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
    log("shoulder: %d points > 0.5 mm, max %.1f mm" % ((mv > 0.5).sum(), mv.max()))
    return dU
