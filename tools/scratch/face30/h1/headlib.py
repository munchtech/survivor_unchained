"""Her head from heroine.glb (skinned rest), its UVs, triangles and ear keys' moves; hair caps from a style's gltf."""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(WT, "tools", "scratch", "face29"))
from gl import G, skinned  # noqa
ART = os.path.join(WT, "godot", "art", "people")
her = G(os.path.join(ART, "heroine.glb"))
HJ = {her.j["nodes"][n].get("name"): her.W(n) for n in her.j["skins"][0]["joints"]}
def mats_for(g, s=0):
    return np.array([HJ.get(n, g.W(g.j["skins"][s]["joints"][q])) for q, n in enumerate(g.joint_names(s))]) @ g.ibm(s)
EYE_Y = 1.748
CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
def sparse(g, a):
    A = g.j["accessors"][a]
    if "bufferView" in A: return g.acc(a).astype(float)
    out = np.zeros((A["count"], 3)); sp = A.get("sparse")
    if not sp: return out
    def view(bvi, off, dt, n):
        bv = g.j["bufferViews"][bvi]
        return np.frombuffer(g.bin[bv.get("buffer", 0)], dt, count=n, offset=bv.get("byteOffset", 0) + off)
    ix = view(sp["indices"]["bufferView"], sp["indices"].get("byteOffset", 0), CT[sp["indices"]["componentType"]], sp["count"])
    vals = view(sp["values"]["bufferView"], sp["values"].get("byteOffset", 0), np.float32, sp["count"] * 3).reshape(-1, 3)
    out[ix.astype(int)] = vals
    return out
def head():
    for (node, mesh, k, mat, P, J, Wt, s, I, ni) in her.meshes():
        if node == "HeroineHead" and mat == "skin_head":
            me = her.j["meshes"][her.j["nodes"][ni]["mesh"]]; pr = me["primitives"][k]
            names = me.get("extras", {}).get("targetNames", [])
            keys = {}
            for n, t in zip(names, pr.get("targets", [])):
                if n.startswith("ears_"):
                    keys[n] = np.linalg.norm(sparse(her, t["POSITION"]), axis=1)
            HV = skinned(P, J, Wt, mats_for(her, s))
            UV = her.acc(pr["attributes"]["TEXCOORD_0"]).astype(float)
            return HV, UV, I, keys
def caps(path):
    g = G(path); M = mats_for(g); out = []
    for (node, mesh, k, mat, P, J, Wt, sk, I, ni) in g.meshes():
        if mat != "hair_cap": continue
        at = g.j["meshes"][g.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
        col = g.acc(at["COLOR_0"]).astype(float)
        if col.max() > 1.5: col = col / 65535.0
        out.append((skinned(P, J, Wt, M), col, I))
    return out
def raster(UV, I, X, size=1024):
    """Texels (row, col in the image) her triangles cover, each with X interpolated."""
    rows, cols, vals = [], [], []
    T = UV[I] * size
    for k, t in enumerate(T):
        x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int), size - 1)
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        p = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, c = t; v0, v1, v2 = b - a, c - a, p - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12: continue
        v = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den; w = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        bb = np.stack([1 - v - w, v, w], 1); m = (bb > -1e-3).all(1)
        rows.append(ys.ravel()[m]); cols.append(xs.ravel()[m])
        vals.append((X[I[k]][None] * bb[m][:, :, None]).sum(1))
    return np.concatenate(rows), np.concatenate(cols), np.concatenate(vals)
