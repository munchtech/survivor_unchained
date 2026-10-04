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
    path = roof_path(GAP_F - 0.014, GAP_B + 0.014, 18, lift=0.002)
    return ribbon(name + "_gusset", path, 0.013, mkey, lift=0.0, thick=thick, snap=False)


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
    """One perfect form for her breasts: an ellipsoid fitted to the front of
    both (her left mirrored onto her right, so the pair is one shape and
    holds either), grown just enough that every point of both breasts is
    inside it. Its centre, axes (rows of R) and radii, on her right."""
    mirror = np.array([-1.0, 1.0, 1.0])
    front, whole = [], []
    for side_, sg in (("r", -1), ("l", 1)):
        q = NIPPLE[side_]
        near = (np.linalg.norm(P - q, axis=1) < 0.075) & (N[:, 1] < -0.3) & (P[:, 0] * sg > 0.01)
        # (all of each breast that faces out of her, nipples and all: what
        # faces her chest is inside her anyway)
        held = (wsum(f"breast_{side_}") > 0.15) & (P[:, 0] * sg > 0.005) & (N[:, 1] < 0.0)
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
    grow = np.sqrt(((held / ax) ** 2).sum(1)).max()
    print("BREAST FORM axes %s cm (grown x%.3f)" % ((ax * grow * 100).round(1), grow))
    return c, R, ax * grow


BREAST_FORM = breast_ellipsoid()


def ideal_breasts(surface, full=0.05, fade=0.09):
    """A surface with her breasts made the perfect form: each point of each
    breast sent out along the line from the form's centre to the form (only
    out, never in), fully within `full` of her nipple, fading to her own
    shape by `fade`, so whatever is cut from it is uniform over her breasts
    (no lumps, no nipples) and still meets her skin at its edges."""
    c, R, ax = BREAST_FORM
    out = surface.copy()
    for sd, sg in (("r", -1), ("l", 1)):
        flip = np.array([sg * -1.0, 1.0, 1.0])            # (her left onto her right and back)
        q = surface * flip
        loc = (q - c) @ R.T
        r_ell = np.sqrt(((loc / ax) ** 2).sum(1))
        on = c + (loc / np.maximum(r_ell, 1e-9)[:, None]) @ R
        d = np.linalg.norm(surface - NIPPLE[sd], axis=1)
        w = np.clip((fade - d) / (fade - full), 0, 1)
        w = w * w * (3 - 2 * w)
        mine = (surface[:, 0] * sg > 0.0) & (r_ell < 1.0) & (w > 0)
        out[mine] = (q[mine] + (on[mine] - q[mine]) * w[mine, None]) * flip
    return out


# Garments over her breasts are cut from the perfect form, and never lie
# inside her own skin there (the fill that eases her breasts' lumps sinks
# up to centimetres into the curve under them; skin would show through).
P_FILLED = ideal_breasts(P_FILLED)
_on_breast = wsum("breast_l", "breast_r") > 0.01
_out = ((P_FILLED - P) * N).sum(1)
P_FILLED = np.where((_on_breast & (_out < 0))[:, None], P_FILLED - N * _out[:, None], P_FILLED)
print("BREAST FILL kept out of her at", int((_on_breast & (_out < 0)).sum()), "points")


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
    return p2, a2, t2[area > 1e-10]


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
    "darkleather": ("Leather034C", (1, 1, 1), None, 3, 0.0, None),
    "redleather": ("Leather024", (1, 1, 1), None, 4, 0.0, None),
    "oldleather": ("Leather014", (1, 1, 1), None, 4, 0.0, None),
    "velvet": ("velour_velvet", (0.32, 0.1, 0.45), None, 5, 0.0, None),
    "linen": ("rough_linen", (0.3, 0.4, 0.25), None, 5, 0.0, None),
    "fur": ("curly_teddy_natural", (0.55, 0.42, 0.32), 70, 4, 0.0, 0.9),
    "arcvelvet": ("velour_velvet", (0.3, 0.3, 1.0), 66, 5, 0.0, None),
    "plumleather": ("Leather026", (0.5, 0.4, 0.75), 44, 3, 0.0, None),
    "blackleather": ("Leather026", (1, 1, 1), 26, 3, 0.0, None),
    "brownleather": ("Leather037", (1, 0.8, 0.68), 30, 3, 0.0, None),
    "lace": ("rough_linen", (1.0, 1.0, 1.0), 235, 14, 0.0, 0.5, 0.85),
    "darkpurple": ("Leather026", (0.55, 0.2, 0.9), 26, 3, 0.0, 0.35),
    "satin": ("rough_linen", (1.0, 1.0, 1.0), 238, 10, 0.0, 0.3),
    "greenleather": ("Leather026", (0.42, 0.85, 0.45), 52, 3, 0.0, None),
    "bronze": ("Metal048C", (0.72, 0.58, 0.46), 95, 3, 1.0, 0.42),
    "ink": ("rough_linen", (0.22, 0.26, 0.34), 22, 10, 0.0, 0.65),
    "stocking": ("rough_linen", (1.0, 1.0, 1.02), 230, 14, 0.0, 0.45, 0.42),
    "bone": ("rough_linen", (0.92, 0.84, 0.68), 178, 12, 0.0, 0.5),
    "browncloth": ("rough_linen", (0.66, 0.5, 0.36), 112, 6, 0.0, 0.8),
    "forestleather": ("Leather026", (0.42, 0.66, 0.42), 40, 3, 0.0, None),
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
    height above the sheet, wrapping its cut edge). Weights from the
    nearest point of the sheet it binds."""
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
    _, j = cKDTree(src_pos).query(pts)
    obj = finish(name, pts, src_wt[j], tris, mkey, 0.0, 0.0, 10 ** 7)
    obj["hides"] = True
    return obj


def edge_loops(tris):
    """A sheet's edge as loops, found in one pass: each edge of a triangle
    whose reverse no triangle has is on the rim, and following those edges
    the way the triangles wind brings each walk home, pinched corners and
    all, with no searching."""
    from collections import defaultdict
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]).tolist()
    have = set(map(tuple, e))
    out = defaultdict(list)
    for a, b in e:
        if (b, a) not in have:
            out[a].append(b)
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


def bind_edges(name, pos, at, tris, key, width, height, overhang, thick, sigma=0.012):
    """A sheet's cut outline made fair and bound: each edge loop eased into
    one smooth curve, the sheet's own edge points moved onto it, and a
    rolled edge laid along it that covers the cut, as a garment's edges are
    bound or a plate's are rolled."""
    loops = edge_loops(tris)
    if not loops:
        return pos, []
    nor = vertex_normals(pos, tris)
    tree = cKDTree(pos)
    beads = []
    pos = pos.copy()
    moved = np.zeros(len(pos), bool)
    for k, loop in enumerate(loops):
        lp = pos[loop]
        seg = np.linalg.norm(np.diff(np.vstack([lp, lp[:1]]), axis=0), axis=1)
        # A walk that jumped across the sheet, or a hole too small to bind
        # (a finger's), is left as cut.
        if seg.max() > 0.015 or seg.sum() < 0.07:
            continue
        cur = smooth_closed(lp, sigma)
        # Back onto the sheet, and the sheet's normal there.
        _, j = tree.query(cur)
        nrm = nor[j].copy()
        for _ in range(4):
            nrm = (np.roll(nrm, 1, 0) + 2 * nrm + np.roll(nrm, -1, 0)) / 4
        cur = cur + nrm * ((pos[j] - cur) * nrm).sum(1)[:, None]
        tg = np.roll(cur, -1, 0) - np.roll(cur, 1, 0)
        tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
        nrm = nrm - tg * (nrm * tg).sum(1)[:, None]
        nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
        bn = np.cross(nrm, tg)
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
        lt = cKDTree(cur)
        _, jj = lt.query(pos[loop])
        pos[loop] = cur[jj]
        moved[loop] = True
        dn, jn = lt.query(pos)
        near_ = dn < 0.025
        out_ = ((pos - cur[jn]) * outward[jn]).sum(1)
        fix = near_ & (out_ > 0)
        pos[fix] -= outward[jn[fix]] * out_[fix][:, None]
        moved |= fix
        beads.append(tube(f"{name}_bind{k}" if k else f"{name}_bind", cur, nrm, outward, key, width, height, overhang, thick,
                          pos, at[:, 3:3 + NB]))
    # The points next to the edge eased, so the sheet meets its new edge
    # without a crease.
    A = adjacency(len(pos), tris)
    near = (A @ moved.astype(float)) > 0
    near &= ~moved
    for _ in range(6):
        pos = np.where(near[:, None], 0.5 * pos + 0.5 * (A @ pos), pos)
    print("BOUND", name, len(loops), "edge loops")
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
    sp, sw = (P, W) if src is None else src
    _, j = cKDTree(sp).query(pp)
    obj = finish(name, pp, sw[j].astype(float), tt, mkey, 0.0, 0.0, 10 ** 7)
    obj["hides"] = True
    return [obj]


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
    _, j = cKDTree(P).query(pts)
    made = [finish(name, pts, W[j].astype(float), tris, mkey, thick, thick * 0.4, 10 ** 7)]
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
    _, j = cKDTree(P).query(pp)
    obj = finish(name, pp, W[j].astype(float), tt, mkey, 0.0, 0.0, 10 ** 7)
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
    _, j = cKDTree(P).query(pts)
    return [tube(name, pts, nr, out, mkey, 2 * r, 0.0, r, 2 * r, P, W.astype(float))]


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


def clear_of_skin(pos, lift):
    """At least `lift` off her skin everywhere."""
    moved = 0
    for i in range(len(pos)):
        q, n, _, _ = BVH.find_nearest(Vector(pos[i]))
        if q is None:
            continue
        d = (Vector(pos[i]) - q).dot(n)
        if d < lift:
            pos[i] = (Vector(pos[i]) + n * (lift - d))[:]
            moved += 1
    if moved:
        print("CLEAR pushed", moved, "of", len(pos))
    return pos


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
                      (cut if cut is not None else np.ones(len(P)))[:, None], f[:, None]])
    # A garment crossing her crotch is cut off just in front of and just
    # behind the slot between her thighs (`gap` is how far a point is out
    # of that box), and the two cut edges joined by a strip under her.
    gap = np.maximum.reduce([GAP_F - Y, Y - GAP_B, Z - GAP_Z, np.abs(X) - 0.07]) if bridge else np.ones(len(P))
    pos, at, tris = clip(np.minimum(f, gap), P_FILLED if (dome or filled) else P, np.hstack([attr, gap[:, None]]), TRI)
    if len(tris) == 0:
        print("EMPTY", name)
        return []
    pos, at, tris = weld(pos, at, tris)
    gap_at, at = at[:, -1], at[:, :-1]
    nor = at[:, :3] / (np.linalg.norm(at[:, :3], axis=1)[:, None] + 1e-12)
    pos = pos + nor * lift
    if hull is not None:
        pos = hulled(pos, at[:, -3], tris)
    pos = relax(pos, tris, interior=smooth, edge=edge)
    if iron:
        pos = taubin(pos, tris, rounds=iron)
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
        at[:, -1] = np.minimum(at[:, -1], at[:, -2])
        cut_done = True
        pos, at, tris = clip(at[:, -2], pos, at, tris)
        pos, at, tris = weld(pos, at, tris)
        pos = relax(pos, tris, interior=0)
    if not dome and not filled:
        pos = clear_of_skin(pos, lift if clear is None else clear)
    # Every edge bound: in the trim's colour where one is asked, else in the
    # piece's own (a rolled hem). Sheer and painted pieces are left as cut.
    beads = []
    if bind and len(SPEC[mkey]) < 7 and mkey != "ink":
        if trim:
            tkey, w, h, tt = trim
            bspec = (tkey, max(w, 0.005), max(h, 0.0006), 0.0018)
        else:
            bspec = (mkey, 0.0045, 0.0005, 0.0015)
        pos, beads = bind_edges(name, pos, at, tris, bspec[0], bspec[1], bspec[2], bspec[3], thick)
        trim = None
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget or (8000 if dome else 3000))] + beads
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
    for o in made:
        o["hides"] = len(SPEC[mkey]) < 7
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


def steady_on_breasts(wt, least=0.01):
    """Weights with her arms' share taken off wherever her breasts have any
    (that share given to the rest, in proportion; her upper chest's bone if
    nothing else is left)."""
    wt = np.array(wt, float)
    on = wt[:, BREAST_BONES].sum(1) > least
    if not on.any():
        return wt
    w = wt[on].copy()
    w[:, ARM_BONES] = 0
    tot = w.sum(1)
    empty = tot < 1e-6
    w[empty, BI["spine_03"]] = 1
    tot[empty] = 1
    wt[on] = w / tot[:, None]
    return wt


def finish(name, pos, wt, tris, mkey, thick, bevel, budget=3000):
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
    tris = islands(pos, tris)
    # Over her breasts a piece moves with her body and breasts, never her
    # arms: her skin at the outer curve of each breast is partly her arm's,
    # and a garment taking that from it is dragged out of shape when her arm
    # moves (the skin under it is hidden).
    wt = steady_on_breasts(wt)
    # No point left without a bone (it would stay behind when she moves):
    # those take the weights of her skin nearest them.
    tot = wt.sum(1)
    if (tot < 0.01).any():
        _, jz = cKDTree(P).query(pos[tot < 0.01])
        wt = wt.copy()
        wt[tot < 0.01] = W[jz]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pos], [], tris.tolist())
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
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


def ribbon(name, ctrl, width, mkey, lift=0.0035, thick=0.0025, cols=5, trim=None, snap=True):
    """A strap as a strap is made: a ribbon of even width laid along a
    smooth curve on her skin, so its edges are two clean parallel lines.
    It moves with the skin under each point of it."""
    c = on_surface(ctrl, step=0.003)
    if not snap:
        # Taut, as given (it bridges a hollow rather than sinking into it).
        dense = []
        for a, b in zip(ctrl[:-1], ctrl[1:]):
            n = max(2, int(np.linalg.norm(np.array(b) - np.array(a)) / 0.003))
            dense += [np.array(a) + (np.array(b) - np.array(a)) * t for t in np.linspace(0, 1, n, endpoint=False)]
        c = np.array(dense + [np.array(ctrl[-1])])
    for _ in range(3):
        c[1:-1] = (c[:-2] + 2 * c[1:-1] + c[2:]) / 4
        if snap:
            c = np.array([SKIN_BVH.find_nearest(Vector(p))[0][:] for p in c])
    nrm = np.array([SKIN_BVH.find_nearest(Vector(p))[1][:] for p in c])
    for _ in range(4):
        nrm[1:-1] = (nrm[:-2] + 2 * nrm[1:-1] + nrm[2:]) / 4
    nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    tg = np.gradient(c, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
    bn = np.cross(nrm, tg)
    bn /= np.linalg.norm(bn, axis=1)[:, None] + 1e-12
    off = np.linspace(-width / 2, width / 2, cols)
    pos = (c[:, None, :] + nrm[:, None, :] * lift + bn[:, None, :] * off[None, :, None]).reshape(-1, 3)
    tris = grid(len(c), cols)
    nor = vertex_normals(pos, tris)
    if (nor * np.repeat(nrm, cols, 0)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    _, j = cKDTree(P).query(pos)
    edge = np.tile(width / 2 - np.abs(off), len(c))
    at = np.hstack([nor, W[j].astype(float), edge[:, None]])
    made = trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim, budget=10 ** 7)
    for o in made:
        o["hides"] = True
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
    """A pair of plate cups, each a perfect form rather than a cast of her:
    part of one smooth ellipsoid, fitted to the front of her breasts (both,
    her left mirrored onto her right, so the pair is one shape and holds
    either) and grown just enough that every point of both breasts is inside
    it, `lift` more. Nothing of her skin's own lumps reaches it. Below and at
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
    c, R, ax = BREAST_FORM
    ax = ax + lift
    # The ellipsoid as an even mesh of triangles (a geodesic sphere, ~2 mm
    # apart over it): no poles. (A grid by angles has one at the front of
    # each breast, where its lines crowd together, were welded into a flat
    # disc, and showed as a dent at the nipple.)
    ico = bmesh.new()
    bmesh.ops.create_icosphere(ico, subdivisions=6, radius=1.0)
    unit = np.array([v.co[:] for v in ico.verts])
    tris = np.array([[v.index for v in f.verts] for f in ico.faces])
    ico.free()
    pos = c + (unit * ax) @ R
    nor = vertex_normals(pos, tris)
    if (nor * (pos - c)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    # Where it is out of her (her skin's side the normal points to), and
    # within the outline.
    sdist = np.zeros(len(pos))
    for i, q in enumerate(pos):
        loc_, nrm, _, _ = BVH.find_nearest(Vector(q))
        sdist[i] = (Vector(q) - loc_).dot(nrm)
    axs = np.abs(pos[:, 0])
    f = np.minimum.reduce([top(axs) - pos[:, 2], axs - gap, abs(nip[0]) + side - axs, sdist - lift * 0.5,
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
        o_["hides"] = True
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


def hanging(name, a0, a1, z_top, hem, mkey, flare=0.15, lift=0.01, gap=0.012, thick=0.0025, trim=None, nu=56):
    """Cloth hanging from her hips, all round her between the angles a0 and
    a1 (radians; 0 her front, rising toward her left): at each angle it
    falls from the hips, flaring out by `flare` a metre of fall, and never
    nearer her than `gap` (so it goes over her thighs, not into them). Its
    hem is `hem(u)`, u from -1 at a0 to 1 at a1. It is weighted to the
    pelvis at the top and more and more to the thigh on its side below the
    hip, so it swings with her stride."""
    ring = (np.abs(Z - z_top) < 0.008) & (ARMW["l"] + ARMW["r"] < 0.3)
    cy = (Y[ring].min() + Y[ring].max()) / 2
    zs = np.arange(z_top, min(hem(u) for u in np.linspace(-1, 1, 41)) - 0.03, -0.006)
    a = np.linspace(a0, a1, nu)
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
    for k in range(1, len(zs)):
        R[k] = np.where(np.isnan(R[k]), 0, R[k])
    hang = (R[0] + lift)[None, :] + flare * (z_top - zs)[:, None]
    r = np.maximum(hang, R + gap)
    r = np.maximum.accumulate(r, axis=0)
    for _ in range(6):
        r[1:-1] = (r[:-2] + 2 * r[1:-1] + r[2:]) / 4
        r[:, 1:-1] = (r[:, :-2] + 2 * r[:, 1:-1] + r[:, 2:]) / 4
        r = np.maximum(r, R + gap)
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
    f = np.minimum.reduce([pos[:, 2] - zb, z_top - pos[:, 2] + 0.002, arc])
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
    wt = wt * (1 - near[:, None]) + W[body][j] * near[:, None]
    attr = np.hstack([nor, wt, f[:, None]])
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
    # The straps: from each cup's peak, over her shoulder, down her back to
    # the strap round it.
    back_z = UNDERBUST + 0.035
    cups = plate_cups("warden.cups", "steel", plunge_line(), lift=0.003, thick=0.003, trim=gold(0.007), studs="gold")
    # Where her cups meet below her cleavage: the sun of her Order joins them.
    gore_at = np.array([0.0, CUP_LOW[1] - 0.004, CUP_LOW[2] - 0.004])
    buckle_at = front_point(0.0, bz0)
    buckle_n = np.array(SKIN_BVH.find_nearest(Vector(buckle_at))[1][:])
    straps = []
    for sd, sg in (("l", 1), ("r", -1)):
        # (from just under the cup's rim at its peak: it runs up from behind the plate)
        pk = CUP_PEAK[sd]
        top = front_point(pk[0] - sg * 0.004, pk[2] - 0.012)
        straps.append([top, np.array([sg * (abs(pk[0]) - 0.01), -0.05, 1.53]), np.array([sg * 0.11, 0.03, 1.565]),
                       np.array([sg * 0.1, 0.11, 1.47]), np.array([sg * 0.085, 0.125, back_z])])
    out = [
        *cups,
        *[o for k, cv in enumerate(straps) for o in ribbon(f"warden.strap{k}", cv, 0.018, "darkleather", thick=0.003,
                                                          trim=gold(0.003))],
        *girdle("warden.backstrap", lambda a_: np.full_like(a_, back_z), 0.022, "darkleather", lift=0.003, thick=0.003,
                trim=gold(0.003), arc=(1.2, 2 * np.pi - 1.2), mask=arms < 0.3),
        *girdle("warden.belt", belt_z, 0.05, "darkleather", lift=0.006, thick=0.005, trim=gold(0.005)),
        *sunburst("warden.buckle", buckle_at + buckle_n * 0.009, buckle_n, np.array([0, 0, 1.0]), 0.034, "gold",
                  boss="steel"),
        *sunburst("warden.gore", gore_at, np.array([0, -1.0, 0.25]), np.array([0, 0, 1.0]), 0.019, "gold", rays=8,
                  thick=0.003, boss="steel"),

        # Beneath, a thong: a narrow front (under the fauld) and a string
        # down the back from the belt.
        *piece("warden.thong", AND(FRONT - 0.3, np.minimum(0.012 + 0.42 * np.maximum(Z - CROTCH, 0), 0.034) - np.abs(X),
                                   (under_belt + 0.01) - Z, Z - (CROTCH - 0.03)), "darkleather", lift=0.002, smooth=2, soften=0),
        *ribbon("warden.thong_back", thong_path(under_belt + 0.06), 0.02, "darkleather", lift=0.003, thick=0.003, snap=False),
    ]
    # A skirt of steel plates hung all round from the belt, each its own (her
    # legs move freely between them; each swings with the thigh it is over),
    # gold-edged and rounded at its foot: longest in front, over her crotch,
    # shorter behind (the lower curve of her cheeks glimpsed below them); a
    # second row behind the gaps, a little shorter and darker, so nothing
    # shows through them.
    plates = 12
    step = 2 * np.pi / plates
    for row, (lift_, drop, key, w_) in enumerate(((0.021, 0.0, "steel", 0.47), (0.015, 0.02, "darksteel", 0.4))):
        for k in range(plates):
            ac = (k + 0.5 * row) * step
            fr_ = (1 + np.cos(ac)) / 2
            hem = CROTCH - 0.06 * fr_ + 0.035 * (1 - fr_) + drop
            out += hanging(f"warden.skirt{row}_{k}", ac - step * w_, ac + step * w_, under_belt + 0.004,
                           lambda u, h=hem: h + 0.022 * u * u, key, flare=0.14, lift=lift_, gap=0.016, thick=0.0025,
                           trim=gold(0.006) if row == 0 else None)
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
    w = (0.0095 + 0.42 * np.maximum(Z - CROTCH, 0)) * FRONT + (-0.01 + 1.5 * np.maximum(Z - CROTCH - 0.13, 0)) * (1 - FRONT)
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
    corset = AND(neck_top - Z, OR(Z - 1.13, leotard), sleeve("l"), sleeve("r"), plunge)
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
        *ribbon("arcanist.thong", thong_path(CROTCH + 0.155), 0.016, "plumleather", lift=0.003, thick=0.003,
               trim=gold(0.004), snap=False),
        *piece("arcanist.corset", corset, "plumleather", lift=0.0035, smooth=8, trim=gold(0.008), keep_off=("Head",), filled=True, edge=120, soften=80),
        *piece("arcanist.choker", choker, "blackleather", lift=0.002, soften=0, keep_off=("Head",)),
        *witch_hat("arcanist.hat", "plumleather", "darkpurple"),
    ]
    for sd in "lr":
        out += [
            *piece(f"arcanist.glove_{sd}", limb(sd, WRIST_S - 0.08, 9.9, legs=False), "blackleather", lift=0.0012, thick=0.001, bevel=0.0004, trim=gold(0.008), edge=30, soften=12),
            *piece(f"arcanist.stocking_{sd}", AND(LEGW[sd] - 0.5, stock_top(sd) - Z, (X * (1 if sd == "l" else -1) - 0.004) * 0.3), "stocking", lift=0.0012, thick=0.0, bevel=0.0, soften=10),
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
    """The stalker: one fitted bodysuit of brown leather, a corset that
    holds her: strapless, a sweetheart line over her breasts (hugged tight,
    on their perfect form), her shoulders and the top of her chest bare,
    laced up the front over a strip of her skin, cinched, and on down over
    her crotch: cut high over her right hip to a thong behind, so her right
    hip and cheek are bare; her left leg in a light tan pant leg into her
    boot. A belt slung round her hips with a bronze buckle; a buckled strap
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
    # The sweetheart: an arc over each breast, well above the nipple, down
    # to a point between them; behind, a straight band round her back.
    # (round her side at her nipple's height, under her arm, so the whole of
    # each breast is held; the band behind is lower)
    sweet = PchipInterpolator([0.0, 0.025, nx * 0.6, nx, nx + 0.04, nx + 0.09, nx + 0.14],
                              [nzn - 0.014, nzn - 0.004, nzn + 0.026, nzn + 0.034, nzn + 0.03, nzn + 0.012, nzn + 0.0],
                              extrapolate=True)
    top_z = sweet(np.minimum(ax_, nx + 0.14)) * FRONT + (UNDERBUST + 0.06) * (1 - FRONT)
    # Below, each leg's opening a single smooth line round her hip, by the
    # angle round her (0 her front, pi behind): on her right, from her crotch
    # up over her hip bone, high at her side, and down across her cheek to
    # the top of the cleft (her right hip and cheek bare); on her left, a
    # cheeky seat (the lower curve of her cheek bare). Between her legs, a
    # narrow strip, widening a little in front.
    ang = np.abs(np.arctan2(X, -(Y - CROTCH_Y)))
    edge_r = CROTCH + PchipInterpolator([0, 0.5, 1.1, 1.57, 2.1, 2.6, np.pi], [0.02, 0.12, 0.19, 0.21, 0.19, 0.15, 0.13])(ang)
    edge_l = CROTCH + PchipInterpolator([0, 0.6, 1.2, 1.57, 2.1, 2.6, np.pi], [-0.02, 0.0, 0.03, 0.05, 0.065, 0.06, 0.055])(ang)
    rise = np.maximum(Z - CROTCH, 0)
    strip = (0.012 + 0.3 * rise) * FRONT + (0.009 + 0.05 * rise) * (1 - FRONT) - ax_
    legs = OR(Z - np.where(X < 0, edge_r, edge_l), strip)
    # (her breasts always held, however near her arms they come)
    not_arms = np.where(wsum("breast_l", "breast_r") > 0.03, 1.0, 0.5 - arms)
    body = AND(top_z - Z, Z - (CROTCH - 0.025), not_arms, legs)
    # Its front laced across a strip of her skin from under her breasts to
    # her waist.
    lace_top, lace_bot = UNDERBUST - 0.012, float(belt_z(0.0)) + 0.02
    gap = np.where((Z < lace_top) & (Z > lace_bot) & (FRONT > 0.5), ax_ - 0.007, 1.0)
    corset = AND(body, gap)
    lift, thick = 0.0035, 0.003
    rows = np.linspace(lace_top - 0.008, lace_bot + 0.008, 8)
    holes = {}
    for sg in (1, -1):
        e = []
        for z in rows:
            q = front_point(sg * 0.0125, z)
            n = np.array(SKIN_BVH.find_nearest(Vector(q))[1][:])
            e.append((q + n * (lift + thick + 0.0008), n))
        holes[sg] = e
    eyelets = [q for sg in (1, -1) for q, _ in holes[sg]]
    enorm = [n for sg in (1, -1) for _, n in holes[sg]]
    laces = []
    for i in range(len(rows) - 1):
        for sg in (1, -1):
            laces += ribbon(f"ranger.lace{i}{'ab'[sg > 0]}", [holes[sg][i][0], holes[-sg][i + 1][0]], 0.0035, "darkleather",
                            lift=0.0008, thick=0.0012, snap=False)
    # The belt and its buckle; the strap on her right thigh.
    bfront = front_point(0.035, float(belt_z(0.2)))
    bn_ = np.array(SKIN_BVH.find_nearest(Vector(bfront))[1][:])
    tz = leg_z("r", 0.16)
    tpt = front_point(LEG["r"][0][0] - 0.03, tz)
    tn_ = np.array(SKIN_BVH.find_nearest(Vector(tpt))[1][:])
    fingers = wsum(*[n for n in BONES if n.split("_")[0] in ("index", "middle", "ring", "pinky", "thumb") and n.split("_")[1] in ("02", "03")])
    tops = {"r": KNEE_S - 0.03, "l": KNEE_S + 0.1}
    out = [
        *piece("ranger.corset", corset, "forestleather", lift=lift, thick=thick, smooth=8, iron=60, soften=20, slot="right",
               trim=edge(0.006), filled=True, keep_off=("Head", "neck_01")),
        *domes("ranger.eyelets", eyelets, enorm, "bronze", r=0.0026),
        *laces,
        *girdle("ranger.belt", belt_z, 0.042, "brownleather", lift=0.011, thick=0.004, trim=edge(0.005)),
        *frame("ranger.buckle", bfront + bn_ * 0.022, bn_, np.array([0, 0, 1.0]), 0.042, 0.052, "bronze", r=0.0028),
        *girdle("ranger.thighstrap", lambda a: np.full_like(a, tz), 0.028, "brownleather", lift=0.003, thick=0.003,
                trim=edge(0.004), mask=(LEGW["r"] > 0.6) & (np.abs(Z - tz) < 0.05)),
        *frame("ranger.thighbuckle", tpt + tn_ * 0.008, tn_, np.array([0, 0, 1.0]), 0.03, 0.036, "bronze", r=0.0022),
        # Her left leg in light tan leather, from under the corset's edge
        # into her boot.
        # (its top up under the corset in front, below her cheek behind)
        *piece("ranger.pant", limb("l", -0.1, tops["l"] + 0.06, front_dip=-0.19), "browncloth", lift=0.0025, thick=0.0025,
               smooth=6, soften=8, trim=edge(0.004, "brownleather")),
    ]
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
    off = np.linspace(-1, 1, rows)
    pos = np.zeros((rows, nu, 3))
    for k, o in enumerate(off):
        z = zc + o * half
        r = np.array([np.interp(z[j], zs, R[:, j]) for j in range(nu)])
        rl = r + lift + flare * k / (rows - 1)
        pos[k] = np.stack([cxy[0] + rl * np.sin(a), cxy[1] - rl * np.cos(a), z], -1)
    for _ in range(3):
        if arc is None:
            pos = (np.roll(pos, 1, 1) + 2 * pos + np.roll(pos, -1, 1)) / 4
        else:
            pos[:, 1:-1] = (pos[:, :-2] + 2 * pos[:, 1:-1] + pos[:, 2:]) / 4
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
    _, j = cKDTree(P[src]).query(pos)
    j = src[j]
    edge = ((1 - np.abs(off))[:, None] * half[None, :]).ravel()
    if arc is not None:
        run = np.abs(np.diff(a)).mean() * np.mean(R)
        col = np.tile(np.arange(nu), rows)
        edge = np.minimum(edge, np.minimum(col, nu - 1 - col) * run)
    at = np.hstack([nor, W[j].astype(float), edge[:, None]])
    made = trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim, budget=10 ** 7)
    for o in made:
        o["hides"] = True
    print("GIRDLE", name)
    return made


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
        m = body_pts & (np.abs(Z - z) < 0.01)
        q = P[m][:, :2]
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
    made = trimmed(name, pos, at, tris, mkey, thick, 0.001, trim)
    for o in made:
        o["hides"] = True
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
        *bandeau("reaver.strap", "oldleather", nz - 0.01, 0.07, trim=edge()),
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
            AND(FRONT - 0.3, np.minimum(0.012 + 0.42 * np.maximum(Z - CROTCH, 0), 0.034) - np.abs(X), (belt_z + 0.005) - Z, Z - (CROTCH - 0.03)),
            ), "oldleather", lift=0.002, smooth=2, soften=0),
        *ribbon("reaver.gstring_back", thong_path(bz0 + 0.07), 0.022, "oldleather", lift=0.003, thick=0.004,
                trim=edge(0.004, "blackleather"), snap=False),
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
        "browncloth": "cloth", "satin": "gloss", "bone": "leather", "fur": "fur", "stocking": "sheer"}


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
        # The rim: faces that stand square to the sheet round them (the
        # sheet's own way there: the main axis of the normals of the faces
        # near by, either side of it alike), or the sheet's own border if it
        # has no rim. Not square to her skin: under a garment shaped to a
        # perfect form her skin may lie any way.
        fc = np.array([np.mean([V[i] for i in p.vertices], 0) for p in me.polygons])
        fn = np.array([(o.matrix_world.to_3x3() @ p.normal).normalized()[:] for p in me.polygons])
        fc = np.where(np.isfinite(fc), fc, 0.0)
        fn = np.where(np.isfinite(fn), fn, 0.0)
        _, nbr = cKDTree(fc).query(fc, k=min(32, len(fc)))
        _, vec = np.linalg.eigh(np.einsum("fki,fkj->fij", fn[nbr], fn[nbr]))
        rimf = np.abs((fn * vec[:, :, -1]).sum(1)) < 0.5
        rimv = np.unique(np.concatenate([list(me.polygons[i].vertices) for i in np.nonzero(rimf)[0]])) if rimf.any() else np.array([], int)
        if len(rimv) < 3:
            ek = {}
            for p in me.polygons:
                vs = list(p.vertices)
                for a, b in zip(vs, vs[1:] + vs[:1]):
                    k = (min(a, b), max(a, b))
                    ek[k] = ek.get(k, 0) + 1
            rimv = np.unique([v for k, c in ek.items() if c == 1 for v in k]).astype(int)
        # (a broken point, no number at all, is far from every edge and sees the sky)
        fin = np.isfinite(V).all(1)
        rimv = rimv[fin[rimv]]
        dist = np.full(len(V), 0.05)
        if len(rimv):
            dist[fin] = cKDTree(V[rimv]).query(V[fin])[0]
        V = np.where(fin[:, None], V, 0.0)
        Nv = np.where(np.isfinite(Nv).all(1)[:, None], Nv, [0.0, 0.0, 1.0])
        # Convexity: how far each point stands out from the middle of its neighbours, along its normal.
        nb = [[] for _ in range(len(V))]
        for e in me.edges:
            a, b = e.vertices
            nb[a].append(b)
            nb[b].append(a)
        conv = np.zeros(len(V))
        for i, n_ in enumerate(nb):
            if n_:
                d = V[n_].mean(0) - V[i]
                el = np.linalg.norm(V[n_] - V[i], axis=1).mean() + 1e-6
                conv[i] = -(d @ Nv[i]) / el
        for _ in range(3):
            conv = np.array([0.5 * conv[i] + 0.5 * conv[n_].mean() if n_ else conv[i] for i, n_ in enumerate(nb)])
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
        loops = np.zeros(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", loops)
        du = me.uv_layers.new(name="detail")
        du.data.foreach_set("uv", np.c_[dist, conv][loops].astype(np.float32).ravel())
        me.uv_layers.active_index = 0
        me.uv_layers[0].active_render = True
        rnd = (zlib.crc32(o.name.split(".")[-1].split("_")[0].encode()) % 1000) / 1000.0
        col = me.color_attributes.new("detail", "FLOAT_COLOR", "POINT")
        col.data.foreach_set("color", np.c_[ao, np.full(len(V), rnd), np.zeros(len(V)), np.ones(len(V))].astype(np.float32).ravel())
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

# Her skin under each outfit's fitted pieces is marked, one colour channel
# an outfit (CHANNELS, as People.cs has them), for the game to leave undrawn: a smooth
# cup need not clear every bump of hers, and nothing of her shows through.
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
        # Where pieces were shaped over her smoothed skin (nipples, lumps
        # filled), her own skin may stand proud of them: hidden from behind too.
        _, jj = cKDTree(P).query(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices]))
        smoothed = (np.linalg.norm(P_FILLED - P, axis=1)[jj] > 1e-4) & (P[jj, 2] > CROTCH + 0.12)
        for v in me.vertices:
            co = body.matrix_world @ v.co
            n = (mw3 @ v.normal).normalized()
            if tree.ray_cast(co + n * 0.0005, n, 0.012)[0] is not None or (
                    smoothed[v.index] and tree.ray_cast(co + n * 0.0005, -n, 0.015)[0] is not None):
                vals[v.index, k] = 1
                hid += 1
        if name in BALD:
            # Her hair is part of her body: hidden under a hat that is to carry the look.
            _, j = cKDTree(P).query(np.array([(body.matrix_world @ v.co)[:] for v in me.vertices]))
            hair = HAIR.copy()
            for _ in range(6):
                hair = np.maximum(hair, (ADJ @ hair > 0.05).astype(float))
            vals[(hair[j] > 0.5) & (wsum("Head", "neck_01")[j] > 0.2), k] = 1
        print("HIDES", name, hid, "of", len(me.vertices), "vertices of her skin")
    col.data.foreach_set("color", vals.ravel())
    me.color_attributes.active_color = col
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
for name in OUTFITS:
    mine = [o for o in made if o.name.startswith(name + ".")]
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
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLTF_SEPARATE", export_texture_dir="outfit_tex", use_selection=True,
                              export_skins=True, export_animations=False, export_yup=True, export_vertex_color="ACTIVE")
    print("OUTFIT", name, len(mine), "pieces,", sum(len(o.data.polygons) for o in mine), "faces ->", path)
