"""Her Sunderer greatsword: the blade The Long Cut forms in her hands (CLASSES.md, FLARE_LOOK.md "The Long Cut").

    blender -b -P tools/assets/sunder_blade.py

A knight's two-hander at HER scale (1.41 m, not the Warden's giant 1.6 m Watch blade): a gilt wheel pommel, its dished faces
each carrying a sunburst round a domed boss (her belt buckle's sun); 0.27 m of grip for her two fists with a lever gap
between them (dark leather, a little waisted, a gilt ferrule at each end); a straight gilt crossguard 0.30 m wide, 18 mm deep
and near square, flaring at its ends, over a 45 x 35 mm block; a broad clean blade 1.04 m long (70 mm at the guard, 48 mm at
80% of its length, then a true point, 7 mm thick at the root so its edge bevel has a face), its fuller 18 mm wide and 2.5 mm
deep over 70% of the blade. The gilt etched panel below the guard, the steel's brushing and the leather's spiral are the
shader's (godot/shaders/sunder_steel.gdshader). Round 1 (1.35 m, a 55 mm blade) failed its close-up judge.

Out: godot/art/weapons/sunder_blade.glb, one mesh "SunderBlade" (one material; LampIron.SunderBlade shades it with
sunder_steel.gdshader). Vertex colour as watch_blade.py: R convexity (0.5 flat, 1 a sharp outer edge, 0 a crease), G the part
(0.5 the gilt fittings, 1.0 the grip's leather; on the blade 0.05 the edge bevel, 0.15 the flats, 0.25 the fuller), B a
per-part random. Frame (the game's): the pommel's end at y = 0, the tip up +y at 1.412, the guard along x. Arms
"sunder_blade" scales it by its Spec (Length 1.412, so 1:1).

Her fists (m from the pommel end): the right (upper) fist's centre at 0.290 (its forefinger at the guard's ferrule), the
left (lower) at 0.120 (its heel at the pommel's ferrule), a lever gap of about 0.08 m between them; the leather runs
0.068-0.338.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'godot', 'art', 'weapons')
NAME = 'sunder_blade'
G2B = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
rng = random.Random(23)

POMMEL_Y = 0.033      # the wheel's centre
GRIP_Y0 = 0.068       # the leather's lower end
GRIP_Y1 = 0.338       # the leather's upper end (0.27 m of leather)
GUARD_Y = 0.355       # the crossguard bar's centre line
BLADE_Y = 0.372       # the blade's root (inside the guard's block)
TIP_Y = BLADE_Y + 1.04
GUARD_HALF = 0.150
BLOCK = (0.045, 0.035, 0.034)   # the guard's centre block: along the guard, along the blade, through
BLOCK_Y = 0.360
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


def blade():
    """Lofted sections along y: a flattened hexagon with a fuller and its edge bevel, each face tagged with its region,
    the rows denser toward the point (where the outline curves)."""
    bm = bmesh.new()
    rows, tags = [], []
    n = 84
    L = TIP_Y - BLADE_Y
    tip0 = BLADE_Y + 0.80 * L       # where the point begins
    full_end = BLADE_Y + 0.70 * L   # the fuller: 70% of the blade from the guard
    L = TIP_Y - BLADE_Y
    for i in range(n + 1):
        u = i / n
        y = BLADE_Y + L * (1 - (1 - u) ** 1.25)
        s = (y - BLADE_Y) / L
        w = 0.035 - 0.0110 * min(s, 0.8) / 0.8       # half-width: 70 mm at the guard, 48 mm where the point begins
        t = 0.0070 - 0.0030 * s                      # thickness
        if y > tip0:
            p = (y - tip0) / (TIP_Y - tip0)
            k = (1 - p ** 1.5) ** 0.62 * (1 - 0.18 * p)   # a true point, its sides just convex
            w *= max(k, 0.0)
            t *= max(0.35 + 0.65 * k, 0.0) if p < 1 else 0.0
        fd = 0.0025 * min(1.0, max(0.0, (y - BLADE_Y - 0.008) / 0.025)) * max(0.0, min(1.0, (full_end - y) / 0.05))
        fw = 0.0090 * (1 - 0.25 * s)                 # the fuller: 18 mm wide at the guard, 2.5 mm deep
        if i == n:
            rows.append([bm.verts.new((0, TIP_Y, 0))])
            continue
        ht = t / 2
        e = 0.60   # the edge bevel's inner line, as a fraction of the half-width
        sh = min(fw * 1.5, w * e * 0.9)
        pts = [(w, 0), (w * e, ht * 0.92), (sh, ht), (fw, ht - fd * 0.12), (fw * 0.55, ht - fd * 0.78), (0, ht - fd),
               (-fw * 0.55, ht - fd * 0.78), (-fw, ht - fd * 0.12), (-sh, ht), (-w * e, ht * 0.92), (-w, 0)]
        pts += [(x, -z) for x, z in reversed(pts[1:-1])]
        rows.append([bm.verts.new((x, y, z)) for x, z in pts])
        f = fd > 0.0004
        fu = G_FULLER if f else G_FLAT
        top = [G_BEVEL, G_FLAT, G_FLAT, fu, fu, fu, fu, G_FLAT, G_FLAT, G_BEVEL]
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
    """The grip: oval, a little waisted between the hands; its leather's lapped spiral (12 mm pitch) is the shader's."""
    y0, y1 = GRIP_Y0, GRIP_Y1
    segs = 16
    bm = bmesh.new()
    n = int((y1 - y0) / 0.006)
    rows = []
    for i in range(n + 1):
        y = y0 + (y1 - y0) * i / n
        s = (y - y0) / (y1 - y0)
        r = 0.0153 - 0.0013 * math.sin(math.pi * s) ** 2 + 0.0007 * s     # waisted, a touch fuller under the guard
        ring = []
        for k in range(segs):
            th = k * math.tau / segs
            ring.append(bm.verts.new((r * math.cos(th), y, 0.84 * r * math.sin(th))))
        rows.append(ring)
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(segs):
            bm.faces.new((r0[k], r0[(k + 1) % segs], r1[(k + 1) % segs], r1[k]))
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def guard_bar():
    """The crossguard: straight, square in section, thickest at the block, slimming, then flaring to squared ends."""
    bm = bmesh.new()
    n = 36
    rows = []
    for i in range(n + 1):
        x = -GUARD_HALF + 2 * GUARD_HALF * i / n
        a = abs(x) / GUARD_HALF
        fl = max(0.0, (a - 0.8) / 0.2) ** 1.6
        hy = 0.0090 - 0.0016 * min(a / 0.8, 1.0) + 0.0040 * fl     # 18 mm deep at the block
        hz = 0.0095 - 0.0016 * min(a / 0.8, 1.0) + 0.0040 * fl
        c = 0.0018
        sec = [(hy, hz - c), (hy - c, hz), (-hy + c, hz), (-hy, hz - c), (-hy, -hz + c), (-hy + c, -hz), (hy - c, -hz), (hy, -hz + c)]
        rows.append([bm.verts.new((x, GUARD_Y + dy, dz)) for dy, dz in sec])
    m = 8
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(m):
            bm.faces.new((r0[k], r0[(k + 1) % m], r1[(k + 1) % m], r1[k]))
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def sun_rays(face_z, sgn):
    """A sunburst on one face of the wheel (her belt buckle's sun): sixteen faceted rays round the boss, long and short in
    turn, each a ridge rising from the dish at its root and running down to its point."""
    bm = bmesh.new()
    for k in range(16):
        a = k * math.tau / 16
        r0, r1 = 0.0098, (0.0212 if k % 2 == 0 else 0.0182)
        hw = 0.0026 if k % 2 == 0 else 0.0021
        d = Vector((math.cos(a), math.sin(a), 0))
        n = Vector((-math.sin(a), math.cos(a), 0))
        z0 = face_z * sgn
        up = Vector((0, 0, sgn))
        base = d * r0
        vl = bm.verts.new(base + n * hw + up * 0 + Vector((0, 0, z0)))
        vr = bm.verts.new(base - n * hw + Vector((0, 0, z0)))
        vt = bm.verts.new(d * r1 + Vector((0, 0, z0)))
        vh = bm.verts.new(base + Vector((0, 0, z0)) + up * 0.0030)
        vm = bm.verts.new(d * (r0 + 0.6 * (r1 - r0)) + Vector((0, 0, z0)) + up * 0.0014)
        bm.faces.new((vl, vh, vm, vt))
        bm.faces.new((vr, vt, vm, vh))
        bm.faces.new((vl, vr, vh))
        bm.faces.new((vl, vt, vr))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def fittings():
    parts = []
    # Wheel pommel, its axis along z: a raised rim, a dished face with a sunburst round a domed boss; the tang's peen below.
    half = [(0.0290, 0.0), (0.0284, 0.0075), (0.0268, 0.0125), (0.0250, 0.0160), (0.0228, 0.0162), (0.0216, 0.0128),
            (0.0120, 0.0120), (0.0092, 0.0126), (0.0083, 0.0168), (0.0062, 0.0192), (0.0032, 0.0201), (0.0, 0.0203)]
    prof = [(r, -z) for r, z in reversed(half)] + [(r, z) for r, z in half[1:]]
    pom = lathe(prof, 32)
    rot = Matrix.Translation((0, POMMEL_Y, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'X')
    parts.append((pom, rot))
    # (the lathe's axis y becomes z under the rotation; the rays are built in the turned frame, so only moved)
    for sgn in (1, -1):
        parts.append((sun_rays(0.0119, sgn), Matrix.Translation((0, POMMEL_Y, 0))))
    parts.append((lathe([(0.0065, 0.0060), (0.0060, 0.0018), (0.0035, 0.0002), (0.0, 0.0)], 10), Matrix.Identity(4)))
    # Ferrules: one between pommel and grip, one under the guard.
    parts.append((lathe([(0.0, GRIP_Y0 + 0.003), (0.0150, GRIP_Y0 + 0.003), (0.0170, GRIP_Y0 - 0.002), (0.0145, GRIP_Y0 - 0.010),
                         (0.0, GRIP_Y0 - 0.010)], 16, zscale=0.84), Matrix.Identity(4)))
    parts.append((lathe([(0.0, GRIP_Y1 - 0.003), (0.0165, GRIP_Y1 - 0.003), (0.0182, GRIP_Y1 + 0.002), (0.0175, GUARD_Y - 0.007),
                         (0.0, GUARD_Y - 0.007)], 16, zscale=0.84), Matrix.Identity(4)))
    # The guard: the bar, and a block at its middle with the blade's root through it.
    parts.append((guard_bar(), Matrix.Identity(4)))
    parts.append((box(*BLOCK, 0.0035), Matrix.Translation((0, BLOCK_Y, 0))))
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
    me = bpy.data.meshes.new('SunderBlade')
    bm.to_mesh(me)
    bm.free()
    mat = bpy.data.materials.new('sunder_steel')
    mat.diffuse_color = (0.5, 0.5, 0.5, 1)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(38))
    me.color_attributes.active_color = me.color_attributes['Col']
    ob = bpy.data.objects.new('SunderBlade', me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    path = os.path.join(OUT, NAME + '.glb')
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
              export_yup=True, export_materials='EXPORT')
    try:
        bpy.ops.export_scene.gltf(**kw, export_vertex_color='ACTIVE')
    except TypeError:
        bpy.ops.export_scene.gltf(**kw, export_colors=True)
    fix_colours(path)
    lo = [min(v.co[i] for v in me.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in me.vertices) for i in range(3)]
    print('SUNDER tris', sum(len(p.vertices) - 2 for p in me.polygons), 'bounds (blender xyz)', [round(a, 4) for a in lo], [round(a, 4) for a in hi])


def fix_colours(path):
    """Blender 4.5's exporter writes a white COLOR_0 and the 'Col' layer as COLOR_1, and Godot reads only COLOR_0: point
    COLOR_0 at the real layer and drop the white one (as watch_blade.py)."""
    import json, struct
    d = open(path, 'rb').read()
    jl = struct.unpack('<I', d[12:16])[0]
    j = json.loads(d[20:20 + jl])
    for m in j['meshes']:
        for p in m['primitives']:
            a = p['attributes']
            if 'COLOR_1' in a:
                a['COLOR_0'] = a.pop('COLOR_1')
    js = json.dumps(j, separators=(',', ':')).encode()
    js += b' ' * (-len(js) % 4)
    rest = d[20 + jl:]
    out = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(js) + len(rest)) + struct.pack('<I4s', len(js), b'JSON') + js + rest
    open(path, 'wb').write(out)


main()
