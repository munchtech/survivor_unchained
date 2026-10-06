"""glb_normals.py heroine.glb mesh: for points of a mesh sharing a place (split at seams), how far their normals disagree."""
import json
import struct
import sys

import numpy as np

path, want = sys.argv[1], sys.argv[2]
data = open(path, "rb").read()
jl = struct.unpack("<I", data[12:16])[0]
g = json.loads(data[20:20 + jl])
bin0 = 20 + jl + 8


def acc(i):
    a = g["accessors"][i]
    bv = g["bufferViews"][a["bufferView"]]
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a["componentType"]]
    off = bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return np.frombuffer(data, dt, a["count"] * n, off).reshape(a["count"], n)


for m in g["meshes"]:
    if m["name"] != want and not any(n.get("mesh") == g["meshes"].index(m) and n.get("name") == want for n in g["nodes"]):
        continue
    for p in m["primitives"]:
        P = acc(p["attributes"]["POSITION"]).astype(np.float64)
        N = acc(p["attributes"]["NORMAL"]).astype(np.float64)
        key = np.round(P / 1e-6).astype(np.int64)
        _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
        inv = inv.ravel()
        worst = np.zeros(len(cnt))
        mean = np.zeros((len(cnt), 3))
        np.add.at(mean, inv, N)
        mean /= np.linalg.norm(mean, axis=1)[:, None] + 1e-12
        ang = np.degrees(np.arccos(np.clip((N * mean[inv]).sum(1), -1, 1)))
        np.maximum.at(worst, inv, ang)
        shared = cnt > 1
        print(m["name"], len(P), "points;", shared.sum(), "places shared by more than one;",
              "normal disagreement at shared places: mean %.2f deg, 99%% %.2f, max %.2f" % (
                  worst[shared].mean(), np.percentile(worst[shared], 99), worst[shared].max()))
        bad = np.where(worst > 5)[0]
        if len(bad):
            pos = np.array([P[inv == b][0] for b in bad[:20]])
            print("  disagreeing by over 5 deg:", len(bad), "e.g.", np.round(pos[:8], 3).tolist())
        # also: how smooth are neighbouring normals (triangles' corners)
        idx = acc(p["indices"]).ravel().reshape(-1, 3)
        e = np.vstack([idx[:, [0, 1]], idx[:, [1, 2]], idx[:, [2, 0]]])
        d = np.degrees(np.arccos(np.clip((N[e[:, 0]] * N[e[:, 1]]).sum(1), -1, 1)))
        L = np.linalg.norm(P[e[:, 0]] - P[e[:, 1]], axis=1)
        print("  across edges: degrees per mm, 99%%: %.1f, max %.1f" % (np.percentile(d / (L * 1000 + 1e-9), 99), (d / (L * 1000 + 1e-9)).max()))
