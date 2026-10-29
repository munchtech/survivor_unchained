"""Fill a built piece's triangle fans with rings (armor 17 N5).

The Warden's pauldrons showed a fan of rays at the Look (judge OJ2): each lame's broad face is one fan of long thin
triangles from a single pole vertex (Blender's n-gon, triangulated on export). A highlight on a fan follows its
spokes, whatever its normals: across each 3 cm sliver the normal is interpolated linearly, and its slope kinks at
every spoke. Smoothing the normals alone barely dimmed it (OUTFIT_DEBUG_VIEW=5 kept every ray).

This cuts every spoke of each fan into rings (about --step metres apart) and gives the new points the normal of a
smooth surface (a quadratic fitted to the fan's outer ring and its pole), eased to the ring's own normals at the outer
row so the rolled rims join as before. The new points' other data (UVs, baked edge/convexity/sky, colour, skin
weights) are interpolated along their spoke. Positions stay on the old facets (the change is under a millimetre's
sag at the Look; the shading is what showed). Old vertices keep their indices (the new go at the end), so anything
keyed to the piece's vertices still holds.

    python tools/armor/fan_fill.py godot/art/armor/plate_pauldrons_warden.gltf plate_pauldrons_warden.pauldrons.steel
        [--step 0.003] [--min-fan 8] [--dry]

Idempotent: a filled fan has no sliver fan left, so a second run finds nothing.
"""
import argparse, json, os
import numpy as np

CT = {5126: 'f4', 5123: 'u2', 5125: 'u4', 5121: 'u1'}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read(g, buf, i):
    a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]
    dt = np.dtype(CT[a['componentType']]).newbyteorder('<'); n = NC[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    st = bv.get('byteStride', dt.itemsize * n)
    if st != dt.itemsize * n: raise SystemExit('interleaved buffers are not handled')
    return np.frombuffer(bytes(buf[off: off + st * a['count']]), dt).reshape(a['count'], n).copy()


def fans(T, P, min_fan):
    """Each pole (a vertex with at least min_fan sliver triangles round it) and its incident triangles."""
    A, B, C = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    area2 = np.linalg.norm(np.cross(B - A, C - A), axis=1)
    L = np.stack([np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1), np.linalg.norm(A - C, axis=1)], 1)
    aspect = L.max(1) ** 2 / np.maximum(area2, 1e-15)          # (longest edge over its altitude)
    sliver = (aspect > 6.0) & (L.max(1) > 0.012)
    cnt = np.bincount(T[sliver].ravel(), minlength=len(P))
    poles = []
    for v in np.argsort(-cnt):
        if cnt[v] < min_fan: break
        poles.append(int(v))
    out, used = [], np.zeros(len(T), bool)
    for v in poles:
        tri = np.nonzero((T == v).any(1) & ~used)[0]
        if np.count_nonzero(sliver[tri]) < min_fan: continue
        used[tri] = True
        out.append((v, tri))
    return out


def quad_fit(P, N, idx):
    """A height field z = quadratic(x, y) over the mean normal's plane, through points idx: (origin, frame, coefs)."""
    z = N[idx].mean(0); z /= np.linalg.norm(z)
    x = np.cross([0.0, 1.0, 0.0], z)
    if np.linalg.norm(x) < 1e-3: x = np.cross([1.0, 0.0, 0.0], z)
    x /= np.linalg.norm(x); y = np.cross(z, x)
    o = P[idx].mean(0)
    d = P[idx] - o; u, v, h = d @ x, d @ y, d @ z
    s = max(np.abs(u).max(), np.abs(v).max(), 1e-6)       # (scaled to the patch, so the cubic stays well posed)
    c = np.linalg.lstsq(basis(u / s, v / s), h, rcond=None)[0]
    return o, (x, y, z), c, s


def basis(u, v):
    """A cubic in (u, v) (ten terms; a quadratic left the cop's broad wrap 2.7 mm off)."""
    return np.stack([np.ones_like(u), u, v, u * u, u * v, v * v, u ** 3, u * u * v, u * v * v, v ** 3], -1)


def quad_normal(fit, q):
    o, (x, y, z), c, s = fit
    d = q - o; u, v = d @ x / s, d @ y / s
    hu = (c[1] + 2 * c[3] * u + c[4] * v + 3 * c[6] * u * u + 2 * c[7] * u * v + c[8] * v * v) / s
    hv = (c[2] + c[4] * u + 2 * c[5] * v + c[7] * u * u + 2 * c[8] * u * v + 3 * c[9] * v * v) / s
    n = -np.asarray(hu)[..., None] * x - np.asarray(hv)[..., None] * y + z
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def sstep(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def mix_weights(J0, W0, J1, W1, t):
    acc = {}
    for j, w in zip(J0, W0): acc[int(j)] = acc.get(int(j), 0.0) + (1 - t) * float(w)
    for j, w in zip(J1, W1): acc[int(j)] = acc.get(int(j), 0.0) + t * float(w)
    top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]
    s = sum(w for _, w in top) or 1.0
    J = [j for j, _ in top] + [0] * (4 - len(top)); W = [w / s for _, w in top] + [0.0] * (4 - len(top))
    return J, W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('gltf'); ap.add_argument('mesh')
    ap.add_argument('--step', type=float, default=0.003); ap.add_argument('--min-fan', type=int, default=8)
    ap.add_argument('--blend', type=float, default=0.004, help='metres from the pole and the outer ring over which the new normals ease to theirs')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    g = json.load(open(a.gltf))
    binp = os.path.join(os.path.dirname(a.gltf), g['buffers'][0]['uri'])
    buf = bytearray(open(binp, 'rb').read())
    mesh = [m for m in g['meshes'] if m['name'] == a.mesh]
    if not mesh: raise SystemExit(f'no mesh {a.mesh}')
    new_views = {}                                    # accessor index -> new bytes
    for prim in mesh[0]['primitives']:
        att = {k: read(g, buf, i) for k, i in prim['attributes'].items()}
        T = read(g, buf, prim['indices']).astype(np.int64).reshape(-1, 3)
        P = att['POSITION'].astype(float); N = att['NORMAL'].astype(float)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        F = fans(T, P, a.min_fan)
        if not F: print(f'{a.mesh}: no fans'); continue
        cols = {k: [] for k in att}                       # (new vertices' attribute rows)
        nv = len(P); keep = np.ones(len(T), bool); add_tris = []
        # (a fan cut by UV seams comes as several poles at one place, each with a wedge: one fit for them all, so the
        # wedges' normals agree where they meet; the plate's two faces (normals apart) kept apart)
        groups = []
        for pole, tri in F:
            for gi, (gp, gt) in enumerate(groups):
                if np.linalg.norm(P[gp[0]] - P[pole]) < 0.003 and N[gp[0]] @ N[pole] > 0.5:
                    gp.append(pole); gt.append(tri); break
            else: groups.append(([pole], [tri]))
        fits = {}
        for gp, gt in groups:
            allv = np.unique(np.concatenate([T[t].ravel() for t in gt]))
            fit = quad_fit(P, N, allv)
            o, (x, y, z), c, s = fit
            d = P[allv] - o; h = d @ z
            r = h - basis(d @ x / s, d @ y / s) @ c
            print(f'  group of {len(gp)} poles at {np.round(P[gp[0]], 3)}: {len(allv)} points, fit residual p90 {np.percentile(abs(r), 90) * 1000:.2f} mm')
            for pl in gp: fits[pl] = fit
        for pole, tri in F:
            ring = np.unique(T[tri].ravel()); ring = ring[ring != pole]
            fit = fits[pole]
            res = np.degrees(np.arccos(np.clip((quad_normal(fit, P[ring]) * N[ring]).sum(1), -1, 1)))
            K = max(1, int(np.ceil(max(np.linalg.norm(P[ring] - P[pole], axis=1)) / a.step)))
            L = {int(b): float(np.linalg.norm(P[b] - P[pole])) for b in ring}
            spoke = {}                                    # outer vertex -> [pole, p1 .. p(K-1), outer]
            fq = quad_normal(fit, P[pole])
            for b in ring:
                pts = [pole]
                for k in range(1, K):
                    t = k / K
                    q = (1 - t) * P[pole] + t * P[b]
                    # (eased to the pole's and the ring's own normals only within --blend of them: the ring's normals
                    # step from spoke to spoke (the rolled rim's rows), and carried further in they drew the rays again)
                    wp = sstep(1.0 - min(t * L[b] / a.blend, 1.0)); wb = sstep(1.0 - min((1 - t) * L[b] / a.blend, 1.0))
                    n = quad_normal(fit, q) + wp * (N[pole] - fq) + wb * (N[b] - quad_normal(fit, P[b]))
                    n /= np.linalg.norm(n)
                    if os.environ.get("FAN_DEBUG"): n = np.array([0.0, 0.0, 1.0])
                    for key, arr in att.items():
                        if key == 'POSITION': row = q
                        elif key == 'NORMAL': row = n
                        elif key.startswith('JOINTS') or key.startswith('WEIGHTS'): continue
                        else: row = (1 - t) * arr[pole].astype(float) + t * arr[b].astype(float)
                        cols[key].append(row)
                    if 'JOINTS_0' in att:
                        J, W = mix_weights(att['JOINTS_0'][pole], att['WEIGHTS_0'][pole], att['JOINTS_0'][b], att['WEIGHTS_0'][b], t)
                        cols['JOINTS_0'].append(J); cols['WEIGHTS_0'].append(W)
                    pts.append(nv); nv += 1
                pts.append(int(b)); spoke[int(b)] = pts
            for ti in tri:
                t3 = list(T[ti]); r = t3.index(pole); p_, A_, B_ = t3[r], t3[(r + 1) % 3], t3[(r + 2) % 3]
                SA, SB = spoke[A_], spoke[B_]
                for k in range(K):
                    a0, a1, b0, b1 = SA[k], SA[k + 1], SB[k], SB[k + 1]
                    add_tris.append((a0, a1, b1))
                    if k > 0: add_tris.append((a0, b1, b0))
            keep[tri] = False
            print(f'  pole {pole} at {np.round(P[pole], 3)}: {len(tri)} triangles, {len(ring)} spokes, {K} rings; '
                  f'quadratic vs ring normals p50 {np.percentile(res, 50):.1f} p90 {np.percentile(res, 90):.1f} deg')
        T2 = np.concatenate([T[keep], np.array(add_tris, np.int64)])
        print(f'{a.mesh}: {len(F)} fans, verts {len(P)} -> {nv}, tris {len(T)} -> {len(T2)}')
        if a.dry: continue
        for key, i in prim['attributes'].items():
            acc = g['accessors'][i]; dt = np.dtype(CT[acc['componentType']]).newbyteorder('<')
            arr = np.concatenate([att[key], np.array(cols[key]).astype(float).reshape(-1, att[key].shape[1])])
            if acc.get('normalized') and dt.kind == 'u':
                arr = np.clip(np.round(arr), 0, np.iinfo(dt).max) if np.issubdtype(att[key].dtype, np.integer) else arr
            arr = arr.astype(dt)
            acc['count'] = len(arr)
            if key == 'POSITION': acc['min'] = arr.min(0).astype(float).tolist(); acc['max'] = arr.max(0).astype(float).tolist()
            new_views[i] = arr.tobytes()
        ia = g['accessors'][prim['indices']]
        if nv > 65535: ia['componentType'] = 5125
        idx = T2.ravel().astype(np.dtype(CT[ia['componentType']]).newbyteorder('<'))
        ia['count'] = len(idx); new_views[prim['indices']] = idx.tobytes()
    if a.dry or not new_views: return
    # the buffer rewritten, every view in order, the changed ones with their new bytes (4-byte aligned)
    out = bytearray(); view_bytes = {}
    for ai, acc in enumerate(g['accessors']):
        if ai in new_views: view_bytes[acc['bufferView']] = new_views[ai]
    for vi, bv in enumerate(g['bufferViews']):
        data = view_bytes.get(vi)
        if data is None: data = bytes(buf[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']])
        while len(out) % 4: out.append(0)
        bv['byteOffset'] = len(out); bv['byteLength'] = len(data); out += data
    g['buffers'][0]['byteLength'] = len(out)
    open(binp, 'wb').write(bytes(out))
    with open(a.gltf, 'w') as fh: json.dump(g, fh, indent=1)
    print('written', a.gltf, binp)


if __name__ == '__main__':
    main()
