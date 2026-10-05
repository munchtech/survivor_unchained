"""Her face's paint put right where the painting and her head disagree. Her
face was painted (heroine_face.py) from flat views of her head and laid
back onto it; where a painted feature lands off the shape it belongs to,
she shows it twice, and where no view saw her, her old skin shows through.

- Her upper lids: painted with her eyes open, the painting drew her lash
  line where the lid meets the eye; when she blinks, the lid stretches down
  over the eye and that line with it, into stripes. The lid (what her blink
  moves) is cleaned to skin: every thin dark line closed over by the skin
  round it (a grey-scale closing, keeping the lid's colour and shading).
- Her nose's base: the painting drew her nostrils lower and further forward
  than her nose has them, so she had two on each side. The painted ones are
  lifted out (dark patches too big to be freckles, closed over by the skin
  round them; freckles and pores kept), and her real nostrils darkened from
  her head's own shape: how much of the sky each point of it sees (its
  occlusion, by rays), deep and reddened in the nostrils, a soft shadow in
  the creases round her nose's wings.
- Where her lips meet: the insides of her lips, rolled in to meet, were
  seen by no painting and kept her old skin's colour, a pale, stepped band
  along her mouth. Seen from in front, the faces showing a pale line between
  her lips' red take the colour of the nearest lip.

Every change is drawn into the paint by her UVs and kept to the UV islands
of the faces it is for (never spilling onto another part of her lying
beside them in the paint).

As a step of heroine_head.py (fix(head, path)), or alone on the blend it
saved (from the paint as heroine_head.py made it, kept in RAW):

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_face_fixes.py
"""
import os

import numpy as np

# Her head's paint as heroine_head.py made it, before these fixes (kept so
# they can be run again without compounding).
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "comfy", "out", "heroes", "heroine_head_raw.jpg")


# ------------------------------------------------------------- drawing --
_islands = {}


def islands(head):
    """Each face's UV island (faces joined across an edge whose UVs agree on
    both sides), as a number a face."""
    if head.name in _islands:
        return _islands[head.name]
    me = head.data
    uv = me.uv_layers.active.data
    parent = list(range(len(me.polygons)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    edge = {}
    for p in me.polygons:
        lis = list(p.loop_indices)
        for k in range(len(lis)):
            l0, l1 = lis[k], lis[(k + 1) % len(lis)]
            v0, v1 = me.loops[l0].vertex_index, me.loops[l1].vertex_index
            key = (min(v0, v1), max(v0, v1))
            uvs = {v0: tuple(round(c, 5) for c in uv[l0].uv), v1: tuple(round(c, 5) for c in uv[l1].uv)}
            if key in edge:
                q, quvs = edge[key]
                if quvs == uvs:
                    parent[find(p.index)] = find(q)
            else:
                edge[key] = (p.index, uvs)
    _islands[head.name] = np.array([find(i) for i in range(len(me.polygons))])
    return _islands[head.name]


def _draw(head, faces, w, h):
    """Faces filled in, by their UVs, at a texture's size."""
    from PIL import Image, ImageDraw
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    uv = head.data.uv_layers.active.data
    for p in faces:
        draw.polygon([(uv[li].uv[0] * w, (1 - uv[li].uv[1]) * h) for li in p.loop_indices], fill=255)
    return np.asarray(mask, np.float32) / 255


def faces_mask(head, faces, w, h, grow=7, soft=3):
    """The given faces drawn by their UVs, grown a little and feathered, but
    only over their own UV islands."""
    from scipy import ndimage
    m = _draw(head, faces, w, h)
    isl = islands(head)
    own = set(isl[[p.index for p in faces]].tolist())
    cover = _draw(head, [p for p in head.data.polygons if isl[p.index] in own], w, h)
    cover = ndimage.binary_dilation(cover > 0.5, iterations=2)
    return ndimage.gaussian_filter(ndimage.maximum_filter(m, grow), soft) * cover


def raster(head, values, faces, w, h):
    """Values at her head's points (a row a point) drawn by her UVs, blended
    across each face (a texel past its edges): the image, and where drawn."""
    uv = head.data.uv_layers.active.data
    img = np.zeros((h, w, values.shape[1]), np.float32)
    got = np.zeros((h, w), bool)
    for p in faces:
        vs, lis = list(p.vertices), list(p.loop_indices)
        for j in range(1, len(vs) - 1):
            tri = [0, j, j + 1]
            U = np.array([(uv[lis[t]].uv[0] * w, (1 - uv[lis[t]].uv[1]) * h) for t in tri])
            val = values[[vs[t] for t in tri]]
            x0, y0 = np.floor(U.min(0)).astype(int) - 1
            x1, y1 = np.ceil(U.max(0)).astype(int) + 1
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, w - 1), min(y1, h - 1)
            if x1 < x0 or y1 < y0:
                continue
            T = np.array([[U[0, 0] - U[2, 0], U[1, 0] - U[2, 0]], [U[0, 1] - U[2, 1], U[1, 1] - U[2, 1]]])
            if abs(np.linalg.det(T)) < 1e-9:
                continue
            Ti = np.linalg.inv(T)
            yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
            px, py = xx + 0.5 - U[2, 0], yy + 0.5 - U[2, 1]
            l0 = Ti[0, 0] * px + Ti[0, 1] * py
            l1 = Ti[1, 0] * px + Ti[1, 1] * py
            l2 = 1 - l0 - l1
            tol = -1.0 / max(1.0, float(np.abs(T).max()))
            inside = (l0 >= tol) & (l1 >= tol) & (l2 >= tol)
            v = l0[..., None] * val[0] + l1[..., None] * val[1] + l2[..., None] * val[2]
            img[yy[inside], xx[inside]] = v[inside]
            got[yy[inside], xx[inside]] = True
    return img, got


def sample(head, a):
    """Her paint's colour at each of her head's points (over its corners)."""
    me = head.data
    uv = me.uv_layers.active.data
    h, w = a.shape[:2]
    col = np.zeros((len(me.vertices), 3))
    cnt = np.zeros(len(me.vertices))
    for p in me.polygons:
        for li in p.loop_indices:
            x = min(w - 1, max(0, int(uv[li].uv[0] * w)))
            y = min(h - 1, max(0, int((1 - uv[li].uv[1]) * h)))
            vi = me.loops[li].vertex_index
            col[vi] += a[y, x]
            cnt[vi] += 1
    return col / np.maximum(cnt, 1)[:, None]


def landmarks(head):
    """Her head's points in the world, her eyes' height and her face's front."""
    mw = head.matrix_world
    P = np.array([(mw @ v.co)[:] for v in head.data.vertices])
    eyes = [o for o in head.users_scene[0].objects if o.name == "HeroineEyes"]
    ez = float(np.mean([(eyes[0].matrix_world @ v.co)[2] for v in eyes[0].data.vertices])) if eyes else P[:, 2].max() - 0.12
    return P, ez, P[:, 1].min()


# --------------------------------------------------------------- fixes --
def lids(head, a, moved=0.0015, size=13):
    """Her upper lids cleaned of painted lashes (`a`: the paint, changed in place)."""
    from scipy import ndimage
    me = head.data
    keys = me.shape_keys.key_blocks
    base = np.array([v.co[:] for v in keys["Basis"].data])
    down = np.zeros(len(base), bool)
    for name in ("blink_l", "blink_r"):
        if name in keys:
            d = np.array([v.co[:] for v in keys[name].data]) - base
            down |= (d[:, 2] < -moved)
    faces = [p for p in me.polygons if down[list(p.vertices)].sum() * 2 > len(p.vertices)]
    h, w = a.shape[:2]
    m = faces_mask(head, faces, w, h)[..., None]
    closed = np.stack([ndimage.grey_closing(a[..., c], size=(size, size)) for c in range(3)], -1)
    closed = np.stack([ndimage.gaussian_filter(closed[..., c], 1.2) for c in range(3)], -1)
    a[:] = a * (1 - m) + closed * m
    print("LIDS cleaned:", len(faces), "faces of her upper lids")


def nose(head, a, size=41, freckle=160, rays=96, reach=0.02):
    """Her nose's base: painted nostrils out, her real ones shaded in."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from scipy import ndimage
    me = head.data
    P, ez, front = landmarks(head)
    base = (P[:, 2] < ez - 0.012) & (P[:, 2] > ez - 0.058) & (np.abs(P[:, 0]) < 0.03) & (P[:, 1] < front + 0.045)
    faces = [p for p in me.polygons if base[list(p.vertices)].all()]
    h, w = a.shape[:2]
    m = faces_mask(head, faces, w, h, grow=9, soft=4)[..., None]
    # The painted nostrils lifted out: what is darker than the skin round it
    # (its closing), in patches too big to be a freckle (by area: a painted
    # nostril is long but can be thin), given back.
    closed = np.stack([ndimage.grey_closing(a[..., c], size=(size, size)) for c in range(3)], -1)
    hat = closed - a
    dark = (hat.mean(2) > 8) & (m[..., 0] > 0.05)
    lab, n = ndimage.label(dark)
    area = ndimage.sum(dark, lab, index=np.arange(1, n + 1))
    big = np.isin(lab, np.nonzero(area > freckle)[0] + 1)
    big = ndimage.gaussian_filter(ndimage.binary_dilation(big, iterations=3).astype(np.float32), 2)[..., None]
    a[:] = a + hat * big * m
    # Her real nostrils: each point's openness to the sky (rays over its
    # hemisphere, out to 2 cm), on her nose's base and wings only (not the
    # corners of her eyes, which her eyes' own shading darkens).
    bvh = BVHTree.FromPolygons([tuple(q) for q in P], [tuple(p.vertices) for p in me.polygons])
    mw3 = head.matrix_world.to_3x3()
    N = np.array([(mw3 @ v.normal).normalized()[:] for v in me.vertices])
    near = (P[:, 2] < ez - 0.022) & (P[:, 2] > ez - 0.065) & (np.abs(P[:, 0]) < 0.034) & (P[:, 1] < front + 0.05)
    rng = np.random.default_rng(3)
    dirs = rng.normal(size=(rays, 3))
    dirs /= np.linalg.norm(dirs, axis=1)[:, None]
    open_ = np.ones(len(P))
    for i in np.nonzero(near)[0]:
        nn = N[i]
        hemi = dirs * np.sign(dirs @ nn)[:, None]
        o = Vector(P[i] + nn * 0.0003)
        hit = sum(float(d @ nn) for d in hemi if bvh.ray_cast(o, Vector(d), reach)[0] is not None)
        open_[i] = 1 - hit / max(1e-6, float(np.abs(hemi @ nn).sum()))
    img, got = raster(head, open_[:, None], [p for p in me.polygons if near[list(p.vertices)].any()], w, h)
    shade = np.where(got, ndimage.gaussian_filter(np.where(got, img[..., 0], 1.0), 1.5), 1.0)
    # Deep and reddened where little sky is seen (in the nostrils), a soft
    # shadow where a little is lost (the creases round her nose's wings).
    s = np.clip((shade - 0.25) / 0.6, 0, 1)[..., None]
    deep = np.array([95.0, 38.0, 34.0])
    a[:] = a * (0.35 + 0.65 * s) + deep * (1 - s) * 0.35 * (1 - s)
    print("NOSE cleaned:", len(faces), "faces of her nose's base;", int(near.sum()), "points shaded by her shape")


def front_view(head, a, faces, res=0.0001):
    """Her mouth as seen straight from in front (x across, z up, a pixel
    every tenth of a millimetre): at each pixel the nearest face of those
    given, and her paint's colour there (each face's UVs blended across it)."""
    me = head.data
    mw = head.matrix_world
    P = np.array([(mw @ v.co)[:] for v in me.vertices])
    uv = me.uv_layers.active.data
    vs_all = np.unique(np.concatenate([list(p.vertices) for p in faces]))
    x0, z0 = P[vs_all, 0].min(), P[vs_all, 2].min()
    nx = int((P[vs_all, 0].max() - x0) / res) + 2
    nz = int((P[vs_all, 2].max() - z0) / res) + 2
    depth = np.full((nz, nx), np.inf)
    face = -np.ones((nz, nx), int)
    col = np.zeros((nz, nx, 3), np.float32)
    h, w = a.shape[:2]
    for p in faces:
        vs, lis = list(p.vertices), list(p.loop_indices)
        for j in range(1, len(vs) - 1):
            tri = [0, j, j + 1]
            Q = P[[vs[t] for t in tri]]
            X = (Q[:, 0] - x0) / res
            Z = (Q[:, 2] - z0) / res
            T = np.array([[X[0] - X[2], X[1] - X[2]], [Z[0] - Z[2], Z[1] - Z[2]]])
            if abs(np.linalg.det(T)) < 1e-9:
                continue
            Ti = np.linalg.inv(T)
            i0, i1 = max(int(Z.min()), 0), min(int(Z.max()) + 1, nz - 1)
            k0, k1 = max(int(X.min()), 0), min(int(X.max()) + 1, nx - 1)
            zz, xx = np.mgrid[i0:i1 + 1, k0:k1 + 1]
            px, pz = xx + 0.5 - X[2], zz + 0.5 - Z[2]
            l0 = Ti[0, 0] * px + Ti[0, 1] * pz
            l1 = Ti[1, 0] * px + Ti[1, 1] * pz
            l2 = 1 - l0 - l1
            inside = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
            y = l0 * Q[0, 1] + l1 * Q[1, 1] + l2 * Q[2, 1]          # (nearer her front: smaller y)
            U = np.array([uv[lis[t]].uv[:] for t in tri])
            u = l0 * U[0, 0] + l1 * U[1, 0] + l2 * U[2, 0]
            v = l0 * U[0, 1] + l1 * U[1, 1] + l2 * U[2, 1]
            nearer = inside & (y < depth[zz, xx])
            zi, xi = zz[nearer], xx[nearer]
            depth[zi, xi] = y[nearer]
            face[zi, xi] = p.index
            tx = np.clip((u[nearer] * w).astype(int), 0, w - 1)
            ty = np.clip(((1 - v[nearer]) * h).astype(int), 0, h - 1)
            col[zi, xi] = a[ty, tx]
    return face, col


def lips(head, a):
    """Where her lips meet: seen from in front, a pale line between her upper
    lip and her lower (the insides of her lips, curled back to meet, kept her
    old skin's colour: no painting saw them). Found where it is seen: pale
    pixels her lips' red closes round from above and below. The faces seen
    there take the colour of the nearest lip, a little deeper (wet, in
    shade), on their pale texels only."""
    from scipy import ndimage
    from scipy.spatial import cKDTree
    me = head.data
    P, ez, front = landmarks(head)
    box = (np.abs(P[:, 0]) < 0.035) & (P[:, 2] < ez - 0.05) & (P[:, 2] > ez - 0.12) & (P[:, 1] < front + 0.07)
    faces = [p for p in me.polygons if box[list(p.vertices)].all()]
    face, col = front_view(head, a, faces)
    red = (face >= 0) & (col[..., 0] - col[..., 1] > 55)
    # (her lips only: the big patches of red that cross her middle, not a
    # flush on her cheek, nor her nostrils, reddened by nose() before this:
    # taken for lips, the faces beside them were painted lip-red)
    lab, n = ndimage.label(red)
    area = ndimage.sum(red, lab, index=np.arange(1, n + 1))
    x0 = P[np.unique(np.concatenate([list(p.vertices) for p in faces])), 0].min()
    mid = np.abs(x0 + (np.arange(red.shape[1]) + 0.5) * 0.0001) < 0.002
    crosses = np.unique(lab[:, mid][red[:, mid]])
    red = np.isin(lab, [k for k in np.nonzero(area > 0.05 * area.max())[0] + 1 if k in crosses])
    # (closed over 1.2 mm up and down only: the line between her lips, not round them)
    shut = ndimage.binary_closing(red, structure=np.ones((25, 3), bool))
    band = shut & ~red & (face >= 0) & (col[..., 0] - col[..., 1] < 50)
    hit = np.unique(face[band])
    hit = hit[hit >= 0]
    if not len(hit):
        print("LIPS: nothing between them")
        return
    pts = sample(head, a)
    redv = box & (pts[:, 0] - pts[:, 1] > 55)
    vs = np.unique(np.concatenate([list(me.polygons[i].vertices) for i in hit]))
    fill = pts.copy()
    _, j = cKDTree(P[redv]).query(P[vs])
    fill[vs] = pts[redv][j] * np.array([0.85, 0.78, 0.8])
    h, w = a.shape[:2]
    img, got = raster(head, fill, [me.polygons[i] for i in hit], w, h)
    pale = got & (a[..., 0] - a[..., 1] < 50)
    a[pale] = img[pale]
    print("LIPS:", int(band.sum()), "pixels of a pale line between her lips;", len(hit), "faces,", int(pale.sum()), "texels given her lips' colour")


def fix(head, path, raw=None):
    """All her face's paint put right, the file at `path` (her head's) in
    place, from its raw copy (made from it the first time; `raw` another
    than RAW, for another face's paint)."""
    import shutil
    from PIL import Image
    raw = raw or RAW
    if not os.path.exists(raw):
        os.makedirs(os.path.dirname(raw), exist_ok=True)
        shutil.copy(path, raw)
    a = np.asarray(Image.open(raw).convert("RGB"), np.float32).copy()
    lids(head, a)
    nose(head, a)
    lips(head, a)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(path, quality=92)


if __name__ == "__main__":
    import bpy
    head = bpy.data.objects["HeroineHead"]
    tex = next(n.image for n in head.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE")
    path = bpy.path.abspath(tex.filepath)
    fix(head, path)
    # (packed in the blend: its old paint dropped, the new read and packed)
    if tex.packed_file:
        tex.unpack(method="REMOVE")
    tex.filepath = path
    tex.reload()
    tex.pack()
    bpy.ops.wm.save_mainfile()
