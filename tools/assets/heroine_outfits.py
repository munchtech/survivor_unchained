"""The heroine's outfits, one for each calling, cut from her own body.

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_outfits.py -- <out dir>/x [--body <heroine.glb>] [--only warden]

Each outfit is written as <out dir>/heroine_outfit_<name>.gltf (and .bin), the
textures in <out dir>/outfit_tex.

With --body her body is written again, marked where each outfit hides her.

The scene is the one build_heroine.py saved, so every piece is exported
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

ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = ARGS[0]
ONLY = ARGS[ARGS.index("--only") + 1] if "--only" in ARGS else None
BODY_OUT = ARGS[ARGS.index("--body") + 1] if "--body" in ARGS else None
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "outfit")

arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = next(o for o in bpy.data.objects if o.type == "MESH" and o.parent == arm)
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


HAIR = _hair()
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


def crotch_bridge(name, pos, tris, gap_at, mkey, thick, bevel, trim, lift, rows=18, cols=13):
    """The strip that carries a garment across her crotch: from its front
    cut edge to its back one, each row straight across, its middle along
    the top of the slot (so it spans the gap as cloth does, never dipping
    in), its edges running into her thighs either side."""
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    bv = np.unique(uk[c == 1])
    cutv = bv[(np.abs(gap_at[bv]) < 0.0025) & (pos[bv, 2] < GAP_Z + 0.004)]
    front = cutv[pos[cutv, 1] < CROTCH_Y]
    back = cutv[pos[cutv, 1] >= CROTCH_Y]
    if len(front) < 2 or len(back) < 2:
        print("BRIDGE", name, "no edges to join", len(front), len(back))
        return []

    def resample(ids):
        q = pos[ids][np.argsort(pos[ids, 0])]
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
        t = np.linspace(0, d[-1], cols)
        return np.stack([np.interp(t, d, q[:, k]) for k in range(3)], 1)

    fr, bk = resample(front), resample(back)
    g = np.zeros((rows, cols, 3))
    for i in range(rows):
        t = i / (rows - 1)
        g[i] = fr * (1 - t) + bk * t
    # The middle of each row along the roof of the slot; the whole row
    # lowered with it, so it stays straight across.
    for i in range(1, rows - 1):
        mid = g[i, cols // 2]
        target = min(mid[2], roof_z(mid[0], mid[1]) - lift)
        g[i, :, 2] += target - mid[2]
    for _ in range(6):
        g[1:-1] = (g[:-2] + 2 * g[1:-1] + g[2:]) / 4
    pts = g.reshape(-1, 3)
    tt = grid(rows, cols)
    nor = vertex_normals(pts, tt)
    if nor[:, 2].mean() > 0:            # facing down, out of her
        tt = tt[:, ::-1]
        nor = -nor
    _, j = cKDTree(P).query(pts)
    width = np.linalg.norm(g[:, -1] - g[:, 0], axis=1)
    col = np.tile(np.arange(cols), rows)
    edge = np.minimum(col, cols - 1 - col) / (cols - 1) * np.repeat(width, cols)
    at = np.hstack([nor, W[j].astype(float), edge[:, None]])
    made = trimmed(name + "_bridge", pts, at, tt, mkey, thick, bevel, trim, budget=10 ** 7)
    for o in made:
        o["hides"] = True
    print("BRIDGE", name, "%.1f cm wide in front, %.1f behind" % (width[0] * 100, width[-1] * 100))
    return made          # 1 in front of the body's middle, 0 behind


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
    m = (np.abs(P[:, 0]) > 0.07) & (P[:, 2] > 1.3) & (P[:, 2] < 1.5) & (P[:, 1] < -0.05)
    first = P[np.where(m)[0][np.argmax(proud[m])]]
    out = {}
    for s, sd in ((1, "l"), (-1, "r")):
        guess = np.array([abs(first[0]) * s, first[1], first[2]])
        near = np.where(np.linalg.norm(P - guess, axis=1) < 0.02)[0]
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
    lumps = P[breast & (np.abs(proud) > 0.0018)]
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


def piece(name, field, mkey, lift=0.003, thick=0.003, smooth=0, bevel=0.0012, trim=None, clear=None, soften=3, dome=False, keep_off=("Head", "neck_01"), cut=None, iron=0, hull=None, studs=None, budget=None, filled=False, edge=30, slot=True, bridge=False):
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
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget or (8000 if dome else 3000))]
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


def finish(name, pos, wt, tris, mkey, thick, bevel, budget=3000):
    """A sheet made a piece: her weights, its texture laid out at true size,
    a thickness and a rounded edge, bound to her skeleton. The sheet is
    first thinned to `budget` triangles (cut from a finely divided skin,
    it carries far more than its shape needs)."""
    tris = islands(pos, tris)
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


def smooth_cups(name, mkey, size=1.0, lift=0.005, thick=0.003, trim=None):
    """A pair of cups made as smooth domes, not cut from her skin: an
    ellipsoid fitted to the front of her right breast (the areola filled),
    a patch of it round the nipple with a clean rounded outline (round
    below, rising a little toward the top inner corner), lifted `lift` off
    her, and the same mirrored onto her left. `size` scales the patch.
    Weights from the nearest point of her skin, so the cups move (and
    jiggle) with her breasts; the skin under them is hidden."""
    sd, s_ = "r", -1
    nip = NIPPLE[sd]
    near = (np.linalg.norm(P_FILLED - nip, axis=1) < 0.075) & (N[:, 1] < -0.3) & (P[:, 0] * s_ > 0.01)
    q0 = P_FILLED[near]
    m = q0.mean(0)
    _, _, R = np.linalg.svd(q0 - m)
    q = (q0 - m) @ R.T
    k, *_ = np.linalg.lstsq(np.c_[q ** 2, q], np.ones(len(q)), rcond=None)
    A, B, C, D, E, F = k
    cl = -np.array([D / (2 * A), E / (2 * B), F / (2 * C)])
    g = 1 + A * cl[0] ** 2 + B * cl[1] ** 2 + C * cl[2] ** 2
    ax = np.sqrt(g / np.array([A, B, C]))
    c = m + cl @ R
    # Grown just enough to clear her front under it, then lifted.
    loc = (q0 - c) @ R.T
    ax = ax * np.sqrt(((loc / ax) ** 2).sum(1)).max() + lift
    print("CUP ellipsoid axes", (ax * 100).round(1), "cm")

    def on(d):
        l = d @ R.T
        return c + (l / np.sqrt(((l / ax) ** 2).sum(1))[:, None]) @ R

    # The patch: directions round the one through the nipple; its outline
    # in angle, round with a lift toward up-and-in.
    z = nip - c
    z /= np.linalg.norm(z)
    up = np.array([0.0, 0.0, 1.0]) - z[2] * z
    up /= np.linalg.norm(up)
    side = np.cross(z, up)
    inward = np.array([-s_, 0, 0])
    if side @ inward < 0:
        side = -side
    peak = 0.75 * up + 0.35 * side
    peak /= np.linalg.norm(peak)
    base = math.radians(42) * size
    nr, na = 40, 120
    phi = np.linspace(0, 2 * np.pi, na, endpoint=False)
    dirc = np.cos(phi)[:, None] * up + np.sin(phi)[:, None] * side
    lobe = np.clip(dirc @ peak, 0, 1) ** 3
    tmax = base * (1 + 0.35 * lobe) * (1 - 0.12 * np.clip(-(dirc @ up), 0, 1))
    tmax = (np.roll(tmax, 1) + 2 * tmax + np.roll(tmax, -1)) / 4
    pts, edge = [z[None]], [np.array([tmax.min()])]
    for i in range(1, nr + 1):
        t = tmax * i / nr
        d = np.cos(t)[:, None] * z + np.sin(t)[:, None] * dirc
        pts.append(d)
        edge.append(tmax - t)
    dirs = np.vstack(pts)
    pos = on(dirs)
    # Edge distance in metres (for the trim): angle left times the radius.
    rad = np.linalg.norm(pos - c, axis=1)
    edge = np.concatenate(edge) * rad
    tris = [(0, 1 + j, 1 + (j + 1) % na) for j in range(na)]
    for i in range(nr - 1):
        a0, b0 = 1 + i * na, 1 + (i + 1) * na
        for j in range(na):
            j1 = (j + 1) % na
            tris += [(a0 + j, b0 + j, b0 + j1), (a0 + j, b0 + j1, a0 + j1)]
    tris = np.array(tris)
    nor = vertex_normals(pos, tris)
    if (nor * (pos - c)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    _, j = cKDTree(P).query(pos)
    wt = W[j].astype(float)
    # Mirrored: her left is her right's image.
    mp = pos * np.array([-1, 1, 1])
    pos2 = np.vstack([pos, mp])
    wt2 = np.vstack([wt, wt[:, SWAP]])
    nor2 = np.vstack([nor, nor * np.array([-1, 1, 1])])
    tris2 = np.vstack([tris, tris[:, ::-1] + len(pos)])
    at = np.hstack([nor2, wt2, np.r_[edge, edge][:, None]])
    made = trimmed(name, pos2, at, tris2, mkey, thick, 0.0004, trim, budget=10 ** 7)
    for o in made:
        o["hides"] = True
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
    pos, at, tris = clip(f, pos, attr, tris)
    pos, at, tris = weld(pos, at, tris)
    pos = relax(pos, tris)
    return trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim)


def witch_hat(name, mkey, band_key, brim=0.21, height=0.34, droop=0.09, bald=False):
    """A wide-brimmed hat with a tall crown that bends back and droops at
    the tip, set on her hair: its crown is as wide as her hair at the brim
    and never nearer it than a centimetre above. All of it is her head's."""
    hd = (wsum("Head") > 0.5) & ((HAIR < 0.5) if bald else True)
    top = Z[hd].max()
    upper = hd & (Z > top - 0.1)
    cx, cy = X[upper].mean(), Y[upper].mean()
    zb = top - 0.07
    ang = np.arctan2(X[hd] - cx, -(Y[hd] - cy))
    rad = np.hypot(X[hd] - cx, Y[hd] - cy)
    nu = 64
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)

    def hair_r(z, dz=0.008):
        m = np.abs(Z[hd] - z) < dz
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
def warden():
    """The oath-knight: polished plate over quilted leather, edged in gold."""
    cup, band = cups(cover=0.6, plunge=0.012)
    for sd in "lr":
        print("NIPPLE COVER warden", sd, "cup field %.4f" % cup[np.argmin(np.linalg.norm(P - NIPPLE[sd], axis=1))])
    bot = bottom("cheeky")
    plate = AND(bot, FRONT - 0.5, (CROTCH + 0.13) - Z)

    def gold(w=0.007):
        return ("gold", w, 0.0004, 0.0015)

    out = [
        *smooth_cups("warden.cups", "steel", thick=0.0022),
        *piece("warden.band", band, "darkleather", lift=0.003, smooth=3, soften=25, trim=gold(0.006)),
        *[o for k, cv in enumerate(shoulder_strap_curves()) for o in ribbon(f"warden.strap{k}", cv, 0.016, "darkleather")],
        *piece("warden.bottom", bot, "darkleather", lift=0.003, smooth=2, bridge=True),
        *piece("warden.plate", plate, "steel", lift=0.006, thick=0.003, smooth=6, trim=gold(0.006), studs="gold"),
    ]
    for sd in "lr":
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
    corset = AND(neck_top - Z, OR(Z - 1.13, leotard), sleeve("l"), sleeve("r"))
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


def ranger():
    """The ranger: green leather, asymmetric. Her right arm and shoulder
    bare, the cup there held by a halter strap round her neck; her left in
    a full sleeve with a high collar and a layered bronze pauldron. A laced
    brown corset and belt, a pouch on her left hip; a leotard cut high over
    her right hip, that leg bare to the boot but for a buckled thigh strap,
    her left leg in green leather. Bracers, fingerless gloves, cuffed boots,
    the right one laced."""
    arms = ARMW["l"] + ARMW["r"]

    def gold(w=0.006, key="bronze"):
        return (key, w, 0.0004, 0.0013)

    cup, _ = cups(cover=0.6, plunge=0.012)
    # Above the cups on her left: chest, shoulder, back; and the sleeve.
    # (It stops where the cup begins: under a smooth cup, not over her.)
    upper_l = AND(X + 0.005, Z - (UNDERBUST - 0.04), 0.5 - ARMW["r"], (WRIST_S - 0.03) - ARM_S["l"] + 9 * (ARMW["l"] < 0.5), 0.004 - cup)
    nz = head("neck_01")[2]
    collar = AND(wsum("neck_01", "Head") - 0.3, X + 0.02, (nz + 0.075) - Z, 0.3 - arms)
    halter_curve = [NIPPLE["r"] + np.array([0.01, 0.0, 0.03]), np.array([-0.06, -0.1, 1.5]), np.array([-0.035, -0.06, nz + 0.03]),
                    np.array([0.0, 0.0, nz + 0.05])]
    # The suit below the corset: all round on her left, a high-cut leotard
    # on her right; her left leg in it down into the boot.
    hips = AND(1.06 - Z, Z - (CROTCH - 0.03), 0.3 - arms)
    lower = OR(AND(hips, OR(X + 0.01, bottom("full", top=0.11, side_rise=0.09))), limb("l", 0.0, KNEE_S + 0.05))
    ctop = UNDERBUST + 0.008 + 0.05 * (1 - FRONT)
    corset = AND(ctop - Z, Z - (1.03 - 0.03 * np.exp(-(X / 0.05) ** 2) * FRONT), 0.35 - arms, OFF_BREAST)
    lz = np.linspace(UNDERBUST - 0.03, 1.05, 9)
    lacing = AND(front_poly([((0.02 if i % 2 else -0.02), z) for i, z in enumerate(lz)], 0.011), corset - 0.003)
    belt_z = 1.0 - 0.035 * X / 0.18
    belt = AND(0.018 - np.abs(Z - belt_z), 0.3 - arms)
    thigh = limb("r", 0.13, 0.165)
    fingers = wsum(*[n for n in BONES if n.split("_")[0] in ("index", "middle", "ring", "pinky", "thumb") and n.split("_")[1] in ("02", "03")])
    out = [
        *smooth_cups("ranger.cups", "greenleather", thick=0.0022),
        *piece("ranger.upper", upper_l, "greenleather", lift=0.003, smooth=4),
        *piece("ranger.collar", collar, "greenleather", lift=0.004, smooth=4, keep_off=("Head",), trim=gold(0.006, "brownleather")),
        *ribbon("ranger.halter", halter_curve, 0.024, "brownleather", lift=0.005),
        *piece("ranger.suit", lower, "greenleather", lift=0.0025, smooth=3, slot="right"),
        *piece("ranger.corset", corset, "brownleather", lift=0.0055, smooth=6, soften=25, trim=gold(0.006, "darkleather")),
        *piece("ranger.lacing", lacing, "darkleather", lift=0.013, thick=0.0018, smooth=6, soften=1),
        *piece("ranger.belt", belt, "brownleather", lift=0.014, thick=0.004, smooth=3),
        *piece("ranger.buckle", AND(0.024 - np.linalg.norm(P - front_point(0.03, 1.0 - 0.035 * 0.03 / 0.18), axis=1), belt + 0.004), "bronze", lift=0.019, thick=0.003, smooth=4, soften=1),
        *piece("ranger.thighstrap", thigh, "brownleather", lift=0.004, thick=0.003, smooth=3),
        *piece("ranger.thighbuckle", AND(0.018 - np.linalg.norm(P - front_point(LEG["r"][0][0] - 0.01, LEG["r"][0][2] - 0.145), axis=1), thigh + 0.004), "bronze", lift=0.008, thick=0.003, smooth=3, soften=1),
        *pouch("ranger.pouch", "l", -0.01, 0.95, (0.022, 0.05, 0.06), "brownleather"),
    ]
    sh = shoulder("l")
    for k, (dz, r, lift) in enumerate(((0.0, 0.11, 0.022), (-0.045, 0.1, 0.017), (-0.09, 0.09, 0.012))):
        c = sh + np.array([0.02 * k, 0, dz])
        out += piece(f"ranger.pauldron{k}", AND(cap(c, r), Z - (c[2] - r * 0.55)), "bronze", lift=lift, thick=0.004, smooth=14, trim=gold(0.008, "brownleather"))
    for sd in "lr":
        out += [
            *piece(f"ranger.bracer_{sd}", limb(sd, ELBOW_S + 0.04, WRIST_S - 0.015, legs=False), "bronze", lift=0.007, smooth=8, trim=gold(0.006, "brownleather"), studs="darksteel"),
            *piece(f"ranger.glove_{sd}", AND(limb(sd, WRIST_S - 0.03, 9.9, legs=False), 0.4 - fingers), "darkleather", lift=0.0015, thick=0.0012, bevel=0.0004),
            *piece(f"ranger.boot_{sd}", limb(sd, KNEE_S - 0.03, 9.9), "brownleather", lift=0.005, smooth=8, iron=300, hull=LEG_S[sd] - ANKLE_S - 0.03),
            *piece(f"ranger.cuff_{sd}", limb(sd, KNEE_S - 0.06, KNEE_S + 0.02), "brownleather", lift=0.013, thick=0.004, smooth=8),
        ]
    kx, kz = LEG["r"][1][0], LEG["r"][1][2]
    ax_, az = LEG["r"][2][0], LEG["r"][2][2]
    zs = np.linspace(kz - 0.08, az + 0.06, 11)
    laces = front_poly([(kx + (ax_ - kx) * (kz - 0.08 - z) / (kz - 0.08 - az) + (0.016 if i % 2 else -0.016), z) for i, z in enumerate(zs)], 0.006)
    out += piece("ranger.laces", AND(laces, limb("r", KNEE_S + 0.05, ANKLE_S)), "darkleather", lift=0.0085, thick=0.0015, smooth=4, soften=1)
    return out


CHANNELS = ["warden", "arcanist", "reaver", "ranger"]
BALD = set()
def hull_radius_grid(z0, z1, nu=160, step=0.004, mask=None):
    """Her body's section (arms and hair left out) as a convex hull, its
    radius at each of `nu` angles round her (0 her front), every `step`
    in height from z0 to z1, and the centre it is measured from."""
    from scipy.spatial import ConvexHull
    body_pts = (ARMW["l"] + ARMW["r"] < 0.25) & (HAIR < 0.5) if mask is None else mask
    zs = np.arange(z0, z1 + step, step)
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    d = np.stack([np.sin(a), -np.cos(a)], 1)
    m0 = body_pts & (np.abs(Z - (z0 + z1) / 2) < 0.02)
    cxy = P[m0][:, :2].mean(0)
    R = np.zeros((len(zs), nu))
    for k, z in enumerate(zs):
        q = P[body_pts & (np.abs(Z - z) < 0.006)][:, :2]
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


def girdle(name, zfun, width, mkey, lift=0.004, thick=0.004, trim=None, rows=9, nu=160, mask=None, gap=None):
    """A belt round her, its middle at height zfun(angle) (angle 0 her
    front, rising toward her left), `width` tall, pulled taut over her
    (on the convex hull of her body there), so its edges are two clean
    even curves. It moves with the skin nearest each point of it."""
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    zc = zfun(a)
    zs, _, R, cxy = hull_radius_grid(zc.min() - width, zc.max() + width, nu, mask=mask)
    off = np.linspace(-width / 2, width / 2, rows)
    pos = np.zeros((rows, nu, 3))
    for k, o in enumerate(off):
        z = zc + o
        r = np.array([np.interp(z[j], zs, R[:, j]) for j in range(nu)])
        pos[k] = np.stack([cxy[0] + (r + lift) * np.sin(a), cxy[1] - (r + lift) * np.cos(a), z], -1)
    for _ in range(3):
        pos = (np.roll(pos, 1, 1) + 2 * pos + np.roll(pos, -1, 1)) / 4
    pos = pos.reshape(-1, 3)
    idx = np.arange(rows * nu).reshape(rows, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    tris = idx[grid(rows, nu + 1)]
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
    edge = np.repeat(width / 2 - np.abs(off), nu)
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
    out = [
        *bandeau("reaver.strap", "oldleather", nz - 0.01, 0.07, trim=edge()),
        *girdle("reaver.belt", lambda a: bz0 + 0.05 * np.clip(np.abs(0.17 * np.sin(a)) / 0.15, 0, 1) ** 2
               + 0.07 * ramp(-np.cos(a), -0.15, 0.35), 0.036, "oldleather", lift=0.006, thick=0.004, trim=edge(0.005)),
        *piece("reaver.buckle", AND(0.022 - np.linalg.norm(P - front_point(0.0, bz0), axis=1), belt + 0.004), "rust", lift=0.017, thick=0.003, smooth=4, soften=1),
        *hanging("reaver.loin_front", -0.33, 0.33, bz0, lambda u: 0.52 + 0.07 * u * u, "oldleather", flare=0.06, lift=0.016, trim=edge(0.01)),
        # Beneath it a G-string hung from the belt itself: a narrow front
        # (hidden by the panel) and a string down the back, both running up
        # into the belt, so belt and G-string are one piece of gear.
        *piece("reaver.gstring", OR(
            AND(FRONT - 0.3, np.minimum(0.012 + 0.42 * np.maximum(Z - CROTCH, 0), 0.034) - np.abs(X), (belt_z + 0.005) - Z, Z - (CROTCH - 0.03)),
            ), "oldleather", lift=0.002, smooth=2, soften=0),
        *ribbon("reaver.gstring_back", back_string(bz0 + 0.07, CROTCH + 0.005), 0.022, "oldleather", lift=0.003, thick=0.004,
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
        smoothed = np.linalg.norm(P_FILLED - P, axis=1)[jj] > 1e-4
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
    body.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(filepath=BODY_OUT, export_format="GLB", use_selection=True, export_skins=True, export_animations=False,
                              export_yup=True, export_vertex_color="ACTIVE")
    print("BODY", BODY_OUT)

# Nothing else rides along (the scene may hold strays).
for o in [o for o in bpy.data.objects if o not in made and o not in (arm, body)]:
    bpy.data.objects.remove(o)
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
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLTF_SEPARATE", export_texture_dir="outfit_tex", use_selection=True,
                              export_skins=True, export_animations=False, export_yup=True)
    print("OUTFIT", name, len(mine), "pieces,", sum(len(o.data.polygons) for o in mine), "faces ->", path)
