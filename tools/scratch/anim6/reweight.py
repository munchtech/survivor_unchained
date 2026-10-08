"""Her body with its weights split onto the helpers by a variant of
helpers.split, written into a copy of the built body (which has the helper
joints), for Godot to read at run time (anim_review's BODYDIR): weight
variants seen without a Blender build.

    python reweight.py <out dir> <profile tent|smooth> [share k]
"""
import json
import shutil
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from sweep import S, WT  # noqa: E402
import helpers as hp  # noqa: E402
from rig import Skeleton  # noqa: E402
from skin import Body, Gltf  # noqa: E402

out = Path(sys.argv[1])
hp.SPEC["weights"]["profile"] = sys.argv[2]
if len(sys.argv) > 3:
    hp.SPEC["weights"]["share"] = float(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
after = WT / "godot" / "art" / "people" / "heroine.glb"
sk = Skeleton.load(WT / "tools" / "anim" / "data" / "heroine_skeleton.json")
# The before body split here (its weights as they were, then the variant's split).
b = Body(Skeleton.load(S / "before" / "data" / "heroine_skeleton.json"), [(S / "before" / "people" / "heroine.glb", lambda n: n == "Heroine", "skin")], None, helpers=True)
names = b.sk.names
g = Gltf(after)
js = g.js
buf = bytearray(g.buffers[0])
base = 0
for n in js["nodes"]:
    if n.get("name") != "Heroine" or "mesh" not in n:
        continue
    joints = [js["nodes"][j]["name"] for j in js["skins"][n["skin"]]["joints"]]
    jix = {nm: i for i, nm in enumerate(joints)}
    for pr in js["meshes"][n["mesh"]]["primitives"]:
        a = pr["attributes"]
        cnt = js["accessors"][a["POSITION"]]["count"]
        J = b.J[base:base + cnt]
        W = b.W[base:base + cnt]
        base += cnt
        Jg = np.array([[jix[names[j]] for j in row] for row in J])
        W = np.where(W > 1e-6, W, 0.0)
        W = W / W.sum(1, keepdims=True)
        for key, data in (("JOINTS_0", Jg), ("WEIGHTS_0", W)):
            acc = js["accessors"][a[key]]
            bv = js["bufferViews"][acc["bufferView"]]
            dt = np.dtype(Gltf.TYPES[acc["componentType"]])
            assert not bv.get("byteStride") or bv["byteStride"] == dt.itemsize * 4, "strided"
            start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
            if acc.get("normalized"):
                arr = np.round(data * np.iinfo(dt).max).astype(dt)
            else:
                arr = data.astype(dt)
            raw = arr.tobytes()
            buf[start:start + len(raw)] = raw
assert base == len(b.P), (base, len(b.P))
# The glb again: its JSON chunk as it was, the binary chunk rewritten.
src = after.read_bytes()
n = struct.unpack_from("<I", src, 12)[0]
off = 20 + n
ln = struct.unpack_from("<I", src, off)[0]
assert ln == len(buf)
(out / "heroine.glb").write_bytes(src[:off + 8] + bytes(buf) + src[off + 8 + ln:])
print("wrote", out / "heroine.glb", "profile", hp.SPEC["weights"]["profile"], "share", hp.SPEC["weights"]["share"])
