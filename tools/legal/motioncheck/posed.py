"""A flagged frame of the legal motion check in three dimensions (run.sh with DUMP=1 writes
<picture prefix>_NN_posed.json/.bin and tris_*.bin): which of her coded skin a view sees, her
skin tucked as her shader draws it, and for each patch seen, how it got out from under her
outfit: beyond a garment's edge (nothing over it), under a lifted edge (a garment over it,
seen in under its edge from the side), or through it. Rays go through the coded pixels of the
picture itself, so what it says is what was drawn.
    python posed.py <..._NN_posed> <view> <outfit channel 0-3> <the coded picture of that view>
Views are the run's (chest, left, side, below, over; low, lowside, top lying down)."""
import json
import os
import sys

import numpy as np


def load(prefix):
    head = json.load(open(prefix + '.json'))
    raw = open(prefix + '.bin', 'rb').read()
    d = os.path.dirname(prefix)
    meshes = []
    for e in head['meshes']:
        n, o = e['verts'], e['off']
        m = {'name': e['name'], 'surface': e['surface'],
             'pos': np.frombuffer(raw, np.float32, n * 3, o).reshape(n, 3).astype(float),
             'nrm': np.frombuffer(raw, np.float32, n * 3, o + n * 12).reshape(n, 3).astype(float),
             'uv2': np.frombuffer(raw, np.float32, n * 2, e['uv2']).reshape(n, 2) if 'uv2' in e else None,
             'col': np.frombuffer(raw, np.float32, n * 4, e['color']).reshape(n, 4) if 'color' in e else None,
             'tris': np.fromfile(os.path.join(d, 'tris_%s_%d.bin' % (e['name'], e['surface'])), np.int32).reshape(-1, 3)}
        meshes.append(m)
    return head, meshes


def project(cam, p):
    b = np.array(cam['basis']).reshape(3, 3).T          # (columns: the camera's x, y, z)
    q = (p - np.array(cam['origin'])) @ b
    w, h = cam['size']
    f = (h / 2) / np.tan(np.radians(cam['fov']) / 2)
    return np.c_[w / 2 + q[:, 0] / -q[:, 2] * f, h / 2 - q[:, 1] / -q[:, 2] * f], -q[:, 2]


def first_hits(o, dirs, tri_pos, chunk=3000):
    """For rays from o (one point, or one per ray) along unit dirs: the distance to the
    first triangle hit (inf: none)."""
    o = np.broadcast_to(np.asarray(o, float), dirs.shape)
    best = np.full(len(dirs), np.inf)
    for s in range(0, len(tri_pos), chunk):
        v0, v1, v2 = (tri_pos[s:s + chunk, k] for k in range(3))
        e1, e2 = v1 - v0, v2 - v0
        pv = np.cross(dirs[:, None, :], e2[None])
        det = (e1[None] * pv).sum(2)
        ok = np.abs(det) > 1e-14
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = o[:, None, :] - v0[None]
        u = (tv * pv).sum(2) * inv
        qv = np.cross(tv, e1[None])
        v = (dirs[:, None, :] * qv).sum(2) * inv
        t = (e2[None] * qv).sum(2) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
        best = np.minimum(best, np.where(hit, t, np.inf).min(1))
    return best


def main():
    """Rays through every coded pixel of the picture (green: the strip; areola: blue with
    red under 2.2 cm), each mesh's first hit along them, her skin tucked as drawn. Skin hit
    first with a garment a few mm behind: through it; nothing near behind: past its edge."""
    prefix, view, ch, png = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    from PIL import Image
    head, meshes = load(prefix)
    cam = [c for c in head['cams'] if c['name'] == view][0]
    o = np.array(cam['origin'])
    a = np.asarray(Image.open(png).convert('RGB')).astype(int)
    strip = (a[..., 1] >= 250) & (a[..., 0] <= 8) & (a[..., 2] <= 8)
    near = (a[..., 2] >= 250) & (a[..., 1] <= 8) & (a[..., 0] > 16)
    areola = near & ((a[..., 0] / 255.0) ** 2.2 / 0.9 * 6.0 < 2.2)
    b = np.array(cam['basis']).reshape(3, 3).T
    w, h = cam['size']
    f = (h / 2) / np.tan(np.radians(cam['fov']) / 2)
    for what, m in (('strip', strip), ('areola', areola)):
        ys, xs = np.nonzero(m)
        if not len(xs):
            continue
        d = np.c_[(xs + 0.5 - w / 2) / f, -(ys + 0.5 - h / 2) / f, -np.ones(len(xs))] @ b.T
        d /= np.linalg.norm(d, axis=1)[:, None]
        print('%s: %d px, around (%d, %d)' % (what, len(xs), xs.mean(), ys.mean()))
        for mm in meshes:
            k = mm['col'][:, ch] if (mm['name'] == 'Heroine' and mm['col'] is not None) else np.zeros(len(mm['pos']))
            p = mm['pos'] - mm['nrm'] * (0.010 * k)[:, None]
            t = first_hits(o, d, p[mm['tris']])
            if np.isfinite(t).any():
                tt = t[np.isfinite(t)]
                print('  %-22s surface %d: on %d of %d rays, first hit %.4f to %.4f m' % (mm['name'], mm['surface'], len(tt), len(t), tt.min(), tt.max()))


if __name__ == '__main__':
    main()
