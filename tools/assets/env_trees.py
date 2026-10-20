"""Our own trees for the tutorial (E4, the foliage kit), made here from nothing: no kit, no scan.

    python tools/assets/env_trees.py tex [--species spruce]          the atlas: sprays + bark, painted (paint_tex)
    blender -b -P tools/assets/env_trees.py -- mesh [--species spruce]  the trees: three sizes, three LODs each

Out: godot/art/world/flora/<species>_atlas.png (one sheet, one material per species: one draw per
bucket and LOD) and <species>_<size>.gltf (+ .bin), each with three meshes lod0, lod1, lod2 at the
same origin (the foot of the trunk on the ground). Dressing.cs draws "own:<species>_<size>" pieces
(--flora-own remaps the kit's Pine_1-5 to them): lod0 near, lod1 and lod2 farther by visibility
range, lod1 alone into the shadows.

The atlas (2048 square, Blender's v up; the image's top row is v = 1):
  u 0-.75   six branch sprays, 3 columns x 2 rows of 512 x 1024; the twig's foot at the cell's
            bottom, its tip at the top. Painted clumps (one brush scale: the clump), dark toward
            the foot and the twig, lighter toward the tips; no needle-scale detail.
  u .75-1   the bark strip, 512 x 2048, seamless around (u); v runs up the trunk.
The material's name, Leaves_Own<Species>, tells KitLook it is ours (kit.gdshader's OWN_FOLIAGE:
the radial normals kept on both faces, back light through the needles, a per-tree hue jitter,
branch flutter; the bark strip, u > .75, is solid and takes none of it).

The spruce (painterly realism: forms real, a little chunkier; the crown read from 30 m above):
whorls of drooping branches with up-turned tips on a straight trunk, each branch one to three
bent spray cards, the crown a ragged narrow cone, a leader at the top. Vertex normals point out
from the trunk (and up), so the crown shades as one mass, not as cards.
"""
import math
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'godot', 'art', 'world', 'flora')
A = 2048            # atlas side
CW, CH = 512, 1024  # spray cell
BU = 0.75           # bark strip starts at this u

# sizes: authored as tall as the kit's pines (the zone's own scale, x1.13, is in the placements)
SPRUCE = {
    'a': dict(H=7.1, R=2.35, seed=11),
    'b': dict(H=8.4, R=2.75, seed=23),
    'c': dict(H=10.0, R=3.1, seed=37),
}


def arg(name, default):
    a = sys.argv
    return a[a.index(name) + 1] if name in a else default


# ---------------------------------------------------------------- texture (numpy, no Blender)

def srgb(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def spray(seed):
    """One branch spray in a CW x CH cell: rgb (sRGB 0-1), alpha, height. A spray is a clump of
    three to five spruce shoots off one twig (the twig's foot at the cell's bottom, its tip at the
    top), each shoot a bottle-brush: needles all round its twig, painted as a ragged mass, dark at
    the twig and light only toward the needle tips and the shoot's end. The side shoots leave the
    twig at uneven places and angles, never mirror-even, so the unit read at the play camera is
    the shoot clump (a third of the card across), not a comb of teeth. Drawn at twice the size and
    halved (smooth edges)."""
    import cv2
    rng = np.random.default_rng(seed)
    S = 2
    W, H = CW * S, CH * S
    col = np.zeros((H, W, 3), np.float32)
    al = np.zeros((H, W), np.float32)
    hg = np.zeros((H, W), np.float32)
    pal = [srgb(h) for h in ('#122117', '#223b28', '#345537', '#4d7244', '#76955a')]

    def shade(v):
        v = float(np.clip(v, 0, 0.999)) * (len(pal) - 1)
        i = int(v); f = v - i
        return pal[i] * (1 - f) + pal[i + 1] * f

    def path(p0, ang, length, curl, n):
        pts = [np.array(p0, np.float64)]
        for i in range(n):
            a = ang + curl * (i / n)
            pts.append(pts[-1] + np.array([math.cos(a), math.sin(a)]) * length / n)
        return np.array(pts)

    # the twig: from the foot up, gently bent; its end is the leading shoot
    foot = np.array([W / 2 + rng.uniform(-20, 20) * S, H - 8 * S])
    up = -math.pi / 2 + rng.uniform(-0.12, 0.12)
    twig = path(foot, up, H * rng.uniform(0.86, 0.92), rng.uniform(-0.35, 0.35), 40)
    # shoots: (points, radius px at its foot, its base value); the leading shoot is the twig's upper part
    lead0 = int(len(twig) * rng.uniform(0.24, 0.34))
    shoots = [(twig[lead0:], rng.uniform(140, 160) * S, 0.0)]
    n_side = int(rng.integers(2, 5))
    cuts = np.sort(rng.uniform(0.1, 0.55, n_side))
    for i in range(1, n_side):                      # (never two at one place)
        cuts[i] = max(cuts[i], cuts[i - 1] + 0.09)
    sides = rng.permutation([1, -1] * 3)[:n_side]
    if abs(sides.sum()) == n_side:                  # (both sides used)
        sides[-1] *= -1
    for c, sd in zip(cuts, sides):
        if c > 0.8:
            continue
        p = twig[int(c * (len(twig) - 1))]
        ang = up + sd * math.radians(rng.uniform(22, 70))
        ln = H * rng.uniform(0.26, 0.44) * (1.05 - 0.5 * c)
        pts = path(p, ang, ln, -sd * rng.uniform(0.05, 0.4), 18)
        # (keep it in the cell)
        pts[:, 0] = np.clip(pts[:, 0], 130 * S, W - 130 * S)
        shoots.append((pts, rng.uniform(118, 140) * S * (1.1 - 0.35 * c), 0.05 * sd))
    # the bare twig's foot (below the shoots): a few short needles, so the card's foot is not a stick
    shoots.append((twig[:lead0 + 6], 74 * S, -0.04))
    # back to front: the foot's stub, then the side shoots from the foot up, the leading shoot last
    order = [len(shoots) - 1] + sorted(range(1, len(shoots) - 1), key=lambda i: shoots[i][0][0, 1], reverse=True) + [0]

    def stroke(pa, pe, c, w, img, a, h, hv):
        pa, pe = tuple(int(x) for x in pa), tuple(int(x) for x in pe)
        cv2.line(img, pa, pe, c, w, cv2.LINE_AA); cv2.line(a, pa, pe, 255, w, cv2.LINE_AA); cv2.line(h, pa, pe, hv, w, cv2.LINE_AA)

    for si in order:
        pts, r0, vb = shoots[si]
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        L = seg.sum()
        cum = np.concatenate([[0], np.cumsum(seg)])
        # a slow wobble of the radius along the shoot: tufts, not a sausage
        ph, fq = rng.uniform(0, 6.28, 2), rng.uniform(1.4, 2.6)

        def at(d):
            i = int(np.clip(np.searchsorted(cum, d) - 1, 0, len(pts) - 2))
            f = (d - cum[i]) / max(seg[i], 1e-6)
            dv = (pts[i + 1] - pts[i]) / max(seg[i], 1e-6)
            return pts[i] + (pts[i + 1] - pts[i]) * f, dv

        def rad(s):
            taper = (1 - 0.7 * s ** 1.5) * (0.3 + 0.7 * smooth(0, 0.22, s))
            return r0 * taper * (1 + 0.16 * math.sin(fq * 6.28 * s + ph[0]) + 0.08 * math.sin(2.3 * fq * 6.28 * s + ph[1]))

        # 1. the shoot's dark core (the shadowed inside of the brush): a filled ragged mass, 60% of the radius
        lay = np.zeros((H, W), np.float32)
        for d in np.arange(0.1 * L, L, 6 * S):
            s = d / L
            p, _ = at(d)
            cv2.circle(lay, tuple(int(x) for x in p), int(rad(s) * 0.42 * rng.uniform(0.85, 1.1)), 1.0, -1, cv2.LINE_AA)
        dark = shade(0.12 + vb)
        m = lay[..., None]
        col = col * (1 - m) + dark[None, None] * m
        al = np.maximum(al, lay); hg = hg * (1 - lay) + 0.25 * lay
        # 2. the needles: all round the twig (seen from any side a brush shows needles across it,
        # pointing forward), each a short stroke, dark at its root, light at its tip
        cimg = (col * 255).astype(np.uint8); aimg = (al * 255).astype(np.uint8); himg = (hg * 255).astype(np.uint8)
        # the needles come in tufts (a few dozen sharing a lean, their ends at uneven reach), so the
        # rim is ragged clumps, not an even comb of rakes; the shoot's lit flank (its -x side) lighter
        nt = int(L / (0.075 * r0)) + 8
        for k in range(nt):
            d0 = rng.uniform(0, L)
            x0 = rng.uniform(-1, 1)
            lean = rng.normal(0, 0.35)
            reach = rng.uniform(0.75, 1.2)
            for q in range(int(rng.integers(26, 44))):
                d = float(np.clip(d0 + rng.normal(0, 0.09 * r0), 0, L))
                s = d / L
                p, dv = at(d)
                nv = np.array([-dv[1], dv[0]])
                x = float(np.clip(x0 + rng.normal(0, 0.3), -1, 1))
                R = rad(s) * reach
                ang = lean + rng.normal(0, 0.18)
                lat = x * R * rng.uniform(0.55, 1.05)
                fwd = R * rng.uniform(0.2, 0.75) * (1 - 0.45 * abs(x))
                ca, sa = math.cos(ang), math.sin(ang)
                off = dv * (fwd * ca - lat * sa * 0.3) + nv * (lat * ca + fwd * sa * 0.5)
                e = p + off
                mid = p + (e - p) * 0.45
                tip = 0.5 * s ** 1.2 + 0.2 * smooth(0.55, 1.0, s)  # (light only toward the shoot's end)
                jit = rng.normal(0, 0.04)
                flank = 0.12 * (-x)                                # (the lit flank)
                c1 = (shade(0.16 + vb + 0.25 * tip + 0.5 * flank + jit) * 255).astype(int).tolist()
                c2 = (shade(0.25 + vb + 0.6 * tip + flank + 0.12 * abs(x) ** 2 + jit) * 255).astype(int).tolist()
                w = int(max(2, 3.0 * S * rng.uniform(0.8, 1.2)))
                stroke(p + (e - p) * 0.1, mid, c1, w, cimg, aimg, himg, int(120 + 60 * tip))
                stroke(mid, e, c2, w, cimg, aimg, himg, int(160 + 80 * tip))
        col = cimg.astype(np.float32) / 255; al = aimg.astype(np.float32) / 255; hg = himg.astype(np.float32) / 255
    col = cv2.resize(col, (CW, CH), interpolation=cv2.INTER_AREA)
    al = cv2.resize(al, (CW, CH), interpolation=cv2.INTER_AREA)
    hg = cv2.resize(hg, (CW, CH), interpolation=cv2.INTER_AREA)
    col = np.clip(col / np.maximum(al, 1e-3)[..., None], 0, 1) * (al > 0)[..., None]
    ys = np.mgrid[0:CH, 0:CW][0].astype(np.float32)
    col *= (0.78 + 0.22 * smooth(0, 0.6, 1 - ys / CH))[..., None]
    return col, al, cv2.GaussianBlur(hg, (5, 5), 1.5)


def bark(seed, W=512, H=2048):
    """The spruce's bark strip: thin rounded scales, grey-brown, seamless round the trunk (u)."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    cx, cy = 20, 46
    gx, gy = np.meshgrid(np.arange(0, W, cx), np.arange(0, H + cy, cy))
    pts = np.stack([gx.ravel() + rng.uniform(0, cx, gx.size), gy.ravel() + rng.uniform(0, cy, gy.size)], 1)
    allp = np.concatenate([pts, pts + [W, 0], pts - [W, 0]])
    ids = np.concatenate([np.arange(len(pts))] * 3)
    tree = cKDTree(allp * [1, 0.5])
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    q = np.stack([xs.ravel(), ys.ravel() * 0.5], 1)
    d, i = tree.query(q, k=2)
    edge = (d[:, 1] - d[:, 0]).reshape(H, W)
    cell = ids[i[:, 0]].reshape(H, W)
    rnd = rng.random(len(pts)).astype(np.float32)[cell]
    lowf = np.zeros((H, W), np.float32)
    for s, w in ((64, 0.6), (24, 0.4)):
        n = rng.random((H // s + 2, W // s + 1)).astype(np.float32)
        n = np.concatenate([n, n[:, :1]], 1)
        import cv2
        lowf += w * cv2.resize(n, (W + s, H + 2 * s), interpolation=cv2.INTER_CUBIC)[:H, :W]
    hgt = smooth(0, 5, edge) * (0.6 + 0.4 * rnd) + 0.3 * lowf
    brown, grey, crev, lich = srgb('#44382f'), srgb('#5d564f'), srgb('#2b231e'), srgb('#6f7565')
    base = brown[None, None] + (grey - brown)[None, None] * (0.35 * rnd + 0.4 * lowf)[..., None]
    col = crev[None, None] + (base - crev[None, None]) * (0.5 + 0.5 * np.maximum(smooth(0, 4, edge), smooth(0.45, 0.7, lowf)))[..., None]
    lm = smooth(0.7, 0.82, lowf) * smooth(2, 6, edge)
    col = col + (lich - col) * (0.55 * lm)[..., None]
    return col, hgt


def normals(h, k):
    gy, gx = np.gradient(h * k)
    n = np.dstack([-gx, gy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def bleed(col, al):
    """Fill the cut-out's empty texels with the colour nearby (no dark fringe in the mips)."""
    import cv2
    out = col.copy()
    m = (al > 0.02).astype(np.float32)
    acc, w = col * m[..., None], m.copy()
    for s in (2, 6, 16, 48):
        k = int(s * 3) | 1
        ca = cv2.GaussianBlur(acc, (k, k), s)
        wa = cv2.GaussianBlur(w, (k, k), s)
        fill = ca / np.maximum(wa, 1e-5)[..., None]
        hole = (m < 0.5) & (wa > 1e-4)
        out[hole] = fill[hole]
        m = np.maximum(m, hole.astype(np.float32))
        acc, w = out * m[..., None], m.copy()
    return out


def tex(species):
    sys.path.insert(0, os.path.dirname(__file__))
    import paint_tex as pt
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    atlas = np.zeros((A, A, 4), np.float32)
    pf = pt.preset('foliage', {})
    for j in range(6):
        c, a, h = spray(100 + j * 7)
        c = bleed(c, a)
        p = pt.paint(c, normals(h, 3.0), pf)
        r, k = j // 3, j % 3          # row 0 = the atlas's top half
        atlas[r * CH:(r + 1) * CH, k * CW:(k + 1) * CW, :3] = p
        atlas[r * CH:(r + 1) * CH, k * CW:(k + 1) * CW, 3] = a
    c, h = bark(5)
    p = pt.paint(c, normals(h, 2.0), pt.preset('bark', {}))
    atlas[:, int(BU * A):, :3] = p
    atlas[:, int(BU * A):, 3] = 1
    out = os.path.join(OUT, f'{species}_atlas.png')
    Image.fromarray((np.clip(atlas, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(out)
    print(out)


# ---------------------------------------------------------------- geometry (Blender)

def cell_uv(j):
    """A spray cell's (u0, v0, du, dv) in Blender's UV (v up)."""
    r, k = j // 3, j % 3
    du, dv = CW / A, CH / A
    return k * du, 1 - (r + 1) * dv, du, dv


def frame(d):
    """A branch's side (horizontal, across it) and its card's up."""
    side = np.cross(np.array([0, 0, 1.0]), d)
    if np.linalg.norm(side) < 1e-4:
        side = np.array([1.0, 0, 0])
    side /= np.linalg.norm(side)
    up = np.cross(d, side)
    return side, up / np.linalg.norm(up)


class Build:
    def __init__(self):
        self.v, self.n, self.uv, self.f, self.c = [], [], [], [], []

    def quad_grid(self, P, N, UV, nu, nv, C=None, flip=False):
        """P, N, UV (and C, each vertex's (occlusion, tip, card: 1 where its front is the upper side)): (nv+1) x (nu+1) arrays; faces between
        them (flip: the other winding, so a card's front is its upper side)."""
        base = len(self.v)
        for j in range(nv + 1):
            for i in range(nu + 1):
                self.v.append(P[j][i]); self.n.append(N[j][i]); self.uv.append(UV[j][i])
                self.c.append(C[j][i] if C is not None else (1.0, 0.0, 0.0))
        w = nu + 1
        for j in range(nv):
            for i in range(nu):
                a = base + j * w + i
                self.f.append((a, a + w, a + w + 1, a + 1) if flip else (a, a + 1, a + w + 1, a + w))


def crown_normal(p, cn, d, H):
    """Out from the trunk and up, a little of the card's own: the crown shades as one mass."""
    r = np.array([p[0], p[1], 0.0])
    ln = np.linalg.norm(r)
    r = r / ln if ln > 0.15 else np.array([d[0], d[1], 0.0]) / max(np.linalg.norm(d[:2]), 1e-6)
    t = np.clip(p[2] / H, 0, 1)
    n = r * 0.45 + np.array([0, 0, 0.75 + 0.2 * t]) + cn * 0.3
    return n / np.linalg.norm(n)


def occlusion(p, H, R):
    """How open a point of the crown is (1 at the crown's skin, 0.35 at its axis): by its distance
    from the trunk against the crown's radius at its height (the crown a ragged cone)."""
    t = np.clip(p[2] / H, 0, 1)
    rc = max(R * (1 - t) ** 0.92 * 0.95, 0.3)
    return 0.35 + 0.65 * float(smooth(0.12, 0.92, math.hypot(p[0], p[1]) / rc))


def card(b, c0, d, length, width, roll, arch, droop, j, H, R, segs_l=2, segs_w=2, mirror=False):
    """A spray card from c0 along d (its foot at c0), bent: its sides hang (an A across it, the
    pendant branchlets) and its outer end droops; its front is its upper side."""
    side, up = frame(d)
    cr, sr = math.cos(roll), math.sin(roll)
    side, up = side * cr + up * sr, up * cr - side * sr
    u0, v0, du, dv = cell_uv(j)
    P, N, UV, C = [], [], [], []
    for jl in range(segs_l + 1):
        s = jl / segs_l
        rowP, rowN, rowU, rowC = [], [], [], []
        for iw in range(segs_w + 1):
            w = iw / segs_w * 2 - 1
            p = c0 + d * length * s + side * (w * width / 2 * (1 - 0.12 * w * w)) + up * (arch * width - droop * s * s * length - (0.24 + 0.16 * s) * width * w * w)
            rowP.append(p)
            rowN.append(crown_normal(p, up, d, H))
            uw = (-w if mirror else w)
            rowU.append((u0 + (uw + 1) / 2 * du * 0.96 + du * 0.02, v0 + s * dv * 0.97 + dv * 0.015))
            rowC.append((occlusion(p, H, R), s, 1.0))
        P.append(rowP); N.append(rowN); UV.append(rowU); C.append(rowC)
    b.quad_grid(P, N, UV, segs_w, segs_l, C, flip=True)


def trunk(b, H, rb, sides, rings, rng):
    lean = rng.normal(0, 0.03, 2)
    P, N, UV = [], [], []
    for k in range(rings + 1):
        t = k / rings
        z = -0.25 + (H + 0.25) * t ** 1.0
        rad = max(0.015, rb * (1 - t) ** 0.85)
        flare = 1 + 0.55 * math.exp(-max(z, 0) / 0.35)
        rowP, rowN, rowU = [], [], []
        for i in range(sides + 1):
            a = i / sides * 2 * math.pi
            bump = 1 + (0.18 * math.cos(a * 4 + 0.7) if z < 0.9 else 0) * math.exp(-max(z, 0) / 0.4)
            rr = rad * flare * bump
            p = np.array([math.cos(a) * rr + lean[0] * z * 0.1, math.sin(a) * rr + lean[1] * z * 0.1, z])
            rowP.append(p)
            rowN.append(np.array([math.cos(a), math.sin(a), 0.15]) / 1.011)
            v = 0.985 * (1 - math.exp(-max(z + 0.25, 0) / 3.6))
            rowU.append((BU + (1 - BU) * i / sides * 0.995, v))
        P.append(rowP); N.append(rowN); UV.append(rowU)
    # (the trunk stands in the crown's shade)
    b.quad_grid(P, N, UV, sides, rings, [[(0.6, 0.0, 0.0)] * (sides + 1)] * (rings + 1))


def spruce(H, R, seed, lod):
    """lod 0: every whorl, cards bent 2 x 2; 1: every other whorl, larger flat-ish cards; 2: a few tiers of big cards."""
    rng = np.random.default_rng(seed)
    b = Build()
    rb = 0.022 * H + 0.05
    trunk(b, H, rb, (10, 7, 5)[lod], (10, 5, 2)[lod], np.random.default_rng(seed + 1))
    hs = 0.55 + 0.03 * H                         # the lowest live whorl
    gap = (0.36, 0.72, 1.4)[lod]
    h = hs
    az0 = rng.uniform(0, 6.28)
    whorls = []
    while h < H - 0.45:
        whorls.append(h)
        h += gap * rng.uniform(0.8, 1.2)
    for wi, h in enumerate(whorls):
        t = (h - hs) / (H - hs)
        prof = (1 - t) ** 0.92 * (0.78 + 0.22 * smooth(0, 0.14, t)) + 0.05
        nb = int(rng.integers(5, 8)) if lod < 2 else 5
        az0 += 2.4
        for k in range(nb):
            az = az0 + k * 2 * math.pi / nb + rng.normal(0, 0.22)
            L = R * prof * rng.uniform(0.82, 1.12) * (1.08 if lod else 1.0)
            if L < 0.25:
                continue
            pitch = -math.radians(6 + 22 * (1 - t)) + rng.normal(0, 0.06)
            d = np.array([math.cos(az) * math.cos(pitch), math.sin(az) * math.cos(pitch), math.sin(pitch)])
            c0 = np.array([math.cos(az) * rb * (1 - t) * 0.6, math.sin(az) * rb * (1 - t) * 0.6, h])
            nc = 1 if lod == 2 else max(1, min(3, round(L / (1.05 if lod == 0 else 1.6))))
            seg = L / nc
            p = c0
            for ci in range(nc):
                f = (ci + 1) / nc
                dd = d + np.array([0, 0, 0.18 * f - 0.05])   # the tip turns up
                dd /= np.linalg.norm(dd)
                ln = seg * 1.3 * rng.uniform(0.85, 1.15)
                wd = ln * (0.7 if lod == 0 else 0.76) * rng.uniform(0.75, 1.25)
                card(b, p - dd * seg * 0.12, dd, ln, wd, rng.uniform(-0.55, 0.55), 0.1, (0.16 + 0.16 * (1 - t)) * (0.6 + 0.4 * f), int(rng.integers(0, 6)), H, R,
                     segs_l=(3, 2, 1)[lod], segs_w=(2, 2, 1)[lod], mirror=bool(rng.random() < 0.5))
                p = p + dd * seg
    # the leader: two crossed upright cards
    for a in (0.3, 0.3 + math.pi / 2):
        d = np.array([0.0, 0.0, 1.0])
        side = np.array([math.cos(a), math.sin(a), 0])
        u0, v0, du, dv = cell_uv(int(rng.integers(0, 6)))
        ln = 0.95
        P = [[np.array([0, 0, H - 0.5]) + side * w * 0.25 + d * ln * s for w in (-1, 1)] for s in (0, 1)]
        N = [[crown_normal(np.array([side[0] * w, side[1] * w, H]), np.array([0, 0, 1.0]), side, H) for w in (-1, 1)] for s in (0, 1)]
        UV = [[(u0 + (w + 1) / 2 * du, v0 + s * dv) for w in (-1, 1)] for s in (0, 1)]
        b.quad_grid(P, N, UV, 1, 1, [[(1.0, 1.0, 0.0)] * 2] * 2)
    return b


def shadow_proxy(H, R, seed):
    """What the tree casts (shadows only): stacked jagged cones, one per tier, so its shadow is a
    dense spiky spruce, not the cards' lace. Solid (its uvs in the bark strip), a few hundred tris."""
    rng = np.random.default_rng(seed + 5)
    b = Build()
    hs = 0.55 + 0.03 * H
    tiers = max(4, int((H - hs) / 1.05))
    th = (H - hs) / tiers
    uv = (BU + 0.1, 0.5)
    for k in range(tiers):
        h0 = hs + k * th
        t = (h0 - hs) / (H - hs)
        # (0.8 of the crown: the outer sprays stand outside it, so they take the key light; only the
        # crown's inside falls in the tree's own shadow)
        r = R * ((1 - t) ** 0.92 * (0.78 + 0.22 * smooth(0, 0.14, t)) + 0.05) * 0.8
        n = int(rng.integers(12, 16))
        az0 = rng.uniform(0, 6.28)
        ring = []
        for i in range(n * 2):
            a = az0 + i * math.pi / n + rng.normal(0, 0.1)
            rr = r * (rng.uniform(0.78, 1.1) if i % 2 == 0 else rng.uniform(0.38, 0.62))
            ring.append(np.array([math.cos(a) * rr, math.sin(a) * rr, h0 - (0.3 * rr if i % 2 == 0 else 0.0)]))
        ring.append(ring[0])
        apex = np.array([0.0, 0.0, min(h0 + th * 1.3, H)])
        P = [ring, [apex] * len(ring)]
        N = [[np.array([0, 0, 1.0])] * len(ring)] * 2
        UV = [[uv] * len(ring)] * 2
        b.quad_grid(P, N, UV, len(ring) - 1, 1)
    return b


def mesh(species):
    import bpy
    os.makedirs(OUT, exist_ok=True)
    img_path = os.path.join(OUT, f'{species}_atlas.png')
    for size, prm in SPRUCE.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        img = bpy.data.images.load(img_path)
        mat = bpy.data.materials.new(f'Leaves_Own{species.capitalize()}')
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes['Principled BSDF']
        ti = nt.nodes.new('ShaderNodeTexImage'); ti.image = img
        nt.links.new(ti.outputs['Color'], bsdf.inputs['Base Color'])
        clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
        nt.links.new(ti.outputs['Alpha'], clip.inputs[0]); nt.links.new(clip.outputs[0], bsdf.inputs['Alpha'])
        bsdf.inputs['Roughness'].default_value = 0.85
        mat.use_backface_culling = False
        tris = []
        for lod in range(4):
            b = spruce(prm['H'], prm['R'], prm['seed'], lod) if lod < 3 else shadow_proxy(prm['H'], prm['R'], prm['seed'])
            name = f'lod{lod}' if lod < 3 else 'shadow'
            me = bpy.data.meshes.new(name)
            me.from_pydata([tuple(p) for p in b.v], [], b.f)
            uvl = me.uv_layers.new(name='UV')
            for poly in me.polygons:
                for li in poly.loop_indices:
                    uvl.data[li].uv = b.uv[me.loops[li].vertex_index]
            me.normals_split_custom_set_from_vertices([tuple(n) for n in b.n])
            ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
            for i, c in enumerate(b.c):
                ca.data[i].color = (c[0], c[1], c[2], 1.0)
            me.color_attributes.active_color = ca
            me.materials.append(mat)
            ob = bpy.data.objects.new(name, me)
            bpy.context.scene.collection.objects.link(ob)
            tris.append(sum(len(p.vertices) - 2 for p in me.polygons))
        out = os.path.join(OUT, f'{species}_{size}.gltf')
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLTF_SEPARATE', export_texture_dir='', export_normals=True,
                                  export_tangents=False, export_materials='EXPORT', export_image_format='AUTO',
                                  export_keep_originals=True, export_yup=True, export_apply=True,
                                  export_vertex_color='ACTIVE')
        print(f'{out} tris lod0/1/2/shadow: {tris}')


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    species = arg('--species', 'spruce')
    if argv and argv[0] == 'tex':
        tex(species)
    elif argv and argv[0] == 'mesh':
        mesh(species)
    else:
        print(__doc__)
