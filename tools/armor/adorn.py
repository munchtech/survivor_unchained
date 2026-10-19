"""Adornment on a built armor piece, and a tier variant's build (docs/armor/PIECE_SCHEMA.md).

    python tools/armor/adorn.py <id>            a piece with `base`: its base's built shell copied (never refit),
                                                the base's adornment kept or dropped (`base_adorn`), its own added
    python tools/armor/adorn.py <id> --post     a piece built in Blender: the adornment Blender doesn't make (every
                                                kind but a `row` of `rivet`), added to its exported file

Run by tools/armor/build.py (no Blender turn needed: numpy on the built files). Writes godot/art/armor/<id>.gltf +
.bin, armor_tuck/<id>.bin (the base's, byte for byte), <id>.sockets.json and its armor_index.json row; numbers to
.shots/armor2/build/<id>/numbers.json.

What each kind makes (all skinned on her skeleton; every new vertex carries the outfit shader's data, COLOR_0 sky /
piece / painted / flag and TEXCOORD_1 edge / convexity, taken from the shell at its foot and then set as below):
- `row`: library elements along a rim, `inset` in on the shell's outer face, `spacing` apart, none within `avoid` of
  the shell's fixings; each element rigid on the shell's blend at its foot. A row the same as one of the base's own
  (rim, mesh, spacing, inset, r, avoid) that `base_adorn: false` dropped is the base's very elements in its `mat`
  (the plain rivets gilt). Dropped from the gameplay LOD (a pixel at the play camera).
- `mesh`: a library mesh at a socket (its frame: +Z out, roll, offset, scale); its `metal` slot in `mat`, its `gem`
  slot in `gem_mat` (default gem_garnet). Rigid on the socket's blend. Kept in the gameplay LOD (a jewel is a focus).
- `trim`: a swept band along a rim, `inset` its centre line in from the rim, `width` across, `height` proud, its foot
  sunk 0.2 mm into the plate; a dark groove `gap` wide each side, a film on the plate (the shell's own mesh, its sky
  and convexity dropped: the shader draws it dark and rough). Each section rigid on the plate's blend under it; lowered
  where a strap crosses it (never through the leather). A coarser band in the gameplay LOD, on that LOD's own surface.
- `paint` `etch_<name>`: the etched pattern as a film 0.25 mm over the plate in the shell's own mesh and material,
  its sky and convexity dropped so the outfit shader draws it as acid-etched steel (darker, rougher, recessed: its
  hollow and occlusion terms), bright polished steel between. Why a film, not a texture: the metal kind of
  heroine_outfit.gdshader draws its texture's mean colour only (no albedo, normal or roughness pattern reaches the
  screen), so a pattern baked into a material's textures would not show without a shader edit; the shader's own
  per-vertex terms do. Kept in the gameplay LOD (coarser, on that LOD's surface): it is what tells the tier there.
"""
import copy
import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "assets"))
sys.path.insert(0, HERE)
import heroine_lod as hl  # noqa: E402
import piece_lod as pl  # noqa: E402

ART = os.path.join(ROOT, "godot", "art", "armor")
LIB = os.path.join(ART, "lib")
TEX = os.path.join(ART, "tex")
MATS = os.path.join(ROOT, "godot", "art", "people", "outfit_materials.json")
NATIVE = lambda ad: ad["kind"] == "row" and ad.get("mesh", "rivet") == "rivet"   # (piece_blender.py builds these)
GEMS = {"gem_garnet": ((70, 6, 16), (205, 32, 48)), "gem_amethyst": ((52, 14, 78), (160, 70, 205)),
        "gem_sapphire": ((8, 18, 78), (52, 104, 220)), "gem_emerald": ((4, 52, 26), (34, 170, 96))}
ETCH_SKY, ETCH_CONV = 0.28, 0.1      # (the film's sky (x the plate's) and convexity: dark, rough, hollow)
GROOVE_SKY, GROOVE_CONV = 0.12, 0.04
FILM = 0.00025                       # (m over the plate: the etch film and the grooves)
SUNK = 0.0002                        # (m: a trim's foot and a mesh's base into the plate, so no hairline shows)


def say(*a):
    print("ADORN", *a, flush=True)


# ----------------------------------------------------------------------------------------- the model --
class Model:
    """A built piece's glTF as meshes of numpy arrays (one primitive each), written back compact."""

    def __init__(self, path):
        self.g = hl.Gltf(path)
        self.js = self.g.js
        self.joints = self.g.joint_names()
        self.meshes = []
        for i, m in enumerate(self.js["meshes"]):
            if len(m["primitives"]) != 1:
                raise SystemExit(f"ADORN: {m['name']} has {len(m['primitives'])} primitives (one each expected)")
            mat, attrs, tris = self.g.prims(i)[0]
            self.meshes.append({"name": m["name"], "mat": mat, "attrs": {k: [np.array(v[0]), v[1]] for k, v in attrs.items()},
                                "tris": tris, "extras": copy.deepcopy(m.get("extras", {})), "node": None})
        for k, n in enumerate(self.js["nodes"]):
            if "mesh" in n:
                self.meshes[n["mesh"]]["node"] = k
        self.parent = next(k for k, n in enumerate(self.js["nodes"]) if self.meshes[0]["node"] in n.get("children", []))

    def get(self, name):
        return next((m for m in self.meshes if m["name"] == name), None)

    def rename(self, old, new):
        for m in self.meshes:
            if m["name"].startswith(old + "."):
                m["name"] = new + m["name"][len(old):]
                if "of" in m["extras"]:
                    m["extras"]["of"] = [new + o[len(old):] if o.startswith(old + ".") else o for o in m["extras"]["of"]]
                if m["extras"].get("outfit") == old:
                    m["extras"]["outfit"] = new

    def material(self, name):
        for i, m in enumerate(self.js["materials"]):
            if m["name"] == name:
                return i
        self.js["materials"].append(material_def(name, self.js))
        return len(self.js["materials"]) - 1

    def save(self, path):
        js = self.js
        out = bytearray()
        views, accs = [], []

        def add(arr, normalized=False, target=None, minmax=False):
            arr = np.ascontiguousarray(arr)
            while len(out) % 4:
                out.append(0)
            v = {"buffer": 0, "byteOffset": len(out), "byteLength": arr.nbytes}
            if target:
                v["target"] = target
            out.extend(arr.tobytes())
            views.append(v)
            a = {"bufferView": len(views) - 1, "componentType": hl._CODE[arr.dtype], "count": len(arr),
                 "type": hl._TYPE[1 if arr.ndim == 1 else arr.shape[1]]}
            if normalized:
                a["normalized"] = True
            if minmax:
                a["min"], a["max"] = arr.min(0).tolist(), arr.max(0).tolist()
            accs.append(a)
            return len(accs) - 1

        ibm = self.g.acc(js["skins"][0]["inverseBindMatrices"])[0]
        js["skins"][0]["inverseBindMatrices"] = add(ibm.astype(np.float32))
        meshes, nodes = [], js["nodes"]
        for k, n in enumerate(nodes):
            n.pop("mesh", None)
        for m in self.meshes:
            p = {"attributes": {}, "material": self.material(m["mat"])}
            for key in ("POSITION", "NORMAL", "TEXCOORD_0", "TEXCOORD_1", "TEXCOORD_2", "COLOR_0", "JOINTS_0", "WEIGHTS_0"):
                if key in m["attrs"]:
                    arr, norm = m["attrs"][key]
                    p["attributes"][key] = add(arr, norm, 34962, minmax=key == "POSITION")
            t = m["tris"].ravel()
            p["indices"] = add(t.astype(np.uint32 if len(m["attrs"]["POSITION"][0]) > 65535 else np.uint16), False, 34963)
            meshes.append({"name": m["name"], "primitives": [p], "extras": m["extras"]})
            if m["node"] is None:
                nodes.append({"name": m["name"], "skin": 0})
                nodes[self.parent].setdefault("children", []).append(len(nodes) - 1)
                m["node"] = len(nodes) - 1
            nodes[m["node"]]["name"] = m["name"]
            nodes[m["node"]]["mesh"] = len(meshes) - 1
        js["meshes"], js["accessors"], js["bufferViews"] = meshes, accs, views
        base = os.path.splitext(os.path.basename(path))[0] + ".bin"
        js["buffers"] = [{"byteLength": len(out), "uri": base}]
        open(os.path.join(os.path.dirname(path), base), "wb").write(bytes(out))
        json.dump(js, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def material_def(name, js):
    """A glTF material for an outfit_materials.json entry: the outfits' own textures (art/people/outfit_tex) where an
    outfit has that material, a gem's from art/armor/tex."""
    def tex(uri):
        for i, im in enumerate(js.setdefault("images", [])):
            if im["uri"] == uri:
                break
        else:
            js["images"].append({"uri": uri, "mimeType": "image/png" if uri.endswith(".png") else "image/jpeg",
                                 "name": os.path.splitext(os.path.basename(uri))[0]})
            i = len(js["images"]) - 1
        if not js.get("samplers"):
            js["samplers"] = [{"magFilter": 9729, "minFilter": 9987}]
        for k, t in enumerate(js.setdefault("textures", [])):
            if t["source"] == i:
                return k
        js["textures"].append({"sampler": 0, "source": i})
        return len(js["textures"]) - 1

    if name in GEMS:
        gem_textures()
        return {"name": name, "doubleSided": False,
                "pbrMetallicRoughness": {"baseColorTexture": {"index": tex(f"tex/{name}_diff.png")}, "metallicFactor": 0.0, "roughnessFactor": 0.12}}
    import glob
    for f in sorted(glob.glob(os.path.join(ROOT, "godot", "art", "people", "heroine_outfit_*.gltf"))):
        if f.endswith("_lod.gltf"):
            continue
        o = json.load(open(f, encoding="utf-8"))
        for m in o.get("materials", []):
            if m["name"] != name:
                continue
            uri = lambda t: "../people/" + o["images"][o["textures"][t["index"]]["source"]]["uri"]
            pb = m.get("pbrMetallicRoughness", {})
            d = {"name": name, "doubleSided": False, "pbrMetallicRoughness": {"metallicFactor": pb.get("metallicFactor", 1.0)}}
            if "roughnessFactor" in pb:
                d["pbrMetallicRoughness"]["roughnessFactor"] = pb["roughnessFactor"]
            if pb.get("baseColorTexture"):
                d["pbrMetallicRoughness"]["baseColorTexture"] = {"index": tex(uri(pb["baseColorTexture"]))}
            if m.get("normalTexture"):
                d["normalTexture"] = {"index": tex(uri(m["normalTexture"]))}
            return d
    raise SystemExit(f"ADORN: no outfit has a material {name!r} to take its textures from")


def gem_textures():
    """Each gem's colour (procedural): deep at its girdle, lit within, brightest a little below its centre (the light
    through it), a faint table ring; read through the stone's own UVs (its footprint)."""
    from PIL import Image
    os.makedirs(TEX, exist_ok=True)
    n = 128
    y, x = (np.mgrid[0:n, 0:n] + 0.5) / n
    r = np.hypot(x - 0.5, y - 0.5) * 2
    glow = np.exp(-((x - 0.5) ** 2 + (y - 0.6) ** 2) / (2 * 0.17 ** 2))
    ring = np.exp(-((r - 0.55) / 0.05) ** 2) * 0.25
    for k, (deep, bright) in GEMS.items():
        f = os.path.join(TEX, f"{k}_diff.png")
        if os.path.exists(f):
            continue
        t = np.clip(0.15 + 0.85 * glow + ring - 0.35 * np.clip(r - 0.75, 0, 1), 0, 1)[..., None]
        img = np.asarray(deep, float) * (1 - t) + np.asarray(bright, float) * t
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(f)


# ------------------------------------------------------------------------------------ weights, data --
def dense(m, nb):
    j = m["attrs"]["JOINTS_0"][0].astype(np.int64)
    w = pl.floats(*m["attrs"]["WEIGHTS_0"]).astype(np.float64)
    out = np.zeros((len(j), nb))
    np.add.at(out, (np.arange(len(j))[:, None].repeat(4, 1), j), w)
    return out


def top4(d):
    k = np.argsort(-d, 1)[:, :4]
    w = np.take_along_axis(d, k, 1)
    w[w < 1e-4] = 0
    w /= np.maximum(w.sum(1, keepdims=True), 1e-12)
    return k.astype(np.uint8), w.astype(np.float32)


def colour(m):
    return pl.floats(*m["attrs"]["COLOR_0"]).astype(np.float64)


# ------------------------------------------------------------------------------------- the surface --
class Surface:
    """A mesh's big parts (plates, rolled edges: not rivets, buckles) as a surface to lay adornment on: closest
    points, rays, and its per-vertex data at any point (barycentric)."""

    def __init__(self, m, nb):
        P = m["attrs"]["POSITION"][0].astype(np.float64)
        T = m["tris"]
        lab = pl.parts(P, T)
        keep = np.zeros(len(T), bool)
        for c in np.unique(lab):
            s = lab == c
            v = P[np.unique(T[s])]
            if np.linalg.norm(v.max(0) - v.min(0)) >= pl.SMALL:
                keep |= s
        if "TEXCOORD_2" in m["attrs"]:
            # (not the rolled edges: their trim UVs run along them; adornment lies on the plates)
            tu = m["attrs"]["TEXCOORD_2"][0]
            keep &= ~(np.abs(tu[T][..., 0]) > 1e-6).any(1)
        self.P, self.T = P, T[keep]
        self.N = m["attrs"]["NORMAL"][0].astype(np.float64)
        self.W = dense(m, nb)
        self.C = colour(m)
        self.U1 = m["attrs"]["TEXCOORD_1"][0].astype(np.float64)
        self.U0 = m["attrs"]["TEXCOORD_0"][0].astype(np.float64)
        a, b, c = (P[self.T[:, k]] for k in range(3))
        self.A, self.E0, self.E1 = a, b - a, c - a
        # (which way a face looks, from its vertices' normals: the materials are double-sided, so winding says nothing)
        fn = self.N[self.T].sum(1)
        self.FN = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-15)
        self.tree = cKDTree((a + b + c) / 3)
        self._ray = None

    def closest(self, Q, nref=None, k=24):
        """Closest points on the surface to Q (and, with nref, only faces facing the way of nref): point, face, bary."""
        Q = np.atleast_2d(Q)
        _, cand = self.tree.query(Q, k=k)
        A, E0, E1 = self.A[cand], self.E0[cand], self.E1[cand]
        d = Q[:, None] - A
        d00, d01, d11 = (E0 * E0).sum(2), (E0 * E1).sum(2), (E1 * E1).sum(2)
        d20, d21 = (d * E0).sum(2), (d * E1).sum(2)
        den = np.maximum(d00 * d11 - d01 * d01, 1e-20)
        v = (d11 * d20 - d01 * d21) / den
        w = (d00 * d21 - d01 * d20) / den
        v, w = np.clip(v, 0, 1), np.clip(w, 0, 1)
        s = v + w
        over = s > 1
        s = np.maximum(s, 1e-12)
        v = np.where(over, v / s, v)
        w = np.where(over, w / s, w)
        X = A + E0 * v[..., None] + E1 * w[..., None]
        dist = np.linalg.norm(Q[:, None] - X, axis=2)
        if nref is not None:
            nref = np.atleast_2d(nref)
            facing = (self.FN[cand] * nref[:, None]).sum(2) > 0.2
            dist = np.where(facing, dist, dist + 1.0)
        j = dist.argmin(1)
        r = np.arange(len(Q))
        f = cand[r, j]
        bary = np.stack([1 - v[r, j] - w[r, j], v[r, j], w[r, j]], 1)
        return X[r, j], f, bary

    def at(self, arr, f, bary):
        return (arr[self.T[f]] * bary[..., None]).sum(1)

    def normal(self, f, bary, nref=None):
        n = self.at(self.N, f, bary)
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        if nref is not None:
            n *= np.sign((n * np.atleast_2d(nref)).sum(1))[:, None] + (np.abs((n * np.atleast_2d(nref)).sum(1)) < 1e-9)[:, None]
        return n

    def snap(self, Q, nref, lift=0.002, rounds=2):
        """Q onto the outer face (the one facing nref): from `lift` above it each round."""
        p, f, b = self.closest(Q, nref)
        for _ in range(rounds):
            n = self.normal(f, b, nref)
            p, f, b = self.closest(p + n * lift, n)
        return p, f, b, self.normal(f, b, nref)

    def ray(self, O, D):
        """First hits of rays O + t D on faces facing against D: (points, faces, bary, hit mask)."""
        import trimesh
        if self._ray is None:
            tm = trimesh.Trimesh(self.P, self.T, process=False)
            try:
                from trimesh.ray.ray_pyembree import RayMeshIntersector
                self._ray = RayMeshIntersector(tm)
            except Exception:
                self._ray = tm.ray
        loc, ri, ti = self._ray.intersects_location(O, D, multiple_hits=True)
        n = len(O)
        best = np.full(n, np.inf)
        fi = np.full(n, -1)
        pt = np.zeros((n, 3))
        for l_, r_, t_ in zip(loc, ri, ti):
            if (self.FN[t_] @ D[r_]) >= -0.2:
                continue
            dd = np.linalg.norm(l_ - O[r_])
            if dd < best[r_]:
                best[r_], fi[r_], pt[r_] = dd, t_, l_
        hit = fi >= 0
        _, f, b = self.closest(np.where(hit[:, None], pt, O), -D)
        return pt, f, b, hit


# ---------------------------------------------------------------------------------------- the rims --
def rim_names(sock, stem):
    rims = sock["rims"]
    if stem in rims:
        return [stem]
    out = [k for k in (f"{stem}_l", f"{stem}_r") if k in rims]
    if not out:
        raise SystemExit(f"ADORN: no rim {stem!r} (rims: {sorted(rims)})")
    return out


def socket_names(sock, stem):
    ss = sock["sockets"]
    if stem in ss:
        return [stem]
    out = [k for k in (f"{stem}_l", f"{stem}_r") if k in ss]
    if not out:
        raise SystemExit(f"ADORN: no socket {stem!r} (sockets: {sorted(ss)})")
    return out


def rim_line(rim, step):
    """A closed rim resampled `step` apart: points, outward (in the surface, away from the plate), normals, run (m)."""
    P = np.array(rim["points"])
    O = np.array(rim["outward"])
    N = np.array(rim["normals"])
    Pc = np.vstack([P, P[:1]])
    run = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pc, axis=0), axis=1))]
    n = max(8, int(round(run[-1] / step)))
    s = np.arange(n) * run[-1] / n
    at = lambda a: np.stack([np.interp(s, run, np.vstack([a, a[:1]])[:, k]) for k in range(3)], 1)
    p, o, nn = at(P), at(O), at(N)
    nn /= np.linalg.norm(nn, axis=1, keepdims=True)
    # (outward made square to the line and the normal: the rim's own outward wanders along it, which zig-zagged a
    # band laid by it)
    k = max(1, int(round(0.004 / max(run[-1] / n, 1e-6))))
    t = np.roll(p, -k, 0) - np.roll(p, k, 0)
    o2 = np.cross(t, nn)
    o2 /= np.maximum(np.linalg.norm(o2, axis=1, keepdims=True), 1e-12)
    o2 *= np.sign((o2 * o).sum(1, keepdims=True) + 1e-12)
    return p, o2, nn, s


def inward(surf, P, O, N, d, steps=4):
    """Points `d` in from the rim points P along the surface (marched in steps, snapped to the outer face each),
    their faces, bary and normals."""
    p, n, o = P.copy(), N.copy(), O.copy()
    f = b = None
    if d <= 0:
        p, f, b, n = surf.snap(p, n)
        return p, f, b, n
    for _ in range(steps):
        o_ = o - n * (o * n).sum(1, keepdims=True)
        o_ /= np.maximum(np.linalg.norm(o_, axis=1, keepdims=True), 1e-12)
        p, f, b, n = surf.snap(p - o_ * (d / steps), n)
        o = o_
    return p, f, b, n


def frame(n, up=None):
    """The socket frame at a point (schema): Z the normal, Y world up squared against it (her forward if Z is near
    vertical), X = Y x Z."""
    n = n / np.linalg.norm(n)
    u = np.array([0, 1.0, 0]) if up is None else np.asarray(up, float)
    if abs(u @ n) > 0.95:
        u = np.array([0, 0, 1.0])
    y = u - n * (u @ n)
    y /= np.linalg.norm(y)
    return np.cross(y, n), y, n


# ---------------------------------------------------------------------------------------- builders --
class Out:
    """New geometry for one mesh (a material): arrays to append."""

    def __init__(self):
        self.P, self.N, self.U0, self.U1, self.C, self.W, self.T = [], [], [], [], [], [], []
        self.n = 0

    def add(self, P, N, U0, U1, C, W, T):
        self.T.append(np.asarray(T, np.int64) + self.n)
        for k, a in (("P", P), ("N", N), ("U0", U0), ("U1", U1), ("C", C), ("W", W)):
            getattr(self, k).append(np.asarray(a, np.float64))
        self.n += len(P)

    def empty(self):
        return self.n == 0

    def arrays(self):
        return {k: np.concatenate(getattr(self, k)) for k in ("P", "N", "U0", "U1", "C", "W", "T")}


def grid_tris(ns, na, closed):
    """Quads of an ns x na grid (rows along, columns across) as triangles, wound for +Z out when
    columns run from the rim inward... (orientation fixed afterwards by fix_winding)."""
    T = []
    for i in range(ns if closed else ns - 1):
        i2 = (i + 1) % ns
        for j in range(na - 1):
            a, b, c, d = i * na + j, i2 * na + j, i2 * na + j + 1, i * na + j + 1
            T += [(a, b, c), (a, c, d)]
    return np.array(T, np.int64)


def fix_winding(P, T, N):
    """Each triangle wound so its face normal agrees with its vertices' normals."""
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    flip = (fn * N[T].mean(1)).sum(1) < 0
    T = T.copy()
    T[flip] = T[flip][:, [0, 2, 1]]
    return T


def smooth_normals(P, T):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    N = np.zeros_like(P)
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-15)


def film_strip(surf, rim, d0, d1, step, na, sky, conv, lift=FILM):
    """A film on the plate between d0 and d1 in from a rim (the etch's bands, a trim's grooves)."""
    P0, O0, N0, s = rim_line(rim, step)
    rows = []
    for d in np.linspace(d0, d1, na):
        rows.append(inward(surf, P0, O0, N0, d))
    ns = len(P0)
    P = np.stack([r[0] for r in rows], 1).reshape(-1, 3)
    N = np.stack([r[3] for r in rows], 1).reshape(-1, 3)
    F = np.stack([r[1] for r in rows], 1).ravel()
    B = np.stack([r[2] for r in rows], 1).reshape(-1, 3)
    T = fix_winding(P, grid_tris(ns, na, True), N)
    return film_from(surf, P, N, F, B, T, sky, conv, lift)


def film_from(surf, P, N, F, B, T, sky, conv, lift=FILM):
    C = surf.at(surf.C, F, B)
    C[:, 0] = np.clip(C[:, 0] * sky, 0, 1)
    U1 = surf.at(surf.U1, F, B)
    U1[:, 0] = np.maximum(U1[:, 0], 0.004)     # (no edge polish on it)
    U1[:, 1] = conv
    return P + N * lift, N, surf.at(surf.U0, F, B), U1, C, surf.at(surf.W, F, B), T


PROFILES = {
    # (across -1..1, height 0..1): a flat-topped band with rounded shoulders and a short wall
    "gold_band": [(-1, 0), (-1, 0.55), (-0.86, 0.88), (-0.6, 1.0), (-0.2, 1.0), (0.2, 1.0), (0.6, 1.0), (0.86, 0.88), (1, 0.55), (1, 0)],
    "rolled": [(np.cos(a), np.sin(a)) for a in np.linspace(np.pi, 0, 9)],
    "rope": [(np.cos(a), np.sin(a)) for a in np.linspace(np.pi, 0, 9)],
    "filigree": [(-1, 0), (-1, 0.5), (-0.7, 0.8), (-0.35, 0.6), (0, 1.0), (0.35, 0.6), (0.7, 0.8), (1, 0.5), (1, 0)],
}


def trim_band(surf, rim, ad, step, leather, lod=False):
    """A swept band along a rim on the surface (see the module doc)."""
    prof = PROFILES[ad.get("profile", "gold_band")]
    if lod:
        prof = [(-1, 0), (-1, 0.7), (-0.6, 1.0), (0.6, 1.0), (1, 0.7), (1, 0)]
    w, h, dc = ad.get("width", 0.005), ad.get("height", 0.0015), ad.get("inset", 0.0)
    P0, O0, N0, s = rim_line(rim, step)
    pc, fc, bc, nc = inward(surf, P0, O0, N0, dc)
    # (each section's own across direction: from a point a little further in)
    pi_, _, _, _ = inward(surf, P0, O0, N0, dc + w / 2)
    po_, _, _, _ = inward(surf, P0, O0, N0, max(dc - w / 2, 0.0))
    ac = pi_ - po_
    ac -= nc * (ac * nc).sum(1, keepdims=True)
    ac /= np.maximum(np.linalg.norm(ac, axis=1, keepdims=True), 1e-12)
    # (lowered where leather crosses it: its height there under the leather's underside, less 0.4 mm)
    hh = np.full(len(pc), h)
    if leather is not None:
        lt = cKDTree(leather)
        for i, (p, n) in enumerate(zip(pc, nc)):
            near = lt.query_ball_point(p, w * 0.5 + 0.004)
            if near:
                up = (leather[near] - p) @ n
                up = up[up > -0.0005]
                if len(up):
                    hh[i] = min(hh[i], max(up.min() - 0.0004, 0.0002))
        hh = np.minimum(hh, np.convolve(np.r_[hh[-2:], hh, hh[:2]], np.ones(5) / 5, "valid"))
    # (rigid sections: each on the plate's blend at its centre)
    Wc = surf.at(surf.W, fc, bc)
    Cc = surf.at(surf.C, fc, bc)
    na = len(prof)
    P, N, U0, U1, C, W = [], [], [], [], [], []
    for i in range(len(pc)):
        for a, z in prof:
            z_ = z
            if ad.get("profile") == "rope":
                z_ = z * (0.72 + 0.28 * np.cos(2 * np.pi * s[i] / max(w * 1.6, 1e-3) + np.pi * a))
            P.append(pc[i] + ac[i] * (a * w / 2) + nc[i] * (z_ * hh[i] - SUNK))
            U0.append((s[i] * 3.0, (a + 1) * w / 2 * 3.0))   # (gold's repeats a metre)
            U1.append((max((1 - abs(a)) * w / 2, 0.0), 0.5 + 0.3 * z))
            c = Cc[i].copy()
            c[3] = 1.0
            C.append(c)
            W.append(Wc[i])
    P = np.array(P)
    T = grid_tris(len(pc), na, True)
    Nn = smooth_normals(P, T)
    ref = np.repeat(nc, na, 0)
    if (Nn * ref).sum(1).mean() < 0:
        T = T[:, [0, 2, 1]]
        Nn = -Nn
    return {"P": P, "N": Nn, "U0": np.array(U0), "U1": np.array(U1), "C": np.array(C), "W": np.array(W), "T": T,
            "sections": len(pc), "height_min": float(hh.min()), "height": h, "centre": pc, "normal": nc}


def lib_mesh(mid):
    """A library mesh (art/armor/lib/<id>.glb, its own axes the socket frame): {slot: (points, normals, tris)}."""
    g = hl.Gltf(os.path.join(LIB, f"{mid}.glb"))
    out = {}
    for mat, a, t in g.prims(0):
        out[mat] = (a["POSITION"][0].astype(np.float64), a["NORMAL"][0].astype(np.float64), t)
    return out


def place(lm, slot, origin, X, Y, Z, scale, roll, offset):
    P, N, T = lm[slot]
    c, s_ = np.cos(np.radians(roll)), np.sin(np.radians(roll))
    R = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1.0]])
    M = np.stack([X, Y, Z], 1) @ R
    o = origin + M @ np.asarray(offset, float) - Z * SUNK
    return (P * scale) @ M.T + o, N @ M.T, T, P


def element(lm, slot, origin, X, Y, Z, w_row, c_row, scale=1.0, roll=0.0, offset=(0, 0, 0), gem_uv=False):
    P, N, T, P0 = place(lm, slot, origin, X, Y, Z, scale, roll, offset)
    n = len(P)
    ext = np.abs(P0[:, :2]).max() or 1.0
    U0 = (np.c_[0.5 + P0[:, 0] / (2 * ext), 0.5 - P0[:, 1] / (2 * ext)] if gem_uv else P0[:, :2] * 3.0)
    c = c_row.copy()
    c[3] = 1.0
    zz = P0[:, 2] / max(P0[:, 2].max(), 1e-6)
    U1 = np.c_[np.full(n, 0.002), 0.5 + 0.3 * zz]     # (polished: an element is all edge)
    return P, N, U0, U1, np.repeat(c[None], n, 0), np.repeat(w_row[None], n, 0), T


# ---------------------------------------------------------------------------------------- the etch --
def spiral(cx, cy, r0, r1, a0, turns, n=60, sign=1):
    a = a0 + sign * np.linspace(0, 2 * np.pi * turns, n)
    r = np.linspace(r0, r1, n)
    return np.c_[cx + r * np.cos(a), cy + r * np.sin(a)]


def bez(p0, p1, p2, p3, n=40):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def scroll_strokes():
    """The 'scroll' motif in mm on a cup's chart (x outward from the gore, y up, the crown at 0,0): a lyre of two
    C-scrolls rising from a stem under the crown and curling in round it, a pair of leaves off the stem, and a bud
    above; symmetric about x = 0. Each stroke: (points (n, 2), width at its start, width at its end)."""
    out = []
    for sx in (1, -1):
        m = np.array([sx, 1.0])
        # the scroll: from the stem's top out and up round the crown, ending in a curl above-outside it
        a = bez(np.array([0, -15.0]), np.array([9, -15.0]), np.array([17, -8.0]), np.array([17, 2.0]))
        b = bez(np.array([17, 2.0]), np.array([17, 10.0]), np.array([11, 14.0]), np.array([7, 11.0]), 24)
        c = spiral(9.5, 8.5, 3.4, 1.0, np.radians(225), 0.9, 30, sign=-1)
        out.append((np.vstack([a, b[1:], c[1:]]) * m, 1.9, 0.9))
        # a leaf off the stem, down and out, its tip curled
        l1 = bez(np.array([0, -24.0]), np.array([6, -23.0]), np.array([12, -27.0]), np.array([14, -33.0]), 24)
        l2 = spiral(11.8, -33.0, 2.2, 0.7, np.radians(0), 0.8, 18, sign=-1)
        out.append((np.vstack([l1, l2[1:]]) * m, 1.6, 0.8))
        # a small inner tendril from the scroll's base, curling toward the crown's underside
        t1 = bez(np.array([7, -14.6]), np.array([8, -10.0]), np.array([6, -7.5]), np.array([4, -8.5]), 16)
        out.append((t1 * m, 1.1, 0.6))
    out.append((np.c_[np.zeros(30), np.linspace(-40.0, -15.0, 30)], 2.1, 1.9))    # the stem
    out.append((np.c_[np.zeros(10), np.linspace(15.5, 20.5, 10)], 1.6, 0.8))      # the bud above the crown
    return out


def ribbon(pts, w0, w1):
    """A stroke as a ribbon in 2D: left and right edge points (n, 2) each."""
    d = np.gradient(pts, axis=0)
    d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    nrm = np.c_[-d[:, 1], d[:, 0]]
    w = np.linspace(w0, w1, len(pts))[:, None] / 2
    return pts + nrm * w, pts - nrm * w


def resample(pts, step):
    run = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    n = max(2, int(np.ceil(run[-1] / step)) + 1)
    s = np.linspace(0, run[-1], n)
    return np.c_[np.interp(s, run, pts[:, 0]), np.interp(s, run, pts[:, 1])]


def etch(surf, sock, ad, lod):
    """The etched pattern (`pattern` etch_scroll): on each cup a double border inside the rim's rivets (a broad etched
    band and a fine line in from it) and the scroll motif round its crown."""
    name = ad.get("pattern", "etch_scroll")
    if name != "etch_scroll":
        raise SystemExit(f"ADORN: no etched pattern {name!r} (etch_scroll)")
    k = float(ad.get("strength", 1.0))
    sky = 1 - (1 - ETCH_SKY) * k
    conv = ETCH_CONV
    step = 0.006 if lod else 0.002
    lift = FILM * (1.6 if lod else 1.0)
    parts, stats = [], {"bands": 0, "strokes": 0, "missed": 0}
    band = ad.get("band", [0.0115, 0.0175])
    line = ad.get("line", [0.0198, 0.021])
    for rn in rim_names(sock, ad.get("rim", "cup_rim")):
        rim = sock["rims"][rn]
        parts.append(film_strip(surf, rim, band[0], band[1], step, 2 if lod else 3, sky, conv, lift))
        stats["bands"] += 1
        if not lod:
            parts.append(film_strip(surf, rim, line[0], line[1], step, 2, sky, conv, lift))
    for sn in socket_names(sock, ad.get("socket", "cup")):
        so = sock["sockets"][sn]
        c, n, up = np.array(so["point"]), np.array(so["normal"]), np.array(so["up"])
        X = np.cross(up, n)
        sx = 1.0 if X[0] * c[0] > 0 else -1.0       # (x outward from the gore on both cups: mirrored)
        sc = float(ad.get("scale", 1.0))
        for pts, w0, w1 in scroll_strokes():
            pts = resample(pts * sc, 2.4 if lod else 0.7)
            L, R = ribbon(pts, max(w0 * sc, 1.6 if lod else 0), max(w1 * sc, 1.2 if lod else 0))
            two = np.stack([L, R], 1).reshape(-1, 2) / 1000.0
            O = c + n * 0.06 + np.outer(two[:, 0] * sx, X) + np.outer(two[:, 1], up)
            p, f, b, hit = surf.ray(O, np.repeat(-n[None], len(O), 0))
            nn = surf.normal(f, b, n)
            T = fix_winding(p, grid_tris(len(pts), 2, False), nn)
            if not hit.all():
                stats["missed"] += int((~hit).sum())
                good = hit.reshape(-1, 2).all(1)
                keep = good[np.arange(len(pts) - 1)] & good[np.arange(1, len(pts))]
                T = T.reshape(-1, 2, 3)[keep].reshape(-1, 3)
            parts.append(film_from(surf, p, nn, f, b, T, sky, conv, lift))
            stats["strokes"] += 1
    return parts, stats


# ------------------------------------------------------------------------------------------ helpers --
def append(m, parts, nb):
    """New geometry into a mesh (its own attribute set; TEXCOORD_2 zero where the mesh has it). The tris of each
    append are recorded in its extras' adorn_tris, so a later variant can drop them."""
    have = m["attrs"]
    n0, t0 = len(have["POSITION"][0]), len(m["tris"])
    ps = [p for p in parts if len(p[0])]
    if not ps:
        return 0
    P = np.concatenate([p[0] for p in ps])
    N = np.concatenate([p[1] for p in ps])
    U0 = np.concatenate([p[2] for p in ps])
    U1 = np.concatenate([p[3] for p in ps])
    C = np.concatenate([p[4] for p in ps])
    W = np.concatenate([p[5] for p in ps])
    T, off = [], 0
    for p in ps:
        T.append(np.asarray(p[6]) + off + n0)
        off += len(p[0])
    T = np.concatenate(T)
    J, Wt = top4(W)
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    new = {"POSITION": P.astype(np.float32), "NORMAL": N.astype(np.float32), "TEXCOORD_0": U0.astype(np.float32),
           "TEXCOORD_1": U1.astype(np.float32), "TEXCOORD_2": np.zeros((len(P), 2), np.float32),
           "COLOR_0": np.round(np.clip(C, 0, 1) * 65535).astype(np.uint16), "JOINTS_0": J, "WEIGHTS_0": Wt}
    for k, (arr, norm) in list(have.items()):
        v = new[k]
        if k == "COLOR_0" and arr.dtype != np.uint16:
            v = (np.clip(C, 0, 1) * {np.dtype(np.uint8): 255}.get(arr.dtype, 1)).astype(arr.dtype)
        have[k] = [np.concatenate([arr, v.astype(arr.dtype)]), norm]
    m["tris"] = np.concatenate([m["tris"], T])
    m["extras"].setdefault("adorn_tris", []).append([int(t0), int(len(T))])
    return len(T)


def new_mesh(model, name, mat, like, extras):
    m = {"name": name, "mat": mat, "attrs": {}, "tris": np.zeros((0, 3), np.int64), "extras": extras, "node": None}
    for k in ("POSITION", "NORMAL", "TEXCOORD_0", "TEXCOORD_1", "COLOR_0", "JOINTS_0", "WEIGHTS_0"):
        arr, norm = like["attrs"][k]
        m["attrs"][k] = [np.zeros((0, arr.shape[1]), arr.dtype), norm]
    model.meshes.append(m)
    return m


def soup(m, keep=None):
    """A mesh's triangles as sorted rows of their vertices' bytes (every attribute): equal soups are bit-equal
    geometry, weights and shading data, whatever the vertex order."""
    T = m["tris"] if keep is None else m["tris"][keep]
    cols = [np.ascontiguousarray(m["attrs"][k][0]).view(np.uint8).reshape(len(m["attrs"][k][0]), -1)
            for k in sorted(m["attrs"])]
    V = np.concatenate(cols, 1)
    rows = np.concatenate([V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]], 1)
    from collections import Counter
    return Counter(r.tobytes() for r in rows)


def compact(m):
    used, inv = np.unique(m["tris"].ravel(), return_inverse=True)
    for k in m["attrs"]:
        m["attrs"][k][0] = m["attrs"][k][0][used]
    m["tris"] = inv.reshape(-1, 3)


# ------------------------------------------------------------------------------------------ the pose check --
def pose_check(shell_id, model, new_by_mesh, base_full):
    """Every new vertex skinned into each test pose (her skinning matrices from the shell's build, poses.npz), and
    its signed distance to her posed skin there: through if under it. The shell's own vertices skinned the same way
    must land on the build's posed shell (a check of the matrices)."""
    f = os.path.join(ROOT, ".shots", "armor2", "build", shell_id, "poses.npz")
    if not os.path.exists(f):
        return {"skipped": f"no {os.path.relpath(f, ROOT)}: build {shell_id} (Blender) first"}
    z = np.load(f, allow_pickle=False)
    out = {}
    for pn in [str(x) for x in z["names"]]:
        bones = [str(b) for b in z[f"{pn}__bones"]]
        mats = z[f"{pn}__mats"]
        bi = {b: i for i, b in enumerate(bones)}
        M = np.stack([mats[bi[j]] for j in model.joints])
        skin, skin_n = z[f"{pn}__skin"], z[f"{pn}__skin_n"]
        st = cKDTree(skin)

        def pose(m, sel=None):
            P = m["attrs"]["POSITION"][0].astype(np.float64)
            J = m["attrs"]["JOINTS_0"][0].astype(np.int64)
            W = pl.floats(*m["attrs"]["WEIGHTS_0"]).astype(np.float64)
            if sel is not None:
                P, J, W = P[sel], J[sel], W[sel]
            Ph = np.c_[P, np.ones(len(P))]
            return np.einsum("nk,nkij,nj->ni", W, M[J], Ph)[:, :3]

        r = {"new_vertices": 0, "through": 0, "min_clear_mm": None}
        clear = []
        for m, sel in new_by_mesh:
            q = pose(m, sel)
            d, j = st.query(q, k=6)
            # (the signed distance off her skin: along the normal of the nearest skin points)
            sd = ((q[:, None] - skin[j]) * skin_n[j]).sum(2)
            sd = np.where(d[:, :1] < 0.03, np.median(sd, 1)[:, None], 1.0)[:, 0]
            clear.append(sd)
        cl = np.concatenate(clear) if clear else np.zeros(0)
        r["new_vertices"] = int(len(cl))
        r["through"] = int((cl < 0).sum())
        r["min_clear_mm"] = round(float(cl.min() * 1000), 2) if len(cl) else None
        sh = z[f"{pn}__shell"]
        bq = pose(base_full)
        dd, _ = cKDTree(bq).query(sh)
        r["skinning_check_mm"] = round(float(np.percentile(dd, 99) * 1000), 3)
        out[pn] = r
    return out


# ------------------------------------------------------------------------------------------- the build --
def mats_table():
    return json.load(open(MATS, encoding="utf-8"))


def check_mats(piece, table):
    bad = []
    names = [piece.get("material", "steel")] + [a.get("mat") for a in piece.get("adorn", []) if a.get("mat")] + \
            [a.get("gem_mat", "gem_garnet") for a in piece.get("adorn", []) if a["kind"] == "mesh"]
    for n in names:
        if n not in table:
            bad.append(n)
    if bad:
        raise SystemExit(f"ADORN REFUSED: {piece['id']}: material names not in outfit_materials.json: {sorted(set(bad))}")


def sig(ad):
    return (ad.get("rim", "cup_rim"), ad.get("mesh", "rivet"), round(ad.get("spacing", 0.021), 5), round(ad.get("inset", 0.0075), 5),
            round(ad.get("r", 0.0028), 5), round(ad.get("avoid", 0.014), 5))


def piece_json(pid):
    return json.load(open(os.path.join(ART, "src", pid, "piece.json"), encoding="utf-8"))


def build(pid, post=False):
    import shutil
    piece = piece_json(pid)
    table = mats_table()
    check_mats(piece, table)
    scratch = os.path.join(ROOT, ".shots", "armor2", "build", pid)
    os.makedirs(scratch, exist_ok=True)
    slot = piece["slot"]
    num = {"id": pid}
    if post:
        src_id, own = pid, [a for a in piece.get("adorn", []) if not NATIVE(a)]
        if not own:
            return {"id": pid, "post": "nothing to add"}
        model = Model(os.path.join(ART, f"{pid}.gltf"))
        sock = json.load(open(os.path.join(ART, f"{pid}.sockets.json"), encoding="utf-8"))
        shell_id = pid
        dropped_rows = {}
        base_piece = None
    else:
        src_id = piece["base"]
        base_piece = piece_json(src_id)
        if base_piece.get("base"):
            raise SystemExit(f"ADORN: {pid}'s base {src_id} is itself a variant (name the plain piece)")
        if base_piece["slot"] != slot:
            raise SystemExit(f"ADORN: {pid} is a {slot}, its base {src_id} a {base_piece['slot']}")
        model = Model(os.path.join(ART, f"{src_id}.gltf"))
        base_model = Model(os.path.join(ART, f"{src_id}.gltf"))
        sock = json.load(open(os.path.join(ART, f"{src_id}.sockets.json"), encoding="utf-8"))
        shell_id = src_id
        model.rename(src_id, pid)
        model.js["asset"]["extras"] = dict(model.js["asset"].get("extras", {}), armor_piece=pid, tier=piece.get("tier"), base=src_id,
                                           source=f"godot/art/armor/src/{pid}/piece.json")
        own = list(piece.get("adorn", []))
        keep_base = piece.get("base_adorn", True)
        # (kept, the base's built adornment is already in its file: native rows and adorn.py's alike)
        dropped_rows = {}
        if not keep_base:
            # the base's adornment out of every mesh: its native rows (found by their feet) and anything adorn.py added
            for m in model.meshes:
                if m["extras"].get("lod"):
                    continue
                P = m["attrs"]["POSITION"][0].astype(np.float64)
                lab = pl.parts(P, m["tris"])
                drop = np.zeros(len(m["tris"]), bool)
                for a, n in [(t0, c) for t0, c in m["extras"].pop("adorn_tris", [])]:
                    drop[a:a + n] = True
                for rec in sock.get("adorn", []):
                    if rec.get("mat", "steel") != m["mat"]:
                        continue
                    feet = np.array(rec["points"])
                    labs = np.unique(lab)
                    cen = np.array([P[np.unique(m["tris"][lab == c])].mean(0) for c in labs])
                    size = np.array([np.linalg.norm(np.ptp(P[np.unique(m["tris"][lab == c])], 0)) for c in labs])
                    d, j = cKDTree(cen).query(feet)
                    if (d > 0.004).any() or (size[j] > pl.SMALL).any() or len(set(j.tolist())) != len(feet):
                        raise SystemExit(f"ADORN: {src_id}'s {rec['rim']} row: {int((d > 0.004).sum())} of {len(feet)} elements not found by their feet")
                    sel = np.isin(lab, labs[j])
                    drop |= sel
                    # (kept aside: a variant row the same as this one is these very elements in its own mat)
                    sub = {"attrs": {k: [v[0], v[1]] for k, v in m["attrs"].items()}, "tris": m["tris"][sel]}
                    dropped_rows[sig(rec)] = dropped_rows.get(sig(rec), []) + [sub]
                if drop.any():
                    m["tris"] = m["tris"][~drop]
                    compact(m)
                    num.setdefault("base_adorn_dropped_tris", {})[m["name"]] = int(drop.sum())
    nb = len(model.joints)
    jindex = {n: i for i, n in enumerate(model.joints)}
    shell_full = model.get(f"{pid}.{slot}.{piece.get('material', 'steel')}") or model.get(f"{pid}.{slot}.{base_piece.get('material', 'steel') if base_piece else 'steel'}")
    shell_lod = model.get(f"{pid}.lod1.{shell_full['mat']}")
    leather = np.concatenate([m["attrs"]["POSITION"][0].astype(np.float64) for m in model.meshes
                              if not m["extras"].get("lod") and m is not shell_full and table.get(m["mat"], {}).get("kind") == "leather"] or [np.zeros((0, 3))])
    S_full = Surface(shell_full, nb)
    S_lod = Surface(shell_lod, nb) if shell_lod is not None else None
    base_full_snapshot = {"attrs": {k: [v[0].copy(), v[1]] for k, v in shell_full["attrs"].items()}, "tris": shell_full["tris"].copy()}
    full_new, lod_new = {}, {}       # mat -> list of parts
    stats = {"rows": [], "meshes": [], "trims": [], "paint": []}
    for ad in own:
        kind, mat = ad["kind"], ad.get("mat", piece.get("material", "steel"))
        if kind == "row":
            if sig(ad) in dropped_rows:
                for sub in dropped_rows.pop(sig(ad)):
                    T = sub["tris"]
                    used, inv = np.unique(T.ravel(), return_inverse=True)
                    a = sub["attrs"]
                    W = dense({"attrs": {"JOINTS_0": [a["JOINTS_0"][0][used]], "WEIGHTS_0": [a["WEIGHTS_0"][0][used], a["WEIGHTS_0"][1]]}}, nb)
                    full_new.setdefault(mat, []).append((a["POSITION"][0][used].astype(np.float64), a["NORMAL"][0][used].astype(np.float64),
                                                         a["TEXCOORD_0"][0][used], a["TEXCOORD_1"][0][used], colour({"attrs": {"COLOR_0": [a["COLOR_0"][0][used], a["COLOR_0"][1]]}}),
                                                         W, inv.reshape(-1, 3)))
                    stats["rows"].append({"rim": ad.get("rim"), "mesh": ad.get("mesh", "rivet"), "mat": mat, "from_base": True,
                                          "elements": int(len(np.unique(pl.parts(a["POSITION"][0][used].astype(np.float64), inv.reshape(-1, 3)))))})
                continue
            lm = lib_mesh(ad.get("mesh", "rivet"))
            info = json.load(open(os.path.join(LIB, "lib.json"), encoding="utf-8"))[ad.get("mesh", "rivet")]
            scale = ad.get("r", 0.0028) / (max(info["size_mm"][:2]) / 2000.0)
            fix = np.array(sock.get("fixings", [])).reshape(-1, 3)
            count = 0
            for rn in rim_names(sock, ad.get("rim", "cup_rim")):
                rim = sock["rims"][rn]
                P0, O0, N0, s = rim_line(rim, 0.0005)
                n_ = max(3, int(round(s[-1] / ad.get("spacing", 0.021))))
                pick = np.round((np.arange(n_) + 0.5) * len(P0) / n_).astype(int) % len(P0)
                p, f, b, nn = inward(S_full, P0[pick], O0[pick], N0[pick], ad.get("inset", 0.0075))
                for k in range(len(p)):
                    if len(fix) and np.linalg.norm(fix - p[k], axis=1).min() < ad.get("avoid", 0.014):
                        continue
                    X, Y, Z = frame(nn[k])
                    w_row = S_full.at(S_full.W, f[k:k + 1], b[k:k + 1])[0]
                    c_row = S_full.at(S_full.C, f[k:k + 1], b[k:k + 1])[0]
                    for slot_ in lm:
                        e = element(lm, slot_, p[k], X, Y, Z, w_row, c_row, scale)
                        full_new.setdefault(mat if slot_ != "gem" else ad.get("gem_mat", "gem_garnet"), []).append(e)
                    count += 1
            stats["rows"].append({"rim": ad.get("rim"), "mesh": ad.get("mesh"), "mat": mat, "elements": count})
        elif kind == "mesh":
            lm = lib_mesh(ad["mesh"])
            for sn in socket_names(sock, ad["socket"]):
                so = sock["sockets"][sn]
                n = np.array(so["normal"])
                up = np.array(so["up"])
                X = np.cross(up, n)
                w_row = np.zeros(nb)
                for bn, w in so["weights"]:
                    w_row[jindex[bn]] += w
                p, f, b, nn = S_full.snap(np.array(so["point"])[None], n[None])
                c_row = S_full.at(S_full.C, f, b)[0]
                tris = 0
                for slot_ in lm:
                    m_ = ad.get("gem_mat", "gem_garnet") if slot_ == "gem" else mat
                    e = element(lm, slot_, p[0], X, up, n, w_row, c_row, ad.get("scale", 1.0), ad.get("roll", 0.0),
                                ad.get("offset", [0, 0, 0]), gem_uv=slot_ == "gem")
                    full_new.setdefault(m_, []).append(e)
                    lod_new.setdefault(m_, []).append(e)
                    tris += len(e[6])
                stats["meshes"].append({"socket": sn, "mesh": ad["mesh"], "mat": mat, "gem_mat": ad.get("gem_mat", "gem_garnet"), "tris": tris})
        elif kind == "trim":
            for rn in rim_names(sock, ad["rim"]):
                rim = sock["rims"][rn]
                tb = trim_band(S_full, rim, ad, 0.0022, leather)
                full_new.setdefault(mat, []).append((tb["P"], tb["N"], tb["U0"], tb["U1"], tb["C"], tb["W"], tb["T"]))
                gap = ad.get("gap", 0.001)
                w, dc = ad.get("width", 0.005), ad.get("inset", 0.0)
                grooves = []
                if gap > 0:
                    for d0, d1 in ((max(dc - w / 2 - gap, 0), dc - w / 2), (dc + w / 2, dc + w / 2 + gap)):
                        grooves.append(film_strip(S_full, rim, d0, d1, 0.0022, 2, GROOVE_SKY, GROOVE_CONV))
                    full_new.setdefault(shell_full["mat"], []).extend(grooves)
                stats["trims"].append({"rim": rn, "profile": ad.get("profile", "gold_band"), "mat": mat, "sections": tb["sections"],
                                       "width_mm": w * 1000, "height_mm": tb["height"] * 1000, "height_min_mm": round(tb["height_min"] * 1000, 2),
                                       "inset_mm": dc * 1000, "gap_mm": gap * 1000, "tris": int(len(tb["T"])),
                                       "groove_tris": int(sum(len(g[6]) for g in grooves))})
                if S_lod is not None:
                    tl = trim_band(S_lod, rim, ad, 0.006, leather, lod=True)
                    lod_new.setdefault(mat, []).append((tl["P"], tl["N"], tl["U0"], tl["U1"], tl["C"], tl["W"], tl["T"]))
        elif kind == "paint":
            parts, st = etch(S_full, sock, ad, False)
            full_new.setdefault(shell_full["mat"], []).extend(parts)
            st["tris"] = int(sum(len(p[6]) for p in parts))
            if S_lod is not None:
                lparts, lst = etch(S_lod, sock, ad, True)
                lod_new.setdefault(shell_full["mat"], []).extend(lparts)
                st["lod1_tris"] = int(sum(len(p[6]) for p in lparts))
            stats["paint"].append(dict(st, pattern=ad.get("pattern")))
        else:
            raise SystemExit(f"ADORN: no adornment kind {kind!r}")
    # into the meshes
    new_sel = []
    for lodn, bucket in (("full", full_new), ("lod1", lod_new)):
        for mat, parts in bucket.items():
            if mat != "lod_shadow" and mat not in table:
                raise SystemExit(f"ADORN REFUSED: material {mat!r} not in outfit_materials.json")
            name = f"{pid}.{slot}.{mat}" if lodn == "full" else f"{pid}.lod1.{mat}"
            m = model.get(name)
            if m is None:
                ex = {"outfit": pid, "slot": slot, "material": mat, "rank": 0, "tier": piece.get("tier")} if lodn == "full" else \
                     {"lod": "lod1", "of": [f"{pid}.{slot}.{mat}"], "material": mat}
                m = new_mesh(model, name, mat, shell_full, ex)
            n0 = len(m["attrs"]["POSITION"][0])
            append(m, parts, nb)
            if lodn == "full":
                new_sel.append((m, np.arange(n0, len(m["attrs"]["POSITION"][0]))))
    # numbers
    full = [m for m in model.meshes if not m["extras"].get("lod")]
    lod1 = [m for m in model.meshes if m["extras"].get("lod") == "lod1"]
    shadow = [m for m in model.meshes if m["extras"].get("lod") == "shadow"]
    lod1_mats = {m["mat"] for m in lod1}
    num.update({"base": None if post else src_id, "tier": piece.get("tier"),
                "triangles": {"lod0": int(sum(len(m["tris"]) for m in full)), "gameplay": int(sum(len(m["tris"]) for m in lod1)) +
                              int(sum(len(m["tris"]) for m in full if m["mat"] not in lod1_mats)),
                              "shadow": int(sum(len(m["tris"]) for m in shadow))},
                "draws": {"lod0": len(full), "gameplay": len(lod1) + len([m for m in full if m["mat"] not in lod1_mats]), "shadow_pass": len(shadow)},
                "meshes": {m["name"]: int(len(m["tris"])) for m in model.meshes}, "adornment": stats})
    if not post:
        # the shell, bit-equal: every one of the base's meshes, less only the base's adornment it dropped, is in the
        # variant's mesh of the same name, its triangles' vertices byte for byte (every attribute)
        eq = {}
        for bm in base_model.meshes:
            vm = model.get(pid + bm["name"][len(src_id):])
            drop_n = num.get("base_adorn_dropped_tris", {}).get(vm["name"], 0)
            ext = vm["extras"].get("adorn_tris", [])
            keep = np.ones(len(vm["tris"]), bool)
            for a, n in ext:
                keep[a:a + n] = False
            sb = soup(bm)
            sv = soup(vm, keep)
            nb_, nv_ = sum(sb.values()), sum(sv.values())
            if drop_n:
                eq[bm["name"]] = {"base_tris": nb_, "kept": nv_, "dropped": drop_n,
                                  "bit_equal_less_dropped": bool(not (sv - sb) and nv_ == nb_ - drop_n)}
            else:
                eq[bm["name"]] = {"bit_equal": sv == sb, "tris": nb_}
        num["shell_vs_base"] = eq
        tb = open(os.path.join(ART, "armor_tuck", f"{src_id}.bin"), "rb").read()
    num["poses"] = pose_check(shell_id, model, new_sel, {"attrs": base_full_snapshot["attrs"], "tris": base_full_snapshot["tris"]})
    # write
    out = os.path.join(ART, f"{pid}.gltf")
    model.save(out)
    if not post:
        os.makedirs(os.path.join(ART, "armor_tuck"), exist_ok=True)
        open(os.path.join(ART, "armor_tuck", f"{pid}.bin"), "wb").write(tb)
        num["tuck_bit_equal"] = open(os.path.join(ART, "armor_tuck", f"{pid}.bin"), "rb").read() == tb
        s2 = dict(sock, id=pid, base=src_id)
        s2["uv_surface"] = dict(sock.get("uv_surface", {}), mesh=f"{pid}.{slot}.{shell_full['mat']}")
        if not piece.get("base_adorn", True):
            s2["adorn"] = []
        json.dump(s2, open(os.path.join(ART, f"{pid}.sockets.json"), "w", encoding="utf-8"), indent=1)
        ix_path = os.path.join(ART, "armor_index.json")
        rows = json.load(open(ix_path, encoding="utf-8"))
        brow = next(r for r in rows if r["id"] == src_id)
        rows = [r for r in rows if r["id"] != pid]
        row = dict(brow, id=pid, meshes=sorted(m["name"] for m in full), tuck=f"armor_tuck/{pid}.bin", file=f"res://art/armor/{pid}.gltf",
                   tier=piece.get("tier"), base=src_id)
        if piece.get("covers"):
            row["covers"] = piece["covers"]
        if piece.get("hold"):
            row["hold"] = piece["hold"]
        rows.append(row)
        rows.sort(key=lambda r: r["id"])
        json.dump(rows, open(ix_path, "w", encoding="utf-8"), indent=1)
        imp = out + ".import"
        if not os.path.exists(imp):
            ref = os.path.join(ROOT, "godot", "art", "people", "heroine_outfit_warden.gltf.import")
            keep_ = [l for l in open(ref, encoding="utf-8").read().splitlines() if not l.startswith(("uid=", "path=", "dest_files=", "source_file="))]
            open(imp, "w", encoding="utf-8", newline=chr(10)).write(chr(10).join(keep_) + chr(10))
    else:
        ix_path = os.path.join(ART, "armor_index.json")
        rows = json.load(open(ix_path, encoding="utf-8"))
        for r in rows:
            if r["id"] == pid:
                r["meshes"] = sorted(m["name"] for m in full)
        json.dump(rows, open(ix_path, "w", encoding="utf-8"), indent=1)
    npth = os.path.join(scratch, "numbers.json")
    old = json.load(open(npth, encoding="utf-8")) if (post and os.path.exists(npth)) else {}
    old["adorn"] = num
    json.dump(old if post else num, open(npth, "w", encoding="utf-8"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    return num


def main(argv):
    pid = argv[0]
    num = build(pid, post="--post" in argv)
    print("ADORN NUMBERS", json.dumps(num, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
    bad = []
    for k, v in (num.get("shell_vs_base") or {}).items():
        if not (v.get("bit_equal") or v.get("bit_equal_less_dropped")):
            bad.append(k)
    th = sum(v.get("through", 0) for v in (num.get("poses") or {}).values() if isinstance(v, dict))
    if bad or th:
        print("ADORN FAILED: shell not bit-equal %s, adornment through her skin %d" % (bad, th))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
