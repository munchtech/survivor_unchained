"""The heroine's outfits, one for each calling, cut from her own body.

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_outfits.py -- <out dir>/x [--body <heroine.glb>] [--only warden]

Each outfit is written as <out dir>/heroine_outfit_<name>.gltf (and .bin), the
textures in <out dir>/outfit_tex.

With --body her body is written again, marked where each outfit hides her.

The scene is the one heroine_head.py saved, so every piece is exported
from the very skeleton her body was and binds to hers exactly.

A piece is a region of her skin, bounded by a smooth curve: each region is
a field over her surface (positive inside, roughly in metres), and the
surface is cut where the field crosses zero, between vertices, so an edge
runs clean across the triangles instead of stepping along them. The piece
is then lifted off the skin, given a thickness and a rounded edge, and
keeps her weights (her springs included), so it moves as she does. Plate
is smoothed first, so it bridges the grooves of her muscles as metal would,
and then held clear of the skin everywhere.

The front of the crotch is always covered; how much of the seat is bare is
each outfit's own.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy import sparse
import scipy.sparse.csgraph
from scipy.spatial import cKDTree

# Progress shown as it happens (Blender holds output back otherwise).
sys.stdout.reconfigure(line_buffering=True)
ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = ARGS[0]
ONLY = ARGS[ARGS.index("--only") + 1] if "--only" in ARGS else None
BODY_OUT = ARGS[ARGS.index("--body") + 1] if "--body" in ARGS else None
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "outfit")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_rig as rig_helpers  # noqa: E402  (her helper bones, added just before export)

arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = bpy.data.objects["Heroine"]
# Her head is a mesh of its own (heroine_head.py), with its parts and her
# hairstyles beside it.
HEAD = bpy.data.objects.get("HeroineHead")
HEAD_PARTS = [o for o in bpy.data.objects if o.type == "MESH" and o.parent == arm and o.name.startswith("Heroine") and o != body]
# (her brows are in her face's paint once heroine_face.py has painted it: their
# cards, kept for that painting, are not the game's, as heroine_head.py has it)
if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "heroine_face", "face_paint.png")):
    HEAD_PARTS = [o for o in HEAD_PARTS if o.name != "HeroineBrows"]
HAIR_DEFAULT = bpy.data.objects.get("hair_long")
BONES = [b.name for b in arm.data.bones]
BI = {n: i for i, n in enumerate(BONES)}

# ------------------------------------------------------------ her surface --
# Welded (the paint's seams split her vertices) and in triangles.
bm = bmesh.new()
bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.verts.ensure_lookup_table()
bm.normal_update()
mw = body.matrix_world
P = np.array([(mw @ v.co)[:] for v in bm.verts])
N = np.array([(mw.to_3x3() @ v.normal).normalized()[:] for v in bm.verts])
TRI = np.array([[v.index for v in f.verts] for f in bm.faces])
dl = bm.verts.layers.deform.active
gname = {g.index: g.name for g in body.vertex_groups}
W = np.zeros((len(P), len(BONES)), np.float32)
for v in bm.verts:
    for g, w in v[dl].items():
        n = gname.get(g)
        if n in BI:
            W[v.index, BI[n]] = w
bm.free()
# Her head's surface joined on (it shares her points along her neck), so
# collars and hats are fitted to her as she is.
if HEAD:
    hb = bmesh.new()
    hb.from_mesh(HEAD.data)
    bmesh.ops.triangulate(hb, faces=hb.faces)
    hb.verts.ensure_lookup_table()
    hb.normal_update()
    hP = np.array([(HEAD.matrix_world @ v.co)[:] for v in hb.verts])
    hN = np.array([(HEAD.matrix_world.to_3x3() @ v.normal).normalized()[:] for v in hb.verts])
    hT = np.array([[v.index for v in f.verts] for f in hb.faces])
    hW = np.zeros((len(hP), len(BONES)), np.float32)
    hl = hb.verts.layers.deform.active
    hname = {g.index: g.name for g in HEAD.vertex_groups}
    for v in hb.verts:
        for g, w in v[hl].items():
            if hname.get(g) in BI:
                hW[v.index, BI[hname[g]]] = w
    hb.free()
    d, j = cKDTree(P).query(hP)
    shared = d < 1e-5
    idx = np.where(shared, j, len(P) + np.cumsum(~shared) - 1)
    P, N, W = np.vstack([P, hP[~shared]]), np.vstack([N, hN[~shared]]), np.vstack([W, hW[~shared]])
    TRI = np.vstack([TRI, idx[hT]])
    print("HEAD joined on:", int(shared.sum()), "points shared,", int((~shared).sum()), "of its own")


def subdivide(P, N, W, TRI):
    """Each triangle made four (a point at the middle of every edge), so a
    strap narrower than her triangles still finds skin to be cut from."""
    e = np.sort(np.vstack([TRI[:, [0, 1]], TRI[:, [1, 2]], TRI[:, [2, 0]]]), 1)
    uk, inv = np.unique(e, axis=0, return_inverse=True)
    inv = inv.ravel()
    m = len(P) + np.arange(len(uk))
    P2 = np.vstack([P, (P[uk[:, 0]] + P[uk[:, 1]]) / 2])
    N2 = np.vstack([N, N[uk[:, 0]] + N[uk[:, 1]]])
    N2 /= np.linalg.norm(N2, axis=1)[:, None] + 1e-12
    W2 = np.vstack([W, (W[uk[:, 0]] + W[uk[:, 1]]) / 2])
    t = len(TRI)
    ab, bc, ca = m[inv[:t]], m[inv[t:2 * t]], m[inv[2 * t:]]
    a, b, c = TRI[:, 0], TRI[:, 1], TRI[:, 2]
    T2 = np.vstack([np.c_[a, ab, ca], np.c_[ab, b, bc], np.c_[ca, bc, c], np.c_[ab, bc, ca]])
    return P2, N2, W2, T2


P, N, W, TRI = subdivide(P, N, W, TRI)
BVH = BVHTree.FromPolygons([tuple(p) for p in P], TRI.tolist())
# Her hair, by its paint (it is part of her mesh, and some strands are
# weighted to her neck and back, not her head): red, above her shoulders.
def _hair():
    me = body.data
    img = next(n.image for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
    w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]
    uv = np.zeros((len(me.vertices), 2))
    cnt = np.zeros(len(me.vertices))
    for l in me.loops:
        uv[l.vertex_index] += me.uv_layers.active.data[l.index].uv
        cnt[l.vertex_index] += 1
    uv /= np.maximum(cnt, 1)[:, None]
    col = px[np.clip((uv[:, 1] * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * w).astype(int), 0, w - 1)]
    co = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
    red = (col[:, 0] > 0.25) & (col[:, 0] > col[:, 1] * 1.7) & (col[:, 0] > col[:, 2] * 1.7) & (co[:, 2] > 1.4)
    _, j = cKDTree(co).query(P)
    return red[j].astype(float)


# (With a head of her own her hair is apart from her body: none of it on her.)
HAIR = np.zeros(len(P)) if HEAD else _hair()
print("HAIR", int(HAIR.sum()), "surface points")
# Her skin without her hair, for laying curves on.
_hair = (W[:, [BI[n] for n in ("Head", "neck_01") if n in BI]].sum(1) > 0.5)
_skin = ~_hair[TRI].any(1)
SKIN_BVH = BVHTree.FromPolygons([tuple(p) for p in P], TRI[_skin].tolist())
# Curves are laid on her skin, never on her hair.
SKIN_BVH = BVHTree.FromPolygons([tuple(p) for p in P], TRI[_skin & ~(HAIR[TRI] > 0.5).any(1)].tolist())
print("SURFACE", len(P), "vertices", len(TRI), "triangles")


def head(b):
    return np.array((arm.matrix_world @ arm.data.bones[b].head_local)[:])


def wsum(*names):
    return sum(W[:, BI[n]] for n in names if n in BI)


# ------------------------------------------------------------- landmarks --
X, Y, Z = P[:, 0], P[:, 1], P[:, 2]
mid = (np.abs(X) < 0.008) & (Z > 0.8) & (Z < 1.15) & (np.abs(Y) < 0.12)
# The crotch: down the middle from the pelvis until the skin first breaks
# off (below it the middle is the gap between her thighs, or where they
# touch further down).
zs = np.sort(Z[mid])[::-1]
zs = zs[zs < head("pelvis")[2]]
gap = np.where(np.diff(zs) < -0.012)[0]
CROTCH = zs[gap[0]] if len(gap) else zs[-1]
CROTCH_Y = Y[mid][np.argmin(np.abs(Z[mid] - CROTCH))]
if "crotch" in body.keys():
    _cr = mw @ Vector(body["crotch"])
    CROTCH, CROTCH_Y = _cr.z, _cr.y
NIP = {}
for s, sd in ((1, "l"), (-1, "r")):
    m = (Z > 1.25) & (Z < 1.5) & (X * s > 0.03) & (X * s < 0.2)
    NIP[sd] = P[np.where(m)[0][np.argmin(Y[m])]]
UNDERBUST = (NIP["l"][2] + NIP["r"][2]) / 2 - 0.056
WAIST = head("spine_01")[2]
NECK = head("neck_01")
LEG = {sd: [head(f"thigh_{sd}"), head(f"calf_{sd}"), head(f"foot_{sd}"), head(f"ball_{sd}")] for sd in "lr"}
ARM = {sd: [head(f"upperarm_{sd}"), head(f"lowerarm_{sd}"), head(f"hand_{sd}"), head(f"middle_01_{sd}")] for sd in "lr"}
print("LANDMARKS crotch %.3f underbust %.3f waist %.3f" % (CROTCH, UNDERBUST, WAIST))


def ramp(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def chain(pts):
    """Each vertex's place along a limb: arc length from the chain's start
    to the nearest point on it, and the distance off it."""
    best_d = np.full(len(P), 1e9)
    best_s = np.zeros(len(P))
    run = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        ab = b - a
        L = np.linalg.norm(ab)
        t = np.clip(((P - a) @ ab) / (L * L), 0, 1)
        d = np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
        better = d < best_d
        best_d[better] = d[better]
        best_s[better] = run + t[better] * L
        run += L
    return best_s, best_d


LEG_S = {}
ARM_S = {}
for sd, s in (("l", 1), ("r", -1)):
    LEG_S[sd] = chain(LEG[sd])[0]
    ARM_S[sd] = chain([head(f"clavicle_{sd}")] + ARM[sd])[0]
LEGW = {sd: wsum(f"thigh_{sd}", f"calf_{sd}", f"foot_{sd}", f"ball_{sd}") for sd in "lr"}
ARMW = {sd: wsum(*[n for n in BONES if n.endswith(f"_{sd}") and n.split("_")[0] in
                   ("upperarm", "lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb")]) for sd in "lr"}
KNEE_S = np.linalg.norm(LEG["l"][1] - LEG["l"][0])
ANKLE_S = KNEE_S + np.linalg.norm(LEG["l"][2] - LEG["l"][1])
ELBOW_S = np.linalg.norm(ARM["l"][0] - head("clavicle_l")) + np.linalg.norm(ARM["l"][1] - ARM["l"][0])
WRIST_S = ELBOW_S + np.linalg.norm(ARM["l"][2] - ARM["l"][1])
FRONT = ramp(-(Y - CROTCH_Y), -0.03, 0.03)
# The slot between her thighs under the crotch (they press together there):
# its two walls face each other across a gap of a centimetre or two.
# Garments span it, as cloth does, and never dive in; below the stocking
# tops it is just her inner thighs.
SLOT = ((np.abs(X) < 0.022) & (Z < CROTCH - 0.004) & (Z > CROTCH - 0.06) & (np.abs(Y - CROTCH_Y) < 0.07)
        & (N[:, 0] * np.sign(X + 1e-9) < -0.55))
print("SLOT", int(SLOT.sum()), "points of her inner thighs under the crotch")
# The box a crossing garment is cut out of: from in front of the slot to
# behind it, below just over the crotch.
GAP_F, GAP_B, GAP_Z = CROTCH_Y - 0.03, CROTCH_Y + 0.04, CROTCH + 0.012


def thong_path(z_top, y_front=None):
    """A thong's line: down the cleft behind from z_top, then forward
    under her along the top of the slot, to tuck under the front."""
    back = back_string(z_top, CROTCH + 0.012)
    y0 = back[-1][1] - 0.004
    y1 = (GAP_F - 0.006) if y_front is None else y_front
    return back + roof_path(y0, y1, 10)


def roof_z(x, y):
    """Height of her skin straight above a point under her crotch (the top
    of the slot between her thighs), seen from below."""
    hit = BVH.ray_cast(Vector((x, y, CROTCH - 0.3)), Vector((0, 0, 1)), 0.6)
    return hit[0].z if hit[0] is not None else CROTCH


def roof_path(y0, y1, n=12, x=0.0, lift=0.003):
    """Points along the top of the slot, under her, from y0 to y1."""
    return [np.array([x, y, roof_z(x, y) - lift]) for y in np.linspace(y0, y1, n)]


def crotch_bridge(name, pos, tris, gap_at, mkey, thick, bevel, trim, lift):
    """What carries a garment under her crotch, where it was cut away
    either side of the slot between her thighs: a gusset of even width laid
    straight along the roof of the slot, overlapping the garment's bound
    edges in front and behind."""
    # (close under her, her skin tucked under it, and each line of it moving
    # with the skin under that line, as the thongs' gussets)
    # (cut from her own skin, as the thongs' gussets: see gusset())
    return gusset(name + "_gusset", mkey, GAP_F - 0.014, GAP_B + 0.014, thick=thick)


def gusset(name, mkey, y_front, y_back, half=0.016, steep=0.9, thick=0.0018):
    """A gusset cut from her own skin under her crotch, skin-tight (1 mm off
    her), its edges bound and her skin tucked under it: from y_front to
    y_back, |x| under `half`, and up the walls of the slot between her thighs
    only as far as they face down (|N_x| under `steep`). (A flat strip 1 mm
    under the midline crossed the walls 6 mm out, the top of the slot being
    only 4 to 8 mm wide, and left their rounded shoulders bare; hung lower,
    her skin came through it as her thighs parted.)"""
    field = AND(half - np.abs(X), (steep - np.abs(N[:, 0])) * 0.02, y_back - Y, Y - y_front,
                Z - (CROTCH - 0.015), (CROTCH + 0.03) - Z)
    return piece(name, field, mkey, lift=0.001, thick=thick, smooth=2, soften=0, slot=False)


def spline(pts, step=0.004):
    """A smooth curve through control points (Catmull-Rom, centripetal: no
    loops or overshoot where they bunch), sampled every `step` or so."""
    p = [np.array(q, float) for q in pts]
    if len(p) < 3:
        n = max(2, int(np.linalg.norm(p[-1] - p[0]) / step))
        return np.array([p[0] + (p[-1] - p[0]) * t for t in np.linspace(0, 1, n)])
    p = [2 * p[0] - p[1]] + p + [2 * p[-1] - p[-2]]
    out = []
    for k in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[k - 1], p[k], p[k + 1], p[k + 2]
        t0 = 0.0
        t1 = t0 + np.linalg.norm(p1 - p0) ** 0.5 + 1e-9
        t2 = t1 + np.linalg.norm(p2 - p1) ** 0.5 + 1e-9
        t3 = t2 + np.linalg.norm(p3 - p2) ** 0.5 + 1e-9
        n = max(2, int(np.linalg.norm(p2 - p1) / step))
        for t in np.linspace(t1, t2, n, endpoint=False):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    out.append(p[-2])
    return np.array(out)


def on_surface(pts, step=0.004):
    """A curve through control points, sampled and laid on her skin."""
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = np.array(a), np.array(b)
        n = max(2, int(np.linalg.norm(b - a) / step))
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(a + (b - a) * t)
    out.append(np.array(pts[-1]))
    return np.array([SKIN_BVH.find_nearest(Vector(p))[0][:] for p in out])


def strap(pts, width):
    """Within half the width of a curve laid on her skin."""
    d, _ = cKDTree(on_surface(pts, step=0.0015)).query(P)
    return width / 2 - d


def front_point(x, z):
    """Her skin straight in front at (x, z), as a ray from ahead finds it."""
    hit = BVH.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)), 1.2)
    return np.array(hit[0][:]) if hit[0] is not None else np.array([x, -0.1, z])


def front_poly(pts, width, n=30):
    """A line through (x, z) points down her front, on her skin as seen
    from ahead (a lacing's zigzag, a boot's laces)."""
    on = []
    for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
        on += [front_point(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t) for t in np.linspace(0, 1, n)]
    d, _ = cKDTree(np.array(on)).query(P)
    return width / 2 - d


def side_point(sd, y, z):
    """Her skin on her side at (y, z), as a ray from beside her finds it."""
    s_ = 1 if sd == "l" else -1
    hit = BVH.ray_cast(Vector((0.6 * s_, y, z)), Vector((-s_, 0, 0)), 1.2)
    return np.array(hit[0][:]) if hit[0] is not None else np.array([0.18 * s_, y, z])


def pouch(name, sd, y, z, size, mkey):
    """A leather pouch on her hip: a rounded box (a superellipsoid), its
    back against her skin, moving as her skin there does."""
    s_ = 1 if sd == "l" else -1
    at = side_point(sd, y, z)
    a, b, c = size
    nu, nv = 18, 32
    th = np.linspace(0.02, np.pi - 0.02, nu)[:, None]
    ph = np.linspace(0, 2 * np.pi, nv, endpoint=False)[None, :]
    e = 0.3

    def sp(v):
        return np.sign(v) * np.abs(v) ** e

    lx = a * sp(np.sin(th) * np.cos(ph))
    ly = b * sp(np.sin(th) * np.sin(ph))
    lz = c * sp(np.cos(th) * np.ones_like(ph))
    pos = np.stack([at[0] + s_ * (a + 0.004) + s_ * lx, at[1] + ly, at[2] + lz], -1).reshape(-1, 3)
    idx = np.arange(nu * nv).reshape(nu, nv)
    idx = np.c_[idx, idx[:, :1]].ravel()
    tris = idx[grid(nu, nv + 1)]
    n = vertex_normals(pos, tris)
    if ((pos - pos.mean(0)) * n).sum(1).mean() < 0:
        tris = tris[:, ::-1]
    _, j = cKDTree(P).query(at)
    wt = np.repeat(W[j][None, :], len(pos), 0)
    return [finish(name, pos, wt, tris, mkey, 0.002, 0.0)]


def front_line(x0, z0, x1, z1, width, n=80):
    """A line down her front from (x0, z0) to (x1, z1), on her skin as seen
    from ahead (not wandering onto her breasts, as the nearest skin would)."""
    pts = np.array([front_point(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t) for t in np.linspace(0, 1, n)])
    d, _ = cKDTree(pts).query(P)
    return width / 2 - d


def skin_point(p):
    return np.array(SKIN_BVH.find_nearest(Vector(p))[0][:])


def AND(*f):
    return np.minimum.reduce(f)


def OR(*f):
    return np.maximum.reduce(f)


# ------------------------------------------------------------- the cut --
def adjacency(n, tris):
    """Each vertex's neighbours, as a row-normalised sparse matrix."""
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    e = np.vstack([e, e[:, ::-1]])
    m = sparse.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    m.data[:] = 1
    deg = np.asarray(m.sum(1)).ravel()
    deg[deg == 0] = 1
    return sparse.diags(1 / deg) @ m


ADJ = adjacency(len(P), TRI)
# Her breasts' weights eased up their upper slope. As authored they fell from
# most to nothing within two centimetres at the top of each breast, so in a
# swing the flesh above stayed put while the breast (and whatever she wears
# on it) moved: a hinge across her chest. Spread over about six centimetres,
# the slope moves with the breast; the rest of each point's weight makes room.
W_AUTHORED = W.copy()
_armw = W[:, [BI[n] for n in BONES if n.split("_")[0] in ("clavicle", "upperarm", "lowerarm", "hand")]].sum(1)
for _b in ("breast_l", "breast_r"):
    if _b not in BI:
        continue
    _bi = BI[_b]
    _h = np.array((arm.matrix_world @ arm.data.bones[_b].head_local)[:])
    _wb = W[:, _bi].astype(float)
    _near = (np.linalg.norm(P - _h, axis=1) < 0.16) & (P[:, 1] < _h[1] + 0.04) & (_armw < 0.3) & (P[:, 2] > _h[2] - 0.02)
    _sm = _wb.copy()
    for _ in range(160):
        _sm = np.where(_near, ADJ @ _sm, _wb)
    _new = np.where(_near, np.maximum(_wb, 0.9 * _sm), _wb)
    _rest = 1.0 - _wb
    _scale = np.where(_rest > 1e-6, (1.0 - _new) / np.maximum(_rest, 1e-6), 1.0)
    _others = np.ones(W.shape[1], bool)
    _others[_bi] = False
    W[:, _others] = (W[:, _others] * _scale[:, None]).astype(W.dtype)
    W[:, _bi] = _new.astype(W.dtype)
print("BREAST WEIGHTS eased at", int((np.abs(W - W_AUTHORED).sum(1) > 1e-4).sum()), "points")
# All her skin's weights eased over about 1.5 cm (but her hands' and head's,
# which shape fingers and a face), and cut to four bones smoothly: her
# skin's weights jump from point to point, and where a garment's eased
# edge lay on them, her skin moved by another rule and came through the
# edge in steps when she moved. Garments take these, so the two agree.
_keep = wsum(*[n for n in BONES if n.split("_")[0] in ("hand", "index", "middle", "ring", "pinky", "thumb", "Head")]) > 0.05
_el = np.linalg.norm(P[TRI[:, 0]] - P[TRI[:, 1]], axis=1)
_rounds = int(np.clip((0.015 / float(np.median(_el))) ** 2, 0, 80))
_W = W.copy()
for _ in range(_rounds):
    _W = ADJ @ _W
W = np.where(_keep[:, None], W, _W)
_fifth = -np.partition(-W, 4, axis=1)[:, 4]
W = np.maximum(W - _fifth[:, None], 0)
W = W / np.maximum(W.sum(1, keepdims=True), 1e-9)
print("SKIN WEIGHTS eased over", _rounds, "rounds, all but", int(_keep.sum()), "points of her hands and head")


# Within 4 cm of the skin heroine_head.py made anew over her shoulders
# (where her own skin meets coarser, the smoothing that finds bumps finds
# them all along the join): no nipple sought there, no lump filled.
_ga = body.data.attributes.get("graft")
if _ga:
    _gv = np.zeros(len(body.data.vertices), int)
    _ga.data.foreach_get("value", _gv)
    _gp = np.array([(body.matrix_world @ body.data.vertices[i].co)[:] for i in np.nonzero(_gv)[0]])
    NEAR_GRAFT = cKDTree(_gp).query(P)[0] < 0.04
else:
    NEAR_GRAFT = np.zeros(len(P), bool)


def nipples():
    """Each nipple: the most proud small bump on the breast (proud of her
    skin smoothed over a centimetre or so, so the breast's own curve does
    not count), away from the cleavage. Hers sit high and to the outside,
    not at the breast's most forward point."""
    S = P.copy()
    for _ in range(12):
        S = ADJ @ S
    proud = ((P - S) * N).sum(1)
    # The strongest such bump on either breast; the other nipple is sought
    # near its mirror image (they are level), so a lump elsewhere on one
    # breast cannot be taken for it.
    m = (np.abs(P[:, 0]) > 0.07) & (P[:, 2] > 1.3) & (P[:, 2] < 1.5) & (P[:, 1] < -0.05) & ~NEAR_GRAFT
    first = P[np.where(m)[0][np.argmax(proud[m])]]
    out = {}
    for s, sd in ((1, "l"), (-1, "r")):
        guess = np.array([abs(first[0]) * s, first[1], first[2]])
        near = np.where((np.linalg.norm(P - guess, axis=1) < 0.02) & ~NEAR_GRAFT)[0]
        out[sd] = P[near[np.argmax(proud[near])]]
        print("NIPPLE", sd, out[sd].round(3), "proud %.4f" % proud[near].max())
    return out


NIPPLE = nipples()


def filled_nipples(radius=0.03, rounds=4000):
    """Her skin with only each nipple and its raised areola filled in, all else
    untouched: armour cut from this is exactly her shape, without the point.
    The fill carries the breast's own curvature across the patch (the
    surface whose bending is least, not the flattest one, which would leave
    a dent where the nipple was)."""
    out = P.copy()
    inside = np.zeros(len(P), bool)
    for n in NIPPLE.values():
        inside |= np.linalg.norm(P - n, axis=1) < radius
    # Any other small lump or dent on the breasts (the sculpt has a lump low
    # on her left), so a cup copies her shape and not its flaws.
    S = P.copy()
    for _ in range(12):
        S = ADJ @ S
    proud = ((P - S) * N).sum(1)
    breast = (np.abs(P[:, 0]) > 0.03) & (P[:, 2] > 1.28) & (P[:, 2] < 1.5) & (P[:, 1] < -0.05)
    # Dents as well as lumps (a crease at the top of her left breast).
    lumps = P[breast & (np.abs(proud) > 0.0018) & ~NEAR_GRAFT]
    if len(lumps):
        d, _ = cKDTree(lumps).query(P)
        inside |= breast & (d < 0.02)
    # And her crotch, where the sculpt's skin between her thighs is
    # crumpled: a garment lies on it smooth.
    crotch = np.array([0.0, CROTCH_Y, CROTCH])
    inside |= (np.linalg.norm(P - crotch, axis=1) < 0.045) & (np.abs(X) < 0.04)
    print("FILLED", int(inside.sum()), "vertices of skin under cups")
    for _ in range(60):
        out = np.where(inside[:, None], ADJ @ out, out)
    for _ in range(rounds):
        lap = ADJ @ out - out
        out = np.where(inside[:, None], out - 0.15 * (ADJ @ lap - lap), out)
    return out


P_FILLED = filled_nipples()


def breast_ellipsoid():
    """An ellipsoid fitted to the front of both her breasts (her left
    mirrored onto her right, so the pair is one shape): the frame her cups'
    form is measured in. Its centre, axes (rows of R) and radii, on her
    right; and its radii grown to hold all of both breasts, nipples and all
    (the line the stalker's corset follows round their undersides)."""
    mirror = np.array([-1.0, 1.0, 1.0])
    front, whole = [], []
    for side_, sg in (("r", -1), ("l", 1)):
        q = NIPPLE[side_]
        near = (np.linalg.norm(P - q, axis=1) < 0.075) & (N[:, 1] < -0.3) & (P[:, 0] * sg > 0.01)
        held = (W_AUTHORED[:, BI[f"breast_{side_}"]] > 0.15) & (P[:, 0] * sg > 0.005) & (N[:, 1] < 0.0)
        flip = mirror if sg > 0 else np.ones(3)
        front.append(P_FILLED[near] * flip)
        whole.append(P[held] * flip)
    q0 = np.vstack(front)
    m = q0.mean(0)
    _, _, R = np.linalg.svd(q0 - m)
    loc = (q0 - m) @ R.T
    k, *_ = np.linalg.lstsq(np.c_[loc ** 2, loc], np.ones(len(loc)), rcond=None)
    A, B, C, D, E, F = k
    cl = -np.array([D / (2 * A), E / (2 * B), F / (2 * C)])
    g = 1 + A * cl[0] ** 2 + B * cl[1] ** 2 + C * cl[2] ** 2
    ax = np.sqrt(g / np.array([A, B, C]))
    c = m + cl @ R
    held = (np.vstack(whole) - c) @ R.T
    hold = np.sqrt(((held / ax) ** 2).sum(1)).max()
    return c, R, ax, ax * hold


def breast_form(c, R, ax):
    """Her breasts' own form, smooth: how far out it is in each direction
    from the ellipsoid's centre (as a part of the ellipsoid's radius there),
    hugging her breasts with the nipples filled (both, her left mirrored
    onto her right, so the pair is one shape). A membrane laid over them (it bridges a dip, never sinks into one),
    eased over about a centimetre, and lifted only where some of her stands
    proud of the eased one, by as much: it holds all of her, a few
    millimetres off at most. (An ellipsoid grown to hold all of her stood a
    centimetre off her breasts: the cups looked a size too big and showed
    her through the gap.) Returns a function of unit directions (in the
    ellipsoid's scaled frame)."""
    mirror = np.array([-1.0, 1.0, 1.0])
    ico = bmesh.new()
    bmesh.ops.create_icosphere(ico, subdivisions=5, radius=1.0)
    U = np.array([v.co[:] for v in ico.verts])
    ico.free()
    U /= np.linalg.norm(U, axis=1)[:, None]
    tree = cKDTree(U)

    def kernel(sig):
        rows, cols, vals = [], [], []
        for i, nb in enumerate(tree.query_ball_point(U, 3 * sig)):
            w = np.exp(-0.5 * (np.linalg.norm(U[nb] - U[i], axis=1) / sig) ** 2)
            rows += [i] * len(nb)
            cols += nb
            vals += list(w / w.sum())
        return sparse.csr_matrix((vals, (rows, cols)), shape=(len(U), len(U)))

    # Her breasts themselves (not her ribs below them, so the form turns into
    # her at the crease under each, where a cup ends), as her skin is, but
    # for each nipple and its areola, filled. (The fill elsewhere sinks into
    # the curve under them, and a form fitted to it went into her there.)
    pts = []
    for side_, sg in (("r", -1), ("l", 1)):
        d = np.linalg.norm(P - NIPPLE[side_], axis=1)
        m = (W_AUTHORED[:, BI[f"breast_{side_}"]] > 0.15) & (d < 0.11) & (P[:, 0] * sg > 0.0) & (N[:, 1] < 0.3)
        pts.append(np.where((d < 0.03)[:, None], P_FILLED, P)[m] * (mirror if sg > 0 else np.ones(3)))
    v = ((np.vstack(pts) - c) @ R.T) / ax
    rho = np.linalg.norm(v, axis=1)
    _, i = tree.query(v / rho[:, None])
    t = np.full(len(U), -np.inf)
    np.maximum.at(t, i, rho)
    has = np.isfinite(t)
    f = t.copy()
    f[~has] = t[has][cKDTree(U[has]).query(U[~has])[1]]
    small, big = kernel(0.04), kernel(0.07)
    for _ in range(60):
        f = np.where(has, np.maximum(t, small @ f), small @ f)
    f = big @ (big @ f)
    proud = np.where(has, np.maximum(t - f, 0), 0)
    f = f + big @ np.array([proud[nb].max() for nb in tree.query_ball_point(U, 0.18)])
    f = f + max(0.0, (t[has] - f[has]).max())

    def at(dirs):
        d, j = tree.query(dirs, 6)
        w = np.exp(-0.5 * (d / 0.02) ** 2) + 1e-12
        return (f[j] * w).sum(1) / w.sum(1)
    fr = at(v / rho[:, None])
    gap = (fr - rho) / fr * np.linalg.norm(np.vstack(pts) - c, axis=1)
    print("BREAST FORM off her by %.1f mm (median), %.1f (most), %.1f (least)" % (np.median(gap) * 1e3, gap.max() * 1e3, gap.min() * 1e3))
    return at


_c, _R, _ax, _ax_hold = breast_ellipsoid()
BREAST_FORM = (_c, _R, _ax, breast_form(_c, _R, _ax))
BREAST_HOLD = (_c, _R, _ax_hold)


def ideal_breasts(surface, full=0.05, fade=0.09):
    """A surface with her breasts made the perfect form: each point of each
    breast sent out along its normal to the form (only out, never in, and
    only where the form is near her), fully within `full` of her nipple,
    fading to her own
    shape by `fade`, so whatever is cut from it is uniform over her breasts
    (no lumps, no nipples) and still meets her skin at its edges."""
    c, R, ax, form = BREAST_FORM
    out = surface.copy()
    for sd, sg in (("r", -1), ("l", 1)):
        flip = np.array([sg * -1.0, 1.0, 1.0])            # (her left onto her right and back)
        q = surface * flip
        loc = (q - c) @ R.T
        r_e = np.sqrt(((loc / ax) ** 2).sum(1))
        reach = form(loc / ax / np.maximum(r_e, 1e-9)[:, None])
        r_ell = r_e / reach                               # (1 on the form)
        on = c + (loc / np.maximum(r_ell, 1e-9)[:, None]) @ R
        d = np.linalg.norm(surface - NIPPLE[sd], axis=1)
        w = np.clip((fade - d) / (fade - full), 0, 1)
        w = w * w * (3 - 2 * w)
        mine = (surface[:, 0] * sg > 0.0) & (r_ell < 1.0) & (w > 0)
        # Out along her skin's own normal, and only where the form is a few
        # millimetres off her: past where it was fitted (toward her arms) it
        # only carries on from its edge, and her skin sent out to it there,
        # sideways along the line from its centre, folded over itself.
        n_q = N * flip
        g = np.maximum(((on - q) * n_q).sum(1), 0)
        k = np.clip((0.008 - g) / 0.004, 0, 1)
        out[mine] = (q[mine] + n_q[mine] * (g * w * k)[mine, None]) * flip
    return out


# Garments over her breasts are cut from the perfect form, and never lie
# inside her own skin there (the fill that eases her breasts' lumps sinks
# up to centimetres into the curve under them; skin would show through).
P_FILLED = ideal_breasts(P_FILLED)
# (but for her nipples and areolae, which stay filled: kept out to her skin
# there, her nipples came back into everything cut over them, and through
# a plate cup)
_on_breast = (wsum("breast_l", "breast_r") > 0.01) & (np.minimum(*[np.linalg.norm(P - q, axis=1) for q in NIPPLE.values()]) > 0.03)
_out = ((P_FILLED - P) * N).sum(1)
P_FILLED = np.where((_on_breast & (_out < 0))[:, None], P_FILLED - N * _out[:, None], P_FILLED)
print("BREAST FILL kept out of her at", int((_on_breast & (_out < 0)).sum()), "points")


def untangled(S, rounds=300):
    """A surface made from her skin with no triangle turned over: sent out
    to her breasts' form, the skin at their sides toward her arms folded
    over itself, and a garment cut there showed the fold as a black notch.
    Each folded triangle and two rings round it are eased toward their
    neighbours, and kept out of her, until none is left."""
    def normals(Q):
        return np.cross(Q[TRI[:, 1]] - Q[TRI[:, 0]], Q[TRI[:, 2]] - Q[TRI[:, 0]])
    n0 = normals(P)
    first = None
    for k in range(rounds):
        flip = (normals(S) * n0).sum(1) <= 0
        if first is None:
            first = int(flip.sum())
        if not flip.any():
            break
        bad = np.zeros(len(S))
        bad[TRI[flip].ravel()] = 1
        for _ in range(2):
            bad = np.maximum(bad, (ADJ @ bad > 0).astype(float))
        S = np.where(bad[:, None] > 0, 0.5 * S + 0.5 * (ADJ @ S), S)
        o = ((S - P) * N).sum(1)
        S = np.where((bad > 0)[:, None] & (o < 0)[:, None], S - N * o[:, None], S)
    print("UNTANGLED", first, "folded triangles, left", int(((normals(S) * n0).sum(1) <= 0).sum()), "after", k + 1, "rounds")
    return S


P_FILLED = untangled(P_FILLED)


def smooth_field(f, k=3):
    """A field eased over her surface, so its zero line has no kinks from
    the triangles or the weights it was made from."""
    for _ in range(k):
        f = 0.5 * f + 0.5 * (ADJ @ f)
    return f


def clip(f, pos, attr, tris):
    """The part of a surface where f >= 0, cut along f = 0 between vertices:
    positions, attributes (interpolated) and triangles."""
    f = np.where(np.abs(f) < 1e-6, 1e-6, f)
    inside = f >= 0
    keep_tri = inside[tris].all(1)
    mixed = inside[tris].any(1) & ~keep_tri
    used = np.where(inside)[0]
    idx = -np.ones(len(pos), int)
    idx[used] = np.arange(len(used))
    out_p, out_a = [pos[used]], [attr[used]]
    out_t = [idx[tris[keep_tri]]]
    cut, extra = {}, []

    def edge(a, b):
        k = (min(a, b), max(a, b))
        if k not in cut:
            t = f[a] / (f[a] - f[b])
            cut[k] = len(used) + len(extra)
            extra.append((pos[a] * (1 - t) + pos[b] * t, attr[a] * (1 - t) + attr[b] * t))
        return cut[k]

    more = []
    for tri in tris[mixed]:
        poly = []
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            if inside[a]:
                poly.append(idx[a])
            if inside[a] != inside[b]:
                poly.append(edge(a, b))
        for i in range(1, len(poly) - 1):
            more.append((poly[0], poly[i], poly[i + 1]))
    if extra:
        out_p.append(np.array([e[0] for e in extra]))
        out_a.append(np.array([e[1] for e in extra]))
    if more:
        out_t.append(np.array(more))
    p2, a2, t2 = np.concatenate(out_p), np.concatenate(out_a), np.concatenate(out_t).astype(int)
    if len(t2) == 0:
        return p2[:0], a2[:0], t2
    # Only the vertices some triangle uses.
    live = np.unique(t2)
    re = -np.ones(len(p2), int)
    re[live] = np.arange(len(live))
    return p2[live], a2[live], re[t2]


def weld(pos, attr, tris, r=0.0007):
    """Points closer than r made one (the cut leaves slivers by the vertices
    it passes close to); triangles that collapse are dropped."""
    if os.environ.get("WELDDUMP"):  # SOLVER1 TEMP
        global _WELD_N
        _WELD_N = globals().get("_WELD_N", 0) + 1
        _nm = sys._getframe(1).f_locals.get("name", sys._getframe(1).f_code.co_name)
        np.savez(os.path.join(os.environ["WELDDUMP"], "weld_%04d_%s.npz" % (_WELD_N, _nm)), pos=pos, tris=tris, r=r,
                 caller=sys._getframe(1).f_code.co_name, line=sys._getframe(1).f_lineno)
    parent = np.arange(len(pos))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in cKDTree(pos).query_pairs(r):
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)
    root = np.array([find(i) for i in range(len(pos))])
    keys, inv = np.unique(root, return_inverse=True)
    cnt = np.bincount(inv)
    p2 = np.zeros((len(keys), 3))
    np.add.at(p2, inv, pos)
    a2 = np.zeros((len(keys), attr.shape[1]))
    np.add.at(a2, inv, attr)
    p2 /= cnt[:, None]
    a2 /= cnt[:, None]
    t2 = inv[tris]
    ok = (t2[:, 0] != t2[:, 1]) & (t2[:, 1] != t2[:, 2]) & (t2[:, 2] != t2[:, 0])
    t2 = t2[ok]
    area = np.linalg.norm(np.cross(p2[t2[:, 1]] - p2[t2[:, 0]], p2[t2[:, 2]] - p2[t2[:, 0]]), axis=1)
    return p2, a2, cancelled(t2[area > 1e-10])


def cancelled(tris):
    """Triangles on the same three points (a sliver the weld folded flat)
    cancelled by their winding, as a fold of no area: left in, three or four
    triangles met at an edge, the walk round the sheet's rim broke there, and
    the piece's edge was left as cut (the warden's left pauldron, unbound)."""
    st = np.sort(tris, 1)
    _, inv, cnt = np.unique(st, axis=0, return_inverse=True, return_counts=True)
    inv = np.asarray(inv).ravel()
    dup = cnt[inv] > 1
    if not dup.any():
        return tris
    # (+1 where a triangle runs round its sorted points, -1 the other way)
    r = np.argmin(tris, 1)
    par = np.where(tris[np.arange(len(tris)), (r + 1) % 3] == st[:, 1], 1, -1)
    keep = ~dup
    for g in np.unique(inv[dup]):
        ids = np.where(inv == g)[0]
        net = int(par[ids].sum())
        keep[ids[par[ids] == np.sign(net)][:abs(net)]] = True
    return tris[keep]


def vertex_normals(pos, tris):
    fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
    vn = np.zeros_like(pos)
    for k in range(3):
        np.add.at(vn, tris[:, k], fn)
    return vn / (np.linalg.norm(vn, axis=1)[:, None] + 1e-12)


def relax(pos, tris, interior=0, edge=12):
    """Smoothing: the inside (plate spanning hollows) and, along itself
    only, the edge, so a cut runs as one clean curve."""
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    be = uk[c == 1]
    n = len(pos)
    onb = np.zeros(n, bool)
    onb[be.ravel()] = True
    B = sparse.coo_matrix((np.ones(2 * len(be)), (np.r_[be[:, 0], be[:, 1]], np.r_[be[:, 1], be[:, 0]])), shape=(n, n)).tocsr()
    db = np.asarray(B.sum(1)).ravel()
    B = sparse.diags(1 / np.maximum(db, 1)) @ B
    A = adjacency(n, tris)
    for _ in range(interior):
        pos = np.where(onb[:, None], pos, 0.5 * pos + 0.5 * (A @ pos))
    # Along the edge only where it is a simple line (two edge neighbours).
    line = (onb & (db == 2))[:, None]
    for _ in range(max(edge, interior)):
        pos = np.where(line, 0.5 * pos + 0.5 * (B @ pos), pos)
    return pos


# ------------------------------------------------------------- materials --
# Each material: its scan, a tint, the mean brightness its colour is brought
# to (None keeps the scan's), how many times it repeats in a metre, and its
# metalness and roughness where the scan has no map of them. The colour is
# baked into a texture of the material's own (outfit_<key>_diff.jpg), so the
# game gets exactly what was made here.
SPEC = {
    "steel": ("Metal038", (1.0, 1.0, 1.02), 175, 2.5, 1.0, None),
    "darksteel": ("Metal046B", (1.0, 1.0, 1.05), 95, 2.5, 1.0, None),
    "gold": ("Metal048C", (1.0, 0.92, 0.8), None, 3, 1.0, None),
    "rust": ("Metal053C", (1, 1, 1), None, 2.5, 0.8, None),
    "leather": ("Leather037", (1, 1, 1), None, 4, 0.0, None),
    "darkleather": ("Leather026", (1.0, 0.8, 0.65), 30, 3, 0.0, None),
    "redleather": ("Leather024", (1, 1, 1), None, 4, 0.0, None),
    "oldleather": ("Leather014", (1, 1, 1), None, 4, 0.0, None),
    "velvet": ("velour_velvet", (0.32, 0.1, 0.45), None, 5, 0.0, None),
    "linen": ("rough_linen", (0.3, 0.4, 0.25), None, 5, 0.0, None),
    "fur": ("curly_teddy_natural", (0.55, 0.42, 0.32), 70, 4, 0.0, 0.9),
    "arcvelvet": ("velour_velvet", (0.3, 0.3, 1.0), 66, 5, 0.0, None),
    "plumleather": ("Leather026", (0.5, 0.4, 0.75), 44, 3, 0.0, None),
    "blackleather": ("Leather026", (1, 1, 1), 26, 3, 0.0, None),
    "brownleather": ("Leather037", (1, 0.8, 0.68), 30, 3, 0.0, None),
    "lace": ("rough_linen", (1.652, 1.379, 1.12), 235, 14, 0.0, 0.5, 0.85),
    "darkpurple": ("Leather026", (0.55, 0.2, 0.9), 26, 3, 0.0, 0.35),
    "satin": ("rough_linen", (1.652, 1.379, 1.12), 235, 10, 0.0, 0.3),
    "greenleather": ("Leather026", (0.42, 0.85, 0.45), 52, 3, 0.0, None),
    "bronze": ("Metal048C", (0.72, 0.58, 0.46), 95, 3, 1.0, 0.42),
    "ink": ("rough_linen", (0.22, 0.26, 0.34), 22, 10, 0.0, 0.65),
    "stocking": ("rough_linen", (1.624, 1.356, 1.11), 232, 14, 0.0, 0.45, 0.42),
    # (the linen scan is blue, about (145, 171, 205): these two are tinted from
    # it to a colour, warm ivory and a light saddle brown)
    "bone": ("rough_linen", (1.376, 1.099, 0.779), 183, 12, 0.0, 0.5),
    "browncloth": ("rough_linen", (0.606, 0.573, 0.234), 78, 18, 0.0, 0.8),
    "forestleather": ("Leather026", (0.42, 0.66, 0.42), 40, 3, 0.0, None),
    "thread": ("rough_linen", (1.349, 1.034, 0.682), 170, 60, 0.0, 0.5),
}
MATS = {}


def mat(key):
    if key in MATS:
        return MATS[key]
    src, tint, mean, _, metal, rough = SPEC[key][:6]
    alpha = SPEC[key][6] if len(SPEC[key]) > 6 else 1.0
    from PIL import Image
    col = np.asarray(Image.open(os.path.join(TEX, f"{src}_diff.jpg")).convert("RGB"), np.float32)
    col = col * np.array(tint)
    if mean:
        col = col * (mean / col.mean())
    if key in ("steel", "darksteel", "gold", "bronze"):
        # Scratches and flecks in the scan read as white specks at this scale.
        med = np.median(col.reshape(-1, 3), 0)
        col = np.clip(col, med * 0.8, med * 1.18)
    out = os.path.join(TEX, f"outfit_{key}_diff.jpg")
    Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(out, quality=92)
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]

    def img(path, non_color=False):
        if not os.path.exists(path):
            return None
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(path, check_existing=True)
        if non_color:
            n.image.colorspace_settings.name = "Non-Color"
        return n

    d = img(out)
    nt.links.new(d.outputs["Color"], bsdf.inputs["Base Color"])
    r = img(os.path.join(TEX, f"{src}_rough.jpg"), True)
    if r and rough is None:
        nt.links.new(r.outputs["Color"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = rough if rough is not None else 0.55
    mm = img(os.path.join(TEX, f"{src}_metal.jpg"), True)
    if mm:
        nt.links.new(mm.outputs["Color"], bsdf.inputs["Metallic"])
    else:
        bsdf.inputs["Metallic"].default_value = metal
    n = img(os.path.join(TEX, f"{src}_nor.jpg"), True)
    if n:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if alpha < 1:
        bsdf.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    MATS[key] = m
    return m


# ------------------------------------------------------------- bindings --
def smooth_closed(curve, sigma, step=0.002):
    """A closed line resampled evenly (every `step`) and eased with a
    Gaussian `sigma` long, so it runs as one fair curve."""
    c = np.vstack([curve, curve[:1]])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    n = max(24, int(d[-1] / step))
    t = np.linspace(0, d[-1], n, endpoint=False)
    r = np.stack([np.interp(t, d, c[:, k]) for k in range(3)], 1)
    sg = sigma / (d[-1] / n)
    if sg > 0.3:
        k = int(np.ceil(3 * sg))
        g = np.exp(-0.5 * (np.arange(-k, k + 1) / sg) ** 2)
        g /= g.sum()
        r = sum(np.roll(r, -i, 0) * g[i + k] for i in range(-k, k + 1))
    return r


def tube(name, curve, nrm, outward, mkey, width, height, overhang, thick, src_pos, src_wt, closed=True, nv=12):
    """A rolled edge along a line: a flattened tube `width` across, centred
    so it reaches `overhang` past the line on its `outward` side, and stands
    `height` proud of a sheet `thick` thick lying under it (half its
    height above the sheet, wrapping its cut edge). Weights from the sheet
    it binds, one set to each ring."""
    n = len(curve)
    c0 = curve + outward * (overhang - width / 2) + nrm * (thick / 2)
    rw, rh = width / 2, thick / 2 + height
    th = np.linspace(0, 2 * np.pi, nv, endpoint=False)
    pts = (c0[:, None, :] + outward[:, None, :] * (rw * np.cos(th))[None, :, None]
           + nrm[:, None, :] * (rh * np.sin(th))[None, :, None]).reshape(-1, 3)
    rows = n + (0 if closed else -1)
    tris = []
    for i in range(rows):
        i1 = (i + 1) % n
        for j in range(nv):
            j1 = (j + 1) % nv
            a, b, c, d = i * nv + j, i * nv + j1, i1 * nv + j, i1 * nv + j1
            tris += [(a, c, b), (b, c, d)]
    tris = np.array(tris)
    if not closed:
        # Ends closed with a fan.
        caps = []
        for i in (0, n - 1):
            ci = len(pts) + len(caps)
            caps.append(c0[i])
            for j in range(nv):
                j1 = (j + 1) % nv
                tris = np.vstack([tris, [(ci, i * nv + j1, i * nv + j)] if i == 0 else [(ci, i * nv + j, i * nv + j1)]])
        pts = np.vstack([pts, np.array(caps)])
    cen = np.vstack([np.repeat(c0, nv, 0), c0[[0, -1]]]) if not closed else np.repeat(c0, nv, 0)
    vn = vertex_normals(pts, tris)
    if ((pts - cen) * vn).sum(1).mean() < 0:
        tris = tris[:, ::-1]
    # One set of weights to each ring of it, from the sheet within about a
    # centimetre of the ring (weighed by nearness), eased along it: each
    # point taking its nearest point of the sheet's, it kinked where that
    # point changed, as she moved.
    kk = min(24, len(src_pos))
    d_, j_ = cKDTree(src_pos).query(c0, k=kk)
    d_, j_ = np.reshape(d_, (len(c0), kk)), np.reshape(j_, (len(c0), kk))
    g_ = np.exp(-0.5 * (d_ / 0.006) ** 2) + 1e-12
    ring = (np.asarray(src_wt, float)[j_] * g_[:, :, None]).sum(1) / g_.sum(1)[:, None]
    for _ in range(8):
        ring = (np.roll(ring, 1, 0) + 2 * ring + np.roll(ring, -1, 0)) / 4 if closed else             np.vstack([ring[:1], (ring[:-2] + 2 * ring[1:-1] + ring[2:]) / 4, ring[-1:]])
    wt = np.repeat(ring, nv, 0)
    if not closed:
        wt = np.vstack([wt, ring[[0, -1]]])
    obj = finish(name, pts, wt, tris, mkey, 0.0, 0.0, 10 ** 7)
    obj["hides"] = False
    return obj


def edge_loops(tris):
    """A sheet's edge as loops, found in one pass: each edge of a triangle
    whose reverse no triangle has is on the rim, and following those edges
    the way the triangles wind brings each walk home, pinched corners and
    all, with no searching. Edges are counted by direction, and an edge is
    on the rim as many times as it runs one way more than the other: so the
    rim is always closed, even where the weld left three or four triangles
    on one edge (counted as present or not, such an edge dropped out of the
    rim and the walk stopped short: the ranger's left glove, a loop's last
    step 27 mm back to its start)."""
    from collections import Counter, defaultdict
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]).tolist()
    count = Counter(map(tuple, e))
    out = defaultdict(list)
    for (a, b), n in count.items():
        out[a].extend([b] * max(n - count.get((b, a), 0), 0))
    out = defaultdict(list, {a: v for a, v in out.items() if v})
    loops = []
    while out:
        start = next(iter(out))
        loop, v = [start], start
        while v in out:
            nxt = out[v].pop()
            if not out[v]:
                del out[v]
            if nxt == start:
                break
            loop.append(nxt)
            v = nxt
        if len(loop) > 8:
            loops.append(loop)
    return loops


def bind_edges(name, pos, at, tris, key, width, height, overhang, thick, sigma=0.012, stitch=False):
    """A sheet's cut outline made fair and bound: each edge loop eased into
    one smooth curve, the sheet's own edge points moved onto it, and a
    rolled edge laid along it that covers the cut, as a garment's edges are
    bound or a plate's are rolled."""
    loops = edge_loops(tris)
    if not loops:
        return pos, []
    nor = vertex_normals(pos, tris)
    tree = cKDTree(pos)
    sheet_bvh = BVHTree.FromPolygons([tuple(p) for p in pos], tris.tolist())
    beads = []
    pos = pos.copy()
    moved = np.zeros(len(pos), bool)
    bound = 0
    for k, loop in enumerate(loops):
        lp = pos[loop]
        seg = np.linalg.norm(np.diff(np.vstack([lp, lp[:1]]), axis=0), axis=1)
        # A walk that jumped across the sheet, or a hole too small to bind
        # (a finger's), is left as cut.
        if seg.max() > 0.015 or seg.sum() < 0.07:
            print("UNBOUND %s: an edge loop of %d points left as cut (longest step %.1f mm, %.1f cm round)"
                  % (name, len(loop), seg.max() * 1000, seg.sum() * 100))
            continue
        bound += 1
        cur = smooth_closed(lp, sigma)
        # Back onto the sheet (its surface, not the plane of the nearest
        # point: that changed from point to point and stepped the line in
        # depth, unseen face-on, kinked at a glancing view), the move eased
        # along the line; and the sheet's normal there.
        # (the sheet's facing, from its surface, eased well along the line:
        # taken from the nearest point's normal it swung near the cut edge,
        # and the rolled edge, set off sideways by it, folded into a Z)
        hits = [sheet_bvh.find_nearest(Vector(q)) for q in cur]
        on = np.array([h[0][:] for h in hits])
        nrm = np.array([h[1][:] for h in hits])
        _, j = tree.query(cur)
        nrm = np.where(((nrm * nor[j]).sum(1) < 0)[:, None], -nrm, nrm)
        for _ in range(12):
            nrm = (np.roll(nrm, 1, 0) + 2 * nrm + np.roll(nrm, -1, 0)) / 4
        nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
        mv = on - cur
        for _ in range(6):
            mv = (np.roll(mv, 1, 0) + 2 * mv + np.roll(mv, -1, 0)) / 4
        cur = cur + mv
        tg = np.roll(cur, -1, 0) - np.roll(cur, 1, 0)
        tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
        nrm = nrm - tg * (nrm * tg).sum(1)[:, None]
        nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
        bn = np.cross(nrm, tg)
        for _ in range(8):
            bn = (np.roll(bn, 1, 0) + 2 * bn + np.roll(bn, -1, 0)) / 4
        bn = bn - tg * (bn * tg).sum(1)[:, None]
        bn /= np.linalg.norm(bn, axis=1)[:, None] + 1e-12
        # Outward: away from the sheet's points near the line.
        votes = []
        for i in range(0, len(cur), 4):
            near = tree.query_ball_point(cur[i], 0.02)
            if near:
                votes.append(((pos[near].mean(0) - cur[i]) @ bn[i]))
        sgn = -1.0 if np.median(votes) > 0 else 1.0
        outward = bn * sgn
        # The sheet's edge points onto the fair line, and anything of the
        # sheet still standing out past it (scraps, pinched corners) pulled
        # back inside it.
        # (each edge point to its own place on the line, the line being its
        # loop eased: sent to the nearest place instead, neighbours landed
        # on one spot, their triangles fell flat, and thickened they stood
        # out as spikes and steps along her neckline)
        lt = cKDTree(cur)
        run = np.r_[0, np.cumsum(seg)]                     # (each point's way along its loop)
        tt = np.linspace(0, run[-1], len(cur), endpoint=False)
        cw = np.vstack([cur, cur[:1]])
        tw = np.r_[tt, run[-1]]
        pos[loop] = np.stack([np.interp(run[:-1], tw, cw[:, k]) for k in range(3)], 1)
        moved[loop] = True
        dn, jn = lt.query(pos)
        near_ = dn < 0.025
        out_ = ((pos - cur[jn]) * outward[jn]).sum(1)
        fix = near_ & (out_ > -0.0003)
        fix[loop] = False
        pos[fix] -= outward[jn[fix]] * (out_[fix] + 0.0003)[:, None]
        moved |= fix
        beads.append(tube(f"{name}_bind{k}" if k else f"{name}_bind", cur, nrm, outward, key, width, height, overhang, thick,
                          pos, at[:, 3:3 + NB]))
        if stitch:
            # (sewn through the binding, along its inner shoulder)
            c0 = cur + outward * (overhang - width / 2) + nrm * (thick / 2)
            line = c0 - outward * (width / 2) * 0.45 + nrm * ((thick / 2 + height) * 0.893 + 0.0001)
            beads += stitches(f"{name}_stitch{k}", line, nrm, tg, pos, at[:, 3:3 + NB], closed=True)
    # The points next to the edge eased, so the sheet meets its new edge
    # without a crease.
    A = adjacency(len(pos), tris)
    near = (A @ moved.astype(float)) > 0
    near &= ~moved
    nor_e = vertex_normals(pos, tris)
    for _ in range(6):
        d_ = 0.5 * (A @ pos - pos)
        d_ -= nor_e * (d_ * nor_e).sum(1)[:, None]
        pos = np.where(near[:, None], pos + d_, pos)
    print("BOUND", name, bound, "of", len(loops), "edge loops")
    return pos, beads


def domes(name, pts, nrms, mkey, r=0.0028, src=None):
    """Small domed studs (eyelets, rivets) at points, standing on normals."""
    P2, T2 = [], []
    nu, nv = 12, 4
    for p0, n in zip(pts, nrms):
        n = n / np.linalg.norm(n)
        t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        t /= np.linalg.norm(t)
        b = np.cross(n, t)
        o = sum(len(x) for x in P2)
        q = [p0 + n * r * 0.7]
        for k in range(1, nv + 1):
            th = (np.pi / 2) * k / nv
            for j in range(nu):
                ph = 2 * np.pi * j / nu
                q.append(p0 + (np.cos(ph) * t + np.sin(ph) * b) * r * np.sin(th) + n * r * 0.7 * np.cos(th))
        tri = [(o, o + 1 + j, o + 1 + (j + 1) % nu) for j in range(nu)]
        for k in range(nv - 1):
            a0, b0 = o + 1 + k * nu, o + 1 + (k + 1) * nu
            for j in range(nu):
                j1 = (j + 1) % nu
                tri += [(a0 + j, b0 + j, b0 + j1), (a0 + j, b0 + j1, a0 + j1)]
        P2.append(np.array(q))
        T2.append(np.array(tri))
    pp, tt = np.vstack(P2), np.vstack(T2)
    cen = np.repeat(np.array(pts), nu * nv + 1, 0)
    if ((pp - cen) * vertex_normals(pp, tt)).sum(1).mean() < 0:
        tt = tt[:, ::-1]
    # (each moves as one piece: its centre's weights for all of it)
    cen_ = np.array(pts, float)
    if src is None:
        wc = soft_weights(cen_)
    else:
        _, jc = cKDTree(src[0]).query(cen_)
        wc = np.asarray(src[1], float)[jc]
    obj = finish(name, pp, np.repeat(wc, nu * nv + 1, 0), tt, mkey, 0.0, 0.0, 10 ** 7)
    obj["hides"] = True
    return [obj]


def grommets(name, pts, nrms, mkey, r_out=0.0036, r_in=0.0018, height=0.0014, hole="blackleather"):
    """Eyelets as a corsetier sets them: a rolled metal ring at each point,
    standing on its normal, with the dark of the hole inside it (a dome
    reads as a stud, not as a hole a lace goes through)."""
    nu, nv = 20, 8
    R0, rw, rh = (r_out + r_in) / 2, (r_out - r_in) / 2, height / 2
    P2, T2, C2, H2, HT = [], [], [], [], []
    for p0, n in zip(pts, nrms):
        n = n / np.linalg.norm(n)
        t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        t /= np.linalg.norm(t)
        b = np.cross(n, t)
        o = sum(len(x) for x in P2)
        q, cen = [], []
        for i in range(nu):
            radial = np.cos(2 * np.pi * i / nu) * t + np.sin(2 * np.pi * i / nu) * b
            for j in range(nv):
                th = 2 * np.pi * j / nv
                q.append(p0 + n * rh + radial * (R0 + rw * np.cos(th)) + n * rh * np.sin(th))
                cen.append(p0 + n * rh + radial * R0)
        tri = []
        for i in range(nu):
            i1 = (i + 1) % nu
            for j in range(nv):
                j1 = (j + 1) % nv
                a_, b_, c_, d_ = o + i * nv + j, o + i * nv + j1, o + i1 * nv + j, o + i1 * nv + j1
                tri += [(a_, c_, b_), (b_, c_, d_)]
        P2.append(np.array(q))
        T2.append(np.array(tri))
        C2.append(np.array(cen))
        ho = sum(len(x) for x in H2)
        H2.append(np.array([p0 + n * rh * 0.5] + [p0 + n * rh * 0.5 + (np.cos(2 * np.pi * i / nu) * t + np.sin(2 * np.pi * i / nu) * b)
                                                  * (r_in + rw * 0.5) for i in range(nu)]))
        tr = np.array([(ho, ho + 1 + i, ho + 1 + (i + 1) % nu) for i in range(nu)])
        if (vertex_normals(H2[-1], tr - ho) @ n).mean() < 0:
            tr = tr[:, ::-1]
        HT.append(tr)
    pp, tt, cc = np.vstack(P2), np.vstack(T2), np.vstack(C2)
    if ((pp - cc) * vertex_normals(pp, tt)).sum(1).mean() < 0:
        tt = tt[:, ::-1]
    hp, ht = np.vstack(H2), np.vstack(HT)
    made = []
    wc = soft_weights(np.array(pts, float))
    for nm, q, tr, key, per in ((name, pp, tt, mkey, nu * nv), (name + "_holes", hp, ht, hole, nu + 1)):
        made.append(finish(nm, q, np.repeat(wc, per, 0), tr, key, 0.0, 0.0, 10 ** 7))
    for o_ in made:
        o_["hides"] = False
    return made


def cord(name, pts, mkey, r=0.0014, nv=10):
    """A round cord (a lace, a bow) along points given densely, as they are
    (taut, not laid on her). It hides nothing of her: what shows between
    the laces is her skin."""
    c = np.asarray(pts, float)
    nrm = np.array([SKIN_BVH.find_nearest(Vector(p))[1][:] for p in c])
    tg = np.gradient(c, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
    nrm = nrm - tg * (nrm * tg).sum(1)[:, None]
    nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
    obj = tube(name, c, nrm, np.cross(nrm, tg), mkey, 2 * r, r, r, 0.0, P, W.astype(float), closed=False, nv=nv)
    obj["hides"] = False
    return [obj]


def bezier(p0, p1, p2, step=0.0012):
    """Points along a quadratic curve from p0 to p2 drawn toward p1."""
    n = max(4, int((np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1)) / step))
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def stitches(name, line, nrm, tg, src_pos, src_wt, step=0.004, length=0.0026, width=0.00065, height=0.0004, closed=False,
             mkey="thread"):
    """Saddle stitching along a line laid on a surface (`nrm` its normal,
    `tg` the line's way): a dash of waxed thread every `step`, its ends sunk
    into the leather, every one exactly in line and evenly spaced, as a
    careful hand sews. (Painted stitches, laid out from screen derivatives,
    wandered and broke at the texture's seams.)"""
    line, nrm, tg = (np.asarray(x, float) for x in (line, nrm, tg))
    if closed:
        line, nrm, tg = np.vstack([line, line[:1]]), np.vstack([nrm, nrm[:1]]), np.vstack([tg, tg[:1]])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))]
    if len(line) < 2 or d[-1] < 3 * step:
        return []
    n_ = int(d[-1] / step)
    ss = (np.arange(n_) + 0.5) * d[-1] / n_
    c = np.stack([np.interp(ss, d, line[:, k]) for k in range(3)], 1)
    nn = np.stack([np.interp(ss, d, nrm[:, k]) for k in range(3)], 1)
    nn /= np.linalg.norm(nn, axis=1)[:, None] + 1e-12
    tt = np.stack([np.interp(ss, d, tg[:, k]) for k in range(3)], 1)
    tt -= nn * (tt * nn).sum(1)[:, None]
    tt /= np.linalg.norm(tt, axis=1)[:, None] + 1e-12
    bb = np.cross(nn, tt)
    nu, nv = 4, 4
    ph = np.linspace(0, 2 * np.pi, nu, endpoint=False) + np.pi / 4
    tv = np.linspace(-1, 1, nv + 1)[1:-1]
    ring = np.sqrt(1 - tv ** 2)
    base = c - nn * height * 0.35
    # (per stitch: an end, nv-1 rings of nu, the other end)
    ends0 = base - tt * length / 2
    ends1 = base + tt * length / 2
    rings = (base[:, None, None, :] + tt[:, None, None, :] * (tv * length / 2)[None, :, None, None]
             + (np.cos(ph)[None, None, :, None] * bb[:, None, None, :] * width / 2
                + np.sin(ph)[None, None, :, None] * nn[:, None, None, :] * height) * ring[None, :, None, None])
    per = 2 + (nv - 1) * nu
    pts = np.concatenate([ends0[:, None], rings.reshape(len(c), -1, 3), ends1[:, None]], 1).reshape(-1, 3)
    tri = [(0, 1 + (j + 1) % nu, 1 + j) for j in range(nu)]
    for k in range(nv - 2):
        a0, b0 = 1 + k * nu, 1 + (k + 1) * nu
        tri += [t for j in range(nu) for t in ((a0 + j, a0 + (j + 1) % nu, b0 + j), (b0 + j, a0 + (j + 1) % nu, b0 + (j + 1) % nu))]
    last = 1 + (nv - 2) * nu
    tri += [(per - 1, last + j, last + (j + 1) % nu) for j in range(nu)]
    tri = np.array(tri)
    tris = (tri[None] + (np.arange(len(c)) * per)[:, None, None]).reshape(-1, 3)
    cen = np.repeat(base, per, 0)
    if ((pts - cen) * vertex_normals(pts, tris)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
    # (each stitch weighed as the binding's rings are, so it stays on them)
    kk = min(24, len(src_pos))
    d_, j_ = cKDTree(src_pos).query(base, k=kk)
    d_, j_ = np.reshape(d_, (len(base), kk)), np.reshape(j_, (len(base), kk))
    g_ = np.exp(-0.5 * (d_ / 0.006) ** 2) + 1e-12
    w_ = (np.asarray(src_wt, float)[j_] * g_[:, :, None]).sum(1) / g_.sum(1)[:, None]
    obj = finish(name, pts, np.repeat(w_, per, 0), tris, mkey, 0.0, 0.0, 10 ** 7, scraps=False)
    obj["hides"] = False
    return [obj]


def studs_on(name, objs, aims, mkey, r=0.0026):
    """Rivets set on the outer face of pieces already made (a belt, a strap),
    where a ray from outside toward each aim (origin, target) first meets
    them: the visible fixing of one piece to another."""
    vs, fs = [], []
    for o in objs:
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        fs += [[base + i for i in p.vertices] for p in o.data.polygons]
    tree = BVHTree.FromPolygons(vs, fs)
    pts, nrms = [], []
    for org, tgt in aims:
        d = Vector(tuple(np.asarray(tgt) - np.asarray(org))).normalized()
        hit = tree.ray_cast(Vector(tuple(org)), d, 2.0)
        if hit[0] is not None:
            n = np.array(hit[1][:])
            if n @ np.array(d[:]) > 0:
                n = -n
            pts.append(np.array(hit[0][:]) + n * 0.0002)
            nrms.append(n)
    if not pts:
        return []
    made = domes(name, pts, nrms, mkey, r=r)
    for o_ in made:
        o_["hides"] = False
    return made


def sunburst(name, centre, nrm, up, radius, mkey, rays=12, thick=0.0035, boss=None):
    """The sun of the Order of the Morning Light, as a smith would cut it:
    a disc ringed by `rays` rays, long and short by turns, the long ones
    tapering to points, `thick` deep with rounded edges, a domed boss in its
    middle (of `boss`, or of its own metal). Standing at `centre` on a
    surface whose normal is `nrm` (`up` its long way); weighted as her skin
    nearest it."""
    n = nrm / np.linalg.norm(nrm)
    u = up - n * (up @ n)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    # The outline: between each pair of rays a notch at the disc's rim.
    ang = np.linspace(0, 2 * np.pi, 4 * rays, endpoint=False) + np.pi / 2
    rr = []
    for i in range(4 * rays):
        ray = i // 2
        if i % 2 == 0:
            rr.append(radius * (1.0 if ray % 2 == 0 else 0.78))       # a ray's point
        else:
            rr.append(radius * 0.56)                                  # the notch between rays
    rr = np.array(rr)
    rings = 6
    pts = [centre]
    for kk in range(1, rings + 1):
        for a_, r_ in zip(ang, rr * kk / rings):
            pts.append(centre + (np.cos(a_) * u + np.sin(a_) * v) * r_)
    pts = np.array(pts)
    m = len(ang)
    tris = [(0, 1 + j, 1 + (j + 1) % m) for j in range(m)]
    for kk in range(rings - 1):
        a0, b0 = 1 + kk * m, 1 + (kk + 1) * m
        for j in range(m):
            j1 = (j + 1) % m
            tris += [(a0 + j, b0 + j, b0 + j1), (a0 + j, b0 + j1, a0 + j1)]
    tris = np.array(tris)
    if (vertex_normals(pts, tris) @ n).mean() < 0:
        tris = tris[:, ::-1]
    wc = soft_weights(np.array([centre]), sigma=radius, k=32)
    made = [finish(name, pts, np.repeat(wc, len(pts), 0), tris, mkey, thick, thick * 0.4, 10 ** 7)]
    made += domes(name + "_boss", [centre + n * thick], [n], boss or mkey, r=radius * 0.38)
    for o_ in made:
        o_["hides"] = False
    return made


def fangs(name, pts, outs, downs, mkey, length=0.026, base=0.0045, curl=0.35, rng=None):
    """Wolf fangs strung on a cord: at each point a tooth, its root a little
    off the cord along `out`, curving down (`down`) and out to a point,
    round and tapering, each a little longer or shorter than the next."""
    rng = rng or np.random.default_rng(3)
    P2, T2 = [], []
    nu, nv = 10, 12
    for p0, o, dn in zip(pts, outs, downs):
        o = o / np.linalg.norm(o)
        dn = dn - o * (dn @ o)
        dn /= np.linalg.norm(dn)
        side = np.cross(o, dn)
        L = length * rng.uniform(0.75, 1.1)
        off = len(sum([list(x) for x in P2], []))
        ring_pts = []
        for k in range(nv + 1):
            t = k / nv
            # the tooth's middle line: down, curling out toward its point
            c = p0 + o * 0.003 + dn * L * t + o * L * curl * t * t
            tang = dn + o * 2 * L * curl * t / max(L, 1e-6)
            tang /= np.linalg.norm(tang)
            a1 = np.cross(tang, side)
            a1 /= np.linalg.norm(a1)
            r = base * (1 - t) ** 0.8 + 0.0002
            for j in range(nu):
                ph = 2 * np.pi * j / nu
                ring_pts.append(c + (np.cos(ph) * side + np.sin(ph) * a1) * r * (1.0 if np.sin(ph) > 0 else 0.8))
        ring_pts.append(p0 + o * 0.003 + dn * L + o * L * curl + dn * 0.0006)
        tri = []
        for k in range(nv):
            a0_, b0_ = off + k * nu, off + (k + 1) * nu
            for j in range(nu):
                j1 = (j + 1) % nu
                tri += [(a0_ + j, b0_ + j, b0_ + j1), (a0_ + j, b0_ + j1, a0_ + j1)]
        tip = off + (nv + 1) * nu
        tri += [(off + nv * nu + j, tip, off + nv * nu + (j + 1) % nu) for j in range(nu)]
        # its root closed
        tri += [(off, off + (j + 1) % nu, off + j) for j in range(1, nu - 1)]
        P2.append(np.array(ring_pts))
        T2.append(np.array(tri))
    pp, tt = np.vstack(P2), np.vstack(T2)
    if (vertex_normals(pp, tt) * (pp - np.repeat(np.array(pts), (nv + 1) * nu + 1, 0))).sum(1).mean() < 0:
        tt = tt[:, ::-1]
    wc = soft_weights(np.array(pts, float))
    obj = finish(name, pp, np.repeat(wc, (nv + 1) * nu + 1, 0), tt, mkey, 0.0, 0.0, 10 ** 7)
    obj["hides"] = False
    return [obj]


def frame(name, centre, nrm, up, w, h, mkey, r=0.002, corner=0.004, lift=0.0):
    """A buckle frame: a rounded rectangle of rod `r` thick, `w` by `h`,
    standing on a surface at `centre` (normal `nrm`, `up` its long way)."""
    n = nrm / np.linalg.norm(nrm)
    u = up - n * (up @ n)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    pts = []
    hw, hh = w / 2 - corner, h / 2 - corner
    for cx, cy, a0 in ((hw, hh, 0), (-hw, hh, np.pi / 2), (-hw, -hh, np.pi), (hw, -hh, 3 * np.pi / 2)):
        for a in np.linspace(a0, a0 + np.pi / 2, 8, endpoint=False):
            pts.append(centre + n * lift + v * (cx + corner * np.cos(a)) + u * (cy + corner * np.sin(a)))
    pts = np.array(pts)
    nr = np.repeat(n[None], len(pts), 0)
    tg = np.roll(pts, -1, 0) - np.roll(pts, 1, 0)
    tg /= np.linalg.norm(tg, axis=1)[:, None]
    out = np.cross(nr, tg)
    if ((pts - pts.mean(0)) * out).sum(1).mean() < 0:
        out = -out
    c_ = pts.mean(0)
    wc = soft_weights(c_[None], sigma=max(w, h) / 2, k=32)
    return [tube(name, pts, nr, out, mkey, 2 * r, 0.0, r, 2 * r, c_[None], wc)]


# ----------------------------------------------------------------- pieces --
NB = len(BONES)


def hulled(pos, where, tris, blend=0.02):
    """Where `where` > 0 (a boot's foot), the piece laid on the convex hull
    of itself there: toes become one rounded toe box, as leather over them
    is; it eases back to its own shape over `blend` of `where`."""
    from scipy.spatial import ConvexHull
    m = where > -blend
    if m.sum() < 10:
        return pos
    h = ConvexHull(pos[m])
    hv = pos[m]
    bvh = BVHTree.FromPolygons([tuple(p) for p in hv], h.simplices.tolist())
    out = pos.copy()
    t = np.clip((where + blend) / blend, 0, 1)
    for i in np.where(m)[0]:
        q = bvh.find_nearest(Vector(pos[i]))[0]
        if q is not None:
            out[i] = pos[i] * (1 - t[i]) + np.array(q[:]) * t[i]
    return out


def rim_loops(pos, tris):
    """The edge of a sheet as closed loops, in order. Spurs (where the cut
    left a stray edge) are pruned; at a branch the walk takes the
    straightest way on, and backs up from a dead end, until it is home."""
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    nbr = {}
    # An edge on the rim is used by an odd number of triangles (once, or
    # three times where the cut pinched the sheet).
    for a, b in uk[c % 2 == 1]:
        nbr.setdefault(int(a), set()).add(int(b))
        nbr.setdefault(int(b), set()).add(int(a))
    changed = True
    while changed:
        changed = False
        for v in [v for v, n in nbr.items() if len(n) < 2]:
            for w in nbr.pop(v):
                nbr.get(w, set()).discard(v)
            changed = True
    left = set(nbr)
    loops = []
    while left:
        start = max(left, key=lambda v: (len(nbr[v]) == 2, -v))
        path, onpath = [start], {start}
        tried = {start: set()}
        found = False
        while path and not found:
            v = path[-1]
            prev = path[-2] if len(path) > 1 else None
            d0 = pos[v] - pos[prev] if prev is not None else None
            cands = [w for w in nbr[v] if w != prev and w not in tried[v] and (w not in onpath or (w == start and len(path) > 8))]
            if not cands:
                path.pop()
                onpath.discard(v)
                continue
            if d0 is not None:
                cands.sort(key=lambda w: -np.dot(d0, pos[w] - pos[v]) / (np.linalg.norm(pos[w] - pos[v]) + 1e-12))
            w = cands[0]
            tried[v].add(w)
            if w == start:
                found = True
                break
            path.append(w)
            onpath.add(w)
            tried[w] = set()
        if found and len(path) > 20:
            loops.append(path)
        left -= set(path) | {start}
        left -= {v for v in list(left) if not (nbr[v] & left)}
    return loops


ROUND_RIM = 20      # rounds of smoothing a cup's outline gets
FILLED_BVH = None


def bra_cup(pos, tris, edge, skin, skin_n, lift, blend=0.0):
    """A cup shaped as a bra's is: an ellipsoid (a sphere stretched along
    the breast's own axes) fitted to the front of her breast under it (not
    the fold beneath, which faces down), as large as her breast and `lift`
    more, the even grid laid on it straight out from its centre; only its
    last `blend` toward the edge eases onto the edge itself. Her skin under
    it is not drawn, so it need not clear any bump of hers."""
    out = pos.copy()
    for side in (pos[:, 0] < 0, pos[:, 0] >= 0):
        sk = skin[(skin[:, 0] < 0) == (side[0] if False else bool(pos[side][0, 0] < 0))] if side.any() else None
        if sk is None:
            continue
        sn = skin_n[(skin[:, 0] < 0) == bool(pos[side][0, 0] < 0)]
        front = sk[(sn[:, 1] < -0.25)]
        if len(front) < 30:
            continue
        m = front.mean(0)
        _, _, R = np.linalg.svd(front - m)
        q = (front - m) @ R.T
        k, *_ = np.linalg.lstsq(np.c_[q ** 2, q], np.ones(len(q)), rcond=None)
        A, B, C, D, E, F = k
        if min(A, B, C) <= 0:
            print("BRA CUP fit not an ellipsoid", (A, B, C))
            continue
        cl = -np.array([D / (2 * A), E / (2 * B), F / (2 * C)])
        g = 1 + A * cl[0] ** 2 + B * cl[1] ** 2 + C * cl[2] ** 2
        ax = np.sqrt(g / np.array([A, B, C])) + lift
        c = m + cl @ R
        v = pos[side]
        loc = (v - c) @ R.T
        on = c + (loc / np.sqrt(((loc / ax) ** 2).sum(1))[:, None]) @ R
        t = np.clip(edge[side] / blend, 0, 1)[:, None] if blend > 0 else np.ones((side.sum(), 1))
        t = t * t * (3 - 2 * t)
        out[side] = v * (1 - t) + on * t
        print("BRA CUP axes", (ax * 100).round(1), "cm")
    return out


def onto_breast(pos, tris, lift, rounds=150):
    """A cup's even grid laid on her breast as it is (the areola filled in,
    nothing else changed): each point sent straight in or out to her skin,
    lifted, then ironed smooth without shrinking, so the cup has her own
    round shape, close-fitting, with no crease or bump in it."""
    global FILLED_BVH
    if FILLED_BVH is None:
        FILLED_BVH = BVHTree.FromPolygons([tuple(p) for p in P_FILLED], TRI.tolist())
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    rim = np.zeros(len(pos), bool)
    rim[uk[c == 1].ravel()] = True
    out = pos.copy()
    for side in (pos[:, 0] < 0, pos[:, 0] >= 0):
        q = pos[side & rim]
        if len(q) < 10:
            continue
        _, _, R = np.linalg.svd(q - q.mean(0))
        n = R[2]
        if n[1] > 0:
            n = -n            # out of her front
        for i in np.where(side & ~rim)[0]:
            best = None
            for d in (n, -n):
                hit = FILLED_BVH.ray_cast(Vector(pos[i] - d * 0.002), Vector(d), 0.2)
                if hit[0] is not None and (best is None or hit[3] < best[1]):
                    best = (np.array(hit[0][:]), hit[3], np.array(hit[1][:]))
            if best is not None:
                out[i] = best[0] + best[2] * lift
    out = taubin(out, tris, rounds=rounds)
    return out
FULLER = 0.005      # how far a cup stands off her skin


def even_cup(pos, at, tris, h=0.004):
    """Each cup's sheet made again on an even grid of triangles spanning
    its rim (the cut leaves slivers and the filled areola is crumpled, and
    a membrane solved on uneven triangles folds where their size changes).
    The rim is kept exactly; inside, points on a grid in the rim's own
    plane, the membrane then solved from the rim alone; everything else
    (weights, the field) from the nearest old point."""
    from matplotlib.path import Path as MPath
    from scipy.spatial import Delaunay
    tree = cKDTree(pos)
    P2, A2, T2 = [], [], []
    # (Twice-made triangles out, which would hide an edge.)
    _, first = np.unique(np.sort(tris, 1), axis=0, return_index=True)
    tris = tris[np.sort(first)]
    loops = rim_loops(pos, tris)
    print("CUP RIMS", [len(l) for l in loops])
    for loop in sorted(loops, key=len, reverse=True)[:2]:
        # The outline itself made a smooth curve (it follows her skin's cut
        # exactly, corners and all, and the bowl takes its shape from it).
        rimp = pos[loop].copy()
        for _ in range(ROUND_RIM):
            rimp = 0.5 * rimp + 0.25 * (np.roll(rimp, 1, 0) + np.roll(rimp, -1, 0))
        m = rimp.mean(0)
        _, _, R = np.linalg.svd(rimp - m)
        u, v = R[0], R[1]
        r2 = np.c_[(rimp - m) @ u, (rimp - m) @ v]
        path = MPath(r2)
        lo, hi = r2.min(0), r2.max(0)
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h * 0.866))
        gx[1::2] += h / 2
        g = np.c_[gx.ravel(), gy.ravel()]
        g = g[path.contains_points(g)]
        if len(g):
            d, _ = cKDTree(r2).query(g)
            g = g[d > 0.6 * h]
        pts2 = np.vstack([r2, g])
        tri = Delaunay(pts2).simplices
        tri = tri[path.contains_points(pts2[tri].mean(1))]
        p3 = np.vstack([rimp, m + g[:, :1] * u + g[:, 1:] * v])
        _, j = tree.query(p3)
        a3 = at[j].copy()
        # How far in from the edge (what the trim follows), measured across
        # the rim's plane.
        a3[:, -1] = np.r_[np.zeros(len(rimp)), cKDTree(r2).query(g)[0] if len(g) else []]
        base = sum(len(x) for x in P2)
        P2.append(p3)
        A2.append(a3)
        T2.append(tri + base)
    return np.vstack(P2), np.vstack(A2), np.vstack(T2)


def bubble(pos, tris, clear, out, ref=None):
    """A cup as a soap bubble blown in its rim, like a bra cup: nothing of
    her skin is kept but the rim, where the cup meets her. Across it, a
    membrane under even pressure: each point at its neighbours' middle,
    less the pressure along its normal (solved directly, the normals
    updated a few times), which settles perfectly smooth and round. The
    pressure is set, by halving, so the cup stands as high as her breast."""
    from scipy.sparse.linalg import splu
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    rim = np.zeros(len(pos), bool)
    rim[uk[c == 1].ravel()] = True
    inner = np.where(~rim)[0]
    A = adjacency(len(pos), tris).tocsr()
    L = (sparse.identity(len(pos)) - A).tocsr()
    Lii = splu(L[inner][:, inner].tocsc())
    Lib = L[inner][:, np.where(rim)[0]]
    xb = pos[rim]
    h = np.linalg.norm(pos[uk[:, 0]] - pos[uk[:, 1]], axis=1).mean()
    sign = 1.0 if (vertex_normals(pos, tris) * out).sum(1).mean() > 0 else -1.0

    def blow(p):
        x = pos.copy()
        for _ in range(12):
            n = sign * vertex_normals(x, tris)
            rhs = -(Lib @ xb) + p * h * h * n[inner]
            x[inner] = np.column_stack([Lii.solve(rhs[:, k]) for k in range(3)])
        return x

    # Sized to her: the cup stands as high off its rim as her breast does
    # under it, and a few millimetres more (her skin under a cup is not
    # drawn, so no small bump of hers needs clearing).
    right = (pos[:, 0] < 0) & ~rim
    up = out[right].mean(0)
    up /= np.linalg.norm(up)
    base = pos[rim & (pos[:, 0] < 0)].mean(0)

    def height(x):
        return ((x[right] - base) @ up).max()

    # Her breast's own height, from the sheet as it was cut from her.
    target = (((ref[ref[:, 0] < 0] - base) @ up).max() if ref is not None else height(pos)) + FULLER
    lo, hi = 0.0, 0.05
    while height(blow(hi)) < target and hi < 1e4:
        lo, hi = hi, hi * 2
    for _ in range(14):
        mid = (lo + hi) / 2
        if height(blow(mid)) < target:
            lo = mid
        else:
            hi = mid
    x = blow(hi)
    print("BUBBLE pressure %.3f, height %.4f (her breast %.4f)" % (hi, height(x), target - FULLER))
    return x


def taubin(pos, tris, rounds=40):
    """Creases, lumps and uneven patches taken out of a sheet without
    shrinking it (Taubin's smoothing: a step in, a slightly larger step back
    out); the more rounds, the larger the unevenness ironed out, while the
    size and fit stay. The edge stays put."""
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    onb = np.zeros(len(pos), bool)
    onb[uk[c == 1].ravel()] = True
    A = adjacency(len(pos), tris)
    for _ in range(rounds):
        for k in (0.5, -0.53):
            pos = np.where(onb[:, None], pos, pos + k * (A @ pos - pos))
    return pos


def fuller(pos, f, tris, most=0.004, reach=0.03):
    """A cup filled out where it runs toward the cleavage (her skin goes a
    little flat there, which in plate reads as pinched): lifted along its
    normal by up to `most`, nothing at its edge, the full amount `reach`
    inside it, and more toward the middle of her chest than the outside."""
    inward = np.clip(1 - np.abs(pos[:, 0]) / 0.14, 0, 1)
    t = np.clip(f / reach, 0, 1)
    lift = most * (t * t * (3 - 2 * t)) * (0.35 + 0.65 * inward)
    return pos + vertex_normals(pos, tris) * lift[:, None]


# Each bone's opposite number, for mirroring a piece's weights.
SWAP = np.array([BI.get(n[:-2] + {"_l": "_r", "_r": "_l"}[n[-2:]], i) if n[-2:] in ("_l", "_r") else i
                 for i, n in enumerate(BONES)])


def mirrored(pos, at, tris):
    """A pair made of its right half and that half's mirror image (her
    breasts are not quite each other's; the cups should be)."""
    keep = (pos[tris][:, :, 0] < 0).all(1)
    t = tris[keep]
    used = np.unique(t)
    re = -np.ones(len(pos), int)
    re[used] = np.arange(len(used))
    p, a, t = pos[used], at[used], re[t]
    mp = p * np.array([-1, 1, 1])
    ma = a.copy()
    ma[:, 0] *= -1                                   # the normal
    ma[:, 3:3 + NB] = a[:, 3:3 + NB][:, SWAP]        # the weights
    return np.vstack([p, mp]), np.vstack([a, ma]), np.vstack([t, t[:, ::-1] + len(p)])


def pushes_off_skin(pos, lift):
    """How far, and which way, each point must move to stand `lift` off her skin."""
    push = np.zeros_like(pos)
    for i in range(len(pos)):
        q, n, _, _ = BVH.find_nearest(Vector(pos[i]))
        if q is None:
            continue
        d = (Vector(pos[i]) - q).dot(n)
        if d < lift:
            push[i] = (n * (lift - d))[:]
    return push


def clear_of_skin(pos, lift, tris=None, spread=0.003, rounds=20, fall=0.9):
    """At least `lift` off her skin everywhere. With `tris`, the part of any
    push over `spread` is smoothed over the sheet, its way averaged with its
    neighbours' and its size never less than the point's own need, nor less
    than `fall` of theirs (so it fades out round the pushed patch): a plate
    lifted off a hollow moves as one piece. (Pushed point by point, each
    along its own nearest normal, the neck side of the ranger's second
    pauldron, 19 mm off her over the rise of her neck, was torn from 5 mm
    steps to 24 mm and its rim could not be bound.) Pushes under `spread`
    (every skin-tight piece's) are left exactly as they were."""
    push = pushes_off_skin(pos, lift)
    size = np.linalg.norm(push, axis=1)
    if tris is not None and len(tris) and size.max() > spread:
        over = push * (np.maximum(size - spread, 0) / np.maximum(size, 1e-12))[:, None]
        need = np.linalg.norm(over, axis=1)
        A = adjacency(len(pos), tris)
        eased = over.copy()
        for _ in range(rounds):
            m = A @ eased
            ml = np.linalg.norm(m, axis=1)
            mag = np.maximum(ml * fall, need)
            eased = np.where((ml > 1e-12)[:, None], m / np.maximum(ml, 1e-12)[:, None] * mag[:, None], eased)
        pos = pos + (push - over) + eased
        # (an eased push can lean off a point's own normal: made up here)
        push = pushes_off_skin(pos, lift)
        size = np.linalg.norm(push, axis=1)
        print("CLEAR eased pushes over %.0f mm (largest %.1f mm) out over the sheet" % (spread * 1000, np.linalg.norm(over, axis=1).max() * 1000 + spread * 1000))
    pos = pos + push
    if (size > 0).any():
        print("CLEAR pushed", int((size > 0).sum()), "of", len(pos))
    return pos


def dump(name, stage, pos, tris, field):
    """A piece's sheet at a stage of its making, saved for study (DUMP=its
    name in the environment)."""
    if name in os.environ.get("DUMP", "").split(","):
        np.savez(os.path.join(os.environ.get("TEMP", "."), f"dump_{name}_{stage}.npz"), pos=pos, tris=tris, field=field)


def over_nipples(pos, tris, least=0.003, s=0.009):
    """A garment cut over her filled breasts drawn over each nipple as a
    low, soft rise (`least` high, `s` its spread), so her nipples show
    through it as shapes; the tip of her nipple, through it, is hidden
    under it (the owner: hide the tip, leave the nipple visible). (Raised
    to clear all of her nipple, it was a cone.)"""
    nor = vertex_normals(pos, tris)
    out = pos.copy()
    for sd in ("l", "r"):
        tip = NIPPLE[sd]
        near = np.where(np.linalg.norm(pos - tip, axis=1) < 0.05)[0]
        if len(near) < 10:
            continue
        centre = pos[near[cKDTree(pos[near]).query(tip)[1]]]
        h = least
        d = np.linalg.norm(pos[near] - centre, axis=1)
        out[near] += nor[near] * (h * np.exp(-(d / s) ** 2))[:, None]
        print("NIPPLE RISE %s %.1f mm" % (sd, h * 1e3))
    return out


def piece(name, field, mkey, lift=0.003, thick=0.003, smooth=0, bevel=0.0012, trim=None, clear=None, soften=3, dome=False, keep_off=("Head", "neck_01"), cut=None, iron=0, hull=None, studs=None, budget=None, filled=False, edge=30, slot=True, bridge=False, bind=True):
    """A region of her skin made into a piece of her outfit. `trim`, as
    (material, width, height, thickness), edges it with a band laid on the
    piece itself, so the two can never part. `clear` is how close to the
    skin it may come once smoothed (the lift unless said): plate lifted well
    off and allowed close only at a peak keeps the peak as a hint, not a
    cast of it. `soften` eases the field first; a strap, narrower than
    some of her triangles, is not eased (easing would wear it through)."""
    # Never her head or hair (the hair is part of her mesh).
    slot_m = SLOT if slot is True else (SLOT & (X < 0) if slot == "right" else (SLOT & (X > 0) if slot == "left" else np.zeros(len(P), bool)))
    f = smooth_field(np.minimum.reduce([field, (0.3 - wsum(*keep_off)) * 0.1, (0.5 - HAIR) * 0.1,
                                        np.where(slot_m, -0.004, 1.0)]), soften)
    # `cut`, a second field, trims the piece after it is shaped: a cup
    # keeps the shape of the full cup however low it is cut.
    attr = np.hstack([N, W, (hull if hull is not None else -np.ones(len(P)))[:, None],
                      (cut if (cut is not None and not callable(cut)) else np.ones(len(P)))[:, None], f[:, None]])
    # A garment crossing her crotch is cut off just in front of and just
    # behind the slot between her thighs (`gap` is how far a point is out
    # of that box), and the two cut edges joined by a strip under her.
    gap = np.maximum.reduce([GAP_F - Y, Y - GAP_B, Z - GAP_Z, np.abs(X) - 0.07]) if bridge else np.ones(len(P))
    dump(name, "0skin", P_FILLED if (dome or filled) else P, TRI, np.minimum(f, gap))  # SOLVER1 TEMP
    pos, at, tris = clip(np.minimum(f, gap), P_FILLED if (dome or filled) else P, np.hstack([attr, gap[:, None]]), TRI)
    if len(tris) == 0:
        print("EMPTY", name)
        return []
    pos, at, tris = weld(pos, at, tris)
    dump(name, "1clip", pos, tris, at[:, -2])
    gap_at, at = at[:, -1], at[:, :-1]
    nor = at[:, :3] / (np.linalg.norm(at[:, :3], axis=1)[:, None] + 1e-12)
    pos = pos + nor * lift
    if hull is not None:
        pos = hulled(pos, at[:, -3], tris)
    pos = relax(pos, tris, interior=smooth, edge=edge)
    if iron:
        pos = taubin(pos, tris, rounds=iron)
    dump(name, "2shaped", pos, tris, at[:, -1])
    if filled and not dome:
        pos = over_nipples(pos, tris)
    if dome:
        cut_from, cut_at = pos.copy(), at.copy()
        pos, at, tris = even_cup(pos, at, tris)
        pos = bra_cup(pos, tris, at[:, -1], cut_from, cut_at[:, :3], FULLER)
        # Weights, normals and any cut, from where each point of the bowl
        # now stands over the sheet it replaced.
        _, j = cKDTree(cut_from).query(pos)
        edge = at[:, -1].copy()
        at = cut_at[j].copy()
        at[:, -1] = edge
        pos, at, tris = mirrored(pos, at, tris)
    if cut is not None:
        if callable(cut):
            at[:, -2] = cut(pos)
        at[:, -1] = np.minimum(at[:, -1], at[:, -2])
        cut_done = True
        pos, at, tris = clip(at[:, -2], pos, at, tris)
        pos, at, tris = weld(pos, at, tris)
        pos = relax(pos, tris, interior=0)
        dump(name, "3cut", pos, tris, at[:, -1])
    if not dome and not filled:
        pos = clear_of_skin(pos, lift if clear is None else clear, tris)
    dump(name, "3pre", pos, tris, at[:, -1])  # SOLVER1 TEMP
    # Every edge bound: in the trim's colour where one is asked, else in the
    # piece's own (a rolled hem). Sheer and painted pieces are left as cut.
    beads = []
    # (eased before its edge is bound, so the binding moves as the edge does)
    at[:, 3:3 + NB] = four_bones(eased_weights(pos, tris, at[:, 3:3 + NB]))
    if bind and len(SPEC[mkey]) < 7 and mkey != "ink":
        if trim:
            tkey, w, h, tt = trim
            bspec = (tkey, max(w, 0.005), max(h, 0.0006), 0.0018)
        else:
            bspec = (mkey, 0.0045, 0.0005, 0.0015)
        pos, beads = bind_edges(name, pos, at, tris, bspec[0], bspec[1], bspec[2], bspec[3], thick,
                                stitch=kind(mkey) == "leather")
        dump(name, "4bound", pos, tris, at[:, -1])
        trim = None
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget or (8000 if dome else 3000))] + beads
    if any("_stitch" in o.name for o in beads):
        made[0]["geo_stitch"] = True
    if bridge:
        made += crotch_bridge(name, pos, tris, gap_at, mkey, thick, bevel, trim, lift)
    if studs:
        made += rivets(name, pos, at, tris, thick, studs)
    if trim:
        tkey, w, h, tt = trim
        tp, ta, tr = clip(w - at[:, -1], pos, at, tris)
        if len(tr):
            tp, ta, tr = weld(tp, ta, tr)
            tp = relax(tp + vertex_normals(tp, tr) * (thick + h), tr, edge=30)
            made.append(finish(name + "_trim", tp, ta[:, 3:3 + NB], tr, tkey, tt, bevel, 1500))
    # Only the piece itself hides her skin: its binding, trim, studs and
    # stitches overhang its edge, and skin hidden under them showed as holes
    # in her just past it.
    for o in made:
        o["hides"] = o is made[0] and len(SPEC[mkey]) < 7
    return made


def rivets(name, pos, at, tris, thick, mkey, spacing=0.028, inset=0.011, r=0.0032):
    """Domed rivets set in from a piece's edge every `spacing`, on its
    outer face: the detail that makes a plate read as made."""
    f = at[:, -1]
    cand = np.where(np.abs(f - inset) < 0.0025)[0]
    if len(cand) == 0:
        return []
    picked = []
    tree_p = []
    for i in cand[np.argsort(pos[cand, 2])]:
        if all(np.linalg.norm(pos[i] - q) >= spacing for q in tree_p):
            picked.append(i)
            tree_p.append(pos[i])
    nor = vertex_normals(pos, tris)
    P2, W2, T2 = [], [], []
    nu, nv = 12, 4
    for i in picked:
        n = nor[i]
        t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        t /= np.linalg.norm(t)
        b = np.cross(n, t)
        base = pos[i] + n * (thick + 0.0003)
        pts = [base + n * r * 0.75]
        for k in range(1, nv + 1):
            th = (np.pi / 2) * k / nv
            for j in range(nu):
                ph = 2 * np.pi * j / nu
                pts.append(base + (np.cos(ph) * t + np.sin(ph) * b) * r * np.sin(th) + n * r * 0.75 * np.cos(th))
        o = sum(len(x) for x in P2)
        tri = [(o, o + 1 + j, o + 1 + (j + 1) % nu) for j in range(nu)]
        for k in range(nv - 1):
            a0, b0 = o + 1 + k * nu, o + 1 + (k + 1) * nu
            for j in range(nu):
                j1 = (j + 1) % nu
                tri += [(a0 + j, b0 + j, b0 + j1), (a0 + j, b0 + j1, a0 + j1)]
        P2.append(np.array(pts))
        W2.append(np.repeat(at[i:i + 1, 3:3 + NB], len(pts), 0))
        T2.append(np.array(tri))
    if not P2:
        return []
    pp, ww, tt = np.vstack(P2), np.vstack(W2), np.vstack(T2)
    if (vertex_normals(pp, tt) * (pp - np.repeat(np.array([pos[i] for i in picked]), (nv * nu + 1), 0))).sum(1).mean() < 0:
        tt = tt[:, ::-1]
    print("RIVETS", name, len(picked))
    return [finish(name + "_rivets", pp, ww, tt, mkey, 0.0002, 0.0, 10 ** 7)]


def islands(pos, tris, keep_frac=0.02):
    """Triangles of a sheet in pieces too small to be meant (scraps a cut
    leaves): only pieces with at least keep_frac of the sheet are kept."""
    n = len(pos)
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]]])
    g = sparse.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    k, lab = sparse.csgraph.connected_components(g, directed=False)
    if k == 1:
        return tris
    size = np.bincount(lab[tris[:, 0]], minlength=k)
    good = size >= keep_frac * len(tris)
    return tris[good[lab[tris[:, 0]]]]


ARM_BONES = [BI[n] for n in BONES if n.split("_")[0] in ("clavicle", "upperarm", "lowerarm", "hand")]
BREAST_BONES = [BI[n] for n in ("breast_l", "breast_r") if n in BI]


UNSTEADIED = set()  # pieces that keep her skin's own weights over her breasts (bandeau)


def steady_on_breasts(wt, least=0.01, full=0.1):
    """Weights with her arms' share taken off where her breasts have any:
    none at `least` of her breasts' weight, all of it by `full` (that share
    given to the rest, in proportion; her upper chest's bone if nothing else
    is left). (Taken off all at once at a line, the line stepped the
    arcanist's neckline when she moved.)"""
    wt = np.array(wt, float)
    b = wt[:, BREAST_BONES].sum(1)
    on = b > least
    if not on.any():
        return wt
    k = np.clip((b[on] - least) / (full - least), 0, 1)
    k = k * k * (3 - 2 * k)
    w = wt[on].copy()
    w[:, ARM_BONES] *= (1 - k)[:, None]
    tot = w.sum(1)
    empty = tot < 1e-6
    w[empty, BI["spine_03"]] = 1
    tot[empty] = 1
    wt[on] = w / tot[:, None]
    return wt


def four_bones(wt):
    """At most four bones to a point, as the game takes them, cut smoothly:
    every weight less the point's fifth largest. (Left to the exporter,
    which keeps each point's four largest, neighbours kept different fours
    where a fourth and a fifth crossed, and an edge stepped there when she
    moved.)"""
    wt = np.array(wt, float)
    if wt.shape[1] <= 4:
        return wt
    fifth = -np.partition(-wt, 4, axis=1)[:, 4]
    wt = np.maximum(wt - fifth[:, None], 0)
    return wt / np.maximum(wt.sum(1, keepdims=True), 1e-9)


def eased_weights(pos, tris, wt, over=0.008):
    """Weights eased over about `over` of a sheet: her skin's weights are
    uneven from point to point, and an edge that took them as they are was
    pulled into steps and tears when she moved (her belts were, before
    theirs were eased too)."""
    if not len(tris):
        return wt
    el = np.linalg.norm(pos[tris[:, 0]] - pos[tris[:, 1]], axis=1)
    rounds = int(np.clip((over / max(float(np.median(el)), 1e-4)) ** 2, 0, 80))
    if not rounds:
        return wt
    A_ = adjacency(len(pos), tris)
    wt = np.array(wt, float)
    for _ in range(rounds):
        wt = A_ @ wt
    return wt / np.maximum(wt.sum(1, keepdims=True), 1e-9)


def pinholes_filled(name, pos, wt, tris, most=0.03):
    """Any small hole inside a sheet (a pocket where the field it was cut
    by dipped below nothing: it showed as a black notch in her suit) closed
    with a fan of triangles, wound as its neighbours are. Its edges proper,
    however short, are each at least a quarter of its longest."""
    from collections import defaultdict
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]).tolist()
    have = set(map(tuple, e))
    nxt = defaultdict(list)
    for a, b in e:
        if (b, a) not in have:
            nxt[a].append(b)
    loops = []
    while nxt:
        start = next(iter(nxt))
        loop, v = [start], start
        while v in nxt:
            w = nxt[v].pop()
            if not nxt[v]:
                del nxt[v]
            if w == start:
                break
            loop.append(w)
            v = w
        loops.append(loop)
    if len(loops) < 2:
        return pos, wt, tris
    per = [float(np.linalg.norm(pos[lp] - pos[np.roll(lp, 1)], axis=1).sum()) for lp in loops]
    big = max(per)
    nrm = vertex_normals(pos, tris)
    add_p, add_w, add_t = [], [], []
    for lp, pr in zip(loops, per):
        if len(lp) < 3 or len(set(lp)) < len(lp) or pr >= most or pr >= big * 0.25:
            continue
        # A hole's fill faces the way the sheet round it does; a loop round
        # a small piece of its own (a fringe's tongue, a strip of trim)
        # would be filled facing against it, over the piece: never that.
        cen = pos[lp].mean(0)
        a_, b_ = pos[lp], pos[np.roll(lp, -1)]
        fan = np.cross(a_ - b_, cen - b_)
        if (fan * nrm[lp]).sum() <= 0:
            continue
        k = len(pos) + len(add_p)
        add_p.append(cen)
        add_w.append(wt[lp].mean(0))
        add_t += [[b, a, k] for a, b in zip(lp, np.roll(lp, -1))]
    if not add_p:
        return pos, wt, tris
    print("PINHOLES closed in %s: %d" % (name, len(add_p)))
    return np.vstack([pos, add_p]), np.vstack([wt, add_w]), np.vstack([tris, np.array(add_t, int)])


def finish(name, pos, wt, tris, mkey, thick, bevel, budget=3000, scraps=True):
    """A sheet made a piece: her weights, its texture laid out at true size,
    a thickness and a rounded edge, bound to her skeleton. The sheet is
    first thinned to `budget` triangles (cut from a finely divided skin,
    it carries far more than its shape needs)."""
    # Any point that came out of the shaping as no number at all is dropped,
    # with the triangles it was part of.
    okp = np.isfinite(pos).all(1)
    if not okp.all():
        print("DROPPED", int((~okp).sum()), "broken points of", name)
        tris = tris[okp[tris].all(1)]
        pos = np.where(okp[:, None], pos, 0.0)
    # (scraps a cut leaves are dropped; a piece made of many small parts
    # on purpose, stitches, keeps them all)
    if scraps:
        # (points on top of each other made one, and the flat triangles
        # between them dropped: they have no facing, and thickened, stood
        # out as spikes)
        pos, wt, tris = weld(pos, np.asarray(wt, float), tris, r=0.0002)
        tris = islands(pos, tris)
        pos, wt, tris = pinholes_filled(name, pos, wt, tris)
    # Its true edge, the sheet's border before it is thickened (both faces of
    # it): the shader's stitching and worn edges are measured from this. A
    # guess from its shape took any crease for an edge, and stitched rings
    # round them in the middle of a panel.
    e_ = np.sort(np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1)
    uk_, cnt_ = np.unique(e_, axis=0, return_counts=True)
    be = uk_[cnt_ == 1]
    rim = None
    if len(be):
        t_ = np.linspace(0, 1, 4, endpoint=False)
        a_, b_ = pos[be[:, 0]], pos[be[:, 1]]
        rim = (a_[:, None] + (b_ - a_)[:, None] * t_[None, :, None]).reshape(-1, 3)
        rn = vertex_normals(pos, tris)[np.repeat(be[:, 0], len(t_))]
        rim = np.vstack([rim, rim + rn * thick])
        rim = rim[np.isfinite(rim).all(1)]
    # Over her breasts a piece moves with her body and breasts, never her
    # arms: her skin at the outer curve of each breast is partly her arm's,
    # and a garment taking that from it is dragged out of shape when her arm
    # moves (the skin under it is hidden). But at its edges it keeps her
    # skin's own weights, eased in over 3 cm: there her skin is seen, and
    # with her arm's share gone from the edge alone, her skin drew away from
    # under a plate cup's top as she ran, and you saw down into the cup.
    steady = np.asarray(wt, float) if any(name.startswith(n) for n in UNSTEADIED) else steady_on_breasts(wt)
    if len(be):
        d_ = cKDTree(pos[np.unique(be)]).query(pos)[0]
        s_ = np.clip((d_ - 0.005) / 0.025, 0, 1)
        s_ = (s_ * s_ * (3 - 2 * s_))[:, None]
        wt = steady * s_ + np.asarray(wt, float) * (1 - s_)
    else:
        wt = steady
    if scraps:
        wt = eased_weights(pos, tris, wt)
    # No point left without a bone (it would stay behind when she moves):
    # those take the weights of her skin nearest them.
    tot = wt.sum(1)
    if (tot < 0.01).any():
        _, jz = cKDTree(P).query(pos[tot < 0.01])
        wt = wt.copy()
        wt[tot < 0.01] = W[jz]
    wt = four_bones(wt)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pos], [], tris.tolist())
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    if rim is not None and len(rim):
        obj["rim"] = rim.astype(np.float32).ravel().tolist()
    groups = {}
    for i in range(len(wt)):
        top = np.argsort(-wt[i])[:4]
        tot = wt[i, top].sum() or 1
        for j in top:
            if wt[i, j] > 0.003:
                if j not in groups:
                    groups[j] = obj.vertex_groups.new(name=BONES[j])
                groups[j].add([i], float(wt[i, j] / tot), "REPLACE")
    me.validate(clean_customdata=False)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # A piece that faces mostly one way (a cup, a plate, a knee) is laid out
    # in one projection along that way: no seams for the texture to break at.
    fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
    ax = fn.sum(0)
    ax /= np.linalg.norm(ax) + 1e-12
    facing = (fn / (np.linalg.norm(fn, axis=1)[:, None] + 1e-12)) @ ax
    uv = me.uv_layers.new().data
    if np.percentile(facing, 2) > 0.15:
        u = np.cross(ax, [0, 0, 1] if abs(ax[2]) < 0.9 else [1, 0, 0])
        u /= np.linalg.norm(u)
        v = np.cross(ax, u)
        for poly in me.polygons:
            for li in poly.loop_indices:
                co = np.array(me.vertices[me.loops[li].vertex_index].co[:])
                uv[li].uv = (float(co @ u), float(co @ v))
    else:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
    uv = me.uv_layers.active.data
    a3 = sum(p.area for p in me.polygons)
    a2 = 0.0
    for p in me.polygons:
        l = [uv[k].uv for k in p.loop_indices]
        for k in range(1, len(l) - 1):
            a2 += abs((l[k] - l[0]).cross(l[k + 1] - l[0])) / 2
    k = math.sqrt(a3 / max(a2, 1e-12)) * SPEC[mkey][3]
    for d in uv:
        d.uv = d.uv * k
    me.materials.append(mat(mkey))
    for p in me.polygons:
        p.use_smooth = True
    # A large piece keeps enough triangles to hold her curves (thinned too
    # far, it flattens and her skin pokes through between its points).
    area = sum(p.area for p in me.polygons)
    budget = max(budget, int(area * 60000))
    if len(me.polygons) > budget:
        # Only the inside is thinned: the edge and two rows in from it keep
        # every point, so a cut line stays the smooth curve it was made.
        e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
        uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
        keep = np.zeros(len(pos))
        keep[uk[c == 1].ravel()] = 1
        A = adjacency(len(pos), tris)
        for _ in range(2):
            keep = np.maximum(keep, (A @ keep > 0).astype(float))
        inner = obj.vertex_groups.new(name="_thin")
        inner.add([int(i) for i in np.where(keep == 0)[0]], 1.0, "REPLACE")
        dc = obj.modifiers.new("thin", "DECIMATE")
        dc.decimate_type = "COLLAPSE"
        dc.vertex_group = "_thin"
        dc.vertex_group_factor = 1000.0
        dc.ratio = budget / len(me.polygons)
        dc.use_symmetry = bool(abs(pos[:, 0].mean()) < 0.02)
        dc.symmetry_axis = "X"
    # (A sheer piece is one sheet: layered, it would not be sheer.)
    so = obj.modifiers.new("thick", "SOLIDIFY") if thick > 0 else None
    if so:
        so.thickness = thick
        so.offset = 1
        so.use_even_offset = False
        so.use_quality_normals = True
        so.use_rim = True
    if bevel > 0:
        bv = obj.modifiers.new("edge", "BEVEL")
        bv.width = min(bevel, thick * 0.45)
        bv.segments = 2
        bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(50)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if "_thin" in obj.vertex_groups:
        obj.vertex_groups.remove(obj.vertex_groups["_thin"])
    # After thickening and bevelling, any point left without a bone takes
    # the weights of the nearest point that has some.
    vs = obj.data.vertices
    tot = np.array([sum(g.weight for g in v.groups) for v in vs])
    fin = np.array([all(math.isfinite(c) for c in v.co) for v in vs])
    bare = np.where((tot < 0.01) & fin)[0]
    if len(bare):
        good = np.where((tot >= 0.01) & fin)[0]
        gco = np.array([vs[i].co[:] for i in good])
        _, jn = cKDTree(gco).query(np.array([vs[i].co[:] for i in bare]))
        for i, j in zip(bare, good[jn]):
            for g in vs[j].groups:
                obj.vertex_groups[g.group].add([int(i)], g.weight, "REPLACE")
        print("WEIGHTS given to", len(bare), "bare points of", name)
    me.set_sharp_from_angle(angle=math.radians(50))
    obj.parent = arm
    am = obj.modifiers.new("Armature", "ARMATURE")
    am.object = arm
    print("PIECE", name, len(me.polygons), "faces")
    return obj


# ------------------------------------------------------------- the cuts --
def bottom(style, top=0.075, side_rise=0.05, gusset=0.022):
    """Briefs: the front a panel from the crotch widening to the hips, the
    top edge low in front and rising over the hip bones; `style` shapes the
    seat: 'full', 'cheeky' (the lower cheeks bare) or 'thong'."""
    ax = np.abs(X)
    top_line = CROTCH + top + side_rise * np.clip(ax / 0.15, 0, 1) ** 2 + 0.035
    rise = np.maximum(Z - CROTCH, 0)
    front_w = gusset + rise * 1.9
    if style == "thong":
        back_w = 0.008 + ramp(Z, CROTCH + 0.1, top_line - 0.01) * 0.16 + rise * 0.05
    elif style == "cheeky":
        back_w = gusset + rise * 1.1
    else:
        back_w = gusset + rise * 2.2
    w = front_w * FRONT + back_w * (1 - FRONT)
    panel = AND(w - ax, top_line - Z, Z - (CROTCH - 0.02))
    band = AND(top_line - Z, Z - (top_line - 0.022), 0.25 - ax, 0.5 - LEGW["l"] - LEGW["r"])
    return OR(panel, band)


# Nothing but a cup on her breasts (a band or corset running up under one
# would stand off it as a shelf): positive off them, in metres-ish.
# Off her breasts and out from under them (where a breast hangs over her
# ribs, a band or corset would stand off it as a shelf), so torso pieces
# end flush on her ribs, short of the breast.
def _off_breast():
    wb = wsum("breast_l", "breast_r")
    bp = P[wb > 0.02]
    tree = cKDTree(bp[:, :2])
    under = np.zeros(len(P), bool)
    for i, nb in enumerate(tree.query_ball_point(P[:, :2], 0.015)):
        if nb:
            dz = bp[nb, 2] - P[i, 2]
            under[i] = ((dz > 0.002) & (dz < 0.009)).any()
    # In or out, eased over her surface into a smooth slope, so the line
    # where a piece ends is one even curve, not the triangles' steps.
    f = np.where(under | (wb > 0.003), -1.0, 1.0)
    for _ in range(60):
        f = 0.5 * f + 0.5 * (ADJ @ f)
    return np.where(f > 0.6, 1.0, f * 0.03)


OFF_BREAST = _off_breast()


def hero_briefs(top=0.125, cut=0.95):
    """Briefs as a superhero wears them over her suit: broad across the
    front and seat up to a waistband `top` above the crotch, the leg holes
    cut high, rising toward the hips at slope `cut`."""
    ax = np.abs(X)
    legs = (Z - CROTCH + 0.02) - cut * np.maximum(ax - 0.03, 0) * (0.75 + 0.25 * FRONT)
    return AND((CROTCH + top) - Z, Z - (CROTCH - 0.03), legs, 0.3 - ARMW["l"] - ARMW["r"])


def cups(cover=0.62, plunge=0.02, band=0.03, over=0.022, reach=0.088):
    """A half-cup under each breast and the band under them: the cup holds
    the breast from below, its top edge `over` above the nipple and dipping
    toward the middle, so the upper breast shows; `reach` is how far round
    the breast it comes; its inner edge leaves `plunge` of the cleavage
    bare. (`cover` is kept for callers; the nipple sets the line.)"""
    parts = []
    for sd, s in (("l", 1), ("r", -1)):
        n = NIP[sd]
        nip = NIPPLE[sd]
        c = n + np.array([0, 0.035, -0.012])
        r = np.linalg.norm(P - c, axis=1)
        top = nip[2] + over - 0.45 * np.maximum(0, abs(nip[0]) - np.abs(X)) - 0.3 * np.maximum(0, np.abs(X) - abs(nip[0]) - 0.02)
        parts.append(AND(reach - r, top - Z, X * s - plunge, -(Y - 0.02)))
    ub = AND(Z - (UNDERBUST - band - 0.03), UNDERBUST + 0.006 - Z, 0.4 - ARMW["l"] - ARMW["r"], OFF_BREAST)
    return OR(*parts), ub


def ribbon(name, ctrl, width, mkey, lift=0.0035, thick=0.0025, cols=5, trim=None, snap=True, centre=None,
           hides=False, follow=False, flare=None):
    """A strap as a strap is made: a ribbon of even width laid along a
    smooth curve on her skin, so its edges are two clean parallel lines.
    It moves with the skin under each point of it. With `centre` (a point
    inside her), it is laid on her by looking out from there through each
    point of it: the skin nearest a point inside her can jump from one
    curve of her to another (from her breast to her chest), and kinked it.
    `hides`: her skin under it is tucked in, as under a fitted piece (a
    gusset or a thong's string, which she must never show through).
    `follow`: each line along it moves with the skin under that line, as
    stretched cloth does, rather than the whole width as one strap (a
    gusset: her thighs part the skin under its edges, and a strap's edges,
    staying put, let it out from under them). `flare` (width, length): the
    ribbon widens to that width over that length at its end, as a thong's
    string opens into its gusset."""
    def lay(pts):
        if centre is None:
            return np.array([SKIN_BVH.find_nearest(Vector(p))[0][:] for p in pts])
        o = np.asarray(centre, float)
        out_ = []
        for p in pts:
            d = np.asarray(p) - o
            hit = SKIN_BVH.ray_cast(Vector(o), Vector(d / np.linalg.norm(d)), 1.0)
            out_.append(np.array(hit[0][:]) if hit[0] is not None else np.array(SKIN_BVH.find_nearest(Vector(p))[0][:]))
        return np.array(out_)
    # (columns fine enough that a trim along its edges is a clean line)
    cols = max(cols, int(np.ceil(max(width, flare[0] if flare else 0.0) / 0.0015)) + 1)
    # (a smooth curve through its points, not straight runs between them:
    # those met at corners, and a strap kinked at each)
    c = spline(ctrl, step=0.003)
    if snap:
        c = lay(c)
    # (not snapped, it is taut, as given: it bridges a hollow rather than
    # sinking into it)
    for _ in range(3):
        c[1:-1] = (c[:-2] + 2 * c[1:-1] + c[2:]) / 4
        if snap:
            c = lay(c)
    nrm = np.array([SKIN_BVH.find_nearest(Vector(p))[1][:] for p in c])
    for _ in range(4):
        nrm[1:-1] = (nrm[:-2] + 2 * nrm[1:-1] + nrm[2:]) / 4
    nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    tg = np.gradient(c, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
    bn = np.cross(nrm, tg)
    bn /= np.linalg.norm(bn, axis=1)[:, None] + 1e-12
    off = np.linspace(-0.5, 0.5, cols)
    wrow = np.full(len(c), width)
    if flare:
        run = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
        wrow = width + (flare[0] - width) * ramp(run, run[-1] - flare[1], run[-1])
    pos = (c[:, None, :] + nrm[:, None, :] * lift + bn[:, None, :] * (off[None, :] * wrow[:, None])[:, :, None]).reshape(-1, 3)
    tris = grid(len(c), cols)
    nor = vertex_normals(pos, tris)
    if (nor * np.repeat(nrm, cols, 0)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    # (one set of weights across its width, eased along it: it moves as a
    # strap; or, following, each line along it its own)
    wt = soft_weights(pos).reshape(len(c), cols, -1)
    if not follow:
        wt[:] = wt.mean(1, keepdims=True)
    for _ in range(6):
        wt[1:-1] = (wt[:-2] + 2 * wt[1:-1] + wt[2:]) / 4
    edge = (wrow[:, None] / 2 - np.abs(off[None, :] * wrow[:, None])).ravel()
    at = np.hstack([nor, wt.reshape(len(pos), -1), edge[:, None]])
    made = trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim, budget=10 ** 7)
    for o in made:
        o["hides"] = hides and o is made[0]
    if kind(mkey) == "leather" and width >= 0.012:
        inset = 0.0028
        for k, sgn in enumerate((1, -1)):
            ln = c + nrm * (lift + thick + 0.0001) + bn[:] * (sgn * (wrow[:, None] / 2 - inset))
            made += stitches(f"{name}_stitch{k}", ln, nrm, tg, pos, at[:, 3:3 + NB])
        made[0]["geo_stitch"] = True
    return made


def shoulder_strap_curves():
    out = []
    for sd, s in (("l", 1), ("r", -1)):
        n = NIP[sd]
        out.append([n + np.array([0.012 * s, 0, 0.065]), np.array([0.105 * s, -0.04, 1.52]), np.array([0.11 * s, 0.03, 1.565]),
                    np.array([0.1 * s, 0.11, 1.47]), np.array([0.085 * s, 0.12, UNDERBUST - 0.02])])
    return out


def shoulder_straps(width=0.016):
    f = []
    for sd, s in (("l", 1), ("r", -1)):
        n = NIP[sd]
        pts = [n + np.array([0.012 * s, 0, 0.065]), np.array([0.105 * s, -0.04, 1.52]), np.array([0.11 * s, 0.03, 1.565]),
               np.array([0.1 * s, 0.11, 1.47]), np.array([0.085 * s, 0.12, UNDERBUST - 0.02])]
        f.append(strap(pts, width))
    return OR(*f)


def limb(sd, s0, s1, legs=True, front_dip=0.0):
    """A sleeve of a limb from s0 to s1 along it (metres from the hip or the
    collarbone); its top edge dips at the back by front_dip."""
    S = LEG_S[sd] if legs else ARM_S[sd]
    Wm = LEGW[sd] if legs else ARMW[sd]
    top = s0 - front_dip * (1 - FRONT)
    return AND(S - top, s1 - S, Wm - 0.5)


def cap(center, radius):
    c = skin_point(center)
    return radius - np.linalg.norm(P - c, axis=1)


def shoulder(sd):
    return head(f"upperarm_{sd}") + np.array([0.02 * (1 if sd == "l" else -1), 0, 0.06])


# Where the last cups made hold their straps (their peaks, outside) and meet
# (their inner rims' lowest point), for the pieces fixed to them.
CUP_PEAK = {}
CUP_LOW = None


def plate_cups(name, mkey, top, lift=0.003, thick=0.003, trim=None, studs=None, gap=0.011, side=0.07, only=None):
    """A pair of plate cups, each a smooth form rather than a cast of her:
    her breasts' form (breast_form: both, her left mirrored onto her right,
    so the pair is one shape and holds either; a few millimetres off her at
    most), `lift` more. Nothing of her skin's own lumps reaches it; her
    nipples, filled under it, are hidden where they would show through it.
    Below and at
    the side it ends where it meets her (it goes into her chest there, as a
    breast does), a clean seam; above, it is cut to the line `top(|x|)` (a
    height for each distance from her middle: a plunge falls toward her
    middle); inside, `gap` from her middle; outside, `side` past her nipple.
    Made on her right and mirrored onto her left (with `only`, that side
    alone), its weights from her skin nearest it (it moves, and swings, with
    her)."""
    sd, s_ = "r", -1
    nip = NIPPLE[sd]
    mirror = np.array([-1.0, 1.0, 1.0])
    c, R, ax, form = BREAST_FORM
    # The form as an even mesh of triangles (a geodesic sphere, ~2 mm apart
    # over it): no poles. (A grid by angles has one at the front of each
    # breast, where its lines crowd together, were welded into a flat disc,
    # and showed as a dent at the nipple.) Then `lift` off it.
    ico = bmesh.new()
    bmesh.ops.create_icosphere(ico, subdivisions=6, radius=1.0)
    unit = np.array([v.co[:] for v in ico.verts])
    tris = np.array([[v.index for v in f.verts] for f in ico.faces])
    ico.free()
    unit /= np.linalg.norm(unit, axis=1)[:, None]
    pos = c + (unit * ax * form(unit)[:, None]) @ R
    nor = vertex_normals(pos, tris)
    if (nor * (pos - c)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    pos = pos + nor * lift
    # Where it meets her, as a drawn line: round the axis through her
    # nipple, at each bearing, how far out from it the plate still stands
    # clear of her (of her skin with the nipples filled; which side of her
    # it is, by the plate's own normal: her filled nipple's folded
    # triangles face every way, and cut a ring round it), never past the
    # first place it goes into her, and eased round. (Cut where it met her
    # skin, a snug plate met it so shallowly that the edge wandered.)
    global FILLED_BVH
    if FILLED_BVH is None:
        FILLED_BVH = BVHTree.FromPolygons([tuple(p) for p in P_FILLED], TRI.tolist())
    out_of = np.zeros(len(pos))
    for i, q in enumerate(pos):
        v_ = np.array(q) - np.array(FILLED_BVH.find_nearest(Vector(q))[0][:])
        out_of[i] = np.linalg.norm(v_) * np.sign(v_ @ nor[i])
    un = ((nip - c) @ R.T) / ax
    un /= np.linalg.norm(un)
    e1 = np.cross(un, [0.0, 0.0, 1.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(un, e1)
    theta = np.arccos(np.clip(unit @ un, -1, 1))
    bins = 120
    phi_f = (np.arctan2(unit @ e2, unit @ e1) + np.pi) / (2 * np.pi) * bins
    phi = phi_f.astype(int) % bins
    reach = np.full(bins, np.pi)
    inside = (out_of < lift * 0.5) & (theta > 0.25)
    np.minimum.at(reach, phi[inside], theta[inside])
    from scipy.ndimage import gaussian_filter1d, minimum_filter1d
    reach = gaussian_filter1d(minimum_filter1d(reach, 9, mode="wrap"), 4, mode="wrap") - 0.01
    reach_at = np.interp(phi_f - 0.5, np.arange(-1, bins + 1), np.r_[reach[-1], reach, reach[0]])
    axs = np.abs(pos[:, 0])
    f = np.minimum.reduce([top(axs) - pos[:, 2], axs - gap, abs(nip[0]) + side - axs, (reach_at - theta) * 0.08,
                           # (her right side only: the left is its mirror)
                           -pos[:, 0] - 0.001])
    _, j = cKDTree(P).query(pos)
    attr = np.hstack([nor, W[j].astype(float), np.zeros((len(pos), 1))])
    pos, at, tris = clip(f, pos, attr, tris)
    pos, at, tris = weld(pos, at, tris)
    tris = islands(pos, tris, keep_frac=0.2)
    loops = edge_loops(tris)
    rim = np.unique(np.concatenate([np.array(lp) for lp in loops])) if loops else np.arange(0)
    at[:, -1] = cKDTree(pos[rim]).query(pos)[0] if len(rim) else 0.05
    # Its peak at the outside, where a strap holds it (for the outfit's straps).
    outer = rim[np.abs(pos[rim, 0]) > abs(nip[0]) * 0.85]
    CUP_PEAK["r"] = pos[outer[np.argmax(pos[outer, 2])]]
    CUP_PEAK["l"] = CUP_PEAK["r"] * mirror
    inner = rim[np.abs(pos[rim, 0]) < gap + 0.006]
    global CUP_LOW
    CUP_LOW = pos[inner[np.argmin(pos[inner, 2])]] if len(inner) else np.array([0.0, nip[1], UNDERBUST])
    pos2 = np.vstack([pos, pos * mirror])
    at2 = np.vstack([at, np.hstack([at[:, :3] * mirror, at[:, 3:3 + NB][:, SWAP], at[:, -1:]])])
    tris2 = np.vstack([tris, tris[:, ::-1] + len(pos)])
    if only == "r":
        pos2, at2, tris2 = pos, at, tris
    elif only == "l":
        pos2, at2, tris2 = pos2[len(pos):], at2[len(pos):], tris[:, ::-1]
    beads = []
    if trim:
        tkey, w, h, tt = trim
        pos2, beads = bind_edges(name, pos2, at2, tris2, tkey, max(w, 0.005), max(h, 0.0006), 0.0018, thick)
    made = [finish(name, pos2, at2[:, 3:3 + NB], tris2, mkey, thick, 0.0006, 10 ** 7)] + beads
    if studs:
        made += rivets(name, pos2, at2, tris2, thick, studs)
    for o_ in made:
        o_["hides"] = o_ is made[0]
    print("PLATE CUP %s: %d points" % (name, len(pos2)))
    return made


def trimmed(name, pos, at, tris, mkey, thick, bevel, trim, budget=3000):
    """A sheet and, if asked, the gold along its edge (the field in `at`'s
    last column is the distance in from the edge)."""
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget)]
    if trim:
        tkey, w, h, tt = trim
        tp, ta, tr = clip(w - at[:, -1], pos, at, tris)
        if len(tr):
            tp, ta, tr = weld(tp, ta, tr)
            tp = relax(tp + vertex_normals(tp, tr) * (thick + h), tr, edge=30)
            made.append(finish(name + "_trim", tp, ta[:, 3:3 + NB], tr, tkey, tt, bevel))
    return made


def grid(nu, nv):
    i = np.arange(nu - 1)[:, None] * nv + np.arange(nv - 1)[None, :]
    i = i.ravel()
    return np.vstack([np.c_[i, i + nv, i + 1], np.c_[i + 1, i + nv, i + nv + 1]])


def fringe(hem, strips, depth, notch=0.18):
    """A hem cut into `strips` strips: between each, a V-notch `depth` deep
    and `notch` of a strip wide, so the leather hangs in tongues."""
    def f(u):
        ph = ((u + 1) / 2 * strips) % 1.0
        v = max(0.0, 1 - abs(ph - 1.0 if ph > 0.5 else ph) / (notch / 2))
        return hem(u) + depth * v
    return f


def hanging(name, a0, a1, z_top, hem, mkey, flare=0.15, lift=0.01, gap=0.012, thick=0.0025, trim=None, nu=56, snug=None):
    """Cloth hanging from her hips, all round her between the angles a0 and
    a1 (radians; 0 her front, rising toward her left): at each angle it
    falls from the hips, flaring out by `flare` a metre of fall, and never
    nearer her than `gap` (so it goes over her thighs, not into them). Its
    hem is `hem(u)`, u from -1 at a0 to 1 at a1. It is weighted to the
    pelvis at the top and more and more to the thigh on its side below the
    hip, so it swings with her stride.
    `z_top` may be a function of the angle (a plate hung from under a belt
    follows the belt's line). With `snug` it is tucked: only `snug` off her at
    its top, easing to `gap` over its first 5 cm, and its top edge (hidden
    under what it hangs from) is not trimmed."""
    a = np.linspace(a0, a1, nu)
    top = np.asarray(z_top(a), float) if callable(z_top) else np.full(nu, float(z_top))
    zmax = float(top.max())
    ring = (np.abs(Z - zmax) < 0.008) & (ARMW["l"] + ARMW["r"] < 0.3)
    cy = (Y[ring].min() + Y[ring].max()) / 2
    zs = np.arange(zmax, min(hem(u) for u in np.linspace(-1, 1, 41)) - 0.03, -0.006)
    body = (ARMW["l"] + ARMW["r"] < 0.3) & (wsum("Head") < 0.3)
    ang = np.arctan2(X, -(Y - cy))
    rad = np.hypot(X, Y - cy)
    R = np.full((len(zs), nu), np.nan)
    for k, z in enumerate(zs):
        m = body & (np.abs(Z - z) < 0.006)
        if not m.any():
            continue
        for j, aj in enumerate(a):
            d = np.abs((ang[m] - aj + np.pi) % (2 * np.pi) - np.pi)
            w = d < 0.12
            if w.any():
                R[k, j] = rad[m][w].max()
    R[0] = np.where(np.isnan(R[0]), np.nanmax(R[0]), R[0])
    # (her radius at each angle's own top, from the levels measured there)
    R_top = np.array([np.interp(top[j], zs[::-1], np.where(np.isnan(R[::-1, j]), R[0, j], R[::-1, j])) for j in range(nu)])
    for k in range(1, len(zs)):
        R[k] = np.where(np.isnan(R[k]), 0, R[k])
    fall = np.maximum(top[None, :] - zs[:, None], 0)
    clear = gap if snug is None else snug + (gap - snug) * ramp(fall, 0.0, 0.05)
    hang = (R_top + lift)[None, :] + flare * fall
    r = np.maximum(hang, R + clear)
    r = np.maximum.accumulate(r, axis=0)
    for _ in range(6):
        r[1:-1] = (r[:-2] + 2 * r[1:-1] + r[2:]) / 4
        r[:, 1:-1] = (r[:, :-2] + 2 * r[:, 1:-1] + r[:, 2:]) / 4
        r = np.maximum(r, R + clear)
    zz = np.repeat(zs[:, None], nu, 1)
    aa = np.repeat(a[None, :], len(zs), 0)
    pos = np.stack([r * np.sin(aa), cy - r * np.cos(aa), zz], -1).reshape(-1, 3)
    tris = grid(len(zs), nu)
    nor = vertex_normals(pos, tris)
    out = np.c_[np.sin(aa).ravel(), -np.cos(aa).ravel()]
    if ((nor[:, :2] * out).sum(1)).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    u = (aa.ravel() - a0) / (a1 - a0) * 2 - 1
    zb = np.array([hem(x) for x in u])
    arc = np.minimum(aa.ravel() - a0, a1 - aa.ravel()) * r.ravel()
    top_at = np.repeat(top[None, :], len(zs), 0).ravel()
    f = np.minimum.reduce([pos[:, 2] - zb, top_at - pos[:, 2] + 0.002, arc])
    # (a tucked top is hidden: its trim would only stand into what hides it)
    f_trim = np.minimum(pos[:, 2] - zb, arc) if snug is not None else f
    hip = head("thigh_l")[2]
    leg = 0.85 * ramp(hip - pos[:, 2], 0.0, 0.45)
    side = 1 / (1 + np.exp(-pos[:, 0] / 0.035))
    wt = np.zeros((len(pos), NB))
    wt[:, BI["pelvis"]] = 1 - leg
    wt[:, BI["thigh_l"]] = leg * side
    wt[:, BI["thigh_r"]] = leg * (1 - side)
    # Where it lies close over her (her seat, her hips) it moves exactly as
    # her skin there does, springs and all, so she cannot slide through it.
    d, j = cKDTree(P[body]).query(pos)
    near = 1 - ramp(d, gap + 0.004, 0.06)
    wt = wt * (1 - near[:, None]) + soft_weights(pos, np.where(body)[0], sigma=0.02) * near[:, None]
    attr = np.hstack([nor, wt, f_trim[:, None]])
    if os.environ.get("HANGDEBUG"):
        print("HANGDEBUG", name, "grid z %.3f..%.3f" % (pos[:, 2].min(), pos[:, 2].max()), "kept pts", int((f >= 0).sum()), "of", len(f),
              "zb %.3f..%.3f" % (zb.min(), zb.max()), "kept z %.3f..%.3f" % (pos[f >= 0, 2].min(), pos[f >= 0, 2].max()) if (f >= 0).any() else "")
    pos, at, tris = clip(f, pos, attr, tris)
    pos, at, tris = weld(pos, at, tris)
    pos = relax(pos, tris)
    if os.environ.get("HANGDEBUG"):
        print("HANGDEBUG", name, "after clip", len(pos), "pts z %.3f..%.3f" % (pos[:, 2].min(), pos[:, 2].max()), len(tris), "tris")
    return trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim)


def witch_hat(name, mkey, band_key, brim=0.21, height=0.34, droop=0.09, bald=False):
    """A wide-brimmed hat with a tall crown that bends back and droops at
    the tip, set on her hair: its crown is as wide as her hair at the brim
    and never nearer it than a centimetre above. All of it is her head's."""
    hd = (wsum("Head") > 0.5) & ((HAIR < 0.5) if bald else True)
    # Her head, and her own hairstyle over it (a mesh apart).
    pts = np.c_[X[hd], Y[hd], Z[hd]]
    if HAIR_DEFAULT and not bald:
        pts = np.vstack([pts, [(HAIR_DEFAULT.matrix_world @ v.co)[:] for v in HAIR_DEFAULT.data.vertices]])
    hx, hy, hz = pts.T
    top = hz.max()
    upper = hz > top - 0.1
    cx, cy = hx[upper].mean(), hy[upper].mean()
    zb = top - 0.07
    ang = np.arctan2(hx - cx, -(hy - cy))
    rad = np.hypot(hx - cx, hy - cy)
    nu = 64
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)

    def hair_r(z, dz=0.008):
        m = np.abs(hz - z) < dz
        out = np.zeros(nu)
        for j, aj in enumerate(a):
            d = np.abs((ang[m] - aj + np.pi) % (2 * np.pi) - np.pi) < 0.15
            if d.any():
                out[j] = rad[m][d].max()
        return out

    base = hair_r(zb) + 0.012
    base = np.maximum(base, np.percentile(base, 60) * 0.92)
    for _ in range(4):
        base = (np.roll(base, 1) + 2 * base + np.roll(base, -1)) / 4
    # The crown, ring by ring.
    K = 36
    rings = []
    for k in range(K + 1):
        t = k / K
        z = zb + height * t
        bend = max(0.0, t - 0.45) / 0.55
        ccy = cy + 0.13 * bend ** 2
        cz = z - droop * bend ** 3
        scale = (1 - t) ** 1.15
        rr = base * scale + 0.004 * (1 - t)
        need = hair_r(z) + 0.01
        rr = np.maximum(rr, need * (need > 0.01))
        rings.append(np.stack([cx + rr * np.sin(a), ccy - rr * np.cos(a), np.full(nu, cz)], -1))
    crown = np.array(rings).reshape(-1, 3)
    ct = grid(K + 1, nu + 1)
    # Close the seam: wrap the angle.
    idx = np.arange((K + 1) * nu).reshape(K + 1, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    ct = idx[ct]
    # The brim: from the crown's base out, sagging a little, its sides
    # turned up and front and back down (the witch's wave).
    M = 14
    br = []
    for k in range(M + 1):
        t = k / M
        rr = base + brim * t
        z = zb - 0.012 * t * t + 0.03 * t * t * (np.cos(2 * a) * -1 + 1) / 2 - 0.015 * t * t
        br.append(np.stack([cx + rr * np.sin(a), cy - rr * np.cos(a), z], -1))
    brimp = np.array(br).reshape(-1, 3)
    idx = np.arange((M + 1) * nu).reshape(M + 1, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    bt = idx[grid(M + 1, nu + 1)]
    # A band round the crown's foot.
    # The crown closed underneath (seen from below, it was open).
    capc = rings[0].mean(0)
    capp = np.vstack([rings[0], capc[None]])
    capt = np.array([(j, (j + 1) % nu, nu) for j in range(nu)])
    bandp = np.array(rings[:4]).reshape(-1, 3)
    bandp[:, :2] = (bandp[:, :2] - [cx, cy]) * 1.03 + [cx, cy]
    bandt = np.arange(4 * nu).reshape(4, nu)
    bandt = np.c_[bandt, bandt[:, :1]].ravel()[grid(4, nu + 1)]
    out = []
    for nm, pp, tt, key, th in ((name + "_crown", crown, ct, mkey, 0.003), (name + "_brim", brimp, bt, mkey, 0.004),
                                (name + "_band", bandp, bandt, band_key, 0.002), (name + "_cap", capp, capt, mkey, 0.002)):
        n = vertex_normals(pp, tt)
        rad_out = pp[:, :2] - [cx, cy]
        if (n[:, :2] * rad_out).sum(1).mean() < 0 and nm.endswith(("crown", "band")):
            tt = tt[:, ::-1]
        if nm.endswith("brim") and n[:, 2].mean() < 0:
            tt = tt[:, ::-1]
        wt = np.zeros((len(pp), NB))
        wt[:, BI["Head"]] = 1
        out.append(finish(nm, pp, wt, tt, key, th, 0.001))
    print("HAT brim at %.3f, crown base %.3f-%.3f m" % (zb, base.min(), base.max()))
    return out


# ---------------------------------------------------------------- outfits --
def plunge_line(over=0.03, low=0.03, wing=0.022):
    """The top edge of a plunging cup, as a height for each distance from her
    middle: from `low` over her underbust at her middle, rising in a curve
    to `over` above her nipple, highest a little past it where a strap
    would hold it (`wing` higher), then down the side of her breast toward
    her arm."""
    from scipy.interpolate import PchipInterpolator
    nx = abs(NIPPLE["r"][0])
    nz = NIPPLE["r"][2]
    xs = np.array([0.0, 0.012, nx * 0.45, nx * 0.8, nx, nx + 0.025, nx + 0.05, nx + 0.09])
    zs = np.array([UNDERBUST + low - 0.005, UNDERBUST + low, nz - 0.01, nz + over * 0.8, nz + over, nz + over + wing,
                   nz + over + 0.005, nz - 0.02])
    return PchipInterpolator(xs, zs, extrapolate=True)


def warden():
    """The oath-knight, sworn to the Order of the Morning Light: formed
    plate cups, plunging deep between her breasts, gold-bound and riveted,
    held by straps over her shoulders and a strap round her back; a war belt
    slung low on her hips, a skirt of steel plates hung from it, and
    beneath it only a thong; plate at her shoulders, forearms, knees and
    shins."""
    arms = ARMW["l"] + ARMW["r"]
    nx, nz = abs(NIPPLE["r"][0]), NIPPLE["r"][2]

    def gold(w=0.007):
        return ("gold", w, 0.0004, 0.0015)

    # The belt: slung low, where a brief's waistband would run, rising over
    # her hip bones and behind.
    bz0 = CROTCH + 0.13

    def belt_z(a):
        return bz0 + 0.05 * np.clip(np.abs(0.17 * np.sin(a)) / 0.15, 0, 1) ** 2 + 0.06 * ramp(-np.cos(a), -0.15, 0.35)
    under_belt = bz0 - 0.022
    thong_back = back_string(under_belt + 0.06, CROTCH + 0.012)
    # The straps: from each cup's peak, over her shoulder, down her back to
    # the strap round it.
    back_z = UNDERBUST + 0.035
    cups = plate_cups("warden.cups", "steel", plunge_line(), lift=0.002, thick=0.003, trim=gold(0.007), studs="gold")
    # Where her cups meet below her cleavage: the sun of her Order joins them.
    gore_at = np.array([0.0, CUP_LOW[1] - 0.004, CUP_LOW[2] - 0.004])
    buckle_at = front_point(0.0, bz0)
    buckle_n = np.array(SKIN_BVH.find_nearest(Vector(buckle_at))[1][:])
    straps = []
    for sd, sg in (("l", 1), ("r", -1)):
        # (from just under the cup's rim at its peak: it runs up from behind the plate)
        pk = CUP_PEAK[sd]
        top = front_point(pk[0] - sg * 0.004, pk[2] - 0.012)
        # (straight up from the cup to her shoulder: a point between them
        # put a kink in it)
        straps.append([top, np.array([sg * 0.11, 0.03, 1.565]),
                       np.array([sg * 0.1, 0.11, 1.47]), np.array([sg * 0.085, 0.125, back_z])])
    strap_objs = [o for k, cv in enumerate(straps) for o in ribbon(f"warden.strap{k}", cv, 0.018, "darkleather", thick=0.003,
                                                                  trim=gold(0.003), centre=(0.0, 0.0, 1.33))]
    backstrap = girdle("warden.backstrap", lambda a_: np.full_like(a_, back_z), 0.022, "darkleather", lift=0.003, thick=0.003,
                       trim=gold(0.003), arc=(1.48, 2 * np.pi - 1.48), mask=arms < 0.3)
    belt = girdle("warden.belt", belt_z, 0.05, "darkleather", lift=0.006, thick=0.005, trim=gold(0.005))
    out = [
        *cups,
        *strap_objs,
        *backstrap,
        *belt,
        # Each strap riveted where it meets the strap round her back.
        *studs_on("warden.strap_rivets", strap_objs + backstrap,
                  [((sg * 0.085, 0.7, back_z + 0.003), (sg * 0.085, 0.0, back_z + 0.003)) for sg in (1, -1)]
                  + [((sg * 0.7 * np.sin(1.53), -0.7 * np.cos(1.53), back_z), (0.0, 0.0, back_z)) for sg in (1, -1)], "gold", r=0.003),
        *sunburst("warden.buckle", buckle_at + buckle_n * 0.009, buckle_n, np.array([0, 0, 1.0]), 0.034, "gold",
                  boss="steel"),
        *sunburst("warden.gore", gore_at, np.array([0, -1.0, 0.25]), np.array([0, 0, 1.0]), 0.019, "gold", rays=8,
                  thick=0.003, boss="steel"),

        # Beneath, a thong: a narrow front (under the fauld) and a string
        # down the back from the belt.
        # (its front starts well under the plates' tucked tops, and lies
        # close, so they hang clear of it)
        *piece("warden.thong", AND(FRONT - 0.3, np.minimum(0.015 + 0.42 * np.maximum(Z - CROTCH, 0), 0.034) - np.abs(X),
                                   (bz0 - 0.04) - Z, Z - (CROTCH - 0.03)), "darkleather", lift=0.0012, thick=0.0018, smooth=2,
               soften=0),
        # (opening into the gusset over its last 3 cm, as a thong's string
        # does: 2 cm wide all the way, her skin beside it slipped out as her
        # cheeks parted in a vault)
        *ribbon("warden.thong_back", thong_back, 0.02, "darkleather", lift=0.003, thick=0.003, snap=False, hides=True,
                flare=(0.034, 0.03)),
        # (under her, a gusset wider than the string, as a thong's is: the
        # string alone left her bare either side there as she lay on her back)
        # (close under her, 1 mm, her skin tucked in under it and each line of
        # it moving with the skin under that line: hung 6 mm under her and
        # moving as one strap, her skin came through it as her thighs parted)
        # (from 6 mm up into her cleft, under the string's foot: begun 4 mm
        # short of it, the turn between them was bare)
        *gusset("warden.thong_gusset", "darkleather", GAP_F - 0.006, thong_back[-1][1] + 0.006),
    ]
    # A skirt of steel plates hung all round from the belt, each its own (her
    # legs move freely between them; each swings with the thigh it is over),
    # gold-edged and rounded at its foot: longest in front, over her crotch,
    # shorter behind (the lower curve of her cheeks glimpsed below them); a
    # second row behind the gaps, a little shorter and darker, so nothing
    # shows through them.
    # Each plate's top is tucked up under the belt all along the belt's own
    # line (it rises over her hips and behind), snug there, so the plate
    # comes out from under the belt's edge as if part of it, then flares
    # clear of her thighs. Two gold rivets on the belt fix each plate of
    # the front row.
    plates = 12
    step = 2 * np.pi / plates
    ring = (np.abs(Z - bz0) < 0.01) & (arms < 0.3)
    cy = (Y[ring].min() + Y[ring].max()) / 2
    aims = []
    for row, (snug, drop, key, w_, th_) in enumerate(((0.003, 0.0, "steel", 0.47, 0.0025), (0.0008, 0.02, "darksteel", 0.4, 0.002))):
        for k in range(plates):
            ac = (k + 0.5 * row) * step
            fr_ = (1 + np.cos(ac)) / 2
            hem = CROTCH - 0.06 * fr_ + 0.035 * (1 - fr_) + drop
            out += hanging(f"warden.skirt{row}_{k}", ac - step * w_, ac + step * w_, lambda a_: belt_z(a_) - 0.018,
                           lambda u, h=hem: h + 0.022 * u * u, key, flare=0.14, lift=snug, gap=0.016 - 0.004 * row, thick=th_,
                           trim=gold(0.006) if row == 0 else None, snug=snug)
            if row == 0:
                for da in (-0.5, 0.5):
                    a_ = ac + da * step * w_
                    z_ = float(belt_z(a_)) - 0.013
                    aims.append(((0.7 * np.sin(a_), cy - 0.7 * np.cos(a_), z_), (0.0, cy, z_)))
    out += studs_on("warden.skirt_rivets", belt, aims, "gold", r=0.0028)
    for sd, sg in (("l", 1), ("r", -1)):
        out += [
            *piece(f"warden.pauldron_{sd}", cap(shoulder(sd), 0.11), "steel", lift=0.012, thick=0.004, smooth=14, trim=gold(0.01), studs="gold"),
            *piece(f"warden.vambrace_{sd}", limb(sd, ELBOW_S + 0.05, WRIST_S - 0.01, legs=False), "steel", lift=0.006, smooth=8, trim=gold(), studs="gold"),
            *piece(f"warden.greave_{sd}", limb(sd, KNEE_S + 0.03, ANKLE_S + 0.01, front_dip=0.04), "steel", lift=0.008, smooth=12, trim=gold(), studs="gold"),
            *piece(f"warden.knee_{sd}", cap(LEG[sd][1] + np.array([0, -0.06, 0]), 0.06), "steel", lift=0.016, thick=0.004, smooth=12, trim=gold(0.006)),
            *piece(f"warden.sabaton_{sd}", limb(sd, ANKLE_S - 0.02, 9.9), "darksteel", lift=0.005, smooth=6),
        ]
    return out


def arcanist():
    """The arcanist: a velvet capelet and sleeves, a plum leather corset
    with gold boning under low velvet half-cups, an open coat that bares
    her thighs, sheer stockings, thigh boots and a witch's hat."""
    def gold(w=0.006):
        return ("darkpurple", w, 0.0004, 0.0013)

    # The warden's cups (their shape is the one), cut lower toward the
    # middle so the inner and upper breast show; at the outside the cut is
    # above the nipple, so the full cup's edge stands there.
    cup, _ = cups(cover=0.6, plunge=0.012)
    low = np.min([NIPPLE[sd][2] + 0.035 - 0.5 * np.maximum(0, abs(NIPPLE[sd][0]) - np.abs(X)) for sd in "lr"], axis=0) - Z
    for sd in "lr":
        print("NIPPLE COVER arcanist", sd, "cup field %.4f" % cup[np.argmin(np.linalg.norm(P - NIPPLE[sd], axis=1))])
    arms = ARMW["l"] + ARMW["r"]
    ctop = UNDERBUST + 0.012 + 0.07 * (1 - FRONT)
    cbot = 1.012 - 0.04 * np.exp(-(X / 0.04) ** 2) * FRONT
    # A skin-tight one-piece: from under her cups down over her hips to a
    # leotard's high-cut legs.
    ax = np.abs(X)
    # Cut as high as it goes: the leg line rises from the crotch almost to
    # her waist at the sides, front and back.
    # A narrow V in front rising steeply to her hip bones; a thong behind
    # widening into a V above her cheeks.
    # (2.9 cm across at its foot: what must be covered there is 2.4 cm, and
    # at 1.9 cm her skin showed either side of it in a lunge)
    w = (0.0145 + 0.42 * np.maximum(Z - CROTCH, 0)) * FRONT + (-0.01 + 1.5 * np.maximum(Z - CROTCH - 0.13, 0)) * (1 - FRONT)
    leotard = AND(Z - (CROTCH - 0.03), w - ax)
    # A bodysuit: over her breasts and up to a high neck.
    neck_top = head("neck_01")[2] + 0.07 - 0.035 * (1 - FRONT)
    # Clean armholes: round each shoulder, at a set distance along the
    # arm from the collarbone.
    def sleeve(sd):
        # Sleeves to the gloves: on her arm, down to just inside the glove;
        # her torso always.
        torso = smooth_field(0.5 - ARMW[sd], 40) * 0.1
        side = X * (1 if sd == "l" else -1) > 0
        arm = WRIST_S - 0.06 - ARM_S[sd]
        return np.where(side, np.maximum(arm, torso), 1.0)
    # A plunge: a deep V from her collar to below where her breasts meet,
    # its sides crossing the inner curve of each breast well inside her
    # nipples (her cleavage bare, her breasts held), the high collar kept
    # round the sides and back of her neck.
    v_lo, v_hi = UNDERBUST + 0.004, head("neck_01")[2] + 0.02
    nx_ = abs(NIPPLE["r"][0])
    v_half = np.interp(Z, [v_lo, (NIPPLE["r"][2] + v_lo) / 2, NIPPLE["r"][2] + 0.03, v_hi],
                       [0.0, nx_ * 0.42, nx_ * 0.62, 0.05])
    plunge = np.where(FRONT > 0.5, np.abs(X) - v_half, 1.0)
    plunge = np.where(Z < v_lo, 1.0, plunge)
    # Its leg lines and plunge are cut exactly once it is shaped (cut on her
    # skin and then smoothed, they wandered); her skin's field is left a
    # little wider there, so the exact lines decide.
    corset = AND(neck_top - Z, OR(Z - 1.13, leotard + 0.02), sleeve("l"), sleeve("r"), plunge + 0.02)

    def exact(q):
        qx, qy, qz = q[:, 0], q[:, 1], q[:, 2]
        fr = ramp(-(qy - CROTCH_Y), -0.03, 0.03)
        r = qz - CROTCH
        wq = (0.0145 + 0.42 * np.maximum(r, 0)) * fr + (-0.01 + 1.5 * np.maximum(r - 0.13, 0)) * (1 - fr)
        legs = np.maximum(qz - 1.13, wq - np.abs(qx))
        vh = np.interp(qz, [v_lo, (NIPPLE["r"][2] + v_lo) / 2, NIPPLE["r"][2] + 0.03, v_hi], [0.0, nx_ * 0.42, nx_ * 0.62, 0.05])
        pl = np.where((fr > 0.5) & (qz >= v_lo), np.abs(qx) - vh, 1.0)
        return np.minimum(legs, pl)
    belt_z = 1.0 + 0.035 * X / 0.18
    belt = AND(0.016 - np.abs(Z - belt_z), 0.3 - arms)
    bones = OR(*[front_line(x, UNDERBUST - 0.022, x * 0.8, 1.025 - 0.025 * (abs(x) < 0.05), 0.009)
                 for x in (-0.085, -0.04, 0.04, 0.085)])
    bones = AND(bones, corset - 0.004)
    nz = head("neck_01")[2]
    choker = AND(0.009 - np.abs(Z - (nz + 0.035)), wsum("neck_01", "Head") - 0.4, 0.3 - wsum("Head") + wsum("neck_01") * 0, 0.3 - arms)
    mantle = OR(cap(shoulder("l"), 0.14), cap(shoulder("r"), 0.14),
                AND(Z - 1.43, (Y - 0.0), 0.3 - arms))
    global GARTER_Z
    GARTER_Z = CROTCH + 0.2
    out = [
        # (opening into the gusset at its foot, as the warden's does)
        *ribbon("arcanist.thong", back_string(CROTCH + 0.155, CROTCH + 0.012), 0.016, "plumleather", lift=0.003, thick=0.003,
               trim=gold(0.004), snap=False, hides=True, flare=(0.034, 0.03)),
        *piece("arcanist.corset", corset, "plumleather", lift=0.0035, smooth=8, iron=60, trim=gold(0.008), keep_off=("Head",), filled=True, edge=120, soften=80,
               bridge=True, cut=exact),
        *piece("arcanist.choker", choker, "blackleather", lift=0.002, soften=0, keep_off=("Head",)),
        *witch_hat("arcanist.hat", "plumleather", "darkpurple"),
    ]
    for sd in "lr":
        out += [
            *piece(f"arcanist.glove_{sd}", limb(sd, WRIST_S - 0.08, 9.9, legs=False), "blackleather", lift=0.0012, thick=0.001, bevel=0.0004, trim=gold(0.008), edge=30, soften=12),
            # (her leg by where it is, not by its weights: her inner thigh is
            # partly her hips', and a weight test tore a hole there; and no
            # gap kept for the slot between her thighs, which ends above it)
            *piece(f"arcanist.stocking_{sd}", AND(0.3 - ARMW["l"] - ARMW["r"], stock_top(sd) - Z, (X * (1 if sd == "l" else -1) - 0.004) * 0.3, (KNEE_S - 0.03) - LEG_S[sd]), "stocking", lift=0.0012, thick=0.0, bevel=0.0, soften=10, slot=False),
            *girdle(f"arcanist.lace_{sd}", stock_band, 0.03, "satin", lift=0.003, thick=0.0018,
                    trim=("satin", 0.0035, 0.0006, 0.0012), mask=(LEGW[sd] > 0.6) & (Z < CROTCH + 0.02) & (X * (1 if sd == "l" else -1) > 0.002)),
            *piece(f"arcanist.boot_{sd}", limb(sd, KNEE_S - 0.05, 9.9, front_dip=-0.03), "blackleather", lift=0.005, smooth=8, iron=300, hull=LEG_S[sd] - ANKLE_S - 0.03, trim=gold(0.008), edge=30),
            *piece(f"arcanist.cuff_{sd}", limb(sd, KNEE_S - 0.065, KNEE_S - 0.015), "blackleather", lift=0.009, thick=0.003, smooth=6, trim=gold(0.005)),
        ]
    return out


def leg_z(sd, s0):
    """Height of the point `s0` along a leg (metres from the hip)."""
    pts = LEG[sd]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.array(pts), axis=0), axis=1))]
    return float(np.interp(s0, d, np.array(pts)[:, 2]))


def ranger():
    """The stalker: a corset that holds her. It is strapless, with a
    sweetheart line over her breasts (hugged tight, on their perfect form),
    leaving her shoulders and the top of her chest bare. It is laced up the
    front over a strip of her skin and tied in a bow, and runs on down over
    her crotch. On her right it is cut away from her waist: a straight line
    in front to just shy of her crotch, and behind a line over the top of
    her cheek into a thong, so her right hip and cheek are bare. Her left
    leg is in a light brown pant leg, tucked up under the corset and down
    into her boot. A belt slung round her hips with a bronze buckle; a buckled strap
    cinched high on her bare right thigh; bronze lames at her left
    shoulder, bronze bracers, fingerless gloves; knee boots with folded
    cuffs, the right one laced up the front. Corset, gloves and boots of
    forest-green leather; the pant leg light brown cloth."""
    from scipy.interpolate import PchipInterpolator
    arms = ARMW["l"] + ARMW["r"]

    def edge(w=0.006, key="darkleather"):
        return (key, w, 0.0006, 0.0013)

    def belt_z(a):
        return CROTCH + 0.085 - 0.022 * np.sin(a)

    nx, nzn = abs(NIPPLE["r"][0]), NIPPLE["r"][2]
    ax_ = np.abs(X)

    def smin(a, b, k=0.004):
        m = np.minimum(a, b)
        return m - k * np.log(np.exp(-(a - m) / k) + np.exp(-(b - m) / k))

    # The top: a sweetheart over her breasts, well above each nipple, down to
    # a point between them; then, by the angle round her chest, down under
    # her arm (below all the skin her arm moves, so the edge is this line and
    # never the ragged edge of her arm's weights) into a straight band round
    # her back. The two met by a smooth minimum: one fair curve.
    sweet = PchipInterpolator([0.0, 0.025, nx * 0.6, nx, nx + 0.04, nx + 0.09],
                              [nzn - 0.014, nzn - 0.004, nzn + 0.026, nzn + 0.034, nzn + 0.03, nzn + 0.02])
    under_arm = PchipInterpolator([0, 50, 62, 72, 82, 92, 104, 118, 180],
                                  [1.8, 1.8, nzn + 0.05, nzn + 0.025, nzn, nzn - 0.03, UNDERBUST + 0.062, UNDERBUST + 0.06,
                                   UNDERBUST + 0.06])

    def top_at(q):
        round_ = np.degrees(np.abs(np.arctan2(q[:, 0], -(q[:, 1] + 0.03))))
        return smin(sweet(np.minimum(np.abs(q[:, 0]), nx + 0.09)), under_arm(round_))

    top_z = top_at(P)
    # Below, her right is cut away. In front the corset keeps only her abs:
    # its edge runs up from just shy of her crotch along the groove at their
    # outer edge (found on her: about 7 cm out from her middle, narrowing
    # toward her crotch), then curves out round her side at her lower ribs.
    # Behind, from there it runs level, then curves down over the top of her
    # cheek to her middle above the cleft, and a thong runs down it. Her
    # whole right hip, flank and cheek are bare. Her left is a cheeky seat
    # over the top of her pant leg.
    ang = np.abs(np.arctan2(X, -(Y - CROTCH_Y)))
    rise_ = Z - CROTCH
    hug = PchipInterpolator([-0.035, 0.0, 0.02, 0.04, 0.07, 0.1, 0.16, 0.22, 0.28, 0.33, 0.37, 0.40],
                            [0.012, 0.016, 0.026, 0.045, 0.063, 0.072, 0.075, 0.077, 0.08, 0.092, 0.13, 0.2])
    right_front = hug(np.clip(rise_, -0.035, 0.40)) + X
    u_ = np.clip(-X / 0.13, 0, 1)
    right_back = Z - (CROTCH + 0.31 + 0.095 * u_ ** 0.9)
    right = right_front * FRONT + right_back * (1 - FRONT)
    edge_l = CROTCH + PchipInterpolator([0, 0.6, 1.2, 1.57, 2.1, 2.6, np.pi], [-0.02, 0.0, 0.03, 0.05, 0.065, 0.06, 0.055])(ang)
    rise = np.maximum(Z - CROTCH, 0)
    # (between her legs a narrow strip, a little wider in front; behind, a
    # thong down her cleft)
    strip = (0.012 + 0.3 * rise) * FRONT + np.minimum(0.008 + 0.07 * rise, 0.018) * (1 - FRONT) - ax_
    legs = OR(np.where(X < 0, right + 0.03, Z - edge_l), strip)
    # (her skin's field reaches lower under her crotch than the exact foot)
    # (her breasts always held; elsewhere never her arm, the cut eased so it
    # can never be ragged)
    # (a hard switch at the breasts' edge frayed it under her arm: the two
    # tests now meet smoothly, and the top is cut exactly, after shaping)
    not_arms = np.maximum(smooth_field(0.5 - arms, 30), (wsum("breast_l", "breast_r") - 0.03) * 10)
    body = AND(top_z + 0.02 - Z, Z - (CROTCH - 0.035), not_arms, legs)
    # Its front is laced over a strip of her skin, from under her breasts to
    # above her belt. The skin shows in a gap between bound edges, with
    # bronze eyelets either side. The lace crosses between them over her
    # skin, with a bar across the foot, and is tied at the top in a bow
    # under her breasts.
    lace_top, lace_bot = UNDERBUST - 0.008, CROTCH + 0.118
    half = 0.011
    def exact(q):
        # In front, her abs kept by one straight line from just shy of her
        # crotch up to under her breast; outside it, only her breast, the
        # edge following its underside up to her side. Behind, open from
        # beside her spine across to her side, up to a line a few
        # centimetres under the band. The thong between her legs, and her
        # lace opening's two straight sides.
        qx, qy, qz = q[:, 0], q[:, 1], q[:, 2]
        fr = ramp(-(qy - CROTCH_Y), -0.03, 0.03)
        r = qz - CROTCH
        reach = np.where(r < 0, 0.012 + 0.004 * np.clip(r / 0.035 + 1, 0, 1), 0.016 + 0.056 * np.clip(r, 0, None) / 0.24)
        # (her breast held by its own form: inside the ellipsoid her cups are
        # built on, a little grown, so the edge runs round its underside as
        # one closed curve; a height for each width folded back on the
        # breast's curved side and left a hole there)
        c_b, R_b, ax_b = BREAST_HOLD
        r_ell = np.sqrt((((q - c_b) @ R_b.T / ax_b) ** 2).sum(1))
        front = np.maximum(qx + reach, (1.07 - r_ell) * 0.08)
        u = np.clip(-qx / 0.13, 0, 1)
        band = qz - (UNDERBUST + 0.015 + 0.01 * u)
        side = front * fr + band * (1 - fr)
        rq = np.maximum(r, 0)
        thong = (0.015 + 0.3 * rq) * fr + np.minimum(0.015 + 0.07 * rq, 0.018) * (1 - fr) - np.abs(qx)
        right_q = np.where(qx < 0, np.maximum(side, thong), 1.0)
        slot = np.where((qz < lace_top + 0.018) & (qz > lace_bot - 0.045) & (fr > 0.5), np.abs(qx) - half, 1.0)
        # (and its foot under her crotch, cut with the rest, so the corner
        # where her leg line meets it is one clean turn)
        return np.minimum.reduce([right_q, slot, r + 0.024, top_at(q) - qz])

    corset = body
    lift, thick = 0.0035, 0.003
    rows = np.linspace(lace_top - 0.012, lace_bot + 0.012, 9)
    eye, enrm = {1: [], -1: []}, {1: [], -1: []}
    for sg in (1, -1):
        for z in rows:
            q = front_point(sg * (half + 0.0085), z)
            n = np.array(SKIN_BVH.find_nearest(Vector(q))[1][:])
            eye[sg].append(q + n * (lift + thick + 0.0003))
            enrm[sg].append(n)

    def at_eye(sg, i):
        return eye[sg][i] + enrm[sg][i] * 0.0007

    laces = []
    nf = (enrm[1][-1] + enrm[-1][-1]) / 2
    laces += cord("ranger.lace_foot", bezier(at_eye(1, -1), (at_eye(1, -1) + at_eye(-1, -1)) / 2 + nf * 0.003, at_eye(-1, -1)),
                  "darkleather")
    for i in range(len(rows) - 1, 0, -1):
        for sg in (1, -1):
            # Each pair crosses at its middle, one over the other by turns
            # (a Bezier's middle is half its control's offset).
            a_, b_ = at_eye(sg, i), at_eye(-sg, i - 1)
            nm = (enrm[sg][i] + enrm[-sg][i - 1]) / 2
            up_ = 0.0044 if (sg > 0) == (i % 2 == 0) else -0.0012
            laces += cord(f"ranger.lace{i}{'ab'[sg > 0]}", bezier(a_, (a_ + b_) / 2 + nm * (0.0016 + up_), b_), "darkleather")
    # The bow: a knot just above the top eyelets, two loops, two tails.
    knot = front_point(0.0, rows[0] + 0.013)
    kn = np.array(SKIN_BVH.find_nearest(Vector(knot))[1][:])
    knot = knot + kn * (lift + thick + 0.0035)
    up_v = np.array([0, 0, 1.0]) - kn * kn[2]
    up_v /= np.linalg.norm(up_v)
    side_v = np.cross(up_v, kn)
    side_v *= np.sign(side_v[0])
    tips, tip_dirs = [], []
    for sg in (1, -1):
        a_ = at_eye(sg, 0)
        laces += cord(f"ranger.lace_top{'ab'[sg > 0]}", bezier(a_, (a_ + knot) / 2 + kn * 0.003, knot), "darkleather")
        ph = np.linspace(0, 2 * np.pi, 64)
        loop = (knot[None] + side_v[None] * (sg * 0.019 * (1 - np.cos(ph)))[:, None]
                + up_v[None] * (0.009 * np.sin(ph) - 0.005 * (1 - np.cos(ph)))[:, None]
                + kn[None] * (0.0035 * (1 - np.cos(ph)))[:, None])
        laces += cord(f"ranger.bow{'ab'[sg > 0]}", loop, "darkleather", r=0.0014)
        tail = []
        for t in np.linspace(0, 1, 40):
            z = knot[2] - 0.1 * t
            q = front_point(sg * (0.004 + 0.024 * t + 0.003 * np.sin(t * 6)), z)
            qn = np.array(SKIN_BVH.find_nearest(Vector(q))[1][:])
            tail.append(q + qn * (lift + thick + 0.0048 - 0.0008 * t))
        tail[0] = knot
        tail = np.array(tail)
        laces += cord(f"ranger.tail{'ab'[sg > 0]}", tail[:-3], "darkleather", r=0.0014)
        laces += cord(f"ranger.aglet{'ab'[sg > 0]}", tail[-4:], "bronze", r=0.0019)
    knot_ = domes("ranger.lace_knot", [knot - kn * 0.001], [kn], "darkleather", r=0.0042)
    for o_ in knot_:
        o_["hides"] = False
    laces += knot_

    def belt_lift(a):
        # Over the corset and pant (her left, her front) it clears them; on
        # her bare right hip and cheek it lies close to her skin.
        am = (np.asarray(a) + np.pi) % (2 * np.pi) - np.pi
        over = np.where(am >= 0, 1 - ramp(am, 2.75, 3.05), ramp(am, -0.75, -0.45))
        return 0.0045 + 0.0065 * over

    # The belt and its buckle; the strap on her right thigh.
    bfront = front_point(0.035, float(belt_z(0.2)))
    bn_ = np.array(SKIN_BVH.find_nearest(Vector(bfront))[1][:])
    tz = leg_z("r", 0.16)
    tpt = front_point(LEG["r"][0][0] - 0.03, tz)
    tn_ = np.array(SKIN_BVH.find_nearest(Vector(tpt))[1][:])
    tz2 = leg_z("r", 0.29)
    tpt2 = front_point(LEG["r"][0][0] - 0.022, tz2)
    tn2_ = np.array(SKIN_BVH.find_nearest(Vector(tpt2))[1][:])
    fingers = wsum(*[n for n in BONES if n.split("_")[0] in ("index", "middle", "ring", "pinky", "thumb") and n.split("_")[1] in ("02", "03")])
    tops = {"r": KNEE_S - 0.03, "l": KNEE_S + 0.1}
    # Her left leg in light brown cloth. Its top reaches up under the
    # corset's edge all the way round, so no skin shows between them; its
    # foot goes down into her boot. Both ends are hidden, so neither is bound.
    pant = AND(X - 0.004, (edge_l + 0.03) - Z, (tops["l"] + 0.06) - LEG_S["l"], 0.3 - ARMW["l"])
    out = [
        *piece("ranger.corset", corset, "forestleather", lift=lift, thick=thick, smooth=8, iron=60, soften=20, slot="right",
               trim=edge(0.006), filled=True, keep_off=("Head", "neck_01"), edge=6, cut=exact),
        *grommets("ranger.eyelets", eye[1] + eye[-1], enrm[1] + enrm[-1], "bronze"),
        *laces,
        *girdle("ranger.belt", belt_z, 0.042, "brownleather", lift=belt_lift, thick=0.004),
        *frame("ranger.buckle", bfront + bn_ * 0.022, bn_, np.array([0, 0, 1.0]), 0.042, 0.052, "bronze", r=0.0028),
        *girdle("ranger.thighstrap", lambda a: np.full_like(a, tz), 0.028, "brownleather", lift=0.003, thick=0.003,
                mask=(LEGW["r"] > 0.6) & (np.abs(Z - tz) < 0.05)),
        *frame("ranger.thighbuckle", tpt + tn_ * 0.008, tn_, np.array([0, 0, 1.0]), 0.03, 0.036, "bronze", r=0.0022),
        *girdle("ranger.thighstrap2", lambda a: np.full_like(a, tz2), 0.024, "brownleather", lift=0.003, thick=0.003,
                mask=(LEGW["r"] > 0.6) & (np.abs(Z - tz2) < 0.05)),
        *frame("ranger.thighbuckle2", tpt2 + tn2_ * 0.008, tn2_, np.array([0, 0, 1.0]), 0.026, 0.032, "bronze", r=0.002),
        *piece("ranger.pant", pant, "browncloth", lift=0.0008, thick=0.001, smooth=6, soften=8, slot="right", bind=False),
    ]
    seam = []
    legl = LEGW["l"] > 0.6
    for z in np.linspace(CROTCH + 0.07, leg_z("l", tops["l"]) - 0.01, 40):
        m = legl & (np.abs(Z - z) < 0.004)
        if m.sum() > 3:
            seam.append(P[m][np.argmax(X[m])])
    seam = np.array(seam)
    for _ in range(4):
        seam[1:-1] = (seam[:-2] + 2 * seam[1:-1] + seam[2:]) / 4
    out += ribbon("ranger.pant_seam", list(seam), 0.005, "brownleather", lift=0.0022, thick=0.0012)
    sh = shoulder("l")
    for k, (dz, r, lft) in enumerate(((0.0, 0.11, 0.024), (-0.045, 0.1, 0.019), (-0.09, 0.09, 0.014), (-0.13, 0.08, 0.009))):
        c = sh + np.array([0.02 * k, 0, dz])
        out += piece(f"ranger.pauldron{k}", AND(cap(c, r), Z - (c[2] - r * 0.55)), "bronze", lift=lft, thick=0.004, smooth=14,
                     soften=10, studs="darksteel")
    for sd in "lr":
        cz = leg_z(sd, tops[sd] + 0.02)
        out += [
            *piece(f"ranger.bracer_{sd}", limb(sd, ELBOW_S + 0.04, WRIST_S - 0.015, legs=False), "bronze", lift=0.007, smooth=8,
                   soften=10, trim=edge(0.006, "brownleather"), studs="darksteel"),
            *piece(f"ranger.glove_{sd}", AND(limb(sd, WRIST_S - 0.03, 9.9, legs=False), 0.4 - fingers), "forestleather", lift=0.0015,
                   thick=0.0012, bevel=0.0004, soften=8),
            *piece(f"ranger.boot_{sd}", limb(sd, tops[sd], 9.9), "forestleather", lift=0.005 if sd == "r" else 0.0065, smooth=8,
                   iron=300, hull=LEG_S[sd] - ANKLE_S - 0.03, soften=10),
            *girdle(f"ranger.cuff_{sd}", lambda a, cz=cz: np.full_like(a, cz), 0.06, "forestleather", lift=0.01 if sd == "r" else 0.012,
                    thick=0.003, trim=edge(0.005), mask=(LEGW[sd] > 0.6) & (np.abs(Z - cz) < 0.07), flare=0.012),
        ]
    # The right boot laced up the front of her shin, below its cuff.
    kx = LEG["r"][1][0]
    ax0 = LEG["r"][2][0]
    z0, z1 = LEG["r"][2][2] + 0.07, leg_z("r", tops["r"] + 0.02) - 0.04
    lz = np.linspace(z1, z0, 9)
    bl = {}
    for sgn in (1, -1):
        e = []
        for z in lz:
            t = (LEG["r"][1][2] - z) / (LEG["r"][1][2] - LEG["r"][2][2])
            x = kx + (ax0 - kx) * t + 0.013 * sgn
            q = front_point(x, z)
            n = np.array(SKIN_BVH.find_nearest(Vector(q))[1][:])
            e.append(q + n * 0.0095)
        bl[sgn] = e
    for i in range(len(lz) - 1):
        for sg in (1, -1):
            out += ribbon(f"ranger.bootlace{i}{'ab'[sg > 0]}", [bl[sg][i], bl[-sg][i + 1]], 0.003, "darkleather", lift=0.0005,
                          thick=0.0012, snap=False)
    return out


CHANNELS = ["warden", "arcanist", "reaver", "ranger"]
BALD = set()
def hull_radius_grid(z0, z1, nu=160, step=0.004, mask=None, angles=None):
    """Her body's section (arms and hair left out) as a convex hull, its
    radius at each of `nu` angles round her (0 her front), every `step`
    in height from z0 to z1, and the centre it is measured from."""
    from scipy.spatial import ConvexHull
    body_pts = (ARMW["l"] + ARMW["r"] < 0.25) & (HAIR < 0.5) if mask is None else mask
    zs = np.arange(z0, z1 + step, step)
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False) if angles is None else angles
    nu = len(a)
    d = np.stack([np.sin(a), -np.cos(a)], 1)
    m0 = body_pts & (np.abs(Z - (z0 + z1) / 2) < 0.02)
    cxy = P[m0][:, :2].mean(0)
    R = np.zeros((len(zs), nu))
    for k, z in enumerate(zs):
        q = P[body_pts & (np.abs(Z - z) < 0.006)][:, :2]
        if len(q) < 8:
            # Past the end of what is measured: the nearest level's.
            R[k] = R[k - 1] if k else 0
            continue
        hv = q[ConvexHull(q).vertices]
        best = np.zeros(nu)
        for i in range(len(hv)):
            p0, p1 = hv[i] - cxy, hv[(i + 1) % len(hv)] - cxy
            e = p1 - p0
            den = d[:, 0] * e[1] - d[:, 1] * e[0]
            ok = np.abs(den) > 1e-12
            t = np.where(ok, (p0[0] * e[1] - p0[1] * e[0]) / np.where(ok, den, 1), -1)
            u = np.where(ok, (p0[0] * d[:, 1] - p0[1] * d[:, 0]) / np.where(ok, den, 1), -1)
            best = np.where(ok & (t > 0) & (u >= 0) & (u <= 1), np.maximum(best, t), best)
        R[k] = best
    for k in range(len(zs) - 2, -1, -1):
        if not R[k].any():
            R[k] = R[k + 1]
    return zs, a, R, cxy


GARTER_Z = None


def stock_band(a):
    """The middle of a stocking's top band at angle a round her leg (0 her
    front): just under her crotch in front, dropping under her cheeks
    behind, so it frames them and never crosses them."""
    return np.full_like(np.asarray(a, float), CROTCH - 0.07)


def stock_top(sd):
    """Where a stocking's sheer part ends: inside its band, by the same
    angle round the leg (so the two always match)."""
    m = (LEGW[sd] > 0.6) & (np.abs(Z - (CROTCH - 0.05)) < 0.01)
    cx, cy = P[m][:, 0].mean(), P[m][:, 1].mean()
    a = np.arctan2(X - cx, -(Y - cy))
    return stock_band(a) + 0.004


def garters(name, sd, top_field, band_field, mkey, width=0.01):
    """Garter straps on one leg, front and back: each straight down her
    thigh from the garter belt (GARTER_Z) to the top of the stocking."""
    s_ = 1 if sd == "l" else -1
    out = []
    for k, (fy, xo) in enumerate(((-1, 0.1), (1, 0.08))):
        side = (np.sign(Y - CROTCH_Y) == fy) & (np.abs(X * s_ - xo) < 0.005)
        band = P[side & (band_field > 0)]
        if not len(band):
            continue
        z1 = band[:, 2].max() - 0.008
        ctrl = []
        for z in np.linspace(GARTER_Z, z1, 10):
            hit = BVH.ray_cast(Vector((xo * s_, 0.6 * fy, z)), Vector((0, -fy, 0)), 1.2)
            if hit[0] is not None:
                ctrl.append(np.array(hit[0][:]))
        if len(ctrl) > 2:
            out += ribbon(f"{name}{k}", ctrl, width, mkey, lift=0.004, thick=0.0015, snap=False)
    return out


def back_string(z0, z1, n=12):
    """A line down the cleft between her cheeks from z0 to z1: straight
    down the middle of her (midway between her buttock bones), each point
    where a ray from behind first meets her skin there."""
    xc = (head("glute_l")[0] + head("glute_r")[0]) / 2
    out = []
    for z in np.linspace(z0, z1, n):
        hit = BVH.ray_cast(Vector((xc, 0.6, z)), Vector((0, -1, 0)), 1.0)
        if hit[0] is not None:
            out.append(np.array(hit[0][:]))
    return out


def soft_weights(pts, src_idx=None, sigma=0.015, k=16):
    """Bone weights from her skin near each point, averaged over a couple of
    centimetres: smooth from point to point. (Taken from each point's
    nearest skin, a belt bridging her hollows took bones in jumps, and
    crumpled when she moved.)"""
    sp = P if src_idx is None else P[src_idx]
    sw = W if src_idx is None else W[src_idx]
    tree = cKDTree(sp)
    out = np.zeros((len(pts), W.shape[1]))
    for a in range(0, len(pts), 3000):
        dd, jj = tree.query(pts[a:a + 3000], k=k)
        ww = np.exp(-(dd / sigma) ** 2) + 1e-9
        ww /= ww.sum(1, keepdims=True)
        out[a:a + 3000] = np.einsum("pk,pkb->pb", ww, sw[jj].astype(float))
    return out / (out.sum(1, keepdims=True) + 1e-12)


def girdle(name, zfun, width, mkey, lift=0.004, thick=0.004, trim=None, rows=9, nu=160, mask=None, gap=None, arc=None, flare=0.0, span=None):
    """A belt round her, its middle at height zfun(angle) (angle 0 her
    front, rising toward her left), `width` tall, pulled taut over her
    (on the convex hull of her body there), so its edges are two clean
    even curves. It moves with the skin nearest each point of it."""
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False) if arc is None else np.linspace(arc[0], arc[1], nu)
    if span is not None:
        # From a lower to an upper line, each its own height at each angle.
        zlo, zhi = span(a)
        zc, half = (zlo + zhi) / 2, (zhi - zlo) / 2
    else:
        zc, half = zfun(a), np.full(nu, width / 2)
    zs, _, R, cxy = hull_radius_grid((zc - half).min() - 0.01, (zc + half).max() + 0.01, nu, mask=mask, angles=a)
    # The hull's corners shift from level to level, and a belt laid on them
    # creases along them (thin bright lines in its shine). So: eased round
    # her and up her, then lifted back out by however far that brought it
    # inside the hull anywhere near, eased too. Fair, and never in her.
    from scipy.ndimage import gaussian_filter, maximum_filter
    run_a = max(np.abs(np.diff(a)).mean() * float(np.mean(R)), 1e-4)
    sg_ = (0.008 / 0.004, 0.02 / run_a)
    md = ("nearest", "wrap" if arc is None else "nearest")
    R_s = gaussian_filter(R, sg_, mode=md)
    lack = maximum_filter(np.maximum(R - R_s, 0), size=(5, max(3, int(0.03 / run_a))), mode=md)
    R = R_s + gaussian_filter(lack, sg_, mode=md) * 1.1
    # (rows fine enough that a trim band cut along the edge is a clean line)
    rows = max(rows, int(np.ceil(width / 0.0016)) | 1)
    off = np.linspace(-1, 1, rows)
    pos = np.zeros((rows, nu, 3))
    # (`lift` may be a function of the angle: a belt over a garment on one
    # side and bare skin on the other stands off each by what is under it)
    lift_a = lift(a) if callable(lift) else lift
    for k, o in enumerate(off):
        z = zc + o * half
        r = np.array([np.interp(z[j], zs, R[:, j]) for j in range(nu)])
        rl = r + lift_a + flare * k / (rows - 1)
        pos[k] = np.stack([cxy[0] + rl * np.sin(a), cxy[1] - rl * np.cos(a), z], -1)
    for _ in range(3):
        if arc is None:
            pos = (np.roll(pos, 1, 1) + 2 * pos + np.roll(pos, -1, 1)) / 4
        else:
            pos[:, 1:-1] = (pos[:, :-2] + 2 * pos[:, 1:-1] + pos[:, 2:]) / 4
    seams = []
    if kind(mkey) == "leather" and width >= 0.012:
        inset = 0.003 if width < 0.03 else 0.0038
        for sgn in (1, -1):
            o_ = sgn * (1 - inset / np.maximum(half, inset * 2))
            z = zc + o_ * half
            r = np.array([np.interp(z[j], zs, R[:, j]) for j in range(nu)])
            rl = r + lift_a + flare * (o_ + 1) / 2
            ln = np.stack([cxy[0] + rl * np.sin(a), cxy[1] - rl * np.cos(a), z], -1)
            for _ in range(3):
                if arc is None:
                    ln = (np.roll(ln, 1, 0) + 2 * ln + np.roll(ln, -1, 0)) / 4
                else:
                    ln[1:-1] = (ln[:-2] + 2 * ln[1:-1] + ln[2:]) / 4
            radial = np.stack([np.sin(a), -np.cos(a), np.zeros_like(a)], -1)
            tgl = np.gradient(ln, axis=0)
            seams.append((ln + radial * (thick + 0.0001), radial, tgl))
    pos = pos.reshape(-1, 3)
    idx = np.arange(rows * nu).reshape(rows, nu)
    if arc is None:
        idx = np.c_[idx, idx[:, :1]].ravel()
        tris = idx[grid(rows, nu + 1)]
    else:
        tris = grid(rows, nu)
    if gap is not None:
        # Open where it would meet its twin (between her thighs, hidden).
        tris = tris[(np.abs(pos[tris][:, :, 0]) > gap).all(1)]
    nor = vertex_normals(pos, tris)
    if (nor[:, :2] * (pos[:, :2] - cxy)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    src = np.where(mask)[0] if mask is not None else np.arange(len(P))
    # (one set of weights across its width, eased along it: it moves as a belt)
    wt = soft_weights(pos, src).reshape(rows, nu, -1)
    wt[:] = wt.mean(0, keepdims=True)
    for _ in range(12):
        if arc is None:
            wt = (np.roll(wt, 1, 1) + 2 * wt + np.roll(wt, -1, 1)) / 4
        else:
            wt[:, 1:-1] = (wt[:, :-2] + 2 * wt[:, 1:-1] + wt[:, 2:]) / 4
    wt = wt.reshape(len(pos), -1)
    edge = ((1 - np.abs(off))[:, None] * half[None, :]).ravel()
    if arc is not None:
        run = np.abs(np.diff(a)).mean() * np.mean(R)
        col = np.tile(np.arange(nu), rows)
        edge = np.minimum(edge, np.minimum(col, nu - 1 - col) * run)
    at = np.hstack([nor, wt, edge[:, None]])
    made = trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim, budget=10 ** 7)
    for o in made:
        o["hides"] = False
    for k, (ln, rn, tgl) in enumerate(seams):
        made += stitches(f"{name}_stitch{k}", ln, rn, tgl, pos, at[:, 3:3 + NB], closed=arc is None)
    if seams:
        made[0]["geo_stitch"] = True
    print("GIRDLE", name)
    return made


def section(z, keep):
    """Her outline at height z, as points (x, y): where her triangles whose
    points are all `keep` cross that level."""
    tri = TRI[keep[TRI].all(1)]
    out = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        p, q = P[tri[:, i]], P[tri[:, j]]
        s = (p[:, 2] - z) * (q[:, 2] - z) < 0
        t = (z - p[s, 2]) / (q[s, 2] - p[s, 2])
        out.append(p[s, :2] + t[:, None] * (q[s, :2] - p[s, :2]))
    return np.vstack(out)


def bandeau(name, mkey, zc, width, lift=0.004, thick=0.003, trim=None, rows=11, nu=120):
    """A strip of leather round her chest at height `zc`, `width` tall,
    pulled taut: each row of it lies on the convex hull of her body's
    section there (her arms left out), so it runs straight across the
    cleavage from breast to breast as a strap does, never into it. It
    moves with the skin nearest each point of it (her breasts' springs
    included)."""
    from scipy.spatial import ConvexHull
    body_pts = (ARMW["l"] + ARMW["r"] < 0.25) & (HAIR < 0.5)
    zs = np.linspace(zc - width / 2, zc + width / 2, rows)
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    R = np.zeros((rows, nu))
    cxy = None
    for k, z in enumerate(zs):
        # Her outline at this row's own height, exactly (where her triangles
        # cross it). (The hull of her points within a centimetre of it took
        # the fuller breast below for the row above: the upper rows stood 5 to
        # 20 mm off her upper breast, and a camera at her side saw in behind
        # the band to her areola as she vaulted.)
        q = section(z, body_pts)
        if cxy is None:
            cxy = q.mean(0)
        h = ConvexHull(q)
        hv = q[h.vertices]
        d = np.stack([np.sin(a), -np.cos(a)], 1)
        best = np.zeros(nu)
        for i in range(len(hv)):
            p0, p1 = hv[i] - cxy, hv[(i + 1) % len(hv)] - cxy
            e = p1 - p0
            den = d[:, 0] * e[1] - d[:, 1] * e[0]
            ok = np.abs(den) > 1e-12
            t = np.where(ok, (p0[0] * e[1] - p0[1] * e[0]) / np.where(ok, den, 1), -1)
            u = np.where(ok, (p0[0] * d[:, 1] - p0[1] * d[:, 0]) / np.where(ok, den, 1), -1)
            hit = ok & (t > 0) & (u >= 0) & (u <= 1)
            best = np.where(hit, np.maximum(best, t), best)
        R[k] = best
    for _ in range(3):
        R[1:-1] = (R[:-2] + 2 * R[1:-1] + R[2:]) / 4
        R = (np.roll(R, 1, 1) + 2 * R + np.roll(R, -1, 1)) / 4
    R = R + lift
    # Its top and bottom edges pressed onto her, as a strap's edge bites:
    # standing off by its lift, the camera above saw down behind its top.
    R[0] -= lift + 0.001
    R[-1] -= lift + 0.001
    R[1] -= (lift + 0.001) * 0.4
    R[-2] -= (lift + 0.001) * 0.4
    zz = np.repeat(zs[:, None], nu, 1)
    aa = np.repeat(a[None, :], rows, 0)
    pos = np.stack([cxy[0] + R * np.sin(aa), cxy[1] - R * np.cos(aa), zz], -1).reshape(-1, 3)
    idx = np.arange(rows * nu).reshape(rows, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    tris = idx[grid(rows, nu + 1)]
    nor = vertex_normals(pos, tris)
    if (nor[:, :2] * (pos[:, :2] - cxy)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    _, j = cKDTree(P).query(pos)
    edge = np.minimum(pos[:, 2] - zs[0], zs[-1] - pos[:, 2])
    at = np.hstack([nor, W[j].astype(float), edge[:, None]])
    # (all of it on her skin's own weights, her arms' share kept: steadied, it
    # stayed put as her arm drew the skin at her breasts' sides from under it)
    UNSTEADIED.add(name)
    made = trimmed(name, pos, at, tris, mkey, thick, 0.001, trim)
    for o in made:
        o["hides"] = o is made[0]
    print("BANDEAU", name, "at %.3f, %.3f tall" % (zc, width))
    return made


def limb_angle(sd, legs=True):
    """Each point's angle round a limb's upper segment (radians)."""
    a, b = (LEG[sd][0], LEG[sd][1]) if legs else (ARM[sd][0], ARM[sd][1])
    ax = (b - a) / np.linalg.norm(b - a)
    ref = np.cross(ax, [1.0, 0, 0]) if abs(ax[0]) < 0.9 else np.cross(ax, [0, 1.0, 0])
    ref /= np.linalg.norm(ref)
    sec = np.cross(ax, ref)
    d = P - a
    return np.arctan2(d @ sec, d @ ref)


def zigzag_band(sd, s0, legs=True, width=0.014, amp=0.014, teeth=6):
    """A tattooed band round a limb at `s0` along it: a zigzag line,
    `teeth` points round, `amp` high."""
    S = LEG_S[sd] if legs else ARM_S[sd]
    Wm = LEGW[sd] if legs else ARMW[sd]
    th = limb_angle(sd, legs)
    tri = np.arcsin(np.sin(teeth * th)) / (np.pi / 2)
    return AND(width / 2 - np.abs(S - s0 - amp * tri), Wm - 0.5)


def reaver():
    """The reaver: a loincloth panel in front on a belt slung low on her hips, a
    G-string beneath, a strip of leather
    across her breasts, a fur half cape over her left shoulder, fur-topped
    boots and fur cuffs at her wrists, leather bracers, and tattoos: zigzag
    bands round her right arm and left thigh."""
    arms = ARMW["l"] + ARMW["r"]

    def edge(w=0.005, key="darkleather"):
        return (key, w, 0.0004, 0.0013)

    nz = (NIPPLE["l"][2] + NIPPLE["r"][2]) / 2
    # Slung low, where a brief's waistband would run: low in front and
    # behind, rising over the hip bones.
    bz0 = CROTCH + 0.12
    # Behind, it rides up over the top of her cheeks, so they stand clear
    # of it and the string shows from the belt down.
    belt_z = bz0 + 0.05 * np.clip(np.abs(X) / 0.15, 0, 1) ** 2 + 0.07 * (1 - FRONT)
    belt = AND(0.02 - np.abs(Z - belt_z), 0.3 - arms)
    # Fur over her left shoulder only (a mantle down her back clashed
    # with the strap).
    cape = cap(shoulder("l"), 0.13)
    buckle_at = front_point(0.0, bz0)
    buckle_n = np.array(SKIN_BVH.find_nearest(Vector(buckle_at))[1][:])
    # The cord: round the base of her neck behind, over her collarbones, and
    # down to a point above her cleavage; the fangs along its lowest part.
    neck_z = head("neck_01")[2]
    cord = [np.array([0.0, 0.07, neck_z + 0.02]), np.array([0.055, 0.03, neck_z]), np.array([0.07, -0.04, neck_z - 0.045]),
            front_point(0.035, nz + 0.06), front_point(0.0, nz + 0.035), front_point(-0.035, nz + 0.06),
            np.array([-0.07, -0.04, neck_z - 0.045]), np.array([-0.055, 0.03, neck_z]), np.array([0.0, 0.07, neck_z + 0.02])]
    path = on_surface(cord[2:7], step=0.003)
    for _ in range(3):
        path[1:-1] = (path[:-2] + 2 * path[1:-1] + path[2:]) / 4
    low = path[np.argsort(path[:, 2])[:len(path) // 3]]
    low = low[np.argsort(low[:, 0])]
    pick = np.linspace(0, len(low) - 1, 7).round().astype(int)
    fang_at = low[pick]
    fang_out = np.array([SKIN_BVH.find_nearest(Vector(q))[1][:] for q in fang_at])
    fang_down = np.tile([0.0, 0.0, -1.0], (len(fang_at), 1))
    out = [
        # (pulled tight: standing off her by 4 mm, the camera above saw down
        # behind its top to her areola as she ran)
        *bandeau("reaver.strap", "oldleather", nz - 0.01, 0.07, lift=0.0015, trim=edge()),
        *girdle("reaver.belt", lambda a: bz0 + 0.05 * np.clip(np.abs(0.17 * np.sin(a)) / 0.15, 0, 1) ** 2
               + 0.07 * ramp(-np.cos(a), -0.15, 0.35), 0.036, "oldleather", lift=0.006, thick=0.004, trim=edge(0.005)),
        *frame("reaver.buckle", buckle_at + buckle_n * 0.017, buckle_n, np.array([0, 0, 1.0]), 0.05, 0.042, "rust", r=0.0034,
               corner=0.006),
        # The panel's hem cut into a fringe: strips with V-notches between.
        # (columns ~1 mm apart: any closer and the weld merges them)
        *hanging("reaver.loin_front", -0.33, 0.33, bz0, fringe(lambda u: 0.52 + 0.07 * u * u, 11, 0.075, notch=0.26), "oldleather",
                 flare=0.06, lift=0.016, trim=edge(0.01), nu=120),
        # Wolf fangs on a cord round her neck, hanging into her cleavage:
        # trophies of the Verge's wolves.
        *ribbon("reaver.cord", cord, 0.004, "blackleather", lift=0.0025, thick=0.003),
        *fangs("reaver.fangs", fang_at, fang_out, fang_down, "bone"),
        # Beneath it a G-string hung from the belt itself: a narrow front
        # (hidden by the panel) and a string down the back, both running up
        # into the belt, so belt and G-string are one piece of gear.
        *piece("reaver.gstring", OR(
            AND(FRONT - 0.3, np.minimum(0.015 + 0.42 * np.maximum(Z - CROTCH, 0), 0.034) - np.abs(X), (belt_z + 0.005) - Z, Z - (CROTCH - 0.03)),
            ), "oldleather", lift=0.002, smooth=2, soften=0),
        # (opening into the gusset at its foot, as on the warden's thong)
        *ribbon("reaver.gstring_back", back_string(bz0 + 0.07, CROTCH + 0.012), 0.022, "oldleather", lift=0.003, thick=0.004,
                trim=edge(0.004, "blackleather"), snap=False, hides=True, flare=(0.028, 0.03)),
        # (under her a gusset wider than the string, close under her and
        # following her skin, as on the warden's thong)
        *gusset("reaver.gstring_gusset", "oldleather", GAP_F - 0.006, back_string(bz0 + 0.07, CROTCH + 0.012)[-1][1] + 0.006),
        *piece("reaver.cape", cape, "fur", lift=0.012, thick=0.004, smooth=12, soften=10, keep_off=("Head",)),
        *piece("reaver.tattoo_arm", OR(zigzag_band("r", ELBOW_S - 0.12, legs=False), zigzag_band("r", ELBOW_S - 0.06, legs=False, amp=0.01, width=0.012)), "ink", lift=0.0012, thick=0.0002, bevel=0.0, soften=0, budget=10 ** 7),
        *piece("reaver.tattoo_thigh", OR(zigzag_band("l", 0.15), zigzag_band("l", 0.22, amp=0.01, width=0.013)), "ink", lift=0.0012, thick=0.0002, bevel=0.0, soften=0, budget=10 ** 7),
    ]
    for sd in "lr":
        out += [
            *piece(f"reaver.bracer_{sd}", limb(sd, ELBOW_S + 0.05, WRIST_S - 0.04, legs=False), "oldleather", lift=0.004, smooth=6, trim=edge(), studs="rust"),
            *piece(f"reaver.wristfur_{sd}", limb(sd, WRIST_S - 0.05, WRIST_S + 0.005, legs=False), "fur", lift=0.012, thick=0.012, smooth=8),
            *piece(f"reaver.boot_{sd}", limb(sd, KNEE_S - 0.01, 9.9), "oldleather", lift=0.005, smooth=8, iron=300, hull=LEG_S[sd] - ANKLE_S - 0.03),
            *piece(f"reaver.bootfur_{sd}", limb(sd, KNEE_S - 0.05, KNEE_S + 0.06), "fur", lift=0.016, thick=0.016, smooth=10),
        ]
    return out


OUTFITS = {"warden": warden, "arcanist": arcanist, "ranger": ranger, "reaver": reaver}

# How each material is drawn in the game (shaders/heroine_outfit.gdshader):
# leather (grain, burnished edges, stitching), metal (forged, polished at
# the edges, dark in the crevices), cloth (weave, sheen), gloss (latex,
# satin: clean). Fur and sheer stockings have shaders of their own.
KIND = {"steel": "metal", "darksteel": "metal", "gold": "metal", "bronze": "metal", "rust": "metal",
        "velvet": "cloth", "arcvelvet": "cloth", "linen": "cloth", "lace": "cloth", "ink": "cloth",
        "browncloth": "twill", "thread": "gloss", "satin": "gloss", "bone": "leather", "fur": "fur", "stocking": "sheer"}


def kind(key):
    return KIND.get(key, "leather")


def detail(objs, rays=20, reach=0.03):
    """What the outfit's shader needs to know of each point of each piece,
    from the pieces as made (thickened, bevelled), all of the outfit and
    her skin together:
      - how far it is from the piece's edge (its rim, where the sheet turns
        over: the faces that stand across her skin rather than along it), in
        metres: for stitching, burnished and polished edges, and wear;
      - how convex it is there (a bulge is worn, a hollow keeps its dirt);
      - how much of the sky it sees (rays out to 3 cm against everything
        else): darker and dirtier where pieces overlap or meet her;
      - a number for the piece (each its own shade).
    The first two as a second UV, the others as its vertex colours."""
    from mathutils import Vector
    import zlib
    allv, allt = [P], [TRI]
    base = len(P)
    for o in objs:
        me = o.data
        allv.append(np.array([(o.matrix_world @ v.co)[:] for v in me.vertices]))
        allt.append(np.array([[v + base for v in p.vertices[:3]] for p in me.polygons if len(p.vertices) >= 3]))
        base += len(me.vertices)
    bvh = BVHTree.FromPolygons([tuple(q) for q in np.vstack(allv)], np.vstack(allt).tolist())
    rng = np.random.default_rng(1)
    dirs = rng.normal(size=(rays, 3))
    dirs /= np.linalg.norm(dirs, axis=1)[:, None]
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        V = np.array([(o.matrix_world @ v.co)[:] for v in me.vertices])
        Nv = np.array([(o.matrix_world.to_3x3() @ v.normal).normalized()[:] for v in me.vertices])
        # The edge: a sheet knows its own (finish() kept its border). A closed
        # piece (a cord, a rolled binding, a rivet) has none: guessed from its
        # shape, its curve read as edges and drew stitches across it.
        fin = np.isfinite(V).all(1)
        dist = np.full(len(V), 0.05)
        if "rim" in o.keys():
            M = np.array(o.matrix_world)
            rp = np.array(o["rim"].to_list() if hasattr(o["rim"], "to_list") else o["rim"], float).reshape(-1, 3)
            rp = rp @ M[:3, :3].T + M[:3, 3]
            dist[fin] = cKDTree(rp).query(V[fin])[0]
            del o["rim"]
        V = np.where(fin[:, None], V, 0.0)
        Nv = np.where(np.isfinite(Nv).all(1)[:, None], Nv, [0.0, 0.0, 1.0])
        # Convexity: how far each point stands out from the middle of its neighbours, along its normal.
        ev = np.zeros(len(me.edges) * 2, np.int32)
        me.edges.foreach_get("vertices", ev)
        ev = ev.reshape(-1, 2)
        A = sparse.coo_matrix((np.ones(2 * len(ev)), (np.r_[ev[:, 0], ev[:, 1]], np.r_[ev[:, 1], ev[:, 0]])),
                              shape=(len(V), len(V))).tocsr()
        deg = np.asarray(A.sum(1)).ravel()
        has = deg > 0
        mean_nb = lambda x: np.where(has if x.ndim == 1 else has[:, None], (A @ x) / np.maximum(deg, 1)[(slice(None),) + (None,) * (x.ndim - 1)], x)
        d = mean_nb(V) - V
        el = np.array([np.linalg.norm(V[A.indices[A.indptr[i]:A.indptr[i + 1]]] - V[i], axis=1).mean() if deg[i] else 1.0
                       for i in range(len(V))]) + 1e-6
        conv = np.where(has, -(d * Nv).sum(1) / el, 0.0)
        el_med = float(np.median(el)) if len(el) else 0.002
        for _ in range(int(np.clip((0.012 / max(el_med, 1e-4)) ** 2, 3, 120))):
            conv = 0.5 * conv + 0.5 * mean_nb(conv)
        conv = np.tanh(conv * 4) * 0.5 + 0.5
        ao = np.ones(len(V))
        for i in range(len(V)):
            n = Nv[i]
            hemi = dirs * np.sign(dirs @ n)[:, None]
            org = Vector(V[i] + n * 0.0008)
            seen = 0.0
            tot = 0.0
            for d in hemi:
                w = float(d @ n)
                tot += w
                if bvh.ray_cast(org, Vector(d), reach)[0] is None:
                    seen += w
            ao[i] = seen / max(tot, 1e-6)
        # (each point's few rays are noisy: eased over its neighbours, or a
        # smooth plate reads blotched)
        el_mean = float(np.median(el)) if len(el) else 0.002
        for _ in range(int(np.clip((0.015 / max(el_mean, 1e-4)) ** 2, 8, 200))):
            ao = 0.5 * ao + 0.5 * mean_nb(ao)
        loops = np.zeros(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", loops)
        du = me.uv_layers.new(name="detail")
        du.data.foreach_set("uv", np.c_[dist, conv][loops].astype(np.float32).ravel())
        me.uv_layers.active_index = 0
        me.uv_layers[0].active_render = True
        rnd = (zlib.crc32(o.name.split(".")[-1].split("_")[0].encode()) % 1000) / 1000.0
        col = me.color_attributes.new("detail", "FLOAT_COLOR", "POINT")
        painted = 0.0 if o.get("geo_stitch") else 1.0
        col.data.foreach_set("color", np.c_[ao, np.full(len(V), rnd), np.full(len(V), painted), np.ones(len(V))].astype(np.float32).ravel())
        me.color_attributes.active_color = col
    print("DETAIL", len(objs), "pieces")


def material_table(path):
    """The outfit materials' table for the game: each one's kind and how
    many times its texture repeats in a metre (its UVs are in those units)."""
    import json
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({k: {"kind": kind(k), "repeats": v[3]} for k, v in SPEC.items()}, fh, indent=1)

made = []
for name, build in OUTFITS.items():
    if ONLY and name != ONLY:
        continue
    made += [o for o in build() if o]


# ---------------------------------------------------- what must be covered --
# The legal motion check's own regions (tools/legal/motioncheck/marks_section.py),
# measured here at rest after every build: the strip a garment must cover (the
# midline, 1.2 cm either side, from 2.3 cm behind the lowest point under her
# crotch forward to just below the front of her mons, skin facing sideways left
# out) and each areola (2.2 cm round the centre of its pigment). For each outfit,
# how much of each is bare at rest, and how near bare skin comes to it: the margin
# it has to move in before the check sees it. (The motion check proves it moving.)
def _cover_regions():
    mid = np.abs(X) < 0.003
    down = mid & (Z > 0.6) & (Z < 1.1) & (N[:, 2] < -0.9) & (np.abs(N[:, 0]) < 0.6)
    u = P[down][np.argmin(Z[down])]
    fwd = mid & (Y < u[1]) & (Z > u[2]) & (Z < u[2] + 0.15) & (N[:, 1] < -0.8)
    m = P[fwd][np.argmin(Z[fwd])]
    strip = (np.abs(X) < 0.012) & (np.abs(N[:, 0]) < 0.7) & (Y < u[1] + 0.023) & (Z > u[2] - 0.005) & (Z < m[2] - 0.005)
    # Her paint at each point (the darkest of a seam's sides), as the check reads it.
    me = body.data
    img = next(n.image for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
    w_, h_ = img.size
    px = np.array(img.pixels[:]).reshape(h_, w_, 4)[:, :, :3]
    lum_v = np.full(len(me.vertices), 9.0)
    uvl = me.uv_layers.active.data
    for l in me.loops:
        uv_ = uvl[l.index].uv
        c_ = px[min(max(int(uv_[1] * h_), 0), h_ - 1), min(max(int(uv_[0] * w_), 0), w_ - 1)]
        lum_v[l.vertex_index] = min(lum_v[l.vertex_index], 0.3 * c_[0] + 0.59 * c_[1] + 0.11 * c_[2])
    co = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
    _, jl = cKDTree(co).query(P)
    lum = lum_v[jl]
    areolas = {}
    for sd in "lr":
        bn = arm.data.bones[f"breast_{sd}"]
        hd = np.array((arm.matrix_world @ bn.head_local)[:])
        ax_ = np.array((arm.matrix_world @ bn.tail_local)[:]) - hd
        ax_ /= np.linalg.norm(ax_)
        own = W[:, BI[f"breast_{sd}"]] > 0.5
        along = (P - hd) @ ax_
        cand = own & (along >= 0.5 * along[own].max())
        dark = cand & (lum < 0.8 * np.median(lum[cand]))
        areolas[sd] = P[dark].mean(0)
    print("COVER regions: strip %d points, from %.3f to %.3f deep and %.3f to %.3f high; areolas at %s and %s"
          % (strip.sum(), u[1] + 0.023, P[strip, 1].min(), u[2] - 0.005, m[2] - 0.005,
             areolas["l"].round(3), areolas["r"].round(3)))
    return strip, areolas


def cover_report(name, objs, tuck=None):
    """How bare her strip and areolas are under one outfit at rest (see above),
    her skin drawn tucked in as the game draws it (`tuck`: metres, each point)."""
    Pt = P - N * (tuck[:, None] if tuck is not None else 0.0)
    vs, fs = [], []
    for o in objs:
        key = o.data.materials[0].name if o.data.materials else ""
        if key in SPEC and len(SPEC[key]) >= 7:   # (seen through: stockings, lace)
            continue
        base = len(vs)
        vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        fs += [[base + i for i in p.vertices] for p in o.data.polygons]
    if not fs:
        return
    tree = BVHTree.FromPolygons(vs, fs)
    near = np.zeros(len(P), bool)
    for c in [P[COVER_STRIP].mean(0)] + list(COVER_AREOLAS.values()):
        near |= np.linalg.norm(P - c, axis=1) < 0.1
    bare = np.zeros(len(P), bool)
    for i in np.where(near)[0]:
        bare[i] = tree.ray_cast(Vector(Pt[i] + N[i] * 0.0003), Vector(N[i]), 0.03)[0] is None
    # (bare skin facing sideways, the walls of the slot between her thighs, is
    # hidden in it and left out of the strip by the check too: not counted near it)
    seen = bare & (np.abs(N[:, 0]) < 0.7)
    regions = [("strip", COVER_STRIP, seen)] + [("areola %s" % sd, np.linalg.norm(P - c, axis=1) < 0.022, bare)
                                                for sd, c in COVER_AREOLAS.items()]
    for rname, reg, against in regions:
        if not reg.any():
            continue
        bt = cKDTree(P[against]) if against.any() else None
        if bt is None:
            print("COVER %s %s: all of %d points covered; no bare skin within 10 cm" % (name, rname, reg.sum()))
            continue
        d, j = bt.query(P[reg])
        k = int(np.argmin(d))
        where = P[reg][k]
        print("COVER %s %s: %d of %d points bare at rest; bare skin nearest %.1f mm away (at %s)"
              % (name, rname, int((bare & reg).sum()), int(reg.sum()), d[k] * 1000, where.round(3)))


COVER_STRIP, COVER_AREOLAS = _cover_regions()

# Her skin under each outfit's fitted pieces is marked, one colour channel
# an outfit (CHANNELS, as People.cs has them), for the game to draw tucked a
# few millimetres in (shaders/heroine_skin.gdshader): a smooth cup need not
# clear every bump of hers, nothing of her shows through, and since nothing
# of her is cut away no gap can open where a piece moves off her.
# Loose things (a coat, a hat) and sheer ones hide nothing.
if BODY_OUT:
    me = body.data
    col = me.color_attributes.get("hide") or me.color_attributes.new("hide", "BYTE_COLOR", "POINT")
    vals = np.zeros((len(me.vertices), 4))
    vals[:, 3] = 0
    mw3 = body.matrix_world.to_3x3()
    for name in OUTFITS:
        k = CHANNELS.index(name)
        objs = [o for o in made if o.name.startswith(name + ".") and o.get("hides")]
        if not objs or k > 3:
            continue
        vs, fs = [], []
        for o in objs:
            base = len(vs)
            vs += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
            fs += [[base + i for i in p.vertices] for p in o.data.polygons]
        tree = BVHTree.FromPolygons(vs, fs)
        hid = 0
        # Her skin under a piece (it faces the piece, within 12 mm), and
        # where her skin stands proud of the filled form the pieces are cut
        # from (a nipple's tip under a plate cup), from behind too. Never
        # more: skin hidden past a piece's edge shows as a hole in her.
        _, jj = cKDTree(P).query(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices]))
        # (and all of each nipple's disc, under whatever covers it: hidden only
        # at the tip, the skin round the tip came through a plate cup as she
        # ran, the plate and her breast swinging a little apart)
        to_tip = np.minimum(*[np.linalg.norm(P[jj] - q, axis=1) for q in NIPPLE.values()])
        disc = to_tip < 0.028
        proud = ((((P - P_FILLED) * N).sum(1)[jj] > 0.0005) & (P[jj, 2] > CROTCH + 0.12)) | disc
        # (and each nipple's bump, standing proud of the form the pieces are
        # made on, tucked all the way under whatever covers it: tucked only as
        # deep as the piece lay close, 2 to 4 mm off it, its tip came through a
        # cup's outline by a pixel as she swung; at least 2 cm inside every
        # piece's edge, so the deeper tuck can't be seen)
        bump = (((P - P_FILLED) * N).sum(1)[jj] > 0.0005) & (to_tip < 0.012)
        # Tucked as deep as the piece lies close: skin a piece stands well
        # clear of (a pauldron, a bracer) cannot come through it, and tucked
        # there it showed as a deeper gap under the piece's edge as it swung.
        for v in me.vertices:
            co = body.matrix_world @ v.co
            n = (mw3 @ v.normal).normalized()
            hit = tree.ray_cast(co + n * 0.0005, n, 0.012)
            if proud[v.index] and tree.ray_cast(co + n * 0.0005, -n, 0.015)[0] is not None:
                vals[v.index, k] = 1
            elif hit[0] is not None:
                vals[v.index, k] = 1.0 if bump[v.index] else 0.8 * np.clip((0.005 - hit[3] - 0.0005) / 0.004, 0, 1)
            hid += vals[v.index, k] > 0
        # Tucked in gradually from the border, a third, two thirds, then all
        # the way, so her skin slopes under a piece's edge as if it pressed
        # in, rather than stepping down.
        if "_body_nb" not in globals():
            ev = np.array([e.vertices[:] for e in me.edges])
            globals()["_body_nb"] = sparse.coo_matrix((np.ones(2 * len(ev)), (np.r_[ev[:, 0], ev[:, 1]], np.r_[ev[:, 1], ev[:, 0]])),
                                                      shape=(len(me.vertices), len(me.vertices))).tocsr()
        under = vals[:, k] > 0
        reached, ring = ~under, np.zeros(len(under))
        for r_ in (1, 2):
            nxt = under & ~reached & ((_body_nb @ reached.astype(float)) > 0)
            ring[nxt], reached = r_, reached | nxt
        vals[:, k] *= np.where(ring > 0, ring / 3, 1.0)
        if name in BALD:
            # Her hair is part of her body: hidden under a hat that is to carry the look.
            _, j = cKDTree(P).query(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices]))
            hair = HAIR.copy()
            for _ in range(6):
                hair = np.maximum(hair, (ADJ @ hair > 0.05).astype(float))
            vals[(hair[j] > 0.5) & (wsum("Head", "neck_01")[j] > 0.2), k] = 1
        print("HIDES", name, hid, "of", len(me.vertices), "vertices of her skin")
    col.data.foreach_set("color", vals.ravel())
    # Each outfit's coverage at rest, her skin tucked as the game draws it
    # (heroine_skin.gdshader: 10 mm times the outfit's channel).
    _, jb = cKDTree(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])).query(P)
    for name in OUTFITS:
        objs = [o for o in made if o.name.startswith(name + ".")]
        if objs and CHANNELS.index(name) <= 3:
            cover_report(name, objs, 0.010 * vals[jb, CHANNELS.index(name)])
    _, jw = cKDTree(P).query(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices]))
    changed = np.abs(W - W_AUTHORED).sum(1) > 1e-4
    groups = {vg.name: vg for vg in body.vertex_groups}
    n_eased = 0
    for v in me.vertices:
        j = jw[v.index]
        if not changed[j]:
            continue
        for e in list(v.groups):
            body.vertex_groups[e.group].remove([v.index])
        row = W[j]
        top = np.argsort(-row)[:4]
        tot = row[top].sum() or 1.0
        for b in top:
            if row[b] > 0.003:
                vg = groups.get(BONES[b]) or body.vertex_groups.new(name=BONES[b])
                groups[BONES[b]] = vg
                vg.add([v.index], float(row[b] / tot), "REPLACE")
        n_eased += 1
    print("BODY breast weights eased at", n_eased, "of her vertices")
    me.color_attributes.active_color = col
    # Her helper bones (twists at the shoulders and down the forearms, shares
    # at the shoulders, elbows and knees: tools/anim/helpers.py), her weights
    # split onto them; her pieces take the same split below.
    rig_helpers.apply(arm, [body])
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for o in [body] + HEAD_PARTS:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(filepath=BODY_OUT, export_format="GLB", use_selection=True, export_skins=True, export_animations=False,
                              export_yup=True, export_vertex_color="ACTIVE")
    print("BODY", BODY_OUT)

# Nothing else rides along (the scene may hold strays).
for o in [o for o in bpy.data.objects if o not in made and o not in (arm, body)]:
    bpy.data.objects.remove(o)
material_table(os.path.join(os.path.dirname(OUT), "outfit_materials.json"))
# One file an outfit, so the game loads only what she wears.
# (each outfit's pieces listed before any are joined: a joined piece is gone)
# Every piece split onto her helper bones as her skin is, so they move as one.
rig_helpers.apply(arm, made)
pieces_of = {name: [o for o in made if o.name.startswith(name + ".")] for name in OUTFITS}
for name in OUTFITS:
    mine = pieces_of[name]
    if not mine:
        continue
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for o in mine:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    # Text and binary apart, the textures beside them in one folder that
    # every outfit shares (embedded, each file carried its own copies).
    path = os.path.join(os.path.dirname(OUT), f"heroine_outfit_{name}.gltf")
    detail(mine)
    by_mat = {}
    for o in mine:
        by_mat.setdefault(o.data.materials[0].name if o.data.materials else "none", []).append(o)
    joined = []
    for key, objs in by_mat.items():
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        objs[0].name = objs[0].data.name = f"{name}.{key}"
        joined.append(objs[0])
    print("MERGED", name, len(mine), "pieces into", len(joined), "meshes")
    mine = joined
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for o in mine:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLTF_SEPARATE", export_texture_dir="outfit_tex", use_selection=True,
                              export_skins=True, export_animations=False, export_yup=True, export_vertex_color="ACTIVE")
    print("OUTFIT", name, len(mine), "pieces,", sum(len(o.data.polygons) for o in mine), "faces ->", path)
