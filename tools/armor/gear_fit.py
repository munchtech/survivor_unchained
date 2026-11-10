"""Gear fit engine (P2): one binding per gear piece to the base topology, made once, evaluated on any body built on it.

Every gear row (the four callings' 30 slot rows in godot/art/people/armor_index.json, each calling's gameplay lod file
as one more unit "<calling>.lod", and the 10 armor pieces in godot/art/armor/armor_index.json with their .lod1.* and
.shadow meshes) was fit to body A (heroine.glb). `bind` carries each piece onto her_b (the published P1 body,
godot/art/people/body_p1, built from tools/body/out/round_36) by surface point as tools/body/skin_pieces.py does, keeps
A's clearance (layer band), and binds every vertex to a TOPOLOGY triangle of the base (stage close.npz / play.npz "T",
the same triangle on every body built on the base) or to a HeroineHead triangle (its vertex order is fixed on every
body; a slider body moves the head rigidly, and its glb holds the moved head, so the binding needs nothing more):

    triangle index into the combined surface [topology T ; HeroineHead T + n_topo]   (int32)
    barycentrics (uint16 /65535, two stored, the third 1 - both)
    offset in the triangle's local frame there: n = the interpolated vertex normal (area-weighted, welded), t = the
    triangle's first edge (v1 - v0) squared against n, b = n x t                       (float32)
    the vertex normal in that frame (int16 snorm), per vertex (duplicates may carry their own normals)

Vertices are bound once per unique position (A's seam duplicates share one binding, so they never split). Only binding
data and a pointer to A's file and node are stored (godot/art/gear/bind/<id>.npz); UVs, colors, indices, materials and
mesh extras are read from A's file at build time.

`build --body <dir>` evaluates every binding on a body (its body.glb / play.glb and its stage npz for topology order):
    bendy vertices: the bound triangle's point + the offset in this body's frame there; B's skin weights at the point
      (barycentric, top 8); B's blend shapes at the point (every Heroine shape that moves the piece; HeroineHead's face
      shapes are not carried). On a body other than the bind body a piece follows by gear_field: the body's move as a
      spatially smooth field (so a stand-off part bound to two surfaces follows as one surface; an optional exact band
      on the skin, gear_field FIELD near_m, is off: it measured worse); the tight set (within 4 mm on the bind body)
      then holds its bind clearance two-sided along the new skin's (smoothed) normal, and a smooth one-sided push keeps
      every vertex out of the new skin; on the bind body none of it runs (built == bind geometry).
    rigid components (rows "rigid": true and the plate_* / mar_her_* styles, their metal meshes): never bend (one blend
      of weights: the mean of B's weights over its bound points, top 8; its blend shapes as their mean delta) but are
      made to measure per body: rotation + translation + a scale per own principal axis (0.85-1.25, no shear) fit to
      the field's move, then the smallest change of translation and scales that clears the new skin (an LP). Small
      components (rivets, gems: under 2% of the tier's rigid area) ride the nearest big component.
    refuse or flag: on a body other than the bind body every row's meshes are measured (field_metrics: stretch beyond
      the body's own on edges of 1.5 mm and more, edges over 2x, inside the new skin, the tight set's clearance) and
      the row's "fit" is "ok" or "flagged" with "fit_fail" (the failing numbers per mesh); the game skips flagged rows
      on NPC bodies.
Writes <out>/<id>.gltf + .bin (A's node and mesh names, mesh extras, materials; B's body.glb skin verbatim) and
<out>/gear_index.json (A's row fields, "file", "body_hash" = the body glb's sha1), and <id>.sockets.json for armor.

`check --body <dir> [--synthetic]` reports the acceptance numbers (JSON + a short table): on the bind body the identity,
on another body (built on the base: a slider variant, a second woman) it builds it and reports each mesh's follow
numbers and the flagged rows; `check --field all` runs the synthetic and the +1 slider stress bodies (information).

    python tools/armor/gear_fit.py bind [--only id,id]
    python tools/armor/gear_fit.py build --body godot/art/people/body_p1 [--out dir] [--only ...]
    python tools/armor/gear_fit.py check --body godot/art/people/body_p1 [--synthetic]
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import time

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "tools", "body"))
sys.path.insert(0, os.path.join(REPO, "tools", "anim"))

from surfdist import Surface  # noqa: E402
from skin import Gltf  # noqa: E402
import gear_field  # noqa: E402

PEOPLE = os.path.join(REPO, "godot", "art", "people")
ARMOR = os.path.join(REPO, "godot", "art", "armor")
GEAR = os.path.join(REPO, "godot", "art", "gear")
BIND = os.path.join(GEAR, "bind")
BIND_VERSION = 1  # bump when the bind step changes what it writes; `stale` then rebinds everything
OUT = os.path.join(GEAR, "out")
BIND_BODY = os.path.join(PEOPLE, "body_p1")
A_PATH = os.path.join(PEOPLE, "heroine.glb")
BAND_MM = {0: 1.0, 1: 1.0, 2: 2.0, 3: 3.0}
BENDY_MATS = ("leather", "thread", "cloth", "satin", "fur", "hide", "linen", "stocking", "glove", "pipe")
SMALL_SHARE = 0.02
SMOOTH = {"rounds": 12, "near_m": 0.004, "far_m": 0.02}
TIERS = ("close", "play")


def U(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def rel(p):
    return os.path.relpath(p, REPO).replace("\\", "/")


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


# ---------------------------------------------------------------- units (rows)

def is_rigid_mesh(unit_rigid, node):
    if not unit_rigid or node.endswith(".shadow"):
        return False
    mat = node.rsplit(".", 1)[-1]
    return not any(k in mat for k in BENDY_MATS)


def units():
    """Every gear unit: {id, kind, row, src (repo-relative A file), meshes [(node, tier, rigid)], sockets}."""
    out = []
    rows = json.load(open(os.path.join(PEOPLE, "armor_index.json")))
    callings = []
    for r in rows:
        f = os.path.join(PEOPLE, f"heroine_outfit_{r['outfit']}.gltf")
        out.append({"id": r["id"], "kind": "outfit", "row": r, "src": rel(f),
                    "meshes": [(m, "close", False) for m in r["meshes"]], "sockets": None})
        if r["outfit"] not in callings:
            callings.append(r["outfit"])
    for c in callings:
        f = os.path.join(PEOPLE, f"heroine_outfit_{c}_lod.gltf")
        js = json.load(open(f))
        ms = [n["name"] for n in js["nodes"] if "mesh" in n and n["name"] != "lod_body"]
        out.append({"id": f"{c}.lod", "kind": "outfit_lod",
                    "row": {"id": f"{c}.lod", "outfit": c, "slot": None, "lod": True, "meshes": ms},
                    "src": rel(f), "meshes": [(m, "play", False) for m in ms], "sockets": None})
    for r in json.load(open(os.path.join(ARMOR, "armor_index.json"))):
        f = os.path.join(ARMOR, f"{r['id']}.gltf")
        js = json.load(open(f))
        rigid = bool(r.get("rigid")) or r["id"].startswith(("plate_", "mar_her_"))
        names = [n["name"] for n in js["nodes"] if "mesh" in n]
        ms = [(m, "close", is_rigid_mesh(rigid, m)) for m in r["meshes"]]
        ms += [(m, "play", is_rigid_mesh(rigid, m)) for m in names
               if m.startswith(r["id"] + ".lod1.") or m == r["id"] + ".shadow"]
        sk = os.path.join(ARMOR, f"{r['id']}.sockets.json")
        out.append({"id": r["id"], "kind": "armor", "row": r, "src": rel(f), "meshes": ms, "rigid_row": rigid,
                    "sockets": rel(sk) if os.path.exists(sk) else None})
    return out


# ---------------------------------------------------------------- bodies

def weld_ids(P, tol=1e-7):
    k = np.round(P / tol).astype(np.int64)
    _, inv = np.unique(k, axis=0, return_inverse=True)
    return inv.reshape(-1)


def vertex_normals(V, T, wid=None):
    if wid is None:
        wid = np.arange(len(V))
    Tw = wid[T]
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros((wid.max() + 1, 3))
    for k in range(3):
        np.add.at(N, Tw[:, k], fn)
    return U(N)[wid]


class Body:
    """A tier of a body as the bindings see it: [topology ; HeroineHead] points, triangles, normals, skin, shapes."""

    def __init__(self, Pt, Tt, Jt, Wt, shapes, Ph, Th, Jh, Wh, joint_names, name="body", glb=None, hash_=None):
        self.nt = len(Pt)
        self.ntri_t = len(Tt)
        self.V = np.vstack([Pt, Ph]).astype(np.float64)
        self.T = np.vstack([Tt, Th + self.nt]).astype(np.int64)
        pad = lambda a, k=8: np.pad(a, ((0, 0), (0, k - a.shape[1]))) if a.shape[1] < k else a[:, :k]  # noqa: E731
        self.J = np.vstack([pad(Jt), pad(Jh)]).astype(np.int64)
        self.W = np.vstack([pad(Wt), pad(Wh)]).astype(np.float64)
        self.shapes = {k: np.vstack([v, np.zeros((len(Ph), 3))]) for k, v in shapes.items()}
        wid = np.r_[np.arange(self.nt), self.nt + weld_ids(np.asarray(Ph, np.float64))]
        self.N = vertex_normals(self.V, self.T, wid)
        self.joint_names = joint_names
        self.name, self.glb, self.hash = name, glb, hash_
        self._surf = None

    @property
    def surf(self):
        if self._surf is None:
            self._surf = Surface(self.V, self.T)
        return self._surf

    @staticmethod
    def stage_dir(body_dir):
        st = os.path.join(body_dir, "stage")
        if os.path.isdir(st):
            return st
        pj = os.path.join(body_dir, "publish.json")
        if os.path.exists(pj):
            return os.path.join(REPO, json.load(open(pj))["source"], "stage")
        raise SystemExit(f"gear_fit: no stage for {body_dir} (no stage/ and no publish.json source)")

    @classmethod
    def load(cls, body_dir, tier):
        from gl import Glb
        path = os.path.join(body_dir, "body.glb" if tier == "close" else "play.glb")
        z = np.load(os.path.join(cls.stage_dir(body_dir), f"{tier}.npz"))
        g = Glb(path)
        m, h = g.mesh("Heroine"), g.mesh("HeroineHead")
        src, nv = z["src"], len(z["V"])
        assert len(src) == len(m.P), f"{path}: stage src does not match the glb"
        first = np.full(nv, -1)
        first[src[::-1]] = np.arange(len(src))[::-1]
        assert (first >= 0).all(), "a topology vertex has no glb vertex"
        Pt = m.P.astype(np.float64)[first]
        shapes = {k: v["POSITION"].astype(np.float64)[first] for k, v in m.targets.items()}
        names = [g.nodes[j].get("name") for j in g.js["skins"][0]["joints"]]
        Tt = src[z["T"]]  # (stage T indexes the glb's UV-split vertices: topology triangles are src[T])
        return cls(Pt, Tt, m.J[first], m.W[first], shapes, h.P, h.T, h.J, h.W, names,
                   name=os.path.basename(os.path.normpath(body_dir)), glb=path, hash_=sha1(path))

    def with_points(self, Vnew, name):
        """A copy of this body with its [topology ; head] points replaced (normals recomputed)."""
        b = object.__new__(Body)
        b.__dict__.update(self.__dict__)
        b.V = np.asarray(Vnew, np.float64)
        Ph = b.V[b.nt:]
        wid = np.r_[np.arange(b.nt), b.nt + weld_ids(Ph)]
        b.N = vertex_normals(b.V, b.T, wid)
        b.name, b._surf, b.hash = name, None, None
        return b


# ---------------------------------------------------------------- binding core

def frames(body, tri, w):
    """The bound points and their local frames [n,3,3] (columns t, b, n) on a body."""
    Tv = body.T[tri]
    P0, P1, P2 = body.V[Tv[:, 0]], body.V[Tv[:, 1]], body.V[Tv[:, 2]]
    p = w[:, :1] * P0 + w[:, 1:2] * P1 + w[:, 2:] * P2
    n = U(w[:, :1] * body.N[Tv[:, 0]] + w[:, 1:2] * body.N[Tv[:, 1]] + w[:, 2:] * body.N[Tv[:, 2]])
    e = P1 - P0
    t = U(e - (e * n).sum(1, keepdims=True) * n)
    b = np.cross(n, t)
    return p, np.stack([t, b, n], -1)


def q_bary(w):
    """Barycentrics quantized to uint16 (two stored) and their exact float values."""
    a = np.round(w[:, 0] * 65535).astype(np.int64)
    b = np.round(w[:, 1] * 65535).astype(np.int64)
    over = a + b - 65535
    b = np.where(over > 0, b - over, b)
    q = np.stack([a, b], 1).astype(np.uint16)
    return q, unq(q)


def unq(q):
    q = q.astype(np.float64) / 65535.0
    return np.c_[q, 1.0 - q[:, 0] - q[:, 1]]


def bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.where(np.abs(d00 * d11 - d01 * d01) < 1e-30, 1e-30, d00 * d11 - d01 * d01)
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    w = np.clip(np.stack([1 - v - w, v, w], 1), 0, None)
    return w / np.maximum(w.sum(1, keepdims=True), 1e-12)


def bind_points(body, X, N=None, k=16):
    """X (and unit vectors N) on body -> (tri int32, bary uint16 [n,2], local offset float32, local N)."""
    q, _, tri, _ = body.surf.closest(X, k=k)
    Tv = body.T[tri]
    w = bary(q, body.V[Tv[:, 0]], body.V[Tv[:, 1]], body.V[Tv[:, 2]])
    bq, wq = q_bary(w)
    p, F = frames(body, tri, wq)
    off = np.einsum("nji,nj->ni", F, X - p).astype(np.float32)
    nl = None if N is None else np.einsum("nji,nj->ni", F, N)
    return tri.astype(np.int32), bq, off, nl


def eval_points(body, tri, bq, off):
    p, F = frames(body, tri.astype(np.int64), unq(bq))
    return p + np.einsum("nij,nj->ni", F, off.astype(np.float64)), F


def snorm16(v):
    return np.round(np.clip(U(v), -1, 1) * 32767).astype(np.int16)


def unsnorm16(v):
    return U(v.astype(np.float64) / 32767.0)


def dense_weights(body, tri, w, nj):
    """[n, nj] B's skin weights at the bound points (barycentric over the triangle's corners)."""
    Tv = body.T[tri]
    J = body.J[Tv].reshape(len(tri), -1)
    W = (body.W[Tv] * w[:, :, None]).reshape(len(tri), -1)
    rows = np.repeat(np.arange(len(tri)), J.shape[1])
    D = np.bincount(rows * nj + J.reshape(-1), weights=W.reshape(-1), minlength=len(tri) * nj)
    return D.reshape(len(tri), nj)


def top_k(D, k=8):
    if D.shape[1] < k:
        D = np.pad(D, ((0, 0), (0, k - D.shape[1])))
    idx = np.argsort(-D, axis=1)[:, :k]
    val = np.take_along_axis(D, idx, 1)
    val = np.where(val > 0, val, 0)
    s = val.sum(1, keepdims=True)
    val = np.where(s > 0, val / np.maximum(s, 1e-12), 0)
    val[s[:, 0] <= 0, 0] = 1.0
    idx = np.where(val > 0, idx, 0)
    return idx.astype(np.uint16), val.astype(np.float32)


ROLES_PATH = os.path.join(HERE, "rigid_roles.json")
_ROLES = {}


def roles_path():
    """The roles file every tool reads: tools/armor/rigid_roles.json, or the file the GEAR_ROLES environment variable
    names (a trial's laws, tried without editing the repo's file while other builds run; child processes inherit it)."""
    return os.environ.get("GEAR_ROLES") or ROLES_PATH


def rigid_roles(path=None):
    """tools/armor/rigid_roles.json or GEAR_ROLES' file (roles_path; cached): the bone roles and, per slot, the roles a
    rigid blend may ride."""
    path = path or roles_path()
    if path not in _ROLES:
        _ROLES[path] = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {"slots": {}}
    return _ROLES[path]


def rigid_blend(body, trs, ws, slot, roles=None):
    """A rigid component's one blend of weights (top 8): the mean of B's weights over its bound points (trs, ws), kept to
    the roles its slot may ride (rigid_roles.json "slots": each role's share a number, or "mean": its share in the
    mean; "one_bone": each role's share on its strongest bone in the mean, else spread as in the mean; a role the mean
    does not reach rides its anchor, on the side the mean leans to). A slot with no rule keeps the mean."""
    import re
    names = body.joint_names
    D = dense_weights(body, trs, ws, len(names)).mean(0)
    rr = roles if roles is not None else rigid_roles()
    rule = rr.get("slots", {}).get(slot) if slot else None
    if rule:
        role = np.array([next((k for k, pats in rr["roles"].items() if any(re.fullmatch(p, n) for p in pats)), "")
                         for n in names])
        side = np.array([n[-2:] for n in names])
        lean = "l" if D[side == "_l"].sum() >= D[side == "_r"].sum() else "r"
        out = np.zeros(len(names))
        for k, v in rule["ride"].items():
            s = float(D[role == k].sum()) if v == "mean" else float(v)
            if s <= 0:
                continue
            part = np.where(role == k, D, 0.0)
            if part.sum() > 1e-9:
                if rule.get("one_bone"):
                    out[int(np.argmax(part))] += s
                else:
                    out += s * part / part.sum()
            else:
                a = rr.get("anchors", {}).get(k, "").replace("{s}", lean)
                if a in names:
                    out[names.index(a)] += s
        if out.sum() > 1e-9:
            D = out
    jj, ww = top_k(D[None])
    return jj[0], ww[0]


def body_weights(body, tri, w, k=8, chunk=60000):
    nj = len(body.joint_names)
    J = np.zeros((len(tri), k), np.uint16)
    W = np.zeros((len(tri), k), np.float32)
    for s in range(0, len(tri), chunk):
        J[s:s + chunk], W[s:s + chunk] = top_k(dense_weights(body, tri[s:s + chunk], w[s:s + chunk], nj), k)
    return J, W


def kabsch(A, B):
    """R, ca, cb with R (A - ca) + cb ~ B (rotation, no scale)."""
    ca, cb = A.mean(0), B.mean(0)
    H = (A - ca).T @ (B - cb)
    u, _, vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(vt.T @ u.T))
    R = vt.T @ np.diag([1, 1, d]) @ u.T
    return R, ca, cb


def edges_of(T):
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    e = np.sort(e, 1)
    e = e[e[:, 0] != e[:, 1]]
    return np.unique(e, axis=0)


def adjacency(E, n):
    A = sparse.coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    return A


def smooth_field(D, E, n, alpha, rounds):
    """Laplacian rounds of D over the edges, each vertex moved toward its neighbours' mean by alpha."""
    if not len(E) or not (alpha > 0).any():
        return D
    A = adjacency(E, n)
    deg = np.asarray(A.sum(1)).reshape(-1)
    a = (alpha * (deg > 0))[:, None]
    for _ in range(rounds):
        M = (A @ D) / np.maximum(deg, 1)[:, None]
        D = D + a * (M - D)
    return D


def components(T, n, P):
    """Connected components of a mesh (over unique vertices) and each one's area."""
    E = edges_of(T)
    nc, lab = connected_components(adjacency(E, n), directed=False) if len(E) else (n, np.arange(n))
    ar = 0.5 * np.linalg.norm(np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]), axis=1)
    area = np.bincount(lab[T[:, 0]], weights=ar, minlength=nc)
    return nc, lab, area


# ---------------------------------------------------------------- A -> B (bind time)

class Carrier:
    """A -> B at bind time. B's rest stance is not A's (her arms and legs stand at other angles: the bracers' points move
    17 cm, the boots' 12 cm), so a nearest-point carry with a turned offset tears every stand-off part (skirts and
    boots measured 30-60% p99 edge stretch). Instead each piece is POSED as A's body is posed into B's rest by the
    maps (her_target.target: the fit's bones, her_a's a_rest chain; tools/anim skin.Body, her helpers and correctives
    as the game sets them), with its own A weights, so it moves exactly as A's body under it moves (A's posed body ==
    the maps' src_a.P to 0.0 mm). What is left, B's surface against that posed A (p50 0.2, p95 1.8 mm; the breasts
    and hands most), is laid on as a field along posed A's normal at each piece point's closest posed-A point,
    smoothed over the piece toward vertices far from the skin. Clearance and push are measured on the full-resolution
    bodies for both tiers (A's lod_body is cut under each outfit: no surface to measure against)."""

    def __init__(self):
        from gl import Glb
        import her_a_target
        import skin
        from sliders import load_spec
        spec = load_spec(os.path.join(REPO, "tools", "body", "specs", "her_b.json"))
        ha = spec["her_a"]
        fit = load_spec(os.path.join(REPO, ha["fit_spec"]))
        cap = {}
        orig = skin.Body.globals

        def grab(self_, *a, **k):
            G = orig(self_, *a, **k)
            cap["G"], cap["body"] = G, self_
            return G
        skin.Body.globals = grab
        try:
            src_a = her_a_target.a_source(ha, fit)
        finally:
            skin.Body.globals = orig
        self.G, self.sk = cap["G"], cap["body"].sk
        a = Glb(A_PATH)
        am, ah = a.mesh("Heroine"), a.mesh("HeroineHead")
        assert len(src_a.P) == len(am.P)
        assert np.abs(cap["body"].pose(self.G) - src_a.P).max() < 1e-9, "the captured pose is not the maps' pose"
        self.na = len(am.P)
        self.AP = np.vstack([am.P, ah.P]).astype(np.float64)
        self.AT = np.vstack([am.T, ah.T + self.na])
        self.n_body_tris = len(am.T)
        g = Glb(os.path.join(BIND_BODY, "body.glb"))
        bm, bh = g.mesh("Heroine"), g.mesh("HeroineHead")
        # (the head: A's and B's HeroineHead share their vertex order; B's is A's moved, ~25 mm down)
        self.APb = np.vstack([np.asarray(src_a.P, np.float64), bh.P.astype(np.float64)])
        self.a_surf = Surface(self.AP, self.AT)
        self.p_surf = Surface(self.APb, self.AT)
        nb = len(bm.P)
        BP = np.vstack([bm.P, bh.P]).astype(np.float64)
        self.b_surf = Surface(BP, np.vstack([bm.T, bh.T + nb]))
        # the head: posed by the same pose (A's HeroineHead skinned on its Head and neck bones), and its field the full
        # vector to B's head (same vertex order; B's head is placed by the build, ~25 mm under A's posed one)
        import skin
        hb_ = skin.Body(self.sk, [(A_PATH, lambda n: n == "HeroineHead", "skin")], None, label="head", helpers=True)
        Hp = hb_.pose(self.G)
        assert len(Hp) == len(ah.P)
        self.APb[self.na:] = Hp
        self.p_surf = Surface(self.APb, self.AT)
        nA = vertex_normals(self.APb, self.AT, weld_ids(self.AP))
        q, _, _, _ = self.b_surf.closest(self.APb, k=16)
        self.e = ((q - self.APb) * nA).sum(1, keepdims=True) * nA
        self.e[self.na:] = bh.P.astype(np.float64) - Hp
        # the head moves rigidly A -> B (its skin mats are not the body's head bone's: B's head is placed by the
        # build); its points are B's own, the field there is the head's move
        self.head_move = (bh.P.astype(np.float64) - ah.P.astype(np.float64)).mean(0)
        self.AB_head = self.AP.copy()
        self.AB_head[self.na:] = bh.P.astype(np.float64)

    def a_clear(self, X):
        """Signed clearance to A's rest skin (outward +)."""
        q, fn, _, d = self.a_surf.closest(X, k=16)
        return d * np.sign(((X - q) * fn).sum(1) + 1e-15)

    def b_clear(self, X, tier=None):
        q, fn, _, d = self.b_surf.closest(X, k=16)
        return d * np.sign(((X - q) * fn).sum(1) + 1e-15), fn

    def pose_unit(self, path, nodes):
        """{node: (posed points [n,3], blended skin matrices [n,3,3])} for a file's nodes (A's rest -> B's rest)."""
        import skin
        pb = skin.Body(self.sk, [(path, lambda n: n in nodes, "skin")], None, label="piece", helpers=True)
        Xp = pb.pose(self.G)
        S = pb.skin_mats(self.G)[:, :3, :3]
        M = np.zeros((len(Xp), 3, 3))
        for k in range(pb.Jv.shape[1]):
            M += pb.W[:, k, None, None] * S[pb.Jv[:, k]]
        pc = np.array(pb.piece)
        return {n: (Xp[pc == n], M[pc == n], pb.P[pc == n]) for n in nodes}

    def field(self, Xp):
        """B's surface against posed A at each posed piece point's closest posed-A point."""
        q, _, t, _ = self.p_surf.closest(Xp, k=16)
        Tv = self.AT[t]
        w = bary(q, *(self.APb[Tv[:, k]] for k in range(3)))
        return (w[:, :, None] * self.e[Tv]).sum(1), np.linalg.norm(q - Xp, axis=1)


def least_rot(a, b):
    v = np.cross(a, b)
    c = (a * b).sum(1)
    K = np.zeros((len(a), 3, 3))
    K[:, 0, 1], K[:, 0, 2], K[:, 1, 0] = -v[:, 2], v[:, 1], v[:, 2]
    K[:, 1, 2], K[:, 2, 0], K[:, 2, 1] = -v[:, 0], -v[:, 1], v[:, 0]
    k = 1.0 / np.maximum(1.0 + c, 1e-9)
    return np.eye(3)[None] + K + np.einsum("nij,njk->nik", K, K) * k[:, None, None]


def a_rest_points(gl_, node_index, P, J, W):
    """A piece's points at A's rest (its file's inverse binds and joint rests; A's outfits are bound at rest)."""
    js = gl_.js
    sk = js["skins"][js["nodes"][node_index]["skin"]]
    ibm = gl_.accessor(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1).astype(np.float64)
    worlds = NodeWorlds(js)
    M = np.stack([worlds(j) for j in sk["joints"]]) @ ibm
    Ph = np.c_[P.astype(np.float64), np.ones(len(P))]
    Wn = W / np.maximum(W.sum(1, keepdims=True), 1e-12)
    out = np.zeros((len(P), 3))
    for k in range(J.shape[1]):
        out += Wn[:, k:k + 1] * np.einsum("nij,nj->ni", M[J[:, k]], Ph)[:, :3]
    return out


class NodeWorlds:
    def __init__(self, js):
        self.js = js
        self.parent = {c: i for i, n in enumerate(js["nodes"]) for c in n.get("children", [])}
        self.cache = {}

    def __call__(self, i):
        if i not in self.cache:
            from skin import _trs
            self.cache[i] = (self(self.parent[i]) if i in self.parent else np.eye(4)) @ _trs(self.js["nodes"][i])
        return self.cache[i]


def read_prim(gl_, node):
    """(node index, primitive dict, P, N, T, J, W) of a node's single primitive in a glTF."""
    js = gl_.js
    ni = next(i for i, n in enumerate(js["nodes"]) if n.get("name") == node and "mesh" in n)
    prims = js["meshes"][js["nodes"][ni]["mesh"]]["primitives"]
    assert len(prims) == 1, f"{node}: one primitive expected"
    pr = prims[0]
    a = pr["attributes"]
    P = gl_.accessor(a["POSITION"]).astype(np.float32)
    N = gl_.accessor(a["NORMAL"]).astype(np.float64) if "NORMAL" in a else np.zeros((len(P), 3))
    T = gl_.accessor(pr["indices"]).reshape(-1, 3).astype(np.int64)
    sets = [s for s in range(4) if f"JOINTS_{s}" in a]
    J = np.concatenate([gl_.accessor(a[f"JOINTS_{s}"]).astype(np.int64) for s in sets], 1)
    W = np.concatenate([gl_.accessor(a[f"WEIGHTS_{s}"]).astype(np.float64) for s in sets], 1)
    return ni, pr, P, N, T, J, W


def uniques(P):
    v = np.ascontiguousarray(P.astype(np.float32)).view(np.dtype((np.void, 12))).reshape(-1)
    _, first, inv = np.unique(v, return_index=True, return_inverse=True)
    return first, inv.reshape(-1).astype(np.int32)


def rigid_groups(Xs, Ts, ns, rigid_flags):
    """Over the rigid meshes of one tier: (per mesh: global component id per unique or -1), leader per component,
    component areas."""
    comp_of, areas, base = [], [], 0
    for X, T, n, rg in zip(Xs, Ts, ns, rigid_flags):
        if not rg:
            comp_of.append(np.full(n, -1, np.int64))
            continue
        nc, lab, area = components(T, n, X)
        comp_of.append(lab + base)
        areas.append(area)
        base += nc
    if not base:
        return comp_of, np.zeros(0, np.int64), np.zeros(0)
    areas = np.concatenate(areas)
    big = areas >= SMALL_SHARE * areas.sum()
    if not big.any():
        big[np.argmax(areas)] = True
    lead = np.arange(base)
    Pall = np.vstack([X[c >= 0] for X, c in zip(Xs, comp_of) if (c >= 0).any()])
    Call = np.concatenate([c[c >= 0] for c in comp_of if (c >= 0).any()])
    from scipy.spatial import cKDTree
    keep = big[Call]
    tree = cKDTree(Pall[keep])
    ccent = np.zeros((base, 3))
    np.add.at(ccent, Call, Pall)
    ccent /= np.maximum(np.bincount(Call, minlength=base), 1)[:, None]
    for c in np.where(~big)[0]:
        _, j = tree.query(ccent[c])
        lead[c] = Call[keep][j]
    return comp_of, lead, areas


def procrustes_move(X0, X1, comp, lead):
    """Each rigid vertex moved by its leader component's rigid transform taking X0 onto X1 (bendy rows untouched)."""
    out = X1.copy()
    rot = {}
    for c in np.unique(lead[comp[comp >= 0]]) if (comp >= 0).any() else []:
        m = (comp >= 0) & (lead[np.maximum(comp, 0)] == c)
        own = comp == c
        R, ca, cb = kabsch(X0[own], X1[own])
        out[m] = (X0[m] - ca) @ R.T + cb
        rot[int(c)] = R
    return out, rot


def bind_unit(u, car, bodies):
    """One unit: A's meshes carried to B (her_b), the move smoothed over each piece (stand-off parts as one surface),
    rigid components placed by Procrustes, pushed to keep A's clearance (the layer band), bound to their tier's
    topology."""
    t0 = time.time()
    g = Gltf(os.path.join(REPO, u["src"]))
    band = BAND_MM.get(int(u["row"].get("layer") or 1), 1.0) / 1000.0
    rep = {"id": u["id"], "src": u["src"], "meshes": {}}
    arrays, metas = {}, []
    by_tier = {}
    posed = car.pose_unit(os.path.join(REPO, u["src"]), [m[0] for m in u["meshes"]])
    for i, (node, tier, rg) in enumerate(u["meshes"]):
        ni, pr, P, N, T, J, W = read_prim(g, node)
        Xp_all, M_all, P_check = posed[node]
        assert len(P_check) == len(P) and np.abs(P_check - P).max() < 1e-6, f"{node}: posed order differs"
        first, inv = uniques(P)
        X = a_rest_points(g, ni, P, J, W)[first]
        Xp = Xp_all[first]
        ev, _ = car.field(Xp)
        cA = car.a_clear(X)
        Tu = inv[T]
        E = edges_of(Tu)
        alpha = np.clip((np.abs(cA) - SMOOTH["near_m"]) / (SMOOTH["far_m"] - SMOOTH["near_m"]), 0, 1)
        D = smooth_field(ev, E, len(X), alpha, SMOOTH["rounds"])
        Xb = Xp + D
        # (on the head: the head moves rigidly A -> B, and a piece skinned over Head and neck bones (the hood) poses
        # only half that move (12 of 25 mm); a vertex whose closest A point is on the head takes the head's move,
        # blended over the piece's edges into the posed carry below it)
        qa, _, ta, _ = car.a_surf.closest(X, k=16)
        h = (ta >= car.n_body_tris).astype(np.float64)[:, None]
        if h.any():
            Ta = car.AT[ta]
            wa = bary(qa, *(car.AP[Ta[:, k]] for k in range(3)))
            mv = (wa[:, :, None] * (car.AB_head - car.AP)[Ta]).sum(1)     # the closest head point's own move
            mv = np.where(h > 0, mv, car.head_move)
            mv = smooth_field(mv, E, len(X), np.maximum(alpha, 0.5), 30)
            h = smooth_field(h, E, len(X), np.ones(len(X)), 8)
            Xb = h * (X + mv) + (1 - h) * Xb
        Nv = U(np.einsum("nij,nj->ni", M_all, U(N)))
        if h.any():
            Nv = U(h[inv] * U(N) + (1 - h[inv]) * Nv)
        by_tier.setdefault(tier, []).append(dict(i=i, node=node, rg=rg, X=X, Xb=Xb, Nv=Nv, Mu=M_all[first], N=U(N), inv=inv,
                                                 T=Tu, E=E, nv=len(P), cA=cA, move=np.linalg.norm(Xb - X, axis=1)))
    aux = None
    if u.get("sockets"):
        aux = socket_points(json.load(open(os.path.join(REPO, u["sockets"]))))
    for tier, ms in by_tier.items():
        body = bodies[tier]
        comp_of, lead, areas = rigid_groups([m["X"] for m in ms], [m["T"] for m in ms], [len(m["X"]) for m in ms],
                                           [m["rg"] for m in ms])
        X0 = np.vstack([m["X"] for m in ms])
        X1 = np.vstack([m["Xb"] for m in ms])
        comp = np.concatenate(comp_of)
        X1r, rotAB = procrustes_move(X0, X1, comp, lead) if len(lead) else (X1, {})
        cA = np.concatenate([m["cA"] for m in ms])
        need = np.minimum(cA, band)
        moved = np.zeros((len(X1r), 3))
        rgm = comp >= 0
        for _ in range(6):
            cB, fn = car.b_clear(X1r)
            short = need - cB
            short[short < 1e-6] = 0
            if not short.any():
                break
            push = short[:, None] * fn
            push[rgm] = 0
            for c in (np.unique(lead[comp[rgm]]) if rgm.any() else []):
                mm = rgm & (lead[np.maximum(comp, 0)] == c)
                if short[mm].any():
                    push[mm] = min_translation(fn[mm], short[mm])
            moved += push
            X1r = X1r + push
        off = 0
        for m in ms:
            n = len(m["X"])
            m["Xb"] = X1r[off:off + n]
            m["comp"] = comp[off:off + n]
            m["moved"] = np.linalg.norm(moved[off:off + n], axis=1)
            off += n
        bind_tier(u, tier, ms, body, car, rotAB, lead, arrays, metas, rep)
        arrays[f"lead_{tier}"] = lead.astype(np.int32)
    if aux:
        bind_aux(u, aux, car, bodies["close"], by_tier.get("close", []), arrays, metas)
    meta = {"id": u["id"], "kind": u["kind"], "bind_version": BIND_VERSION, "src": u["src"], "src_sha1": sha1(os.path.join(REPO, u["src"])),
            "bind_body": rel(BIND_BODY), "bind_hash": {t: bodies[t].hash for t in TIERS},
            "meshes": metas, "sockets": u.get("sockets"), "aux": aux and {"keys": aux["keys"]},
            "row": u["row"], "rigid_row": u.get("rigid_row", False)}
    arrays["meta"] = np.frombuffer(json.dumps(meta).encode(), np.uint8)
    os.makedirs(BIND, exist_ok=True)
    np.savez_compressed(os.path.join(BIND, f"{u['id']}.npz"), **arrays)
    rep["secs"] = round(time.time() - t0, 1)
    return rep


def min_translation(fn, short, iters=300):
    """A small translation t with fn_i . t >= short_i for all i (cyclic projections onto the violated half-spaces)."""
    t = np.zeros(3)
    for _ in range(iters):
        v = short - fn @ t
        k = int(np.argmax(v))
        if v[k] <= 1e-7:
            break
        t = t + v[k] * fn[k]
    return t


def bind_tier(u, tier, ms, body, car, rotAB, lead, arrays, metas, rep):
    pc = lambda x: [round(float(v), 3) for v in np.percentile(x * 1000, [50, 95, 100])] if len(x) else []  # noqa: E731
    for m in ms:
        i = m["i"]
        Xb = m["Xb"]
        comp = m["comp"]
        Nb = m["Nv"].copy()
        for c, Rc in rotAB.items():
            sel = ((comp >= 0) & (lead[np.maximum(comp, 0)] == c))[m["inv"]]
            Nb[sel] = m["N"][sel] @ Rc.T
        tri, bq, off, _ = bind_points(body, Xb)
        _, F = frames(body, tri.astype(np.int64), unq(bq))
        nloc = np.einsum("nji,nj->ni", F[m["inv"]], Nb)
        arrays.update({f"inv{i}": m["inv"], f"tri{i}": tri, f"bw{i}": bq, f"off{i}": off, f"nrm{i}": snorm16(nloc),
                       f"comp{i}": comp.astype(np.int32)})
        metas.append({"i": i, "node": m["node"], "tier": tier, "rigid": bool(m["rg"]), "nv": int(m["nv"]),
                      "nu": int(len(Xb))})
        Xe, _ = eval_points(body, tri, bq, off)
        cB, _ = car.b_clear(Xb)
        cA = m["cA"]
        E = m["E"]
        la = np.linalg.norm(m["X"][E[:, 0]] - m["X"][E[:, 1]], axis=1)
        lb = np.linalg.norm(Xb[E[:, 0]] - Xb[E[:, 1]], axis=1)
        ok = la > 1e-4
        st = np.abs(lb[ok] / la[ok] - 1) if ok.any() else np.zeros(1)
        out_ = cA >= 0
        rep["meshes"][m["node"]] = {
            "tier": tier, "rigid": bool(m["rg"]), "verts": int(m["nv"]), "uniques": int(len(Xb)),
            "identity_mm": round(float(np.abs(Xe - Xb).max() * 1000), 5),
            "a_inside": int((cA < 0).sum()), "b_inside": int((cB < 0).sum()),
            "offset_change_mm_p50_95_max": pc(np.abs(cB - cA)),
            "offset_change_outside_mm_p50_95_max": pc(np.abs(cB - cA)[out_]),
            "offset_change_tight_mm_p50_95_max": pc(np.abs(cB - cA)[out_ & (cA < SMOOTH["near_m"])]),
            "standoff_share": round(float((cA >= SMOOTH["near_m"]).mean()), 3),
            "move_mm_p50_95_max": pc(m["move"]),
            "pushed": int((m["moved"] > 1e-6).sum()), "push_mm_max": round(float(m["moved"].max() * 1000), 3) if len(Xb) else 0,
            "edge_stretch_ab_pct_p99_max": [round(float(np.percentile(st, 99) * 100), 2), round(float(st.max() * 100), 2)]}
        os.makedirs(os.path.join(OUT, "_bindref"), exist_ok=True)
        np.save(os.path.join(OUT, "_bindref", f"{u['id']}.{i}.npy"), Xb.astype(np.float64))


# sockets: points, frames and weights carried with the shell

def socket_points(sj):
    keys, P, Nn, Up = [], [], [], []
    for name, s in (sj.get("sockets") or {}).items():
        keys.append(["socket", name])
        P.append(s["point"])
        Nn.append(s.get("normal", [0, 0, 1]))
        Up.append(s.get("up", [0, 1, 0]))
    for name, r in (sj.get("rims") or {}).items():
        for k, p in enumerate(r.get("points", [])):
            keys.append(["rim", name, k])
            P.append(p)
            Nn.append([0, 0, 1])
            Up.append([0, 1, 0])
    for k, p in enumerate(sj.get("fixings") or []):
        keys.append(["fixing", k])
        P.append(p)
        Nn.append([0, 0, 1])
        Up.append([0, 1, 0])
    if not keys:
        return None
    return {"keys": keys, "P": np.array(P, float), "N": U(np.array(Nn, float)), "Up": U(np.array(Up, float))}


def bind_aux(u, aux, car, body, ms, arrays, metas):
    """Socket / rim / fixing points: carried as piece points; on a rigid row each rides its nearest rigid
    component (its comp id stored), bendy otherwise."""
    from scipy.spatial import cKDTree
    P0 = np.vstack([m["X"] for m in ms])
    _, j = cKDTree(P0).query(aux["P"])
    mv = np.vstack([m["Xb"] - m["X"] for m in ms])[j]
    Mu = np.concatenate([m["Mu"] for m in ms])[j]
    Xb = aux["P"] + mv          # (the nearest piece point's move: points on or next to the shell)
    Nb = U(np.einsum("nij,nj->ni", Mu, aux["N"]))
    Ub = U(np.einsum("nij,nj->ni", Mu, aux["Up"]))
    comp = np.full(len(Xb), -1, np.int64)
    rig = [m for m in ms if m["rg"]]
    if rig:
        from scipy.spatial import cKDTree
        P0 = np.vstack([m["X"] for m in rig])
        C = np.concatenate([m["comp"] for m in rig])
        lead = arrays["lead_close"]
        d, j = cKDTree(P0).query(aux["P"])
        comp = np.where(d < 0.05, lead[C[j]], -1)
        # the rigid ride: the same transform as the component on A -> B
        P1 = np.vstack([m["Xb"] for m in rig])
        for c in np.unique(comp[comp >= 0]):
            sel = lead[C] == c
            R, ca, cb = kabsch(P0[sel], P1[sel])
            a = comp == c
            Xb[a] = (aux["P"][a] - ca) @ R.T + cb
            Nb[a] = aux["N"][a] @ R.T
            Ub[a] = aux["Up"][a] @ R.T
    tri, bq, off, nl = bind_points(body, Xb, Nb)
    _, F = frames(body, tri.astype(np.int64), unq(bq))
    ul = np.einsum("nji,nj->ni", F, Ub)
    arrays.update({"aux_tri": tri, "aux_bw": bq, "aux_off": off, "aux_nrm": snorm16(nl), "aux_up": snorm16(ul),
                   "aux_comp": comp.astype(np.int32)})


# ---------------------------------------------------------------- evaluation (build time)

class Binding:
    def __init__(self, path):
        z = np.load(path)
        self.z = {k: z[k] for k in z.files}
        self.meta = json.loads(bytes(self.z["meta"]).decode())
        self.id = self.meta["id"]


# (GEAR_STANDOFF: a trial copy of the measured targets, as GEAR_ROLES is of the roles; unset = the live folder)
STANDOFF = os.environ.get("GEAR_STANDOFF") or os.path.join(GEAR, "standoff")


def standoff_law(slot, roles=None):
    """rigid_roles.json slots[slot]["standoff"] (or None): the stand-off law of the slot's plates."""
    rr = roles if roles is not None else rigid_roles()
    return (rr.get("slots", {}).get(slot) or {}).get("standoff")


def top_groups(X, comp, lead, side_m=0.02):
    """Per point: True where its rigid group (a leader's components: a plate with its rivets and trims) is one of the
    TOPMOST of its side (left, right, or the middle within side_m of x = 0): the group reaching highest (Y) and every
    group whose mean height is at or above that group's lowest point (a cop's layers of steel, leather and gold are
    separate groups at one height; the lames hang below it)."""
    comp = np.asarray(comp)
    g = np.where(comp >= 0, np.asarray(lead)[np.maximum(comp, 0)], -1)
    ids = np.unique(g[g >= 0])
    top = np.zeros(len(g), bool)
    if not len(ids):
        return top
    mx = np.array([X[g == k, 0].mean() for k in ids])
    side = np.where(np.abs(mx) < side_m, 0, np.sign(mx)).astype(int)
    my = np.array([X[g == k, 1].mean() for k in ids])
    for sd in np.unique(side):
        of = np.nonzero(side == sd)[0]
        hi = of[int(np.argmax([X[g == ids[k], 1].max() for k in of]))]
        lo = X[g == ids[hi], 1].min()
        for k in of:
            if my[k] >= lo:
                top[g == ids[k]] = True
    return top


def standoff_floor(bd, ms, ev, path=None):
    """The stand-off each rigid point of a tier must reach (m; NaN where none), or None: the slot's law
    (rigid_roles.json "standoff": "cap_mm") over the unit's measured targets (godot/art/gear/standoff/<id>.json, written
    by tools/armor/gear_standoff.py from her skin's excursion under the plate over the clips: per node, [unique vertex,
    clearance m]). A measured need over the cap is held at the cap (a plate that stands further off floats); "cap_mm" 0 is no
    stand-off (the law's tuck keys alone). "seat_cap_mm" (optional) is the cap of the TOPMOST rigid plates of each side
    (a pauldron's cop and what rides it: top_groups), so the cop stays seated on the shoulder top while the lames below
    it may stand off to "cap_mm". "rest_min_mm" (optional) is THE REST FLOOR: every rigid point, measured need or not,
    stands at least this far off her untucked skin at rest (a point the clips never drove through has no target, and
    sat under her skin where the form the plate was made on was smaller than she is)."""
    law = standoff_law(bd.meta["row"].get("slot"))
    fp = path or os.path.join(STANDOFF, f"{bd.id}.json")
    if not law or not os.path.isfile(fp):
        return None
    tg = json.load(open(fp)).get("targets", {})
    cap = float(law.get("cap_mm", 20.0)) / 1000.0
    if cap <= 0:
        return None
    rest = float(law.get("rest_min_mm", 0.0)) / 1000.0
    caps = [np.full(len(ev[m["i"]]["X"]), cap) for m in ms]
    if ms and law.get("seat_cap_mm") is not None:
        comp = np.concatenate([ev[m["i"]]["comp"] for m in ms])
        top = top_groups(np.vstack([ev[m["i"]]["Xbind"] for m in ms]), comp, bd.z[f"lead_{ms[0]['tier']}"])
        seat = np.where(top, min(cap, float(law["seat_cap_mm"]) / 1000.0), cap)
        caps = np.split(seat, np.cumsum([len(c) for c in caps])[:-1])
    out = []
    for m in ms:
        f = np.full(len(ev[m["i"]]["X"]), np.nan)
        for u, c in tg.get(m["node"], []):
            if 0 <= int(u) < len(f):
                f[int(u)] = min(float(c), caps[len(out)][int(u)])
        if rest > 0:
            f = np.where(np.isfinite(f), np.maximum(f, rest), rest)
        f[ev[m["i"]]["comp"] < 0] = np.nan
        out.append(f)
    out = np.concatenate(out) if out else np.zeros(0)
    return out if np.isfinite(out).any() else None


def eval_unit(bd, bodies, bind_bodies, stats=None):
    """{node: dict(P, N, J, W, shapes)} and aux on one body; bind_bodies None when the body IS the bind body."""
    z, out = bd.z, {}
    fit = {"rigid": {}, "solve": {}}
    rots_tier = {}
    for tier in TIERS:
        ms = [m for m in bd.meta["meshes"] if m["tier"] == tier]
        if not ms:
            continue
        body = bodies[tier]
        bbody = None if bind_bodies is None else bind_bodies[tier]
        lead = z[f"lead_{tier}"]
        rots = {}
        ev = {}
        for m in ms:
            i = m["i"]
            tri, bq, off = z[f"tri{i}"], z[f"bw{i}"], z[f"off{i}"]
            X, F = eval_points(body, tri, bq, off)
            Xbind, Fbind = (X, F) if bbody is None else eval_points(bbody, tri, bq, off)
            ev[i] = dict(X=X, F=F, Xbind=Xbind, Fbind=Fbind, w=unq(bq), tri=tri.astype(np.int64), comp=z[f"comp{i}"])
            if bbody is not None:
                # the follow field (gear_field): exact on the skin (1 mm), the body's smoothed move beyond; c0 is the
                # vertex's signed clearance on the bind body (what the tight set holds and the push keeps)
                c0, n0 = gear_field.signed_clear(bbody, Xbind, k=16)
                bt = gear_field.beta(c0)
                fld = gear_field.field_for(body, bbody)
                Xf, G = fld(Xbind)
                Xe, Re = gear_field.exact_follow(X, F, Xbind, Fbind, off)
                ev[i].update(c0=c0, n0=n0, beta=bt, G=G, Gk=fld.gradient(Xbind), Re=Re, X=Xe + bt[:, None] * (Xf - Xe))
        # rigid components: transforms from all rigid uniques of the tier
        comp = np.concatenate([ev[m["i"]]["comp"] for m in ms])
        # (the stand-off law, rigid_roles.json slots "standoff": each plate point's measured need, on every body)
        flo = standoff_floor(bd, ms, ev)
        if (comp >= 0).any() and (bbody is not None or flo is not None):
            Xa = np.vstack([ev[m["i"]]["Xbind"] for m in ms])
            Xn = np.vstack([ev[m["i"]]["X"] for m in ms])
            if bbody is None:
                c0s = gear_field.signed_clear(body, Xa, k=16)[0]
            else:
                c0s = np.concatenate([ev[m["i"]]["c0"] for m in ms])
            for c in np.unique(lead[comp[comp >= 0]]):
                # made to measure: rotation + translation + a scale per own principal axis (never bends: one blend
                # of weights), then the smallest translation that clears it (and stands off where she moves)
                own = comp == c
                grp = (comp >= 0) & (lead[np.maximum(comp, 0)] == c)
                fg = None if flo is None else flo[grp]
                if bbody is None and (fg is None or not np.isfinite(fg).any()):
                    continue
                M, ca, cb, info = gear_field.rigid_fit_clear(body, Xa[own], Xn[own], Xa[grp], c0s[grp], fg)
                rots[int(c)] = (M, ca, cb)
                fit["rigid"][f"{tier}/{int(c)}"] = info
        rots_tier[tier] = rots
        if bbody is not None:
            # one smooth correction over every mesh of the tier at once (gear_field.follow_solve: each edge keeps the
            # field's expected deformation, the tight set its bind clearance, the rest clear of the new skin), so a
            # garment's layers (leather, its stitches, its trims) are moved as one
            cut = np.cumsum([0] + [len(ev[m["i"]]["X"]) for m in ms])
            Xall = np.vstack([ev[m["i"]]["X"] for m in ms])
            c0all = np.concatenate([ev[m["i"]]["c0"] for m in ms])
            bend_all = comp < 0
            Tall = np.vstack([bd_tris(bd, m["i"]) + cut[k] for k, m in enumerate(ms)])
            Xall, sst = gear_field.follow_solve(body, Xall, np.vstack([ev[m["i"]]["Xbind"] for m in ms]), Tall,
                                                np.concatenate([ev[m["i"]][gear_field.SOLVE["target"]] for m in ms]),
                                                np.concatenate([ev[m["i"]]["Gk"] for m in ms]), c0all, np.vstack([ev[m["i"]]["n0"] for m in ms]), bend_all)
            fit["solve"][tier] = sst
            if stats is not None:
                stats[tier] = dict(sst)
            for k, m in enumerate(ms):
                ev[m["i"]]["X"] = np.where(bend_all[cut[k]:cut[k + 1], None], Xall[cut[k]:cut[k + 1]], ev[m["i"]]["X"])
        for m in ms:
            e = ev[m["i"]]
            i, comp_i = m["i"], e["comp"]
            X = e["X"]
            inv = z[f"inv{i}"]
            nloc = unsnorm16(z[f"nrm{i}"])
            N = np.einsum("nij,nj->ni", e["F"][inv], nloc)
            if bbody is not None:
                bend = comp_i < 0
                if bend.any():
                    # normals: the exact frame's near the skin, the field's (J^-T of the bind normal) beyond
                    bt = e["beta"]
                    Nb = np.einsum("nij,nj->ni", e["Fbind"][inv], nloc)
                    Ji = np.linalg.inv(np.eye(3)[None] + bt[:, None, None] * (e["G"] - np.eye(3)[None]))
                    Nf = U(np.einsum("nji,nj->ni", Ji[inv], Nb))
                    bv = (bt * bend)[inv][:, None]
                    Ne = np.einsum("nij,nj->ni", e["Re"][inv], Nb)
                    N = np.where(bend[inv][:, None], (1 - bv) * Ne + bv * Nf, N)
            rg = comp_i >= 0
            if rots and rg.any():
                Nb = np.einsum("nij,nj->ni", e["Fbind"][inv], nloc)
                for c, (M, ca, cb) in rots.items():
                    sel = rg & (lead[np.maximum(comp_i, 0)] == c)
                    X[sel] = (e["Xbind"][sel] - ca) @ M.T + cb
                    sv = sel[inv]
                    N[sv] = Nb[sv] @ np.linalg.inv(M)
            # weights and shapes
            J, W = body_weights(body, e["tri"], e["w"])
            Tv = body.T[e["tri"]]
            shapes = {}
            for nm, dP in body.shapes.items():
                s = (e["w"][:, :, None] * dP[Tv]).sum(1)
                if np.abs(s).max() > 1e-5:
                    shapes[nm] = s
            rg = comp_i >= 0
            if rg.any():
                for c in np.unique(lead[comp_i[rg]]):
                    sel = rg & (lead[np.maximum(comp_i, 0)] == c)
                    own_all = np.concatenate([ev[mm["i"]]["comp"] for mm in ms]) == c
                    # the leader's bound points over all meshes of the tier
                    trs = np.concatenate([ev[mm["i"]]["tri"] for mm in ms])[own_all]
                    ws = np.vstack([ev[mm["i"]]["w"] for mm in ms])[own_all]
                    J[sel], W[sel] = rigid_blend(body, trs, ws, bd.meta["row"].get("slot"))
                    Tvs = body.T[trs]
                    for nm, dP in body.shapes.items():
                        mean = (ws[:, :, None] * dP[Tvs]).sum(1).mean(0)
                        if nm in shapes:
                            shapes[nm][sel] = mean
                        elif np.abs(mean).max() > 1e-5:
                            shapes[nm] = np.where(sel[:, None], mean, (e["w"][:, :, None] * dP[Tv]).sum(1))
            out[m["node"]] = {"Xu": X, "inv": inv, "N": U(N), "J": J[inv], "W": W[inv],
                              "shapes": {k: v[inv] for k, v in shapes.items()}, "tier": tier, "comp": comp_i,
                              "Xbind": e["Xbind"], "h": z[f"off{i}"][:, 2]}
            if "beta" in e:
                out[m["node"]].update(beta=e["beta"], G=e["G"], Gk=e["Gk"])
    if "aux_tri" in z:
        body = bodies["close"]
        tri, bq, off = z["aux_tri"], z["aux_bw"], z["aux_off"]
        X, F = eval_points(body, tri, bq, off)
        Nn = np.einsum("nij,nj->ni", F, unsnorm16(z["aux_nrm"]))
        Up = np.einsum("nij,nj->ni", F, unsnorm16(z["aux_up"]))
        comp = z["aux_comp"]
        if (comp >= 0).any() and rots_tier.get("close"):
            # sockets on a rigid component ride its fit (positions by the full map, directions turned by its rotation)
            Xb, Fb = eval_points(bodies["close"] if bind_bodies is None else bind_bodies["close"], tri, bq, off)
            rots = rots_tier.get("close", {})
            for c in np.unique(comp[comp >= 0]):
                if int(c) not in rots:
                    continue
                M, ca, cb = rots[int(c)]
                u_, _, vt_ = np.linalg.svd(M)
                R = u_ @ vt_
                a = comp == c
                X[a] = (Xb[a] - ca) @ M.T + cb
                Nn[a] = np.einsum("nij,nj->ni", Fb[a], unsnorm16(z["aux_nrm"][a])) @ R.T
                Up[a] = np.einsum("nij,nj->ni", Fb[a], unsnorm16(z["aux_up"][a])) @ R.T
        J, W = body_weights(body, tri.astype(np.int64), unq(bq), k=4)
        out["__aux__"] = {"X": X, "N": U(Nn), "Up": U(Up), "J": J, "W": W}
    if bind_bodies is not None:
        out["__fit__"] = fit
    return out


_EDGES = {}


def bd_edges(bd, i):
    """The piece mesh's edges over its uniques (from A's file indices, cached)."""
    key = (bd.id, i)
    if key not in _EDGES:
        g = gltf_cached(bd.meta["src"])
        node = next(m["node"] for m in bd.meta["meshes"] if m["i"] == i)
        js = g.js
        ni = next(k for k, n in enumerate(js["nodes"]) if n.get("name") == node and "mesh" in n)
        pr = js["meshes"][js["nodes"][ni]["mesh"]]["primitives"][0]
        T = g.accessor(pr["indices"]).reshape(-1, 3).astype(np.int64)
        _EDGES[key] = edges_of(bd.z[f"inv{i}"][T])
        _TRIS[key] = bd.z[f"inv{i}"][T]
    return _EDGES[key]


_TRIS = {}


def bd_tris(bd, i):
    """The piece mesh's triangles over its uniques (cached with bd_edges)."""
    if (bd.id, i) not in _TRIS:
        bd_edges(bd, i)
    return _TRIS[(bd.id, i)]


_GL = {}


def gltf_cached(src):
    if src not in _GL:
        _GL[src] = Gltf(os.path.join(REPO, src))
    return _GL[src]


# ---------------------------------------------------------------- writing

def write_unit(path, bd, ev, ref_glb):
    """<id>.gltf + .bin: B's joints and skin verbatim, A's nodes / meshes / materials with our geometry."""
    import glbwrite
    g = gltf_cached(bd.meta["src"])
    ajs = g.js
    rjs, rbin = glbwrite._read_glb(ref_glb)
    out = glbwrite._Out()
    sk = rjs["skins"][0]
    nj = len(sk["joints"])
    assert sk["joints"] == list(range(nj))
    nodes = [dict(rjs["nodes"][j]) for j in range(nj)]
    for n in nodes:
        n["children"] = [c for c in n.get("children", []) if c < nj]
        if not n["children"]:
            n.pop("children")
    skin = {"name": "Armature", "joints": list(range(nj)),
            "inverseBindMatrices": out.copy_acc(rjs, rbin, sk["inverseBindMatrices"])}
    # materials (and their textures, images uri'd from the out folder)
    mat_map, tex_map, img_map, smp_map = {}, {}, {}, {}
    mats, texs, imgs, smps = [], [], [], []
    src_dir = os.path.dirname(os.path.join(REPO, bd.meta["src"]))
    out_dir = os.path.dirname(path)

    def img(i):
        if i not in img_map:
            im = dict(ajs["images"][i])
            if "uri" in im:
                im["uri"] = os.path.relpath(os.path.join(src_dir, im["uri"]), out_dir).replace("\\", "/")
            imgs.append(im)
            img_map[i] = len(imgs) - 1
        return img_map[i]

    def smp(i):
        if i not in smp_map:
            smps.append(dict(ajs["samplers"][i]))
            smp_map[i] = len(smps) - 1
        return smp_map[i]

    def tex(i):
        if i not in tex_map:
            t = dict(ajs["textures"][i])
            if "source" in t:
                t["source"] = img(t["source"])
            if "sampler" in t:
                t["sampler"] = smp(t["sampler"])
            texs.append(t)
            tex_map[i] = len(texs) - 1
        return tex_map[i]

    def fix(o):
        if isinstance(o, dict):
            o = {k: fix(v) for k, v in o.items()}
            if "index" in o and isinstance(o["index"], int):
                o["index"] = tex(o["index"])
            return o
        if isinstance(o, list):
            return [fix(v) for v in o]
        return o

    def mat(i):
        if i not in mat_map:
            mats.append(fix(json.loads(json.dumps(ajs["materials"][i]))))
            mat_map[i] = len(mats) - 1
        return mat_map[i]

    meshes, mesh_nodes = [], []
    for m in bd.meta["meshes"]:
        e = ev[m["node"]]
        ni = next(k for k, n in enumerate(ajs["nodes"]) if n.get("name") == m["node"] and "mesh" in n)
        an = ajs["nodes"][ni]
        am = ajs["meshes"][an["mesh"]]
        pr = am["primitives"][0]
        P = e["Xu"][e["inv"]]
        att = {}
        for k, ai in pr["attributes"].items():
            if k == "POSITION":
                att[k] = out.acc(P.astype(np.float32), "VEC3", 5126, 34962, minmax=True)
            elif k == "NORMAL":
                att[k] = out.acc(e["N"].astype(np.float32), "VEC3", 5126, 34962)
            elif k.startswith(("JOINTS_", "WEIGHTS_", "TANGENT")):
                continue
            else:
                a = ajs["accessors"][ai]
                att[k] = out.acc(g.accessor(ai), a["type"], a["componentType"], 34962, normalized=a.get("normalized", False))
        for s in range(2):
            att[f"JOINTS_{s}"] = out.acc(e["J"][:, 4 * s:4 * s + 4], "VEC4", 5123, 34962)
            att[f"WEIGHTS_{s}"] = out.acc(e["W"][:, 4 * s:4 * s + 4], "VEC4", 5126, 34962)
        idx = g.accessor(pr["indices"]).astype(np.uint32).reshape(-1)
        p = {"attributes": att, "indices": out.acc(idx, "SCALAR", 5125, 34963)}
        if "material" in pr:
            p["material"] = mat(pr["material"])
        if "mode" in pr:
            p["mode"] = pr["mode"]
        names = sorted(e["shapes"])
        if names:
            p["targets"] = [{"POSITION": sparse_acc(out, e["shapes"][nm])} for nm in names]
        extras = dict(am.get("extras") or {})
        if names or "targetNames" in extras:
            extras["targetNames"] = names
        mesh = {"name": am.get("name", m["node"]), "primitives": [p]}
        if extras:
            mesh["extras"] = extras
        if names:
            mesh["weights"] = [0.0] * len(names)
        meshes.append(mesh)
        nd = {"name": m["node"], "mesh": len(meshes) - 1, "skin": 0}
        if an.get("extras"):
            nd["extras"] = an["extras"]
        mesh_nodes.append(nd)
    base = len(nodes)
    nodes += mesh_nodes
    roots = [j for j in range(nj) if not any(j in n.get("children", []) for n in nodes[:nj])]
    nodes.append({"name": "Armature", "children": list(range(base, base + len(mesh_nodes))) + roots})
    js = {"asset": {"generator": "Survivor Unchained tools/armor/gear_fit.py", "version": "2.0",
                    "extras": {"gear_fit": {"binding": f"godot/art/gear/bind/{bd.id}.npz", "a_source": bd.meta["src"]}}},
          "scene": 0, "scenes": [{"name": "Scene", "nodes": [len(nodes) - 1]}], "nodes": nodes, "meshes": meshes,
          "skins": [skin], "accessors": out.accs, "bufferViews": out.views}
    if mats:
        js["materials"] = mats
    if texs:
        js["textures"] = texs
    if imgs:
        js["images"] = imgs
    if smps:
        js["samplers"] = smps
    while len(out.bin) % 4:
        out.bin += b"\0"
    binname = os.path.basename(path)[:-5] + ".bin"
    js["buffers"] = [{"byteLength": len(out.bin), "uri": binname}]
    with open(os.path.join(out_dir, binname), "wb") as f:
        f.write(bytes(out.bin))
    with open(path, "w") as f:
        json.dump(js, f, separators=(",", ":"))


def sparse_acc(out, d, eps=1e-7):
    """A morph target POSITION accessor: sparse over zeros when that is smaller."""
    d = d.astype(np.float32)
    nz = np.where(np.abs(d).max(1) > eps)[0]
    mn = [float(x) for x in d.min(0)]
    mx = [float(x) for x in d.max(0)]
    if len(nz) * 16 >= len(d) * 12 or not len(nz):
        a = out.acc(d, "VEC3", 5126, 34962)
        out.accs[a]["min"], out.accs[a]["max"] = mn, mx
        return a
    iv = out.view(nz.astype(np.uint32).tobytes())
    vv = out.view(np.ascontiguousarray(d[nz]).tobytes())
    out.accs.append({"componentType": 5126, "count": int(len(d)), "type": "VEC3", "min": mn, "max": mx,
                     "sparse": {"count": int(len(nz)), "indices": {"bufferView": iv, "componentType": 5125},
                                "values": {"bufferView": vv}}})
    return len(out.accs) - 1


def write_sockets(path, bd, ev, body):
    sj = json.load(open(os.path.join(REPO, bd.meta["sockets"])))
    a = ev["__aux__"]
    names = body.joint_names
    out = json.loads(json.dumps(sj))
    out["body_hash"] = body.hash
    out["space"] = "glTF / Godot: Y up, metres, the body's bind pose (gear_fit build)"
    for k, key in enumerate(bd.meta["aux"]["keys"]):
        p = [round(float(x), 5) for x in a["X"][k]]
        if key[0] == "socket":
            s = out["sockets"][key[1]]
            s["point"], s["normal"] = p, [round(float(x), 5) for x in a["N"][k]]
            s["up"] = [round(float(x), 5) for x in a["Up"][k]]
            s["weights"] = [[names[int(j)], round(float(w), 4)] for j, w in zip(a["J"][k], a["W"][k]) if w > 0]
        elif key[0] == "rim":
            out["rims"][key[1]]["points"][key[2]] = p
        else:
            out["fixings"][key[1]] = p
    with open(path, "w") as f:
        json.dump(out, f, indent=1)


# ---------------------------------------------------------------- commands

def load_bodies(body_dir):
    return {t: Body.load(body_dir, t) for t in TIERS}


def is_bind_body(bodies, bd):
    return all(bodies[t].hash == bd.meta["bind_hash"][t] for t in TIERS)


def bindings(only=None):
    fs = sorted(f for f in os.listdir(BIND) if f.endswith(".npz"))
    out = [Binding(os.path.join(BIND, f)) for f in fs]
    return [b for b in out if not only or b.id in only]


def build(bodies, out_dir, only=None, bind_bodies=None, write=True):
    """Every binding evaluated on bodies; returns {id: eval}. bind_bodies is loaded when bodies is another body."""
    os.makedirs(out_dir, exist_ok=True)
    index, evs = [], {}
    bds = bindings(only)
    for bd in bds:
        same = is_bind_body(bodies, bd)
        if not same and bind_bodies is None:
            bind_bodies = load_bodies(os.path.join(REPO, bd.meta["bind_body"]))
        ev = eval_unit(bd, bodies, None if same else bind_bodies)
        evs[bd.id] = ev
        if not write:
            continue
        if same:
            fit, why = "ok", None
        else:
            ev["__metrics__"] = field_metrics(bd, ev, bodies, bind_bodies)
            fit, why = fit_verdict(ev["__metrics__"])
        fp = os.path.join(out_dir, f"{bd.id}.gltf")
        write_unit(fp, bd, ev, bodies["close"].glb)
        row = dict(bd.meta["row"])
        row.pop("tuck", None)
        row.pop("tuck_count", None)
        row["a_file"] = row.get("file") or bd.meta["src"]
        row["file"] = "res://" + rel(fp)[len("godot/"):]
        row["body_hash"] = bodies["close"].hash
        row["play_hash"] = bodies["play"].hash
        row["binding"] = f"godot/art/gear/bind/{bd.id}.npz"
        # refuse or flag (the owner, 20 Oct): a mesh missing the follow gates on this body flags the row
        row["fit"] = fit
        if why:
            row["fit_fail"] = why
        if bd.meta.get("sockets") and "__aux__" in ev:
            sp = os.path.join(out_dir, f"{bd.id}.sockets.json")
            write_sockets(sp, bd, ev, bodies["close"])
            row["sockets"] = "res://" + rel(sp)[len("godot/"):]
        if bd.meta["kind"] == "outfit":
            row["lod_file"] = "res://" + rel(os.path.join(out_dir, f"{row['outfit']}.lod.gltf"))[len("godot/"):]
        index.append(row)
    if write:
        # (her skin's tuck and each piece's cover, native on this body: tools/armor/gear_tuck.py)
        import gear_tuck
        gear_tuck.write_all(out_dir, bodies["close"].glb, bodies["play"].glb, index)
        ip = os.path.join(out_dir, "gear_index.json")
        if only and os.path.exists(ip):
            # (a build of some pieces keeps the folder's other rows as they stand, when they are this body's)
            old = json.load(open(ip))
            if old.get("body_hash") == bodies["close"].hash:
                new = {r["id"]: r for r in index}
                index = [new.pop(r["id"], r) for r in old.get("rows", [])] + list(new.values())
        with open(ip, "w") as f:
            json.dump({"body": bodies["close"].name, "body_hash": bodies["close"].hash, "rows": index}, f, indent=1)
    return evs


# ---------------------------------------------------------------- synthetic second body

def synthetic(bodies):
    """her_b's points displaced by a smooth field: +10% radial scale about the chest centre on the torso (B's spine,
    breast, pec and lat weights, so it fades out over the skin-weight blend toward the neck, arms and hips: ~10 cm),
    and +6% girth on the left thigh about the thigh bone's axis; head moves rigidly with the neck's share."""
    out = {}
    for t, b in bodies.items():
        names = b.joint_names
        V = b.V.copy()
        torso = [names.index(n) for n in names if n.startswith(("spine_", "breast", "pec_", "lat_"))]
        th = [names.index(n) for n in names if n.startswith("thigh") and n.endswith("_l")]
        Wd = np.bincount((np.arange(len(V))[:, None] * len(names) + b.J).reshape(-1), weights=b.W.reshape(-1),
                         minlength=len(V) * len(names)).reshape(len(V), len(names))
        wt = Wd[:, torso].sum(1)
        wl = Wd[:, th].sum(1)
        wt[b.nt:] = 0
        wl[b.nt:] = 0
        bt = b.V[:b.nt][(np.abs(b.V[:b.nt, 1] - 1.38) < 0.03)]
        c = bt.mean(0)
        V += 0.10 * wt[:, None] * (b.V - c) * np.array([1, 0, 1])
        leg = b.V[:b.nt][wl[:b.nt] > 0.9]
        ax_c = leg.mean(0)
        u, s, vt = np.linalg.svd(leg - ax_c)
        ax = vt[0]
        r = b.V - ax_c
        rad = r - (r @ ax)[:, None] * ax
        V += 0.06 * wl[:, None] * rad
        out[t] = b.with_points(V, "synthetic")
    return out


# ---------------------------------------------------------------- check

def check(body_dir, synth=False, only=None, out_dir=None):
    t0 = time.time()
    bodies = load_bodies(body_dir)
    bind_bodies = bodies
    if synth:
        bodies = synthetic(bind_bodies)
    tb = time.time()
    evs = build(bodies, out_dir or os.path.join(OUT, "_check"), only, bind_bodies=bind_bodies, write=not synth)
    secs = time.time() - tb
    res = {"body": bodies["close"].name, "build_secs": round(secs, 1), "rows": {}}
    pc = lambda x: [round(float(v), 3) for v in np.percentile(x, [50, 95, 99, 100])] if len(x) else []  # noqa: E731
    for bd in bindings(only):
        ev = evs[bd.id]
        r = {}
        for m in bd.meta["meshes"]:
            e = ev[m["node"]]
            body = bodies[m["tier"]]
            X = e["Xu"]
            rr = {"tier": m["tier"], "rigid": m["rigid"], "nan": int(np.isnan(X).sum() + np.isnan(e["N"]).sum())}
            ref = os.path.join(OUT, "_bindref", f"{bd.id}.{m['i']}.npy")
            if not synth and os.path.exists(ref):
                rr["identity_mm"] = round(float(np.abs(X - np.load(ref)).max() * 1000), 5)
            E = bd_edges(bd, m["i"])
            l0 = np.linalg.norm(e["Xbind"][E[:, 0]] - e["Xbind"][E[:, 1]], axis=1)
            l1 = np.linalg.norm(X[E[:, 0]] - X[E[:, 1]], axis=1)
            ok = l0 > 1e-6
            st = l1[ok] / l0[ok] - 1
            rr["stretch_pct_p50_95_99_max"] = pc(np.abs(st) * 100)
            rr["edges_over_3x"] = int((l1[ok] > 3 * l0[ok]).sum())
            # expected stretch: the body's own areal stretch at the bound triangles (the tight layers follow it)
            if synth:
                tri = bd.z[f"tri{m['i']}"].astype(np.int64)
                bb = bind_bodies[m["tier"]]
                a0 = tri_area(bb.V, bb.T[tri])
                a1 = tri_area(body.V, body.T[tri])
                sv = np.sqrt(a1 / np.maximum(a0, 1e-14))
                exp = 0.5 * (sv[E[:, 0]] + sv[E[:, 1]])[ok]
                rr["excess_stretch_pct_p50_95_99_max"] = pc(np.abs((1 + st) / exp - 1) * 100)
                cB, _ = signed_clear(body, X)
                cB0, _ = signed_clear(bb, e["Xbind"])
                clear0 = cB0 > -1e-6
                rr["inside_over_1mm_where_clear"] = int(((cB < -0.001) & clear0).sum())
                rr["inside_any"] = int((cB < -1e-6).sum())
            rg = e["comp"] >= 0
            if rg.any():
                worst = 0.0
                for c in np.unique(e["comp"][rg]):
                    sel = np.where(e["comp"] == c)[0]
                    if len(sel) > 400:
                        sel = sel[np.linspace(0, len(sel) - 1, 400).astype(int)]
                    d0 = np.linalg.norm(e["Xbind"][sel][:, None] - e["Xbind"][sel][None], axis=2)
                    d1 = np.linalg.norm(X[sel][:, None] - X[sel][None], axis=2)
                    worst = max(worst, float(np.abs(d1 - d0).max()))
                rr["rigid_dist_err_mm"] = round(worst * 1000, 5)
            r[m["node"]] = rr
        res["rows"][bd.id] = r
    res["total_secs"] = round(time.time() - t0, 1)
    return res


GATE = {"stretch_p99": 8.0, "stretch_max": 25.0, "over": 2.0, "inside_mm": 0.5, "tight_p95_mm": 0.5, "edge_min_mm": 1.5}


def field_metrics(bd, ev, bodies, bind_bodies):
    """The follow acceptance for one unit on one body (not the bind body): per mesh, NaNs; bendy edges of 1.5 mm and
    more (bevels apart, reported only): stretch beyond the body's own (gear_field.expected_edges: what a skin-tight edge
    would do there) p99 / max %, raw edges over 2x; vertices inside the new skin by over 0.5 mm among those clear on
    her_b (bendy and rigid); the tight vertices' (within 4 mm on her_b) clearance change p95 mm; each rigid component's
    made-to-measure scales (reported, not gated). "fail" lists the gates missed, "why" their numbers."""
    r = {}
    fit = ev.get("__fit__", {})
    for m in bd.meta["meshes"]:
        e = ev[m["node"]]
        body, bb = bodies[m["tier"]], bind_bodies[m["tier"]]
        X, X0, comp = e["Xu"], e["Xbind"], e["comp"]
        rr = {"nan": int(np.isnan(X).sum() + np.isnan(e["N"]).sum())}
        fail, why = [], {}
        if rr["nan"]:
            fail.append("nan")
            why["nan"] = rr["nan"]
        E = bd_edges(bd, m["i"])
        E = E[(comp[E[:, 0]] < 0) & (comp[E[:, 1]] < 0)]
        l0 = np.linalg.norm(X0[E[:, 0]] - X0[E[:, 1]], axis=1)
        ok = l0 > 1e-6
        E, l0 = E[ok], l0[ok]
        if len(E):
            l1 = np.linalg.norm(X[E[:, 0]] - X[E[:, 1]], axis=1)
            le = gear_field.expected_edges(bb, body, bd.z[f"tri{m['i']}"].astype(np.int64), E, X0, e.get("beta"),
                                           e.get(gear_field.FIELD["expect"]))
            ex = np.abs(l1 / np.maximum(le, 1e-9) - 1) * 100
            raw = np.abs(l1 / l0 - 1) * 100
            lg = l0 >= GATE["edge_min_mm"] / 1000
            rr["edges"] = [int(lg.sum()), int((~lg).sum())]
            if lg.any():
                rr["stretch_p99_max"] = [round(float(np.percentile(ex[lg], 99)), 2), round(float(ex[lg].max()), 2)]
                rr["raw_p99_max"] = [round(float(np.percentile(raw[lg], 99)), 2), round(float(raw[lg].max()), 2)]
                rr["over_2x"] = int((l1[lg] > GATE["over"] * l0[lg]).sum())
                if rr["stretch_p99_max"][0] > GATE["stretch_p99"] or rr["stretch_p99_max"][1] > GATE["stretch_max"] or rr["over_2x"]:
                    fail.append("stretch")
                    why["stretch_p99_max"], why["over_2x"] = rr["stretch_p99_max"], rr["over_2x"]
            if (~lg).any():
                bv = ~lg
                rr["bevel_p99_max"] = [round(float(np.percentile(ex[bv], 99)), 2), round(float(ex[bv].max()), 2)]
                rr["bevel_over_2x"] = int((l1[bv] > GATE["over"] * l0[bv]).sum())
        cB, _ = signed_clear(body, X)
        cB0, _ = signed_clear(bb, X0)
        clear0 = cB0 > -1e-6
        rr["inside"] = int(((cB < -GATE["inside_mm"] / 1000) & clear0).sum())
        rr["inside_mm_max"] = round(float(max(0.0, -cB[clear0].min() if clear0.any() else 0.0)) * 1000, 2)
        rr["bind_inside"] = int((~clear0).sum())
        if rr["inside"]:
            fail.append("inside")
            why["inside"], why["inside_mm_max"] = rr["inside"], rr["inside_mm_max"]
        tight = (np.abs(cB0) < 0.004) & (comp < 0)
        if tight.any():
            rr["tight_p95_mm"] = round(float(np.percentile(np.abs(cB - cB0)[tight], 95)) * 1000, 3)
            if rr["tight_p95_mm"] > GATE["tight_p95_mm"]:
                fail.append("tight")
                why["tight_p95_mm"] = rr["tight_p95_mm"]
        rg = comp >= 0
        if rg.any():
            lead = bd.z[f"lead_{m['tier']}"]
            rr["rigid_scale"] = {str(int(c)): fit.get("rigid", {}).get(f"{m['tier']}/{int(c)}", {}).get("scale")
                                 for c in np.unique(lead[comp[rg]])}
        rr["fail"] = fail
        if fail:
            rr["why"] = why
        r[m["node"]] = rr
    return r


def fit_verdict(metrics):
    """A row's "fit" on a body: "ok", or ("flagged", {node: the failing numbers})."""
    bad = {node: rr["why"] for node, rr in metrics.items() if rr["fail"]}
    return ("flagged", bad) if bad else ("ok", None)


def check_field(body_dir, only=None, tests=None, json_path=None):
    """The follow field's acceptance on the test bodies: the synthetic one and her_b with one slider at a strong setting
    (gear_field.SLIDER_TESTS); her_b itself for the identity (built == bind geometry)."""
    bind_bodies = load_bodies(body_dir)
    res = {"bodies": {}}
    t0 = time.time()
    ident = {}
    for bd in bindings(only):
        ev = eval_unit(bd, bind_bodies, None)
        for m in bd.meta["meshes"]:
            Xb, _ = eval_points(bind_bodies[m["tier"]], bd.z[f"tri{m['i']}"], bd.z[f"bw{m['i']}"], bd.z[f"off{m['i']}"])
            ident[f"{bd.id}/{m['node']}"] = float(np.abs(ev[m["node"]]["Xu"] - Xb).max() * 1000)
    res["her_b_identity_mm_max"] = round(max(ident.values()), 6)
    res["her_b_build_secs"] = round(time.time() - t0, 1)
    makers = [("synthetic", lambda: synthetic(bind_bodies))]
    makers += [(f"{n}{v:+g}", (lambda n=n, v=v: gear_field.slider_body(bind_bodies, n, v))) for n, v in gear_field.SLIDER_TESTS]
    for name, mk in makers:
        if tests and name not in tests:
            continue
        bodies = mk()
        gear_field._CACHE.clear()
        tb = time.time()
        evs = build(bodies, os.path.join(OUT, "_check"), only, bind_bodies=bind_bodies, write=False)
        secs = time.time() - tb
        rows = {bd.id: field_metrics(bd, evs[bd.id], bodies, bind_bodies) for bd in bindings(only)}
        res["bodies"][name] = {"build_secs": round(secs, 1), "rows": rows}
        nf = sum(bool(rr["fail"]) for r in rows.values() for rr in r.values())
        print(f"[{name}] build {secs:.1f} s, meshes failing: {nf}", flush=True)
        if json_path:
            with open(json_path, "w") as f:
                json.dump(res, f, indent=1)
    return res


def check_body(body_dir, only=None, out_dir=None):
    """The follow acceptance on a real body built on the base (not the bind body): builds it (gear_index.json "fit" per
    row) and returns the per-mesh numbers in check_field's shape, with the build time."""
    bodies = load_bodies(body_dir)
    bds = bindings(only)
    if bds and is_bind_body(bodies, bds[0]):
        raise SystemExit("gear_fit check: that is the bind body (use check without --field for the identity)")
    bind_bodies = load_bodies(os.path.join(REPO, bds[0].meta["bind_body"]))
    gear_field._CACHE.clear()
    out_dir = out_dir or os.path.join(OUT, bodies["close"].name)
    tb = time.time()
    evs = build(bodies, out_dir, only, bind_bodies=bind_bodies)
    secs = time.time() - tb
    rows = {bd.id: evs[bd.id]["__metrics__"] for bd in bds}
    flagged = {bd.id: fit_verdict(rows[bd.id])[1] for bd in bds if fit_verdict(rows[bd.id])[0] != "ok"}
    return {"bodies": {bodies["close"].name: {"build_secs": round(secs, 1), "rows": rows, "flagged": flagged,
                                               "out": rel(out_dir)}}}


def tri_area(V, Tv):
    return 0.5 * np.linalg.norm(np.cross(V[Tv[:, 1]] - V[Tv[:, 0]], V[Tv[:, 2]] - V[Tv[:, 0]]), axis=1)


def signed_clear(body, X):
    return gear_field.signed_clear(body, X, k=16)


def ncomp(E, n):
    return connected_components(adjacency(E, n), directed=False)[0] if len(E) else n


def stale_units(bodies=None, bind_dir=None, unit_list=None):
    """[(unit id, reason)] for every unit `bind` would make whose npz is missing or out of date; plus orphan npz ids."""
    bind_dir = bind_dir or BIND
    unit_list = units() if unit_list is None else unit_list
    if bodies is None:
        bodies = {t: Body.load(BIND_BODY, t) for t in TIERS}
    out, ids = [], set()
    for u in unit_list:
        ids.add(u["id"])
        p = os.path.join(bind_dir, f"{u['id']}.npz")
        if not os.path.exists(p):
            out.append((u["id"], "missing"))
            continue
        try:
            meta = json.loads(bytes(np.load(p)["meta"]).decode())
        except Exception as e:  # noqa: BLE001
            out.append((u["id"], f"unreadable ({e})"))
            continue
        if meta.get("bind_version") != BIND_VERSION:
            out.append((u["id"], f"bind_version {meta.get('bind_version')} != {BIND_VERSION}"))
        elif meta.get("src_sha1") != sha1(os.path.join(REPO, u["src"])):
            out.append((u["id"], "source changed"))
        elif any(meta.get("bind_hash", {}).get(t) != bodies[t].hash for t in TIERS):
            out.append((u["id"], "bind body changed"))
    orphans = sorted(f[:-4] for f in os.listdir(bind_dir) if f.endswith(".npz") and f[:-4] not in ids) if os.path.isdir(bind_dir) else []
    return out, orphans


def bind_units(only=None):
    car = Carrier()
    bodies = {t: Body.load(BIND_BODY, t) for t in TIERS}
    reps = {}
    for u in units():
        if only and u["id"] not in only:
            continue
        reps[u["id"]] = r = bind_unit(u, car, bodies)
        print(u["id"], r["secs"], "s")
        for k, v in r["meshes"].items():
            print("   ", k, v)
    os.makedirs(OUT, exist_ok=True)
    rp = os.path.join(OUT, "_bindref", "bind_report.json")
    old = json.load(open(rp)) if os.path.exists(rp) else {}
    old.update(reps)
    os.makedirs(os.path.dirname(rp), exist_ok=True)
    with open(rp, "w") as f:
        json.dump(old, f, indent=1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bind")
    b.add_argument("--only", default="")
    st = sub.add_parser("stale")
    st.add_argument("--json", default="")
    for name in ("build", "check"):
        p = sub.add_parser(name)
        p.add_argument("--body", default=rel(BIND_BODY))
        p.add_argument("--out", default="")
        p.add_argument("--only", default="")
        p.add_argument("--synthetic", action="store_true")
        p.add_argument("--field", default="", help="check: the follow field's test bodies (all, or names: synthetic,weight+1,...)")
        p.add_argument("--json", default="", help="check: the report's file (build writes none: its numbers are the "
                       "folder's gear_index.json)")
        if name == "build":
            p.add_argument("--no-bind", action="store_true", help="skip the stale check and rebind")
    a = ap.parse_args()
    only = [x for x in getattr(a, "only", "").split(",") if x]
    if a.cmd == "bind":
        bind_units(only)
        return
    if a.cmd == "stale":
        bad, orphans = stale_units()
        for uid, why in bad:
            print(f"STALE {uid}: {why}")
        for o in orphans:
            print(f"warning: orphan binding {o}.npz (no unit makes it)")
        print(f"gear_fit stale: {len(bad)} stale of {len(units())} units, {len(orphans)} orphans")
        if a.json:
            with open(a.json, "w") as f:
                json.dump({"stale": dict(bad), "orphans": orphans}, f, indent=1)
        sys.exit(1 if bad else 0)
    body_dir = os.path.join(REPO, a.body) if not os.path.isabs(a.body) else a.body
    if a.cmd == "build":
        t0 = time.time()
        if not a.no_bind:
            bad = [uid for uid, _ in stale_units()[0] if not only or uid in only]
            if bad:
                print(f"gear_fit build: rebinding {len(bad)} stale units: {', '.join(bad)}")
                bind_units(bad)
            else:
                print("gear_fit build: bindings current, rebound nothing")
        bodies = load_bodies(body_dir)
        name = bodies["close"].name
        out_dir = a.out or os.path.join(OUT, name)
        build(bodies, out_dir, only)
        if a.json:
            print("gear_fit build: --json is check's; a build writes gear_index.json in its folder, nothing else")
        print(f"gear_fit build: {len(bindings(only))} units on {name} -> {rel(out_dir)} in {time.time() - t0:.1f} s")
        return
    if a.field:
        res = check_field(body_dir, only, None if a.field == "all" else a.field.split(","), a.json or None)
        if a.json:
            with open(a.json, "w") as f:
                json.dump(res, f, indent=1)
        print(json.dumps({k: v for k, v in res.items() if k != "bodies"}))
        for name, bo in res["bodies"].items():
            for rid, r in bo["rows"].items():
                for node, rr in r.items():
                    if rr["fail"]:
                        print(f"{name:12s} {rid:24s} {node:40s} " + " ".join(f"{k}={v}" for k, v in rr.items()))
        return
    if not a.synthetic and Body.load(body_dir, "close").hash != bindings(only)[0].meta["bind_hash"]["close"]:
        res = check_body(body_dir, only, a.out or None)
        if a.json:
            with open(a.json, "w") as f:
                json.dump(res, f, indent=1)
        for name, bo in res["bodies"].items():
            n = sum(len(r) for r in bo["rows"].values())
            nf = sum(bool(rr["fail"]) for r in bo["rows"].values() for rr in r.values())
            print(f"[{name}] build {bo['build_secs']} s, meshes {n}, failing {nf}, rows flagged {len(bo['flagged'])}")
            for rid, why in bo["flagged"].items():
                print(f"  FLAGGED {rid}: {json.dumps(why)}")
        return
    res = check(body_dir, a.synthetic, only, a.out or None)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}))
    for rid, r in res["rows"].items():
        for node, rr in r.items():
            print(f"{rid:24s} {node:44s} " + " ".join(f"{k}={v}" for k, v in rr.items() if k not in ("tier",)))


# (base-native pieces, authored on her_b: tools/armor/gear_native.py joins units, bind, stale and build here)
import gear_native  # noqa: E402
gear_native.install(sys.modules[__name__])

if __name__ == "__main__":
    main()
