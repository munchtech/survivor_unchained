"""A small GLB reader for her body: positions, normals, UVs, joints, weights, triangles,
the skin's joint names and inverse binds, and embedded images.
    from glbread import Body;  b = Body(path)"""
import io
import json
import struct

import numpy as np
from PIL import Image

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


class Body:
    def __init__(self, path, mesh='Mesh_0'):
        data = open(path, 'rb').read()
        jlen = struct.unpack('<I', data[12:16])[0]
        self.gl = json.loads(data[20:20 + jlen])
        boff = 20 + jlen
        blen = struct.unpack('<I', data[boff:boff + 4])[0]
        self.bin = data[boff + 8:boff + 8 + blen]
        gl = self.gl
        skin = gl['skins'][0]
        self.jnames = [gl['nodes'][j]['name'] for j in skin['joints']]
        self.ibm = self.acc(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
        m = [x for x in gl['meshes'] if x['name'] == mesh][0]
        cols = {k: [] for k in ('V', 'N', 'UV', 'J', 'W', 'T', 'MAT', 'C')}
        base = 0
        for pr in m['primitives']:
            at = pr['attributes']
            v = self.acc(at['POSITION']).astype(float)
            cols['V'].append(v)
            cols['N'].append(self.acc(at['NORMAL']).astype(float))
            cols['UV'].append(self.acc(at['TEXCOORD_0']).astype(float))
            cols['J'].append(self.acc(at['JOINTS_0']).astype(int))
            cols['W'].append(self.acc(at['WEIGHTS_0']).astype(float))
            cols['C'].append(self.acc(at['COLOR_0']).astype(float) if 'COLOR_0' in at else np.zeros((len(v), 4)))
            cols['T'].append(self.acc(pr['indices']).reshape(-1, 3).astype(int) + base)
            cols['MAT'].append(np.full(len(v), pr.get('material', 0)))
            base += len(v)
        for k, v in cols.items():
            setattr(self, k, np.concatenate(v) if k == 'MAT' else np.vstack(v))

    def acc(self, i):
        a = self.gl['accessors'][i]
        bv = self.gl['bufferViews'][a['bufferView']]
        dt = np.dtype(CT[a['componentType']])
        n, c = a['count'], NC[a['type']]
        stride = bv.get('byteStride', dt.itemsize * c)
        start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        raw = np.frombuffer(self.bin, dtype=np.uint8, count=stride * (n - 1) + dt.itemsize * c, offset=start)
        out = np.lib.stride_tricks.as_strided(raw, shape=(n, stride), strides=(stride, 1))[:, :dt.itemsize * c].copy()
        out = out.view(dt).reshape(n, c)
        if a.get('normalized') and dt != np.float32:
            out = out.astype(np.float32) / np.iinfo(dt).max
        return out

    def image(self, name):
        im = [i for i in self.gl['images'] if i.get('name') == name][0]
        bv = self.gl['bufferViews'][im['bufferView']]
        raw = self.bin[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']]
        return Image.open(io.BytesIO(raw)).convert('RGB')
