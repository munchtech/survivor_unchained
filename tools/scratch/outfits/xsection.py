"""Cross-sections of her body and an outfit at rest, across her (x against height) at given
depths, near her crotch: where a gusset or string lies against her skin, and what the motion
check's strip is there. In Blender's axes (y back, z up); glTF files are read and turned.
    python xsection.py <heroine.glb> <heroine_outfit_X.gltf> <out.png> [y,y,...]
          [--box x0,x1,z0,z1]   (default -0.03,0.03,0.88,0.975)"""
import json
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbread import Body  # noqa: E402

CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def gltf_meshes(path):
    gl = json.load(open(path))
    base = os.path.dirname(path)
    bins = [open(os.path.join(base, b['uri']), 'rb').read() for b in gl['buffers']]

    def acc(i):
        a = gl['accessors'][i]
        v = gl['bufferViews'][a['bufferView']]
        raw = bins[v['buffer']]
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        n = a['count'] * NC[a['type']]
        return np.frombuffer(raw, CT[a['componentType']], n, off).reshape(a['count'], -1)

    out = []
    for m in gl['meshes']:
        for pr in m['primitives']:
            V = acc(pr['attributes']['POSITION']).astype(float)
            T = acc(pr['indices']).reshape(-1, 3).astype(int)
            out.append((m['name'], V, T))
    return out


def to_blender(V):
    return np.stack([V[:, 0], -V[:, 2], V[:, 1]], 1)


def slice_y(V, T, y):
    """Segments (x0, z0, x1, z1) where the triangles cross the plane at depth y."""
    p = V[T]
    d = p[:, :, 1] - y
    segs = []
    for tri, dd in zip(p, d):
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if dd[i] * dd[j] < 0:
                t = dd[i] / (dd[i] - dd[j])
                q = tri[i] + t * (tri[j] - tri[i])
                pts.append((q[0], q[2]))
        if len(pts) == 2:
            segs.append(pts)
    return segs


args = [a for a in sys.argv[1:] if not a.startswith('--')]
box = (-0.03, 0.03, 0.88, 0.975)
if '--box' in sys.argv:
    box = tuple(float(v) for v in sys.argv[sys.argv.index('--box') + 1].split(','))
    args = [a for a in args if a != sys.argv[sys.argv.index('--box') + 1]]
body_path, outfit_path, out_png = args[:3]
ys = [float(v) for v in args[3].split(',')] if len(args) > 3 else [0.0, 0.012, 0.024]
b = Body(body_path)
BV, BT = to_blender(b.V), b.T
near = (np.abs(BV[BT].mean(1)[:, 0]) < 0.1) & (np.abs(BV[BT].mean(1)[:, 2] - 0.93) < 0.12)
BT = BT[near]
meshes = [(n, to_blender(V), T) for n, V, T in gltf_meshes(outfit_path)]
S = 900  # pixels per panel side
x0, x1, z0, z1 = box
sc = S / max(x1 - x0, z1 - z0)
W = int((x1 - x0) * sc)
H = int((z1 - z0) * sc)
sheet = Image.new('RGB', (W * len(ys), H + 20), (16, 16, 16))
cols = [(255, 120, 60), (90, 200, 255), (250, 220, 80), (200, 120, 255), (120, 255, 140), (255, 255, 255)]
for k, y in enumerate(ys):
    im = Image.new('RGB', (W, H), (30, 30, 30))
    d = ImageDraw.Draw(im)

    def px(x, z):
        return ((x - x0) * sc, (z1 - z) * sc)
    # a 1 cm grid, and the strip's sides (|x| = 1.2 cm)
    for gx in np.arange(np.ceil(x0 * 100) / 100, x1, 0.01):
        d.line([px(gx, z0), px(gx, z1)], fill=(55, 55, 55))
    for gz in np.arange(np.ceil(z0 * 100) / 100, z1, 0.01):
        d.line([px(x0, gz), px(x1, gz)], fill=(55, 55, 55))
    for sx in (-0.012, 0.012):
        d.line([px(sx, z0), px(sx, z1)], fill=(40, 110, 40))
    for s in slice_y(BV, BT, y):
        d.line([px(*s[0]), px(*s[1])], fill=(235, 190, 160), width=2)
    for i, (n, V, T) in enumerate(meshes):
        keep = (np.abs(V[T].mean(1)[:, 1] - y) < 0.05) & (V[T].mean(1)[:, 2] < z1 + 0.05) & (V[T].mean(1)[:, 2] > z0 - 0.05)
        for s in slice_y(V, T[keep], y):
            d.line([px(*s[0]), px(*s[1])], fill=cols[i % len(cols)], width=1)
    sheet.paste(im, (k * W, 20))
    ImageDraw.Draw(sheet).text((k * W + 6, 4), 'y = %+.3f m (behind +)   %s' % (y, ' '.join(
        '%s' % n for n, _, _ in meshes)), fill=(220, 220, 220))
sheet.save(out_png)
print(out_png, sheet.size)
