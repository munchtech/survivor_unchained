"""Two builds of one outfit, attribute by attribute: max difference per
mesh primitive.   python bindiff.py <outfit> <worktree A> <worktree B>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "anim"))
import numpy as np  # noqa: E402
from skin import Gltf  # noqa: E402

o, A, B = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
ga = Gltf(A / "godot/art/people" / f"heroine_outfit_{o}.gltf")
gb = Gltf(B / "godot/art/people" / f"heroine_outfit_{o}.gltf")
worst = {}
for ma, mb in zip(ga.js["meshes"], gb.js["meshes"]):
    for pa, pb in zip(ma["primitives"], mb["primitives"]):
        for k in pa["attributes"]:
            x = ga.accessor(pa["attributes"][k]).astype(float)
            y = gb.accessor(pb["attributes"][k]).astype(float)
            d = float(np.abs(x - y).max()) if x.shape == y.shape else float("inf")
            n = int((np.abs(x - y).max(1) > 1e-6).sum()) if x.shape == y.shape and x.ndim > 1 else -1
            print(f"{ma.get('name','?'):24s} {k:12s} max {d:.6f} points differing {n}/{len(x)}")
