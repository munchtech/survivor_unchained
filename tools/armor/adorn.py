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
- `gild`: parts of the base's own shell (`parts`: rolled_rim, the cups' rolled edges; gore, the gore plate and its
  rolled edge) copied into `mat` `lift` out along their normals (never toward her), the steel kept under it: the tier's
  gilt rim and gore. Each copied vertex keeps its weights and shading data; faces turned to her are not copied. Kept
  in the gameplay LOD (from that LOD's own shell). Checked in the poses as the shell is: against her tucked skin.
- `paint` `etch_<name>`: the etched pattern as a film 0.25 mm over the plate in the shell's own mesh and material (or
  `ground`'s: a leather one draws it as a matte black fill, see etch()),
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
from carry_targets import closest  # noqa: E402
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
# (m: where the plate under it is itself under her tucked skin (the shell's own check reports that), an adornment is
# held to within the plate's own thickness of its outer face: a trim's foot is sunk 0.2 mm into it, and a 4 mm band's
# edge cuts the chord of a rolled edge's curve by a few tenths more)
SHELL_TOL = 0.0008
FOOT_R = 0.005                       # (m: an adornment vertex's foot, the deepest shell point within this of it)
GILT_TOL = 0.0001                    # (m: the nearest-skin measure's own noise between a gilt vertex and its steel, 0.25 mm apart)
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
    row = mats_table().get(name, {})
    if row.get("albedo_srgb"):
        # (r2, F2: blacksteel, the etch's blackened ground: a dark metal of its own colour (the metal shader draws a
        # texture's mean only), metallic, at the shader's satin roughness)
        from PIL import Image
        os.makedirs(TEX, exist_ok=True)
        f = os.path.join(TEX, f"{name}_diff.png")
        Image.fromarray(np.full((16, 16, 3), np.round(np.asarray(row["albedo_srgb"], float) * 255), np.uint8)).save(f)
        return {"name": name, "doubleSided": False,
                "pbrMetallicRoughness": {"baseColorTexture": {"index": tex(f"tex/{name}_diff.png")}, "metallicFactor": 1.0,
                                         "roughnessFactor": row.get("roughness", 0.45)}}
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


def fair(surf, row, width=0.012, rounds=3):
    """An inward row (closed) made fair along its line: averaged over `width` of its length and snapped back, so an
    offset round a tight corner of the rim doesn't fold into a kink."""
    p, f, b, n = row
    seg = np.linalg.norm(np.diff(np.vstack([p, p[:1]]), axis=0), axis=1).mean()
    k = max(1, int(round(width / 2 / max(seg, 1e-6))))
    for _ in range(rounds):
        q = sum(np.roll(p, i, 0) for i in range(-k, k + 1)) / (2 * k + 1)
        p, f, b, n = surf.snap(q, n)
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


def film_strip(surf, rim, d0, d1, step, na, sky, conv, lift=FILM, matte=False, edge_min=0.004):
    """A film on the plate between d0 and d1 in from a rim (the etch's bands, a trim's grooves)."""
    P0, O0, N0, s = rim_line(rim, step)
    rows = []
    for d in np.linspace(d0, d1, na):
        rows.append(fair(surf, inward(surf, P0, O0, N0, d)))
    ns = len(P0)
    P = np.stack([r[0] for r in rows], 1).reshape(-1, 3)
    N = np.stack([r[3] for r in rows], 1).reshape(-1, 3)
    F = np.stack([r[1] for r in rows], 1).ravel()
    B = np.stack([r[2] for r in rows], 1).reshape(-1, 3)
    T = fix_winding(P, grid_tris(ns, na, True), N)
    return film_from(surf, P, N, F, B, T, sky, conv, lift, matte, edge_min)


def film_from(surf, P, N, F, B, T, sky, conv, lift=FILM, matte=False, edge_min=0.004):
    """A film's vertex data from the plate under it: its sky times `sky`, its convexity `conv` (None: the plate's own),
    its edge distance at least `edge_min` (0.004: no edge polish on it; 0.021 and over: also clear of the metal
    shader's dirt band just inside a rim, 2-20 mm, which grimes the plate there to a part-dielectric matte)."""
    C = surf.at(surf.C, F, B)
    C[:, 0] = np.clip(C[:, 0] * sky, 0, 1)
    if matte:
        C[:, 2:4] = 0.0                        # (in a leather material: no stitch row, drawn matte)
    U1 = surf.at(surf.U1, F, B)
    U1[:, 0] = np.maximum(U1[:, 0], edge_min)
    if conv is not None:
        U1[:, 1] = conv
    return P + N * lift, N, surf.at(surf.U0, F, B), U1, C, surf.at(surf.W, F, B), T


PROFILES = {
    # (across -1..1, height 0..1): a flat-topped band with rounded shoulders and a short wall
    "gold_band": [(-1, 0), (-1, 0.55), (-0.86, 0.88), (-0.6, 1.0), (-0.2, 1.0), (0.2, 1.0), (0.6, 1.0), (0.86, 0.88), (1, 0.55), (1, 0)],
    "rolled": [(np.cos(a), np.sin(a)) for a in np.linspace(np.pi, 0, 9)],
    "rope": [(np.cos(a), np.sin(a)) for a in np.linspace(np.pi, 0, 9)],
    "filigree": [(-1, 0), (-1, 0.5), (-0.7, 0.8), (-0.35, 0.6), (0, 1.0), (0.35, 0.6), (0.7, 0.8), (1, 0.5), (1, 0)],
    # (r2, F1: a raised half-round bead, so it draws a lit line over a shadow line: a short foot wall, then the round)
    "bead": [(-1, 0)] + [(np.cos(a), 0.12 + 0.88 * np.sin(a)) for a in np.linspace(np.pi, 0, 9)] + [(1, 0)],
    # (a lighter bead for a long run of small rims: five points over the round)
    "bead_lo": [(-1, 0)] + [(np.cos(a), 0.12 + 0.88 * np.sin(a)) for a in np.linspace(np.pi, 0, 5)] + [(1, 0)],
}
LOD_PROFILES = {"bead": [(-1, 0)] + [(np.cos(a), 0.12 + 0.88 * np.sin(a)) for a in np.linspace(np.pi, 0, 4)] + [(1, 0)]}
LOD_PROFILES["bead_lo"] = LOD_PROFILES["bead"]


def trim_band(surf, rim, ad, step, leather, lod=False):
    """A swept band along a rim on the surface (see the module doc)."""
    prof = PROFILES[ad.get("profile", "gold_band")]
    if lod:
        prof = LOD_PROFILES.get(ad.get("profile"), [(-1, 0), (-1, 0.7), (-0.6, 1.0), (0.6, 1.0), (1, 0.7), (1, 0)])
    w, h, dc = ad.get("width", 0.005), ad.get("height", 0.0015), ad.get("inset", 0.0)
    P0, O0, N0, s = rim_line(rim, step)
    pc, fc, bc, nc = fair(surf, inward(surf, P0, O0, N0, dc))
    # (each section's own across direction: from a point a little further in)
    pi_, _, _, _ = fair(surf, inward(surf, P0, O0, N0, dc + w / 2))
    po_, _, _, _ = fair(surf, inward(surf, P0, O0, N0, max(dc - w / 2, 0.0)))
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


# ---------------------------------------------------------------------------------------- the gild --
def gild(m, sock, ad, nb, table, mat):
    """`gild`: parts of the base's own shell (`parts`: "rolled_rim", the cups' rolled edges; "gore", the gore plate and
    its rolled edge, not its rivets) copied into `mat`, `lift` out along their welded normals: a gilt skin over the
    steel, the base's shell untouched under it (a tier adds adornment only). Each copied vertex keeps its own weights
    and shading data (it rides and wears as the steel under it does). Faces turned toward her (their normal against
    the plate's outward one by more than `facing`) are not copied: hidden, and they would stand nearer her skin."""
    P = m["attrs"]["POSITION"][0].astype(np.float64)
    N = m["attrs"]["NORMAL"][0].astype(np.float64)
    T = m["tris"]
    tu = m["attrs"]["TEXCOORD_2"][0][:, 0] if "TEXCOORD_2" in m["attrs"] else np.zeros(len(P))
    lab = pl.parts(P, T)
    # (each rim's line, ten points to a segment, so a distance to it is to the line, not its points)
    dz = lambda a_: np.vstack([a_ + (np.roll(a_, -1, 0) - a_) * t for t in np.linspace(0, 1, 10, endpoint=False)])
    rp = np.vstack([dz(np.array(r["points"])) for r in sock["rims"].values()])
    rn = np.vstack([dz(np.array(r["normals"])) for r in sock["rims"].values()])
    rn /= np.maximum(np.linalg.norm(rn, axis=1, keepdims=True), 1e-12)
    rt = cKDTree(rp)
    g = sock["sockets"].get("gore")
    want = set(ad.get("parts", ["rolled_rim", "gore"]))
    facing = ad.get("facing", -0.3)
    fn = N[T].sum(1)
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-15)
    keep = np.zeros(len(T), bool)
    vref = np.zeros((len(P), 3))                              # (each copied vertex's plate outward: away from her)
    gv = np.zeros(len(P), bool)
    got = {}
    for c in np.unique(lab):
        sel = lab == c
        v = np.unique(T[sel])
        size = float(np.linalg.norm(np.ptp(P[v], 0)))
        if size < 0.02:
            continue                                           # (rivets, buckles' bits)
        d_rim = rt.query(P[v])[0]
        kind = None
        if "rolled_rim" in want and np.median(d_rim) < 0.004 and d_rim.max() < 0.006 and (np.abs(tu[v]) > 1e-6).mean() > 0.9:
            kind = "rolled_rim"
            ref = rn[rt.query(P[T[sel]].mean(1))[1]]
        elif "gore" in want and g is not None and np.linalg.norm(P[v].mean(0) - np.array(g["point"])) < 0.03 and size < 0.09:
            kind = "gore"
            ref = np.repeat(np.array(g["normal"])[None], int(sel.sum()), 0)
        if kind is None:
            continue
        # (the gore's rolled edge's walls toward the cups are not copied (`facing_gore`): they face her breasts across
        # the 1.5 mm gap, hidden under the cups' rims)
        ok = (fn[sel] * ref).sum(1) > (ad.get("facing_gore", 0.25) if kind == "gore" else facing)
        if kind == "gore":
            # (nor its corners tucked under the cups' rolled edges: there her breasts move against the rigid gore)
            ok &= rt.query(P[T[sel]].reshape(-1, 3))[0].reshape(-1, 3).min(1) > ad.get("gore_clear", 0.004)
        idx = np.nonzero(sel)[0][ok]
        keep[idx] = True
        vref[T[idx].ravel()] = np.repeat(ref[ok], 3, 0)
        gv[T[idx].ravel()] = kind == "gore"
        got.setdefault(kind, {"parts": 0, "tris": 0, "dropped_facing_her": 0})
        got[kind]["parts"] += 1
        got[kind]["tris"] += int(ok.sum())
        got[kind]["dropped_facing_her"] += int((~ok).sum())
    if not keep.any():
        return None, got
    Tk = T[keep]
    used, inv = np.unique(Tk.ravel(), return_inverse=True)
    # (welded normals: a hard edge's split vertices move together, so no crack opens in the gilt)
    _, wi = np.unique(np.round(P[used] / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    wi = wi.ravel()
    ns = np.zeros((wi.max() + 1, 3))
    np.add.at(ns, wi, N[used])
    ns = ns[wi] / np.maximum(np.linalg.norm(ns[wi], axis=1, keepdims=True), 1e-12)
    # (never lifted toward her: a normal turned her way (a rolled edge's underside, kept where its face is not) loses
    # that part, so the gilt stands out sideways there, never nearer her than the steel it covers)
    vr = vref[used]
    vr /= np.maximum(np.linalg.norm(vr, axis=1, keepdims=True), 1e-12)
    k_ = np.minimum((ns * vr).sum(1, keepdims=True) - 0.3, 0.0)     # (at least 0.3 of it outward)
    dn = ns - k_ * vr
    if ad.get("gore_straight", True):
        dn[gv[used]] = vr[gv[used]]                           # (the gore's gilt straight out off her sternum)
    dn /= np.maximum(np.linalg.norm(dn, axis=1, keepdims=True), 1e-12)
    Pn = P[used] + dn * ad.get("lift", 0.00025)
    k = table.get(mat, {}).get("repeats", 3) / max(table.get(m["mat"], {}).get("repeats", 2.5), 1e-6)
    U0 = m["attrs"]["TEXCOORD_0"][0][used].astype(np.float64) * k
    U1 = m["attrs"]["TEXCOORD_1"][0][used].astype(np.float64)
    C = colour(m)[used]
    W = dense(m, nb)[used]
    return (Pn, N[used], U0, U1, C, W, inv.reshape(-1, 3), P[used]), got


# ---------------------------------------------------------------------------------------- the etch --
def vine_chart(L, ad):
    """The running vine on a band's chart, in mm (u along the band's centre line 0..L, closed; v across, 0 the centre):
    a wavy stem (a whole number of waves round the loop, so it closes without a kink) and a tapering leaf off each
    crest into the bay under it (so the leaves alternate sides). Returns the outline points (n, 2) and inside(pts)."""
    from matplotlib.path import Path
    A, hw = ad.get("amp", 2.2), ad.get("stem", 1.4) / 2
    nw = max(2, int(round(L / ad.get("wave", 14.0))))
    k = 2 * np.pi / (L / nw)

    def edges(n):
        # (the stem's edges: its centre offset along its own normal)
        u = np.arange(n) * L / n
        t = np.c_[np.ones(n), A * k * np.cos(k * u)]
        t /= np.linalg.norm(t, axis=1, keepdims=True)
        c, nr = np.c_[u, A * np.sin(k * u)], np.c_[-t[:, 1], t[:, 0]]
        return c + nr * hw, c - nr * hw
    hi_d, lo_d = edges(int(L / 0.05))

    def side(e, u):
        o = np.argsort(e[:, 0])
        x, y = e[o, 0], e[o, 1]
        return np.interp(u % L, np.r_[x[-1] - L, x, x[0] + L], np.r_[y[-1], y, y[0]])

    def in_stem(p, m=0.0):
        return (p[:, 1] < side(hi_d, p[:, 0]) - m) & (p[:, 1] > side(lo_d, p[:, 0]) + m)
    leaves = []
    ll, wl = hw + ad.get("leaf", 3.0), ad.get("leaf_width", 1.3)
    a0 = np.radians(ad.get("leaf_lean", -5.0))
    a1 = a0 + np.radians(ad.get("leaf_curl", 30.0))
    for j in range(0, 2 * nw, int(ad.get("leaf_every", 1))):
        s = 1.0 if j % 2 == 0 else -1.0                      # (the crest's side: its leaf goes to the other)
        uc = (np.pi / 2 + j * np.pi) / k
        x = np.linspace(0, 1, max(8, int(np.ceil(ll / 0.35))) + 1)
        th = a0 + (a1 - a0) * x
        d = np.c_[np.sin(th), -s * np.cos(th)]
        c = np.array([uc, s * A]) + np.r_[[[0, 0]], np.cumsum((d[1:] + d[:-1]) / 2 * np.diff(x)[:, None] * ll, 0)]
        nr = np.c_[-d[:, 1], d[:, 0]]
        w = wl / 2 * np.sin(np.pi * x) ** 0.7
        poly = np.vstack([c[:-1] + nr[:-1] * w[:-1, None], c[-1:], (c[1:-1] - nr[1:-1] * w[1:-1, None])[::-1]])
        leaves.append((poly, Path(np.vstack([poly, poly[:1]]))))

    def in_leaf(p):
        r = np.zeros(len(p), bool)
        q = np.c_[p[:, 0] % L, p[:, 1]]
        for poly, pa in leaves:
            lo, hi = poly.min(0) - 0.1, poly.max(0) + 0.1
            box = (q[:, 0] > lo[0]) & (q[:, 0] < hi[0]) & (q[:, 1] > lo[1]) & (q[:, 1] < hi[1])
            if box.any():
                r[box] |= pa.contains_points(q[box])
        return r
    inside = lambda p: in_stem(p) | in_leaf(p)
    hi, lo = edges(int(np.ceil(L / 0.7)))
    stem = np.vstack([hi, lo])
    stem = stem[~in_leaf(stem)]
    lf = np.vstack([p for p, _ in leaves])
    lf = lf[~in_stem(lf, 0.03)]
    return np.vstack([stem, lf]), inside, {"waves": nw, "leaves": len(leaves)}


def vine_band(surf, rim, d0, d1, ad, sky, conv, lift, matte=False, edge_min=0.004):
    """The band's blackened ground (a film) between d0 and d1 in from a rim, with gaps where the vine runs: triangulated
    on the band's chart (u, v), then laid on the plate by its inward rows. And the vine (r3, F2): the gaps' own film, the
    same triangulation's other triangles (so they meet the ground's edges exactly), returned to go in the shell's own
    steel with the cup's open-plate data (its sky, its convexity, clear of the rim's dirt band), so it is lit as the cup
    is: the bare plate under the gaps lies in the shader's dirt band inside the rim and read as a matte pale line."""
    from scipy.spatial import Delaunay
    P0, O0, N0, _ = rim_line(rim, 0.001)
    nr = int(np.ceil((d1 - d0) / 0.00075)) + 1
    nr += 1 - nr % 2                                         # (odd: a row on the centre line)
    dr = np.linspace(d0, d1, nr)
    rows = [fair(surf, inward(surf, P0, O0, N0, d)) for d in dr]
    G = np.stack([r[0] for r in rows], 1)                    # (ns, nr, 3)
    GN = np.stack([r[3] for r in rows], 1)
    ns = len(G)
    cen = G[:, nr // 2]
    uc = np.r_[0, np.cumsum(np.linalg.norm(np.roll(cen, -1, 0) - cen, axis=1) * 1000)]   # (mm, the loop closed)
    L, hb = uc[-1], (d1 - d0) / 2 * 1000
    out, inside, st = vine_chart(L, ad)
    ne = int(np.ceil(L / 2.0))
    eu = np.arange(ne) * L / ne
    pts = np.vstack([out, np.c_[eu, np.full(ne, hb)], np.c_[eu, np.full(ne, -hb)]])
    pts[:, 0] %= L
    idx = np.arange(len(pts))
    a, b = pts[:, 0] < 6, pts[:, 0] > L - 6
    allp = np.vstack([pts, pts[a] + [L, 0], pts[b] - [L, 0]])
    alli = np.r_[idx, idx[a], idx[b]]
    T = Delaunay(allp).simplices
    c = allp[T].mean(1)
    keep = (c[:, 0] >= 0) & (c[:, 0] < L) & (np.abs(c[:, 1]) < hb)
    vin = keep.copy()
    ins = inside(c[keep])
    keep[keep] &= ~ins
    vin[vin] &= ins
    TV = alli[T[vin]]
    T = alli[T[keep]]
    # (a sound strip: no edge in more than two triangles, none degenerate)
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    if cnt.max() > 2 or (T[:, 0] == T[:, 1]).any() or (T[:, 1] == T[:, 2]).any() or (T[:, 0] == T[:, 2]).any():
        raise SystemExit(f"ADORN: vine band not a sound strip ({int((cnt > 2).sum())} edges in 3+ triangles)")
    # (onto the plate: bilinear in the rows, then snapped)
    ci = np.interp(pts[:, 0], uc, np.arange(ns + 1))
    i0 = np.floor(ci).astype(int)
    fi = (ci - i0)[:, None]
    i0, i1 = i0 % ns, (i0 + 1) % ns
    ri = np.clip(np.interp(d0 + (pts[:, 1] + hb) / 1000, dr, np.arange(nr)), 0, nr - 1)
    j0 = np.minimum(np.floor(ri).astype(int), nr - 2)
    fj = (ri - j0)[:, None]

    def bil(X):
        return ((X[i0, j0] * (1 - fj) + X[i0, j0 + 1] * fj) * (1 - fi)
                + (X[i1, j0] * (1 - fj) + X[i1, j0 + 1] * fj) * fi)
    p, f, bb, n = surf.snap(bil(G), bil(GN))
    st.update(chart_mm=[round(float(L), 1), round(float(2 * hb), 2)], ground_tris=int(len(T)), vine_tris=int(len(TV)),
              boundary_edges=int((cnt == 1).sum()))
    ground = film_from(surf, p, n, f, bb, fix_winding(p, T, n), sky, conv, lift, matte, edge_min)
    vine = film_from(surf, p, n, f, bb, fix_winding(p, TV, n), 1.0, None, lift, False, ad.get("vine_edge", 0.03))
    return ground, vine, st


def matte_ground(ad):
    return ad.get("ground") is not None and mats_table().get(ad["ground"], {}).get("kind") == "leather"


def etch(surf, sock, ad, lod):
    """The etched pattern (`pattern` etch_band_vine): on each cup a Renaissance blackened band inside the rim's rivets
    (`band`, in from the rim, m): its ground a dark rough film with a running vine left bright in it (gaps in the
    film: a wavy stem, a leaf off each crest), framed each side by a fine etched line (`lines`). The gameplay LOD
    keeps the dark band only (no vine, no lines): a darker border at the play camera. `ground` names the material its
    films go in (default the shell's): a leather one draws them as a matte black fill (the metal kind darkens a film
    by its sky to only ~0.8 of the bare plate's luminance at the close-up; Renaissance blackening is a matte fill
    anyway); `sky` its sky (x the plate's)."""
    name = ad.get("pattern", "etch_band_vine")
    if name != "etch_band_vine":
        raise SystemExit(f"ADORN: no etched pattern {name!r} (etch_band_vine)")
    k = float(ad.get("strength", 1.0))
    sky = 1 - (1 - ad.get("sky", ETCH_SKY)) * k
    conv = ad.get("conv", ETCH_CONV)
    lift = FILM * (1.6 if lod else 1.0)
    mt = matte_ground(ad)
    em = ad.get("ground_edge", 0.004)
    parts, vines, stats = [], [], {"bands": 0, "lines": 0}
    band = ad.get("band", [0.0122, 0.0212])
    lines = ad.get("lines", [[0.0106, 0.0116], [0.0218, 0.0228]])
    for rn in rim_names(sock, ad.get("rim", "cup_rim")):
        rim = sock["rims"][rn]
        if lod:
            parts.append(film_strip(surf, rim, band[0], band[1], 0.006, 3, sky, conv, lift, mt, em))
        else:
            film, vine, st = vine_band(surf, rim, band[0], band[1], ad, sky, conv, lift, mt, em)
            parts.append(film)
            vines.append(vine)
            stats.setdefault("vine", []).append(st)
            for l0, l1 in lines:
                # (a hair higher: the inner line crosses where the left cup's plate is within 0.3 mm of her skin
                # with the arms overhead)
                parts.append(film_strip(surf, rim, l0, l1, 0.002, 2, sky, conv, lift * 1.2, mt, em))
                stats["lines"] += 1
        stats["bands"] += 1
    return parts, vines, stats


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
TRIM_IDS = set()


def pose_check(shell_id, model, new_by_mesh, base_full):
    """Every new vertex skinned into each test pose (her skinning matrices from the shell's build, poses.npz), and
    its signed distance to her posed skin there: through if under it. The shell's own vertices skinned the same way
    must land on the build's posed shell (a check of the matrices). A gilt vertex (`gild`, a skin on the shell) is held
    to the shell's own standard: against her skin tucked as the game draws it (poses.npz's tuck), or, from an older
    poses.npz without it, by how far it stands out of the steel it covers where that steel lies under her skin."""
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

        def pose(m, sel=None, P_=None):
            P = m["attrs"]["POSITION"][0].astype(np.float64)
            J = m["attrs"]["JOINTS_0"][0].astype(np.int64)
            W = pl.floats(*m["attrs"]["WEIGHTS_0"]).astype(np.float64)
            if sel is not None:
                P, J, W = P[sel], J[sel], W[sel]
            if P_ is not None:
                P = P_
            Ph = np.c_[P, np.ones(len(P))]
            return np.einsum("nk,nkij,nj->ni", W, M[J], Ph)[:, :3]

        r = {"new_vertices": 0, "through": 0, "min_clear_mm": None}
        clear = []
        gilt_tucked = 0

        tk = z[f"{pn}__tuck"].astype(np.float64) if f"{pn}__tuck" in z.files else None
        tk = None if tk is None else 0.010 * np.where(tk > 0.973, 1.0, tk)     # (as the base's check: her skin drawn in)

        def signed(q, tucked=False, near=None, back=False):
            d, j = st.query(q, k=6) if near is None else near
            # (the signed distance off her skin: along the normal of the nearest skin points)
            sd = ((q[:, None] - skin[j]) * skin_n[j]).sum(2)
            if tucked:
                sd = sd + tk[j]
            out_ = np.where(d[:, :1] < 0.03, np.median(sd, 1)[:, None], 1.0)[:, 0]
            return (out_, (d, j)) if back else out_
        # (the shell posed: every new vertex's foot on it, its nearest shell point)
        bq = pose(base_full)
        bqt = cKDTree(bq)
        sall = signed(bq, tucked=True) if tk is not None else None
        for m, sel, src, *tmk in new_by_mesh:
            sd = signed(pose(m, sel))
            if tmk and tmk[0].any() and tk is not None:
                # (a trim rides the shell's own rolled edge, which the game draws against her skin tucked in: held to the
                # same standard as the shell and its gilt)
                sd[tmk[0]] = signed(pose(m, sel[tmk[0]]), tucked=True)
            g = ~np.isnan(src[:, 0])
            if g.any() and tk is not None:
                # (the gilt is a skin on the shell: held to the shell's own standard, her skin tucked as the game draws it)
                ss, nr = signed(pose(m, sel[g], src[g]), back=True)
                gilt_tucked += int((ss < 0).sum())
                sg = signed(pose(m, sel[g]), near=nr)        # (on the steel's own nearest skin: their difference is the lift's)
                st_ = signed(pose(m, sel[g]), tucked=True)
                # (through only if it is under her tucked skin and deeper in her than the steel it covers: where the
                # nearest-skin measure puts the base's own rolled edge under her (side-on at her flank, where the
                # base's ray check finds it clear), the gilt over it is no worse than the steel)
                rel = sg - np.minimum(ss, 0.0)
                if os.environ.get("ADORN_DIAG") and (st_ < 0).any():
                    b_ = (st_ < 0) & (rel + GILT_TOL < 0)
                    say("GILT DIAG2", pn, int(b_.sum()), "rel_mm", np.round(rel[b_][:6] * 1000, 3).tolist(), "steel", np.round(ss[b_][:6] * 1000, 2).tolist(), "tucked", np.round(st_[b_][:6] * 1000, 2).tolist())
                sd[g] = np.maximum(st_, rel + GILT_TOL)
                if os.environ.get("ADORN_DIAG"):
                    say("GILT DIAG3", pn, m["name"], "gilt through", int((sd[g] < 0).sum()), "other through", int((sd[~g] < 0).sum()),
                        "gilt at", np.round(src[g][sd[g] < 0][:5], 4).tolist(), "other at", np.round(m["attrs"]["POSITION"][0][sel[~g]][sd[~g] < 0][:5], 4).tolist(), "other sd mm", np.round(sd[~g][sd[~g] < 0][:5] * 1000, 2).tolist())
            elif g.any():
                ss = signed(pose(m, sel[g], src[g]))
                if os.environ.get("ADORN_DIAG"):
                    bad_ = (sd[g] - np.minimum(ss, 0.0)) < 0
                    if bad_.any():
                        say("GILT DIAG", pn, int(bad_.sum()), "sd", np.round(sd[g][bad_][:8] * 1000, 2).tolist(), "steel", np.round(ss[bad_][:8] * 1000, 2).tolist(),
                            "at", np.round(src[g][bad_][:4], 4).tolist())
                sd[g] = sd[g] - np.minimum(ss, 0.0)
                gilt_tucked += int((ss < 0).sum())
            if tk is not None:
                # (the shell's own standard for all of it, as the gilt's: a trim, a film or an element on the plate is
                # through only if it lies under her tucked skin AND deeper in her than the shell at its foot, both
                # measured on its own nearest skin; where the plate itself lies under her (tucked by the shell's own rule, or
                # not: the shell's check is its own), what rides on it is no worse than the plate)
                q_ = pose(m, sel)
                # (its foot: the deepest in her of the shell's points within FOOT_R of it, the plate under a band or a
                # rivet rather than the rolled edge beside it standing proud)
                dk, ik = bqt.query(q_, k=16, distance_upper_bound=FOOT_R)
                ik = np.where(np.isfinite(dk), ik, bqt.query(q_)[1][:, None])
                foot = np.take_along_axis(ik, np.argmin(sall[ik], 1)[:, None], 1)[:, 0]
                sv, nv = signed(q_, tucked=True, back=True)
                sf = signed(bq[foot], tucked=True, near=nv)
                # (and the closest place on the shell's faces: its plates are coarse, their points far apart)
                _, cf, cb = closest(q_, bq, np.asarray(base_full["tris"]).reshape(-1, 3), k=24)
                cp_ = (bq[np.asarray(base_full["tris"]).reshape(-1, 3)[cf]] * cb[:, :, None]).sum(1)
                sf = np.minimum(sf, signed(cp_, tucked=True, near=nv))
                sd = np.maximum(sd, sv - np.minimum(sf, 0.0) + np.where(sf < 0, SHELL_TOL, GILT_TOL))
                r["held_to_shell"] = r.get("held_to_shell", 0) + int((sf < 0).sum())
            clear.append(sd)
        cl = np.concatenate(clear) if clear else np.zeros(0)
        r["new_vertices"] = int(len(cl))
        r["through"] = int((cl < 0).sum())
        r["min_clear_mm"] = round(float(cl.min() * 1000), 2) if len(cl) else None
        r["gilt_on_tucked_steel"] = gilt_tucked
        sh = z[f"{pn}__shell"]
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
            obst = leather
            pz = os.path.join(ROOT, ".shots", "armor2", "build", shell_id, "poses.npz")
            if ad.get("clear_arm", True) and os.path.exists(pz):
                # (and her arm: her skin in each test pose, where it comes over the plate (as a strap's underside
                # lowers it); her skin under the plate lies below the band's foot and is passed over)
                z_ = np.load(pz)
                obst = np.vstack([leather] + [z_[f"{str(n_)}__skin"] for n_ in z_["names"]])
            for rn in rim_names(sock, ad["rim"]):
                rim = sock["rims"][rn]
                tb = trim_band(S_full, rim, ad, ad.get("step", 0.0022), obst)
                t_ = (tb["P"], tb["N"], tb["U0"], tb["U1"], tb["C"], tb["W"], tb["T"])
                TRIM_IDS.add(id(t_))
                full_new.setdefault(mat, []).append(t_)
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
                    tl = trim_band(S_lod, rim, ad, ad.get("lod_step", 0.006), obst, lod=True)
                    lod_new.setdefault(mat, []).append((tl["P"], tl["N"], tl["U0"], tl["U1"], tl["C"], tl["W"], tl["T"]))
        elif kind == "gild":
            part, got = gild(shell_full, sock, ad, nb, table, mat)
            st = {"mat": mat, "lift_mm": ad.get("lift", 0.00025) * 1000, "full": got}
            if part is not None:
                full_new.setdefault(mat, []).append(part)
            if shell_lod is not None and ad.get("lod", True):
                lpart, lgot = gild(shell_lod, sock, ad, nb, table, mat)
                st["lod1"] = lgot
                if lpart is not None:
                    lod_new.setdefault(mat, []).append(lpart)
            stats.setdefault("gild", []).append(st)
        elif kind == "paint":
            parts, vines, st = etch(S_full, sock, ad, False)
            gm = ad.get("ground", shell_full["mat"])
            full_new.setdefault(gm, []).extend(parts)
            # (the vine in the shell's own mesh and steel: no draw of its own)
            full_new.setdefault(shell_full["mat"], []).extend(vines)
            st["tris"] = int(sum(len(p[6]) for p in parts))
            st["vine_tris"] = int(sum(len(p[6]) for p in vines))
            if S_lod is not None:
                lparts, _, lst = etch(S_lod, sock, ad, True)
                lod_new.setdefault(gm, []).extend(lparts)
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
                # (a gilt vertex's steel under it, for the pose check: NaN for the rest)
                src = np.concatenate([p[7] if len(p) > 7 else np.full((len(p[0]), 3), np.nan) for p in parts if len(p[0])])
                tm_ = np.concatenate([np.full(len(p[0]), id(p) in TRIM_IDS) for p in parts if len(p[0])])
                new_sel.append((m, np.arange(n0, len(m["attrs"]["POSITION"][0])), src, tm_))
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
        if piece.get("replaces"):
            row["replaces"] = piece["replaces"]      # (a calling row id: ArmorIndex.Calling wears this piece in its place)
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
