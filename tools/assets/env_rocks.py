"""Our own rocks, pebbles and ford stepping stones (E5), sculpted here from noise: no kit, no scan.

    python tools/assets/env_rocks.py tex                               the stone sheet (painted, paint_tex 'rock')
    blender -b -P tools/assets/env_rocks.py -- mesh [--preset boulder]   the pieces (every preset if none named)
                                                                         (L1 C3a: the plane rocks, below; --form sculpt E5's)
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
    # (e22r1a, the Env 22 triage: boulder_b "a pillow/loaf with a seam" from the play camera: the zone squashes rocks and boulders
    # to 0.6 of their height (flora.bin), so near-level crown faces and a strata notch read as a soft loaf: now steeper crown
    # faces (fup 0.3-0.6), deeper cuts, a small crown, sunk 0.35, and two tilted beds (a layered step) instead of the notch)
    'boulder': dict(lods=(2200, 700, 220), shadow=True, variants=[
        dict(method='frac', seed=1101, ax=(1.6, 1.3, 1.15), cz=0.75, sink=0.3, fn=11, ftop=5, fup=(0.35, 0.7), fd=(0.66, 0.94), fk=0.08, chips=6, chip_d=(0.06, 0.14), beds=2, bed_d=0.09, bed_tilt=0.55, lump=0.025, fcrown=0.84, amp=0.012, freq=0.8, fine=0.006, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1113, ax=(1.7, 1.4, 1.3), cz=0.6, sink=0.35, fn=12, ftop=5, fup=(0.3, 0.6), fcrown=0.9, fd=(0.66, 0.86), fk=0.05, round=1.15, chips=7, chip_d=(0.06, 0.12), beds=2, bed_d=0.09, bed_tilt=0.55, lean=8, lump=0.03, amp=0.01, freq=0.8, fine=0.006, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1127, ax=(1.6, 1.35, 1.15), cz=0.6, sink=0.3, fn=9, ftop=4, fup=(0.35, 0.7), fd=(0.66, 0.92), fk=0.1, round=1.02, chips=4, chip_d=(0.06, 0.12), beds=2, bed_d=0.09, bed_tilt=0.55, lump=0.06, amp=0.015, freq=0.9, fine=0.006, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1131, ax=(1.5, 1.4, 1.15), cz=0.75, sink=0.3, fn=9, ftop=4, fup=(0.35, 0.7), fd=(0.66, 0.95), fk=0.06, chips=7, chip_d=(0.06, 0.15), beds=2, bed_d=0.09, bed_tilt=0.55, lump=0.06, amp=0.01, freq=0.9, fine=0.006, foot=-0.45, cut=-0.3),
    ]),
    # field rock: angular, broken faces with soft bevels, lichened in the shader (the kit's 'rock': scale ~0.6, squashed)
    # (lf5c, the lf0 triage on the boulders and field rocks: "grey block-like": now broken from planes (sculpt_frac): an angular
    # chunk, a tilted slab standing out of the ground, a low half-sunk one with a ledge, one cracked in two, a chipped one)
    # (e22r1a: fieldrock_b (strata seam) and fieldrock_d (split: a "hot cross bun" crease) read as round buns: rebuilt as
    # boulder_b, no splits or seams, beds instead, sunk 0.3; then every boulder and field rock: their splits and shallow
    # ledge notches read from above as creases (the gate's "hot cross bun"): gone, two tilted beds and sunk 0.3 instead)
    'fieldrock': dict(lods=(1600, 500, 160), shadow=True, variants=[
        dict(method='frac', seed=1201, ax=(1.6, 1.35, 1.2), cz=0.58, side_z=(0.05, 0.5), sink=0.3, fn=13, ftop=4, fup=(0.35, 0.7), fd=(0.66, 0.93), fk=0.05, chips=7, chip_d=(0.06, 0.14), beds=2, bed_d=0.09, bed_tilt=0.55, lump=0.06, amp=0.01, freq=1.0, fine=0.007, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1211, ax=(1.75, 1.1, 1.35), cz=0.48, side_z=(0.05, 0.5), sink=0.3, fn=13, ftop=4, fup=(0.35, 0.65), fcrown=0.9, fd=(0.64, 0.86), fk=0.05, round=1.15, chips=7, chip_d=(0.05, 0.12), beds=2, bed_d=0.09, bed_tilt=0.55, lean=12, lump=0.03, amp=0.01, freq=1.0, fine=0.007, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1223, ax=(1.6, 1.45, 1.05), cz=0.38, side_z=(0.05, 0.5), sink=0.15, fn=13, ftop=5, fup=(0.35, 0.7), fd=(0.66, 0.93), fk=0.06, chips=6, chip_d=(0.06, 0.13), beds=2, bed_d=0.09, bed_tilt=0.55, lump=0.06, amp=0.012, freq=1.0, fine=0.007, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1227, ax=(1.65, 1.3, 1.3), cz=0.58, side_z=(0.05, 0.5), sink=0.3, fn=14, ftop=5, fup=(0.35, 0.65), fcrown=0.9, fd=(0.64, 0.86), fk=0.05, round=1.15, chips=7, chip_d=(0.05, 0.12), beds=4, bed_d=0.06, lump=0.03, amp=0.01, freq=1.0, fine=0.007, foot=-0.45, cut=-0.3),
        dict(method='frac', seed=1229, ax=(1.55, 1.45, 1.15), cz=0.58, side_z=(0.05, 0.5), sink=0.3, fn=15, ftop=5, fup=(0.35, 0.7), fd=(0.66, 0.93), fk=0.045, chips=9, chip_d=(0.05, 0.14), beds=2, bed_d=0.09, bed_tilt=0.55, lump=0.06, amp=0.01, freq=1.0, fine=0.007, foot=-0.45, cut=-0.3),
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
    # (e22r1a, the triage's "pillow/loaf with a seam": a strata notch reads as one seam round a soft body) beds: 'beds' layers
    # each set back on its sides further than the one under it (by a random share of 'bed_d' of its mean radius), so each bed's top shows as a
    # ledge (moss and litter catch on it) and its outline steps: a layered stone, its bedding tilted 'bed_tilt' and wavy
    if prm.get('beds'):
        L = prm['beds']
        rb = np.random.default_rng(prm['seed'] + 3)
        sb = np.maximum.accumulate(np.cumsum(rb.uniform(-0.25, 1.0, L + 3))) * prm.get('bed_d', 0.08) * float(np.mean(ax))   # (upper beds back more: steps up its sides)
        sb[:2] = 0.0
        tb = rb.uniform(0, 2 * math.pi)
        bn = np.array([math.cos(tb) * prm.get('bed_tilt', 0.15), math.sin(tb) * prm.get('bed_tilt', 0.15), 1.0])
        bn /= np.linalg.norm(bn)
        h = ((P @ bn) + ax[2]) / (2 * ax[2]) * L + 0.25 * fbm3(P, 0.5, prm['seed'] + 4, 2)
        kb = np.clip(np.floor(h).astype(int) + 1, 0, L + 1)
        fb = h - np.floor(h)
        bw = prm.get('bed_w', 0.12)                                             # (how sharp the step: its share of a bed)
        s = sb[kb] + (sb[kb + 1] - sb[kb]) * smooth(1 - bw, 1.0, fb)
        P[:, :2] *= (1 - s / float(np.mean(ax)))[:, None]                # (taken in about its middle: the whole bed, crown and all)
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


# ---------------------------------------------------------------- the plane rocks (L1 C3a: LOOK_BIBLE rules 9 and 10)
# FROM (b) MB4's rock panel and targets 10 and 12's boulders: a few big rounded planes (a crown, two to four shoulders,
# four to six sides), muted moon-blue grey, rims rounded so the band catches them, no small facets, chips or noise;
# (a) the play camera (a plane must be 6+ px: no plane under about a sixth of the piece); (c) each preset's sizes,
# heights, cuts, variants and LOD scheme are E5's (PRESETS above), so the zones' placements keep their sizes.
# A piece is the smooth minimum (k m, its rounding) of its ellipsoid and its planes, each plane set in at fd of the
# ellipsoid's support. Its uvs: one island per plane chart (the planes' normals, and fill directions where none is
# within 50 degrees) and variant, each face projected onto its chart, all presets in one atlas (rock_atlas.png, the
# painter's: tools/look/wild.py rocks). lod0 and lod1 are one mesh (it is already cheaper than E5's lod1); lod2 and the
# shadow are decimated, their faces charted the same way.
PLANES = {
    # crown: (z of its normal low, high); sh: shoulders (count, normal z low, high); sides: (count, z low, high);
    # fd: planes set in (share of the support, low, high); k: rounding (share of the smallest half size); tris: lod0, lod2
    # (round 1 at k 0.1-0.2 and fd 0.74-0.9: the log-sum-exp of ten planes rounded a boulder into a smooth egg at play; now
    # the planes cut deeper and meet in a bevel of a few cm, rule 10's "bigger bevels" the band can catch)
    # crease (L1 W2 wild): a plane face's normal is this share its plane's, the rest its smooth normal (crease_normals)
    # (L1 l9 kit, judge 1: 06's rocks read as faceted prisms; rule 9 "a few big rounded planes", MB4's rock and T10/T12's
    # boulders: a domed crown, two or three broad shoulders, four sides, each plane shallower (fd up) and the bevels between
    # them wide (k 0.05 -> 0.16 of the smallest half size: a rim of 15-25 cm the band rolls over, not a hard edge), the
    # crease halved so a plane is a broad tilt of the shading, not a flat facet)
    'boulder': dict(crown=(0.8, 0.92), sh=(3, 0.5, 0.7), sides=(4, 0.0, 0.2), fd=(0.8, 0.9), k=0.16, tris=(700, 180), crease=0.4),
    'fieldrock': dict(crown=(0.8, 0.92), sh=(2, 0.45, 0.65), sides=(4, -0.05, 0.2), fd=(0.78, 0.9), k=0.14, tris=(600, 150), crease=0.4),
    'cliff': dict(crown=(0.9, 0.99), sh=(4, 0.3, 0.55), sides=(6, -0.15, 0.15), fd=(0.66, 0.8), k=0.035, tris=(900, 250), crease=0.75),
    'stepping': dict(crown=(0.93, 0.99), sh=(2, 0.6, 0.8), sides=(5, -0.25, 0.1), fd=(0.72, 0.85), k=0.05, tris=(300, 90), crease=0.75),
    'pebbles': dict(crown=(0.9, 0.98), sh=(2, 0.45, 0.7), sides=(3, -0.1, 0.2), fd=(0.72, 0.86), k=0.08, tris=(240, 80)),
}


def plane_set(spec, rng):
    """The planes' normals (z up): one crown, the shoulders and sides spread round the piece."""
    N = []
    a = rng.uniform(0, 2 * math.pi)
    z = rng.uniform(*spec['crown']); N.append((math.cos(a) * math.sqrt(1 - z * z), math.sin(a) * math.sqrt(1 - z * z), z))
    for cnt, lo, hi, off in ((spec['sh'][0], spec['sh'][1], spec['sh'][2], 0.3), (spec['sides'][0], spec['sides'][1], spec['sides'][2], 0.0)):
        a0 = rng.uniform(0, 2 * math.pi)
        for i in range(cnt):
            a = a0 + (i + rng.uniform(-0.18, 0.18)) * 2 * math.pi / cnt
            z = rng.uniform(lo, hi)
            N.append((math.cos(a) * math.sqrt(1 - z * z), math.sin(a) * math.sqrt(1 - z * z), z))
    return np.array(N)


def sculpt_planes(ax, center, spec, rng, sub=5):
    """One piece: (V, F, plane normals). The smooth minimum of the ellipsoid's radius and each plane's along each ray."""
    D, F = icosphere(sub)
    ax = np.asarray(ax, float)
    Np = plane_set(spec, rng)
    re = 1.0 / np.sqrt(((D / ax) ** 2).sum(1))
    sup = np.sqrt(((Np * ax) ** 2).sum(1))
    d = sup * rng.uniform(*spec['fd'], len(Np))
    cosv = D @ Np.T
    T = np.where(cosv > 1e-3, d[None, :] / np.maximum(cosv, 1e-3), 1e3)
    R = np.concatenate([re[:, None], np.minimum(T, 1e3)], 1)
    k = spec['k'] * ax.min()
    r = softmin(R, k)
    V = D * r[:, None] + np.asarray(center, float)
    return V, F, Np, dict(center=np.asarray(center, float), ax=ax, Np=Np, d=d, k=k)


def crease_weights(V, pl):
    """(L1 W2 wild) Each point's share of the ellipsoid (column 0) and of each plane (1..), the softmin's own weights at its
    rounding k: one-hot inside a plane, shared only across the bevel of a few cm between two."""
    P = V - pl['center']
    D = P / np.maximum(np.linalg.norm(P, axis=1, keepdims=True), 1e-9)
    re = 1.0 / np.sqrt(((D / pl['ax']) ** 2).sum(1))
    cosv = D @ pl['Np'].T
    T = np.where(cosv > 1e-3, pl['d'][None, :] / np.maximum(cosv, 1e-3), 1e3)
    R = np.concatenate([re[:, None], np.minimum(T, 1e3)], 1)
    e = np.exp(-(R - R.min(1, keepdims=True)) / pl['k'])
    return e / e.sum(1, keepdims=True)


def crease_normals(V0, F0, Vd, Wd, Nd, kd, Np, idx, rnd):
    """(L1 W2 wild: rule 9 "a few big rounded planes", the wave-1 judge "the planes don't step in the band") Per face corner
    (len(F0) x 3 x 3): a face on a plane (its centre's plane share over a half, from the dense mesh's nearest point) takes
    that plane's normal, rnd of its corners' smooth normals kept (rounded planes, never flat facets); a face on the
    ellipsoid's round keeps the smooth normals. So two planes meet in a step the band can catch, not a smooth roll."""
    cen = V0[F0].mean(1)
    j = np.array([kd.find(c)[1] for c in cen])
    W = Wd[j]
    Nv = Nd[idx][F0]                                  # the corners' smooth normals
    Nf = W[:, 1:] @ Np + W[:, :1] * Nd[j]
    Nf /= np.maximum(np.linalg.norm(Nf, axis=1, keepdims=True), 1e-9)
    on_plane = (W[:, 1:].max(1) > 0.5)[:, None, None]
    Nc = np.where(on_plane, (1 - rnd) * Nf[:, None, :] + rnd * Nv, Nv)
    return Nc / np.maximum(np.linalg.norm(Nc, axis=2, keepdims=True), 1e-9)


def charts_for(Np):
    """Chart directions: the planes' normals, then fill directions (the 14 of a cube's faces and corners, and straight
    down) wherever none is within 50 degrees."""
    C = [n / np.linalg.norm(n) for n in Np]
    fill = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)] + [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    for f in fill:
        f = np.array(f, float); f /= np.linalg.norm(f)
        if max(float(np.dot(f, c)) for c in C) < math.cos(math.radians(50)):
            C.append(f)
    return np.array(C)


def chart_frame(c):
    up = np.array([0.0, 0.0, 1.0]) if abs(c[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(up, c); u /= np.linalg.norm(u)
    return u, np.cross(c, u)


def face_charts(V, F, C):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    return np.argmax(fn @ C.T, 1)


def rock_atlas(pieces, A=2048, gap=8):
    """pieces: [(key, V, F, C)] (lod0). Each (key, chart)'s projected box, shelf-packed at the largest density that fits.
    Returns ({(key, chart): (u0, v0, scale, (pu0, pv0))}, px per metre)."""
    boxes = []
    for key, V, F, C in pieces:
        fc = face_charts(V, F, C)
        for ci in np.unique(fc):
            u, v = chart_frame(C[ci])
            P = V[np.unique(F[fc == ci])]
            pu, pv = P @ u, P @ v
            pad = 0.06 * max(np.ptp(pu), np.ptp(pv)) + 0.02
            boxes.append(((key, int(ci)), pu.min() - pad, pv.min() - pad, np.ptp(pu) + 2 * pad, np.ptp(pv) + 2 * pad))

    def pack(ppm):
        order = sorted(boxes, key=lambda b: (-b[4], -b[3], str(b[0])))
        x = y = gap; rowh = 0; out = {}
        for key, pu0, pv0, w, h in order:
            W, Hh = math.ceil(w * ppm), math.ceil(h * ppm)
            if x + W > A - gap:
                x, y, rowh = gap, y + rowh + gap, 0
            if y + Hh > A - gap:
                return None
            out[key] = (x / A, y / A, ppm / A, (pu0, pv0))
            x += W + gap; rowh = max(rowh, Hh)
        return out
    lo, hi = 5.0, 600.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if pack(mid):
            lo = mid
        else:
            hi = mid
    return pack(lo), lo


def corner_uvs(V, F, C, key, atlas):
    """Per face corner (len(F) x 3 x 2): each face's vertices projected onto its chart, placed in the chart's island
    (a chart this LOD has but lod0 had not: its nearest chart that lod0 has)."""
    fc = face_charts(V, F, C)
    UV = np.zeros((len(F), 3, 2))
    have = [ci for ci in range(len(C)) if (key, ci) in atlas]
    for ci in np.unique(fc):
        cj = ci if (key, int(ci)) in atlas else max(have, key=lambda h: float(np.dot(C[h], C[ci])))
        u0, v0, s, (pu0, pv0) = atlas[(key, int(cj))]
        u, v = chart_frame(C[cj])
        P = V[F[fc == ci]]
        UV[fc == ci, :, 0] = u0 + (P @ u - pu0) * s
        UV[fc == ci, :, 1] = 1 - (v0 + (P @ v - pv0) * s)
    return UV


def pebble_stones(prm, rng):
    """A pebble cluster's stones (ax, centre): E5's sizes and spacing (anchor, middling, small), each flat and sunk."""
    sizes = [rng.uniform(0.08, 0.095) for _ in range(prm['n'][0])] + [rng.uniform(0.045, 0.055) for _ in range(prm['n'][1])] \
        + [rng.uniform(0.022, 0.03) for _ in range(prm['n'][2])]
    placed = []
    for rad in sizes:
        c = np.zeros(2)
        if placed:
            for _ in range(200):
                q, qr = placed[rng.integers(len(placed))]
                gap = rng.uniform(1.0, 2.0) * 2 * min(rad, qr)
                a = rng.uniform(0, 2 * math.pi)
                c = q + (rad + qr + gap) * np.array([math.cos(a), math.sin(a)])
                if all(np.linalg.norm(c - p2) >= rad + r2 + 2 * min(rad, r2) - 1e-6 for p2, r2 in placed):
                    break
        placed.append((c, rad))
    mid = np.mean([c for c, _ in placed], 0)
    return [((rad, rad * rng.uniform(0.7, 0.9), rad * 0.45), (c[0] - mid[0], c[1] - mid[1], rad * 0.45 * 0.4)) for c, rad in placed]


def mesh_planes(only=None):
    """Every preset as plane rocks into flora/<preset>.gltf (lod0 = lod1, lod2, shadow), one material per preset
    (Stone_Own<Preset>) on rock_atlas.png; the painter's sheet godot/art/world/painted/_src/rocks_sheet.glb (every
    preset's every variant's lod0, side by side, material 'rock')."""
    import bpy
    ROOTP = os.path.join(ROOT, 'godot', 'art', 'world', 'painted', '_src')
    os.makedirs(OUT, exist_ok=True); os.makedirs(ROOTP, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    built = {}
    for name, pre in PRESETS.items():
        spec = PLANES[name]
        vs = []
        for vi, prm in enumerate(pre['variants']):
            rng = np.random.default_rng(prm['seed'] + 7)
            parts = pebble_stones(prm, rng) if name == 'pebbles' else [(prm['ax'], (0.0, 0.0, prm.get('cz', 0.6)))]
            Vs, Fs, Cs, o, pls = [], [], [], 0, []
            for ax, cen in parts:
                V, F, Np, pl = sculpt_planes(ax, cen, spec, rng, sub=5 if name != 'pebbles' else 4)
                if prm.get('cut') is not None:
                    V, F = cut(V, F, prm['cut'])
                Vs.append(V); Fs.append(F + o); Cs.append(Np); o += len(V); pls.append(pl)
            V, F = np.concatenate(Vs), np.concatenate(Fs)
            Np = np.concatenate(Cs)
            # (the creases: one piece's planes; a pebble cluster's stones stay smooth, 2-9 cm, under rule 9's 3 cm read)
            Wd = crease_weights(V, pls[0]) if len(pls) == 1 and spec.get('crease', 0) else None
            col, N = bake(V, F)
            from mathutils import kdtree
            kd = kdtree.KDTree(len(V))
            for i, q in enumerate(V):
                kd.insert(q, i)
            kd.balance()
            per = spec['tris'][0] * len(parts) if name != 'pebbles' else spec['tris'][0]
            L0 = decimate(V, F, per)
            L2 = decimate(V, F, max(spec['tris'][1], 24 * len(parts)))
            C = charts_for(Np)
            vs.append(dict(dense=(V, F, col, N, kd), L=[L0, L0, L2, L2], C=C, W=Wd, Np=Np, rnd=spec.get('crease', 0)))
            print(f'  {name} {vi}: planes {len(Np)}, charts {len(C)}, size {np.ptp(V, 0).round(2)}, lod0 {len(L0[1])} lod2 {len(L2[1])} tris')
        built[name] = vs
    atlas, ppm = rock_atlas([((nm, vi), d['L'][0][0], d['L'][0][1], d['C']) for nm, vs in built.items() for vi, d in enumerate(vs)])
    print(f'rocks: atlas {ppm:.1f} px/m')

    def obj(nm, parts, mats):
        """parts: [(V, F, UV corners, N, colour)]: one object, corner uvs, the dense normals and colours."""
        Vs, Fs, UVs, Ns, Cs, o = [], [], [], [], [], 0
        for V, F, UV, N, col in parts:
            Vs.append(V); Fs.append(F + o); UVs.append(UV); Ns.append(N); Cs.append(col); o += len(V)
        V, F, UV, N, col = np.concatenate(Vs), np.concatenate(Fs), np.concatenate(UVs), np.concatenate(Ns), np.concatenate(Cs)
        me = bpy.data.meshes.new(nm)
        me.from_pydata(V.tolist(), [], F.tolist())
        for p in me.polygons:
            p.use_smooth = True
        if N.ndim == 3:     # (per face corner: the creased planes)
            me.normals_split_custom_set([tuple(n) for n in N.reshape(-1, 3)])
        else:
            me.normals_split_custom_set_from_vertices([tuple(n) for n in N])
        ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set('color', col.astype(np.float32).ravel())
        me.color_attributes.active_color = ca
        uvl = me.uv_layers.new(name='UVMap')
        uvl.data.foreach_set('uv', UV.reshape(-1, 2).astype(np.float32).ravel())
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(nm, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob

    def piece(nm, vi, d, li, off=None):
        V0, F0 = d['L'][li]
        Vd, Fd, col, N, kd = d['dense']
        idx = np.array([kd.find(p)[1] for p in V0])
        UV = corner_uvs(V0, F0, d['C'], (nm, vi), atlas)
        C4 = np.concatenate([col[idx], np.full((len(V0), 1), (vi + 0.5) / 8)], 1)
        Nout = N[idx][F0] if d['W'] is None else crease_normals(V0, F0, Vd, d['W'], N, kd, d['Np'], idx, 1 - d['rnd'])
        return (V0 + (off if off is not None else 0), F0, UV, Nout, C4)

    # the sheet: every piece's lod0 on a grid, 8 m apart (no piece's AO reaches another)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mr = bpy.data.materials.new('rock')
    parts, k = [], 0
    for nm, vs in built.items():
        for vi, d in enumerate(vs):
            parts.append(piece(nm, vi, d, 0, np.array([8.0 * (k % 6), 8.0 * (k // 6), 0.0]))); k += 1
    obj('lod0', parts, [mr])
    bpy.ops.export_scene.gltf(filepath=os.path.join(ROOTP, 'rocks_sheet.glb'), export_format='GLB', export_normals=True,
                              export_tangents=False, export_materials='EXPORT', export_yup=True, export_apply=True,
                              export_vertex_color='ACTIVE')
    img_path = os.path.join(OUT, 'rock_atlas.png')
    report = {}
    for nm, vs in built.items():
        if only and nm != only:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        mat = bpy.data.materials.new(f'Stone_Own{nm.capitalize()}'); mat.use_nodes = True
        bsdf = mat.node_tree.nodes['Principled BSDF']
        if os.path.exists(img_path):
            ti = mat.node_tree.nodes.new('ShaderNodeTexImage'); ti.image = bpy.data.images.load(img_path)
            mat.node_tree.links.new(ti.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 1.0
        names = ['lod0', 'lod1', 'lod2'] + (['shadow'] if PRESETS[nm]['shadow'] else [])
        tris = []
        for li, on in enumerate(names):
            obj(on, [piece(nm, vi, d, min(li, 3)) for vi, d in enumerate(vs)], [mat])
            tris.append(sum(len(d['L'][min(li, 3)][1]) for d in vs) // len(vs))
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{nm}.gltf'), export_format='GLTF_SEPARATE', export_texture_dir='',
                                  export_normals=True, export_tangents=False, export_materials='EXPORT', export_image_format='AUTO',
                                  export_keep_originals=True, export_yup=True, export_apply=True, export_vertex_color='ACTIVE')
        report[nm] = dict(zip(names, tris))
        print(f'{nm}.gltf tris per variant {report[nm]}')
    print('REPORT', json.dumps(dict(rocks=report, ppm=round(ppm, 1))))


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


# ---------------------------------------------------------------- the night kit's boulders (L1 l13 K2: docs/design/NIGHT_KIT.md)
# FROM (a) the play camera (78 px per metre, 50 degrees above: a plane must be a tone the eye can count, so few and large);
# (b) target 09's boulders: block-rounded, a pale flat top, dark planar sides, a hard step between; (c) K1's contract, "tones
# step where normals step": every face is FLAT (its plane's normal on every corner, never the sculpt's), so the standing
# material picks one tone a plane. A boulder is one to three convex blocks, each the cut of a few planes: a near-level top
# (within 'ttilt' degrees of up), 'sides' planar sides leaning back 'lean' degrees, a shoulder bevel over each side (its
# normal 48-60 degrees from up: the body tone between the top and a side) and a corner bevel between two sides ('corner' m
# wide). The shoulder's size is solved so the tops cover 'top' of the footprint seen from above (the design's 35-45%).
# Albedo: rock_dabs.png, a tiling sheet of flat low-contrast dabs (no cracks, no noise), each face projected onto it in its
# own plane; drawn by OWN_ROCK's painted branch (kit.gdshader: the mesh normal as it is, no bump, no moss or lichen).
# Vertex colour: r, g, b 0 (no baked wear: the planes carry the painting), a the variant, as every packed species.
#     python tools/assets/env_rocks.py tex --kit night                        rock_dabs.png
#     blender -b -P tools/assets/env_rocks.py -- mesh --preset boulder_s      (or boulder_m, boulder_l, round_s, round_m,
#                                                                             round_l) -> <species>.gltf
#     python tools/assets/env_rocks.py sheet --kit stone --out X.png          the kit's review sheet (the play camera's angle
#                                                                             and size, three flat tones by normal) and its table
# A species' name carries no underscore (FloraSpecies.ByMaterial cuts a material's name at one), so the design's preset
# boulder_s is the species 'bouldersmall' (pieces boulder_s_a, boulder_s_b), boulder_m 'bouldermid', boulder_l 'boulderlarge'.
# TWO FORMS on the same hulls (L1 l14 S2; lead 14 on the first sheet: the blocks read as crates with lids and cut gems,
# vertical dark walls over half of each piece, where the target's boulders are rounded lumps wider than tall):
#   facet  boulder_s/m/l: lower blocks (height about 0.45 of the width), sides leaning back 12-22 degrees and unequal,
#          shoulders only on a run of neighbouring sides and never under 0.15 m wide (none on the small), no corner bevel on
#          a block under 2 m; flat normals.
#   round  round_s/m/l -> 'roundsmall', 'roundmid', 'roundlarge' (pieces round_s_a, ...): each block a low lump, a
#          super-ellipse footprint with two broad lobes under a gently domed top (its profile's exponent solved for 'top'),
#          the widest ring a little over the ground and a small tuck under it; SMOOTH normals taken from the surface itself,
#          no noise, no feature under 0.15 m. The stepped material draws its tone boundaries as curves.
DAB_TILE = 4.0      # metres the dab sheet covers
# size: a block's x, y across and its height over the ground (m); off: its place (x, y); block: how square its outline
# (2 an ellipse, 4 a block); sides; lean (degrees, low, high); ttilt (degrees); corner: the corner bevel's width (m, 0 none);
# shoulders: how many neighbouring sides carry one (default half of them)
HULLS = {
    's': [
        dict(seed=2101, blocks=[dict(size=(0.64, 0.50, 0.27), sides=5, lean=(12, 22), ttilt=(9, 15), block=2.6, corner=0.0, shoulders=0)]),
        dict(seed=2113, blocks=[dict(size=(0.84, 0.62, 0.34), sides=5, lean=(12, 22), ttilt=(9, 15), block=2.8, corner=0.0, shoulders=0)]),
    ],
    'm': [
        dict(seed=2201, blocks=[dict(size=(1.45, 1.15, 0.60), sides=5, lean=(12, 22), ttilt=(7, 13), block=2.8, corner=0.0)]),
        dict(seed=2213, blocks=[dict(size=(1.55, 1.2, 0.64), sides=6, lean=(12, 22), ttilt=(7, 12), block=3.0, corner=0.0),
                                dict(size=(0.72, 0.6, 0.32), off=(-0.62, -0.42), sides=5, lean=(12, 20), ttilt=(9, 15), block=2.6, corner=0.0, shoulders=0)]),
        dict(seed=2227, blocks=[dict(size=(1.3, 1.1, 0.62), sides=5, lean=(12, 22), ttilt=(8, 13), block=2.8, corner=0.0),
                                dict(size=(0.8, 0.7, 0.36), off=(0.55, -0.35), sides=5, lean=(12, 20), ttilt=(9, 15), block=2.6, corner=0.0, shoulders=0)]),
    ],
    'l': [
        dict(seed=2301, blocks=[dict(size=(2.6, 2.0, 1.1), sides=6, lean=(12, 22), ttilt=(6, 11), block=3.0, corner=0.24),
                                dict(size=(1.5, 1.2, 0.62), off=(1.15, -0.75), sides=5, lean=(12, 20), ttilt=(8, 13), block=2.8, corner=0.0)]),
        dict(seed=2311, blocks=[dict(size=(3.0, 2.2, 1.15), sides=7, lean=(12, 22), ttilt=(5, 10), block=3.2, corner=0.26),
                                dict(size=(1.2, 1.0, 0.5), off=(-1.2, -0.7), sides=5, lean=(12, 20), ttilt=(9, 14), block=2.6, corner=0.0)]),
        dict(seed=2323, blocks=[dict(size=(2.3, 1.9, 1.15), sides=6, lean=(12, 22), ttilt=(6, 11), block=3.0, corner=0.24, seg=28, rings=7),
                                dict(size=(1.7, 1.2, 0.75), off=(-0.85, 0.6), sides=5, lean=(12, 20), ttilt=(8, 13), block=2.8, corner=0.0),
                                dict(size=(1.0, 0.9, 0.45), off=(0.9, 1.0), sides=5, lean=(12, 20), ttilt=(9, 14), block=2.6, corner=0.0, shoulders=0)]),
    ],
}
_LONG = {'s': 'small', 'm': 'mid', 'l': 'large'}
# (hz: the round form's height over the block's; a lump as low as the facet block read as a river pebble on the sheet)
# (the small round stones stay low, 0.92: at 1.18 the one in her fire stood up as an egg in frame 09)
NIGHT = {f'{pre}_{k}': dict(species=f'{pre}{_LONG[k]}', form=form, top=top, hz=hz * (0.78 if k == 's' and form == 'round' else 1.0), variants=HULLS[k])
         for pre, form, top, hz in (('boulder', 'facet', 0.42, 1.0), ('round', 'round', 0.42, 1.18)) for k in 'sml'}
COS30 = math.cos(math.radians(30))
COS80 = math.cos(math.radians(80))


def polytope(planes):
    """planes [(n, d)], the solid n.x <= d: its faces [(plane index, polygon k x 3, counter-clockwise from outside)]."""
    Nn = np.array([p[0] for p in planes], float); Dd = np.array([p[1] for p in planes], float)
    m = len(planes)
    I = np.array([(i, j, k) for i in range(m) for j in range(i + 1, m) for k in range(j + 1, m)])
    A = Nn[I]
    ok = np.abs(np.linalg.det(A)) > 1e-7
    X = np.linalg.solve(A[ok], Dd[I[ok]][..., None])[..., 0]
    X = X[(X @ Nn.T <= Dd[None] + 1e-6).all(1)]
    faces = []
    for i in range(m):
        P = X[np.abs(X @ Nn[i] - Dd[i]) < 1e-6]
        if len(P) < 3:
            continue
        P = P[np.unique(np.round(P, 4), axis=0, return_index=True)[1]]
        if len(P) < 3:
            continue
        u, v = chart_frame(Nn[i])
        c = P.mean(0)
        faces.append((i, P[np.argsort(np.arctan2((P - c) @ v, (P - c) @ u))]))
    return faces


def night_block(bp, rng, sd, sink=0.12):
    """One block's planes [(n, d, kind)]: top, sides, a shoulder over each side set sd m down it, corner bevels, the foot."""
    ax, ay, h = bp['size'][0] / 2, bp['size'][1] / 2, bp['size'][2]
    o = np.array(list(bp.get('off', (0.0, 0.0))) + [0.0])
    n, p = bp['sides'], bp['block']
    ta, tt = rng.uniform(0, 2 * math.pi), math.radians(rng.uniform(*bp['ttilt']))
    nt = np.array([math.cos(ta) * math.sin(tt), math.sin(ta) * math.sin(tt), math.cos(tt)])
    out = [(nt, nt[2] * h, 'top')]
    a0, sides = rng.uniform(0, 2 * math.pi), []
    sh0, shn = int(rng.integers(0, n)), bp.get('shoulders', n // 2)     # (the run of sides that carry a shoulder)
    for i in range(n):
        a = a0 + (i + rng.uniform(-0.32, 0.32)) * 2 * math.pi / n       # (unequal sides: an even ring reads as a cut gem)
        r = (abs(math.cos(a) / ax) ** p + abs(math.sin(a) / ay) ** p) ** (-1 / p) * rng.uniform(0.84, 1.0)
        l = math.radians(rng.uniform(*bp['lean']))
        ns = np.array([math.cos(a) * math.cos(l), math.sin(a) * math.cos(l), math.sin(l)])
        sides.append((ns, r * math.cos(l)))
        out.append((ns, r * math.cos(l), 'side'))
        # the shoulder: through the side's point 'drop' down from the top, its normal 44-58 degrees from up; only on the
        # run of sides, and only when it is 0.18 m wide or more before the block is fitted to its size (0.15 after: under that it is a notch)
        ph, drop = math.radians(rng.uniform(44, 58)), sd * rng.uniform(0.8, 1.2)
        if (i - sh0) % n < shn and drop / math.sin(ph) >= 0.18:
            zq = h - drop
            q = np.array([math.cos(a), math.sin(a), 0.0]) * (r - zq * math.tan(l)) + np.array([0, 0, zq])
            nsh = np.array([math.cos(a) * math.sin(ph), math.sin(a) * math.sin(ph), math.cos(ph)])
            out.append((nsh, float(nsh @ q), 'shoulder'))
    if bp['corner'] > 0:
        for i in range(n):
            (n1, d1), (n2, d2) = sides[i], sides[(i + 1) % n]
            mm = n1 + n2; mm /= np.linalg.norm(mm)
            beta = 0.5 * math.acos(float(np.clip(n1 @ n2, -1, 1)))
            try:    # the corner's line at half height
                cxy = np.linalg.solve(np.array([n1[:2], n2[:2]]), np.array([d1 - n1[2] * h / 2, d2 - n2[2] * h / 2]))
            except np.linalg.LinAlgError:
                continue
            cpt = np.array([cxy[0], cxy[1], h / 2])
            out.append((mm, float(mm @ cpt) - 0.5 * bp['corner'] * rng.uniform(0.8, 1.2) * math.tan(beta), 'bevel'))
    out.append((np.array([0, 0, -1.0]), sink, 'foot'))
    return [(nn, d + float(nn @ o), k) for nn, d, k in out]


def night_piece(prm, top, name=''):
    """One boulder: dict(name, V, F, N per face, K kinds per face, UV per corner). Flat: each face's corners are its own."""
    def build(sd):
        rng = np.random.default_rng(prm['seed'])
        V, F, N, K, UV = [], [], [], [], []
        for bp in prm['blocks']:
            pl = night_block(bp, rng, sd * bp['size'][2])
            faces = polytope([(nn, d) for nn, d, _ in pl])
            allp = np.concatenate([P for _, P in faces])
            lo_, hi_ = allp.min(0), allp.max(0)     # (the block keeps to its size: unequal leaning sides overran it)
            sc = np.array([bp['size'][0] / (hi_[0] - lo_[0]), bp['size'][1] / (hi_[1] - lo_[1]), 1.0])
            c0 = np.array([(lo_[0] + hi_[0]) / 2, (lo_[1] + hi_[1]) / 2, 0.0])
            c1 = np.array(list(bp.get('off', (0.0, 0.0))) + [0.0])
            for pi, P in faces:
                nn, _, kind = pl[pi]
                if kind == 'foot':
                    continue
                P = (P - c0) * sc + c1
                nn = nn / sc; nn = nn / np.linalg.norm(nn)
                u, v = chart_frame(nn)
                uv0 = rng.uniform(0, 1, 2)
                base = len(V)
                V += list(P)
                for j in range(1, len(P) - 1):
                    F.append((base, base + j, base + j + 1)); N.append(nn); K.append(kind)
                    UV.append([uv0 + np.array([P[t] @ u, P[t] @ v]) / DAB_TILE for t in (0, j, j + 1)])
        return dict(name=name, V=np.array(V), F=np.array(F), N=np.array(N), K=K, UV=np.array(UV), fam='stone',
                    CN=np.repeat(np.array(N)[:, None], 3, 1))
    lo, hi = 0.04, 0.6      # (the shoulder's drop, a share of the block's height: more of it, less top)
    for _ in range(12):
        mid = (lo + hi) / 2
        pc = build(mid)
        if shares(pc)['top'] > top:
            lo = mid
        else:
            hi = mid
    pc['sd'] = round(mid, 3)
    pc['lods'] = [pc, pc, pc]       # (a faceted boulder is under 150 triangles: one mesh at every distance)
    return pc


def round_block(bp, rng, e, seg, rings, sink=0.12):
    """One block as a low lump: (V, F, VN, UV per vertex). A pole, 'rings' rings of 'seg': rings - 2 down the dome at equal
    steps of arc to the widest ring (0.22 of the height over the ground), one on the ground under a small tuck, one 'sink'
    under it. Then the lump is pressed against a few planes with a soft edge (a near-level top and two or three leaning
    sides: the block's flats, each edge a round one), which is what makes it a boulder and not a river pebble. The normals
    are the surface's own, read off the same surface built four times finer, so every lod shades alike."""
    ax, ay, h = bp['size'][0] / 2, bp['size'][1] / 2, bp['size'][2]
    o = np.array(list(bp.get('off', (0.0, 0.0))) + [0.0])
    p = bp.get('round', 2.5)
    lob = [(k, rng.uniform(0.07, 0.13) * (1.0 if k == 2 else 0.75), rng.uniform(0, 2 * math.pi)) for k in (2, 3)]
    sa, sm = rng.uniform(0, 2 * math.pi), rng.uniform(0.25, 0.5)       # (the lump leans: m sideways per m of height)
    shx, shy = sm * math.cos(sa), sm * math.sin(sa)
    uv0 = rng.uniform(0, 1, 2)
    fa0 = rng.uniform(0, 2 * math.pi)
    # the flats: (bearing, the normal's rise over the level in degrees, how deep it presses as a share of the lump's reach)
    flats = [(fa0 + (i + rng.uniform(-0.25, 0.25)) * 2 * math.pi / 3, rng.uniform(18, 48), rng.uniform(0.74, 0.88)) for i in range(3)]
    flats.append((rng.uniform(0, 2 * math.pi), rng.uniform(76, 84), rng.uniform(0.86, 0.93)))      # (the top)
    if (ax + ay) < 1.0:
        flats = flats[1:]           # (a small stone: two sides and the top)
    zc = 0.22 * h
    k4 = 4
    segd, nu = seg * k4, (rings - 2) * k4

    def rad(th):
        base = (np.abs(np.cos(th) / ax) ** p + np.abs(np.sin(th) / ay) ** p) ** (-1 / p)
        return base * (1 + sum(a * np.cos(k * (th - t0)) for k, a, t0 in lob))
    t = np.linspace(0, math.pi / 2, 400)
    pr, pz = np.sin(t) ** (2 / e), zc + (h - zc) * np.cos(t) ** (2 / e)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(pr) * (ax + ay) / 2, np.diff(pz)))])
    sj = s[-1] * np.arange(1, nu + 1) / nu
    rr, zz = np.interp(sj, s, pr), np.interp(sj, s, pz)
    bz, br = 1.6 * zc, 0.5                      # (the tuck: an arc from the widest ring to the ground)
    rg = 1 - br * (1 - math.cos(math.asin(zc / bz)))
    rr, zz = np.concatenate([rr, [rg, rg]]), np.concatenate([zz, [0.0, -sink]])
    nr = nu + 2
    th = np.arange(segd) * 2 * math.pi / segd
    R, c, sn = rad(th), np.cos(th), np.sin(th)
    V = np.concatenate([np.array([[shx * h, shy * h, h]])] +
                       [np.stack([R * rr[j] * c + shx * zz[j], R * rr[j] * sn + shy * zz[j], np.full(segd, zz[j])], 1) for j in range(nr)])
    wsoft = max(0.05, 0.09 * (ax + ay) / 2)     # (the flats' edge: round, never a crease)
    cz = np.array([0.0, 0.0, zc])
    for az, rise, deep in flats:
        nf = np.array([math.cos(az) * math.cos(math.radians(rise)), math.sin(az) * math.cos(math.radians(rise)), math.sin(math.radians(rise))])
        tt = (V - cz) @ nf
        d = deep * tt.max()
        V = V + (-wsoft * np.logaddexp(0.0, (tt - d) / wsoft))[:, None] * nf
    V[1 + (nr - 1) * segd:, :2] = V[1 + (nr - 2) * segd:1 + (nr - 1) * segd, :2]; V[1 + (nr - 1) * segd:, 2] = -sink
    V[:, 2] *= h / V[:, 2].max()                # (the pressing lowered it: back to the block's height)
    sx, sy = 2 * ax / np.ptp(V[:, 0]), 2 * ay / np.ptp(V[:, 1])        # (and to its size across)
    V = V * [sx, sy, 1.0]
    V[:, 0] -= (V[:, 0].max() + V[:, 0].min()) / 2; V[:, 1] -= (V[:, 1].max() + V[:, 1].min()) / 2

    def faces(sg, n):
        F = [(0, 1 + i, 1 + (i + 1) % sg) for i in range(sg)]
        for j in range(n - 1):
            a0, b0 = 1 + j * sg, 1 + (j + 1) * sg
            for i in range(sg):
                i1 = (i + 1) % sg
                F += [(a0 + i, b0 + i, b0 + i1), (a0 + i, b0 + i1, a0 + i1)]
        return np.array(F)
    VNd = vertex_normals(V, faces(segd, nr))
    # the lod's own vertices: every fourth of the fine surface (and its last two rings whole)
    ringsel = [k4 * (j + 1) - 1 for j in range(rings - 2)] + [nr - 2, nr - 1]
    idx = np.concatenate([[0]] + [1 + j * segd + np.arange(seg) * k4 for j in ringsel])
    V, VN = V[idx], VNd[idx]
    F = faces(seg, rings)
    # the dabs: the dome laid flat about its pole (each vertex its meridian's arc from the pole, along its bearing)
    m = np.zeros(len(V)); prev = np.repeat(V[:1], seg, 0); acc = np.zeros(seg)
    for j in range(rings):
        ring = V[1 + j * seg:1 + (j + 1) * seg]
        acc = acc + np.linalg.norm(ring - prev, axis=1); m[1 + j * seg:1 + (j + 1) * seg] = acc; prev = ring
    c, sn = c[::k4], sn[::k4]
    ct, st = np.concatenate([[0.0], np.tile(c, rings)]), np.concatenate([[0.0], np.tile(sn, rings)])
    UV = uv0 + np.stack([m * ct, m * st], 1) / DAB_TILE
    return V + o, F, VN, UV


def round_piece(prm, top, name='', hz=1.0):
    """One rounded boulder: the same hull blocks as the facet form, each a lump; the dome's exponent (2 a half ellipse,
    more a flatter top over steeper sides) solved so the tops cover 'top' of the footprint from above. lods: three."""
    def build(e, lod=0):
        rng = np.random.default_rng(prm['seed'] + 7)
        V, F, CN, UV, o = [], [], [], [], 0
        for bi, bp in enumerate(prm['blocks']):
            bp = dict(bp, size=(bp['size'][0], bp['size'][1], bp['size'][2] * hz))
            w = (bp['size'][0] + bp['size'][1]) / 2
            seg = (bp.get('seg', 24 if w < 1.0 else 28 if w < 2.0 else 32) if bi == 0 else 20 if w >= 1.0 else 16)
            rings = (bp.get('rings', 7 if w < 2.0 else 8) if bi == 0 else 5)
            if lod:
                seg, rings = (max(seg // 2, 10), max(rings - 2, 4)) if lod == 1 else (max(seg // 3, 8), 4)
            v, f, vn, uv = round_block(bp, rng, e, seg, rings)
            V.append(v); F.append(f + o); CN.append(vn[f]); UV.append(uv[f]); o += len(v)
        CN = np.concatenate(CN)
        N = CN.sum(1); N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        return dict(name=name, V=np.concatenate(V), F=np.concatenate(F), N=N, CN=CN, K=[], UV=np.concatenate(UV), fam='stone')
    lo, hi = 2.0, 2.7        # (over 2.7 the lump is a drum: a flat lid over a wall; the share is then what it is)
    for _ in range(10):
        mid = (lo + hi) / 2
        if shares(build(mid))['top'] < top:
            lo = mid
        else:
            hi = mid
    e = round(2.0 if shares(build(2.0))['top'] >= top else mid, 2)
    pc = build(e)
    pc['e'] = e
    pc['lods'] = [pc, build(e, 1), build(e, 2)]
    return pc


def night_pieces(only=None):
    """{preset: [piece]} (the pieces' names boulder_s_a, ..., round_s_a, ...)."""
    return {nm: [round_piece(prm, pre['top'], f'{nm}_{"abcdefgh"[vi]}', pre['hz']) if pre['form'] == 'round' else
                 night_piece(prm, pre['top'], f'{nm}_{"abcdefgh"[vi]}') for vi, prm in enumerate(pre['variants'])]
            for nm, pre in NIGHT.items() if not only or nm == only}


# ---- measuring and the review sheet (numpy; shared with env_trees.py's kit pieces)
TOPDOWN = np.eye(3)
_e = math.radians(50)
PLAY = np.array([[1.0, 0, 0], [0, math.sin(_e), math.cos(_e)], [0, -math.cos(_e), math.sin(_e)]])   # (right, up, toward the eye)


def raster(V, F, R, ppm, pad=2, bary=False):
    """An orthographic z-buffer of the triangles seen with R's rows (right, up, toward the eye): (face ids, -1 empty; x0, y0 px)
    and, with bary, each pixel's weights of its face's first two corners."""
    P = V @ R.T
    x, y, z = P[:, 0] * ppm, -P[:, 1] * ppm, P[:, 2]
    x0, y0 = math.floor(x.min()) - pad, math.floor(y.min()) - pad
    W, H = int(math.ceil(x.max()) - x0) + pad, int(math.ceil(y.max()) - y0) + pad
    ids = -np.ones((H, W), np.int64); zb = np.full((H, W), -1e9)
    B0, B1 = np.zeros((H, W)), np.zeros((H, W))
    for fi, (a, b, c) in enumerate(F):
        xs, ys = x[[a, b, c]] - x0, y[[a, b, c]] - y0
        i0, i1 = max(int(xs.min()), 0), min(int(math.ceil(xs.max())) + 1, W)
        j0, j1 = max(int(ys.min()), 0), min(int(math.ceil(ys.max())) + 1, H)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if i1 <= i0 or j1 <= j0 or abs(d) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(i0, i1) + 0.5, np.arange(j0, j1) + 0.5)
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        w2 = 1 - w0 - w1
        zz = w0 * z[a] + w1 * z[b] + w2 * z[c]
        sub = zb[j0:j1, i0:i1]
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0) & (zz > sub)
        sub[m] = zz[m]; ids[j0:j1, i0:i1][m] = fi
        if bary:
            B0[j0:j1, i0:i1][m] = w0[m]; B1[j0:j1, i0:i1][m] = w1[m]
    return (ids, (x0, y0), (B0, B1)) if bary else (ids, (x0, y0))


def groups(N):
    """Each face's tone group by its baked normal: 0 top (within 30 degrees of up), 1 body, 2 inner or low (80 degrees or more)."""
    return np.where(N[:, 2] >= COS30, 0, np.where(N[:, 2] > COS80, 1, 2))


def shares(pc, ppm=60):
    """From straight above: the footprint's area (m2), the share of it each group shows, and the share of its hull left open."""
    ids, _ = raster(pc['V'], pc['F'], TOPDOWN, ppm)
    cov = ids >= 0
    g = groups(pc['N'])[ids[cov]]
    ys, xs = np.nonzero(cov)
    pts = sorted(set(zip(xs.tolist(), ys.tolist())))
    def half(ps):
        h = []
        for q in ps:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (q[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (q[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(q)
        return h
    hull = half(pts)[:-1] + half(pts[::-1])[:-1]
    ha = 0.5 * abs(sum(hull[i][0] * hull[(i + 1) % len(hull)][1] - hull[(i + 1) % len(hull)][0] * hull[i][1] for i in range(len(hull))))
    n = max(int(cov.sum()), 1)
    return dict(area=round(n / ppm ** 2, 2), top=float((g == 0).mean()), body=float((g == 1).mean()), low=float((g == 2).mean()),
                gaps=round(1 - n / max(ha, 1), 3))


def oklch(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l, m, s = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3, (L - 0.1055613458 * a - 0.0638541728 * b) ** 3, (L - 0.0894841775 * a - 1.291485548 * b) ** 3
    lin = np.array([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s]).clip(0, 1)
    return np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)


# (the design's table, NIGHT_KIT.md K1: S1 side, S2 body, S3 top per family, as sRGB; the sheet's ground the moonlit S2)
TONES = {'stone': [oklch(0.43, 0.12, 255), oklch(0.27, 0.085, 261), oklch(0.18, 0.05, 268)],
         'leaf': [oklch(0.355, 0.075, 237), oklch(0.23, 0.063, 250), oklch(0.14, 0.035, 254)],
         'bark': [oklch(0.28, 0.05, 268), oklch(0.20, 0.05, 272), oklch(0.15, 0.035, 262)]}
GROUND = oklch(0.27, 0.073, 255)
MOON = np.array([-0.55, 0.45, 0.70]) / np.linalg.norm([-0.55, 0.45, 0.70])     # (to the moon: up, from the left, behind)


def sheet(rows, out, ppm=78.0, gap=0.5):
    """The kit's review sheet: rows of pieces side by side from the play camera's angle (50 degrees above) at its size
    (78 px per metre), flat-lit in three tones a family by each face's baked normal (a stand-in for K1's rule, not the
    shader: top within 30 degrees of up or square to the moon; side facing away from it or low; body the rest)."""
    from PIL import Image
    tiles = []
    for row in rows:
        rt = []
        for pc in row:
            ids, _, (b0, b1) = raster(pc['V'], pc['F'], PLAY, ppm, bary=True)
            cov = ids >= 0; f = ids[cov]
            CN = pc['CN'] if pc.get('CN') is not None else np.repeat(pc['N'][:, None], 3, 1)
            w0, w1 = b0[cov][:, None], b1[cov][:, None]
            N = CN[f, 0] * w0 + CN[f, 1] * w1 + CN[f, 2] * (1 - w0 - w1)
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
            t = N @ MOON
            tone = np.where((N[:, 2] >= COS30) | (t > 0.8), 0, np.where((t < 0.1) | (N[:, 2] <= COS80), 2, 1))
            fam = pc.get('fams') if pc.get('fams') is not None else [pc['fam']] * len(pc['F'])
            T = np.array([TONES[x] for x in fam])
            img = np.tile(GROUND, (ids.shape[0], ids.shape[1], 1))
            img[cov] = T[f, tone]
            rt.append(img)
        tiles.append(rt)
    g = int(gap * ppm)
    W = max(sum(t.shape[1] for t in rt) + g * (len(rt) + 1) for rt in tiles)
    H = sum(max(t.shape[0] for t in rt) for rt in tiles) + g * (len(tiles) + 1)
    can = np.tile(GROUND, (H, W, 1))
    y = g
    for rt in tiles:
        hh = max(t.shape[0] for t in rt); x = g
        for t in rt:
            can[y + hh - t.shape[0]:y + hh, x:x + t.shape[1]] = t
            x += t.shape[1] + g
        y += hh + g
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    Image.fromarray((can * 255 + 0.5).astype(np.uint8)).save(out)
    print(out, f'{W}x{H}')


def table(pc):
    s = shares(pc)
    V = pc['V']; above = V[V[:, 2] > -1e-6] if (V[:, 2] > 0).any() else V
    kinds = pc.get('K')
    line = f"{pc['name']}: {np.ptp(V[:, 0]):.2f} x {np.ptp(V[:, 1]):.2f} m, z {max(V[:, 2].min(), 0):.2f}-{V[:, 2].max():.2f} m, {len(pc['F'])} tris, " \
           f"from above top {s['top']:.0%} body {s['body']:.0%} low {s['low']:.0%}, gaps {s['gaps']:.0%}"
    if kinds:
        ar = {}
        for (a, b, c), k, n in zip(pc['F'], kinds, pc['N']):
            if k == 'side':
                key = tuple(np.round(n, 3)); ar[key] = ar.get(key, 0) + 0.5 * np.linalg.norm(np.cross(V[b] - V[a], V[c] - V[a]))
        line += f", side planes {sum(1 for v in ar.values() if v > 0.15 * max(ar.values()))}, shoulder {pc.get('sd')} of the height"
    if pc.get('e'):
        line += f", dome exponent {pc['e']}, lods {' / '.join(str(len(q['F'])) for q in pc['lods'])} tris"
    return line


def dab_sheet(N, base, seed, tile=DAB_TILE, scales=(0.7, 0.25), step=0.05, warm=None, wrap=True):
    """A flat painted field (N x N x 3, sRGB 0-1): 'base' with angular dabs at two sizes (m across), each one flat value
    step up or down (and a breath of 'warm'); no noise, no gradient. Tiles when wrap."""
    import cv2
    rng = np.random.default_rng(seed)
    img = np.tile(srgb(base), (N, N, 1)).astype(np.float32)
    ppm = N / tile
    for si, s in enumerate(scales):
        for _ in range(int((0.9, 0.55)[min(si, 1)] * (tile / s) ** 2)):
            c = rng.uniform(0, N, 2)
            k = int(rng.integers(4, 7))
            ang = np.sort(rng.uniform(0, 2 * math.pi, k))
            rad = s * ppm * 0.5 * rng.uniform(0.7, 1.25, k)
            poly = np.stack([c[0] + rad * np.cos(ang) * 1.3, c[1] + rad * np.sin(ang)], 1)
            col = srgb(base) * (1 + step * rng.choice([-1.0, -0.5, 0.5, 1.0]))
            if warm is not None and rng.random() < 0.3:
                col = col * 0.9 + srgb(warm) * 0.1
            for ox in ((-N, 0, N) if wrap else (0,)):
                for oy in ((-N, 0, N) if wrap else (0,)):
                    cv2.fillPoly(img, [np.round(poly + [ox, oy]).astype(np.int32)], [float(x) for x in col], cv2.LINE_AA)
    return np.clip(img, 0, 1)


def night_tex():
    from PIL import Image
    out = os.path.join(OUT, 'rock_dabs.png')
    Image.fromarray((dab_sheet(1024, '#6c6f72', 71, warm='#8c7560') * 255 + 0.5).astype(np.uint8)).save(out)
    print(out)


def night_mesh(only=None):
    """Each night preset's species file: lod0, lod1, lod2 and shadow (the facet form one mesh: a boulder is under 150
    triangles; the round form three, the shadow its lod2), each corner the piece's own normal (a facet's plane or the
    lump's surface), material Stone_Own<Species> on rock_dabs.png."""
    import bpy
    img_path = os.path.join(OUT, 'rock_dabs.png')
    for nm, pcs in night_pieces(only).items():
        sp = NIGHT[nm]['species']
        bpy.ops.wm.read_factory_settings(use_empty=True)
        mat = bpy.data.materials.new(f'Stone_Own{sp.capitalize()}'); mat.use_nodes = True
        bsdf = mat.node_tree.nodes['Principled BSDF']
        ti = mat.node_tree.nodes.new('ShaderNodeTexImage'); ti.image = bpy.data.images.load(img_path)
        mat.node_tree.links.new(ti.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 1.0
        for pc in pcs:
            print('  ' + table(pc))
        for on, li in (('lod0', 0), ('lod1', 1), ('lod2', 2), ('shadow', 2)):
            V, F, Nv, UV, C, o = [], [], [], [], [], 0
            for vi, pc0 in enumerate(pcs):
                pc = pc0['lods'][li]
                # (each corner its own vertex, so a corner's normal is exactly the piece's)
                V.append(pc['V'][pc['F']].reshape(-1, 3)); Nv.append(pc['CN'].reshape(-1, 3)); UV.append(pc['UV'].reshape(-1, 2))
                F.append(np.arange(len(pc['F']) * 3).reshape(-1, 3) + o); o += len(pc['F']) * 3
                C.append(np.tile([0.0, 0.0, 0.0, (vi + 0.5) / 8], (len(pc['F']) * 3, 1)))
            V, F, Nv, UV, C = np.concatenate(V), np.concatenate(F), np.concatenate(Nv), np.concatenate(UV), np.concatenate(C)
            me = bpy.data.meshes.new(on)
            me.from_pydata(V.tolist(), [], F.tolist())
            me.normals_split_custom_set_from_vertices([tuple(n) for n in Nv])
            ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
            ca.data.foreach_set('color', C.astype(np.float32).ravel())
            me.color_attributes.active_color = ca
            uvl = me.uv_layers.new(name='UVMap')
            uvl.data.foreach_set('uv', np.stack([UV[:, 0], 1 - UV[:, 1]], 1).astype(np.float32).ravel())
            me.materials.append(mat)
            bpy.context.scene.collection.objects.link(bpy.data.objects.new(on, me))
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{sp}.gltf'), export_format='GLTF_SEPARATE', export_texture_dir='',
                                  export_normals=True, export_tangents=False, export_materials='EXPORT', export_image_format='AUTO',
                                  export_keep_originals=True, export_yup=True, export_apply=True, export_vertex_color='ACTIVE')
        print(f'{sp}.gltf: {len(pcs)} variants, lod0 {sum(len(q["F"]) for q in pcs)} tris')


def kit_sheet(out, which='all'):
    rows = []
    if which in ('all', 'stone'):
        allp = night_pieces()
        rows += [[pc for nm, pcs in allp.items() if NIGHT[nm]['form'] == form for pc in pcs] for form in ('facet', 'round')]
    if which != 'stone':
        sys.path.insert(0, os.path.dirname(__file__))
        import env_trees
        rows += env_trees.kit_rows(which)
    for row in rows:
        for pc in row:
            print(table(pc))
    sheet(rows, out)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    if argv and argv[0] == 'tex' and arg('--kit', '') == 'night':
        night_tex()
    elif argv and argv[0] == 'sheet':
        kit_sheet(arg('--out', os.path.join(ROOT, 'kit_sheet.png')), arg('--kit', 'all'))
    elif argv and argv[0] == 'mesh' and arg('--preset', '') in NIGHT:
        night_mesh(arg('--preset', None))
    elif argv and argv[0] == 'tex':
        tex()
    elif argv and argv[0] == 'mesh' and arg('--form', 'planes') == 'planes':
        mesh_planes(arg('--preset', None))   # (L1 C3a; --form sculpt: E5's sculpted pieces on the triplanar sheet, kept to compare)
    elif argv and argv[0] == 'mesh':
        mesh(arg('--preset', None))
    else:
        print(__doc__)
