"""Shaded clay views of a glTF body's bind pose, untextured, by splatting dense surface samples
with a depth test (CPU only). For checking whether a base body has anatomical detail.
    python relief.py <in.gltf> <out.png> [y_from y_to]   (y in the mesh's units; default whole)"""
import sys

import numpy as np
import trimesh
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
scene = trimesh.load(src, force='scene')
meshes = [g for g in scene.dump() if isinstance(g, trimesh.Trimesh)]
m = trimesh.util.concatenate(meshes)
lo, hi = m.bounds
y0, y1 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (lo[1], hi[1])
pts, fi = trimesh.sample.sample_surface_even(m, 3_000_000)
nrm = m.face_normals[fi]
keep = (pts[:, 1] >= y0) & (pts[:, 1] <= y1)
pts, nrm = pts[keep], nrm[keep]
light = np.array([0.35, 0.45, 0.82])
light /= np.linalg.norm(light)
views = []
for ang in (0, 35, 90, 180):
    a = np.radians(ang)
    rot = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    p = pts @ rot.T
    n = nrm @ rot.T
    H = 900
    span = max(y1 - y0, 1e-6)
    s = H / span
    W = int((p[:, 0].max() - p[:, 0].min()) * s) + 20
    x = ((p[:, 0] - p[:, 0].min()) * s + 10).astype(int)
    y = ((y1 - p[:, 1]) * s).astype(int).clip(0, H - 1)
    z = p[:, 2]
    order = np.argsort(z)  # far first; nearer points overwrite
    img = np.full((H, W), 40, np.uint8)
    shade = (np.clip(n @ light, 0, 1) * 200 + 40).astype(np.uint8)
    facing = n[:, 2] > 0
    o = order[facing[order]]
    img[y[o], x[o]] = shade[o]
    views.append(Image.fromarray(img))
total = sum(v.width for v in views)
sheet = Image.new('L', (total, views[0].height), 40)
xo = 0
for v in views:
    sheet.paste(v, (xo, 0))
    xo += v.width
sheet.save(out)
print(out, sheet.size, 'bounds', lo.round(3), hi.round(3))
