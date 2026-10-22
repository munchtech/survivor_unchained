"""The Ford-Warden's sword: an old Watch blade, straight and corroded (concept A, warden_concepts/pick/A_hero.png).

    blender -b -P tools/assets/watch_blade.py

A plain hand-and-a-half sword drawn to a giant's two-hander: a wheel pommel with its peened tang, a
long cord-wrapped grip, a straight square-section crossguard with flared ends, and a long straight
blade with a fuller two-thirds down it, a bevelled edge, and nicks along both edges from use.

Out: godot/art/weapons/watch_blade.glb, one mesh "WatchBlade" (one material, keeper_iron in the
game). Its vertex colour: R convexity (0.5 flat, 1 a sharp outer edge, 0 a crease), G the part
(0.5 iron, 1.0 the grip's cord), B a per-part random. Frame (the game's): the pommel's end at y = 0,
the tip up +y at 1.55, the guard along x. Arms "watch_blade" scales it by its Spec.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'godot', 'art', 'weapons')
G2B = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
rng = random.Random(11)

GUARD_Y = 0.36
BLADE_Y = 0.385
TIP_Y = 1.55


def box(sx, sy, sz, bevel=0.0, segs=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=segs, affect='EDGES', profile=0.5)
    return bm


def lathe(profile, segs, rot=0.0, zscale=1.0):
    bm = bmesh.new()
    rings = []
    for r, y in profile:
        n = segs if r > 1e-7 else 1
        rings.append([bm.verts.new((r * math.cos(rot + k * math.tau / segs), y, zscale * r * math.sin(rot + k * math.tau / segs)))
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


def nicks():
    """A few dents along each edge: (side, y, depth, width)."""
    out = []
    for side in (-1, 1):
        for _ in range(7):
            out.append((side, rng.uniform(BLADE_Y + 0.08, TIP_Y - 0.08), rng.uniform(0.0015, 0.0045), rng.uniform(0.004, 0.012)))
    return out


def blade():
    """Lofted sections along y: a flattened hexagon with a fuller, its edge bevel and nicks."""
    bm = bmesh.new()
    nk = nicks()
    rows = []
    n = 90
    tip0 = TIP_Y - 0.16
    full_end = BLADE_Y + 0.68
    for i in range(n + 1):
        u = i / n
        y = BLADE_Y + (TIP_Y - BLADE_Y) * (u ** 0.92)
        s = (y - BLADE_Y) / (TIP_Y - BLADE_Y)
        w = 0.030 - 0.009 * s                       # half-width, base to the point's start
        t = 0.0095 - 0.0045 * s                      # thickness
        if y > tip0:
            p = (y - tip0) / (TIP_Y - tip0)
            k = math.sqrt(max(1 - p * p, 0.0)) * (1 - 0.25 * p)   # an ogival point
            w *= max(k, 0.0)
            t *= max(0.35 + 0.65 * k, 0.0) if p < 1 else 0.0
        fd = 0.0024 * min(1.0, (y - BLADE_Y) / 0.03) * max(0.0, min(1.0, (full_end - y) / 0.06))
        fw = 0.0085 * (1 - 0.3 * s)
        wl = wr = w
        for side, ny, dep, wid in nk:
            d = math.exp(-((y - ny) / wid) ** 2) * dep
            if side < 0:
                wl -= d
            else:
                wr -= d
        wl, wr = max(wl, 0.0), max(wr, 0.0)
        if i == n:
            rows.append([bm.verts.new((0, TIP_Y, 0))])
            continue
        ht = t / 2
        e = 0.62   # the edge bevel's inner line, as a fraction of the half-width
        pts = [(wr, 0), (wr * e + fw * (1 - e) * 0.2, ht * 0.86), (fw * 1.5, ht), (fw, ht - fd * 0.5), (0, ht - fd),
               (-fw, ht - fd * 0.5), (-fw * 1.5, ht), (-(wl * e + fw * (1 - e) * 0.2), ht * 0.86), (-wl, 0)]
        pts += [(x, -z) for x, z in reversed(pts[1:-1])]
        rows.append([bm.verts.new((x, y, z)) for x, z in pts])
    m = len(rows[0])
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(m):
            if len(r1) == 1:
                bm.faces.new((r0[k], r0[(k + 1) % m], r1[0]))
            else:
                bm.faces.new((r0[k], r0[(k + 1) % m], r1[(k + 1) % m], r1[k]))
    bm.faces.new(list(reversed(rows[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def grip():
    """The grip, oval, a swell in the middle, wrapped in cord (ridges every 9 mm)."""
    y0, y1 = 0.072, GUARD_Y - 0.006
    prof = [(0.0, y0 - 0.001), (0.0150, y0)]
    n = int((y1 - y0) / 0.0045)
    for i in range(1, n):
        y = y0 + (y1 - y0) * i / n
        s = (y - y0) / (y1 - y0)
        r = 0.0150 + 0.0022 * math.sin(math.pi * s)
        r += 0.0007 if i % 2 else -0.0003
        prof.append((r, y))
    prof += [(0.0150, y1), (0.0, y1 + 0.001)]
    return lathe(prof, 14, zscale=0.84)


def fittings():
    parts = []
    # Wheel pommel, its axis along z, and the peen.
    pom = lathe([(0.0, -0.0135), (0.022, -0.0135), (0.031, -0.0115), (0.0365, -0.006), (0.0375, 0.0), (0.0365, 0.006),
                 (0.031, 0.0115), (0.022, 0.0135), (0.0, 0.0135)], 24)
    parts.append((pom, Matrix.Translation((0, 0.040, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'X')))
    parts.append((lathe([(0.0075, 0.004), (0.0068, 0.0005), (0.0035, -0.002), (0.0, -0.0025)], 10), Matrix.Identity(4)))
    # A collar between pommel and grip, and one under the guard.
    parts.append((lathe([(0.0, 0.0755), (0.0135, 0.0755), (0.0155, 0.0710), (0.0130, 0.0665), (0.0, 0.0665)], 12, zscale=0.86), Matrix.Identity(4)))
    parts.append((lathe([(0.0, GUARD_Y - 0.009), (0.016, GUARD_Y - 0.009), (0.0175, GUARD_Y - 0.003), (0.0, GUARD_Y - 0.003)], 12, zscale=0.86), Matrix.Identity(4)))
    # The guard: a square-section bar, a block at the middle, flared ends.
    parts.append((box(0.27, 0.019, 0.022, 0.003), Matrix.Translation((0, GUARD_Y + 0.0095, 0))))
    parts.append((box(0.062, 0.027, 0.03, 0.004), Matrix.Translation((0, GUARD_Y + 0.0135, 0))))
    for sx in (-1, 1):
        parts.append((box(0.022, 0.026, 0.028, 0.0045), Matrix.Translation((sx * 0.142, GUARD_Y + 0.011, 0))))
    return parts


def convexity(bm):
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


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(OUT, exist_ok=True)
    parts = [(blade(), Matrix.Identity(4), 0.5), (grip(), Matrix.Identity(4), 1.0)] + [(b, m, 0.5) for b, m in fittings()]
    bm = bmesh.new()
    for pbm, at, part in parts:
        pbm.verts.ensure_lookup_table()
        conv = convexity(pbm)
        lay = pbm.verts.layers.float_color.new('Col')
        rnd = rng.random()
        for v in pbm.verts:
            v[lay] = (conv[v.index], part, rnd, 1.0)
        pbm.transform(G2B @ at)
        me = bpy.data.meshes.new('tmp')
        pbm.to_mesh(me)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        pbm.free()
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('WatchBlade')
    bm.to_mesh(me)
    bm.free()
    mat = bpy.data.materials.new('watch_iron')
    mat.diffuse_color = (0.05, 0.048, 0.045, 1)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(38))
    me.color_attributes.active_color = me.color_attributes['Col']
    ob = bpy.data.objects.new('WatchBlade', me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    kw = dict(filepath=os.path.join(OUT, 'watch_blade.glb'), export_format='GLB', use_selection=True, export_apply=True,
              export_yup=True, export_materials='EXPORT')
    try:
        bpy.ops.export_scene.gltf(**kw, export_vertex_color='ACTIVE')
    except TypeError:
        bpy.ops.export_scene.gltf(**kw, export_colors=True)
    print('BLADE tris', sum(len(p.vertices) - 2 for p in me.polygons))


main()
