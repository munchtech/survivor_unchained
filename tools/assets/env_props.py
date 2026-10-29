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
        self.vmod = None  # (E9d) a corner's own tint from its face's: vmod(tint, game-frame position), for smooth fading and soil


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
    if p.region == 'tile':
        # (E9d) cloth on its own tiling sheet (canvas_tile.png, 0.5 m a tile): box-projected in metres, no atlas
        for f in bm.faces:
            ax = max(range(3), key=lambda i: abs(f.normal[i]))
            for l in f.loops:
                c = l.vert.co
                a, b = (c.x, c.z) if ax == 1 else (c.z, c.y) if ax == 0 else (c.x, c.y)
                l[uvl].uv = (a / 0.5, b / 0.5)
        return
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
        # (E8) the far castle's lit windows ('glow') sit on the soil region: their vertex colour is their glow
        u0, v0, u1, v1 = ATLAS.get(region, ATLAS['soil'])['uv']
        mu, mv = ATLAS.get(region, ATLAS['soil'])['m']

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


OLD = {}  # (lf6d) the preset's "old" (env_props.json): top_chip, the chance a wall's open-topped block is knocked at a corner; jag

MOSS = Vector((0.5, 0.6, 0.34))  # (E7b r2) moss, linear: a pale sage that still reads green under the moon


def bake_colours(me, tints, kind_of_face, ground=True, rays=14, vmods=None):
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
    # Height is y here (bm is in the game frame after B2G). (E8 r2) "zup" read it off z (a depth) by mistake: the drums'
    # grime and ground shade lay front to back (E8 later: measured, luma 0.10 at the back to 0.40 at the front). Fixed:
    # height is y for all; the far castle alone keeps the old axis (its "old": {"grime_depth": true}, its judged look).
    UP = 2 if OLD.get('grime_depth') else 1
    top_y = GRIME.get('run_top') or max((v.co[UP] for v in bm.verts), default=0.0)
    for v in bm.verts:
        n = v.normal
        t = n.orthogonal().normalized()
        b = n.cross(t)
        hit = 0.0
        for d in dirs:
            w = (t * d.x + n * d.y + b * d.z).normalized()
            o = v.co + n * 0.004
            if ground and w[UP] < 0 and o[UP] > -0.01:
                hit += 1.0 if (o[UP] / max(-w[UP], 1e-4)) < 0.45 else 0.0
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
        if kind_of_face[poly.index] == 'glow':
            # (E8) a lit window of the far castle: its glow colour as it is, flagged by alpha 0 (OwnProps' far material)
            for li in poly.loop_indices:
                ca.data[li].color = (tint.x, tint.y, tint.z, 0.0)
            continue
        hard = kind_of_face[poly.index] in ('wood', 'iron', 'endgrain', 'stone', 'bark')
        barky = kind_of_face[poly.index] == 'bark'
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            y = bm.verts[vi].co[UP]
            if barky and ground:
                # (round 2) moss and lichen where the bark meets the ground, in patches
                co = bm.verts[vi].co
                mf = min(1.0, max(0.0, (0.16 - y) / 0.12)) * min(1.0, max(0.0, 0.5 + 1.6 * hnoise(co * 3.0, 17)))
                tint = tint.lerp(Vector((tint.x * 0.72, tint.y * 0.95, tint.z * 0.42)), mf)
            lt = tint
            if vmods and vmods[poly.index]:
                lt = vmods[poly.index](tint, bm.verts[vi].co)
            run_flag = upf = False
            if GRIME['h'] > 0 and kind_of_face[poly.index] in ('stone', 'soil') and not (OLD.get('soil_clean') and kind_of_face[poly.index] == 'soil'):
                # (E7b) grime rising from the ground: the foot darker and greened in patches, moss on what faces up
                co = bm.verts[vi].co
                up = poly.normal.z
                # (E8 later r2) what faces up near the foot (the footing's weathering course, the ring the play camera
                # looks down on) keeps a quarter of the grime and none of the foot band, ground shade or base darkening: at full it went black
                upf = GRIME.get('runs') and up > 0.45
                g = min(1.0, max(0.0, y / GRIME['h']))
                g = g * g * (3 - 2 * g)
                if upf:
                    g = 0.75 + 0.25 * g
                nz = 0.5 + 0.9 * hnoise(co * 1.7, 23)
                lt = lt * (0.58 + 0.42 * g)
                lt = lt.lerp(Vector((lt.x * 0.86, lt.y * 0.94, lt.z * 0.64)), (1 - g) * min(1.0, max(0.0, nz)))
                if kind_of_face[poly.index] == 'stone' and GRIME['foot'] > 0:
                    # (E7b r2) the foot band (the bottom 0.6 m) darker and greener, its top edge ragged; blotches of
                    # weather over the whole face (no block left clean); streaks run down from under the top course
                    fb = 0.0 if upf else 1.0 - smooth01(0.5, 0.85, y + 0.12 * hnoise(co * 2.9, 37))
                    lt = lt * (1.0 - GRIME['foot'] * fb)
                    lt = lt.lerp(Vector((lt.x * 0.8, lt.y * 0.97, lt.z * 0.6)), 0.7 * fb)
                    lt = lt * (0.86 + 0.2 * smooth01(-0.6, 0.6, hnoise(co * 1.3, 43)))
                    if abs(up) < 0.4 and GRIME.get('runs'):
                        # (E8 later r2) grime runs: the faces that take them are flagged (vertex alpha 0.5) and the runs
                        # drawn per pixel by OwnProps' runs material (shaders/props_runs.gdshader): at the vertices (blocks
                        # 0.4-0.7 m a triangle) a 0.2-0.7 m run smeared to nothing. Outer faces only (a drum's outward,
                        # a wall's south and ends), never the parapet's inner face the play camera looks down on.
                        ng = Vector((poly.normal.x, poly.normal.z, -poly.normal.y))
                        if GRIME.get('ring'):
                            pc = B2G @ poly.center  # (the face's own centre: one flag a face, no blend across it)
                            run_flag = ng.x * pc.x + ng.z * pc.z > 0.3 * math.hypot(pc.x, pc.z)
                        else:
                            run_flag = ng.z > -0.3
                    if GRIME.get('base') and not upf:
                        # (E8 later) the masonry darker toward its base (splash, damp, soil), over the lower half
                        lt = lt * (1.0 - GRIME['base'] * (1.0 - smooth01(0.0, top_y * 0.55, y)))
                    if abs(up) < 0.4 and GRIME['top'] > 0 and not GRIME.get('runs'):
                        st = smooth01(0.05, 0.45, hnoise(Vector((co.x * 2.7 + co.z * 2.7, 0.0, 0.0)), 41))
                        hi = smooth01(GRIME['top'] * 0.4, GRIME['top'] * 0.78, y)
                        lt = lt.lerp(Vector((lt.x * 0.62, lt.y * 0.62, lt.z * 0.56)), GRIME['streak'] * st * hi)
                if GRIME['moss'] > 0 and up > 0.78 and kind_of_face[poly.index] == 'stone':
                    # (E7b r2) moss in patches (about half the top), ragged, a light sage that still reads green under
                    # the moon (the old dark olive went black at night); creeping over the arris a little
                    mz = 0.5 + 0.55 * hnoise(co * 4.2, 23) + 0.35 * hnoise(co * 11.0, 29)
                    m = GRIME['moss'] * smooth01(0.42, 0.58, mz) * min(1.0, (up - 0.78) * 6.0)
                    lt = lt.lerp(MOSS * (0.85 + 0.3 * hnoise(co * 5.0, 31)), m)
            # (e22r1a: earth that runs out into the ground ('soil_clean') takes no contact shade at its foot: a dark ring)
            soil_out = OLD.get('soil_clean') and kind_of_face[poly.index] == 'soil'
            s = occ[vi] * (0.72 + 0.28 * min(1.0, max(0.0, y / 0.08)) if ground and not upf and not soil_out else 1.0)
            if hard:
                s *= 1.0 + 0.35 * max(0.0, min(conv[vi], 0.6))
            s *= 1.0 + 0.4 * min(0.0, max(conv[vi], -0.5)) * 0.6
            c = lt * s
            ca.data[li].color = (min(c.x, 1.0), min(c.y, 1.0), min(c.z, 1.0), 0.5 if run_flag else 1.0)
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
        info.append((p.tint * (1.0 + rng(-p.jitter, p.jitter)), p.region, p.smooth, ft, p.vmod))
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
        # (E8d) smooth == 'faces': each face keeps its own flag (a drum block's face smooth, its arrises flat)
        if info[pidx[poly.index]][2] != 'faces':
            poly.use_smooth = info[pidx[poly.index]][2]
    tints = [info[i][0] if info[i][3] is None else Vector([a * b for a, b in zip(info[i][0], info[i][3][k])]) for i, k in zip(pidx, sidx)]
    kinds = [info[i][1] for i in pidx]
    bake_colours(me, tints, kinds, vmods=[info[i][4] for i in pidx])
    me.materials.append(mat)
    for kind_, mname in (('tile', 'cloth'), ('glow', 'glow')):
        # (E9d) the cloth's faces take a material of their own (main() splits them off as <name>_cloth); (E8 later) so
        # do a near prop's lit panes (<name>_glow: OwnProps' unshaded glow), not the far castle's (its one far mesh)
        if kind_ not in kinds or (kind_ == 'glow' and GRIME.get('far')):
            continue
        cm = bpy.data.materials.get(mname) or bpy.data.materials.new(mname)
        me.materials.append(cm)
        for poly in me.polygons:
            if kinds[poly.index] == kind_:
                poly.material_index = len(me.materials) - 1
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ------------------------------------------------------------ (lf6d) old stone --

MOSS_DARK = Vector((0.2, 0.27, 0.085))   # (lf6d) a cushion moss, linear: dark and rich, so a moonlit top reads stone and moss
MOSS_SAGE = Vector((0.36, 0.44, 0.17))
MOSS_WET = Vector((0.24, 0.4, 0.08))     # (E8d) wet moss low on the drums: a green that holds through the dawn's blue mist
LICHEN = Vector((0.6, 0.6, 0.47))           # pale grey-green crust lichen: the moonlit pops on old stone
LEAF = (Vector((0.3, 0.16, 0.05)), Vector((0.2, 0.1, 0.04)), Vector((0.36, 0.25, 0.08)), Vector((0.12, 0.08, 0.04)))


def _ring(rng, n, rx, rz, rag):
    pts = []
    ph = rng(0, 6.28)
    for k in range(n):
        a = 2 * math.pi * k / n
        r = 1.0 + rag * (0.55 * math.sin(3 * a + ph) + 0.45 * math.sin(5 * a + 2.1 * ph)) + rng(-rag, rag) * 0.6
        pts.append((math.cos(a) * rx * r, math.sin(a) * rz * r))
    return pts


def _cushion(rng, cx, cz, y, rx, rz, rag=0.32, n=11, dome=0.012, lim=None):
    """A ragged flat cushion (moss, turf, lichen) lying on a local +y face at y: a fan from a raised middle."""
    bm = bmesh.new()
    c = bm.verts.new((cx, y + dome, cz))
    ring = []
    for x, z in _ring(rng, n, rx, rz, rag):
        x, z = cx + x, cz + z
        if lim:
            x = min(max(x, lim[0]), lim[1])
            z = min(max(z, lim[2]), lim[3])
        ring.append(bm.verts.new((x, y + rng(0.0, 0.004), z)))
    for k in range(n):
        bm.faces.new((c, ring[(k + 1) % n], ring[k]))
    return bm


def _leaves(rng, pts, s):
    """Fallen leaves (each a flat diamond, 2 tris) at local points on a +y face."""
    bm = bmesh.new()
    for (x, y, z) in pts:
        a = rng(0, 6.28)
        L, W = s * rng(0.7, 1.3), s * rng(0.35, 0.55)
        d, q = Vector((math.cos(a), 0, math.sin(a))), Vector((-math.sin(a), 0, math.cos(a)))
        o = Vector((x, y + 0.003, z))
        vs = [bm.verts.new(o + d * L), bm.verts.new(o + q * W + Vector((0, 0.006, 0))), bm.verts.new(o - d * L * 0.8), bm.verts.new(o - q * W)]
        bm.faces.new((vs[0], vs[3], vs[2], vs[1]))
    return bm


def _leaf_tint(c):
    h = 0.5 + 0.5 * hnoise(c * 9.7, 91)
    return LEAF[min(3, int(h * 4))]


def dress(parts, d, seed):
    """(lf6d) Old stone from the play camera: each stone piece's open top (local +y, turned up in the world) dressed
    with cushions of dark moss (ragged, part of the top), pale lichen crusts, fallen leaves and a tuft or two of
    grass; lichen crusts on its faces. d (env_props.json "dress"): moss (share of tops), cover (of the top's span),
    lichen (crusts per top), leaves (per top), tufts (share of tops), side (crusts per upright face),
    up (how far a top must turn up), min (the smallest top's span), unit (the piece's units a metre)."""
    rng = Rng(seed * 7 + 911)
    u = d.get('unit', 1.0)
    out = list(parts)
    for pt in parts:
        if pt.region != 'stone' or pt.bm is None:
            continue
        rot = pt.at.to_3x3()
        pt.bm.normal_update()
        tops = [f for f in pt.bm.faces if f.normal.y > 0.9]
        wup = (rot @ Vector((0, 1, 0))).normalized().y
        if tops and wup > d.get('up', 0.8):
            vs = [v.co for f in tops for v in f.verts]
            x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
            z0, z1 = min(v.z for v in vs), max(v.z for v in vs)
            y = max(v.y for v in vs)
            sx, sz = x1 - x0, z1 - z0
            if min(sx, sz) > d.get('min', 0.12) * u:
                lim = (x0 + 0.01 * u, x1 - 0.01 * u, z0 + 0.01 * u, z1 - 0.01 * u)
                if wup < 0.85 and rng() < d.get('moss', 0.6):
                    # a slope (a roof slab, local z down it): moss along its lower edge, where the water runs off
                    # (sage, near the slab's own value: the dark cushion read as a hole under the moon)
                    tn = MOSS_SAGE * rng(0.95, 1.3)
                    cx = x0 + sx * rng(0.4, 0.6)
                    out.append(Part(_cushion(rng, cx, z1 - sz * 0.12, y, sx * rng(0.42, 0.6), sz * rng(0.09, 0.15), rag=0.3, n=13, dome=0.006, lim=lim), 'soil', tn, pt.at, jitter=0.0))
                elif rng() < d.get('moss', 0.6):
                    k = d.get('cover', 0.4) * rng(0.6, 1.25)
                    cx, cz = x0 + sx * rng(0.25, 0.75), z0 + sz * rng(0.25, 0.75)
                    tn = MOSS_DARK.lerp(MOSS_SAGE, rng(0.0, 0.6)) * rng(0.85, 1.2)
                    out.append(Part(_cushion(rng, cx, cz, y, sx * k, sz * k, lim=lim), 'soil', tn, pt.at, jitter=0.0))
                    if rng() < 0.5:
                        # a second, smaller, where the first ran out
                        cx2, cz2 = x0 + sx * rng(0.15, 0.85), z0 + sz * rng(0.15, 0.85)
                        out.append(Part(_cushion(rng, cx2, cz2, y + 0.002, sx * k * 0.5, sz * k * 0.5, lim=lim), 'soil', tn * rng(0.8, 1.3), pt.at, jitter=0.0))
                for _ in range(int(d.get('lichen', 1.0) + rng())):
                    r = min(sx, sz) * rng(0.07, 0.16)
                    cx, cz = x0 + sx * rng(0.12, 0.88), z0 + sz * rng(0.12, 0.88)
                    out.append(Part(_cushion(rng, cx, cz, y + 0.003, r, r * rng(0.7, 1.0), rag=0.2, n=7, dome=0.002, lim=lim), 'soil', LICHEN * rng(0.85, 1.1), pt.at, jitter=0.0))
                nl = int(d.get('leaves', 3) * rng(0.4, 1.4))
                if nl:
                    lp = [(x0 + sx * rng(0.05, 0.95), y + 0.004, z0 + sz * rng(0.05, 0.95)) for _ in range(nl)]
                    lv = Part(_leaves(rng, lp, 0.045 * u), 'soil', Vector((1, 1, 1)), pt.at, jitter=0.0)
                    lv.ftint = _leaf_tint
                    out.append(lv)
                if rng() < d.get('tufts', 0.25):
                    w = pt.at @ Vector((x0 + sx * rng(0.2, 0.8), y, z0 + sz * rng(0.2, 0.8)))
                    out.append(tuft(rng, Vector((w.x, w.y - 0.01 * u, w.z)), rng(0.16, 0.3) * u, n=6))
        ns = d.get('side', 0.0)
        if ns > 0:
            # crusts on the upright faces: the biggest few
            sides = sorted([f for f in pt.bm.faces if abs(f.normal.y) < 0.3 and f.calc_area() > (0.2 * u) ** 2], key=lambda f: -f.calc_area())[:2]
            for f in sides:
                if rng() > ns:
                    continue
                n = f.normal.copy()
                c = f.calc_center_median()
                t = Vector((0, 1, 0)).cross(n).normalized()
                r = math.sqrt(f.calc_area()) * rng(0.08, 0.16)
                # a crust laid on the face: build on +y then turn +y to the face's normal
                q = n.to_track_quat('Y', 'Z').to_matrix().to_4x4()
                off = c + n * 0.003 + t * math.sqrt(f.calc_area()) * rng(-0.25, 0.25) + Vector((0, math.sqrt(f.calc_area()) * rng(0.0, 0.3), 0))
                out.append(Part(_cushion(rng, 0.0, 0.0, 0.0, r, r * rng(0.6, 0.9), rag=0.22, n=7, dome=0.002), 'soil', LICHEN * rng(0.8, 1.05),
                                pt.at @ T(*off) @ q, jitter=0.0))
    return out


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
            parts.append(Part(box(sh, W - 2 * pt, st * 0.8, 0.003), 'wood', wood * rng(0.84, 1.1), T(0, y, sz * (D / 2 - st * 0.4 - 0.004)) @ R('Z', math.pi / 2), cap='endgrain'))
        for sx in (-1, 1):
            parts.append(Part(box(sh, D - 2 * pt, st * 0.8, 0.003), 'wood', wood * rng(0.84, 1.1), T(sx * (W / 2 - st * 0.4 - 0.004), y, 0) @ R('Y', math.pi / 2) @ R('Z', math.pi / 2), cap='endgrain'))
    diag = math.atan2(H - 0.1, W - 2 * pt)
    for sz in (-1, 1):
        ln = math.hypot(H - 0.1, W - 2 * pt)
        parts.append(Part(box(0.07, ln - 0.05, st, 0.004), 'wood', wood * 0.95, T(0, H / 2, sz * (D / 2 + st * 0.3)) @ R('Z', -(math.pi / 2 - diag) * sz), cap='endgrain'))
    for sx in (-1, 1):
        ln = math.hypot(H - 0.1, D - 2 * pt)
        d2 = math.atan2(H - 0.1, D - 2 * pt)
        parts.append(Part(box(st, ln - 0.05, 0.07, 0.004), 'wood', wood * 0.95, T(sx * (W / 2 + st * 0.3), H / 2, 0) @ R('X', (math.pi / 2 - d2) * sx), cap='endgrain'))
    # The lid (lf5c, the lf0 triage: "flat crates": from the play camera its top was one even board): four boards of
    # unequal width with dark gaps between (2-2.5 cm: the inside's shadow shows), each its own tone (one weathered pale,
    # one dark), a few mm proud or sunk and a little twisted; two battens across them near the ends, a nail pair at each
    # crossing; the bake's lit edges wear their rims
    gap = p.get('gap', 0.022)
    ws = [rng(0.8, 1.2) for _ in range(4)]
    ws = [w / sum(ws) * (D - 3 * gap - 0.004) for w in ws]
    tones = [rng(0.78, 1.12) for _ in range(4)]
    tones[int(rng(0, 4)) % 4] = rng(1.12, 1.22)
    z = -D / 2 + 0.002
    for k in range(4):
        zc = z + ws[k] / 2
        dy = rng(-0.003, 0.004)
        tw = rng(-0.02, 0.02)
        parts.append(Part(box(st, W, ws[k], 0.005), 'wood', wood * tones[k], T(0, H + st / 2 + dy, zc) @ R('X', tw) @ R('Z', math.pi / 2), cap='endgrain'))
        z += ws[k] + gap
    bw = 0.075
    for sx in (-1, 1):
        x = sx * (W / 2 - pt - bw / 2 + 0.01)
        parts.append(Part(box(bw, D - 0.03, st, 0.005), 'wood', wood * rng(0.7, 0.82), T(x, H + st * 1.5 + 0.004, 0) @ R('X', math.pi / 2), cap='endgrain'))
        z = -D / 2 + 0.002
        for k in range(4):
            zc = z + ws[k] / 2
            for o in (-0.22, 0.22):
                parts.append(Part(box(0.011, 0.006, 0.011), 'iron', hexlin('#3a3632'), T(x + o * bw * rng(0.8, 1.2), H + st * 2 + 0.006, zc + o * ws[k] * rng(0.6, 1.0))))
            z += ws[k] + gap
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


def lay_course(xa, xb, bl, rng, half_first, forced=(), var=(0.75, 1.2)):
    """One course's joints from xa to xb: blocks about bl long ('var' times it: 0.75-1.2x), the first a half (running bond)
    when half_first, joints forced at the given x (an opening's edges); no sliver under 0.28 bl."""
    xs = [xa]
    x = xa
    first = True
    while x < xb - 1e-6:
        n = bl * (rng(0.45, 0.6) if (first and half_first) else rng(*var))
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
            if ok and y + cy > keep(m) - cy * 0.7 and rng() < OLD.get('lost', 0.22):
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
                   tint, rng, drop=tuple(drop), top_cuts=(2 if GRIME['moss'] > 0 and '+y' not in drop else 0),
                   chip=(OLD.get('top_chip', 0.45) if '+y' not in drop else 0.45), jag=(OLD.get('jag', 0.01) if '+y' not in drop else 0.01))
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
    keep = profile_fn(p['top'], H, rng, p.get('old', {}).get('jag_top', 0.05))
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


def mound_y(x, z, a, b, h, seed, sag=0.0, lump=0.04, pw=0.55):
    """A heap of earth (elliptic, a by b), its rim under the ground, settled in the middle by sag; pw (lf6d) its
    shoulder: 0.55 a steep-sided loaf, over 1 a hump whose foot runs out into the ground."""
    r = math.sqrt((x / a) ** 2 + (z / b) ** 2)
    if r < 1:
        y = h * (1 - r * r) ** pw - sag * h * math.exp(-r * r * 3)
    else:
        y = -(0.12 if pw < 1 else 0.4) * (r - 1) * max(a, b) - (0.0 if pw < 1 else 0.02)
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


def mound(a, b, h, seed, tint, cx=0.0, cz=0.0, sag=0.0, moss=0.5, step=0.12, cell=3, head=0.45, tufts=10, old=None):
    """A grave's earth as patches of soil (E7b r2: its head end, toward -z, raised; the earth darker at its foot
    where it meets the grass; weeds greening its sides; tufts of grass standing out of them)."""
    # (lf6d) old: an old grave grassed over (the zone's night grass), bare earth only where it settled; its foot
    # running out into the ground (pw), grass standing all over it, leaves caught on it
    old = old or {}
    pw, grass = old.get('pw', 0.55), old.get('grass', 0.0)
    if old:
        step = old.get('step', step)
    ext = 1.18 if not old else 1.08
    nu = max(4, int(2 * a * ext / step))
    nv = max(4, int(2 * b * ext / step))
    weed = Vector((0.5, 0.82, 0.32))
    turf = Vector((old.get('turf', (0.42, 0.62, 0.22))))
    def fn(u, v):
        x, z = (u - 0.5) * 2 * a * ext, (v - 0.5) * 2 * b * ext
        y = mound_y(x, z, a, b, h, seed, sag, pw=pw)
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
        col = Vector((1, 1, 1)).lerp(weed, m)
        if grass > 0:
            # turf over most of it, in clumps; the settled middle and a few scuffs bare; darker and damper at its foot
            g = smooth01(-0.25, 0.35, hnoise(Vector((c.x * 3.7, 0, c.z * 3.7)), seed + 13) + 0.45 * smooth01(0.2, 0.9, r) - 0.5 * math.exp(-r * r * 4) * sag)
            col = col.lerp(turf * (0.8 + 0.4 * (0.5 + 0.5 * hnoise(Vector((c.x * 9.0, 0, c.z * 9.0)), seed + 21))), grass * g)
            col = col * (0.82 + 0.3 * (0.5 + 0.5 * hnoise(Vector((c.x * 6.1, 0, c.z * 6.1)), seed + 29)))
            return col * (1.0 - old.get('foot', 0.42) * foot)
        return col * (1.0 - 0.32 * foot)
    out = patches(fn, nu, nv, cell, cell, 'soil', tint, ft)
    rng = Rng(seed + 77)
    for i in range(tufts):
        sx = 1 if i % 2 else -1
        x = sx * a * rng(0.55, 0.95)
        z = b * rng(-0.85, 0.85)
        y = max(0.0, mound_y(x, z, a, b, h, seed, sag, pw=pw))
        out.append(tuft(rng, Vector((cx + x, y - 0.01, cz + z)), rng(0.2, 0.34)))
    for i in range(old.get('tufts', 0)):
        # (lf6d) grass all over, thicker toward the sides; a few leaves
        rr = math.sqrt(rng(0.04, 1.0)) * 0.98
        an = rng(0, 6.283)
        x, z = math.cos(an) * a * rr, math.sin(an) * b * rr
        y = max(0.0, mound_y(x, z, a, b, h, seed, sag, pw=pw))
        tf = tuft(rng, Vector((cx + x, y - 0.015, cz + z)), rng(0.14, 0.3), n=int(rng(5, 8)))
        tf.tint = Vector(old.get('tuft', (0.3, 0.42, 0.16))) * rng(0.8, 1.2)
        out.append(tf)
    nf = old.get('fringe', 0)
    for i in range(nf):
        # (e22r1a, the Env 22 triage: the mound's edge hard against the turf) a fringe of grass round its foot, standing
        # over the line where its earth meets the ground, so the turf runs up onto it
        an = 2 * math.pi * (i + rng(-0.4, 0.4)) / nf
        rr = rng(0.86, 1.06)
        x, z = math.cos(an) * a * rr, math.sin(an) * b * rr
        y = max(0.0, mound_y(x, z, a, b, h, seed, sag, pw=pw))
        tf = tuft(rng, Vector((cx + x, y - 0.02, cz + z)), rng(0.12, 0.26), n=int(rng(6, 10)))
        tf.tint = Vector(old.get('fringe_tint', old.get('tuft', (0.3, 0.42, 0.16)))) * rng(0.75, 1.2)
        out.append(tf)
    nl = old.get('leaves', 0)
    if nl:
        pts = []
        for i in range(nl):
            rr = math.sqrt(rng(0.0, 1.0)) * 0.95
            an = rng(0, 6.283)
            x, z = math.cos(an) * a * rr, math.sin(an) * b * rr
            pts.append((cx + x, mound_y(x, z, a, b, h, seed, sag, pw=pw) + 0.004, cz + z))
        lv = Part(_leaves(rng, pts, 0.05), 'soil', Vector((1, 1, 1)), jitter=0.0)
        lv.ftint = _leaf_tint
        out.append(lv)
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
    parts += mound(W * 0.42, ml / 2, p.get('mh', 0.3), p['seed'], soil, cz=mz, sag=p.get('sag', 0.4), moss=p.get('moss', 0.85), old=p.get('mound'))
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
    parts += mound(W * 0.46, 0.5, 0.14, p['seed'], soil, cz=0.55, sag=0.2, moss=0.85, old=p.get('mound'))
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
    parts += mound(0.34, p.get('mlen', 0.85), 0.16, p['seed'], soil, cz=p.get('mz', 0.75), sag=0.3, moss=0.8, old=p.get('mound'))
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
        return max(0.0, mound_y(x - cx, z, a, b, Hm, p['seed'], 0.0, 0.07, pw=p.get('pw', 0.55)))
    def fn(uu, vv):
        x, z = cx + (uu - 0.5) * 2 * a * 1.15, (vv - 0.5) * 2 * b * 1.15
        return (x, mound_y(x - cx, z, a, b, Hm, p['seed'], 0.0, 0.16, pw=p.get('pw', 0.55)), z)
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
    nf = p.get('fringe', 0)
    for i in range(nf):
        # (e22r1a, the Env 22 triage: a dark ring round the heap at the Watch-post) grass standing over its foot, where its
        # spoil runs out into the ground, so soil and grass meet the rubble
        an = 2 * math.pi * (i + rng(-0.4, 0.4)) / nf
        rr = rng(0.8, 1.08)
        x, z = cx + math.cos(an) * a * rr, math.sin(an) * b * rr
        tf = tuft(rng, Vector((x, hy(x, z) - 0.02, z)), rng(0.14, 0.3) * u, n=int(rng(6, 10)))
        tf.tint = Vector(p.get('fringe_tint', (0.5, 0.62, 0.28))) * rng(0.75, 1.2)
        parts.append(tf)
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


def bed(p):
    """(E9c3) A cottage bed for the house insides (props Bed_Twin1's box): an oak frame (four posts, the head pair
    taller with a boarded headboard, side rails and a low footboard), a lumpy straw tick of linen on it, a wool
    blanket over it in bold folds, draped over the sides and the foot, its head turned down (a pale band), and a
    linen bolster. Read from the play camera's steep top: the frame shows round the blanket, the folds by their shade."""
    rng = Rng(p['seed'])
    wood, tick, blanket, band, pillow = (hexlin(p[k]) for k in ('wood', 'tick', 'blanket', 'band', 'pillow'))
    W, L, H = p['w'], p['len'], p['h']
    pw, rail = 0.09, 0.13
    parts = []
    hx, hz = W / 2 - pw / 2, L / 2 - pw / 2
    for sx in (-1, 1):
        for sz in (-1, 1):
            ph = H if sz < 0 else H * 0.62
            parts.append(Part(box(pw, ph, pw, 0.01), 'wood', wood * (0.85 + rng(-0.05, 0.05)), T(sx * hx, ph / 2, sz * hz), cap='endgrain'))
    ry = 0.26
    for sx in (-1, 1):
        parts.append(Part(box(0.07, L - 2 * pw + 0.02, rail, 0.008), 'wood', wood * 0.8, T(sx * hx, ry + rail / 2, 0) @ R('X', math.pi / 2), cap='endgrain'))
    for sz, top in ((-1, H - 0.05), (1, H * 0.62 - 0.04)):
        parts.append(Part(box(0.07, W - 2 * pw + 0.02, rail, 0.008), 'wood', wood * 0.8, T(0, ry + rail / 2, sz * hz) @ R('Z', math.pi / 2), cap='endgrain'))
        # boards between the posts (the headboard tall, the footboard low), a capping rail
        nb = 3
        for k in range(nb):
            x = -(W - 2 * pw) / 2 + (W - 2 * pw) * (k + 0.5) / nb
            bh = top - (ry + rail)
            parts.append(Part(box(bh, (W - 2 * pw) / nb - 0.012, 0.035, 0.006), 'wood', wood * (0.9 + rng(-0.08, 0.06)),
                              T(x, ry + rail + bh / 2, sz * hz) @ R('Z', math.pi / 2), cap='endgrain', jitter=0.06))
        parts.append(Part(box(0.06, W - 2 * pw + 0.04, 0.07, 0.008), 'wood', wood * 0.95, T(0, top + 0.03, sz * hz) @ R('Z', math.pi / 2), cap='endgrain'))
    # the straw tick: lumpy, its edges rounded down onto the rails
    tw, tl, t0, tt = W - 2 * pw - 0.02, L - 2 * pw - 0.02, ry + rail - 0.03, 0.16
    def tk(u, v):
        x, z = (u - 0.5) * tw, (v - 0.5) * tl
        e = max(abs(u - 0.5) * 2, abs(v - 0.5) * 2)
        y = t0 + tt * (1 - max(0.0, e - 0.82) / 0.18 * 0.7) + 0.02 * hnoise((x * 4, 0, z * 4), p['seed'] + 7)
        return (x, y, z)
    parts.append(Part(grid(10, 14, tk, skirt=0.04), 'canvas', tick, smooth=True, jitter=0.0))
    top = t0 + tt
    # the blanket: from the foot (v 0, +z) to its turned-down head (v 1), over the tick, its sides draped down
    bw = tw + 0.1
    fold_v, rf = 0.74, 0.03
    def bl(u, v):
        s = (u - 0.5) * 2
        a = abs(s)
        x = s * bw / 2 if a < 0.86 else (math.copysign(1, s) * (tw / 2 + 0.045))
        drop = 0.0 if a < 0.78 else min(1.0, (a - 0.78) / 0.22) * (tt + 0.03)
        folds = 0.028 * math.sin(v * 13.0 + s * 3.1 + 1.3 * hnoise((s, 0, v * 2), p['seed'])) * (0.45 + 0.55 * math.sin(v * 4.1 + s * 2.3) ** 2)
        lump = 0.015 * hnoise((s * 3, 2, v * 6), p['seed'] + 1)
        base = top + 0.03 + folds + lump - drop
        z0 = tl / 2 + 0.03
        if v <= fold_v:
            return (x * (1 + 0.02 * math.sin(v * 9)), base, z0 - v / fold_v * (tl * fold_v + 0.03))
        zf = z0 - (tl * fold_v + 0.03)
        d = (v - fold_v) / (1 - fold_v) * 0.32
        if d < math.pi * rf:
            th = d / rf
            return (x, base + rf - rf * math.cos(th), zf - rf * math.sin(th))
        return (x, base + 2 * rf + 0.004, zf + (d - math.pi * rf))
    bmb = grid(12, 26, bl)
    flap = [f for f in bmb.faces if f.calc_center_median().y > top + 0.03 + 1.6 * rf and f.calc_center_median().z > -tl / 2 + 0.05 and
            f.calc_center_median().z < z_of_fold(tl, fold_v) + 0.35]
    dup = bmesh.ops.duplicate(bmb, geom=flap)
    bmesh.ops.reverse_faces(bmb, faces=[g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)])
    parts.append(Part(bmb, 'cloth', blanket, smooth=True, jitter=0.0))
    # the turned-down band
    def bandf(u, v):
        q = bl(u, 1.0 - (1.0 - v) * 0.18)
        return (q[0], q[1] + 0.003, q[2])
    parts.append(Part(grid(12, 3, bandf), 'cloth', band, smooth=True, jitter=0.0))
    # the bolster at the head
    pr = 0.1
    parts += [q for q in roll_parts(p, tw * 0.86, pr, T(0, top + pr * 0.7, -tl / 2 + 0.17) @ S(1, 0.62, 1), rng, pillow, pillow * 0.95, pillow)
              if q.region in ('cloth', 'rollend')]
    return parts


def z_of_fold(tl, fold_v):
    return tl / 2 + 0.03 - (tl * fold_v + 0.03)


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
    # (lf6d) old: the ridge sagged in its middle (sag m), slabs of a wider value spread, more lichen, more slipped
    # and laid more askew, so the roof reads as weathered courses from above, not a tiled grid
    ro = p.get('roof_old', {})
    sag = ro.get('sag', 0.0)
    vlo, vhi = ro.get('value', (0.74, 1.12))
    p_lichen, p_slip, yaw = ro.get('lichen', 0.14), ro.get('slip', 0.015), ro.get('yaw', 0.04)
    def sagged(pos):
        return pos - Vector((0, sag * max(0.0, 1 - (2 * pos.z / ln) ** 2), 0))
    for sx in (-1, 1):
        down = Vector((sx * math.cos(ang), -math.sin(ang), 0.0))
        up = Vector((sx * math.sin(ang), math.cos(ang), 0.0))
        along = Vector((0.0, 0.0, 1.0))
        frame = basis(along, up, down)  # local x along the ridge, y off the slope, z down it
        # the underlay: a dark deck under the slabs (what a slipped slab shows)
        parts.append(Part(box(ln - 0.1, 0.08, run - 0.15), 'stone', slab * 0.45, T(*(ridge + down * (run / 2 + 0.02) - up * 0.06 - Vector((0, sag, 0)))) @ frame, cap='stone', jitter=0.0))
        # (e22r1a, the Env 22 triage: "an even grid of slabs, like wall texture" from the play camera) 'course' the courses'
        # depth and 'bl_var' the slabs' spread of width: bigger, unequal slates, so fewer, uneven joints
        course = ro.get('course', 0.56)
        nk = int(run / course + 0.999)
        # (lf6d) old: courses of unequal depth (the quarry's beds), slabs of unequal width, so no grid shows
        cvar = ro.get('course_var', 0.0)
        cds = [course * (1 + cvar * (rng(-1, 1) if cvar else 0.0)) for _ in range(nk)]
        cds = [c * run / sum(cds) * nk * course / run for c in cds] if cvar else cds
        s_at = [sum(cds[:k]) for k in range(nk)]
        for k in range(nk):
            s0 = s_at[k]
            course = cds[k]
            lift = 0.035  # each course rides on the one below at its tail
            xs = lay_course(-ln / 2, ln / 2, ro.get('bl', 0.82), rng, k % 2 == 1, var=tuple(ro.get('bl_var', (0.75, 1.2))))
            t = (s0 + course / 2) / run
            for a, b in zip(xs, xs[1:]):
                xm = (a + b) / 2
                if rng() < p_slip and 0 < k < nk - 1:
                    continue  # slipped: the underlay shows
                sw, sl = b - a - 0.035, course + 0.16
                mz = 0.5 + 0.55 * hnoise(Vector((xm * 1.7, 0, s0 * 1.7 + sx * 3.1)), 61)
                m = max(smooth01(0.62, 1.0, t), 0.8 * smooth01(0.16, 0.0, t)) * smooth01(0.3, 0.6, mz)
                m = max(m, 0.35 * smooth01(0.62, 0.8, mz))
                dark = 1.0 - 0.3 * smooth01(0.7, 1.0, t)
                tn = slab * rng(vlo, vhi) * dark
                if ro.get('cluster'):
                    # weathering in drifts across the slabs (wet, darker; dry, paler), not slab by slab
                    tn = tn * (1 + ro['cluster'] * hnoise(Vector((xm * 0.8, 0, s0 * 1.1 + sx * 5.3)), 63))
                if ro.get('streak'):
                    # (e22r1a) rain streaks: dark bands down the slope, the same along it (by the slab's place across the roof),
                    # stronger toward the eave where the run-off gathers
                    sk = smooth01(0.5, 0.85, 0.5 + 0.55 * hnoise(Vector((xm * 1.9, 0, sx * 7.7)), 73))
                    tn = tn * (1 - ro['streak'] * sk * (0.55 + 0.45 * t))
                if rng() < p_lichen:
                    tn = tn.lerp(Vector((0.86, 0.85, 0.74)), rng(0.3, 0.6))  # pale lichen
                tn = tn.lerp(moss * rng(0.85, 1.1), min(1.0, m * 0.9))
                if k == nk - 1:
                    tn = tn.lerp(Vector((0.26, 0.33, 0.15)), 0.55 + 0.3 * smooth01(0.4, 0.7, mz))  # the eave: dark, mossed
                pos = ridge + down * (s0 + sl / 2 - 0.08) + up * (th / 2 + lift * (1 - (k % 2) * 0.3)) + along * xm
                tilt = R('X', -0.06 + rng(-0.025, 0.025))  # the tail down, the butt up over the course below
                parts.append(Part(stone_block(sw, th * rng(0.85, 1.1), sl, rng, bevel=0.02, chip=0.7, jag=0.02), 'stone', tn,
                                  T(*sagged(pos)) @ frame @ tilt @ R('Y', rng(-yaw, yaw)), cap='stone', jitter=0.0))
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
                                  T(*sagged(pos)) @ frame, cap='stone', jitter=0.0))
    # the ridge: capping stones, a little apart, mossed in patches
    n = int(ln / 0.62)
    for k in range(n):
        z = -ln / 2 + (k + 0.5) * ln / n
        mz = 0.5 + 0.55 * hnoise(Vector((0, 0, z * 1.3)), 71)
        tn = slab * rng(0.9, 1.05)
        tn = tn.lerp(moss, 0.8 * smooth01(0.35, 0.6, mz))
        parts.append(Part(stone_block(0.34, 0.34, ln / n - 0.04, rng, bevel=0.04, chip=0.6), 'stone', tn,
                          T(*sagged(Vector((0, ridge.y + 0.1, z)))) @ R('Z', math.pi / 4 + rng(-0.05, 0.05)), cap='stone', jitter=0.0))


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


# ------------------------------------------------------------ the town (E9d) --
# The Waystation's square: market stalls, the notice board and the clutter of a working market (handcart, sacks,
# crates, barrels, a trough, hay, straw, dung, crocks). Everything on the one atlas but the notices' paper
# (notice_paper.png, tools/assets/env_notice_paper.py: their writing needs pixels of its own).

def sphere(r, segs=8, rings=5, squash=1.0):
    prof = [(r * math.sin(math.pi * k / rings), -r * squash * math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    prof[0] = (0.0, prof[0][1])
    prof[-1] = (0.0, prof[-1][1])
    return lathe(prof, segs)


def lumpy(bm, amt, freq, seed):
    for v in bm.verts:
        v.co *= 1 + amt * hnoise(v.co * freq, seed)
    bm.normal_update()
    return bm


def sheet(nu, nv, fn, t=0.006):
    """A cloth: grid() given a thickness (both faces drawn, the props material culls backs)."""
    bm = grid(nu, nv, fn)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=t)
    bm.normal_update()
    return bm


def basket(parts, at, r, h, tint, fill=None, fill_tint=None, rng=None, n_fruit=7, fruit_r=0.04):
    """A wicker basket (the weave in its rings, over and under), a rim, and what it holds heaped over the top."""
    segs, rings = 24, 6
    prof = [(r * (0.78 + 0.22 * k / rings), h * k / rings) for k in range(rings + 1)]
    bm = lathe(prof, segs, cap0=True, cap1=False)
    for v in bm.verts:
        a = math.atan2(v.co.z, v.co.x)
        i = int(round((a + math.pi) / (2 * math.pi) * segs))
        k = int(round(v.co.y / h * rings))
        if 0 < k < rings:
            s = 1 + 0.035 * (1 if (i + k) % 2 else -1)
            v.co.x *= s
            v.co.z *= s
    bm.normal_update()
    parts.append(Part(bm, 'wood', tint, at, smooth=False, jitter=0.05))
    parts.append(Part(torus(r, 0.014, segs, 5), 'wood', tint * 0.85, at @ T(0, h, 0), smooth=True, jitter=0.0))
    if fill:
        rng = rng or Rng(int(r * 1000))
        top = h * 0.92
        dome = lathe([(r * 0.97, top - 0.01), (r * 0.7, top + fruit_r * 0.9), (0.0, top + fruit_r * 1.5)], 12, cap0=False, cap1=False)
        parts.append(Part(lumpy(dome, 0.06, 14, 3), 'cloth', fill_tint * 0.8, at, smooth=True, jitter=0.0))
        for k in range(n_fruit):
            a = k * 2.4 + rng(0, 0.5)
            d = r * (0.25 + 0.55 * ((k * 0.618) % 1))
            y = top + fruit_r * (1.5 - 0.9 * d / r)
            f = lumpy(sphere(fruit_r * rng(0.85, 1.12), 8, 5, 0.9), 0.08, 30, k)
            c = fill_tint * rng(0.8, 1.15)
            parts.append(Part(f, fill, c, at @ T(d * math.cos(a), y, d * math.sin(a)) @ R('Y', a), smooth=True, jitter=0.06))


def crock(parts, at, h, r, tint, mouth=0.55, handle=False, rng=None):
    """An earthenware crock or jug: a lathe of fired clay, a glaze line at the shoulder."""
    prof = [(r * 0.6, 0.0), (r * 0.92, h * 0.08), (r, h * 0.35), (r * 0.9, h * 0.62), (r * mouth, h * 0.86), (r * mouth * 0.95, h * 0.95),
            (r * mouth * 1.12, h), (r * mouth * 0.95, h * 0.97), (r * mouth * 0.75, h * 0.6)]
    bm = lathe(prof, 14, cap0=True, cap1=True)
    parts.append(Part(bm, 'stone', tint, at, smooth=True, jitter=0.06))
    if handle:
        hb = torus(h * 0.18, 0.012, 8, 5, -1.3, 1.3)
        parts.append(Part(hb, 'stone', tint * 0.95, at @ T(r * 0.88, h * 0.62, 0) @ R('X', math.pi / 2), smooth=True, jitter=0.0))


def bolt(parts, at, L, r, tint):
    """A bolt of cloth: the roll and its spiral end (the rolled blanket's end tile)."""
    bm = lathe([(r, -L / 2), (r * 1.02, -L / 2 + 0.02), (r * 1.02, L / 2 - 0.02), (r, L / 2)], 14)
    p = Part(bm, 'cloth', tint, at, smooth=True, jitter=0.05, cap='rollend', capr=r, capto=0.13)
    parts.append(p)


def hang_bunch(parts, at, L, r, tint, rng, head=None):
    """Herbs hung to dry, heads down (E9d r2: stalks you can see, not a dark cone): a fan of thin stalks splaying from the
    tie, each with its leaves in small clumps along it and a seed head or flower tuft at its tip, dried green or ochre,
    lighter at the tips; the cord to the rail."""
    n = 12
    for k in range(n):
        a = k * 2.399 + rng(-0.3, 0.3)
        spread = r * rng(0.55, 1.15)
        ln = L * rng(0.8, 1.05)
        tip = Vector((math.cos(a) * spread, -ln, math.sin(a) * spread))
        ln2, sat = along(Vector((0, -0.01, 0)), tip, side=Vector((math.cos(a + 1.57), 0, math.sin(a + 1.57))))
        parts.append(Part(box(0.007, ln2, 0.007), 'canvas', tint * rng(0.7, 0.9), at @ sat, jitter=0.0))
        # leaf blades along it, angled out and down from the stalk, alternate sides: a sprig's silhouette, not beads
        d = tip.normalized()
        out = Vector((math.cos(a), 0, math.sin(a)))
        for j in range(4):
            t = 0.3 + 0.17 * j + rng(-0.04, 0.04)
            c = tip * t
            sgn = 1 if j % 2 else -1
            lv = (d * 0.55 + out * sgn * 0.8 + Vector((0, -0.2, 0))).normalized()
            ll = rng(0.045, 0.07)
            lln, lat = along(c, c + lv * ll, side=Vector((-out.z, 0, out.x)))
            parts.append(Part(box(0.022, lln, 0.003), 'canvas', tint * rng(0.95, 1.2), at @ lat, jitter=0.0))
        hd = lumpy(sphere(r * rng(0.14, 0.2), 5, 3, 1.4), 0.25, 30, k + 50)
        parts.append(Part(hd, 'canvas', (head if head is not None else tint) * rng(1.0, 1.2), at @ T(tip.x, tip.y, tip.z), smooth=True, jitter=0.0))
    parts.append(Part(box(0.018, 0.04, 0.018), 'leather', Vector((0.6, 0.52, 0.4)), at @ T(0, -0.01, 0), jitter=0.0))
    parts.append(Part(box(0.006, 0.12, 0.006), 'leather', Vector((0.6, 0.52, 0.4)), at @ T(0, 0.06, 0), jitter=0.0))


DYE = {'madder': '#b0503e', 'woad': '#5878a4', 'weld': '#d2b04a', 'linen': '#ece2cc', 'walnut': '#9a7a5a'}


def stall(p):
    """A market stall (E9d): a hewn frame (four posts, rails, knee braces), a dyed canvas awning tied over it, sagging
    between the rails and drooping at the front into a valance (scalloped or ragged), sun-faded on top, its low edge
    soiled, sewn in panels with a patch or two; a plank counter on trestles, closed in front, laden with the day's wares
    by kind; stock below and behind. Its frame: the counter's front at +z, x along it."""
    rng = Rng(p['seed'])
    wood = hexlin(p['wood'])
    dye = hexlin(DYE.get(p['dye'], p['dye']))
    dye2 = hexlin(DYE.get(p.get('dye2', 'linen'), p.get('dye2', 'linen')))
    pale = hexlin(DYE['linen'])
    # (E9d r3) what the sun bleaches the top toward: linen by default; a dark dye's own greyed pale (the woad's went lilac)
    fade_to = hexlin(p['fade_to']) if 'fade_to' in p else pale
    stripe = p.get('stripe', 0.0)
    parts = []
    hx, zb, zf = 1.3, -0.8, 0.9
    # (E9d r3: lift raises the whole awning, the posts with it: the herb stall's valance hid its stallholder's head)
    yb, yf = 2.42 + p.get('lift', 0.0), 2.05 + p.get('lift', 0.0)
    pw = 0.11
    # Posts, hewn, each a little off plumb.
    for sx in (-1, 1):
        for z, hgt in ((zb, yb), (zf, yf)):
            parts.append(Part(box(pw, hgt + 0.06, pw * 0.92, 0.012), 'wood', wood * rng(0.85, 1.0),
                              T(sx * hx, (hgt + 0.06) / 2 - 0.03, z) @ R('Z', rng(-0.02, 0.02)) @ R('X', rng(-0.02, 0.02)), cap='endgrain', jitter=0.08))
    # Rails: front and back along x, the sides sloping back to front.
    for z, y in ((zb, yb - 0.05), (zf, yf - 0.05)):
        parts.append(Part(box(0.08, 2 * hx + 0.3, 0.075, 0.008), 'wood', wood * 0.9, T(0, y, z) @ R('Z', math.pi / 2), cap='endgrain'))
    for sx in (-1, 1):
        ln, at = along((sx * hx, yb - 0.02, zb - 0.1), (sx * hx, yf - 0.02, zf + 0.1), side=Vector((1, 0, 0)))
        parts.append(Part(box(0.07, ln, 0.08, 0.008), 'wood', wood * 0.88, at, cap='endgrain'))
        # knee braces at each post
        for z, y in ((zb, yb - 0.1), (zf, yf - 0.1)):
            ln, at = along((sx * hx, y - 0.45, z), (sx * (hx - 0.45), y, z), side=Vector((0, 0, 1)))
            parts.append(Part(box(0.06, ln + 0.06, 0.055, 0.006), 'wood', wood * 0.84, at, cap='endgrain'))
    # The counter: planks on two trestles, a skirt of upright boards in front, sides closed.
    cy, cz0, cz1 = 0.9, 0.38, 1.08
    nb = 3
    for i in range(nb):
        z = cz0 + (cz1 - cz0) * (i + 0.5) / nb
        parts.append(Part(box(0.045, 2 * hx + 0.22, (cz1 - cz0) / nb - 0.01, 0.006), 'wood', wood * rng(0.92, 1.05),
                          T(rng(-0.02, 0.02), cy - 0.022 + rng(-0.004, 0.004), z) @ R('Z', math.pi / 2), cap='endgrain', jitter=0.08))
    nsk = 11
    for i in range(nsk):
        x = -hx - 0.06 + (2 * hx + 0.12) * (i + 0.5) / nsk
        hb = cy - 0.06 - rng(0.0, 0.06)
        parts.append(Part(box((2 * hx + 0.12) / nsk - 0.012, hb, 0.025, 0.005), 'wood', wood * rng(0.8, 0.98),
                          T(x, hb / 2 + 0.02, cz1 - 0.03) @ R('Z', rng(-0.012, 0.012)), cap='endgrain', jitter=0.08))
    for sx in (-1, 1):
        parts.append(Part(box(0.025, cy - 0.08, cz1 - cz0 - 0.05, 0.005), 'wood', wood * 0.82, T(sx * (hx + 0.02), (cy - 0.08) / 2 + 0.02, (cz0 + cz1) / 2), cap='endgrain'))
    parts.append(Part(box(0.06, 2 * hx, 0.06, 0.006), 'wood', wood * 0.75, T(0, cy - 0.09, cz0 + 0.05) @ R('Z', math.pi / 2), cap='endgrain'))

    # ---- the awning: a sheet over the rails, sagging in each bay, the front drooping into the valance
    W = 2 * hx + 0.32
    z0, z1 = zb - 0.14, zf + 0.22
    sag = p.get('sag', 0.13)
    ph = rng(0, 6.28)

    def roof(u, v):
        x = -W / 2 + W * u
        z = z0 + (z1 - z0) * v
        t = (z - zb) / (zf - zb)
        y = yb + 0.035 + (yf + 0.035 - yb - 0.035) * t
        ax = min(1.0, max(0.0, (x + hx) / (2 * hx)))
        az = min(1.0, max(0.0, t))
        s = sag * math.sin(math.pi * ax) * math.sin(math.pi * az) ** 0.7
        # tension folds running from the post tops toward the middle, and a looser rumple
        s += p.get('folds', 0.018) * math.sin(11 * (x * 0.8 + z) + ph) * math.sin(math.pi * ax) + 0.012 * hnoise(Vector((x * 3, 0, z * 3)), p['seed'])
        over_x = max(0.0, abs(x) - hx)
        y -= s + over_x * 0.9
        if z > zf:
            dz = z - zf
            y -= dz * 0.9 + 1.6 * dz * dz
            z = zf + dz * 0.75
        if z < zb:
            y -= (zb - z) * 0.8
        return Vector((x, y, z))
    NU, NV = 40, 16
    sw = W / NU

    def stripe_of(c):
        col = 0 if stripe <= 0 else int(math.floor((c.x + W / 2) / stripe))
        return dye if (col % 2 == 0) else dye2

    def cloth_mod(base, c):
        return cloth_tint(c, c.y > roof(min(1, max(0, (c.x + W / 2) / W)), min(1, max(0, (c.z - z0) / (z1 - z0)))).y - 0.003, base)

    def cloth_tint(c, face_top=True, base=None):
        x, y, z = c.x, c.y, c.z
        n1 = hnoise(Vector((x * 2.3, 0, z * 2.3)), p['seed'] + 5)
        fade = (p.get('fade', 0.24) if face_top else 0.08) + 0.12 * n1
        if face_top and p.get('crown', 0.0) > 0:
            # (E9d r2) sun-faded most on the crown: the high middle of the sheet, least at its edges
            ax = min(1.0, max(0.0, (x + hx) / (2 * hx)))
            az = min(1.0, max(0.0, (z - zb) / (zf - zb)))
            fade += p['crown'] * math.sin(math.pi * ax) ** 1.5 * (1 - az) ** 0.6
        base = base.lerp(fade_to, max(0.0, min(0.8, fade)))
        if face_top and p.get('sag_shade', 0.0) > 0 and abs(x) < hx and zb < z < zf:
            # (E9d r2) the bellies between the rails darker, the cloth over the rails and posts lighter: the sag reads from above
            ax = (x + hx) / (2 * hx)
            az = (z - zb) / (zf - zb)
            dip = math.sin(math.pi * ax) * math.sin(math.pi * az) ** 0.7
            base = base * (1.0 + p['sag_shade'] * (0.35 - dip))
        # soiled toward the low edges, tide marks in blotches, a dark rain line along the back
        low = smooth01(0.3, 1.0, (z - zf + 0.3) / 0.5) * 0.25 + smooth01(hx - 0.1, hx + 0.16, abs(x)) * 0.22
        blot = smooth01(0.35, 0.62, hnoise(Vector((x * 4.1, 1.3, z * 4.1)), p['seed'] + 9)) * 0.14
        k = 1.0 - low - blot
        soil = Vector((0.86, 0.8, 0.7))
        return Vector((base.x * k * (1 - (1 - soil.x) * (low + blot)), base.y * k * (1 - (1 - soil.y) * (low + blot)), base.z * k * (1 - (1 - soil.z) * (low + blot))))
    aw = sheet(NU, NV, roof, 0.006)
    awp = Part(aw, 'tile', Vector((1, 1, 1)), smooth=True, jitter=0.0)
    awp.ftint = stripe_of
    awp.vmod = cloth_mod
    parts.append(awp)
    # Sewn seams between the panels (each two stripes wide), raised a little: a stitched ridge that catches the light.
    panel = (2 * stripe) if stripe > 0 else p.get('panel', 0.6)
    xs = -W / 2 + panel
    while xs < W / 2 - 0.1:
        u = (xs + W / 2) / W
        pts = [roof(u, v / 12) + Vector((0, 0.006, 0)) for v in range(13)]
        parts.append(Part(ribbon(pts, 0.014, 0.004), 'tile', dye2 * 0.72 if stripe else dye * 0.7, smooth=True, jitter=0.0))
        xs += panel
    # A patch or two, sewn over a tear (a scrap of another cloth).
    for (pu, pv, pw2, ph2, ptint) in p.get('patches', []):
        rag = p.get('patch_rag', 0.0)

        def patch(u, v, pu=pu, pv=pv, pw2=pw2, ph2=ph2):
            du, dv = u - 0.5, v - 0.5
            if rag > 0:
                # (E9d r3) a torn scrap, not a cut label: its edge in and out by up to rag of its size
                a = math.atan2(dv, du)
                k = 1.0 - rag * (0.5 + 0.5 * math.sin(3 * a + pu * 9) * 0.6 + 0.4 * hnoise(Vector((math.cos(a) * 2.5, 0, math.sin(a) * 2.5)), p['seed'] + 31))
                e = max(abs(du), abs(dv)) * 2
                du, dv = du * (1 - (1 - k) * e), dv * (1 - (1 - k) * e)
            uu = pu + du * pw2 / W
            vv = pv + dv * ph2 / (z1 - z0)
            return roof(uu, vv) + Vector((0, 0.009, 0))
        pn = 10 if rag > 0 else 3
        pp = Part(sheet(pn, pn, patch, 0.003), 'tile', hexlin(DYE.get(ptint, ptint)), smooth=True, jitter=0.04)
        if p.get('patch_weather'):
            # (E9d r3) faded, shaded and soiled as the sheet under it, so it sits within its value
            pp.vmod = lambda t, c: cloth_tint(c, True, t)
            pp.jitter = 0.0
        parts.append(pp)
        if p.get('patch_stitch'):
            # (E9d r2) its hem sewn round in a darker thread: a patch, not a tag
            for (ua, va, ub, vb) in ((0, 0, 1, 0), (1, 0, 1, 1), (1, 1, 0, 1), (0, 1, 0, 0)):
                pts = [patch(ua + (ub - ua) * k / 6, va + (vb - va) * k / 6) + Vector((0, 0.003, 0)) for k in range(7)]
                parts.append(Part(ribbon(pts, 0.012, 0.003), 'tile', hexlin(DYE.get(ptint, ptint)) * 0.6, smooth=True, jitter=0.0))
    # The valance: hung from the front edge, its hem scalloped (or torn ragged), a band of the second cloth.
    vk = p.get('valance', 'scallop')
    vd = 0.3
    edge_u = [i / NU for i in range(NU + 1)]

    def val(u, v):
        top = roof(u, 1.0)
        x = top.x
        if vk == 'scallop':
            sc = W / 9
            ph2 = ((x + W / 2) / sc) % 1.0
            d = vd * (0.55 + 0.45 * math.sin(math.pi * ph2) ** 0.6)
        else:
            d = vd * (0.7 + 0.3 * hnoise(Vector((x * 9.0, 0, 0)), p['seed'] + 2) + 0.25 * (1 if int((x + 3) * 13) % 5 == 0 else 0))
        y = top.y - 0.01 - d * v
        z = top.z + 0.01 + 0.025 * math.sin(x * 6.0 + ph) * v + 0.02 * v
        return Vector((x, y, z))
    vb = sheet(NU, 4, val, 0.005)
    vp = Part(vb, 'tile', Vector((1, 1, 1)), smooth=True, jitter=0.0)
    band = hexlin(DYE.get(p.get('band', p['dye']), p.get('band', p['dye'])))

    def vtint(c):
        n1 = hnoise(Vector((c.x * 3.0, c.y * 3.0, 0.0)), p['seed'] + 11)
        b = band.lerp(pale, 0.15 + 0.15 * n1)
        low = 0.18 + 0.12 * n1
        return b * (1 - low * smooth01(yf - 0.32, yf - 0.5, c.y))
    vp.vmod = lambda t, c: vtint(c)
    parts.append(vp)
    # Ties: a cord at each post top, lashing the canvas down.
    for sx in (-1, 1):
        for z, y in ((zb, yb), (zf, yf)):
            parts.append(Part(torus(0.075, 0.009, 10, 4), 'leather', Vector((0.62, 0.55, 0.42)), T(sx * hx, y - 0.06, z), smooth=True, jitter=0.0))

    # ---- wares
    ware = p.get('wares', 'produce')
    top = cy + 0.0
    cm = (cz0 + cz1) / 2
    straw = hexlin('#e0c890')
    if ware == 'produce':
        fills = [('cloth', hexlin('#b8443a')), ('cloth', hexlin('#7a9a50')), ('cloth', hexlin('#d8c8b0')), ('cloth', hexlin('#c46a2a'))]
        for i, (x, sz) in enumerate(((-0.95, 0.2), (-0.38, 0.22), (0.2, 0.19), (0.78, 0.2))):
            basket(parts, T(x, top, cm + rng(-0.06, 0.06)) @ R('Y', rng(0, 6)), sz, 0.16, straw * rng(0.75, 0.95), fills[i][0], fills[i][1], rng, 8, 0.045 if i != 1 else 0.07)
        # a string of onions down the front post, a loaf or two
        for k in range(7):
            parts.append(Part(lumpy(sphere(0.04, 8, 5, 0.85), 0.1, 30, k), 'cloth', hexlin('#c8a070') * rng(0.85, 1.1),
                              T(hx - 0.1 + 0.03 * math.sin(k * 2.1), yf - 0.3 - k * 0.075, zf + 0.06 + 0.03 * math.cos(k * 2.1)), smooth=True, jitter=0.0))
        for k, x in enumerate((1.2, 1.08)):
            parts.append(Part(lumpy(sphere(0.09, 10, 5, 0.55), 0.05, 12, k), 'canvas', hexlin('#c08a50'), T(x, top + 0.05, cm + 0.12 - k * 0.2) @ S(1.4, 1, 1), smooth=True, jitter=0.05))
        basket(parts, T(-0.6, 0.0, cz1 + 0.35) @ R('Y', 1.0), 0.24, 0.22, straw * 0.8, 'cloth', hexlin('#b8443a'), rng, 9, 0.05)
        basket(parts, T(-0.05, 0.0, cz1 + 0.3) @ R('Y', 2.0), 0.21, 0.2, straw * 0.75, 'cloth', hexlin('#8aa858'), rng, 5, 0.075)
    elif ware == 'cloth':
        cols = ['#7a8eb0', '#b06a50', '#d8ccb0', '#7e8a58', '#9a6a8a', '#c8a860']
        k = 0
        for row, (n, y0) in enumerate(((4, 0.1), (3, 0.28), (2, 0.45))):
            for i in range(n):
                x = -0.95 + (i + row * 0.5) * 0.19
                bolt(parts, T(x, top + y0 - 0.01, cm) @ R('X', math.pi / 2), 0.62, 0.095, hexlin(cols[k % len(cols)]) * rng(0.85, 1.05))
                k += 1
        # folded lengths, stacked; one hung over the front rail
        y = top
        for i, c in enumerate(['#d8ccb0', '#8a9a68', '#b07058', '#6e82a6']):
            hgt = 0.045
            parts.append(Part(box(0.5 - i * 0.02, hgt, 0.42, 0.012), 'cloth', hexlin(c), T(0.55 + rng(-0.03, 0.03), y + hgt / 2, cm) @ R('Y', rng(-0.1, 0.1)), smooth=False, jitter=0.03))
            y += hgt
        def drape(u, v):
            x = -0.6 + 0.9 * u
            yy = yf - 0.05 - 1.0 * v
            zz = zf + 0.07 + 0.04 * math.sin(u * 9 + v * 2) + 0.02 * v
            return Vector((x, yy + 0.05 * math.sin(u * 7) * v, zz))
        dp = Part(sheet(10, 8, drape, 0.004), 'tile', hexlin('#a85848'), smooth=True, jitter=0.0)
        parts.append(dp)
        for i in range(2):
            bolt(parts, T(-1.0 + i * 0.25, 0.4, cz1 + 0.3) @ R('X', -0.25 + i * 0.12), 0.8, 0.1, hexlin(cols[(i + 3) % 6]))
    elif ware == 'herbs':
        greens = ['#b8c07a', '#dcbc64', '#a8b872', '#e0c470', '#c4b47a']
        heads = ['#d8c890', '#e0b860', '#c8b0c8', '#e8d080', '#d0c088']
        for i in range(9):
            x = -1.1 + i * 0.27 + rng(-0.03, 0.03)
            hang_bunch(parts, T(x, yf - 0.12, zf + 0.06), rng(0.28, 0.36), rng(0.07, 0.09), hexlin(greens[i % 5]) * rng(0.9, 1.05), rng, hexlin(heads[i % 5]))
        for i in range(5):
            crock(parts, T(-1.0 + i * 0.22, top, cm - 0.05 + rng(-0.05, 0.05)), rng(0.14, 0.22), rng(0.05, 0.075), hexlin('#b07a5c') * rng(0.85, 1.1), 0.6, False, rng)
        basket(parts, T(0.45, top, cm) @ R('Y', 0.5), 0.22, 0.15, straw * 0.85, 'cloth', hexlin('#9a8058'), rng, 7, 0.04)
        for i in range(3):
            parts.append(Part(lumpy(lathe([(0.0, -0.17), (0.035, -0.1), (0.05, 0.1), (0.0, 0.17)], 7), 0.15, 20, i), 'bark', hexlin(greens[i]),
                              T(0.95 + i * 0.1, top + 0.04, cm + rng(-0.1, 0.1)) @ R('Z', math.pi / 2) @ R('X', rng(-0.3, 0.3)), smooth=True, jitter=0.05))
    elif ware == 'pots':
        clay = ['#b8704e', '#a86048', '#c48a62', '#8a6a58']
        for i in range(5):
            h = rng(0.22, 0.36)
            crock(parts, T(-1.05 + i * 0.42, top, cm + rng(-0.08, 0.08)), h, h * rng(0.38, 0.5), hexlin(clay[i % 4]) * rng(0.9, 1.05), rng(0.45, 0.7), i % 2 == 0, rng)
        # bowls stacked, upside down
        for k in range(4):
            bw = lathe([(0.0, 0.0), (0.09, 0.0), (0.14 - k * 0.003, 0.07)], 14, cap0=True, cap1=False)
            parts.append(Part(bw, 'stone', hexlin('#b47c5a') * (0.9 + 0.05 * k), T(1.15, top + 0.075 + k * 0.03, cm) @ R('X', math.pi), smooth=True, jitter=0.03))
        for i in range(4):
            h = rng(0.35, 0.55)
            crock(parts, T(-0.9 + i * 0.5, 0.0, cz1 + 0.35 + rng(-0.08, 0.08)), h, h * rng(0.4, 0.5), hexlin(clay[(i + 1) % 4]) * rng(0.85, 1.0), rng(0.5, 0.7), i == 1, rng)
        straw_spill(parts, Vector((0, 0, cz1 + 0.35)), 1.1, 0.45, 90, rng)
    # stock behind: a crate and a sack by the keeper
    parts += sack_parts(0.58, 0.21, p['seed'] + 3, hexlin('#9a8668'), T(-0.95, 0, zb + 0.25) @ R('Y', 0.6))
    cp = dict(w=0.6, d=0.5, h=0.5, wood=p['wood'], seed=p['seed'] + 7)
    parts += [moved(q, T(0.9, 0, zb + 0.3) @ R('Y', 0.2)) for q in crate(cp)]
    return parts


def moved(q, m):
    q.at = m @ q.at
    return q


def straw_spill(parts, c, rx, rz, n, rng, tint=None):
    """Loose straw on the ground: flat stalks at their own angles, thinning out to the edge."""
    tint = tint or hexlin('#e2cc8c')
    bm = bmesh.new()
    for i in range(n):
        a = rng(0, 6.283)
        d = math.sqrt(rng(0, 1))
        px, pz = c.x + rx * d * math.cos(a), c.z + rz * d * math.sin(a)
        ln = rng(0.1, 0.24)
        w = rng(0.005, 0.009)
        th = rng(0, 3.14)
        dx, dz = math.cos(th) * ln / 2, math.sin(th) * ln / 2
        sx, sz = -math.sin(th) * w, math.cos(th) * w
        y = c.y + 0.004 + 0.006 * rng(0, 1)
        vs = [bm.verts.new((px - dx - sx, y, pz - dz - sz)), bm.verts.new((px - dx + sx, y, pz - dz + sz)),
              bm.verts.new((px + dx + sx, y + 0.003, pz + dz + sz)), bm.verts.new((px + dx - sx, y + 0.003, pz + dz - sz))]
        f = bm.faces.new(vs)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.y < 0:
            f.normal_flip()
    sp = Part(bm, 'wood', tint, smooth=False, jitter=0.0)
    sp.ftint = lambda m: Vector((1, 1, 1)) * (0.8 + 0.35 * hnoise(m * 9, 4))
    parts.append(sp)


def notice_board(p):
    """The square's notice board (E9d): two posts sunk in the setts, a plank back, a small shingled hood, and the notices
    (their own mesh, notice_board_paper: notice_paper.png's sheets, aged in their own tones, inked, one corner torn,
    nailed, a couple over each other)."""
    rng = Rng(p['seed'])
    wood = hexlin(p['wood'])
    parts = []
    W, H0, H1 = p['w'], 0.75, 2.05
    for sx in (-1, 1):
        parts.append(Part(box(0.14, 2.55, 0.14, 0.012), 'wood', wood * 0.85, T(sx * (W / 2 + 0.05), 1.27, 0) @ R('Z', sx * 0.012), cap='endgrain', jitter=0.08))
    nb = 5
    for i in range(nb):
        y = H0 + (H1 - H0) * (i + 0.5) / nb
        parts.append(Part(box((H1 - H0) / nb - 0.008, W + 0.04, 0.035, 0.005), 'wood', wood * rng(0.85, 1.02),
                          T(rng(-0.01, 0.01), y, 0) @ R('Z', math.pi / 2), cap='endgrain', jitter=0.08))
    for y in (H0 - 0.03, H1 + 0.03):
        parts.append(Part(box(0.07, W + 0.2, 0.06, 0.006), 'wood', wood * 0.8, T(0, y, 0.01) @ R('Z', math.pi / 2), cap='endgrain'))
    # The hood: two pitched boards of shingles over a ridge, its eaves out over the notices.
    ridge = 2.55
    for sz in (-1, 1):
        a = 0.62
        for row in range(3):
            d = 0.06 + row * 0.13
            y = ridge - d * math.sin(a) - 0.01 * row
            z = sz * d * math.cos(a)
            for k in range(9):
                x = -W / 2 - 0.2 + (W + 0.4) * (k + 0.5) / 9 + (0.04 if row % 2 else 0.0)
                if abs(x) > W / 2 + 0.22:
                    continue
                parts.append(Part(box((W + 0.4) / 9 - 0.012, 0.2, 0.018, 0.004), 'wood', wood * rng(0.6, 0.8),
                                  T(x, y, z) @ R('X', -sz * (math.pi / 2 - a)) @ R('Z', rng(-0.04, 0.04)), cap='endgrain', jitter=0.1))
    parts.append(Part(box(0.07, W + 0.45, 0.07, 0.006), 'wood', wood * 0.6, T(0, ridge + 0.02, 0) @ R('Z', math.pi / 2), cap='endgrain'))
    for sx in (-1, 1):
        ln, at = along((sx * (W / 2 + 0.05), 2.3, 0.0), (sx * (W / 2 + 0.05), ridge - 0.02, 0.0))
        parts.append(Part(box(0.08, ln, 0.08, 0.006), 'wood', wood * 0.7, at, cap='endgrain'))
    notice_nails(parts)
    return parts


# The notices: (x, y, w, h, tilt degrees, cell in notice_paper.png, torn corner 0-3 or -1, z layer)
NOTICES = [(-0.82, 1.62, 0.36, 0.46, -3, 0, 1, 0), (-0.36, 1.48, 0.42, 0.56, 2, 1, -1, 0), (0.12, 1.66, 0.34, 0.42, -1, 2, 2, 0),
           (0.6, 1.5, 0.4, 0.52, 4, 3, -1, 0), (-0.62, 1.06, 0.38, 0.4, 1, 4, -1, 0), (-0.05, 1.12, 0.3, 0.38, -5, 5, 0, 1),
           (0.45, 1.02, 0.34, 0.3, 2, 6, -1, 0), (0.88, 1.12, 0.22, 0.3, -2, 7, 3, 1)]


def trough_water_mesh(name, mat, p):
    """(E9d r3) The trough's water: a flat sheet inside its boards, UVs in metres (OwnProps' water material ripples it)."""
    L, Wd, H, t = p['len'], 0.55, 0.5, 0.05
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    x0, x1, z0, z1, y = -L / 2 + t, L / 2 - t, -Wd / 2 + t, Wd / 2 - t, H - 0.08
    vs = [bm.verts.new(c) for c in ((x0, y, z0), (x0, y, z1), (x1, y, z1), (x1, y, z0))]
    f = bm.faces.new(vs)
    for l in f.loops:
        l[uvl].uv = (l.vert.co.x, l.vert.co.z)
    bm.normal_update()
    if f.normal.y < 0:
        f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.transform(G2B)
    bm.to_mesh(me)
    bm.free()
    ca_ = me.color_attributes.new('tint', 'FLOAT_COLOR', 'CORNER')
    for li in range(len(me.loops)):
        ca_.data[li].color = (1, 1, 1, 1)
    me.color_attributes.active_color = ca_
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def notice_paper_mesh(name, mat):
    """The notices on the board's face: each a sheet bowed off the planks a little, UVs on its cell of notice_paper.png
    (4 x 2 cells), a corner torn off where it says; nails (two or three, on the atlas mesh, see notice_nails)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    for (x, y, w, h, tilt, cell, torn, layer) in NOTICES:
        cu, cv = cell % 4, cell // 4
        a = math.radians(tilt)
        ca, sa = math.cos(a), math.sin(a)
        n = 4
        V = {}
        for i in range(n + 1):
            for j in range(n + 1):
                lx, ly = (i / n - 0.5) * w, (j / n - 0.5) * h
                bow = 0.006 * (1 - (2 * i / n - 1) ** 2) + 0.008 * max(0.0, (0.5 - j / n)) ** 2 * 4
                gx, gy = x + lx * ca - ly * sa, y + lx * sa + ly * ca
                V[(i, j)] = (bm.verts.new((gx, gy, 0.022 + 0.003 * layer + bow)), ((cu + i / n) / 4, 1 - (cv + 1 - j / n) / 2))
        for i in range(n):
            for j in range(n):
                cl = {0: (0, 0), 1: (n - 1, 0), 2: (n - 1, n - 1), 3: (0, n - 1)}.get(torn)
                if cl == (i, j):
                    # a torn corner: half the cell gone, along its diagonal
                    q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                    drop = {0: 0, 1: 1, 2: 2, 3: 3}[torn]
                    tri = [q[(drop + 1) % 4], q[(drop + 2) % 4], q[(drop + 3) % 4]]
                    f = bm.faces.new([V[k][0] for k in tri])
                    for l, k in zip(f.loops, tri):
                        l[uvl].uv = V[k][1]
                    continue
                ks = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                f = bm.faces.new([V[k][0] for k in ks])
                for l, k in zip(f.loops, ks):
                    l[uvl].uv = V[k][1]
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.transform(G2B)
    bm.to_mesh(me)
    bm.free()
    ca_ = me.color_attributes.new('tint', 'FLOAT_COLOR', 'CORNER')
    for li in range(len(me.loops)):
        ca_.data[li].color = (1, 1, 1, 1)
    me.color_attributes.active_color = ca_
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def notice_nails(parts):
    for (x, y, w, h, tilt, cell, torn, layer) in NOTICES:
        a = math.radians(tilt)
        for (lx, ly) in ((-w * 0.38, h * 0.42), (w * 0.38, h * 0.42)) if cell % 2 else ((0.0, h * 0.44),):
            gx, gy = x + lx * math.cos(a) - ly * math.sin(a), y + lx * math.sin(a) + ly * math.cos(a)
            parts.append(Part(lathe([(0.011, 0.0), (0.011, 0.004), (0.0, 0.006)], 6), 'iron', hexlin('#8a8078'),
                              T(gx, gy, 0.026 + 0.003 * layer) @ R('X', math.pi / 2), smooth=False, jitter=0.0))


def handcart(p):
    """A two-wheeled handcart at rest, its legs down at the front, its handles on the ground behind... laden with sacks
    and a basket. Its frame: the bed along z (handles to +z)."""
    rng = Rng(p['seed'])
    wood, iron = hexlin(p['wood']), hexlin('#ffffff')
    parts = []
    L, Wd, Rw = 1.5, 0.95, 0.42
    tilt = math.atan2(Rw + 0.05 - 0.35, L / 2 + 0.6)  # the handles' ends down on their stand
    up = T(0, Rw + 0.05, 0) @ R('X', -tilt)
    nb = 5
    for k in range(nb):
        x = -Wd / 2 + Wd * (k + 0.5) / nb
        parts.append(Part(box(Wd / nb - 0.01, L, 0.035, 0.004), 'wood', wood * rng(0.85, 1.0), up @ T(x, 0.02, 0) @ R('X', math.pi / 2), cap='endgrain', jitter=0.08))
    for sx in (-1, 1):
        parts.append(Part(box(0.07, L + 1.0, 0.07, 0.006), 'wood', wood * 0.85, up @ T(sx * (Wd / 2 - 0.08), -0.04, 0.45) @ R('X', math.pi / 2), cap='endgrain'))
        parts.append(Part(box(0.26, L, 0.03, 0.004), 'wood', wood * 0.92, up @ T(sx * (Wd / 2 + 0.01), 0.15, 0) @ basis((0, 1, 0), (0, 0, 1), (1, 0, 0)), cap='endgrain'))
        for z in (-L / 2 + 0.05, L / 2 - 0.05):
            parts.append(Part(box(0.05, 0.32, 0.05, 0.005), 'wood', wood * 0.85, up @ T(sx * (Wd / 2 + 0.03), 0.14, z), cap='endgrain'))
    parts.append(Part(box(0.24, Wd, 0.03, 0.004), 'wood', wood, up @ T(0, 0.15, -L / 2 - 0.01) @ R('Z', math.pi / 2), cap='endgrain'))
    parts.append(Part(box(0.07, Wd + 0.2, 0.07, 0.006), 'wood', wood * 0.8, T(0, Rw, -0.05) @ R('Z', math.pi / 2), cap='endgrain'))
    for sx in (-1, 1):
        for reg, bm, m, cap in wheel(Rw, 0.045, 8):
            parts.append(Part(bm, reg, iron if reg == 'iron' else wood, T(sx * (Wd / 2 + 0.1), Rw, -0.05) @ R('Y', math.pi / 2) @ m, cap=cap))
    # a prop leg under the handles
    hz = L / 2 + 0.9
    parts.append(Part(box(0.05, 0.36, 0.05, 0.005), 'wood', wood * 0.8, T(0, 0.18, hz - 0.15), cap='endgrain'))
    sk = [hexlin('#9a8668'), hexlin('#8c7a60'), hexlin('#a89474')]
    for i, (x, z, ry) in enumerate(((-0.2, -0.35, 0.3), (0.22, -0.2, -0.5), (0.0, 0.32, 1.2))):
        parts += sack_parts(0.55, 0.2, p['seed'] + i, sk[i], up @ T(x, 0.05 + 0.2 * 0.8, z) @ R('Y', ry) @ R('X', 1.35) @ T(0, -0.27, 0))
    basket(parts, up @ T(0.25, 0.04, 0.45), 0.17, 0.18, hexlin('#d0b880'), 'cloth', hexlin('#7a9a50'), rng, 4, 0.07)
    return parts


def trough(p):
    """A plank water trough on two blocks, iron straps, the water dark in it, a bucket at its end."""
    rng = Rng(p['seed'])
    wood = hexlin(p['wood'])
    parts = []
    L, Wd, H = p['len'], 0.55, 0.5
    t = 0.05
    parts.append(Part(box(t, L, Wd, 0.006), 'wood', wood * 0.8, T(0, 0.12, 0) @ R('Z', math.pi / 2), cap='endgrain'))
    for sz in (-1, 1):
        for k in range(2):
            parts.append(Part(box(0.17, L, t, 0.005), 'wood', wood * rng(0.8, 0.95), T(0, 0.22 + k * 0.175, sz * (Wd / 2 - t / 2)) @ R('Z', math.pi / 2), cap='endgrain', jitter=0.08))
    for sx in (-1, 1):
        parts.append(Part(box(Wd - 2 * t, 0.35, t, 0.005), 'wood', wood * 0.82, T(sx * (L / 2 - t / 2), 0.31, 0) @ R('Y', math.pi / 2), cap='endgrain'))
        parts.append(Part(box(0.22, 0.14, Wd + 0.12, 0.01), 'stone', hexlin('#b8b0a4'), T(sx * L * 0.33, 0.07, 0), jitter=0.05))
        parts.append(Part(box(0.04, 0.36, 0.006), 'iron', hexlin('#ffffff'), T(sx * L * 0.2, 0.3, Wd / 2 + 0.003), jitter=0.0))
    # (E9d r3) the water: its own mesh and material (trough_water_mesh; OwnProps' glossy rippled water), not the canvas
    # region (its weave read as woven mesh at the close camera)
    bk = lathe([(0.12, 0.0), (0.15, 0.3)], 12, cap0=True, cap1=False)
    parts.append(Part(bk, 'wood', wood * 0.85, T(L / 2 + 0.3, 0, 0.25), smooth=False))
    parts.append(Part(torus(0.15, 0.008, 12, 4), 'iron', hexlin('#ffffff'), T(L / 2 + 0.3, 0.25, 0.25), smooth=True, jitter=0.0))
    parts.append(Part(torus(0.15, 0.006, 10, 4, 0, math.pi), 'iron', hexlin('#ffffff'), T(L / 2 + 0.3, 0.3, 0.25) @ R('X', math.pi / 2) @ R('Y', 0.4), smooth=True, jitter=0.0))
    return parts


def hay_bale(parts, at, L, Wd, H, rng):
    """A bale of hay: a lumpy block, stalks sticking out of it, two twine bands round it."""
    bm = box(L, H, Wd, 0.04)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
    for v in bm.verts:
        v.co += v.co.normalized() * 0.03 * hnoise(v.co * 9, 5) + Vector((0, 0, 0))
    bm.normal_update()
    hay = hexlin('#d8bc78')
    hp = Part(bm, 'wood', hay, at @ T(0, H / 2, 0), smooth=True, jitter=0.05)
    hp.ftint = lambda c: Vector((1, 1, 1)) * (0.85 + 0.25 * hnoise(c * 11, 7))
    parts.append(hp)
    for sx in (-0.28, 0.28):
        parts.append(Part(box(0.012, H + 0.03, Wd + 0.03), 'leather', hexlin('#8a7050'), at @ T(sx * L, H / 2, 0), jitter=0.0))


def market_heap(p):
    """A cluster of the market's stock and leavings (E9d): items from a list, each [what, x, z, turn, ...], merged into one
    mesh (one draw): crate, barrel, sack, sack_lying, basket, hay, straw, dung, crock, bucket."""
    rng = Rng(p['seed'])
    parts = []
    allp = PRESETS
    for it in p['items']:
        what, x, z, ry = it[0], it[1], it[2], math.radians(it[3])
        at = T(x, 0, z) @ R('Y', ry)
        if what in ('crate', 'barrel'):
            q = dict(allp[what])
            if len(it) > 4:
                q.update(it[4])
            y = q.pop('y', 0.0)
            parts += [moved(pp, T(0, y, 0) @ at) for pp in KINDS[what](q)]
        elif what == 'sack':
            parts += sack_parts(rng(0.52, 0.64), rng(0.19, 0.23), int(rng(0, 99)), hexlin('#9a8668') * rng(0.85, 1.05), at)
        elif what == 'sack_lying':
            h, r = 0.6, 0.21
            parts += sack_parts(h, r, int(rng(0, 99)), hexlin('#8c7a60') * rng(0.85, 1.05), at @ T(0, r * 0.8, 0) @ R('Z', 1.45) @ T(0, -h / 2, 0))
        elif what == 'basket':
            fill = it[4] if len(it) > 4 else '#b8443a'
            basket(parts, at, 0.22, 0.2, hexlin('#d0b880') * rng(0.75, 0.95), 'cloth', hexlin(fill), rng, 8, 0.05)
        elif what == 'hay':
            hay_bale(parts, at @ T(0, it[4] if len(it) > 4 else 0.0, 0), 0.95, 0.5, 0.45, rng)
        elif what == 'straw':
            straw_spill(parts, Vector((x, 0, z)), it[4], it[5], int(it[4] * it[5] * 260), rng)
        elif what == 'dung':
            for k in range(it[4]):
                d = lumpy(sphere(rng(0.035, 0.05), 8, 4, 0.6), 0.2, 25, k)
                parts.append(Part(d, 'soil', hexlin('#7a6248') * rng(0.7, 0.95), T(x + rng(-0.15, 0.15), 0.012, z + rng(-0.12, 0.12)), smooth=True, jitter=0.0))
        elif what == 'crock':
            h = it[4] if len(it) > 4 else 0.4
            crock(parts, at, h, h * 0.45, hexlin('#b8704e') * rng(0.85, 1.05), 0.55, True, rng)
        elif what == 'woodpile':
            # (E9d r2) split firewood stacked against a wall: rows of billets, their cut ends out
            nrow, ncol, L2 = it[4], it[5], 0.45
            for rr in range(nrow):
                for cc in range(ncol - (rr % 2)):
                    rb = rng(0.06, 0.08)
                    bl = lathe([(rb, -L2 / 2), (rb * rng(0.9, 1.0), L2 / 2)], 5, cap0=True, cap1=True)
                    xx = -ncol * 0.075 + cc * 0.15 + (0.075 if rr % 2 else 0) + rng(-0.01, 0.01)
                    parts.append(Part(bl, 'bark', hexlin('#b8a890') * rng(0.85, 1.1), at @ T(xx, 0.07 + rr * 0.13, rng(-0.03, 0.03)) @ R('X', math.pi / 2) @ R('Y', rng(0, 6)), cap='endgrain', jitter=0.0))
        elif what == 'bench':
            # (E9d r2) a plank bench on two splayed legs
            ln = it[4] if len(it) > 4 else 1.4
            wood = hexlin('#c8b8a0')
            parts.append(Part(box(0.05, ln, 0.3, 0.006), 'wood', wood, at @ T(0, 0.45, 0) @ R('Z', math.pi / 2), cap='endgrain'))
            for sx in (-1, 1):
                parts.append(Part(box(0.26, 0.44, 0.05, 0.005), 'wood', wood * 0.85, at @ T(sx * (ln / 2 - 0.15), 0.215, 0) @ R('Y', math.pi / 2) @ R('Z', sx * 0.06), cap='endgrain'))
        elif what == 'crock_on':
            crock(parts, at @ T(0, it[5], 0), it[4], it[4] * 0.45, hexlin('#b8704e') * rng(0.85, 1.05), 0.55, True, rng)
        elif what == 'bucket':
            bk = lathe([(0.12, 0.0), (0.15, 0.3)], 12, cap0=True, cap1=False)
            parts.append(Part(bk, 'wood', hexlin('#c9ae92') * 0.85, at, smooth=False))
            parts.append(Part(torus(0.15, 0.008, 12, 4), 'iron', hexlin('#ffffff'), at @ T(0, 0.25, 0), smooth=True, jitter=0.0))
    return parts


def brazier(p):
    """(E9d r2) The square's brazier: a wrought-iron stand of three legs with a ring between them, a hammered bowl on top,
    grey ash in it with a few coals and half-burnt sticks (dark by day; the glow is the lamps' code)."""
    rng = Rng(p['seed'])
    iron = hexlin(p.get('iron', '#d8d0c8'))
    parts = []
    H = p.get('h', 1.0)
    rb = 0.32
    for k in range(3):
        a = k * 2.094 + 0.3
        top = Vector((math.cos(a) * rb * 0.55, H - 0.12, math.sin(a) * rb * 0.55))
        foot = Vector((math.cos(a) * rb * 1.05, 0.0, math.sin(a) * rb * 1.05))
        ln, at = along(foot, top)
        parts.append(Part(box(0.035, ln, 0.035, 0.004), 'iron', iron, at, jitter=0.05))
        parts.append(Part(lumpy(sphere(0.04, 6, 3, 0.5), 0.1, 20, k), 'iron', iron * 0.9, T(foot.x, 0.01, foot.z), smooth=True, jitter=0.0))
    parts.append(Part(torus(rb * 0.75, 0.012, 16, 4), 'iron', iron * 0.95, T(0, H * 0.45, 0), smooth=True, jitter=0.0))
    bowl = lathe([(0.0, H - 0.2), (0.12, H - 0.2), (0.27, H - 0.1), (rb, H + 0.04), (rb + 0.03, H + 0.06)], 16, cap0=True, cap1=False)
    lumpy(bowl, 0.02, 9, p['seed'])
    parts.append(Part(bowl, 'iron', iron, smooth=True, jitter=0.0))
    parts.append(Part(torus(rb + 0.02, 0.018, 18, 4), 'iron', iron * 1.05, T(0, H + 0.055, 0), smooth=True, jitter=0.0))
    ash = lathe([(0.0, H + 0.03), (rb - 0.03, H + 0.0)], 14, cap0=True, cap1=False)
    lumpy(ash, 0.04, 14, p['seed'] + 1)
    parts.append(Part(ash, 'soil', hexlin(p.get('ash', '#c8c2ba')), smooth=True, jitter=0.0))
    for k in range(int(p.get('coals', 9))):
        a, d = rng(0, 6.28), rng(0.0, rb * 0.65)
        c = lumpy(sphere(rng(0.035, 0.055), 7, 4, 0.7), 0.25, 30, k)
        tint = hexlin('#3c322c') if k % 3 else hexlin('#8a4a30')
        parts.append(Part(c, 'soil', tint * rng(0.8, 1.1), T(math.cos(a) * d, H + 0.035, math.sin(a) * d) @ R('Y', rng(0, 6)), smooth=True, jitter=0.0))
    for k in range(3):
        a = rng(0, 6.28)
        ln, at = along(Vector((math.cos(a) * 0.05, H + 0.04, math.sin(a) * 0.05)), Vector((math.cos(a + 0.6) * 0.22, H + 0.1, math.sin(a + 0.6) * 0.22)))
        parts.append(Part(box(0.05, ln, 0.045, 0.004), 'bark', hexlin('#6a5e54'), at, cap='endgrain', jitter=0.05))
    return parts


PRESETS = {}


# ------------------------------------- E8: the Waystation's gate, walls and towers at Low Ford; the far castle --
# Built in metres (props_own.json "kits" scales each to its KayKit piece: 1/5.2 the wall runs and the gate, 1/4.68
# the towers). Local frame: x along the wall, y up from the kit piece's floor, +z south (the outer face, toward the
# ford and the play camera). The near pieces' own meshes cast no shadow: each has a low-poly proxy (<name>_shadow,
# a few boxes and lathes) that casts it (OwnProps.Piece). The far castle (<name>_far) is one low mesh, no shadow,
# its lit windows flagged in the vertex alpha (0: a window, its colour its glow; OwnProps' far material).

SHADOW = []  # (E8) the preset's shadow proxy: [(bmesh, matrix)], built by main() as <name>_shadow


def shadow_box(sx, sy, sz, at):
    SHADOW.append((box(sx, sy, sz), at))


def st(stone, rng, k=0.09):
    return stone * (1 + rng(-k, k))


def merlons(parts, rng, x0, x1, y, zc, depth, mh, mw, gap, stone, broken=(), loops=(), shadow=True, fall_z=None, skip=(), fall_y=None):
    """A battlemented top from x0 to x1 standing on y (z about zc): merlons (a block, a weathered cap; with a loop:
    two halves either side of a slit, the dark behind) and the crenels between (a sill); broken: merlon indices lost
    to a ragged stump, the lost stone lying on the walk (at fall_z); skip: indices gone altogether (a breach)."""
    n = max(2, int(round((x1 - x0 + gap) / (mw + gap))))
    w = (x1 - x0 - gap * (n - 1)) / n
    for i in range(n):
        cx = x0 + i * (w + gap) + w / 2
        if i in skip:
            continue
        if i in broken:
            hb = mh * rng(0.25, 0.5)
            parts.append(Part(broken_block(w - 0.04, hb, depth - 0.04, rng, cuts=2, chip=0.8), 'stone', st(stone, rng) * 0.96,
                              T(cx + rng(-0.03, 0.03), y + hb / 2, zc), cap='stone', jitter=0.0))
            if fall_z is not None:
                k = rng(0.6, 0.9)
                bm = broken_block(w * k, mh * 0.6 * k, depth * 0.8, rng, cuts=1, chip=0.9)
                m = bedded(bm, T(cx + rng(-0.4, 0.4), 0, fall_z) @ R('Y', rng(-0.6, 0.6)) @ R('X', rng(-0.3, 0.3)), 0.02)
                parts.append(Part(bm, 'stone', st(stone, rng) * 0.9, T(0, y if fall_y is None else fall_y, 0) @ m, cap='stone', jitter=0.0))
        else:
            hb = mh - 0.13
            if i in loops:
                hw = (w - 0.13) / 2
                for s in (-1, 1):
                    sblock(parts, (hw - 0.02, hb - 0.02, depth - 0.02), T(cx + s * (hw / 2 + 0.065), y + hb / 2, zc), st(stone, rng), rng, drop=('-y',))
                parts.append(Part(box(0.16, hb * 0.86, 0.1), 'stone', stone * 0.06, T(cx, y + hb * 0.48, zc - depth * 0.3), jitter=0.0))
            else:
                sblock(parts, (w - 0.03, hb - 0.02, depth - 0.02), T(cx, y + hb / 2, zc) @ R('Y', rng(-0.02, 0.02)), st(stone, rng), rng, drop=('-y',))
            # (E8d) a fine arris on the cap (the 3 cm bevel's lower edge caught the light: a pale rim under every cap)
            sblock(parts, (w + 0.05, 0.13, depth + 0.07), T(cx, y + hb + 0.065, zc) @ R('Z', rng(-0.02, 0.02)), st(stone, rng) * 1.04, rng, chip=0.6, bevel=0.012)
            if shadow:
                shadow_box(w, mh, depth, T(cx, y + mh / 2, zc))
        if i < n - 1 and (i + 1) not in skip:
            sblock(parts, (gap + 0.06, 0.12, depth + 0.04), T(cx + w / 2 + gap / 2, y + 0.06, zc) @ R('X', 0.06), st(stone, rng) * 1.03, rng, chip=0.5, drop=('-y',))
    return n, w


def flags(parts, rng, x0, x1, z0, z1, y, stone, rows=2):
    """A wall-walk of flagstones from x0 to x1, z0 to z1, their tops at y: rows across, joints in bond."""
    dz = (z1 - z0) / rows
    for r in range(rows):
        zc = z0 + dz * (r + 0.5)
        xs = lay_course(x0, x1, 0.95, rng, r % 2 == 1)
        for a, b in zip(xs, xs[1:]):
            sblock(parts, (b - a - 0.03, 0.18, dz - 0.03), T((a + b) / 2, y - 0.09 - rng(0, 0.025), zc) @ R('X', rng(-0.015, 0.015)) @ R('Z', rng(-0.015, 0.015)),
                   st(stone, rng, 0.12) * 0.94, rng, drop=('-y',), chip=0.6, top_cuts=1)


def footing(parts, rng, x0, L, zf, F, foot, stone, mortar, top=0.55):
    """A wall's footing: big blocks from foot metres under the kit floor (the slope falls away south of the wall)
    to top, stood out from the face, and a chamfered weathering course over them."""
    wall_parts(parts, rng, L, foot + top, F + 0.3, 0.6, 1.35, stone * 0.92, mortar, lambda x: 99.0, x0, at=T(0, -foot, zf + 0.15), gap=0.03, sink=0.0)
    xs = lay_course(x0, x0 + L, 1.25, rng, False)
    for a, b in zip(xs, xs[1:]):
        sblock(parts, (b - a - 0.03, 0.2, 0.42), T((a + b) / 2, top + 0.02, zf + F / 2 + 0.1) @ R('X', 0.55), st(stone, rng) * 0.95, rng, chip=0.6, drop=('-y',))


def retint(parts, test, f):
    """The stone parts whose middles pass test(x, y) re-tinted by f (a repaired stretch: newer, paler stone)."""
    for pt in parts:
        if pt.region == 'stone':
            o = pt.at.to_translation()
            if test(o.x, o.y):
                pt.tint = f(pt.tint)


def curtain(p):
    """(E8) A curtain wall run: a battered footing, the outer face in courses (arrow loops through it), a parapet with
    merlons (some with loops, some lost, a breach where several are gone and the parapet with them), the walk of
    flagstones behind and a low lip on its inner edge, a buttress or two; a repaired stretch in paler stone, a
    settled crack; streaks and grime from the foot."""
    rng = Rng(p['seed'])
    L, H, D, F = p.get('len', 10.4), p.get('h', 5.2), p.get('d', 2.6), p.get('face', 0.55)
    ph, mh = p.get('para', 1.0), p.get('mh', 0.85)
    foot = p.get('footing', 1.8)
    stone, mortar = hexlin(p['stone']), hexlin(p['mortar'])
    x0 = -L / 2
    zf = D / 2 - F / 2
    parts = []
    footing(parts, rng, x0, L, zf, F, foot, stone, mortar)
    top = H + ph
    holes = [(x - 0.1, x + 0.1, 1.5, 2.8) for x in p.get('slits', [])]
    br = p.get('breach')  # [x0, x1, depth]: the parapet broken down over a stretch

    def keep(x):
        if br and br[0] < x < br[1]:
            m = 1 - abs((x - (br[0] + br[1]) / 2) / ((br[1] - br[0]) / 2))
            return top - br[2] * smooth01(0.0, 0.5, m) + 0.15 * math.sin(x * 5.1)
        return top + 0.3
    wall_parts(parts, rng, L, top - 0.55, F, p.get('course', 0.5), p.get('block', 0.95), stone, mortar,
               lambda x: keep(x) - 0.55, x0, at=T(0, 0.55, zf), holes=[(a, b, c - 0.55, d - 0.55) for a, b, c, d in holes],
               crack=p.get('crack') and (x0 + p['crack'][0] * L, x0 + p['crack'][1] * L), sink=0.0)
    for (a, b, c, d) in holes:
        parts.append(Part(box(b - a + 0.06, d - c, 0.12), 'stone', stone * 0.05, T((a + b) / 2, (c + d) / 2, D / 2 - F - 0.02), jitter=0.0))
    mw, gap = p.get('mw', 1.0), p.get('gap', 0.55)
    n = max(2, int(round((L - 0.1 + gap) / (mw + gap))))
    w = (L - 0.1 - gap * (n - 1)) / n
    skip = set()
    if br:
        for i in range(n):
            cx = x0 + 0.05 + i * (w + gap) + w / 2
            if br[0] - w * 0.3 < cx < br[1] + w * 0.3:
                skip.add(i)
    merlons(parts, rng, x0 + 0.05, x0 + L - 0.05, top, zf, F, mh, mw, gap, stone, broken=set(p.get('lost', [])),
            loops=set(p.get('loops', [])), fall_z=-0.4, skip=skip, fall_y=H)
    if br:
        # the breach's stones: a heap on the walk behind it, a few down the outer face's foot
        bx = (br[0] + br[1]) / 2
        for j in range(5):
            bm = broken_block(rng(0.5, 0.95), rng(0.3, 0.45), rng(0.4, 0.55), rng, cuts=2, chip=0.9)
            m = bedded(bm, T(bx + rng(-1.0, 1.0), 0, rng(-0.9, 0.2)) @ R('Y', rng(0, 6.28)) @ R('X', rng(-0.4, 0.4)), 0.03)
            parts.append(Part(bm, 'stone', st(stone, rng) * 0.88, T(0, H, 0) @ m, cap='stone', jitter=0.0))
    # the walk and its inner lip
    flags(parts, rng, x0 + 0.02, x0 + L - 0.02, -D / 2 + 0.42, D / 2 - F, H, stone)
    xs = lay_course(x0, x0 + L, 1.1, rng, True)
    for a, b in zip(xs, xs[1:]):
        sblock(parts, (b - a - 0.03, 0.42, 0.4), T((a + b) / 2, H + 0.19, -D / 2 + 0.2), st(stone, rng) * 0.97, rng, drop=('-y',), chip=0.6, top_cuts=1)
    # the core under the walk (its outer face behind the facing; its inner face never seen from the south)
    parts.append(Part(box(L - 0.04, H + foot - 0.2, D - F - 0.02), 'stone', mortar * 0.55, T(0, (H - foot) / 2 - 0.1, -F / 2), cap='stone', jitter=0.0))
    # buttresses: battered piers stood out from the face, a sloped weathering on top
    for bx in p.get('buttress', []):
        y, k = -foot, 0
        bw, bd = 1.5, 0.95
        while y < p.get('bh', 3.4):
            cy = 0.55 if y > -0.01 else foot / 2
            s = 1.0 - 0.05 * k
            sblock(parts, (bw * s, cy - 0.02, bd * s), T(bx, y + cy / 2, D / 2 + bd * s / 2 - 0.05), st(stone, rng), rng, drop=('-y', '+y'), chip=0.6)
            y += cy
            k += 1
        sblock(parts, (bw * 0.82, 0.3, bd * 0.7), T(bx, y + 0.02, D / 2 + bd * 0.28) @ R('X', 0.6), st(stone, rng) * 1.02, rng, chip=0.7)
        shadow_box(bw, y + foot, bd, T(bx, (y - foot) / 2, D / 2 + bd / 2))
    if p.get('patch'):
        a, b, c, d = p['patch']
        warm = Vector((1.1, 1.05, 0.9))
        retint(parts, lambda x, y: x0 + a * L < x < x0 + b * L and c < y < d, lambda t: Vector((t.x * warm.x, t.y * warm.y, t.z * warm.z)))
    shadow_box(L, top + foot, D, T(0, (top - foot) / 2, 0))
    return parts


def voussoirs(parts, rng, r, spring, S, top, zc, depth, stone, n=11):
    """An arch's ring of wedge stones about (0, spring), its intrados radius r, each stone's outer edge carried to the
    square |x| = S, y = top (the coursed face's opening), the keystone stood a little proud."""
    def hit(a):
        c, s = math.cos(a), math.sin(a)
        t = min(S / abs(c) if abs(c) > 1e-6 else 1e9, (top - spring) / s if s > 1e-6 else 1e9)
        return (c * t, spring + s * t)
    ca = math.atan2(top - spring, S)
    for i in range(n):
        a0, a1 = math.pi * (1 - i / n), math.pi * (1 - (i + 1) / n)
        am = (a0 + a1) / 2
        inner = [(r * math.cos(a0), spring + r * math.sin(a0)), (r * math.cos(am), spring + r * math.sin(am)), (r * math.cos(a1), spring + r * math.sin(a1))]
        outer = [hit(a1)]
        for cn in (ca, math.pi - ca):
            if a1 < cn < a0:
                outer.append((S if cn < math.pi / 2 else -S, top))
        outer.append(hit(a0))
        outer.sort(key=lambda q: math.atan2(q[1] - spring, q[0]))
        poly = inner + outer
        key = i == n // 2
        cx = sum(q[0] for q in poly) / len(poly)
        cy = sum(q[1] for q in poly) / len(poly)
        sh = 0.025
        poly = [(q[0] - sh * (q[0] - cx) / max(0.05, math.hypot(q[0] - cx, q[1] - cy)), q[1] - sh * (q[1] - cy) / max(0.05, math.hypot(q[0] - cx, q[1] - cy))) for q in poly]
        bm = prism(poly, depth + (0.08 if key else 0.0), bevel=0.025)
        parts.append(Part(bm, 'stone', st(stone, rng) * (1.06 if key else 1.0), T(0, 0, zc + (0.04 if key else 0.0)), cap='stone', jitter=0.0))


def gatehouse(p):
    """(E8) The gatehouse between the towers: a passage under a round arch (voussoirs, quoined jambs, a keystone),
    the portcullis drawn up with its teeth under the crown, the two timber leaves swung back inside; over the arch
    a machicolated gallery on corbels, battlements front and back, a walk of flagstones."""
    rng = Rng(p['seed'])
    W, DG, HG = p.get('w', 8.6), p.get('d', 5.0), p.get('h', 7.6)
    F, ph, mh, foot = p.get('face', 0.6), p.get('para', 1.0), p.get('mh', 0.85), p.get('footing', 1.8)
    r, spring, vd = p.get('r', 1.95), p.get('spring', 3.2), p.get('vd', 0.75)
    stone, mortar = hexlin(p['stone']), hexlin(p['mortar'])
    wood, iron = hexlin(p.get('wood', '#8a7460')), hexlin(p.get('iron', '#5a5a60'))
    x0 = -W / 2
    zf = DG / 2 - F / 2
    parts = []
    S = r + vd
    top = HG + ph
    for (a, b) in ((x0, -r - 0.05), (r + 0.05, W / 2)):
        wall_parts(parts, rng, b - a, foot + 0.55, F + 0.3, 0.6, 1.3, stone * 0.92, mortar, lambda x: 99.0, a, at=T(0, -foot, zf + 0.15), gap=0.03, sink=0.0)
    # the face in courses, the arch's opening cut square; the course that straddles its top sets where the voussoirs stop
    yb = spring + S - 0.55
    rows = wall_parts(parts, rng, W, top - 0.55, F, 0.52, 0.95, stone, mortar, lambda x: top + 1.0, x0, at=T(0, 0.55, zf),
                      holes=[(-S, S, -0.6, yb)], sink=0.0)
    ytop = min([y1 for (k, a, b, y0, y1) in rows if y0 < yb <= y1 + 1e-6] or [yb]) + 0.55
    # the jambs: quoins, long and short in turn, up to the springing
    y, k = -0.3, 0
    while y < spring - 0.05:
        cy = min(0.52, spring - y)
        long_ = k % 2 == 0
        wq = vd if long_ else vd * 0.6
        for s in (-1, 1):
            sblock(parts, (wq - 0.03, cy - 0.025, F + 0.04), T(s * (r + wq / 2), y + cy / 2, zf + 0.02), st(stone, rng) * 1.06, rng, drop=('-y', '+y'), chip=0.5)
            if not long_:
                sblock(parts, (vd * 0.4 - 0.03, cy - 0.025, F), T(s * (r + vd * 0.8), y + cy / 2, zf), st(stone, rng), rng, drop=('-y', '+y'))
        y += cy
        k += 1
    voussoirs(parts, rng, r, spring, S, ytop, zf, F + 0.04, stone * 1.03, n=p.get('n_v', 11))
    # the core: two halves either side of the passage, the arch's curve carried through it (the vault)
    for sg in (-1, 1):
        pts = [(sg * (W / 2 - 0.02), -foot), (sg * r, -foot), (sg * r, spring)]
        for i in range(1, 12):
            a = (0.0 if sg > 0 else math.pi) + sg * (math.pi / 2) * (i / 12)
            pts.append((r * math.cos(a), spring + r * math.sin(a)))
        pts += [(0.0, spring + r), (0.0, HG - 0.02), (sg * (W / 2 - 0.02), HG - 0.02)]
        if sg > 0:
            pts.reverse()
        parts.append(Part(prism(pts, DG - F - 0.04, bevel=0.0), 'stone', mortar * 0.42, T(0, 0, -F / 2 - 0.02), cap='stone', jitter=0.0))
    # the portcullis drawn up (its teeth under the crown), in its slot behind the face
    zp = zf - F / 2 - 0.35
    bars = 9
    ylo = spring + r - 0.75
    for i in range(bars):
        x = -r * 0.9 + 2 * r * 0.9 * i / (bars - 1)
        yl = ylo - (0.22 if i % 2 == 0 else 0.1)
        hh = spring + r + 0.25 - yl
        parts.append(Part(box(0.1, hh, 0.1), 'wood', wood * 0.55 * (1 + rng(-0.1, 0.1)), T(x, yl + hh / 2, zp), jitter=0.0))
        parts.append(Part(lathe([(0.07, 0.0), (0.0, -0.22)], 4), 'iron', iron, T(x, yl, zp), jitter=0.0))
    for yy in (ylo + 0.12, ylo + 0.5):
        hw = math.sqrt(max(0.0, r * r - (yy - spring) ** 2)) if yy > spring else r
        parts.append(Part(box(2 * hw - 0.05, 0.09, 0.13), 'wood', wood * 0.5, T(0, yy, zp + 0.07), jitter=0.0))
    # the leaves swung back against the passage walls at its inner end
    for s in (-1, 1):
        lw, lh = r * 0.98, spring + r * 0.62
        xc = s * (r - 0.09)
        zc = -DG / 2 + 0.55 + lw / 2
        n_pl = 5
        for j in range(n_pl):
            zz = zc - lw / 2 + lw * (j + 0.5) / n_pl
            parts.append(Part(box(0.09, lh - 0.05 * (j % 2), lw / n_pl - 0.015), 'wood', wood * (1 + rng(-0.12, 0.12)), T(xc, lh / 2, zz), jitter=0.0))
        for yy in (0.5, lh * 0.5, lh - 0.5):
            parts.append(Part(box(0.03, 0.12, lw * 0.92), 'iron', iron * 0.8, T(xc - s * 0.06, yy, zc), jitter=0.0))
    # the machicolated gallery over the arch: corbels, a parapet stood out on them (the slots dark between), merlons
    gx = p.get('gallery', 2.9)
    gz = DG / 2 + 0.45
    yc = HG - 1.15
    nc = 6
    for i in range(nc):
        x = -gx + 2 * gx * i / (nc - 1)
        for j in range(3):
            d = 0.3 + 0.2 * j
            sblock(parts, (0.42, 0.33, d), T(x, yc + 0.17 + 0.33 * j, DG / 2 + d / 2 - 0.02), st(stone, rng), rng, drop=('-z',), chip=0.6)
    yg = yc + 1.0
    wall_parts(parts, rng, 2 * gx + 0.5, top - yg, 0.42, 0.48, 0.9, stone, mortar, lambda x: 99.0, -gx - 0.25, at=T(0, yg, gz + 0.2), sink=0.0)
    parts.append(Part(box(2 * gx + 0.4, 0.08, 0.5), 'stone', stone * 0.05, T(0, yg - 0.03, DG / 2 + 0.2), jitter=0.0))
    merlons(parts, rng, -gx - 0.25, gx + 0.25, top, gz + 0.2, 0.45, mh, 0.95, 0.5, stone, loops={1, 3}, shadow=False)
    for (a, b) in ((x0 + 0.04, -gx - 0.3), (gx + 0.3, W / 2 - 0.04)):
        merlons(parts, rng, a, b, top, zf, F, mh, 0.95, 0.5, stone, shadow=False)
    # the rear parapet, battlemented, one merlon lost
    wall_parts(parts, rng, W, ph + 0.25, 0.5, 0.5, 0.95, stone * 0.98, mortar, lambda x: 99.0, x0, at=T(0, HG - 0.25, -DG / 2 + 0.25), sink=0.0)
    merlons(parts, rng, x0 + 0.04, W / 2 - 0.04, top, -DG / 2 + 0.25, 0.5, mh, 0.95, 0.5, stone, broken={2}, fall_z=-DG / 2 + 1.1, fall_y=HG, shadow=False)
    flags(parts, rng, x0 + 0.02, W / 2 - 0.02, -DG / 2 + 0.5, DG / 2 - F, HG, stone, rows=4)
    # (E8c) the proxy keeps the passage open, the arch's curve through it (as the core): the dawn sun, low in the
    # north-north-east, shines through the gate onto the road (Low Ford's gatedawn left sun pool; a solid block shut it out)
    for sg in (-1, 1):
        pts = [(sg * W / 2, -foot), (sg * r, -foot), (sg * r, spring)]
        for i in range(1, 12):
            a = (0.0 if sg > 0 else math.pi) + sg * (math.pi / 2) * (i / 12)
            pts.append((r * math.cos(a), spring + r * math.sin(a)))
        pts += [(0.0, spring + r), (0.0, top), (sg * W / 2, top)]
        if sg > 0:
            pts.reverse()
        # (shadow_d: the block as deep as the KayKit gate's, not the passage's 5 m, so the slant reaches through)
        SHADOW.append((prism(pts, p.get('shadow_d', DG), bevel=0.0), T(0, 0, 0)))
    # (E8d) the battlements' teeth on the proxy itself, at its south edge: the front gallery's and merlons' own boxes
    # stood 1-2 m south of the 2.5 m proxy, floating, so the moon cast them as a toothed band beyond a lit stripe
    sd = p.get('shadow_d', DG)
    nt = max(2, int(round((W + 0.5) / 1.45)))
    wt = (W - 0.5 * (nt - 1)) / nt
    for i in range(nt):
        shadow_box(wt, mh, 0.5, T(-W / 2 + i * (wt + 0.5) + wt / 2, top + mh / 2, sd / 2 - 0.25))
    return parts


def ring(parts, rng, r, y0, H, ch, n, stone, F=0.5, slits=(), k0=0, arc=None):
    """A round tower's wall in courses from y0, H high: n tangent blocks a course, the joints broken course to course;
    slits: (angle, y) a loop through it (two narrow jambs, the dark behind) over two courses; arc: blocks only
    within this angle of south (the side every camera sees: the play camera looks north, as C01 s8a), the back a
    plain shell of the same stone (the triangle budget)."""
    if arc is not None:
        parts.append(Part(lathe([(r - 0.02, y0), (r - 0.02, y0 + H)], 10, cap0=False, cap1=False, a0=math.pi / 2 + arc, a1=2.5 * math.pi - arc, closed=False),
                          'stone', stone * 0.92, T(0, 0, 0), cyl=r, jitter=0.0))
    step = 2 * math.pi / n
    bw = 2 * r * math.tan(step / 2)
    y, k = y0, k0
    rows = []
    while y < y0 + H - 0.08:
        cy = min(ch * rng(0.92, 1.08), y0 + H - y)
        if y0 + H - (y + cy) < 0.2:
            cy = y0 + H - y
        rows.append((y, cy, k))
        y += cy
        k += 1
    for (y, cy, k) in rows:
        off = step / 2 if k % 2 else 0.0
        for i in range(n):
            a = i * step + off
            if arc is not None and abs(math.atan2(math.sin(a), math.cos(a))) > arc:
                continue
            sl = [s for s in slits if abs(math.atan2(math.sin(a - s[0]), math.cos(a - s[0]))) < step / 2 and s[1] - 0.05 <= y < s[1] + 0.95]
            t = st(stone, rng)
            at = R('Y', a) @ T(0, y + cy / 2, r - F / 2)
            if sl:
                jw = (bw - 0.16) / 2
                for s in (-1, 1):
                    sblock(parts, (jw - 0.02, cy - 0.02, F), at @ T(s * (jw / 2 + 0.08), 0, 0), t * 1.05, rng, drop=('-y', '+y'), chip=0.4)
                parts.append(Part(box(0.2, cy, 0.1), 'stone', stone * 0.05, at @ T(0, 0, -F / 2 - 0.02), jitter=0.0))
            else:
                sblock(parts, (bw + 0.02, cy - 0.025, F), at @ R('Y', rng(-0.01, 0.01)), t, rng, drop=('-y', '+y'), chip=0.5)
    return y0 + H


def cone_slates(parts, rng, re, ye, h, slate, sw=0.46, sl=0.66, vis=0.44, moss=0.0):
    """A conical roof of slates from the eave (radius re at ye) to the apex h over it: courses of thin slates, each
    lapping the one below, the joints broken, each slate its own tone (a few darker, a few pale), moss low down;
    a lead cap at the top."""
    L = math.hypot(re, h)
    phi = math.atan2(h, re)
    nr = int(L / vis)
    last = 0
    for i in range(nr):
        t = i * vis / L
        r = re * (1 - t)
        if r < 0.42:
            break
        last = i
        y = ye + h * t
        m = max(6, int(round(2 * math.pi * r / sw)))
        off = rng(0, 2 * math.pi / m)
        for j in range(m):
            a = off + 2 * math.pi * j / m + rng(-0.012, 0.012)
            w = 2 * math.pi * r / m * 1.08
            bm = box(w, 0.035, sl)
            bm.normal_update()
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.y < -0.9], context='FACES')
            q = rng()
            tone = 0.72 if q < 0.12 else (1.28 if q > 0.93 else 1.0)
            tn = slate * tone * (1 + rng(-0.1, 0.1))
            if moss and rng() < moss * (1 - t) ** 2:
                tn = tn.lerp(MOSS_SAGE * 0.75, rng(0.3, 0.6))
            at = R('Y', a) @ T(0, y, r) @ R('X', phi) @ T(0, 0.022 + 0.008 * (i % 2), sl / 2 - 0.03) @ R('Z', rng(-0.03, 0.03))
            parts.append(Part(bm, 'stone', tn, at, jitter=0.0))
    tt = (last + 1) * vis / L
    rc = max(0.42, re * (1 - tt)) + 0.12
    yc = ye + h * tt - 0.15
    parts.append(Part(lathe([(rc, yc - 0.15), (rc * 0.9, yc), (0.06, ye + h + 0.05)], 12), 'iron', slate * 0.65, T(0, 0, 0), smooth=True, jitter=0.0))


def arc_block(L, h, F, r, rng, bevel=0.03, chip=0.4, jag=0.006, drop=('-z',), smooth_face=False):
    """(E8 r2) A dressed block bent to a drum: L along the arc (at the outer face, radius r), h high, F deep (the
    outer face at local z +F/2); cut along its length so the bend is smooth (the drum's outline round, no tangent
    corners standing out course by course: the old rings' jagged silhouette), its arrises beveled, hand-jittered."""
    bm = stone_block(L, h, F, rng, bevel=bevel, chip=chip, jag=jag, drop=drop)
    if '-z' in drop:
        # its back bevels too (inside the wall: the triangle budget)
        bm.normal_update()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.5], context='FACES')
    cuts = max(1, int(L / 0.45))
    es = [e for e in bm.edges if e.calc_length() > 0.12 and abs((e.verts[1].co - e.verts[0].co).normalized().x) > 0.9]
    if es:
        bmesh.ops.subdivide_edges(bm, edges=es, cuts=cuts, use_grid_fill=True)
    rc = r - F / 2
    for v in bm.verts:
        x, z = v.co.x, v.co.z
        th = x / r
        rho = rc + z
        v.co.x, v.co.z = rho * math.sin(th), rho * math.cos(th) - rc
    bm.normal_update()
    if smooth_face:
        # (E8d) the face shaded smooth round the drum (its strips' flat normals stepped 6-9 degrees, staggered course
        # to course: a checkerboard of lit and shaded facets at 1:1), cut free of its flat arrises (their normals apart)
        front = []
        for f in bm.faces:
            c = f.calc_center_median()
            rad = Vector((c.x, 0.0, c.z + rc))
            ok = rad.length > 1e-6 and f.normal.dot(rad.normalized()) > 0.97
            f.smooth = ok
            if ok:
                front.append(f)
        fs = set(front)
        edges = [e for f in front for e in f.edges if any(g not in fs for g in e.link_faces) or len(e.link_faces) < 2]
        if edges:
            bmesh.ops.split_edges(bm, edges=list(set(edges)))
        bm.normal_update()
    return bm


def damp(stone, y, rng, wet=1.0, at=None):
    """(E8 r2) A drum's stone by its height (m over the kit floor): the lower metre dark and damp, greened in
    patches with moss, easing to the dry stone by 2.6 m; the top courses a touch paler (weathered).
    (E8d) at: the block's middle (game frame): the moss in the damp band (the lower 1.6 m) in patches across blocks
    (a noise, so a patch spans a few blocks), a green that holds under the dawn's mist; the rest damp-dark, a little green."""
    if y < 1.0:
        k = 0.56 + 0.12 * max(0.0, y)
        m = (0.5 - 0.3 * max(0.0, y)) * wet
    elif y < 2.6:
        t = (y - 1.0) / 1.6
        k, m = 0.68 + 0.32 * t, 0.2 * (1 - t) * wet
    else:
        k, m = 1.0 + 0.06 * min(1.0, (y - 2.6) / 8.0), 0.0
    c = stone * k
    if at is not None:
        if m > 0:
            band = 1.0 - smooth01(0.9, 1.7, y)
            patch = smooth01(0.36, 0.56, 0.5 + 0.7 * hnoise(at * 0.55, 61))
            c = c.lerp(MOSS_DARK * 1.25, m * 0.6)
            c = c.lerp(MOSS_WET, min(1.0, wet * band * patch * rng(0.6, 0.9)))
        return c
    if m > 0 and rng() < 0.75:
        c = c.lerp(MOSS_DARK * 1.25, m * rng(0.35, 1.0))
    return c


def arc_ring(parts, rng, r, y0, H, F, stone, at=Matrix.Identity(4), arc=None, chs=(0.44, 0.5, 0.56, 0.62, 0.7), ls=(0.55, 1.15),
             slits=(), top=False, wet=1.0, mortar=None):
    """(E8 r2) A round wall in courses from y0, H high, outer radius r, F deep: each course its own height (chs, a
    little varied), each block its own length (ls), the joints falling where they fall, course by course; arc: blocks
    only within this angle of south (+z: what every camera sees), the back a plain shell of the stone (the triangle
    budget); slits: (angle, y) a loop through two courses (two narrow jambs, the dark behind); top: the last course's
    tops kept (a wall-head seen from above)."""
    if arc is not None:
        parts.append(Part(lathe([(r - 0.03, y0), (r - 0.03, y0 + H)], 12, cap0=False, cap1=False, a0=math.pi / 2 + arc, a1=2.5 * math.pi - arc, closed=False),
                          'stone', damp(stone, y0 + H * 0.6, rng, 0.0) * 0.9, at, cyl=r, jitter=0.0))
    if mortar is not None:
        # (E8d) the bed of mortar behind the faces, 4.5 cm back: the joints read as recessed mortar, not the dark core
        # (rows for the grime rising from the foot)
        a0, a1 = (math.pi / 2 - arc, math.pi / 2 + arc) if arc is not None else (0.0, 2 * math.pi)
        ys = [y0] + [y for y in (0.0, 0.6, 1.3, 2.2, 3.4) if y0 + 0.2 < y < y0 + H - 0.2] + [y0 + H - 0.02]
        parts.append(Part(lathe([(r - 0.045, y) for y in ys], 20, cap0=False, cap1=False, a0=a0, a1=a1,
                                closed=arc is None), 'stone', mortar, at, cyl=r, jitter=0.0))
    rows, y = [], y0
    while y < y0 + H - 0.08:
        cy = min(chs[int(rng(0, len(chs) - 0.001))] * rng(0.96, 1.04), y0 + H - y)
        if y0 + H - (y + cy) < 0.25:
            cy = y0 + H - y
        rows.append((y, cy))
        y += cy
    for ci, (y, cy) in enumerate(rows):
        last = ci == len(rows) - 1
        a = rng(0, 2 * math.pi)
        end = a + 2 * math.pi - 0.02 / r
        while a < end - 1e-4:
            L = min(rng(*ls), (end - a) * r)
            if (end - a) * r - L < ls[0] * 0.6:
                L = (end - a) * r
            da = L / r
            ac = a + da / 2
            a += da
            if arc is not None and abs(math.atan2(math.sin(ac), math.cos(ac))) > arc:
                continue
            sl = [s for s in slits if abs(math.atan2(math.sin(ac - s[0]), math.cos(ac - s[0]))) * r < L / 2 + 0.05 and s[1] - 0.05 <= y < s[1] + 0.95]
            # (E8d) each block its own colour (+-7%), its faces one: flush (+-4 mm), smooth round the drum, few chips
            mid = at @ R('Y', ac) @ Vector((0.0, y + cy / 2, r))
            t = damp(stone, y + cy / 2, rng, wet, at=mid) * (1 + rng(-0.07, 0.07))
            # (E8d) the ends dropped too (the joint shows the mortar bed, not a block's end lit edge-on by a torch)
            drop = ('-z', '-y', '-x', '+x') if (top and last) else ('-z', '-y', '+y', '-x', '+x')
            jut = rng(-0.004, 0.004)
            base = at @ R('Y', ac) @ T(0, y + cy / 2, r - F / 2 + jut)
            if sl and L > 0.5:
                jw = (L - 0.2) / 2
                for s in (-1, 1):
                    parts.append(Part(arc_block(jw - 0.02, cy - 0.022, F, r, rng, bevel=0.016, chip=0.05, drop=('-z', '-y', '+y'), smooth_face=True), 'stone', t * 1.04,
                                      at @ R('Y', ac + s * (jw / 2 + 0.1) / r) @ T(0, y + cy / 2, r - F / 2), cap='stone', smooth='faces', jitter=0.0))
                parts.append(Part(box(0.22, cy, 0.1), 'stone', stone * 0.05, base @ T(0, 0, -F / 2 - 0.02), jitter=0.0))
            else:
                parts.append(Part(arc_block(L - 0.022, cy - 0.022, F, r, rng, bevel=0.016, chip=0.05, drop=drop, smooth_face=True), 'stone', t, base,
                                  cap='stone', smooth='faces', jitter=0.0))
    return y0 + H


def drum_merlons(parts, rng, r, y, F, stone, n, mh=0.9, at=Matrix.Identity(4), loops=(), lost=()):
    """(E8 r2) Battlements round a drum's parapet: n merlons (a block bent to the drum and a coping on it, a loop
    through some), the crenels' sills the parapet's own tops between; shadow teeth for the proxy."""
    step = 2 * math.pi / n
    mw = 2 * math.pi * r / n * 0.56
    a0 = rng(0, step)
    for i in range(n):
        if i in lost:
            continue
        ac = a0 + i * step
        hb = mh - 0.12
        if i in loops:
            hw = (mw - 0.14) / 2
            for s in (-1, 1):
                parts.append(Part(arc_block(hw, hb, F, r, rng, chip=0.2, drop=('-y',), smooth_face=True), 'stone', st(stone, rng),
                                  at @ R('Y', ac + s * (hw / 2 + 0.07) / r) @ T(0, y + hb / 2, r - F / 2), cap='stone', smooth='faces', jitter=0.0))
            parts.append(Part(box(0.15, hb * 0.86, 0.1), 'stone', stone * 0.06, at @ R('Y', ac) @ T(0, y + hb * 0.48, r - F * 0.75), jitter=0.0))
        else:
            parts.append(Part(arc_block(mw, hb, F, r, rng, chip=0.2, drop=('-y',), smooth_face=True), 'stone', st(stone, rng), at @ R('Y', ac) @ T(0, y + hb / 2, r - F / 2),
                              cap='stone', smooth='faces', jitter=0.0))
        cap = st(stone, rng) * 1.05
        if rng() < 0.45:
            cap = cap.lerp(MOSS_SAGE, rng(0.25, 0.55))
        parts.append(Part(arc_block(mw + 0.06, 0.12, F + 0.06, r + 0.03, rng, bevel=0.012, chip=0.3, drop=(), smooth_face=True), 'stone', cap,
                          at @ R('Y', ac) @ T(0, y + hb + 0.06, r + 0.03 - (F + 0.06) / 2), cap='stone', smooth='faces', jitter=0.0))
        shadow_box(mw, mh, F, at @ R('Y', ac) @ T(0, y + mh / 2, r - F / 2))


def tower(p):
    """(E8 r2) A round flanking tower after the Edwardian gatehouses (Conwy, Harlech, Beaumaris): a battered footing,
    the drum in courses of blocks bent to it (each course its own height, the joints falling where they fall), its
    lower metre dark and damp with moss, arrow loops; at the top a corbel table (a machicolated one, the slots dark
    between, if "machi") carrying a solid parapet stood out from the drum, battlements round it, a walk of flagstones
    inside; "turret": a stair turret at the back rising over the walk with its own battlements. No roof (round 1's
    cones read as witch hats: sky under a floating roof, light through the slates)."""
    rng = Rng(p['seed'])
    R0, Hd, foot = p.get('r', 2.95), p.get('h', 10.0), p.get('footing', 1.8)
    stone, mortar = hexlin(p['stone']), hexlin(p['mortar'])
    machi = p.get('machi', False)
    parts = []
    # the footing: battered, a chamfered weathering course over it
    arc_ring(parts, rng, R0 + 0.32, -foot, foot - 0.3, 0.7, stone * 0.92, arc=math.radians(120), chs=(0.5, 0.56, 0.62), wet=1.2, mortar=mortar * 0.8)
    n = 22
    for i in range(n):
        a = (i + rng(0.4, 0.6)) * 2 * math.pi / n
        if abs(math.atan2(math.sin(a), math.cos(a))) > math.radians(120):
            continue
        bw = 2 * math.pi * (R0 + 0.36) / n
        parts.append(Part(arc_block(bw - 0.03, 0.22, 0.48, R0 + 0.36, rng, chip=0.5, drop=('-y', '-z')), 'stone', damp(stone, 0.0, rng, 1.2) * 0.95,
                          R('Y', a) @ T(0, -0.2, R0 + 0.36 - 0.24) @ R('X', 0.55), cap='stone', jitter=0.0))
    slits = [(math.radians(a), y) for a, y in p.get('slits', [[-30, 2.2], [25, 5.4], [-5, 7.6]])]
    arc_ring(parts, rng, R0, -0.35, Hd + 0.35, 0.55, stone, arc=math.radians(115), slits=slits, mortar=mortar * 0.85)
    parts.append(Part(lathe([(R0 - 0.5, -foot), (R0 - 0.5, Hd + 0.1)], 12, cap0=False, cap1=False), 'stone', mortar * 0.3, T(0, 0, 0), jitter=0.0))
    # the corbel table and the parapet stood out on it
    # (E8d) the machicolation stood out 0.5 m (at 0.42 it read as a thin ledge in C04 A8)
    R1 = R0 + (0.5 if machi else 0.26)
    nc = 26 if machi else 30
    tiers = 3 if machi else 2
    yc = Hd - 0.3 * tiers - 0.02
    for i in range(nc):
        a = (i + 0.5) * 2 * math.pi / nc
        if abs(math.atan2(math.sin(a), math.cos(a))) > math.radians(125):
            continue
        for j in range(tiers):
            d = 0.2 + (R1 - R0 + 0.12) * (j + 1) / tiers
            sblock(parts, (0.3, 0.28, d), R('Y', a) @ T(0, yc + 0.15 + 0.3 * j, R0 + d / 2 - 0.12), damp(stone, 9.0, rng), rng, chip=0.6, drop=('-z',))
    # under the parapet between the corbels: the machicolation's slots open to the dark, or a soffit in shade
    parts.append(Part(lathe([(R1 - 0.02, Hd - 0.08), (R0 + 0.02, Hd - 0.08)], 26, cap0=False, cap1=False), 'stone', stone * (0.05 if machi else 0.4), T(0, 0, 0), jitter=0.0))
    ph = p.get('para', 1.05)
    arc_ring(parts, rng, R1, Hd - 0.08, ph + 0.08, 0.5, stone * 1.02, chs=(0.5, 0.56), ls=(0.7, 1.2), top=True, wet=0.0, mortar=mortar * 0.9)
    # its inner face (seen from the play camera, looking down into the tower): a plain shell of the stone
    parts.append(Part(lathe([(R1 - 0.5, Hd + ph), (R1 - 0.5, Hd - 0.1)], 24, cap0=False, cap1=False), 'stone', stone * 0.8, T(0, 0, 0), cyl=R1 - 0.5, jitter=0.0))
    ytop = Hd + ph
    drum_merlons(parts, rng, R1, ytop, 0.5, stone * 1.02, p.get('merlons', 11), loops=set(p.get('loops', [2, 7])), lost=set(p.get('lost', [])))
    # the walk: flagstones in two rings round a timber hatch
    ri = R1 - 0.5
    parts.append(Part(lathe([(ri, Hd - 0.12), (0.0, Hd - 0.12)], 20, cap0=False, cap1=False), 'stone', stone * 0.5, T(0, 0, 0), jitter=0.0))
    for (r0, r1, m) in ((0.7, ri * 0.55, 7), (ri * 0.55, ri - 0.02, 11)):
        off = rng(0, 6.28)
        for i in range(m):
            a = off + i * 2 * math.pi / m
            L = 2 * math.pi * (r0 + r1) / 2 / m - 0.04
            parts.append(Part(stone_block(L, 0.14, r1 - r0 - 0.04, rng, bevel=0.02, chip=0.5, drop=('-y',)), 'stone',
                              st(stone, rng, 0.12) * 0.86, R('Y', a) @ T(0, Hd - 0.05 + rng(-0.015, 0.0), (r0 + r1) / 2) @ R('Y', rng(-0.03, 0.03)), cap='stone', jitter=0.0))
    wood = hexlin(p.get('wood', '#6a5848'))
    for k in range(4):
        parts.append(Part(box(0.3, 0.06, 1.2), 'wood', wood * (1 + rng(-0.12, 0.12)), T(-0.45 + 0.3 * k, Hd + 0.0, 0.0), jitter=0.0))
    if p.get('turret'):
        # the stair turret at the back, rising over the walk: coursed, a doorway onto the walk, its own battlements
        ta, rt, ht = math.radians(p['turret'][0]), p['turret'][1], p['turret'][2]
        tc = R0 - rt * 0.55
        at = T(tc * math.sin(ta), 0, tc * math.cos(ta))
        arc_ring(parts, rng, rt, Hd - 0.1, ht + 0.1, 0.4, stone * 1.02, at=at, chs=(0.44, 0.5, 0.56), ls=(0.5, 0.9), top=True, wet=0.0, mortar=mortar * 0.9)
        parts.append(Part(lathe([(rt - 0.38, Hd + ht), (0.0, Hd + ht)], 12, cap0=False, cap1=False), 'stone', stone * 0.55, at, jitter=0.0))
        door_a = math.atan2(-math.sin(ta), -math.cos(ta))
        parts.append(Part(box(0.62, 1.55, 0.1), 'stone', stone * 0.04, at @ R('Y', door_a) @ T(0, Hd + 0.78, rt + 0.01), jitter=0.0))
        drum_merlons(parts, rng, rt, Hd + ht, 0.36, stone * 1.02, 5, mh=0.7, at=at)
        SHADOW.append((lathe([(rt, Hd), (rt, Hd + ht)], 8), at))
    SHADOW.append((lathe([(R0 + 0.32, -foot), (R0, 0.4), (R0, Hd - 0.6), (R1, Hd), (R1, ytop)], 12), Matrix.Identity(4)))
    return parts


# --------------------------------------------------------------- the far castle --

def glow_win(parts, at, w, h, warm):
    """A lit window (the far castle): a thin pane stood proud of the face, flagged to glow (OwnProps' far material)."""
    parts.append(Part(box(w, h, 0.1), 'glow', warm, at, jitter=0.0))


def far_block(parts, rng, sx, sy, sz, at, stone, k=0.06):
    parts.append(Part(box(sx, sy, sz), 'stone', st(stone, rng, k), at, cap='stone', jitter=0.0))


def far_merlons(parts, rng, x0, x1, y, at, depth, stone, mw=0.9, gap=0.7, mh=0.9):
    n = max(2, int(round((x1 - x0 + gap) / (mw + gap))))
    w = (x1 - x0 - gap * (n - 1)) / n
    for i in range(n):
        far_block(parts, rng, w, mh, depth, at @ T(x0 + i * (w + gap) + w / 2, y + mh / 2, 0), stone, 0.04)


def far_wall(parts, rng, a, b, h, th, stone):
    """A curtain wall from a to b ([x, z]), h high, a string course under its battlements on the outer edge."""
    a, b = Vector((a[0], 0, a[1])), Vector((b[0], 0, b[1]))
    L = (b - a).length
    d = (b - a).normalized()
    at = T(*((a + b) / 2)) @ R('Y', math.atan2(d.x, d.z) - math.pi / 2)
    far_block(parts, rng, L, h, th, at @ T(0, h / 2, 0), stone)
    far_block(parts, rng, L, 0.5, th + 0.4, at @ T(0, h - 1.2, 0), stone * 0.9)
    far_merlons(parts, rng, -L / 2 + 0.3, L / 2 - 0.3, h, at @ T(0, 0, th / 2 - 0.3), 0.6, stone)


def far_tower(parts, rng, x, z, r, h, stone, slate, roof=0.0, crenel=False, segs=12, wins=(), warm=None):
    parts.append(Part(lathe([(r * 1.12, 0.0), (r, 2.0), (r, h)], segs, cap0=False), 'stone', st(stone, rng), T(x, 0, z), jitter=0.0))
    if roof > 0:
        parts.append(Part(lathe([(r * 1.25, h - 0.5), (0.0, h + roof)], segs), 'stone', slate * (1 + rng(-0.06, 0.06)), T(x, 0, z), jitter=0.0))
        parts.append(Part(lathe([(0.08, h + roof - 0.3), (0.0, h + roof + 2.2)], 4, cap0=False), 'iron', slate * 0.6, T(x, 0, z), jitter=0.0))
    else:
        parts.append(Part(lathe([(r * 1.12, h - 0.8), (r * 1.12, h)], segs), 'stone', stone * 0.95, T(x, 0, z), jitter=0.0))
    if crenel:
        n = max(6, int(2 * math.pi * r * 1.12 / 1.7))
        for i in range(n):
            far_block(parts, rng, 0.9, 0.95, 0.5, T(x, 0, z) @ R('Y', 2 * math.pi * i / n) @ T(0, h + 0.47, r * 1.12 - 0.25), stone, 0.04)
    for (a, y, w, hh) in wins:
        glow_win(parts, T(x, 0, z) @ R('Y', math.radians(a)) @ T(0, y, r + 0.01), w, hh, warm)


def gable_roof(parts, at, l, d, h, y, tint, stone):
    rf = bmesh.new()
    a = [rf.verts.new(c) for c in ((-l / 2 - 0.5, y, -d / 2 - 0.6), (l / 2 + 0.5, y, -d / 2 - 0.6), (l / 2 + 0.5, y, d / 2 + 0.6), (-l / 2 - 0.5, y, d / 2 + 0.6),
                                  (-l / 2 - 0.5, y + h, 0), (l / 2 + 0.5, y + h, 0))]
    rf.faces.new((a[0], a[1], a[5], a[4]))
    rf.faces.new((a[2], a[3], a[4], a[5]))
    rf.normal_update()
    _outward(rf)
    parts.append(Part(rf, 'stone', tint, at, jitter=0.0))
    for s in (-1, 1):
        g = bmesh.new()
        gv = [g.verts.new((s * l / 2, yy, z)) for yy, z in ((y, -d / 2), (y, d / 2), (y + h - 0.3, 0))]
        g.faces.new(gv if s > 0 else list(reversed(gv)))
        g.normal_update()
        parts.append(Part(g, 'stone', stone, at, jitter=0.0))


def castle(p):
    """(E8) The far castle on its hill north of the Waystation (C01 s8a, 265 m off; one merged low mesh on the props
    atlas, no shadow): the keep under the gold lamp (its lit window high on the south face, the preset's origin at
    the lamp's x, z), its corbelled parapet and corner bartizans with cones, a pyramid slate roof and a chimney; the
    curtain with round corner towers under slate cones and a twin-towered gatehouse; a hall's steep roof over the
    bailey with lit windows; a slender tower to the west. y 0: the hilltop (the curtain's foot)."""
    rng = Rng(p['seed'])
    stone, slate = hexlin(p['stone']), hexlin(p['slate'])
    warm = hexlin(p.get('warm', '#ffb060'))
    parts = []
    ly = p['lamp_y']
    kw, kh = 13.0, p.get('keep_h', 38.0)
    kz = -0.5 - kw / 2
    far_block(parts, rng, kw, kh, kw, T(0, kh / 2, kz), stone)
    for (y, k) in ((kh * 0.32, 0.9), (kh * 0.66, 0.95)):
        far_block(parts, rng, kw + 0.3, 0.45, kw + 0.3, T(0, y, kz), stone * k)
    for x in (-kw / 2 + 0.8, kw / 2 - 0.8):
        far_block(parts, rng, 1.6, kh - 1, 0.6, T(x, (kh - 1) / 2, kz + kw / 2 + 0.25), stone * 0.97)
    far_block(parts, rng, kw + 1.0, 1.4, kw + 1.0, T(0, kh + 0.3, kz), stone * 1.03)
    for s in range(4):
        far_merlons(parts, rng, -kw / 2 - 0.2, kw / 2 + 0.2, kh + 1.0, T(0, 0, kz) @ R('Y', s * math.pi / 2) @ T(0, 0, kw / 2 + 0.2), 0.6, stone, mw=1.0, gap=0.75, mh=1.1)
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (kw / 2 + 0.3), kz + sz * (kw / 2 + 0.3)
            parts.append(Part(lathe([(0.2, kh - 3.0), (1.5, kh - 1.0), (1.5, kh + 2.6)], 10), 'stone', st(stone, rng), T(cx, 0, cz), jitter=0.0))
            parts.append(Part(lathe([(1.75, kh + 2.5), (0.0, kh + 7.5)], 10), 'stone', slate, T(cx, 0, cz), jitter=0.0))
    pr = bmesh.new()
    hw = kw / 2 - 0.7
    v = [pr.verts.new((x, kh + 0.6, z)) for x, z in ((-hw, -hw), (hw, -hw), (hw, hw), (-hw, hw))]
    ap = pr.verts.new((0, kh + 0.6 + p.get('keep_roof', 9.0), 0))
    for i in range(4):
        pr.faces.new((v[i], v[(i + 1) % 4], ap))
    pr.normal_update()
    _outward(pr)
    parts.append(Part(pr, 'stone', slate * 0.95, T(0, 0, kz), jitter=0.0))
    far_block(parts, rng, 1.1, 5.5, 1.1, T(hw * 0.45, kh + 4.2, kz - hw * 0.3), stone * 0.9)
    # its windows: the lamp's (lit, high on the south face, a smaller light over it), others lit lower, a few dark
    zf = kz + kw / 2 + 0.02
    glow_win(parts, T(0, ly - 0.3, zf), 1.3, 2.6, warm)
    one = p.get('one_lamp', False)  # (E8 r2) every window dark but the lamp's (the frame's one point of gold)
    for (x, y, lit) in ((-3.6, ly - 9.5, True), (3.4, ly - 9.5, False), (-3.4, ly - 17.0, False), (3.8, ly - 18.0, True), (-3.6, ly, False), (3.6, ly, False)):
        if lit and not one:
            glow_win(parts, T(x, y, zf), 0.9, 1.7, warm * rng(0.6, 0.85))
        else:
            parts.append(Part(box(0.85, 1.7, 0.1), 'stone', stone * 0.1, T(x, y, zf), jitter=0.0))
    wh = p.get('wall_h', 16.0)
    zs, xw, xe, zb = 22.0, -34.0, 38.0, -40.0
    far_wall(parts, rng, (xw, zs), (-4.5, zs), wh, 3.0, stone)
    far_wall(parts, rng, (5.5, zs), (xe, zs), wh, 3.0, stone)
    far_wall(parts, rng, (xe, zs), (xe + 4, zb), wh + 1, 3.0, stone * 0.92)
    far_wall(parts, rng, (xw - 3, zb), (xw, zs), wh + 1, 3.0, stone * 0.92)
    far_wall(parts, rng, (xw - 3, zb), (xe + 4, zb), wh + 2, 3.0, stone * 0.85)
    for gx in (-6.0, 7.0):
        far_tower(parts, rng, gx, zs + 1.4, 3.4, wh + 6.0, stone, slate, crenel=True)
    far_block(parts, rng, 10.0, 6.0, 4.0, T(0.5, wh + 2.0, zs + 0.5), stone)
    far_merlons(parts, rng, -3.5, 4.5, wh + 5.0, T(0.5, 0, zs + 2.2), 0.6, stone)
    if not one:
        glow_win(parts, T(0.5, wh + 2.4, zs + 2.55), 0.8, 1.4, warm * 0.75)
    far_tower(parts, rng, xw, zs, 4.2, wh + 9.0, stone, slate, roof=9.5, wins=[] if one else [(0, wh + 5.0, 0.7, 1.3)], warm=warm * 0.7)
    far_tower(parts, rng, xe, zs, 4.4, wh + 8.0, stone, slate, roof=10.0)
    far_tower(parts, rng, xe + 4, zb, 4.6, wh + 13.0, stone * 0.92, slate, roof=11.0)
    far_tower(parts, rng, xw - 3, zb, 4.2, wh + 11.0, stone * 0.92, slate, roof=10.0)
    far_tower(parts, rng, -21.0, -18.0, 3.0, p.get('west_h', 36.0), stone * 0.96, slate, roof=12.0, wins=[] if one else [(10, 30.0, 0.6, 1.2)], warm=warm * 0.8)
    hx, hz, hl, hd, hh = 23.0, -6.0, 18.0, 9.0, 20.0
    far_block(parts, rng, hl, hh, hd, T(hx, hh / 2, hz), stone * 0.97)
    gable_roof(parts, T(hx, 0, hz), hl, hd, 7.5, hh, slate * 0.9, stone * 0.95)
    for i in range(5):
        if i != 2 and not one:
            glow_win(parts, T(hx - hl / 2 + 2.2 + i * (hl - 4.4) / 4, hh - 4.0, hz + hd / 2 + 0.02), 0.85, 2.2, warm * rng(0.5, 0.8))
    far_block(parts, rng, 1.2, 4.0, 1.2, T(hx + hl / 2 - 2.5, hh + 7.0, hz), stone * 0.88)
    far_block(parts, rng, 14.0, 19.0, 8.0, T(-14.0, 9.5, -2.0), stone * 0.94)
    gable_roof(parts, T(-14.0, 0, -2.0), 14.0, 8.0, 5.0, 19.0, slate * 0.85, stone * 0.94)
    if not one:
        glow_win(parts, T(-17.0, 15.5, 2.02), 0.8, 1.5, warm * 0.6)
    if p.get('ridge'):
        # (E8 r2) the ridge it stands on: a crest under the curtain's foot, falling away to either side and steeply
        # toward the viewer, its foot lift metres under the castle (the mesh's y 0, so the bake's ground is the foot)
        lift = p['ridge']
        for pt in parts:
            pt.at = T(0, lift, 0) @ pt.at
        parts.append(ridge(lift, p.get('ridge_w', 320.0), hexlin(p.get('ridge_tint', '#3a3c34')), p['seed']))
        if p.get('ridge_trees', True):
            ridge_trees(parts, rng, lift, p.get('ridge_w', 320.0), hexlin(p.get('ridge_tint', '#3a3c34')) * Vector((0.5, 0.62, 0.5)), p['seed'])
    return parts


def ridge_h(x, z, lift, w, seed):
    """(E8 r2) The far ridge's height at (x, z) (local, the castle's frame): the crest at lift under the curtain
    (|x| < 50) falling away to the flanks and in a cliff toward the viewer (+z), lumped by noise, its foot at y 0."""
    ax = abs(x)
    c = lift - 1.0 - max(0.0, ax - 48.0) ** 1.25 * (lift / (w - 48.0) ** 1.25)
    c -= max(0.0, z - 30.0) ** 1.6 * 0.9 + max(0.0, -48.0 - z) ** 1.3 * 0.6
    c += 7.0 * hnoise(Vector((x * 0.03, 0.0, z * 0.03)), seed) * min(1.0, ax / 60.0 + max(0.0, z - 30.0) / 20.0)
    return max(0.0, c)


def ridge(lift, w, tint, seed):
    """(E8 r2) The far castle's ridge: a height grid x in [-w, w], z in [-150, 75] (ridge_h)."""
    nx, nz = 56, 20

    def fn(u, v):
        x, z = -w + 2 * w * u, -150.0 + 225.0 * v
        return Vector((x, ridge_h(x, z, lift, w, seed), z))
    return Part(grid(nx, nz, fn), 'stone', tint, T(0, 0, 0), jitter=0.0)


def ridge_trees(parts, rng, lift, w, tint, seed, x0=44.0, x1=150.0):
    """(E8d) A ragged line of firs along the ridge's crest, either side of the castle (|x| from x0 to x1), two or
    three deep from its brow (z 8-31): the smooth dome's skyline broken (C01 s8a). Each a pair of stacked
    five-sided cones, 6-15 m, dark and a little green; clumps and gaps, a few taller."""
    for sx in (-1, 1):
        x = x0 + rng(0.0, 3.0)
        while x < x1:
            gap = rng() < 0.12
            x += rng(5.0, 11.0) if gap else rng(1.8, 4.2)
            for row in range(3 if rng() < 0.5 else 2):
                z = 31.0 - row * rng(5.0, 9.0) + rng(-1.5, 1.5)
                xx = sx * (x + rng(-1.2, 1.2))
                h = rng(6.0, 11.5) * (1.35 if rng() < 0.12 else 1.0) * (1.0 - 0.3 * max(0.0, (x - 110.0) / 40.0))
                r = h * rng(0.2, 0.27)
                y = ridge_h(xx, z, lift, w, seed) - 0.6
                tn = tint * rng(0.8, 1.15)
                turn = R('Y', rng(0, 1.25))
                parts.append(Part(lathe([(r, 0.0), (0.0, h * 0.68)], 5, cap0=False), 'stone', tn, T(xx, y, z) @ turn, jitter=0.0))
                parts.append(Part(lathe([(r * 0.68, h * 0.42), (0.0, h)], 5, cap0=False), 'stone', tn * 1.05, T(xx, y, z) @ turn, jitter=0.0))


# ------------------------------------------------- (E8 later) beyond the gate, the camp's ground --

def zone_height(path, size, res):
    """A zone's ground height at world (x, z), bilinear over its heights.bin (res x res floats, size metres)."""
    import array
    a = array.array('f')
    with open(os.path.join(ROOT, path), 'rb') as f:
        a.frombytes(f.read())
    cell = size / (res - 1)

    def h(x, z):
        u, v = (x + size / 2) / cell, (z + size / 2) / cell
        i, j = max(0, min(res - 2, int(u))), max(0, min(res - 2, int(v)))
        fu, fv = min(1.0, max(0.0, u - i)), min(1.0, max(0.0, v - j))

        def g(ii, jj):
            return a[jj * res + ii]
        return (g(i, j) * (1 - fu) + g(i + 1, j) * fu) * (1 - fv) + (g(i, j + 1) * (1 - fu) + g(i + 1, j + 1) * fu) * fv
    return h


def drape(ob, d):
    """(E8 later) A ground-hugging preset laid over the zone's ground: each vertex raised by the ground's height at its
    world place over the height at the preset's origin (d: heights, size, res, at [x, z]; the preset placed unturned)."""
    h = zone_height(d['heights'], d['size'], d['res'])
    ax, az = d['at']
    h0 = h(ax, az)
    for v in ob.data.vertices:
        # Blender frame: x is the world's x, -y the world's z, z up
        v.co.z += h(ax + v.co.x, az - v.co.y) - h0
    ob.data.update()


def beyond_house(p):
    """(E8 later) What the open gate shows (C04 A8, dawn): a stone house up the road beyond it, its front to the road,
    a lit window by its near corner and a door, shutters, quoins and a plinth; a shingled roof and a chimney. Seen
    only through the arch at about 60 m, in the dawn mist: plain boxes on the props atlas, no shadow. The origin: the
    front's foot at its middle; the body runs down into the slope behind (the ground rises 0.45 m a metre)."""
    rng = Rng(p['seed'])
    stone, wood, roof = hexlin(p['stone']), hexlin(p['wood']), hexlin(p['roof'])
    warm = hexlin(p['warm'])
    w, d, eave = p['w'], p['d'], p['eave']
    parts = []
    sink = 3.2
    parts.append(Part(box(w, eave + sink, d), 'stone', st(stone, rng, 0.03), T(0, (eave - sink) / 2, -d / 2), cap='stone', jitter=0.0))
    parts.append(Part(box(w + 0.12, 0.45, d + 0.12), 'stone', stone * 0.8, T(0, 0.12, -d / 2), cap='stone', jitter=0.0))
    for sx in (-1, 1):
        for k in range(int(eave / 0.42)):
            lw = 0.5 if k % 2 == 0 else 0.32
            parts.append(Part(box(lw, 0.36, 0.06), 'stone', st(stone * 1.12, rng, 0.06), T(sx * (w / 2 - lw / 2 + 0.03), 0.4 + k * 0.42, 0.03), jitter=0.0))
    gable_roof(parts, T(0, 0, -d / 2), w, d, p['pitch'], eave, roof, stone)
    parts.append(Part(box(0.7, 2.2, 0.7), 'stone', stone * 0.85, T(w / 2 - 0.9, eave + 1.6, -d / 2 - 0.6), cap='stone', jitter=0.0))
    # the lit window near the left corner, its frame, a mullion cross in front of the glow, the shutters open
    wx, wy, ww, wh = p['win']
    glow_win(parts, T(wx, wy, 0.03), ww, wh, warm)
    for (sx_, sy_, px_, py_) in ((ww + 0.16, 0.1, 0, wh / 2 + 0.05), (ww + 0.2, 0.12, 0, -wh / 2 - 0.06), (0.08, wh, -ww / 2 - 0.04, 0), (0.08, wh, ww / 2 + 0.04, 0)):
        parts.append(Part(box(sx_, sy_, 0.1), 'wood', wood * 0.8, T(wx + px_, wy + py_, 0.06), jitter=0.0))
    parts.append(Part(box(0.05, wh, 0.05), 'wood', wood * 0.5, T(wx, wy, 0.1), jitter=0.0))
    parts.append(Part(box(ww, 0.05, 0.05), 'wood', wood * 0.5, T(wx, wy + 0.05, 0.1), jitter=0.0))
    for sx in (-1, 1):
        parts.append(Part(box(ww / 2 + 0.04, wh + 0.04, 0.04), 'wood', wood * rng(0.85, 1.0), T(wx + sx * (ww * 0.5 + 0.08 + ww * 0.24), wy, 0.18) @ R('Y', sx * 1.2), jitter=0.0))
    # the door, set back, its lintel and step
    dx = p['door']
    parts.append(Part(box(1.0, 2.0, 0.08), 'wood', wood * 0.7, T(dx, 1.0, 0.0), jitter=0.0))
    parts.append(Part(box(1.3, 0.22, 0.2), 'wood', wood * 0.6, T(dx, 2.1, 0.05), jitter=0.0))
    parts.append(Part(box(1.2, 0.12, 0.45), 'stone', stone * 0.9, T(dx, 0.06, 0.2), jitter=0.0))
    return parts


def beyond_lamp(p):
    """(E8 later) A road lamp up the road beyond the gate (C04 A8, seen through the arch): a timber post, an arm out
    over the road (+x) braced from below, an iron lantern hanging from it, its panes lit (the glow mesh). No shadow."""
    wood, iron, warm = hexlin(p['wood']), hexlin(p['iron']), hexlin(p['warm'])
    H, arm = p['h'], p['arm']
    parts = [Part(box(0.15, H + 0.4, 0.15), 'wood', wood, T(0, (H - 0.4) / 2, 0), cap='endgrain', jitter=0.0),
             Part(box(arm + 0.1, 0.11, 0.11), 'wood', wood * 0.9, T(arm / 2, H - 0.08, 0), jitter=0.0),
             Part(box(0.07, 0.62, 0.07), 'wood', wood * 0.85, T(0.24, H - 0.35, 0) @ R('Z', 0.75), jitter=0.0)]
    lx, ly = arm - 0.08, H - 0.55
    parts.append(Part(box(0.02, 0.2, 0.02), 'iron', iron, T(lx, H - 0.24, 0), jitter=0.0))
    parts.append(Part(box(0.3, 0.05, 0.3), 'iron', iron, T(lx, ly + 0.2, 0), jitter=0.0))
    parts.append(Part(box(0.16, 0.08, 0.16), 'iron', iron, T(lx, ly + 0.27, 0), jitter=0.0))
    parts.append(Part(box(0.26, 0.04, 0.26), 'iron', iron, T(lx, ly - 0.2, 0), jitter=0.0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(Part(box(0.03, 0.4, 0.03), 'iron', iron, T(lx + sx * 0.12, ly, sz * 0.12), jitter=0.0))
    parts.append(Part(box(0.21, 0.36, 0.21), 'glow', warm, T(lx, ly, 0), jitter=0.0))
    return parts


def pebble(r, rng, flat=0.55, el=1.0):
    """(E8 later) A field stone: a lumpy low icosphere, squashed (flat), drawn out along x (el), its foot sunk (80
    triangles)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    sx, sz = rng(0.8, 1.25) * el, rng(0.75, 1.15)
    sd = rng(0, 100)
    for v in bm.verts:
        c = v.co.copy()
        k = 1.0 + 0.22 * hnoise(c * 1.7 + Vector((sd, 0, 0)), int(sd))
        v.co = Vector((c.x * sx * k * r, c.y * flat * k * r, c.z * sz * k * r))
        if v.co.y < 0:
            v.co.y *= 0.4
    bm.normal_update()
    return bm


def stick(L, r, rng, segs=5):
    """(E8 later) A stick along local x (a short tube, its ends cut)."""
    bm = lathe([(r, -L / 2), (r * rng(0.75, 0.95), L / 2)], segs)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Z'))
    return bm


def flake(r, rng, n=6):
    """(E8 later) A flat ragged scrap (ash, charcoal) lying on the ground."""
    bm = bmesh.new()
    c = bm.verts.new((0, 0.012, 0))
    rim = [bm.verts.new((math.cos(2 * math.pi * k / n) * r * rng(0.55, 1.15), 0.008, math.sin(2 * math.pi * k / n) * r * rng(0.55, 1.15))) for k in range(n)]
    for k in range(n):
        bm.faces.new((c, rim[(k + 1) % n], rim[k]))
    bm.normal_update()
    return bm


def camp_ground(p):
    """(E8 later) The camp's ground dressing round the fire (origin: the fire's middle): field stones at the camp's
    edge and by the paths' mouths, a kindling pile by the short log and loose twigs, ash and charcoal scraps round the
    ring, charred brands. All low (stones <= 0.2 m out of the ground), no colliders, no shadow; draped over the
    ground (main(), "drape")."""
    rng = Rng(p['seed'])
    stone, bark = hexlin(p['stone']), hexlin(p['bark'])
    ash, char = hexlin(p['ash']), hexlin(p['char'])
    parts = []
    for sp_ in p['stones']:
        # (E8 later r2) [x, z, r, flat, el]: each its own size, flatness and length (judge: stamped, all round and alike)
        x, z, r = sp_[:3]
        t = stone * rng(0.75, 1.15)
        parts.append(Part(pebble(r, rng, *sp_[3:5]), 'stone', Vector((t.x, t.y * rng(0.97, 1.03), t.z * rng(0.94, 1.04))), T(x, r * 0.12, z) @ R('Y', rng(0, 6.28)), smooth=True, jitter=0.0))
    kx, kz, ka = p['kindling']
    at = T(kx, 0, kz) @ R('Y', ka)
    for i in range(7):
        L, r = rng(0.45, 0.7), rng(0.022, 0.04)
        y = r + (0.05 if i >= 4 else 0.0) + (0.04 if i == 6 else 0.0)
        parts.append(Part(stick(L, r, rng), 'bark', bark * rng(0.8, 1.1), at @ T(rng(-0.06, 0.06), y, -0.12 + (i % 4) * 0.075 + rng(-0.02, 0.02)) @ R('Y', rng(-0.15, 0.15)), jitter=0.0))
    for (x, z, a, L) in p['twigs']:
        parts.append(Part(stick(L, rng(0.012, 0.022), rng, 4), 'bark', bark * rng(0.7, 1.0), T(x, 0.015, z) @ R('Y', a), jitter=0.0))
    r0, r1 = p['ash_r']
    for i in range(p['ash_n']):
        a = rng(0, 6.28)
        rr = r0 + (r1 - r0) * rng() ** 1.6
        dark = rng() < 0.45
        parts.append(Part(flake(rng(0.04, 0.11) if dark else rng(0.07, 0.17), rng), 'stone', (char if dark else ash) * rng(0.8, 1.2), T(math.cos(a) * rr, 0.004 * (i % 3), math.sin(a) * rr) @ R('Y', rng(0, 6.28)), jitter=0.0))
    for (x, z, a, L) in p['brands']:
        parts.append(Part(stick(L, 0.035, rng, 5), 'endgrain', char * 1.3, T(x, 0.03, z) @ R('Y', a), jitter=0.0))
    return parts


KINDS = {'pylon': pylon, 'bedroll_open': bedroll_open, 'bedroll_rolled': bedroll_rolled, 'pack': pack, 'chest': chest,
         'crate': crate, 'barrel': barrel, 'log': log, 'wagon': wagon,
         'wall': wall, 'pillar': pillar, 'rubble': rubble, 'banner': banner, 'table': table, 'chair': chair, 'bed': bed,
         'fence': fence, 'grave': grave, 'gravestone': gravestone, 'marker': marker, 'crypt': crypt,
         'stall': stall, 'notice_board': notice_board, 'handcart': handcart, 'trough': trough, 'market_heap': market_heap, 'brazier': brazier,
         'curtain': curtain, 'gatehouse': gatehouse, 'tower': tower, 'castle': castle,
         'beyond_house': beyond_house, 'beyond_lamp': beyond_lamp, 'camp_ground': camp_ground}


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
    PRESETS.update(data)
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
        GRIME['far'] = p.get('far', False)
        GRIME['runs'], GRIME['run_top'] = p.get('runs'), p.get('run_top', 0.0)
        GRIME['base'], GRIME['ring'] = p.get('base_dark', 0.0), p['kind'] == 'tower'
        OLD.clear()
        OLD.update(p.get('old', {}))
        SHADOW.clear()
        parts = KINDS[p['kind']](p)
        if p.get('dress'):
            parts = dress(parts, p['dress'], p['seed'])
        ob = finish(name, parts, mat, p['seed'])
        obs = [ob]
        while len(ob.data.materials) > 1:
            # the last extra material's faces split off as <name>_<material> (cloth, glow)
            k = len(ob.data.materials) - 1
            mname = ob.data.materials[k].name.split('.')[0]
            have = set(bpy.context.scene.collection.objects)
            bpy.ops.object.select_all(action='DESELECT')
            ob.select_set(True)
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            ob.active_material_index = k
            bpy.ops.object.material_slot_select()
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            cl = [o for o in bpy.context.scene.collection.objects if o not in have and o.type == 'MESH'][0]
            cl.name = name + '_' + mname
            keep = cl.data.materials[k]
            cl.data.materials.clear()
            cl.data.materials.append(keep)
            ob.data.materials.pop(index=k)
            for pl in cl.data.polygons:
                pl.material_index = 0
            obs.append(cl)
        if SHADOW:
            # (E8) the shadow proxy: its boxes merged, one mesh (OwnProps: shadows only; the preset's own meshes cast none)
            sb = bmesh.new()
            for bm_, at_ in SHADOW:
                bm_.transform(G2B @ at_)
                tmp = bpy.data.meshes.new('tmp')
                bm_.to_mesh(tmp)
                sb.from_mesh(tmp)
                bpy.data.meshes.remove(tmp)
                bm_.free()
            if p.get('shadow_floor'):
                # (E8c) the proxy stands on the piece's floor, its footing cut off: where the ground rises under the wall
                # (Low Ford's gate on its slope; the ground casts no shadow) a sunk footing cast the hill's shadow over
                # the road the low dawn sun grazes, which the KayKit piece, stood on the floor, never did
                for v in sb.verts:
                    v.co.z = max(v.co.z, 0.0)
            if p.get('shadow_h'):
                # (E8 r2) the proxy squashed to this height (its teeth kept): the shadow the KayKit piece cast, so the
                # moon's falls short of the road she walks and the dawn's sun pools stay lit (the piece stands taller)
                # (E8c) shadow_keep: the proxy stands true up to this height (the gatehouse's passage, its arch), squashed above
                zt, zk = max(v.co.z for v in sb.verts), p.get('shadow_keep', 0.0)
                if zt > p['shadow_h']:
                    for v in sb.verts:
                        if v.co.z > zk:
                            v.co.z = zk + (v.co.z - zk) * (p['shadow_h'] - zk) / (zt - zk)
            bmesh.ops.triangulate(sb, faces=sb.faces[:])
            sme = bpy.data.meshes.new(name + '_shadow')
            sb.to_mesh(sme)
            sb.free()
            sme.materials.append(mat)
            so = bpy.data.objects.new(name + '_shadow', sme)
            bpy.context.scene.collection.objects.link(so)
            obs.append(so)
        if p.get('far'):
            # (E8) the far castle: one mesh, no LOD, named for OwnProps' far material
            ob.name = name + '_far'
        meta = {'tris': tris(ob)}
        if p.get('lod_m'):
            meta['lod_m'] = p['lod_m']  # (E8 r2) where its LOD1 takes over (OwnProps.Piece; the default 22 m)
        if SHADOW:
            meta['tris_shadow'] = tris(obs[-1])
        for o in obs[1:]:
            if o.name.endswith(('_cloth', '_glow')):
                meta['tris_' + o.name.rsplit('_', 1)[1]] = tris(o)
        if p.get('no_shadow'):
            meta['no_shadow'] = True  # (E8 later) OwnProps casts no shadow from it (cheap dressing, backdrops)
        if p['kind'] == 'log':
            meta['axis'] = [round(p['r'] * 0.85, 4), p['r']]  # the axis's height and the bark's radius (OwnProps lays logs by it)
        if p.get('drape'):
            drape(ob, p['drape'])
            for o in obs[1:]:
                drape(o, p['drape'])
        if meta['tris'] > 1000 and not p.get('far') and not p.get('no_lod'):
            lo = lod1(ob, p.get('lod1', 0.45))
            obs.insert(1, lo)
            meta['tris_lod1'] = tris(lo)
        if p['kind'] == 'notice_board':
            # (E9d) the notices: their own mesh and material ("paper": OwnProps gives it notice_paper.png)
            pm = bpy.data.materials.get('paper') or bpy.data.materials.new('paper')
            pa = notice_paper_mesh(name + '_paper', pm)
            obs.append(pa)
            meta['tris_paper'] = tris(pa)
        if p['kind'] == 'trough':
            wm = bpy.data.materials.get('water') or bpy.data.materials.new('water')
            obs.append(trough_water_mesh(name + '_water', wm, p))
        bb = [B2G @ Vector(c) for c in ob.bound_box]
        meta['box'] = [round(min(v[i] for v in bb), 3) for i in range(3)] + [round(max(v[i] for v in bb), 3) for i in range(3)]
        if p.get('runs'):
            # (E8 later r2) the grime runs' shape for OwnProps' runs material: where they hang from (the crenels, m), how
            # far below that the machicolation's or corbels' foot is (a second row starts there), their longest, their
            # strength, and whether "along the face" is round a drum
            meta['runs'] = {'top': round(p.get('run_top') or meta['box'][4], 3), 'drop': p.get('run_drop', 0.0), 'len': p['runs'][1],
                            'k': p['runs'][0], 'ring': p['kind'] == 'tower'}
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
