"""Face 30 r3: a built ponytail's tail (chain weight > 0.5): depth (COLOR.r), alpha and arc bands below the tie.  python taildepth.py <gltf>"""
import numpy as np, json, sys
S = sys.argv[1]
g = json.load(open(S)); b = open(S.replace('.gltf', '.bin'), 'rb').read()
def acc(i):
    a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]; dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a['componentType']]
    arr = np.frombuffer(b, dt, a['count'] * n, bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(a['count'], n).astype(float)
    if a.get('normalized'): arr /= np.iinfo(dt).max
    return arr
pr = g['meshes'][0]['primitives'][0]; at = pr['attributes']
P = acc(at['POSITION']); C = acc(at['COLOR_0']); U2 = acc(at['TEXCOORD_1'])
t = U2[:, 1] > 0.5
y = P[t][:, 1]; top = y.max(); r = C[t][:, 0]; a = C[t][:, 3]
print('tail top y %.3f' % top)
for lo in np.arange(0, 0.16, 0.01):
    m = (top - y >= lo) & (top - y < lo + 0.01)
    if m.sum(): print(f"{lo*100:4.0f}cm n{m.sum():5d} depth mean {r[m].mean():.2f} sd {r[m].std():.3f} p10 {np.percentile(r[m],10):.2f} alpha mean {a[m].mean():.2f} p10 {np.percentile(a[m],10):.2f}")
