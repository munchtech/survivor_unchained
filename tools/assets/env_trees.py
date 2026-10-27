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

The alder (--species alder; the kit's CommonTree_1-5): one to three stems from one foot, spreading
branches, a rounded-oval crown of leaf-clump branchlets (leafspray: clumps of round blunt leaves,
dark core, lit rim; a muted olive), lenticelled grey-brown bark (alder_bark), a lumpy shadow proxy.
Its material Leaves_OwnAlder: KitLook gives it more flutter and its own hue floor.
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

    # The twig: from the foot up, bent (never a straight midrib: judge E4b, a straight axis with even,
    # evenly spaced, tapered side shoots read as a fern frond). Half the sprays fork near the top.
    foot = np.array([W / 2 + rng.uniform(-20, 20) * S, H - 8 * S])
    up = -math.pi / 2 + rng.uniform(-0.15, 0.15)
    bend = rng.choice([-1, 1]) * rng.uniform(0.35, 0.6)
    twig = path(foot, up - bend * 0.4, H * rng.uniform(0.78, 0.86), bend, 40)
    twig[:, 0] = np.clip(twig[:, 0], 150 * S, W - 150 * S)
    # shoots: (points, radius px at its foot, its base value); the leading shoot is the twig's upper part
    lead0 = int(len(twig) * rng.uniform(0.24, 0.34))
    fork = rng.random() < 0.5
    fk = int(len(twig) * rng.uniform(0.66, 0.76)) if fork else len(twig) - 1
    shoots = [(twig[lead0:fk + 1], rng.uniform(140, 160) * S, 0.0)]
    end = twig[fk] - twig[fk - 1]
    end_a = math.atan2(end[1], end[0])
    # the end: blunt and clumped, drooping (a fork's two prongs, or a tuft of short shoots at the tip)
    prongs = [(-1, rng.uniform(0.3, 0.5)), (1, rng.uniform(0.3, 0.5))] if fork else \
        [(sd, rng.uniform(0.35, 0.65)) for sd in rng.permutation([-1, 1])[:int(rng.integers(1, 3))]]
    for sd, a in prongs:
        ln = H * (rng.uniform(0.17, 0.25) if fork else rng.uniform(0.09, 0.13))
        pts = path(twig[fk], end_a + sd * a, ln, sd * rng.uniform(0.2, 0.5), 12)
        pts[:, 0] = np.clip(pts[:, 0], 130 * S, W - 130 * S); pts[:, 1] = np.maximum(pts[:, 1], 120 * S)
        shoots.append((pts, rng.uniform(110, 130) * S * (0.9 if fork else 0.75), 0.04 * sd))
    # side shoots: three or four places a side, each side's own (never mirror-even), one or two of
    # them dropped; each its own length (40-100% of the room there), drooping out at its end
    for sd in (-1, 1):
        k = int(rng.integers(3, 5))
        cuts = np.sort(rng.uniform(0.08, 0.6, k))
        for i in range(1, k):
            cuts[i] = max(cuts[i], cuts[i - 1] + 0.08)
        keep = rng.permutation(k)[:k - int(rng.integers(1, 3))]
        for c in cuts[np.sort(keep)]:
            if c > 0.72:
                continue
            p = twig[int(c * (len(twig) - 1))]
            ang = up + sd * math.radians(rng.uniform(25, 72))
            f = rng.uniform(0.4, 1.0)
            ln = H * 0.44 * (1.05 - 0.45 * c) * f
            pts = path(p, ang, ln, sd * rng.uniform(0.1, 0.45), 18)
            # (keep it in the cell)
            pts[:, 0] = np.clip(pts[:, 0], 130 * S, W - 130 * S)
            shoots.append((pts, rng.uniform(112, 138) * S * (1.1 - 0.35 * c) * (0.75 + 0.25 * f), 0.05 * sd))
    # the bare twig's foot (below the shoots): a few short needles, so the card's foot is not a stick
    shoots.append((twig[:lead0 + 6], 74 * S, -0.04))
    # back to front: the foot's stub, then the side shoots from the foot up, the leading shoot last
    order = [len(shoots) - 1] + sorted(range(1, len(shoots) - 1), key=lambda i: shoots[i][0][0, 1], reverse=True) + [0]

    def stroke(pa, pe, c, w, img, a, h, hv):
        pa, pe = tuple(int(x) for x in pa), tuple(int(x) for x in pe)
        cv2.line(img, pa, pe, c, w, cv2.LINE_AA); cv2.line(a, pa, pe, 255, w, cv2.LINE_AA); cv2.line(h, pa, pe, hv, w, cv2.LINE_AA)

    # a slow wobble of each shoot's radius along it: tufts, not a sausage
    wob = [(rng.uniform(0, 6.28, 2), rng.uniform(1.4, 2.6)) for _ in shoots]
    # (every shoot's dark core first, then the needles over them all: a core drawn over the shoot
    # before it stood as a smooth dark oval on its needles)
    for pass_, si in [(0, i) for i in order] + [(1, i) for i in order]:
        pts, r0, vb = shoots[si]
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        L = seg.sum()
        cum = np.concatenate([[0], np.cumsum(seg)])
        ph, fq = wob[si]

        def at(d):
            i = int(np.clip(np.searchsorted(cum, d) - 1, 0, len(pts) - 2))
            f = (d - cum[i]) / max(seg[i], 1e-6)
            dv = (pts[i + 1] - pts[i]) / max(seg[i], 1e-6)
            return pts[i] + (pts[i + 1] - pts[i]) * f, dv

        def rad(s):
            # (blunt: full almost to the end, then rounded off; never drawn out to a point)
            taper = (1 - 0.3 * s ** 2) * (0.3 + 0.7 * smooth(0, 0.22, s)) * (0.55 + 0.45 * math.sqrt(max(0.0, 1 - smooth(0.82, 1.0, s))))
            return r0 * taper * (1 + 0.16 * math.sin(fq * 6.28 * s + ph[0]) + 0.08 * math.sin(2.3 * fq * 6.28 * s + ph[1]))

        if pass_ == 0:
            # 1. the shoot's dark core (the shadowed inside of the brush): a filled ragged mass, 60% of the radius
            lay = np.zeros((H, W), np.float32)
            for d in np.arange(0.1 * L, L, 6 * S):
                s = d / L
                p, _ = at(d)
                cv2.circle(lay, tuple(int(x) for x in p), int(rad(s) * 0.36 * rng.uniform(0.85, 1.1)), 1.0, -1, cv2.LINE_AA)
            dark = shade(0.12 + vb)
            m = lay[..., None]
            col = col * (1 - m) + dark[None, None] * m
            al = np.maximum(al, lay); hg = hg * (1 - lay) + 0.25 * lay
            continue
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


def leafspray(seed, pal=None, big=1.0, narrow=False, umbels=0):
    """One alder spray in a CW x CH cell (as spray: rgb, alpha, height): a leafy branchlet, its twig
    from the cell's foot with one to three side twigs, the leaves in four to six clumps along their
    outer parts and one at each twig's end (so a spray ends blunt, in a clump). A clump is the brush
    unit (about 0.6 m across, a quarter of the card's length): a dark shut-in core, then its leaves,
    round-obovate and blunt-tipped, fanned out from the twig, the inner ones dark and the rim's
    lighter, the lit flank (up and -x) lightest. Drawn at twice the size and halved."""
    import cv2
    rng = np.random.default_rng(seed)
    S = 2
    W, H = CW * S, CH * S
    # a muted olive (hue 80-90: beside the spruce's blue-green, never yellow)
    pal = [srgb(h) for h in (pal or ('#151b0f', '#263119', '#3a4826', '#536534', '#73874c'))]
    # (big: the clump a size larger in its cell, fewer of them: a bush's card is half an alder's, its clump the same in the world)

    def shade(v):
        v = float(np.clip(v, 0, 0.999)) * (len(pal) - 1)
        i = int(v); f = v - i
        return ((pal[i] * (1 - f) + pal[i + 1] * f) * 255).astype(int).tolist()

    def path(p0, ang, length, curl, n):
        pts = [np.array(p0, np.float64)]
        for i in range(n):
            a = ang + curl * (i / n)
            pts.append(pts[-1] + np.array([math.cos(a), math.sin(a)]) * length / n)
        pts = np.array(pts)
        mg = 110 * S * big
        pts[:, 0] = np.clip(pts[:, 0], mg, W - mg); pts[:, 1] = np.maximum(pts[:, 1], mg)
        return pts

    def P(q):
        return tuple(int(x) for x in q)

    foot = np.array([W / 2 + rng.uniform(-24, 24) * S, H - 6 * S])
    up = -math.pi / 2 + rng.uniform(-0.15, 0.15)
    bend = rng.choice([-1, 1]) * rng.uniform(0.3, 0.6)
    twig = path(foot, up - 0.4 * bend, H * rng.uniform(0.74, 0.84), bend, 30)
    twigs = [(twig, 7.0 * S)]
    for c in np.sort(rng.uniform(0.25, 0.62, int(rng.integers(1, 4 if big == 1 else 3)))):
        p = twig[int(c * (len(twig) - 1))]
        sd = rng.choice([-1, 1])
        twigs.append((path(p, up + sd * math.radians(rng.uniform(28, 62)), H * rng.uniform(0.22, 0.36) * (1.1 - 0.5 * c), sd * rng.uniform(0.1, 0.5), 14), 5.0 * S))
    # the clumps: one at each twig's end, the rest along the twigs' outer parts
    clumps = [(tw[-1] + rng.normal(0, 8 * S, 2), rng.uniform(110, 140) * S * big) for tw, _ in twigs]
    for c in np.sort(rng.uniform(0.22, 0.85, int(rng.integers(3, 5) if big == 1 else rng.integers(1, 3)))):   # (down the main twig: no bare stalk)
        q = twig[int(c * (len(twig) - 1))]
        clumps.append((q + rng.normal(0, 22 * S, 2), rng.uniform(100, 130) * S * (0.85 + 0.2 * c) * big))
    for tw, _ in twigs[1:]:
        q = tw[int(rng.uniform(0.35, 0.6) * (len(tw) - 1))]
        clumps.append((q + rng.normal(0, 12 * S, 2), rng.uniform(85, 110) * S * big))
    clumps.sort(key=lambda c: -c[0][1])                   # (back to front: the lower clumps first)
    cimg = np.zeros((H, W, 3), np.uint8); aimg = np.zeros((H, W), np.uint8); himg = np.zeros((H, W), np.uint8)
    # 1. the twigs (grey-brown, showing in the gaps)
    for tw, w0 in twigs:
        for i in range(len(tw) - 1):
            w = int(max(2, w0 * (1 - 0.6 * i / len(tw))))
            cv2.line(cimg, P(tw[i]), P(tw[i + 1]), (52, 46, 40), w, cv2.LINE_AA); cv2.line(aimg, P(tw[i]), P(tw[i + 1]), 255, w, cv2.LINE_AA)
            cv2.line(himg, P(tw[i]), P(tw[i + 1]), 90, w, cv2.LINE_AA)
    # 2. every clump's dark core (a ragged mass, half the clump's radius), under all the leaves
    for c, rc in clumps:
        for _ in range(7):
            q = P(c + rng.normal(0, 0.12 * rc, 2)); r = int(rc * rng.uniform(0.24, 0.36))
            # (0.18, not 0.07: the cores at near black read as holes in the crown by day, judge E4c)
            cv2.circle(cimg, q, r, shade(0.18), -1, cv2.LINE_AA); cv2.circle(aimg, q, r, 255, -1, cv2.LINE_AA); cv2.circle(himg, q, r, 50, -1, cv2.LINE_AA)
    # 2b. every clump's rim a ring of round lobes (leaf masses), under the leaves: the clump's outline
    # scalloped and soft, a broadleaf's, not the spruce's spiky one (judge E4c: the alder's rim as jagged)
    for c, rc in clumps:
        nl = int(rng.integers(6, 10)); a0 = rng.uniform(0, 6.28)
        for i in range(nl):
            a = a0 + (i + rng.normal(0, 0.15)) * 2 * math.pi / nl
            q = P(c + np.array([math.cos(a), math.sin(a)]) * rc * rng.uniform(0.6, 0.74)); r = int(rc * rng.uniform(0.2, 0.27))
            lit = 0.5 * (-math.cos(a) * 0.6 - math.sin(a) * 0.8) + 0.5
            cv2.circle(cimg, q, r, shade(0.3 + 0.2 * lit), -1, cv2.LINE_AA); cv2.circle(aimg, q, r, 255, -1, cv2.LINE_AA); cv2.circle(himg, q, r, 160, -1, cv2.LINE_AA)
    # 3. the leaves, clump by clump: the inner first, the rim's over them
    ts = np.linspace(0, 1, 9)
    for c, rc in clumps:
        lv = sorted((math.sqrt(rng.uniform(0.02, 1)) * 0.82, rng.uniform(0, 2 * math.pi)) for _ in range(int(rc / S * 0.42)))
        for rr, a in lv:
            q = c + np.array([math.cos(a), math.sin(a)]) * rr * rc
            ang = a + rng.normal(0, 0.45)                      # (fanned out from the twig)
            Ll = rc * rng.uniform(0.3, 0.42) * (0.8 + 0.3 * rr)
            Wl = Ll * (rng.uniform(0.4, 0.5) if narrow else rng.uniform(0.62, 0.78))
            dv = np.array([math.cos(ang), math.sin(ang)]); nv = np.array([-dv[1], dv[0]])
            # round-obovate: widest three quarters out, the tip a round end (no point, no notch: the
            # crown's rim scalloped, judge E4c)
            q0 = q - dv * Ll * 0.35
            t1 = np.linspace(0, 0.72, 7)
            hw = Wl / 2 * np.sin(np.pi / 2 * t1 / 0.72) ** 0.7
            left = [q0 + dv * Ll * t + nv * w for t, w in zip(t1, hw)]
            right = [q0 + dv * Ll * t - nv * w for t, w in zip(t1, hw)]
            arc = [q0 + dv * Ll * (0.72 + 0.28 * math.sin(th)) + nv * Wl / 2 * math.cos(th) for th in np.linspace(0.3, math.pi - 0.3, 6)]
            left += arc[:3]; right += arc[3:][::-1]
            notch = q0 + dv * Ll * 1.0
            poly = np.array(left + [notch] + right[::-1], np.int32)
            # value: deep inside dark, the rim light, the lit flank (up and -x) lighter
            lit = 0.5 * (-math.cos(a) * 0.6 - math.sin(a) * 0.8) + 0.5
            v = 0.2 + 0.36 * rr ** 1.3 + 0.28 * lit * rr + rng.normal(0, 0.05)
            cv2.fillPoly(cimg, [poly], shade(v), cv2.LINE_AA); cv2.fillPoly(aimg, [poly], 255, cv2.LINE_AA)
            cv2.fillPoly(himg, [poly], int(110 + 120 * rr), cv2.LINE_AA)
            # the leaf's light half (its blade tilted to the sky), and its midrib a shade darker
            cv2.fillPoly(cimg, [np.array(left + [notch, q0 + dv * Ll * 0.9, q0], np.int32)], shade(v + 0.08), cv2.LINE_AA)
            cv2.line(cimg, P(q0), P(q0 + dv * Ll * 0.85), shade(v - 0.06), max(1, S), cv2.LINE_AA)
    # 4. the elder's umbels: a few flat-topped cream heads on the upper clumps (small, muted: never confetti)
    for c, rc in sorted(clumps, key=lambda c: c[0][1])[:umbels]:
        q = c + np.array([rng.uniform(-0.2, 0.2), -0.25]) * rc
        # (E4h: wider and paler, so a head reads as one cream disc at the play camera, judge E4f: none found at 1:1)
        ru = rc * rng.uniform(0.32, 0.38)
        for _ in range(60):
            a, rr = rng.uniform(0, 6.28), math.sqrt(rng.uniform(0, 1))
            o = P(q + np.array([math.cos(a) * ru * rr, math.sin(a) * ru * rr * 0.55]))
            v = 0.55 + 0.45 * (1 - rr) * (0.5 + 0.5 * -math.sin(a))
            cc = (srgb('#8b8770') + (srgb('#c4bfa2') - srgb('#8b8770')) * v) * 255
            cv2.circle(cimg, o, int(rc * 0.07), cc.astype(int).tolist(), -1, cv2.LINE_AA); cv2.circle(aimg, o, int(rc * 0.07), 255, -1, cv2.LINE_AA)
            cv2.circle(himg, o, int(rc * 0.07), 240, -1, cv2.LINE_AA)
    col = cimg.astype(np.float32) / 255; al = aimg.astype(np.float32) / 255; hg = himg.astype(np.float32) / 255
    col = cv2.resize(col, (CW, CH), interpolation=cv2.INTER_AREA)
    al = cv2.resize(al, (CW, CH), interpolation=cv2.INTER_AREA)
    hg = cv2.resize(hg, (CW, CH), interpolation=cv2.INTER_AREA)
    col = np.clip(col / np.maximum(al, 1e-3)[..., None], 0, 1) * (al > 0)[..., None]
    ys = np.mgrid[0:CH, 0:CW][0].astype(np.float32)
    col *= (0.8 + 0.2 * smooth(0, 0.6, 1 - ys / CH))[..., None]
    return col, al, cv2.GaussianBlur(hg, (5, 5), 1.5)


def alder_bark(seed, W=512, H=2048):
    """The alder's bark strip: dark grey-brown, smooth with pale lenticels (short level dashes, a
    shadow under each), a few shallow cracks, a little lichen; seamless round the trunk (u)."""
    import cv2
    rng = np.random.default_rng(seed)
    lowf = np.zeros((H, W), np.float32)
    for s, w in ((96, 0.55), (32, 0.3), (10, 0.15)):
        n = rng.random((H // s + 2, W // s + 1)).astype(np.float32)
        n = np.concatenate([n, n[:, :1]], 1)
        lowf += w * cv2.resize(n, (W + s, H + 2 * s), interpolation=cv2.INTER_CUBIC)[:H, :W]
    base, grey, crev, lent, lich = srgb('#3f3a35'), srgb('#5a554f'), srgb('#24201c'), srgb('#8d8677'), srgb('#6b7262')
    col = base[None, None] + (grey - base)[None, None] * smooth(0.35, 0.8, lowf)[..., None]
    cim = (col * 255).astype(np.uint8)
    him = (0.3 * lowf * 255).astype(np.uint8)
    cv_crev = (crev * 255).astype(int).tolist()
    # shallow cracks: thin wavy lines up the trunk, sparse
    for _ in range(14):
        x = rng.uniform(0, W); y = rng.uniform(0, H); L = rng.uniform(80, 340)
        pts = [(x + 6 * math.sin(k * 0.4 + x), y + k * L / 20) for k in range(21)]
        wd = int(rng.integers(2, 4))
        for dx in (-W, 0, W):
            pp = np.array([(a + dx, b) for a, b in pts], np.int32)
            cv2.polylines(cim, [pp], False, cv_crev, wd, cv2.LINE_AA); cv2.polylines(him, [pp], False, 10, 3, cv2.LINE_AA)
    # lenticels
    for _ in range(1400):
        x = rng.uniform(0, W); y = rng.uniform(0, H)
        ax = (int(rng.uniform(2, 6.5)), 1)
        lc = ((base + (lent - base) * rng.uniform(0.45, 0.85)) * 255).astype(int).tolist()
        for dx in (-W, 0, W):
            c = (int(x + dx), int(y))
            cv2.ellipse(cim, (c[0], c[1] + 1), ax, 0, 0, 360, cv_crev, -1, cv2.LINE_AA)
            cv2.ellipse(cim, c, ax, 0, 0, 360, lc, -1, cv2.LINE_AA)
            cv2.ellipse(him, c, ax, 0, 0, 360, 200, -1, cv2.LINE_AA)
    col = cim.astype(np.float32) / 255
    lm = smooth(0.72, 0.85, lowf)
    col = col + (lich - col) * (0.45 * lm)[..., None]
    return col, cv2.GaussianBlur(him.astype(np.float32) / 255, (3, 3), 0.8)


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


# ---------------------------------------------------------------- step C's textures (E4f): snag bark, bush leaves, bracken fronds

# (palettes, dark to light: the clump's shut-in core to its lit rim; a muted olive to blue-green, never yellow, never lime)
PAL = {
    'alder': ('#151b0f', '#263119', '#3a4826', '#536534', '#73874c'),     # hue 80-90
    'hazel': ('#141b10', '#25321b', '#384a29', '#4f6538', '#6a8250'),     # a shade bluer than the alder: hue 90-95
    'elder': ('#111a13', '#1f2f22', '#2f4533', '#445f46', '#5e7a5d'),     # blue-green, darker: hue 115-125
    'bracken': ('#131a0e', '#232f17', '#364723', '#4b6131', '#637a43'),   # olive, hue 85-90, its tips no lighter than the alder's
}


def snag_bark(seed, W=512, H=2048):
    """The snag's strip: a dead spruce's wood, weathered silver-grey: long grain streaks up the trunk (a slight
    twist), deep checks (long cracks), knots where the branches were, a few plates of bark left (dark brown-grey),
    pale lichen in spots; seamless round the trunk (u)."""
    import cv2
    rng = np.random.default_rng(seed)
    lowf = np.zeros((H, W), np.float32)
    for s, w in ((128, 0.5), (40, 0.3), (12, 0.2)):
        n = rng.random((H // s + 2, W // s + 1)).astype(np.float32)
        n = np.concatenate([n, n[:, :1]], 1)
        lowf += w * cv2.resize(n, (W + s, H + 2 * s), interpolation=cv2.INTER_CUBIC)[:H, :W]
    # the grain: noise stretched 40 times along v, sheared a little (the twist), wrapped in u
    g = rng.random((H // 40 + 2, W // 2)).astype(np.float32)
    g = np.concatenate([g, g[:, :1]], 1)
    grain = cv2.resize(g, (W + 2, H + 80), interpolation=cv2.INTER_CUBIC)[:H, :W]
    ys = np.arange(H)[:, None]
    grain = np.take_along_axis(np.tile(grain, (1, 3)), (np.arange(W)[None, :] + W + (ys * 0.06).astype(int)) % (3 * W), 1)
    base, light, dark, crev, plate, lich = srgb('#6b6862'), srgb('#8a867d'), srgb('#4b4843'), srgb('#24211e'), srgb('#3e352e'), srgb('#7f8774')
    t = np.clip(0.55 * grain + 0.45 * lowf, 0, 1)
    col = dark[None, None] + (light - dark)[None, None] * smooth(0.25, 0.85, t)[..., None]
    col = col * 0.55 + base[None, None] * 0.45
    hgt = 0.4 * grain + 0.3 * lowf
    cim = (np.clip(col, 0, 1) * 255).astype(np.uint8)
    him = (np.clip(hgt, 0, 1) * 255).astype(np.uint8)
    cc = (crev * 255).astype(int).tolist()
    # checks: long, nearly straight cracks up the wood
    for _ in range(18):
        x = rng.uniform(0, W); y = rng.uniform(-200, H); L = rng.uniform(200, 900)
        pts = [(x + 4 * math.sin(k * 0.3 + x) + k * L / 30 * 0.06, y + k * L / 30) for k in range(31)]
        wd = int(rng.integers(2, 5))
        for dx in (-W, 0, W):
            pp = np.array([(a + dx, b) for a, b in pts], np.int32)
            cv2.polylines(cim, [pp], False, cc, wd, cv2.LINE_AA); cv2.polylines(him, [pp], False, 0, wd + 1, cv2.LINE_AA)
    # knots: dark ovals with a lighter ring, the grain round them
    for _ in range(9):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        ax = (int(rng.uniform(8, 16)), int(rng.uniform(12, 24)))
        for dx in (-W, 0, W):
            c = (int(x + dx), int(y))
            cv2.ellipse(cim, c, (ax[0] + 5, ax[1] + 7), 0, 0, 360, (light * 235).astype(int).tolist(), -1, cv2.LINE_AA)
            cv2.ellipse(cim, c, ax, 0, 0, 360, (plate * 200).astype(int).tolist(), -1, cv2.LINE_AA)
            cv2.ellipse(him, c, ax, 0, 0, 360, 40, -1, cv2.LINE_AA)
    col = cim.astype(np.float32) / 255
    hgt = him.astype(np.float32) / 255
    # plates of bark left, low on the trunk (v small: the image's bottom rows), ragged-edged
    pm = smooth(0.62, 0.7, lowf) * (1 - smooth(0.25, 0.6, 1 - ys / H))
    col = col + (plate - col) * (0.85 * pm)[..., None]
    hgt = hgt + 0.25 * pm
    lm = smooth(0.74, 0.86, lowf) * (1 - pm)
    col = col + (lich - col) * (0.4 * lm)[..., None]
    return col, cv2.GaussianBlur(hgt, (3, 3), 0.8)


def stipe_strip(seed, W=512, H=2048):
    """The bracken's strip (its stems, under the fronds): a dark brown-green, faintly streaked."""
    import cv2
    rng = np.random.default_rng(seed)
    n = rng.random((H // 32 + 2, W // 8 + 1)).astype(np.float32)
    n = np.concatenate([n, n[:, :1]], 1)
    f = cv2.resize(n, (W + 8, H + 64), interpolation=cv2.INTER_CUBIC)[:H, :W]
    a, b = srgb('#1d2014'), srgb('#3a3a24')
    return a[None, None] + (b - a)[None, None] * f[..., None], 0.4 * f


def frond(seed, pal):
    """One bracken frond in a CW x CH cell (rgb, alpha, height): its stipe from the cell's foot (the lower fifth, dark:
    the clump's dark base), then a triangular blade, eight to eleven pairs of pinnae off a bent rachis, the lower ones
    longest, each pinna a lanceolate mass with a lobed (pinnule) edge, dark at the rachis and lighter to its tip, its lit
    flank (up and -x) lighter. At the play camera a frond is one feathery wedge; the pinnae its broken edge. Drawn
    at twice the size and halved."""
    import cv2
    rng = np.random.default_rng(seed)
    S = 2
    W, H = CW * S, CH * S
    pl = [srgb(h) for h in pal]

    def shade(v):
        v = float(np.clip(v, 0, 0.999)) * (len(pl) - 1)
        i = int(v); f = v - i
        return ((pl[i] * (1 - f) + pl[i + 1] * f) * 255).astype(int).tolist()

    cimg = np.zeros((H, W, 3), np.uint8); aimg = np.zeros((H, W), np.uint8); himg = np.zeros((H, W), np.uint8)
    foot = np.array([W / 2 + rng.uniform(-20, 20) * S, H - 4 * S])
    bend = rng.choice([-1, 1]) * rng.uniform(0.15, 0.35)
    n = 40
    rach = [foot]
    for i in range(n):
        a = -math.pi / 2 + bend * (i / n) ** 1.5
        rach.append(rach[-1] + np.array([math.cos(a), math.sin(a)]) * H * 0.95 / n)
    rach = np.array(rach)
    rach[:, 0] = np.clip(rach[:, 0], 80 * S, W - 80 * S)
    t0 = rng.uniform(0.2, 0.25)                     # where the blade starts
    # the stipe and rachis
    for i in range(n):
        t = i / n
        w = int(max(2, (9 if t < t0 else 6 * (1 - t)) * S))
        c = (46, 44, 30) if t < t0 else shade(0.12)
        cv2.line(cimg, tuple(int(x) for x in rach[i]), tuple(int(x) for x in rach[i + 1]), c, w, cv2.LINE_AA)
        cv2.line(aimg, tuple(int(x) for x in rach[i]), tuple(int(x) for x in rach[i + 1]), 255, w, cv2.LINE_AA)
        cv2.line(himg, tuple(int(x) for x in rach[i]), tuple(int(x) for x in rach[i + 1]), 70, w, cv2.LINE_AA)
    npairs = int(rng.integers(12, 16))
    ts = t0 + (0.97 - t0) * (np.arange(npairs) / npairs) ** 0.85
    for k, t in enumerate(ts):
        u = (t - t0) / (0.97 - t0)
        i = int(t * n)
        p = rach[i]
        tang = rach[min(i + 1, n)] - rach[max(i - 1, 0)]; tang /= np.linalg.norm(tang)
        for side in (-1, 1):
            Lp = W * 0.5 * (1 - u) ** 0.8 * rng.uniform(0.85, 1.05) + W * 0.04
            ang = math.atan2(tang[1], tang[0]) + side * math.radians(rng.uniform(55, 72) - 18 * u)
            dv = np.array([math.cos(ang), math.sin(ang)]); nv = np.array([-dv[1], dv[0]])
            q0 = p + side * tang * 0  # (off the rachis)
            q0 = q0 + tang * side * rng.uniform(0, 10) * S * (1 - u)
            wp = Lp * rng.uniform(0.38, 0.46)
            m = 14
            nl = max(3, int(Lp / (34 * S)))      # pinnules along it
            top, bot = [], []
            for j in range(m + 1):
                v = j / m
                lob = 0.62 + 0.38 * abs(math.sin(v * nl * math.pi))
                hw = wp / 2 * (1 - v) ** 0.75 * (0.6 + 0.4 * math.sin(math.pi * min(1, v * 3 + 0.2))) * lob
                cc = q0 + dv * Lp * v + nv * Lp * 0.05 * math.sin(v * 2.6) * side   # (a slight curve)
                top.append(cc + nv * hw); bot.append(cc - nv * hw)
            poly = np.array(top + bot[::-1], np.int32)
            lit = 0.5 * (-dv[0] * 0.6 - dv[1] * 0.8) + 0.5
            v0 = 0.36 + 0.12 * u + 0.22 * lit + rng.normal(0, 0.04)
            cv2.fillPoly(cimg, [poly], shade(v0), cv2.LINE_AA); cv2.fillPoly(aimg, [poly], 255, cv2.LINE_AA)
            cv2.fillPoly(himg, [poly], int(120 + 80 * lit), cv2.LINE_AA)
            # its outer half lighter (the pinnules' lit tips), its midrib dark
            outer = np.array(top[m // 2:] + bot[m // 2:][::-1], np.int32)
            cv2.fillPoly(cimg, [outer], shade(v0 + 0.16), cv2.LINE_AA)
            half = np.array(top[:m] + [q0 + dv * Lp * 0.95], np.int32)
            cv2.fillPoly(cimg, [half], shade(v0 + 0.07 + 0.1 * lit), cv2.LINE_AA)
            cv2.line(cimg, tuple(int(x) for x in q0), tuple(int(x) for x in q0 + dv * Lp * 0.85), shade(v0 - 0.15), max(1, S), cv2.LINE_AA)
    col = cimg.astype(np.float32) / 255; al = aimg.astype(np.float32) / 255; hg = himg.astype(np.float32) / 255
    col = cv2.resize(col, (CW, CH), interpolation=cv2.INTER_AREA)
    al = cv2.resize(al, (CW, CH), interpolation=cv2.INTER_AREA)
    hg = cv2.resize(hg, (CW, CH), interpolation=cv2.INTER_AREA)
    col = np.clip(col / np.maximum(al, 1e-3)[..., None], 0, 1) * (al > 0)[..., None]
    ys = np.mgrid[0:CH, 0:CW][0].astype(np.float32)
    # darker toward the foot (the clump's base, under the blades)
    col *= (0.55 + 0.45 * smooth(0.0, 0.45, 1 - ys / CH))[..., None]
    return col, al, cv2.GaussianBlur(hg, (5, 5), 1.5)


# What each species' atlas holds: its six cells (rgb, alpha, height) and its strip (rgb, height); and its paint presets.
def cells(species):
    if species == 'spruce':
        return [spray(100 + j * 7) for j in range(6)], bark(5)
    if species == 'alder':
        return [leafspray(200 + j * 11) for j in range(6)], alder_bark(9)
    if species == 'snag':
        return None, snag_bark(13)
    if species == 'bush':
        # cells 0-2 hazel, 3-5 elder (narrower leaves; umbels in cells 4 and 5: a few, never confetti)
        return ([leafspray(300 + j * 13, pal=PAL['hazel'], big=1.45) for j in range(3)]
                + [leafspray(400 + j * 13, pal=PAL['elder'], big=1.45, narrow=True, umbels=(0, 1, 2)[j]) for j in range(3)]), alder_bark(17)
    if species == 'bracken':
        return [frond(500 + j * 17, PAL['bracken']) for j in range(6)], stipe_strip(19)
    raise SystemExit(f'no species {species}')


def tex(species):
    if species == 'grass':
        return grass_tex()
    sys.path.insert(0, os.path.dirname(__file__))
    import paint_tex as pt
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    atlas = np.zeros((A, A, 4), np.float32)
    pf = pt.preset('foliage', {})
    cs, (c, h) = cells(species)
    for j, (cc, a, hh) in enumerate(cs or []):
        cc = bleed(cc, a)
        p = pt.paint(cc, normals(hh, 3.0), pf)
        r, k = j // 3, j % 3          # row 0 = the atlas's top half
        atlas[r * CH:(r + 1) * CH, k * CW:(k + 1) * CW, :3] = p
        atlas[r * CH:(r + 1) * CH, k * CW:(k + 1) * CW, 3] = a
    p = pt.paint(c, normals(h, 2.0), pt.preset('bark', {}))
    atlas[:, int(BU * A):, :3] = p
    atlas[:, int(BU * A):, 3] = 1
    if cs is None:   # (a bark-only species: its unused cells its strip's mean, so the mips stay clean)
        atlas[:, :int(BU * A), :3] = p.mean((0, 1)); atlas[:, :int(BU * A), 3] = 1
    out = os.path.join(OUT, f'{species}_atlas.png')
    Image.fromarray((np.clip(atlas, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(out)
    print(out)


# ---------------------------------------------------------------- step D's grass (E4h): painted clump cards

GC = 256            # a grass clump's cell (the atlas: 4 x 2 cells, 1024 x 512)


def grass_kinds():
    import json
    with open(os.path.join(ROOT, 'godot', 'data', 'flora_species.json'), encoding='utf-8') as f:
        return json.load(f)['grass']['kinds']


def grass_clump(seed, olive, cool, flowers=None, nflowers=0, form=0):
    """One grass clump in a GC x GC cell (rgb, alpha, height): three to five blades from one root, never a fan of
    even spokes: the roots a little apart, the clump leaning to one side (its blades' leans uneven, one or two arching
    over), each blade tapered to a point, dark at its root (the ground's shadow in the clump) and lighter to its tip,
    a muted olive or a blue-green per blade; two or three short dark blades at the foot bulk the base. With flowers,
    a few small muted heads on thin stems over the clump (never confetti). Seen side-on (the card faces the camera),
    so at the play camera a clump is a tuft leaning its own way, not a star. Drawn at twice the size and halved."""
    import cv2
    rng = np.random.default_rng(seed)
    S = 2
    W = H = GC * S
    cimg = np.zeros((H, W, 3), np.uint8)
    a8 = np.zeros((H, W), np.uint8)
    h8 = np.zeros((H, W), np.uint8)
    po, pc = [srgb(h) for h in olive], [srgb(h) for h in cool]

    def shade(v, m):
        v = float(np.clip(v, 0, 0.999)) * (len(po) - 1)
        i = int(v); f = v - i
        a = po[i] * (1 - f) + po[i + 1] * f
        b = pc[i] * (1 - f) + pc[i + 1] * f
        return a * (1 - m) + b * m

    def c8(c):
        return (np.clip(c, 0, 1) * 255).astype(int).tolist()

    side = rng.choice([-1, 1])
    cx = W / 2 + rng.uniform(-0.04, 0.04) * W
    n = int(rng.integers(4, 6))
    # blades: (root x, lean rad from upright, length, curl, root width, hue mix, value offset)
    # the clump's form (a cell each, so no two read alike): 0 upright and narrow, 1 spreading and low, 2 one long
    # blade arching over the rest, 3 leaning hard to one side
    spread, lmin, lmax, lean0 = [(0.3, 0.6, 0.92, 0.08), (0.75, 0.38, 0.62, 0.1), (0.45, 0.45, 0.75, 0.15), (0.35, 0.5, 0.82, 0.45)][form % 4]
    leans = np.sort(rng.uniform(-spread, spread, n)) + side * lean0 + rng.normal(0, 0.1, n)
    hm = rng.uniform(0, 1) ** 1.6       # (mostly olive; the blue-green comes with the low ground and the night)
    blades = []
    for k in range(n):
        ln = H * rng.uniform(lmin, lmax)
        curl = np.sign(leans[k] + 1e-3) * rng.uniform(0.2, 0.7)
        if (form % 4 == 2 and k == n - 1) or rng.random() < 0.15:      # one arching over
            curl = side * rng.uniform(1.3, 1.8); ln = H * rng.uniform(0.75, 0.9)
        blades.append((cx + rng.uniform(-0.06, 0.06) * W + leans[k] * 0.05 * W, leans[k], ln, curl,
                       rng.uniform(13, 18) * S, float(np.clip(hm + rng.normal(0, 0.28), 0, 1)), rng.uniform(-0.08, 0.06)))
    # the short dark blades at the foot (drawn first: behind)
    foot = [(cx + rng.uniform(-0.08, 0.08) * W, rng.uniform(-0.9, 0.9), H * rng.uniform(0.2, 0.36), rng.uniform(-0.6, 0.6),
             rng.uniform(11, 15) * S, float(np.clip(hm + rng.normal(0, 0.2), 0, 1)), -0.12) for _ in range(int(rng.integers(3, 6)))]
    order = foot + sorted(blades, key=lambda b: b[2])
    base_y = H - 6 * S
    for (rx, lean, ln, curl, w0, m, vb) in order:
        N = 28
        pts = []
        p = np.array([rx, base_y], np.float64)
        for i in range(N + 1):
            pts.append(p.copy())
            a = lean + curl * (i / N) ** 2
            p = p + np.array([math.sin(a), -math.cos(a)]) * ln / N
            p[0] = np.clip(p[0], 0.06 * W, 0.94 * W); p[1] = max(p[1], 0.04 * H)
        pts = np.array(pts)
        tw = rng.uniform(0, 6.28)
        wd = lambda s: w0 * 0.5 * (1 - s) ** 0.85 * (1 + 0.08 * math.sin(9 * s + tw))
        for i in range(N):
            s0, s1 = i / N, (i + 1) / N
            d = pts[i + 1] - pts[i]
            nv = np.array([-d[1], d[0]]) / max(np.linalg.norm(d), 1e-6)
            q = np.array([pts[i] + nv * wd(s0), pts[i + 1] + nv * wd(s1), pts[i + 1] - nv * wd(s1), pts[i] - nv * wd(s0)])
            sm = (s0 + s1) / 2
            qi = np.round(q * 4).astype(np.int32)
            cv2.fillConvexPoly(cimg, qi, c8(shade(0.06 + 0.86 * sm ** 0.75 + vb + rng.normal(0, 0.02), m)), cv2.LINE_AA, 2)
            cv2.fillConvexPoly(a8, qi, 255, cv2.LINE_AA, 2)
            cv2.fillConvexPoly(h8, qi, int(90 + 140 * sm), cv2.LINE_AA, 2)
        # the blade's lit edge: a thin lighter stroke along one side of its upper half (painted, not a midrib)
        for i in range(N // 2, N - 2):
            s = i / N
            d = pts[i + 1] - pts[i]
            nv = np.array([-d[1], d[0]]) / max(np.linalg.norm(d), 1e-6) * (-side)
            off = nv * wd(s) * 0.5
            cv2.line(cimg, tuple(np.round(pts[i] + off).astype(int)), tuple(np.round(pts[i + 1] + off).astype(int)),
                     c8(shade(0.2 + 0.86 * s ** 0.75 + vb, m) * 1.08), max(2, int(w0 * 0.2 * (1 - s))), cv2.LINE_AA)
    if flowers and nflowers:
        # a few small heads on thin stems, over the clump: muted cream or pale lilac (one colour a clump)
        fc = srgb(flowers[int(rng.integers(0, len(flowers)))])
        for k in range(nflowers):
            fx = cx + rng.uniform(-0.22, 0.22) * W
            top = H * rng.uniform(0.3, 0.5)
            r0 = (int(cx + (fx - cx) * 0.3), int(base_y))
            cv2.line(cimg, r0, (int(fx), int(top)), c8(shade(0.35, hm)), 3 * S, cv2.LINE_AA)
            cv2.line(a8, r0, (int(fx), int(top)), 255, 3 * S, cv2.LINE_AA)
            for j in range(int(rng.integers(4, 7))):
                r = int(rng.uniform(3.5, 5.5) * S)
                ctr = (int(fx + rng.normal(0, 5) * S), int(top + rng.normal(0, 3.5) * S))
                cv2.circle(cimg, ctr, r, c8(fc * rng.uniform(0.82, 1.0)), -1, cv2.LINE_AA)
                cv2.circle(a8, ctr, r, 255, -1, cv2.LINE_AA)
                cv2.circle(h8, ctr, r, 230, -1, cv2.LINE_AA)
    col = cv2.resize(cimg.astype(np.float32) / 255, (GC, GC), interpolation=cv2.INTER_AREA)
    al = cv2.resize(a8.astype(np.float32) / 255, (GC, GC), interpolation=cv2.INTER_AREA)
    hg = cv2.resize(h8.astype(np.float32) / 255, (GC, GC), interpolation=cv2.INTER_AREA)
    col = np.clip(col / np.maximum(al, 1e-3)[..., None], 0, 1) * (al > 0)[..., None]
    return col, al, cv2.GaussianBlur(hg, (5, 5), 1.2)


def grass_tex():
    """Each grass kind's atlas (flora_species.json "grass" "kinds"): 4 x 2 clump cells, the last `flower_cells` of
    them with a few heads; painted as the trees' sprays are (paint_tex, foliage): grass_<kind>_atlas.png. The cards
    themselves are made in the game (World/Grass.cs), not here."""
    sys.path.insert(0, os.path.dirname(__file__))
    import paint_tex as pt
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    pf = pt.preset('foliage', {})
    for ki, (name, k) in enumerate(grass_kinds().items()):
        atlas = np.zeros((GC * 2, GC * 4, 4), np.float32)
        nf = int(k.get('flower_cells', 0))
        for j in range(8):
            fl = j >= 8 - nf
            cc, a, hh = grass_clump(700 + j * 19 + ki * 101, k['olive'], k['cool'], k.get('flowers'), 3 if fl else 0, form=j)
            cc = bleed(cc, a)
            p = pt.paint(cc, normals(hh, 2.0), pf)
            r, c = j // 4, j % 4
            atlas[r * GC:(r + 1) * GC, c * GC:(c + 1) * GC, :3] = p
            atlas[r * GC:(r + 1) * GC, c * GC:(c + 1) * GC, 3] = a
        out = os.path.join(OUT, f"{k['atlas']}_atlas.png")
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


def card(b, c0, d, length, width, roll, arch, droop, j, H, R, segs_l=2, segs_w=2, mirror=False, crown=None):
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
            rowN.append(crown.normal(p, up, d) if crown else crown_normal(p, up, d, H))
            uw = (-w if mirror else w)
            rowU.append((u0 + (uw + 1) / 2 * du * 0.96 + du * 0.02, v0 + s * dv * 0.97 + dv * 0.015))
            rowC.append((crown.occl(p) if crown else occlusion(p, H, R), s, 1.0))
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


# (Low Ford lf1b, judge: from the play camera the old crowns were radial brush blobs, no tiers, no gaps, one flat teal.
# Rebuilt: whorls spaced as a spruce's are (0.5-0.85 m, closer toward the top), each a star of 4-7 drooping branches,
# each branch a main spray with side sprays off it (a fishbone seen from above, the ground and the tier below between
# its sprays); each vertex's openness baked from the sky (sky_bake), so a tier's top and its tips are lit and what
# stands under the tier above is dark.)
SPRUCE_FORM = {
    # gap: whorl spacing low/high (m, at the crown's foot; closer toward the top); nb: branches a whorl; pexp: the cone's
    # curve (>1 a drawn-out spire); droop: the branches' hang; sparse: the share of lower and middle branches lost;
    # wd: a spray card's width over its length
    'a': dict(gap=(0.46, 0.6), nb=(5, 7), pexp=0.95, droop=1.0, sparse=0.06, wd=0.6, pitch=1.0),
    'b': dict(gap=(0.55, 0.75), nb=(5, 7), pexp=0.8, droop=1.35, sparse=0.14, wd=0.58, pitch=1.2),
    'c': dict(gap=(0.62, 0.86), nb=(4, 6), pexp=1.18, droop=1.15, sparse=0.17, wd=0.55, pitch=0.9),
}


def spruce_prof(t, form):
    """The crown's radius share at t (0 its lowest whorl, 1 its top)."""
    return (1 - t) ** form['pexp'] * (0.8 + 0.2 * smooth(0, 0.12, t)) + 0.04


def spruce_branch(b, c0, az, L, t, lod, rng, form, H, R):
    """One branch from c0 (on the trunk) out along az, L long: falls from the trunk, droops, its tip turned up; one to
    three spray cards along it, flat-ish (the play camera sees their tops), and side sprays off it (lod 0, a long one at
    lod 1), so from above it is a fishbone of sprays with the dark below between them."""
    pitch = math.radians(7 + 20 * (1 - t)) * form['pitch'] + rng.normal(0, 0.05)
    dr = form['droop'] * (0.1 + 0.16 * (1 - t))
    hd = np.array([math.cos(az), math.sin(az), 0.0])

    def axis(s):
        return c0 + hd * L * s + np.array([0, 0, L * (-math.tan(pitch) * s - dr * s * s + 0.75 * dr * max(s - 0.55, 0) ** 2 / 0.2)])
    nc = (max(1, min(3, round(L / 0.85))), max(1, min(2, round(L / 1.4))), 1)[lod]
    wd = form['wd'] * (1.0, 1.15, 1.3)[lod]
    for ci in range(nc):
        s0, s1 = ci / nc, (ci + 1) / nc
        p0 = axis(max(s0 - 0.1 / nc, 0))
        d = axis(s1) - axis(s0)
        ln = np.linalg.norm(d) * rng.uniform(1.1, 1.3)
        d /= np.linalg.norm(d)
        roll = rng.normal(0, 0.18)
        if lod == 2 and rng.random() < 0.45:
            # (far: a share hang on edge, so from the side a far spruce is hanging sprays, not slats seen edge-on)
            roll = rng.choice([-1, 1]) * rng.uniform(0.9, 1.3)
        card(b, p0, d, ln, ln * wd * rng.uniform(0.85, 1.15), roll, 0.06, 0.06 + 0.06 * s1, int(rng.integers(0, 6)), H, R,
             segs_l=(2, 2, 1)[lod], segs_w=(2, 1, 1)[lod], mirror=bool(rng.random() < 0.5))
        # a pendant spray under it (the hanging branchlets: from the side a tier is a curtain, from above a thin line)
        if lod < 2 and rng.random() < (0.75, 0.5)[lod] and s1 > 0.3:
            sm = (s0 + s1) / 2
            dp = hd * rng.uniform(0.25, 0.45) + np.array([0, 0, -1.0])
            dp /= np.linalg.norm(dp)
            lp = ln * rng.uniform(0.38, 0.55)
            card(b, axis(sm) + np.array([0, 0, 0.04]), dp, lp, ln * rng.uniform(0.55, 0.75), rng.normal(0, 0.2), 0.04, 0.02,
                 int(rng.integers(0, 6)), H, R, segs_l=(2, 1, 1)[lod], segs_w=1, mirror=bool(rng.random() < 0.5))
        # the side sprays: off the middle of each card but a short last one, one or both sides, swept out and hanging lower
        if lod == 2 or (lod == 1 and L < 1.5) or (s1 > 0.97 and nc > 1):
            continue
        for sd in (-1, 1):
            if rng.random() > (0.8 if lod == 0 else 0.5):
                continue
            sm = (s0 + s1) / 2 + rng.uniform(-0.1, 0.1) / nc
            a2 = az + sd * math.radians(rng.uniform(42, 68))
            pt = math.radians(rng.uniform(14, 30))
            d2 = np.array([math.cos(a2) * math.cos(pt), math.sin(a2) * math.cos(pt), -math.sin(pt)])
            l2 = L * rng.uniform(0.3, 0.45) * (1 - 0.4 * sm)
            if l2 < 0.22:
                continue
            card(b, axis(sm), d2, l2, l2 * wd * 0.85, rng.normal(0, 0.25), 0.05, 0.1, int(rng.integers(0, 6)), H, R,
                 segs_l=(2, 1, 1)[lod], segs_w=1, mirror=bool(rng.random() < 0.5))


def sky_bake(b, H, R, vox=0.2):
    """Each leaf vertex's openness to the sky (13 rays within 60 degrees of the zenith through a voxel grid of the
    crown's own sprays), its colour's r 0.42-1, and its normal turned with it: open, up (a tier's lit top, its tips);
    shut in, out from the trunk and down (the dark under the tier above). The bark keeps its own."""
    V = np.array(b.v, np.float64)
    F = np.array(b.f)
    UV = np.array(b.uv)
    leafq = UV[F[:, 0], 0] < BU
    Q = V[F[leafq]]
    cen = Q.mean(1)
    area = np.linalg.norm(np.cross(Q[:, 2] - Q[:, 0], Q[:, 3] - Q[:, 1]), axis=1) / 2
    lo = np.array([-R - 1.6, -R - 1.6, -0.6])
    dims = np.ceil(np.array([2 * R + 3.2, 2 * R + 3.2, H + 1.6]) / vox).astype(int)
    dens = np.zeros(dims)
    ix = np.clip(((cen - lo) / vox).astype(int), 0, dims - 1)
    np.add.at(dens, (ix[:, 0], ix[:, 1], ix[:, 2]), area)
    # (spread over its neighbours: the quads are coarser than the grid)
    k = np.array([0.25, 0.5, 0.25])
    for ax in (0, 1, 2):
        dens = np.apply_along_axis(lambda v: np.convolve(v, k, 'same'), ax, dens)
    # (a card's spray covers ~55% of it)
    tau_v = dens / vox ** 2 * 0.55 * BAKE_K
    dirs, w = [np.array([0, 0, 1.0])], [1.0]
    for el, n in ((30, 6), (58, 6)):
        for i in range(n):
            a = i * 2 * math.pi / n + (0.5 if el > 40 else 0)
            dirs.append(np.array([math.sin(math.radians(el)) * math.cos(a), math.sin(math.radians(el)) * math.sin(a), math.cos(math.radians(el))]))
            w.append(math.cos(math.radians(el)))
    leafv = UV[:, 0] < BU
    P = V[leafv]
    tot = np.zeros(len(P))
    nsteps = int((H + 2) / vox / 0.5) + 2
    for d, wi in zip(dirs, w):
        tau = np.zeros(len(P))
        for st in range(1, nsteps):
            q = P + d * (0.22 + st * vox)
            ii = ((q - lo) / vox).astype(int)
            ok = np.all((ii >= 0) & (ii < dims), axis=1)
            if not ok.any():
                break
            tau[ok] += tau_v[ii[ok, 0], ii[ok, 1], ii[ok, 2]]
        tot += wi * np.exp(-tau)
    # (lifted: a tier's open top as light as the old crown's skin, judge lf1b r1 at 1:1: the stand went dark)
    op = (tot / sum(w)) ** 0.6
    # the geometric normal of each vertex's card (its upper side up)
    gn = np.zeros_like(V)
    for f in F:
        n = np.cross(V[f[2]] - V[f[0]], V[f[3]] - V[f[1]])
        for i in f:
            gn[i] += n
    gn /= np.maximum(np.linalg.norm(gn, axis=1, keepdims=True), 1e-9)
    gn *= np.where(gn[:, 2:3] < 0, -1, 1)
    idx = np.nonzero(leafv)[0]
    for o, i in zip(op, idx):
        p = V[i]
        r = np.array([p[0], p[1], 0.0]); lr = np.linalg.norm(r)
        r = r / lr if lr > 0.1 else np.array([1.0, 0, 0])
        n = r * (0.55 - 0.15 * o) + np.array([0, 0, -0.15 + 1.0 * o]) + gn[i] * 0.3
        b.n[i] = n / np.linalg.norm(n)
        c = b.c[i]
        b.c[i] = (0.42 + 0.58 * float(o), c[1], c[2])
    return op


BAKE_K = 0.8


def spruce(H, R, seed, lod, form=None):
    """lod 0: whorls as a spruce's, each branch a main spray with side sprays; 1: the same whorls, fewer, larger cards;
    2: every other whorl, a card a branch. Openness baked from the sky."""
    form = form or SPRUCE_FORM['b']
    rng = np.random.default_rng(seed * 3 + lod)
    b = Build()
    rb = 0.022 * H + 0.05
    trunk(b, H - 0.55, rb, (10, 7, 5)[lod], (10, 5, 2)[lod], np.random.default_rng(seed + 1))
    hs = 0.55 + 0.03 * H
    # the whorls: the same heights at every LOD (lod 2 every other one), closer toward the top
    rw = np.random.default_rng(seed + 11)
    whorls, h = [], hs
    while h < H - 0.35:
        whorls.append(h)
        t = (h - hs) / (H - hs)
        h += rw.uniform(*form['gap']) * (1 - 0.5 * t)
    if lod == 2:
        whorls = whorls[::2]
    az0 = rng.uniform(0, 6.28)
    for wi, h in enumerate(whorls):
        t = (h - hs) / (H - hs)
        prof = spruce_prof(t, form) * rng.uniform(0.88, 1.1)
        nb = int(rng.integers(*form['nb'])) if t < 0.8 else int(rng.integers(4, 6))
        if lod == 2:
            nb = min(nb, 5)
        az0 += 2.4
        for k in range(nb):
            if 0.08 < t < 0.75 and rng.random() < form['sparse']:
                continue
            az = az0 + k * 2 * math.pi / nb + rng.normal(0, 0.25)
            L = R * prof * rng.uniform(0.8, 1.12) * (1.06 if lod == 2 else 1.0)
            if L < (0.25 if t < 0.85 else 0.14):
                continue
            c0 = np.array([math.cos(az) * rb * (1 - t) * 0.6, math.sin(az) * rb * (1 - t) * 0.6, h])
            spruce_branch(b, c0, az, L, t, lod, rng, form, H, R)
        # (between whorls, a few short inner branches, under the tier above: the crown's dark inner volume, no bare pole)
        if lod == 0 and wi + 1 < len(whorls) and t < 0.85:
            h2 = (h + whorls[wi + 1]) / 2
            for k in range(int(rng.integers(2, 4))):
                az = rng.uniform(0, 6.28)
                L = R * prof * rng.uniform(0.4, 0.6)
                if L < 0.3:
                    continue
                d = np.array([math.cos(az), math.sin(az), -0.35]); d /= np.linalg.norm(d)
                card(b, np.array([0, 0, h2]), d, L * 1.1, L * 0.7, rng.normal(0, 0.3), 0.06, 0.12, int(rng.integers(0, 6)), H, R,
                     segs_l=2, segs_w=1, mirror=bool(rng.random() < 0.5))
    # the leader: two crossed upright cards, narrow
    for a in (0.3, 0.3 + math.pi / 2):
        side = np.array([math.cos(a), math.sin(a), 0])
        u0, v0, du, dv = cell_uv(int(rng.integers(0, 6)))
        P = [[np.array([0, 0, H - 0.6]) + side * w * 0.11 * (1 - 0.7 * s) + np.array([0, 0, 0.95 * s]) for w in (-1, 1)] for s in (0, 1)]
        N = [[crown_normal(np.array([side[0] * w, side[1] * w, H]), np.array([0, 0, 1.0]), side, H) for w in (-1, 1)] for s in (0, 1)]
        UV = [[(u0 + (w + 1) / 2 * du, v0 + s * dv) for w in (-1, 1)] for s in (0, 1)]
        b.quad_grid(P, N, UV, 1, 1, [[(1.0, 1.0, 0.0)] * 2] * 2)
    sky_bake(b, H, R)
    return b


def shadow_proxy(H, R, seed, form=None):
    """What the tree casts (shadows only): a thin leaning trunk and six to eight tiers, each a star of four to seven
    separate drooping blades (jagged-edged, narrowing to their tips, one now and then missing), so its shadow on the
    ground and the water is a stepped, ragged spruce with light between the branches' ends, not a disc or a cone. Solid
    (its uvs in the bark strip: the shadow pass stays opaque, no alpha test). Each tree its own."""
    form = form or SPRUCE_FORM['b']
    rng = np.random.default_rng(seed + 5)
    b = Build()
    uv = (BU + 0.1, 0.5)
    lean, laz = math.tan(math.radians(rng.uniform(4, 8))), rng.uniform(0, 6.28)
    ld = np.array([math.cos(laz), math.sin(laz), 0.0])
    bow = rng.uniform(0.25, 0.45)

    def axis(z):
        return ld * lean * z * (1 - bow * z / H)
    tube(b, [axis(z) + np.array([0, 0, z]) for z in np.linspace(0, 0.9 * H, 4)],
         [0.16 * math.sqrt(H / 8), 0.055 * math.sqrt(H / 8), 0.035 * math.sqrt(H / 8), 0.02], 5)
    hs = 0.55 + 0.03 * H
    tiers = int(rng.integers(6, 8)) + (1 if H > 9 else 0)
    hts = hs + (H - hs) * (1 - (1 - np.arange(tiers) / tiers) ** 1.25) + rng.normal(0, 0.08, tiers)
    # (lf3b, judge lf2 #5: at dawn the old blades' shadows were smooth spear blades, the tiers merged into one leaf)
    # every other tier shorter, so the outline steps whorl by whorl; the blades narrower, a notch each side at the
    # middle (one row more: about +30% tris), a shallower hang with the tip turned up, and more of them missing, so the
    # low sun shows light between tiers and between branches
    for k, h0 in enumerate(hts):
        t = (h0 - hs) / (H - hs)
        rt = R * spruce_prof(min(max(t, 0), 1), form) * 0.97 * (1.0 if k % 2 == 0 else rng.uniform(0.7, 0.8))
        n = int(rng.integers(5, 8)) if t < 0.75 else 4
        az0 = rng.uniform(0, 6.28)
        c0 = axis(h0) + np.array([0, 0, h0])
        for i in range(n):
            if t < 0.75 and rng.random() < 0.16:
                continue
            az = az0 + i * 2 * math.pi / n + rng.normal(0, 0.22)
            hd = np.array([math.cos(az), math.sin(az), 0.0]); sd = np.array([-hd[1], hd[0], 0.0])
            r = rt * rng.uniform(0.8, 1.15)
            dr = 0.17 + 0.17 * (1 - t)
            P = []
            for s, hw in ((0.0, 0.08), (0.3, rng.uniform(0.22, 0.29)), (0.5, rng.uniform(0.08, 0.12)), (0.74, rng.uniform(0.19, 0.26)), (1.0, rng.uniform(0.02, 0.05))):
                cc = c0 + hd * r * s + np.array([0, 0, -r * (dr * s + 0.2 * s * s - 0.06 * max(s - 0.7, 0) ** 2 / 0.09)])
                j = rng.uniform(-0.08, 0.08) * r
                P.append([cc - sd * (hw * r + j), cc + sd * (hw * r - j)])
            N = [[np.array([0, 0, 1.0])] * 2] * 5
            UV = [[uv] * 2] * 5
            b.quad_grid(P, N, UV, 1, 4)
    return b


# ---------------------------------------------------------------- the alder (the kit's CommonTree_1-5)

# sizes: as tall as the kit's CommonTrees they stand for (6.8-7.4 m: a, b; 9.2 m: c); a and b
# multi-stemmed, as alders by water mostly are
ALDER = {
    'a': dict(H=7.0, R=2.2, seed=13, stems=2),
    'b': dict(H=7.7, R=2.45, seed=29, stems=3),
    'c': dict(H=9.2, R=2.3, seed=41, stems=1),
}


class Oval:
    """An alder's crown: an oval round (0, 0, zc), R across and hz up. Normals out from its middle
    (and up), so it shades as one mass; how open a point is, by how far out in the oval it stands."""
    def __init__(self, R, zc, hz):
        self.R, self.zc, self.hz = R, zc, hz

    def rel(self, p):
        return np.array([p[0] / self.R, p[1] / self.R, (p[2] - self.zc) / self.hz])

    def normal(self, p, cn, d):
        q = self.rel(p)
        ln = np.linalg.norm(q)
        o = q / ln if ln > 0.1 else np.array([0, 0, 1.0])
        n = o * 0.6 + np.array([0, 0, 0.5]) + cn * 0.3
        return n / np.linalg.norm(n)

    def occl(self, p):
        return 0.35 + 0.65 * float(smooth(0.25, 0.95, np.linalg.norm(self.rel(p))))


def tube(b, pts, radii, sides, occ=0.6):
    """A bark tube along pts (its radius at each), the bark strip round it, v along it."""
    pts = [np.asarray(p, np.float64) for p in pts]
    P, N, UV = [], [], []
    Ltot = sum(np.linalg.norm(pts[k] - pts[k - 1]) for k in range(1, len(pts)))
    L = 0.0
    for k, p in enumerate(pts):
        t = pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]
        t /= np.linalg.norm(t)
        ref = np.array([1.0, 0, 0]) if abs(t[0]) < 0.9 else np.array([0, 1.0, 0])
        a1 = np.cross(t, ref); a1 /= np.linalg.norm(a1)
        a2 = np.cross(t, a1)
        if k:
            L += np.linalg.norm(p - pts[k - 1])
        rowP, rowN, rowU = [], [], []
        for i in range(sides + 1):
            a = i / sides * 2 * math.pi
            nr = a1 * math.cos(a) + a2 * math.sin(a)
            rowP.append(p + nr * radii[k]); rowN.append(nr)
            rowU.append((BU + (1 - BU) * i / sides * 0.995, 0.01 + 0.98 * L / max(Ltot, 1e-6)))
        P.append(rowP); N.append(rowN); UV.append(rowU)
    b.quad_grid(P, N, UV, sides, len(pts) - 1, [[(occ, 0.0, 0.0)] * (sides + 1)] * len(pts))


def alder_stems(H, seed, stems):
    """The stems (each a list of points and radii): one to three from one foot, leaning out a little
    and bending, the first the tallest."""
    rng = np.random.default_rng(seed + 3)
    out = []
    az0 = rng.uniform(0, 6.28)
    r0 = (0.17 if stems == 1 else 0.115) * math.sqrt(H / 8)
    for k in range(stems):
        az = az0 + k * 2 * math.pi / stems + rng.normal(0, 0.3)
        lean = math.radians(rng.uniform(5, 11) if stems > 1 else rng.uniform(0, 3))
        top = H * (0.86 if k == 0 else rng.uniform(0.7, 0.82))
        ph = rng.uniform(0, 6.28)
        dx, dy = math.cos(az), math.sin(az)
        off = 0.1 if stems > 1 else 0.0
        pts, rad = [], []
        for i in range(8):
            f = i / 7
            z = -0.2 + (top + 0.2) * f
            w = 0.12 * math.sin(f * 3.1 + ph) * f            # (a slow bend)
            pts.append(np.array([dx * (off + math.tan(lean) * max(z, 0)) - dy * w, dy * (off + math.tan(lean) * max(z, 0)) + dx * w, z]))
            rad.append(max(0.022, r0 * (1 - 0.82 * f) * (1 + 0.45 * math.exp(-max(z, 0) / 0.3))))
        out.append((pts, rad))
    return out


def alder(H, R, seed, lod, stems):
    """lod 0: the stems, main branches and some 64 leaf-clump branchlets, two cards each; 1: fewer,
    larger cards and two branches a stem; 2: a dozen big cards on the stems. The crown a rounded
    oval from a quarter of the height up; each card from inside the crown out to its skin (its
    clumps at the skin: lit tips, dark core)."""
    rng = np.random.default_rng(seed)
    b = Build()
    zc, hz = 0.62 * H, 0.38 * H
    crown = Oval(R, zc, hz)
    sts = alder_stems(H, seed, stems)
    for pts, rad in sts:
        tube(b, pts, rad, (7, 5, 4)[lod])
    # main branches, spreading up and out from the stems
    for pts, rad in sts:
        for i in range((int(rng.integers(3, 6)), 2, 0)[lod]):
            f = rng.uniform(0.38, 0.8)
            k = min(int(f * 7), 6); g = f * 7 - k
            p0 = pts[k] * (1 - g) + pts[k + 1] * g
            az, el = rng.uniform(0, 6.28), math.radians(rng.uniform(25, 55))
            d = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)])
            rr = R * math.sqrt(max(0.05, 1 - ((p0[2] - zc) / hz) ** 2))
            L = max(0.6, rr * rng.uniform(0.6, 0.85))
            r = 0.05 * math.sqrt(H / 8)
            tube(b, [p0, p0 + d * L * 0.5 + np.array([0, 0, 0.08 * L]), p0 + d * L], [r, r * 0.6, r * 0.25], (4, 3, 3)[lod], occ=0.5)
    # the leaf-clump branchlets: spread over the crown's skin (a golden-angle spiral, the bottom left open)
    nc = (64, 30, 13)[lod]
    for i in range(nc):
        zf = 1 - 1.75 * (i + 0.5) / nc
        a = i * 2.39996 + rng.normal(0, 0.25)
        rxy = math.sqrt(max(0.0, 1 - zf * zf))
        o = np.array([rxy * math.cos(a), rxy * math.sin(a), zf])
        f = rng.uniform(0.45, 0.7) if lod == 0 and rng.random() < 0.2 else rng.uniform(0.74, 1.0)
        tip = np.array([0, 0, zc]) + o * np.array([R, R, hz]) * f
        dout = o * np.array([1, 1, 0.5]) + np.array([0, 0, 0.3])
        dout /= np.linalg.norm(dout)
        ln = (1.7, 2.3, 3.1)[lod] * rng.uniform(0.85, 1.15) * math.sqrt(H / 8)
        wd = ln * rng.uniform(0.75, 0.95)
        c0 = tip - dout * ln * 0.8
        roll, j = rng.uniform(-0.6, 0.6), int(rng.integers(0, 6))
        card(b, c0, dout, ln, wd, roll, 0.1, 0.16, j, H, R, segs_l=(3, 2, 1)[lod], segs_w=(2, 2, 1)[lod],
             mirror=bool(rng.random() < 0.5), crown=crown)
        if lod == 0:
            r2 = roll + rng.choice([-1, 1]) * math.radians(rng.uniform(20, 30))
            card(b, c0 + dout * ln * 0.06, dout, ln * rng.uniform(0.82, 0.95), wd * rng.uniform(0.85, 1.0), r2, 0.12, 0.18, (j + int(rng.integers(1, 6))) % 6, H, R,
                 segs_l=2, segs_w=2, mirror=bool(rng.random() < 0.5), crown=crown)
    return b


def alder_proxy(H, R, seed, stems):
    """What the alder casts: its crown as a core and five to seven lumps (each a clump mass about a
    metre across, the radius jittered), so its shadow is scalloped, not one smooth blob, at 0.7 of
    the crown; and its stems below the crown."""
    rng = np.random.default_rng(seed + 5)
    b = Build()
    zc, hz = 0.62 * H, 0.38 * H
    uv = (BU + 0.1, 0.5)

    def lump(c, rx, rz, nu=9, nv=5):
        P, N, UV = [], [], []
        for jv in range(nv + 1):
            th = math.pi * jv / nv
            row, rowN = [], []
            for iu in range(nu + 1):
                ph = 2 * math.pi * (iu % nu) / nu
                o = np.array([math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)])
                row.append(o)
            P.append(row)
        jit = rng.uniform(0.82, 1.18, (nv + 1, nu))
        P = [[c + o * np.array([rx, rx, rz]) * (jit[jv, iu % nu] if 0 < jv < nv else 1.0) for iu, o in enumerate(row)] for jv, row in enumerate(P)]
        N = [[np.array([0, 0, 1.0])] * (nu + 1)] * (nv + 1)
        UV = [[uv] * (nu + 1)] * (nv + 1)
        b.quad_grid(P, N, UV, nu, nv)

    # (0.86 of the crown, judge E4c: the cards' outer halves out of it, so a crown's sunward top reads lit)
    # (and low in it, its top well under the crown's: a low sun over the proxy's top shadowed the crown's whole
    # top, which the camera sees)
    # (lf3b: at dawn the big core and its five to seven lumps cast one smooth pointed blade, judge lf2 #5: a round lump
    # stretches along a low sun into a blade, and lumps round a core fill it) eight to ten flattened clump masses at
    # heights through the crown, each inside 0.9 of it: a flat mass casts its own shape, so under a low sun the masses at
    # different heights fall apart along the shadow, clumps with light between; under a high one they still cover it
    nl = int(rng.integers(8, 11))
    a0 = rng.uniform(0, 6.28)
    for k in range(nl):
        zf = (k + 0.5) / nl * 1.3 - 0.7 + rng.normal(0, 0.06)
        rxy = math.sqrt(max(1 - zf * zf, 0.05))
        a = a0 + k * 2.39996 + rng.normal(0, 0.3)
        off = rng.uniform(0.25, 0.5) * rxy
        rr = min(rng.uniform(0.34, 0.44), 0.9 * rxy - off + 0.12) * R
        lump(np.array([math.cos(a) * off * R, math.sin(a) * off * R, zc + zf * hz]), max(rr, 0.2 * R), rng.uniform(0.12, 0.17) * hz, 7, 3)
    for pts, rad in alder_stems(H, seed, stems):
        tube(b, pts[:4], rad[:4], 4)
    return b


# ---------------------------------------------------------------- step C (E4f): snags, bushes, bracken

# Each species a preset: its pieces (sizes and looks; packed in one file, told apart by COLOR.a) and their shapes.
# The runtime's rules (which kit pieces they replace, LODs, cells, shadow) are godot/data/flora_species.json.
SNAG = {
    # (as tall as the kit's dead trees they stand for: DeadTree_1 9.2 m, 2-4 11.2-12.9 m, 5 16.1 m)
    'snag_a': dict(H=9.2, seed=51, top='snapped'),
    'snag_b': dict(H=12.3, seed=63, top='thin'),
    'snag_c': dict(H=16.0, seed=77, top='snapped'),
}
BUSH = {
    # (the kit's Bush_Common stands 1.35 m, 2 m across; hazel for it, elder for its flowering one)
    'hazel_a': dict(H=1.05, R=0.85, seed=81, look='hazel', proxy=False),
    'hazel_b': dict(H=1.55, R=1.15, seed=93, look='hazel', proxy=True),
    'elder_a': dict(H=1.15, R=0.9, seed=105, look='elder', proxy=False),
    'elder_b': dict(H=1.7, R=1.2, seed=117, look='elder', proxy=True),
}
BRACKEN = {
    # (as the kit's: Fern_1 a spreading patch 9 m across and 2.4 m tall before its placements' x0.57; Plant_1_Big one
    # upright clump 3.7 m tall before their x0.3)
    'bracken_a': dict(H=2.4, R=4.4, seed=131, clumps=5, fronds=(6, 4, 2), ln=(2.4, 3.0), el=(38, 60)),
    'bracken_b': dict(H=3.7, R=1.5, seed=143, clumps=1, fronds=(9, 6, 3), ln=(3.3, 3.9), el=(55, 74)),
}
PACKED = {'snag': SNAG, 'bush': BUSH, 'bracken': BRACKEN}


class Dome:
    """A bush's (or a bracken clump's) mass: an oval round (0, 0, zc), R across, hz up. Normals out from its middle and
    up (it shades as one mass); how open a point is, by how far out in it, and darker toward the ground (its base)."""
    def __init__(self, R, zc, hz, H):
        self.R, self.zc, self.hz, self.H = R, zc, hz, H

    def rel(self, p):
        return np.array([p[0] / self.R, p[1] / self.R, (p[2] - self.zc) / self.hz])

    def normal(self, p, cn, d):
        q = self.rel(p)
        ln = np.linalg.norm(q)
        o = q / ln if ln > 0.1 else np.array([0, 0, 1.0])
        n = o * 0.6 + np.array([0, 0, 0.55]) + cn * 0.3
        return n / np.linalg.norm(n)

    def occl(self, p):
        o = 0.35 + 0.65 * float(smooth(0.2, 0.95, np.linalg.norm(self.rel(p))))
        return o * (0.4 + 0.6 * float(smooth(0.0, 0.55 * self.H, p[2])))


def snag_trunk(b, H, rb, sides, rings, rng, top):
    """The dead trunk: tapering, leaning, bent a little; its foot flared and dark (the base); its top snapped (a ragged
    ring of splinters round a sunken break) or thinned to a bent spike."""
    lean = rng.normal(0, 0.035, 2)
    bendp = rng.uniform(0, 6.28)
    Ht = H * (1.0 if top == 'thin' else 1.0)
    P, N, UV, C = [], [], [], []
    for k in range(rings + 1):
        t = k / rings
        z = -0.25 + (Ht + 0.25) * t
        if top == 'thin':
            rad = max(0.012, rb * (1 - t) ** 0.95)
        else:
            rad = rb * (1 - 0.72 * t) ** 1.1
        flare = 1 + 0.6 * math.exp(-max(z, 0) / 0.4)
        off = np.array([lean[0] * z, lean[1] * z, 0]) + 0.12 * math.sin(t * 2.5 + bendp) * t * np.array([math.cos(bendp), math.sin(bendp), 0])
        rowP, rowN, rowU, rowC = [], [], [], []
        for i in range(sides + 1):
            a = i / sides * 2 * math.pi
            bump = 1 + 0.2 * math.cos(a * 3 + 0.4) * math.exp(-max(z, 0) / 0.5)
            zz = z
            if top != 'thin' and k == rings:
                zz = z + (rng.uniform(0.15, 0.7) if i % 2 == 0 else rng.uniform(-0.1, 0.15)) * (1 if i < sides else 0)
            rr = rad * flare * bump
            rowP.append(np.array([math.cos(a) * rr, math.sin(a) * rr, zz]) + off)
            rowN.append(np.array([math.cos(a), math.sin(a), 0.12]) / 1.007)
            rowU.append((BU + (1 - BU) * i / sides * 0.995, 0.01 + 0.98 * (z + 0.25) / (Ht + 0.5)))
            rowC.append((0.05 + 0.95 * float(smooth(-0.1, 1.4, zz)), 0.0, 0.0))
        if top != 'thin' and k == rings:
            rowP[-1] = rowP[0]
        P.append(rowP); N.append(rowN); UV.append(rowU); C.append(rowC)
    b.quad_grid(P, N, UV, sides, rings, C)
    top_c = (P[-1][0] + P[-1][sides // 2]) / 2
    if top != 'thin':
        # the break: the splinters' ring down to a sunken middle (pale fresh-ish wood: the strip's light grain)
        cz = top_c + np.array([0, 0, -0.08])
        Pc = [P[-1], [cz] * (sides + 1)]
        Nc = [[np.array([0, 0, 1.0])] * (sides + 1)] * 2
        Uc = [[(BU + 0.12, 0.6)] * (sides + 1)] * 2
        b.quad_grid(Pc, Nc, Uc, sides, 1, [[(1.0, 0.0, 0.0)] * (sides + 1)] * 2)
    return lambda z: np.array([lean[0] * z, lean[1] * z, 0]) + 0.12 * math.sin(z / Ht * 2.5 + bendp) * (z / Ht) * np.array([math.cos(bendp), math.sin(bendp), 0])


def snag(H, seed, lod, top, proxy=False):
    """A dead spruce: the grey trunk and whorls of broken stubs, short and snapped low down, longer and drooping in the
    middle (a few forked), short and upturned near the top. lod 0 every whorl, 4-sided stubs; 1 the longer stubs, 3
    sides; 2 the trunk and the longest few. proxy: the trunk and the longer stubs (thin), so its shadow is branchy."""
    rng = np.random.default_rng(seed)
    b = Build()
    rb = 0.02 * H + 0.07
    sides, rings = ((10, 12), (7, 6), (5, 3))[lod] if not proxy else (5, 3)
    axis = snag_trunk(b, H, rb, sides, rings, np.random.default_rng(seed + 1), top)
    h = 0.9 + rng.uniform(0, 0.3)
    az0 = rng.uniform(0, 6.28)
    stubs = []
    while h < H * (0.93 if top == 'thin' else 0.97):
        t = h / H
        for k in range(int(rng.integers(2, 5))):
            az = az0 + k * 2 * math.pi / 4 + rng.normal(0, 0.35)
            if t < 0.3:
                L = rng.uniform(0.12, 0.45)                       # snapped low down
                pitch = rng.uniform(-25, 5)
            elif t < 0.75:
                L = rng.uniform(0.25, 1.5) * (1.2 - 0.4 * t)       # the middle: some long, drooping
                pitch = rng.uniform(-40, -8)
            else:
                L = rng.uniform(0.2, 0.75)
                pitch = rng.uniform(-10, 25)
            stubs.append((h, az, L, math.radians(pitch), rng.random() < 0.3 and L > 0.7))
        h += rng.uniform(0.45, 0.85)
        az0 += 2.4
    for h, az, L, pitch, fork in stubs:
        if proxy and L < 0.6:
            continue
        if lod == 1 and L < 0.45 and not proxy:
            continue
        if lod == 2 and L < 0.9 and not proxy:
            continue
        t = h / H
        rt = max(0.018, rb * (1 - 0.72 * t) * 0.85)
        d = np.array([math.cos(az) * math.cos(pitch), math.sin(az) * math.cos(pitch), math.sin(pitch)])
        p0 = axis(h) + np.array([0, 0, h]) + np.array([math.cos(az), math.sin(az), 0]) * rt * 0.5
        r0 = max(0.02, 0.03 + 0.05 * (L / 1.5)) * (1 + 0.3 * (1 - t))
        droop = np.array([0, 0, -0.12 * L * L])
        pts = [p0, p0 + d * L * 0.55 + droop * 0.3, p0 + d * L + droop]
        ns = 3 if (lod or proxy) else 4
        tube(b, pts if lod == 0 and not proxy else [pts[0], pts[2]], [r0, r0 * 0.7, r0 * 0.45] if lod == 0 and not proxy else [r0, r0 * 0.45], ns, occ=0.85)
        if fork and lod == 0 and not proxy:
            q = pts[1]
            d2 = d + np.array([math.cos(az + 1.4), math.sin(az + 1.4), 0.2]) * 0.6
            d2 /= np.linalg.norm(d2)
            tube(b, [q, q + d2 * L * 0.45], [r0 * 0.55, r0 * 0.25], 3, occ=0.85)
    return b


def lump(b, rng, c, rx, rz, nu=9, nv=5):
    """A rough ellipsoid (a shadow proxy's mass), its radius jittered."""
    uv = (BU + 0.1, 0.5)
    P = []
    jit = rng.uniform(0.82, 1.18, (nv + 1, nu))
    for jv in range(nv + 1):
        th = math.pi * jv / nv
        row = []
        for iu in range(nu + 1):
            ph = 2 * math.pi * (iu % nu) / nu
            o = np.array([math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)])
            row.append(c + o * np.array([rx, rx, rz]) * (jit[jv, iu % nu] if 0 < jv < nv else 1.0))
        P.append(row)
    N = [[np.array([0, 0, 1.0])] * (nu + 1)] * (nv + 1)
    UV = [[uv] * (nu + 1)] * (nv + 1)
    b.quad_grid(P, N, UV, nu, nv)


def bush(H, R, seed, lod, look):
    """A hazel or an elder: a low multi-stemmed dome of leaf-clump cards (the alder's clump, a size larger in its cell),
    the stems showing low down, its base dark. lod 0: some 10-14 clumps, two crossed cards each, and the stems; 1:
    fewer, larger, one card each; 2: four big cards."""
    rng = np.random.default_rng(seed)
    b = Build()
    zc, hz = 0.45 * H, 0.55 * H
    dome = Dome(R, zc, hz, H)
    j0 = 0 if look == 'hazel' else 3
    if lod == 0:
        for k in range(int(rng.integers(4, 7))):
            az = rng.uniform(0, 6.28); el = math.radians(rng.uniform(55, 80))
            d = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)])
            p0 = np.array([math.cos(az), math.sin(az), 0]) * rng.uniform(0.02, 0.12) + np.array([0, 0, -0.1])
            L = H * rng.uniform(0.55, 0.8)
            tube(b, [p0, p0 + d * L * 0.5, p0 + d * L], [0.03, 0.022, 0.012], 3, occ=0.4)
    nc = max(3, round((12, 7, 4)[lod] * (R / 1.0) ** 0.6))
    for i in range(nc):
        zf = 1 - 1.45 * (i + 0.5) / nc
        a = i * 2.39996 + rng.normal(0, 0.3)
        rxy = math.sqrt(max(0.0, 1 - zf * zf))
        o = np.array([rxy * math.cos(a), rxy * math.sin(a), zf])
        tip = np.array([0, 0, zc]) + o * np.array([R, R, hz]) * rng.uniform(0.82, 1.0)
        dout = o * np.array([1, 1, 0.6]) + np.array([0, 0, 0.35])
        dout /= np.linalg.norm(dout)
        ln = (0.95, 1.2, 1.55)[lod] * R * rng.uniform(0.85, 1.15)
        wd = ln * rng.uniform(0.8, 0.95)
        c0 = tip - dout * ln * 0.78
        c0[2] = max(c0[2], -0.05)
        roll, j = rng.uniform(-0.6, 0.6), j0 + int(rng.integers(0, 3))
        card(b, c0, dout, ln, wd, roll, 0.1, 0.12, j, H, R, segs_l=(2, 2, 1)[lod], segs_w=(2, 1, 1)[lod],
             mirror=bool(rng.random() < 0.5), crown=dome)
        if lod == 0:
            r2 = roll + rng.choice([-1, 1]) * math.radians(rng.uniform(25, 40))
            card(b, c0 + dout * ln * 0.05, dout, ln * rng.uniform(0.8, 0.95), wd * rng.uniform(0.85, 1.0), r2, 0.12, 0.14, j0 + (j - j0 + int(rng.integers(1, 3))) % 3, H, R,
                 segs_l=2, segs_w=1, mirror=bool(rng.random() < 0.5), crown=dome)
    return b


def bush_proxy(H, R, seed):
    rng = np.random.default_rng(seed + 5)
    b = Build()
    lump(b, rng, np.array([0, 0, 0.42 * H]), 0.62 * R, 0.42 * H, 8, 4)
    for k in range(3):
        a = rng.uniform(0, 6.28)
        lump(b, rng, np.array([math.cos(a) * 0.45 * R, math.sin(a) * 0.45 * R, 0.4 * H]), 0.42 * R, 0.32 * H, 6, 3)
    return b


def bracken(H, R, seed, lod, clumps, fronds, ln, el):
    """Bracken: clumps of fronds as cards, each from the ground up and out on its stipe, the blade arching over (a
    frond's card: its foot the stipe, dark; the clump's base dark under the blades). Several clumps spread through a
    patch (Fern_1's) or one upright clump (Plant_1_Big's)."""
    rng = np.random.default_rng(seed)
    b = Build()
    cs = [np.zeros(3)]
    while len(cs) < clumps:
        a, r = rng.uniform(0, 6.28), R * rng.uniform(0.25, 0.55)
        c = np.array([math.cos(a) * r, math.sin(a) * r, 0])
        if all(np.linalg.norm(c - q) > R * 0.3 for q in cs):
            cs.append(c)
    for ci, c in enumerate(cs):
        dome = Dome(R * (0.45 if clumps > 1 else 0.9), 0.0, H, H)
        nf = fronds[lod] + (int(rng.integers(-1, 2)) if lod == 0 else 0)
        az0 = rng.uniform(0, 6.28)
        for k in range(nf):
            az = az0 + k * 2 * math.pi / nf + rng.normal(0, 0.3)
            e = math.radians(rng.uniform(*el))
            d = np.array([math.cos(az) * math.cos(e), math.sin(az) * math.cos(e), math.sin(e)])
            L = rng.uniform(*ln) * (1.12 if lod else 1.0)
            wd = L * rng.uniform(0.5, 0.6)
            c0 = c + np.array([math.cos(az), math.sin(az), 0]) * rng.uniform(0, 0.12) * R / 4 + np.array([0, 0, -0.05])

            class Local:
                # (the clump's own mass: normals out from its foot and up, darker toward the ground)
                def normal(self, p, cn, dd, c=c, dome=dome):
                    return dome.normal(p - np.array([c[0], c[1], 0]), cn, dd)

                def occl(self, p, c=c, dome=dome):
                    return dome.occl(p - np.array([c[0], c[1], 0]))
            # (the blade lies over: rolled flat-ish, the front its upper side)
            card(b, c0, d, L, wd, rng.uniform(-0.35, 0.35), 0.05, rng.uniform(0.28, 0.42), int(rng.integers(0, 6)), H, R,
                 segs_l=(3, 2, 1)[lod], segs_w=(2, 1, 1)[lod], mirror=bool(rng.random() < 0.5), crown=Local())
    return b


def piece_build(species, prm, lod, proxy=False):
    """One packed species' piece at a LOD (or its proxy, or None if it casts none)."""
    if species == 'snag':
        return snag(prm['H'], prm['seed'], 2 if proxy else lod, prm['top'], proxy=proxy)
    if species == 'bush':
        if proxy:
            return bush_proxy(prm['H'], prm['R'], prm['seed']) if prm['proxy'] else None
        return bush(prm['H'], prm['R'], prm['seed'], lod, prm['look'])
    if species == 'bracken':
        return None if proxy else bracken(prm['H'], prm['R'], prm['seed'], lod, prm['clumps'], prm['fronds'], prm['ln'], prm['el'])


def pack_into(dst, src, alpha):
    """src's geometry appended to dst, each vertex's COLOR.a alpha (a packed file's piece: (index + 0.5) / 8)."""
    o = len(dst.v)
    dst.v += src.v; dst.n += src.n; dst.uv += src.uv
    dst.c += [(c[0], c[1], c[2], alpha) for c in src.c]
    dst.f += [tuple(i + o for i in f) for f in src.f]


def mesh(species):
    import bpy
    os.makedirs(OUT, exist_ok=True)
    img_path = os.path.join(OUT, f'{species}_atlas.png')
    # (a packed species: one file, its pieces told apart by COLOR.a; else a file per piece)
    jobs = [(species, PACKED[species])] if species in PACKED else [(f'{species}_{size}', prm) for size, prm in (SPRUCE if species == 'spruce' else ALDER).items()]
    for fname, prm in jobs:
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
            if species in PACKED:
                b = Build()
                for v, (nm, pp) in enumerate(prm.items()):
                    pb = piece_build(species, pp, lod, proxy=lod == 3)
                    if pb is None:
                        continue
                    print(f'  {nm} {"lod%d" % lod if lod < 3 else "shadow"}: {sum(2 for f in pb.f)} tris')
                    pack_into(b, pb, (v + 0.5) / 8)
                if not b.f:
                    continue
            elif species == 'spruce':
                fm = SPRUCE_FORM[fname[-1]]
                b = spruce(prm['H'], prm['R'], prm['seed'], lod, fm) if lod < 3 else shadow_proxy(prm['H'], prm['R'], prm['seed'], fm)
            else:
                b = alder(prm['H'], prm['R'], prm['seed'], lod, prm['stems']) if lod < 3 else alder_proxy(prm['H'], prm['R'], prm['seed'], prm['stems'])
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
                ca.data[i].color = (c[0], c[1], c[2], c[3] if len(c) > 3 else 1.0)
            me.color_attributes.active_color = ca
            me.materials.append(mat)
            ob = bpy.data.objects.new(name, me)
            bpy.context.scene.collection.objects.link(ob)
            tris.append(sum(len(p.vertices) - 2 for p in me.polygons))
        out = os.path.join(OUT, f'{fname}.gltf')
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
