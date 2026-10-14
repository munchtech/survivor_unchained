"""mesh.py: a hair style's glTF primitives (positions, UV2, joints, weights, normals) as numpy."""
import json, numpy as np
ART = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/godot/art/people/"
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
def load(style):
    g = json.load(open(ART + "heroine_hair_%s.gltf" % style)); buf = open(ART + g["buffers"][0]["uri"], "rb").read()
    def acc(i):
        a = g["accessors"][i]; bv = g["bufferViews"][a["bufferView"]]; n = NC[a["type"]]; t = np.dtype(CT[a["componentType"]])
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0); stride = bv.get("byteStride", n * t.itemsize)
        raw = np.frombuffer(buf, np.uint8, count=stride * (a["count"] - 1) + n * t.itemsize, offset=off)
        out = np.lib.stride_tricks.as_strided(raw, (a["count"], n * t.itemsize), (stride, 1)).copy().view(t).reshape(a["count"], n)
        if a.get("normalized"): out = out.astype(np.float32) / np.iinfo(t).max
        return out
    joints = [g["nodes"][j]["name"] for j in g["skins"][0]["joints"]]
    prims = []
    for p in g["meshes"][0]["primitives"]:
        A = p["attributes"]
        prims.append(dict(mat=g["materials"][p["material"]]["name"], P=acc(A["POSITION"]), N=acc(A["NORMAL"]), UV2=acc(A["TEXCOORD_1"]),
                          J=acc(A["JOINTS_0"]), W=acc(A["WEIGHTS_0"])))
    return prims, joints
if __name__ == "__main__":
    import sys
    for st in sys.argv[1:]:
        prims, joints = load(st)
        ch = np.array(json.load(open(ART + "heroine_hair_%s.chain.json" % st))["points"])
        print(st, "chain y %.3f..%.3f z %.3f..%.3f" % (ch[:, 1].min(), ch[:, 1].max(), ch[:, 2].min(), ch[:, 2].max()))
        for p in prims:
            m = p["UV2"][:, 1] > 0
            jj = np.unique(p["J"][m][p["W"][m] > 0.01]) if m.any() else []
            print(" ", p["mat"], len(p["P"]), "moving", m.sum(), "uv2.x %.2f..%.2f" % (p["UV2"][m, 0].min(), p["UV2"][m, 0].max()) if m.any() else "",
                  "uv2.y max %.2f" % p["UV2"][:, 1].max(), "joints", [joints[j] for j in jj][:8])
            if m.any():
                # lateral spread from the chain at each place along it
                s = np.clip(p["UV2"][m, 0], 0, 1) * 7; i = np.minimum(np.floor(s).astype(int), 6); f = s - i
                c = ch[i] * (1 - f[:, None]) + ch[i + 1] * f[:, None]; o = p["P"][m] - c
                print("   offset from chain |o| p50 %.3f p90 %.3f max %.3f; x-spread max %.3f" % (np.percentile(np.linalg.norm(o, axis=1), 50), np.percentile(np.linalg.norm(o, axis=1), 90), np.linalg.norm(o, axis=1).max(), np.abs(o[:, 0]).max()))
