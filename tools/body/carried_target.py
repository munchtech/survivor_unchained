"""The carried target: a reference mesh's own posed surface, carried onto another mesh's points through the REST
correspondence. No solver.

A rigged mesh that deforms well (the reference) lends its posed shape to a mesh of another topology whose rest shape
agrees with it (the source). Each source point remembers its closest point on the reference's rest surface (triangle +
barycentrics) and its rest offset from that point. In a pose the point is that barycentric point on the reference's posed
triangle, plus the offset turned by the reference's local surface rotation (smooth per-vertex frames, no faceting).

    car = Carrier(ref_V0, ref_T, P0, N0)                 # once: the correspondence of points P0 (unit normals N0)
    X = car.carry(ref_V)                                 # per pose: the reference's posed vertices -> the points

Posing the reference like the source, for a reference skeleton that is driven by world turns:

    order = transfer_order(ref_names, ref_parent, index, bone_map, only, skip)
    turns = transfer_turns(G, rest, index, ref_index, ref_parent, bone_map, order)
    M = anchor_align(G[a], rest[a], refG0[ra], refG[ra])  # the reference's posed surface onto the source's skeleton

The top of this file is the general core: arrays in, arrays out, no body, bone or path names (it runs on any rigged
mesh). The bottom is HER CONFIG: her body B's shoulder region against her old body A, and the CLI.

    python tools/body/carried_target.py test
    python tools/body/carried_target.py target [--poses name,name]

`target` with no --poses writes out/shoulder/target_a.npz (X [poses, region points, 3], name, side, kind, info, params:
the layout of target.npz, same pose order); a subset writes target_a_dev.npz.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from surfdist import closest_on_tris  # noqa: E402

AREA_EPS = 1e-14          # m^2: a triangle under this is degenerate (no frame, no candidate)


# ============================================================================================ the general core ==
def polar(F):
    """The nearest rotation of each 3x3 in F [..., 3, 3] (det +1)."""
    U, _, Vt = np.linalg.svd(F)
    neg = np.linalg.det(U @ Vt) < 0
    U = U * np.where(neg, -1.0, 1.0)[..., None, None] ** np.array([0, 0, 1])      # flip the weakest axis only
    return U @ Vt


def _frames(V, T):
    """Per triangle: [e1, e2, n] as columns [m, 3, 3] (n the unit normal) and the area [m]."""
    a = V[T[:, 0]]
    e1, e2 = V[T[:, 1]] - a, V[T[:, 2]] - a
    n = np.cross(e1, e2)
    ln = np.linalg.norm(n, axis=1)
    return np.stack([e1, e2, n / np.maximum(ln, 1e-30)[:, None]], 2), 0.5 * ln


def _bary(q, a, b, c):
    """Barycentrics [n, 3] of points q lying on triangles (a, b, c), clamped onto the triangle."""
    v0, v1, v2 = b - a, c - a, q - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-300)
    v, w = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
    B = np.clip(np.stack([1 - v - w, v, w], 1), 0, 1)
    return B / B.sum(1, keepdims=True)


class Carrier:
    """The rest correspondence of points P0 [n, 3] (unit normals N0) to a reference mesh (ref_V0 [nv, 3], ref_T [m, 3]).

    Per point: among the k triangles nearest by centroid, those within `rad` whose rest face normal faces the same way
    as the point's normal (dot > 0) are candidates, and the one with the least `distance + nw * rad * (1 - dot)` wins.
    nw = 0 (the default) is the plain closest point. KNOWN, OPEN: where the points' mesh bridges a tight fold that the
    reference keeps as two walls (her armpit apex), neighbours land on opposite walls (rest normals opposed) and a pose
    that opens the fold tears the edge; nw = 0.2 does not cure it, the rule needs the points' adjacency. Kept: `tri` [n, 3]
    vertex ids, `bary` [n, 3], `d0` = P0 - closest point, `face` the triangle, `ok` (False where no candidate passed:
    those take the closest of the k without the tests; count them with (~ok).sum()).

    The local rotation is smooth: a vertex's rotation is the polar of the area-weighted sum of its triangles' rest ->
    posed rotations (vertices doubled along seams are welded by rest position, `weld` m), a point's is the polar of the
    barycentric sum of its three vertices' rotations.
    """

    def __init__(self, ref_V0, ref_T, P0, N0, rad=0.05, k=64, nw=0.0, weld=1e-6):
        V0, T = np.asarray(ref_V0, float), np.asarray(ref_T, np.int64)
        P0, N0 = np.asarray(P0, float), np.asarray(N0, float)
        n = len(P0)
        E0, area = _frames(V0, T)
        live = np.nonzero(area > AREA_EPS)[0]
        fn = E0[live][:, :, 2]
        kk = min(k, len(live))
        dist, cand = cKDTree(V0[T[live]].mean(1)).query(P0, k=kk)
        dist, cand = dist.reshape(n, kk), cand.reshape(n, kk)
        best, pick = np.full((2, n), np.inf), np.zeros((2, n), np.int64)
        for j in range(kk):
            t = cand[:, j]
            tv = T[live[t]]
            q = closest_on_tris(P0, V0[tv[:, 0]], V0[tv[:, 1]], V0[tv[:, 2]])
            d = np.linalg.norm(P0 - q, axis=1)
            dot = np.einsum("ij,ij->i", fn[t], N0)
            sc = d + nw * rad * (1 - dot)
            for r, m, v in ((0, (dist[:, j] <= rad) & (dot > 0) & (sc < best[0]), sc), (1, d < best[1], d)):
                best[r][m], pick[r][m] = v[m], live[t[m]]
        self.ok = np.isfinite(best[0])
        self.face = np.where(self.ok, pick[0], pick[1])
        self.tri = T[self.face]
        A, B, C = (V0[self.tri[:, i]] for i in range(3))
        self.bary = _bary(closest_on_tris(P0, A, B, C), A, B, C)
        self.d0 = P0 - np.einsum("nk,nkj->nj", self.bary, V0[self.tri])
        self.rad, self.k, self.nw = rad, k, nw
        # the frames: only the triangles around the vertices in use
        _, grp = np.unique(np.round(V0 / weld).astype(np.int64), axis=0, return_inverse=True)
        grp = np.asarray(grp).ravel()
        used = np.unique(grp[self.tri])
        loc = -np.ones(int(grp.max()) + 1, np.int64)
        loc[used] = np.arange(len(used))
        tg = loc[grp[T]]
        inc = np.nonzero((tg >= 0).any(1) & (area > AREA_EPS))[0]
        self._T = T[inc]
        self._E0inv = np.linalg.inv(E0[inc])
        rows, cols, w = tg[inc].ravel(), np.repeat(np.arange(len(inc)), 3), np.repeat(area[inc], 3)
        m = rows >= 0
        self._W = sp.csr_matrix((w[m], (rows[m], cols[m])), (len(used), len(inc)))
        self._pg = loc[grp[self.tri]]

    def rotations(self, ref_V):
        """The reference's local surface rotation rest -> posed at each point [n, 3, 3]."""
        E, _ = _frames(np.asarray(ref_V, float), self._T)
        Rt = polar(E @ self._E0inv)
        Rv = polar((self._W @ Rt.reshape(-1, 9)).reshape(-1, 3, 3))
        return polar(np.einsum("nk,nkij->nij", self.bary, Rv[self._pg]))

    def carry(self, ref_V):
        """The points on the reference's posed surface ref_V [nv, 3] -> [n, 3]."""
        ref_V = np.asarray(ref_V, float)
        q = np.einsum("nk,nkj->nj", self.bary, ref_V[self.tri])
        return q + np.einsum("nij,nj->ni", self.rotations(ref_V), self.d0)


def world_turn(G, rest, j):
    """Bone j's world rotation from its rest to the pose G."""
    return polar(G[j][:3, :3] @ np.linalg.inv(rest[j][:3, :3]))


def transfer_order(ref_names, ref_parent, index, bone_map=None, only=None, skip=()):
    """(order, left): the reference bones to pose, parents first, and those left at rest.

    A reference bone is posed when the source has its bone (`bone_map`: reference name -> source name; unlisted bones
    map by name), it is not in `skip` (the bones the reference's own rig drives) and, if `only` is given, it is in it.
    """
    bone_map = bone_map or {}
    depth = []
    for i in range(len(ref_names)):
        d, k = 0, ref_parent[i]
        while k >= 0:
            d, k = d + 1, ref_parent[k]
        depth.append(d)
    take = [i for i in np.argsort(depth, kind="stable")
            if bone_map.get(ref_names[i], ref_names[i]) in index and ref_names[i] not in skip
            and (only is None or ref_names[i] in only)]
    order = [ref_names[i] for i in take]
    return order, [x for x in ref_names if x not in set(order)]


def transfer_turns(G, rest, index, ref_index, ref_parent, bone_map, order):
    """The [(reference bone name, world turn)] that poses a turn-driven reference skeleton like the source.

    G, rest [nb, 4, 4]: the source's posed and rest globals; index: source bone name -> row. A turn is a world rotation
    applied on the bone's current global, so each bone gets its source bone's world turn with its nearest posed
    ancestor's taken off. `order` lists the reference bones parents first (transfer_order).
    """
    bone_map = bone_map or {}
    turns, done = [], {}
    for rn in order:
        sn = bone_map.get(rn, rn)
        if rn not in ref_index or sn not in index:
            continue
        Rb = world_turn(G, rest, index[sn])
        k, Rp = ref_parent[ref_index[rn]], np.eye(3)
        while k >= 0 and k not in done:
            k = ref_parent[k]
        if k >= 0:
            Rp = done[k]
        turns.append((rn, Rb @ Rp.T))
        done[ref_index[rn]] = Rb
    return turns


def anchor_align(G_anchor, rest_anchor, refG0_anchor, refG_anchor):
    """The 4x4 taking the reference's posed surface onto the source's skeleton at an anchor bone.

    A point rigid to the reference's anchor lands where the source's anchor carries its rest position (the two share
    rest joints there). The rotation part is re-orthonormalized.
    """
    M = G_anchor @ np.linalg.inv(rest_anchor) @ refG0_anchor @ np.linalg.inv(refG_anchor)
    M[:3, :3] = polar(M[:3, :3])
    M[3] = 0, 0, 0, 1
    return M


def edge_ratio(X, X0, ei, ej):
    """(min, max) of posed / rest length over the edges (ei, ej)."""
    r = np.linalg.norm(X[ei] - X[ej], axis=1) / np.maximum(np.linalg.norm(X0[ei] - X0[ej], axis=1), 1e-12)
    return float(r.min()), float(r.max()), r


# ================================================================================================= HER CONFIG ==
HER = {
    "source": "B",                       # deform_audit body keys
    "reference": "A",
    "layer": "full",
    # reference bone <- source bone (A has 3 spine bones for B's 5); every other bone by name
    "bone_map": {"spine_01": "spine_02", "spine_02": "spine_03", "spine_03": "spine_05"},
    # the reference bones posed by the transfer; the rest of A (its own rig's bones, fingers, legs) stays at rest
    "pose_bones": ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "neck_02", "head"]
                  + [f"{b}_{s}" for s in "lr" for b in ("clavicle", "upperarm", "lowerarm", "hand")],
    "anchor_child": "clavicle_{s}",      # the anchor = this bone's parent, on each skeleton
    "rad": 0.05,
    "k": 64,
    "nw": 0.0,                           # the normal term: tried at 0.2, it does not cure the armpit-apex bridge (see T5)
    "out": "target_a.npz",
    "dev_out": "target_a_dev.npz",
    "d0_p95_stop_mm": 4.0,
    "dev_poses": ["x:abd150:l", "x:add0:l", "cast_bolt@0:l", "crossbow_shoot@0:r"],
}
INFO = ["d_pub_p50", "d_pub_p95", "d_pub_max", "edge_min", "edge_max", "edge_car_max", "vol", "girth_mid_deltoid", "girth_insertion"]


class Her:
    """Her body B's shoulder region (region_target.Model) against her old body A."""

    def __init__(self, cfg=HER, verbose=True):
        import deform_audit as da
        import region_target as rt
        self.cfg, self.rt = cfg, rt
        self.bd = bd = da.body(cfg["source"])
        bd.set_layer(cfg["layer"])
        self.Ab = Ab = da.body(cfg["reference"])
        Ab.set_layer(cfg["layer"])
        self.md = md = rt.Model(bd.p)
        self.OUT = rt.OUT
        self.ref_names = list(Ab.p.names)
        self.order, left = transfer_order(self.ref_names, Ab.p.parent, bd.p.index, cfg["bone_map"],
                                          only=set(cfg["pose_bones"]))
        N0 = bd._normals(bd.V0)
        self.car, self.anchor, self.edges = {}, {}, {}
        for s in "lr":
            ids = md.S[s]["ids"]
            pts = md.first[ids]
            self.car[s] = Carrier(Ab.V0, Ab.T, bd.V0[pts], N0[pts], cfg["rad"], cfg["k"], cfg["nw"])
            ch = cfg["anchor_child"].replace("{s}", s)
            ra, ja = Ab.p.parent[Ab.p.index[ch]], bd.p.parent[bd.p.index[ch]]
            rn, sn = self.ref_names[ra], bd.p.names[ja]
            assert cfg["bone_map"].get(rn, rn) == sn, f"anchor: reference {rn} does not map to source {sn}"
            self.anchor[s] = (ja, ra)
            A = sp.triu(md.adj[ids][:, ids], 1).tocoo()
            self.edges[s] = (A.row, A.col)
        self.girth0 = {s: md.girth(md.S[s], md.V0) for s in "lr"}
        if verbose:
            print(f"reference bones posed ({len(self.order)}): {' '.join(self.order)}")
            print(f"reference bones left at rest ({len(left)}): {' '.join(left)}")
            print("anchor:", {s: (self.ref_names[ra], bd.p.names[ja]) for s, (ja, ra) in self.anchor.items()},
                  "(reference, source)")

    def pose_ref(self, G):
        bd, Ab = self.bd, self.Ab
        return Ab.pose_turns(transfer_turns(G, bd.p.rest, bd.p.index, Ab.p.index, Ab.p.parent,
                                            self.cfg["bone_map"], self.order))

    def target(self, G, side, Vp=None):
        """(X [region points, 3], info) for one pose of B's globals G and one side."""
        bd, Ab, md = self.bd, self.Ab, self.md
        sd = md.S[side]
        ids = sd["ids"]
        pts = md.first[ids]
        if Vp is None:
            Vp = self.rt.published(bd, G)
        Va, Ga = self.pose_ref(G)
        ja, ra = self.anchor[side]
        M = anchor_align(G[ja], bd.p.rest[ja], Ab.G0[ra], Ga[ra])
        MC = self.car[side].carry(Va) @ M[:3, :3].T + M[:3, 3]
        b = md.beta[:, None]
        X = b * MC + (1 - b) * Vp[pts]
        d = np.linalg.norm(MC - Vp[pts], axis=1)[md.beta == 1] * 1000
        emin, emax, _ = edge_ratio(X, md.V0[ids], *self.edges[side])
        ecar = edge_ratio(MC, md.V0[ids], *self.edges[side])[1]         # the carried surface alone: a correspondence jump shows here
        Y = Vp[md.first].copy()
        Y[ids] = X
        g = md.girth(sd, Y)
        info = {"d_pub_p50": float(np.percentile(d, 50)), "d_pub_p95": float(np.percentile(d, 95)), "d_pub_max": float(d.max()),
                "edge_min": emin, "edge_max": emax, "edge_car_max": ecar, "vol": md.volume(sd, Y) / sd["vol0"],
                **{f"girth_{k}": float(g[k] / self.girth0[side][k]) for k in ("mid_deltoid", "insertion")}}
        return X, info


def fmt(i):
    return (f"d_pub {i['d_pub_p50']:.1f}/{i['d_pub_p95']:.1f}/{i['d_pub_max']:.1f} mm  edge {i['edge_min']:.2f}..{i['edge_max']:.2f} (carried alone max {i['edge_car_max']:.2f})"
            f"  vol {i['vol']:.3f}  girth mid {i['girth_mid_deltoid']:.3f} ins {i['girth_insertion']:.3f}")


def cmd_test(h):
    bd, Ab, md, cfg = h.bd, h.Ab, h.md, h.cfg
    ok_all = True

    def line(name, ok, text):
        nonlocal ok_all
        ok_all &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'} {name}: {text}")

    rng = np.random.default_rng(7)
    R = polar(rng.normal(size=(3, 3)))
    t = rng.normal(size=3)
    for s in "lr":
        car, ids = h.car[s], md.S[s]["ids"]
        P0 = bd.V0[md.first[ids]]
        e = np.abs(car.carry(Ab.V0) - P0).max()
        line(f"T1 {s}", e < 1e-6, f"carry(rest) - P0 max {e:.2e} m")
        e = np.abs(car.carry(Ab.V0 @ R.T + t) - (P0 @ R.T + t)).max()
        line(f"T2 {s}", e < 1e-6, f"rigid motion of the rest: max {e:.2e} m")
    Va, Ga = h.pose_ref(bd.G0)
    dv, dg = np.abs(Va - Ab.V0).max(), np.abs(Ga - Ab.G0).max()
    print(f"   transfer of the rest pose: reference vertices off its rest by {dv:.2e} m, globals by {dg:.2e}")
    Vp0 = h.rt.published(bd, bd.G0)
    for s in "lr":
        ids = md.S[s]["ids"]
        X, _ = h.target(bd.G0, s, Vp0)
        e = np.abs(X - md.V0[ids]).max()
        txt = f"X(rest) - md.V0 max {e:.2e} m"
        if e >= 1e-5:
            txt += (f" | published(rest) - md.V0 {np.abs(Vp0[md.first[ids]] - md.V0[ids]).max():.2e}"
                    f", bd.V0 - md.V0 {np.abs(bd.V0[md.first[ids]] - md.V0[ids]).max():.2e}"
                    f", source G0 - rest {np.abs(bd.G0 - bd.p.rest).max():.2e}")
        line(f"T3 {s}", e < 1e-5, txt)
    for s in "lr":
        car, sd = h.car[s], md.S[s]
        d0 = np.linalg.norm(car.d0, axis=1) * 1000
        bad = ~car.ok
        where = ""
        if bad.any() and "arm" in sd:
            arm = np.asarray(sd["arm"])[bad] > 0.5
            where = f" (arm {int(arm.sum())}, torso {int((~arm).sum())}; their |d0| max {d0[bad].max():.1f} mm)"
        p95 = np.percentile(d0, 95)
        line(f"T4 {s}", p95 <= cfg["d0_p95_stop_mm"],
             f"ok False {int(bad.sum())} of {len(d0)}{where}; |d0| p50 {np.percentile(d0, 50):.2f} p95 {p95:.2f} max {d0.max():.2f} mm")
        if p95 > cfg["d0_p95_stop_mm"]:
            print("STOP: the rest shapes do not agree (|d0| p95 over the limit)")
            return False
    z = np.load(h.OUT / "poses.npz")
    names = [str(x) for x in z["name"]]
    for nm in cfg["dev_poses"]:
        if nm not in names:
            line(f"T5 {nm}", False, "not in poses.npz")
            continue
        i = names.index(nm)
        s = str(z["side"][i])
        X, info = h.target(z["G"][i], s)
        line(f"T5 {nm}", info["edge_car_max"] < 3 and np.isfinite(X).all(), fmt(info))
        if info["edge_car_max"] >= 3:
            ids = md.S[s]["ids"]
            ei, ej = h.edges[s]
            r = edge_ratio(X, md.V0[ids], ei, ej)[2]
            w = np.argsort(-r)[:4]
            car = h.car[s]
            for a, b_, rr in zip(ei[w], ej[w], r[w]):
                print(f"     edge {a}-{b_} ratio {rr:.2f} faces {car.face[a]} {car.face[b_]} ok {car.ok[a]} {car.ok[b_]}"
                      f" |d0| {np.linalg.norm(car.d0[a]) * 1000:.1f} {np.linalg.norm(car.d0[b_]) * 1000:.1f} mm"
                      f" beta {md.beta[a]:.2f} {md.beta[b_]:.2f}")
    print("ALL PASS" if ok_all else "SOME FAILED")
    return ok_all


def table(names, kinds, infos):
    for kd in sorted(set(kinds)):
        rows = [i for i, k in zip(infos, kinds) if k == kd]
        print(f"{kd} ({len(rows)} poses)   min / median / max")
        for key in INFO:
            v = np.array([r[key] for r in rows])
            print(f"  {key:18s} {v.min():8.3f} {np.median(v):8.3f} {v.max():8.3f}")
    for key in ("edge_max", "d_pub_max"):
        w = np.argsort([-i[key] for i in infos])[:5]
        print(f"worst by {key}:")
        for i in w:
            print(f"  {names[i]:28s} {kinds[i]:8s} {fmt(infos[i])}")


def cmd_target(h, poses):
    z = np.load(h.OUT / "poses.npz")
    names = [str(x) for x in z["name"]]
    sel = list(range(len(names)))
    if poses:
        miss = [p for p in poses if p not in names]
        if miss:
            sys.exit(f"not in poses.npz: {miss}")
        sel = [names.index(p) for p in poses]
    X, infos = [], []
    for i in sel:
        x, info = h.target(z["G"][i], str(z["side"][i]))
        X.append(x)
        infos.append(info)
        if poses:
            print(f"{names[i]:28s} {fmt(info)}")
    cfg = h.cfg
    out = h.OUT / (cfg["dev_out"] if poses else cfg["out"])
    params = {**{k: v for k, v in cfg.items()}, "method": "carried_target", "posed": h.order,
              "not_ok": {s: int((~h.car[s].ok).sum()) for s in "lr"}}
    np.savez_compressed(out, X=np.array(X), name=z["name"][sel], side=z["side"][sel], kind=z["kind"][sel],
                        info=json.dumps(infos), params=json.dumps(params))
    table([names[i] for i in sel], [str(z["kind"][i]) for i in sel], infos)
    print(f"wrote {out}  X {np.array(X).shape}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["test", "target"])
    ap.add_argument("--poses", default="", help="comma-separated pose names: a subset, written to the dev file")
    a = ap.parse_args()
    h = Her()
    if a.cmd == "test":
        sys.exit(0 if cmd_test(h) else 1)
    cmd_target(h, [p for p in a.poses.split(",") if p])


if __name__ == "__main__":
    main()
