"""Her freckles, as a layer of their own (the skin shader's `freckles` and
`freckle_amount`), not painted into her: none to heavy, chosen in the Look,
each face starting at its portrait's (looks.json's faces, `freckles`).

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_freckles.py -- godot/art/people/head_tex

Laid on her surface, not her UVs, so they are the same size wherever her
paint is finer or coarser: a redhead's, as her portrait has them (her_23),
densest in a band over her nose and across her cheeks, lighter on her
forehead, chin and ears, a few on her neck, and a sun-dusting over her
shoulders and upper chest, thinning to none before her body's own paint
begins, and none over her breasts. Each is soft-edged and uneven (two overlapping spots), 0.6 to 3 mm
across, of its own depth, and has a rank: at an amount a, those ranked under
a show, so a light dusting is the same freckles as a heavy one, fewer.

Written to <out>: heroine_freckles.png (her head's UVs, 2048) and
heroine_freckles_graft.png (the graft's: her neck, shoulders and upper chest,
1024): red each texel's freckle (its depth, soft at its edge), green its rank,
blue how much of her face's grain her skin takes there (all of her head and
neck, none from her collarbones down).
Run again when her head is rebuilt (heroine_head.py).
"""
import os
import sys

import bpy
import numpy as np
from scipy.spatial import cKDTree

OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
rng = np.random.default_rng(23)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def raster(V, T, UV, size):
    """Every texel the triangles cover: row, column, place on her, triangle; and each triangle's area."""
    rows, cols, pts, tri = [], [], [], []
    UVp = UV * size
    for k, t in enumerate(UVp):
        x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        p = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, c = t
        v0, v1, v2 = b - a, c - a, p - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        v = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        w = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        bb = np.stack([1 - v - w, v, w], 1)
        m = (bb > -1e-3).all(1)
        rows.append(ys.ravel()[m])
        cols.append(xs.ravel()[m])
        pts.append((V[T[k]][None] * bb[m][:, :, None]).sum(1))
        tri.append(np.full(m.sum(), k))
    area = 0.5 * np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1)
    return np.concatenate(rows), np.concatenate(cols), np.concatenate(pts), np.concatenate(tri), area


def mesh_tris(o, faces=None):
    me = o.data
    mw = np.array(o.matrix_world)
    V = np.array([v.co[:] for v in me.vertices]) @ mw[:3, :3].T + mw[:3, 3]
    me.calc_loop_triangles()
    lt = [t for t in me.loop_triangles if faces is None or faces(me.polygons[t.polygon_index])]
    T = np.array([t.vertices[:] for t in lt])
    L = np.array([t.loops[:] for t in lt])
    UV = np.array([d.uv[:] for d in me.uv_layers.active.data])[L]
    N = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N /= np.linalg.norm(N, axis=1)[:, None] + 1e-12
    N *= np.sign((N * (V[T].mean(1) - V.mean(0))).sum(1).mean())    # (out from her)
    return V, T, UV, N


def sow(P, tri, area, density):
    """Freckles sown over the texels by density (per square metre): each texel's
    chance its share of its triangle's area times the density there."""
    count = np.bincount(tri, minlength=len(area)).astype(float)
    texel_area = area[tri] / np.maximum(count[tri], 1)
    chance = density * texel_area
    pick = rng.random(len(P)) < chance
    return P[pick]


def freckles(C, N_at):
    """Each freckle as spots: its middle and one beside it (uneven), with a size,
    a depth and a rank. Returns spot centres, radii, depths, ranks."""
    n = len(C)
    r = np.clip(np.exp(rng.normal(np.log(0.0006), 0.45, n)), 0.0003, 0.0015)
    depth = 0.4 + 0.6 * rng.beta(2.0, 2.0, n)
    rank = rng.random(n)
    # (the second spot a little to one side, along her surface)
    t = rng.normal(size=(n, 3))
    t -= (t * N_at).sum(1)[:, None] * N_at
    t /= np.linalg.norm(t, axis=1)[:, None] + 1e-12
    C2 = C + t * (r * rng.uniform(0.35, 0.7, n))[:, None]
    return (np.vstack([C, C2]), np.r_[r, r * rng.uniform(0.5, 0.75, n)], np.r_[depth, depth * 0.85], np.r_[rank, rank])


def draw(P, spots, size, rows, cols):
    C, R, D, K = spots
    img = np.zeros((size, size, 4), np.float32)
    img[..., 3] = 1
    if len(C):
        tree = cKDTree(C)
        dist, idx = tree.query(P, k=6, distance_upper_bound=0.004)
        ok = np.isfinite(dist)
        idx = np.where(ok, idx, 0)
        v = np.where(ok, D[idx] * (1 - smooth((dist / R[idx] - 0.55) / 0.7)), 0)
        best = v.argmax(1)
        val = v[np.arange(len(P)), best]
        rank = np.where(val > 0, K[idx[np.arange(len(P)), best]], 0)
        img[rows, cols, 0] = val
        img[rows, cols, 1] = rank
    return img


def save(img, path):
    from PIL import Image
    a = (np.clip(img[::-1], 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(a).save(path)


# ---------------------------------------------------------------- her face --
head = bpy.data.objects["HeroineHead"]
V, T, UV, FN = mesh_tris(head)
SIZE = 2048
rows, cols, P, tri, area = raster(V, T, UV, SIZE)
N = FN[tri]
eyes = bpy.data.objects["HeroineEyes"]
EV = np.array([(eyes.matrix_world @ v.co)[:] for v in eyes.data.vertices])
ecs = []
for sd in (1, -1):
    e = EV[EV[:, 0] * sd > 0]
    front = e[:, 1].min()
    ecs.append(e[e[:, 1] < front + 0.003].mean(0))
eL, eR = ecs
mid = (eL + eR) / 2
ez = mid[2]
# (her face's front: where her surface faces forward and is in front of her ears)
front = (N[:, 1] < -0.2) & (P[:, 1] < mid[1] + 0.045)
d = P - mid
# the band over her nose and across her cheeks, 2.4 cm under her eyes' line
band = np.exp(-((d[:, 0] / 0.052) ** 2) - (((d[:, 2] + 0.024) / 0.02) ** 2))
dens = np.where(front, 1.0e5 * (0.3 + 1.2 * band), 0.0)               # (per m^2: 10 to 15 a square centimetre)
dens = np.where(front & (d[:, 2] > 0.02), 0.25e5, dens)                  # her forehead
dens = np.where(front & (d[:, 2] < -0.075), 0.15e5, dens)                # her chin
dens = np.where(~front & (np.abs(N[:, 1]) < 0.6) & (d[:, 2] > -0.06) & (d[:, 2] < 0.03), 0.08e5, dens)   # her ears' fronts, her temples
dens = np.where(d[:, 2] < -0.11, 0.05e5, dens)                           # her neck
dens = np.where(d[:, 2] > 0.075, 0.0, dens)                              # (under her hair)
# none in her eyes, their lids and lash lines, nor on her lips
for c in (eL, eR):
    q = P - c
    dens *= smooth((np.hypot(q[:, 0] / 0.021, (q[:, 2] - 0.001) / 0.012) - 1.0) / 0.25)
lips = (np.abs(d[:, 0]) < 0.03) & (d[:, 2] < -0.045) & (d[:, 2] > -0.075) & (P[:, 1] < V[:, 1].min() + 0.03)
dens *= ~lips
C = sow(P, tri, area, dens)
nC = FN[tri][cKDTree(P).query(C)[1]] if len(C) else np.zeros((0, 3))
spots = freckles(C, nC)
print("FRECKLES face: %d (in her band over nose and cheeks %d)" % (len(C), int((np.exp(-(((C - mid)[:, 0] / 0.052) ** 2)
      - ((((C - mid)[:, 2] + 0.024) / 0.02) ** 2)) > 0.5).sum())))
img = draw(P, spots, SIZE, rows, cols)
img[..., 2] = 1                       # (blue: her face's grain on all of her head, her face aside: the skin shader's)
save(img, os.path.join(OUT, "heroine_freckles.png"))

# ---------------------------------------------- her neck, shoulders, chest --
her = bpy.data.objects["Heroine"]
GV, GT, GUV, GFN = mesh_tris(her, lambda p: p.material_index == 1)
GSIZE = 1024
rows, cols, P, tri, area = raster(GV, GT, GUV, GSIZE)
N = GFN[tri]
# (thinning to none toward her body's own paint, 4 cm to 1 cm off it)
body = [p for p in her.data.polygons if p.material_index == 0]
bc = np.array([p.center[:] for p in body]) @ np.array(her.matrix_world)[:3, :3].T + np.array(her.matrix_world)[:3, 3]
off = cKDTree(bc).query(P)[0]
fade = smooth((off - 0.01) / 0.03)
# sun on her shoulders' tops and her upper chest and back, a few on her neck
sun = smooth((N[:, 2] + 0.1) / 0.6) * 0.6 + smooth((-N[:, 1] - 0.2) / 0.5) * 0.4
neck = P[:, 2] > mid[2] - 0.17
# None over her breasts: a sun-dusting thins down her chest, and breasts, clothed most days, are pale; laid over
# them, the freckles read as a speckle (the owner, 6 October: "we want smooth skin aside from pores / freckles",
# "the breasts must look magnificent"). In front, none from her collarbones down (13 to 18 cm over her nipples'
# height, from her body's foremost points: on her upper chest, at the Look's close-up, they too read as specks over
# her breasts); her shoulders, back and neck keep theirs.
BV = np.array([v.co[:] for v in her.data.vertices]) @ np.array(her.matrix_world)[:3, :3].T + np.array(her.matrix_world)[:3, 3]
nips = []
for sd in (1, -1):
    m = (BV[:, 0] * sd > 0.04) & (BV[:, 0] * sd < 0.16) & (BV[:, 2] > 1.34) & (BV[:, 2] < 1.50)
    nips.append(BV[m][np.argmin(BV[m][:, 1])])
nip_z = float(np.mean([q[2] for q in nips]))
front = smooth((-P[:, 1] - 0.02) / 0.04) * (1 - smooth((np.abs(P[:, 0]) - 0.17) / 0.04))
breasts = front * (1 - smooth((P[:, 2] - (nip_z + 0.13)) / 0.05))
dens = np.where(neck, 0.05e5, 0.4e5 * sun) * fade * (1 - breasts)
C = sow(P, tri, area, dens)
nC = GFN[tri][cKDTree(P).query(C)[1]] if len(C) else np.zeros((0, 3))
spots = freckles(C, nC)
print("FRECKLES shoulders and chest: %d (none over her breasts: nipples at %.3f m)" % (len(C), nip_z))
img = draw(P, spots, GSIZE, rows, cols)
# Blue: how much of her face's grain (heroine_grain.png, the skin shader's grain_amount) her skin takes here: all of
# it up her neck, to her face's paint, none from her collarbones down. (Laid over her whole body it was the speckle
# over her breasts: her neck's grain is her face's, her body is smooth but for its pores and freckles.)
img[rows, cols, 2] = smooth((P[:, 2] - 1.47) / 0.08)
# (carried past the islands' edges, so a mipmap never draws a seam of less grain along them)
from scipy import ndimage  # noqa: E402
known = np.zeros(img.shape[:2], bool)
known[rows, cols] = True
_, (iy, ix) = ndimage.distance_transform_edt(~known, return_indices=True)
img[..., 2] = img[..., 2][iy, ix]
save(img, os.path.join(OUT, "heroine_freckles_graft.png"))
