"""P1 R1 breast ROUTE (b): a target SCULPTED ONCE on our topology (designed/breast.json "breast_b", rule "target").
    python tools/body/sculpt/breast_b.py [--tiers close,play] [--from-obj tools/body/sculpt/breast_b.obj]
writes tools/body/base/targets/breast_b_{tier}.npz (D [n, 3], glTF m, the move at v = 1 over the chest wall) and
tools/body/sculpt/breast_b.obj (the sculpted region on the close tier, for an artist to open and refine; its "# vid"
lines keep our vertex ids, and --from-obj rebuilds the close target from an edited copy, play carried by
sliders.carry_to_tier).

The design: per side a SOLID, an egg (an ellipsoid with its own radius on each side of each axis, switched smoothly),
its long axis tilted back from vertical (TILT: the upper end runs into the chest under the clavicle, so the upper pole
is the egg flank, one clean full slope; the lower end rounds forward, the lower pole), turned out by YAW; smoothly
unioned with the chest wall (a C2 polynomial smooth-min of the two signed distances, blend K: the soft fold and the
soft root are the union fillet). The body is her her_r1 sliders with the cup sliders at 0 plus chest_wall (the base
the target is laid on). Each region vertex is carried out from the wall to the union surface along the ray from a
point behind the chest (a star projection: the underside and the flanks get their share), then relaxed (tangential
Laplacian on the quads, the rim pinned) and re-projected onto the surface, ITERS times, so the quads stay even on the
new form. Left side solved, the right mirrored (topology mirror_of). Numbers: EGG below (eval frame of the sliders,
before the stance: y 30 mm higher and z 13 mm further front than the built rest at the breast).
"""
import os
import sys
import json
import argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BODY = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(BODY))
sys.path.insert(0, BODY)

EGG = {
    "c1": [0.09, 1.432, 0.102],         # the big sphere centre (the round lower pole and the apex cap), left, eval frame
    "r1": 0.077,                         # its radius: the lower pole radius
    "c2": [0.09, 1.512, -0.018],        # the small sphere centre, up and back inside the chest under the clavicle
    "r2": 0.03,                          # its radius: the cone between the two is the upper pole (one straight slope)
    "sx_med": 0.9, "sx_lat": 1.08,      # the cross-section width, medial / lateral half (1: round)
    "sx_switch": 0.02,
    "K": 0.045,                           # the union blend: the fold and root fillet size (m)
    "yaw_deg": 13.0,                     # the star projection direction (out from straight ahead)
    "ray_origin_back_m": 0.12,           # the star projection origin: this far behind the big sphere centre
    "region": [{"on": "ell", "c": [0.09, 1.43, 0.06], "r": [0.12, 0.15, 0.13], "full": 0.0}],
    "relax_region": [{"on": "ell", "c": [0.09, 1.43, 0.06], "r": [0.14, 0.17, 0.14], "full": 0.7}],
    "iters": 40, "step": 0.5,
}
SPEC = os.path.join(BODY, "specs", "r1_breast_b.json")


def sw(x, a, b, w):
    g = 0.5 * (1.0 + np.tanh(x / w))
    return a + (b - a) * g


def egg_sdf(e, Q):
    """The breast solid signed distance, left side: a round cone (IQ sdRoundCone: a big sphere r1 at c1, a small one
    r2 at c2 and the cone tangent to both), its cross-section scaled across (sx: medial / lateral)."""
    c1, c2 = np.asarray(e["c1"]), np.asarray(e["c2"])
    r1, r2 = e["r1"], e["r2"]
    A = c2 - c1
    h = np.linalg.norm(A)
    A /= h
    M = np.array([1.0, 0.0, 0.0]) - A[0] * A
    M /= np.linalg.norm(M)
    F = np.cross(A, M)
    q = Q - c1
    qa, qm, qf = q @ A, q @ M, q @ F
    sx = sw(qm, e["sx_med"], e["sx_lat"], e["sx_switch"])
    qm = qm / sx
    b = (r1 - r2) / h
    a = np.sqrt(1.0 - b * b)
    rq = np.sqrt(qm * qm + qf * qf)
    k = -b * rq + a * qa
    d = np.where(k < 0, np.sqrt(rq * rq + qa * qa) - r1,
                 np.where(k > a * h, np.sqrt(rq * rq + (qa - h) ** 2) - r2, a * rq + b * qa - r1))
    return d * np.minimum(sx, 1.0)

class Wall:
    """The chest wall signed distance: the point-plane distance to the nearest wall vertex (its normal)."""
    def __init__(self, V, N):
        from scipy.spatial import cKDTree
        self.V, self.N, self.t = V, N, cKDTree(V)

    def __call__(self, Q):
        _, j = self.t.query(Q, k=4)
        d = ((Q[:, None, :] - self.V[j]) * self.N[j]).sum(2)
        return d.mean(1)


def smin(a, b, k):
    """C2 polynomial smooth minimum (cubic), blend k."""
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h ** 3 * k / 6.0


def union(e, wall, Q):
    return smin(wall(Q), egg_sdf(e, Q), e["K"])


def grad(fun, Q, h=4e-4):
    G = np.zeros_like(Q)
    for k in range(3):
        d = np.zeros(3)
        d[k] = h
        G[:, k] = (fun(Q + d) - fun(Q - d)) / (2 * h)
    return G


def project(fun, Q, n=3):
    for _ in range(n):
        u = fun(Q)
        g = grad(fun, Q)
        Q = Q - (u / np.maximum((g * g).sum(1), 1e-12))[:, None] * g
    return Q


def star(e, fun, P, O, tmax=0.2, step=0.002):
    """Each point P carried out along the ray from O to the first exit of the union (U from <= 0 to > 0)."""
    d = P - O
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    t = np.zeros(len(P))
    live = np.ones(len(P), bool)
    u0 = fun(P)
    live &= u0 <= 0
    lo = np.zeros(len(P))
    hi = np.full(len(P), np.nan)
    s = 0.0
    while s < tmax and live.any():
        s += step
        idx = np.nonzero(live)[0]
        u = fun(P[idx] + s * d[idx])
        out = u > 0
        hi[idx[out]] = s
        lo[idx[~out]] = s
        live[idx[out]] = False
    ok = ~np.isnan(hi)
    a, b = lo[ok], hi[ok]
    for _ in range(25):
        m = 0.5 * (a + b)
        u = fun(P[ok] + m[:, None] * d[ok])
        a = np.where(u <= 0, m, a)
        b = np.where(u <= 0, b, m)
    t[ok] = 0.5 * (a + b)
    return P + t[:, None] * d


def walled_body(tier):
    from sliders import OurSliders, load_spec
    sl = OurSliders(os.path.join(BODY, "base", f"sliders_{tier}.npz"))
    spec = load_spec(SPEC)
    vals = {k: v for k, v in spec["sliders"].items() if v and k != "breast_b" and not k.startswith("support_")}
    return sl, sl.evaluate(vals, post=False)


def sculpt(tier, e=EGG, log=print):
    import breast_form as bf
    import scipy.sparse as sp
    sl, Vw = walled_body(tier)
    X = bf.extra(sl)
    Q = X["Q"]
    N = bf.vnormals(Vw, Q)
    wall = Wall(Vw, N)
    fun = lambda P: union(e, wall, P)
    left = sl.V0[:, 0] >= -1e-4
    reg = (sl.mask(e["region"], sl.V0) > 0) & left
    keep = [X["parts"].index(p) for p in ("trunk", "breast", "shoulder")]
    reg &= np.isin(X["part"], keep) & (Vw[:, 2] > -0.02)
    yaw = np.radians(e["yaw_deg"])
    a = np.array([np.sin(yaw), 0.0, np.cos(yaw)])
    O = np.asarray(e["c1"]) - e["ray_origin_back_m"] * a
    V = Vw.copy()
    idx = np.nonzero(reg)[0]
    V[idx] = star(e, fun, Vw[idx], O)
    log(tier, "star moved", int((np.linalg.norm(V - Vw, axis=1) > 1e-4).sum()), "max mm", round(float(np.linalg.norm(V - Vw, axis=1).max()) * 1e3, 1))
    # relax on the new form: tangential Laplacian, the rim pinned, then back onto the union surface
    A = X["A"]
    deg = np.asarray(A.sum(1)).ravel()
    w = sl.mask(e["relax_region"], sl.V0) * e["step"]
    w[~left] = 0.0
    act = np.nonzero(w > 1e-4)[0]
    mid = np.abs(sl.V0[:, 0]) <= 1e-4
    for it in range(e["iters"]):
        Vm = bf.mirror_left(sl, V - Vw) + Vw                    # the right side mirrored (the midline neighbours)
        Nn = bf.vnormals(Vm, Q)
        Lp = (A @ Vm) / deg[:, None] - Vm
        Lp -= (Lp * Nn).sum(1, keepdims=True) * Nn
        V[act] = Vm[act] + w[act, None] * Lp[act]
        V[mid, 0] = 0.0
        V[act] = project(fun, V[act], 2)
        V[mid, 0] = 0.0
    D = bf.mirror_left(sl, V - Vw)
    return sl, Vw, D


def save(tier, sl, D):
    import build_topo as bt
    z = np.load(os.path.join(BODY, "out", "topo", f"{tier}.npz"))
    os.makedirs(os.path.join(BODY, "base", "targets"), exist_ok=True)
    p = os.path.join(BODY, "base", "targets", f"breast_b_{tier}.npz")
    np.savez_compressed(p, D=D.astype(np.float32), topology=bt.topo_sha(z), made_by="tools/body/sculpt/breast_b.py",
                        egg=json.dumps(EGG))
    return p


def write_obj(path, Vw, D, Q, thr=2e-4):
    moved = np.linalg.norm(D, axis=1) > thr
    qs = Q[moved[Q].any(1)]
    ids = np.unique(qs)
    remap = -np.ones(len(Vw), np.int64)
    remap[ids] = np.arange(len(ids))
    P = Vw + D
    with open(path, "w") as f:
        f.write("# P1 R1 breast route (b): the sculpted region on the close tier (glTF m, eval frame), made by\n")
        f.write("# tools/body/sculpt/breast_b.py; edit the positions (keep the vertex order) and rebuild with --from-obj\n")
        for i in ids:
            f.write("# vid %d\nv %.6f %.6f %.6f\n" % (i, P[i, 0], P[i, 1], P[i, 2]))
        for q in qs:
            f.write("f %d %d %d %d\n" % tuple(remap[q] + 1))
    return len(ids)


def read_obj(path, Vw):
    ids, P = [], []
    with open(path) as f:
        for line in f:
            if line.startswith("# vid"):
                ids.append(int(line.split()[2]))
            elif line.startswith("v "):
                P.append([float(x) for x in line.split()[1:4]])
    D = np.zeros_like(Vw)
    D[np.array(ids)] = np.array(P) - Vw[np.array(ids)]
    return D


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiers", default="close,play")
    ap.add_argument("--from-obj")
    a = ap.parse_args()
    obj = os.path.join(HERE, "breast_b.obj")
    if a.from_obj:
        import sliders
        sl, Vw = walled_body("close")
        D = read_obj(a.from_obj, Vw)
        print("close", save("close", sl, D))
        slp, _ = walled_body("play")
        print("play", save("play", slp, sliders.carry_to_tier(D)))
        return
    for tier in a.tiers.split(","):
        sl, Vw, D = sculpt(tier)
        print(tier, save(tier, sl, D))
        if tier == "close":
            import breast_form as bf
            print("obj vertices", write_obj(obj, Vw, D, bf.extra(sl)["Q"]))


if __name__ == "__main__":
    main()