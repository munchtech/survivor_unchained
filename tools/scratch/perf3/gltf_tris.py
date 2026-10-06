"""Triangles and vertices per mesh in glTF files (.gltf JSON or .glb):
python gltf_tris.py FILE..."""
import json
import struct
import sys


def load(path):
    data = open(path, "rb").read()
    if data[:4] == b"glTF":
        n = struct.unpack_from("<I", data, 12)[0]
        return json.loads(data[20:20 + n])
    return json.loads(data)


for f in sys.argv[1:]:
    g = load(f)
    acc = g["accessors"]
    tot_t = tot_v = 0
    rows = []
    for m in g.get("meshes", []):
        t = v = 0
        prims = len(m["primitives"])
        morphs = len(m["primitives"][0].get("targets", []))
        for p in m["primitives"]:
            v += acc[p["attributes"]["POSITION"]]["count"]
            t += acc[p["indices"]]["count"] // 3 if "indices" in p else acc[p["attributes"]["POSITION"]]["count"] // 3
        rows.append((t, v, prims, morphs, m.get("name", "?")))
        tot_t += t
        tot_v += v
    print(f"{f.split(chr(92))[-1]}: {tot_t:,} tris, {tot_v:,} verts, {len(rows)} meshes")
    for t, v, p, mo, n in sorted(rows, reverse=True):
        print(f"    {t:>9,} tris {v:>9,} verts {p} surf {mo:>3} morphs  {n}")
