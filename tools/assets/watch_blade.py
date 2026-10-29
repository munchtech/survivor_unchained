"""The Ford-Warden's sword: an old Watch blade, straight and corroded (concept A, warden_concepts/pick/A_hero.png).

    blender -b -P tools/assets/watch_blade.py

A two-hand longsword at a giant's scale (Warden 7: the r1 blade read as a toy or a crowbar): a broad
wheel pommel with a raised rim and its peened tang, a grip two hands long bound in a lapped spiral of
leather, a long straight square-section crossguard flaring at its ends, and a broad straight blade with
a fuller two-thirds down it, a wide edge bevel, and nicks along both edges from use.

Out: godot/art/weapons/watch_blade.glb, one mesh "WatchBlade" (one material, keeper_iron in the
game). Its vertex colour: R convexity (0.5 flat, 1 a sharp outer edge, 0 a crease), G the part
(0.5 iron, 1.0 the grip's leather; on the blade 0.05 the edge bevel, 0.15 the flats, 0.25 the fuller), B a per-part random. Frame (the game's): the pommel's end at y = 0,
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

GUARD_Y = 0.355
BLADE_Y = 0.385
TIP_Y = 1.55
GRIP_Y0 = 0.098
# The blade's regions, in the vertex colour's G (keeper_iron.gdshader reads G < 0.35 as the blade's steel).
G_BEVEL, G_FLAT, G_FULLER = 0.05, 0.15, 0.25


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
        for _ in range(8):
            out.append((side, rng.uniform(BLADE_Y + 0.10, TIP_Y - 0.10), rng.uniform(0.0015, 0.004), rng.uniform(0.004, 0.011)))
    return out


def blade():
    """Lofted sections along y: a flattened hexagon with a fuller, its edge bevel and nicks. Each face is tagged with its
    region (the bevel, the flat, the fuller), and the rows split along the regions' borders so the vertex colour (G) is
    crisp: the shader wears the bevel bright, keeps the flats dark and stained, the fuller darker still."""
    bm = bmesh.new()
    nk = nicks()
    rows, tags = [], []
    n = 110
    tip0 = TIP_Y - 0.20
    full_end = BLADE_Y + 0.80
    for i in range(n + 1):
        u = i / n
        y = BLADE_Y + (TIP_Y - BLADE_Y) * (u ** 0.95)
        s = (y - BLADE_Y) / (TIP_Y - BLADE_Y)
        w = 0.043 - 0.014 * s                       # half-width, base to the point's start (a long, gently tapered blade)
        t = 0.0115 - 0.005 * s                      # thickness
        if y > tip0:
            p = (y - tip0) / (TIP_Y - tip0)
            k = math.sqrt(max(1 - p ** 1.7, 0.0)) * (1 - 0.3 * p)   # an ogival point
            w *= max(k, 0.0)
            t *= max(0.4 + 0.6 * k, 0.0) if p < 1 else 0.0
        fd = 0.0030 * min(1.0, (y - BLADE_Y - 0.02) / 0.04) * max(0.0, min(1.0, (full_end - y) / 0.08))
        fd = max(fd, 0.0)
        fw = 0.0105 * (1 - 0.35 * s)
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
        e = 0.64   # the edge bevel's inner line, as a fraction of the half-width
        sh = min(fw * 1.45, w * e * 0.9)
        pts = [(wr, 0), (wr * e, ht * 0.9), (sh, ht), (fw, ht - fd * 0.55), (0, ht - fd),
               (-fw, ht - fd * 0.55), (-sh, ht), (-wl * e, ht * 0.9), (-wl, 0)]
        pts += [(x, -z) for x, z in reversed(pts[1:-1])]
        rows.append([bm.verts.new((x, y, z)) for x, z in pts])
        f = fd > 0.0006
        top = [G_BEVEL, G_FLAT, G_FULLER if f else G_FLAT, G_FULLER if f else G_FLAT, G_FULLER if f else G_FLAT,
               G_FULLER if f else G_FLAT, G_FLAT, G_BEVEL]
        tags.append(top + top)
    m = len(rows[0])
    face_tag = {}
    for r, (r0, r1) in enumerate(zip(rows, rows[1:])):
        for k in range(m):
            if len(r1) == 1:
                fc = bm.faces.new((r0[k], r0[(k + 1) % m], r1[0]))
            else:
                fc = bm.faces.new((r0[k], r0[(k + 1) % m], r1[(k + 1) % m], r1[k]))
            face_tag[fc] = tags[r][k]
    base = bm.faces.new(list(reversed(rows[0])))
    face_tag[base] = G_FLAT
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm, face_tag


def grip():
    """The grip: oval, swelling a little in the middle, bound in a spiral of leather strip (each turn's edge lapped over
    the last, a groove where they meet) and a cord binding at each end."""
    y0, y1 = GRIP_Y0, GUARD_Y - 0.006
    segs, pitch = 18, 0.024
    bm = bmesh.new()
    n = int((y1 - y0) / 0.0032)
    rows = []
    for i in range(n + 1):
        y = y0 + (y1 - y0) * i / n
        s = (y - y0) / (y1 - y0)
        r0 = 0.0158 + 0.0020 * math.sin(math.pi * s)
        ring = []
        for k in range(segs):
            th = k * math.tau / segs
            ph = (y / pitch + th / math.tau) % 1.0
            # the strip: rises from the lapped groove, a soft crown, its edge over the next turn
            lap = 0.0011 * (ph ** 0.6) - (0.0009 if ph > 0.93 else 0.0)
            end = min(1.0, s / 0.06, (1 - s) / 0.06)
            r = r0 + lap * end + (1 - end) * 0.0006 * math.cos(y * 2400)
            ring.append(bm.verts.new((r * math.cos(th), y, 0.86 * r * math.sin(th))))
        rows.append(ring)
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(segs):
            bm.faces.new((r0[k], r0[(k + 1) % segs], r1[(k + 1) % segs], r1[k]))
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def guard_bar():
    """The crossguard: a straight bar of square section, thickest at the block, tapering, then flaring to its ends."""
    bm = bmesh.new()
    half, n = 0.185, 44
    rows = []
    for i in range(n + 1):
        x = -half + 2 * half * i / n
        a = abs(x) / half
        hy = 0.0105 - 0.0030 * min(a / 0.8, 1.0) + 0.0055 * max(0.0, (a - 0.82) / 0.18) ** 1.6
        hz = 0.0125 - 0.0035 * min(a / 0.8, 1.0) + 0.0050 * max(0.0, (a - 0.82) / 0.18) ** 1.6
        c = 0.0022
        sec = [(hy, hz - c), (hy - c, hz), (-hy + c, hz), (-hy, hz - c), (-hy, -hz + c), (-hy + c, -hz), (hy - c, -hz), (hy, -hz + c)]
        rows.append([bm.verts.new((x, GUARD_Y + 0.011 + dy, dz)) for dy, dz in sec])
    m = 8
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(m):
            bm.faces.new((r0[k], r0[(k + 1) % m], r1[(k + 1) % m], r1[k]))
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def fittings():
    parts = []
    # Wheel pommel, its axis along z: a raised rim and a boss on each face; the tang's peen below.
    pom = lathe([(0.0, -0.0175), (0.012, -0.0175), (0.016, -0.0150), (0.028, -0.0120), (0.034, -0.0150), (0.040, -0.0145),
                 (0.0455, -0.008), (0.0465, 0.0), (0.0455, 0.008), (0.040, 0.0145), (0.034, 0.0150), (0.028, 0.0120),
                 (0.016, 0.0150), (0.012, 0.0175), (0.0, 0.0175)], 28)
    parts.append((pom, Matrix.Translation((0, 0.050, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'X')))
    parts.append((lathe([(0.0085, 0.0062), (0.0078, 0.0015), (0.0045, -0.0005), (0.0, -0.001)], 10), Matrix.Identity(4)))
    # Collars: one between pommel and grip, one under the guard (iron ferrules).
    parts.append((lathe([(0.0, GRIP_Y0 + 0.002), (0.0155, GRIP_Y0 + 0.002), (0.0175, GRIP_Y0 - 0.004), (0.0150, GRIP_Y0 - 0.010),
                         (0.0, GRIP_Y0 - 0.010)], 16, zscale=0.86), Matrix.Identity(4)))
    parts.append((lathe([(0.0, GUARD_Y - 0.009), (0.0175, GUARD_Y - 0.009), (0.0190, GUARD_Y - 0.003), (0.0, GUARD_Y - 0.003)], 16, zscale=0.86),
                  Matrix.Identity(4)))
    # The guard: the bar, a block at its middle (and the blade's root through it).
    parts.append((guard_bar(), Matrix.Identity(4)))
    parts.append((box(0.066, 0.032, 0.036, 0.004), Matrix.Translation((0, GUARD_Y + 0.0135, 0))))
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
    bl, tags = blade()
    parts = [(bl, Matrix.Identity(4), None), (grip(), Matrix.Identity(4), 1.0)] + [(b, m, 0.5) for b, m in fittings()]
    bm = bmesh.new()
    for pbm, at, part in parts:
        pbm.verts.ensure_lookup_table()
        conv = convexity(pbm)
        lay = pbm.verts.layers.float_color.new('Col')
        rnd = rng.random()
        for v in pbm.verts:
            v[lay] = (conv[v.index], part if part is not None else G_FLAT, rnd, 1.0)
        if part is None:
            # the blade: split along the regions' borders, then each vertex takes its faces' region
            border = [e for e in pbm.edges if len(e.link_faces) == 2 and tags[e.link_faces[0]] != tags[e.link_faces[1]]]
            bmesh.ops.split_edges(pbm, edges=border)
            for f in pbm.faces:
                g = tags.get(f, G_FLAT)
                for v in f.verts:
                    c = v[lay]
                    v[lay] = (c[0], g, c[2], 1.0)
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
