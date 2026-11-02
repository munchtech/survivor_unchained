"""The canopy fade's stump caps (Env 23): each of our trees' lod0-2 meshes given a lid where its bark crosses the cut.

    python tools/assets/tree_caps.py [species ...]        (default: spruce alder snag; edits the .gltf/.bin in place)

kit.gdshader's canopy fade (OWN_FOLIAGE) cuts a faded tree's bark above crown_keep (flora_species.json) and keeps the trunk
below it as a stump. The trunk is an open tube, so from the play camera the cut showed the ground inside it and a crescent of
its far wall (judge e23v3: "hollow stone wells"). Here every closed loop where the bark strip (u >= 0.75) crosses the plane
y = crown_keep (each stem of an alder, each piece of the packed snag) gets a fan of triangles over it, the exact section of
the mesh, so the lid meets the wall without a seam. A cap's vertices are marked COLOR.b = 0.3 (the cards' b is 0 or 1);
COLOR.g is the loop's mean radius x 2 (m), COLOR.a the piece's (packed); UV in the bark strip carries the offset from the
loop's middle: u = 0.875 + 0.2 dx, v = 0.5 + 0.2 dz. The shader collapses a cap unless its tree is faded (so it costs a
few triangles and no draw) and paints it as sawn wood. Run again: old caps are stripped first (idempotent). Works on the
exported files, so the trees themselves stay exactly as built (no Blender turn).
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FLORA = os.path.join(ROOT, 'godot', 'art', 'world', 'flora')
SPECIES = os.path.join(ROOT, 'godot', 'data', 'flora_species.json')
CT = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
CAP_B = 0.3


def read(g, buf, ai):
    a = g['accessors'][ai]
    bv = g['bufferViews'][a['bufferView']]
    n, dt = NC[a['type']], CT[a['componentType']]
    assert bv.get('byteStride') in (None, n * np.dtype(dt).itemsize)
    arr = np.frombuffer(buf, dt, a['count'] * n, bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(a['count'], n)
    if a.get('normalized'):
        arr = arr.astype(np.float64) / np.iinfo(dt).max
    return arr.astype(np.float64) if dt == np.float32 else arr


def sections(P, UV, F, y):
    """The closed loops where the bark triangles cross the plane at height y: lists of (point, a vertex of the edge)."""
    bark = UV[:, 0] >= 0.75 - 1e-4
    key = lambda i: tuple(np.round(P[i], 5))
    pts, adj = {}, {}
    for t in F:
        if not bark[t].all():
            continue
        cut = []
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            ya, yb = P[a, 1] - y, P[b, 1] - y
            if (ya < 0) != (yb < 0):
                k = tuple(sorted((key(a), key(b))))
                if k not in pts:
                    s = ya / (ya - yb)
                    pts[k] = (P[a] + (P[b] - P[a]) * s, a)
                cut.append(k)
        if len(cut) == 2:
            adj.setdefault(cut[0], []).append(cut[1])
            adj.setdefault(cut[1], []).append(cut[0])
    loops, seen = [], set()
    for k0 in adj:
        if k0 in seen:
            continue
        loop, prev, k = [], None, k0
        while k not in seen:
            seen.add(k)
            loop.append(pts[k])
            nxt = [n for n in adj[k] if n != prev and n not in seen]
            if not nxt:
                break
            prev, k = k, nxt[0]
        if len(loop) >= 3:
            loops.append(loop)
    return loops


def cap_mesh(P, N, UV, C, F, y):
    """The arrays with the caps (old ones stripped first) and the number of cap triangles."""
    old = np.abs(C[:, 2] - CAP_B) < 0.05
    if old.any():
        keep = ~old
        remap = np.cumsum(keep) - 1
        F = F[keep[F].all(axis=1)]
        F = remap[F]
        P, N, UV, C = P[keep], N[keep], UV[keep], C[keep]
    P, N, UV, C, F = list(P), list(N), list(UV), list(C), [tuple(f) for f in F]
    PA = np.array(P)
    tris = 0
    for loop in sections(PA, np.array(UV), np.array(F), y):
        q = np.array([p for p, _ in loop])
        cx, cz = q[:, 0].mean(), q[:, 2].mean()
        rw = float(np.mean(np.hypot(q[:, 0] - cx, q[:, 2] - cz)))
        alpha = C[loop[0][1]][3]
        base = len(P)
        for p in [np.array([cx, y, cz])] + list(q):
            P.append(np.array([p[0], y, p[2]])); N.append(np.array([0.0, 1.0, 0.0]))
            UV.append(np.array([0.875 + 0.2 * (p[0] - cx), 0.5 + 0.2 * (p[2] - cz)]))
            C.append(np.array([0.6, min(1.0, rw * 2.0), CAP_B, alpha]))
        m = len(q)
        for i in range(m):
            F.append((base, base + 1 + i, base + 1 + (i + 1) % m))
        tris += m
    return np.array(P), np.array(N), np.array(UV), np.array(C), np.array(F), tris


def write(path, g, arrays):
    """g's buffer rewritten from arrays (accessor index: numpy array), one buffer view each."""
    out = bytearray()
    views = []
    for ai, a in enumerate(g['accessors']):
        arr = arrays[ai]
        if a['type'] == 'SCALAR' and a['componentType'] in (5123, 5125):
            a['componentType'] = 5125 if arr.max() > 65535 else 5123
            data = arr.astype(CT[a['componentType']]).tobytes()
            target = 34963
        elif a.get('normalized'):
            dt = CT[a['componentType']]
            data = np.round(np.clip(arr, 0, 1) * np.iinfo(dt).max).astype(dt).tobytes()
            target = 34962
        else:
            data = arr.astype(np.float32).tobytes()
            target = 34962
        while len(out) % 4:
            out.append(0)
        views.append({'buffer': 0, 'byteLength': len(data), 'byteOffset': len(out), 'target': target})
        out += data
        a['bufferView'] = ai
        a.pop('byteOffset', None)
        a['count'] = int(arr.shape[0] * (arr.shape[1] if a['type'] == 'SCALAR' and arr.ndim > 1 else 1))
        if a['type'] == 'VEC3' and 'max' in a:
            a['max'] = [float(v) for v in arr.max(axis=0)]; a['min'] = [float(v) for v in arr.min(axis=0)]
    g['bufferViews'] = views
    g['buffers'][0]['byteLength'] = len(out)
    with open(os.path.join(os.path.dirname(path), g['buffers'][0]['uri']), 'wb') as f:
        f.write(out)
    with open(path, 'w') as f:
        json.dump(g, f, indent=None, separators=(',', ':'))


def run(fname, y):
    path = os.path.join(FLORA, fname)
    g = json.load(open(path))
    assert all('bufferView' not in im for im in g.get('images', []))
    buf = open(os.path.join(FLORA, g['buffers'][0]['uri']), 'rb').read()
    arrays = {ai: read(g, buf, ai) for ai in range(len(g['accessors']))}
    report = []
    for m in g['meshes']:
        for pr in m['primitives']:
            at = pr['attributes']
            if m['name'] not in ('lod0', 'lod1', 'lod2'):
                continue
            P, N, UV, C = (arrays[at[k]] for k in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'COLOR_0'))
            F = arrays[pr['indices']].reshape(-1, 3).astype(np.int64)
            P, N, UV, C, F, tris = cap_mesh(P, N, UV, C, F, y)
            arrays[at['POSITION']], arrays[at['NORMAL']], arrays[at['TEXCOORD_0']], arrays[at['COLOR_0']] = P, N, UV, C
            arrays[pr['indices']] = F.reshape(-1, 1)
            report.append(f"{m['name']} +{tris} tris")
    write(path, g, arrays)
    print(fname, 'cut at', y, ':', ', '.join(report))


if __name__ == '__main__':
    sp = json.load(open(SPECIES))['species']
    for s in sys.argv[1:] or ['spruce', 'alder', 'snag']:
        y = sp[s]['shader']['crown_keep']
        files = [f'{s}.gltf'] if sp[s].get('packed') else [f'{p}.gltf' for p in sp[s]['pieces']]
        for f in files:
            run(f, y)
