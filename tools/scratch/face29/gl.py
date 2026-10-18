"""Minimal glTF/GLB reader: skinned mesh positions at the file's skeleton's rest, as Godot computes them when a mesh's
skin is bound by joint NAME onto another file's skeleton (People.HerHair: the hair's inverse binds, her bones' rests)."""
import json, os, struct
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}

class G:
    def __init__(self, path):
        self.path = path
        if path.endswith(".glb"):
            b = open(path, "rb").read()
            n = struct.unpack_from("<I", b, 12)[0]
            self.j = json.loads(b[20:20 + n]); o = 20 + n
            m = struct.unpack_from("<I", b, o)[0]; self.bin = [b[o + 8:o + 8 + m]]
        else:
            self.j = json.load(open(path, encoding="utf-8"))
            self.bin = [open(os.path.join(os.path.dirname(path), x["uri"]), "rb").read() for x in self.j["buffers"]]
        self.world = {}
        par = {}
        for i, nd in enumerate(self.j["nodes"]):
            for c in nd.get("children", []): par[c] = i
        self.par = par
        for i in range(len(self.j["nodes"])): self.W(i)
        self.byname = {nd.get("name", ""): i for i, nd in enumerate(self.j["nodes"])}

    def local(self, i):
        nd = self.j["nodes"][i]
        if "matrix" in nd: return np.array(nd["matrix"], float).reshape(4, 4).T
        t = np.array(nd.get("translation", [0, 0, 0]), float); r = nd.get("rotation", [0, 0, 0, 1]); s = np.array(nd.get("scale", [1, 1, 1]), float)
        x, y, z, w = r
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        M = np.eye(4); M[:3, :3] = R * s; M[:3, 3] = t; return M

    def W(self, i):
        if i not in self.world:
            self.world[i] = (self.W(self.par[i]) if i in self.par else np.eye(4)) @ self.local(i)
        return self.world[i]

    def acc(self, a):
        A = self.j["accessors"][a]; bv = self.j["bufferViews"][A["bufferView"]]
        dt = CT[A["componentType"]]; nc = NC[A["type"]]
        off = bv.get("byteOffset", 0) + A.get("byteOffset", 0); stride = bv.get("byteStride", 0)
        buf = self.bin[bv.get("buffer", 0)]; isz = np.dtype(dt).itemsize * nc
        if stride and stride != isz:
            raw = np.frombuffer(buf, np.uint8, count=stride * (A["count"] - 1) + isz, offset=off)
            idx = np.arange(A["count"])[:, None] * stride + np.arange(isz)[None, :]
            arr = raw[idx].copy().view(dt).reshape(A["count"], nc)
        else:
            arr = np.frombuffer(buf, dt, count=A["count"] * nc, offset=off).reshape(A["count"], nc)
        if A.get("normalized"): arr = arr.astype(float) / np.iinfo(dt).max
        return arr

    def meshes(self):
        """(node name, mesh name, primitive index, material name, positions, joints, weights, skin index, indices)."""
        out = []
        for i, nd in enumerate(self.j["nodes"]):
            if "mesh" not in nd: continue
            me = self.j["meshes"][nd["mesh"]]
            for k, pr in enumerate(me["primitives"]):
                at = pr["attributes"]
                P = self.acc(at["POSITION"]).astype(float)
                J = self.acc(at["JOINTS_0"]).astype(int) if "JOINTS_0" in at else None
                Wt = self.acc(at["WEIGHTS_0"]).astype(float) if "WEIGHTS_0" in at else None
                I = self.acc(pr["indices"]).reshape(-1, 3).astype(int) if "indices" in pr else None
                mat = self.j["materials"][pr["material"]].get("name", "") if "material" in pr else ""
                out.append((nd.get("name", ""), me.get("name", ""), k, mat, P, J, Wt, nd.get("skin"), I, i))
        return out

    def joint_names(self, s):
        return [self.j["nodes"][n].get("name", "") for n in self.j["skins"][s]["joints"]]

    def ibm(self, s):
        sk = self.j["skins"][s]
        return self.acc(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)

def skinned(P, J, Wt, mats):
    """P (n,3), J (n,4) into mats (m,4,4): sum of w * M v."""
    Ph = np.c_[P, np.ones(len(P))]
    out = np.zeros((len(P), 3))
    for c in range(J.shape[1]):
        M = mats[J[:, c]]
        out += Wt[:, c:c + 1] * np.einsum("nij,nj->ni", M, Ph)[:, :3]
    return out
