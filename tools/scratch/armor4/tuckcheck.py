"""tuckcheck.py: for each tuck file, how many of its points are on none of heroine.glb's vertices (HerWear's key, 1e-5 m)."""
import json, struct, sys, glob, os, numpy as np
b = open("godot/art/people/heroine.glb", "rb").read()
jl = struct.unpack_from("<I", b, 12)[0]; J = json.loads(b[20:20 + jl]); B = b[20 + jl + 8:]
keys = set()
for m in J["meshes"]:
    for p in m["primitives"]:
        a = J["accessors"][p["attributes"]["POSITION"]]; v = J["bufferViews"][a["bufferView"]]
        o = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        P = np.frombuffer(B, np.float32, a["count"] * 3, o).reshape(-1, 3)
        keys |= set(map(tuple, np.round(P.astype(np.float64) * 1e5).astype(np.int64)))
for f in sys.argv[1:]:
    d = open(f, "rb").read(); n = struct.unpack_from("<i", d, 0)[0]
    R = np.frombuffer(d, np.int32, n * 4, 4).reshape(-1, 4)[:, :3]
    miss = [tuple(r) for r in R if tuple(r) not in keys]
    if miss: print(os.path.basename(f), n, "missing", len(miss), "e.g.", np.array(miss[:3]) / 1e5)
print("checked", len(sys.argv) - 1)
