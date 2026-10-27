"""Her gameplay LOD: each outfit's pieces, her body under it and her shadow, cut for the play camera (the owner,
11 October 2026: "all those ideas seem worthwhile!", "we worked very hard on these models so they show there no
matter what").

At the play camera (22 to 34 m, about 150 px tall) a millimetre is a tenth of a pixel, and her ~1M triangles land in
about 9,000 px. For each outfit this writes heroine_outfit_SET_lod.gltf beside heroine_outfit_SET.gltf:

  - lod_MAT: each of the outfit's meshes with what no ray can reach removed (inner armour layers, linings under
    plates; kept within KEEP of anything seen, and wherever its weights blend over a joint, which opens in motion),
    then simplified to an error of FLAT (DENSE over her bust, hips and butt), keeping every vertex where it was (no
    vertex moved, so its normal, paint and weights are the full mesh's own), its open edges locked;
  - lod_body: her body with what the outfit hides removed in the same way (never her head, which keeps its keys);
  - lod_shadow: the body and outfit welded into one surface for her shadow, simplified to SHADOW and drawn in by INSET
    along its normals so it never rises over the surface it shades.

The game draws them only in play, beyond 17 m (People.HerLod): at the title, in creation, in conversations, at chests
and in every cinematic she is the full model.

    python tools/assets/heroine_lod.py godot/art/people [SET ...]

Run after every outfit export (heroine_outfits.py), and after heroine.glb is written (its body is cut per outfit).
Needs numpy, scipy, meshoptimizer and embreex (pip).
"""
import json
import os
import struct
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

import ctypes
import meshoptimizer as mo
from meshoptimizer._loader import lib as _mo
import embreex.rtcore_scene as rtcs
from embreex.mesh_construction import TriangleMesh

FLAT = 0.0010        # (m: simplification error over most of her; a pixel is 5-10 mm at the play camera)
DENSE = 0.0005       # (m: over her bust, hips and butt, which make her silhouette)
SHADOW = 0.0025      # (m: her shadow's mesh)
INSET = 0.0015       # (m: her shadow's mesh drawn in along its normals)
KEEP = 0.05          # (m: what lies within this of anything seen, along its own surface, is kept: openings widen in motion)
# (a vertex with another of her surfaces near along its normal (a garment over skin, one garment over another, a strand
# of hair on her) is simplified within a third of that gap, so neither passes through the other: gaps under these, these
# errors)
CLOSE = ((0.0015, 0.0001), (0.003, 0.0005), (0.005, 0.001))
HEADWEAR = 0.3       # (her outfit's pieces weighted this much to her head (a hat, a hood) are kept whole, as her head is)
BLEND = 0.80         # (a vertex whose largest weight is under this blends over a joint: never removed)
RAYS = 64            # (directions tried from each point of a triangle)
NORMALS = 0.06       # (m per unit of a normal's turn: a normal off by 1 degree costs as 1 mm of shape, so broad curves keep their shading)
NO_SHADOW = {"stocking"}   # (sheer: drawn blended, it casts none)
TUCK = 0.010         # (m: heroine_skin.gdshader's tuck, her skin drawn in by a whole unit of its colour)
SHEER = {"stocking"}       # (seen through: hides nothing under it)
HAIR_NEAR = 0.04     # (m: her skin and outfit this near any hair she can wear, at rest, are held as the closest layers: a
                     # strand lying on her is drawn where it passes over or under her surface, to the tenth of a millimetre)
DECALS = {"ink"}     # (painted onto her skin, lying on it: kept as built, and her skin under it, so they meet as in her full model)
DECAL_NEAR = 0.02    # (m: her skin this near a decal's points is kept as built: wider than her skin's triangles, so none under it changes)
DENSE_BONES = ("breast_l", "breast_r", "glute_l", "glute_r", "pelvis")

_CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
_TYPE = {1: "SCALAR", 2: "VEC2", 3: "VEC3", 4: "VEC4", 16: "MAT4"}
_CODE = {np.dtype(v): k for k, v in _CT.items()}


class Gltf:
    """A .gltf (its .bin beside it) or a .glb, its accessors read as numpy arrays."""

    def __init__(self, path):
        self.path = path
        if path.endswith(".glb"):
            b = open(path, "rb").read()
            off, self.js, self.bin = 12, None, b""
            while off < len(b):
                ln, ty = struct.unpack_from("<II", b, off)
                if ty == 0x4E4F534A:
                    self.js = json.loads(b[off + 8:off + 8 + ln])
                elif ty == 0x004E4942:
                    self.bin = b[off + 8:off + 8 + ln]
                off += 8 + ln
        else:
            self.js = json.load(open(path, encoding="utf-8"))
            self.bin = open(os.path.join(os.path.dirname(path), self.js["buffers"][0]["uri"]), "rb").read()

    def acc(self, i):
        """An accessor as an array (n, components), its own type; and whether it is normalized."""
        a = self.js["accessors"][i]
        bv = self.js["bufferViews"][a["bufferView"]]
        dt = np.dtype(_CT[a["componentType"]])
        nc = _NC[a["type"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride", nc * dt.itemsize)
        n = a["count"]
        raw = np.frombuffer(self.bin, np.uint8, count=(n - 1) * stride + nc * dt.itemsize, offset=off)
        if stride == nc * dt.itemsize:
            out = raw.view(dt).reshape(n, nc)
        else:
            out = np.lib.stride_tricks.as_strided(raw.view(dt), shape=(n, nc), strides=(stride, dt.itemsize))
        return np.array(out), a.get("normalized", False)

    def prims(self, mesh_index):
        """Each primitive of a mesh: (material name, {attribute: (array, normalized)}, triangles (t, 3))."""
        out = []
        for p in self.js["meshes"][mesh_index]["primitives"]:
            attrs = {k: self.acc(v) for k, v in p["attributes"].items()}
            tris = self.acc(p["indices"])[0].reshape(-1, 3).astype(np.int64)
            mat = self.js["materials"][p["material"]]["name"] if "material" in p else "none"
            out.append((mat, attrs, tris))
        return out

    def joint_names(self, skin=0):
        return [self.js["nodes"][j]["name"] for j in self.js["skins"][skin]["joints"]]


def bind_positions(g, skin=0):
    """Her joints' places in the space her meshes are bound in (the inverses of their inverse bind matrices)."""
    ibm = g.acc(g.js["skins"][skin]["inverseBindMatrices"])[0].reshape(-1, 4, 4)
    # (glTF matrices are column-major: the translation is the last row as read)
    return {n: np.linalg.inv(m.T)[:3, 3] for n, m in zip(g.joint_names(skin), ibm)}


def weights_of(attrs, names):
    """Per vertex, its largest weight and its weight on each named joint, from JOINTS_0 and WEIGHTS_0."""
    j = attrs["JOINTS_0"][0].astype(np.int64)
    w, norm = attrs["WEIGHTS_0"]
    w = w.astype(np.float64)
    if norm and w.dtype != np.float64:
        w = w / {np.dtype(np.uint8): 255.0, np.dtype(np.uint16): 65535.0}.get(attrs["WEIGHTS_0"][0].dtype, 1.0)
    w = w / np.maximum(w.sum(1, keepdims=True), 1e-9)
    return w.max(1), {k: (w * (j == idx)).sum(1) for k, idx in names.items()}


# (meshoptimizer's own Python wrapper declares no argument types, so its float error cannot be passed: declared here)
_P = ctypes.c_void_p
_S = ctypes.c_size_t
_mo.meshopt_simplify.restype = _S
_mo.meshopt_simplify.argtypes = [_P, _P, _S, _P, _S, _S, _S, ctypes.c_float, ctypes.c_uint, _P]
_mo.meshopt_simplifyWithAttributes.restype = _S
_mo.meshopt_simplifyWithAttributes.argtypes = [_P, _P, _S, _P, _S, _S, _P, _S, _P, _S, _P, _S, ctypes.c_float, ctypes.c_uint, _P]


def mo_simplify(idx, pos, error, options, attrs=None, weights=None, lock=None):
    """Indices kept (a subset of the vertices, none moved) within error; and the error reached."""
    idx = np.ascontiguousarray(idx, np.uint32)
    pos = np.ascontiguousarray(pos, np.float32)
    dst = np.zeros(len(idx), np.uint32)
    err = ctypes.c_float(0)
    if attrs is None:
        n = _mo.meshopt_simplify(dst.ctypes.data, idx.ctypes.data, len(idx), pos.ctypes.data, len(pos), 12, 0, error, options,
                                 ctypes.addressof(err))
    else:
        attrs = np.ascontiguousarray(attrs, np.float32)
        weights = np.ascontiguousarray(weights, np.float32)
        lk = np.ascontiguousarray(lock, np.uint8) if lock is not None else None
        n = _mo.meshopt_simplifyWithAttributes(dst.ctypes.data, idx.ctypes.data, len(idx), pos.ctypes.data, len(pos), 12,
                                               attrs.ctypes.data, attrs.shape[1] * 4, weights.ctypes.data, len(weights),
                                               lk.ctypes.data if lk is not None else None, 0, error, options, ctypes.addressof(err))
    return dst[:n].copy(), err.value


def fib_dirs(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1).astype(np.float32)


def seen(scene, pos, tris, rays=RAYS, seed=1):
    """Which triangles some ray from them reaches open air by: from their middles and near each corner, in RAYS
    directions (turned a little for each triangle, so no direction is missed by all)."""
    rng = np.random.default_rng(seed)
    base = fib_dirs(rays)
    rots = []
    for _ in range(16):
        q, _r = np.linalg.qr(rng.normal(size=(3, 3)))
        rots.append(q.astype(np.float32))
    rots = np.stack(rots)
    v = pos[tris].astype(np.float32)                     # (t, 3, 3)
    mid = v.mean(1)
    points = [mid] + [v[:, k] * 0.75 + mid * 0.25 for k in range(3)]
    out = np.zeros(len(tris), bool)
    for pts in points:
        todo = np.nonzero(~out)[0]
        for chunk in np.array_split(todo, max(1, len(todo) // 20000)):
            if not len(chunk):
                continue
            dirs = np.einsum("tij,kj->tki", rots[chunk % 16], base).reshape(-1, 3)
            org = np.repeat(pts[chunk], rays, 0) + dirs * 2e-4
            hit = scene.run(org.astype(np.float32), dirs.astype(np.float32))
            out[chunk] = (hit.reshape(len(chunk), rays) < 0).any(1)
    return out


def grow(pos, tris, keep, radius):
    """Keep also what lies within radius of a kept triangle, along the mesh's own surface (its vertices welded where
    they share a place, across its seams)."""
    if keep.all() or not keep.any():
        return keep
    _, weld = np.unique(np.round(pos / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    weld = weld.ravel()
    t = weld[tris]
    e = np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]])
    ln = np.linalg.norm(pos[tris[:, [0, 1, 2]]] - pos[tris[:, [1, 2, 0]]], axis=2).T.ravel()
    n = weld.max() + 1
    g = coo_matrix((np.concatenate([ln, ln]) + 1e-9, (np.concatenate([e[:, 0], e[:, 1]]), np.concatenate([e[:, 1], e[:, 0]]))), shape=(n, n)).tocsr()
    seeds = np.unique(t[keep])
    # (one source joined to every seed, so one search finds the nearest)
    src = n
    g2 = coo_matrix((np.concatenate([g.tocoo().data, np.full(len(seeds), 1e-9)]),
                     (np.concatenate([g.tocoo().row, np.full(len(seeds), src)]), np.concatenate([g.tocoo().col, seeds]))),
                    shape=(n + 1, n + 1)).tocsr()
    d = dijkstra(g2, directed=True, indices=src, limit=radius)
    near = np.isfinite(d[:n])
    return keep | near[t].any(1)


def simplify(pos, attrs, tris, dense, gap, whole, error_flat, error_dense, colour_weight=0.004):
    """Her mesh simplified with every vertex left where it was: first over her dense parts (the rest locked), then the
    rest (the dense locked), its open edges locked."""
    # (attribute weights in metres per unit: NORMALS; a UV moved 0.05 costs as 0.5 mm)
    cols = [attrs["NORMAL"][0].astype(np.float32)]
    w = [NORMALS] * 3
    for k in ("TEXCOORD_0", "TEXCOORD_1"):
        if k in attrs:
            cols.append(attrs[k][0].astype(np.float32))
            w += [0.01, 0.01]
    if "COLOR_0" in attrs:
        c, norm = attrs["COLOR_0"]
        c = c.astype(np.float32) / ({np.dtype(np.uint8): 255.0, np.dtype(np.uint16): 65535.0}.get(c.dtype, 1.0) if norm else 1.0)
        cols.append(c)
        w += [colour_weight] * c.shape[1]
    at = np.ascontiguousarray(np.concatenate(cols, 1), np.float32)
    wt = np.array(w, np.float32)
    idx = np.ascontiguousarray(tris.ravel(), np.uint32)
    p = np.ascontiguousarray(pos, np.float32)
    opts = mo.SIMPLIFY_LOCK_BORDER | mo.SIMPLIFY_ERROR_ABSOLUTE
    # (the closest layers first, each band with all else locked, then the dense parts, then the rest; what is whole, never)
    lo = 0.0
    passes = []
    for g, err in CLOSE:
        passes.append((err, ~((gap >= lo) & (gap < g)) | whole))
        lo = g
    close = gap < lo
    passes += [(error_dense, ~dense | close | whole), (error_flat, dense | close | whole)]
    for err, lock in passes:
        idx, _e = mo_simplify(idx, p, err, opts, at, wt, lock)
    return idx.reshape(-1, 3).astype(np.int64)


class Writer:
    """A new glTF: the outfit file's skeleton, skin and materials, and new meshes."""

    def __init__(self, src):
        self.js = {k: v for k, v in src.js.items() if k not in ("meshes", "accessors", "bufferViews", "buffers")}
        self.js["nodes"] = [n for n in src.js["nodes"]]
        self.bin = bytearray()
        self.js["accessors"], self.js["bufferViews"], self.js["meshes"] = [], [], []
        skin = dict(src.js["skins"][0])
        ibm, _ = src.acc(skin["inverseBindMatrices"])
        skin["inverseBindMatrices"] = self.add(ibm.astype(np.float32), False)
        self.js["skins"] = [skin]
        # (the old mesh nodes dropped: the armature keeps only its bones)
        self.mesh_nodes = [i for i, n in enumerate(self.js["nodes"]) if "mesh" in n]
        self.arm = next(i for i, n in enumerate(self.js["nodes"]) if n.get("name") == "Armature")
        self.js["nodes"][self.arm] = dict(self.js["nodes"][self.arm])
        self.js["nodes"][self.arm]["children"] = [c for c in self.js["nodes"][self.arm]["children"] if c not in self.mesh_nodes]

    def add(self, arr, normalized, target=None):
        arr = np.ascontiguousarray(arr)
        while len(self.bin) % 4:
            self.bin.append(0)
        bv = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": arr.nbytes}
        if target:
            bv["target"] = target
        self.bin += arr.tobytes()
        self.js["bufferViews"].append(bv)
        a = {"bufferView": len(self.js["bufferViews"]) - 1, "componentType": _CODE[arr.dtype], "count": len(arr),
             "type": _TYPE[1 if arr.ndim == 1 else arr.shape[1] if arr.shape[1] != 16 else 16]}
        if normalized:
            a["normalized"] = True
        if arr.ndim == 2 and arr.shape[1] == 3 and arr.dtype == np.float32:
            a["min"], a["max"] = arr.min(0).tolist(), arr.max(0).tolist()
        self.js["accessors"].append(a)
        return len(self.js["accessors"]) - 1

    def material(self, name, like=None):
        for i, m in enumerate(self.js["materials"]):
            if m["name"] == name:
                return i
        self.js["materials"].append(dict(like) if like else {"name": name, "doubleSided": False})
        self.js["materials"][-1]["name"] = name
        return len(self.js["materials"]) - 1

    def mesh(self, name, prims):
        """prims: [(material index, {attribute: (array, normalized)}, triangles)]; a skinned node under the armature."""
        out = []
        for mat, attrs, tris in prims:
            used, inv = np.unique(tris.ravel(), return_inverse=True)
            p = {"attributes": {}, "material": mat}
            for k, (arr, norm) in attrs.items():
                p["attributes"][k] = self.add(arr[used], norm, 34962)
            ind = inv.astype(np.uint32 if len(used) > 65535 else np.uint16)
            p["indices"] = self.add(ind, False, 34963)
            out.append(p)
        self.js["meshes"].append({"name": name, "primitives": out})
        self.js["nodes"].append({"name": name, "mesh": len(self.js["meshes"]) - 1, "skin": 0})
        self.js["nodes"][self.arm]["children"].append(len(self.js["nodes"]) - 1)

    def save(self, path):
        # (the old mesh nodes left in place, meshless and unparented, would be empty nodes: emptied and renamed)
        for i in self.mesh_nodes:
            self.js["nodes"][i] = {"name": f"unused_{i}"}
        self.js["buffers"] = [{"byteLength": len(self.bin), "uri": os.path.basename(path)[:-5] + ".bin"}]
        open(path[:-5] + ".bin", "wb").write(self.bin)
        json.dump(self.js, open(path, "w", encoding="utf-8"), indent=1)


def slot_join(items, tag=""):
    """One material's meshes of an outfit, one a slot ((glTF extras, attributes, triangles) each), joined back into the
    one mesh a material was before slots (heroine_outfits.py, armor lead 1): each slot mesh's pieces (extras "pieces":
    [their place in the material's join, their triangles]) cut out, each piece's own run of vertices, and laid back
    in the join's order. Without "pieces", the meshes end to end in their "rank"."""
    # gltf_compact drops an all-zero second weight set per mesh: a slot without it joins with zeros (Body 15)
    for k1 in ("JOINTS_1", "WEIGHTS_1"):
        have = [a for _, a, _ in items if k1 in a]
        if have:
            for _, a, _ in items:
                if k1 not in a:
                    ref = have[0][k1]
                    a[k1] = (np.zeros((len(a["POSITION"][0]),) + ref[0].shape[1:], ref[0].dtype), ref[1])
    keys = list(items[0][1])
    assert all(set(a) == set(keys) for _, a, _ in items), f"{tag}: its slots' meshes carry different attributes"
    for k in keys:
        assert len({a[k][0].dtype for _, a, _ in items}) == 1 and len({a[k][1] for _, a, _ in items}) == 1, f"{tag} {k}"
    chunks = []     # (place in the join, item, first vertex, end vertex, triangles)
    for n, (ex, a, t) in enumerate(items):
        pcs = ex.get("pieces") or [[ex.get("rank", 0) * 100000, len(t)]]
        assert sum(nt for _, nt in pcs) == len(t), f"{tag}: {ex.get('slot')}'s pieces have {sum(nt for _, nt in pcs)} triangles, its mesh {len(t)}"
        off, vend = 0, 0
        for j, nt in pcs:
            tt = t[off:off + nt]
            off += nt
            if not nt:
                continue
            v0, v1 = int(tt.min()), int(tt.max()) + 1
            assert v0 == vend, f"{tag}: a piece's vertices not in one run after the last ({v0} after {vend})"
            vend = v1
            chunks.append((j, n, v0, v1, tt))
        assert vend == len(a["POSITION"][0]), f"{tag}: {len(a['POSITION'][0]) - vend} vertices in no piece"
    chunks.sort(key=lambda c: c[0])
    attrs = {k: (np.concatenate([items[n][1][k][0][v0:v1] for _, n, v0, v1, _ in chunks]), items[0][1][k][1]) for k in keys}
    tris, base = [], 0
    for _, n, v0, v1, tt in chunks:
        tris.append(tt - v0 + base)
        base += v1 - v0
    return attrs, np.concatenate(tris)


def lod(folder, outfit):
    full = Gltf(os.path.join(folder, f"heroine_outfit_{outfit}.gltf"))
    body = Gltf(os.path.join(folder, "heroine.glb"))
    names = full.joint_names()
    assert names == body.joint_names(), "her outfit and her body bound to different joints"
    ibm_a = full.acc(full.js["skins"][0]["inverseBindMatrices"])[0]
    ibm_b = body.acc(body.js["skins"][0]["inverseBindMatrices"])[0]
    assert np.abs(ibm_a - ibm_b).max() < 1e-4, "her outfit and her body bound in different places"
    joints = bind_positions(full)
    
    # Every surface of her, as it stands in her bind pose.
    parts = []      # (kind, name, attrs, tris)
    # (the outfit's meshes are one a slot and material, SET.SLOT.MAT (heroine_outfits.py, armor lead 1): joined back
    # into one a material, the slots end to end in their join's rank (glTF extras), as one mesh a material was)
    by_mat = {}
    for mi, m in enumerate(full.js["meshes"]):
        for mat, attrs, tris in full.prims(mi):
            by_mat.setdefault(mat, []).append((m.get("extras", {}), attrs, tris))
    for mat in sorted(by_mat):
        attrs, tris = slot_join(by_mat[mat], f"{outfit} {mat}")
        parts.append(("outfit", mat, attrs, tris))
    for mi, m in enumerate(body.js["meshes"]):
        node = next(n for n in body.js["nodes"] if n.get("mesh") == mi)
        for mat, attrs, tris in body.prims(mi):
            kind = "body" if node["name"] == "Heroine" else "head"
            if mat in ("eyes", "lashes"):
                continue
            parts.append((kind, mat, attrs, tris))

    scene = rtcs.EmbreeScene()
    for kind, mat, attrs, tris in parts:
        if mat not in SHEER:
            TriangleMesh(scene, attrs["POSITION"][0].astype(np.float32)[tris])

    w = Writer(full)
    report = {}
    hip_y = (joints["thigh_l"][1] + joints["thigh_r"][1]) / 2
    head_i = {"Head": names.index("Head")}
    # What no ray reaches is removed, but never her headwear, nor where her weights blend over a joint.
    # A decal (ink on her skin) and her skin under it are kept as built: a decal lies a hair off her skin, and the least
    # change to either turns it solid where it was half sunk, or the other way round.
    from scipy.spatial import cKDTree
    decal_pts = [attrs["POSITION"][0].astype(np.float64) for kind, mat, attrs, tris in parts if kind == "outfit" and mat in DECALS]
    decal_tree = cKDTree(np.concatenate(decal_pts)) if decal_pts else None
    kept = []
    for kind, mat, attrs, tris in parts:
        if kind == "head":
            continue
        pos = attrs["POSITION"][0].astype(np.float64)
        big, on = weights_of(attrs, head_i)
        whole = on["Head"] > HEADWEAR if kind == "outfit" else np.zeros(len(pos), bool)
        if kind == "outfit" and mat in DECALS:
            whole[:] = True
        elif kind == "body" and decal_tree is not None:
            whole |= decal_tree.query(pos, distance_upper_bound=DECAL_NEAR)[0] < DECAL_NEAR
        vis = seen(scene, pos, tris)
        hold = vis | (big < BLEND)[tris].any(1) | whole[tris].any(1)
        keep = grow(pos, tris, hold, KEEP) if not (os.environ.get("LOD_KEEP_ALL") or os.environ.get("LOD_EXACT")) else np.ones(len(tris), bool)
        kept.append((kind, mat, attrs, tris, keep, whole, int(vis.sum())))
    # How near each vertex lies to another of her surfaces along its normal: what is kept of the others, her head, and
    # every hair she can wear (never its own surface: a garment's own thickness is no other layer).
    others = []
    hair_pts = []
    for kind, mat, attrs, tris in parts:
        if kind == "head":
            others.append(attrs["POSITION"][0].astype(np.float32)[tris])
    for f in sorted(os.listdir(folder)):
        if f.startswith("heroine_hair_") and f.endswith(".gltf"):
            hg = Gltf(os.path.join(folder, f))
            for mi in range(len(hg.js["meshes"])):
                for hm, ha, ht in hg.prims(mi):
                    others.append(ha["POSITION"][0].astype(np.float32)[ht])
                    hair_pts.append(ha["POSITION"][0].astype(np.float32))
    hair_tree = cKDTree(np.concatenate(hair_pts)) if hair_pts else None
    keep_parts = []
    for i, (kind, mat, attrs, tris, keep, whole, nv) in enumerate(kept):
        near = rtcs.EmbreeScene()
        for t in others:
            TriangleMesh(near, t)
        for j, (k2, m2, a2, t2_, kp2, _w, _n) in enumerate(kept):
            if j != i:
                TriangleMesh(near, a2["POSITION"][0].astype(np.float32)[t2_[kp2]])
        pos = attrs["POSITION"][0].astype(np.float64)
        nrm = attrs["NORMAL"][0].astype(np.float32)
        nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
        gap = np.full(len(pos), np.inf)
        for sgn in (1.0, -1.0):
            d = (nrm * sgn).astype(np.float32)
            hit = near.run(pos.astype(np.float32), d, output=1)
            gap = np.minimum(gap, np.where(hit["primID"] >= 0, hit["tfar"], np.inf))
        if hair_tree is not None:
            gap[hair_tree.query(pos, distance_upper_bound=HAIR_NEAR)[0] < HAIR_NEAR] = 0.0
        _, on = weights_of(attrs, {n: names.index(n) for n in DENSE_BONES + ("thigh_l", "thigh_r")})
        # (her dense parts: her bust, her hips and butt, the tops of her thighs)
        dense = (on["breast_l"] + on["breast_r"] + on["glute_l"] + on["glute_r"] + on["pelvis"] > 0.2) |                 ((on["thigh_l"] + on["thigh_r"] > 0.2) & (pos[:, 1] > hip_y - 0.22))
        t2 = tris[keep]
        # (her body's colours are how far each outfit tucks her skin in (heroine_skin.gdshader: up to TUCK): weighed
        # as the shape they make)
        t3 = simplify(pos, attrs, t2, dense, gap, whole, FLAT, DENSE, TUCK if kind == "body" else 0.004) if len(t2) and not os.environ.get("LOD_EXACT") and mat not in os.environ.get("LOD_EXACT_MATS", "").split(",") else t2
        used = np.unique(t2)
        report[f"{kind}.{mat}"] = (len(tris), nv, len(t2), len(t3))
        print(f"  {kind}.{mat}: {len(tris)} tris, {nv} seen, {len(t2)} kept, {len(t3)} after simplifying "
              f"(within 1.5/3/5 mm of another layer {(gap[used] < 1.5e-3).mean():.0%}/{(gap[used] < 3e-3).mean():.0%}/{(gap[used] < 5e-3).mean():.0%}, whole {whole[used].mean():.0%})", flush=True)
        keep_parts.append((kind, mat, attrs, t3))

    # The outfit's meshes (each its own material), her body (its two), her shadow (one).
    for kind, mat, attrs, t3 in keep_parts:
        if kind == "outfit" and len(t3):
            w.mesh(f"lod_{mat}", [(w.material(mat), attrs, t3)])
    bprims = [(w.material(mat), attrs, t3) for kind, mat, attrs, t3 in keep_parts if kind == "body" and len(t3)]
    if bprims:
        w.mesh("lod_body", bprims)

    # Her shadow: every kept triangle that casts one, welded across materials, simplified on its own.
    P, N, J, W, T = [], [], [], [], []
    base = 0
    wdt = None
    for kind, mat, attrs, t3 in keep_parts:
        if mat in NO_SHADOW or not len(t3):
            continue
        used, inv = np.unique(t3.ravel(), return_inverse=True)
        P.append(attrs["POSITION"][0][used].astype(np.float32))
        N.append(attrs["NORMAL"][0][used].astype(np.float32))
        J.append(attrs["JOINTS_0"][0][used].astype(np.uint16))
        ww, norm = attrs["WEIGHTS_0"]
        ww = ww[used].astype(np.float32) / ({np.dtype(np.uint8): 255.0, np.dtype(np.uint16): 65535.0}.get(ww.dtype, 1.0) if norm else 1.0)
        # (her body carries 8 weights since Body 6 S2b: the shadow keeps the largest 4 (JOINTS_0), made whole again)
        ww = ww / np.maximum(ww.sum(1, keepdims=True), 1e-9)
        W.append(ww)
        T.append(inv.reshape(-1, 3) + base)
        base += len(used)
    P, N, J, W, T = map(np.concatenate, (P, N, J, W, T))
    _, first, weld = np.unique(np.round(P / 1e-5).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    weld = weld.ravel()
    T = weld[T]
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 2] != T[:, 0])]
    # (its normals the mean of the welded copies')
    Nw = np.zeros((len(first), 3), np.float64)
    np.add.at(Nw, weld, N)
    Nw /= np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-9)
    Pw = P[first].astype(np.float64) - Nw * INSET
    dst, _e = mo_simplify(T.ravel(), Pw, SHADOW, mo.SIMPLIFY_ERROR_ABSOLUTE | mo.SIMPLIFY_PRUNE)
    Ts = dst.reshape(-1, 3).astype(np.int64)
    sattrs = {"POSITION": (Pw.astype(np.float32), False), "NORMAL": (Nw.astype(np.float32), False),
              "JOINTS_0": (J[first].astype(np.uint16), False), "WEIGHTS_0": (W[first].astype(np.float32), False)}
    w.mesh("lod_shadow", [(w.material("lod_shadow"), sattrs, Ts)])
    report["shadow"] = (len(T), len(T), len(T), len(Ts))
    print(f"  shadow: {len(T)} welded tris, {len(Ts)} after simplifying", flush=True)

    w.js.setdefault("asset", {})["extras"] = {"heroine_lod": {"flat": FLAT, "dense": DENSE, "shadow": SHADOW, "inset": INSET,
                                                              "keep": KEEP, "blend": BLEND, "parts": report}}
    out = os.path.join(folder, f"heroine_outfit_{outfit}_lod.gltf")
    w.save(out)
    # (imported as the outfit is, without Godot's own LODs on top: a first import would generate them)
    imp = out + ".import"
    if not os.path.exists(imp) and os.path.exists(full.path + ".import"):
        keep = [l for l in open(full.path + ".import", encoding="utf-8").read().splitlines()
                if not l.startswith(("uid=", "path=", "dest_files=", "source_file="))]
        open(imp, "w", encoding="utf-8", newline="\n").write("\n".join(keep) + "\n")
    full_t = sum(r[0] for k, r in report.items() if k.startswith(("outfit.", "body.")))
    lod_t = sum(r[3] for k, r in report.items() if k.startswith(("outfit.", "body.")))
    print(f"LOD {outfit}: {full_t} -> {lod_t} tris ({lod_t / full_t:.1%}), shadow {report['shadow'][3]} -> {out}", flush=True)
    return report


def main(argv):
    folder = argv[0]
    sets = argv[1:] or sorted(f[len("heroine_outfit_"):-5] for f in os.listdir(folder)
                              if f.startswith("heroine_outfit_") and f.endswith(".gltf") and not f.endswith("_lod.gltf"))
    for s in sets:
        lod(folder, s)


if __name__ == "__main__":
    main(sys.argv[1:])
