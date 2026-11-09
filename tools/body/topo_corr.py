#!/usr/bin/env python
"""P1 B1 step 1: OUR topology's correspondence onto the reference surface (MakeHuman hm08's woman, CC0: the shape and
proportion reference only), so any hm08 slider body can be carried onto our vertices.

    python tools/body/topo_corr.py [--tiers close,play]      # writes tools/body/base/topo_corr_{tier}.npz + checks

Derived from: (b) the reference = loopplan.json "reference" (tools/body/out/run_a/stage/close.npz: base_woman.json's
woman, stage 2-3 placed, subdivided once), on which topo_build.py laid our vertices; (a) the game's need: our
sliders, landmarks and weights are keyed to OUR vertex order, never to MakeHuman ids, so MakeHuman enters only as a
surface we read positions off.

Method: each of our vertices -> its closest point on the reference's close surface (the body quads, each split 0-2;
candidates from a KD tree of triangle centres, the exact point-triangle distance), stored as the triangle's three
close-point ids + barycentrics, and the vertex's offset from that point in a LOCAL FRAME (n = the barycentric blend of
the surface's area-weighted vertex normals; t1 = the triangle's first edge made square to n; t2 = n x t1). The frame
turns with the surface on a deformed body, so an off-surface vertex keeps its height and side; on the reference it is
exact by construction (round trip = float error). (The interpolated normal rather than the face normal: no jump
across triangle edges for the few vertices that sit off the surface.)

    corr = load(tier); P_close = Reference().close(Vs)    # an hm08 body (MakeHuman space, every point) placed as ours
    V = evaluate(corr, P_close)                           # -> our vertices

Reference(): replays pipeline stages 2-3 (stage_place, forms.compose, stage_tiers) on run_a's base.npz exactly as
build.py made the reference, so Reference().close(None) IS the reference's close surface (checked), and close(Vs)
is a slider body hung from the same head the same way (forms.join: the head and its ring held).
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
REF_DIR = os.path.join(HERE, "out", "run_a", "stage")
TOPO_DIR = os.path.join(HERE, "out", "topo")
BASE_DIR = os.path.join(HERE, "base")
SPEC = os.path.join(HERE, "specs", "base_woman.json")


# ------------------------------------------------------------------------------------------- the reference --
class Reference:
    """The reference body (run_a) and the placement that made it, to carry any hm08 body into our frame."""

    def __init__(self):
        import headmatch as hm
        import pipeline
        from gl import Glb
        from sliders import load_spec
        self.hm = hm
        self.spec = load_spec(SPEC)
        z = np.load(os.path.join(REF_DIR, "base.npz"))
        self.base = {k: z[k] for k in z.files if not k.startswith("g:")}
        self.base["groups"] = {k[2:]: z[k] for k in z.files if k.startswith("g:")}
        A = Glb(os.path.join(REPO, self.spec["ref"]))
        self.pl = pipeline.stage_place(self.base, A, {})
        r = np.load(os.path.join(REF_DIR, "close.npz"))
        self.F = r["F"]
        self.P_ref = r["P"]
        self.T = np.concatenate([self.F[:, [0, 1, 2]], self.F[:, [0, 2, 3]]])

    def composed(self, Vs=None):
        """The base dict with V = the slider body joined under the head (forms.compose), MakeHuman space."""
        import forms
        b = dict(self.base)
        if Vs is not None:
            b["Vs"] = np.asarray(Vs, float)
        return forms.compose(b, self.pl, self.spec, {})

    def close(self, Vs=None):
        """The close-tier points (glTF, the reference's order) of the hm08 body Vs (None: the reference itself)."""
        import stages
        ti = stages.stage_tiers(self.composed(Vs), self.pl, self.spec, {})
        return self.hm.to_gltf(ti["P2"])

    def world(self, Vs=None):
        """(composed base, to_world): skeleton.py's landmark frame for the hm08 body Vs."""
        import stages
        b = self.composed(Vs)
        ti = stages.stage_tiers(b, self.pl, self.spec, {})
        return b, (lambda P: self.hm.to_gltf(ti["body_place"](P)))


# ------------------------------------------------------------------------------------------- geometry --
def vertex_normals(P, T):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    N = np.zeros_like(P)
    for k in range(3):
        np.add.at(N, T[:, k], n)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-20)


def closest_on_tris(X, A, B, C):
    """Per row: the closest point to X on triangle ABC (Ericson), as barycentrics (u, v, w)."""
    ab, ac, ap = B - A, C - A, X - A
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = X - B
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = X - C
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-30, 1e-30, va + vb + vc)
    v, w = vb / den, vc / den
    bary = np.stack([1 - v - w, v, w], 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        # edges and vertices (the region tests in order of precedence, last wins below so reverse it)
        cases = [
            ((va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0), lambda: np.stack(
                [np.zeros_like(d1), 1 - (d4 - d3) / ((d4 - d3) + (d5 - d6)), (d4 - d3) / ((d4 - d3) + (d5 - d6))], 1)),
            ((vb <= 0) & (d2 >= 0) & (d6 <= 0), lambda: np.stack(
                [1 - d2 / (d2 - d6), np.zeros_like(d1), d2 / (d2 - d6)], 1)),
            ((vc <= 0) & (d1 >= 0) & (d3 <= 0), lambda: np.stack(
                [1 - d1 / (d1 - d3), d1 / (d1 - d3), np.zeros_like(d1)], 1)),
            ((d6 >= 0) & (d5 <= d6), lambda: np.tile([0.0, 0, 1], (len(X), 1))),
            ((d3 >= 0) & (d4 <= d3), lambda: np.tile([0.0, 1, 0], (len(X), 1))),
            ((d1 <= 0) & (d2 <= 0), lambda: np.tile([1.0, 0, 0], (len(X), 1))),
        ]
        for m, f in cases:
            if m.any():
                bary[m] = f()[m]
    return np.nan_to_num(bary)


def closest_point(X, P, T, k=24):
    """Closest point on the triangle mesh (P, T): (triangle id, barycentrics [n,3], distance)."""
    cen = P[T].mean(1)
    rad = np.linalg.norm(P[T] - cen[:, None], axis=2).max(1)
    tree = cKDTree(cen)
    best_d = np.full(len(X), np.inf)
    best_t = np.zeros(len(X), np.int64)
    best_b = np.zeros((len(X), 3))
    _, cand = tree.query(X, k=k)
    for j in range(k):
        t = cand[:, j]
        b = closest_on_tris(X, P[T[t, 0]], P[T[t, 1]], P[T[t, 2]])
        q = (b[:, :, None] * P[T[t]]).sum(1)
        d = np.linalg.norm(X - q, axis=1)
        m = d < best_d
        best_d[m], best_t[m], best_b[m] = d[m], t[m], b[m]
    # guarantee: any triangle whose bounding sphere comes nearer than the best found is tested too
    r_max = rad.max()
    todo = np.where(best_d > 1e-5)[0]          # (on the surface to 0.01 mm: nothing nearer can exist)
    for i in todo:
        near = tree.query_ball_point(X[i], best_d[i] + r_max)
        if len(near) <= k:
            continue
        t = np.array(near)
        b = closest_on_tris(np.repeat(X[i][None], len(t), 0), P[T[t, 0]], P[T[t, 1]], P[T[t, 2]])
        q = (b[:, :, None] * P[T[t]]).sum(1)
        d = np.linalg.norm(X[i] - q, axis=1)
        j = int(np.argmin(d))
        if d[j] < best_d[i]:
            best_d[i], best_t[i], best_b[i] = d[j], t[j], b[j]
    return best_t, best_b, best_d


def frames(P, T, N, tri, bary):
    """The local frame (t1, t2, n) at the barycentric points: n the blended vertex normal, t1 edge 0 square to n."""
    n = (bary[:, :, None] * N[T[tri]]).sum(1)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
    e = P[T[tri, 1]] - P[T[tri, 0]]
    t1 = e - n * (e * n).sum(1, keepdims=True)
    t1 /= np.maximum(np.linalg.norm(t1, axis=1, keepdims=True), 1e-20)
    return t1, np.cross(n, t1), n


# ------------------------------------------------------------------------------------------- the correspondence --
def build(V, P, T):
    tri, bary, dist = closest_point(V, P, T)
    N = vertex_normals(P, T)
    q = (bary[:, :, None] * P[T[tri]]).sum(1)
    t1, t2, n = frames(P, T, N, tri, bary)
    d = V - q
    off = np.stack([(d * t1).sum(1), (d * t2).sum(1), (d * n).sum(1)], 1)
    return {"tri": T[tri].astype(np.int32), "bary": bary, "off": off, "dist": dist}


def evaluate(corr, P, T=None):
    """Our vertices on the close surface P (any hm08 body in our frame: Reference().close(Vs)). T: the reference's
    triangles (the normals' support); default the triangles stored in corr."""
    T = corr["T"] if T is None else T
    N = vertex_normals(P, T)
    tri3, bary, off = corr["tri"], corr["bary"], corr["off"]
    q = (bary[:, :, None] * P[tri3]).sum(1)
    n = (bary[:, :, None] * N[tri3]).sum(1)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
    e = P[tri3[:, 1]] - P[tri3[:, 0]]
    t1 = e - n * (e * n).sum(1, keepdims=True)
    t1 /= np.maximum(np.linalg.norm(t1, axis=1, keepdims=True), 1e-20)
    t2 = np.cross(n, t1)
    return q + off[:, :1] * t1 + off[:, 1:2] * t2 + off[:, 2:] * n


def load(tier):
    z = np.load(os.path.join(BASE_DIR, f"topo_corr_{tier}.npz"))
    return {k: z[k] for k in z.files}


def stats_mm(D):
    e = np.linalg.norm(D, axis=1) * 1000
    return {"p50": round(float(np.percentile(e, 50)), 4), "p95": round(float(np.percentile(e, 95)), 4),
            "max": round(float(e.max()), 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiers", default="close,play")
    a = ap.parse_args()
    ref = Reference()
    P0 = ref.close(None)
    replay = stats_mm(P0 - ref.P_ref)
    print("replay of the reference (stages 2-3 on run_a base.npz) vs close.npz, mm:", replay)
    assert replay["max"] < 1e-3, "the replay must be the reference"
    os.makedirs(BASE_DIR, exist_ok=True)
    rep = {"replay_mm": replay}
    for tier in a.tiers.split(","):
        z = np.load(os.path.join(TOPO_DIR, f"{tier}.npz"))
        V = z["V"].astype(float)
        c = build(V, ref.P_ref, ref.T)
        Vr = evaluate({**c, "T": ref.T}, ref.P_ref)
        rt = stats_mm(Vr - V)
        Vr2 = evaluate({**c, "T": ref.T}, P0)
        off = np.abs(c["off"][:, 2]) * 1000
        r = {"vertices": int(len(V)), "round_trip_mm": rt, "round_trip_replay_mm": stats_mm(Vr2 - V),
             "normal_offset_mm": {"p50": round(float(np.percentile(off, 50)), 4),
                                  "p95": round(float(np.percentile(off, 95)), 4), "max": round(float(off.max()), 3),
                                  "over_1mm": int((off > 1).sum())},
             "tangent_offset_max_mm": round(float(np.abs(c["off"][:, :2]).max() * 1000), 4),
             "pass": bool(rt["p95"] <= 0.1 and rt["max"] <= 0.5)}
        print(tier, json.dumps(r))
        np.savez_compressed(os.path.join(BASE_DIR, f"topo_corr_{tier}.npz"), tri=c["tri"],
                            bary=c["bary"].astype(np.float64), off=c["off"].astype(np.float64), T=ref.T.astype(np.int32),
                            n_close=np.int64(len(ref.P_ref)))
        rep[tier] = r
    with open(os.path.join(BASE_DIR, "topo_corr.json"), "w") as f:
        json.dump({"about": "topo_corr.py's check (P1 B1 step 1): round trip on the reference, mm.", **rep}, f, indent=1)
    assert all(rep[t]["pass"] for t in a.tiers.split(","))


if __name__ == "__main__":
    main()
