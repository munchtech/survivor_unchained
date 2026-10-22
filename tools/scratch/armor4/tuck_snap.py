"""tuck_snap.py <bin>...: (armor 14) records on no vertex of heroine.glb snapped to her nearest vertex within 3 mm
(the neck-shape step moved her nape points 1-2 mm after the records were keyed); a record already there keeps the max."""
import json, struct, sys, numpy as np
from scipy.spatial import cKDTree
b = open("godot/art/people/heroine.glb", "rb").read(); jl = struct.unpack_from("<I", b, 12)[0]
J = json.loads(b[20:20 + jl]); B = b[20 + jl + 8:]
K = []
for m in J["meshes"]:
    for p in m["primitives"]:
        a = J["accessors"][p["attributes"]["POSITION"]]; v = J["bufferViews"][a["bufferView"]]
        o = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        K.append(np.frombuffer(B, np.float32, a["count"] * 3, o).reshape(-1, 3))
K = np.unique(np.round(np.concatenate(K).astype(np.float64) * 1e5).astype(np.int64), axis=0)
T = cKDTree(K)
dt = [("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")]
for f in sys.argv[1:]:
    d = open(f, "rb").read(); n = struct.unpack_from("<I", d, 0)[0]
    rec = np.frombuffer(d, dtype=dt, count=n, offset=4)
    P = np.stack([rec["x"], rec["y"], rec["z"]], 1).astype(np.int64)
    dd, j = T.query(P)
    miss = dd > 0
    if not miss.any():
        continue
    got = {}
    for k, (p, t, m_, jj, d_) in enumerate(zip(map(tuple, P), rec["t"], miss, j, dd)):
        key = tuple(K[jj]) if (m_ and d_ <= 300) else p
        got[key] = max(got.get(key, 0.0), float(t))
    ks = sorted(got); new = np.zeros(len(ks), dtype=dt)
    new["x"], new["y"], new["z"] = np.array(ks).T; new["t"] = [got[k] for k in ks]
    open(f, "wb").write(struct.pack("<I", len(new)) + new.tobytes())
    print("%s: %d of %d snapped (max %.2f mm), %d records now" % (f, int((miss & (dd <= 300)).sum()), n, dd[miss].max() / 100, len(new)))
