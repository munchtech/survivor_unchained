"""A free mesh's exact install on the shipped body (lane D, 16 Nov 2026): piece_ship.py's step for a `style: mesh` piece.

A free mesh is modelled at heroine.glb's rest (docs/armor/PIECE_SCHEMA.md "Free meshes"), but build.py builds on a blend
body that is not heroine.glb (re-meshed; arm rest moves), and the follow then carried the mesh off its authored points.
In exact mode the build runs with ARMOR_EXACT=1 (no push-out against the blend's skin: its points stay the file's), the
follow onto heroine.glb runs only for what it carries besides positions (the tuck re-keyed to her points, her helper
joints), and then, here, on the staged gltf:
  1. positions: every point back to its pre-follow place (the staged build before the follow, `pre/`), i.e. the
     authored mesh itself (its LODs as piece_lod made them from it);
  2. weights: her skin's own at the closest place on her surface (barycentric over heroine.glb's eight-weight skin,
     helpers included), eight kept; a rigid shell (a welded component whose built weights are one set: the `_rigid`
     objects, their rivets with them) rides ONE blend, the mean of hers over all its points, four kept;
  3. bind: every joint's inverse bind and rest taken from heroine.glb by name (the game binds by name: a joint bound
     at the blend's rest would draw the piece off its points);
then the follow runs once more with heroine.glb as both bodies (the identity: no move, no weight change) to carry her
shoulder shapes at the authored points. measure() gives the numbers the ship gates on.

    python tools/armor/pin_shipped.py MEASURE <installed gltf> <pre gltf> <body glb> [<authored glb>]
"""
import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "assets"))
import body_follow_post as bf  # noqa: E402
from heroine_neck import _Gl  # noqa: E402
from gltf_compact import compact  # noqa: E402

EXACT_MAX_MM = 0.5          # the gate: no point of the installed piece further than this from its authored place


def prims(G):
    """(node, mesh, primitive index, primitive) once per POSITION accessor, nodes with meshes in file order."""
    out, seen = [], set()
    for n in G.g["nodes"]:
        if "mesh" not in n:
            continue
        m = G.g["meshes"][n["mesh"]]
        for k, p in enumerate(m["primitives"]):
            ai = p["attributes"]["POSITION"]
            if ai not in seen:
                seen.add(ai)
                out.append((n, m, k, p))
    return out


def _faces(G, p, n):
    return G.get(p["indices"]).reshape(-1, 3).astype(int) if "indices" in p else np.arange(n).reshape(-1, 3)


def _keys(G, n, p):
    """Each point's weight set (bone name, weight to 3 places), or None unskinned."""
    a = p["attributes"]
    if "JOINTS_0" not in a or "skin" not in n:
        return [None] * G.g["accessors"][a["POSITION"]]["count"]
    nm = [G.g["nodes"][j]["name"] for j in G.g["skins"][n["skin"]]["joints"]]
    J, W = bf._weights(G, a)
    return [tuple(sorted((nm[j], round(float(w), 3)) for j, w in zip(jr, wr) if w > 1e-3)) for jr, wr in zip(J, W)]


def her_weights(B, Q):
    """Her skin's dense weights (over B.names) at the closest place on her surface to each of Q, and the signed
    distance off her there."""
    d, f, b, sd, _, _ = B.surface(Q)
    return (B.W[B.F[f]] * b[:, :, None]).sum(1), sd


def _top(W, k):
    W = np.where(W < 1e-4, 0.0, W)
    top = np.argsort(-W, 1)[:, :k]
    tw = np.take_along_axis(W, top, 1)
    tw /= np.maximum(tw.sum(1, keepdims=True), 1e-12)
    return top, tw


def pin(path, pre, body, B=None, drop=()):
    """The staged piece `path` (followed) back on its pre-follow points, her weights and her bind. Returns numbers.
    `drop` (piece params.rigid_drop, bone name prefixes): left out of every rigid shell's blend, the rest renormalized
    (a helm rides Head only: the mean of her skin under its rim took neck_01 and spine_03, and its brim swung off her
    head as she turned it)."""
    B = B or bf.Body(body)
    G, Gp = _Gl(path), _Gl(pre)
    g = G.g
    pr = prims(G)
    pre_of = {(m.get("name"), k): (n, p) for n, m, k, p in prims(Gp)}
    res = {"follow_moved_mm": 0.0}
    Ps, Ks, Fs, o = [], [], [], 0
    for n, m, k, p in pr:
        n0, p0 = pre_of[(m.get("name"), k)]
        X0 = Gp.get(p0["attributes"]["POSITION"]).astype(np.float32)
        X = G.get(p["attributes"]["POSITION"])
        if len(X0) != len(X):
            raise SystemExit("PIN: %s prim %d has %d points, %d before the follow" % (m.get("name"), k, len(X), len(X0)))
        res["follow_moved_mm"] = max(res["follow_moved_mm"], float(np.abs(X - X0).max() * 1000) if len(X) else 0.0)
        ai = p["attributes"]["POSITION"]
        G.put(ai, X0)
        g["accessors"][ai]["min"], g["accessors"][ai]["max"] = X0.min(0).tolist(), X0.max(0).tolist()
        Ps.append(X0.astype(float))
        Ks += _keys(Gp, n0, p0)
        Fs.append(_faces(G, p, len(X)) + o)
        o += len(X)
    offs = np.cumsum([0] + [len(x) for x in Ps])
    P = np.vstack(Ps)
    first, inv = bf._weld(P)
    Q = P[first]
    Fw = inv[np.vstack(Fs)]
    Fw = Fw[(Fw[:, 0] != Fw[:, 1]) & (Fw[:, 1] != Fw[:, 2]) & (Fw[:, 2] != Fw[:, 0])]
    comp = bf._components(Fw, len(Q))
    key = [None] * len(Q)
    for i, kk in zip(inv, Ks):
        if key[i] is None:
            key[i] = kk
    # rigid shells: welded components whose built points all carry one weight set, grouped by that set
    rigid = np.full(len(Q), -1)
    groups = {}
    for c in np.unique(comp):
        sel = np.nonzero(comp == c)[0]
        ks = {key[i] for i in sel}
        if len(sel) >= 3 and len(ks) == 1 and None not in ks:
            groups.setdefault(ks.pop(), []).append(sel)
    Wq, sd = her_weights(B, Q)
    nb = len(B.names)
    TOP = np.zeros((len(Q), 8), int)
    TW = np.zeros((len(Q), 8))
    for gi, sels in enumerate(groups.values()):
        sel = np.concatenate(sels)
        rigid[sel] = gi
        mw = Wq[sel].mean(0)
        if drop:
            kd = np.array([not str(nm_).startswith(tuple(drop)) for nm_ in B.names])
            if (mw * kd).sum() > 1e-6:
                mw = mw * kd
        t, w = _top(mw[None], 4)
        TOP[sel, :4], TW[sel, :4] = t[0], w[0]
    bend = rigid < 0
    if bend.any():
        TOP[bend], TW[bend] = _top(Wq[bend], 8)
    dense = np.zeros((len(Q), nb))
    np.put_along_axis(dense, TOP, TW, 1)
    res["rigid_shells"] = len(groups)
    res["rigid_points"] = int((~bend).sum())
    res["bend_points"] = int(bend.sum())
    res["weight_diff_max"] = float(np.abs(dense[bend] - Wq[bend]).max()) if bend.any() else 0.0
    res["weight_diff_p99"] = float(np.percentile(np.abs(dense[bend] - Wq[bend]).max(1), 99)) if bend.any() else 0.0
    res["clear_min_mm"] = float(sd[bend].min() * 1000) if bend.any() else None
    res["inside_her"] = int((sd[bend] < 0).sum())
    # her bind: every joint she has at her rest and inverse bind; the joints the weights need added
    need = set(np.array(B.names)[np.unique(TOP[TW > 0])])
    jmaps = bf._add_joints(G, B, need)
    ibm_d = 0.0
    for sk in g.get("skins", []):
        ibm = G.get(sk["inverseBindMatrices"]).reshape(-1, 16).astype(float)
        for r, j in enumerate(sk["joints"]):
            nm = g["nodes"][j]["name"]
            if nm in B.names:
                bi = B.names.index(nm)
                ibm_d = max(ibm_d, float(np.abs(ibm[r] - B.ibm[bi]).max()))
                ibm[r] = B.ibm[bi]
                src = B.nodes[B.joint_nodes[bi]]
                for t in ("translation", "rotation", "scale"):
                    g["nodes"][j].pop(t, None)
                    if t in src:
                        g["nodes"][j][t] = list(src[t])
        sk["inverseBindMatrices"] = bf._add_acc(G, ibm.astype(np.float32), 5126, "MAT4")
    res["bind_changed_max"] = ibm_d
    for k, (node, m, _, p) in enumerate(pr):
        a = p["attributes"]
        if "JOINTS_0" not in a or "skin" not in node:
            continue
        jm = jmaps[node["skin"]]
        wi = inv[offs[k]:offs[k + 1]]
        tw = TW[wi]
        tj = np.array([jm.get(nm, 0) for nm in B.names])[TOP[wi]]
        tj[tw <= 0] = 0
        jt = g["accessors"][a["JOINTS_0"]]["componentType"]
        jt = jt if jt == 5123 or len(jm) <= 256 else 5123
        jd = np.uint8 if jt == 5121 else np.uint16
        a["JOINTS_0"] = bf._add_acc(G, tj[:, :4].astype(jd), jt, "VEC4")
        a["WEIGHTS_0"] = bf._add_acc(G, tw[:, :4].astype(np.float32), 5126, "VEC4")
        a["JOINTS_1"] = bf._add_acc(G, tj[:, 4:].astype(jd), jt, "VEC4")
        a["WEIGHTS_1"] = bf._add_acc(G, tw[:, 4:].astype(np.float32), 5126, "VEC4")
    # (the identity follow that comes next must run: its done-mark cleared)
    ex = g.setdefault("asset", {}).setdefault("extras", {})
    ex.pop(bf.MARK, None)
    ex["exact_install"] = {"body": bf.hashlib.sha1(open(body, "rb").read()).hexdigest()[:8], "rigid_shells": len(groups)}
    g["buffers"][0]["byteLength"] = len(G.buf) - G.b0
    G.save()
    compact(path, bf.SHAPE_POS_MIN, bf.SHAPE_NOR_MIN)
    return res


def _glb_objects(path):
    """{node name: its points} of a mesh file (identity transforms: the contract's). Nodes sharing a name are one
    source part (a plate and its gold, one material each: the importer reads them as `<name>`, `<name>.001` and puts
    them on ONE blend), so their points join."""
    G = _Gl(path)
    out = {}
    for n in G.g["nodes"]:
        if "mesh" in n:
            pts = [G.get(p["attributes"]["POSITION"]).astype(float) for p in G.g["meshes"][n["mesh"]]["primitives"]]
            nm = n.get("name", "")
            out[nm] = np.vstack([out[nm]] + pts) if nm in out else np.vstack(pts)
    return out


def measure(path, pre, body, authored=None, B=None):
    """The installed piece against its authored points and her skin: largest move off the pre-follow points (every
    mesh, LODs too); with the authored file: its points against the full meshes' (both ways), the weights at the
    points of its bending objects against hers at the closest place, and the distinct blends over each `_rigid`
    object's points (1: it never bends); the shoulder shapes carried."""
    B = B or bf.Body(body)
    G, Gp = _Gl(path), _Gl(pre)
    pre_of = {(m.get("name"), k): p for n, m, k, p in prims(Gp)}
    out = {"move_max_mm": 0.0, "points": 0, "shapes": 0}
    full, fullD = [], []
    for n, m, k, p in prims(G):
        X = G.get(p["attributes"]["POSITION"]).astype(float)
        X0 = Gp.get(pre_of[(m.get("name"), k)]["attributes"]["POSITION"]).astype(float)
        out["move_max_mm"] = max(out["move_max_mm"], float(np.linalg.norm(X - X0, axis=1).max() * 1000))
        out["points"] += len(X)
        out["shapes"] = max(out["shapes"], len(p.get("targets", [])))
        a = p["attributes"]
        if (m.get("extras") or {}).get("lod") or "JOINTS_0" not in a or "skin" not in n:
            continue
        nm = [G.g["nodes"][j]["name"] for j in G.g["skins"][n["skin"]]["joints"]]
        J, W = bf._weights(G, a)
        D = np.zeros((len(X), len(B.names)))
        bix = np.array([B.names.index(x) if x in B.names else 0 for x in nm])
        np.add.at(D, (np.repeat(np.arange(len(J)), J.shape[1]), bix[J.ravel()]), W.ravel())
        full.append(X)
        fullD.append(D)
    if not authored:
        return out
    F, FD = np.vstack(full), np.vstack(fullD)
    kd = cKDTree(F)
    objs = _glb_objects(authored)
    A = np.vstack(list(objs.values()))
    out["installed_to_authored_mm"] = float(cKDTree(A).query(F)[0].max() * 1000)
    out["authored_to_installed_mm"] = float(kd.query(A)[0].max() * 1000)
    out["bend_weight_diff_max"], out["rigid_blends"] = 0.0, {}
    for name, X in objs.items():
        _, j = kd.query(X)
        D = FD[j]
        if name.endswith("_rigid"):
            out["rigid_blends"][name] = len({tuple(np.round(r, 4)) for r in D})
        else:
            Wq, _ = her_weights(B, F[j])
            out["bend_weight_diff_max"] = max(out["bend_weight_diff_max"], float(np.abs(D - Wq).max()))
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "MEASURE":
        print(json.dumps(measure(a[1], a[2], a[3], a[4] if len(a) > 4 else None), indent=1))
