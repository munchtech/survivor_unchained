"""Her arms' edge loops: new SURFACE at the elbow, the armpit's folds and the deltoid, her shape exactly kept (Body 23,
28 Oct 2026).

Six rounds of scripted reshaping could not give her arm a front armpit fold or an elbow corner: every fold attempt made
a knot or a fin, because her arm (densified by split/flip/relax: ~5 mm triangles) has no edge loops there. The sculpt
candidates need loops first. This step adds them and nothing else:

  INDEX-PRESERVING  every original vertex keeps its index and its exact bytes (every attribute, every morph target);
                    new vertices are APPENDED per primitive and the index buffers rewritten (tuck maps, the neck graft
                    npz, breast records and outfit follow all key on the old ids).
  EXACT SHAPE       every new vertex lies on an old edge (so on the old triangles): cuts are exact splits along iso-lines
                    of smooth scalar fields (marching triangles on the piecewise-linear field), then the split
                    triangles retriangulated (a quad's diagonal: the larger minimum angle); refinement is 1-to-4 at
                    edge midpoints with red-green closure. No vertex moves.
  ATTRIBUTES        per new vertex, from its edge's two ends at the split's t: NORMAL (renormalized), TEXCOORD_n,
                    COLOR_n, JOINTS/WEIGHTS (the corners' influences merged by weight, the top 8 kept, renormalized),
                    every morph target's POSITION and NORMAL deltas. A seam edge (its two triangles on different
                    vertex ids) gets one new vertex per side, at the same place.
  NO SLIVERS        a crossing within SNAP (0.5 mm) of an end routes the cut through that vertex; open edges are never
                    split (their count is kept).

WHERE (both arms; each side in its own bone frames, left-canonical: the right side's points and joints mirrored x ->
-x, so the fields are mirror images; her right arm is NOT her left's mirror vertex for vertex: median 2 mm apart):
  elbow         rings round the arm: iso-lines of the position along the elbow's axis (the upper arm's and forearm's
                directions averaged, through the elbow joint): 4 mm apart within +-12 mm, 6 mm out to +-30 mm; then
                1-to-4 over the olecranon (behind the joint) and along the inner crease (front, on the joint's ring)
  front fold    3 cuts 4 mm apart along the RIM of the pit's front opening (her rest arm hangs out: the pit is an
                open tunnel under the shoulder): the contour where her smoothed normal turns toward the front, an arch
                from her chest wall over the opening's top into her arm; field = signed distance to that rim
  back fold     1 cut along the back opening's rim (the lat / teres edge); then 1-to-4 over the pit's roof
  deltoid       2 cuts along the deltopectoral groove (her front seen straight on), 2 along each of its front and back
                borders converging on its V ~45% down the outer upper arm (the upper arm's (s, phi) chart; points from
                arm_anatomy_post's heads and relief bands): signed distance to a quadratic through 3 chart points
A LOOP MAP (json): per arm and feature, each cut's vertex ids in order along it (per primitive, all copies), so the
sculptors can address them.

    python tools/assets/arm_loops_post.py IN.glb OUT.glb [--map loop_map.json]
Done-mark arm_loops (a marked body is refused). Not registered in heroine_body_post.py (the sculpt candidates' input).
"""
import json
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heroine_neck import _Gl, _CT, _NC  # noqa: E402

MARK = "arm_loops"
MM_ = 0.001
SNAP = 0.0005          # m: a crossing nearer an end than this goes through the end
SNAP_REL = float(os.environ.get("LOOPS_SNAP_REL", 0.25))   # ... or nearer than this share of the edge
SNAP_CAP = float(os.environ.get("LOOPS_SNAP_CAP", 1.0)) * MM_  # ... but never farther than this
NINF = 8               # influences kept (JOINTS_0 + JOINTS_1)
MM = 0.001

ELBOW_RINGS = [-30, -24, -18, -12, -8, -4, 0, 4, 8, 12, 18, 24, 30]     # mm along the elbow's axis
ELBOW_REACH = 0.085                                                     # m from the elbow's axis
OLECRANON = dict(z=(-16.0, 12.0), back=50.0)     # mm along the axis; deg either side of straight back
CREASE = dict(z=(-7.0, 7.0), front=75.0)         # mm; deg either side of straight front
PIT_R = 0.016                                    # m round the pit's apex, refined
# U chart: (x lateral, y front, s down the humerus) mm, origin her shoulder joint (arm_anatomy_post.frames)
# The folds: her rest arm hangs out (~38 deg): the pit is an open tunnel front to back under her shoulder. Each fold
# is the RIM of the tunnel's opening (front: the pectoral's lower border; back: the lat / teres edge), an arch from her
# chest wall up over the opening's top and down into her arm: the contour where her smoothed normal turns LEVEL toward
# the opening's way (the opening's face from its walls), within RIM_REACH of the tunnel's axis point (the apex, AX_DROP
# lower), its longest piece, smoothed. Field: the distance to that rim curve, signed by its side (+ out on the face,
# - into the tunnel), so the cuts run parallel to the rim, on both sides of it.
AX_DROP = 0.012          # m below the apex
RIM_LEVEL = 0.4          # the smoothed normal's share along the opening's way at the rim
RIM_REACH = 0.058        # m from the axis point
NSMOOTH = 12             # passes smoothing her normals for the rim
FOLD_FRONT = dict(cuts=[-4, 0, 4], half=0.011)      # (+-8: broken into pieces where the rim curls)
FOLD_BACK = dict(cuts=[0], half=0.011)
# deltoid lines: signed distance (mm) to a smooth curve through three points in a chart. "U": (s mm down the humerus,
# phi deg round it: 0 front, 90 out, 180 back), its arc at R0; "front": (dx, dy) mm from her shoulder joint (left-
# canonical world x out, y up), her front surface seen straight on
R0 = 40.0
DELT = {
    "delt_groove": dict(chart="front", pts=[(-42.0, 18.0), (-8.0, -14.0), (40.0, -51.0)], cuts=[-2, 2], half=9.0, ext=0.08),
    "delt_front": dict(chart="U", pts=[(60.0, 15.0), (95.0, 50.0), (117.0, 82.0)], cuts=[-2, 2], half=9.0, ext=0.06),
    "delt_back": dict(chart="U", pts=[(20.0, 200.0), (75.0, 150.0), (117.0, 95.0)], cuts=[-2, 2], half=9.0, ext=0.06),
}


# ------------------------------------------------------------------ the mesh --
def _acc(G, ai):
    """an accessor's data as stored (sparse filled in)"""
    a = G.g["accessors"][ai]
    n, dt = _NC[a["type"]], np.dtype(_CT[a["componentType"]])
    x = G.get(ai) if "bufferView" in a else np.zeros((a["count"], n), dt)
    sp = a.get("sparse")
    if sp:
        def raw(d, dtype, cnt):
            bv = G.g["bufferViews"][d["bufferView"]]
            off = G.b0 + bv.get("byteOffset", 0) + d.get("byteOffset", 0)
            return np.frombuffer(bytes(G.buf[off:off + dtype.itemsize * cnt]), dtype)
        idx = raw(sp["indices"], np.dtype(_CT[sp["indices"]["componentType"]]), sp["count"]).astype(np.int64)
        x = x.copy()
        x[idx] = raw(sp["values"], dt, sp["count"] * n).reshape(-1, n)
    return x


class Mesh:
    """her body's primitives (all but skin_head), welded by place; splits keep every old vertex and append"""

    def __init__(s, G):
        g = s.g = G.g
        s.G = G
        node = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
        s.mesh = g["meshes"][node["mesh"]]
        s.pidx = [i for i, p in enumerate(s.mesh["primitives"]) if g["materials"][p["material"]].get("name") != "skin_head"]
        s.P = []
        for i in s.pidx:
            p = s.mesh["primitives"][i]
            d = dict(orig={k: _acc(G, v) for k, v in p["attributes"].items()},
                     torig=[{k: _acc(G, v) for k, v in t.items()} for t in p.get("targets", [])])
            d["A"] = {k: v.astype(np.float64) for k, v in d["orig"].items()}
            d["T"] = [{k: v.astype(np.float64) for k, v in t.items()} for t in d["torig"]]
            d["F"] = _acc(G, p["indices"]).reshape(-1, 3).astype(np.int64)
            d["n0"], d["F0"] = len(d["A"]["POSITION"]), d["F"].copy()
            d["O"] = np.arange(len(d["F"]))       # each face's original face
            s.P.append(d)
        sk = g["skins"][0]
        s.names = [g["nodes"][j].get("name") for j in sk["joints"]]
        s.ibm = G.get(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        s.J = {n: np.linalg.inv(s.ibm[i])[:3, 3] for i, n in enumerate(s.names)}
        Pp = np.vstack([d["A"]["POSITION"] for d in s.P])
        _, first, wid = np.unique(np.round(Pp / 1e-6).astype(np.int64), axis=0, return_index=True, return_inverse=True)
        s.U = Pp[first].copy()
        off = np.r_[0, np.cumsum([d["n0"] for d in s.P])]
        for k, d in enumerate(s.P):
            d["wid"] = wid.ravel()[off[k]:off[k + 1]].copy()
        s.memb = [set() for _ in range(len(s.U))]     # per welded point: the cuts it lies on
        s.tag = [set() for _ in range(len(s.U))]      # per welded point: the patches that made it
        s.U0, s.nU0 = s.U.copy(), len(s.U)
        s.F0w = np.vstack([d["wid"][d["F0"]] for d in s.P])
        s.trunc = [0, 0.0]

    # welded views
    def faces(s):
        return np.vstack([d["wid"][d["F"]] for d in s.P])

    def edges(s):
        Fw = s.faces()
        H = np.sort(np.r_[Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]], axis=1)
        E, cnt = np.unique(H, axis=0, return_counts=True)
        return E, cnt

    def vnormals(s):
        Fw = s.faces()
        q = np.cross(s.U[Fw[:, 1]] - s.U[Fw[:, 0]], s.U[Fw[:, 2]] - s.U[Fw[:, 0]])
        N = np.zeros_like(s.U)
        for k in range(3):
            np.add.at(N, Fw[:, k], q)
        return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-20)

    def weights(s, names):
        """per welded point: the summed weight of these bones (its first copy)"""
        ids = [s.names.index(n) for n in names if n in s.names]
        out = np.zeros(len(s.U))
        for d in s.P:
            J = np.hstack([d["A"]["JOINTS_0"], d["A"]["JOINTS_1"]]).astype(int)
            W = np.hstack([d["A"]["WEIGHTS_0"], d["A"]["WEIGHTS_1"]])
            out[d["wid"]] = (W * np.isin(J, ids)).sum(1)
        return out

    # the one operation: split welded edges at t (from the lower welded id), retriangulate every face touching them
    def split(s, E, t, cut=None, tag=None):
        if not len(E):
            return 0
        E = np.sort(E, 1)
        key = {(int(a), int(b)): i for i, (a, b) in enumerate(E)}
        nw0 = len(s.U)
        Unew = (1 - t)[:, None] * s.U[E[:, 0]] + t[:, None] * s.U[E[:, 1]]
        Unew = Unew.astype(np.float32).astype(np.float64)   # stored as float32: every copy the same bytes
        s.U = np.vstack([s.U, Unew])
        for i, (a, b) in enumerate(E):
            m = s.memb[a] & s.memb[b]
            if cut is not None:
                m = m | {cut}
            s.memb.append(m)
            tg = (s.tag[a] & s.tag[b])
            if tag is not None:
                tg = tg | {tag}
            s.tag.append(tg)
        for d in s.P:
            s._split_prim(d, key, t, nw0, Unew)
        return len(E)

    def _split_prim(s, d, key, t, nw0, Unew):
        F, wid = d["F"], d["wid"]
        Fw = wid[F]
        # per face edge (k: v_k -> v_k+1): the split's welded index or -1
        sp = np.full((len(F), 3), -1)
        for k in range(3):
            a, b = Fw[:, k], Fw[:, (k + 1) % 3]
            lo, hi = np.minimum(a, b), np.maximum(a, b)
            for fi in np.nonzero(np.isin(lo, [x[0] for x in key]))[0]:
                e = key.get((int(lo[fi]), int(hi[fi])))
                if e is not None:
                    sp[fi, k] = e
        hit = np.nonzero((sp >= 0).any(1))[0]
        if not len(hit):
            return
        # new unwelded vertices: one per (unwelded edge) per primitive
        nv = len(d["A"]["POSITION"])
        made, src = {}, []
        for fi in hit:
            for k in range(3):
                e = sp[fi, k]
                if e < 0:
                    continue
                i, j = int(F[fi, k]), int(F[fi, (k + 1) % 3])
                ue = (min(i, j), max(i, j))
                if ue in made:
                    continue
                a = min(i, j)
                lo_w = min(int(wid[i]), int(wid[j]))
                ta = t[e] if wid[a] == lo_w else 1 - t[e]     # t measured from vertex a
                made[ue] = nv + len(src)
                src.append((a, max(i, j), ta, e))
        src_a = np.array([x[0] for x in src])
        src_b = np.array([x[1] for x in src])
        tt = np.array([x[2] for x in src])
        ee = np.array([x[3] for x in src])
        s._append(d, src_a, src_b, tt, nw0 + ee, Unew[ee])
        # retriangulate
        keep = np.ones(len(F), bool)
        keep[hit] = False
        newF, newO = [], []

        def mid(fi, k):
            i, j = int(F[fi, k]), int(F[fi, (k + 1) % 3])
            return made[(min(i, j), max(i, j))]

        for fi in hit:
            v = [int(x) for x in F[fi]]
            ks = [k for k in range(3) if sp[fi, k] >= 0]
            if len(ks) == 1:
                k = ks[0]
                m = mid(fi, k)
                a, b, c = v[k], v[(k + 1) % 3], v[(k + 2) % 3]
                newF += [(a, m, c), (m, b, c)]
            elif len(ks) == 2:
                # the corner between the two split edges: k0 = the edge ending at it
                k0 = ks[0] if (ks[0] + 1) % 3 == ks[1] else ks[1]
                k1 = (k0 + 1) % 3
                m0, m1 = mid(fi, k0), mid(fi, k1)
                a, b, c = v[k0], v[(k0 + 1) % 3], v[(k0 + 2) % 3]      # edges a-b (m0), b-c (m1)
                newF.append((m0, b, m1))
                # quad a, m0, m1, c
                q1 = [(a, m0, m1), (a, m1, c)]
                q2 = [(a, m0, c), (m0, m1, c)]
                newF += q1 if s._qual(d, q1) >= s._qual(d, q2) else q2
            else:
                m0, m1, m2 = mid(fi, 0), mid(fi, 1), mid(fi, 2)
                a, b, c = v
                newF += [(a, m0, m2), (m0, b, m1), (m2, m1, c), (m0, m1, m2)]
            newO += [d["O"][fi]] * (len(newF) - len(newO))
        d["F"] = np.vstack([F[keep], np.array(newF, np.int64)])
        d["O"] = np.r_[d["O"][keep], np.array(newO, np.int64)]

    def _qual(s, d, tris):
        X = s.U[d["wid"][np.array(tris)]]
        return min_angles(X).min()

    def _append(s, d, ia, ib, t, w_new, Pnew):
        A, T = d["A"], d["T"]
        w0, w1 = (1 - t)[:, None], t[:, None]
        add = {}
        for k, v in A.items():
            if k == "POSITION":
                add[k] = Pnew
            elif k.startswith("JOINTS") or k.startswith("WEIGHTS"):
                continue
            else:
                x = w0 * v[ia] + w1 * v[ib]
                if k == "NORMAL":
                    x /= np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-20)
                elif k.startswith("TANGENT"):
                    nn = add["NORMAL"] if "NORMAL" in add else None
                    xyz = x[:, :3]
                    if nn is not None:
                        xyz = xyz - (xyz * nn).sum(1, keepdims=True) * nn
                    xyz /= np.maximum(np.linalg.norm(xyz, axis=1, keepdims=True), 1e-20)
                    x = np.c_[xyz, np.where(v[ia][:, 3:4] < 0, -1.0, 1.0)]
                elif k.startswith("COLOR"):
                    dt = d["orig"][k].dtype
                    if dt.kind == "u":
                        x = np.round(x)
                add[k] = x
        # joints and weights: merged, the top NINF, renormalized
        sets = sorted(k[-1] for k in A if k.startswith("JOINTS"))
        J = np.hstack([A["JOINTS_" + k] for k in sets]).astype(int)
        W = np.hstack([A["WEIGHTS_" + k] for k in sets])
        nj = len(s.names)
        M = np.zeros((len(ia), nj))
        r = np.arange(len(ia))
        for c in range(J.shape[1]):
            np.add.at(M, (r, J[ia, c]), w0[:, 0] * W[ia, c])
            np.add.at(M, (r, J[ib, c]), w1[:, 0] * W[ib, c])
        top = np.argsort(-M, 1, kind="stable")[:, :J.shape[1]]
        tw = np.take_along_axis(M, top, 1)
        drop = M.sum(1) - tw.sum(1)
        s.trunc[0] += int((drop > 1e-9).sum())
        s.trunc[1] = max(s.trunc[1], float(drop.max()) if len(drop) else 0.0)
        tw = np.where(tw > 0, tw, 0.0)
        tw /= np.maximum(tw.sum(1, keepdims=True), 1e-20)
        top = np.where(tw > 0, top, 0)
        n4 = A["JOINTS_0"].shape[1]
        for i, k in enumerate(sets):
            add["JOINTS_" + k] = top[:, i * n4:(i + 1) * n4].astype(np.float64)
            add["WEIGHTS_" + k] = tw[:, i * n4:(i + 1) * n4]
        for k in A:
            A[k] = np.vstack([A[k], add[k]])
        for tg in T:
            for k in tg:
                tg[k] = np.vstack([tg[k], w0 * tg[k][ia] + w1 * tg[k][ib]])
        d["wid"] = np.r_[d["wid"], w_new]

    # a cut: the iso-line f = c inside the region
    def cut(s, f, c, region, cut_id, family=()):
        """family: the cut ids of this one's siblings (a point on one of them is never routed onto this one too: the
        loops stay apart)"""
        g = f - c
        E, cnt = s.edges()
        a, b = E[:, 0], E[:, 1]
        ok = region[a] & region[b] & (cnt != 1)
        L = np.linalg.norm(s.U[a] - s.U[b], axis=1)
        fam = set(family)
        free = np.array([not (x & fam) for x in s.memb])
        g[free & region & (np.abs(g) < 0.6 * SNAP)] = 0.0
        for _ in range(3):
            x = ok & (g[a] * g[b] < 0)
            t = g[a][x] / (g[a][x] - g[b][x])
            l = L[x]
            sa = a[x][t * l < np.minimum(np.maximum(SNAP, SNAP_REL * l), SNAP_CAP)]
            sb = b[x][(1 - t) * l < np.minimum(np.maximum(SNAP, SNAP_REL * l), SNAP_CAP)]
            snap = np.unique(np.r_[sa, sb])
            snap = snap[free[snap] & (g[snap] != 0)]
            if not len(snap):
                break
            s.snapdev = max(getattr(s, "snapdev", 0.0), float(np.abs(g[snap]).max()))
            g[snap] = 0.0
        x = ok & (g[a] * g[b] < 0)
        t = g[a][x] / (g[a][x] - g[b][x])
        # points ON the line already (snapped or exact), inside the region
        on = np.nonzero((g == 0) & region)[0]
        for v in on:
            s.memb[v].add(cut_id)
        return s.split(E[x], t, cut=cut_id), len(on)

    def refine(s, vmask, tag):
        """1-to-4 over the faces whose three points are in vmask (closure: their neighbours bisected)"""
        Fw = s.faces()
        fm = vmask[Fw].all(1)
        if not fm.any():
            return 0
        H = np.sort(np.r_[Fw[fm][:, [0, 1]], Fw[fm][:, [1, 2]], Fw[fm][:, [2, 0]]], axis=1)
        E = np.unique(H, axis=0)
        Eall, cnt = s.edges()
        border = {(int(x), int(y)) for (x, y), c in zip(Eall, cnt) if c == 1}
        E = np.array([e for e in E if (int(e[0]), int(e[1])) not in border])
        return s.split(E, np.full(len(E), 0.5), tag=tag)


def improve(m, passes=30):
    """flip edges INSIDE an old face (its pieces are coplanar: the shape can't change) toward the larger minimum angle;
    never a cut's edge (the loops) nor an old face's edge. Returns flips made."""
    total = 0
    for d in m.P:
        F, O, wid = d["F"], d["O"], d["wid"]
        cntO = np.bincount(O, minlength=O.max() + 1)
        cand = np.nonzero(cntO[O] > 1)[0]
        for _ in range(passes):
            emap = {}
            for fi in cand:
                f = F[fi]
                for k in range(3):
                    i, j = int(f[k]), int(f[(k + 1) % 3])
                    emap.setdefault((min(i, j), max(i, j)), []).append((fi, k))
            done = set()
            nflip = 0
            for (i, j), lst in emap.items():
                if len(lst) != 2:
                    continue
                (f1, k1), (f2, k2) = lst
                if O[f1] != O[f2] or f1 in done or f2 in done:
                    continue
                wi, wj = int(wid[i]), int(wid[j])
                if m.memb[wi] & m.memb[wj]:
                    continue
                a, b, c = (int(x) for x in np.roll(F[f1], -k1))      # a-b the edge, c opposite
                a2, b2, e = (int(x) for x in np.roll(F[f2], -k2))    # b-a, e opposite
                old = [(a, b, c), (b2, a2, e)]
                new = [(c, a, e), (e, b, c)]
                X0 = m.U[wid[np.array(old)]]
                X1 = m.U[wid[np.array(new)]]
                n0 = np.cross(X0[0, 1] - X0[0, 0], X0[0, 2] - X0[0, 0])
                n1 = np.cross(X1[:, 1] - X1[:, 0], X1[:, 2] - X1[:, 0])
                if (n1 @ n0 <= 0).any():
                    continue
                if min_angles(X1).min() > min_angles(X0).min() + 1e-6:
                    F[f1], F[f2] = new[0], new[1]
                    done.update((f1, f2))
                    nflip += 1
            total += nflip
            if not nflip:
                break
    return total


def min_angles(X):
    """X (n, 3, 3) triangles -> each one's smallest angle, deg"""
    out = np.full(len(X), 180.0)
    for i in range(3):
        a, b, c = X[:, i], X[:, (i + 1) % 3], X[:, (i + 2) % 3]
        u, v = b - a, c - a
        cs = (u * v).sum(1) / np.maximum(np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1), 1e-30)
        out = np.minimum(out, np.degrees(np.arccos(np.clip(cs, -1, 1))))
    return out


def quality(U, Fw, mask=None):
    X = U[Fw] if mask is None else U[Fw[mask]]
    ang = min_angles(X)
    area = np.linalg.norm(np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0]), axis=1) / 2
    return dict(faces=int(len(X)), min_angle=round(float(ang.min()), 2), p1_angle=round(float(np.percentile(ang, 1)), 2),
                lt10=int((ang < 10).sum()), lt5=int((ang < 5).sum()), min_area_mm2=round(float(area.min() * 1e6), 4),
                p1_area_mm2=round(float(np.percentile(area, 1) * 1e6), 3))


# ------------------------------------------------------------------ the frames --
class Side:
    """one arm, left-canonical: X(c) = mirrored for the right"""

    def __init__(s, m, side):
        s.side = side
        s.k = np.array([1.0, 1.0, 1.0]) if side == "l" else np.array([-1.0, 1.0, 1.0])
        J = {n[:-2]: m.J[n] * s.k for n in m.J if n.endswith("_" + side)}
        s.Jn = J

        def fr(A, B):
            a = (B - A) / np.linalg.norm(B - A)
            f = np.array([0, 0, 1.0]) - a[2] * a
            f /= np.linalg.norm(f)
            return dict(O=A, a=a, f=f, l=np.cross(f, a), L=float(np.linalg.norm(B - A)))
        s.Uf = fr(J["upperarm"], J["lowerarm"])
        s.Ff = fr(J["lowerarm"], J["hand"])
        d = s.Uf["a"] + s.Ff["a"]
        d /= np.linalg.norm(d)
        f = np.array([0, 0, 1.0]) - d[2] * d
        f /= np.linalg.norm(f)
        s.Ef = dict(O=J["lowerarm"], a=d, f=f, l=np.cross(f, d))

    def c(s, X):
        return X * s.k

    def u2w(s, x, y, z):
        """U chart mm (x lateral, y front, s down) -> canonical m"""
        F = s.Uf
        return F["O"] + (x * F["l"] + y * F["f"] + z * F["a"]) * MM

    def sp2dir(s, phi):
        F = s.Uf
        p = np.radians(phi)
        return np.cos(p) * F["f"] + np.sin(p) * F["l"]


def ray_hit(Uc, Fw, o, dvec, near=None, outer=False):
    """first hit of the ray o + t dvec (t > 0) on the mesh (canonical points Uc), Moller-Trumbore over faces near it;
    outer: the farthest hit along the whole line (her surface on that side, wherever o is)"""
    if near is not None:
        Fw = Fw[near[Fw].any(1)]
    v0, v1, v2 = Uc[Fw[:, 0]], Uc[Fw[:, 1]], Uc[Fw[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    p = np.cross(dvec, e2)
    det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-14
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    tv = o - v0
    u = (tv * p).sum(1) * inv
    q = np.cross(tv, e1)
    v = (q @ dvec) * inv
    t = (e2 * q).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & ((t > 1e-6) | outer)
    if not hit.any():
        raise RuntimeError("ray missed her surface")
    i = np.argmax(np.where(hit, t, -np.inf)) if outer else np.argmin(np.where(hit, t, np.inf))
    return o + t[i] * dvec


def to_surface(Uc, Fw, o, dvec, near, reach=0.03):
    """o taken to her surface along dvec (the first hit within reach), else to her nearest point"""
    try:
        h = ray_hit(Uc, Fw, o, dvec, near)
        if np.linalg.norm(h - o) < reach:
            return h
    except RuntimeError:
        pass
    return Uc[np.argmin(np.linalg.norm(Uc - o, axis=1))].copy()


def smooth_normals(m, N, k):
    """her vertex normals umbrella-smoothed k passes (old mesh)"""
    E, _ = m.edges()
    n = len(N)
    from scipy.sparse import coo_matrix
    A = coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    X = N.copy()
    for _ in range(k):
        X = 0.5 * X + 0.5 * (A @ X) / deg[:, None]
        X /= np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-20)
    return X


def rim(Fw, U, val, level, near, Ns, smooth=6, step=0.0015):
    """the contour val = level over faces whose three points are near: its longest piece as a polyline (smoothed,
    resampled every step m) and the smoothed normal along it"""
    F = Fw[near[Fw].all(1)]
    g = val - level
    segs = []
    for f in F:
        pts = []
        for k in range(3):
            a, b = int(f[k]), int(f[(k + 1) % 3])
            if (g[a] < 0) != (g[b] < 0):
                pts.append((min(a, b), max(a, b)))
        if len(pts) == 2:
            segs.append(pts)
    adj = {}
    for p, q in segs:
        adj.setdefault(p, []).append(q)
        adj.setdefault(q, []).append(p)
    seen, best = set(), []
    for st in [v for v, n in adj.items() if len(n) == 1] + list(adj):
        if st in seen:
            continue
        path, v, prev = [st], st, None
        seen.add(st)
        while True:
            nx = [w for w in adj[v] if w != prev and w not in seen]
            if not nx:
                break
            prev, v = v, nx[0]
            seen.add(v)
            path.append(v)
        if len(path) > len(best):
            best = path

    def at(e):
        a, b = e
        t = g[a] / (g[a] - g[b])
        return (1 - t) * U[a] + t * U[b], (1 - t) * Ns[a] + t * Ns[b]
    P = np.array([at(e)[0] for e in best])
    N = np.array([at(e)[1] for e in best])
    for _ in range(smooth):
        P[1:-1] = 0.5 * P[1:-1] + 0.25 * (P[:-2] + P[2:])
        N[1:-1] = 0.5 * N[1:-1] + 0.25 * (N[:-2] + N[2:])
    cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.linspace(0, cum[-1], max(int(cum[-1] / step), 2))
    P = np.stack([np.interp(s, cum, P[:, i]) for i in range(3)], 1)
    N = np.stack([np.interp(s, cum, N[:, i]) for i in range(3)], 1)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    return P, N


class RimField:
    """signed distance (m) to a rim polyline: + on its side where val rises (the opening's face), - into the tunnel;
    and u (0..1 along it)"""

    def __init__(s, P, N, U, val):
        s.P, s.N = P, N
        T = np.gradient(P, axis=0)
        T /= np.linalg.norm(T, axis=1, keepdims=True)
        s.B = np.cross(T, N)
        # orient: the side where val rises
        kd = cKDTree(U)
        mid = len(P) // 2
        hi = val[kd.query(P[mid] + 0.005 * s.B[mid])[1]]
        lo = val[kd.query(P[mid] - 0.005 * s.B[mid])[1]]
        if hi < lo:
            s.B = -s.B
        s.cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]

    def __call__(s, X):
        A, D = s.P[:-1], np.diff(s.P, axis=0)
        best = np.full(len(X), np.inf)
        sg = np.ones(len(X))
        uu = np.zeros(len(X))
        L = s.cum[-1]
        for i in range(len(A)):
            w = X - A[i]
            tr = (w @ D[i]) / (D[i] @ D[i])
            tt = np.clip(tr, 0, 1)
            if i == 0:
                tt = np.minimum(tr, 1)
            if i == len(A) - 1:
                tt = np.maximum(tt, np.where(tr > 1, tr, tt))
            e = w - tt[:, None] * D[i]
            dd = np.linalg.norm(e, axis=1)
            b = dd < best
            best = np.where(b, dd, best)
            Bv = (1 - np.clip(tt, 0, 1))[:, None] * s.B[i] + np.clip(tt, 0, 1)[:, None] * s.B[i + 1]
            sg = np.where(b, np.sign((e * Bv).sum(1)), sg)
            uu = np.where(b, (s.cum[i] + tt * np.linalg.norm(D[i])) / L, uu)
        return best * np.where(sg == 0, 1, sg), uu


def bezier3(P, ext, n=240):
    """the quadratic through three chart points (the middle one at its half), extended straight by ext of its length
    at both ends: (points, u) with u 0..1 over the curve itself"""
    Cc = 2 * P[1] - (P[0] + P[2]) / 2
    t = np.linspace(0, 1, n)[:, None]
    B = (1 - t) ** 2 * P[0] + 2 * (1 - t) * t * Cc + t ** 2 * P[2]
    L = np.linalg.norm(np.diff(B, axis=0), axis=1).sum()
    d0 = (B[0] - B[1]) / np.linalg.norm(B[0] - B[1])
    d1 = (B[-1] - B[-2]) / np.linalg.norm(B[-1] - B[-2])
    k = np.linspace(1, 0, 20, endpoint=False)[:, None] * ext * L
    B = np.vstack([B[0] + k * d0, B, B[-1] + k[::-1] * d1])
    cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(B, axis=0), axis=1))]
    u = (cum - ext * L) / L
    return B, u


def curve_dist(Q, crv):
    """signed distance (chart units; + on the left of its direction) of 2D points to the curve, and u at the nearest"""
    B, u = crv
    A, D = B[:-1], np.diff(B, axis=0)
    best = np.full(len(Q), np.inf)
    sgn = np.ones(len(Q))
    uu = np.zeros(len(Q))
    for i in range(len(A)):
        w = Q - A[i]
        tt = np.clip((w @ D[i]) / (D[i] @ D[i]), 0, 1)
        e = w - tt[:, None] * D[i]
        dd = np.hypot(e[:, 0], e[:, 1])
        b = dd < best
        best = np.where(b, dd, best)
        sgn = np.where(b, np.sign(D[i, 0] * w[:, 1] - D[i, 1] * w[:, 0]), sgn)
        uu = np.where(b, u[i] + tt * (u[i + 1] - u[i]), uu)
    return best * np.where(sgn == 0, 1, sgn), uu


def seg_dist(X, P):
    """distance of points X to the polyline P, and the position along it (0..1 by arc length, beyond at the ends)"""
    best = np.full(len(X), np.inf)
    u = np.zeros(len(X))
    Ls = np.linalg.norm(np.diff(P, axis=0), axis=1)
    cum = np.r_[0, np.cumsum(Ls)]
    for i in range(len(P) - 1):
        A, B = P[i], P[i + 1]
        ab = B - A
        tt = ((X - A) @ ab) / (ab @ ab)
        tc = np.clip(tt, 0, 1)
        dd = np.linalg.norm(X - (A + tc[:, None] * ab), axis=1)
        better = dd < best
        best = np.where(better, dd, best)
        te = tc.copy()
        if i == 0:
            te = np.where(tt < 0, tt, te)
        if i == len(P) - 2:
            te = np.where(tt > 1, tt, te)
        uu = (cum[i] + te * Ls[i]) / cum[-1]
        u = np.where(better, uu, u)
    return best, u


# ------------------------------------------------------------------ the plan --
def plan_side(m, sd, log):
    """the cuts and patches of one arm: [(kind, name, field fn(Uc)->f, values, region fn(Uc)->mask, info)]"""
    Uc0 = sd.c(m.U)
    Fw0 = m.faces()
    N0 = m.vnormals() * sd.k
    arm = m.weights([n for n in m.names if n.endswith("_" + sd.side) and n.split("_")[0] in ("upperarm", "lowerarm", "hand")])
    info = {}
    ops = []
    # elbow rings
    E = sd.Ef
    zf = lambda X: (X - E["O"]) @ E["a"]
    def near_e(X):
        d = X - E["O"]
        z = d @ E["a"]
        return (np.abs(z) < 0.045) & (np.linalg.norm(d - z[:, None] * E["a"], axis=1) < ELBOW_REACH)
    for c in ELBOW_RINGS:
        ops.append(("cut", "elbow_ring%+d" % c, zf, c * MM, near_e))

    # the pit's apex: the highest down-facing point under her shoulder joint
    Js = sd.Jn["upperarm"]
    cand = (np.abs(Uc0[:, 2] - Js[2]) < 0.006) & (Uc0[:, 0] > 0.08) & (Uc0[:, 0] < Js[0]) & (N0[:, 1] < -0.3) &            (Uc0[:, 1] < Js[1]) & (Uc0[:, 1] > Js[1] - 0.2)
    ap = Uc0[np.nonzero(cand)[0][np.argmax(Uc0[cand, 1])]]
    info["pit_apex"] = ap.round(4).tolist()
    # the folds: the tunnel's rims
    C = ap - np.array([0, AX_DROP, 0])
    Ns = smooth_normals(m, N0, NSMOOTH)
    for name, cfg, sg in (("front_fold", FOLD_FRONT, 1.0), ("back_fold", FOLD_BACK, -1.0)):
        dirv = sd.Uf["f"] * sg
        near = (np.linalg.norm(Uc0 - C, axis=1) < RIM_REACH) & (((Uc0 - C) @ dirv) > 0.0)
        P, Nr = rim(Fw0, Uc0, Ns @ dirv, RIM_LEVEL, near, Ns)
        fld = RimField(P, Nr, Uc0, Ns @ dirv)

        def f(X, fld=fld):
            return fld(X)[0]

        def reg(X, fld=fld, cfg=cfg):
            g, u = fld(X)
            return (np.abs(g) < cfg["half"]) & (u > 0.0) & (u < 1.0)
        info[name] = dict(rim_pts=len(P), rim_len_mm=round(float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum() * 1000), 1),
                          ends=[P[0].round(4).tolist(), P[-1].round(4).tolist()])
        for c in cfg["cuts"]:
            ops.append(("cut", "%s%+d" % (name, c), f, c * MM, reg))

    # deltoid lines: signed distance to a smooth curve in a chart
    def chart_u(X):
        d = (X - sd.Uf["O"]) / MM
        s_ = d @ sd.Uf["a"]
        ph = np.degrees(np.arctan2(d @ sd.Uf["l"], d @ sd.Uf["f"]))
        ph = np.where(ph < -90, ph + 360, ph)
        r = np.linalg.norm(d - s_[:, None] * sd.Uf["a"], axis=1)
        return np.c_[s_, np.radians(ph) * R0], r

    def chart_f(X):
        d = (X - sd.Uf["O"]) / MM
        return d[:, :2], d[:, 2]
    for name, cfg in DELT.items():
        Pc = np.array(cfg["pts"], float)
        if cfg["chart"] == "U":
            Pc[:, 1] = np.radians(Pc[:, 1]) * R0
        crv = bezier3(Pc, cfg["ext"])

        def f(X, cfg=cfg, crv=crv):
            Q, _ = chart_u(X) if cfg["chart"] == "U" else chart_f(X)
            return curve_dist(Q, crv)[0] * MM

        def reg(X, cfg=cfg, crv=crv):
            Q, h = chart_u(X) if cfg["chart"] == "U" else chart_f(X)
            dd, u = curve_dist(Q, crv)
            m_ = (np.abs(dd) < cfg["half"]) & (u > 0) & (u < 1)
            # the U chart: her arm only (not the torso behind the axis's ray); the front chart: her front only
            return m_ & ((h < 65.0) if cfg["chart"] == "U" else (h > -15.0))
        info[name] = dict(chart=cfg["chart"], pts=cfg["pts"])
        for c in cfg["cuts"]:
            ops.append(("cut", "%s%+d" % (name, c), f, c * MM, reg))

    # patches
    def ang(X):
        d = X - E["O"]
        return np.degrees(np.arctan2(d @ E["l"], d @ E["f"]))

    def olec(X):
        z, a = zf(X) / MM, ang(X)
        return near_e(X) & (z > OLECRANON["z"][0]) & (z < OLECRANON["z"][1]) & (np.abs(a) > 180 - OLECRANON["back"])

    def crease(X):
        z, a = zf(X) / MM, ang(X)
        return near_e(X) & (z > CREASE["z"][0]) & (z < CREASE["z"][1]) & (np.abs(a) < CREASE["front"])
    pit = lambda X, ap=ap: np.linalg.norm(X - ap, axis=1) < PIT_R
    ops += [("refine", "olecranon", None, None, olec), ("refine", "crease", None, None, crease),
            ("refine", "pit_floor", None, None, pit)]
    info["arm_w_min_in_rings"] = None
    return ops, info, arm


# ------------------------------------------------------------------ chains --
def chains(m, cut_id):
    """the welded points of one cut in order along it (one list per piece; closed loops repeat no point)"""
    on = np.array([cut_id in x for x in m.memb])
    E, _ = m.edges()
    k = on[E[:, 0]] & on[E[:, 1]]
    adj = {}
    for a, b in E[k]:
        adj.setdefault(int(a), []).append(int(b))
        adj.setdefault(int(b), []).append(int(a))
    seen, out = set(), []
    ends = [v for v, n in adj.items() if len(n) == 1]
    for start in ends + list(adj):
        if start in seen:
            continue
        path, v, prev = [start], start, None
        seen.add(start)
        while True:
            nx = [w for w in adj[v] if w != prev and w not in seen]
            if not nx:
                break
            prev, v = v, nx[0]
            seen.add(v)
            path.append(v)
        out.append(path)
    branch = sum(1 for n in adj.values() if len(n) > 2)
    return sorted(out, key=len, reverse=True), branch


def copies(m):
    """welded id -> [(prim k, index)]"""
    out = {}
    for k, d in enumerate(m.P):
        for i, w in enumerate(d["wid"]):
            out.setdefault(int(w), []).append((k, i))
    return out


# ------------------------------------------------------------------ write --
def write(m, dst, extras):
    from wrap_post import compact
    G, g = m.G, m.g
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])

    def view(data, target=None):
        while len(binb) % 4:
            binb.append(0)
        g["bufferViews"].append({"buffer": 0, "byteOffset": len(binb), "byteLength": len(data), **({"target": target} if target else {})})
        binb.extend(data)
        return len(g["bufferViews"]) - 1

    def put(arr, oa, target, mm=False):
        a = {"bufferView": view(np.ascontiguousarray(arr).tobytes(), target), "componentType": oa["componentType"],
             "count": int(len(arr)), "type": oa["type"]}
        if oa.get("normalized"):
            a["normalized"] = True
        if mm:
            a["min"] = [float(x) for x in arr.min(0)]
            a["max"] = [float(x) for x in arr.max(0)]
        g["accessors"].append(a)
        return len(g["accessors"]) - 1

    def sparse(arr):
        arr = np.ascontiguousarray(arr, dtype="<f4")
        nz = np.nonzero((arr.view("<u4") != 0).any(1))[0]      # by bits: a -0.0 is kept as stored
        if not len(nz):
            nz = np.zeros(1, np.int64)
        iv = view(nz.astype("<u4").tobytes())
        vv = view(arr[nz].astype("<f4").tobytes())
        g["accessors"].append({"componentType": 5126, "count": int(len(arr)), "type": "VEC3",
                               "sparse": {"count": int(len(nz)), "indices": {"bufferView": iv, "componentType": 5125},
                                          "values": {"bufferView": vv}},
                               "min": [float(x) for x in np.minimum(arr[nz].min(0), 0)],
                               "max": [float(x) for x in np.maximum(arr[nz].max(0), 0)]})
        return len(g["accessors"]) - 1
    for pi, d in zip(m.pidx, m.P):
        p = m.mesh["primitives"][pi]
        n0 = d["n0"]
        newa = {}
        for k, ai in p["attributes"].items():
            oa = g["accessors"][ai]
            dt = d["orig"][k].dtype
            arr = np.vstack([d["orig"][k], d["A"][k][n0:].astype(dt)])
            newa[k] = put(arr, oa, 34962, k == "POSITION")
        p["attributes"] = newa
        nv = len(d["A"]["POSITION"])
        idt, ict = (np.uint16, 5123) if nv < 65536 else (np.uint32, 5125)
        a = g["accessors"][p["indices"]]
        p["indices"] = put(d["F"].astype(idt).ravel(), dict(componentType=ict, type="SCALAR"), 34963)
        tg = []
        for to, tn in zip(d["torig"], d["T"]):
            tg.append({k: sparse(np.vstack([to[k], tn[k][n0:].astype(to[k].dtype)])) for k in to})
        p["targets"] = tg
    g["buffers"][0]["byteLength"] = len(binb)
    G.buf, G.b0 = binb, 0
    compact(G)
    g["asset"].setdefault("extras", {})[MARK] = extras
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    binb = G.buf
    while len(binb) % 4:
        binb.append(0)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)


# ------------------------------------------------------------------ run --
def run(src, dst, map_path=None, log=print):
    G = _Gl(src)
    if G.g.get("asset", {}).get("extras", {}).get(MARK):
        raise SystemExit("ARM_LOOPS: %s has had it" % src)
    m = Mesh(G)
    E0, c0 = m.edges()
    q0 = quality(m.U, m.faces())
    nv0 = [d["n0"] for d in m.P]
    nf0 = [len(d["F"]) for d in m.P]
    cut_names, plan_info = [], {}
    feats = {}
    for side in ("l", "r"):
        sd = Side(m, side)
        ops, info, arm = plan_side(m, sd, log)
        plan_info[side] = info
        for kind, name, f, c, reg in ops:
            Uc = sd.c(m.U)
            if kind == "cut":
                cid = len(cut_names)
                cut_names.append((side, name))
                fam = [i for i, (sd_, nm) in enumerate(cut_names[:-1]) if sd_ == side and nm.rstrip("+-0123456789") == name.rstrip("+-0123456789")]
                n, on = m.cut(f(Uc), c, reg(Uc), cid, fam)
                log("  %s %-18s split %4d edges, through %3d old points" % (side, name, n, on))
            else:
                n = m.refine(reg(Uc), (side, name))
                log("  %s %-18s refined: %4d edges split" % (side, name, n))
    log("  flips inside old faces: %d" % improve(m))
    E1, c1 = m.edges()
    Fw1 = m.faces()
    new_mask_f = (Fw1 >= m.nU0).any(1)
    q1 = quality(m.U, Fw1)
    # the region's quality: old faces that were split vs their pieces
    def fkey(F):
        F = np.sort(F, 1).astype(np.int64)
        return (F[:, 0] * 200000 + F[:, 1]) * 200000 + F[:, 2]
    old_split = ~np.isin(fkey(m.F0w), fkey(Fw1))
    q0r = quality(m.U0, m.F0w, old_split)
    q1r = quality(m.U, Fw1, new_mask_f)
    # loop map
    cp = copies(m)
    lm = {"_doc": "per arm and feature: each cut's points in order along it, as [prim, vertex] per copy (prim 0 her body, "
                  "1 her back graft); 'old' marks points that were already hers (cuts routed through them); refine "
                  "patches list their new points", "prims": [m.mesh["primitives"][i].get("material") for i in m.pidx]}
    branches = 0
    cuts_rep = {}
    E2, _ = m.edges()
    eset = {(int(a), int(b)) for a, b in E2}
    for cid, (side, name) in enumerate(cut_names):
        ch, br = chains(m, cid)
        branches += br
        cuts_rep["%s %s" % (side, name)] = [(len(c), int((min(c[0], c[-1]), max(c[0], c[-1])) in eset),
                                             round(float(np.linalg.norm(np.diff(m.U[c], axis=0), axis=1).sum() * 1000), 1)) for c in ch]
        feat = name.rstrip("+-0123456789")
        ent = lm.setdefault(side, {}).setdefault(feat, {})
        ent[name[len(feat):]] = [[[list(x) for x in cp[w]] for w in c] for c in ch]
        ent.setdefault("_old", {})[name[len(feat):]] = [[int(w < m.nU0) for w in c] for c in ch]
    for w in range(m.nU0, len(m.U)):
        for side, name in m.tag[w]:
            lm.setdefault(side, {}).setdefault(name, []).append([list(x) for x in cp[w]])
    extras = {"rings_mm": ELBOW_RINGS, "snap_mm": SNAP * 1000, "plan": plan_info,
              "verts": [nv0, [len(d["A"]["POSITION"]) for d in m.P]], "faces": [nf0, [len(d["F"]) for d in m.P]]}
    write(m, dst, extras)
    if map_path:
        json.dump(lm, open(map_path, "w"), separators=(",", ":"))
    rep = dict(verts=extras["verts"], faces=extras["faces"], welded=[m.nU0, len(m.U)],
               open_edges=[int((c0 == 1).sum()), int((c1 == 1).sum())],
               nonmanifold=[int((c0 > 2).sum()), int((c1 > 2).sum())],
               quality_all=[q0, q1], quality_region=[q0r, q1r], weight_trunc=dict(n=m.trunc[0], max=round(m.trunc[1], 5)),
               branches=branches, snap_dev_mm=round(getattr(m, "snapdev", 0.0) * 1000, 3), cuts=cuts_rep, plan=plan_info,
               shared=int(sum(1 for x in m.memb if len(x) > 1)))
    return rep, m


def verify(src, dst):
    """old bytes kept; new points on the old surface"""
    sys.path.insert(0, os.path.join(HERE, "arm_graft"))
    from geo import closest_tri
    A, B = Mesh(_Gl(src)), Mesh(_Gl(dst))
    same = True
    for da, db in zip(A.P, B.P):
        n0 = da["n0"]
        for k in da["orig"]:
            same &= da["orig"][k].tobytes() == db["orig"][k][:n0].tobytes()
        for ta, tb in zip(da["torig"], db["torig"]):
            for k in ta:
                same &= ta[k].tobytes() == tb[k][:n0].tobytes()
    # new points vs the old triangles
    Fo = A.faces()
    C = A.U[Fo].mean(1)
    kd = cKDTree(C)
    newP = np.vstack([db["orig"]["POSITION"][da["n0"]:] for da, db in zip(A.P, B.P)]).astype(np.float64)
    _, nb = kd.query(newP, k=24)
    best = np.full(len(newP), np.inf)
    for j in range(nb.shape[1]):
        f = Fo[nb[:, j]]
        q, _ = closest_tri(newP, A.U[f[:, 0]], A.U[f[:, 1]], A.U[f[:, 2]])
        best = np.minimum(best, np.linalg.norm(newP - q, axis=1))
    return dict(old_bytes_identical=bool(same), new_points=int(len(newP)),
                max_dist_mm=float(best.max() * 1000) if len(best) else 0.0)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    mp = next((sys.argv[i + 1] for i, x in enumerate(sys.argv) if x == "--map"), None)
    rep, _ = run(a[0], a[1], mp)
    rep["verify"] = verify(a[0], a[1])
    print(json.dumps(rep, indent=1))
