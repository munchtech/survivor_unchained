"""Our own rocks, pebbles and ford stepping stones (E5), sculpted here from noise: no kit, no scan.

    python tools/assets/env_rocks.py tex                               the stone sheet (painted, paint_tex 'rock')
    blender -b -P tools/assets/env_rocks.py -- mesh [--preset boulder]   the pieces (every preset if none named)
    then  Godot_console --headless --path godot --import               (frames.py does not reimport)

Out: godot/art/world/flora/stone_albedo.png (RGBA: the painted stone, its alpha the moss's breakup) and
stone_normal.png, one tiling sheet every stone piece shares (drawn triplanar in world space, kit.gdshader's
OWN_ROCK; its palette is data, godot/data/flora_species.json "stone"); and <preset>.gltf (+ .bin), each
preset's variants packed in one file (told apart per vertex, COLOR.a = (index + 0.5) / 8, one draw for all of
them, as env_trees.py's packed species), with meshes lod0, lod1, lod2 and (a caster) shadow.

Each piece: an icosphere (80k triangles) pushed out along each direction to a shape (an ellipsoid, cut by
soft planes for the angular ones, noise, strata, a flattened top or foot), its faces under the ground cut
away, then decimated per LOD. Every LOD's normals are the dense sculpt's (nearest vertex), so a 2k-triangle
rock shades as the 80k one did (no flat facets close up), and its vertex colour is baked on the dense one:
  r  edge wear: how convex at a few cm (its rims and ridges, lightened in the shader)
  g  cavity: how concave at a few cm (cracks, joints, the gaps between pebbles)
  b  broad occlusion: concave at the piece's own scale (under a ledge, between the stones' lobes)
  a  the variant (packed)
Authored at the kit's own size (Rock_Medium_1-3: about 3.2 x 2.8 m, 2 m high; Pebble_*: 0.45 m), so the
zones' placements keep their sizes; the stepping stones at their real size (a causeway lays them, Dressing).
Blender is z up here; glTF is y up (the exporter turns it).
"""
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'godot', 'art', 'world', 'flora')
DATA = os.path.join(ROOT, 'godot', 'data', 'flora_species.json')

# ---------------------------------------------------------------- presets (data: each a list of variants)
# shape: 'ax' the ellipsoid's half sizes (x, y, z up) and 'cz' its middle's height; 'planes' how many soft cuts
# (angular faces), 'k' their softness (the bevel, m), 'tilt' how far from level their normals may lean (1: any);
# 'amp'/'freq' the noise (lumps), 'fine' a finer noise; 'strata' layers (cliff); 'top' a flattened top's height;
# 'foot' where the flattened foot lies; 'cut' faces wholly under this height are dropped (under the ground).
# lods: triangles per variant at lod0, lod1, lod2; shadow: lod2 cast as the piece's shadow (else it casts none).
PRESETS = {
    # river boulder: rounded, water-worn, a few broad soft facets (the kit's boulders: scale ~1.7, 5 m across)
    'boulder': dict(lods=(2200, 700, 220), shadow=True, variants=[
        dict(seed=101, ax=(1.6, 1.3, 1.2), cz=0.8, planes=4, k=0.35, tilt=0.6, amp=0.07, freq=1.1, fine=0.012, foot=-0.45, cut=-0.3),
        dict(seed=113, ax=(1.5, 1.45, 1.05), cz=0.75, planes=5, k=0.3, tilt=0.7, amp=0.08, freq=1.3, fine=0.012, foot=-0.45, cut=-0.3),
        dict(seed=127, ax=(1.7, 1.2, 1.25), cz=0.85, planes=3, k=0.4, tilt=0.5, amp=0.06, freq=0.9, fine=0.01, foot=-0.45, cut=-0.3),
        dict(seed=131, ax=(1.45, 1.35, 1.15), cz=0.7, planes=6, k=0.28, tilt=0.8, amp=0.09, freq=1.5, fine=0.012, foot=-0.45, cut=-0.3),
    ]),
    # field rock: angular, broken faces with soft bevels, lichened in the shader (the kit's 'rock': scale ~0.6, squashed)
    'fieldrock': dict(lods=(1600, 500, 160), shadow=True, variants=[
        dict(seed=201, ax=(1.6, 1.35, 1.25), cz=0.75, planes=9, k=0.07, tilt=1.0, amp=0.05, freq=1.6, fine=0.014, foot=-0.45, cut=-0.3),
        dict(seed=211, ax=(1.7, 1.2, 1.2), cz=0.8, planes=8, k=0.06, tilt=1.0, amp=0.05, freq=1.8, fine=0.014, foot=-0.45, cut=-0.3),
        dict(seed=223, ax=(1.5, 1.4, 1.3), cz=0.7, planes=11, k=0.08, tilt=1.0, amp=0.04, freq=1.4, fine=0.012, foot=-0.45, cut=-0.3),
        dict(seed=227, ax=(1.65, 1.3, 1.1), cz=0.85, planes=7, k=0.05, tilt=0.9, amp=0.06, freq=2.0, fine=0.016, foot=-0.45, cut=-0.3),
        dict(seed=229, ax=(1.55, 1.45, 1.2), cz=0.75, planes=10, k=0.07, tilt=1.0, amp=0.05, freq=1.6, fine=0.014, foot=-0.45, cut=-0.3),
    ]),
    # cliff / outcrop chunk: blocky, stratified in layers (each its own inset, a joint between), stacks (scale ~5: 17 m)
    'cliff': dict(lods=(6000, 1800, 500), shadow=True, variants=[
        dict(seed=301, ax=(1.65, 1.45, 1.25), cz=0.75, planes=8, k=0.06, tilt=0.35, amp=0.05, freq=1.4, fine=0.01, strata=5, foot=-0.45, cut=-0.3),
        dict(seed=307, ax=(1.7, 1.35, 1.3), cz=0.7, planes=7, k=0.05, tilt=0.3, amp=0.05, freq=1.6, fine=0.01, strata=6, foot=-0.45, cut=-0.3),
        dict(seed=311, ax=(1.6, 1.5, 1.2), cz=0.8, planes=9, k=0.06, tilt=0.4, amp=0.06, freq=1.2, fine=0.01, strata=4, foot=-0.45, cut=-0.3),
        dict(seed=313, ax=(1.75, 1.3, 1.25), cz=0.75, planes=8, k=0.05, tilt=0.35, amp=0.05, freq=1.5, fine=0.01, strata=5, foot=-0.45, cut=-0.3),
    ]),
    # pebble cluster: five to eight water-rounded pebbles in one piece, sunk a third (the kit's pebbles: 0.45 m, scale ~1.8)
    'pebbles': dict(lods=(600, 200, 200), shadow=False, variants=[
        dict(seed=401, n=6), dict(seed=409, n=5), dict(seed=419, n=8), dict(seed=421, n=7),
    ]),
    # ford stepping stone: flat-topped, worn round its rim, a deep body sunk in the bed (real size, m; top at 0.75)
    'stepping': dict(lods=(1200, 400, 140), shadow=False, variants=[
        dict(seed=501, ax=(0.62, 0.5, 0.6), cz=0.4, planes=6, k=0.07, tilt=0.5, amp=0.06, freq=2.2, fine=0.008, top=0.75, foot=0.0, cut=0.25),
        dict(seed=503, ax=(0.55, 0.45, 0.6), cz=0.4, planes=5, k=0.08, tilt=0.45, amp=0.07, freq=2.0, fine=0.008, top=0.75, foot=0.0, cut=0.25),
        dict(seed=509, ax=(0.7, 0.42, 0.6), cz=0.4, planes=7, k=0.06, tilt=0.5, amp=0.05, freq=2.4, fine=0.008, top=0.75, foot=0.0, cut=0.25),
        dict(seed=521, ax=(0.5, 0.5, 0.6), cz=0.4, planes=5, k=0.09, tilt=0.4, amp=0.07, freq=1.9, fine=0.008, top=0.75, foot=0.0, cut=0.25),
        dict(seed=523, ax=(0.66, 0.52, 0.6), cz=0.4, planes=8, k=0.06, tilt=0.55, amp=0.05, freq=2.3, fine=0.008, top=0.75, foot=0.0, cut=0.25),
        dict(seed=541, ax=(0.58, 0.4, 0.6), cz=0.4, planes=6, k=0.07, tilt=0.5, amp=0.06, freq=2.1, fine=0.008, top=0.75, foot=0.0, cut=0.25),
    ]),
}


def arg(name, default):
    a = sys.argv
    return a[a.index(name) + 1] if name in a else default


def stone_data():
    with open(DATA, encoding='utf-8') as f:
        return json.load(f)['stone']


# ---------------------------------------------------------------- the stone sheet (numpy + paint_tex, no Blender)

def srgb(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def tnoise(N, cells, rng, aniso=1.0):
    """Tileable value noise, N x N, 'cells' across (x stretched by aniso: a grain)."""
    import cv2
    cy, cx = cells, max(1, int(round(cells / aniso)))
    g = rng.random((cy, cx)).astype(np.float32)
    big = np.tile(g, (3, 3))
    r = cv2.resize(big, (3 * N, 3 * N), interpolation=cv2.INTER_CUBIC)
    return r[N:2 * N, N:2 * N]


def fbm(N, rng, octs, aniso=1.0):
    out = np.zeros((N, N), np.float32)
    tot = 0
    for c, w in octs:
        out += w * tnoise(N, c, rng, aniso); tot += w
    return out / tot


def cracks(N, n, rng):
    """Tileable Voronoi edges (a few joints and cracks), 0 on a crack, rising away from it (px)."""
    from scipy.spatial import cKDTree
    pts = rng.random((n, 2)) * N
    allp = np.concatenate([pts + [dx * N, dy * N] for dx in (-1, 0, 1) for dy in (-1, 0, 1)])
    t = cKDTree(allp)
    ys, xs = np.mgrid[0:N, 0:N].astype(np.float32)
    d, _ = t.query(np.stack([xs.ravel(), ys.ravel()], 1), k=2)
    return (d[:, 1] - d[:, 0]).reshape(N, N)


def tex():
    sys.path.insert(0, os.path.dirname(__file__))
    import paint_tex as pt
    from PIL import Image
    sd = stone_data()
    pal = [srgb(h) for h in sd['palette']]           # dark to light
    warm, cool = srgb(sd['warm']), srgb(sd['cool'])
    N = 1024
    rng = np.random.default_rng(7)
    # the stone's body: broad value patches (the brush scale), a faint grain along x, small pits
    body = fbm(N, rng, ((3, 0.45), (6, 0.3), (12, 0.15), (24, 0.1)))
    grain = fbm(N, rng, ((8, 0.6), (20, 0.4)), aniso=3.0)
    pits = fbm(N, rng, ((48, 0.6), (96, 0.4)))
    cr = cracks(N, 14, rng)
    crack = 1 - smooth(0.0, 5.0, cr + 6 * (fbm(N, rng, ((16, 1.0),)) - 0.5))
    crack *= smooth(0.35, 0.65, fbm(N, rng, ((5, 1.0),)))   # (cracks broken, not a net)
    hgt = 0.55 * body + 0.2 * grain + 0.12 * smooth(0.55, 0.85, pits) - 0.35 * crack
    # colour: dark to light by the body and grain, warm and cool patches, the cracks dark
    v = np.clip(0.15 + 0.85 * (0.65 * body + 0.35 * grain - 0.1), 0, 1)
    seg = v * (len(pal) - 1)
    i0 = np.clip(seg.astype(int), 0, len(pal) - 2)
    t = (seg - i0)[..., None]
    P = np.stack(pal)
    col = P[i0] * (1 - t) + P[i0 + 1] * t
    wc = fbm(N, rng, ((4, 0.6), (9, 0.4)))
    col = col + (warm - col) * (0.35 * smooth(0.55, 0.8, wc))[..., None] + (cool - col) * (0.3 * smooth(0.55, 0.2, wc))[..., None]
    col = col * (1 - 0.55 * crack)[..., None] * (1 - 0.12 * smooth(0.6, 0.9, pits))[..., None]
    gy, gx = np.gradient(np.tile(hgt, (3, 3))[N - 1:2 * N + 1, N - 1:2 * N + 1] * 6.0)
    gy, gx = gy[1:-1, 1:-1], gx[1:-1, 1:-1]
    nrm = np.dstack([-gx, gy, np.ones_like(hgt)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    nrm = nrm * 0.5 + 0.5
    p = pt.paint(col, nrm, pt.preset('rock', sd.get('paint', {})))
    # the moss's breakup (alpha): soft clumps, so moss grows in patches, not as a flat coat
    moss = smooth(0.3, 0.75, fbm(N, rng, ((6, 0.5), (14, 0.3), (40, 0.2))))
    os.makedirs(OUT, exist_ok=True)
    a = np.dstack([p, moss])
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'stone_albedo.png'))
    Image.fromarray((np.clip(nrm, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'stone_normal.png'))
    for name, nm in (('stone_albedo.png', 0), ('stone_normal.png', 1)):
        imp = os.path.join(OUT, name + '.import')
        if not os.path.exists(imp):
            with open(imp, 'w', encoding='utf-8') as f:
                f.write(pt.IMPORT.format(src=f'res://art/world/flora/{name}').replace('compress/normal_map=2', f'compress/normal_map={nm or 2}'))
    lab = p.reshape(-1, 3).mean(0)
    print('stone sheet: mean sRGB', np.round(lab * 255).astype(int), 'value 5/50/95%', np.percentile(p.mean(2), [5, 50, 95]).round(3))


# ---------------------------------------------------------------- the sculpt (Blender)

def icosphere(sub):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    V = np.array([v.co[:] for v in bm.verts], np.float64)
    F = np.array([[v.index for v in f.verts] for f in bm.faces], np.int64)
    bm.free()
    return V, F


def fbm3(P, freq, seed, octs=4):
    from mathutils import noise, Vector
    off = Vector((seed * 7.13, seed * 3.71, seed * 5.37))
    out = np.zeros(len(P))
    for i, p in enumerate(P):
        a, f, s = 1.0, freq, 0.0
        q = Vector(p)
        for _ in range(octs):
            s += a * noise.noise(q * f + off)
            a *= 0.5; f *= 2.03
        out[i] = s
    return out


def softmin(R, k):
    m = R.min(1, keepdims=True)
    return (m - k * np.log(np.exp(-(R - m) / k).sum(1, keepdims=True)))[:, 0]


def sculpt(prm):
    """One piece's dense mesh (V, F), z up, its foot's ground at z = 0."""
    rng = np.random.default_rng(prm['seed'])
    D, F = icosphere(7)
    ax = np.array(prm['ax'])
    re = 1 / np.sqrt(((D / ax) ** 2).sum(1))
    R = [re]
    for _ in range(prm.get('planes', 0)):
        n = rng.normal(size=3)
        n[2] *= prm['tilt']
        n /= np.linalg.norm(n)
        if rng.random() < 0.5 and prm['tilt'] < 0.5:
            n[2] = abs(n[2])
        rn = 1 / math.sqrt(((n / ax) ** 2).sum())
        dist = rn * rng.uniform(0.72, 0.92)
        dn = D @ n
        R.append(np.where(dn > 1e-3, dist / np.maximum(dn, 1e-3), 1e3))
    r = softmin(np.stack(R, 1), prm['k']) if len(R) > 1 else re
    P = D * r[:, None]
    r *= 1 + prm['amp'] * fbm3(P, prm['freq'], prm['seed'])
    P = D * r[:, None]
    P += D * (prm['fine'] * fbm3(P, 6.0, prm['seed'] + 1, 3))[:, None]
    if prm.get('strata'):
        # layers: each its own inset and a joint between (an undercut notch), the joints a little wavy
        L = prm['strata']
        h = (P[:, 2] + ax[2]) / (2 * ax[2]) * L + 0.25 * fbm3(P, 0.5, prm['seed'] + 2, 2)
        li = np.floor(h).astype(int)
        insets = rng.uniform(0.0, 0.11, L + 3)
        fr = h - li
        inset = insets[np.clip(li, 0, L + 2)] + 0.05 * (smooth(0.12, 0.0, fr) + smooth(0.88, 1.0, fr))
        P[:, :2] *= (1 - inset)[:, None]
    P[:, 2] += prm['cz']
    if 'top' in prm:
        # a worn flat top: the stone's crown pressed to 'top' (soft rim), dished by a few mm
        k = 0.05
        z = P[:, 2]
        P[:, 2] = -k * np.log(np.exp(-z / k) + np.exp(-prm['top'] / k)) + 0.006 * fbm3(P, 3.0, prm['seed'] + 3, 2)
    k = 0.08
    z = P[:, 2]
    P[:, 2] = k * np.log(np.exp(z / k) + np.exp(prm['foot'] / k))
    return P, F


def pebble_cluster(prm):
    rng = np.random.default_rng(prm['seed'])
    Vs, Fs, o = [], [], 0
    placed = []
    for i in range(prm['n']):
        rad = rng.uniform(0.045, 0.11) * (1.3 if i == 0 else 1.0)
        for _ in range(40):
            c = rng.uniform(-0.17, 0.17, 2)
            if all(np.linalg.norm(c - q) > (rad + qr) * 0.8 for q, qr in placed):
                break
        placed.append((c, rad))
        D, F = icosphere(4)
        ax = np.array([rad, rad * rng.uniform(0.6, 0.9), rad * rng.uniform(0.4, 0.6)])
        ang = rng.uniform(0, math.pi)
        Rz = np.array([[math.cos(ang), -math.sin(ang), 0], [math.sin(ang), math.cos(ang), 0], [0, 0, 1]])
        P = (D * ax) * (1 + 0.08 * fbm3(D, 1.4, prm['seed'] + i, 2))[:, None]
        P = P @ Rz.T + np.array([c[0], c[1], ax[2] * 0.45])
        Vs.append(P); Fs.append(F + o); o += len(P)
    return np.concatenate(Vs), np.concatenate(Fs)


def vertex_normals(V, F):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    N = np.zeros_like(V)
    for j in range(3):
        np.add.at(N, F[:, j], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def bake(V, F):
    """Edge wear, cavity and broad occlusion per dense vertex (r, g, b), from the surface's convexity at two scales."""
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    deg = np.bincount(E[:, 0], minlength=len(V)).astype(np.float64)
    N = vertex_normals(V, F)

    def lap(S, it):
        for _ in range(it):
            acc = np.zeros_like(S)
            np.add.at(acc, E[:, 0], S[E[:, 1]])
            S = 0.5 * S + 0.5 * acc / np.maximum(deg, 1)[:, None]
        return S
    def laps(x, it):
        for _ in range(it):
            acc = np.zeros_like(x)
            np.add.at(acc, E[:, 0], x[E[:, 1]])
            x = 0.5 * x + 0.5 * acc / np.maximum(deg, 1)
        return x
    s4 = lap(V.copy(), 6)
    s40 = lap(s4, 60)
    # (each relative to its own surroundings, so a rounded rock is not all 'convex'; then by percentile, so every
    # piece has its rims and cracks whatever its size: about the top tenth worn, a tenth in cavity)
    c4 = ((V - s4) * N).sum(1)
    c4 = c4 - laps(c4, 40)
    c40 = ((V - s40) * N).sum(1)
    c40 = c40 - laps(c40, 150)
    q = np.percentile
    r = smooth(q(c4, 78), q(c4, 96), c4)
    g = smooth(q(-c4, 80), q(-c4, 97), -c4)
    b = smooth(q(-c40, 75), q(-c40, 97), -c40)
    return np.stack([r, g, b], 1), N


def decimate(V, F, tris):
    """The mesh at about 'tris' triangles (Blender's collapse)."""
    import bpy
    me = bpy.data.meshes.new('d')
    me.from_pydata(V.tolist(), [], F.tolist())
    ob = bpy.data.objects.new('d', me)
    bpy.context.scene.collection.objects.link(ob)
    if tris < len(F):
        m = ob.modifiers.new('dec', 'DECIMATE')
        m.ratio = tris / len(F)
        dg = bpy.context.evaluated_depsgraph_get()
        em = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    else:
        em = me
    em.calc_loop_triangles()
    V2 = np.array([v.co[:] for v in em.vertices])
    F2 = np.array([t.vertices[:] for t in em.loop_triangles])
    bpy.data.objects.remove(ob)
    return V2, F2


def cut(V, F, z):
    """Faces wholly under z dropped (under the ground), and the vertices no face keeps."""
    keep = ~(V[F][:, :, 2] < z).all(1)
    F = F[keep]
    used = np.unique(F)
    remap = -np.ones(len(V), np.int64); remap[used] = np.arange(len(used))
    return V[used], remap[F]


def mesh(only=None):
    import bpy
    from mathutils import kdtree
    os.makedirs(OUT, exist_ok=True)
    report = {}
    for name, pre in PRESETS.items():
        if only and name != only:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        mat = bpy.data.materials.new(f'Stone_Own{name.capitalize()}')
        mat.use_nodes = True
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.3, 0.29, 0.27, 1)
        mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.85
        dense = []
        for vi, prm in enumerate(pre['variants']):
            V, F = pebble_cluster(prm) if name == 'pebbles' else sculpt(prm)
            C, N = bake(V, F)
            kd = kdtree.KDTree(len(V))
            for i, q in enumerate(V):
                kd.insert(q, i)
            kd.balance()
            dense.append((V, F, C, N, kd))
            print(f'  {name} {vi}: {len(F)} dense tris, size {np.ptp(V, 0).round(2)}, edge>0.5 {np.mean(C[:, 0] > 0.5):.2f} cavity>0.5 {np.mean(C[:, 1] > 0.5):.2f} broad>0.5 {np.mean(C[:, 2] > 0.5):.2f}')
        tris = []
        names = ['lod0', 'lod1', 'lod2'] + (['shadow'] if pre['shadow'] else [])
        for li, nm in enumerate(names):
            target = pre['lods'][min(li, 2)]
            allV, allN, allC, allF, o = [], [], [], [], 0
            for vi, (V, F, C, N, kd) in enumerate(dense):
                # (the dense mesh cut first, so the triangles go to what shows)
                cz = pre['variants'][vi].get('cut')
                Vc, Fc = (V, F) if cz is None else cut(V, F, cz)
                Vd, Fd = decimate(Vc, Fc, target)
                idx = np.array([kd.find(p)[1] for p in Vd])
                allV.append(Vd); allN.append(N[idx]); allF.append(Fd + o)
                allC.append(np.concatenate([C[idx], np.full((len(Vd), 1), (vi + 0.5) / 8)], 1))
                o += len(Vd)
            V, F, N, C = np.concatenate(allV), np.concatenate(allF), np.concatenate(allN), np.concatenate(allC)
            me = bpy.data.meshes.new(nm)
            me.from_pydata(V.tolist(), [], F.tolist())
            for p in me.polygons:
                p.use_smooth = True
            me.normals_split_custom_set_from_vertices([tuple(n) for n in N])
            ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
            ca.data.foreach_set('color', C.astype(np.float32).ravel())
            me.color_attributes.active_color = ca
            me.materials.append(mat)
            ob = bpy.data.objects.new(nm, me)
            bpy.context.scene.collection.objects.link(ob)
            tris.append(len(F) // len(dense))
        out = os.path.join(OUT, f'{name}.gltf')
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLTF_SEPARATE', export_texture_dir='', export_normals=True,
                                  export_tangents=False, export_materials='EXPORT', export_image_format='AUTO',
                                  export_keep_originals=True, export_yup=True, export_apply=True,
                                  export_vertex_color='ACTIVE')
        report[name] = dict(zip(names, tris))
        print(f'{out} tris per variant {dict(zip(names, tris))}')
    print('REPORT', json.dumps(report))


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    if argv and argv[0] == 'tex':
        tex()
    elif argv and argv[0] == 'mesh':
        mesh(arg('--preset', None))
    else:
        print(__doc__)
