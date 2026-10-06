"""Texel points of his body (cached) and the relief's tilt by region."""
import os, sys
import bpy
import numpy as np
from PIL import Image
S = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab82cbe99e2937ddd"
him = bpy.data.objects["Hero"]
me = him.data
me.calc_loop_triangles()
V = np.array([v.co[:] for v in me.vertices])
T = np.array([t.vertices[:] for t in me.loop_triangles])
L = np.array([t.loops[:] for t in me.loop_triangles])
UV = np.array([d.uv[:] for d in me.uv_layers.active.data])[L]
size = 4096
rows, cols, tri, bb = [], [], [], []
for k, t in enumerate(UV * size):
    x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
    x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int), size - 1)
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
    q = np.stack([1 - v - w, v, w], 1)
    m = (q > -1e-3).all(1)
    rows.append(ys.ravel()[m]); cols.append(xs.ravel()[m]); tri.append(np.full(m.sum(), k)); bb.append(q[m])
rows, cols, tri, bb = (np.concatenate(x) for x in (rows, cols, tri, bb))
P = (V[T[tri]] * bb[:, :, None]).sum(1)
np.savez(os.path.join(S, "texels.npz"), rows=rows, cols=cols, P=P.astype(np.float32))
nim = np.asarray(Image.open(os.path.join(WT, r"tools\comfy\out\heroes\hero_tex\hero_body_normal.png")).convert("RGB"), np.float32)[::-1] / 255
n = nim[rows, cols] * 2 - 1
z = n[:, 2]
clav = (P[:, 2] > 1.5) & (P[:, 2] < 1.62) & (np.abs(P[:, 0]) < 0.2) & (P[:, 1] < 0)
abs_ = (P[:, 2] > 1.1) & (P[:, 2] < 1.3) & (np.abs(P[:, 0]) < 0.15) & (P[:, 1] < 0)
for name, m in (("clavicle", clav), ("abs", abs_), ("all", np.ones(len(z), bool))):
    print(name, m.sum(), "z pct", np.round(np.percentile(z[m], [1, 5, 10, 25, 50]), 3))
print("hand |x|>0.75:", np.round(np.percentile(z[np.abs(P[:, 0]) > 0.75], [1, 5, 10, 25, 50]), 3))
print("x range", P[:, 0].min(), P[:, 0].max())
