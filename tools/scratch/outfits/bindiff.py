"""Where two builds of an outfit's .bin differ: per accessor, how many values and by how much.
    python bindiff.py <a.gltf> <b.gltf>"""
import json
import os
import sys

import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
ga = json.load(open(sys.argv[1]))
bins = [np.fromfile(os.path.join(os.path.dirname(p), json.load(open(p))['buffers'][0]['uri']), dtype=np.uint8) for p in sys.argv[1:3]]
names = {}
for m in ga['meshes']:
    for pr in m['primitives']:
        for k, v in pr['attributes'].items():
            names[v] = m['name'] + '.' + k
        names[pr['indices']] = m['name'] + '.indices'
for i, a in enumerate(ga['accessors']):
    if 'bufferView' not in a:
        continue
    bv = ga['bufferViews'][a['bufferView']]
    dt = np.dtype(CT[a['componentType']])
    n = a['count'] * NC[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    x = bins[0][off:off + n * dt.itemsize].view(dt).astype(float)
    y = bins[1][off:off + n * dt.itemsize].view(dt).astype(float)
    d = np.abs(x - y)
    if d.max() > 0:
        print('%-40s %7d of %7d differ, max %.3g' % (names.get(i, 'accessor %d' % i), int((d > 0).sum()), n, d.max()))
