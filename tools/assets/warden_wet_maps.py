"""The Ford-Warden's wet-pass data maps (shaders/warden_wet.gdshader), baked from his package's bind pose.

His textures are an atlas of tiny charts, so nothing in UV space knows what is face, beard or shin. These maps carry
that, per surface, in the surface's own UVs (1024, RGBA, gutters dilated):
  R  silt: 1 below his tide line (bind height TIDE m, wobbled +-WOBBLE m by 3D noise so it is a ragged line), 0 above,
     a soft 2-3 cm edge (the shader draws the muddy band on the edge and dulls the cloth below);
  G  occlusion: the share of the outward hemisphere (rays against every mesh, within 0.3 m) that is blocked, so the
     hood's inside and the face deep in it can go dark while the beard and the hood's outside keep their light;
  B  beard (head only): pale, in the hood's opening and below the beard's top line;
  A  face (head only): the pale skin above that line (brow, eyes, cheekbones, nose).

  python tools/assets/warden_wet_maps.py [PKG_DIR] [--size 1024] [--tide 0.42]
Writes PKG_DIR/wet_generated.png and (a TRELLIS-head package only) PKG_DIR/wet_head.png.
"""
import argparse, io, json, os, struct
import numpy as np
import trimesh
from PIL import Image
from scipy import ndimage

CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
BEARD_TOP = 1.600  # the beard below this line on the face (bind, metres), rising 0.4 m/m toward the cheeks


class Glb:
    def __init__(self, path):
        b = open(path, "rb").read()
        n = struct.unpack("<I", b[12:16])[0]
        self.j = json.loads(b[20:20 + n])
        self.bin = b[20 + n + 8:]

    def acc(self, i):
        a = self.j["accessors"][i]
        bv = self.j["bufferViews"][a["bufferView"]]
        dt = np.dtype(CT[a["componentType"]])
        nc = NC[a["type"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        st = bv.get("byteStride", 0) or dt.itemsize * nc
        raw = np.frombuffer(self.bin, np.uint8, count=st * (a["count"] - 1) + dt.itemsize * nc, offset=off)
        out = np.lib.stride_tricks.as_strided(raw, (a["count"], dt.itemsize * nc), (st, 1)).copy().view(dt).reshape(a["count"], nc)
        if a.get("normalized") and dt != np.float32:
            out = out.astype(np.float32) / np.iinfo(dt).max
        return out

    def prim(self, mat):
        for m in self.j["meshes"]:
            for p in m["primitives"]:
                if self.j["materials"][p["material"]]["name"] == mat:
                    d = {k: self.acc(v) for k, v in p["attributes"].items()}
                    d["idx"] = self.acc(p["indices"]).reshape(-1, 3).astype(np.int64)
                    d["mat"] = self.j["materials"][p["material"]]
                    return d

    def image(self, tex):
        im = self.j["images"][self.j["textures"][tex]["source"]]
        bv = self.j["bufferViews"][im["bufferView"]]
        o = bv.get("byteOffset", 0)
        return Image.open(io.BytesIO(self.bin[o:o + bv["byteLength"]])).convert("RGB")


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noise3(p, scale, seed=3):
    """Smooth value noise in 3D, -1..1."""
    rng = np.random.default_rng(seed)
    g = rng.uniform(-1, 1, (64, 64, 64))
    q = p / scale
    i = np.floor(q).astype(int)
    f = q - i
    f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + w * g[(i[:, 0] + dx) % 64, (i[:, 1] + dy) % 64, (i[:, 2] + dz) % 64]
    return out


def occlusion(scene, P, N, k=32, reach=0.3, seed=5):
    rng = np.random.default_rng(seed)
    d = rng.normal(size=(len(P), k, 3))
    d /= np.linalg.norm(d, axis=2, keepdims=True)
    s = np.sign((d * N[:, None]).sum(2, keepdims=True))
    d = d * np.where(s == 0, 1, s) + N[:, None] * 0.3
    d /= np.linalg.norm(d, axis=2, keepdims=True)
    o = np.repeat(P + N * 1e-3, k, 0)
    dd = d.reshape(-1, 3)
    blocked = np.zeros(len(o), bool)
    for a in range(0, len(o), 500000):
        loc, ri, _ = scene.ray.intersects_location(o[a:a + 500000], dd[a:a + 500000], multiple_hits=False)
        near = np.linalg.norm(loc - o[a:a + 500000][ri], axis=1) < reach
        blocked[a + ri[near]] = True
    return blocked.reshape(-1, k).mean(1)


def raster(uv, idx, vals, size):
    """Per-vertex values (n, c) into a size x size map over the UV triangles (glTF UV: v down), gutters dilated."""
    c = vals.shape[1]
    out = np.zeros((size, size, c), np.float32)
    have = np.zeros((size, size), bool)
    px = uv * size - 0.5
    for t in idx:
        a, b, cc = px[t[0]], px[t[1]], px[t[2]]
        x0, y0 = np.floor(np.minimum(np.minimum(a, b), cc)).astype(int)
        x1, y1 = np.ceil(np.maximum(np.maximum(a, b), cc)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        den = (b[1] - cc[1]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[1] - cc[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - cc[1]) * (X - cc[0]) + (cc[0] - b[0]) * (Y - cc[1])) / den
        w1 = ((cc[1] - a[1]) * (X - cc[0]) + (a[0] - cc[0]) * (Y - cc[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if not m.any():
            continue
        v = w0[m, None] * vals[t[0]] + w1[m, None] * vals[t[1]] + w2[m, None] * vals[t[2]]
        out[Y[m], X[m]] = v
        have[Y[m], X[m]] = True
    # gutters: nearest covered texel
    _, (iy, ix) = ndimage.distance_transform_edt(~have, return_indices=True)
    return out[iy, ix]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkg", nargs="?", default=os.path.join(os.path.dirname(__file__), "..", "..", "godot", "art", "npc", "ford_warden"))
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--tide", type=float, default=0.42)
    ap.add_argument("--wobble", type=float, default=0.035)
    a = ap.parse_args()
    g = Glb(os.path.join(a.pkg, "body.glb"))
    # (Warden 5: the as-generated Meshy package has no grafted warden_head or base skin; the body map is made alone and
    #  wet_head.png is not written, so the beard/face channels stay zero)
    parts = {m: q for m in ("generated", "warden_head", "skin") if (q := g.prim(m)) is not None}
    V, F, o = [], [], 0
    for p in parts.values():
        V.append(p["POSITION"].astype(float)); F.append(p["idx"] + o); o += len(p["POSITION"])
    scene = trimesh.Trimesh(np.vstack(V), np.vstack(F), process=False)
    for mat, out in (("generated", "wet_generated.png"), ("warden_head", "wet_head.png")):
        if mat not in parts:
            continue
        p = parts[mat]
        P = p["POSITION"].astype(float)
        N = p["NORMAL"].astype(float)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
        uv = p["TEXCOORD_0"].astype(float)
        h = P[:, 1] + a.wobble * noise3(P, 0.09) + 0.01 * noise3(P, 0.02, 9)
        silt = smoothstep(a.tide + 0.012, a.tide - 0.012, h)
        occ = occlusion(scene, P, N)
        beard = np.zeros(len(P))
        face = np.zeros(len(P))
        if mat == "warden_head":
            col = np.asarray(g.image(p["mat"]["pbrMetallicRoughness"]["baseColorTexture"]["index"]), np.float32) / 255
            s = col.shape[0]
            cv = col[np.clip((uv[:, 1] * s).astype(int), 0, s - 1), np.clip((uv[:, 0] * s).astype(int), 0, s - 1)]
            pal = smoothstep(0.12, 0.22, cv.max(1))  # (the re-baked head is darker than the bust warden_head.py classed)
            x, y, z = P[:, 0], P[:, 1], P[:, 2]
            # inside the hood's opening: not its crown, not its sides
            front = smoothstep(0.11, 0.08, np.abs(x)) * smoothstep(0.03, 0.07, z) * smoothstep(1.715, 1.69, y)
            pale_front = pal * front
            # the beard's top: under the nose, rising toward the cheeks (measured on the front check: the
            # moustache's top 1.604 m, the cheek beard's ~1.615; warden_head.py's NOSE_Z line is under the eyes)
            line = BEARD_TOP + 0.4 * np.maximum(np.abs(x) - 0.02, 0)
            below = smoothstep(line + 0.006, line - 0.006, y)
            beard = pale_front * below
            face = pale_front * (1 - below)
            # smooth over the mesh's edges
            e = np.r_[p["idx"][:, [0, 1]], p["idx"][:, [1, 2]], p["idx"][:, [2, 0]]]
            for _ in range(4):
                for f in (beard, face):
                    acc = np.zeros(len(P)); cnt = np.zeros(len(P))
                    np.add.at(acc, e[:, 0], f[e[:, 1]]); np.add.at(cnt, e[:, 0], 1)
                    np.add.at(acc, e[:, 1], f[e[:, 0]]); np.add.at(cnt, e[:, 1], 1)
                    f[:] = 0.5 * f + 0.5 * acc / np.maximum(cnt, 1)
        vals = np.c_[silt, occ, beard, face].astype(np.float32)
        m = raster(uv, p["idx"], vals, a.size)
        Image.fromarray((np.clip(m, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(a.pkg, out))
        print(f"{out}: silt {silt.mean():.3f} of verts, occlusion mean {occ.mean():.2f}, beard {(beard > 0.5).mean():.3f}, face {(face > 0.5).mean():.3f}")


if __name__ == "__main__":
    main()
