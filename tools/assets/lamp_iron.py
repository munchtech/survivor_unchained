"""The Ford-Warden's lamp-iron (BossViews/LampIron.cs), boss-prop detail, made here from nothing.

    blender -b -P tools/assets/lamp_iron.py

Concept A (warden_concepts/pick/A_fist.png): a flat-topped square black-iron cage. Four bevelled
corner posts, two round bars a side, three riveted flat straps round it, a stepped top plate with
a finial and the ring it hangs by, a stepped base on four feet, an oil font with its wick, and four
glass panes behind the bars. A chain-link bail through the ring for the fist (shown by LampIron
only when it is hung).

Out: godot/art/props/keeper_lamp/keeper_lamp.glb, nodes
  Cage   the iron that throws the bars' shadows (posts, bars, straps, rivets, base, font)
  Cap    the top plate, finial and ring (no shadow: the flame's light reaches up past it)
  Bail   the link the fist closes on
  Glass  the four panes (UV: u across, v down each pane)
and iron_masks.png beside it: a tiling RGBA mask the game's shaders/keeper_iron.gdshader projects
(R rust blotches, G grain, B pitting height, A vertical water streaks).
The iron carries a vertex colour: R its convexity (0.5 flat, 1 a sharp outer edge, 0 a crease),
B a per-part random, for the edge wear and rust in the shader.

Frame (the game's, y up): the ring's centre at the origin; the flame at y = -0.15 (LampIron.FlameY),
the feet's underside at y = -0.23 (LampIron.FootY); the cage 0.141 square.
"""
import math
import os
import random

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'godot', 'art', 'props', 'keeper_lamp')
G2B = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
rng = random.Random(7)


# ------------------------------------------------------------- textures --

def noise(shape, seed, octaves=5, base=4, stretch=(1, 1)):
    """Tiling value noise (periodic at the image edge), 0..1. stretch: cells per axis multiplier (y, x)."""
    r = np.random.default_rng(seed)
    h, w = shape
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        ny, nx = int(base * stretch[0]) * 2 ** o, int(base * stretch[1]) * 2 ** o
        g = r.random((ny + 1, nx + 1)).astype(np.float32)
        g[-1, :] = g[0, :]
        g[:, -1] = g[:, 0]
        ys = np.linspace(0, ny, h, endpoint=False)
        xs = np.linspace(0, nx, w, endpoint=False)
        y0, x0 = ys.astype(int), xs.astype(int)
        fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy)
        tot += amp
        amp *= 0.55
    return out / tot


def masks(size=512):
    rust = noise((size, size), 11, 5, 3)
    grain = noise((size, size), 23, 3, 32)
    # Pitting: sparse small pits (thresholded fine noise), over a soft hammered undulation.
    pits = np.clip((noise((size, size), 37, 2, 48) - 0.62) * 6, 0, 1)
    hammer = noise((size, size), 41, 3, 6)
    height = np.clip(0.55 + 0.35 * (hammer - 0.5) - 0.45 * pits, 0, 1)
    # Streaks: noise squeezed across x, long down y (the image's v is the projection's up).
    streak = noise((size, size), 53, 4, 2, stretch=(1, 16))
    streak = np.clip((streak - 0.35) * 2.2, 0, 1)
    img = bpy.data.images.new('iron_masks', size, size, alpha=True)
    img.colorspace_settings.name = 'Non-Color'
    px = np.stack([rust, grain, height, streak], -1).astype(np.float32)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = os.path.join(OUT, 'iron_masks.png')
    img.file_format = 'PNG'
    img.save()


# ------------------------------------------------------------- geometry --

def box(sx, sy, sz, bevel=0.0, segs=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=segs, affect='EDGES', profile=0.5)
    return bm


def lathe(profile, segs, rot=0.0):
    """A solid of revolution about y: profile [(r, y)] bottom to top; r = 0 closes a pole."""
    bm = bmesh.new()
    rings = []
    for r, y in profile:
        n = segs if r > 1e-7 else 1
        rings.append([bm.verts.new((r * math.cos(rot + k * math.tau / segs), y, r * math.sin(rot + k * math.tau / segs)))
                      for k in range(n)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(segs):
            if len(r0) == 1 and len(r1) == 1:
                continue
            if len(r0) == 1:
                bm.faces.new((r0[0], r1[(k + 1) % segs], r1[k]))
            elif len(r1) == 1:
                bm.faces.new((r0[k], r0[(k + 1) % segs], r1[0]))
            else:
                bm.faces.new((r0[k], r0[(k + 1) % segs], r1[(k + 1) % segs], r1[k]))
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def tube(path, r, sides, closed):
    """A round rod swept along a polyline (closed: a loop)."""
    bm = bmesh.new()
    pts = [Vector(p) for p in path]
    n = len(pts)
    rings = []
    prev_side = None
    for i, p in enumerate(pts):
        if closed:
            t = (pts[(i + 1) % n] - pts[i - 1]).normalized()
        else:
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        side = prev_side if prev_side is not None else (Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0)))
        side = (side - t * side.dot(t)).normalized()
        prev_side = side
        up = t.cross(side)
        rings.append([bm.verts.new(p + (side * math.cos(a) + up * math.sin(a)) * r)
                      for a in (k * math.tau / sides for k in range(sides))])
    m = n if closed else n - 1
    for i in range(m):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(sides):
            bm.faces.new((a[k], b[k], b[(k + 1) % sides], a[(k + 1) % sides]))
    if not closed:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def T(x, y, z):
    return Matrix.Translation((x, y, z))


def RY(a):
    return Matrix.Rotation(a, 4, 'Y')


def RX(a):
    return Matrix.Rotation(a, 4, 'X')


def rivet(r):
    """A domed rivet head along +y, its flat at y = 0."""
    return lathe([(r, -0.0004), (r, 0), (0.93 * r, 0.38 * r), (0.72 * r, 0.7 * r), (0.38 * r, 0.92 * r), (0, r)], 8)


# Sizes (the game's frame, lamp units).
HALF = 0.0705          # the posts' outer faces
POST = 0.012
TOP, BOT = -0.063, -0.205   # the cage between the top plate and the base
BAR_X = 0.0215
BANDS = (-0.0695, -0.108, -0.1985)


def cage_parts():
    parts = []
    # Corner posts.
    c = HALF - POST / 2
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append((box(POST, TOP - BOT + 0.004, POST, 0.0018), T(sx * c, (TOP + BOT) / 2, sz * c)))
    for k in range(4):
        side = RY(k * math.pi / 2)
        # Two round bars a side, a hair inside the straps.
        for bx in (-BAR_X, BAR_X):
            parts.append((tube([(bx, BOT - 0.001, HALF - 0.0031), (bx, TOP + 0.001, HALF - 0.0031)], 0.0031, 8, False), side))
        # Flat straps round the outside, overlapping at the corners; a rivet where each crosses a post or bar.
        for y in BANDS:
            th = 0.0034
            h = 0.0105 if y != BANDS[1] else 0.009
            parts.append((box(2 * HALF + 2 * th, h, th, 0.0011), side @ T(0, y, HALF + th / 2)))
            for x in (-HALF + POST / 2, -BAR_X, BAR_X, HALF - POST / 2):
                rr = 0.0021 if abs(x) < 0.05 else 0.0024
                parts.append((rivet(rr), side @ T(x, y, HALF + th) @ RX(math.pi / 2)))
    # The base: a plate, a step under it and four feet; the oil font and its wick on top.
    parts.append((box(0.152, 0.012, 0.152, 0.0022), T(0, BOT - 0.006, 0)))
    parts.append((box(0.134, 0.006, 0.134, 0.0015), T(0, BOT - 0.015, 0)))
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append((lathe([(0.0085, -0.23), (0.0095, -0.2265), (0.0075, -0.2225), (0.0075, -0.217)], 8, math.pi / 8),
                          T(sx * 0.058, 0, sz * 0.058)))
    parts.append((lathe([(0.028, BOT), (0.032, BOT + 0.004), (0.032, BOT + 0.0085), (0.027, BOT + 0.0135),
                         (0.016, BOT + 0.0175), (0.0085, BOT + 0.0185), (0.0075, BOT + 0.0215), (0.0058, BOT + 0.0235),
                         (0.0, BOT + 0.0235)], 18), Matrix.Identity(4)))
    parts.append((lathe([(0.0016, BOT + 0.023), (0.0014, BOT + 0.0265), (0.0, BOT + 0.0275)], 6), Matrix.Identity(4)))
    return parts


def cap_parts():
    parts = []
    # The flat top: a plate over the cage, a smaller raised plate, a finial with an eye, the ring.
    parts.append((box(0.154, 0.0095, 0.154, 0.0022), T(0, TOP + 0.00475, 0)))
    parts.append((box(0.104, 0.0055, 0.104, 0.0016), T(0, TOP + 0.0095 + 0.00275, 0)))
    y0 = TOP + 0.015
    parts.append((lathe([(0.016, y0), (0.0145, y0 + 0.003), (0.0095, y0 + 0.0055), (0.0075, y0 + 0.009),
                         (0.0092, y0 + 0.0125), (0.0092, y0 + 0.0145), (0.0062, y0 + 0.0175), (0.0055, y0 + 0.022),
                         (0.0, y0 + 0.0225)], 12, math.pi / 12), Matrix.Identity(4)))
    # The ring, standing up in the x-y plane, its bottom through the finial's top.
    R, r = 0.0215, 0.0042
    pts = [(R * math.cos(a), R * math.sin(a), 0) for a in (k * math.tau / 28 for k in range(28))]
    parts.append((tube(pts, r, 8, True), Matrix.Identity(4)))
    return parts


def bail_parts():
    """A chain link through the ring, in the y-z plane, up to where the fist closes (y about 0.07..0.095)."""
    a, b, w, r = 0.008, 0.092, 0.0115, 0.0036
    pts = []
    for k in range(9):          # the bottom bend, through the ring
        t = math.pi + k * math.pi / 8
        pts.append((0, a + w + w * math.sin(t), w * math.cos(t)))
    for k in range(9):          # the top bend
        t = k * math.pi / 8
        pts.append((0, b - w + w * math.sin(t), w * math.cos(t)))
    return [(tube(pts, r, 8, True), Matrix.Identity(4))]


def glass_parts():
    parts = []
    z = HALF - 0.0095
    w, y0, y1 = 2 * (HALF - POST) + 0.004, BOT, TOP
    for k in range(4):
        bm = bmesh.new()
        uv = bm.loops.layers.uv.verify()
        # Two rows of quads, so a pane can bow a hair (a hand-blown pane is never flat).
        cols, rows = 4, 6
        vs = [[bm.verts.new((-w / 2 + w * i / cols, y1 - (y1 - y0) * j / rows,
                             z + 0.0012 * math.sin(math.pi * i / cols) * math.sin(math.pi * j / rows)))
               for i in range(cols + 1)] for j in range(rows + 1)]
        for j in range(rows):
            for i in range(cols):
                f = bm.faces.new((vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1], vs[j][i]))
                for l, (ii, jj) in zip(f.loops, ((i, j + 1), (i + 1, j + 1), (i + 1, j), (i, j))):
                    l[uv].uv = (ii / cols, 1 - jj / rows)
        parts.append((bm, RY(k * math.pi / 2)))
    return parts


def convexity(bm):
    """Per vertex: 0.5 + half the mean signed dihedral (radians over pi/2) of its edges, clamped 0..1."""
    out = {}
    for v in bm.verts:
        s, n = 0.0, 0
        for e in v.link_edges:
            if len(e.link_faces) == 2:
                s += e.calc_face_angle_signed(0.0)
                n += 1
        c = (s / n) / (math.pi / 2) if n else 0.0
        out[v.index] = min(max(0.5 + 0.5 * c * 1.6, 0.0), 1.0)
    return out


def build(name, parts, mat, colour=True):
    bm = bmesh.new()
    col = bm.verts.layers.float_color.new('Col') if colour else None
    uvl = bm.loops.layers.uv.verify()
    for pbm, at in parts:
        pbm.verts.ensure_lookup_table()
        conv = convexity(pbm) if colour else {}
        rnd = rng.random()
        pbm.transform(G2B @ at)
        me = bpy.data.meshes.new('tmp')
        if colour:
            lay = pbm.verts.layers.float_color.new('Col')
            for v in pbm.verts:
                v[lay] = (conv[v.index], 0.5, rnd, 1.0)
        pbm.to_mesh(me)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        pbm.free()
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(42))
    if colour:
        me.color_attributes.active_color = me.color_attributes['Col']
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(OUT, exist_ok=True)
    masks()
    iron = bpy.data.materials.new('keeper_iron')
    iron.diffuse_color = (0.04, 0.038, 0.035, 1)
    glass = bpy.data.materials.new('keeper_glass')
    glass.diffuse_color = (0.3, 0.32, 0.3, 0.3)
    obs = [build('Cage', cage_parts(), iron), build('Cap', cap_parts(), iron),
           build('Bail', bail_parts(), iron), build('Glass', glass_parts(), glass, colour=False)]
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    path = os.path.join(OUT, 'keeper_lamp.glb')
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
              export_materials='EXPORT')
    try:
        bpy.ops.export_scene.gltf(**kw, export_vertex_color='ACTIVE')
    except TypeError:
        bpy.ops.export_scene.gltf(**kw, export_colors=True)
    print('LAMP tris', {o.name: tris(o) for o in obs}, 'total', sum(tris(o) for o in obs))


if __name__ == '__main__':
    main()
