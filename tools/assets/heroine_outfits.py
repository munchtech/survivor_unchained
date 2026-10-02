"""The heroine's outfits, one for each calling, cut from her own body.

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_outfits.py -- <out.glb> [--body <heroine.glb>] [--only warden]

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
FRONT = ramp(-(Y - CROTCH_Y), -0.03, 0.03)          # 1 in front of the body's middle, 0 behind


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
    "fur": ("faux_fur_geometric", (0.6, 0.48, 0.36), None, 4, 0.0, None),
    "arcvelvet": ("velour_velvet", (0.3, 0.3, 1.0), 66, 5, 0.0, None),
    "plumleather": ("Leather026", (0.5, 0.4, 0.75), 44, 3, 0.0, None),
    "blackleather": ("Leather026", (1, 1, 1), 26, 3, 0.0, None),
    "brownleather": ("Leather037", (1, 0.85, 0.75), 42, 3, 0.0, None),
    "lace": ("velour_velvet", (0.3, 0.3, 0.32), 14, 8, 0.0, 0.5),
    "stocking": ("rough_linen", (0.4, 0.38, 0.42), 18, 14, 0.0, 0.45, 0.62),
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


def bubble(pos, tris, clear, out):
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
        for _ in range(6):
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

    target = height(pos) + 0.003
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
    print("BUBBLE pressure %.3f, height %.4f (her breast %.4f)" % (hi, height(x), target - 0.003))
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


def piece(name, field, mkey, lift=0.003, thick=0.003, smooth=0, bevel=0.0012, trim=None, clear=None, soften=3, dome=False, keep_off=("Head", "neck_01"), cut=None):
    """A region of her skin made into a piece of her outfit. `trim`, as
    (material, width, height, thickness), edges it with a band laid on the
    piece itself, so the two can never part. `clear` is how close to the
    skin it may come once smoothed (the lift unless said): plate lifted well
    off and allowed close only at a peak keeps the peak as a hint, not a
    cast of it. `soften` eases the field first; a strap, narrower than
    some of her triangles, is not eased (easing would wear it through)."""
    # Never her head or hair (the hair is part of her mesh).
    f = smooth_field(np.minimum.reduce([field, (0.3 - wsum(*keep_off)) * 0.1, (0.5 - HAIR) * 0.1]), soften)
    # `cut`, a second field, trims the piece after it is shaped: a cup
    # keeps the shape of the full cup however low it is cut.
    attr = np.hstack([N, W, (cut if cut is not None else np.ones(len(P)))[:, None], f[:, None]])
    pos, at, tris = clip(f, P_FILLED if dome else P, attr, TRI)
    if len(tris) == 0:
        print("EMPTY", name)
        return []
    pos, at, tris = weld(pos, at, tris)
    nor = at[:, :3] / (np.linalg.norm(at[:, :3], axis=1)[:, None] + 1e-12)
    pos = pos + nor * lift
    pos = relax(pos, tris, interior=smooth)
    if dome:
        pos = bubble(pos, tris, lift if clear is None else clear, at[:, :3])
        pos, at, tris = mirrored(pos, at, tris)
    if cut is not None:
        at[:, -1] = np.minimum(at[:, -1], at[:, -2])
        cut_done = True
        pos, at, tris = clip(at[:, -2], pos, at, tris)
        pos, at, tris = weld(pos, at, tris)
        pos = relax(pos, tris, interior=0)
    if not dome:
        pos = clear_of_skin(pos, lift if clear is None else clear)
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel)]
    if trim:
        tkey, w, h, tt = trim
        tp, ta, tr = clip(w - at[:, -1], pos, at, tris)
        if len(tr):
            tp, ta, tr = weld(tp, ta, tr)
            tp = relax(tp + vertex_normals(tp, tr) * (thick + h), tr)
            made.append(finish(name + "_trim", tp, ta[:, 3:3 + NB], tr, tkey, tt, bevel))
    for o in made:
        o["hides"] = len(SPEC[mkey]) < 7
    return made


def finish(name, pos, wt, tris, mkey, thick, bevel):
    """A sheet made a piece: her weights, its texture laid out at true size,
    a thickness and a rounded edge, bound to her skeleton."""
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
    so = obj.modifiers.new("thick", "SOLIDIFY")
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


def cups(cover=0.62, plunge=0.02, band=0.03):
    """A cup over each breast and the band under them: the cup takes the
    breast to `cover` of its height above the nipple, and its inner edge
    leaves `plunge` of the cleavage bare."""
    parts = []
    for sd, s in (("l", 1), ("r", -1)):
        n = NIP[sd]
        c = n + np.array([0, 0.035, -0.012])
        r = np.linalg.norm(P - c, axis=1)
        top = n[2] + 0.075 * cover - np.maximum(0, (n[0] - X) * s) * 0.35   # the inner top dips toward the middle
        # Never below 3.5 cm over the nipple itself (hers sit high and to
        # the outside, above the breast's most forward point).
        nip = NIPPLE[sd]
        top = np.maximum(top, nip[2] + 0.035 - 0.5 * np.maximum(0, abs(nip[0]) - np.abs(X)) - 0.8 * np.maximum(0, np.abs(X) - abs(nip[0]) - 0.03))
        parts.append(AND(0.098 - r, top - Z, X * s - plunge, -(Y - 0.02)))
    ub = AND(Z - (UNDERBUST - band), UNDERBUST + 0.006 - Z, 0.4 - ARMW["l"] - ARMW["r"])
    return OR(*parts), ub


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


def trimmed(name, pos, at, tris, mkey, thick, bevel, trim):
    """A sheet and, if asked, the gold along its edge (the field in `at`'s
    last column is the distance in from the edge)."""
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel)]
    if trim:
        tkey, w, h, tt = trim
        tp, ta, tr = clip(w - at[:, -1], pos, at, tris)
        if len(tr):
            tp, ta, tr = weld(tp, ta, tr)
            tp = relax(tp + vertex_normals(tp, tr) * (thick + h), tr)
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
    attr = np.hstack([nor, wt, f[:, None]])
    pos, at, tris = clip(f, pos, attr, tris)
    pos, at, tris = weld(pos, at, tris)
    pos = relax(pos, tris)
    return trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim)


def witch_hat(name, mkey, band_key, brim=0.21, height=0.34, droop=0.09):
    """A wide-brimmed hat with a tall crown that bends back and droops at
    the tip, set on her hair: its crown is as wide as her hair at the brim
    and never nearer it than a centimetre above. All of it is her head's."""
    hd = wsum("Head") > 0.5
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
    bandp = np.array(rings[:4]).reshape(-1, 3)
    bandp[:, :2] = (bandp[:, :2] - [cx, cy]) * 1.03 + [cx, cy]
    bandt = np.arange(4 * nu).reshape(4, nu)
    bandt = np.c_[bandt, bandt[:, :1]].ravel()[grid(4, nu + 1)]
    out = []
    for nm, pp, tt, key, th in ((name + "_crown", crown, ct, mkey, 0.003), (name + "_brim", brimp, bt, mkey, 0.004),
                                (name + "_band", bandp, bandt, band_key, 0.002)):
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
        *piece("warden.cups", cup, "steel", lift=0.009, thick=0.003, clear=0.0015, dome=True, trim=gold()),
        *piece("warden.band", band, "darkleather", lift=0.003, smooth=3),
        *piece("warden.straps", shoulder_straps(), "darkleather", lift=0.0035, soften=0),
        *piece("warden.bottom", bot, "darkleather", lift=0.003, smooth=2),
        *piece("warden.plate", plate, "steel", lift=0.006, thick=0.003, smooth=6, trim=gold(0.006)),
    ]
    for sd in "lr":
        out += [
            *piece(f"warden.pauldron_{sd}", cap(shoulder(sd), 0.11), "steel", lift=0.012, thick=0.004, smooth=14, trim=gold(0.01)),
            *piece(f"warden.vambrace_{sd}", limb(sd, ELBOW_S + 0.05, WRIST_S - 0.01, legs=False), "steel", lift=0.006, smooth=8, trim=gold()),
            *piece(f"warden.greave_{sd}", limb(sd, KNEE_S + 0.03, ANKLE_S + 0.01, front_dip=0.04), "steel", lift=0.008, smooth=12, trim=gold()),
            *piece(f"warden.knee_{sd}", cap(LEG[sd][1] + np.array([0, -0.06, 0]), 0.06), "steel", lift=0.016, thick=0.004, smooth=12, trim=gold(0.006)),
            *piece(f"warden.sabaton_{sd}", limb(sd, ANKLE_S - 0.02, 9.9), "darksteel", lift=0.005, smooth=6),
        ]
    return out


def arcanist():
    """The arcanist: a velvet capelet and sleeves, a plum leather corset
    with gold boning under low velvet half-cups, an open coat that bares
    her thighs, sheer stockings, thigh boots and a witch's hat."""
    def gold(w=0.006):
        return ("gold", w, 0.0004, 0.0013)

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
    corset = AND(ctop - Z, Z - cbot, 0.35 - arms)
    belt_z = 1.0 + 0.035 * X / 0.18
    belt = AND(0.016 - np.abs(Z - belt_z), 0.3 - arms)
    bones = OR(*[strap([np.array([x, -0.25, UNDERBUST - 0.004]), np.array([x * 0.85, -0.25, 1.02 - 0.02 * (abs(x) < 0.05)])], 0.005)
                 for x in (-0.085, -0.04, 0.04, 0.085)])
    bones = AND(bones, corset - 0.004)
    nz = head("neck_01")[2]
    choker = AND(0.009 - np.abs(Z - (nz + 0.035)), wsum("neck_01", "Head") - 0.4, 0.3 - wsum("Head") + wsum("neck_01") * 0, 0.3 - arms)
    mantle = OR(cap(shoulder("l"), 0.14), cap(shoulder("r"), 0.14),
                AND(Z - 1.43, (Y - 0.0), 0.3 - arms))
    out = [
        *piece("arcanist.cups", cup, "arcvelvet", lift=0.009, thick=0.0025, clear=0.0015, dome=True, trim=gold(), cut=low),
        *piece("arcanist.corset", corset, "plumleather", lift=0.0035, smooth=6, trim=gold(0.007)),
        *piece("arcanist.boning", bones, "gold", lift=0.0095, thick=0.0012, smooth=6, soften=0),
        *piece("arcanist.briefs", bottom("full"), "arcvelvet", lift=0.0025, smooth=2),
        *piece("arcanist.mantle", mantle, "arcvelvet", lift=0.016, thick=0.004, smooth=12, trim=gold(0.01)),
        *piece("arcanist.choker", choker, "blackleather", lift=0.002, soften=0, keep_off=("Head",)),
        *piece("arcanist.belt", belt, "brownleather", lift=0.017, thick=0.004, smooth=3),
        *piece("arcanist.buckle", AND(cap(np.array([0.0, -0.2, 1.0]), 0.02), belt), "gold", lift=0.021, thick=0.003, soften=0),
        *hanging("arcanist.apron", -0.3, 0.3, 1.0, lambda u: 0.56 + 0.07 * abs(u), "arcvelvet", flare=0.12, lift=0.012, trim=gold(0.012)),
        *hanging("arcanist.coat", 1.2, 2 * np.pi - 1.2, 1.0, lambda u: 0.3 + 0.16 * abs(u) ** 1.5, "arcvelvet", flare=0.1, lift=0.012, trim=gold(0.014)),
        *witch_hat("arcanist.hat", "arcvelvet", "gold"),
    ]
    for sd in "lr":
        out += [
            *piece(f"arcanist.sleeve_{sd}", limb(sd, 0.17, WRIST_S - 0.03, legs=False), "arcvelvet", lift=0.005, smooth=4, trim=gold(0.01)),
            *piece(f"arcanist.glove_{sd}", limb(sd, WRIST_S - 0.08, 9.9, legs=False), "blackleather", lift=0.0012, thick=0.001, bevel=0.0004),
            *piece(f"arcanist.stocking_{sd}", limb(sd, KNEE_S - 0.2, 9.9), "stocking", lift=0.001, thick=0.0006, bevel=0.0),
            *piece(f"arcanist.lace_{sd}", limb(sd, KNEE_S - 0.2, KNEE_S - 0.165), "lace", lift=0.0022, thick=0.001, soften=1),
            *piece(f"arcanist.boot_{sd}", limb(sd, KNEE_S - 0.05, 9.9, front_dip=-0.03), "brownleather", lift=0.005, smooth=30),
            *piece(f"arcanist.cuff_{sd}", limb(sd, KNEE_S - 0.065, KNEE_S - 0.015), "brownleather", lift=0.009, thick=0.003, smooth=6, trim=gold(0.005)),
        ]
    return out


OUTFITS = {"warden": warden, "arcanist": arcanist}

made = []
for name, build in OUTFITS.items():
    if ONLY and name != ONLY:
        continue
    made += [o for o in build() if o]

# Her skin under each outfit's fitted pieces is marked, one colour channel
# an outfit (in OUTFITS' order), for the game to leave undrawn: a smooth
# cup need not clear every bump of hers, and nothing of her shows through.
# Loose things (a coat, a hat) and sheer ones hide nothing.
if BODY_OUT:
    me = body.data
    col = me.color_attributes.get("hide") or me.color_attributes.new("hide", "BYTE_COLOR", "POINT")
    vals = np.zeros((len(me.vertices), 4))
    vals[:, 3] = 0
    mw3 = body.matrix_world.to_3x3()
    for k, name in enumerate(OUTFITS):
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
        for v in me.vertices:
            co = body.matrix_world @ v.co
            n = (mw3 @ v.normal).normalized()
            if tree.ray_cast(co + n * 0.0005, n, 0.03)[0] is not None:
                vals[v.index, k] = 1
                hid += 1
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
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for o in made:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_skins=True, export_animations=False, export_yup=True)
print("OUTFITS", len(made), "pieces ->", OUT)
