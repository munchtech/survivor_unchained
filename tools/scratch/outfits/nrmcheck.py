"""Degenerate normals, tangents and UVs in an outfit's glTF (a NaN source for lighting).
    python nrmcheck.py <outfit.gltf>"""
import json
import os
import sys

import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
p = sys.argv[1]
g = json.load(open(p))
b = np.fromfile(os.path.join(os.path.dirname(p), g['buffers'][0]['uri']), dtype=np.uint8)


def acc(i):
    a = g['accessors'][i]
    bv = g['bufferViews'][a['bufferView']]
    dt = np.dtype(CT[a['componentType']])
    n, c = a['count'], NC[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    st = bv.get('byteStride', dt.itemsize * c)
    raw = b[off: off + st * (n - 1) + dt.itemsize * c]
    out = np.lib.stride_tricks.as_strided(raw, shape=(n, st), strides=(st, 1))[:, :dt.itemsize * c].copy().view(dt).reshape(n, c)
    return out.astype(float)


for m in g['meshes']:
    for pr in m['primitives']:
        at = pr['attributes']
        pos = acc(at['POSITION'])
        nrm = acc(at['NORMAL'])
        tri = acc(pr['indices']).astype(int).reshape(-1, 3)
        nl = np.linalg.norm(nrm, axis=1)
        msg = '%-22s verts %7d  normals: nan %d, |n|<0.5 %d' % (m['name'], len(pos), int(np.isnan(nl).sum()), int((nl < 0.5).sum()))
        if 'TANGENT' in at:
            tg = acc(at['TANGENT'])
            tl = np.linalg.norm(tg[:, :3], axis=1)
            msg += ', tangents: nan %d, |t|<0.5 %d' % (int(np.isnan(tl).sum()), int((tl < 0.5).sum()))
        else:
            msg += ', no tangents'
        uv = acc(at['TEXCOORD_0'])
        e1, e2 = uv[tri[:, 1]] - uv[tri[:, 0]], uv[tri[:, 2]] - uv[tri[:, 0]]
        uva = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
        p1, p2 = pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]]
        area = np.linalg.norm(np.cross(p1, p2), axis=1)
        msg += ', tris %d: zero-area %d, zero-UV-area %d' % (len(tri), int((area < 1e-12).sum()), int((uva < 1e-14).sum()))
        print(msg)
