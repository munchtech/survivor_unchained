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


def ride_weights(mean_w, names, ride, bone_names):
    """params.rigid_ride: [{"match": substring of a mesh name, "weights": {bone: w}, "mix": 0-1 (default 1)}]. The first
    entry whose `match` is in any of the group's mesh `names` replaces the mean blend (mixed with it by `mix`, then
    normalized). Returns (weights, the entry's match or None). An unknown bone is a SystemExit naming it."""
    for e in ride:
        if not any(e["match"] in (n or "") for n in names):
            continue
        g = np.zeros(len(bone_names))
        for bn, w in e["weights"].items():
            if bn not in bone_names:
                raise SystemExit("PIN: rigid_ride bone %r is not one of her joints" % bn)
            g[list(bone_names).index(bn)] += float(w)
        if g.sum() <= 0:
            raise SystemExit("PIN: rigid_ride %r has no weight" % e["match"])
        g = g / g.sum()
        t = float(e.get("mix", 1.0))
        w = (1 - t) * np.asarray(mean_w, float) + t * g
        return w / w.sum(), e["match"]
    return mean_w, None


def _ray_hits(O, D, X, F, reach, k=96):
    """Nearest forward hit (0 < t <= reach) of rays O, D [n, 3] on the faces F of points X: t (inf: none), face, bary."""
    from scipy.spatial import cKDTree as _T
    C = X[F].mean(1)
    k = min(k, len(F))
    _, ci = _T(C).query(O + D * reach * 0.5, k=k)
    ci = ci.reshape(len(O), -1)
    V = X[F[ci]]
    v0, e1, e2 = V[:, :, 0], V[:, :, 1] - V[:, :, 0], V[:, :, 2] - V[:, :, 0]
    d = np.broadcast_to(D[:, None], e2.shape)
    p = np.cross(d, e2)
    det = (e1 * p).sum(2)
    ok = np.abs(det) > 1e-14
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    s = O[:, None] - v0
    u = (s * p).sum(2) * inv
    q = np.cross(s, e1)
    v = (d * q).sum(2) * inv
    t = (e2 * q).sum(2) * inv
    hit = ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (t > 0) & (t <= reach)
    t = np.where(hit, t, np.inf)
    j = t.argmin(1)
    r = np.arange(len(O))
    return t[r, j], ci[r, j], np.c_[1 - u[r, j] - v[r, j], u[r, j], v[r, j]]


def over_ride(B, Q, nrm, spec):
    """params.bend_ride (the brief under the belt, armor-D 16 Nov): a bending garment worn UNDER another piece rides
    that piece where it covers it, so the two move as one there and the under one never comes out through it (the
    brief's top under the belt's pelvis-rigid tasset and back plates, its hinge-ridden hip plates and its rings).
    spec {"over": installed piece id or gltf path, "reach": m (default .06), "ease": m (default .02), "mix": 0-1}:
    a point is covered when a ray out along her normal `nrm` meets one of the over piece's faces (its LOD 0) within
    `reach`; it takes that piece's weights at the hit (barycentric, dense over B.names); a point within `ease` of a
    covered one takes the nearest covered point's, by smoothstep(1 - d / ease), so the ride fades into her skin's own
    below the plate's edge. Returns (covered [n] bool, the target weights [n, len(B.names)], the share f [n])."""
    over = spec["over"]
    if not over.endswith((".gltf", ".glb")):
        over = os.path.join(ROOT, "godot", "art", "armor", over + ".gltf")
    G = _Gl(over)
    Xs, Fs, Ws, o = [], [], [], 0
    for n, m, k, p in prims(G):
        if (m.get("extras") or {}).get("lod") or "JOINTS_0" not in p["attributes"] or "skin" not in n:
            continue
        a = p["attributes"]
        X = G.get(a["POSITION"]).astype(float)
        nm = [G.g["nodes"][j]["name"] for j in G.g["skins"][n["skin"]]["joints"]]
        idx = np.array([B.names.index(x) if x in B.names else -1 for x in nm])
        J, W = bf._weights(G, a)
        Wd = np.zeros((len(X), len(B.names)))
        for c in range(J.shape[1]):
            jj = idx[J[:, c]]
            okc = jj >= 0
            np.add.at(Wd, (np.nonzero(okc)[0], jj[okc]), W[okc, c])
        Wd /= np.maximum(Wd.sum(1, keepdims=True), 1e-12)
        Xs.append(X)
        Fs.append(_faces(G, p, len(X)) + o)
        Ws.append(Wd)
        o += len(X)
    if not Xs:
        raise SystemExit("PIN: bend_ride over %r has no skinned mesh" % over)
    X, F, Wo = np.vstack(Xs), np.vstack(Fs), np.vstack(Ws)
    t, fi, bc = _ray_hits(Q, nrm, X, F, float(spec.get("reach", 0.06)))
    cov = np.isfinite(t)
    # spec "only" {bone: min share} (optional, armor-D r7): only the over piece's faces carrying at least that share
    # of each named bone are ridden (e.g. {"pelvis": .9}: the belt's pelvis-rigid back plates and V, not its rings,
    # strap or thigh-hinged hip plates), so the under piece keeps following her own skin everywhere else
    only = spec.get("only") or {}
    if only and cov.any():
        ic_ = np.nonzero(cov)[0]
        Wf = Wo[F[fi[ic_]]].mean(1)
        keep = np.ones(len(ic_), bool)
        for bn, mn in only.items():
            keep &= (Wf[:, B.names.index(bn)] if bn in B.names else np.zeros(len(ic_))) >= float(mn)
        cov[ic_[~keep]] = False
    T = np.zeros((len(Q), len(B.names)))
    f = np.zeros(len(Q))
    if not cov.any():
        return cov, T, f
    T[cov] = (Wo[F[fi[cov]]] * bc[cov][:, :, None]).sum(1)
    f[cov] = 1.0
    ease = float(spec.get("ease", 0.02))
    un = np.nonzero(~cov)[0]
    if ease > 0 and len(un):
        ic = np.nonzero(cov)[0]
        dd, jn = cKDTree(Q[ic]).query(Q[un])
        x = np.clip(1 - dd / ease, 0, 1)
        f[un] = x * x * (3 - 2 * x)
        T[un] = T[ic[jn]]
    return cov, T, f


def part_names(Q, sels, objs):
    """The authored object (a node of the free mesh, `_glb_objects`) most of a rigid shell's points `Q[sels]` sit on:
    its name, as a {name} for the shell's rigid_ride match (the installed meshes are named by material only:
    `<id>.<slot>.steel` holds both cops and both lame sets). Nearest point, by majority (its LOD points too)."""
    on = list(objs)
    if not on:
        return set()
    A = np.vstack([objs[k] for k in on])
    lab = np.repeat(np.arange(len(on)), [len(objs[k]) for k in on])
    _, j = cKDTree(A).query(Q[np.concatenate(sels)])
    return {on[int(np.bincount(lab[j]).argmax())]}


def _trs(n):
    """A glTF node's local matrix."""
    sys.path.insert(0, os.path.join(ROOT, "tools", "anim"))
    from rig import qmatrix
    M = np.eye(4)
    M[:3, :3] = qmatrix(n.get("rotation", [0, 0, 0, 1.0])) * np.asarray(n.get("scale", [1.0, 1, 1]), float)
    M[:3, 3] = n.get("translation", [0, 0, 0])
    return M


def with_hinges(B):
    """Her body `B` (bf.Body) with her hip hinges (tools/anim/helpers.py SPEC "hinges") as joints of its skin, in
    memory only (her file is never written): each a node under its parent at its pivot, its world rest turn none, its
    inverse bind its rest's inverse, no skin of hers on it (a zero column of B.W). So a piece's rigid_ride can name
    "thigh_hinge_l" (or the tasset hinge, SPEC "tassets": "tasset_hinge") and its bind carries the joint, as the game
    adds it (HerJoints.AddHinges). Safe to call again."""
    import bodies
    if bodies.cur().name != "a":      # (the hinge pivots below are body A's SPEC: another body needs its own)
        bodies.cur().need(os.path.join(bodies.PEOPLE, "body_p1", "rig_helpers.json"),
                          "hip/tasset hinge spec (rig_helpers.json) for the body: tools/anim/helpers.py SPEC is A's")
    sys.path.insert(0, os.path.join(ROOT, "tools", "anim"))
    import helpers as hp
    par = {c: i for i, n in enumerate(B.nodes) for c in n.get("children", [])}

    def world(i):
        return (world(par[i]) if i in par else np.eye(4)) @ _trs(B.nodes[i])

    # (the hip hinges per side, then the centred tasset hinge (SPEC "tassets"): name, parent, the bones it reads, pivot)
    items = [(hg["name"].replace("{s}", s), hg["parent"].replace("{s}", s), [hg["bone"].replace("{s}", s)], hp.hinge_pivot(hg, s))
             for hg in hp.SPEC.get("hinges", []) for s in "lr"]
    items += [(tg["name"], tg["parent"], list(tg["thighs"]), np.asarray(tg["pivot"], float)) for tg in hp.SPEC.get("tassets", [])]
    for nm, pn, reads, pivot in items:
        if nm in B.names or pn not in B.names or any(r not in B.names for r in reads):
            continue
        pi = B.joint_nodes[B.names.index(pn)]
        Hw = np.eye(4)
        Hw[:3, 3] = pivot
        L = np.linalg.inv(world(pi)) @ Hw
        from rig import qfrom_matrix
        node = {"name": nm, "translation": [float(x) for x in L[:3, 3]],
                "rotation": [float(x) for x in qfrom_matrix(L[:3, :3] / np.linalg.norm(L[:3, :3], axis=0))]}
        B.nodes.append(node)
        ni = len(B.nodes) - 1
        B.nodes[pi].setdefault("children", []).append(ni)
        par[ni] = pi
        B.joint_nodes.append(ni)
        B.names.append(nm)
        B.ibm = np.vstack([B.ibm, np.linalg.inv(Hw).T.reshape(1, 16)])
        B.W = np.hstack([B.W, np.zeros((len(B.W), 1))])
    return B


def pin(path, pre, body, B=None, drop=(), ride=(), authored=None, bend=None, fit=None):
    """The staged piece `path` (followed) back on its pre-follow points, her weights and her bind. Returns numbers.
    `drop` (piece params.rigid_drop, bone name prefixes): left out of every rigid shell's blend, the rest renormalized
    (a helm rides Head only: the mean of her skin under its rim took neck_01 and spine_03, and its brim swung off her
    head as she turned it). `authored` (the free mesh file): each rigid shell is also named by its authored object
    (part_names), so a `ride` match can name a part ("cop_l"), not only a material's mesh."""
    B = with_hinges(B or bf.Body(body))
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
    gnames = {}
    mname = [None] * len(Q)
    for (n_, m_, k_, p_), a_, b_ in zip(pr, offs[:-1], offs[1:]):
        for i in inv[a_:b_]:
            if mname[i] is None:
                mname[i] = m_.get("name") or ""
    for c in np.unique(comp):
        sel = np.nonzero(comp == c)[0]
        ks = {key[i] for i in sel}
        if len(sel) >= 3 and len(ks) == 1 and None not in ks:
            kk_ = ks.pop()
            groups.setdefault(kk_, []).append(sel)
            gnames.setdefault(kk_, set()).update(mname[i] for i in sel)
    if authored and ride:
        objs = _glb_objects(authored)
        for kk_, sels in groups.items():
            gnames[kk_] |= part_names(Q, sels, objs)
    Wq, sd = her_weights(B, Q)
    if bend:
        # (params.bend_ride: the bending points under another piece ride it there, over_ride; rigid shells unchanged)
        nrm = B.surface(Q)[4]
        cov_, T_, f_ = over_ride(B, Q, nrm, bend)
        mx_ = float(bend.get("mix", 1.0)) * f_[:, None]
        Wq = (1 - mx_) * Wq + mx_ * T_
        Wq /= np.maximum(Wq.sum(1, keepdims=True), 1e-12)
        res["bend_ride"] = {"covered": int(cov_.sum()), "eased": int(((f_ > 0) & ~cov_).sum()), "points": len(Q)}
    nb = len(B.names)
    TOP = np.zeros((len(Q), 8), int)
    TW = np.zeros((len(Q), 8))
    mesh_names = {gi_: gnames[k_] for gi_, k_ in enumerate(groups)}
    for gi, sels in enumerate(groups.values()):
        sel = np.concatenate(sels)
        rigid[sel] = gi
        mw = Wq[sel].mean(0)
        if drop:
            kd = np.array([not str(nm_).startswith(tuple(drop)) for nm_ in B.names])
            if (mw * kd).sum() > 1e-6:
                mw = mw * kd
        if ride:
            mw, hit = ride_weights(mw, mesh_names.get(gi, ()), ride, B.names)
            if hit is not None:
                res.setdefault("rigid_ride", {})
                res["rigid_ride"][hit] = res["rigid_ride"].get(hit, 0) + 1
        t, w = _top(mw[None], 4)
        TOP[sel, :4], TW[sel, :4] = t[0], w[0]
    bend = rigid < 0
    if fit and bend.any():
        # (params.bend_fit, set per body (l7, 17 Nov): the bending points' weights refit one-sided against her posed
        # skin through her clips, correctives, worn rest and springs as wearcheck poses her (bend_fit.fit))
        import bend_fit
        # (passes: the fit run again from its own result, her motion posed once; each pass's veto is against the last)
        mo_ = bend_fit.her_motion(fit.get("clips"), int(fit.get("step", 1)), fit.get("shapes"), fit.get("hold"))
        Wb = Wq[bend]
        for _ in range(int(fit.get("passes", 1))):
            Wb, rep_ = bend_fit.fit(Q[bend], Wb, list(B.names), fit, mo_)
        Wq = Wq.copy()
        Wq[bend] = Wb
        res["bend_fit"] = rep_
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
    B = with_hinges(B or bf.Body(body))
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
