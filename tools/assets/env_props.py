"""The set-dressing props generator (E7a), made here from nothing (no kit, no scan).

    python tools/assets/env_props_atlas.py                 # the shared painted atlas, first
    blender -b -P tools/assets/env_props.py [-- name ...]   # the presets (all, or those named)

Presets are data (tools/assets/env_props.json): a kind (one builder below), a seed,
sizes in metres and a palette. Kinds:

  bedroll_open    a groundsheet, a wool blanket thrown back at the head (a turned-down
                  flap), a rolled cloak for a pillow, two loose leather straps
  bedroll_rolled  the blanket rolled (a spiral of layers at each end), two straps, buckles
  pack            a canvas rucksack with a leather flap and straps, a blanket roll on top
  chest           iron-banded boards, a barrel lid, corner irons, hasp, handles
  crate           a slatted crate: corner posts, rails, slats, a brace on each side
  barrel          staves with their seams, four iron hoops, a head inset under the chime
  log             a log to sit on: bark, sawn ends (rings), an adze-flattened seat, a stub
  wagon           a two-wheeled cart down on one side: its wheel off and broken on the
                  ground, the bed rolled onto its axle stub, shafts down, sacks spilled

Each GLB (godot/art/world/props/<preset>.glb): the preset's mesh (node <preset>) and,
over 1k triangles, its LOD1 (<preset>_LOD1, about 45%). One material, "props": the game
gives it the shared atlas (props_albedo.jpg, props_normal.png, props_orm.png; Godot's
OwnProps). Vertex colours carry the palette tint times a baked occlusion (rays in the
mesh and the ground), contact darkening and lit edges, so every prop shares one material
and one atlas (look bible 11). Origin: on the ground, centred; long axes as noted per kind.
props.json beside them: each preset's triangles per LOD and box.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'godot', 'art', 'world', 'props')
DATA = os.path.join(ROOT, 'tools', 'assets', 'env_props.json')
ATLAS = json.load(open(os.path.join(OUT, 'props_atlas.json')))['regions']

# Game frame (y up, +z out) to Blender's (z up).
G2B = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
B2G = G2B.inverted()


class Rng:
    """A small deterministic generator (no numpy needed in Blender's frame)."""

    def __init__(self, seed):
        self.s = (seed * 2654435761 + 12345) & 0xFFFFFFFF

    def __call__(self, a=0.0, b=1.0):
        self.s = (self.s * 1664525 + 1013904223) & 0xFFFFFFFF
        return a + (b - a) * (self.s / 4294967296.0)


def hexlin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return Vector([x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c])


def hnoise(p, seed=0):
    """Cheap smooth 3D noise in -1..1 (sums of sines, enough for lumps and rumples)."""
    x, y, z = p
    s = seed * 1.7
    return (math.sin(x * 3.1 + s) * math.cos(z * 2.7 - s) + 0.6 * math.sin(y * 4.3 + x * 1.9 + s * 2)
            + 0.4 * math.sin(z * 7.1 - y * 3.3 + s * 3) * math.cos(x * 6.2 + s)) / 2.0


# ----------------------------------------------------------------- parts --

class Part:
    """One piece in its own frame (its grain along local y), its atlas region,
    its tint (linear), placed by a matrix in the game frame.
    cap: the region the faces across the grain (normal along local y) take
    (a board's end grain); capc/capr: a log's cap centre and radius (its rings).
    smooth: shade smooth (cloth, sacks, logs) or flat (boards, iron)."""

    def __init__(self, bm, region, tint, at=Matrix.Identity(4), cap=None, smooth=False, jitter=0.06, capr=None, capto=0.23):
        self.bm, self.region, self.tint, self.at = bm, region, Vector(tint), at
        self.cap, self.smooth, self.jitter, self.capr, self.capto = cap, smooth, jitter, capr, capto


def basis(xa, ya, za):
    """The matrix taking local x, y, z to these game-frame axes."""
    m = Matrix.Identity(4)
    for c, a in enumerate((xa, ya, za)):
        for r in range(3):
            m[r][c] = a[r]
    return m


def T(x, y, z):
    return Matrix.Translation((x, y, z))


def R(axis, a):
    return Matrix.Rotation(a, 4, axis)


def S(x, y, z):
    return Matrix.Diagonal((x, y, z, 1))


def box(sx, sy, sz, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=1, affect='EDGES', profile=0.5)
    return bm


def lathe(profile, segs, cap0=True, cap1=True, a0=0.0, a1=2 * math.pi, closed=True):
    """Rings about local y from (radius, y) pairs; capped with fans."""
    bm = bmesh.new()
    n = segs if closed else segs + 1
    rings = []
    for r, y in profile:
        ring = []
        for i in range(n):
            a = a0 + (a1 - a0) * i / segs
            ring.append(bm.verts.new((r * math.cos(a), y, r * math.sin(a))))
        rings.append(ring)
    for k in range(len(rings) - 1):
        A, B = rings[k], rings[k + 1]
        for i in range(segs):
            j = (i + 1) % n
            if profile[k][0] < 1e-6 and profile[k + 1][0] < 1e-6:
                continue
            bm.faces.new((A[i], A[j], B[j], B[i]) if not closed or True else None)
    if closed:
        if cap0 and profile[0][0] > 1e-6:
            bm.faces.new(list(reversed(rings[0])))
        if cap1 and profile[-1][0] > 1e-6:
            bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.normal_update()
    _outward(bm)
    return bm


def _outward(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def ribbon(pts, w, t, up=Vector((0, 1, 0))):
    """A flat strip (width w, thickness t) along a polyline, lying with its face to `up`."""
    bm = bmesh.new()
    top, bot = [], []
    for i, p in enumerate(pts):
        p = Vector(p)
        d = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
        side = d.cross(up).normalized() * (w / 2)
        top.append((bm.verts.new(p + side + up * t), bm.verts.new(p - side + up * t)))
        bot.append((bm.verts.new(p + side), bm.verts.new(p - side)))
    for i in range(len(pts) - 1):
        a, b = top[i], top[i + 1]
        bm.faces.new((a[0], b[0], b[1], a[1]))
        c, d2 = bot[i], bot[i + 1]
        bm.faces.new((c[1], d2[1], d2[0], c[0]))
        bm.faces.new((c[0], d2[0], b[0], a[0]))
        bm.faces.new((a[1], b[1], d2[1], c[1]))
    _outward(bm)
    return bm


def torus(R_, r, segs, tube, a0=0.0, a1=2 * math.pi, rect=False, width=None):
    """A ring about local y (radius R_, tube r); an arc when a1 - a0 < 2 pi. rect: a band r deep, width wide."""
    width = width or 5 * r
    bm = bmesh.new()
    closed = abs(a1 - a0 - 2 * math.pi) < 1e-6
    n = segs if closed else segs + 1
    prof = ([(R_ + r, -width / 2), (R_ + r, width / 2), (R_, width / 2), (R_, -width / 2)] if rect else
            [(R_ + r * math.cos(2 * math.pi * k / tube), r * math.sin(2 * math.pi * k / tube)) for k in range(tube)])
    rings = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / segs
        rings.append([bm.verts.new((rr * math.cos(a), yy, rr * math.sin(a))) for rr, yy in prof])
    m = len(prof)
    for i in range(segs if closed else segs):
        A, B = rings[i], rings[(i + 1) % n]
        for k in range(m):
            bm.faces.new((A[k], A[(k + 1) % m], B[(k + 1) % m], B[k]))
    if not closed:
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
    _outward(bm)
    return bm


def grid(nu, nv, fn, skirt=None):
    """A surface over (u, v) in 0..1 x 0..1, nu x nv quads, fn(u, v) -> (x, y, z).
    skirt: drop the border this far (a cloth's edge thickness to the ground)."""
    bm = bmesh.new()
    V = [[bm.verts.new(fn(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((V[i][j], V[i][j + 1], V[i + 1][j + 1], V[i + 1][j]))
    if skirt:
        border = [V[i][0] for i in range(nu + 1)] + [V[nu][j] for j in range(1, nv + 1)] + \
                 [V[i][nv] for i in range(nu - 1, -1, -1)] + [V[0][j] for j in range(nv - 1, 0, -1)]
        low = [bm.verts.new(v.co - Vector((0, skirt, 0))) for v in border]
        k = len(border)
        for i in range(k):
            bm.faces.new((border[i], border[(i + 1) % k], low[(i + 1) % k], low[i]))
    bm.normal_update()
    up = sum((f.normal.y for f in bm.faces), 0.0)
    if up < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    return bm


# ------------------------------------------------------------------- UVs --

def uv_part(p, rng):
    """Box-project the part's faces into its region, in its own frame (grain along local y),
    each island placed at a random spot in the region (shrunk only if it is bigger)."""
    bm = p.bm
    uvl = bm.loops.layers.uv.verify()
    groups = {}
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        region = p.cap if (ax == 1 and p.cap) else p.region
        if p.capr and ax == 1 and p.cap:
            # A sawn end or a roll's end: the tile's rings centred, the edge at capto metres out
            # (the end grain's bark rim at 0.23 of its 0.5 m; a roll's spiral to its tile's edge).
            u0, v0, u1, v1 = ATLAS[region]['uv']
            mu = ATLAS[region]['m'][0]
            k = p.capto / p.capr / mu
            for l in f.loops:
                c = l.vert.co
                l[uvl].uv = (u0 + (u1 - u0) * (0.5 + c.x * k), v0 + (v1 - v0) * (0.5 + c.z * k))
            continue
        groups.setdefault((region, ax), []).append(f)
    for (region, ax), faces in groups.items():
        u0, v0, u1, v1 = ATLAS[region]['uv']
        mu, mv = ATLAS[region]['m']

        def ab(c):
            if ax == 1:
                return c.x, c.z
            if ax == 0:
                return c.z, c.y
            return c.x, c.y
        pts = [ab(l.vert.co) for f in faces for l in f.loops]
        amin, amax = min(a for a, _ in pts), max(a for a, _ in pts)
        bmin, bmax = min(b for _, b in pts), max(b for _, b in pts)
        k = min(1.0, mu / max(amax - amin, 1e-6), mv / max(bmax - bmin, 1e-6))
        offa = rng(0, max(0.0, mu - (amax - amin) * k))
        offb = rng(0, max(0.0, mv - (bmax - bmin) * k))
        for f in faces:
            for l in f.loops:
                a, b = ab(l.vert.co)
                uu = (offa + (a - amin) * k) / mu
                vv = (offb + (b - bmin) * k) / mv
                l[uvl].uv = (u0 + (u1 - u0) * min(max(uu, 0.004), 0.996), v0 + (v1 - v0) * min(max(vv, 0.004), 0.996))


# ---------------------------------------------------------------- shading --

def bake_colours(me, tints, kind_of_face, ground=True, rays=14):
    """Vertex colours per face corner: tint x occlusion (rays against the mesh and the
    ground plane y = 0) x contact darkening x lit convex edges (wood and iron)."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.transform(B2G)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    tree = BVHTree.FromBMesh(bm)
    # Hemisphere directions (a fixed spiral).
    dirs = []
    for i in range(rays):
        z = 1 - (i + 0.5) / rays
        r = math.sqrt(max(0.0, 1 - z * z))
        a = i * 2.39996
        dirs.append(Vector((r * math.cos(a), z, r * math.sin(a))))
    occ, conv = [], []
    for v in bm.verts:
        n = v.normal
        t = n.orthogonal().normalized()
        b = n.cross(t)
        hit = 0.0
        for d in dirs:
            w = (t * d.x + n * d.y + b * d.z).normalized()
            o = v.co + n * 0.004
            if ground and w.y < 0 and o.y > -0.01:
                hit += 1.0 if (o.y / max(-w.y, 1e-4)) < 0.45 else 0.0
                continue
            h = tree.ray_cast(o, w, 0.45)
            if h[0] is not None:
                hit += 1.0 - (h[3] / 0.45) * 0.6
        occ.append(1.0 - 0.75 * hit / rays)
        c = 0.0
        for e in v.link_edges:
            o2 = e.other_vert(v).co - v.co
            if o2.length > 1e-6:
                c -= n.dot(o2.normalized())
        conv.append(c / max(1, len(v.link_edges)))
    if 'tint' in me.color_attributes:
        me.color_attributes.remove(me.color_attributes['tint'])
    ca = me.color_attributes.new('tint', 'FLOAT_COLOR', 'CORNER')
    for poly in me.polygons:
        tint = tints[poly.index]
        hard = kind_of_face[poly.index] in ('wood', 'iron', 'endgrain', 'stone', 'bark')
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            y = bm.verts[vi].co.y
            s = occ[vi] * (0.72 + 0.28 * min(1.0, max(0.0, y / 0.08)) if ground else 1.0)
            if hard:
                s *= 1.0 + 0.35 * max(0.0, min(conv[vi], 0.6))
            s *= 1.0 + 0.4 * min(0.0, max(conv[vi], -0.5)) * 0.6
            c = tint * s
            ca.data[li].color = (min(c.x, 1.0), min(c.y, 1.0), min(c.z, 1.0), 1.0)
    me.color_attributes.active_color = ca
    bm.free()


def finish(name, parts, mat, seed):
    """Merge the parts (each face keeps its part's tint and kind), triangulate, bake, link."""
    rng = Rng(seed)
    bm = bmesh.new()
    lay_t = bm.faces.layers.int.new('part')
    info = []
    for pi, p in enumerate(parts):
        p.bm.normal_update()
        uv_part(p, rng)
        p.bm.transform(G2B @ p.at)
        if p.at.determinant() < 0:
            bmesh.ops.reverse_faces(p.bm, faces=p.bm.faces[:])
        me = bpy.data.meshes.new('tmp')
        p.bm.to_mesh(me)
        n0 = len(bm.faces)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        p.bm.free()
        bm.faces.ensure_lookup_table()
        lay_t = bm.faces.layers.int.get('part') or bm.faces.layers.int.new('part')
        for f in bm.faces[n0:]:
            f[lay_t] = pi
        info.append((p.tint * (1.0 + rng(-p.jitter, p.jitter)), p.region, p.smooth))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    lay_t = bm.faces.layers.int.get('part')
    pidx = [f[lay_t] for f in bm.faces]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = info[pidx[poly.index]][2]
    tints = [info[i][0] for i in pidx]
    kinds = [info[i][1] for i in pidx]
    bake_colours(me, tints, kinds)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# --------------------------------------------------------------- presets --

def strap_loop(R_, w, t, segs=14):
    """A leather strap round a roll (about local y), flat band."""
    bm = bmesh.new()
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        c, s = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((rr * c, yy, rr * s)) for rr, yy in ((R_ + t, -w / 2), (R_ + t, w / 2), (R_, w / 2), (R_, -w / 2))])
    for i in range(segs):
        A, B = rings[i], rings[(i + 1) % segs]
        for k in range(4):
            bm.faces.new((A[k], A[(k + 1) % 4], B[(k + 1) % 4], B[k]))
    _outward(bm)
    return bm


def roll_parts(p, L, r, at, rng, blanket, band, strap, sag=0.0):
    """A blanket rolled along local x: the roll (soft, lumpy, a woven band near each end),
    a spiral at each end, two straps with buckles."""
    out = []
    segs, rings = 14, 6
    prof = []
    for k in range(rings + 1):
        x = -L / 2 + L * k / rings
        rr = r * (1 + 0.05 * math.sin(k * 1.7 + p['seed']))
        prof.append((rr, x))
    bm = lathe(prof, segs, cap0=False, cap1=False)
    for v in bm.verts:
        v.co.x *= 1 + 0.04 * hnoise(v.co * 6, p['seed'])
        v.co.z *= 1 + 0.04 * hnoise(v.co * 5, p['seed'] + 1)
        v.co.y += sag * (1 - (2 * v.co.y / L) ** 2) * 0
    # local y is the roll's axis: turn it to x
    turn = R('Z', -math.pi / 2)
    out.append(Part(bm, 'cloth', blanket, at @ turn, smooth=True, jitter=0.0))
    for sgn in (-1, 1):
        endc = lathe([(r * 0.98, 0.0), (0.0, 0.004)], segs, cap0=False, cap1=False)
        out.append(Part(endc, 'rollend', blanket * 0.95, at @ turn @ T(0, sgn * L / 2, 0) @ (R('X', math.pi) if sgn < 0 else Matrix.Identity(4)),
                        cap='rollend', smooth=True, jitter=0.0, capr=r, capto=0.14))
        # the woven band near the end
        bnd = lathe([(r * 1.006, -0.03), (r * 1.006, 0.03)], segs, cap0=False, cap1=False)
        out.append(Part(bnd, 'cloth', band, at @ turn @ T(0, sgn * (L / 2 - 0.08), 0), smooth=True, jitter=0.0))
        st = strap_loop(r * 1.01, 0.035, 0.006)
        out.append(Part(st, 'leather', strap, at @ turn @ T(0, sgn * L * 0.27, 0)))
        bk = box(0.045, 0.045, 0.012)
        out.append(Part(bk, 'iron', hexlin('#ffffff'), at @ turn @ T(0, sgn * L * 0.27, 0) @ T(r + 0.012, 0, 0) @ R('Z', math.pi / 2)))
    return out


def bedroll_open(p):
    rng = Rng(p['seed'])
    L, W = p['len'], p['wide']
    parts = []
    blanket, band, sheet, pillow, strap = (hexlin(p[k]) for k in ('blanket', 'band', 'sheet', 'pillow', 'strap'))

    # The groundsheet: oiled canvas, edges curling up a little.
    def gs(u, v):
        x, z = (u - 0.5) * (W + 0.1), (v - 0.5) * (L + 0.28)
        e = max(abs(u - 0.5), abs(v - 0.5)) * 2
        y = 0.008 + 0.012 * max(0.0, e - 0.85) / 0.15 + 0.004 * hnoise((x * 3, 0, z * 3), p['seed'])
        return (x, y, z)
    parts.append(Part(grid(6, 14, gs, skirt=0.012), 'canvas', sheet, smooth=True, jitter=0.0))

    # The blanket: foot (v = 0, +z) to head (v = 1, -z); the head end turned down along a slanted line.
    fold_v = 0.62
    rf = 0.022

    def fold_at(u):
        return fold_v + 0.08 * (u - 0.5)

    def bl(u, v):
        x = (u - 0.5) * W
        rump = 0.02 * hnoise((x * 4, 0, v * 7), p['seed']) + 0.012 * math.sin(v * 17 + u * 5) * (0.5 + 0.5 * math.sin(u * 9 + 1))
        # the body's hollow: a little lower down the middle of the lower half, raised edges
        hollow = -0.006 * math.exp(-((u - 0.5) / 0.22) ** 2) + 0.004 * (abs(u - 0.5) * 2) ** 3
        # edges draped down to the sheet
        drape = -0.02 * max(0.0, abs(u - 0.5) * 2 - 0.86) / 0.14
        base = 0.03 + rump + hollow + drape
        vf = fold_at(u)
        if v <= vf:
            z = (0.5 - v) * L
            return (x, base, z)
        d = (v - vf) * L
        zf = (0.5 - vf) * L
        if d < math.pi * rf:
            th = d / rf
            return (x, base + rf - rf * math.cos(th), zf - rf * math.sin(th) * 0.9)
        back = d - math.pi * rf
        return (x, base + 2 * rf + 0.006 * hnoise((x * 5, 1, back * 9), p['seed'] + 3), zf + back)
    nu, nv = 8, 22
    bmb = grid(nu, nv, bl)
    # The flap's faces turned over (its top is the blanket's underside): both sides drawn there.
    flap = [f for f in bmb.faces if sum(1 for v in f.verts if v.co.y > 0.03 + 1.2 * rf) >= 2]
    dup = bmesh.ops.duplicate(bmb, geom=flap)
    bmesh.ops.reverse_faces(bmb, faces=[g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)])
    for g in dup['geom']:
        if isinstance(g, bmesh.types.BMVert):
            g.co.y += 0.003
    parts.append(Part(bmb, 'cloth', blanket, smooth=True, jitter=0.0))
    # A woven band across the blanket near its foot, and one on the flap (the head end's band, turned).
    for vb in (0.08, 0.94):
        def bandf(u, v, vb=vb):
            q = bl(u, vb + (v - 0.5) * 0.045)
            return (q[0], q[1] + 0.0025, q[2])
        bb = grid(nu, 1, bandf)
        if vb > 0.5:
            bmesh.ops.reverse_faces(bb, faces=bb.faces[:])
        parts.append(Part(bb, 'cloth', band, smooth=True, jitter=0.0))
    # The pillow: a rolled cloak across the head of the sheet.
    pr = 0.085
    parts += roll_parts(p, W * 0.78, pr, T(0, pr * 0.8, -(L / 2) - 0.02) @ S(1, 0.72, 1), rng, pillow, pillow * 1.1, strap)
    # Two straps lying loose by the head, curving.
    for k, (x0, z0, a) in enumerate(((W / 2 + 0.12, -L / 2 + 0.25, 0.4), (W / 2 + 0.05, -L / 2 + 0.55, -0.3))):
        pts = []
        for i in range(7):
            t = i / 6
            pts.append((x0 + 0.08 * math.sin(t * 3 + k), 0.004 + 0.006 * math.sin(t * 7), z0 + (t - 0.5) * 0.55))
        parts.append(Part(ribbon(pts, 0.032, 0.006), 'leather', strap, R('Y', a) @ T(0, 0, 0)))
        parts.append(Part(box(0.05, 0.012, 0.045), 'iron', hexlin('#ffffff'), R('Y', a) @ T(pts[0][0], 0.008, pts[0][2])))
    return parts


def bedroll_rolled(p):
    rng = Rng(p['seed'])
    r = p['r']
    return roll_parts(p, p['len'], r, T(0, r * 0.92, 0), rng, hexlin(p['blanket']), hexlin(p['band']), hexlin(p['strap']))


def pack(p):
    rng = Rng(p['seed'])
    H, Rr = p['h'], p['r']
    parts = []
    cloth, flap, strap = hexlin(p['cloth']), hexlin(p['flap']), hexlin(p['strap'])
    prof = [(Rr * 0.8, 0.0), (Rr * 0.97, 0.05), (Rr, 0.18), (Rr * 0.98, 0.33), (Rr * 0.9, 0.45), (Rr * 0.72, H * 0.9), (Rr * 0.5, H)]
    body = lathe(prof, 14, cap0=True, cap1=True)
    for v in body.verts:
        # flattened back to front (a pack, not a sack), lumpy with what's in it, slumped forward
        v.co.z *= 0.72
        k = 1 + 0.06 * hnoise(v.co * 7, p['seed'])
        v.co.x *= k
        v.co.z *= k
        v.co.z += 0.03 * (v.co.y / H) ** 2
        v.co.y = max(v.co.y, 0.0)
    parts.append(Part(body, 'canvas', cloth, smooth=True, jitter=0.0))
    # The leather flap over the top and down the front.
    def fl(u, v):
        a = (u - 0.5) * 2.0
        x = a * Rr * 0.7
        if v < 0.45:
            t = v / 0.45
            z = -Rr * 0.5 + t * Rr * 0.95
            y = H + 0.012 + 0.03 * math.sin(t * math.pi)
        else:
            t = (v - 0.45) / 0.55
            z = Rr * 0.45 + 0.03 * t
            y = H - t * H * 0.42
        return (x, y + 0.004 * hnoise((x * 9, y, z), 2), z + 0.012)
    parts.append(Part(grid(5, 8, fl), 'leather', flap, smooth=True, jitter=0.0))
    # Two buckled straps down the flap.
    for sx in (-1, 1):
        x = sx * Rr * 0.35
        parts.append(Part(box(0.035, H * 0.5, 0.008), 'leather', strap * 0.85, T(x, H * 0.55, Rr * 0.76 + 0.03)))
        parts.append(Part(box(0.05, 0.045, 0.012), 'iron', hexlin('#ffffff'), T(x, H * 0.45, Rr * 0.76 + 0.04)))
    # Shoulder straps on the back.
    for sx in (-1, 1):
        pts = [(sx * Rr * 0.4, H * 0.85, -Rr * 0.72 - 0.005), (sx * Rr * 0.45, H * 0.5, -Rr * 0.8 - 0.06),
               (sx * Rr * 0.5, H * 0.15, -Rr * 0.74 - 0.005)]
        parts.append(Part(ribbon(pts, 0.045, 0.008, up=Vector((0, 0, -1))), 'leather', strap))
    # The blanket roll strapped across the top.
    parts += roll_parts(dict(p, seed=p['seed'] + 5), Rr * 2.6, 0.085, T(0, H + 0.075, -0.02), rng, hexlin(p['roll']), hexlin(p['band']), strap)
    return parts


def chest(p):
    W, D, H, Lh = p['w'], p['d'], p['h'], p['lid']
    wood, iron = hexlin(p['wood']), hexlin(p['iron'])
    parts = []
    t = 0.03
    nb = 3
    bh = H / nb
    for k in range(nb):
        y = bh * (k + 0.5)
        for sz in (-1, 1):  # front and back boards (grain along x: turn local y to x)
            parts.append(Part(box(bh - 0.006, W, t, 0.004), 'wood', wood, T(0, y, sz * (D / 2 - t / 2)) @ R('Z', math.pi / 2), cap='endgrain'))
        for sx in (-1, 1):
            parts.append(Part(box(bh - 0.006, D - 2 * t, t, 0.004), 'wood', wood, T(sx * (W / 2 - t / 2), y, 0) @ R('Y', math.pi / 2) @ R('Z', math.pi / 2), cap='endgrain'))
    parts.append(Part(box(W - 0.01, 0.025, D - 0.01), 'wood', wood * 0.8, T(0, 0.0125, 0)))
    # The lid: slats along x on an arc over z, end pieces.
    ns = 6
    Rl = (D / 2) ** 2 / (2 * Lh) + Lh / 2
    cy = H + Lh - Rl
    half = math.asin(min(1.0, (D / 2) / Rl))
    for k in range(ns):
        a = -half + 2 * half * (k + 0.5) / ns
        w = 2 * Rl * math.sin(half / ns) - 0.004
        parts.append(Part(box(0.026, W + 0.012, w, 0.004), 'wood', wood,
                          T(0, cy, 0) @ R('X', -a) @ T(0, Rl, 0) @ R('Z', math.pi / 2), cap='endgrain'))
    for sx in (-1, 1):
        prof = [(Vector((0, H, -D / 2)))]
        bm = bmesh.new()
        vs = [bm.verts.new((sx * (W / 2 + 0.002), H, -D / 2))]
        for k in range(ns + 1):
            a = -half + 2 * half * k / ns
            vs.append(bm.verts.new((sx * (W / 2 + 0.002), cy + Rl * math.cos(a), Rl * math.sin(a))))
        vs.append(bm.verts.new((sx * (W / 2 + 0.002), H, D / 2)))
        bm.faces.new(vs if sx > 0 else list(reversed(vs)))
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        parts.append(Part(bm, 'wood', wood * 0.9))
    # Iron: two bands over the lid and down front and back, corner irons, a hasp and lock, handles.
    for bx in (-W * 0.3, W * 0.3):
        for k in range(ns):
            a = -half + 2 * half * (k + 0.5) / ns
            w = 2 * Rl * math.sin(half / ns) + 0.002
            parts.append(Part(box(0.06, 0.008, w), 'iron', iron, T(bx, cy, 0) @ R('X', -a) @ T(0, Rl + 0.017, 0)))
        for sz in (-1, 1):
            parts.append(Part(box(0.06, H - 0.02, 0.008), 'iron', iron, T(bx, H / 2 + 0.01, sz * (D / 2 + 0.004))))
    for sx in (-1, 1):
        for sz in (-1, 1):
            for y in (0.06, H - 0.06):
                parts.append(Part(box(0.012, 0.12, 0.1), 'iron', iron, T(sx * (W / 2 + 0.006), y, sz * (D / 2 - 0.05))))
                parts.append(Part(box(0.1, 0.12, 0.012), 'iron', iron, T(sx * (W / 2 - 0.05), y, sz * (D / 2 + 0.006))))
        # a hoop hanging from two staples, in the side's plane
        parts.append(Part(torus(0.06, 0.011, 8, 4, 0, math.pi), 'iron', iron, T(sx * (W / 2 + 0.02), H * 0.66, 0) @ basis((0, 0, 1), (-1, 0, 0), (0, -1, 0))))
        for z in (-0.06, 0.06):
            parts.append(Part(box(0.014, 0.03, 0.02), 'iron', iron, T(sx * (W / 2 + 0.008), H * 0.66, z)))
    parts.append(Part(box(0.07, 0.16, 0.01), 'iron', iron, T(0, H - 0.02, D / 2 + 0.012)))
    parts.append(Part(box(0.09, 0.1, 0.035, 0.006), 'iron', iron, T(0, H - 0.1, D / 2 + 0.025)))
    return parts


def crate(p):
    W, D, H = p['w'], p['d'], p['h']
    wood = hexlin(p['wood'])
    parts = []
    pt = 0.06
    rng = Rng(p['seed'])
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(Part(box(pt, H, pt, 0.006), 'wood', wood, T(sx * (W / 2 - pt / 2), H / 2, sz * (D / 2 - pt / 2)), cap='endgrain'))
    st = 0.022
    for y in (0.05, H - 0.05):
        for sz in (-1, 1):
            parts.append(Part(box(0.08, W - 2 * pt, st, 0.004), 'wood', wood, T(0, y, sz * (D / 2 - st / 2)) @ R('Z', math.pi / 2), cap='endgrain'))
        for sx in (-1, 1):
            parts.append(Part(box(0.08, D - 2 * pt, st, 0.004), 'wood', wood, T(sx * (W / 2 - st / 2), y, 0) @ R('Y', math.pi / 2) @ R('Z', math.pi / 2), cap='endgrain'))
    # Slats between the rails, gaps between them, and a diagonal brace on each side.
    ns = 3
    span = H - 0.18
    sh = span / ns - 0.025
    for k in range(ns):
        y = 0.09 + span * (k + 0.5) / ns
        for sz in (-1, 1):
            parts.append(Part(box(sh, W - 2 * pt, st * 0.8, 0.003), 'wood', wood, T(0, y, sz * (D / 2 - st * 0.4 - 0.004)) @ R('Z', math.pi / 2), cap='endgrain'))
        for sx in (-1, 1):
            parts.append(Part(box(sh, D - 2 * pt, st * 0.8, 0.003), 'wood', wood, T(sx * (W / 2 - st * 0.4 - 0.004), y, 0) @ R('Y', math.pi / 2) @ R('Z', math.pi / 2), cap='endgrain'))
    diag = math.atan2(H - 0.1, W - 2 * pt)
    for sz in (-1, 1):
        ln = math.hypot(H - 0.1, W - 2 * pt)
        parts.append(Part(box(0.07, ln - 0.05, st, 0.004), 'wood', wood * 0.95, T(0, H / 2, sz * (D / 2 + st * 0.3)) @ R('Z', -(math.pi / 2 - diag) * sz), cap='endgrain'))
    for sx in (-1, 1):
        ln = math.hypot(H - 0.1, D - 2 * pt)
        d2 = math.atan2(H - 0.1, D - 2 * pt)
        parts.append(Part(box(st, ln - 0.05, 0.07, 0.004), 'wood', wood * 0.95, T(sx * (W / 2 + st * 0.3), H / 2, 0) @ R('X', (math.pi / 2 - d2) * sx), cap='endgrain'))
    # The lid: four boards across.
    for k in range(4):
        z = -D / 2 + D * (k + 0.5) / 4
        parts.append(Part(box(st, W, D / 4 - 0.012, 0.004), 'wood', wood, T(0, H + st / 2, z) @ R('Z', math.pi / 2), cap='endgrain'))
    return parts


def barrel(p):
    H, Rm, Re = p['h'], p['r'], p['r_end']
    wood, iron = hexlin(p['wood']), hexlin(p['iron'])
    rng = Rng(p['seed'])
    parts = []
    ns, nr = 16, 6

    def rad(y):
        t = (y / H) * 2 - 1
        return Re + (Rm - Re) * (1 - t * t)
    for s in range(ns):
        a0, a1 = 2 * math.pi * s / ns, 2 * math.pi * (s + 1) / ns
        bm = bmesh.new()
        cols = [(a0, -0.006), (a0 + 0.012, 0.0), (a1 - 0.012, 0.0), (a1, -0.006)]
        V = []
        for k in range(nr + 1):
            y = H * k / nr
            row = []
            for a, dr in cols:
                r = rad(y) + dr
                row.append(bm.verts.new((r * math.cos(a), y, r * math.sin(a))))
            V.append(row)
        for k in range(nr):
            for c in range(3):
                bm.faces.new((V[k][c], V[k + 1][c], V[k + 1][c + 1], V[k][c + 1]))
        bm.normal_update()
        if sum(f.normal.dot(f.calc_center_median().normalized()) for f in bm.faces) < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        parts.append(Part(bm, 'wood', wood, smooth=True, jitter=0.08))
    # The chime (inside of the staves over the head) and the heads.
    for y0, sgn in ((0.0, 1), (H, -1)):
        yh = y0 + sgn * 0.035
        ch = lathe([(Re - 0.004, y0), (Re - 0.018, yh)], ns, cap0=False, cap1=False)
        bmesh.ops.reverse_faces(ch, faces=ch.faces[:])
        parts.append(Part(ch, 'wood', wood * 0.7, smooth=True, jitter=0.0))
        hd = lathe([(Re - 0.018, yh), (0.0, yh)], ns, cap0=False, cap1=False)
        hd.normal_update()
        if sum(f.normal.y for f in hd.faces) * sgn < 0:
            bmesh.ops.reverse_faces(hd, faces=hd.faces[:])
        parts.append(Part(hd, 'wood', wood * 0.9, cap='wood', jitter=0.0))
    # Hoops: two near each end.
    for y in (0.09, 0.26, H - 0.26, H - 0.09):
        r = rad(y) + 0.004
        hp = lathe([(r + 0.004, y - 0.03), (r + 0.006, y), (r + 0.004, y + 0.03)], ns, cap0=False, cap1=False)
        parts.append(Part(hp, 'iron', iron, smooth=True, jitter=0.0))
    return parts


def log(p):
    L, r = p['len'], p['r']
    bark, cut = hexlin(p['bark']), hexlin(p['cut'])
    seed = p['seed']
    parts = []
    segs, rings = 16, max(6, int(L / 0.16))
    # a little thinner toward +y (the top of the tree), out of round, bowed, the bark lumpy in plates
    prof = [(r * (1.0 - 0.1 * k / rings), -L / 2 + L * k / rings) for k in range(rings + 1)]
    bm = lathe(prof, segs, cap0=False, cap1=False)
    flat = p.get('flat', 0.0)
    for v in bm.verts:
        a = math.atan2(v.co.z, v.co.x)
        k = (1 + 0.05 * hnoise(v.co * 4.5, seed) + 0.025 * math.sin(a * 5 + v.co.y * 3 + seed)) * (1 + 0.05 * math.cos(2 * a + seed))
        v.co.x *= k
        v.co.z *= k
        v.co.x += 0.025 * (1 - (2 * v.co.y / L) ** 2)  # bowed up in the middle
    # local y is the log's axis; it lies along game x, so its "up" is local +x before the turn.
    seat = []
    if flat > 0:
        top = r - flat
        for f in bm.faces:
            if all(v.co.x > top - 0.02 for v in f.verts):
                seat.append(f)
        for v in bm.verts:
            if v.co.x > top:
                v.co.x = top + 0.004 * hnoise(v.co * 20, seed)
    turn = T(0, r * 0.85, 0) @ R('Z', math.pi / 2)  # local y -> -x (along), local x -> +y (up)
    if seat:
        sbm = bmesh.new()
        vm = {}
        for f in seat:
            vs = []
            for v in f.verts:
                if v.index not in vm:
                    vm[v.index] = sbm.verts.new(v.co + Vector((0.002, 0, 0)))
                vs.append(vm[v.index])
            sbm.faces.new(vs)
        bmesh.ops.delete(bm, geom=seat, context='FACES_ONLY')
        # the seat's grain runs along the log (local y): wood, box-projected on its own up axis
        sbm.normal_update()
        parts.append(Part(sbm, 'wood', cut * 0.85, turn, smooth=False, jitter=0.0))
    parts.append(Part(bm, 'bark', bark, turn, smooth=True, jitter=0.0))
    # Sawn ends: the end rings of the bark tube, filled.
    for sgn in (-1, 1):
        cbm = bmesh.new()
        ring = [v for v in bm.verts if abs(v.co.y - sgn * L / 2) < 1e-4]
        ring.sort(key=lambda v: math.atan2(v.co.z, v.co.x))
        vs = [cbm.verts.new(v.co.copy()) for v in ring]
        f = cbm.faces.new(vs if sgn > 0 else list(reversed(vs)))
        cbm.normal_update()
        if f.normal.y * sgn < 0:
            f.normal_flip()
        bmesh.ops.triangulate(cbm, faces=cbm.faces[:])
        parts.append(Part(cbm, 'endgrain', cut, turn, cap='endgrain', capr=r, jitter=0.0))
    # A branch stub.
    st = lathe([(0.055, 0.0), (0.04, 0.12), (0.03, 0.2)], 6, cap0=False, cap1=True)
    parts.append(Part(st, 'bark', bark * 0.9, turn @ T(r * 0.2, L * 0.18, r * 0.75) @ R('X', 1.2), smooth=True, jitter=0.0))
    return parts


def wheel(R_, rim_w, spokes, broken=(), split=None):
    """A spoked wheel in the x-y plane about local z (its axle), centred. broken: spokes gone
    (stubs left at the hub); split: (a0, a1) an arc of the rim missing."""
    parts = []
    iron = hexlin('#ffffff')
    segs = 16
    a0, a1 = 0.0, 2 * math.pi
    if split:
        a0, a1 = split[1], split[0] + 2 * math.pi
    rim = torus(R_ - 0.065, 0.058, segs, 4, a0, a1, rect=True, width=0.06)  # felloes: a band about local y
    parts.append(('wood', rim, R('X', math.pi / 2), None))
    tyre = torus(R_ - 0.007, 0.008, segs, 4, a0, a1, rect=True, width=0.066)
    parts.append(('iron', tyre, R('X', math.pi / 2), None))
    hub = lathe([(0.07, -0.1), (0.09, -0.04), (0.09, 0.04), (0.07, 0.1)], 8)
    parts.append(('wood', hub, R('X', math.pi / 2), 'endgrain'))
    for k in range(spokes):
        a = 2 * math.pi * (k + 0.5) / spokes
        if k in broken:
            ln = 0.12
        else:
            ln = R_ - 0.12
            if split and (split[0] <= a <= split[1]):
                ln = (R_ - 0.12) * 0.55
        sp = box(0.035, ln, 0.03)
        parts.append(('wood', sp, R('Z', a - math.pi / 2) @ T(0, 0.08 + ln / 2, 0), 'endgrain'))
    return parts


def sack(H, Rr, seed, lie=False):
    prof = [(Rr * 0.7, 0.0), (Rr * 0.95, 0.04), (Rr, 0.14), (Rr * 0.95, H * 0.62), (Rr * 0.6, H * 0.85), (Rr * 0.2, H * 0.95), (Rr * 0.28, H)]
    bm = lathe(prof, 12)
    for v in bm.verts:
        k = 1 + 0.08 * hnoise(v.co * 6, seed)
        v.co.x *= k
        v.co.z *= k * 0.85
    return bm


def wagon(p):
    """In the cart's frame: its length along z (front, the shafts, at +z), its +x side still on its
    wheel, its -x side down on the broken axle; the broken wheel on the ground off the -x side."""
    L, Wd, side, Rw, roll = p['len'], p['wide'], p['side'], p['wheel_r'], p['roll']
    wood, iron, sk, sk2 = hexlin(p['wood']), hexlin(p['iron']), hexlin(p['sack']), hexlin(p['sack2'])
    rng = Rng(p['seed'])
    parts = []
    # The upright cart first (bed on the axle), then turned about the good wheel's foot.
    axle_y = Rw
    bed_y = axle_y + 0.1
    pivot = Vector((Wd / 2 + 0.12, 0, 0))
    lean = T(*pivot) @ R('Z', roll) @ T(*(-pivot))
    pitch = R('X', 0.0)
    up = lean @ pitch
    nb = 6
    bw = Wd / nb
    for k in range(nb):
        x = -Wd / 2 + bw * (k + 0.5)
        parts.append(Part(box(bw - 0.008, L, 0.04, 0.004), 'wood', wood, up @ T(x, bed_y, 0) @ R('X', math.pi / 2), cap='endgrain'))
    # Under-frame: two long beams and the shafts carrying on forward.
    for sx in (-1, 1):
        parts.append(Part(box(0.09, L + 0.2, 0.1, 0.008), 'wood', wood * 0.9, up @ T(sx * (Wd / 2 - 0.2), bed_y - 0.07, -0.1) @ R('X', math.pi / 2), cap='endgrain'))
    # Sides: two planks each, stakes; the -x side's upper plank broken off short.
    for sx in (-1, 1):
        for k in range(2):
            y = bed_y + 0.02 + side * (k + 0.5) / 2
            ln = L if not (sx < 0 and k == 1) else L * 0.55
            z = 0 if ln == L else (L - ln) / 2
            parts.append(Part(box(side / 2 - 0.012, ln, 0.035, 0.004), 'wood', wood, up @ T(sx * (Wd / 2 + 0.017), y, z) @ basis((0, 1, 0), (0, 0, 1), (1, 0, 0)), cap='endgrain'))
        for z in (-L / 2 + 0.06, 0.0, L / 2 - 0.06):
            parts.append(Part(box(0.06, side + 0.06, 0.06, 0.006), 'wood', wood * 0.92, up @ T(sx * (Wd / 2 + 0.05), bed_y + side / 2, z), cap='endgrain'))
    # Tailboard (back, -z).
    parts.append(Part(box(side - 0.02, Wd, 0.035, 0.004), 'wood', wood, up @ T(0, bed_y + side / 2, -L / 2 - 0.02) @ R('Z', math.pi / 2), cap='endgrain'))
    # Axle and the good wheel (+x), the broken axle stub (-x).
    parts.append(Part(box(0.08, Wd + 0.1, 0.08, 0.006), 'wood', wood * 0.85, up @ T(0.05, axle_y, 0.1) @ R('Z', math.pi / 2), cap='endgrain'))
    for reg, bm, m, cap in wheel(Rw, 0.05, 10):
        parts.append(Part(bm, reg, iron if reg == 'iron' else wood, up @ T(Wd / 2 + 0.12, axle_y, 0.1) @ R('Y', math.pi / 2) @ m, cap=cap))
    # Shafts: forward from the front beams, down to the ground (tips resting).
    for sx in (-1, 1):
        a = Vector((sx * (Wd / 2 - 0.2), bed_y - 0.07, L / 2 + 0.05))
        tip = up @ a
        end = Vector((tip.x + sx * 0.08, 0.05, tip.z + 1.6))
        d = end - tip
        parts.append(Part(box(0.07, d.length, 0.07, 0.006), 'wood', wood * 0.9,
                          T(*((tip + end) / 2)) @ Vector((0, 1, 0)).rotation_difference(d.normalized()).to_matrix().to_4x4(), cap='endgrain'))
    # The broken wheel, lying on the ground off the low side, a spoke snapped and a felloe gone.
    for reg, bm, m, cap in wheel(Rw, 0.05, 10, broken=(2, 3), split=(0.6, 1.5)):
        parts.append(Part(bm, reg, iron if reg == 'iron' else wood * 0.95, T(-Wd / 2 - 0.95, 0.1, 0.75) @ R('X', -math.pi / 2 + 0.06) @ R('Z', 0.4) @ m, cap=cap))
    # A loose felloe and a spoke on the ground.
    parts.append(Part(torus(Rw - 0.065, 0.058, 3, 4, 0, 0.9, rect=True, width=0.06), 'wood', wood * 0.9, T(-Wd / 2 - 0.3, 0.03, -0.4) @ R('Y', 2.2)))
    parts.append(Part(box(0.035, Rw * 0.6, 0.03), 'wood', wood * 0.9, T(-Wd / 2 - 0.5, 0.018, 1.6) @ R('Y', 0.7) @ R('X', math.pi / 2), cap='endgrain'))
    # Spilled sacks off the low side, one still in the bed against the low side.
    for (x, z, ry, rz, h, r, c) in ((-Wd / 2 - 0.45, -0.6, 0.4, 1.35, 0.62, 0.22, sk), (-Wd / 2 - 0.25, 0.15, -0.9, 1.45, 0.58, 0.21, sk2),
                                     (-Wd / 2 - 1.05, -1.25, 2.1, 1.5, 0.55, 0.2, sk)):
        sbm = sack(h, r, int(x * 10 + z * 7))
        parts.append(Part(sbm, 'canvas', c, T(x, r * 0.8, z) @ R('Y', ry) @ R('Z', rz) @ T(0, -h / 2, 0), smooth=True, jitter=0.0))
    sbm = sack(0.6, 0.21, 11)
    parts.append(Part(sbm, 'canvas', sk2, up @ T(-Wd / 2 + 0.35, bed_y + 0.2, -0.5) @ R('X', 1.4) @ R('Y', 0.3) @ T(0, -0.3, 0), smooth=True, jitter=0.0))
    return parts


KINDS = {'bedroll_open': bedroll_open, 'bedroll_rolled': bedroll_rolled, 'pack': pack, 'chest': chest,
         'crate': crate, 'barrel': barrel, 'log': log, 'wagon': wagon}


# ---------------------------------------------------------------- build --

def material():
    m = bpy.data.materials.new('props')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    va = nt.nodes.new('ShaderNodeVertexColor')
    va.layer_name = 'tint'
    nt.links.new(va.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.85
    return m


def lod1(ob, ratio=0.45):
    c = ob.copy()
    c.data = ob.data.copy()
    c.name = ob.name + '_LOD1'
    c.data.name = ob.data.name + '_LOD1'
    bpy.context.scene.collection.objects.link(c)
    m = c.modifiers.new('dec', 'DECIMATE')
    m.ratio = ratio
    m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = c
    bpy.ops.object.modifier_apply(modifier='dec')
    return c


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    data = json.load(open(DATA))['presets']
    names = argv or list(data)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(OUT, exist_ok=True)
    mat = material()
    meta_path = os.path.join(OUT, 'props.json')
    info = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for name in names:
        p = dict(data[name])
        for o in list(bpy.context.scene.collection.objects):
            bpy.data.objects.remove(o)
        parts = KINDS[p['kind']](p)
        ob = finish(name, parts, mat, p['seed'])
        obs = [ob]
        meta = {'tris': tris(ob)}
        if meta['tris'] > 1000:
            lo = lod1(ob)
            obs.append(lo)
            meta['tris_lod1'] = tris(lo)
        bb = [B2G @ Vector(c) for c in ob.bound_box]
        meta['box'] = [round(min(v[i] for v in bb), 3) for i in range(3)] + [round(max(v[i] for v in bb), 3) for i in range(3)]
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs:
            o.select_set(True)
        path = os.path.join(OUT, name + '.glb')
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                                  export_yup=True, export_materials='EXPORT', export_vertex_color='ACTIVE',
                                  export_image_format='NONE')
        info[name] = meta
        print(f'PROP {name}: {meta}')
    with open(meta_path, 'w') as f:
        json.dump(info, f, indent=1)


main()
