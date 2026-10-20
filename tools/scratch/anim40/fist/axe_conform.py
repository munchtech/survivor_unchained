"""anim-40: the viking axe's haft made holdable (her one-handed fist, the Blade1H pocket and WRAP["sword"]'s hollow).

    python tools/scratch/anim40/fist/axe_conform.py --out DIR [--rc 13.7] [--win 50] [--blend 45]

The haft is one straight two-ring prism (51 x 35.5 mm, butt ring at t -115, top ring at +647 inside the head) under a
sculpted leather wrap (57.7 x 40 mm, t -118..+172). No fist closes on either. So:
  - the prism TAPERS along its whole length: its butt ring (hidden in the wrap) drawn in to BUTT, its top ring (inside
    the head's eye) to TOP: a straight taper, no kink, the bare haft 29 x 26 mm above the wrap swelling to about
    44 x 33 into the head;
  - the wrap: round (Rc mm, its own relief kept, scaled) over the fist's window |t| <= win, then blended (smoothstep
    over `blend` mm) to the tapered haft plus the wrap's own overhang (3.1 / 2.25 mm, as the original) at both ends;
    a wrap point between the prism's surface and the wrap's keeps its place between the two (the end caps stay on the
    haft).
  - an anchor_grip at the haft's own line point nearest the old grip point (0.1 mm off it), -Y up the haft toward the
    head (8.8 deg off the bounds' axis, which the plain mount laid), +Z the old mount's +Z (Roll pi kept).
Normals by the map's Jacobian (finite differences), tangents by it too; UVs, indices and the head untouched.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from axe_haft import gc, haft_frame, coords, long_tris  # noqa: E402

WRAP_HALF = (28.8, 20.0)      # the wrap's half-extents (u: the head's plane, v: across), mm
PRISM_HALF = (25.7, 17.75)    # the haft prism's
BUTT = (9.6, 11.0)            # the prism's butt ring, new half-extents (hidden in the wrap)
TOP = (23.0, 17.0)            # its top ring (in the head)
OVER = (WRAP_HALF[0] - PRISM_HALF[0], WRAP_HALF[1] - PRISM_HALF[1])


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def build(rc=13.7, win=50.0, blend=45.0, butt=BUTT, top=TOP, src=None, flare=0.0, f0=0.0, f1=40.0, wc=0.0, ov=1.0):
    pc = gc.load("viking_axe", rev=src)
    O, d, a1, a2 = haft_frame(pc)
    tt, u, v = coords(pc, O, d, a1, a2)
    r = np.hypot(u, v)
    I, L = long_tris(pc)
    ring = np.unique(L)
    from scipy.spatial import cKDTree
    near = cKDTree(pc.P[ring]).query(pc.P)[0] * pc.mm < 0.01
    tb, tT = float(tt[ring][tt[ring] < 0].mean()), float(tt[ring][tt[ring] > 0].mean())
    butt_v = near & (tt < 0); top_v = near & (tt > 0)
    wrap_v = ~near & (tt > -135) & (tt < 185) & (r < 45)
    # the wrap's outline (its outer envelope by angle: the 95th percentile per 5 deg, smoothed) over the window rings
    th = np.arctan2(v, u)
    win_v = wrap_v & (np.abs(tt) < 140)
    nb = 72; k = ((th + np.pi) / (2 * np.pi) * nb).astype(int) % nb
    o = np.array([np.percentile(r[win_v & (k == q)], 95) if (win_v & (k == q)).sum() >= 3 else np.nan for q in range(nb)])
    ang = -np.pi + (np.arange(nb) + 0.5) * 2 * np.pi / nb
    ok = ~np.isnan(o)
    o = np.interp(ang, ang[ok], o[ok], period=2 * np.pi)
    o = np.convolve(np.r_[o[-2:], o, o[:2]], np.ones(5) / 5, "valid")

    def outline(x):
        return np.interp(x, ang, o, period=2 * np.pi)

    def prism(t):
        f = (t - tb) / (tT - tb)
        return butt[0] + (top[0] - butt[0]) * f, butt[1] + (top[1] - butt[1]) * f

    def F(t, uu, vv):
        """The wrap's map at (t mm, u, v mm): (u', v')."""
        Pu, Pv = prism(t)
        su_p, sv_p = Pu / PRISM_HALF[0], Pv / PRISM_HALF[1]
        su_w, sv_w = (Pu + OVER[0]) / WRAP_HALF[0], (Pv + OVER[1]) / WRAP_HALF[1]
        rho = np.hypot(uu / WRAP_HALF[0], vv / WRAP_HALF[1])
        lam = np.clip((rho - 0.89) / 0.11, 0, 1)
        su = su_p + (su_w - su_p) * lam; sv = sv_p + (sv_w - sv_p) * lam
        Au, Av = uu * su, vv * sv
        th_ = np.arctan2(vv, uu)
        ell = 1.0 / np.sqrt(np.cos(th_) ** 2 / ov + np.sin(th_) ** 2 * ov)     # an oval (ov > 1: long in the head's plane), its area kept
        g = (rc + flare * smooth((t - f0) / (f1 - f0))) * ell / outline(th_)
        w = 1 - smooth((np.abs(t - wc) - win) / blend)
        return w * uu * g + (1 - w) * Au, w * vv * g + (1 - w) * Av

    newP = pc.P.copy()
    # wrap points
    sel = np.flatnonzero(wrap_v)
    nu, nv = F(tt[sel], u[sel], v[sel])
    def to_world(t, uu, vv):
        return O + np.outer(t / pc.mm, d) + np.outer(uu / pc.mm, a1) + np.outer(vv / pc.mm, a2)
    newP[sel] = to_world(tt[sel], nu, nv)
    # the Jacobian (world, per point) of the wrap's map, by central differences in (t, u, v)
    h = 0.02
    J = np.zeros((len(sel), 3, 3))
    B = np.stack([d, a1, a2], 1)   # world from (t,u,v)/mm
    for c in range(3):
        dt = np.zeros(3); dt[c] = h
        p1 = to_world(tt[sel] + dt[0], *F(tt[sel] + dt[0], u[sel] + dt[1], v[sel] + dt[2]))
        p0 = to_world(tt[sel] - dt[0], *F(tt[sel] - dt[0], u[sel] - dt[1], v[sel] - dt[2]))
        J[:, :, c] = (p1 - p0) / (2 * h / pc.mm)          # world per world-unit along (t,u,v)
    Jw = J @ B.T[None]                                     # d new / d old (world)
    # the prism's rings: scaled about the haft line
    Jp = {}
    for m_, (hu, hv), ref in ((butt_v, butt, None), (top_v, top, None)):
        idx = np.flatnonzero(m_)
        s1, s2 = hu / PRISM_HALF[0], hv / PRISM_HALF[1]
        newP[idx] = to_world(tt[idx], u[idx] * s1, v[idx] * s2)
        S = np.eye(3) + (s1 - 1) * np.outer(a1, a1) + (s2 - 1) * np.outer(a2, a2)
        for i in idx:
            Jp[i] = S
    maps = {int(i): Jw[n] for n, i in enumerate(sel)}
    maps.update(Jp)
    return pc, O, d, newP, maps, dict(tb=tb, tT=tT, outline=o, n_wrap=len(sel), n_butt=int(butt_v.sum()), n_top=int(top_v.sum()))


def write(pc, O, d, newP, maps, out):
    g = pc.g; base = 0
    for node, p, M in pc.parts:
        A = M[:3, :3]; Ai = np.linalg.inv(A)
        po, V = g.acc(p["attributes"]["POSITION"]); n = len(V)
        rows = [i - base for i in maps if base <= i < base + n]
        if rows:
            rows = np.array(sorted(rows))
            V2 = V.copy(); V2[rows] = (newP[base + rows] - M[:3, 3]) @ Ai.T
            o = V2.astype("<f4"); g.b[po:po + o.nbytes] = o.tobytes()
            a = g.js["accessors"][p["attributes"]["POSITION"]]
            a["min"] = o.min(0).astype(float).tolist(); a["max"] = o.max(0).astype(float).tolist()
            if "NORMAL" in p["attributes"]:
                no, Nn = g.acc(p["attributes"]["NORMAL"])
                Nw = Nn @ Ai                                   # model -> world normals (A^-T)
                N2 = Nn.copy()
                for rr in rows:
                    Jm = maps[base + rr]
                    nw = np.linalg.solve(Jm.T, Nw[rr]); nw /= np.linalg.norm(nw)
                    N2[rr] = nw @ A; N2[rr] /= np.linalg.norm(N2[rr])
                o = N2.astype("<f4"); g.b[no:no + o.nbytes] = o.tobytes()
            if "TANGENT" in p["attributes"]:
                to, T = g.acc(p["attributes"]["TANGENT"], 4)
                T2 = T.copy()
                for rr in rows:
                    Jm = maps[base + rr]
                    tw = Jm @ (A @ T[rr, :3]); tm = Ai @ tw
                    nm = np.frombuffer(bytes(g.b[no + rr * 12: no + rr * 12 + 12]), "<f4").astype(float) if "NORMAL" in p["attributes"] else None
                    if nm is not None:
                        tm = tm - nm * (tm @ nm)
                    T2[rr, :3] = tm / np.linalg.norm(tm)
                o = T2.astype("<f4"); g.b[to:to + o.nbytes] = o.tobytes()
        base += n
    # the anchor: origin on the haft's line at the old grip point, -Y toward the head along the haft, +Z the old mount's +Z
    Y = -d; Z = pc.turn[2] - d * (pc.turn[2] @ d); Z /= np.linalg.norm(Z); X = np.cross(Y, Z)
    gc.write_anchor(g, O, np.array([X, Y, Z]).T, pc.node_index)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    g.write(Path(out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--rc", type=float, default=13.7)
    ap.add_argument("--win", type=float, default=50.0)
    ap.add_argument("--blend", type=float, default=45.0)
    ap.add_argument("--src", default=None)
    ap.add_argument("--flare", type=float, default=0.0)
    ap.add_argument("--f0", type=float, default=0.0)
    ap.add_argument("--f1", type=float, default=40.0)
    ap.add_argument("--wc", type=float, default=0.0)
    ap.add_argument("--ov", type=float, default=1.0)
    a = ap.parse_args()
    pc, O, d, newP, maps, info = build(a.rc, a.win, a.blend, src=a.src, flare=a.flare, f0=a.f0, f1=a.f1, wc=a.wc, ov=a.ov)
    print({k: (np.round(v, 1).tolist() if isinstance(v, np.ndarray) else v) for k, v in info.items()})
    write(pc, O, d, newP, maps, a.out)
    print("written", a.out)
