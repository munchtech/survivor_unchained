"""Make a generated mesh's triangles and normals face outward, in place, in a .glb (a baked NPC package's body/lod).

Generated meshes (TRELLIS busts and bodies, remeshed and decimated) come out with a fifth of their triangles wound
inward and vertex normals averaged across the disagreement. In Godot a back-wound triangle on a culled material is a
hole (the Ford-Warden's "black tar flakes" on his cheek were the hood's dark inside seen through such holes), and a
vertex normal pointing in shades its face as if lit from behind.

Per triangle, which side is outside is measured, not assumed: the mesh is looked at from many directions all round
(orthographic ray grids against every mesh in the file, the bind pose), and the side of a triangle that is seen first
from outside is its outside (a thin shell seen from both sides: the side seen more). A triangle never seen keeps
what its vertex normals say. Then:
  - triangles wound inward are rewound (two indices swapped);
  - a vertex normal pointing against the (now outward) faces around it is negated (its smoothing is kept).
Positions, UVs, skin and every other byte are unchanged; the index and normal buffers are rewritten in place.

  python tools/assets/glb_orient.py FILE.glb [--materials warden_head,generated,skin] [--rays 24] [--dry]

Needs numpy and trimesh with embree (pip embreex): about a minute for a body.
"""
import argparse, json, struct
import numpy as np
import trimesh

CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


class Glb:
    def __init__(self, path):
        self.raw = bytearray(open(path, "rb").read())
        n = struct.unpack("<I", self.raw[12:16])[0]
        self.j = json.loads(self.raw[20:20 + n])
        self.bin0 = 20 + n + 8

    def _where(self, i):
        a = self.j["accessors"][i]
        bv = self.j["bufferViews"][a["bufferView"]]
        dt = np.dtype(CT[a["componentType"]])
        nc = NC[a["type"]]
        off = self.bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride", 0) or dt.itemsize * nc
        return a, dt, nc, off, stride

    def acc(self, i):
        a, dt, nc, off, stride = self._where(i)
        raw = np.frombuffer(self.raw, np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * nc, offset=off)
        out = np.lib.stride_tricks.as_strided(raw, (a["count"], dt.itemsize * nc), (stride, 1)).copy().view(dt).reshape(a["count"], nc)
        return out

    def put(self, i, arr):
        a, dt, nc, off, stride = self._where(i)
        arr = np.ascontiguousarray(arr, dtype=dt).reshape(a["count"], nc)
        if stride == dt.itemsize * nc:
            self.raw[off:off + arr.nbytes] = arr.tobytes()
        else:
            for k in range(a["count"]):
                self.raw[off + k * stride:off + k * stride + dt.itemsize * nc] = arr[k].tobytes()

    def prims(self):
        for m in self.j["meshes"]:
            for p in m["primitives"]:
                yield self.j["materials"][p["material"]]["name"] if "material" in p else "", p


def fib_sphere(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = np.pi * (1 + 5 ** 0.5) * i
    return np.c_[np.cos(th) * np.sin(phi), np.cos(phi), np.sin(th) * np.sin(phi)]


def votes(scene, tri0, ntri, lo, hi, dirs, step):
    """Per triangle of [tri0, tri0+ntri) of the scene: sum over views from outside (orthographic, along each of dirs,
    over the box lo..hi at step metres) of +1 where its first-hit side faces the viewer, -1 where its back does."""
    v = np.zeros(ntri)
    seen = np.zeros(ntri)
    c = (lo + hi) / 2
    r = np.linalg.norm(hi - lo) / 2
    far = np.linalg.norm(scene.bounds[1] - scene.bounds[0]) + 1
    for d in dirs:
        a = np.cross(d, [0, 1, 0] if abs(d[1]) < 0.9 else [1, 0, 0]); a /= np.linalg.norm(a)
        b = np.cross(d, a)
        k = np.arange(-r, r, step)
        U, W = np.meshgrid(k, k)
        o = c + U.reshape(-1, 1) * a + W.reshape(-1, 1) * b - d * far
        dd = np.tile(d, (len(o), 1))
        ti = scene.ray.intersects_first(o, dd)
        ti = ti[(ti >= tri0) & (ti < tri0 + ntri)] - tri0
        s = -np.sign(scene.face_normals[ti + tri0] @ d)
        np.add.at(v, ti, s)
        np.add.at(seen, ti, 1)
    return v, seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("--materials", default="")
    ap.add_argument("--views", type=int, default=160)
    ap.add_argument("--step", type=float, default=0.002, help="ray spacing, metres (a body: 0.004)")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    g = Glb(a.glb)
    want = set(filter(None, a.materials.split(",")))
    prims = [(name, p) for name, p in g.prims() if "indices" in p and (not want or name in want)]
    every = [(name, p) for name, p in g.prims() if "indices" in p]
    # every mesh in the file is an occluder (a head's back sits inside the body's hood)
    V, F, o, first = [], [], 0, {}
    for _, p in every:
        first[id(p)] = sum(len(f) for f in F)
        P = g.acc(p["attributes"]["POSITION"]).astype(float)
        I = g.acc(p["indices"]).reshape(-1, 3).astype(np.int64)
        V.append(P); F.append(I + o); o += len(P)
    scene = trimesh.Trimesh(np.vstack(V), np.vstack(F), process=False)
    dirs = fib_sphere(a.views)
    for name, p in prims:
        P = g.acc(p["attributes"]["POSITION"]).astype(float)
        I = g.acc(p["indices"]).reshape(-1, 3).astype(np.int64)
        N = g.acc(p["attributes"]["NORMAL"]).astype(float) if "NORMAL" in p["attributes"] else None
        fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]])
        area = np.linalg.norm(fn, axis=1)
        fn /= np.maximum(area, 1e-12)[:, None]
        step = max(a.step, float(np.max(P.max(0) - P.min(0))) / 600)
        v, seen = votes(scene, first[id(p)], len(I), P.min(0), P.max(0), dirs, step)
        vote = np.sign((fn * N[I].mean(1)).sum(1)) if N is not None else np.ones(len(I))
        out = np.where(v > 0, 1, np.where(v < 0, -1, np.where(vote == 0, 1, vote)))
        flip = out < 0
        I2 = I.copy()
        I2[flip] = I2[flip][:, [0, 2, 1]]
        msg = f"{name}: {len(I)} tris, {flip.sum()} rewound ({(v == 0).sum()} unseen or tied, by their normals)"
        if N is not None:
            ofn = fn * out[:, None]
            acc = np.zeros_like(N)
            for k in range(3):
                np.add.at(acc, I[:, k], ofn * area[:, None])
            neg = (acc * N).sum(1) < 0
            N2 = N.copy()
            N2[neg] *= -1
            msg += f", {neg.sum()} of {len(N)} normals negated"
            # (a negated normal's tangent frame keeps its bitangent: the tangent's handedness flips with it)
            if "TANGENT" in p["attributes"]:
                T = g.acc(p["attributes"]["TANGENT"]).astype(np.float32)
                T[neg, 3] *= -1
        print(msg, flush=True)
        if not a.dry:
            g.put(p["indices"], I2.reshape(-1))
            if N is not None:
                g.put(p["attributes"]["NORMAL"], N2.astype(np.float32))
                if "TANGENT" in p["attributes"]:
                    g.put(p["attributes"]["TANGENT"], T)
    if not a.dry:
        open(a.glb, "wb").write(bytes(g.raw))
        print("wrote", a.glb)


if __name__ == "__main__":
    main()
