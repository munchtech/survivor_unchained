"""Stages 3-6 of the base build (build.py; stage 2 is pipeline.stage_place)."""
import json
import os

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

import headmatch as hm

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
HEADS = ["HeroineEyes", "HeroineHead", "HeroineLashes", "HeroineTeeth", "HeroineTongue"]


def smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def laplacian(F, n):
    k = F.shape[1]
    e = np.concatenate([F[:, [i, (i + 1) % k]] for i in range(k)])
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    A = ((A + A.T) > 0).astype(float)
    return (sp.diags(np.asarray(A.sum(1)).ravel()) - A).tocsr()


def harmonic(L, known, vals, free):
    """Values on `free` points harmonic (L x = 0) given `vals` on `known` and 0 on every other point."""
    x = np.zeros((L.shape[0], vals.shape[1]))
    x[known] = vals
    Lff = L[free][:, free].tocsc()
    rhs = -(L[free] @ x)
    solve = spl.factorized(Lff)
    x[free] = np.stack([solve(np.ascontiguousarray(rhs[:, k])) for k in range(vals.shape[1])], 1)
    return x


def stage_tiers(base, pl, spec, rep):
    """3: the close tier: every skin face subdivided once (pl["Sub"]); the head's faces dropped; the body placed
    (`body_place`), its ring snapped onto the head's, the fit's move there eased into the body below."""
    V = base["V"]
    s = pl["sim"][0]
    F2, U2 = pl["F2"], pl["U2"]
    P2mh = pl["Sub"] @ V
    head_q = np.zeros(len(F2), bool)
    head_q[pl["head_quads"]] = True
    BF = F2[~head_q]
    inhead = np.zeros(len(P2mh), bool)
    inhead[F2[head_q].ravel()] = True
    inbody = np.zeros(len(P2mh), bool)
    inbody[BF.ravel()] = True
    ring = np.where(inhead & inbody)[0]
    ease = spec["neck_ease_m"]
    c = P2mh[ring].mean(0)
    Tb = hm.place(c[None], pl["sim"])[0] - s * c
    Tb[0] = 0.0

    def body_place(P):
        """The head's similarity at and above SPLIT; below it eased, over `neck_ease_m`, to the same scale upright and
        on her middle (x = 0): MakeHuman's body stays symmetric and the head's few degrees of turn are the neck's."""
        P = np.asarray(P, float)
        Ph = hm.place(P, pl["sim"])
        w = smooth01(1 + hm.s_split(Ph) / ease)[:, None]
        return w * Ph + (1 - w) * (s * P + Tb)
    P2 = body_place(P2mh)
    inv = -np.ones(len(P2), np.int64)
    inv[pl["match"]] = np.arange(len(pl["match"]))
    ring_A = inv[ring]
    D = pl["HPw"][ring_A] - P2[ring]
    L = laplacian(BF, len(P2))
    zone = inbody & (hm.s_split(P2) > -spec["fit_ease_m"])
    zone[ring] = False
    P2 = P2 + harmonic(L, ring, D, np.where(zone)[0])
    P2[ring] = pl["HPw"][ring_A]
    G = hm.to_gltf(P2[inbody])
    rep["tiers"] = {"close_tris_body": int(2 * len(BF)), "ring_points": int(len(ring)),
                    "ring_fit_move_max_mm": round(float(np.linalg.norm(D, axis=1).max()) * 1000, 2),
                    "body_move_m": [round(float(x), 5) for x in Tb], "feet_lowest_m": round(float(G[:, 1].min()), 4),
                    "top_m": round(float(hm.to_gltf(pl["HPw"])[:, 1].max()), 4)}
    return {"P2": P2, "BF": BF, "U2": U2[~head_q], "ring": ring, "ring_A": ring_A, "inbody": inbody,
            "body_place": body_place}


def load_mh(name):
    d = os.path.join(os.environ.get("APPDATA", ""), "Blender Foundation", "Blender", "4.5", "extensions",
                     "user_default", "mpfb", "data", "rigs", "standard", name)
    with open(d) as f:
        return json.load(f)


def stage_skeleton(base, ti, rep):
    """4."""
    import skeleton as sk
    with open(os.path.join(HERE, "skeleton.json")) as f:
        skel = json.load(f)
    rig, wts = load_mh("rig.default.json"), load_mh("weights.default.json")["weights"]
    names, par, worlds, ends, info = sk.place_skeleton(skel, base, rig, wts,
                                                         lambda P: hm.to_gltf(ti["body_place"](P)))
    rep["skeleton"] = info
    return {"skel": skel, "names": names, "parents": par, "worlds": worlds, "ends": ends, "mh_rig": rig, "mh_w": wts}


def stage_weights(base, pl, ti, sk, A, spec, rep):
    """5 (weights.py's steps), and the head's: A's mapped by bone name; the body's ring takes them, eased below."""
    import weights as wt
    names, par = sk["names"], sk["parents"]
    V = base["V"]
    W0, owner = wt.map_mh(sk["skel"], sk["mh_rig"], sk["mh_w"], len(V), names)
    pairs = wt.mirror_pairs(V)
    W0 = wt.symmetrize(W0, pairs, names)
    W = np.asarray(pl["Sub"] @ W0)
    P = hm.to_gltf(ti["P2"])
    frames = {n: sk["worlds"][i] for i, n in enumerate(names)}
    tails = {n: sk["ends"][n][1] for n in names}
    for side in ("l", "r"):
        W = wt.chain_split(W, P, names, sk["ends"], side)
        W = wt.shares(W, P, names, frames, side)
        W = wt.points(W, P, names, frames, side)
        W = wt.muscles(W, P, names, par, tails, side)
        W = wt.breast(W, P, names, sk["ends"], side)
    W = np.maximum(W, 0)
    W /= np.maximum(W.sum(1, keepdims=True), 1e-12)
    sA = A.skeleton()
    amap = spec["head_bone_map"]
    jmap = np.array([names.index(amap.get(n, n)) if amap.get(n, n) in names else -1 for n in sA.names])
    head = A.mesh("HeroineHead")
    Hw = np.zeros((len(head.P), len(names)))
    for k in range(head.J.shape[1]):
        jj = jmap[head.J[:, k]]
        assert (jj[head.W[:, k] > 0] >= 0).all(), "a head bone with no counterpart"
        np.add.at(Hw, (np.arange(len(head.P)), np.maximum(jj, 0)), head.W[:, k] * (jj >= 0))
    Hw /= Hw.sum(1, keepdims=True)
    ringW = Hw[pl["head_uniq"][ti["ring_A"]]]
    blend = spec["ring_blend_m"]
    L = laplacian(ti["BF"], len(P))
    sd = hm.s_split(ti["P2"])
    band = ti["inbody"] & (sd > -blend - 0.03)
    band[ti["ring"]] = False
    Hx = np.maximum(harmonic(L, ti["ring"], ringW, np.where(band)[0]), 0)
    Hx /= np.maximum(Hx.sum(1, keepdims=True), 1e-12)
    b = (1 - smooth01(-sd / blend)) * band
    b[ti["ring"]] = 1.0
    W = b[:, None] * Hx + (1 - b[:, None]) * W
    J, Wk = wt.cap(W, wt.RULES["cap"])
    rep["weights"] = {"mh_bones_mapped": len(owner), "base_mirror_pairs": int((pairs >= 0).sum()),
                      "max_influences": int((Wk > 0).sum(1).max()), "rules": "tools/body/weights.py RULES"}
    return {"J": J, "W": Wk, "jmap_head": np.maximum(jmap, 0)}


def vertex_normals(P, T):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    N = np.zeros_like(P)
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def stage_export(spec, pl, ti, sk, wt_, A, out, rep):
    """6: body.glb (glbwrite.py)."""
    import glbwrite
    BF, U2 = ti["BF"], ti["U2"]
    corner_p = BF.ravel()
    corner_uv = U2.reshape(-1, 2)
    key = np.concatenate([corner_p[:, None].astype(np.float64), np.round(corner_uv * 2 ** 20)], 1)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel()
    vp = corner_p[first]                                   # each glTF vertex's point
    Q = inv.reshape(-1, 4)
    T = np.stack([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]], 1).reshape(-1, 3)
    Pg = hm.to_gltf(ti["P2"])
    Tp = np.stack([BF[:, [0, 1, 2]], BF[:, [0, 2, 3]]], 1).reshape(-1, 3)
    Np = vertex_normals(Pg, Tp)
    Pv = Pg.astype(np.float32)
    head = A.mesh("HeroineHead")
    hv = pl["head_uniq"][ti["ring_A"]]
    Pv[ti["ring"]] = head.P[hv]                            # the ring: the head's points as stored
    Np[ti["ring"]] = head.N[hv]                            # and its normals, so the seam lights as one
    UV = corner_uv[first].copy()
    UV[:, 1] = 1.0 - UV[:, 1]                              # Blender's v up -> glTF's v down
    body = {"node": "Heroine", "material": spec["body_material"], "P": Pv[vp], "N": Np[vp], "UV": UV, "T": T,
            "J": wt_["J"][vp], "W": wt_["W"][vp]}
    skel = {"names": sk["names"], "parents": sk["parents"], "worlds": sk["worlds"], "scale": spec.get("bone_scale", {})}
    glbwrite.write(os.path.join(out, "body.glb"), os.path.join(REPO, spec["ref"]), skel, body, HEADS, wt_["jmap_head"],
                   extras={"body_base": {"spec": rep["spec"], "skeleton": "tools/body/skeleton.json", "version": 1}})
    ht = int(sum(len(A.mesh(h).T) for h in HEADS))
    rep["export"] = {"body_vertices": int(len(vp)), "close_tris_body": int(len(T)), "head_tris": ht,
                     "close_tris_whole": int(len(T)) + ht}


def write_rig(sk, out):
    names, worlds = sk["names"], sk["worlds"]
    axes = {n: {"x": [round(float(v), 6) for v in worlds[names.index(n)][:3, 0]], "flexion": "+X"}
            for n in ("lowerarm_l", "lowerarm_r", "calf_l", "calf_r")}
    with open(os.path.join(HERE, "base_drive.json")) as f:
        drive = json.load(f)
    rig = {"poser": "tools.body.base_drive", "body_mesh": "Heroine", "close_meshes": ["HeroineHead"],
           "roles": {"upperarm": "upperarm_{s}", "lowerarm": "lowerarm_{s}", "hand": "hand_{s}", "thigh": "thigh_{s}",
                     "calf": "calf_{s}", "foot": "foot_{s}"},
           "hinge": {"elbow": "local_x", "knee": "local_x"}, "axes": axes, "correctives": [], "helpers": drive["helpers"]}
    with open(os.path.join(out, "rig.json"), "w") as f:
        json.dump(rig, f, indent=1)
