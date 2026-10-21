"""The lamed pauldrons' proof numbers on her skin as the game draws it (armor 10, b_design_spec section 1, Proof):
her final skin (godot/art/people/heroine.glb) tucked by the piece's own armor_tuck record and posed as wearcheck poses
it (tools/anim/skin.py, her helpers and correctives), never the build scene's body.

  standoff  the cop's inner face off her tucked skin at rest (all, its neck rim: s < medial + 12 mm), p50/p99/max mm
  order     each lame's outer face under the plate above (cop > lame1 > lame2), wherever they overlapped at rest, in
            every frame of the clips: the least clearance, and the frames under --order-min (0.5 mm)

The plates are told apart by their blend (pl_row: one weight row per plate); the cop is the row with the least arm
share, its inner face the vertices whose normal faces her skin, on its largest island (the rolled edges are their own).

    python tools/armor/paul_check.py [--piece plate_pauldrons_plain] [--clips c1,..] [--step 2] [--out <json>]
                                     [--no-order]
"""
import json
import os
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wearcheck as wc  # noqa: E402  (its skin, its tuck reading, its clips)

skin = wc.skin


def closest_on_tris(Q, V, T, kd, k=24):
    """Each point's nearest point on triangles T of points V (candidates: the k nearest triangle centres)."""
    _, cand = kd.query(Q, k=k)
    A, B, C = V[T[cand, 0]], V[T[cand, 1]], V[T[cand, 2]]
    q = Q[:, None, :]
    ab, ac, ap = B - A, C - A, q - A
    d1, d2 = (ab * ap).sum(-1), (ac * ap).sum(-1)
    bp = q - B
    d3, d4 = (ab * bp).sum(-1), (ac * bp).sum(-1)
    cp = q - C
    d5, d6 = (ab * cp).sum(-1), (ac * cp).sum(-1)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) > 1e-20, va + vb + vc, 1e-20)
    v, w = vb / den, vc / den
    X = A + ab * v[..., None] + ac * w[..., None]
    # (the regions outside the face: vertices and edges)
    def put(m, P_):
        nonlocal X
        X = np.where(m[..., None], P_, X)
    t_ab = d1 / np.where(np.abs(d1 - d3) > 1e-20, d1 - d3, 1e-20)
    t_ac = d2 / np.where(np.abs(d2 - d6) > 1e-20, d2 - d6, 1e-20)
    t_bc = (d4 - d3) / np.where(np.abs((d4 - d3) + (d5 - d6)) > 1e-20, (d4 - d3) + (d5 - d6), 1e-20)
    put((vc <= 0) & (d1 >= 0) & (d3 <= 0), A + ab * t_ab[..., None])
    put((vb <= 0) & (d2 >= 0) & (d6 <= 0), A + ac * t_ac[..., None])
    put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), B + (C - B) * t_bc[..., None])
    put((d1 <= 0) & (d2 <= 0), A)
    put((d3 >= 0) & (d4 <= d3), B)
    put((d6 >= 0) & (d5 <= d6), C)
    dist = np.linalg.norm(X - q, axis=-1)
    j = dist.argmin(1)
    r = np.arange(len(Q))
    return X[r, j], dist[r, j]


def islands(T, n):
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    g = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    return connected_components(g, directed=False)[1]


def stats(d):
    d = np.asarray(d) * 1000
    return {"n": int(len(d)), "p50": round(float(np.median(d)), 2), "p99": round(float(np.percentile(d, 99)), 2),
            "max": round(float(d.max()), 2)} if len(d) else None


def main(argv):
    opt = lambda n, d: argv[argv.index(n) + 1] if n in argv else d
    pid = opt("--piece", "plate_pauldrons_plain")
    clips = opt("--clips", ",".join(wc.CLIPS)).split(",")
    step = int(opt("--step", "2"))
    omin = float(opt("--order-min", "0.5")) / 1000
    rows = wc.catalogue({pid})
    r = rows[0]
    pj = json.load(open(os.path.join(wc.ROOT, "godot", "art", "armor", "src", pid, "piece.json"), encoding="utf-8"))
    S_MED = pj["params"]["cop"]["medial"]
    sk = skin.Skeleton.load(skin.SKELETONS / "heroine_skeleton.json")
    steel = [m for m in r["meshes"] if m.endswith(".steel")]
    files = [(skin.PEOPLE / "heroine.glb", lambda n: n == "Heroine", "skin"),
             (skin.PEOPLE / "heroine.glb", lambda n: n == "HeroineHead", "head"),
             (skin.Path(r["path"]), lambda n, s=frozenset(steel): n in s, "garment")]
    body = skin.Body(sk, files, skin.Jiggle(sk, 1, 1), label="her", helpers=True)
    P0 = body.P
    isk = np.nonzero(body.kind == "skin")[0]
    ish = np.nonzero(body.kind != "garment")[0]
    ig = np.nonzero(body.kind == "garment")[0]
    loc = np.full(len(P0), -1)
    loc[ish] = np.arange(len(ish))
    TS = loc[body.T[(body.kind[body.T] != "garment").all(1)]]
    N0 = np.zeros_like(P0)
    N0[ish] = skin._normals(P0[ish], TS)
    tk = np.zeros(len(P0))
    gone = np.zeros(len(P0), bool)
    tk[isk], gone[isk] = wc.tuck_of(r["tuck_path"], P0[isk])
    TSk = body.T[(body.kind[body.T] == "skin").all(1)]
    TSk_drawn = TSk[~gone[TSk].all(1)]
    Ptk = P0 - N0 * tk[:, None]
    out = {"piece": pid, "tucked_skin_points": int((tk > 0).sum()), "gone_points": int(gone.sum())}

    # the plates: by blend row, per side
    TG = body.T[(body.kind[body.T] == "garment").all(1)]
    key = np.round(np.concatenate([body.J[ig], body.W[ig]], 1), 4)
    _, row_of = np.unique(key, axis=0, return_inverse=True)
    row_of = np.asarray(row_of).ravel()
    rowv = np.full(len(P0), -1)
    rowv[ig] = row_of
    heads = {n: body.rest[j][:3, 3] for n, j in sk.index.items()}
    arm_bones = {sd: [j for n, j in sk.index.items() if n.endswith("_" + sd) and n.split("_")[0] in ("upperarm", "lowerarm", "hand")] for sd in "lr"}
    plates = {}
    for sd in "lr":
        ctr = heads[f"upperarm_{sd}"]
        ax = heads[f"lowerarm_{sd}"] - ctr
        ax /= np.linalg.norm(ax)
        side = np.sign(ctr[0])
        mine = ig[np.sign(P0[ig, 0]) == side]
        info = []
        for rv in np.unique(rowv[mine]):
            v = mine[rowv[mine] == rv]
            if len(v) < 30:
                continue
            arm = sum(body.W[v[0], k] for k in range(body.W.shape[1]) if body.J[v[0], k] in arm_bones[sd])
            info.append((arm, v))
        info.sort(key=lambda t: t[0])
        plates[sd] = {"F": (ctr, ax), "rows": info}
        out.setdefault("arm_share", {})[sd] = [round(float(a), 3) for a, _ in info]

    # standoff at rest, on the tucked skin (and, for the record, the untucked final skin)
    kd_tk = cKDTree(Ptk[TSk_drawn].mean(1))
    kd_un = cKDTree(P0[TSk].mean(1))
    for sd in "lr":
        ctr, ax = plates[sd]["F"]
        cop = plates[sd]["rows"][0][1]
        inc = np.zeros(len(P0), bool)
        inc[cop] = True
        Tc = TG[inc[TG].all(1)]
        nrm = np.zeros_like(P0)
        fn = np.cross(P0[Tc[:, 1]] - P0[Tc[:, 0]], P0[Tc[:, 2]] - P0[Tc[:, 0]])
        for k in range(3):
            np.add.at(nrm, Tc[:, k], fn)
        lab = islands(Tc, len(P0))
        big = np.bincount(lab[cop]).argmax()
        cand = cop[lab[cop] == big]
        X, d = closest_on_tris(P0[cand], Ptk, TSk_drawn, kd_tk)
        inner = ((X - P0[cand]) * nrm[cand]).sum(1) > 0
        q = cand[inner]
        s_ = (P0[q] - ctr) @ ax
        neck = s_ < S_MED + 0.012
        _, du = closest_on_tris(P0[q], P0, TSk, kd_un)
        out.setdefault("standoff_cop_mm", {})[sd] = {"all": stats(d[inner]), "neck_rim": stats(d[inner][neck])}
        out.setdefault("standoff_cop_untucked_mm", {})[sd] = {"all": stats(du), "neck_rim": stats(du[neck])}
        # (where the neck rim stands farthest off: s mm, bearing deg (pl_limb_frame's: 0 up the outer arm, + front))
        ref = ctr + np.array([0.02 * (1 if sd == "l" else -1), 0.06, 0.0])
        e0 = (ref - ctr) - ax * ((ref - ctr) @ ax)
        e0 /= np.linalg.norm(e0)
        e1 = np.cross(ax, e0) * (1 if sd == "l" else -1)
        rr = P0[q] - ctr - np.outer(s_, ax)
        th = np.degrees(np.arctan2(rr @ e1, rr @ e0))
        wn = np.nonzero(neck)[0][np.argsort(-d[inner][neck])[:5]]
        out.setdefault("neck_rim_worst_at", {})[sd] = [[round(float(s_[i] * 1000), 1), round(float(th[i]), 0), round(float(d[inner][i] * 1000), 1)] for i in wn]
        wa = np.argsort(-d[inner])[:5]
        out.setdefault("cop_worst_at", {})[sd] = [[round(float(s_[i] * 1000), 1), round(float(th[i]), 0), round(float(d[inner][i] * 1000), 1)] for i in wa]
        tkq = tk[isk][np.linalg.norm(P0[isk] - P0[q].mean(0), axis=1) < 0.06]
        out.setdefault("tuck_near_cop", {})[sd] = {"tucked": int((tkq > 0).sum()), "max_mm": round(float(tkq.max() * 1000), 2) if len(tkq) else 0}
    print(json.dumps(out, indent=1), flush=True)
    if "--no-order" in argv:
        json.dump(out, open(opt("--out", os.path.join(os.environ.get("TEMP", "."), "paul_check.json")), "w"), indent=1)
        return

    # lame order: each lower plate's outer face vs the plate above's inner face, along the lower plate's normal
    tests = []
    for sd in "lr":
        rws = plates[sd]["rows"]
        for up_i in range(len(rws) - 1):
            up, lo = rws[up_i][1], rws[up_i + 1][1]
            m_up = np.zeros(len(P0), bool)
            m_up[up] = True
            m_lo = np.zeros(len(P0), bool)
            m_lo[lo] = True
            Tu, Tl = TG[m_up[TG].all(1)], TG[m_lo[TG].all(1)]
            nl = np.zeros_like(P0)
            fl = np.cross(P0[Tl[:, 1]] - P0[Tl[:, 0]], P0[Tl[:, 2]] - P0[Tl[:, 0]])
            for k in range(3):
                np.add.at(nl, Tl[:, k], fl)
            nl[lo] /= np.maximum(np.linalg.norm(nl[lo], axis=1, keepdims=True), 1e-12)
            # (the lower plate's outer face: its normal facing away from her skin)
            _, nsk = cKDTree(P0[isk]).query(P0[lo])
            outer = lo[((P0[lo] - P0[isk[nsk]]) * nl[lo]).sum(1) > 0]
            # (overlapped at rest: a ray out from its outer face meets the plate above within 8 mm)
            kd_u = cKDTree(P0[Tu].mean(1))
            O, D = P0[outer], nl[outer]
            _, cand = kd_u.query(O, k=min(48, len(Tu)))
            t, fa, _, _ = wc.cast(O, D, P0[Tu[cand]])
            g, _, _ = wc.signed_gap(t, fa, 0.008)
            ov = np.isfinite(g)
            tests.append({"side": sd, "pair": f"{['cop', 'lame1', 'lame2'][up_i]}>{['cop', 'lame1', 'lame2'][up_i + 1]}",
                          "pts": outer[ov], "candv": Tu[cand[ov]], "rest": g[ov], "Tl": Tl, "lo": lo,
                          "min": np.full(ov.sum(), np.inf), "bad": 0, "frames": 0, "worst": (np.inf, None, None)})
    need = np.unique(np.concatenate([np.r_[x["pts"], x["candv"].ravel(), x["Tl"].ravel()] for x in tests]))
    at = np.full(len(P0), -1)
    at[need] = np.arange(len(need))
    for c in clips:
        clip = body.clip(c)
        frames = body.frames(clip)
        for f in range(0, len(frames), step):
            Pp = body.pose(frames[f], need)
            for x in tests:
                Tl = x["Tl"]
                fl = np.cross(Pp[at[Tl[:, 1]]] - Pp[at[Tl[:, 0]]], Pp[at[Tl[:, 2]]] - Pp[at[Tl[:, 0]]])
                nl = np.zeros((len(need), 3))
                for k in range(3):
                    np.add.at(nl, at[Tl[:, k]], fl)
                D = nl[at[x["pts"]]]
                D /= np.maximum(np.linalg.norm(D, axis=1, keepdims=True), 1e-12)
                O = Pp[at[x["pts"]]]
                t, fa, _, _ = wc.cast(O, D, Pp[at[x["candv"]]])
                g, _, _ = wc.signed_gap(t, fa, 0.02)
                gg = np.where(np.isfinite(g), g, np.inf)
                x["min"] = np.minimum(x["min"], gg)
                x["frames"] += 1
                if (gg < omin).any():
                    x["bad"] += 1
                k = int(gg.argmin())
                if gg[k] < x["worst"][0]:
                    x["worst"] = (float(gg[k]), c, f)
        print(f"paul_check: {c}", flush=True)
    out["order"] = [{"side": x["side"], "pair": x["pair"], "samples": int(len(x["pts"])),
                     "rest_min_mm": round(float(x["rest"].min() * 1000), 2) if len(x["rest"]) else None,
                     "min_mm": round(float(x["min"].min() * 1000), 2) if len(x["min"]) else None,
                     "frames_under": x["bad"], "frames": x["frames"], "worst": f"{x['worst'][1]}@{x['worst'][2]}"} for x in tests]
    print(json.dumps(out["order"], indent=1))
    json.dump(out, open(opt("--out", os.path.join(os.environ.get("TEMP", "."), "paul_check.json")), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
