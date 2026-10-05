"""Her hairstyles, as hair cards: strips of drawn strands grown from her scalp
and draped by their own weight over her head, shoulders and back.

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_hair.py -- godot/art/people [atlas] [style ...]

With HAIR_BLEND=<blend> the styles are kept in a blend too (heroine_built.blend
itself, before heroine_outfits.py, sizes her hats over her long hair).

The strands are drawn once into an atlas (godot/art/people/head_tex/
hair_strands.png): columns of fine strands, each a clump of a kind (dense,
loose, wisps), grey from root to tip for the game to dye. A style is a set of
guide strands, rooted over her scalp (above her hairline) and laid out by
how the style is combed (a parting, swept back, a tie), then let fall: each
a chain of points under gravity, kept its length, stiff near its root, and
held off her head and body (her skin's nearest points, a few millimetres
out). Each guide becomes a card, a strip of the atlas along it facing out
from her, in layers (wide ones close to her, fine ones and stray wisps over
them). Written as heroine_hair_<style>.gltf, weighted to her head and, where
it lies on her, to her skin there.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from scipy.spatial import cKDTree

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import face_shapes as fs  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
ART = os.path.abspath(ARGS[0])
ONLY = ARGS[1:]
TEX = os.path.join(ART, "head_tex")
ATLAS = os.path.join(TEX, "hair_strands.png")
SCALP = os.path.join(TEX, "hair_scalp.png")
# The atlas's columns, each a clump of a kind: dense (the body of the hair),
# loose, locks (gathered to a point at the tip) and wisps (a few strays).
KINDS = ["dense"] * 6 + ["loose"] * 5 + ["lock"] * 3 + ["wisp"] * 2
COLUMNS = len(KINDS)
RNG = np.random.default_rng(11)

arm = bpy.data.objects["Armature"]
head = bpy.data.objects["HeroineHead"]
body = bpy.data.objects["Heroine"]
BONES = [b.name for b in arm.data.bones]
BI = {n: i for i, n in enumerate(BONES)}


# --------------------------------------------------------------- strands --
def padded(img):
    """Colour carried from the nearest strand into the gaps (so filtering at
    a strand's edge takes no black from them)."""
    from scipy import ndimage
    have = img[..., 3] > 8
    _, (iy, ix) = ndimage.distance_transform_edt(~have, return_indices=True)
    img[..., :3] = img[iy, ix, :3]
    return img


def draw_atlas(size=(4096, 2048), over=3):
    """The strands: COLUMNS strips side by side, each a clump of strands from
    its root (the top) to its tip, drawn large and shrunk (soft edges), its
    strands thinning out toward its sides (no hard edge to a card). Red: each
    strand's shade, those at the back of the clump darker; green: a number
    for each strand (the game varies its colour by it); alpha: the strands."""
    from PIL import Image, ImageDraw
    cw, h = size[0] // COLUMNS * over, size[1] * over
    out = np.zeros((size[1], size[0], 4), np.float32)
    for col, kind in enumerate(KINDS):
        r = np.random.default_rng(100 + col)
        n = {"dense": 900, "loose": 380, "lock": 300, "wisp": 24}[kind]
        spread = {"dense": 0.2, "loose": 0.25, "lock": 0.17, "wisp": 0.2}[kind]
        reach = {"dense": (0.8, 1.0), "loose": (0.6, 1.0), "lock": (0.75, 1.0), "wisp": (0.4, 1.0)}[kind]
        gather = {"dense": (0.1, 0.4), "loose": (0.0, 0.3), "lock": (0.6, 0.95), "wisp": (-0.3, 0.3)}[kind]
        strands = []
        for i in range(n):
            x0 = np.clip(r.normal(0.5, spread), 0.03, 0.97) * cw
            t0 = r.uniform(0.0, 0.015)
            t1 = min(1.0, t0 + r.uniform(*reach))
            t = np.linspace(t0, t1, 140)
            f = (t - t0) / (t1 - t0)
            amp = r.uniform(0.0, 0.025) * cw * (2.5 if kind == "wisp" else 1.0)
            xs = x0 + (cw / 2 - x0) * r.uniform(*gather) * f ** 2 + amp * np.sin(2 * np.pi * r.uniform(0.8, 2.5) * t + r.uniform(0, 6.3))
            if r.random() < (0.06 if kind != "wisp" else 0.5):     # a flyaway, drifting off the clump
                xs += np.sign(x0 - cw / 2) * r.uniform(0.05, 0.25) * cw * f ** 2
            strands.append((xs, t * h, f, r.uniform(0.8, 1.5) * over, (0.5 + 0.5 * i / n) * r.uniform(0.8, 1.0), r.uniform(0.02, 0.98)))
        shade, ident, alpha = (Image.new("L", (cw, h), 0) for _ in range(3))
        ds, di, da = ImageDraw.Draw(shade), ImageDraw.Draw(ident), ImageDraw.Draw(alpha)
        # (back to front: the later, lighter strands over the ones behind)
        for xs, ys, f, wd, sh, idv in strands:
            for c0 in range(0, len(xs) - 1, 20):
                c1 = min(c0 + 21, len(xs))
                w = max(1, int(round(wd * (1 - 0.5 * f[c0]))))
                pts = list(zip(xs[c0:c1], ys[c0:c1]))
                ds.line(pts, fill=int(255 * sh * (0.9 + 0.1 * f[c0])), width=w, joint="curve")
                di.line(pts, fill=int(255 * idv), width=w, joint="curve")
        # Alpha: the strands' fading tips first, faintest first (where they
        # cross, the stronger shows: no tip cuts into one behind it), then all
        # their bodies over them.
        tips = []
        for xs, ys, f, wd, sh, idv in strands:
            for k in np.nonzero(f > 0.9)[0][:-1]:
                tips.append((int(255 * (1 - f[k]) / 0.1), (xs[k], ys[k]), (xs[k + 1], ys[k + 1]), max(1, int(round(wd * (1 - 0.5 * f[k]))))))
        for a_, p0, p1, wd_ in sorted(tips, key=lambda q: q[0]):
            da.line([p0, p1], fill=a_, width=wd_)
        for xs, ys, f, wd, sh, idv in strands:
            body_ = np.nonzero(f <= 0.9)[0]
            for c0 in range(0, len(body_) - 1, 20):
                seg = body_[c0:c0 + 21]
                da.line(list(zip(xs[seg], ys[seg])), fill=255, width=max(1, int(round(wd * (1 - 0.5 * f[seg[0]])))), joint="curve")
        small = [np.asarray(im.resize((cw // over, h // over), Image.LANCZOS), np.float32) for im in (shade, ident, alpha)]
        x = col * (size[0] // COLUMNS)
        out[:, x:x + cw // over] = np.stack([small[0], small[1], small[0], small[2]], 2)
    Image.fromarray(np.clip(padded(out), 0, 255).astype(np.uint8)).save(ATLAS)
    print("ATLAS", ATLAS)


def draw_scalp(size=1024, over=2):
    """Strands lying side by side, tiling every way (the cap's, laid along
    the way her hair is combed): long, gently waving, of every shade."""
    from PIL import Image, ImageDraw
    w = size * over
    shade, ident, alpha = (Image.new("L", (w, w), 0) for _ in range(3))
    ds, di, da = ImageDraw.Draw(shade), ImageDraw.Draw(ident), ImageDraw.Draw(alpha)
    r = np.random.default_rng(7)
    y = np.linspace(0, w, 160)
    for i in range(1800):
        x = r.uniform(0, w) + r.uniform(0, 0.02) * w * np.sin(2 * np.pi * r.integers(1, 3) * y / w + r.uniform(0, 6.3))
        wd = max(1, int(round(r.uniform(1.0, 2.0) * over)))
        sh, idv = int(255 * r.uniform(0.35, 1.0)), int(255 * r.uniform(0.02, 0.98))
        for dx in (-w, 0, w):                                       # (and its copies either side: it tiles)
            pts = list(zip(x + dx, y))
            ds.line(pts, fill=sh, width=wd, joint="curve")
            di.line(pts, fill=idv, width=wd, joint="curve")
            da.line(pts, fill=255, width=wd, joint="curve")
    small = [np.asarray(im.resize((size, size), Image.LANCZOS), np.float32) for im in (shade, ident, alpha)]
    img = padded(np.stack([small[0], small[1], small[0], small[2]], 2))
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(SCALP)
    print("SCALP", SCALP)


# ---------------------------------------------------------------- her --
def world(o):
    """An object's points and normals in the world, as it stands."""
    o.data.calc_loop_triangles() if hasattr(o.data, "calc_loop_triangles") else None
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.normal_update()
    mw = o.matrix_world
    P = np.array([(mw @ v.co)[:] for v in bm.verts])
    N = np.array([(mw.to_3x3() @ v.normal).normalized()[:] for v in bm.verts])
    bm.free()
    return P, N


HP, HN = world(head)
BP, BN = world(body)
_up = BP[:, 2] > 0.95
COLLIDE_P = np.vstack([HP, BP[_up]])
COLLIDE_N = np.vstack([HN, BN[_up]])
COLLIDE_HEAD = np.r_[np.ones(len(HP), bool), np.zeros(_up.sum(), bool)]
COLLIDE = cKDTree(COLLIDE_P)
EYES = np.array([(bpy.data.objects["HeroineEyes"].matrix_world @ v.co)[:] for v in bpy.data.objects["HeroineEyes"].data.vertices])
EYE_Z = float(EYES[:, 2].mean())
CENTRE = np.array([0.0, 0.0, EYE_Z + 0.03])            # her skull's middle, near enough


def _key_moves(name):
    """How far a shape key of her head (heroine_head.py's) moves each point."""
    kb = head.data.shape_keys.key_blocks if head.data.shape_keys else {}
    if name not in kb:
        return np.zeros(len(HP))
    co, base = np.zeros(len(HP) * 3), np.zeros(len(HP) * 3)
    kb[name].data.foreach_get("co", co)
    kb[0].data.foreach_get("co", base)
    return np.linalg.norm((co - base).reshape(-1, 3), axis=1)


# Her ears (what her ears' own keys move), where no hair grows: it grows
# in front of them, over them and behind them.
EAR = (_key_moves("ears_out+") > 0.0005) | (_key_moves("ears_pointed+") > 0.0003) | (_key_moves("ears_lobes+") > 0.0003)
EAR_TREE = cKDTree(HP[EAR]) if EAR.any() else None
EAR_V = EAR_TREE.query(HP)[0] < 0.006 if EAR_TREE is not None else np.zeros(len(HP), bool)
# Her neck, between her jaw and her shoulders (her skin there facing out,
# not up or down), which hair hanging by it is kept well clear of: lying on
# it, a strand read as a scratch on her skin, and as her head turned, the
# strands weighted partly to her head and partly to her body were drawn
# into it.
_nz = COLLIDE_P[:, 2] - EYE_Z
NECK = (_nz > -0.17) & (_nz < -0.085) & (np.hypot(COLLIDE_P[:, 0], COLLIDE_P[:, 1] - 0.03) < 0.085) & (np.abs(COLLIDE_N[:, 2]) < 0.6)
NECK_CLEAR = 0.016


def hairline_z(theta):
    """Height of her hairline at an angle round her head (0 her front):
    face_shapes.HAIRLINE, over her eyes."""
    return EYE_Z + fs.hairline_height(theta)


def scalp(below=0.0):
    """Her head's surface above her hairline (and `below` it), as triangles
    (not her ears)."""
    me = head.data
    me.calc_loop_triangles()
    T = np.array([t.vertices[:] for t in me.loop_triangles])
    c = HP[T].mean(1)
    theta = np.arctan2(c[:, 0] - CENTRE[0], -(c[:, 1] - CENTRE[1]))
    ear = EAR_TREE.query(c)[0] < 0.006 if EAR_TREE is not None else (np.abs(c[:, 0]) > 0.079) & (c[:, 2] < EYE_Z + 0.05)
    # (her outside only: not the inside of her mouth, nose or ears, deep in
    # her head. Facing away from her middle is not enough: shaped from her
    # reference, the roof of her mouth lies behind her middle, under her
    # nape's hairline, and hair grew from it out under her jaw. Her outside
    # is as far out as her head goes that way, at that height, her ears
    # aside, within 6 mm; and never near the middle of her head below her
    # crown, where only her mouth's inside is.)
    n = np.cross(HP[T[:, 1]] - HP[T[:, 0]], HP[T[:, 2]] - HP[T[:, 0]])
    r = c - CENTRE
    outside = (np.linalg.norm(r, axis=1) > 0.06) & ((n * r).sum(1) > 0)
    core = (np.hypot(r[:, 0], r[:, 1]) < 0.045) & (c[:, 2] < EYE_Z + 0.06)
    return T[(c[:, 2] > hairline_z(theta) - below) & ~ear & outside & ~core & (depth_in(c) < 0.006)]


def depth_in(c):
    """How far each point lies inside her head's outline round her middle
    (at its own height and angle; her ears not part of the outline)."""
    ok = ~EAR_V
    th = np.degrees(np.arctan2(HP[ok, 0] - CENTRE[0], -(HP[ok, 1] - CENTRE[1])))
    rr = np.hypot(HP[ok, 0] - CENTRE[0], HP[ok, 1] - CENTRE[1])
    key = lambda t, z: (np.floor((t + 180) / 5).astype(int) % 72) * 1000 + np.floor(z / 0.005).astype(int) % 1000
    outer = {}
    for k, r_ in zip(key(th, HP[ok, 2]), rr):
        outer[k] = max(outer.get(k, 0.0), r_)
    tc = np.degrees(np.arctan2(c[:, 0] - CENTRE[0], -(c[:, 1] - CENTRE[1])))
    rc = np.hypot(c[:, 0] - CENTRE[0], c[:, 1] - CENTRE[1])
    return np.array([outer.get(k, r_) - r_ for k, r_ in zip(key(tc, c[:, 2]), rc)])


def roots(spacing, above=0.0, below=None, soft=0.0):
    """Points over her scalp about `spacing` apart (randomly, evenly), at
    least `above` over her hairline (and with `below`, no more than that);
    with `soft`, fewer and fewer of them toward that edge over so far (no
    row of roots: the hair thins out to its edge, as a real hairline does)."""
    T = scalp(below=max(0.0, -above))
    c = HP[T].mean(1)
    theta = np.arctan2(c[:, 0] - CENTRE[0], -(c[:, 1] - CENTRE[1]))
    up = c[:, 2] - hairline_z(theta)
    # (`above` over her forehead, easing to a quarter of it by her ears: hair hanging there needs its roots)
    margin = above * np.interp(np.degrees(np.abs(theta)), [0, 50, 80], [1.0, 1.0, 0.25])
    T = T[(up >= margin) & (up <= (below if below is not None else 1.0))]
    a, b, c = HP[T[:, 0]], HP[T[:, 1]], HP[T[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    n = int(area.sum() / (spacing ** 2) * 3)
    k = RNG.choice(len(T), n, p=area / area.sum())
    u, v = RNG.random(n), RNG.random(n)
    flip = u + v > 1
    u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
    pts = a[k] + (b[k] - a[k]) * u[:, None] + (c[k] - a[k]) * v[:, None]
    nrm = np.cross(b - a, c - a)[k]
    nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    # thinned to the spacing (a point kept unless one kept is nearer)
    keep = []
    tree = None
    order = RNG.permutation(n)
    kept_pts = []
    for i in order:
        if kept_pts and tree is not None and tree.query(pts[i])[0] < spacing:
            continue
        kept_pts.append(pts[i])
        keep.append(i)
        if len(keep) % 50 == 0:
            tree = cKDTree(np.array(kept_pts))
    keep = np.array(keep)
    pts, nrm = pts[keep], nrm[keep]
    # (a final pass, the tree rebuilt on all of them)
    d, _ = cKDTree(pts).query(pts, k=2)
    good = d[:, 1] > spacing * 0.7
    pts, nrm = pts[good], nrm[good]
    if soft > 0:
        th = np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))
        m = above * np.interp(np.degrees(np.abs(th)), [0, 50, 80], [1.0, 1.0, 0.25])
        p = np.clip((rise(pts) - m) / soft, 0, 1)
        keep = RNG.random(len(pts)) < 0.12 + 0.88 * p * p * (3 - 2 * p)
        pts, nrm = pts[keep], nrm[keep]
    return pts, nrm


# --------------------------------------------------------------- falling --
def lie(starts, dirs, comb, L, steps, offset, side=None, lift=0.0, stop=None):
    """Each strand laid along her scalp from its root, `offset` off it, a
    link at a time, turned more and more the way `comb` (a function of
    where it is, and which side of a parting its root is: `side`, or her
    parting's) says, for as many links as `steps` says (each its own),
    rising `lift` more off her by its tip; a strand stops where `stop`
    says (its last points then all there): combed hair lies on the head
    before it falls."""
    S = len(starts)
    K = int(steps.max()) + 1
    paths = np.zeros((S, K, 3))
    p = starts.copy()
    d = dirs.copy()
    paths[:, 0] = p
    side = part_side(starts) if side is None else side         # (each keeps to its root's side of her parting)
    lift = np.broadcast_to(np.asarray(lift, float), (S,))
    held = np.zeros(S, bool)
    r0 = rise(starts)
    for k in range(1, K):
        want = comb(p, side)
        _, idx = COLLIDE.query(p, k=3)
        n = COLLIDE_N[idx].mean(1)
        n /= np.linalg.norm(n, axis=1)[:, None] + 1e-9
        d = d * 0.6 + want * 0.4
        d -= n * (d * n).sum(1)[:, None]
        d /= np.linalg.norm(d, axis=1)[:, None] + 1e-9
        q = p + d * L[:, None]
        _, idx = COLLIDE.query(q, k=3)
        c, n = COLLIDE_P[idx].mean(1), COLLIDE_N[idx].mean(1)
        n /= np.linalg.norm(n, axis=1)[:, None] + 1e-9
        # (rising to its height off her over its first 4 cm: no root standing up off her scalp)
        h = offset * np.clip(k * L / 0.04, 0.2, 1.0) + lift * np.clip(k / np.maximum(steps, 1), 0, 1)
        q = q - n * (((q - c) * n).sum(1) - h)[:, None]
        # (never down over her face: a strand laid on her scalp stops at her
        # hairline over her brow and temples, as a stray one ran down her cheek)
        onto_face = (rise(q) < np.minimum(r0, 0.0) - 0.004) & (q[:, 1] < -0.02) & (q[:, 2] > EYE_Z - 0.13)
        go = (k <= steps) & ~held & ~onto_face
        held |= onto_face
        p = np.where(go[:, None], q, p)
        if stop is not None:
            held |= stop(p)
        paths[:, k] = p
    return paths


def resample(P, K):
    """Each strand's points spread evenly along it again, K of them (one
    that stopped short ends where it stopped)."""
    out = np.zeros((len(P), K, 3))
    for i, q in enumerate(P):
        arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
        t = np.linspace(0, max(arc[-1], 1e-9), K)
        for j in range(3):
            out[i, :, j] = np.interp(t, arc, q[:, j])
    return out


def drape(starts, dirs, length, points=24, offset=0.004, stiff_root=0.05, steps=160, gravity=1.0, extra=None, pinned=None):
    """Guide strands let fall: each from its root along its direction (or
    along `pinned`, a path laid on her scalp, as far as it goes), then under
    gravity, its links keeping their length, stiff for `stiff_root` metres
    from the root, and kept `offset` off her skin."""
    S, K = len(starts), points
    L = length / (K - 1)
    P = np.zeros((S, K, 3))
    for k in range(K):
        P[:, k] = starts + dirs * min(k * L, stiff_root) + np.array([0, 0, -1.0]) * max(0.0, k * L - stiff_root)
    npin = np.zeros(S, int)
    if pinned is not None:
        paths, npin = pinned
        for s in range(S):
            P[s, :npin[s] + 1] = paths[s, :npin[s] + 1]
            for k in range(npin[s] + 1, K):
                P[s, k] = P[s, npin[s]] + np.array([0, 0, -1.0]) * (k - npin[s]) * L
    held = np.arange(K)[None, :] <= np.maximum(npin, 0)[:, None]
    hold = P.copy()
    prev = P.copy()
    g = np.array([0, 0, -0.0018]) * gravity
    off = offset if np.ndim(offset) else np.full(S, offset)
    nroot = max(2, int(stiff_root / L) + 1)
    for step in range(steps):
        vel = (P - prev) * 0.85
        speed = np.linalg.norm(vel, axis=2)[:, :, None]
        vel *= np.minimum(1.0, 0.004 / (speed + 1e-9))      # (no more than 4 mm a step: nothing flies off)
        prev = P.copy()
        P[:, 2:] += vel[:, 2:] + g
        if extra is not None:
            extra(P, step)
        for _ in range(4):
            P[:, 0] = starts
            for k in range(1, nroot):
                P[:, k] = np.where(held[:, k][:, None], P[:, k], starts + dirs * k * L)
            P[held] = hold[held]
            # links
            for k in range(1, K - 1):
                d = P[:, k + 1] - P[:, k]
                dl = np.linalg.norm(d, axis=1)[:, None] + 1e-9
                free = ~held[:, k + 1]
                P[free, k + 1] = (P[:, k] + d / dl * L)[free]
            # bending: a strand bends gently (each point toward the middle of its neighbours)
            mid = 0.15 * ((P[:, :-2] + P[:, 2:]) / 2 - P[:, 1:-1])
            mid[held[:, 1:-1]] = 0
            mid[:, :nroot - 1] = 0
            P[:, 1:-1] += mid
            # off her skin
            flat = P[:, 2:].reshape(-1, 3)
            dist, idx = COLLIDE.query(flat, k=3)
            q = COLLIDE_P[idx].mean(1)
            n = COLLIDE_N[idx].mean(1)
            n /= np.linalg.norm(n, axis=1)[:, None] + 1e-9
            sd = ((flat - q) * n).sum(1)
            want = np.repeat(off, K - 2)
            want = np.where(NECK[idx[:, 0]], np.maximum(want, NECK_CLEAR), want)
            inside = sd < want
            flat[inside] += n[inside] * (want[inside] - sd[inside])[:, None]
            P[:, 2:] = flat.reshape(S, K - 2, 3)
    return P


# ----------------------------------------------------------------- cards --
def onto(Q, want, lying):
    """Points held `want` off her skin (a distance for each): all of those
    `lying` on her, and any nearer than that (never into her)."""
    flat = Q.reshape(-1, 3).copy()
    _, idx = COLLIDE.query(flat, k=3)
    c, n = COLLIDE_P[idx].mean(1), COLLIDE_N[idx].mean(1)
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-9
    sd = ((flat - c) * n).sum(1)
    w = np.broadcast_to(want, Q.shape[:2]).ravel()
    fix = lying.ravel() | (sd < w * 0.7)
    flat[fix] += n[fix] * (w[fix] - sd[fix])[:, None]
    return flat.reshape(Q.shape)


def cards(P, width, columns, off, root=None, narrow=0.55):
    """A card along each guide: a strip of the atlas (a column chosen from
    `columns`) as wide as `width` at its root, narrowing to its tip, facing
    out from her, three points across: where it lies on her, curved round her
    (each point as far off her as its middle); elsewhere bulging a little at
    its middle (some body). Its points' normals all face out from her (hair
    lit as one mass, not card by card). With `root`, each that much narrower
    at its root, widening to its full width a quarter of the way down."""
    S, K, _ = P.shape
    t = np.zeros_like(P)
    t[:, 1:-1] = P[:, 2:] - P[:, :-2]
    t[:, 0], t[:, -1] = P[:, 1] - P[:, 0], P[:, -1] - P[:, -2]
    t /= np.linalg.norm(t, axis=2)[:, :, None] + 1e-9
    flat = P.reshape(-1, 3)
    _, idx = COLLIDE.query(flat, k=6)
    out = COLLIDE_N[idx].mean(1).reshape(S, K, 3)
    # (her head's middle for the part over it: the nearest skin's normal is noisy there)
    radial = P - CENTRE
    radial /= np.linalg.norm(radial, axis=2)[:, :, None]
    near_head = COLLIDE_HEAD[idx].mean(1).reshape(S, K)[:, :, None]
    out = out * (1 - near_head) + radial * near_head
    for _ in range(3):                                           # smoothed along the strand: no twisting
        out[:, 1:-1] = (out[:, :-2] + 2 * out[:, 1:-1] + out[:, 2:]) / 4
    out /= np.linalg.norm(out, axis=2)[:, :, None] + 1e-9
    side = np.cross(t, out)
    side /= np.linalg.norm(side, axis=2)[:, :, None] + 1e-9
    f = np.linspace(0, 1, K)
    taper = (0.75 + 0.25 * np.sin(np.minimum(f / 0.25, 1) * np.pi / 2)) * (1 - narrow * f ** 1.5)
    w = width[:, None] * taper[None]
    if root is not None:
        w = w * (root[:, None] + (1 - root[:, None]) * np.clip(f / 0.25, 0, 1)[None])
    # (how far its middle is off her: lying on her if within a few millimetres of where it was laid)
    _, i3 = COLLIDE.query(flat, k=3)
    n3 = COLLIDE_N[i3].mean(1)
    n3 /= np.linalg.norm(n3, axis=1)[:, None] + 1e-9
    sd = ((flat - COLLIDE_P[i3].mean(1)) * n3).sum(1).reshape(S, K)
    lying = sd < off + 0.004
    held = np.maximum(sd, 0.0015)
    Lv = onto(P - side * w[:, :, None] / 2, held, lying)
    Rv = onto(P + side * w[:, :, None] / 2, held, lying)
    # (where it lies, no edge of it past her hairline: drawn in toward its middle)
    rp = rise(flat).reshape(S, K)
    for Q in (Lv, Rv):
        rq = rise(Q.reshape(-1, 3)).reshape(S, K)
        k_ = np.where(lying & (rq < 0.002) & (rp > rq), np.clip((rp - 0.002) / (rp - rq + 1e-9), 0, 1), 1.0)
        Q[:] = P + (Q - P) * k_[:, :, None]
    Mv = onto(P + out * (w * 0.08)[:, :, None], held + 0.0008, lying)
    V = np.concatenate([Lv, Mv, Rv], axis=1)                  # S x 3K x 3
    N = np.concatenate([out, out, out], axis=1)
    col = np.asarray(columns)[RNG.integers(0, len(columns), S)]
    u0, u1 = col / COLUMNS + 0.002, (col + 1) / COLUMNS - 0.002
    v = np.tile(1 - f, 3)[None].repeat(S, 0)
    u = np.concatenate([np.repeat(u0[:, None], K, 1), np.repeat(((u0 + u1) / 2)[:, None], K, 1), np.repeat(u1[:, None], K, 1)], 1)
    base = (np.arange(S) * 3 * K)[:, None]
    k = np.arange(K - 1)[None, :]
    # (wound to face out from her, as their normals do)
    q1 = np.stack([base + K + k, base + K + k + 1, base + k + 1, base + k], -1).reshape(-1, 4)
    q2 = np.stack([base + 2 * K + k, base + 2 * K + k + 1, base + K + k + 1, base + K + k], -1).reshape(-1, 4)
    return dict(V=V.reshape(-1, 3), N=N.reshape(-1, 3), UV=np.c_[u.ravel(), v.ravel()], F=np.vstack([q1, q2]),
                along=np.tile(f, 3 * S), card=np.repeat(RNG.random(S), 3 * K), at=np.concatenate([P, P, P], 1).reshape(-1, 3))


# ---------------------------------------------------------------- styles --
def part_side(pts, part_x=0.022):
    """Which side of a parting (on her left) each root is: +1 her left."""
    px = np.where(pts[:, 1] < 0.04, part_x, part_x * np.clip(1 - (pts[:, 1] - 0.04) / 0.05, 0, 1))
    return np.where(pts[:, 0] > px, 1.0, -1.0)


def combed(pts, nrm, sweep):
    """Each root's starting way: along her scalp, as `sweep` says, lifted a
    little off it (hair has some body at the root)."""
    d = sweep - nrm * (sweep * nrm).sum(1)[:, None]
    d /= np.linalg.norm(d, axis=1)[:, None] + 1e-9
    d = d * 0.85 + nrm * 0.3
    return d / np.linalg.norm(d, axis=1)[:, None]


def wave(P, amp, length, seed_pts):
    """A soft wave along each strand (after the first few centimetres),
    across it and out from her, in phase with the strands near it (clumps
    wave together)."""
    S, K, _ = P.shape
    t = np.zeros_like(P)
    t[:, 1:] = P[:, 1:] - P[:, :-1]
    t[:, 0] = t[:, 1]
    t /= np.linalg.norm(t, axis=2)[:, :, None] + 1e-9
    out = P - CENTRE
    out -= (out * t).sum(2)[:, :, None] * t
    out /= np.linalg.norm(out, axis=2)[:, :, None] + 1e-9
    side = np.cross(t, out)
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P[0], axis=0), axis=1))]
    # (each strand's phase from where its root is, so neighbours share it)
    phase = (seed_pts[:, 0] * 37 + seed_pts[:, 1] * 23 + seed_pts[:, 2] * 11) % (2 * np.pi)
    arcs = np.stack([np.r_[0, np.cumsum(np.linalg.norm(np.diff(P[s], axis=0), axis=1))] for s in range(S)])
    grow = np.clip((arcs - 0.06) / 0.08, 0, 1)
    w = amp * grow * np.sin(2 * np.pi * arcs / length + phase[:, None])
    w2 = amp * 0.5 * grow * np.cos(2 * np.pi * arcs / length + phase[:, None])
    return P + side * w[:, :, None] + out * np.abs(w2)[:, :, None]


def style_long():
    """Long, past her shoulders, parted on her left, full at the crown, most
    of it down her back and some over her shoulders in front, with a soft wave."""
    layers = []
    for spacing, width, cols, off, length in ((0.009, (0.030, 0.040), range(0, 6), 0.003, 0.50),
                                              (0.008, (0.020, 0.030), range(0, 8), 0.007, 0.52),
                                              (0.007, (0.014, 0.022), range(3, 11), 0.011, 0.54),
                                              (0.008, (0.012, 0.018), range(6, 14), 0.015, 0.54)):
        pts, nrm = roots(spacing, above=0.004)
        side = part_side(pts)
        # Away from the parting and back over her head (her forehead's hair
        # swept back, not let fall over her face), then down.
        sweep = np.c_[side * 0.8, np.full(len(pts), 0.7), np.full(len(pts), -0.2)]
        back = pts[:, 1] > 0.03
        sweep[back] = np.c_[np.zeros(back.sum()), np.ones(back.sum()) * 0.6, -np.ones(back.sum())]
        # Her face framed: the hair over her temples and the sides of her
        # forehead falling forward of her ears, down past her cheeks and in
        # front of her shoulders (kept off her face: off_face), not all swept
        # back off it (slicked to her crown, she read bald-browed).
        front = ((pts[:, 1] < 0.005) & (np.abs(pts[:, 0]) > 0.042) & (pts[:, 2] < EYE_Z + 0.075) & (pts[:, 2] > EYE_Z)
                 & (RNG.random(len(pts)) < 0.8))      # (from her temples, not by her ears: swept out from there they stood off her jaw)
        front &= off > 0.005                                     # (not her base layer's)
        sweep[front] = np.c_[np.sign(pts[front, 0]) * 0.9, -np.full(front.sum(), 0.15), -np.ones(front.sum())]
        dirs = combed(pts, nrm, sweep)
        start = pts - nrm * 0.002                  # (the root a little under her scalp: its card's end hidden)
        L = length * RNG.uniform(0.85, 1.08, len(pts))
        L[front] = RNG.uniform(0.30, 0.40, front.sum())         # (past her collarbones)
        # Laid on her head till behind her ears (her front's and top's), then
        # let fall; with some body on top, lifted off her by her parting.
        lie_for = np.clip(0.04 - pts[:, 1], 0, 0.14) + np.clip(pts[:, 2] - (EYE_Z + 0.06), 0, 0.1) * 0.6
        lie_for = np.maximum(lie_for, 0.05)
        lie_for[front] = 0.025
        body = 0.006 * np.clip((pts[:, 2] - (EYE_Z + 0.07)) / 0.04, 0, 1) * np.clip(1 - np.abs(pts[:, 0] - 0.022) / 0.06, 0, 1)
        P = drape_lengths(start, dirs, L, off, comb=comb_long, lie_for=lie_for, lift=body)
        P = wave(P, 0.007, 0.15, pts)
        # (any strand gone astray, far off her, left out)
        far = COLLIDE.query(P.reshape(-1, 3))[0].reshape(P.shape[:2]).max(1) > 0.12
        if far.any():
            print("  left out %d astray" % far.sum())
            P, pts, front = P[~far], pts[~far], front[~far]
        near = np.clip(rise(pts) / 0.03, 0.35, 1.0)              # (finer at their roots near her hairline)
        if os.environ.get("HAIR_DUMP"):
            np.savez(os.environ["HAIR_DUMP"] + "_%d.npz" % len(layers), P=P, pts=pts, front=front)
        layers.append(cards(P, RNG.uniform(*width, len(pts)), list(cols), off, root=near))
        print("  layer: %d cards" % len(pts))
    layers += hairline_hairs(comb_long)
    # Its chain: down the middle of what hangs behind her, from her nape.
    hang = np.vstack([c["at"] for c in layers])
    hang = hang[(hang[:, 1] > 0.03) & (hang[:, 2] < EYE_Z - 0.06)]
    top, bottom = EYE_Z - 0.06, np.percentile(hang[:, 2], 3)
    zs = np.linspace(top, bottom, 8)
    pts = []
    for z in zs:
        m = np.abs(hang[:, 2] - z) < 0.03
        pts.append([np.median(hang[m, 0]), np.percentile(hang[m, 1], 60), z] if m.sum() > 20 else [0.0, pts[-1][1] if pts else 0.1, z])
    global CHAIN
    CHAIN = {"points": np.array(pts), "bone": "spine_03", "stiff": 0.05,
             "weight": lambda at: np.clip((top + 0.02 - at[:, 2]) / 0.08, 0, 1) * np.clip(at[:, 1] / 0.05, 0, 1)}
    return layers


def hairline_hairs(comb, spacing=0.0026, points=8, sides=None):
    """Her hairline, soft as a real one is, not the cards' ends in a row:
    fine short hairs lying on her scalp the way it is combed, thinning out
    toward its edge; and over its edge baby hairs, finer, shorter and fainter
    (each card's alpha), a few astray. Two sets of cards."""
    out = []
    pts, nrm = roots(spacing, above=-0.001, below=0.022, soft=0.014)
    theta = np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))
    near = np.abs(np.degrees(theta)) < 125
    pts, nrm = pts[near], nrm[near]
    L = RNG.uniform(0.025, 0.06, len(pts))
    dirs = combed(pts, nrm, comb(pts))
    P = lie(pts - nrm * 0.001, dirs, comb, L / (points - 1), np.full(len(pts), points - 1), 0.0015,
            side=sides(pts) if sides else None)
    c = cards(P, RNG.uniform(0.003, 0.006, len(pts)), list(range(6, 16)), 0.0015)
    c["alpha"] = np.repeat(RNG.uniform(0.65, 1.0, len(pts)), 3 * points)
    out.append(c)
    print("  hairline: %d cards" % len(pts))
    # Baby hairs: about her hairline's edge (6 mm either side), short, fine
    # and faint, each a little off the way it is combed, some curling.
    pts, nrm = roots(0.0034, above=-0.006, below=0.006)
    n, k = len(pts), 6
    turn = RNG.normal(0, 0.45, n) + np.where(RNG.random(n) < 0.15, RNG.normal(0, 1.0, n), 0)

    def astray(p, side=None):
        w = comb(p, side)
        return w * np.cos(turn)[:, None] + np.cross(nrm, w) * np.sin(turn)[:, None]
    L = RNG.uniform(0.008, 0.022, n)
    P = lie(pts - nrm * 0.0005, combed(pts, nrm, astray(pts)), astray, L / (k - 1), np.full(n, k - 1), 0.0009,
            side=sides(pts) if sides else None, lift=RNG.uniform(0.0, 0.0025, n))
    c = cards(P, RNG.uniform(0.0018, 0.0032, n), [14, 15], 0.0009, narrow=0.7)
    c["alpha"] = np.repeat(RNG.uniform(0.3, 0.55, n), 3 * k)
    out.append(c)
    print("  baby hairs: %d cards" % n)
    return out


def rise(p):
    """How far over her hairline each point is."""
    return p[:, 2] - hairline_z(np.arctan2(p[:, 0] - CENTRE[0], -(p[:, 1] - CENTRE[1])))


def comb_long(p, side=None):
    """How her long hair is combed where it lies: away from her parting (on
    `side` of it, if given) and back round her head, down behind her ears;
    straight back off her hairline (each hair leaving it, not running along it)."""
    sd = (part_side(p) if side is None else side) * 0.7 * np.clip(rise(p) / 0.04, 0.2, 1.0)
    w = np.c_[sd, np.full(len(p), 0.8), -np.clip((0.06 - (p[:, 2] - EYE_Z)) * 12, 0.2, 1.5)]
    # (in front of her ears, below her temples, straight down: combed back
    # there, it met her ear and was turned out sideways, standing off her jaw)
    th = np.degrees(np.abs(np.arctan2(p[:, 0] - CENTRE[0], -(p[:, 1] - CENTRE[1]))))
    down = np.clip((EYE_Z + 0.015 - p[:, 2]) / 0.015, 0, 1) * np.clip(1 - np.abs(th - 80) / 25, 0, 1)
    w = w * (1 - down)[:, None] + np.array([0.0, 0.15, -1.0]) * down[:, None]
    return w / np.linalg.norm(w, axis=1)[:, None]


def off_face(P, step):
    """No hair hangs over her face: from her brows to her chin, in front of
    her ears, it is kept out past her cheeks; and below, in front of her,
    out to either side of her throat and breastbone (over her collarbones)."""
    x = P[..., 0]
    # (how far out: past her cheeks; by her neck, past it by NECK_CLEAR, none
    # of it hanging against her throat; over her collarbones, beside it)
    out = np.where(P[..., 2] > EYE_Z - 0.13, 0.078, np.where(P[..., 2] > EYE_Z - 0.17, 0.088, 0.075))
    face = (P[..., 2] < EYE_Z + 0.03) & (P[..., 2] > EYE_Z - 0.13) & (P[..., 1] < 0.0) & (np.abs(x) < out)
    chest = (P[..., 2] <= EYE_Z - 0.13) & (P[..., 2] > EYE_Z - 0.45) & (P[..., 1] < 0.02) & (np.abs(x) < out)
    m = face | chest
    P[..., 0] = np.where(m, np.where(x < 0, -1, 1) * out, x)


def drape_lengths(start, dirs, L, off, points=24, comb=None, lie_for=None, lift=0.0):
    """Strands of several lengths let fall together: their links scaled to
    each (so all have as many points); with `comb`, each first laid along her
    scalp for `lie_for` metres, rising `lift` more off her as it goes (some
    body to the hair, each strand its own)."""
    lift = np.broadcast_to(np.asarray(lift, float), (len(start),))
    S = len(start)
    out = np.zeros((S, points, 3))
    # (grouped by length, in bins, each bin draped as one)
    bins = np.digitize(L, np.quantile(L, np.linspace(0, 1, 6)[1:-1]))
    for b in np.unique(bins):
        m = bins == b
        Lm = float(L[m].mean())
        pinned = None
        if comb is not None:
            seg = Lm / (points - 1)
            steps = np.minimum((lie_for[m] / seg).astype(int), points - 4)
            # (lying flatter than it hangs: combed hair lies close on the head)
            pinned = (lie(start[m], dirs[m], comb, np.full(m.sum(), seg), steps, 0.003 + (off - 0.003) * 0.75, lift=lift[m]), steps)
        out[m] = drape(start[m], dirs[m], Lm, points=points, offset=off, pinned=pinned, extra=off_face)
    return out


# The chain a style swings on in the game (src/Actors/HairSway.cs): a line of
# points down the middle of what hangs, its bone (the one it hangs from), and
# which of the style's points move with it (a weight for each: by its parts'
# "swing", or a function of where its strand is). Set by the style.
CHAIN = None


def along_chain(at, pts):
    """Each point's place along a chain (0 its root, 1 its end): the nearest
    point of it to its own."""
    best_t, best_d = np.zeros(len(at)), np.full(len(at), np.inf)
    for i in range(len(pts) - 1):
        a, ab = pts[i], pts[i + 1] - pts[i]
        u = np.clip(((at - a) @ ab) / (ab @ ab), 0, 1)
        d = np.linalg.norm(at - (a + u[:, None] * ab), axis=1)
        m = d < best_d
        best_d[m], best_t[m] = d[m], (i + u[m]) / (len(pts) - 1)
    return best_t


def chain_spheres():
    """What the chain is kept out of: the back of her head, and her neck and
    back, a ball every 5 cm down her spine (each moving with the spine bone
    nearest it), reaching to the skin of her back there."""
    back = (np.abs(HP[:, 0]) < 0.02) & (np.abs(HP[:, 2] - CENTRE[2]) < 0.02) & (HP[:, 1] > CENTRE[1])
    out = [{"bone": "Head", "at": CENTRE, "r": float(HP[back, 1].max() - CENTRE[1]) + 0.004}]
    mw = arm.matrix_world
    bones = [(n, np.array((mw @ arm.data.bones[n].head_local)[:])) for n in ("neck_01", "spine_03", "spine_02", "spine_01")]
    top, bottom = bones[0][1][2] + 0.04, bones[-1][1][2]
    for z in np.arange(top, bottom, -0.05):
        name, c = min(bones, key=lambda nb: abs(nb[1][2] - z) if nb[1][2] <= z + 0.02 else 1e9)
        c = np.array([0.0, np.interp(z, [bb[1][2] for bb in bones][::-1], [bb[1][1] for bb in bones][::-1]), z])
        near = (np.abs(BP[:, 2] - z) < 0.025) & (np.abs(BP[:, 0]) < 0.03) & (BP[:, 1] > c[1])
        r = float(BP[near, 1].max() - c[1]) if near.any() else 0.08
        out.append({"bone": name, "at": c, "r": r + 0.008})
    return out


def no_part(p):
    """No parting: every root on the same side."""
    return np.ones(len(p))


def back_of_head(z, out=0.012):
    """The back of her head, in her middle, at height `z` (`out` off it)."""
    m = (np.abs(HP[:, 0]) < 0.012) & (np.abs(HP[:, 2] - z) < 0.008)
    return np.array([0.0, HP[m, 1].max() + out, z])


def toward(T):
    """Hair combed to a tie at T."""
    def comb(p, side=None):
        w = T - p
        w /= np.linalg.norm(w, axis=1)[:, None] + 1e-9
        # (round her ears, not over them: near one and below its top, drawn
        # up past it, as hair pulled back is)
        if EAR_TREE is not None:
            near = np.clip(1 - (EAR_TREE.query(p)[0] - 0.006) / 0.02, 0, 1) * (p[:, 2] < EYE_Z + 0.03)
            w[:, 2] += near * 1.2
            w /= np.linalg.norm(w, axis=1)[:, None] + 1e-9
        return w
    return comb


def gathered(T, layers, points=18, reach=0.012, lift=0.0):
    """Her hair drawn back along her scalp from every root to a tie at T,
    each strand laid along her head to it and ending under the tie (with
    `lift`, standing that much off her on top: some body)."""
    comb = toward(T)
    out = []
    for spacing, width, cols, off in layers:
        pts, nrm = roots(spacing, above=0.004)
        L = np.linalg.norm(T - pts, axis=1) * 1.6 + 0.02          # (more than enough: each stops at the tie)
        P = lie(pts - nrm * 0.002, combed(pts, nrm, comb(pts)), comb, L / (points - 1), np.full(len(pts), points - 1), off,
                side=no_part(pts), stop=lambda q: np.linalg.norm(q - T, axis=1) < reach,
                lift=lift * np.clip((pts[:, 2] - (EYE_Z + 0.06)) / 0.04, 0, 1))
        P = resample(P, points)
        out.append(cards(P, RNG.uniform(*width, len(pts)), list(cols), off, root=np.clip(rise(pts) / 0.03, 0.35, 1.0)))
        print("  gathered: %d cards" % len(pts))
    out += hairline_hairs(comb, sides=no_part)
    return out


def frame(P):
    """Along each strand: its way, out from her, and across."""
    t = np.gradient(P, axis=-2)
    t /= np.linalg.norm(t, axis=-1)[..., None] + 1e-9
    _, idx = COLLIDE.query(P.reshape(-1, 3), k=8)
    out = COLLIDE_N[idx].mean(1).reshape(P.shape)
    for _ in range(4):
        out[..., 1:-1, :] = (out[..., :-2, :] + 2 * out[..., 1:-1, :] + out[..., 2:, :]) / 4
    out -= t * (out * t).sum(-1)[..., None]
    out /= np.linalg.norm(out, axis=-1)[..., None] + 1e-9
    return t, out, np.cross(t, out)


def tube(path, ra, rb, up, sides=8, tile=0.025):
    """A tube along `path`, `ra` across and `rb` out (`up` the way out at
    each point; either radius a number or one a point), its UVs a tile every
    `tile` metres round and along (the scalp's strands laid along it)."""
    K = len(path)
    t = np.gradient(path, axis=0)
    t /= np.linalg.norm(t, axis=1)[:, None] + 1e-9
    up = up - t * (up * t).sum(1)[:, None]
    up /= np.linalg.norm(up, axis=1)[:, None] + 1e-9
    ac = np.cross(t, up)
    ra, rb = np.broadcast_to(ra, (K,)), np.broadcast_to(rb, (K,))
    phi = np.linspace(0, 2 * np.pi, sides + 1)
    c, s_ = np.cos(phi)[None, :, None], np.sin(phi)[None, :, None]
    V = path[:, None] + ac[:, None] * (ra[:, None, None] * c) + up[:, None] * (rb[:, None, None] * s_)
    N = ac[:, None] * (c / ra[:, None, None]) + up[:, None] * (s_ / rb[:, None, None])
    N /= np.linalg.norm(N, axis=2)[..., None]
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    round_ = np.pi * (ra + rb).mean()
    UV = np.stack(np.broadcast_arrays((phi / (2 * np.pi) * round_ / tile)[None, :], (arc / tile)[:, None]), -1)
    i = np.arange(K - 1)[:, None] * (sides + 1) + np.arange(sides)[None, :]
    F = np.stack([i, i + sides + 1, i + sides + 2, i + 1], -1).reshape(-1, 4)   # (wound to face out)
    n = K * (sides + 1)
    return dict(V=V.reshape(-1, 3), N=N.reshape(-1, 3), UV=UV.reshape(-1, 2), F=F, along=np.ones(n), card=np.full(n, RNG.random()),
                at=np.repeat(path, sides + 1, 0))


def band(T, axis, radius, wide=0.007, thick=0.0035):
    """A leather tie round her hair at T, across `axis`."""
    e1 = np.cross(axis, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    a = np.linspace(0, 2 * np.pi, 33)
    ring = T + radius * (np.cos(a)[:, None] * e1 + np.sin(a)[:, None] * e2)
    t = tube(ring, wide / 2, thick, ring - T, sides=10)
    t["mat"] = 2
    return t


def trim(q, length):
    """A strand cut `length` along it."""
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
    j = int(np.searchsorted(arc, length))
    if j >= len(q):
        return q
    end = q[j - 1] + (q[j] - q[j - 1]) * ((length - arc[j - 1]) / (arc[j] - arc[j - 1] + 1e-12))
    return np.vstack([q[:j], end])


def tail(T, axis, layers, length, spread=0.014, fan=3.0, points=24):
    """The tail from a tie at T: strands from a bundle there (a disc across
    `axis`), out along it a way, then let fall all together; as they fall
    each keeps its place in the bundle, the bundle widening to `fan` times as
    wide at the tips (hair has body: it does not fall to a string). Its
    layers (each so many strands, so wide, from such columns) after."""
    e1 = np.cross(axis, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    n = sum(ly[0] for ly in layers)
    r, a = spread * np.sqrt(RNG.random(n)), RNG.uniform(0, 2 * np.pi, n)
    disc = e1 * (r * np.cos(a))[:, None] + e2 * (r * np.sin(a))[:, None]
    disc -= disc.mean(0)
    dirs = axis + disc / spread * 0.45
    dirs /= np.linalg.norm(dirs, axis=1)[:, None]

    def extra(P, step):
        K = P.shape[1]
        for k in range(3, K):
            fall = (P[:, k] - P[:, k - 1]).mean(0)
            fall /= np.linalg.norm(fall) + 1e-9
            d = P[:, k] - P[:, k].mean(0)
            d -= np.outer(d @ fall, fall)
            want = disc * (1 + (fan - 1) * k / (K - 1))
            want -= np.outer(want @ fall, fall)
            P[:, k] += (want - d) * 0.15                       # (no drift: both have no mean)
        off_face(P, step)
    L = length * RNG.uniform(0.82, 1.05, n)
    P = drape(T + disc, dirs, L.max(), points=points, offset=0.006, extra=extra)
    middle = resample(P.mean(0)[None], 8)[0]                     # (the chain it swings on)
    P = np.array([resample(trim(P[i], L[i])[None], points)[0] for i in range(n)])
    P = wave(P, 0.004, 0.13, T + disc * 40)
    out, at = [], 0
    for k, width, cols, off in layers:
        c = cards(P[at:at + k], RNG.uniform(*width, k), list(cols), off, root=np.full(k, 0.3), narrow=0.3)
        c["swing"] = True
        out.append(c)
        at += k
    print("  tail: %d cards" % n)
    return out, middle


def style_ponytail():
    """Drawn back off her face to a tie high at the back of her head, the
    tail falling from it down between her shoulder blades."""
    T = back_of_head(EYE_Z + 0.07)
    axis = np.array([0.0, 0.55, -0.83])
    parts = gathered(T, ((0.009, (0.024, 0.032), range(0, 6), 0.003),
                         (0.008, (0.016, 0.024), range(0, 9), 0.006),
                         (0.008, (0.012, 0.018), range(3, 12), 0.009)), lift=0.003)
    hang, middle = tail(T + axis * 0.006, axis, ((120, (0.028, 0.038), range(0, 6), 0.004),
                                                 (150, (0.018, 0.028), range(0, 11), 0.008),
                                                 (90, (0.010, 0.016), range(6, 16), 0.012)), 0.46)
    parts += hang
    parts.append(band(T + axis * 0.004, axis, 0.0135))
    global CHAIN
    CHAIN = {"points": middle, "bone": "Head", "stiff": 0.01}
    return parts


def comb_pony(p, side=None):
    return toward(back_of_head(EYE_Z + 0.07))(p)


def style_braid():
    """Drawn back to a tie low at her nape, then one thick braid down her
    back: three strands crossing over and under each other, each a rope of
    hair with loose hairs over it, tied off near the end and a short tail."""
    T = back_of_head(EYE_Z - 0.035)
    parts = gathered(T, ((0.009, (0.024, 0.032), range(0, 6), 0.003),
                         (0.008, (0.016, 0.024), range(0, 9), 0.006),
                         (0.008, (0.012, 0.018), range(3, 12), 0.009)))
    on_head = len(parts)
    axis = np.array([0.0, 0.25, -0.97])
    axis /= np.linalg.norm(axis)
    C = drape(T[None] + axis * 0.01, axis[None], 0.46, points=90, offset=0.018, extra=off_face)[0]
    t, out, ac = frame(C)
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
    f = arc / arc[-1]
    taper = 1 - 0.4 * f
    end = int(np.searchsorted(f, 0.84))
    pitch = 0.062
    for k in range(3):
        th = 2 * np.pi * arc / pitch + 2 * np.pi * k / 3
        path = C + ac * (0.019 * taper * np.sin(th))[:, None] + out * (0.0075 * taper * np.sin(2 * th))[:, None]
        lobe = tube(path[:end + 2], 0.0145 * taper[:end + 2], 0.0100 * taper[:end + 2], out[:end + 2], sides=12)
        lobe["mat"] = 1
        parts.append(lobe)
        # (loose hairs over each strand of it)
        fuzz = np.stack([path[:end + 2] + out[:end + 2] * 0.008 * taper[:end + 2, None]])
        parts.append(cards(resample(fuzz, 32), np.array([0.026]), list(range(6, 11)), 0.012))
    # Tied off, and a short tail below.
    parts.append(band(C[end], t[end], 0.0135 * taper[end], wide=0.014, thick=0.004))
    n = 40
    r, a = 0.009 * np.sqrt(RNG.random(n)), RNG.uniform(0, 2 * np.pi, n)
    disc = ac[end] * (r * np.cos(a))[:, None] + out[end] * (r * np.sin(a))[:, None]
    P = drape_lengths(C[end] + disc, np.repeat(t[end][None], n, 0), np.full(n, 0.075), 0.01, points=10)
    parts.append(cards(P, RNG.uniform(0.012, 0.02, n), list(range(6, 14)), 0.01, root=np.full(n, 0.4)))
    print("  braid: %.2f m, tail %d cards" % (arc[end], n))
    for c in parts[on_head:]:                                    # (all after what is gathered to the tie)
        c["swing"] = True
    global CHAIN
    CHAIN = {"points": resample(np.vstack([C[:end + 1], P.mean(0)])[None], 8)[0], "bone": "Head", "stiff": 0.012}
    return parts


def comb_braid(p, side=None):
    return toward(back_of_head(EYE_Z - 0.035))(p)


def comb_bob(p, side=None):
    """How her bob is combed where it lies: away from her parting, then
    down round her head (little of it back)."""
    sd = (part_side(p) if side is None else side) * 0.8 * np.clip(rise(p) / 0.04, 0.2, 1.0)
    sd = sd * np.clip((0.07 - p[:, 1]) / 0.08, 0, 1)            # (parted in front only: behind, straight down)
    w = np.c_[sd, np.full(len(p), 0.35), -np.clip((0.07 - (p[:, 2] - EYE_Z)) * 12, 0.3, 1.5)]
    return w / np.linalg.norm(w, axis=1)[:, None]


def bob_line(p):
    """Where her bob is cut, by its angle round her: at her chin in front,
    a little shorter behind."""
    a = np.degrees(np.abs(np.arctan2(p[:, 0] - CENTRE[0], -(p[:, 1] - CENTRE[1]))))
    return EYE_Z + np.interp(a, [0, 60, 120, 180], [-0.125, -0.12, -0.108, -0.1])


def cut(P, line, K):
    """Each strand cut where it first falls below `line` (a height for each
    point), its points spread along what is left."""
    out = []
    for q in P:
        below = np.nonzero(q[:, 2] < line(q))[0]
        if len(below) and below[0] > 0:
            j = below[0]
            lo, hi = q[j], q[j - 1]
            zl, zh = lo[2] - line(lo[None])[0], hi[2] - line(hi[None])[0]
            end = hi + (lo - hi) * (zh / (zh - zl + 1e-9))
            q = np.vstack([q[:j], end])
        out.append(resample(q[None], K)[0])
    return np.array(out)


def style_bob():
    """A bob: parted on her left, falling round her head to a blunt line at
    her chin, a little shorter behind, its ends turned in toward her neck."""
    layers = []
    for spacing, width, cols, off in ((0.009, (0.026, 0.034), range(0, 6), 0.003),
                                      (0.008, (0.018, 0.026), range(0, 9), 0.007),
                                      (0.007, (0.012, 0.020), range(3, 12), 0.011)):
        pts, nrm = roots(spacing, above=0.004)
        lie_for = np.maximum(np.clip(pts[:, 2] - (EYE_Z + 0.04), 0, 0.1) * 0.8, 0.04)
        P = drape_lengths(pts - nrm * 0.002, combed(pts, nrm, comb_bob(pts)), np.full(len(pts), 0.34), off,
                          comb=comb_bob, lie_for=lie_for)
        P = cut(P, bob_line, 20)
        # (its ends turned in, toward her neck)
        f = np.linspace(0, 1, P.shape[1])
        inward = -np.c_[P[:, -1, 0], P[:, -1, 1] - 0.01, np.zeros(len(P))]
        inward /= np.linalg.norm(inward, axis=1)[:, None] + 1e-9
        P = P + inward[:, None] * (0.012 * np.clip((f - 0.7) / 0.3, 0, 1) ** 2)[None, :, None]
        P = wave(P, 0.003, 0.1, pts)
        layers.append(cards(P, RNG.uniform(*width, len(pts)), list(cols), off, root=np.clip(rise(pts) / 0.03, 0.35, 1.0)))
        print("  layer: %d cards" % len(pts))
    layers += hairline_hairs(comb_bob)
    return layers


def comb_pixie(p, side=None):
    """How her pixie cut is combed: on top and in front swept forward to her
    right (a fringe across her forehead); her sides and nape down and back."""
    top = np.clip((p[:, 2] - (EYE_Z + 0.06)) / 0.04, 0, 1)
    front = np.clip(-p[:, 1] / 0.05, 0, 1)
    w = np.clip(top + front * 0.6, 0, 1)[:, None]
    sweep = np.array([-0.8, -0.45, -0.25])
    down = np.array([0.0, 0.45, -1.0])
    v = sweep * w + down * (1 - w)
    return v / np.linalg.norm(v, axis=1)[:, None]


def style_pixie():
    """A pixie cut: short at her sides and nape, longer and lifted on top,
    swept forward to her right in a fringe that stops above her brows."""
    layers = []
    for spacing, width, cols, off in ((0.008, (0.014, 0.022), range(0, 6), 0.002),
                                      (0.007, (0.010, 0.016), range(3, 12), 0.004),
                                      (0.007, (0.008, 0.013), range(6, 14), 0.006)):
        pts, nrm = roots(spacing, above=0.003)
        top = np.clip((pts[:, 2] - (EYE_Z + 0.05)) / 0.05, 0, 1) + np.clip(-pts[:, 1] / 0.06, 0, 1) * 0.5
        top = np.clip(top, 0, 1)
        L = (0.028 + 0.06 * top) * RNG.uniform(0.85, 1.1, len(pts))
        points = 12
        stop = lambda q: ((q[:, 1] < -0.02) & (q[:, 2] < EYE_Z + 0.04)) | ((np.abs(q[:, 0]) > 0.06) & (q[:, 2] < EYE_Z - 0.005))
        P = lie(pts - nrm * 0.002, combed(pts, nrm, comb_pixie(pts)), comb_pixie, L / (points - 1), np.full(len(pts), points - 1),
                off, side=no_part(pts), lift=0.007 * top, stop=stop)
        P = resample(P, points)
        layers.append(cards(P, RNG.uniform(*width, len(pts)), list(cols), off, root=np.clip(rise(pts) / 0.03, 0.4, 1.0)))
        print("  layer: %d cards" % len(pts))
    layers += hairline_hairs(comb_pixie, sides=no_part)
    return layers


# Each style: its cards, how its hair is combed where it lies (for the cap),
# and which side of its parting each point is (none: all one side).
STYLES = {"long": (style_long, comb_long, part_side),
          "ponytail": (style_ponytail, comb_pony, no_part),
          "braid": (style_braid, comb_braid, no_part),
          "bob": (style_bob, comb_bob, part_side),
          "pixie": (style_pixie, comb_pixie, no_part)}


def cap(comb, sides=part_side):
    """Her scalp under the hair, a millimetre out from it: no skin shows
    between the cards, and her parting is a parting. Its UVs run along the way
    her hair is combed (the atlas's scalp strands lie that way), a tile every
    2.5 cm; faded out over its first 6 mm over her hairline, unevenly (its
    alpha): her skin under it is darkened to her hair's colour there
    (People.HerScalp), and a long fade, its alpha hashed, read as a speckled,
    pixelated edge."""
    from scipy.sparse import coo_matrix, identity
    from scipy.sparse.linalg import spsolve
    T = scalp(below=0.012)                       # (on past her hairline, unseen there: no edge to it)
    used = np.unique(T)
    idx = -np.ones(len(HP), int)
    idx[used] = np.arange(len(used))
    F = idx[T]
    V = HP[used] + HN[used] * 0.001
    N = HN[used]
    theta = np.arctan2(V[:, 0] - CENTRE[0], -(V[:, 1] - CENTRE[1]))
    # (unevenly: a millimetre or two of slow waves either way,
    # so its fade is no line round her head)
    r = np.random.default_rng(5)
    wav = sum(0.0018 * np.sin(V @ (u / np.linalg.norm(u)) * 2 * np.pi / lam + ph)
              for u, lam, ph in zip(r.normal(size=(4, 3)), (0.011, 0.017, 0.023, 0.031), r.uniform(0, 6.3, 4)))
    fade = np.clip((V[:, 2] - hairline_z(theta) - 0.002 + 0.5 * wav) / 0.006, 0, 1)
    # Along the combing (v) and across it (u), each edge as long in them as
    # along and across the combing there (least squares). Across, the same
    # way on both sides of her parting (mirrored there, not torn).
    E = np.unique(np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0)
    mid = (V[E[:, 0]] + V[E[:, 1]]) / 2
    nm = N[E[:, 0]] + N[E[:, 1]]
    nm /= np.linalg.norm(nm, axis=1)[:, None]
    fl = comb(mid)
    fl -= nm * (fl * nm).sum(1)[:, None]
    fl /= np.linalg.norm(fl, axis=1)[:, None] + 1e-9
    ac = np.cross(nm, fl) * sides(mid)[:, None]
    d = V[E[:, 1]] - V[E[:, 0]]
    m = len(E)
    A = coo_matrix((np.r_[-np.ones(m), np.ones(m)], (np.r_[np.arange(m), np.arange(m)], np.r_[E[:, 0], E[:, 1]])),
                   shape=(m, len(V))).tocsr()
    M = (A.T @ A + 1e-8 * identity(len(V))).tocsc()
    v = spsolve(M, A.T @ (d * fl).sum(1))
    u = spsolve(M, A.T @ (d * ac).sum(1))
    return dict(V=V, N=N, F=F, UV=np.c_[u - u.min(), v - v.min()] / 0.025, fade=fade)


def build(style):
    global RNG, CHAIN
    import zlib
    CHAIN = None
    RNG = np.random.default_rng(zlib.crc32(style.encode()))  # (each style the same however many are made)
    old = bpy.data.objects.get(f"hair_{style}")             # (from a run before, saved in the blend)
    if old:
        bpy.data.meshes.remove(old.data)
    shape, comb, sides = STYLES[style]
    layers = shape()
    V, N, UV, C, F, M = [], [], [], [], [], []
    base = 0
    for li, c in enumerate(layers):
        mat = c.get("mat", 0)                                # (0 cards; 1 a solid rope of hair, as the cap; 2 a tie)
        V.append(c["V"]), N.append(c["N"]), UV.append(c["UV"])
        F.extend((c["F"] + base).tolist())
        M.extend([mat] * len(c["F"]))
        # (its alpha: how much of it shows, the baby hairs at her hairline faint)
        C.append(np.c_[np.zeros(len(c["V"])), c["card"], np.full(len(c["V"]), 1.0 if mat == 1 else 0.0),
                       c.get("alpha", np.ones(len(c["V"])))])
        base += len(c["V"])
    # How deep in her hair each point is: darker the more hair lies over it
    # (out from her, within 2.5 cm), and a little at the root.
    Vh, Nh = np.vstack(V), np.vstack(N)
    hairy = np.concatenate([np.full(len(c["V"]), c.get("mat", 0) != 2) for c in layers])
    along = np.concatenate([c["along"] for c in layers])
    tree = cKDTree(Vh[hairy])
    Vin = Vh[hairy]
    over = np.zeros(len(Vh))
    for a in range(0, len(Vh), 20000):
        sl = slice(a, a + 20000)
        for i, nb in enumerate(tree.query_ball_point(Vh[sl], 0.025, workers=-1)):
            d = Vin[nb] - Vh[a + i]
            over[a + i] = ((d @ Nh[a + i]) > 0.002).sum()
    depth = np.exp(-over / np.percentile(over[hairy], 75).clip(1)) * (0.8 + 0.2 * np.clip(along / 0.1, 0, 1))
    Ch = np.vstack(C)
    rope = np.concatenate([np.full(len(c["V"]), c.get("mat", 0) == 1) for c in layers])
    Ch[:, 0] = np.where(hairy, np.where(rope, 0.6 + 0.4 * depth, 0.25 + 0.75 * depth), 1.0)   # (a braid's strands shade each other less)
    C = [Ch]
    cp = cap(comb, sides)
    V.append(cp["V"]), N.append(cp["N"]), UV.append(cp["UV"])
    F.extend((cp["F"] + base).tolist())
    M.extend([1] * len(cp["F"]))
    C.append(np.c_[np.full(len(cp["V"]), 0.4), np.full(len(cp["V"]), 0.5), np.zeros(len(cp["V"])), cp["fade"]])
    at = np.vstack([c.get("at", c["V"]) for c in layers] + [cp["V"]])
    V, N, UV, C = np.vstack(V), np.vstack(N), np.vstack(UV), np.vstack(C)
    me = bpy.data.meshes.new(f"hair_{style}")
    me.from_pydata([tuple(p) for p in V], [], F)
    loops = np.zeros(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", loops)
    uvl = me.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", UV[loops].astype(np.float32).ravel())
    col = me.color_attributes.new("ao", "FLOAT_COLOR", "POINT")
    col.data.foreach_set("color", C.astype(np.float32).ravel())
    me.color_attributes.active_color = col
    me.polygons.foreach_set("material_index", np.array(M, np.int32))
    me.shade_smooth()
    me.normals_split_custom_set_from_vertices([tuple(n) for n in N])
    o = bpy.data.objects.new(f"hair_{style}", me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(hair_material("hair", ATLAS))
    o.data.materials.append(hair_material("hair_cap", SCALP))
    o.data.materials.append(tie_material())
    follow_head(o, at)
    # Its chain: each point's place along it and how much it moves with it
    # (a second UV); and the chain, its bone and what it is kept out of, in a
    # file beside it (in the game's axes: x, up, toward her front).
    cw = np.zeros((len(V), 2))
    if CHAIN is not None:
        swing = np.concatenate([np.full(len(c["V"]), bool(c.get("swing"))) for c in layers] + [np.zeros(len(cp["V"]), bool)])
        cw[:, 0] = along_chain(at, CHAIN["points"])
        cw[:, 1] = CHAIN["weight"](at) if "weight" in CHAIN else swing
        cw[len(V) - len(cp["V"]):, 1] = 0                       # (never the cap on her scalp)
        import json
        g = lambda v: [float(v[0]), float(v[2]), float(-v[1])]
        with open(os.path.join(ART, f"heroine_hair_{style}.chain.json"), "w", encoding="utf-8") as fh:
            json.dump({"bone": CHAIN["bone"], "stiff": CHAIN["stiff"], "points": [g(q) for q in CHAIN["points"]],
                       "spheres": [{"bone": sp["bone"], "at": g(sp["at"]), "r": sp["r"]} for sp in chain_spheres()]}, fh, indent=1)
        # (what swings on a chain from her head is her head's alone: the chain moves it)
        if CHAIN["bone"] == "Head":
            at = np.where((cw[:, 1] > 0)[:, None], CENTRE, at)
    uv2 = me.uv_layers.new(name="chain")
    uv2.data.foreach_set("uv", cw[loops].astype(np.float32).ravel())
    me.uv_layers.active_index = 0
    rig(o, V, at)
    print("STYLE", style, len(V), "points,", len(F), "faces")
    return o


def follow_head(o, at):
    """Her face's sliders on her hair too (each of her head's keys that
    moves her scalp, heroine_head.py's): each point moved as the nearest of
    her head moves (its strand's point `at`, so a card moves whole), so a
    higher forehead or broader face takes her hairline and her hair with it
    (the game sets a key on every mesh that has it: People.HerFace). Hair
    hanging far from her head follows the nearest of her neck, which no key
    moves."""
    kb = head.data.shape_keys.key_blocks if head.data.shape_keys else []
    if not kb:
        return
    base = np.zeros(len(HP) * 3)
    kb[0].data.foreach_get("co", base)
    base = base.reshape(-1, 3)
    d, i = cKDTree(HP).query(at, k=6)
    w = 1.0 / (d + 1e-4)
    w /= w.sum(1, keepdims=True)
    V0 = np.zeros(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", V0)
    made = []
    for k in kb[1:]:
        if not k.name.endswith(("+", "-")) and not k.name.startswith("face_"):   # (her sliders' and faces', not her expressions')
            continue
        co = np.zeros(len(HP) * 3)
        k.data.foreach_get("co", co)
        D = co.reshape(-1, 3) - base
        Dh = (D[i] * w[:, :, None]).sum(1)
        # (moves under a tenth of a millimetre dropped: the key is written
        # sparse, only the points it moves; a key moving none by half a
        # millimetre not made at all)
        Dh[np.linalg.norm(Dh, axis=1) < 1e-4] = 0
        if np.abs(Dh).max() < 5e-4:
            continue
        if not o.data.shape_keys:
            o.shape_key_add(name="Basis", from_mix=False)
        o.shape_key_add(name=k.name, from_mix=False).data.foreach_set("co", (V0 + Dh.ravel()).astype(np.float32))
        made.append(k.name)
    print("  follows her head's keys: %s" % " ".join(made))


_bw = None


def body_weights():
    """Her body's weights, a row a point (for hair lying on her)."""
    global _bw
    if _bw is None:
        gname = {g.index: g.name for g in body.vertex_groups}
        _bw = np.zeros((len(body.data.vertices), len(BONES)))
        for v in body.data.vertices:
            for g in v.groups:
                if gname.get(g.group) in BI:
                    _bw[v.index, BI[gname[g.group]]] = g.weight
    return _bw


SPINE = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "Head"]


def spine_only(W):
    """Each bone's weight given to the nearest of its ancestors in her spine:
    hair falling down her moves with her trunk, not her arms (by them a tail
    over her shoulder blades was torn in two as her arms came down)."""
    out = np.zeros_like(W)
    for b, name in enumerate(BONES):
        a = arm.data.bones[name]
        while a is not None and a.name not in SPINE:
            a = a.parent
        out[:, BI[a.name] if a is not None else BI["pelvis"]] += W[:, b]
    return out


def rig(o, V, at=None):
    """Hair over her head moves with her head; hair lying on her body as
    her trunk under it does, eased from one to the other over 6 cm. Each
    point weighted as `at` (its strand's middle, so a card moves whole)."""
    at = V if at is None else at
    W = np.zeros((len(V), len(BONES)))
    W[:, BI["Head"]] = 1
    d, i = cKDTree(BP).query(at)
    on_body = np.clip(1 - (at[:, 2] - (EYE_Z - 0.10)) / 0.06, 0, 1)    # below her jaw, more and more her body's
    bw = spine_only(body_weights()[i])
    bw /= bw.sum(1, keepdims=True) + 1e-9
    W = W * (1 - on_body[:, None]) + bw * on_body[:, None]
    o.parent = arm
    mod = o.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    for b in np.nonzero(W.max(0) > 1e-3)[0]:
        g = o.vertex_groups.new(name=BONES[b])
        for k in np.nonzero(W[:, b] > 1e-3)[0]:
            g.add([int(k)], float(W[k, b]), "REPLACE")


def hair_material(name, image):
    """Strands (the game dyes them: heroine_hair.gdshader), their alpha
    cutting the card to them."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    t = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None) or nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(image, check_existing=True)
    t.image.reload()
    bsdf = nt.nodes["Principled BSDF"]
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], bsdf.inputs["Alpha"])
    m.surface_render_method = "DITHERED"
    return m


def tie_material():
    """Dark leather, for the ties in her hair."""
    m = bpy.data.materials.get("hair_tie") or bpy.data.materials.new("hair_tie")
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.055, 0.035, 0.024, 1)
    bsdf.inputs["Roughness"].default_value = 0.55
    return m


def export(o, style):
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(ART, f"heroine_hair_{style}.gltf")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLTF_SEPARATE", export_texture_dir="head_tex", use_selection=True,
                              export_skins=True, export_animations=False, export_yup=True, export_tangents=True,
                              export_vertex_color="ACTIVE", export_morph_normal=False, export_morph_tangent=False,
                              export_try_sparse_sk=True)
    # The data's checksum written into the .gltf: Godot reimports when the
    # .gltf changes, not its .bin (a style rebuilt with as many points would
    # otherwise keep the old one).
    import hashlib
    import json
    with open(path, encoding="utf-8") as fh:
        g = json.load(fh)
    with open(os.path.join(ART, g["buffers"][0]["uri"]), "rb") as fh:
        g["asset"]["extras"] = {"data": hashlib.md5(fh.read()).hexdigest()}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(g, fh, indent=1)
    print("WRITTEN", path)


if __name__ == "__main__":
    if not os.path.exists(ATLAS) or "atlas" in ONLY:
        draw_atlas()
    if not os.path.exists(SCALP) or "atlas" in ONLY:
        draw_scalp()
    for st in [s for s in (ONLY or STYLES) if s in STYLES]:
        export(build(st), st)
    if os.environ.get("HAIR_BLEND"):
        # (kept without their face's keys: the blend is for sizing her hats
        # over her hair, and the keys made it three times the size)
        for o in bpy.data.objects:
            if o.name.startswith("hair_") and o.data.shape_keys:
                o.shape_key_clear()
        bpy.ops.wm.save_as_mainfile(filepath=os.environ["HAIR_BLEND"])
