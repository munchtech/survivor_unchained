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
    # (E5c, judge r2: the soft-faceted ones read as smooth grey domes: each now broken by 'fract' (2-3) real fracture planes,
    # flat faces 'fdepth' of its radius in, their rims a hard 'fk' m bevel the bake lights; set facing up-and-out 'fup' so the
    # play camera, looking down, sees them, spaced round it)
    # (lf5c, the lf0 triage: "grey block-like boulders", FAR: rebuilt from planes (sculpt_frac), not pushed noise: a cracked block,
    # a tilted slab, a half-sunk water-worn one, a chipped angular one; each about the old one's size)
    'boulder': dict(lods=(2200, 700, 220), shadow=True, variants=[
        dict(method='frac', seed=1101, ax=(1.6, 1.3, 1.15), cz=0.75, fn=11, ftop=5, fup=(0.55, 0.85), fd=(0.74, 0.94), fk=0.08, chips=6, chip_d=(0.06, 0.14), ledges=1, splits=1, split_w=0.06, split_d=0.15, lump=0.025, fcrown=0.84, amp=0.012, freq=0.8, fine=0.006, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1113, ax=(1.7, 1.4, 0.95), cz=0.6, fn=10, ftop=4, fup=(0.75, 0.92), fd=(0.8, 0.95), fk=0.07, chips=5, chip_d=(0.06, 0.12), ledges=2, ledge_d=(0.12, 0.2), strata=4, strata_d=0.035, lean=8, lump=0.05, amp=0.01, freq=0.8, fine=0.006, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1127, ax=(1.6, 1.35, 1.15), cz=0.6, sink=0.15, fn=9, ftop=4, fup=(0.5, 0.8), fd=(0.76, 0.92), fk=0.1, round=1.02, ledges=1, chips=4, chip_d=(0.06, 0.12), lump=0.06, amp=0.015, freq=0.9, fine=0.006, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1131, ax=(1.5, 1.4, 1.15), cz=0.75, fn=9, ftop=4, fup=(0.45, 0.85), fd=(0.72, 0.95), fk=0.06, chips=7, chip_d=(0.06, 0.15), ledges=2, splits=1, split_w=0.05, split_d=0.13, lump=0.06, amp=0.01, freq=0.9, fine=0.006, foot=-0.45, cut=-0.3),
    ]),
    # field rock: angular, broken faces with soft bevels, lichened in the shader (the kit's 'rock': scale ~0.6, squashed)
    # (lf5c, the lf0 triage on the boulders and field rocks: "grey block-like": now broken from planes (sculpt_frac): an angular
    # chunk, a tilted slab standing out of the ground, a low half-sunk one with a ledge, one cracked in two, a chipped one)
    'fieldrock': dict(lods=(1600, 500, 160), shadow=True, variants=[
        dict(method='frac', seed=1201, ax=(1.6, 1.35, 1.2), cz=0.58, side_z=(0.05, 0.5), fn=13, ftop=4, fup=(0.5, 0.85), fd=(0.7, 0.93), fk=0.05, chips=7, chip_d=(0.06, 0.14), ledges=1, splits=1, split_w=0.05, split_d=0.12, lump=0.06, amp=0.01, freq=1.0, fine=0.007, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1211, ax=(1.75, 1.0, 1.2), cz=0.48, side_z=(0.05, 0.5), fn=12, ftop=3, fup=(0.6, 0.85), fd=(0.8, 0.94), fk=0.05, chips=5, chip_d=(0.05, 0.12), strata=5, strata_d=0.03, lean=16, lump=0.06, amp=0.01, freq=1.0, fine=0.007, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1223, ax=(1.6, 1.45, 1.05), cz=0.38, side_z=(0.05, 0.5), sink=0.1, fn=13, ftop=5, fup=(0.65, 0.9), fd=(0.7, 0.93), fk=0.06, chips=6, chip_d=(0.06, 0.13), ledges=2, lump=0.06, amp=0.012, freq=1.0, fine=0.007, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1227, ax=(1.65, 1.3, 1.1), cz=0.58, side_z=(0.05, 0.5), fn=14, ftop=5, fup=(0.5, 0.85), fd=(0.7, 0.94), fk=0.05, chips=6, chip_d=(0.05, 0.12), splits=1, split_w=0.11, split_d=0.32, lump=0.06, amp=0.01, freq=1.0, fine=0.007, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1229, ax=(1.55, 1.45, 1.15), cz=0.58, side_z=(0.05, 0.5), fn=15, ftop=5, fup=(0.45, 0.85), fd=(0.72, 0.93), fk=0.045, chips=9, chip_d=(0.05, 0.14), ledges=1, lump=0.06, amp=0.01, freq=1.0, fine=0.007, foot=-0.45, cut=-0.3),
    ]),
    # cliff / outcrop chunk: blocky, stratified in layers (each its own inset, a joint between), stacks (scale ~5: 17 m)
    'cliff': dict(lods=(6000, 1800, 500), shadow=True, variants=[
        dict(seed=301, ax=(1.65, 1.45, 1.25), cz=0.75, planes=8, k=0.06, tilt=0.35, amp=0.05, freq=1.4, fine=0.01, strata=5, foot=-0.45, cut=-0.3),
        dict(seed=307, ax=(1.7, 1.35, 1.3), cz=0.7, planes=7, k=0.05, tilt=0.3, amp=0.05, freq=1.6, fine=0.01, strata=6, foot=-0.45, cut=-0.3),
        dict(seed=311, ax=(1.6, 1.5, 1.2), cz=0.8, planes=9, k=0.06, tilt=0.4, amp=0.06, freq=1.2, fine=0.01, strata=4, foot=-0.45, cut=-0.3),
        dict(seed=313, ax=(1.75, 1.3, 1.25), cz=0.75, planes=8, k=0.05, tilt=0.35, amp=0.05, freq=1.5, fine=0.01, strata=5, foot=-0.45, cut=-0.3),
    ]),
    # pebble cluster (E5c, judge r2: not 6-12 equal pale balls): one anchor, one or two middling, one to three small (three
    # sizes), each 1-2 of its diameters from its neighbour, flat (height 0.45 of its width) and sunk 30%; each stone its own
    # colour (UV: u its class, slate / ochre / umber, v its value; the shader's 'stone_mix') (the kit's pebbles: 0.45 m, scale ~1.8)
    'pebbles': dict(lods=(600, 200, 200), shadow=False, variants=[
        dict(seed=401, n=(1, 2, 2)), dict(seed=409, n=(1, 1, 2)), dict(seed=419, n=(1, 2, 3)), dict(seed=421, n=(1, 1, 1)),
    ]),
    # ford stepping stone (C03 env fix; was E5b's rounded slab, which from a camera at the water read as a row of hockey
    # pucks: vertical sides, flat pale tops): now a river stone, its crown a dome (an ellipsoid's top, no pressed top) at
    # about 0.75 m, 'sides' (5-7) soft cuts leaning back ('side_lean') round an ellipse of L:W 1.2-1.8 for its outline
    # from over it, two soft 'planes' and one fracture breaking a side off the dome, its body deeper than its crown
    # ('az_lo') and taken in a little under its widest ('waist': the river's undercut, shown where it stands tall);
    # its sizes and tilts, and how proud it stands, Dressing's (the causeway's data)
    # (lf5c, lf4: the stepping stones read as brown loaves, smooth domes with pale foam rings: now river stones broken from planes
    # (sculpt_frac): a low faceted crown (three near-level faces, no flat lid, no dome), sides leaning back ('side_z'), worn
    # rims 3 cm, chips off its edges, one in three cracked or stepped; the crown at about 0.75 m as before (Dressing's 'top')
    'stepping': dict(lods=(1200, 400, 140), shadow=False, variants=[
        dict(method='frac', seed=1501, ax=(0.604, 0.416, 0.25), az_lo=0.6, cz=0.52, fn=9, ftop=3, fup=(0.78, 0.92), fcrown=0.9, side_z=(0.1, 0.4), fd=(0.8, 0.92), fk=0.03, round=1.05, chips=5, chip_d=(0.04, 0.09), lump=0.04, amp=0.012, freq=1.5, fine=0.004, foot=-0.2, cut=0.05),
        dict(method='frac', seed=1503, ax=(0.632, 0.357, 0.22), az_lo=0.6, cz=0.52, fn=8, ftop=3, fup=(0.78, 0.92), fcrown=0.9, side_z=(0.1, 0.4), fd=(0.8, 0.92), fk=0.03, round=1.05, chips=5, chip_d=(0.04, 0.09), splits=1, split_w=0.025, split_d=0.05, lump=0.04, amp=0.012, freq=1.5, fine=0.004, foot=-0.2, cut=0.05),
        dict(method='frac', seed=1509, ax=(0.651, 0.34, 0.27), az_lo=0.6, cz=0.52, fn=10, ftop=3, fup=(0.78, 0.92), fcrown=0.9, side_z=(0.1, 0.4), fd=(0.8, 0.92), fk=0.03, round=1.05, chips=5, chip_d=(0.04, 0.09), ledges=1, ledge_d=(0.12, 0.2), lump=0.04, amp=0.012, freq=1.5, fine=0.004, foot=-0.2, cut=0.05),
        dict(method='frac', seed=1537, ax=(0.558, 0.408, 0.24), az_lo=0.6, cz=0.52, fn=8, ftop=3, fup=(0.78, 0.92), fcrown=0.9, side_z=(0.1, 0.4), fd=(0.8, 0.92), fk=0.03, round=1.05, chips=5, chip_d=(0.04, 0.09), lump=0.04, amp=0.012, freq=1.5, fine=0.004, foot=-0.2, cut=0.05),
        dict(method='frac', seed=1523, ax=(0.604, 0.383, 0.26), az_lo=0.6, cz=0.52, fn=10, ftop=3, fup=(0.78, 0.92), fcrown=0.9, side_z=(0.1, 0.4), fd=(0.8, 0.92), fk=0.03, round=1.05, chips=5, chip_d=(0.04, 0.09), splits=1, split_w=0.025, split_d=0.05, lump=0.04, amp=0.012, freq=1.5, fine=0.004, foot=-0.2, cut=0.05),
        dict(method='frac', seed=1541, ax=(0.632, 0.442, 0.23), az_lo=0.6, cz=0.52, fn=9, ftop=3, fup=(0.78, 0.92), fcrown=0.9, side_z=(0.1, 0.4), fd=(0.8, 0.92), fk=0.03, round=1.05, chips=5, chip_d=(0.04, 0.09), ledges=1, ledge_d=(0.12, 0.2), lump=0.04, amp=0.012, freq=1.5, fine=0.004, foot=-0.2, cut=0.05),
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


def fractures(N, n, rng):
    """Tileable long open fractures (E5b, judge: not a polygon net): n wandering lines, each 0.4-0.75 of the sheet long,
    drawn on a 3 x 3 tiling so they wrap; returns each pixel's distance to the nearest (px) and that line's own width."""
    import cv2
    M = np.zeros((3 * N, 3 * N), np.uint8)
    W = np.zeros((3 * N, 3 * N), np.float32)
    for j in range(n):
        p = rng.random(2) * N
        ang = rng.uniform(0, math.pi)
        L = rng.uniform(0.4, 0.75) * N
        w = rng.uniform(1.6, 3.2)
        pts = [p.copy()]
        for _ in range(int(L / 6)):
            ang += rng.normal(0, 0.12)
            p = p + 6 * np.array([math.cos(ang), math.sin(ang)])
            pts.append(p.copy())
        P = np.array(pts)
        for dx in (0, 1, 2):
            for dy in (0, 1, 2):
                q = (P + [dx * N, dy * N]).astype(np.int32).reshape(-1, 1, 2)
                cv2.polylines(M, [q], False, 255, 1)
                cv2.polylines(W, [q], False, float(w), 7)
    d = cv2.distanceTransform((255 - M), cv2.DIST_L2, 5)
    W = cv2.dilate(W, np.ones((9, 9), np.uint8))
    return d[N:2 * N, N:2 * N], np.maximum(W[N:2 * N, N:2 * N], 1.6)


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
    # (E5b: a few long open fractures, 2-3 across a stepping stone, fading in and out along their length; not a net)
    fd, fw = fractures(N, int(sd.get('fractures', 8)), rng)
    crack = 1 - smooth(0.0, fw, fd + 1.5 * (fbm(N, rng, ((24, 1.0),)) - 0.5))
    crack *= smooth(0.25, 0.55, fbm(N, rng, ((4, 1.0),)))
    hgt = 0.55 * body + 0.2 * grain + 0.035 * smooth(0.55, 0.85, pits) - 0.22 * crack   # (E5b: pits faint: at 0.12 their lit rims read as a crazed net)
    # colour: dark to light by the body and grain, warm and cool patches, the cracks dark
    v = np.clip(0.15 + 0.85 * (0.65 * body + 0.35 * grain - 0.1), 0, 1)
    # (lf5c: 'contrast' spreads the value about its middle (the lf4 sheet's p5-p95 luma was .29-.45: one flat grey-brown from
    # the play camera); 'speck' a granite's light and dark grains (feldspar, mica: a sparkle of value at 1:1, not a smooth wash);
    # 'blotch' broad dark weathered patches (where water sat: a value break across a face))
    v = np.clip(0.5 + float(sd.get('contrast', 1.0)) * (v - 0.5), 0, 1)
    if sd.get('speck'):
        sp = fbm(N, rng, ((160, 0.6), (320, 0.4)))
        v = np.clip(v + float(sd['speck']) * (smooth(0.62, 0.72, sp) - 0.7 * smooth(0.36, 0.28, sp)), 0, 1)
    if sd.get('blotch'):
        bl = fbm(N, rng, ((5, 0.6), (11, 0.4)))
        v = v * (1 - float(sd['blotch']) * smooth(0.55, 0.75, bl))
    seg = v * (len(pal) - 1)
    i0 = np.clip(seg.astype(int), 0, len(pal) - 2)
    t = (seg - i0)[..., None]
    P = np.stack(pal)
    col = P[i0] * (1 - t) + P[i0 + 1] * t
    wc = fbm(N, rng, ((4, 0.6), (9, 0.4)))
    col = col + (warm - col) * (0.35 * smooth(0.55, 0.8, wc))[..., None] + (cool - col) * (0.3 * smooth(0.55, 0.2, wc))[..., None]
    col = col * (1 - float(sd.get('crack_dark', 0.28)) * crack)[..., None] * (1 - 0.05 * smooth(0.6, 0.9, pits))[..., None]
    gy, gx = np.gradient(np.tile(hgt, (3, 3))[N - 1:2 * N + 1, N - 1:2 * N + 1] * 6.0)
    gy, gx = gy[1:-1, 1:-1], gx[1:-1, 1:-1]
    nrm = np.dstack([-gx, gy, np.ones_like(hgt)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    nrm = nrm * 0.5 + 0.5
    p = pt.paint(col, nrm, pt.preset('rock', sd.get('paint', {})))
    # (lf5c: 'post_contrast' the painted sheet's value spread about its mean, after the brush (which evens it): the value
    # the play camera sees is the 5-50 cm patches, a 5 m boulder ~250 px across, so its range lives there, not in grains)
    if sd.get('post_contrast'):
        lum = p.mean(2, keepdims=True)
        m = float(lum.mean())
        p = np.clip(p * (m + float(sd['post_contrast']) * (lum - m)) / np.maximum(lum, 1e-3), 0, 1)
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
    # ('az_lo': the ellipsoid's half height under its middle, if not ax z: a body deeper than its crown)
    axd = np.where(D[:, 2:3] < 0, np.array([ax[0], ax[1], prm.get('az_lo', ax[2])]), ax)
    re = 1 / np.sqrt(((D / axd) ** 2).sum(1))
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
    if prm.get('sides'):
        # (a slab's outline: 'sides' near-vertical cuts spaced round it, each a little off even, inside the ellipse)
        ns = prm['sides']
        for j in range(ns):
            th = 2 * math.pi * (j + rng.uniform(-0.22, 0.22)) / ns
            # ('side_lean': the cuts lean back that far (normal's z), a shoulder's facets, not a wall; else near vertical)
            lean = prm.get('side_lean')
            n = np.array([math.cos(th), math.sin(th), rng.uniform(*lean) if lean else rng.uniform(-0.08, 0.08)])
            n /= np.linalg.norm(n)
            rn = 1 / math.sqrt(((n / ax) ** 2).sum())
            dist = rn * rng.uniform(0.8, 0.88)
            dn = D @ n
            R.append(np.where(dn > 1e-3, dist / np.maximum(dn, 1e-3), 1e3))
    r = softmin(np.stack(R, 1), prm['k']) if len(R) > 1 else re
    if prm.get('fract'):
        # fracture planes: spaced round it (each a little off even), leaning up by fup, cut fdepth of its radius in, hard rims
        nf = prm['fract']
        a0 = rng.uniform(0, 2 * math.pi)
        Rf = [r]
        for j in range(nf):
            th = a0 + 2 * math.pi * (j + rng.uniform(-0.18, 0.18)) / nf
            up = rng.uniform(*prm['fup'])
            n = np.array([math.cos(th) * math.sqrt(1 - up * up), math.sin(th) * math.sqrt(1 - up * up), up])
            dn = D @ n
            # (its depth against the soft body's own surface that way, not the ellipsoid's: the soft cuts sit well inside it)
            rn = r[np.argmax(dn)]
            Rf.append(np.where(dn > 1e-3, rn * rng.uniform(*prm['fdepth']) / np.maximum(dn, 1e-3), 1e3))
        Rf = np.stack(Rf, 1)
        r = softmin(Rf, prm['fk'])
        # (the faces, for the report: each plane's share of the surface it is (within 1 cm))
        prm['_faces'] = [float(np.mean((Rf[:, j] - r < 0.01) & (Rf[:, 0] - Rf[:, j] > 0.02))) for j in range(1, nf + 1)]
    P = D * r[:, None]
    flat = np.zeros(len(r))
    if prm.get('fract'):
        # (a fracture face stays near flat: its lumps a fifth of the body's)
        flat = smooth(0.0, 0.03, Rf[:, 0] - r) * 0.8
    r *= 1 + prm['amp'] * (1 - flat) * fbm3(P, prm['freq'], prm['seed'])
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
    if prm.get('waist'):
        # (a waist under its widest: the river's undercut at the waterline, 'waist' of its width taken in 'waist_h' m down)
        wz = smooth(0.0, prm.get('waist_h', 0.18), -P[:, 2])
        P[:, :2] *= (1 - prm['waist'] * wz)[:, None]
    P[:, 2] += prm['cz']
    if 'top' in prm:
        # a worn flat top: the stone's crown pressed to 'top' (soft rim, E5c: a 3-4 cm bevel, 'rim_k'), dished by a few mm
        k = prm.get('rim_k', 0.035)
        z = P[:, 2]
        # (a low crown: the pressed height falls 'dome' m from its middle to its rim)
        # ('peak' (x, y): the crown's high point off its middle, as a share of its half sizes: a lopsided dome)
        pk = prm.get('peak', (0.0, 0.0))
        tz = prm['top'] - prm.get('dome', 0.0) * np.clip(((P[:, 0] - pk[0] * ax[0]) / ax[0]) ** 2 + ((P[:, 1] - pk[1] * ax[1]) / ax[1]) ** 2, 0, 1.6)
        P[:, 2] = -k * np.log(np.exp(-z / k) + np.exp(-tz / k)) + 0.004 * fbm3(P, 3.0, prm['seed'] + 3, 2)
    k = 0.08
    z = P[:, 2]
    P[:, 2] = k * np.log(np.exp(z / k) + np.exp(prm['foot'] / k))
    return P, F


def sculpt_frac(prm):
    """(lf5c) A broken stone: one dense mesh (V, F), z up, its foot's ground at z = 0, cut from planes, not pushed by noise.

    The lf0 triage: the noise-pushed ellipsoids read as "grey block-like boulders" (soft domes, or rounded cubes) from the
    play camera. Here the body is a convex block of 'fn' fracture planes (each its support's 'fd' share in: a broken
    face), 'ftop' of them leaning up-and-out (normals 'fup' z: the faces the camera looks down on, set round it so they
    catch the moon in turn), the rest round its sides; their meeting edges worn only 'fk' m (crisp-but-worn rims the bake
    lights); then 'chips' small planes taking an edge off ('chip_d' its radius deep: a broken outline, not a box);
    'splits' grooves through it (a joint, 'split_w' m wide, 'split_d' deep, fading along it: a cracked boulder), 'strata'
    shallow bands (sandstone's bedding: value lines on its sides), a little 'amp' wave (no face dead flat) and 'fine'.
    'sink' lowers it into the ground (a half-sunk stone, its foot under the grass), 'lean' tilts it (deg).
    """
    rng = np.random.default_rng(prm['seed'])
    D, F = icosphere(7)
    ax = np.array(prm['ax'], np.float64)
    # ('az_lo': its body's half depth under its middle, if not ax z: a stone deeper than its crown)
    axd = np.where(D[:, 2:3] < 0, np.array([ax[0], ax[1], prm.get('az_lo', ax[2])]), ax)
    re = 1 / np.sqrt(((D / axd) ** 2).sum(1))

    def support(n):
        return math.sqrt(((ax * n) ** 2).sum())

    def plane(n, d):
        dn = D @ n
        return np.where(dn > 1e-3, d / np.maximum(dn, 1e-3), 1e3)

    R = [re * prm.get('round', 1.08)]
    nt, ns = prm['ftop'], prm['fn'] - prm['ftop']
    a0 = rng.uniform(0, 2 * math.pi)
    for j in range(nt):
        th = a0 + 2 * math.pi * (j + rng.uniform(-0.25, 0.25)) / max(nt, 1)
        up = rng.uniform(*prm['fup']) if j else rng.uniform(0.9, 0.98)   # (one near-level crown face, 'fcrown' in: a broad top, not a peak)
        n = np.array([math.cos(th) * math.sqrt(1 - up * up), math.sin(th) * math.sqrt(1 - up * up), up])
        R.append(plane(n, support(n) * (rng.uniform(*prm['fd']) if j else prm.get('fcrown', 0.8))))
    a1 = rng.uniform(0, 2 * math.pi)
    for j in range(ns):
        th = a1 + 2 * math.pi * (j + rng.uniform(-0.3, 0.3)) / max(ns, 1)
        z = rng.uniform(*prm.get('side_z', (-0.25, 0.3)))
        n = np.array([math.cos(th) * math.sqrt(1 - z * z), math.sin(th) * math.sqrt(1 - z * z), z])
        R.append(plane(n, support(n) * rng.uniform(*prm['fd'])))
    r = softmin(np.stack(R, 1), prm['fk'])
    # chips: small planes taking an edge or a corner off (where the body is most convex: its corners stand furthest out)
    for _ in range(prm.get('chips', 0)):
        far = r / re
        cand = np.argsort(-far + 0.15 * rng.random(len(far)))[:400]
        i = cand[rng.integers(len(cand))]
        q = D[i] * r[i]
        n = D[i] + rng.normal(size=3) * 0.3
        if rng.random() < 0.6:
            n[2] = abs(n[2]) * 0.8 + 0.1
        n /= np.linalg.norm(n)
        d = max(q @ n - rng.uniform(*prm['chip_d']) * float(np.mean(ax)), 0.5 * r[i])
        r = softmin(np.stack([r, plane(n, d)], 1), prm['fk'] * 0.7)
    # ledges: a step taken out of its crown's edge (where it is over the plane 'n1' and past the side plane 'n2': a notch, its
    # floor a ledge that holds moss and litter, its riser a lit or shaded wall; not a convex gem)
    for _ in range(prm.get('ledges', 0)):
        th = rng.uniform(0, 2 * math.pi)
        hz = np.array([math.cos(th), math.sin(th), 0.0])
        n1 = np.array([0.0, 0.0, 1.0]) + hz * rng.uniform(-0.15, 0.25)
        n1 /= np.linalg.norm(n1)
        top = float((D * r[:, None] @ n1).max())
        d1 = top - rng.uniform(*prm.get('ledge_d', (0.15, 0.3))) * ax[2] * 2
        n2 = hz + np.array([0, 0, rng.uniform(-0.1, 0.2)])
        n2 /= np.linalg.norm(n2)
        side = float((D * r[:, None] @ n2).max())
        d2 = side * rng.uniform(0.3, 0.6)
        t = np.maximum(plane(n1, d1), plane(n2, d2))
        r = softmin(np.stack([r, t], 1), prm['fk'] * 0.8)
    # lumps: the faces bent a little (a broad noise on the radius), so its outline is not a polygon's
    if prm.get('lump'):
        r *= 1 + prm['lump'] * fbm3(D, prm.get('lump_f', 0.8), prm['seed'] + 5, 2)
    P = D * r[:, None]
    # a little wave over every face (none dead flat), and the fine grain
    P += D * (prm['amp'] * float(np.mean(ax)) * fbm3(P, prm['freq'], prm['seed'], 3))[:, None]
    P += D * (prm['fine'] * fbm3(P, 5.0, prm['seed'] + 1, 3))[:, None]
    # splits: a joint through the stone (a near-vertical plane near its middle), a V groove fading along its length
    for s in range(prm.get('splits', 0)):
        th = rng.uniform(0, math.pi)
        n = np.array([math.cos(th), math.sin(th), rng.uniform(-0.35, 0.35)])
        n /= np.linalg.norm(n)
        c = np.array([rng.uniform(-0.25, 0.25) * ax[0], rng.uniform(-0.25, 0.25) * ax[1], 0.0])
        sd = (P - c) @ n
        w = prm['split_w'] * (1 + 0.5 * fbm3(P, 1.2, prm['seed'] + 10 + s, 2))
        along = smooth(0.15, 0.55, 0.5 + fbm3(P, 0.45, prm['seed'] + 20 + s, 2))   # (it fades in and out)
        g = np.exp(-(sd / np.maximum(w, 0.01)) ** 2) * along
        P -= D * (prm['split_d'] * g)[:, None]
    if prm.get('strata'):
        L = prm['strata']
        h = (P[:, 2] + ax[2]) / (2 * ax[2]) * L + 0.3 * fbm3(P, 0.6, prm['seed'] + 2, 2)
        fr = h - np.floor(h)
        notch = smooth(0.1, 0.0, fr) + smooth(0.9, 1.0, fr)
        side = np.clip(1 - np.abs(D[:, 2]) * 1.4, 0, 1)                  # (on its sides, not its crown)
        P -= D * (prm.get('strata_d', 0.03) * notch * side)[:, None]
    if prm.get('lean'):
        a = math.radians(prm['lean']) * rng.choice([-1, 1])
        b = rng.uniform(0, 2 * math.pi)
        k = np.array([math.cos(b), math.sin(b), 0.0])
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        Rm = np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K
        P = P @ Rm.T
    P[:, 2] += prm['cz'] - prm.get('sink', 0.0)
    k = 0.06
    z = P[:, 2]
    P[:, 2] = k * np.log(np.exp(z / k) + np.exp(prm['foot'] / k))
    return P, F


def pebble_cluster(prm):
    """A cluster's stones (V, F) and each dense vertex's UV (u its colour class's middle, v its value: one per stone)."""
    rng = np.random.default_rng(prm['seed'])
    Vs, Fs, Us, o = [], [], [], 0
    placed = []
    # (sizes: anchor 8-9.5 cm, middling 4.5-5.5, small 2.2-3 (radius; in the zone at scale ~1.8))
    sizes = [rng.uniform(0.08, 0.095) for _ in range(prm['n'][0])]         + [rng.uniform(0.045, 0.055) for _ in range(prm['n'][1])] + [rng.uniform(0.022, 0.03) for _ in range(prm['n'][2])]
    cls = rng.permutation([0, 1, 2] * 3)
    for i, rad in enumerate(sizes):
        c = np.zeros(2)
        if placed:
            for _ in range(200):
                q, qr = placed[rng.integers(len(placed))]
                # (a gap of 1-2 of the smaller one's diameter from a neighbour, never nearer than one to any other)
                gap = rng.uniform(1.0, 2.0) * 2 * min(rad, qr)
                a = rng.uniform(0, 2 * math.pi)
                c = q + (rad + qr + gap) * np.array([math.cos(a), math.sin(a)])
                if all(np.linalg.norm(c - p2) >= rad + r2 + 1.0 * 2 * min(rad, r2) - 1e-6 for p2, r2 in placed):
                    break
        placed.append((c, rad))
        D, F = icosphere(4)
        ax = np.array([rad, rad * rng.uniform(0.7, 0.9), rad * 0.45])
        ang = rng.uniform(0, math.pi)
        Rz = np.array([[math.cos(ang), -math.sin(ang), 0], [math.sin(ang), math.cos(ang), 0], [0, 0, 1]])
        P = (D * ax) * (1 + 0.07 * fbm3(D, 1.4, prm['seed'] + i, 2))[:, None]
        # (sunk 30% of its height: its middle 0.4 of its half-height up)
        P = P @ Rz.T + np.array([c[0], c[1], ax[2] * 0.4])
        Vs.append(P); Fs.append(F + o); o += len(P)
        Us.append(np.tile([(cls[i % len(cls)] + 0.5) / 3, rng.random()], (len(P), 1)))
    V = np.concatenate(Vs)
    V[:, :2] -= V[:, :2].mean(0)
    gaps = []
    for i, (c, r) in enumerate(placed):
        gaps.append(min((np.linalg.norm(c - c2) - r - r2) / (2 * min(r, r2)) for j, (c2, r2) in enumerate(placed) if j != i) if len(placed) > 1 else 0)
    print(f'  pebbles {prm["seed"]}: {len(placed)} stones, diameters (cm) {sorted(round(200 * r, 1) for _, r in placed)}, height/width 0.45,'
          f' sunk 30%, nearest gap in diameters {np.round(gaps, 2).tolist()}, classes {[int(cls[i % 9]) for i in range(len(placed))]}')
    return V, np.concatenate(Fs), np.concatenate(Us)


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
            if name == 'pebbles':
                V, F, U = pebble_cluster(prm)
            else:
                (V, F), U = (sculpt_frac(prm) if prm.get('method') == 'frac' else sculpt(prm)), None
            if U is None:
                U = np.tile([0.5, 0.5], (len(V), 1))
            C, N = bake(V, F)
            if prm.get('_faces') is not None:
                fc = prm['_faces']
                print(f'  {name} {vi}: fracture faces {sum(f > 0.03 for f in fc)} of {len(fc)} over 3% of its surface, shares {np.round(fc, 3).tolist()}')
            kd = kdtree.KDTree(len(V))
            for i, q in enumerate(V):
                kd.insert(q, i)
            kd.balance()
            dense.append((V, F, C, N, kd, U))
            if name == 'stepping':
                up = N[:, 2] > 0.9
                zt = V[up, 2]
                band = V[(V[:, 2] > prm.get('top', 0.75) - 0.15) & (V[:, 2] < prm.get('top', 0.75) - 0.1)][:, :2]
                c = band - band.mean(0)
                ev = np.linalg.eigh(np.cov(c.T))[1]
                ext = np.ptp(c @ ev, 0)
                print(f'  stepping {vi}: sides {prm.get("sides", prm.get("fn"))}, dome {zt.max() - np.percentile(zt, 3):.3f} m, footprint {ext.max():.2f} x {ext.min():.2f} m, L:W {ext.max() / ext.min():.2f}')
            print(f'  {name} {vi}: {len(F)} dense tris, size {np.ptp(V, 0).round(2)}, edge>0.5 {np.mean(C[:, 0] > 0.5):.2f} cavity>0.5 {np.mean(C[:, 1] > 0.5):.2f} broad>0.5 {np.mean(C[:, 2] > 0.5):.2f}')
        tris = []
        names = ['lod0', 'lod1', 'lod2'] + (['shadow'] if pre['shadow'] else [])
        for li, nm in enumerate(names):
            target = pre['lods'][min(li, 2)]
            allV, allN, allC, allF, allU, o = [], [], [], [], [], 0
            for vi, (V, F, C, N, kd, U) in enumerate(dense):
                # (the dense mesh cut first, so the triangles go to what shows)
                cz = pre['variants'][vi].get('cut')
                Vc, Fc = (V, F) if cz is None else cut(V, F, cz)
                Vd, Fd = decimate(Vc, Fc, target)
                idx = np.array([kd.find(p)[1] for p in Vd])
                allV.append(Vd); allN.append(N[idx]); allF.append(Fd + o); allU.append(U[idx])
                allC.append(np.concatenate([C[idx], np.full((len(Vd), 1), (vi + 0.5) / 8)], 1))
                o += len(Vd)
            V, F, N, C, UV = np.concatenate(allV), np.concatenate(allF), np.concatenate(allN), np.concatenate(allC), np.concatenate(allU)
            me = bpy.data.meshes.new(nm)
            me.from_pydata(V.tolist(), [], F.tolist())
            for p in me.polygons:
                p.use_smooth = True
            me.normals_split_custom_set_from_vertices([tuple(n) for n in N])
            ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
            ca.data.foreach_set('color', C.astype(np.float32).ravel())
            me.color_attributes.active_color = ca
            # (UV: a pebble's own colour class and value (u, v), one per stone; 0.5, 0.5 for the rest)
            uvl = me.uv_layers.new(name='UVMap')
            li = np.zeros(len(me.loops), np.int64)
            me.loops.foreach_get('vertex_index', li)
            uvl.data.foreach_set('uv', UV[li].astype(np.float32).ravel())
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
