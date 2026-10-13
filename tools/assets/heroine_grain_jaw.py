"""Her face's grain eased off under her jaw: the blue of heroine_freckles.png (how much of the skin shader's grain her
head takes) brought to half under her jaw, back to all of it over the 2.5 cm above SPLIT, where the graft's (all of
it up her neck) takes over.

At grain 3, under her jaw, in its shadow, the grain read as dark speckle on every face, like stubble (judge f6,
11 October 2026); her portraits' necks there are smooth but for pores. Her cheeks and the rest keep theirs.

    blender -b tools/comfy/out/heroes/heroine_unpainted.blend --python tools/assets/heroine_grain_jaw.py -- \
        godot/art/people/head_tex/heroine_freckles.png [JAW_DIR ...]

The zone under her jaw is tools/assets/heroine_face/jaw_zone.png (her head's paint's UVs, rows from the top): every
face's under_jaw cut (heroine_face.py, FACE_JAW_ONLY=1, each face's DIR/jaw_cut.png) at its most. Given JAW_DIRs,
it is made again from their jaw_cut.png first. Only the blue is written; the freckles stay as heroine_freckles.py
laid them. Run again after heroine_freckles.py.
"""
import os
import sys

import bpy
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ZONE = os.path.join(HERE, "heroine_face", "jaw_zone.png")
args = sys.argv[sys.argv.index("--") + 1:]
OUT, DIRS = args[0], args[1:]
HALF = 0.5          # (the grain left under her jaw)
EASE = 0.025        # (metres above SPLIT over which it comes back)

if DIRS:
    z = None
    for d in DIRS:
        c = np.asarray(Image.open(os.path.join(d, "jaw_cut.png")).convert("L"), np.float32) / 255
        z = c if z is None else np.maximum(z, c)
    Image.fromarray((z * 255 + 0.5).astype(np.uint8)).save(ZONE)
    print("JAW ZONE from %d faces: %.2f%% of her head's texture" % (len(DIRS), 100 * (z > 0.5).mean()))

img = np.asarray(Image.open(OUT).convert("RGBA"), np.float32)[::-1] / 255      # (rows from the bottom, as UVs)
SIZE = img.shape[0]
zone = np.asarray(Image.open(ZONE).convert("L").resize((SIZE, SIZE), Image.BOX), np.float32)[::-1] / 255
zone = ndimage.gaussian_filter(zone, SIZE / 1024)

head = bpy.data.objects["HeroineHead"]
me = head.data
mw = np.array(head.matrix_world)
V = np.array([v.co[:] for v in me.vertices]) @ mw[:3, :3].T + mw[:3, 3]
me.calc_loop_triangles()
T = np.array([t.vertices[:] for t in me.loop_triangles])
UV = np.array([d.uv[:] for d in me.uv_layers.active.data])[np.array([t.loops[:] for t in me.loop_triangles])] * SIZE
known = np.zeros((SIZE, SIZE), bool)
blue = np.ones((SIZE, SIZE), np.float32)
for k, t in enumerate(UV):
    x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
    x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int), SIZE - 1)
    if x1 < x0 or y1 < y0:
        continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
    p = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, c = t
    v0, v1, v2 = b - a, c - a, p - a
    den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < 1e-12:
        continue
    v = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
    w = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
    bb = np.stack([1 - v - w, v, w], 1)
    m = (bb > -1e-3).all(1)
    P = (V[T[k]][None] * bb[m][:, :, None]).sum(1)
    s = P[:, 2] - (1.625 + 0.27 * (P[:, 1] + 0.02))                         # (above SPLIT, as heroine_face.py's)
    e = np.clip(s / EASE, 0, 1)
    r, cc = ys.ravel()[m], xs.ravel()[m]
    blue[r, cc] = 1 - HALF * zone[r, cc] * e * e * (3 - 2 * e)
    known[r, cc] = True
# (carried past the islands' edges, so a mipmap draws no seam of more grain along them)
_, (iy, ix) = ndimage.distance_transform_edt(~known, return_indices=True)
img[..., 2] = blue[iy, ix]
Image.fromarray((np.clip(img[::-1], 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT)
print("GRAIN UNDER JAW: blue %.2f at least; %d of her %d texels under 0.75" % (blue[known].min(), (blue[known] < 0.75).sum(), known.sum()))
