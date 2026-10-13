"""A marker head paint for measuring her ears at the Look: grey, the ears (heroine_ears' mask, w > 0.9) pure green, a
cheek patch on the cheekbone pure blue. Rendered with --head-paint, it says which pixels are ear and which cheek.
    python ear_marker.py OUT.png"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/tools/assets")
import heroine_ears as he
from heroine_ao_seam import raster

js, binc = he.hs._load(he.GLB)
mats = [m.get("name") for m in js["materials"]]
prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] == "skin_head")
P = he.hs._read(js, binc, prim["attributes"]["POSITION"]).astype(np.float64)
UV = he.hs._read(js, binc, prim["attributes"]["TEXCOORD_0"])
T = he.hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
ax = np.abs(P[:, 0])
d = np.linalg.norm(np.c_[ax, P[:, 1:]] - np.array(he.EAR), axis=1)
ear = ((1 - he.smooth(he.EAR_R[0], he.EAR_R[1], d)) * he.smooth(he.EAR_X[0], he.EAR_X[1], ax) > 0.9).astype(float)
# the cheekbone: the skin at the front of her face's side, under the eye
front = P[:, 2] > np.percentile(P[(P[:, 1] > 1.69) & (P[:, 1] < 1.74), 2], 70)
cheek = (ax > 0.035) & (ax < 0.052) & (P[:, 1] > 1.695) & (P[:, 1] < 1.722) & (P[:, 2] > 0.02)
print("ear verts", int(ear.sum()), "cheek verts", int(cheek.sum()), "cheek mean", np.round(P[cheek].mean(0), 3), "z range", np.round([P[cheek, 2].min(), P[cheek, 2].max()], 3))
n = 2048
me = raster(UV, T, ear, n)
mc = raster(UV, T, cheek.astype(float), n)
im = np.full((n, n, 3), 0.55)
im[mc > 0.5] = (0, 0, 1)
im[me > 0.5] = (0, 1, 0)
Image.fromarray((im * 255).astype(np.uint8)).save(sys.argv[1])
