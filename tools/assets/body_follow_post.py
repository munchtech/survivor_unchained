"""Her outfits, hair and armor pieces carried from the body they were built on (BASE) to the body of record (BODY):
the G3 chain's follow (Body 13 b1, 26 October 2026).

The body of record is BASE plus post-steps on the body alone (Body 5-12: the shoulder rig's ten helper joints
delt/lat/pec/scap/trap _l/_r and eight weights a point, the shoulder reweight and sculpt, the pit re-mesh (its welded
points renumbered, 44665 -> 44513), the 18 shoulder pose shapes, heroine_arm_form's upper-arm rest moves (up to 7 mm),
heroine_arm_lines' front-arm fill (up to 3 mm)). The pieces are exported against BASE and know none of it. Here:

  1. correspondence: each BASE skin point found on BODY by its paint place (same primitive, same UV, the nearest such
     within MATCH_R); a point the re-mesh took away by the closest place on BODY's surface. Its move D and its weights'
     change dW (BODY's minus BASE's, by bone name) are the skin's own.
  2. rest: every piece point near her skin (bind place) moved by D at its closest place on BASE's surface (barycentric),
     whole within NEAR, none past FAR; the move smoothed over the piece's own welded surface (no tear where the
     closest skin flips between arm and side); then within KEEP of her skin the point set back onto its old signed
     distance off her (BODY's surface and normal there), so a garment's clearance (or tuck) is what it was.
  3. weights: the piece point's weights take dW at that place (whole within W_NEAR, none past W_FAR), clipped,
     normalized, eight kept (JOINTS_1/WEIGHTS_1 where a point needs more than four). A piece with weights the same
     over a whole shell (a rigid plate) takes the shell's mean change, so it stays rigid. The helper joints are added
     to the piece's skin (nodes as BODY has them, same rest and inverse bind): the game binds a piece's skin to her
     skeleton by bone name (People.HerOutfit: mi.Skeleton = ".."), so the garment rides the helpers as her skin does.
  4. shapes: BODY's shoulder pose shapes (shoulder_*, ShoulderPsd's 18 slots) carried onto every top, cloak and collar
     (SHAPE_NEAR/SHAPE_FAR) and pauldrons (PAULDRON_NEAR/FAR), the outfits' and the armor's (the armor's lod1/shadow
     meshes with them), as axilla_fold_post.follow does: the skin's nearest points' deltas. Old targets of those
     names replaced.
  5. records: tuck and cover records (armor_tuck/, armor_cover/ beside people/ and armor/) re-keyed from BASE's bind
     points to BODY's; BODY points the re-mesh made take the value of BASE's nearest point there (when it had one).

    python tools/assets/body_follow_post.py BASE_GLB BODY_GLB ART_DIR [--parts outfits,hair,armor] [--dry]

ART_DIR is godot/art (people/ and armor/ under it). Done-mark body_follow (with BODY's sha1) on each file; a marked
file is skipped. Prints FOLLOW lines (the chain's numbers).
"""
import glob
import hashlib
import json
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heroine_neck import _Gl  # noqa: E402
from worn_reaver_post import _sparse, _vn, _ss  # noqa: E402
from shoulder_psd_post import _read_sparse  # noqa: E402
from carry_targets import closest  # noqa: E402
from gltf_compact import compact  # noqa: E402

MARK = "body_follow"
MATCH_R = 0.020                 # m: a BASE point's paint twin on BODY looked for this near
NEAR, FAR = float(os.environ.get("BF_NEAR", 0.04)), float(os.environ.get("BF_FAR", 0.09))
KEEP = (0.010, 0.016)           # m off her skin: the signed distance kept whole within the first, none past the second
PIT_OUT = 0.0005                # m
KEEP_ROUNDS = int(os.environ.get("BF_KEEP_ROUNDS", 4))
SMOOTH_IT = int(os.environ.get("BF_SMOOTH", 12))
W_NEAR, W_FAR = float(os.environ.get("BF_WNEAR", 0.025)), float(os.environ.get("BF_WFAR", 0.06))
SHAPE_NEAR, SHAPE_FAR = 0.06, 0.10          # (shoulder_psd_post's FOLLOW_NEAR/FAR)
PAULDRON_NEAR, PAULDRON_FAR = 0.11, 0.15
SHAPE_K, SHAPE_POW = 3, 4
# sparse shape entries below these are not written (0.1 mm, 0.01 of a unit normal): the fade touched most points by
# hundredths of a millimetre, and 18 shapes on whole tops took heroine_outfit_warden.bin past GitHub's 100 MB (Body 15)
SHAPE_POS_MIN, SHAPE_NOR_MIN = 1e-4, 0.01
SHAPE_PARTS = ("top", "cloak", "collar")
HAIR_WEIGHTS = False            # (hair keeps its own chains' weights; its rest follows)
# pauldrons (a slot): BF_PAUL_HELPERS=fold folds the helper joints' weight change into their parents (the plate rides
# the arm and clavicle, not the deltoid's bulge); BF_PAUL_SHAPES=0 carries no shoulder shapes onto them
PAUL_HELPERS = os.environ.get("BF_PAUL_HELPERS", "on")
PAUL_SHAPES = os.environ.get("BF_PAUL_SHAPES", "1") != "0"


def _say(*a):
    print(*a, flush=True)


def _append(G, data, align=4):
    while len(G.buf) % align:
        G.buf.append(0)
    off = len(G.buf)
    G.buf += data
    G.g["bufferViews"].append({"buffer": 0, "byteOffset": off - G.b0, "byteLength": len(data)})
    return len(G.g["bufferViews"]) - 1


def _add_acc(G, arr, ctype, typ, minmax=False):
    dt = {5126: "<f4", 5123: "<u2", 5121: "u1", 5125: "<u4"}[ctype]
    bv = _append(G, np.ascontiguousarray(arr, dtype=dt).tobytes())
    a = {"bufferView": bv, "componentType": ctype, "count": int(len(arr)), "type": typ}
    if minmax:
        a["min"], a["max"] = np.asarray(arr).min(0).tolist(), np.asarray(arr).max(0).tolist()
    G.g["accessors"].append(a)
    return len(G.g["accessors"]) - 1


def _weights(G, attrs):
    J = np.hstack([G.get(attrs[f"JOINTS_{q}"]).astype(int) for q in range(4) if f"JOINTS_{q}" in attrs])
    W = np.hstack([G.get(attrs[f"WEIGHTS_{q}"]).astype(float) for q in range(4) if f"JOINTS_{q}" in attrs])
    if W.max() > 1.5:
        W = W / (255.0 if W.max() <= 255 else 65535.0)
    return J, W


class Body:
    """Her body's skin (the Heroine node's primitives but skin_head), welded by place: U, F, per-point dense weights
    over the skin's joint names, UVs per copy, the shoulder shapes welded."""

    def __init__(s, path):
        G = s.G = _Gl(path)
        g = G.g
        hn = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
        s.mesh = g["meshes"][hn["mesh"]]
        sk = g["skins"][hn["skin"]]
        s.names = [g["nodes"][j]["name"] for j in sk["joints"]]
        s.ibm = G.get(sk["inverseBindMatrices"]).reshape(-1, 16)
        s.nodes = g["nodes"]
        s.joint_nodes = sk["joints"]
        s.prims = [p for p in s.mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
        P, Fs, UV, Wd, pid, o = [], [], [], [], [], 0
        for k, p in enumerate(s.prims):
            a = p["attributes"]
            X = G.get(a["POSITION"]).astype(float)
            P.append(X)
            Fs.append(G.get(p["indices"]).reshape(-1, 3).astype(int) + o)
            UV.append(G.get(a["TEXCOORD_0"]).astype(float))
            J, W = _weights(G, a)
            d = np.zeros((len(X), len(s.names)))
            np.add.at(d, (np.repeat(np.arange(len(X)), J.shape[1]), J.ravel()), W.ravel())
            Wd.append(d)
            pid.append(np.full(len(X), k))
            o += len(X)
        s.Pc, s.UVc, s.pid = np.vstack(P), np.vstack(UV), np.concatenate(pid)
        _, first, wid = np.unique(np.round(s.Pc / 1e-6).astype(np.int64), axis=0, return_index=True, return_inverse=True)
        s.wid, s.first = wid.ravel(), first
        s.U = s.Pc[first]
        F = s.wid[np.vstack(Fs)]
        s.F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 2] != F[:, 0])]
        s.W = np.vstack(Wd)[first]
        s.N = _vn(s.U, s.F)
        s.tn = (s.mesh.get("extras") or {}).get("targetNames", [])

    def shape(s, name):
        k = s.tn.index(name)
        out = []
        for p in s.prims:
            n = s.G.g["accessors"][p["attributes"]["POSITION"]]["count"]
            t = p.get("targets", [])
            out.append(_read_sparse(s.G, t[k]["POSITION"]) if k < len(t) and "POSITION" in t[k] else np.zeros((n, 3)))
        return np.vstack(out)[s.first]

    def surface(s, Q, X=None):
        """Closest place on the surface (X: its points, default U): distance, face, barycentric, signed distance, normal."""
        X = s.U if X is None else X
        d, f, b = closest(Q, X, s.F, k=24)
        c = (X[s.F[f]] * b[:, :, None]).sum(1)
        N = s.N if X is s.U else _vn(X, s.F)
        n = (N[s.F[f]] * b[:, :, None]).sum(1)
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        return d, f, b, ((Q - c) * n).sum(1), n, c


class Field:
    """BASE -> BODY at each BASE skin point: D (rest move), dW (weight change over BODY's joint names), the twin."""

    def __init__(s, A, B):
        s.A, s.B = A, B
        names = B.names
        miss = [n for n in A.names if n not in names]
        assert not miss, "BASE bones BODY lacks: %s" % miss
        # paint twins: the same primitive (by material) and UV, nearest within MATCH_R
        mA = [A.G.g["materials"][p["material"]].get("name") for p in A.prims]
        mB = [B.G.g["materials"][p["material"]].get("name") for p in B.prims]
        twin = np.full(len(A.U), -1)
        tdist = np.full(len(A.U), np.inf)
        for ka, m in enumerate(mA):
            if m not in mB:
                continue
            kb = mB.index(m)
            ia, ib = np.nonzero(A.pid == ka)[0], np.nonzero(B.pid == kb)[0]
            T = cKDTree(B.UVc[ib])
            cand = T.query_ball_point(A.UVc[ia], 2e-6)
            for i, c in zip(ia, cand):
                if not c:
                    continue
                wb = B.wid[ib[c]]
                dd = np.linalg.norm(B.U[wb] - A.Pc[i], axis=1)
                j = int(np.argmin(dd))
                w = A.wid[i]
                if dd[j] < MATCH_R and dd[j] < tdist[w]:
                    twin[w], tdist[w] = wb[j], dd[j]
        s.twin = twin
        ok = twin >= 0
        # (a twin claimed twice: the nearer keeps it)
        order = np.argsort(tdist)
        seen = set()
        for i in order[ok[order]]:
            if twin[i] in seen:
                twin[i] = -1
            else:
                seen.add(twin[i])
        ok = twin >= 0
        X1 = np.zeros_like(A.U)
        X1[ok] = B.U[twin[ok]]
        Wb = np.zeros((len(A.U), len(names)))
        Wb[ok] = B.W[twin[ok]]
        lost = np.nonzero(~ok)[0]
        if len(lost):
            _, f, b, _, _, c = B.surface(A.U[lost])
            X1[lost] = c
            Wb[lost] = (B.W[B.F[f]] * b[:, :, None]).sum(1)
        s.X1 = X1
        s.D = X1 - A.U
        Wa = np.zeros((len(A.U), len(names)))
        Wa[:, [names.index(n) for n in A.names]] = A.W
        s.dW = Wb - Wa
        s.lost = lost
        # BODY points with no BASE twin (the re-mesh's new points)
        has = np.zeros(len(B.U), bool)
        has[twin[ok]] = True
        s.new = np.nonzero(~has)[0]
        mv = np.linalg.norm(s.D, axis=1)
        _say("FOLLOW field: BASE %d pts, BODY %d; twins %d, re-meshed away %d (placed on BODY's surface), BODY's new %d; "
             "rest move max %.2f mm (%d > 0.5 mm); weight change > 0.05 at %d"
             % (len(A.U), len(B.U), ok.sum(), len(lost), len(s.new), mv.max() * 1000, (mv > 5e-4).sum(),
                (np.abs(s.dW).sum(1) / 2 > 0.05).sum()))
        live = (mv > 1e-5) | (np.abs(s.dW).max(1) > 1e-4)
        s.lo, s.hi = A.U[live].min(0) - FAR, A.U[live].max(0) + FAR


def _rkey(P):
    return np.round(P.astype(np.float32).astype(np.float64) * 1e5).astype(np.int64)


def remap_records(path, fld, dry=False):
    """A tuck/cover record file re-keyed BASE -> BODY; BODY's new points take BASE's nearest point's value."""
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[:4])[0]
    rec = np.frombuffer(b, np.dtype([("k", "<i4", 3), ("v", "<f4")]), n, 4).copy()
    if not n:
        return 0, 0, 0
    kA, kB = _rkey(fld.A.U), _rkey(fld.B.U)
    ia = {tuple(k): i for i, k in enumerate(kA)}
    val = {}
    other = []
    for r in rec:
        i = ia.get(tuple(int(x) for x in r["k"]))
        if i is None:
            # (not a BASE skin point (her head's, or stale already): kept as it is)
            other.append(r)
            continue
        val[i] = float(r["v"])
    out = {}
    for i, v in val.items():
        t = fld.twin[i]
        if t >= 0:
            out[t] = max(out.get(t, 0.0), v)
    # BODY's new points: BASE's nearest point (at its BODY place) with a record
    added = 0
    if len(fld.new) and val:
        T = cKDTree(fld.X1)
        d, j = T.query(fld.B.U[fld.new], k=3)
        for q, dd, jj in zip(fld.new, d, j):
            vs = [val[x] for x, e in zip(jj, dd) if x in val and e < 0.008]
            if vs:
                out[q] = float(np.mean(vs))
                added += 1
    keys = sorted(out)
    nr = np.zeros(len(keys), rec.dtype)
    nr["k"] = kB[keys]
    nr["v"] = [out[q] for q in keys]
    if other:
        nr = np.concatenate([nr, np.array(other, rec.dtype)])
    if not dry:
        open(path, "wb").write(struct.pack("<I", len(nr)) + nr.tobytes())
    return n, len(nr), added


def _weld(P):
    _, first, inv = np.unique(np.round(P / 1e-6).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    return first, inv.ravel()


def _smooth_move(M, Fw, n, it):
    """The move averaged over the piece's welded surface (Jacobi, uniform)."""
    if it <= 0 or not len(Fw):
        return M
    E = np.vstack([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]])
    E = np.vstack([E, E[:, ::-1]])
    deg = np.bincount(E[:, 0], minlength=n).astype(float)
    for _ in range(it):
        S = np.zeros_like(M)
        np.add.at(S, E[:, 0], M[E[:, 1]])
        M = np.where(deg[:, None] > 0, 0.5 * M + 0.5 * S / np.maximum(deg, 1)[:, None], M)
    return M


def _components(Fw, n):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    if not len(Fw):
        return np.arange(n)
    r = np.concatenate([Fw[:, 0], Fw[:, 1], Fw[:, 2]])
    c = np.concatenate([Fw[:, 1], Fw[:, 2], Fw[:, 0]])
    return connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)[1]


def _slot_of(mesh_name, kind):
    parts = mesh_name.split(".")
    if kind == "armor":
        return parts[1] if len(parts) > 1 else ""
    return parts[1] if len(parts) > 1 else ""


def _add_joints(G, B, need):
    """BODY's joints the piece's skin lacks, added (nodes with BODY's local rest under the same parent, BODY's inverse
    bind) to every skin of the file. Returns {name: joint index} per skin."""
    g = G.g
    bp = {}
    for i, n in enumerate(B.nodes):
        for c in n.get("children", []):
            bp[c] = i
    out = []
    for sk in g.get("skins", []):
        names = [g["nodes"][j]["name"] for j in sk["joints"]]
        ibm = G.get(sk["inverseBindMatrices"]).reshape(-1, 16)
        byname = {g["nodes"][j]["name"]: j for j in sk["joints"]}
        # (every joint of BODY's the skin lacks, in BODY's order: an outfit bound to the body's own joint list, as
        # heroine_lod.py asserts; a piece on another list takes only the joints its weights need)
        same = names == B.names[:len(names)]
        add = [nm for nm in B.names if nm not in names and (same or nm in need)]
        for nm in add:
            bj = B.joint_nodes[B.names.index(nm)]
            par = B.nodes[bp[bj]]["name"]
            if par not in byname:
                raise RuntimeError("piece skin lacks %s's parent %s" % (nm, par))
            src = B.nodes[bj]
            node = {"name": nm}
            for k in ("translation", "rotation", "scale"):
                if k in src:
                    node[k] = list(src[k])
            g["nodes"].append(node)
            ni = len(g["nodes"]) - 1
            g["nodes"][byname[par]].setdefault("children", []).append(ni)
            byname[nm] = ni
            sk["joints"].append(ni)
            names.append(nm)
            ibm = np.vstack([ibm, B.ibm[B.names.index(nm)]])
        if add:
            sk["inverseBindMatrices"] = _add_acc(G, ibm.astype(np.float32), 5126, "MAT4")
        out.append({nm: k for k, nm in enumerate(names)})
    return out


def _piece_slot(path, kind):
    if kind != "armor":
        return None
    stem = os.path.basename(path).replace(".gltf", "")
    try:
        return [r["slot"] for r in json.load(open(os.path.join(os.path.dirname(path), "armor_index.json"))) if r["id"] == stem][0]
    except (OSError, IndexError):
        return None


RIGID_MATS = ("steel", "darksteel", "blacksteel", "gold", "bronze", "iron", "rust", "rivetbronze", "claspgold", "bone",
              "amethyst", "shadow")
RIGID = os.environ.get("BF_RIGID", "1") != "0"


def _rigid_groups(G, prims, inv, offs, Fw, n):
    """Rigid shells: welded components of the metal meshes (and the shadow proxy) whose points all carry one weight
    set (skinned rigidly in the game), grouped by that set: [point indices] a group."""
    g = G.g
    key = np.full(n, None, object)
    metal = np.zeros(n, bool)
    for k, (node, m, p) in enumerate(prims):
        mat = m.get("name", "").rsplit(".", 1)[-1]
        a = p["attributes"]
        if not (mat in RIGID_MATS or mat.startswith("gem_")) or "JOINTS_0" not in a or "skin" not in node:
            continue
        sk = g["skins"][node["skin"]]
        nm = [g["nodes"][j]["name"] for j in sk["joints"]]
        J, W = _weights(G, a)
        wi = inv[offs[k]:offs[k + 1]]
        for i, (jr, wr) in enumerate(zip(J, W)):
            key[wi[i]] = tuple(sorted((nm[j], round(float(w), 3)) for j, w in zip(jr, wr) if w > 1e-3))
        metal[wi] = True
    comp = _components(Fw, n)
    groups = {}
    for c in np.unique(comp[metal]):
        sel = np.nonzero(comp == c)[0]
        if not metal[sel].all() or len(sel) < 9:
            continue
        ks = set(key[sel])
        if len(ks) == 1:
            groups.setdefault(ks.pop(), []).append(sel)
    return [np.concatenate(v) for v in groups.values()]


def _kabsch(X, Y):
    """The rotation and translation that best carry points X onto Y (least squares)."""
    cx, cy = X.mean(0), Y.mean(0)
    U, _, Vt = np.linalg.svd((X - cx).T @ (Y - cy))
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return R, cy - cx @ R.T


def _fold_helpers(dw, B, A):
    """dw [n, len(B.names)]: each joint BODY has and BASE lacks (the shoulder helpers) folded into its parent."""
    bp = {}
    for i, n in enumerate(B.nodes):
        for c in n.get("children", []):
            bp[c] = i
    dw = dw.copy()
    for k, nm in enumerate(B.names):
        if nm in A.names:
            continue
        pi = bp[B.joint_nodes[k]]
        while B.nodes[pi]["name"] not in A.names:
            pi = bp[pi]
        dw[:, B.names.index(B.nodes[pi]["name"])] += dw[:, k]
        dw[:, k] = 0
    return dw


def follow_file(path, fld, kind, shapes, dry=False):
    A, B = fld.A, fld.B
    G = _Gl(path)
    g = G.g
    pslot = _piece_slot(path, kind)
    ex = g.setdefault("asset", {}).setdefault("extras", {})
    bsha = fld.bsha
    if (ex.get(MARK) or {}).get("body") == bsha:
        _say("FOLLOW %s: done already" % os.path.basename(path))
        return None
    # every primitive's points (each accessor once), welded across the file
    prims, seen = [], {}
    for mi, n in enumerate(g["nodes"]):
        if "mesh" not in n:
            continue
        m = g["meshes"][n["mesh"]]
        for p in m["primitives"]:
            ai = p["attributes"]["POSITION"]
            if ai in seen:
                continue
            seen[ai] = len(prims)
            prims.append((n, m, p))
    if not prims:
        return None
    Ps = [G.get(p["attributes"]["POSITION"]).astype(float) for _, _, p in prims]
    offs = np.cumsum([0] + [len(x) for x in Ps])
    P = np.vstack(Ps)
    first, inv = _weld(P)
    Q = P[first]
    Fw = []
    for k, (_, _, p) in enumerate(prims):
        f = G.get(p["indices"]).reshape(-1, 3).astype(int) if "indices" in p else np.arange(len(Ps[k])).reshape(-1, 3)
        Fw.append(inv[f + offs[k]])
    Fw = np.vstack(Fw)
    Fw = Fw[(Fw[:, 0] != Fw[:, 1]) & (Fw[:, 1] != Fw[:, 2]) & (Fw[:, 2] != Fw[:, 0])]
    inb = np.nonzero(((Q > fld.lo) & (Q < fld.hi)).all(1))[0]
    res = {"pts": len(P), "rigid": 0, "bend_mm": 0.0, "near": 0, "moved": 0, "max_mm": 0.0, "wpts": 0, "spike_mm": 0.0, "soft": 0, "pit_out": 0}
    M = np.zeros_like(Q)
    if len(inb):
        d, f, b, sd, n0, _ = A.surface(Q[inb])
        Dq = (fld.D[A.F[f]] * b[:, :, None]).sum(1)
        fade = _ss((FAR - d) / (FAR - NEAR))
        M[inb] = Dq * fade[:, None]
        M = _smooth_move(M, Fw, len(Q), SMOOTH_IT if kind != "hair" else 0)
        Q1 = Q + M
        # the signed distance off her skin kept where she is near
        # (each round's correction smoothed over the piece's surface a little: where the closest skin jumps (the
        # pit's crease) a lone point would otherwise spike; the last round unsmoothed for the exact offset)
        kp = inb[d < KEEP[1]]
        if len(kp):
            sd0 = sd[d < KEEP[1]]
            kw = _ss((KEEP[1] - np.abs(sd0)) / (KEEP[1] - KEEP[0]))
            # (over the skin the pit re-mesh replaced, BASE's old faces were folded and its offset there is no
            # measure: those points take the smoothed rounds only, never the exact one, so nothing spikes)
            soft = np.isin(A.F[f[d < KEEP[1]]], fld.lost).any(1)
            res["soft"] = int(soft.sum())
            for r in range(KEEP_ROUNDS):
                _, _, _, s1, n1, _ = B.surface(Q1[kp])
                C = np.zeros_like(Q1)
                C[kp] = ((sd0 - s1) * kw)[:, None] * n1
                if r < KEEP_ROUNDS - 1:
                    C = _smooth_move(C, Fw, len(Q), 3)
                else:
                    C[kp[soft]] = 0
                Q1 += C
            # (and none of those left newly under her skin: out to its old offset, at most PIT_OUT)
            _, _, _, s1, n1, _ = B.surface(Q1[kp])
            want = np.minimum(sd0, PIT_OUT)
            out = soft & (sd0 >= 0) & (s1 < want)
            Q1[kp[out]] += ((want - s1)[out])[:, None] * n1[out]
            res["pit_out"] = int(out.sum())
        M = Q1 - Q
        # rigid shells moved rigidly: the best-fit rotation and translation of their points' moves
        res["rigid"], res["bend_mm"] = 0, 0.0
        if RIGID:
            for sel in _rigid_groups(G, prims, inv, offs, Fw, len(Q)):
                if np.abs(M[sel]).max() < 1e-7:
                    continue
                R, t = _kabsch(Q[sel], Q1[sel])
                X1 = Q[sel] @ R.T + t
                res["bend_mm"] = max(res["bend_mm"], float(np.linalg.norm(X1 - Q1[sel], axis=1).max() * 1000))
                M[sel] = X1 - Q[sel]
                res["rigid"] += len(sel)
        res["near"] = int((d < 0.010).sum())
        mv = np.linalg.norm(M, axis=1)
        res["moved"] = int((mv > 1e-5).sum())
        res["max_mm"] = float(mv.max() * 1000)
        # (a lone point moved off its neighbours' mean: the follow's own crumple, if any)
        res["spike_mm"] = float(np.linalg.norm(2 * (M - _smooth_move(M, Fw, len(Q), 1)), axis=1).max() * 1000)
        # weights' change at the place, faded
        wf = _ss((W_FAR - d) / (W_FAR - W_NEAR))
        dWq = (fld.dW[A.F[f]] * b[:, :, None]).sum(1) * wf[:, None]
    # write positions (and normals turned with the surface: left as they are, the moves are mm on cm-scale curvature)
    for k, (_, _, p) in enumerate(prims):
        ai = p["attributes"]["POSITION"]
        X = (Ps[k] + M[inv[offs[k]:offs[k + 1]]]).astype(np.float32)
        G.put(ai, X)
        a = g["accessors"][ai]
        a["min"], a["max"] = X.min(0).tolist(), X.max(0).tolist()
    # weights
    if len(inb) and (kind != "hair" or HAIR_WEIGHTS):
        dWw = np.zeros((len(Q), len(B.names)))
        dWw[inb] = dWq
        live = np.abs(dWw).max(1) > 1e-4
        if live.any():
            need = set(np.array(B.names)[np.abs(dWw[live]).max(0) > 1e-4])
            jmaps = _add_joints(G, B, need)
            comp = _components(Fw, len(Q))
            for k, (node, m, p) in enumerate(prims):
                a = p["attributes"]
                if "JOINTS_0" not in a or "skin" not in node:
                    continue
                jm = jmaps[node["skin"]]
                sk = g["skins"][node["skin"]]
                pn = [g["nodes"][j]["name"] for j in sk["joints"]]
                J, W = _weights(G, a)
                wi = inv[offs[k]:offs[k + 1]]
                dw = dWw[wi]
                if not (np.abs(dw).max(1) > 1e-4).any():
                    continue
                if PAUL_HELPERS == "fold" and (pslot or _slot_of(m.get("name", ""), kind)) == "pauldrons":
                    dw = _fold_helpers(dw, B, A)
                # dense over BODY's names
                Dn = np.zeros((len(J), len(B.names)))
                bix = np.array([B.names.index(pn[j]) for j in range(len(pn))])
                np.add.at(Dn, (np.repeat(np.arange(len(J)), J.shape[1]), bix[J.ravel()]), W.ravel())
                # rigid shells (one weight set over the whole shell) take the shell's mean change
                cc = comp[wi]
                for c in np.unique(cc[np.abs(dw).max(1) > 1e-4]):
                    sel = cc == c
                    if np.abs(Dn[sel] - Dn[sel][0]).max() < 1e-3 and sel.sum() > 8:
                        dw[sel] = dw[sel].mean(0)
                Nw = np.clip(Dn + dw, 0, None)
                Nw[Nw < 1e-4] = 0
                Nw /= np.maximum(Nw.sum(1, keepdims=True), 1e-12)
                top = np.argsort(-Nw, 1)[:, :8]
                tw = np.take_along_axis(Nw, top, 1)
                tw /= np.maximum(tw.sum(1, keepdims=True), 1e-12)
                tj = np.array([jm.get(nm, 0) for nm in B.names])[top]
                tj[tw <= 0] = 0
                wide = (tw[:, 4:] > 0).any()
                # (the joints' own component type kept where it holds the skin: heroine_lod joins by type)
                jt = g["accessors"][a["JOINTS_0"]]["componentType"]
                jt = jt if jt == 5123 or len(jm) <= 256 else 5123
                jd = np.uint8 if jt == 5121 else np.uint16
                a["JOINTS_0"] = _add_acc(G, tj[:, :4].astype(jd), jt, "VEC4")
                a["WEIGHTS_0"] = _add_acc(G, tw[:, :4].astype(np.float32), 5126, "VEC4")
                if wide:
                    a["JOINTS_1"] = _add_acc(G, tj[:, 4:].astype(jd), jt, "VEC4")
                    a["WEIGHTS_1"] = _add_acc(G, tw[:, 4:].astype(np.float32), 5126, "VEC4")
                else:
                    a.pop("JOINTS_1", None)
                    a.pop("WEIGHTS_1", None)
                res["wpts"] += int((np.abs(dw).max(1) > 1e-4).sum())
            # (one weight layout over the file: where any primitive took eight, every skinned one carries the second
            # set, zeros where unused; heroine_lod joins a material's primitives attribute by attribute)
            if any("JOINTS_1" in p["attributes"] for _, _, p in prims):
                for node, m, p in prims:
                    a = p["attributes"]
                    if "JOINTS_0" in a and "JOINTS_1" not in a:
                        n = g["accessors"][a["POSITION"]]["count"]
                        jt = g["accessors"][a["JOINTS_0"]]["componentType"]
                        a["JOINTS_1"] = _add_acc(G, np.zeros((n, 4), np.uint8 if jt == 5121 else np.uint16), jt, "VEC4")
                        a["WEIGHTS_1"] = _add_acc(G, np.zeros((n, 4), np.float32), 5126, "VEC4")
    # shapes
    res["shaped"] = 0
    if shapes and kind != "hair":
        res["shaped"] = _shapes(G, prims, Ps, M, inv, offs, fld, shapes, kind, path)
    ex[MARK] = {"body": bsha, "near_mm": [NEAR * 1000, FAR * 1000], "keep_mm": [KEEP[0] * 1000, KEEP[1] * 1000],
                "weights_mm": [W_NEAR * 1000, W_FAR * 1000]}
    g["buffers"][0]["byteLength"] = len(G.buf) - G.b0
    if not dry:
        G.save()
        if path.endswith(".gltf"):
            # repack: the replaced targets' old views go, and an all-zero second weight set is dropped
            compact(path, SHAPE_POS_MIN, SHAPE_NOR_MIN)
    return res


def _shapes(G, prims, Ps, M, inv, offs, fld, shapes, kind, path):
    g = G.g
    B = fld.B
    tree = cKDTree(B.U)
    names = [nm for nm, _ in shapes]
    total = 0
    meshes_done = set()
    stem = os.path.basename(path).replace(".gltf", "")
    piece_slot = None
    if kind == "armor":
        try:
            piece_slot = [r["slot"] for r in json.load(open(os.path.join(os.path.dirname(path), "armor_index.json"))) if r["id"] == stem][0]
        except (OSError, IndexError):
            piece_slot = None
    for k, (node, m, p) in enumerate(prims):
        slot = piece_slot if kind == "armor" else _slot_of(m.get("name", ""), kind)
        if slot in SHAPE_PARTS:
            near, far = SHAPE_NEAR, SHAPE_FAR
        elif slot == "pauldrons" and PAUL_SHAPES:
            near, far = PAULDRON_NEAR, PAULDRON_FAR
        else:
            continue
        mid = g["meshes"].index(m)
        if mid in meshes_done:
            continue
        meshes_done.add(mid)
        tn = list((m.get("extras") or {}).get("targetNames", []))
        # (old targets of these names out; every primitive of the mesh keeps the same list)
        keep = [i for i, t in enumerate(tn) if t not in names]
        for pp in m["primitives"]:
            t = pp.get("targets", [])
            pp["targets"] = [t[i] for i in keep if i < len(t)]
            if not pp["targets"]:
                pp.pop("targets")
        tn = [tn[i] for i in keep]
        for pp in m["primitives"]:
            X = G.get(pp["attributes"]["POSITION"]).astype(float)
            d, j = tree.query(X, k=SHAPE_K)
            w = 1 / np.maximum(d, 1e-4) ** SHAPE_POW
            w /= w.sum(1, keepdims=True)
            fade = 1 - _ss((d[:, 0] - near) / (far - near))
            Ff = G.get(pp["indices"]).reshape(-1, 3).astype(int) if "indices" in pp else np.arange(len(X)).reshape(-1, 3)
            binb = G.buf
            for _, D in shapes:
                Dp = (D[j] * w[..., None]).sum(1) * fade[:, None]
                Dp[np.linalg.norm(Dp, axis=1) < SHAPE_POS_MIN] = 0
                ip = np.nonzero(np.abs(Dp).max(1) > 0)[0]
                t = {"POSITION": _sparse_g(G, len(X), ip, Dp[ip])}
                if "NORMAL" in pp["attributes"]:
                    dN = _vn(X + Dp, Ff) - _vn(X, Ff)
                    dN[np.linalg.norm(dN, axis=1) < SHAPE_NOR_MIN] = 0
                    inn = np.nonzero(np.abs(dN).max(1) > 0)[0]
                    t["NORMAL"] = _sparse_g(G, len(X), inn, dN[inn])
                pp.setdefault("targets", []).append(t)
                total += len(ip)
        m.setdefault("extras", {})["targetNames"] = tn + names
        m["weights"] = [0.0] * len(m["extras"]["targetNames"])
    return total


def _sparse_g(G, n, idx, val):
    if not len(idx):
        idx, val = np.zeros(1, int), np.zeros((1, 3))
    iv = _append(G, idx.astype("<u4").tobytes())
    vv = _append(G, val.astype("<f4").tobytes())
    a = {"componentType": 5126, "count": int(n), "type": "VEC3",
         "sparse": {"count": int(len(idx)), "indices": {"bufferView": iv, "componentType": 5125}, "values": {"bufferView": vv}},
         "min": [float(x) for x in np.minimum(val.min(0), 0)], "max": [float(x) for x in np.maximum(val.max(0), 0)]}
    G.g["accessors"].append(a)
    return len(G.g["accessors"]) - 1


def files_of(art, parts):
    pe, ar = os.path.join(art, "people"), os.path.join(art, "armor")
    out = []
    if "outfits" in parts:
        out += [(f, "outfit") for f in sorted(glob.glob(os.path.join(pe, "heroine_outfit_*.gltf"))) if not f.endswith("_lod.gltf")]
    if "hair" in parts:
        out += [(f, "hair") for f in sorted(glob.glob(os.path.join(pe, "heroine_hair_*.gltf")))]
    if "armor" in parts:
        out += [(f, "armor") for f in sorted(glob.glob(os.path.join(ar, "*.gltf")))]
    return out


def main(argv):
    a = [x for x in argv if not x.startswith("--")]
    base, body, art = a[0], a[1], a[2]
    parts = set((argv[argv.index("--parts") + 1] if "--parts" in argv else "outfits,hair,armor").split(","))
    dry = "--dry" in argv
    A, B = Body(base), Body(body)
    fld = Field(A, B)
    fld.bsha = hashlib.sha1(open(body, "rb").read()).hexdigest()[:8]
    shapes = [(nm, B.shape(nm)) for nm in B.tn if nm.startswith("shoulder_")]
    _say("FOLLOW shapes carried: %d (%s .. %s)" % (len(shapes), shapes[0][0] if shapes else "-", shapes[-1][0] if shapes else "-"))
    for f, kind in files_of(art, parts):
        r = follow_file(f, fld, kind, shapes, dry)
        if r:
            _say("FOLLOW %-34s %7d pts: %6d within 10 mm of her, %6d moved (max %.2f mm, off its neighbours %.2f; %d over the re-meshed pit, %d of them set back out of her), %6d reweighted, %7d shape moves; %d points in rigid shells moved rigidly (bend taken out: max %.2f mm)"
                 % (os.path.basename(f), r["pts"], r["near"], r["moved"], r["max_mm"], r["spike_mm"], r["soft"], r["pit_out"], r["wpts"], r["shaped"], r["rigid"], r["bend_mm"]))
    # records
    subs = []
    if "outfits" in parts:
        subs += [os.path.join(art, "people", s) for s in ("armor_tuck", "armor_cover")]
    if "armor" in parts:
        subs += [os.path.join(art, "armor", s) for s in ("armor_tuck", "armor_cover")]
    tot = [0, 0, 0]
    for d in subs:
        for fp in sorted(glob.glob(os.path.join(d, "*.bin"))):
            n0, n1, add = remap_records(fp, fld, dry)
            tot = [tot[0] + n0, tot[1] + n1, tot[2] + add]
    _say("FOLLOW records: %d -> %d (BODY's new points recorded: %d)" % tuple(tot))


if __name__ == "__main__":
    main(sys.argv[1:])
