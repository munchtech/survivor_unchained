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


def hairline_z(theta):
    """Height of her hairline at an angle round her head (0 her front):
    over her forehead, back at her temples, just over her ears, down to her nape."""
    a = np.degrees(np.abs((theta + np.pi) % (2 * np.pi) - np.pi))
    from scipy.interpolate import PchipInterpolator
    return EYE_Z + PchipInterpolator([0, 25, 50, 75, 100, 130, 180], [0.080, 0.076, 0.062, 0.042, 0.024, -0.026, -0.07])(a)


def scalp(below=0.0):
    """Her head's surface above her hairline (and `below` it), as triangles
    (not her ears)."""
    me = head.data
    me.calc_loop_triangles()
    T = np.array([t.vertices[:] for t in me.loop_triangles])
    c = HP[T].mean(1)
    theta = np.arctan2(c[:, 0] - CENTRE[0], -(c[:, 1] - CENTRE[1]))
    ear = (np.abs(c[:, 0]) > 0.079) & (c[:, 2] < EYE_Z + 0.05)
    # (her outside only: not the inside of her mouth and nose, deep in her head)
    n = np.cross(HP[T[:, 1]] - HP[T[:, 0]], HP[T[:, 2]] - HP[T[:, 0]])
    r = c - CENTRE
    outside = (np.linalg.norm(r, axis=1) > 0.06) & ((n * r).sum(1) > 0)
    return T[(c[:, 2] > hairline_z(theta) - below) & ~ear & outside]


def roots(spacing, above=0.0, below=None):
    """Points over her scalp about `spacing` apart (randomly, evenly), at
    least `above` over her hairline (and with `below`, no more than that)."""
    T = scalp()
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
    return pts[good], nrm[good]


# --------------------------------------------------------------- falling --
def lie(starts, dirs, comb, L, steps, offset):
    """Each strand laid along her scalp from its root, `offset` off it, a
    link at a time, turned more and more the way `comb` (a function of
    where it is) says, for as many links as `steps` says (each its own):
    combed hair lies on the head before it falls."""
    S = len(starts)
    paths = np.zeros((S, int(steps.max()) + 1, 3))
    p = starts.copy()
    d = dirs.copy()
    paths[:, 0] = p
    side = part_side(starts)                     # (each keeps to its root's side of her parting)
    for k in range(1, paths.shape[1]):
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
        q = q - n * (((q - c) * n).sum(1) - offset * np.clip(k * L / 0.04, 0.2, 1.0))[:, None]
        go = k <= steps
        p = np.where(go[:, None], q, p)
        paths[:, k] = p
    return paths


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


def cards(P, width, columns, off, root=None):
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
    taper = (0.75 + 0.25 * np.sin(np.minimum(f / 0.25, 1) * np.pi / 2)) * (1 - 0.55 * f ** 1.5)
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
                along=np.tile(f, 3 * S), card=np.repeat(RNG.random(S), 3 * K))


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
        pts, nrm = roots(spacing, above=0.01)
        side = part_side(pts)
        # Away from the parting and back over her head (her forehead's hair
        # swept back, not let fall over her face), then down.
        sweep = np.c_[side * 0.8, np.full(len(pts), 0.7), np.full(len(pts), -0.2)]
        back = pts[:, 1] > 0.03
        sweep[back] = np.c_[np.zeros(back.sum()), np.ones(back.sum()) * 0.6, -np.ones(back.sum())]
        # A few locks by her temples falling in front of her shoulders, to
        # frame her face.
        front = (pts[:, 1] < 0.0) & (np.abs(pts[:, 0]) > 0.055) & (pts[:, 2] < EYE_Z + 0.06) & (RNG.random(len(pts)) < 0.5)
        front &= off > 0.005                                     # (not her base layer's)
        sweep[front] = np.c_[np.sign(pts[front, 0]) * 0.9, -np.full(front.sum(), 0.15), -np.ones(front.sum())]
        dirs = combed(pts, nrm, sweep)
        start = pts - nrm * 0.002                  # (the root a little under her scalp: its card's end hidden)
        L = length * RNG.uniform(0.85, 1.08, len(pts))
        L[front] = RNG.uniform(0.28, 0.34, front.sum())         # (to her collarbones)
        # Laid on her head till behind her ears (her front's and top's), then let fall.
        lie_for = np.clip(0.04 - pts[:, 1], 0, 0.14) + np.clip(pts[:, 2] - (EYE_Z + 0.06), 0, 0.1) * 0.6
        lie_for = np.maximum(lie_for, 0.05)
        lie_for[front] = 0.03
        P = drape_lengths(start, dirs, L, off, comb=comb_long, lie_for=lie_for)
        P = wave(P, 0.007, 0.15, pts)
        # (any strand gone astray, far off her, left out)
        far = COLLIDE.query(P.reshape(-1, 3))[0].reshape(P.shape[:2]).max(1) > 0.12
        if far.any():
            print("  left out %d astray" % far.sum())
            P, pts, front = P[~far], pts[~far], front[~far]
        near = np.clip(rise(pts) / 0.03, 0.35, 1.0)              # (finer at their roots near her hairline)
        layers.append(cards(P, RNG.uniform(*width, len(pts)), list(cols), off, root=near))
        print("  layer: %d cards" % len(pts))
    layers.append(hairline_hairs(comb_long))
    return layers


def hairline_hairs(comb, spacing=0.0035, points=8):
    """Fine short hairs along her hairline, lying on her scalp the way it is
    combed: her hairline soft, as a real one is, not the cards' ends in a row."""
    pts, nrm = roots(spacing, above=0.002, below=0.014)
    theta = np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))
    near = np.abs(np.degrees(theta)) < 115
    pts, nrm = pts[near], nrm[near]
    L = RNG.uniform(0.02, 0.05, len(pts))
    dirs = combed(pts, nrm, comb(pts))
    seg = L / (points - 1)
    P = lie(pts - nrm * 0.001, dirs, comb, seg, np.full(len(pts), points - 1), 0.0015)
    print("  hairline: %d cards" % len(pts))
    return cards(P, RNG.uniform(0.003, 0.006, len(pts)), list(range(6, 16)), 0.0015)


def rise(p):
    """How far over her hairline each point is."""
    return p[:, 2] - hairline_z(np.arctan2(p[:, 0] - CENTRE[0], -(p[:, 1] - CENTRE[1])))


def comb_long(p, side=None):
    """How her long hair is combed where it lies: away from her parting (on
    `side` of it, if given) and back round her head, down behind her ears;
    straight back off her hairline (each hair leaving it, not running along it)."""
    sd = (part_side(p) if side is None else side) * 0.7 * np.clip(rise(p) / 0.04, 0.2, 1.0)
    w = np.c_[sd, np.full(len(p), 0.8), -np.clip((0.06 - (p[:, 2] - EYE_Z)) * 12, 0.2, 1.5)]
    return w / np.linalg.norm(w, axis=1)[:, None]


def off_face(P, step):
    """No hair hangs over her face: from her brows to her chin, in front of
    her ears, it is kept out past her cheeks; and below, in front of her,
    out to either side of her throat and breastbone (over her collarbones)."""
    x = P[..., 0]
    face = (P[..., 2] < EYE_Z + 0.03) & (P[..., 2] > EYE_Z - 0.13) & (P[..., 1] < 0.0) & (np.abs(x) < 0.078)
    chest = (P[..., 2] <= EYE_Z - 0.13) & (P[..., 2] > EYE_Z - 0.45) & (P[..., 1] < 0.02) & (np.abs(x) < 0.075)
    m = face | chest
    P[..., 0] = np.where(m, np.where(x < 0, -1, 1) * np.where(face, 0.078, 0.075), x)


def drape_lengths(start, dirs, L, off, points=24, comb=None, lie_for=None):
    """Strands of several lengths let fall together: their links scaled to
    each (so all have as many points); with `comb`, each first laid along her
    scalp for `lie_for` metres."""
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
            pinned = (lie(start[m], dirs[m], comb, np.full(m.sum(), seg), steps, 0.003 + (off - 0.003) * 0.75), steps)
        out[m] = drape(start[m], dirs[m], Lm, points=points, offset=off, pinned=pinned, extra=off_face)
    return out


# Each style: its cards, and how its hair is combed where it lies (for the cap).
STYLES = {"long": (style_long, comb_long)}


def cap(comb):
    """Her scalp under the hair, a millimetre out from it: no skin shows
    between the cards, and her parting is a parting. Its UVs run along the way
    her hair is combed (the atlas's scalp strands lie that way), a tile every
    2.5 cm; faded out over a centimetre and a half at her hairline (its alpha)."""
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
    fade = np.clip((V[:, 2] - hairline_z(theta)) / 0.016, 0, 1)
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
    ac = np.cross(nm, fl) * part_side(mid)[:, None]
    d = V[E[:, 1]] - V[E[:, 0]]
    m = len(E)
    A = coo_matrix((np.r_[-np.ones(m), np.ones(m)], (np.r_[np.arange(m), np.arange(m)], np.r_[E[:, 0], E[:, 1]])),
                   shape=(m, len(V))).tocsr()
    M = (A.T @ A + 1e-8 * identity(len(V))).tocsc()
    v = spsolve(M, A.T @ (d * fl).sum(1))
    u = spsolve(M, A.T @ (d * ac).sum(1))
    return dict(V=V, N=N, F=F, UV=np.c_[u - u.min(), v - v.min()] / 0.025, fade=fade)


def build(style):
    old = bpy.data.objects.get(f"hair_{style}")             # (from a run before, saved in the blend)
    if old:
        bpy.data.meshes.remove(old.data)
    shape, comb = STYLES[style]
    layers = shape()
    V, N, UV, C, F, M = [], [], [], [], [], []
    base = 0
    for li, c in enumerate(layers):
        V.append(c["V"]), N.append(c["N"]), UV.append(c["UV"])
        F.extend((c["F"] + base).tolist())
        M.extend([0] * len(c["F"]))
        C.append(np.c_[np.zeros(len(c["V"])), c["card"], np.full(len(c["V"]), li / 4), np.ones(len(c["V"]))])
        base += len(c["V"])
    # How deep in her hair each point is: darker the more hair lies over it
    # (out from her, within 2.5 cm), and a little at the root.
    Vh, Nh = np.vstack(V), np.vstack(N)
    along = np.concatenate([c["along"] for c in layers])
    tree = cKDTree(Vh)
    over = np.zeros(len(Vh))
    for a in range(0, len(Vh), 20000):
        sl = slice(a, a + 20000)
        for i, nb in enumerate(tree.query_ball_point(Vh[sl], 0.025, workers=-1)):
            d = Vh[nb] - Vh[a + i]
            over[a + i] = ((d @ Nh[a + i]) > 0.002).sum()
    depth = np.exp(-over / np.percentile(over, 75).clip(1)) * (0.8 + 0.2 * np.clip(along / 0.1, 0, 1))
    Ch = np.vstack(C)
    Ch[:, 0] = 0.25 + 0.75 * depth
    C = [Ch]
    cp = cap(comb)
    V.append(cp["V"]), N.append(cp["N"]), UV.append(cp["UV"])
    F.extend((cp["F"] + base).tolist())
    M.extend([1] * len(cp["F"]))
    C.append(np.c_[np.full(len(cp["V"]), 0.4), np.full(len(cp["V"]), 0.5), np.zeros(len(cp["V"])), cp["fade"]])
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
    rig(o, V)
    print("STYLE", style, len(V), "points,", len(F), "faces")
    return o


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


def rig(o, V):
    """Hair over her head moves with her head; hair lying on her body as
    her skin under it does, eased from one to the other over 6 cm."""
    W = np.zeros((len(V), len(BONES)))
    W[:, BI["Head"]] = 1
    d, i = cKDTree(BP).query(V)
    on_body = np.clip(1 - (V[:, 2] - (EYE_Z - 0.10)) / 0.06, 0, 1)    # below her jaw, more and more her body's
    bw = body_weights()[i]
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


def export(o, style):
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(ART, f"heroine_hair_{style}.gltf")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLTF_SEPARATE", export_texture_dir="head_tex", use_selection=True,
                              export_skins=True, export_animations=False, export_yup=True, export_tangents=True,
                              export_vertex_color="ACTIVE")
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
        bpy.ops.wm.save_as_mainfile(filepath=os.environ["HAIR_BLEND"])
