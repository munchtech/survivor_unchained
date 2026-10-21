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
  pylon           a ford pier of dressed stone (E7 round 2, for the Low Ford's lamp posts): a stepped
                  plinth, courses of blocks (whole and halved, in bond), a corbel and a capping slab
                  overhanging; the lower courses darker and greened (the river's)
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

    def __init__(self, bm, region, tint, at=Matrix.Identity(4), cap=None, smooth=False, jitter=0.06, capr=None, capto=0.23, cyl=None):
        self.bm, self.region, self.tint, self.at = bm, region, Vector(tint), at
        self.cap, self.smooth, self.jitter, self.capr, self.capto = cap, smooth, jitter, capr, capto
        self.cyl = cyl  # a tube about local y of this radius: unwrapped round it, not box-projected
        self.ftint = None  # (E7b) a face's own tint factor by its middle (local): a banner's device, moss on earth
        self.weld = False  # (E7b) welded to the parts it meets (patches of one surface, smooth across their seams)


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

def uv_cyl(p, rng, uvl):
    """Round 3: a log's bark unwrapped round its axis (local y), so the plates run down the trunk at their true
    size everywhere (box projection stretched them 1.4x at the diagonals and the region's fit to a 2.3 m log
    blew them up 1.9x: they read as cobbles). Four quarter islands round it (seams on the diagonals), each
    cut in lengths that fit the region, each island at a random spot in it."""
    u0, v0, u1, v1 = ATLAS[p.region]['uv']
    mu, mv = ATLAS[p.region]['m']
    r = p.cyl
    ys = [v.co.y for v in p.bm.verts]
    ymin, ymax = min(ys), max(ys)
    n = max(1, math.ceil((ymax - ymin) / (mv - 0.04)))
    cl = (ymax - ymin) / n
    q = math.pi / 2
    offs = {}
    for f in p.bm.faces:
        c = f.calc_center_median()
        a = math.atan2(c.z, c.x)
        sec = int(math.floor((a + q / 2) / q)) % 4
        ac = sec * q
        ch = min(n - 1, int((c.y - ymin) / cl))
        if (sec, ch) not in offs:
            offs[(sec, ch)] = (rng(0.03, max(0.031, mu - q * r - 0.03)), rng(0.0, max(0.0, mv - cl - 0.02)))
        oa, ob = offs[(sec, ch)]
        for l in f.loops:
            co = l.vert.co
            da = math.atan2(math.sin(math.atan2(co.z, co.x) - ac), math.cos(math.atan2(co.z, co.x) - ac))
            uu = (oa + (da + q / 2) * r) / mu
            vv = (ob + 0.01 + co.y - (ymin + ch * cl)) / mv
            l[uvl].uv = (u0 + (u1 - u0) * min(max(uu, 0.004), 0.996), v0 + (v1 - v0) * min(max(vv, 0.004), 0.996))


def uv_part(p, rng):
    """Box-project the part's faces into its region, in its own frame (grain along local y),
    each island placed at a random spot in the region (shrunk only if it is bigger)."""
    bm = p.bm
    uvl = bm.loops.layers.uv.verify()
    if p.cyl:
        uv_cyl(p, rng, uvl)
        return
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

GRIME = {'h': 0.0, 'moss': 0.0, 'top': 0.0, 'foot': 0.0, 'streak': 0.0}  # (E7b) the preset's grime height (m), moss on its stone's tops,
# its height (for the streaks under the top course), the foot band's darkening and the streaks' (env_props.json)


MOSS = Vector((0.5, 0.6, 0.34))  # (E7b r2) moss, linear: a pale sage that still reads green under the moon


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
        occ.append(1.0 - 0.75 * GRIME.get('ao', 1.0) * hit / rays)
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
        barky = kind_of_face[poly.index] == 'bark'
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            y = bm.verts[vi].co.y
            if barky and ground:
                # (round 2) moss and lichen where the bark meets the ground, in patches
                co = bm.verts[vi].co
                mf = min(1.0, max(0.0, (0.16 - y) / 0.12)) * min(1.0, max(0.0, 0.5 + 1.6 * hnoise(co * 3.0, 17)))
                tint = tint.lerp(Vector((tint.x * 0.72, tint.y * 0.95, tint.z * 0.42)), mf)
            lt = tint
            if GRIME['h'] > 0 and kind_of_face[poly.index] in ('stone', 'soil'):
                # (E7b) grime rising from the ground: the foot darker and greened in patches, moss on what faces up
                co = bm.verts[vi].co
                g = min(1.0, max(0.0, y / GRIME['h']))
                g = g * g * (3 - 2 * g)
                nz = 0.5 + 0.9 * hnoise(co * 1.7, 23)
                lt = lt * (0.58 + 0.42 * g)
                lt = lt.lerp(Vector((lt.x * 0.86, lt.y * 0.94, lt.z * 0.64)), (1 - g) * min(1.0, max(0.0, nz)))
                up = poly.normal.z
                if kind_of_face[poly.index] == 'stone' and GRIME['foot'] > 0:
                    # (E7b r2) the foot band (the bottom 0.6 m) darker and greener, its top edge ragged; blotches of
                    # weather over the whole face (no block left clean); streaks run down from under the top course
                    fb = 1.0 - smooth01(0.5, 0.85, y + 0.12 * hnoise(co * 2.9, 37))
                    lt = lt * (1.0 - GRIME['foot'] * fb)
                    lt = lt.lerp(Vector((lt.x * 0.8, lt.y * 0.97, lt.z * 0.6)), 0.7 * fb)
                    lt = lt * (0.86 + 0.2 * smooth01(-0.6, 0.6, hnoise(co * 1.3, 43)))
                    if abs(up) < 0.4 and GRIME['top'] > 0:
                        st = smooth01(0.05, 0.45, hnoise(Vector((co.x * 2.7 + co.z * 2.7, 0.0, 0.0)), 41))
                        hi = smooth01(GRIME['top'] * 0.4, GRIME['top'] * 0.78, y)
                        lt = lt.lerp(Vector((lt.x * 0.62, lt.y * 0.62, lt.z * 0.56)), GRIME['streak'] * st * hi)
                if GRIME['moss'] > 0 and up > 0.78 and kind_of_face[poly.index] == 'stone':
                    # (E7b r2) moss in patches (about half the top), ragged, a light sage that still reads green under
                    # the moon (the old dark olive went black at night); creeping over the arris a little
                    mz = 0.5 + 0.55 * hnoise(co * 4.2, 23) + 0.35 * hnoise(co * 11.0, 29)
                    m = GRIME['moss'] * smooth01(0.42, 0.58, mz) * min(1.0, (up - 0.78) * 6.0)
                    lt = lt.lerp(MOSS * (0.85 + 0.3 * hnoise(co * 5.0, 31)), m)
            s = occ[vi] * (0.72 + 0.28 * min(1.0, max(0.0, y / 0.08)) if ground else 1.0)
            if hard:
                s *= 1.0 + 0.35 * max(0.0, min(conv[vi], 0.6))
            s *= 1.0 + 0.4 * min(0.0, max(conv[vi], -0.5)) * 0.6
            c = lt * s
            ca.data[li].color = (min(c.x, 1.0), min(c.y, 1.0), min(c.z, 1.0), 1.0)
    me.color_attributes.active_color = ca
    bm.free()


def finish(name, parts, mat, seed):
    """Merge the parts (each face keeps its part's tint and kind), triangulate, bake, link."""
    rng = Rng(seed)
    bm = bmesh.new()
    lay_t = bm.faces.layers.int.new('part')
    info = []
    lay_s = bm.faces.layers.int.new('sub')
    for pi, p in enumerate(parts):
        p.bm.normal_update()
        uv_part(p, rng)
        ft = [p.ftint(f.calc_center_median()) for f in p.bm.faces] if p.ftint else None
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
        lay_s = bm.faces.layers.int.get('sub')
        for k, f in enumerate(bm.faces[n0:]):
            f[lay_t] = pi
            f[lay_s] = k
        info.append((p.tint * (1.0 + rng(-p.jitter, p.jitter)), p.region, p.smooth, ft))
    welded = {i for i, p in enumerate(parts) if p.weld}
    if welded:
        lay_t = bm.faces.layers.int.get('part')
        vs = list({v for f in bm.faces if f[lay_t] in welded for v in f.verts})
        bmesh.ops.remove_doubles(bm, verts=vs, dist=1e-4)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    lay_t = bm.faces.layers.int.get('part')
    lay_s = bm.faces.layers.int.get('sub')
    pidx = [f[lay_t] for f in bm.faces]
    sidx = [f[lay_s] for f in bm.faces]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = info[pidx[poly.index]][2]
    tints = [info[i][0] if info[i][3] is None else Vector([a * b for a, b in zip(info[i][0], info[i][3][k])]) for i, k in zip(pidx, sidx)]
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
            parts.append(Part(box(bh - 0.006, W, t, 0.004), 'wood', wood, T(0, y, sz * (D / 2 - t / 2)) @ R('Z', math.pi / 2), cap='endgrain', jitter=0.08))
        for sx in (-1, 1):
            parts.append(Part(box(bh - 0.006, D - 2 * t, t, 0.004), 'wood', wood, T(sx * (W / 2 - t / 2), y, 0) @ R('Y', math.pi / 2) @ R('Z', math.pi / 2), cap='endgrain', jitter=0.08))
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
                          T(0, cy, 0) @ R('X', -a) @ T(0, Rl, 0) @ R('Z', math.pi / 2), cap='endgrain', jitter=0.08))
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
    # (round 2) rivets: down the bands front and back, two where each band crosses a lid slat, two on each corner iron
    def rivet(at):
        parts.append(Part(lathe([(0.0085, 0.0), (0.0055, 0.0048), (0.0, 0.0062)], 5, cap0=False, cap1=False), 'iron', iron * 1.15, at, smooth=True, jitter=0.0))
    for bx in (-W * 0.3, W * 0.3):
        for sz in (-1, 1):
            for k in range(4):
                rivet(T(bx, 0.06 + (H - 0.12) * k / 3, sz * (D / 2 + 0.008)) @ R('X', sz * math.pi / 2))
        for k in range(ns):
            a = -half + 2 * half * (k + 0.5) / ns
            for dx in (-0.017, 0.017):
                rivet(T(bx + dx, cy, 0) @ R('X', -a) @ T(0, Rl + 0.021, 0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            for y in (0.06, H - 0.06):
                rivet(T(sx * (W / 2 + 0.012), y, sz * (D / 2 - 0.05)) @ R('Z', -sx * math.pi / 2))
                rivet(T(sx * (W / 2 - 0.05), y, sz * (D / 2 + 0.012)) @ R('X', sz * math.pi / 2))
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
    segs, rings = 20, max(10, int(L / 0.07))
    # a little thinner toward +y (the top of the tree), out of round, bowed, the bark lumpy in plates
    prof = [(r * (1.0 - 0.1 * k / rings), -L / 2 + L * k / rings) for k in range(rings + 1)]
    bm = lathe(prof, segs, cap0=False, cap1=False)
    flat = p.get('flat', 0.0)
    for v in bm.verts:
        a = math.atan2(v.co.z, v.co.x)
        k = (1 + 0.05 * hnoise(v.co * 4.5, seed) + 0.025 * math.sin(a * 5 + v.co.y * 3 + seed)) * (1 + 0.05 * math.cos(2 * a + seed))
        # (round 2) swellings and pinches along the length, so the top edge isn't a ruler
        k *= 1 + 0.08 * hnoise(Vector((0.3, v.co.y * 1.6, 0.7)), seed + 3) + 0.035 * math.sin(v.co.y * 7.3 + seed)
        # burls: two knobs on the upper side that break the top edge
        for (by, ba, bs) in ((-0.22 * L, 0.5, 0.13), (0.31 * L, -0.35, 0.1)):
            dy, da = (v.co.y - by) / bs, math.atan2(math.sin(a - ba), math.cos(a - ba)) / 0.9
            k += 0.16 * math.exp(-(dy * dy + da * da))
        v.co.x *= k
        v.co.z *= k
        v.co.x += 0.025 * (1 - (2 * v.co.y / L) ** 2)  # bowed up in the middle
        v.co.z += 0.035 * math.sin(math.pi * v.co.y / L + seed)  # and a little crooked sideways
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
    parts.append(Part(bm, 'bark', bark, turn, smooth=True, jitter=0.0, cyl=r))
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
    # Two branch stubs (sideways, so the log's height, which scales it to its radius, stays the bark's),
    # the second snapped short, its broken end showing wood.
    st = lathe([(0.065, -0.03), (0.055, 0.0), (0.04, 0.12), (0.03, 0.2)], 7, cap0=False, cap1=True)
    parts.append(Part(st, 'bark', bark * 0.9, turn @ T(r * 0.2, L * 0.18, r * 0.75) @ R('X', 1.2), smooth=True, jitter=0.0))
    st2 = lathe([(0.05, -0.03), (0.042, 0.0), (0.034, 0.07)], 7, cap0=False, cap1=False)
    parts.append(Part(st2, 'bark', bark * 0.85, turn @ T(-r * 0.15, -L * 0.3, -r * 0.82) @ R('X', -1.75), smooth=True, jitter=0.0))
    st3 = lathe([(0.045, -0.03), (0.036, 0.0), (0.026, 0.11), (0.018, 0.17)], 6, cap0=False, cap1=True)
    parts.append(Part(st3, 'bark', bark * 0.9, turn @ T(r * 0.55, L * 0.05, -r * 0.55) @ R('Y', 0.8) @ R('Z', -0.9), smooth=True, jitter=0.0))
    tip = bmesh.new()
    ring = [tip.verts.new((0.034 * math.cos(-a * 2 * math.pi / 7), 0.07 + 0.012 * math.sin(a * 2.3), 0.034 * math.sin(-a * 2 * math.pi / 7))) for a in range(7)]
    tf = tip.faces.new(ring)
    tip.normal_update()
    if tf.normal.y < 0:
        tf.normal_flip()
    parts.append(Part(tip, 'endgrain', cut * 0.8, turn @ T(-r * 0.15, -L * 0.3, -r * 0.82) @ R('X', -1.75), cap='endgrain', capr=0.034, jitter=0.0))
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
    """A grain sack (round 3): the body slumped, its shoulders sagging to one side, the neck pinched by a cord
    and the cloth over it a bunched, ruffled tuft (not a ring)."""
    prof = [(Rr * 0.7, 0.0), (Rr * 0.95, 0.04 * H), (Rr, 0.16 * H), (Rr * 0.99, 0.42 * H), (Rr * 0.93, 0.58 * H),
            (Rr * 0.74, 0.7 * H), (Rr * 0.42, 0.78 * H), (Rr * 0.17, 0.83 * H), (Rr * 0.15, 0.85 * H),
            (Rr * 0.3, 0.88 * H), (Rr * 0.44, 0.93 * H), (Rr * 0.4, 0.97 * H), (Rr * 0.18, H)]
    bm = lathe(prof, 16)
    ph = seed * 1.37
    for v in bm.verts:
        a = math.atan2(v.co.z, v.co.x)
        t = v.co.y / H
        k = 1 + 0.08 * hnoise(v.co * 6, seed)
        tuft = max(0.0, min(1.0, (t - 0.85) / 0.06))
        # the tuft's folds: deep, uneven ruffles, its lip ragged up and down
        k *= 1 + tuft * (0.3 * math.sin(7 * a + ph) + 0.18 * math.sin(11 * a + 2 * ph))
        v.co.x *= k
        v.co.z *= k * 0.85
        v.co.y += tuft * H * (0.025 * math.sin(5 * a + ph) + 0.015 * math.sin(9 * a))
        # the top sags: over the shoulder line it slumps down and leans to one side
        sag = max(0.0, (t - 0.5) / 0.5) ** 2
        v.co.y -= sag * H * (0.07 + 0.04 * math.cos(a - ph))
        v.co.x += sag * Rr * 0.22 * math.cos(ph)
        v.co.z += sag * Rr * 0.22 * math.sin(ph)
    bm.normal_update()
    return bm


def sack_parts(H, Rr, seed, tint, at):
    """A sack and the cord tied round its pinched neck, a loose end hanging (round 3: plain fine weave, the cloth
    region, tinted to burlap)."""
    ph = seed * 1.37
    # where the neck went after the sag (t 0.84: sag ((0.84 - 0.5) / 0.5)^2 = 0.46)
    sag = 0.4624
    ny = 0.84 * H - sag * H * 0.07
    nx, nz = sag * Rr * 0.22 * math.cos(ph), sag * Rr * 0.22 * math.sin(ph)
    tie = torus(Rr * 0.16 + 0.004, 0.008, 12, 5)
    end = lathe([(0.0065, 0.0), (0.006, -0.05), (0.008, -0.075)], 6, cap0=False, cap1=True)
    return [Part(sack(H, Rr, seed), 'cloth', tint, at, smooth=True, jitter=0.0),
            Part(tie, 'leather', Vector((0.55, 0.5, 0.42)), at @ T(nx, ny, nz), smooth=True, jitter=0.0),
            Part(end, 'leather', Vector((0.55, 0.5, 0.42)), at @ T(nx + Rr * 0.17 * math.cos(ph + 1.2), ny, nz + Rr * 0.17 * math.sin(ph + 1.2)) @ R('Z', 0.35), smooth=True, jitter=0.0)]


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
        parts += sack_parts(h, r, int(x * 10 + z * 7), c, T(x, r * 0.8, z) @ R('Y', ry) @ R('Z', rz) @ T(0, -h / 2, 0))
    parts += sack_parts(0.6, 0.21, 11, sk2, up @ T(-Wd / 2 + 0.35, bed_y + 0.2, -0.5) @ R('X', 1.4) @ R('Y', 0.3) @ T(0, -0.3, 0))
    return parts


def pylon(p):
    W, H = p['w'], p['h']
    stone = hexlin(p['stone'])
    rng = Rng(p['seed'])
    parts = []
    y = 0.0

    def block(sx, sy, sz, x, y0, z, k):
        # a dressed block, a little off square and off true, its tint its own (+-8%), the lower ones darker
        low = 1.0 - 0.3 * max(0.0, 1.0 - y0 / (H * 0.3))
        t = Vector((stone.x * low * 0.96, stone.y * low * (1.0 + 0.03 * (1 - low)), stone.z * low * 0.92)) if low < 1 else stone
        parts.append(Part(box(sx, sy, sz, 0.012), 'stone', t * (1 + rng(-0.08, 0.08)),
                          T(x + rng(-0.008, 0.008), y0 + sx / 2, z + rng(-0.008, 0.008)) @ R('Y', rng(-0.025, 0.025)) @ R('Z', math.pi / 2),
                          cap='stone', jitter=0.0))
    # plinth: two stepped courses
    for (hw, ch) in ((W * 0.5, 0.22), (W * 0.45, 0.2)):
        block(ch - 0.01, 2 * hw, 2 * hw, 0, y, 0, 0)
        y += ch
    # shaft: courses, alternately one block and two halves (split along x, then z)
    hw = W * 0.38
    cap_h = 0.32
    n = max(4, int(round((H - y - cap_h) / 0.34)))
    ch = (H - y - cap_h) / n
    for k in range(n):
        if k % 3 == 0:
            block(ch - 0.012, 2 * hw, 2 * hw, 0, y, 0, k)
        elif k % 3 == 1:
            for sx in (-1, 1):
                block(ch - 0.012, hw - 0.006, 2 * hw, sx * hw / 2, y, 0, k)
        else:
            for sz in (-1, 1):
                block(ch - 0.012, 2 * hw, hw - 0.006, 0, y, sz * hw / 2, k)
        y += ch
    # corbel and capping slab, overhanging
    block(0.13, 2 * W * 0.43, 2 * W * 0.43, 0, y, 0, 99)
    y += 0.13
    block(cap_h - 0.13, 2 * W * 0.48, 2 * W * 0.48, 0, y, 0, 100)
    return parts


# ------------------------------------------------- E7b: stone kit, graves --
# The Watch-post's ruin and the Barrow at Low Ford. Every preset is built in the KayKit piece's own units and
# frame (the box in godot/data/zones/kaykit.json), so it stands in the kk node exactly where the kit piece did,
# inside its collider (OwnProps "kits"). The stone pieces share one block maker (dressed, beveled, hand-cut
# arrises, chipped corners) laid in courses with mortar between, so E8's gate and walls reuse lay_course/wall.

def along(a, b, side=Vector((0, 0, 1))):
    """A piece's length and frame from a to b (local y along it, local z toward side)."""
    a, b = Vector(a), Vector(b)
    ya = (b - a).normalized()
    za = (side - ya * ya.dot(side)).normalized()
    return (b - a).length, T(*((a + b) / 2)) @ basis(ya.cross(za), ya, za)


def smooth01(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def stone_block(sx, sy, sz, rng, bevel=0.03, chip=0.45, jag=0.01, drop=(), top_cuts=0):
    """A dressed block about its middle (x long, y up, z deep): beveled, its arrises jittered (hand-cut),
    a corner or two knocked off; drop: main faces hidden in the bond ('+x', '-x', '+y', '-y', '+z', '-z');
    top_cuts: its open top cut in a grid (E7b r2: vertices enough for ragged moss on a wall's broken top)."""
    bv = min(bevel, sx * 0.2, sy * 0.2, sz * 0.2)
    bm = box(sx, sy, sz, bv)
    if top_cuts and '+y' not in drop:
        bm.faces.ensure_lookup_table()
        tf = [f for f in bm.faces if f.normal.y > 0.97]
        if tf:
            es = list({e for f in tf for e in f.edges})
            bmesh.ops.subdivide_edges(bm, edges=es, cuts=top_cuts, use_grid_fill=True)
    for v in bm.verts:
        v.co += Vector((rng(-jag, jag), rng(-jag, jag) * 0.7, rng(-jag, jag)))
    for _ in range(2):
        if rng() < chip:
            cn = Vector((sx / 2 * (1 if rng() < 0.5 else -1), sy / 2 * (1 if rng() < 0.65 else -1), sz / 2 * (1 if rng() < 0.5 else -1)))
            c = min(sx, sy, sz) * rng(0.18, 0.34)
            for v in bm.verts:
                d = (v.co - cn).length
                if d < c * 1.6:
                    v.co -= Vector((math.copysign(1, cn.x), math.copysign(1, cn.y), math.copysign(1, cn.z))) * (c * 1.6 - d) * 0.42
    if drop:
        ax = {'x': 0, 'y': 1, 'z': 2}
        half = (sx / 2, sy / 2, sz / 2)
        gone = []
        bm.normal_update()
        for f in bm.faces:
            for d in drop:
                i, s = ax[d[1]], (1 if d[0] == '+' else -1)
                if f.normal[i] * s > 0.97 and abs(f.calc_center_median()[i] - s * half[i]) < 0.05:
                    gone.append(f)
                    break
        bmesh.ops.delete(bm, geom=gone, context='FACES')
    return bm


def chunk(s, rng):
    """A broken stone: a box knocked irregular (rubble, spalls)."""
    bm = box(s * rng(0.8, 1.3), s * rng(0.5, 0.9), s * rng(0.7, 1.2), s * 0.08)
    for v in bm.verts:
        v.co += Vector((rng(-0.22, 0.22), rng(-0.18, 0.18), rng(-0.22, 0.22))) * s
    return bm


def broken_block(sx, sy, sz, rng, cuts=2, chip=0.7, bevel=0.025):
    """A fractured block (E7b r2): a dressed block with one or two pieces broken off it along rough planes (each
    fracture filled, poked, its middle pushed in or out and its rim roughened), the rest chipped at the corners."""
    bm = stone_block(sx, sy, sz, rng, bevel=bevel, chip=chip)
    for _ in range(cuts):
        n = Vector((rng(-1, 1), rng(-0.5, 1), rng(-1, 1)))
        if n.length < 0.2:
            n = Vector((1, 0.3, 0.2))
        n.normalize()
        ext = abs(n.x) * sx / 2 + abs(n.y) * sy / 2 + abs(n.z) * sz / 2
        co = n * ext * rng(0.05, 0.5)
        res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=n, clear_outer=True)
        ce = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        if not ce:
            continue
        fill = bmesh.ops.holes_fill(bm, edges=ce, sides=0)['faces']
        rim = {v for f in fill for v in f.verts}
        size = min(sx, sy, sz)
        for v in rim:
            v.co += n * rng(-0.05, 0.05) * size
        if fill:
            pk = bmesh.ops.poke(bm, faces=fill)
            for v in pk['verts']:
                v.co += n * rng(-0.14, 0.08) * size
    bm.normal_update()
    return bm


def gravel(s, rng):
    """A stone chip (E7b r2): an unbeveled box knocked irregular (12 tris), for gravel and spalls fanned out."""
    bm = box(s * rng(0.8, 1.3), s * rng(0.45, 0.8), s * rng(0.7, 1.2))
    for v in bm.verts:
        v.co += Vector((rng(-0.25, 0.25), rng(-0.2, 0.2), rng(-0.25, 0.25))) * s
    return bm


def bedded(bm, at, sink):
    """The matrix that stands a placed piece (bm in its frame, at its placing) with its lowest point sunk `sink`
    under y = 0 (E7b r2: blocks tipped and turned, their low edge bitten into the ground, not floating or buried)."""
    lo = min((at @ v.co).y for v in bm.verts)
    return T(0, -lo - sink, 0) @ at


def sblock(parts, size, at, tint, rng, **kw):
    parts.append(Part(stone_block(*size, rng, **kw), 'stone', tint * (1 + rng(-0.07, 0.07)), at, cap='stone', jitter=0.0))


def lay_course(xa, xb, bl, rng, half_first, forced=()):
    """One course's joints from xa to xb: blocks about bl long (0.75-1.2x), the first a half (running bond)
    when half_first, joints forced at the given x (an opening's edges); no sliver under 0.28 bl."""
    xs = [xa]
    x = xa
    first = True
    while x < xb - 1e-6:
        n = bl * (rng(0.45, 0.6) if (first and half_first) else rng(0.75, 1.2))
        first = False
        nx = min(xb, x + n)
        for f in forced:
            if x + 0.15 < f < nx - 0.05:
                nx = f
        if xb - nx < 0.28 * bl:
            nx = xb
        xs.append(nx)
        x = nx
    return xs


def wall_parts(parts, rng, L, H, D, ch, bl, stone, mortar, keep, x0, at=Matrix.Identity(4), holes=(), crack=None,
               gap=0.024, sink=0.3, base_course=None, cap_free=True):
    """A wall in courses (local x along it from x0, y up, z through it, centred on z = 0) laid into parts:
    keep(x) the broken top's height there (blocks whose middles stand under it, carried by the course below);
    holes: (xa, xb, ya, yb) openings; crack: (x at the foot, x at the top) a settled crack, the blocks past it
    dropped and turned; mortar runs behind each course's blocks. Returns the courses' blocks [(k, xa, xb, y0, y1)]."""
    rows = []
    y = 0.0
    k = 0
    while y < H - 0.08:
        cy = min(ch * rng(0.9, 1.1), H - y)
        if H - (y + cy) < 0.18:
            cy = H - y
        forced = [h[0] for h in holes if h[2] - 0.01 <= y < h[3]] + [h[1] for h in holes if h[2] - 0.01 <= y < h[3]]
        xs = lay_course(x0, x0 + L, bl, rng, k % 2 == 1, forced)
        row = []
        for i in range(len(xs) - 1):
            a, b = xs[i], xs[i + 1]
            m = (a + b) / 2
            ok = y + cy * 0.5 < keep(m)
            if ok and y + cy > keep(m) - cy * 0.7 and rng() < 0.22:
                ok = False  # a block lost from the broken edge
            for h in holes:
                if h[0] - 0.01 <= a and b <= h[1] + 0.01 and h[2] - 0.01 <= y < h[3]:
                    ok = False
            if ok and rows:
                below = [r for r in rows[-1] if r[1] - 0.05 <= m <= r[2] + 0.05]
                ok = bool(below)
            if ok:
                row.append((k, a, b, y, y + cy))
        rows.append(row)
        y += cy
        k += 1
    out = []
    for k, row in enumerate(rows):
        above = rows[k + 1] if k + 1 < len(rows) else []
        for i, (kk, a, b, y0, y1) in enumerate(row):
            drop = ['-y']
            if any(r[1] <= a + 0.06 for r in above) and any(r[2] >= b - 0.06 for r in above) and \
                    all(not (r[2] < b - 0.06 and r[2] > a + 0.06 and not any(q[1] <= r[2] + 0.06 and q[1] >= r[2] - 0.06 for q in above)) for r in above):
                covered = sum(max(0.0, min(b, r[2]) - max(a, r[1])) for r in above)
                if covered > (b - a) * 0.97:
                    drop.append('+y')
            if i > 0 and abs(row[i - 1][2] - a) < 1e-4:
                drop.append('-x')
            if i + 1 < len(row) and abs(row[i + 1][1] - b) < 1e-4:
                drop.append('+x')
            yb = y0 - (sink if k == 0 else 0.0)
            sx, sy = b - a - gap, y1 - yb - gap
            dx, dy, turn = 0.0, 0.0, 0.0
            if crack:
                cx = crack[0] + (crack[1] - crack[0]) * (y0 / max(H, 1e-3))
                if (a + b) / 2 > cx and k >= 2:
                    dy, turn = -0.012 * (k - 1), -0.008
                    if a < cx + 0.6 * bl:
                        sx -= 0.03
                        dx = 0.03
                    drop = [d for d in drop if d not in ('-x',)]
            zb = rng(-0.012, 0.012)
            tint = stone * (1 + rng(-0.09, 0.09))
            sblock(parts, (sx, sy, D - rng(0.0, 0.035)), at @ T((a + b) / 2 + dx, (yb + y1) / 2 + dy, zb) @ R('Z', turn) @ R('Y', rng(-0.012, 0.012)),
                   tint, rng, drop=tuple(drop), top_cuts=(2 if GRIME['moss'] > 0 and '+y' not in drop else 0))
            out.append((k, a, b, y0, y1))
        # mortar behind the course's runs of blocks
        runs = []
        for (kk, a, b, y0, y1) in row:
            if runs and abs(runs[-1][1] - a) < 1e-4:
                runs[-1][1] = b
            else:
                runs.append([a, b, y0, y1])
        for a, b, y0, y1 in runs:
            yb = y0 - (sink if k == 0 else 0.0)
            parts.append(Part(box(b - a - 0.05, y1 - yb - 0.01, D - 0.07), 'stone', mortar, at @ T((a + b) / 2, (yb + y1) / 2 - 0.004, 0), cap='stone', jitter=0.03))
    return out


def fallen_heap(parts, rng, keep, x0, L, side_z, D, ch, bl, stone, n=5, chips=10, at=Matrix.Identity(4), unit=1.0):
    """(E7b r2) Blocks fallen from a wall, where they fell from: clustered under its lowest stretch of broken top,
    4-6 of them, broken, 0.5-1.2 of a block, turned 10-40 degrees, tipped 10-35 (the last leaning on the first),
    their low edges bitten 3-5 cm into the ground; 8-12 chips fanned out from them up to 1.5 m.
    unit: kit units per metre (the piece is built in the kit's units)."""
    xs = [x0 + L * (i + 0.5) / 24 for i in range(24)]
    xl = min(xs, key=keep)
    xl = min(max(xl, x0 + 0.5), x0 + L - 0.5)
    placed = []
    for i in range(n):
        k = rng(0.5, 1.2)
        sx, sy, sd = bl * k, ch * rng(0.85, 1.05) * min(1.0, 0.6 + 0.4 * k), D * rng(0.45, 0.75) * min(1.0, 0.55 + 0.45 * k)
        bm = broken_block(sx, sy, sd, rng, cuts=1 if rng() < 0.5 else 2, chip=0.8)
        yaw = math.radians(rng(10, 40)) * (1 if rng() < 0.5 else -1)
        tip = math.radians(rng(10, 35)) * (1 if rng() < 0.5 else -1)
        if i == n - 1 and placed:
            # leaning on the first: beside it, toward it, steeper
            bx, bz, bw = placed[0]
            x, z = bx + (bw * 0.5 + sx * 0.3), bz + rng(-0.1, 0.1)
            loc = T(x, 0, z) @ R('Y', yaw * 0.5) @ R('Z', math.radians(rng(28, 38)))
            lift = sy * 0.35
        else:
            ang = rng(-1.0, 1.0)
            x = xl + ang * L * 0.16 + (i - n / 2) * bl * 0.25
            z = side_z * (D / 2 + rng(0.1, 0.7) * unit + sd * 0.3)
            loc = T(x, 0, z) @ R('Y', yaw) @ (R('X', tip) if rng() < 0.5 else R('Z', tip))
            lift = 0.0
            placed.append((x, z, sx))
        m = bedded(bm, at @ loc, rng(0.03, 0.05) * unit - lift)
        parts.append(Part(bm, 'stone', stone * rng(0.82, 0.95), m, cap='stone', jitter=0.0))
    cx = sum(q[0] for q in placed) / max(1, len(placed))
    cz = sum(q[1] for q in placed) / max(1, len(placed))
    for j in range(chips):
        s = rng(0.1, 0.2) * unit
        a = rng(-1.1, 1.1)
        r = math.sqrt(rng(0.05, 1.0)) * 1.5 * unit
        x, z = cx + math.sin(a) * r, cz + side_z * abs(math.cos(a)) * r
        bm = gravel(s, rng)
        m = bedded(bm, at @ T(x, 0, z) @ R('Y', rng(0, 6.28)) @ R('X', rng(-0.4, 0.4)), s * 0.25)
        parts.append(Part(bm, 'stone', stone * rng(0.72, 0.92), m, cap='stone', jitter=0.0))


def fallen(parts, rng, n, xs, side_z, D, ch, bl, stone, at=Matrix.Identity(4), far=1.0):
    """Blocks fallen from a wall: lying at its feet (mostly on one side), half sunk, turned; spalls round them."""
    for i in range(n):
        x = rng(*xs)
        sz = side_z if rng() < 0.75 else -side_z
        z = sz * (D / 2 + rng(0.15, far))
        sx, sy, sd = bl * rng(0.55, 1.0), ch * rng(0.85, 1.0), D * rng(0.5, 0.9)
        tilt = rng(-0.55, 0.55)
        sblock(parts, (sx, sy, sd), at @ T(x, sy * 0.22, z) @ R('Y', rng(-1.2, 1.2)) @ R('X', tilt) @ R('Z', rng(-0.25, 0.25)),
               stone * 0.9, rng, chip=0.8)
        for j in range(2):
            s = rng(0.1, 0.22)
            parts.append(Part(chunk(s, rng), 'stone', stone * rng(0.75, 0.95),
                              at @ T(x + rng(-0.6, 0.6), s * 0.2, z + rng(-0.4, 0.4)) @ R('Y', rng(0, 6.28)), cap='stone', jitter=0.0))


def profile_fn(pts, H, rng, jag=0.0):
    """keep(x) from [x, h-fraction] points (linear), a little ragged."""
    def keep(x):
        if x <= pts[0][0]:
            h = pts[0][1]
        elif x >= pts[-1][0]:
            h = pts[-1][1]
        else:
            for (xa, ha), (xb, hb) in zip(pts, pts[1:]):
                if xa <= x <= xb:
                    h = ha + (hb - ha) * (x - xa) / max(xb - xa, 1e-6)
                    break
        return H * h + jag * math.sin(x * 7.3 + 1.1)
    return keep


def wall(p):
    """A ruined wall section of dressed stone (dungeon wall_cracked / wall_broken / wall_half): courses in running
    bond, mortar, the top broken to p['top'] ([x, height fraction] along it), fallen blocks at its feet."""
    rng = Rng(p['seed'])
    L, H, D = p['len'], p['h'], p['d']
    x0 = p.get('x0', -L / 2)
    stone, mortar = hexlin(p['stone']), hexlin(p['mortar'])
    parts = []
    keep = profile_fn(p['top'], H, rng, 0.05)
    wall_parts(parts, rng, L, H, D, p.get('course', 0.44), p.get('block', 0.82), stone, mortar, keep, x0,
               crack=p.get('crack') and (x0 + p['crack'][0] * L, x0 + p['crack'][1] * L))
    fallen_heap(parts, rng, keep, x0, L, p.get('side', 1), D, p.get('course', 0.44), p.get('block', 0.82), stone,
                n=p.get('fallen', 5), chips=p.get('chips', 10), unit=p.get('unit', 1.0 / 0.85))
    return parts


def pillar(p):
    """A square pillar of dressed stone (dungeon pillar): a stepped plinth, the shaft in courses (whole and halved,
    in bond), a capital; broken: the shaft stops ragged, its top stone askew, one fallen at its foot."""
    rng = Rng(p['seed'])
    W, H = p['w'], p['h']
    stone = hexlin(p['stone'])
    parts = []
    gr = p.get('grime', 1.2)
    def tint(y):
        low = 0.72 + 0.28 * smooth01(0, gr, y)
        return Vector((stone.x * low, stone.y * low, stone.z * low * 0.97))
    y = -0.3
    for hw, chh in ((W * 0.5, 0.52), (W * 0.43, 0.24)):
        sblock(parts, (2 * hw, chh - 0.02, 2 * hw), T(0, y + chh / 2, 0) @ R('Y', rng(-0.03, 0.03)), tint(y), rng, drop=('-y',))
        y += chh
    hw = W * 0.34
    top = H - 0.42 if not p.get('broken') else H * p['broken']
    ch = 0.46
    k = 0
    while y < top - 0.1:
        cy = min(ch, top - y)
        last = y + cy >= top - 0.1
        if last and p.get('broken'):
            # the top stone halved and askew
            sblock(parts, (2 * hw * 0.62, cy - 0.02, 2 * hw), T(-hw * 0.38, y + cy / 2 + 0.02, 0.02) @ R('Z', 0.09) @ R('Y', 0.12), tint(y), rng, chip=1.0)
            break
        if k % 3 == 0:
            sblock(parts, (2 * hw, cy - 0.02, 2 * hw), T(0, y + cy / 2, 0) @ R('Y', rng(-0.02, 0.02)), tint(y), rng, drop=('-y', '+y'))
        elif k % 3 == 1:
            for sx in (-1, 1):
                sblock(parts, (hw - 0.02, cy - 0.02, 2 * hw), T(sx * hw / 2, y + cy / 2, 0), tint(y), rng, drop=('-y', '+y', '-x' if sx > 0 else '+x'))
        else:
            for sz in (-1, 1):
                sblock(parts, (2 * hw, cy - 0.02, hw - 0.02), T(0, y + cy / 2, sz * hw / 2), tint(y), rng, drop=('-y', '+y', '-z' if sz > 0 else '+z'))
        y += cy
        k += 1
    if not p.get('broken'):
        sblock(parts, (2 * W * 0.4, 0.16, 2 * W * 0.4), T(0, y + 0.08, 0), tint(y), rng, drop=('-y',))
        sblock(parts, (2 * W * 0.46, 0.24, 2 * W * 0.46), T(0, y + 0.28, 0) @ R('Y', 0.02), tint(y), rng, chip=0.7)
    else:
        sblock(parts, (2 * hw, 0.44, 2 * hw * 0.9), T(W * 0.75, 0.2, W * 0.45) @ R('Y', 0.6) @ R('X', 0.25), tint(0), rng, chip=1.0)
        for j in range(4):
            s = rng(0.14, 0.26)
            parts.append(Part(chunk(s, rng), 'stone', tint(0) * 0.9, T(rng(-1, 1) * W * 0.9, s * 0.2, rng(0.3, 1.0) * W) @ R('Y', rng(0, 6.28)), cap='stone', jitter=0.0))
    return parts


def mound_y(x, z, a, b, h, seed, sag=0.0, lump=0.04):
    """A heap of earth (elliptic, a by b), its rim under the ground, settled in the middle by sag."""
    r = math.sqrt((x / a) ** 2 + (z / b) ** 2)
    if r < 1:
        y = h * (1 - r * r) ** 0.55 - sag * h * math.exp(-r * r * 3)
    else:
        y = -0.12 * (r - 1) * max(a, b)
    return y + lump * hnoise(Vector((x * 2.3, 0.0, z * 2.3)), seed) * min(1.0, 1.4 - r)


def patches(fn, nu, nv, cu, cv, region, tint, ftint=None, flip=False):
    """A surface fn(u, v) -> (x, y, z) in nu x nv quads, cut in blocks of cu x cv quads, each a part of its own
    (its own island in the region, at true size) and welded to its neighbours (smooth across the seams)."""
    P = [[Vector(fn(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    parts = []
    for i0 in range(0, nu, cu):
        for j0 in range(0, nv, cv):
            bm = bmesh.new()
            V = {}
            for i in range(i0, min(nu, i0 + cu) + 1):
                for j in range(j0, min(nv, j0 + cv) + 1):
                    V[i, j] = bm.verts.new(P[i][j])
            for i in range(i0, min(nu, i0 + cu)):
                for j in range(j0, min(nv, j0 + cv)):
                    q = (V[i, j], V[i, j + 1], V[i + 1, j + 1], V[i + 1, j])
                    bm.faces.new(tuple(reversed(q)) if flip else q)
            pt = Part(bm, region, tint, smooth=True, jitter=0.0)
            pt.weld = True
            pt.ftint = ftint
            parts.append(pt)
    return parts


def mound(a, b, h, seed, tint, cx=0.0, cz=0.0, sag=0.0, moss=0.5, step=0.12, cell=3, head=0.45, tufts=10):
    """A grave's earth as patches of soil (E7b r2: its head end, toward -z, raised; the earth darker at its foot
    where it meets the grass; weeds greening its sides; tufts of grass standing out of them)."""
    ext = 1.18
    nu = max(4, int(2 * a * ext / step))
    nv = max(4, int(2 * b * ext / step))
    weed = Vector((0.5, 0.82, 0.32))
    def fn(u, v):
        x, z = (u - 0.5) * 2 * a * ext, (v - 0.5) * 2 * b * ext
        y = mound_y(x, z, a, b, h, seed, sag)
        if y > 0:
            y *= 1 + head * (0.5 - 0.5 * max(-1.0, min(1.0, z / b)))
        return (cx + x, y, cz + z)
    def ft(c):
        x, z = c.x - cx, c.z - cz
        r = math.sqrt((x / a) ** 2 + (z / b) ** 2)
        side = smooth01(0.35, 0.8, abs(x) / a)
        m = moss * max(side * 0.85, smooth01(0.1, 0.6, 0.5 + 0.9 * hnoise(Vector((c.x * 3.1, 0, c.z * 3.1)), seed + 5)) * 0.6)
        m *= 0.55 + 0.45 * smooth01(-0.3, 0.3, hnoise(Vector((c.x * 4.3, 0, c.z * 4.3)), seed + 8))
        foot = smooth01(0.72, 1.0, r)
        return Vector((1, 1, 1)).lerp(weed, m) * (1.0 - 0.32 * foot)
    out = patches(fn, nu, nv, cell, cell, 'soil', tint, ft)
    rng = Rng(seed + 77)
    for i in range(tufts):
        sx = 1 if i % 2 else -1
        x = sx * a * rng(0.55, 0.95)
        z = b * rng(-0.85, 0.85)
        y = max(0.0, mound_y(x, z, a, b, h, seed, sag))
        out.append(tuft(rng, Vector((cx + x, y - 0.01, cz + z)), rng(0.2, 0.34)))
    return out


def tuft(rng, at, hgt, n=5):
    """A tuft of grass (E7b r2): n thin blades fanned out of a point, each a narrow sliver two-sided (2 tris)."""
    bm = bmesh.new()
    for k in range(n):
        a = k * 2.399 + rng(-0.3, 0.3)
        d = Vector((math.cos(a), 0, math.sin(a)))
        side = Vector((-d.z, 0, d.x)) * rng(0.022, 0.034)
        tip = d * hgt * rng(0.35, 0.7) + Vector((0, hgt * rng(0.7, 1.1), 0))
        v0, v1, v2 = bm.verts.new(-side), bm.verts.new(side), bm.verts.new(tip)
        bm.faces.new((v0, v1, v2))
        v3, v4, v5 = bm.verts.new(-side), bm.verts.new(side), bm.verts.new(tip)
        bm.faces.new((v5, v4, v3))
    return Part(bm, 'soil', Vector((0.3, 0.42, 0.16)) * rng(0.85, 1.15), T(*at), smooth=False, jitter=0.0)


def outline(kind, w, h, rng):
    """A headstone's face outline (x, y), anticlockwise from the foot's left."""
    pts = [(-w / 2, 0.0), (w / 2, 0.0)]
    if kind == 'round':
        s = h - w / 2
        pts += [(w / 2, s)] + [(w / 2 * math.cos(math.pi * k / 10), s + w / 2 * math.sin(math.pi * k / 10)) for k in range(1, 10)] + [(-w / 2, s)]
    elif kind == 'shoulder':
        s = h * 0.74
        r = w * 0.36
        pts += [(w / 2, s), (w / 2 - w * 0.08, s), (w / 2 - w * 0.08, s + h * 0.04), (r, h - r)]
        pts += [(r * math.cos(math.pi * k / 8), h - r + r * math.sin(math.pi * k / 8)) for k in range(1, 8)]
        pts += [(-r, h - r), (-w / 2 + w * 0.08, s + h * 0.04), (-w / 2 + w * 0.08, s), (-w / 2, s)]
    elif kind == 'gothic':
        R_ = w
        s = h - R_ * math.sin(math.pi / 3)
        pts += [(w / 2, s)]
        pts += [(-w / 2 + R_ * math.cos(math.pi / 3 * k / 5), s + R_ * math.sin(math.pi / 3 * k / 5)) for k in range(1, 5)]
        pts += [(0.0, h)]
        pts += [(w / 2 - R_ * math.cos(math.pi / 3 * k / 5), s + R_ * math.sin(math.pi / 3 * k / 5)) for k in range(4, 0, -1)]
        pts += [(-w / 2, s)]
    else:  # broken: a jagged break across at about half
        s = h
        pts += [(w / 2, s * 0.62)]
        n = 6
        for k in range(1, n):
            pts.append((w / 2 - w * k / n, s * (0.5 + 0.18 * rng(-1, 1)) + (0.08 * s if k == 2 else 0)))
        pts += [(-w / 2, s * 0.7)]
    return pts


def prism(pts, t, bevel=0.012):
    """An outline (x, y) extruded t deep about z = 0, its arrises beveled."""
    bm = bmesh.new()
    f = [bm.verts.new((x, y, t / 2)) for x, y in pts]
    b = [bm.verts.new((x, y, -t / 2)) for x, y in pts]
    n = len(pts)
    bm.faces.new(f)
    bm.faces.new(list(reversed(b)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((f[j], f[i], b[i], b[j]))
    bm.normal_update()
    _outward(bm)
    if bevel > 0:
        es = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > 0.6]
        bmesh.ops.bevel(bm, geom=es, offset=bevel, segments=1, affect='EDGES', profile=0.5, clamp_overlap=True)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    return bm


def headstone(parts, kind, w, h, t, at, tint, rng, chip=0.0):
    bm = prism(outline(kind, w, h, rng), t, 0.014)
    for v in bm.verts:
        v.co += Vector((rng(-0.006, 0.006), rng(-0.004, 0.004), rng(-0.004, 0.004)))
        if chip and v.co.y > h * 0.6 and v.co.x > w * 0.25:
            v.co.x -= chip * smooth01(h * 0.6, h, v.co.y) * smooth01(w * 0.25, w * 0.5, v.co.x) * w * 0.4
    parts.append(Part(bm, 'stone', tint, at, cap='stone', jitter=0.0))


def grave(p):
    """A grave (halloween grave_A / grave_B / grave_A_destroyed): a headstone (round, gothic, shouldered) on a
    plinth stone, sunk and leaning, its earth heaped in front, settled and mossed; a kerb round some; open: the
    pit dug out (dark), the spoil heaped beside it, the stone broken and its top fallen, coffin boards splintered."""
    rng = Rng(p['seed'])
    stone, soil = hexlin(p['stone']), hexlin(p['soil'])
    parts = []
    W, Hs, t = p['w'], p['hs'], p['t']
    z0 = p.get('z0', -0.3)
    lean = p.get('lean', 0.05)
    ml = p.get('mlen', 2.4)
    # the plinth stone, half sunk
    sblock(parts, (W * 1.18, 0.26, t * 2.4), T(0, 0.04, z0) @ R('Y', rng(-0.04, 0.04)), stone * 0.88, rng, chip=0.6, drop=('-y',))
    if p.get('open'):
        headstone(parts, 'broken', W, Hs, t, T(0, 0.12, z0) @ R('X', -lean) @ R('Z', 0.06), stone, rng)
        # its top half fallen across the spoil
        headstone(parts, 'round', W * 0.98, Hs * 0.42, t, T(W * 0.75, 0.12, z0 + 0.7) @ R('Z', 1.25) @ R('Y', 0.5) @ T(0, -Hs * 0.2, 0), stone * 0.95, rng)
        # the pit: a rim of turned earth round a dark hollow; the spoil heaped to +x
        pa, pb = W * 0.42, ml * 0.42
        pc = z0 + 0.25 + pb
        def fn(u, v):
            x, z = (u - 0.5) * 2 * pa * 1.9, (v - 0.5) * 2 * pb * 1.5
            r = max(abs(x) / pa, abs(z) / pb)
            if r < 1:
                y = 0.05 - 0.02 * (1 - r)          # the hollow's floor (dark: reads as depth)
            else:
                y = 0.32 * math.exp(-((r - 1.12) / 0.16) ** 2) - 0.1 * max(0.0, r - 1.5)
            y += 0.035 * hnoise(Vector((x * 3.0, 0, z * 3.0)), p['seed'])
            return (x, y, pc + z)
        dark = Vector((0.2, 0.18, 0.16))
        def ft(c):
            r = max(abs(c.x) / pa, abs(c.z - pc) / pb)
            return Vector((1, 1, 1)).lerp(dark, smooth01(1.08, 0.92, r))
        parts += patches(fn, 18, 22, 3, 3, 'soil', soil, ft)
        parts += mound(pa * 0.9, pb * 1.1, 0.42, p['seed'] + 3, soil * 1.05, cx=pa * 2.0, cz=pc + 0.1, moss=0.15)
        wood = hexlin(p.get('wood', '#8a8076'))
        parts.append(Part(box(0.26, 1.5, 0.03, 0.004), 'wood', wood * 0.7, T(-pa * 0.35, 0.22, pc + 0.15) @ R('X', 0.0) @ basis((1, 0, 0), (0, 0.35, 0.94), (0, 0.94, -0.35)), cap='endgrain', jitter=0.1))
        parts.append(Part(box(0.24, 1.1, 0.03, 0.004), 'wood', wood * 0.8, T(pa * 1.7, 0.42, pc - 0.3) @ basis((0.94, 0, 0.34), (-0.3, 0.3, 0.9), (0.1, 0.95, -0.3)), cap='endgrain', jitter=0.1))
        parts.append(Part(box(0.2, 0.6, 0.03, 0.004), 'wood', wood * 0.75, T(pa * 0.6, 0.36, pc + pb * 1.2) @ R('Y', 0.7) @ R('X', 1.45), cap='endgrain', jitter=0.1))
        return parts
    headstone(parts, p['head'], W, Hs, t, T(0, 0.1, z0) @ R('X', -lean) @ R('Z', rng(-0.05, 0.05)), stone, rng, chip=p.get('chip', 0.0))
    mz = z0 + 0.22 + ml / 2
    parts += mound(W * 0.42, ml / 2, p.get('mh', 0.3), p['seed'], soil, cz=mz, sag=p.get('sag', 0.4), moss=p.get('moss', 0.85))
    if p.get('kerb'):
        # (E7b r2) a stone curb, not a rail: lengths 0.26 wide and low, joints between, one settled and tipped
        kw = p.get('kerb_w', 0.26)
        for sx in (-1, 1):
            n = 3
            for k in range(n):
                ln = ml / n - 0.03
                zz = mz - ml / 2 + (k + 0.5) * ml / n
                settle = (k == 1 and sx > 0)
                sblock(parts, (kw, 0.17, ln), T(sx * (W * 0.5 + kw * 0.2), 0.03 - (0.05 if settle else 0), zz) @ R('Z', sx * (0.12 if settle else rng(0.0, 0.04))) @ R('Y', rng(-0.03, 0.03)),
                       stone * rng(0.78, 0.9), rng, chip=0.6, drop=('-y',))
        sblock(parts, (W + kw * 1.4, 0.17, kw), T(0, 0.03, mz + ml / 2 + kw * 0.2) @ R('X', 0.06), stone * 0.84, rng, chip=0.6, drop=('-y',))
    return parts


def gravestone(p):
    """A lone headstone (halloween gravestone): sunk, leaning, chipped, a little heap at its foot."""
    rng = Rng(p['seed'])
    stone, soil = hexlin(p['stone']), hexlin(p['soil'])
    parts = []
    W, Hs, t = p['w'], p['hs'], p['t']
    headstone(parts, p['head'], W, Hs, t, T(0, -0.12, 0) @ R('X', p.get('lean', -0.1)) @ R('Z', p.get('roll', 0.06)), stone, rng, chip=p.get('chip', 0.0))
    parts += mound(W * 0.46, 0.5, 0.14, p['seed'], soil, cz=0.55, sag=0.2, moss=0.85)
    return parts


def marker(p):
    """A wooden cross over a grave (halloween gravemarker_A / _B): two weathered boards nailed, or two rough poles
    lashed with cord; leaning as the ground settles; a low heap before it."""
    rng = Rng(p['seed'])
    wood, soil = hexlin(p['wood']), hexlin(p['soil'])
    parts = []
    h, w = p['h'], p['w']
    lean = T(0, 0, 0) @ R('Z', p.get('roll', 0.08)) @ R('X', p.get('lean', -0.06))
    if not p.get('lashed'):
        bw, bt = p.get('beam', 0.13), p.get('thick', 0.06)
        parts.append(Part(box(bw, h + 0.3, bt, 0.01), 'wood', wood, lean @ T(0, (h - 0.3) / 2, 0), cap='endgrain', jitter=0.06))
        parts.append(Part(box(bw * 0.9, w, bt * 0.85, 0.01), 'wood', wood * 0.95, lean @ T(0, h * 0.7, bt * 0.92) @ R('Z', math.pi / 2 + 0.05), cap='endgrain', jitter=0.06))
        for dx in (-0.03, 0.03):
            parts.append(Part(box(0.016, 0.016, 0.012), 'iron', Vector((1, 1, 1)), lean @ T(dx, h * 0.7 + dx, bt * 1.38)))
    else:
        pr = p.get('pole', 0.05)
        parts.append(Part(lathe([(pr, -0.3), (pr * 0.92, h * 0.6), (pr * 0.84, h)], 7), 'wood', wood, lean, cyl=pr, smooth=True, cap='endgrain', jitter=0.06))
        parts.append(Part(lathe([(pr * 0.8, -w / 2), (pr * 0.72, w / 2)], 7), 'wood', wood * 0.95, lean @ T(0, h * 0.68, pr * 1.55) @ R('Z', math.pi / 2 - 0.1), cyl=pr * 0.76, smooth=True, cap='endgrain', jitter=0.06))
        rope = hexlin(p.get('rope', '#9a8a6a'))
        for k in range(3):
            parts.append(Part(torus(pr * 1.3, pr * 0.18, 9, 4), 'canvas', rope, lean @ T(0, h * 0.68 + (k - 1) * pr * 0.45, pr * 0.8) @ R('Z', 0.55 * (1 if k % 2 else -1)) @ R('X', math.pi / 2), smooth=True, jitter=0.0))
    parts += mound(0.34, p.get('mlen', 0.85), 0.16, p['seed'], soil, cz=p.get('mz', 0.75), sag=0.3, moss=0.8)
    return parts


def paling_bm(w, h, t, rng):
    pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h - w * 0.55), (0.0 + rng(-0.01, 0.01), h), (-w / 2, h - w * 0.55)]
    # (grain along local y: x across, y up, z through)
    bm = bmesh.new()
    f = [bm.verts.new((x, y, t / 2)) for x, y in pts]
    b = [bm.verts.new((x, y, -t / 2)) for x, y in pts]
    bm.faces.new(f)
    bm.faces.new(list(reversed(b)))
    for i in range(5):
        j = (i + 1) % 5
        bm.faces.new((f[j], f[i], b[i], b[j]))
    _outward(bm)
    return bm


def fence(p):
    """A length of weathered paling fence (halloween fence / fence_broken): posts at its ends and middle, two rails,
    pointed palings, some lost, some leaning or hung from one nail; broken: the top rail down at one end, half the
    palings gone (two in the grass), its end post leaning."""
    rng = Rng(p['seed'])
    wood = hexlin(p['wood'])
    parts = []
    L, H = p['len'], p['h']
    broken = p.get('broken', False)
    lost = set(p.get('lost', []))
    hang = set(p.get('hang', []))
    posts = [-L / 2 + 0.08, 0.0, L / 2 - 0.08]
    for i, x in enumerate(posts):
        tilt = (p.get('lean_post', 0.0) if i == 2 else rng(-0.03, 0.03))
        parts.append(Part(box(0.14, H + 0.35, 0.14, 0.012), 'wood', wood * 0.85,
                          T(x, -0.35, 0) @ R('Z', -tilt) @ T(0, (H + 0.35) / 2 - 0.0, 0) @ R('Y', rng(-0.1, 0.1)), cap='endgrain', jitter=0.08))
        parts.append(Part(box(0.17, 0.05, 0.17, 0.01), 'wood', wood * 0.78, T(x, 0, 0) @ R('Z', -tilt) @ T(0, H + 0.02, 0) @ R('Y', 0.3), cap='endgrain', jitter=0.05))
    rails = [(0.42, 0.0), (H - 0.42, 0.0)]
    for k, (y, _) in enumerate(rails):
        if broken and k == 1:
            # the top rail split off its middle post and down at the end
            a = Vector((-L / 2 + 0.1, y, 0.1))
            b = Vector((L * 0.08, 0.12, 0.38))
            d = b - a
            ln, at = along(a, b)
            parts.append(Part(box(0.12, ln, 0.045, 0.006), 'wood', wood, at, cap='endgrain', jitter=0.08))
            continue
        parts.append(Part(box(0.12, L - 0.04, 0.045, 0.006), 'wood', wood, T(0, y + rng(-0.02, 0.02), 0.1) @ R('Z', math.pi / 2 + rng(-0.01, 0.01)), cap='endgrain', jitter=0.08))
    n = p.get('n', 12)
    for i in range(n):
        x = -L / 2 + 0.25 + (L - 0.5) * (i + 0.5) / n + rng(-0.02, 0.02)
        if i in lost or any(abs(x - q) < 0.1 for q in posts):
            continue
        if broken and x > -L * 0.05 and rng() < 0.7:
            continue
        ph = H * rng(0.94, 1.04) - 0.1
        w = rng(*p.get('paling_w', (0.12, 0.15)))
        if i in hang:
            parts.append(Part(paling_bm(w, ph, 0.025, rng), 'wood', wood * 0.95, T(x, H - 0.42, 0.137) @ R('Z', 2.6 + rng(-0.2, 0.2)) @ T(0, -ph * 0.15, 0), cap='endgrain', jitter=0.1))
            continue
        parts.append(Part(paling_bm(w, ph, 0.025, rng), 'wood', wood * (1 + rng(-0.1, 0.06)),
                          T(x, -0.12, 0.137) @ R('Z', rng(-0.05, 0.05)) @ R('X', rng(-0.04, 0.04)), cap='endgrain', jitter=0.08))
    if broken:
        for x, a in ((L * 0.2, 0.4), (L * 0.36, -0.3)):
            parts.append(Part(paling_bm(0.13, H * 0.9, 0.025, rng), 'wood', wood * 0.9, T(x, 0.03, 0.45) @ R('Y', a) @ R('X', -math.pi / 2 + 0.06), cap='endgrain', jitter=0.1))
    return parts


def rubble(p):
    """A heap of fallen masonry (dungeon rubble_large / rubble_half), E7b r2: a mound of spoil, broken stone bedded
    in it (fractured half and quarter blocks with knocked corners, 0.15-0.5 m, each sunk 30-60% into the earth),
    gravel and spalls round its foot, the earth greened by weeds there and in the hollows between the stones."""
    rng = Rng(p['seed'])
    stone, dirt = hexlin(p['stone']), hexlin(p['dirt'])
    parts = []
    u = p.get('unit', 1.0 / 0.6)  # kit units per metre
    L, Wd, Hm = p['len'], p['wide'], p['h']
    cx = p.get('x0', -L / 2) + L / 2
    a, b = L * 0.42, Wd * 0.42
    def hy(x, z):
        return max(0.0, mound_y(x - cx, z, a, b, Hm, p['seed'], 0.0, 0.07))
    def fn(uu, vv):
        x, z = cx + (uu - 0.5) * 2 * a * 1.15, (vv - 0.5) * 2 * b * 1.15
        return (x, mound_y(x - cx, z, a, b, Hm, p['seed'], 0.0, 0.16), z)
    weed = Vector((0.62, 0.86, 0.42))
    def ft(c):
        r = math.sqrt(((c.x - cx) / a) ** 2 + (c.z / b) ** 2)
        k = 0.8 + 0.25 * hnoise(Vector((c.x * 2.0, 0, c.z * 2.0)), p['seed'] + 2)
        w = smooth01(0.55, 1.0, r) * smooth01(-0.1, 0.4, hnoise(Vector((c.x * 3.3, 0, c.z * 3.3)), p['seed'] + 9))
        w = max(w, 0.6 * smooth01(0.2, 0.5, hnoise(Vector((c.x * 5.1, 0, c.z * 5.1)), p['seed'] + 4)))
        return (Vector((1, 1, 1)) * k).lerp(weed * k, w)
    step = p.get('step', 0.42)
    parts += patches(fn, max(6, int(2 * a * 1.15 / step)), max(5, int(2 * b * 1.15 / step)), 3, 3, 'soil', dirt, ft)
    ch, bl, D = p.get('course', 0.42), p.get('block', 0.8), p.get('d', 0.6)
    for i in range(p.get('blocks', 12)):
        ang = rng(0, 6.283)
        rr = math.sqrt(rng(0.0, 1.0)) * 0.95
        x, z = cx + math.cos(ang) * a * rr, math.sin(ang) * b * rr
        size = (rng(0.15, 0.3) if i % 4 == 3 else rng(0.3, 0.5)) * u
        kind = rng()
        if kind < 0.45:      # a half block
            dims = (size, size * rng(0.45, 0.7), size * rng(0.55, 0.85))
        elif kind < 0.8:     # a quarter, squarer
            dims = (size * 0.8, size * rng(0.5, 0.8), size * 0.75)
        else:                # a long broken end
            dims = (size * 1.2, size * rng(0.4, 0.55), size * 0.6)
        bm = broken_block(*dims, rng, cuts=1 if rng() < 0.4 else 2, chip=0.9, bevel=0.02 * u)
        hgt = max((v.co.y for v in bm.verts)) - min((v.co.y for v in bm.verts))
        loc = T(x, 0, z) @ R('Y', rng(-3.1, 3.1)) @ R('X', rng(-0.5, 0.5)) @ R('Z', rng(-0.5, 0.5))
        m = bedded(bm, loc, hgt * rng(0.3, 0.5) - hy(x, z))
        parts.append(Part(bm, 'stone', stone * rng(0.62, 0.92), m, cap='stone', jitter=0.0))
    for i in range(p.get('chunks', 20)):
        ang = rng(0, 6.283)
        rr = rng(0.75, 1.3) if i % 3 else rng(0.2, 0.8)
        x, z = cx + math.cos(ang) * a * rr, math.sin(ang) * b * rr
        s = rng(0.05, 0.14) * u
        bm = gravel(s, rng)
        m = bedded(bm, T(x, 0, z) @ R('Y', rng(0, 6.28)) @ R('X', rng(-0.4, 0.4)), s * 0.3 - hy(x, z))
        parts.append(Part(bm, 'stone', stone * rng(0.66, 0.9), m, cap='stone', jitter=0.0))
    return parts


def banner(p):
    """The Watch's banner, long faded (dungeon banner_thin_red): an iron arm out of the wall, a pole with knobbed
    ends, the cloth hanging in folds, its foot torn ragged; dull madder gone brown-rose, a pale band and the
    Watch's tower in faded linen; darker and stained toward the foot, faded at the top."""
    rng = Rng(p['seed'])
    cloth, pale, iron, wood = hexlin(p['cloth']), hexlin(p['pale']), hexlin(p['iron']), hexlin(p['wood'])
    parts = []
    W, Lc, top, zw = p['w'], p['len'], p['top'], p['wall']
    zc = zw + 0.3
    # the arm, its bracket plate on the wall, the pole across
    parts.append(Part(box(0.05, 0.36, 0.05), 'iron', iron, T(0, top + 0.08, (zw + zc) / 2) @ R('X', math.pi / 2)))
    parts.append(Part(box(0.05, 0.36, 0.05), 'iron', iron, T(0, top - 0.06, zw + 0.12) @ R('X', math.pi / 2 - 0.85)))
    parts.append(Part(box(0.16, 0.36, 0.03), 'iron', iron * 0.9, T(0, top, zw + 0.015)))
    parts.append(Part(lathe([(0.03, -W / 2 - 0.08), (0.03, W / 2 + 0.08)], 6), 'wood', wood, T(0, top + 0.06, zc) @ R('Z', math.pi / 2), cyl=0.03, smooth=True, cap='endgrain'))
    for sx in (-1, 1):
        parts.append(Part(lathe([(0.0, 0.0), (0.045, 0.02), (0.05, 0.05), (0.03, 0.09), (0.0, 0.1)], 6), 'iron', iron, T(sx * (W / 2 + 0.07), top + 0.06, zc) @ R('Z', -sx * math.pi / 2), smooth=True))
    nu, nv = 10, 22
    cut = [0.0] * (nu + 1)
    for i in range(nu + 1):
        u = i / nu
        cut[i] = 0.07 * abs(math.sin(u * 9.1 + 1.3)) + 0.05 * rng() + (0.12 if 0.55 < u < 0.75 else 0.0) * (1 - abs(u - 0.65) / 0.1)
    def fn(u, v):
        x = (u - 0.5) * W
        iu = min(nu, int(round(u * nu)))
        vv = v * (1 - cut[iu])
        y = top - vv * Lc
        z = zc + 0.035 * math.sin(u * 6.28 * 2.2 + 0.4) * (0.3 + vv) + 0.05 * vv * vv + 0.02 * math.sin(vv * 5 + u * 3)
        x *= 1 - 0.04 * vv
        return (x, y, z)
    def ft(c):
        u = c.x / W + 0.5
        vv = (top - c.y) / Lc
        col = Vector((1, 1, 1))
        band = (0.09 < vv < 0.135) or (0.82 < vv < 0.865)
        tower = 0.4 < u < 0.6 and 0.135 < vv < 0.82  # a pale down its middle
        if band or tower:
            col = Vector((pale.x / cloth.x, pale.y / cloth.y, pale.z / cloth.z))
        fade = 1.0 + 0.18 * smooth01(0.4, 0.0, vv)
        stain = 1.0 - 0.35 * smooth01(0.55, 1.0, vv)
        return col * fade * stain
    parts += patches(fn, nu, nv, 2, 4, 'cloth', cloth, ft)
    parts += patches(lambda u, v: Vector(fn(u, v)) + Vector((0, 0, 0.012)), nu, nv, 2, 4, 'cloth', cloth * 0.8, ft, flip=True)
    return parts


def table(p):
    """A long trestle table (props Table_Large): planks on two cross-legged trestles, a stretcher between; one
    plank cracked short, the boards cupped and grey."""
    rng = Rng(p['seed'])
    wood = hexlin(p['wood'])
    parts = []
    L, H, D = p['len'], p['h'], p['d']
    n = 4
    for i in range(n):
        z = -D / 2 + D * (i + 0.5) / n
        ln = L * (0.72 if i == 2 else 1.0)
        x = -(L - ln) / 2
        parts.append(Part(box(0.05, ln, D / n - 0.012, 0.006), 'wood', wood * (1 + rng(-0.08, 0.05)), T(x, H - 0.025 + rng(-0.004, 0.004), z) @ R('Z', math.pi / 2), cap='endgrain', jitter=0.08))
    for sx in (-1, 1):
        x = sx * L * 0.34
        parts.append(Part(box(0.07, D * 0.9, 0.08, 0.008), 'wood', wood * 0.85, T(x, H - 0.09, 0) @ R('X', math.pi / 2), cap='endgrain'))
        for sz in (-1, 1):
            a = Vector((x, 0.0, sz * D * 0.42))
            b = Vector((x, H - 0.1, -sz * D * 0.1))
            ln, at = along(a, b)
            parts.append(Part(box(0.08, ln, 0.06, 0.008), 'wood', wood * 0.82, at, cap='endgrain', jitter=0.08))
    parts.append(Part(box(0.07, L * 0.68, 0.06, 0.006), 'wood', wood * 0.8, T(0, H * 0.36, 0) @ R('Z', math.pi / 2), cap='endgrain'))
    return parts


def chair(p):
    """A plain joined chair (props Chair_1), E7b r2: sturdy enough to read lying in the yard from the play camera
    (the first read as a wire ladder): square legs, one solid seat slab on aprons, a solid back board between its
    posts under a top rail, lighter weathered wood."""
    rng = Rng(p['seed'])
    wood = hexlin(p['wood'])
    parts = []
    W, H, D, sh = p['w'], p['h'], p['d'], p['seat']
    lw = p.get('leg', 0.075)
    for sx in (-1, 1):
        for sz in (-1, 1):
            lh = H if sz < 0 else sh - 0.03
            parts.append(Part(box(lw, lh, lw, 0.008), 'wood', wood * 0.88, T(sx * (W / 2 - lw / 2), lh / 2, sz * (D / 2 - lw / 2)) @ R('X', 0.03 * sz if sz < 0 else 0), cap='endgrain'))
    st = p.get('slab', 0.06)
    parts.append(Part(box(st, W + 0.02, D + 0.02, 0.01), 'wood', wood * (1 + rng(-0.04, 0.04)), T(0, sh - st / 2, 0) @ R('Z', math.pi / 2), cap='endgrain', jitter=0.04))
    for sz in (-1, 1):
        parts.append(Part(box(0.09, W - 0.04, 0.04, 0.006), 'wood', wood * 0.8, T(0, sh - st - 0.045, sz * (D / 2 - lw / 2)) @ R('Z', math.pi / 2), cap='endgrain'))
    for sx in (-1, 1):
        parts.append(Part(box(0.09, D - 0.08, 0.04, 0.006), 'wood', wood * 0.8, T(sx * (W / 2 - lw / 2), sh - st - 0.045, 0) @ R('X', math.pi / 2), cap='endgrain'))
    bt = sh + (H - sh) * 0.32
    parts.append(Part(box(H - bt - 0.06, W - 0.06, 0.04, 0.006), 'wood', wood * 0.95, T(0, (bt + H - 0.06) / 2, -D / 2 + lw / 2) @ R('Z', math.pi / 2), cap='endgrain', jitter=0.05))
    parts.append(Part(box(0.09, W + 0.02, 0.06, 0.008), 'wood', wood * 0.9, T(0, H - 0.04, -D / 2 + lw / 2 + 0.01) @ R('Z', math.pi / 2), cap='endgrain'))
    return parts


def crypt(p):
    """The Barrow's crypt in our stone (halloween crypt): a plinth course, walls in courses round a door opening
    (jambs and a lintel standing proud), a cornice, gables in courses under the roof, columns either side of the
    door on bases with capitals, two worn steps, a cross at the gable. The roof (stone slates), its coping and
    the iron door stay the zone's (Pieces.Crypt, drawn over this: OwnProps "over")."""
    rng = Rng(p['seed'])
    stone, mortar = hexlin(p['stone']), hexlin(p['mortar'])
    parts = []
    w, d, h = p['w'], p['d'], p['h']
    plinth, wallH, roofH = h * 0.08, h * 0.5, h * 0.3
    iw, idp = w * 0.86, d * 0.86
    Dw = 0.62
    ch, bl = 0.5, 0.95
    gr = p.get('grime', 2.2)
    def tint(y):
        low = 0.68 + 0.32 * smooth01(0, gr, y)
        return Vector((stone.x * low, stone.y * low * (1 + 0.02 * (1 - low)), stone.z * low * 0.95))
    # plinth: one deep course round, sunk
    for side in range(4):
        L_ = (w if side % 2 == 0 else d - 1.8)
        at = (T(0, 0, (d / 2 - 0.45) * (1 if side == 0 else -1)) if side % 2 == 0 else T((w / 2 - 0.45) * (1 if side == 1 else -1), 0, 0) @ R('Y', math.pi / 2))
        wall_parts(parts, rng, L_, plinth, 0.9, plinth, 1.1, tint(0), mortar, lambda x: 9.0, -L_ / 2, at=at, sink=0.3)
    # walls: front (+z, the door), back, sides; corners alternate course by course (quoins)
    door = (-0.98, 0.98, 0.0, 3.2)
    y0 = plinth
    for side in range(4):
        if side % 2 == 0:
            L_ = iw
            at = T(0, y0, (idp / 2 - Dw / 2) * (1 if side == 0 else -1))
        else:
            L_ = idp - 2 * Dw
            at = T((iw / 2 - Dw / 2) * (1 if side == 1 else -1), y0, 0) @ R('Y', math.pi / 2)
        holes = [door] if side == 0 else []
        st = tint(y0 + 1.0)
        wall_parts(parts, rng, L_, wallH, Dw, ch, bl, st, mortar, lambda x: 9.0, -L_ / 2, at=at, holes=holes, sink=0.0)
    fz = idp / 2
    # jambs and lintel, proud of the face
    for sx in (-1, 1):
        y = y0
        k = 0
        while y < y0 + 3.2 - 0.05:
            hh = min(0.62 if k % 2 == 0 else 0.48, y0 + 3.2 - y)
            wj = 0.42 if k % 2 == 0 else 0.3
            sblock(parts, (wj, hh - 0.02, 0.3), T(sx * (0.98 + wj / 2 - 0.04), y + hh / 2, fz + 0.06), tint(y), rng, chip=0.3, drop=('-y', '-z'))
            y += hh
            k += 1
    sblock(parts, (2.8, 0.52, 0.42), T(0, y0 + 3.2 + 0.26, fz + 0.1), tint(4), rng, chip=0.5, drop=('-z',))
    # cornice
    yc = y0 + wallH
    for side in range(4):
        L_ = (iw + 0.3) if side % 2 == 0 else (idp + 0.3 - 2 * 0.56)
        at = (T(0, yc, (idp / 2 + 0.15 - 0.28) * (1 if side == 0 else -1)) if side % 2 == 0 else T((iw / 2 + 0.15 - 0.28) * (1 if side == 1 else -1), yc, 0) @ R('Y', math.pi / 2))
        xs = lay_course(-L_ / 2, L_ / 2, 1.3, rng, False)
        for a, b in zip(xs, xs[1:]):
            sblock(parts, (b - a - 0.02, 0.38, 0.56), at @ T((a + b) / 2, 0.19, 0), tint(yc), rng, chip=0.3, drop=('-y',))
    # gables in courses, their outer corners under the roof's slope
    eave = yc + h * 0.05
    for sz in (1, -1):
        y = eave
        k = 0
        while y < eave + roofH - 0.3:
            cy = 0.48
            hw = (iw / 2) * (1 - (y + cy - eave) / roofH)
            if hw < 0.25:
                break
            xs = lay_course(-hw, hw, bl, rng, k % 2 == 1)
            for a, b in zip(xs, xs[1:]):
                sblock(parts, (b - a - 0.024, cy - 0.024, Dw), T((a + b) / 2, y + cy / 2, sz * (idp / 2 - Dw / 2)), tint(y), rng, drop=('-y',))
            y += cy
            k += 1
    # the columns (code's places), on bases, with capitals
    cr = w * 0.05
    for sx in (-1, 1):
        cx, cz = sx * (0.93 + cr * 2.8), fz + cr * 1.6
        sblock(parts, (cr * 2.9, 0.4, cr * 2.9), T(cx, y0 + 0.2, cz), tint(0.5), rng, chip=0.6, drop=('-y',))
        sh = wallH - 0.8
        parts.append(Part(lathe([(cr * 1.0, 0.0), (cr * 0.92, sh * 0.5), (cr * 0.86, sh)], 10, cap0=False, cap1=False), 'stone', tint(2.0), T(cx, y0 + 0.4, cz), cyl=cr, smooth=True, jitter=0.0))
        parts.append(Part(lathe([(cr * 1.12, 0.0), (cr * 1.12, 0.08), (cr * 0.92, 0.14)], 10, cap0=False, cap1=False), 'stone', tint(0.5), T(cx, y0 + 0.4, cz), smooth=True, jitter=0.0))
        sblock(parts, (cr * 2.6, 0.22, cr * 2.6), T(cx, y0 + 0.4 + sh + 0.11, cz), tint(3), rng, chip=0.4)
        sblock(parts, (cr * 3.2, 0.2, cr * 3.2), T(cx, y0 + 0.4 + sh + 0.32, cz) @ R('Y', 0.02), tint(3), rng, chip=0.5)
    # two worn steps up to the door
    for k in range(2):
        sw = 1.86 * 0.9 * 2 - k * 1.86 * 0.2
        dd = d * 0.12 - k * d * 0.05
        z = d / 2 - d * 0.04 + k * d * 0.02
        xs = lay_course(-sw / 2, sw / 2, 1.15, rng, k == 1)
        for a, b in zip(xs, xs[1:]):
            sblock(parts, (b - a - 0.02, plinth * 0.5 + (0.3 if k == 0 else 0) - 0.01, dd), T((a + b) / 2, k * plinth * 0.5 + (plinth * 0.25 - (0.15 if k == 0 else 0)), z - 0.1), tint(0), rng, bevel=0.06, chip=0.7, drop=('-y',))
    # (E7b r2) the roof, our own: stone slabs in courses down each slope (chipped, laid askew, each course over the
    # one below, a few slipped), darker toward the eave, moss along the eave and up the ridge; an underlay under
    # them; ridge stones and the gables' coping up each slope; a cross on each gable's apex
    roof_parts(parts, rng, iw, idp, eave, roofH, p)
    cs = h * 0.15
    ap = eave + roofH + 0.42
    cpts = [(-0.09 * cs, 0), (0.09 * cs, 0), (0.09 * cs, 0.82 * cs), (0.38 * cs, 0.82 * cs), (0.38 * cs, 1.0 * cs), (0.09 * cs, 1.0 * cs),
            (0.09 * cs, 1.4 * cs), (-0.09 * cs, 1.4 * cs), (-0.09 * cs, 1.0 * cs), (-0.38 * cs, 1.0 * cs), (-0.38 * cs, 0.82 * cs), (-0.09 * cs, 0.82 * cs)]
    for sz in (1, -1):
        zc = sz * (idp / 2 + 0.05)
        sblock(parts, (0.62, 0.3, 0.5), T(0, ap - 0.12, zc), tint(9) * 0.92, rng, chip=0.5)
        parts.append(Part(prism(cpts, 0.24, 0.025), 'stone', tint(9) * (1.0 if sz > 0 else 0.95), T(0, ap + 0.02, zc) @ R('Z', 0.04 * sz), cap='stone', jitter=0.0))
    # (E7b r2) a carved lintel on the long face the path sees (local -x: the south): a long stone proud of the
    # wall under the cornice, a sunk panel in it, a skull and crossed bones in relief between two rosettes
    carved_lintel(parts, rng, -iw / 2, y0 + 2.0, tint(4))
    return parts


def roof_parts(parts, rng, iw, idp, eave, roofH, p):
    slab = hexlin(p.get('slab', '#aaa59c'))
    moss = MOSS
    ang = math.atan2(roofH, iw / 2)
    over_e, over_g = 0.3, 0.36
    run = math.sqrt((iw / 2) ** 2 + roofH ** 2) + over_e
    ln = idp + 2 * over_g
    ridge = Vector((0.0, eave + roofH + 0.12, 0.0))
    th = 0.13
    for sx in (-1, 1):
        down = Vector((sx * math.cos(ang), -math.sin(ang), 0.0))
        up = Vector((sx * math.sin(ang), math.cos(ang), 0.0))
        along = Vector((0.0, 0.0, 1.0))
        frame = basis(along, up, down)  # local x along the ridge, y off the slope, z down it
        # the underlay: a dark deck under the slabs (what a slipped slab shows)
        parts.append(Part(box(ln - 0.1, 0.08, run - 0.15), 'stone', slab * 0.45, T(*(ridge + down * (run / 2 + 0.02) - up * 0.06)) @ frame, cap='stone', jitter=0.0))
        course = 0.56
        nk = int(run / course + 0.999)
        for k in range(nk):
            s0 = k * course
            lift = 0.035  # each course rides on the one below at its tail
            xs = lay_course(-ln / 2, ln / 2, 0.82, rng, k % 2 == 1)
            t = (s0 + course / 2) / run
            for a, b in zip(xs, xs[1:]):
                xm = (a + b) / 2
                if rng() < 0.015 and 0 < k < nk - 1:
                    continue  # slipped: the underlay shows
                sw, sl = b - a - 0.035, course + 0.16
                mz = 0.5 + 0.55 * hnoise(Vector((xm * 1.7, 0, s0 * 1.7 + sx * 3.1)), 61)
                m = max(smooth01(0.62, 1.0, t), 0.8 * smooth01(0.16, 0.0, t)) * smooth01(0.3, 0.6, mz)
                m = max(m, 0.35 * smooth01(0.62, 0.8, mz))
                dark = 1.0 - 0.3 * smooth01(0.7, 1.0, t)
                tn = slab * rng(0.74, 1.12) * dark
                if rng() < 0.14:
                    tn = tn.lerp(Vector((0.86, 0.85, 0.74)), rng(0.3, 0.6))  # pale lichen
                tn = tn.lerp(moss * rng(0.85, 1.1), min(1.0, m * 0.9))
                if k == nk - 1:
                    tn = tn.lerp(Vector((0.26, 0.33, 0.15)), 0.55 + 0.3 * smooth01(0.4, 0.7, mz))  # the eave: dark, mossed
                pos = ridge + down * (s0 + sl / 2 - 0.08) + up * (th / 2 + lift * (1 - (k % 2) * 0.3)) + along * xm
                tilt = R('X', -0.06 + rng(-0.025, 0.025))  # the tail down, the butt up over the course below
                parts.append(Part(stone_block(sw, th * rng(0.85, 1.1), sl, rng, bevel=0.02, chip=0.7, jag=0.02), 'stone', tn,
                                  T(*pos) @ frame @ tilt @ R('Y', rng(-0.04, 0.04)), cap='stone', jitter=0.0))
        # the gables' coping up each slope, standing proud of the slabs
        for sz in (-1, 1):
            n = int(run / 0.7)
            for k in range(n):
                sp = (k + 0.5) * (run - 0.1) / n
                pos = ridge + down * sp + up * (th + 0.12) + along * sz * (idp / 2 + 0.06)
                mz = 0.5 + 0.55 * hnoise(Vector((sz * 2.0, 0, sp * 1.9 + sx)), 67)
                tn = slab * 1.05 * rng(0.9, 1.05)
                tn = tn.lerp(moss, 0.7 * smooth01(0.45, 0.65, mz))
                parts.append(Part(stone_block(0.5, 0.24, (run - 0.1) / n - 0.03, rng, bevel=0.03, chip=0.6), 'stone', tn,
                                  T(*pos) @ frame, cap='stone', jitter=0.0))
    # the ridge: capping stones, a little apart, mossed in patches
    n = int(ln / 0.62)
    for k in range(n):
        z = -ln / 2 + (k + 0.5) * ln / n
        mz = 0.5 + 0.55 * hnoise(Vector((0, 0, z * 1.3)), 71)
        tn = slab * rng(0.9, 1.05)
        tn = tn.lerp(moss, 0.8 * smooth01(0.35, 0.6, mz))
        parts.append(Part(stone_block(0.34, 0.34, ln / n - 0.04, rng, bevel=0.04, chip=0.6), 'stone', tn,
                          T(0, ridge.y + 0.1, z) @ R('Z', math.pi / 4 + rng(-0.05, 0.05)), cap='stone', jitter=0.0))


def carved_lintel(parts, rng, xface, yc, stone):
    """A carved lintel stone on a wall face at x = xface (facing -x): a long block proud of the wall, a panel sunk in
    it, a skull over crossed bones in relief between two rosettes, its lower arris chipped."""
    L, H, D = 3.4, 0.78, 0.3
    at = T(xface - D / 2 + 0.06, yc, 0) @ R('Y', -math.pi / 2)  # local x along the wall, z out of it (toward -x)
    sblock(parts, (L, H, D), at, stone * 1.02, rng, chip=0.7, drop=('-z',))
    # the panel sunk in the face: a darker recess (a thinner slab set back), the frame round it standing proud
    parts.append(Part(box(L - 0.36, H - 0.26, 0.04), 'stone', stone * 0.62, at @ T(0, 0, D / 2 - 0.035), cap='stone', jitter=0.0))
    for y in (H / 2 - 0.07, -H / 2 + 0.07):
        parts.append(Part(stone_block(L - 0.1, 0.12, 0.1, rng, bevel=0.02, chip=0.3), 'stone', stone * 1.04, at @ T(0, y, D / 2 + 0.01), cap='stone', jitter=0.0))
    for x in (L / 2 - 0.1, -L / 2 + 0.1):
        parts.append(Part(stone_block(0.12, H - 0.26, 0.1, rng, bevel=0.02, chip=0.3), 'stone', stone * 1.04, at @ T(x, 0, D / 2 + 0.01), cap='stone', jitter=0.0))
    # the skull: a dome over a jaw block, two sunk eyes; crossed bones behind it
    sk = stone * 1.1
    parts.append(Part(lathe([(0.0, 0.0), (0.15, 0.02), (0.17, 0.1), (0.13, 0.19), (0.0, 0.22)], 9), 'stone', sk, at @ T(0, -0.02, D / 2 + 0.02) @ R('X', math.pi / 2), smooth=True, jitter=0.0))
    parts.append(Part(box(0.16, 0.09, 0.07, 0.015), 'stone', sk * 0.95, at @ T(0, -0.16, D / 2 + 0.03), cap='stone', jitter=0.0))
    for ex in (-0.06, 0.06):
        parts.append(Part(box(0.055, 0.05, 0.03), 'stone', stone * 0.35, at @ T(ex, -0.0, D / 2 + 0.18), cap='stone', jitter=0.0))
    for a in (0.62, -0.62):
        parts.append(Part(lathe([(0.03, -0.27), (0.024, 0.0), (0.03, 0.27)], 6), 'stone', sk * 0.92, at @ T(0, -0.04, D / 2 + 0.035) @ R('Z', a), smooth=True, jitter=0.0))
    for x in (-L * 0.32, L * 0.32):
        parts.append(Part(lathe([(0.0, 0.0), (0.13, 0.0), (0.13, 0.03), (0.07, 0.06), (0.0, 0.07)], 8), 'stone', sk, at @ T(x, 0, D / 2 + 0.01) @ R('X', math.pi / 2), smooth=True, jitter=0.0))


KINDS = {'pylon': pylon, 'bedroll_open': bedroll_open, 'bedroll_rolled': bedroll_rolled, 'pack': pack, 'chest': chest,
         'crate': crate, 'barrel': barrel, 'log': log, 'wagon': wagon,
         'wall': wall, 'pillar': pillar, 'rubble': rubble, 'banner': banner, 'table': table, 'chair': chair,
         'fence': fence, 'grave': grave, 'gravestone': gravestone, 'marker': marker, 'crypt': crypt}


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
        GRIME['h'], GRIME['moss'] = p.get('grime', 0.0), p.get('moss_top', 0.0)
        GRIME['top'], GRIME['foot'], GRIME['streak'] = p.get('h', 0.0), p.get('foot', 0.0), p.get('streak', 0.0)
        GRIME['ao'] = p.get('ao', 1.0)
        parts = KINDS[p['kind']](p)
        ob = finish(name, parts, mat, p['seed'])
        obs = [ob]
        meta = {'tris': tris(ob)}
        if p['kind'] == 'log':
            meta['axis'] = [round(p['r'] * 0.85, 4), p['r']]  # the axis's height and the bark's radius (OwnProps lays logs by it)
        if meta['tris'] > 1000:
            lo = lod1(ob, p.get('lod1', 0.45))
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
