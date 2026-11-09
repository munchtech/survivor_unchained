"""P1 R1 push-up proxy: a plunge cup shell made from the body, clay, to judge a breast under a push-up armor piece.
    python tools/body/sculpt/pushup_proxy.py OUT.png ROW [ROW...] [--views front,q34,side,25] [--y0 --y1 --x --px]
                                             [--write DIR]
a ROW is SPEC (the rest body, formview.body), SPEC+ (the rest body with the proxy), BUILD@hang (a build posed arms
down by the game drive, as formview_hang) or BUILD@hang+ (with the proxy). Rows come in pairs: clay, painted cel.
The proxy is a function of the body: the cup regions are smooth scalar fields phi on the REST vertices (from each
breast apex and fold), cut cleanly along phi = 0 (marching triangles: no stair-step edge) on the posed surface and
offset along its normals: the cups 5 mm (the lower two thirds of each breast: the top edge across the upper pole
rising to the side, the plunge V at the centre gore), a band 3 mm under the bust, straps 2.5 mm; a rim strip closes
each cut edge onto the skin (the cup edge's thickness). --write saves each proxy as an OBJ (glTF m).
"""
import os
import sys
import json
import math
import argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BODY = os.path.dirname(HERE)
sys.path.insert(0, BODY)

CUP = {"top_lat": [0.165, 0.045], "top_med": [0.05, -0.012], "gore_up": 0.012, "x_lat": 0.178, "below_fold": 0.012,
       "band": [-0.042, -0.008], "band_x": 0.21, "strap_lo": [0.15, 0.05], "strap_hi": [0.125, 1.565], "strap_w": 0.016,
       "off_cup": 0.005, "off_band": 0.003, "off_strap": 0.0025}


def vnormals(V, T):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def marks(Vr):
    """Per side (+1 left, -1 right): the apex (the most forward point of the breast zone) and the fold height."""
    out = {}
    for s in (1.0, -1.0):
        x = Vr[:, 0] * s
        zone = (x > 0.03) & (x < 0.17) & (Vr[:, 1] > 1.28) & (Vr[:, 1] < 1.5)
        i = int(np.argmax(np.where(zone, Vr[:, 2], -9)))
        a = Vr[i]
        lp = (np.abs(Vr[:, 0] - a[0]) < 0.02) & (Vr[:, 2] > a[2] - 0.075) & (Vr[:, 1] < a[1]) & zone
        fy = float(Vr[lp, 1].min()) if lp.any() else a[1] - 0.09
        out[s] = (a, fy)
    return out


def seg_dist(P, A, B):
    d = B - A
    t = np.clip(((P - A) @ d) / (d @ d), 0, 1)
    return np.linalg.norm(P - (A + t[:, None] * d), axis=1)


def fields(Vr, c=CUP):
    """phi per region on the rest vertices (> 0 inside): cups, band, straps."""
    mk = marks(Vr)
    x, y, z = Vr[:, 0], Vr[:, 1], Vr[:, 2]
    side = np.where(x >= 0, 1.0, -1.0)
    xs = np.abs(x)
    ay = np.where(side > 0, mk[1.0][0][1], mk[-1.0][0][1])
    fy = np.where(side > 0, mk[1.0][1], mk[-1.0][1])
    (x1, d1), (x0, d0) = c["top_lat"], c["top_med"]
    ytop = ay + d0 + (d1 - d0) * np.clip((xs - x0) / (x1 - x0), 0, None)
    ypl = fy + c["gore_up"] + (ay + d0 - fy - c["gore_up"]) * np.clip(xs / x0, 0, None)
    ypl = np.where(xs < x0, ypl, 9.0)
    front = z > -0.02
    cup = np.minimum.reduce([ytop - y, ypl - y, c["x_lat"] - xs, y - (fy - c["below_fold"]), np.where(front, 1.0, -1.0)])
    b0, b1 = c["band"]
    band = np.minimum.reduce([y - (fy + b0), (fy + b1) - y, c["band_x"] - xs + 0 * y, z + 0.06])
    P2 = np.stack([xs, y], 1)
    A = np.stack([np.full_like(xs, c["strap_lo"][0]), ay + c["strap_lo"][1]], 1)
    B = np.array([c["strap_hi"][0], c["strap_hi"][1]])
    d = np.array([seg_dist(P2[i:i + 1], A[i], B)[0] for i in range(0)]) if False else None
    dd = B[None, :] - A
    t = np.clip(((P2 - A) * dd).sum(1) / (dd * dd).sum(1), 0, 1)
    dist = np.linalg.norm(P2 - (A + t[:, None] * dd), axis=1)
    strap = np.minimum(c["strap_w"] / 2 - dist, np.where(z > -0.01, 1.0, -1.0))
    return {"cup": cup, "band": band, "strap": strap}


def clip(V, N, T, phi, off, rim=True):
    """The surface part phi > 0, cut along phi = 0, offset by off along N; plus the rim strip. Triangle soup."""
    ph = phi[T]
    P_out, N_out = [], []
    rimP, rimN = [], []
    full = (ph > 0).all(1)
    for t in T[full]:
        P_out.append(V[t] + off * N[t])
        N_out.append(N[t])
    part = (ph > 0).any(1) & ~full
    for t, f in zip(T[part], ph[part]):
        poly, cut = [], []
        for k in range(3):
            i, j = t[k], t[(k + 1) % 3]
            fi, fj = f[k], f[(k + 1) % 3]
            if fi > 0:
                poly.append((V[i], N[i]))
            if (fi > 0) != (fj > 0):
                s = fi / (fi - fj)
                q = (V[i] + s * (V[j] - V[i]), N[i] + s * (N[j] - N[i]))
                poly.append(q)
                cut.append(q)
        for k in range(1, len(poly) - 1):
            tri = [poly[0], poly[k], poly[k + 1]]
            P_out.append(np.array([p + off * n for p, n in tri]))
            N_out.append(np.array([n for _, n in tri]))
        if rim and len(cut) == 2:
            (pa, na), (pb, nb) = cut
            q = [pa + 0.0003 * na, pb + 0.0003 * nb, pb + off * nb, pa + off * na]
            m = np.cross(pb - pa, na) ; m = m / max(np.linalg.norm(m), 1e-12)
            for tri in ((0, 1, 2), (0, 2, 3)):
                rimP.append(np.array([q[k] for k in tri]))
                rimN.append(np.array([m, m, m]))
    P = np.array(P_out + rimP).reshape(-1, 3)
    Nn = np.array(N_out + rimN).reshape(-1, 3)
    return P, Nn


def proxy(Vr, Vp, T, c=CUP):
    """The proxy (triangle soup P [3k, 3], normals) for a body: phi on the rest Vr, geometry on the posed Vp."""
    F = fields(Vr, c)
    N = vnormals(Vp, T)
    parts = [clip(Vp, N, T, F["cup"], c["off_cup"]), clip(Vp, N, T, F["band"], c["off_band"]),
             clip(Vp, N, T, F["strap"], c["off_strap"])]
    return np.concatenate([p for p, _ in parts]), np.concatenate([n for _, n in parts])


def render(V, T, N, alb, view, cel):
    import ray
    s = ray.scene(V, T)
    x, y = view.grid()
    org = (view.o + x[..., None] * view.ex + y[..., None] * view.ey + 5.0 * view.cam).reshape(-1, 3)
    d = np.broadcast_to(-view.cam, org.shape)
    pid, tf = ray.hits(s, org, d)
    m = pid >= 0
    img = np.ones(len(pid))
    t = T[pid[m]]
    P = org[m] + tf[m][:, None] * d[m]
    a, b, cc = V[t[:, 0]], V[t[:, 1]], V[t[:, 2]]
    v0, v1, v2 = b - a, cc - a, P - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-20)
    bv = (d11 * d20 - d01 * d21) / den
    bw = (d00 * d21 - d01 * d20) / den
    bu = 1 - bv - bw
    n = N[t[:, 0]] * bu[:, None] + N[t[:, 1]] * bv[:, None] + N[t[:, 2]] * bw[:, None]
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    n = np.where((n @ view.cam)[:, None] < 0, -n, n)
    L = 0.62 * view.cam + 0.55 * view.ey - 0.45 * view.ex
    L /= np.linalg.norm(L)
    lam = np.clip(n @ L, 0, 1)
    al = alb[pid[m]]
    if cel:
        band = 1.0 / (1.0 + np.exp(-(lam - 0.32) / 0.025))
        img[m] = (0.30 + 0.50 * band) * al + 0.10 * np.clip(n @ view.cam, 0, 1) ** 4
    else:
        img[m] = 0.16 + 0.66 * lam * al + 0.10 * np.clip(n @ view.cam, 0, 1)
    return img.reshape(view.h, view.w)


def tiles(V, T, N, alb, views, y0, y1, xw, px, cel):
    import ray
    from formview import VIEWS
    out = []
    for nm in views:
        yaw = VIEWS[nm] if nm in VIEWS else float(nm)
        a = math.radians(yaw)
        v = ray.View([0, 0, 0], [math.cos(a), 0, -math.sin(a)], [0, 1, 0], [math.sin(a), 0, math.cos(a)], px, -xw, xw, y0, y1)
        out.append((np.clip(render(V, T, N, alb, v, cel), 0, 1) * 255).astype(np.uint8))
    return np.concatenate(out, 1)


def hang_body(build, deg=8.0):
    """A build posed arms down (formview_hang: the lbs poser, the game drive): rest and posed vertices, T."""
    import check
    import rig_drive as rd
    from pathlib import Path
    P = check.make_poser("lbs", build + "/body.glb", json.loads(Path(build + "/rig.json").read_text()))
    I = P.index
    h = lambda G, n: G[I[n]][:3, 3]
    Vr, G, _ = P.pose([])
    t = []
    for s, sg in (("l", 1), ("r", -1)):
        dd = rd._n(h(G, "lowerarm_" + s) - h(G, "upperarm_" + s))
        e = math.radians(deg)
        t.append(("upperarm_" + s, rd._arc(dd, rd._n(np.array([sg * math.sin(e), -math.cos(e), 0.03])))))
    Vp, G, _ = P.pose(t)
    return np.asarray(Vr), np.asarray(Vp), np.asarray(P.T)


def write_obj(path, P):
    with open(path, "w") as f:
        f.write("# P1 R1 push-up proxy (tools/body/sculpt/pushup_proxy.py), glTF m\n")
        for p in P:
            f.write("v %.6f %.6f %.6f\n" % tuple(p))
        for k in range(len(P) // 3):
            f.write("f %d %d %d\n" % (3 * k + 1, 3 * k + 2, 3 * k + 3))


def main():
    from PIL import Image
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("rows", nargs="+")
    ap.add_argument("--views", default="front,q34,side,25")
    ap.add_argument("--y0", type=float, default=1.2)
    ap.add_argument("--y1", type=float, default=1.62)
    ap.add_argument("--x", type=float, default=0.30)
    ap.add_argument("--px", type=float, default=700)
    ap.add_argument("--write")
    a = ap.parse_args()
    import formview
    rows = []
    for r in a.rows:
        withp = r.endswith("+")
        r = r.rstrip("+")
        if r.endswith("@hang"):
            Vr, Vp, T = hang_body(r[:-5])
            H = HT = None
        else:
            Vp, T, H, HT, z, rep = formview.body(r)
            Vr = Vp
        V, TT = Vp, T
        Nb = vnormals(Vp, T)
        if H is not None:
            V = np.concatenate([Vp, H])
            TT = np.concatenate([T, HT + len(Vp)])
            Nb = vnormals(V, TT)
        alb = np.ones(len(TT))
        N = Nb
        if withp:
            P, PN = proxy(Vr, Vp, T)
            k = len(P) // 3
            TT = np.concatenate([TT, len(V) + np.arange(3 * k).reshape(k, 3)])
            N = np.concatenate([Nb, PN / np.maximum(np.linalg.norm(PN, axis=1, keepdims=True), 1e-12)])
            V = np.concatenate([V, P])
            alb = np.concatenate([alb, np.full(k, 0.8)])
            if a.write:
                os.makedirs(a.write, exist_ok=True)
                nm = os.path.basename(r.rstrip("/").replace("@hang", "_hang")).replace(".json", "")
                write_obj(os.path.join(a.write, "proxy_" + nm + ".obj"), P)
        vs = a.views.split(",")
        rows.append(tiles(V, TT, N, alb, vs, a.y0, a.y1, a.x, a.px, False))
        rows.append(tiles(V, TT, N, alb, vs, a.y0, a.y1, a.x, a.px, True))
        print("row", r, "proxy" if withp else "")
    Image.fromarray(np.concatenate(rows, 0)).save(a.out)
    print("wrote", a.out)


if __name__ == "__main__":
    main()