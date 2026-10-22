"""Her hairstyles, as hair cards: strips of drawn strands grown from her scalp
and draped by their own weight over her head, shoulders and back.

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_hair.py -- godot/art/people [atlas] [style ...]

With HAIR_BLEND=<blend> the styles are kept in a blend too (heroine_built.blend
itself, before heroine_outfits.py, sizes her hats over her long hair). With
HAIR_DUMP=<prefix>, Loose's guide strands are saved as <prefix>_<layer>.npz
(to hunt strays).

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


# (face 38: the judged lock setting, a2: lock_shade 0.5, gap 0.9, id_jit 0.05; and the judge's two fixes)
ATLAS_LOCKS = dict(lock_shade=0.3, gap=0.9, id_jit=0.05, locks=1.0, gap_floor=0.6, lock_cap=1.12)


def draw_atlas(size=(4096, 2048), over=3):
    """The strands: COLUMNS strips side by side, each a clump of strands from
    its root (the top) to its tip, drawn large and shrunk (soft edges).
    (21 October, face 38: ~900 one-pixel strands a card averaged to one flat
    painted tone at 20-40 px a card. Now drawn in locks (ATLAS_LOCKS): each
    card a few locks, each its own shade, number and wave, its strands drawn
    together to its middle, its edge strands thinner and darker (the gaps
    between locks), never darker than GAP_FLOOR (no near-black grooves), and
    no lock lighter than LOCK_CAP times the rest (one lock went pale grey).)
    Red: each strand's shade; green: a number per strand (the game varies its
    colour by it); alpha: the strands."""
    LOCK_SHADE, GAP, ID_JIT, LOCKS = ATLAS_LOCKS["lock_shade"], ATLAS_LOCKS["gap"], ATLAS_LOCKS["id_jit"], ATLAS_LOCKS["locks"]
    from PIL import Image, ImageDraw
    cw, h = size[0] // COLUMNS * over, size[1] * over
    out = np.zeros((size[1], size[0], 4), np.float32)
    for col, kind in enumerate(KINDS):
        r = np.random.default_rng(100 + col)
        n = {"dense": 900, "loose": 380, "lock": 300, "wisp": 24}[kind]
        nl = max(1, int(round({"dense": 7, "loose": 5, "lock": 3, "wisp": 1}[kind] * LOCKS)))
        spread = {"dense": 0.2, "loose": 0.25, "lock": 0.17, "wisp": 0.2}[kind]
        reach = {"dense": (0.8, 1.0), "loose": (0.6, 1.0), "lock": (0.75, 1.0), "wisp": (0.4, 1.0)}[kind]
        gather = {"dense": (0.1, 0.4), "loose": (0.0, 0.3), "lock": (0.6, 0.95), "wisp": (-0.3, 0.3)}[kind]
        # the locks: centres spread over the card (denser in the middle), widths, shade, number, wave
        cx = np.sort(np.clip(r.normal(0.5, spread * 1.1, nl), 0.08, 0.92)) if nl > 1 else np.array([0.5])
        cwid = r.uniform(0.035, 0.07, nl) * (1.6 if kind == "loose" else 1.0)
        csh = np.minimum(1.0 + LOCK_SHADE * r.uniform(-1.0, 0.6, nl), ATLAS_LOCKS["lock_cap"])
        cid = r.permutation(np.linspace(0.08, 0.92, nl)) if nl > 1 else np.array([r.uniform(0.2, 0.8)])
        cwave = [(r.uniform(0.0, 0.02) * cw, r.uniform(0.8, 2.0), r.uniform(0, 6.3)) for _ in range(nl)]
        cgather = r.uniform(*gather, nl)
        strands = []
        for i in range(n):
            k = int(r.integers(nl))
            u = r.normal(0.0, 1.0)
            while abs(u) > 2.2:
                u = r.normal(0.0, 1.0)
            x0 = cx[k] + u * cwid[k] * 0.5
            if not 0.03 < x0 < 0.97:
                x0 = r.normal(0.5, spread)
                while not 0.03 < x0 < 0.97:
                    x0 = r.normal(0.5, spread)
            edge = min(1.0, abs(u) / 2.2)                       # 0 at the lock's middle, 1 at its edge
            t0 = r.uniform(0.0, 0.015) + r.uniform(0.2, 1.0) * 0.06 * abs(2 * x0 - 1) ** 1.5
            x0 *= cw
            t1 = min(1.0, t0 + r.uniform(*reach))
            t = np.linspace(t0, t1, 140)
            f = (t - t0) / (t1 - t0)
            wa, wf, wp = cwave[k]
            own = r.uniform(0.0, 0.008) * cw * (2.5 if kind == "wisp" else 1.0)
            # (a strand gathers toward its lock's middle, and the lock toward the card's, tip-ward)
            lockx = cx[k] * cw + (cw / 2 - cx[k] * cw) * cgather[k] * f ** 2 + wa * np.sin(2 * np.pi * wf * t + wp)
            xs = lockx + (x0 - cx[k] * cw) * (1.0 - 0.5 * f ** 1.5) + own * np.sin(2 * np.pi * r.uniform(1.5, 3.5) * t + r.uniform(0, 6.3))
            if r.random() < (0.05 if kind != "wisp" else 0.5):
                xs += np.sign(x0 - cw / 2) * r.uniform(0.05, 0.2) * cw * f ** 2
            back = min(1.0, (0.5 + 0.6 * i / n) * r.uniform(0.75, 1.05))
            sh = min(1.0, max(back * csh[k] * (1.0 - GAP * 0.45 * edge ** 2), ATLAS_LOCKS["gap_floor"]))
            idv = float(np.clip(cid[k] + r.normal(0.0, ID_JIT), 0.01, 0.99))
            wd = r.uniform(0.8, 1.5) * over * (1.0 - 0.35 * GAP * edge)
            strands.append((xs, t * h, f, wd, sh, idv))
        # draw edge strands first (they lie under the lock's middle)
        shade, ident, alpha, cov = (Image.new("L", (cw, h), 0) for _ in range(4))
        ds, di, da, dc = ImageDraw.Draw(shade), ImageDraw.Draw(ident), ImageDraw.Draw(alpha), ImageDraw.Draw(cov)
        for xs, ys, f, wd, sh, idv in strands:
            for c0 in range(0, len(xs) - 1, 20):
                c1 = min(c0 + 21, len(xs))
                w = max(1, int(round(wd * (1 - 0.5 * f[c0]))))
                pts = list(zip(xs[c0:c1], ys[c0:c1]))
                ds.line(pts, fill=int(255 * sh * (0.9 + 0.1 * f[c0])), width=w, joint="curve")
                di.line(pts, fill=int(255 * idv), width=w, joint="curve")
                dc.line(pts, fill=255, width=w, joint="curve")
        tips = []
        for xs, ys, f, wd, sh, idv in strands:
            for k in np.nonzero((f > 0.9) | (f < 0.03))[0][:-1]:
                fade = (1 - f[k]) / 0.1 if f[k] > 0.9 else f[k] / 0.03
                tips.append((int(255 * fade), (xs[k], ys[k]), (xs[k + 1], ys[k + 1]), max(1, int(round(wd * (1 - 0.5 * f[k]))))))
        for a_, p0, p1, wd_ in sorted(tips, key=lambda q: q[0]):
            da.line([p0, p1], fill=a_, width=wd_)
        for xs, ys, f, wd, sh, idv in strands:
            body_ = np.nonzero((f <= 0.9) & (f >= 0.03))[0]
            for c0 in range(0, len(body_) - 1, 20):
                seg = body_[c0:c0 + 21]
                da.line(list(zip(xs[seg], ys[seg])), fill=255, width=max(1, int(round(wd * (1 - 0.5 * f[seg[0]])))), joint="curve")
        small = [np.asarray(im.resize((cw // over, h // over), Image.LANCZOS), np.float32) for im in (shade, ident, alpha, cov)]
        c = np.maximum(small[3], 1.0) / 255.0
        small[0], small[1] = (np.where(small[3] > 8, np.minimum(s / c, 255.0), s) for s in small[:2])
        x = col * (size[0] // COLUMNS)
        out[:, x:x + cw // over] = np.stack([small[0], small[1], small[0], small[2]], 2)
    Image.fromarray(np.clip(padded(out), 0, 255).astype(np.uint8)).save(ATLAS)
    print("ATLAS", ATLAS, ATLAS_LOCKS)


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
    # (each strand's own shade to its edge: see draw_atlas)
    c = np.maximum(small[2], 1.0) / 255.0
    small[0], small[1] = (np.where(small[2] > 8, np.minimum(s / c, 255.0), s) for s in small[:2])
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
# Her ears' flaps themselves (what their keys move most: over a tenth of the
# most each moves anything), for the cap, which runs on up to them. (18
# October, face 29: kept 6 mm off all her ears' keys move, as her hair's roots
# are, it left a bare ring round each ear, her scalp's pale paint showing
# behind and above it, a whitish wedge at the Look.)
# (18 October, face 30 H1b: a tenth of each key's most took in a centimetre and
# more of her scalp behind and above each ear, which her keys move too; the cap
# stopped short of it there, her scalp's grey paint the pale patch at the Look.
# Her flap alone is what they move by a quarter of their most or more: traced on
# the game's frames by her head's UV, its edge is her ear's crease. As
# heroine_features.py's scalp tint behind her ears.)
_fm = np.zeros(len(HP))
for _k in ("ears_out+", "ears_pointed+", "ears_lobes+"):
    _mv = _key_moves(_k)
    _fm = np.maximum(_fm, _mv / _mv.max()) if _mv.max() > 0 else _fm
_flap = _fm > 0.25
FLAP_TREE = cKDTree(HP[_flap]) if _flap.any() else None
print("  ears: %d points their keys move, %d their flaps" % (EAR.sum(), _flap.sum()))
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


def scalp(below=0.0, to_ears=False):
    """Her head's surface above her hairline (and `below` it), as triangles
    (not her ears; with `to_ears`, on up to their flaps, 1.5 mm off them)."""
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
    keep = (c[:, 2] > hairline_z(theta) - below) & ~ear & outside & ~core & (depth_in(c) < 0.006)
    if to_ears and FLAP_TREE is not None:
        # (round her ears her head's outline is theirs, so her scalp behind
        # them lay "inside" it: within 3 cm of a flap, her outside is enough)
        near = FLAP_TREE.query(c)[0]
        keep |= (c[:, 2] > hairline_z(theta) - below) & outside & ~core & (near < 0.03) & (near > 0.0015)
    return T[keep]


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
def lie(starts, dirs, comb, L, steps, offset, side=None, lift=0.0, stop=None, face_past=0.004):
    """Each strand laid along her scalp from its root, `offset` off it, a
    link at a time, turned more and more the way `comb` (a function of
    where it is, and which side of a parting its root is: `side`, or her
    parting's) says, for as many links as `steps` says (each its own),
    rising `lift` more off her by its tip; a strand stops where `stop`
    says (its last points then all there): combed hair lies on the head
    before it falls. With `face_past` (each its own), how far past her
    hairline over her face it may go (else 4 mm: the pixie's fringe)."""
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
        onto_face = (rise(q) < np.minimum(r0, 0.0) - face_past) & (q[:, 1] < -0.02) & (q[:, 2] > EYE_Z - 0.13)
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


def cards(P, width, columns, off, root=None, narrow=0.55, face=None, floor=0.0015, out_pts=None, u_by_width=False, edge_in=True):
    """A card along each guide: a strip of the atlas (a column chosen from
    `columns`) as wide as `width` at its root, narrowing to its tip, facing
    out from her, three points across: where it lies on her, curved round her
    (each point as far off her as its middle); elsewhere bulging a little at
    its middle (some body). Its points' normals all face out from her (hair
    lit as one mass, not card by card). With `root`, each that much narrower
    at its root, widening to its full width a quarter of the way down. With
    `out_pts` (a way per point), each point faces that way instead (a tail's
    cards round its bundle)."""
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
    if face is not None:
        # (turned toward where it is seen from: a lock hanging beside her
        # cheek faced out sideways, edge on to anyone before her, and vanished)
        out = out * 0.3 + np.asarray(face, float)[None, None] * 0.7
    if out_pts is not None:
        out = np.array(out_pts, float)
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
    held = np.maximum(sd, floor)
    Lv = onto(P - side * w[:, :, None] / 2, held, lying)
    Rv = onto(P + side * w[:, :, None] / 2, held, lying)
    # (where it lies, no edge of it past her hairline: drawn in toward its
    # middle; but not those with `edge_in` False, a fringe over her forehead)
    rp = rise(flat).reshape(S, K)
    edge_in = np.broadcast_to(np.asarray(edge_in, bool), (S,))[:, None]
    for Q in (Lv, Rv):
        rq = rise(Q.reshape(-1, 3)).reshape(S, K)
        k_ = np.where(edge_in & lying & (rq < 0.002) & (rp > rq), np.clip((rp - 0.002) / (rp - rq + 1e-9), 0, 1), 1.0)
        Q[:] = P + (Q - P) * k_[:, :, None]
    Mv = onto(P + out * (w * 0.08)[:, :, None], held + 0.0008, lying)
    V = np.concatenate([Lv, Mv, Rv], axis=1)                  # S x 3K x 3
    N = np.concatenate([out, out, out], axis=1)
    col = np.asarray(columns)[RNG.integers(0, len(columns), S)]
    u0, u1 = col / COLUMNS + 0.002, (col + 1) / COLUMNS - 0.002
    v = np.tile(1 - f, 3)[None].repeat(S, 0)
    u = np.concatenate([np.repeat(u0[:, None], K, 1), np.repeat(((u0 + u1) / 2)[:, None], K, 1), np.repeat(u1[:, None], K, 1)], 1)
    if u_by_width:
        # (round 3: a tail's cards, a third as wide under the tie, squeezed
        # their strip of the atlas into it: shrunk that much, each blurred to
        # its strip's mean shade, a flat block. Now as much of its strip as it
        # is wide, from its middle: its strands as fine all along)
        ratio = w / w.max(1, keepdims=True)
        mid, half = ((u0 + u1) / 2)[:, None], ((u1 - u0) / 2)[:, None]
        u = np.concatenate([mid - half * ratio, np.repeat(mid, K, 1), mid + half * ratio], 1)
    base = (np.arange(S) * 3 * K)[:, None]
    k = np.arange(K - 1)[None, :]
    # (wound to face out from her, as their normals do)
    q1 = np.stack([base + K + k, base + K + k + 1, base + k + 1, base + k], -1).reshape(-1, 4)
    q2 = np.stack([base + 2 * K + k, base + 2 * K + k + 1, base + K + k + 1, base + K + k], -1).reshape(-1, 4)
    # (how far along it each point is from its root, in metres, and how far
    # over her hairline its root is: for its root's fade at her hairline)
    arc = np.c_[np.zeros(S), np.cumsum(np.linalg.norm(np.diff(P, axis=1), axis=2), 1)]
    return dict(V=V.reshape(-1, 3), N=N.reshape(-1, 3), UV=np.c_[u.ravel(), v.ravel()], F=np.vstack([q1, q2]),
                along=np.tile(f, 3 * S), card=np.repeat(RNG.random(S), 3 * K), at=np.concatenate([P, P, P], 1).reshape(-1, 3),
                arc=np.concatenate([arc, arc, arc], 1).ravel(), length=np.repeat(arc[:, -1], 3 * K),
                root_rise=np.repeat(rise(P[:, 0]), 3 * K))


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
        # (which side of her parting, the parting a little uneven: a straight
        # seam of cards' roots read as a hard pale line)
        side = part_side(pts + np.c_[RNG.normal(0, 0.003, len(pts)), np.zeros((len(pts), 2))])
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
    CHAIN = {"points": np.array(pts), "bone": "spine_03", "stiff": 0.05, "bend": 0.02,
             "weight": lambda at: np.clip((top + 0.02 - at[:, 2]) / 0.08, 0, 1) * np.clip(at[:, 1] / 0.05, 0, 1)}
    return layers


def hairline_hairs(comb, spacing=0.0026, points=8, sides=None, low=None, fine=False):
    """Her hairline, soft as a real one is, not the cards' ends in a row:
    fine short hairs lying on her scalp the way it is combed, thinning out
    toward its edge; and over its edge baby hairs, finer, shorter and fainter
    (each card's alpha), a few astray. Two sets of cards, of their own
    material (hair_fine: the game blends them over her skin, as faint as they
    are; cut by hashed alpha they were a scatter of dots). With `low`, none
    at her sides (past 40 degrees from her front) rooted below that height.
    (18 October, face 30: drawn back, the fine hairs before her ears ran
    down over her cheek, and in profile read as claw scratches at the Look
    and scars at the close-up, however far off her skin: braid and ponytail
    now end them at the top of her ear.)"""
    out = []

    def high(pts):
        if low is None:
            return np.ones(len(pts), bool)
        th = np.degrees(np.abs(np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))))
        return (th < 40) | (pts[:, 2] > low)
    # (21 October, face 38, `fine` (the braid): its hairline a clean painted
    # edge at the front Look. Its fine hairs now rooted closer (1.9 mm), most
    # in its first 4 mm and fewer and fewer back to 2 cm, each a third
    # narrower: a sparse row of fine strands thinning out from the edge.)
    if fine:
        spacing = 0.0019
    pts, nrm = roots(spacing, above=-0.001, below=0.022, soft=0.014)
    if fine:
        rj = rise(pts) - hl_jit(pts)                             # (face 38 r3: from the jittered edge; none in its recesses)
        keep = (RNG.random(len(pts)) < np.interp(rj, [0.0, 0.004, 0.012, 0.022], [1.0, 0.9, 0.45, 0.2])) & (rj > -0.001)
        pts, nrm = pts[keep], nrm[keep]
    theta = np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))
    near = (np.abs(np.degrees(theta)) < 125) & high(pts)
    pts, nrm = pts[near], nrm[near]
    L = RNG.uniform(0.025, 0.06, len(pts))
    dirs = combed(pts, nrm, comb(pts))
    # (18 October, face 29's judge: lying 1.5 mm off her, lit as the hair and
    # with no shadow, the ones by her temples read as scratches on her skin, and
    # at the close-up as cuts. Now lifted (to 4 mm by their tips), a quarter
    # thinner and a fifth fainter, and none goes more than 4 mm down past her
    # hairline: in front of her ears, combed down, they ran on down her cheek.)
    P = lie(pts - nrm * 0.001, dirs, comb, L / (points - 1), np.full(len(pts), points - 1), 0.004,
            side=sides(pts) if sides else None, stop=lambda q: rise(q) < -0.004)
    P = resample(P, points)                                      # (one stopped short ends where it stopped)
    wd_ = RNG.uniform(0.003, 0.006, len(pts))
    if fine:                                                     # (face 38 r3: one stroke each, 0.4-0.6 mm, from the dense columns: ~1 px at the Look)
        c = cards(P, wd_ * 0 + np.random.default_rng(381).uniform(0.0004, 0.0006, len(pts)), [0, 1, 2], 0.004, floor=0.002)
        c["shade"] = 0.85
    else:
        c = cards(P, wd_ * 0.75, list(range(6, 16)), 0.004, floor=0.0025)
    c["alpha"] = np.repeat(RNG.uniform(0.65, 1.0, len(pts)) * 0.8, 3 * points)
    if fine:                                                     # (face 38 r2: 0.6 at her hairline to 0.15 2 cm back, by its root)
        c["alpha"] = c["alpha"] / 0.8 * np.repeat(np.interp(rise(pts) - hl_jit(pts), [0.0, 0.02], [0.6, 0.15]), 3 * points)
    c["mat"] = 3
    if os.environ.get("DBG_NOHL") != "1":                       # (test only)
        out.append(c)
    print("  hairline: %d cards" % len(pts))
    # Baby hairs: about her hairline's edge (6 mm either side), short, fine
    # and faint, each a little off the way it is combed, some curling.
    # (10 October, a judge: none showed. They were drawn from the wisp
    # columns, two dozen strands across a card, at a third to half their
    # alpha: shrunk to the Look's mip, a tenth of cover. Now from the lock
    # columns (a gathered few hairs, holding their cover as they shrink), at
    # half to four fifths, sparser over her forehead, a few more astray.)
    # (10 October, round 2's judge: they showed, but as dark grey strokes lying
    # across her forehead every way and crossing in X's. Now short (2 to 7 mm),
    # rooted in the hairline's first 3 mm and gone about 4 mm out onto her
    # skin, combed nearly as her hair is (0.2 rad, one in twelve astray and
    # never more than 0.7 rad) with a gentle curl, a lighter copper with no
    # darkening at the root or within (flat: their vertex colour's blue), and
    # fainter (0.3 to 0.55), denser at the edge.)
    pts, nrm = roots(0.0021 if fine else 0.0026, above=0.0, below=0.004 if fine else 0.003)
    th = np.degrees(np.abs(np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))))
    keep = (RNG.random(len(pts)) < np.interp(th, [0, 35, 60], [0.6, 0.85, 1.0])) & high(pts)
    keep &= rise(pts) - hl_jit(pts) > -0.002                     # (face 38 r3: fewer in the recesses)
    pts, nrm = pts[keep], nrm[keep]
    n, k = len(pts), 6
    turn = RNG.normal(0, 0.2, n) + np.where(RNG.random(n) < 0.08, np.clip(RNG.normal(0, 0.5, n), -0.7, 0.7), 0)

    def astray(p, side=None):
        w = comb(p, side)
        return w * np.cos(turn)[:, None] + np.cross(nrm, w) * np.sin(turn)[:, None]
    L = RNG.uniform(0.002, 0.007, n)
    P = lie(pts - nrm * 0.0005, combed(pts, nrm, astray(pts)), astray, L / (k - 1), np.full(n, k - 1), 0.002,
            side=sides(pts) if sides else None, lift=RNG.uniform(0.0, 0.0012, n))
    c = cards(P, RNG.uniform(0.0012, 0.0022, n), [11, 12, 13], 0.002, narrow=0.7, floor=0.002)
    c["alpha"] = np.repeat(RNG.uniform(0.3, 0.55, n), 3 * k)
    c["mat"] = 3
    c["flat"] = True
    if os.environ.get("DBG_NOBABY") != "1":                     # (test only)
        out.append(c)
    print("  baby hairs: %d cards" % n)
    return out


def rise(p):
    """How far over her hairline each point is."""
    return p[:, 2] - hairline_z(np.arctan2(p[:, 0] - CENTRE[0], -(p[:, 1] - CENTRE[1])))


# (21 October, face 38 r3, the braid only (HL_JIT, set by gathered(vol)): its
# hairline one crisp painted curve at the front Look. Its solid edge now
# pushed back and forth +-3 mm every ~10 mm along it, and recessed 6 mm at
# each temple: how far back her hair's edge is drawn there, in metres.)
HL_JIT = False
_HLK = np.random.default_rng(38).uniform(-0.003, 0.003, 80)


def hl_jit(p):
    if not HL_JIT:
        return np.zeros(len(p))
    th = np.arctan2(p[:, 0] - CENTRE[0], -(p[:, 1] - CENTRE[1]))
    s = (th + np.pi) * 0.085 / 0.010                              # (knots ~10 mm apart along her hairline)
    i = np.floor(s).astype(int) % 80
    f = s - np.floor(s)
    f = f * f * (3 - 2 * f)
    j = _HLK[i] * (1 - f) + _HLK[(i + 1) % 80] * f
    return j + 0.006 * np.exp(-((np.degrees(np.abs(th)) - 52.0) / 11.0) ** 2)


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


def drape_lengths(start, dirs, L, off, points=24, comb=None, lie_for=None, lift=0.0, extra=None):
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
        out[m] = drape(start[m], dirs[m], Lm, points=points, offset=off, pinned=pinned, extra=extra or off_face)
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


def chain_spheres(margin=0.008):
    """What the chain is kept out of: the back of her head, and her neck and
    back, a ball every 5 cm down her spine (each moving with the spine bone
    nearest it), reaching to the skin of her back there, and `margin` more (a
    number, or a function of each ball's height, centre and reach)."""
    mg = margin if callable(margin) else (lambda z, c, r: margin)
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
        out.append({"bone": name, "at": c, "r": r + float(mg(z, c, r))})
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


# (21 October, face 38: the braid read as a swim cap, "helmet hair": every
# layer flush on her skull, its outline one smooth dome. With `vol` (the braid
# only), each layer's strands are lifted off her by BRAID_VOL's crown and side
# millimetres times its layer's share (the inner layer none, the outer all),
# easing in over each strand's first 12 mm and out over the 2-7 cm before the
# tie, so the gather at the back stays put; the sides only above her ears.)
BRAID_VOL = dict(at=(0.0, 0.02, 0.05, 0.09, 0.14), lift=(0.0015, 0.003, 0.008, 0.0065, 0.004), temple=0.0025,
                 noise=0.35, wave=(0.0025, 0.03), share=(0.0, 0.55, 1.0), root=0.012, tie=(0.02, 0.05))
BRAID_EAR_CLEAR = 0.004        # (no card point nearer her ear than this, below its top: cut short there)


def lift_layer(P, T, share, vol=BRAID_VOL, waves=False, seed=0):
    """Strands P (S, K, 3) pushed out from her skull's middle: the volume.
    (face 38 r2, the judge: an even shell read as a bigger helmet. Now
    tapered: the front 2 cm at most 3 mm, peaking 8 mm about 5 cm behind her
    hairline, temples and over her ear 2.5 mm, her nape 2 mm and under (a
    braid pulls them tight); +-35% strand to strand; with `waves`, +-2.5 mm
    waves about 30 mm long along each strand.)"""
    if share <= 0:
        return P, 0.0, 0.0
    ss = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))
    rng = np.random.default_rng(3800 + seed)
    ear_top = float(HP[EAR, 2].max()) if EAR.any() else EYE_Z + 0.01
    r = P - CENTRE
    R = np.linalg.norm(r, axis=2)
    r /= R[..., None] + 1e-9
    z = P[..., 2]
    th = np.arctan2(P[..., 0] - CENTRE[0], -(P[..., 1] - CENTRE[1]))
    e = np.arcsin(np.clip((hairline_z(th.ravel()).reshape(th.shape) - CENTRE[2]) / (R + 1e-9), -1, 1))
    hf = np.stack([np.sin(th) * np.cos(e), -np.cos(th) * np.cos(e), np.sin(e)], -1)
    d = R * np.arccos(np.clip((r * hf).sum(-1), -1, 1))          # (over her scalp from her hairline, straight back)
    crown = np.interp(d, vol["at"], vol["lift"])
    low = 0.0025 * ss((z - (ear_top - 0.045)) / 0.035) * np.where(np.abs(th) > np.radians(110), 0.8, 1.0)
    top_w = ss((z - (ear_top + 0.01)) / 0.05)
    amt = low + (np.maximum(crown, low) - low) * top_w
    side_w = ss((np.abs(th) - np.radians(30)) / np.radians(30)) * (1 - ss((z - (ear_top + 0.03)) / 0.035))
    amt = amt + (np.minimum(amt, vol["temple"]) - amt) * side_w
    amt = amt * (1 + vol["noise"] * rng.uniform(-1, 1, len(P)))[:, None]
    arc = np.concatenate([np.zeros((len(P), 1)), np.cumsum(np.linalg.norm(np.diff(P, axis=1), axis=2), 1)], 1)
    if waves:
        amt = amt + vol["wave"][0] * np.sin(2 * np.pi * arc / vol["wave"][1] + rng.uniform(0, 2 * np.pi, len(P))[:, None]) * ss(amt / 0.004) * ss((d - 0.015) / 0.02) * (1 - side_w)
    amt = np.minimum(amt, np.interp(d, [0.0, 0.02, 0.03], [0.002, vol["lift"][1], 1.0]))   # (her front 2 cm held to 3 mm whatever the noise)
    fade = ss(arc / vol["root"]) * ss((np.linalg.norm(P - T, axis=2) - vol["tie"][0]) / (vol["tie"][1] - vol["tie"][0]))
    amt = share * np.clip(amt, 0, None) * fade
    if share >= 1 and os.environ.get("LIFT_REPORT", "1") == "1":
        sel = fade > 0.9
        for nm, m in (("front 2cm", d < 0.02), ("crown 4-6cm", (d > 0.04) & (d < 0.06) & (np.abs(th) < 0.5)),
                      ("temple", (side_w > 0.7)), ("nape", (z < ear_top) & (np.abs(th) > np.radians(120)))):
            m = m & sel
            if m.any():
                print("    lift %s: mean %.1f max %.1f mm" % (nm, amt[m].mean() * 1000, amt[m].max() * 1000))
    top, sid = (d > 0.04) & (d < 0.06), side_w > 0.7
    return P + r * amt[..., None], float(amt[top].mean() if top.any() else 0), float(amt[sid].mean() if sid.any() else 0)


def clear_ears(c, K, clr=BRAID_EAR_CLEAR):
    """Each card cut short (its points from there on folded onto the last
    clear one) where it comes within `clr` of her ear below the ear's top:
    hair drawn back passes behind her ear, never through its bowl or rim."""
    if FLAP_TREE is None:
        return 0
    ear_top = float(HP[EAR, 2].max()) + 0.004
    V = c["V"].reshape(-1, 3, K, 3)
    A = c["at"].reshape(-1, 3, K, 3)
    d = FLAP_TREE.query(V.reshape(-1, 3))[0].reshape(V.shape[:3])
    bad = ((d < clr) & (V[..., 2] < ear_top)).any(1)            # (S, K)
    hit = bad.any(1)
    for i in np.nonzero(hit)[0]:
        k = max(int(np.argmax(bad[i])), 1)
        V[i, :, k:] = V[i, :, k - 1:k]
        A[i, :, k:] = A[i, :, k - 1:k]
    c["V"], c["at"] = V.reshape(-1, 3), A.reshape(-1, 3)
    return int(hit.sum())


def gathered(T, layers, points=18, reach=0.012, lift=0.0, vol=False):
    """Her hair drawn back along her scalp from every root to a tie at T,
    each strand laid along her head to it and ending under the tie (with
    `lift`, standing that much off her on top: some body)."""
    global HL_JIT
    comb = toward(T)
    out = []
    HL_JIT = bool(vol)
    for spacing, width, cols, off in layers:
        pts, nrm = roots(spacing, above=0.004)
        L = np.linalg.norm(T - pts, axis=1) * 1.6 + 0.02          # (more than enough: each stops at the tie)
        P = lie(pts - nrm * 0.002, combed(pts, nrm, comb(pts)), comb, L / (points - 1), np.full(len(pts), points - 1), off,
                side=no_part(pts), stop=lambda q: np.linalg.norm(q - T, axis=1) < reach,
                lift=lift * np.clip((pts[:, 2] - (EYE_Z + 0.06)) / 0.04, 0, 1))
        # (18 October, touch-up hair round 2: a strand that never came within `reach` of the tie (held off it by her
        # head, round behind her ear) ran on its whole length past it, down her neck: the thin dark strand under her
        # ear by the fire (C01 s10, the owner's o3). Each now ends where it comes nearest the tie. GATHER_CUT=0: as before.)
        if os.environ.get("GATHER_CUT", "1") == "1":
            dT = np.linalg.norm(P - T, axis=2)
            jn = dT.argmin(1)
            miss = dT.min(1) >= reach
            for i in np.nonzero(miss)[0]:
                P[i, jn[i] + 1:] = P[i, jn[i]]
            print("  gathered: %d of %d never reached the tie, cut where nearest it" % (miss.sum(), len(P)))
        P = resample(P, points)
        if vol:
            P, mc, ms = lift_layer(P, T, BRAID_VOL["share"][min(len(out), 2)], waves=len(out) >= 2, seed=len(out))
            print("  volume: layer %d lifted %.1f mm at her crown, %.1f mm at her sides" % (len(out), mc * 1000, ms * 1000))
        if os.environ.get("DBG_NOLOWG") == "1":                 # (test only: the cards rooted beside her nape, below her ear's top, folded away under her scalp)
            lowg = (pts[:, 2] < float(HP[EAR, 2].max())) & (np.abs(pts[:, 0]) > 0.03)
            P[lowg] = (pts[lowg] - nrm[lowg] * 0.004)[:, None]
            print("  DBG_NOLOWG: %d cards hidden" % lowg.sum())
        out.append(cards(P, RNG.uniform(*width, len(pts)), list(cols), off, root=np.clip(rise(pts) / 0.03, 0.35, 1.0)))
        if vol:
            c_ = out[-1]
            S_, K3 = len(P), len(c_["V"]) // len(P)
            # (face 38 r3: rooted in the jittered edge's recesses, faded out: her hair's edge as drawn back)
            a_ = np.repeat(np.clip((rise(P[:, 0]) - hl_jit(P[:, 0])) / 0.003, 0, 1), K3)
            if len(out) == 3:                                    # (outer: 20% ragged tips, 70-100% long, an 8 mm taper)
                rg = np.random.default_rng(383)
                cut = np.repeat(np.where(rg.random(S_) < 0.2, rg.uniform(0.70, 1.0, S_), 1.0), K3)
                t_ = np.clip((c_["length"] * cut - c_["arc"]) / 0.008, 0, 1)
                a_ = a_ * np.where(cut < 1, t_ * t_ * (3 - 2 * t_), 1.0)
                print("  ragged tips: %d cards" % int((cut[::K3] < 1).sum()))
            c_["alpha"] = a_
        if vol:
            print("  ears: %d cards cut short behind her ear" % clear_ears(out[-1], points))
        print("  gathered: %d cards" % len(pts))
    out += hairline_hairs(comb, sides=no_part, low=float(HP[EAR, 2].max()) if EAR.any() else EYE_Z + 0.01, fine=vol)
    if vol:
        out += braid_flyaways(T, comb)
    # (18 October, face 30 round 3, the judge: the one lock a side lay on her
    # temple and cheek as a thin dark line, a cut or a scar; drawn back reads
    # cleaner. Made and dropped, so the RNG, and all made after, stays as was.)
    tendrils(per_side=1, lock=True)
    return out


def tendrils(per_side=9, lock=False):
    """A few fine locks left loose at her temples, falling past her cheeks
    to her jaw, softly waved: drawn back, her hair framed nothing, and she
    read slicked, bald-browed."""
    pts, nrm = roots(0.003, above=0.0, below=0.025)
    th = np.degrees(np.abs(np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))))
    ok = (th > 45) & (th < 78) & (pts[:, 2] > EYE_Z + 0.005) & (pts[:, 2] < EYE_Z + 0.05)
    pick = []
    for sd in (1, -1):
        cand = np.where(ok & (np.sign(pts[:, 0]) == sd))[0]
        if len(cand) and lock:
            # (18 October, face 30: nine fine ones a side still read as claw
            # scratches across her cheek in profile. Now one, a lock: thicker,
            # tapered to its tip, from her temple to her jaw, wide of her face)
            pick += list(cand[np.argsort(np.abs(th[cand] - 60) + np.abs(pts[cand, 2] - EYE_Z - 0.03) * 300)[:per_side]])
        elif len(cand):
            pick += list(RNG.choice(cand, min(per_side, len(cand)), replace=False))
    if not pick:
        return []
    pts, nrm = pts[pick], nrm[pick]
    sweep = np.c_[np.sign(pts[:, 0]) * 0.35, np.full(len(pts), -0.3), -np.ones(len(pts))]
    dirs = combed(pts, nrm, sweep)
    L = RNG.uniform(0.11, 0.17, len(pts)) if not lock else np.full(len(pts), 0.125)
    # (18 October, face 29's judge: hung 4 mm off her cheek, cut hard and dark,
    # they read as scratches at the Look and as cuts at the close-up. Now held
    # 1 cm off her skin and out past her cheekbones (off_face's 7.8 cm, 8.6),
    # blended as her fine hairs are (soft-edged), a little lighter and fainter.)
    def wide_of_face(P, step):
        x = P[..., 0]
        m = (P[..., 2] < EYE_Z + 0.03) & (P[..., 2] > EYE_Z - 0.13) & (P[..., 1] < 0.0) & (np.abs(x) < 0.086)
        P[..., 0] = np.where(m, np.where(x < 0, -1, 1) * 0.086, x)
    P = drape_lengths(pts - nrm * 0.001, dirs, L, 0.010, points=16, extra=wide_of_face)
    P = wave(P, 0.005, 0.07, pts)
    if lock:
        c = cards(P, np.full(len(pts), 0.016), [11, 12, 13], 0.010, narrow=0.85, face=(0.0, -1.0, 0.0), floor=0.004)
        print("  tendrils: %d locks" % len(pts))
        return [c]
    c = cards(P, RNG.uniform(0.007, 0.013, len(pts)), list(range(8, 15)), 0.010, narrow=0.65, face=(0.0, -1.0, 0.0), floor=0.004)
    c["alpha"] = np.repeat(RNG.uniform(0.75, 1.0, len(pts)) * 0.75, 3 * 16)
    c["mat"] = 3
    c["blue"] = 0.35
    print("  tendrils: %d cards" % len(pts))
    return [c]


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


def band(T, axis, radius, wide=0.007, thick=0.0035, e=None, rb=None):
    """A leather tie round her hair at T, across `axis` (with `e` and `rb`,
    an oval: `radius` along e[0], `rb` along e[1])."""
    if e is None:
        e1 = np.cross(axis, [1.0, 0.0, 0.0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(axis, e1)
    else:
        e1, e2 = (np.asarray(v, float) / np.linalg.norm(v) for v in e)
    a = np.linspace(0, 2 * np.pi, 33)
    ring = T + np.cos(a)[:, None] * e1 * radius + np.sin(a)[:, None] * e2 * (radius if rb is None else rb)
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


def tail(T, axis, layers, length, spread=0.014, fan=3.0, points=24, flat=0.6, fan_thick=1.5):
    """The tail from a tie at T: strands from a bundle there (a disc across
    `axis`), out along it a way, then let fall all together; as they fall
    each keeps its place in the bundle, the bundle widening to `fan` times as
    wide at the tips (hair has body: it does not fall to a string). Its
    layers (each so many strands, so wide, from such columns) after.
    (18 October, face 30: a round bundle fanned 3x every way stood 3-5 cm
    thick off her back, and sank into it as it swung; its cards all faced out
    from her, so from the side it read as one flat ribbon. Now the bundle is
    `flat` as deep toward her back as it is wide, fanning only `fan_thick`
    times that way, and each card faces out round the bundle, as it lies in
    it: a round, full tail, wide on her back, not thick into it.)"""
    e1 = np.cross(axis, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)                                       # (toward her: her back's way in)
    e2 = np.cross(axis, e1)                                        # (side to side)
    n = sum(ly[0] for ly in layers)
    r, a = spread * np.sqrt(RNG.random(n)), RNG.uniform(0, 2 * np.pi, n)
    thick = e1 * (flat * r * np.cos(a))[:, None]
    wide = e2 * (r * np.sin(a))[:, None]
    thick -= thick.mean(0)
    wide -= wide.mean(0)
    disc = thick + wide
    dirs = axis + disc / spread * 0.45
    dirs /= np.linalg.norm(dirs, axis=1)[:, None]

    def extra(P, step):
        K = P.shape[1]
        for k in range(3, K):
            fall = (P[:, k] - P[:, k - 1]).mean(0)
            fall /= np.linalg.norm(fall) + 1e-9
            d = P[:, k] - P[:, k].mean(0)
            d -= np.outer(d @ fall, fall)
            want = wide * (1 + (fan - 1) * k / (K - 1)) + thick * (1 + (fan_thick - 1) * k / (K - 1))
            want -= np.outer(want @ fall, fall)
            P[:, k] += (want - d) * 0.15                       # (no drift: both have no mean)
        off_face(P, step)
    L = length * RNG.uniform(0.82, 1.05, n)
    P = drape(T + disc, dirs, L.max(), points=points, offset=0.006, extra=extra)
    middle = resample(P.mean(0)[None], 8)[0]                     # (the chain it swings on)
    P = np.array([resample(trim(P[i], L[i])[None], points)[0] for i in range(n)])
    P = wave(P, 0.004, 0.13, T + disc * 40)
    # Each point's way out round the bundle: from the chain's nearest point,
    # across it (side to side over her back, and out from her), as far out in
    # the bundle as it lies (its depth over the bundle's, its width over its
    # width), a little more out from her than in.
    Cd = resample(middle[None], 64)[0]
    flat_p = P.reshape(-1, 3)
    j = cKDTree(Cd).query(flat_p)[1]
    tg = np.gradient(Cd, axis=0)[j]
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-9
    away = -e1 - tg * (tg @ -e1)[:, None]
    away /= np.linalg.norm(away, axis=1)[:, None] + 1e-9
    across = np.cross(tg, away)
    d = flat_p - Cd[j]
    f = j / (len(Cd) - 1)
    A = spread * (1 + (fan - 1) * f)
    B = spread * flat * (1 + (fan_thick - 1) * f)
    face = across * ((d * across).sum(1) / A)[:, None] + away * ((d * away).sum(1) / B + 0.25)[:, None]
    face /= np.linalg.norm(face, axis=1)[:, None] + 1e-9
    # (round 3: just under the tie, where the bundle is thinnest, its cards
    # faced every way round it, each its own shine: blocks. There they all
    # face out from her, as one, easing to round the bundle by 7 cm.)
    w_ = np.clip(1 - j / (len(Cd) - 1) / 0.15, 0, 1)[:, None]
    face = face * (1 - w_) + away * w_
    face /= np.linalg.norm(face, axis=1)[:, None] + 1e-9
    face = face.reshape(P.shape)
    out, at = [], 0
    for k, width, cols, off in layers:
        c = cards(P[at:at + k], RNG.uniform(*width, k), list(cols), off, root=np.full(k, 0.3), narrow=0.3, out_pts=face[at:at + k], u_by_width=True)
        c["swing"] = True
        out.append(c)
        at += k
    # (18 October, face 30 round 3, the judge: light and dark blocks just
    # under the tie, from her side and spinning. Each card there was faded in
    # from its root over 8 mm (and the shader's first 1.2% of it), so all of
    # it under the tie was half see-through, its cards blended in the order
    # they were made, each its own shade by how much hair lay over it. Now
    # one set, drawn from her back outward (from behind, the nearest last);
    # their roots under the tie not faded (it hides them; the shader's fade
    # skipped by starting their strands' texture past it); and one shared
    # shade over their first 5 cm, easing to their own by 9 (build()).)
    c = merge_cards(out)
    a0 = 0.015
    c["UV"][:, 1] = 1 - (a0 + (1 - c["UV"][:, 1]) * (1 - a0))
    K3 = 3 * points                                                # (each card's points; by card, nearest her back (+y) first)
    cy = c["V"].reshape(-1, K3, 3)[:, :, 1].mean(1)
    c["F"] = c["F"][np.argsort(cy[c["F"][:, 0] // K3], kind="stable")]
    c["blunt"] = True
    c["shared"] = (0.05, 0.09)
    print("  tail: %d cards" % n)
    return [c], middle


def merge_cards(cs):
    """Several sets of cards as one (their faces after each other)."""
    out, base = {}, 0
    for c in cs:
        for k, v in c.items():
            if k == "F":
                out.setdefault(k, []).append(v + base)
            elif isinstance(v, np.ndarray):
                out.setdefault(k, []).append(v)
            else:
                out[k] = v
        base += len(c["V"])
    return {k: (np.concatenate(v) if isinstance(v, list) else v) for k, v in out.items()}


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
    CHAIN = {"points": middle, "bone": "Head", "stiff": 0.006, "bend": 0.02, "margin": "bind"}
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
                         (0.008, (0.012, 0.018), range(3, 12), 0.009)), vol=os.environ.get("BRAID_VOL", "1") == "1")
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
    # (18 October, touch-up: where it left her gathered hair its three strands began 3.4 cm apart, each an open
    # tube, and past her neck from the front its start read as a flat, square-ended dark tab under her ear. Now
    # they grow out of the gathered hair: begun 1.5 cm up inside it, drawn together there and parting into the
    # plait over its first 4 cm, each strand thin where it starts and full by 2.5 cm. BRAID_GROW=0: as before.)
    grow = os.environ.get("BRAID_GROW", "1") == "1"
    if grow:
        back = T[None] + axis[None] * np.linspace(-0.005, 0.01, 6)[:-1, None]     # (up inside her gathered hair)
        Cs = np.vstack([back, C])
        arc_s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Cs, axis=0), axis=1))] - np.linalg.norm(C[0] - back[0])
        _, out_s, ac_s = frame(Cs)
        sp = np.clip(arc_s / 0.04, 0, 1)
        spread = sp * sp * (3 - 2 * sp)
        thick = 0.35 + 0.65 * np.clip((arc_s + 0.015) / 0.04, 0, 1)
        taper_s = 1 - 0.4 * np.clip(arc_s / arc[-1], 0, 1)
        nb = len(back)
    for k in range(3):
        th = 2 * np.pi * arc / pitch + 2 * np.pi * k / 3
        path = C + ac * (0.019 * taper * np.sin(th))[:, None] + out * (0.0075 * taper * np.sin(2 * th))[:, None]
        if grow:
            th_s = 2 * np.pi * arc_s / pitch + 2 * np.pi * k / 3
            path_s = Cs + ac_s * (0.019 * taper_s * spread * np.sin(th_s))[:, None] + out_s * (0.0075 * taper_s * spread * np.sin(2 * th_s))[:, None]
            lobe = tube(path_s[:nb + end + 2], (0.0145 * taper_s * thick)[:nb + end + 2], (0.0100 * taper_s * thick)[:nb + end + 2],
                        out_s[:nb + end + 2], sides=12)
        else:
            lobe = tube(path[:end + 2], 0.0145 * taper[:end + 2], 0.0100 * taper[:end + 2], out[:end + 2], sides=12)
        lobe["mat"] = 1
        parts.append(lobe)
        # (loose hairs over each strand of it)
        fuzz = np.stack([path[:end + 2] + out[:end + 2] * 0.008 * taper[:end + 2, None]])
        _fz = cards(resample(fuzz, 32), np.array([0.026]), list(range(6, 11)), 0.012)
        _fz["alpha"] = np.r_[np.full(32, 0.45), np.ones(32), np.full(32, 0.45)]       # (face 38 r3: feathered)
        if os.environ.get("DBG_NOFUZZ") != "1":
            parts.append(_fz)
    # Tied off, and a short tail below.
    # (18 October, face 30: a ring 9 mm round its middle, the band sank into
    # the braid, whose strands reach 3.4 cm across it and 1.8 out, and into
    # her: now it wraps them, as wide as they reach each way)
    parts.append(band(C[end], t[end], (0.019 + 0.0145) * taper[end] + 0.001, wide=0.014, thick=0.004,
                      e=(ac[end], out[end]), rb=(0.0075 + 0.0100) * taper[end] + 0.001))
    n = 40
    r, a = 0.009 * np.sqrt(RNG.random(n)), RNG.uniform(0, 2 * np.pi, n)
    disc = ac[end] * (r * np.cos(a))[:, None] + out[end] * (r * np.sin(a))[:, None]
    P = drape_lengths(C[end] + disc, np.repeat(t[end][None], n, 0), np.full(n, 0.075), 0.01, points=10)
    parts.append(cards(P, RNG.uniform(0.012, 0.02, n), list(range(6, 14)), 0.01, root=np.full(n, 0.4)))
    # (18 October, face 30 round 3, the judge: from behind, where it leaves her
    # nape, its outline against her skin was jagged, stair-stepped: its three
    # strands' outer turns, each a 12-sided tube. Now hair over its edges each
    # side, two cards from her nape down to its tie, a little out from it and
    # from her, reaching just past its outer turns: a smooth outline, its
    # crossings still seen between. Made after all else: the RNG and chain stay.)
    reach_ = (0.019 + 0.0145) * taper
    for sd in (1, -1):
        for inset, wd in ((0.0055, 0.013), (0.0105, 0.016)):
            q = C[:end + 1] + ac[:end + 1] * (sd * (reach_[:end + 1] - inset))[:, None] + out[:end + 1] * (0.006 * taper[:end + 1])[:, None]
            q = np.vstack([T + (q[0] - T) * (0.1 if grow else 0.4), q])   # (from up under her gathered hair)
            _cv = cards(resample(q[None], 40), np.array([wd]), list(range(0, 6)), 0.012, root=np.array([0.6]), narrow=0.35)
            _cv["alpha"] = np.r_[np.full(40, 0.45), np.ones(40), np.full(40, 0.45)]   # (face 38 r3: its edges feathered)
            if os.environ.get("DBG_NOCOVER") != "1":
                parts.append(_cv)
    print("  braid: %.2f m, tail %d cards" % (arc[end], n))
    for c in parts[on_head:]:                                    # (all after what is gathered to the tie)
        c["swing"] = True
    global CHAIN
    CHAIN = {"points": resample(np.vstack([C[:end + 1], P.mean(0)])[None], 8)[0], "bone": "Head", "stiff": 0.012, "bend": 0.03, "corner": 60, "margin": "bind"}
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
        # (18 October, face 29: at her nape each ends 3 to 8 mm past her
        # hairline, no further: 3 cm long there, their tips hung down her neck
        # in spikes, her skin pale between them)
        th_ = np.degrees(np.abs(np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))))
        nape = np.clip((th_ - 95) / 30, 0, 1) * (1 - top)
        # (face 30: 1 to 5 mm past it, the fine row under them, pixie_nape_row, thinning out past their tips)
        reach = np.maximum(rise(pts), 0) + 0.001 + 0.004 * np.random.default_rng(len(pts)).random(len(pts))
        L = L * (1 - nape) + np.minimum(L, np.maximum(reach, 0.008)) * nape
        points = 12
        # (round 3, the judge: still spikes, skin between, at 135 and 180: the
        # 8 mm least length took those rooted by her hairline 5 to 8 mm past it.
        # Now at her nape each stops 1 to 3 mm past it, however long; the nape
        # tips under them, pixie_nape_row, the edge)
        past = 0.001 + 0.002 * np.random.default_rng(len(pts) + 7).random(len(pts))
        at_nape = nape > 0.3
        # (20 October, face 32: every fringe card stopped at one height, EYE_Z
        # + 4 cm, a ruled edge straight across her forehead. Now each at its
        # own, 3 mm under to 6 mm over it, so the fringe ends raggedly)
        fz = EYE_Z + 0.04 + np.random.default_rng(len(pts) + 11).uniform(-0.003, 0.006, len(pts))
        stop = lambda q: (((q[:, 1] < -0.02) & (q[:, 2] < fz)) | ((np.abs(q[:, 0]) > 0.06) & (q[:, 2] < EYE_Z - 0.005))
                          | (at_nape & (rise(q) < -past)))
        # (face 32: over her forehead each held 4 mm past her hairline, all of
        # them: her fringe was her hairline's own even curve, a painted
        # shell's edge. Now in front (within 45 degrees) each may fall 4 to
        # 16 mm past it, its own, to its fringe line at most: a fringe)
        # (r3: so the under layer, all reaching alike, still drew one smooth
        # edge. Now the under layer stops by her hairline (0 to 4 mm past
        # it) and the two over it fall in locks, most a little way, a few far)
        fringe = th_ < 45
        u_ = np.random.default_rng(len(pts) + 13).random(len(pts))
        fpast = np.where(fringe, 0.004 * u_ if off < 0.003 else 0.004 + 0.018 * u_ ** 1.5, 0.004)
        P = lie(pts - nrm * 0.002, combed(pts, nrm, comb_pixie(pts)), comb_pixie, L / (points - 1), np.full(len(pts), points - 1),
                off, side=no_part(pts), lift=0.007 * top, stop=stop, face_past=fpast)
        P = resample(P, points)
        # (stopped in the crease over her neck, their edges sank 2-3 mm into her: held 2.8 mm off at her nape)
        # (face 32: tips narrowed to 38% of the root's width, not 45%, and faded out: build's tip_fade)
        c = cards(P, RNG.uniform(*width, len(pts)), list(cols), off, root=np.clip(rise(pts) / 0.03, 0.4, 1.0),
                  floor=np.where(at_nape, 0.0028, 0.0015)[:, None], narrow=PIXIE_NARROW, edge_in=~fringe)
        c["tip_fade"] = PIXIE_TIP
        if off >= 0.003:
            # (the over layers' fringe cards drawn from the atlas's lock
            # columns, gathered to a point at the tip: pointed locks)
            lock = np.repeat(fringe & (np.random.default_rng(len(pts) + 17).random(len(pts)) < 0.7), 3 * points)
            colk = np.repeat(np.random.default_rng(len(pts) + 19).integers(11, 14, len(pts)), 3 * points)
            third = np.tile(np.repeat([0.0, 0.5, 1.0], points), len(pts))
            c["UV"][lock, 0] = (colk[lock] + 0.002 * COLUMNS + third[lock] * (1 - 0.004 * COLUMNS)) / COLUMNS
        layers.append(c)
        print("  layer: %d cards" % len(pts))
    layers += hairline_hairs(comb_pixie, sides=no_part)
    layers += pixie_crown_fill(layers[:3]) + pixie_nape_row()
    layers += pixie_fringe_row() + pixie_flyaways()
    return layers


PIXIE_NARROW = 0.62            # (a card's tip 38% as wide as its root)
PIXIE_TIP = (0.35, 0.014)      # (faded out over its last 35%, at most 14 mm)


def pixie_fringe_row():
    """(20 October, face 32: her fringe's edge was its wide cards' ends, one
    even line.) A row of fine, fainter cards over her fringe, rooted over her
    forehead's hairline, combed as it is, each ending at its own height (2 mm
    under the fringe's line to 8 mm over it), narrow and faded to its tip: the
    fringe's edge uneven and soft, strands of it seen."""
    rng = np.random.default_rng(32)
    pts, nrm = roots(0.0055, above=0.004, below=0.03)
    th = np.degrees(np.abs(np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))))
    keep = th < 55
    pts, nrm = pts[keep], nrm[keep]
    n, points = len(pts), 10
    top = np.clip((pts[:, 2] - (EYE_Z + 0.05)) / 0.05, 0, 1) + np.clip(-pts[:, 1] / 0.06, 0, 1) * 0.5
    top = np.clip(top, 0, 1)
    L = (0.028 + 0.06 * top) * rng.uniform(0.8, 1.15, n)
    # (each its own reach past her hairline, most short, a few long: locks
    # gathered to a point (the atlas's lock columns), of her hair proper)
    fz = EYE_Z + 0.034 + rng.uniform(0, 0.012, n)
    stop = lambda q: (((q[:, 1] < -0.02) & (q[:, 2] < fz)) | ((np.abs(q[:, 0]) > 0.06) & (q[:, 2] < EYE_Z - 0.005)))
    P = lie(pts - nrm * 0.001, combed(pts, nrm, comb_pixie(pts)), comb_pixie, L / (points - 1), np.full(n, points - 1),
            0.006, side=no_part(pts), lift=0.005 * top, stop=stop, face_past=0.006 + 0.022 * rng.random(n) ** 1.5)
    P = resample(P, points)
    c = cards(P, rng.uniform(0.005, 0.009, n), [11, 12, 13], 0.006, narrow=0.65, floor=0.002, edge_in=False)
    c["alpha"] = np.repeat(rng.uniform(0.85, 1.0, n), 3 * points)
    c["tip_fade"] = (0.35, 0.010)
    print("  fringe row: %d cards" % n)
    return [c]


def pixie_flyaways():
    """(20 October, face 32: her outline, crown to temples, one smooth shell.)
    A few fine strands lifted off the mass on her crown, at her fringe and
    temples, a little astray of the comb: her silhouette broken, not frizz."""
    rng = np.random.default_rng(33)
    pts, nrm = roots(0.009, above=0.006)
    th = np.degrees(np.abs(np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))))
    crown = pts[:, 2] > EYE_Z + 0.07
    keep = (crown | (th < 95)) & (rng.random(len(pts)) < 0.6)
    pts, nrm = pts[keep], nrm[keep]
    n, points = len(pts), 10
    turn = rng.normal(0, 0.3, n)

    def astray(p, side=None):
        w = comb_pixie(p, side)
        return w * np.cos(turn)[:, None] + np.cross(nrm, w) * np.sin(turn)[:, None]
    top = np.clip((pts[:, 2] - (EYE_Z + 0.05)) / 0.05, 0, 1)
    L = (0.03 + 0.04 * top) * rng.uniform(0.8, 1.2, n)
    fz = EYE_Z + 0.045 + rng.uniform(0, 0.008, n)
    stop = lambda q: (((q[:, 1] < -0.02) & (q[:, 2] < fz)) | ((np.abs(q[:, 0]) > 0.06) & (q[:, 2] < EYE_Z + 0.005)))
    P = lie(pts - nrm * 0.001, combed(pts, nrm, astray(pts)), astray, L / (points - 1), np.full(n, points - 1),
            0.009, side=no_part(pts), lift=rng.uniform(0.01, 0.022, n), stop=stop)
    P = resample(P, points)
    c = cards(P, rng.uniform(0.0016, 0.0026, n), [11, 12, 13], 0.009, narrow=0.7, floor=0.003)
    c["alpha"] = np.repeat(rng.uniform(0.7, 0.95, n), 3 * points)
    c["mat"] = 3
    c["tip_fade"] = (0.3, 0.012)
    c["lit"] = True                                          # (r5: shaded as deep in hair, near black arcs off her crown; r6, flat as the baby hairs, pale scratches over it; now only undarkened)
    print("  flyaways: %d cards" % n)
    return [c]


def pixie_crown_fill(layers):
    """(18 October, face 30, H8: swept to her right, her pixie parted on the
    left of her crown, its cards lying away on both sides of a strip 1 to
    1.5 cm wide where only their faded roots were: her cap showed through,
    darkened as under hair, a dark hole on top of her head at the close-up.)
    Short cards lying flat the way it is combed, rooted where no card's
    opaque part (past its faded root) lies within 2 mm over her scalp."""
    rng = np.random.default_rng(30)
    opaque = []
    for c in layers:
        Ks = 12                                              # (style_pixie's points along each)
        Vq = c["V"].reshape(-1, 3 * Ks, 3).reshape(-1, 3, Ks, 3)
        aq = c["arc"].reshape(-1, 3, Ks)
        rq = np.minimum(0.008, c["length"].reshape(-1, 3, Ks)[:, :1, :1] / 3)
        # (each card filled in: 5 across, 4 to every link along)
        f = np.linspace(0, 1, 4 * (Ks - 1) + 1)
        i0 = np.minimum((f * (Ks - 1)).astype(int), Ks - 2); w = (f * (Ks - 1) - i0)[None, None, :, None]
        Va = Vq[:, :, i0] * (1 - w) + Vq[:, :, i0 + 1] * w
        Aa = aq[:, :, i0] * (1 - w[..., 0]) + aq[:, :, i0 + 1] * w[..., 0]
        Va = np.concatenate([Va, (Va[:, :1] + Va[:, 1:2]) / 2, (Va[:, 1:2] + Va[:, 2:]) / 2], 1)
        Aa = np.concatenate([Aa, Aa[:, :2]], 1)
        opaque.append(Va[Aa > rq].reshape(-1, 3))
    O = np.vstack(opaque)
    A = cKDTree(O)
    pts, nrm = roots(0.0025, above=0.02)
    top = pts[:, 2] > EYE_Z + 0.05
    # (covered: an opaque part of a card over it, within 2 mm of the line out
    # from it and up to 2 cm out: the top's cards lie lifted, well off her)
    bare = top.copy()
    for i in np.where(top)[0]:
        nb = A.query_ball_point(pts[i] + nrm[i] * 0.01, 0.0105)
        if nb:
            d = O[nb] - pts[i]
            h = d @ nrm[i]
            lat = np.linalg.norm(d - np.outer(h, nrm[i]), axis=1)
            bare[i] = not ((lat < 0.002) & (h > 0) & (h < 0.02)).any()
    if not bare.any():
        return []
    # (each rooted 4 mm back up the way it is combed from a bare point, so
    # its opaque part lies over it, and faded in over its first 2.5 mm only:
    # rooted in the strip itself and faded over 7, they left it as it was)
    b, bn = pts[bare], nrm[bare]
    back = b - combed(b, bn, comb_pixie(b)) * 0.004
    cand, cn = roots(0.0015, above=0.015)
    k = cKDTree(cand).query(back)[1]
    k = np.unique(k)
    pts, nrm = cand[k], cn[k]
    n, points = len(pts), 8
    L = rng.uniform(0.018, 0.026, n)
    P = lie(pts - nrm * 0.001, combed(pts, nrm, comb_pixie(pts)), comb_pixie, L / (points - 1), np.full(n, points - 1), 0.0025, side=no_part(pts))
    P = resample(P, points)
    c = cards(P, rng.uniform(0.012, 0.016, n), list(range(0, 6)), 0.0025)
    c["length"] = np.full(len(c["length"]), 0.0075)          # (build's root fade: a third of this)
    print("  crown fill: %d cards (%d bare points)" % (n, bare.sum()))
    return [c]


def pixie_nape_row():
    """(18 October, face 30: her pixie's nape ended in its cards' tips, spikes
    with her skin between them, at the Look from behind.) One row of short,
    narrow, dense and faint hairs (hair_fine: blended, not cut) from 6 mm
    over her nape's hairline to 2 to 6 mm under it, combed down, so it thins
    out into her skin there as a real nape does."""
    rng = np.random.default_rng(31)
    pts, nrm = roots(0.0022, above=-0.001, below=0.006)
    th = np.degrees(np.abs(np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))))
    keep = th > 112
    pts, nrm = pts[keep], nrm[keep]
    n, points = len(pts), 6
    L = np.maximum(rise(pts), 0) + rng.uniform(0.002, 0.006, n)
    P = lie(pts - nrm * 0.0008, combed(pts, nrm, comb_pixie(pts)), comb_pixie, L / (points - 1), np.full(n, points - 1), 0.0015, side=no_part(pts))
    P = resample(P, points)
    c = cards(P, rng.uniform(0.003, 0.005, n), list(range(6, 16)), 0.0015, floor=0.0015)
    c["alpha"] = np.repeat(rng.uniform(0.45, 0.7, n), 3 * points)
    c["mat"] = 3
    print("  nape row: %d cards" % n)
    # (18 October, face 30 round 3, the judge: still a jagged row of spikes,
    # skin between them, at 135 and 180 on every face; the fine row didn't
    # show. Under it now short, dense, tapered nape tips of her hair proper
    # (cut, not blended): rooted 4 to 14 mm over her nape's hairline, 3 mm
    # apart, 6 to 9 mm wide, each ending 1 to 3 mm past the hairline, so the
    # spikes' gaps fill with hair that tapers out at its edge.)
    pts, nrm = roots(0.003, above=0.004, below=0.014)
    th = np.degrees(np.abs(np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))))
    keep = th > 105
    pts, nrm = pts[keep], nrm[keep]
    m, k = len(pts), 8
    L = np.maximum(rise(pts), 0) + rng.uniform(0.001, 0.003, m)
    P = lie(pts - nrm * 0.0008, combed(pts, nrm, comb_pixie(pts)), comb_pixie, L / (k - 1), np.full(m, k - 1), 0.0035, side=no_part(pts))
    P = resample(P, k)
    t = cards(P, rng.uniform(0.006, 0.009, m), list(range(0, 8)), 0.0035, narrow=0.8, floor=0.0035)
    print("  nape tips: %d cards" % m)
    return [t, c]


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
    2.5 cm; faded out over its first centimetre over her hairline, unevenly
    (its alpha), blended over her skin in the game (heroine_hair_soft.gdshader):
    cut by hashed alpha, a fade that long read as a speckled, pixelated edge,
    and one short enough not to, as a hard one."""
    from scipy.sparse import coo_matrix, identity
    from scipy.sparse.linalg import spsolve
    T = scalp(below=0.012, to_ears=True)         # (on past her hairline, unseen there: no edge to it; and up to her ears)
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
    # (across her hairline, not by height: fs.hairline_across)
    across = fs.hairline_across(theta, V[:, 2] - hairline_z(theta), np.hypot(V[:, 0] - CENTRE[0], V[:, 1] - CENTRE[1]))
    edge = across + 0.001 + 0.5 * wav - hl_jit(V)
    fade = np.clip(edge / 0.011, 0, 1)
    # (face 38 r3, braid: a contact shade on her forehead under it, its blue
    # (the shader's `contact`): ~0.12 dark over the 5 mm under her hairline,
    # to 0.2 of her hair's tint in its last 3 mm, gone 3 mm into the fade)
    sm = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))
    contact = (0.12 * sm((edge + 0.005) / 0.002) + 0.08 * sm((edge + 0.003) / 0.003)) * (1 - sm(edge / 0.003))
    contact = np.where(HL_JIT, contact, 0.0)
    # (and at her ears, faded out over the 3 mm next to each: her hair grows
    # to her ear, its edge there soft, not the cap's cut edge)
    if FLAP_TREE is not None:
        fade = np.minimum(fade, np.clip((FLAP_TREE.query(V)[0] - 0.0015) / 0.003, 0, 1))
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
    return dict(V=V, N=N, F=F, UV=np.c_[u - u.min(), v - v.min()] / 0.025, fade=fade, contact=contact)


BRAID_FLY = 32                 # (flyaways over her crown and temples, braid)


def braid_flyaways(T, comb, n_want=BRAID_FLY):
    """(21 October, face 38: the braid's outline one smooth dome.) Fine
    strands lifted off the drawn-back mass at her crown and temples, a little
    astray of the comb toward the tie, crossing her outline: wisp and lock
    columns, lit as the hair (no depth darkening), faded at their tips."""
    rng = np.random.default_rng(38)
    pts, nrm = roots(0.008, above=0.008)
    th = np.degrees(np.abs(np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))))
    crown = pts[:, 2] > EYE_Z + 0.06
    temple = (th > 25) & (th < 80) & (pts[:, 2] > EYE_Z + 0.02)
    # (face 38 r2, the judge: ~5 hooked ones at the front of her crown, dark curls: none rooted within 3 cm of her front hairline)
    front = (th < 35) & (rise(pts) < 0.03)
    cand = np.nonzero((crown | temple) & ~front & (np.linalg.norm(pts - T, axis=1) > 0.06))[0]
    pick = rng.choice(cand, min(n_want, len(cand)), replace=False)
    pts, nrm = pts[pick], nrm[pick]
    n, points = len(pts), 10
    turn = np.clip(rng.normal(0, 0.3, n), -0.5, 0.5)          # (curl at most ~30 degrees)

    def astray(p, side=None):
        w = comb(p, side)
        return w * np.cos(turn)[:, None] + np.cross(nrm, w) * np.sin(turn)[:, None]
    L = rng.uniform(0.035, 0.07, n)
    P = lie(pts - nrm * 0.001, combed(pts, nrm, astray(pts)), astray, L / (points - 1), np.full(n, points - 1),
            0.011, side=no_part(pts), lift=rng.uniform(0.003, 0.008, n), stop=lambda q: np.linalg.norm(q - T, axis=1) < 0.04)
    P = resample(P, points)
    P, _, _ = lift_layer(P, T, 1.0, seed=9)                      # (off the outer layer, not under it)
    c = cards(P, rng.uniform(0.0016, 0.0028, n), [11, 12, 13, 14, 15], 0.011, narrow=0.6, floor=0.003)
    c["alpha"] = np.repeat(rng.uniform(0.35, 0.5, n), 3 * points)   # (face 38 r2: at most 0.5, no dark lines)
    c["mat"] = 3
    c["tip_fade"] = (0.35, 0.015)
    c["lit"] = True
    print("  flyaways: %d cards (braid), %d cut short by her ear" % (n, clear_ears(c, points)))
    return [c]


def build(style):
    global RNG, CHAIN, HL_JIT
    import zlib
    CHAIN = None
    HL_JIT = False
    RNG = np.random.default_rng(zlib.crc32(style.encode()))  # (each style the same however many are made)
    old = bpy.data.objects.get(f"hair_{style}")             # (from a run before, saved in the blend)
    if old:
        bpy.data.meshes.remove(old.data)
    shape, comb, sides = STYLES[style]
    layers = shape()
    if os.environ.get("DBG_DUMP"):                           # (test only: every layer's points, for finding a stray card)
        np.savez(os.environ["DBG_DUMP"] + f"_{style}.npz", HP=HP, EAR=EAR, EYE_Z=EYE_Z,
                 **{f"L{i}": c["V"] for i, c in enumerate(layers)},
                 **{f"K{i}": np.array([c.get("mat", 0), len(c.get("F", []))]) for i, c in enumerate(layers)})
    V, N, UV, C, F, M = [], [], [], [], [], []
    base = 0
    for li, c in enumerate(layers):
        mat = c.get("mat", 0)                                # (0 cards; 1 a solid rope of hair, as the cap; 2 a tie; 3 fine hairs)
        V.append(c["V"]), N.append(c["N"]), UV.append(c["UV"])
        F.extend((c["F"] + base).tolist())
        M.extend([mat] * len(c["F"]))
        # (its alpha: how much of it shows, the baby hairs at her hairline
        # faint; and every card faded in from its root over 8 mm, or a third
        # of it if shorter, so her hairline melts into her skin and her
        # parting into her hair, not a row of cards' ends: a wig's edge at
        # the Look's close-up)
        alpha = c.get("alpha", np.ones(len(c["V"])))
        if mat in (0, 3) and "arc" in c and not c.get("blunt"):
            ramp = np.clip(c["arc"] / np.minimum(0.008, c["length"] / 3 + 1e-6), 0, 1)
            alpha = alpha * ramp * ramp * (3 - 2 * ramp)
        if "tip_fade" in c:
            # (20 October, face 32: the pixie only. Its cards ended at full
            # cover, a hard even edge at her fringe, temples and nape, a
            # painted shell. Each now fades out over its last `tip_fade` of
            # its length (no more than `tip_max` metres), to near nothing at
            # its tip: its edges dissolve, as real cut hair's do.)
            frac, most = c["tip_fade"]
            span = np.minimum(frac * c["length"], most) + 1e-6
            tf = np.clip((c["length"] - c["arc"]) / span, 0, 1)
            alpha = alpha * (0.04 + 0.96 * tf * tf * (3 - 2 * tf))
        C.append(np.c_[np.zeros(len(c["V"])), c["card"], np.full(len(c["V"]), 1.0 if mat == 1 else 0.0), alpha])
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
    # (10 October, round 2's judge: a dark band ran just over her hairline, half her hair's light in clumps, where a
    # portrait's is lighter (skin through thinning hair). A card rooted within 10 mm of her hairline lies on her
    # skin with nothing over it: no depth, root or AO darkening there, eased back in from 6 to 10 mm.)
    rr = np.concatenate([c.get("root_rise", np.ones(len(c["V"]))) for c in layers])
    Ch[:, 0] = np.maximum(Ch[:, 0], np.where(hairy & ~rope, 1 - np.clip((rr - 0.006) / 0.004, 0, 1), 0))
    # (the baby hairs flat: no darkening at all, and the shader's lighter copper by their blue)
    flat = np.concatenate([np.full(len(c["V"]), bool(c.get("flat"))) for c in layers])
    Ch[flat, 0] = 1.0
    Ch[flat, 2] = 1.0
    lit = np.concatenate([np.full(len(c["V"]), bool(c.get("lit"))) for c in layers])
    Ch[lit, 0] = 1.0                                         # (face 32: the pixie's flyaways, off the mass: no depth darkening)
    Ch[:, 0] *= np.concatenate([np.full(len(c["V"]), float(c.get("shade", 1.0))) for c in layers])   # (face 38 r3: fine hairs 0.85x)
    # (a tail's cards under its tie: one shade, its outer hair's (the 75th
    # percentile just below), over their first `shared[0]` metres, easing to
    # their own by `shared[1]`: no light and dark blocks under the tie)
    at0 = 0
    for c in layers:
        if "shared" in c:
            a, b = c["shared"]
            sl = slice(at0, at0 + len(c["V"]))
            arc_ = c["arc"]
            below = (arc_ > b) & (arc_ < b + 0.04)
            tone = float(np.percentile(Ch[sl, 0][below], 75))
            w = np.clip((b - arc_) / (b - a), 0, 1)
            Ch[sl, 0] = Ch[sl, 0] * (1 - w) + tone * w
            print("  tail's shade under the tie: %.2f" % tone)
        at0 += len(c["V"])
    blue = np.concatenate([np.full(len(c["V"]), float(c.get("blue", 0.0))) for c in layers])
    Ch[:, 2] = np.maximum(Ch[:, 2], blue)
    C = [Ch]
    cp = cap(comb, sides)
    V.append(cp["V"]), N.append(cp["N"]), UV.append(cp["UV"])
    F.extend((cp["F"] + base).tolist())
    M.extend([1] * len(cp["F"]))
    C.append(np.c_[np.full(len(cp["V"]), 0.4), np.full(len(cp["V"]), 0.5), np.minimum(cp["contact"], 0.45), cp["fade"]])
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
    o.data.materials.append(hair_material("hair_fine", ATLAS))
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
            json.dump({"bone": CHAIN["bone"], "stiff": CHAIN["stiff"], "bend": CHAIN["bend"], **({"corner": CHAIN["corner"]} if "corner" in CHAIN else {}), "points": [g(q) for q in CHAIN["points"]],
                       "spheres": [{"bone": sp["bone"], "at": g(sp["at"]), "r": sp["r"]} for sp in chain_spheres(chain_margin(layers))]}, fh, indent=1)
        # (what swings on a chain from her head is her head's alone: the chain moves it)
        if CHAIN["bone"] == "Head":
            at = np.where((cw[:, 1] > 0)[:, None], CENTRE, at)
    uv2 = me.uv_layers.new(name="chain")
    # (its weight written as 1 - weight: the glTF export flips v, and as written the tail reached the shader as 0
    # and never swung, its cap and tie as 1; fixed in the shipped files by tools/scratch/face17/uv2flip.py)
    uv2.data.foreach_set("uv", np.c_[cw[:, 0], 1 - cw[:, 1]][loops].astype(np.float32).ravel())
    me.uv_layers.active_index = 0
    rig(o, V, at)
    print("STYLE", style, len(V), "points,", len(F), "faces")
    return o


def chain_margin(layers):
    """How far the chain is kept off her back beyond her skin: CHAIN's
    "margin" (a number), or for "bind", at each ball as far as the chain lies
    off her skin there as she stands and 4 mm more (8 mm to 4 cm): the chain
    never closer to her back than as built, so as her back comes back to it
    (her breath, the Look's stance) the hair is carried out, not sunk in.
    (18 October, face 30: kept only 8 mm off, as close as a ponytail's chain
    lies at her shoulder blades, the strands squashed under it on her back sank
    1.5 cm into her as she stood at the Look, and a braid's tie 1.4 cm.)"""
    m = CHAIN.get("margin", 0.008)
    if m != "bind":
        return m
    Cp = resample(np.asarray(CHAIN["points"])[None], 64)[0]
    order = np.argsort(Cp[:, 2])
    lo, hi = Cp[:, 2].min(), Cp[:, 2].max()

    def extra(z, c, r):
        if z < lo - 0.03 or z > hi + 0.03:
            return 0.008
        zz = float(np.clip(z, lo, hi))
        q = np.array([np.interp(zz, Cp[order, 2], Cp[order, 1]), zz])
        clear = float(np.hypot(q[0] - c[1], q[1] - c[2])) - r
        return float(np.clip(clear + 0.004, 0.008, 0.04))
    print("  chain kept off her back:", ", ".join("%.1f" % (sp["r"] * 1000) for sp in chain_spheres(extra)), "mm")
    return extra


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


_bw = {}


def mesh_weights(o):
    """A mesh's weights, a row a point."""
    if o.name not in _bw:
        gname = {g.index: g.name for g in o.vertex_groups}
        W = np.zeros((len(o.data.vertices), len(BONES)))
        for v in o.data.vertices:
            for g in v.groups:
                if gname.get(g.group) in BI:
                    W[v.index, BI[gname[g.group]]] = g.weight
        _bw[o.name] = W
    return _bw[o.name]


def body_weights():
    """Her body's weights, a row a point (for hair lying on her)."""
    return mesh_weights(body)


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
    # Hair close to her skin moves as the skin under it does: the weights of
    # the nearest point of her head or body, whichever is under it, all of it
    # within 2 cm, eased off by 5 cm (each bone's as spine_only). Over her
    # skull that is her head's alone, as above; at her nape and behind her ears
    # the head's skin is her head's to below EYE_Z - 0.10 while the rule above
    # gave hair there her body's neck from EYE_Z - 0.04 (up to 0.6 of it), and
    # hair on her body's neck Head = 1 just above the ease. (18 October: her
    # neck shortened 3 cm by her Head joint, hair there no longer moved with
    # the skin under it, by up to 16 mm, and sank 7-10 mm into her head and
    # neck.) What swings on a chain is kept at CENTRE, inside her skull, far
    # from both: unchanged.
    sd, si = cKDTree(np.vstack([HP, BP])).query(at)
    sw = spine_only(np.vstack([mesh_weights(head), body_weights()])[si])
    sw /= sw.sum(1, keepdims=True) + 1e-9
    near = np.clip(1 - (sd - 0.02) / 0.03, 0, 1)
    Wn = W * (1 - near[:, None]) + sw * near[:, None]
    W = np.where((np.abs(Wn - W).max(1) > 1e-6)[:, None], Wn, W)
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
    # Hair that took her neck's weights follows her neck's skin as her body build changed it (heroine_neck.py
    # match_graft, 18 October: her neck's skin under her head moves with her head since her neck was shortened)
    import heroine_neck
    heroine_neck.match_pieces(path, heroine_neck.field(), hair=True)
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
