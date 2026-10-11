"""uv2flip.py: her hair's chain weights the right way up in the shipped glTFs (one-off, 11 October 2026).
heroine_hair.py wrote each point's swing weight as its second UV's v, and Blender's glTF export flips v (1 - v):
so her tail (weight 1) reached the shader as 0 and never swung (it stayed fixed to her head and went through her
chest on all fours, chain_haul), while her cap, tie and fine hairs (0) took the chain's swing, and the short styles'
own sway never ran. This flips TEXCOORD_1's v back in each heroine_hair_*.gltf's buffer; heroine_hair.py now writes
1 - weight, so a rebuild comes out the same."""
import glob, json, os
import numpy as np
D = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\art\people"
for f in sorted(glob.glob(os.path.join(D, "heroine_hair_*.gltf"))):
    js = json.load(open(f, encoding="utf-8"))
    binp = os.path.join(D, js["buffers"][0]["uri"])
    b = bytearray(open(binp, "rb").read())
    done = set()
    for m in js["meshes"]:
        for p in m["primitives"]:
            i = p["attributes"].get("TEXCOORD_1")
            if i is None or i in done: continue
            done.add(i)
            a = js["accessors"][i]; v = js["bufferViews"][a["bufferView"]]
            assert a["componentType"] == 5126 and a["type"] == "VEC2"
            off = v.get("byteOffset", 0) + a.get("byteOffset", 0); st = v.get("byteStride", 8)
            raw = np.frombuffer(b, np.uint8, a["count"] * st, off).reshape(-1, st).copy()
            uv = raw[:, :8].view(np.float32).reshape(-1, 2)
            uv[:, 1] = 1.0 - uv[:, 1]
            raw[:, :8] = uv.view(np.uint8).reshape(-1, 8)
            b[off:off + a["count"] * st] = raw.tobytes()
            if "min" in a: a["min"][1], a["max"][1] = 1.0 - a["max"][1], 1.0 - a["min"][1]
    open(binp, "wb").write(bytes(b))
    with open(f, "w", encoding="utf-8", newline="\n") as fh: json.dump(js, fh, indent=1)
    print("flipped", os.path.basename(f), len(done), "accessors")
