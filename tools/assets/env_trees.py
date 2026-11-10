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


# ---------------------------------------------------------------- the grass cards' atlas: retired here (L1 W2 wild)
# FROM (c) L1 C1 owns grass_meadow_atlas.png (tools/look/ground_paint.py atlas, ground.json "grass_atlas": MB4's big
# flat clumps); E4h's thin-blade painter that wrote the same file is removed, so a tree build can never overwrite it.
# `env_trees.py tex --species grass` now runs C1's command.

def grass_tex():
    import subprocess
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'look', 'ground_paint.py'), 'atlas'], check=True, cwd=ROOT)


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
            P, UV = [], []
            for s, hw in ((0.0, 0.08), (0.3, rng.uniform(0.22, 0.29)), (0.5, rng.uniform(0.08, 0.12)), (0.74, rng.uniform(0.19, 0.26)), (1.0, rng.uniform(0.02, 0.05))):
                cc = c0 + hd * r * s + np.array([0, 0, -r * (dr * s + 0.2 * s * s - 0.06 * max(s - 0.7, 0) ** 2 / 0.09)])
                j = rng.uniform(-0.08, 0.08) * r
                P.append([cc - sd * (hw * r + j), cc + sd * (hw * r - j)])
                # (Env 22 r1c) the blade's own place for leaf_shadow.gdshader: across it -1..1 in u, along it 0..1 in v
                UV.append([(0.0, 0.5 + 0.5 * s), (0.7, 0.5 + 0.5 * s)])
            N = [[np.array([0, 0, 1.0])] * 2] * 5
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


def tube(b, pts, radii, sides, occ=0.6, strip=(BU, 1.0)):
    """A bark tube along pts (its radius at each), the bark strip (or its sub-strip, strip) round it, v along it."""
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
            rowU.append((strip[0] + (strip[1] - strip[0]) * i / sides * 0.995, 0.01 + 0.98 * L / max(Ltot, 1e-6)))
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
        # (Env 22 r1c) each point's place in the flattened mass, its disc seen from above (0 the middle, 1 the rim), for
        # leaf_shadow.gdshader's ragged outline: u = 0.35 + 0.35 x, v = 0.5 + 0.5 y
        UV = [[(0.35 + 0.35 * math.sin(math.pi * jv / nv) * math.cos(2 * math.pi * (iu % nu) / nu),
                0.5 + 0.5 * math.sin(math.pi * jv / nv) * math.sin(2 * math.pi * (iu % nu) / nu)) for iu in range(nu + 1)] for jv in range(nv + 1)]
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


# ---------------------------------------------------------------- the tiered spruce (L1 C3a: LOOK_BIBLE rules 9 and 10)
# FROM (b) MB4's spruce panel (day and night: stacked flat tiers, each a skirt of jagged pointed fronds whose tips
# flick up, a lit top and a darker underside, the trunk seen only under the lowest tier) and target 04's and 09's tree
# masses (11-14 short tiers to a spruce, each tier one value block); (a) the play camera (34 degrees down, 23 m: a
# tier must read as a band of 6+ px, so a tier is 0.45-0.9 m high and never thinner); (c) the sizes, the trunk, the
# material and the shader's conventions (u > .75 the bark strip; COLOR r open, g out along the branch, b card) are
# env_trees.py's own (E4). Each tier is a closed wedge: its top from the trunk out to the jagged rim, its underside back
# up to the trunk, a hard rim between (the ink's silhouette and the painter's bevel stroke catch it). The atlas is the
# painter's (tools/look/wild.py: bake_forms.py --keep-uv, paint_core.py): every tier of the three sizes has its own
# island (its top seen from above, its underside from below at half the density), so lod1, lod2 and the shadow, which
# keep each tier's rim and lose only rings, sample the same painted tier.
TIER = {
    # n: tiers; hs: the lowest tier's foot (share of H); prof: the cone's curve; drop: a tier's rim below its foot
    # (share of its radius); th: its underside's rise at the trunk (share of its drop); notch: a notch's radius share;
    # w: the crown's width over E4's R (MB4's spruce is 0.45 as wide as tall: 0.8 takes E4's 0.33 R / H to 0.26);
    # lap: a tier's rim hangs at least this share of the step to the next tier down (MB4: each skirt over the next, no sky
    # between them; round 1's upper tiers stood as thin plates on a bare stick)
    # ridge: each frond's spine raised over its notches (share of the tier's radius, at the rim): target 04's tiers are
    # rings of separate pointed fronds, each a lit spine and a shaded flank from above (round 1's flat star discs took one
    # light over the whole tier)
    # (L1 W2 wild, rule 5 "two bands, lit and shade" and the wave-1 judge: at the title camera, 01 and 03, the tiers showed
    # triangle facets with grey speckle and by day, 04, each frond's underside striped the tier) bend: the tier top's normals
    # are the tier's smooth cone (no lobe, no ridge) bent up by this (+bend x up, then normalised), so each top takes one
    # light; ubend: the underside's bent down the same way, so it is one shade; ridge 0.16 -> 0.04 (the fronds' jags stay
    # on the rim, the notches 0.5 deep, not as creases across the faces the painter's bevel and cavity striped)
    'a': dict(n=11, hs=0.13, prof=0.95, drop=0.5, th=0.42, notch=0.5, w=0.8, lap=1.15, ridge=0.04, bend=1.2, ubend=1.5),
    'b': dict(n=12, hs=0.12, prof=0.9, drop=0.52, th=0.42, notch=0.52, w=0.8, lap=1.15, ridge=0.04, bend=1.2, ubend=1.5),
    'c': dict(n=14, hs=0.11, prof=1.05, drop=0.48, th=0.4, notch=0.5, w=0.8, lap=1.15, ridge=0.04, bend=1.2, ubend=1.5),
}
BARK_V = 8.0      # bark v: metres of trunk over the strip's height
TIER_LOBES = (6, 12)


def tier_plan(H, R, seed, tf):
    """Each tier's foot height, radius, drop, lobes and the rim's points (angle, radius share, height share, tip)."""
    rng = np.random.default_rng(seed * 7 + 3)
    n, hs = tf['n'], tf['hs'] * H
    R = R * tf.get('w', 1.0)
    top = H - 0.55
    tiers = []
    zf = lambda t: hs + (top - hs) * (1 - (1 - t) ** 1.18)   # closer toward the top
    for i in range(n):
        t = i / (n - 1)
        z = zf(t)
        r = R * ((1 - t) ** tf['prof'] * 0.9 + 0.1) * rng.uniform(0.93, 1.05)
        step = z - zf(max(t - 1 / (n - 1), 0.0)) if i else 0.0
        drop = min(max(r * tf['drop'], tf.get('lap', 0.0) * step, 0.0) * rng.uniform(0.9, 1.1), z - 0.32, 1.1 * r)
        K = int(np.clip(round(TIER_LOBES[0] + (TIER_LOBES[1] - TIER_LOBES[0]) * r / R), *TIER_LOBES))
        a0 = rng.uniform(0, 2 * math.pi)
        rim = []
        for k in range(2 * K):
            tip = k % 2 == 0
            a = a0 + (k + (rng.uniform(-0.22, 0.22) if tip else rng.uniform(-0.1, 0.1))) * math.pi / K
            rs = rng.uniform(0.9, 1.06) if tip else tf['notch'] * rng.uniform(0.92, 1.08)
            hz = rng.uniform(0.92, 1.08) if tip else 0.7    # a notch hangs less: the rim zig-zags in height too
            rim.append((a, rs, hz, tip))
        ext = 2.0 * r * max(x[1] for x in rim) * 1.03     # (an island spans the rim's real extent, not a guess)
        tiers.append(dict(z=z, r=r, drop=drop, th=tf['th'], K=K, rim=rim, rin=0.06 + 0.022 * H * (1 - t) ** 0.85, ext=ext,
                          ridge=tf.get('ridge', 0.0), bend=tf.get('bend', 0.0), ubend=tf.get('ubend', 0.0)))
    return tiers


def tier_point(T, k, s, under=False, flick=0.07):
    """A point of tier T at rim index k (fractional: between rim points), s 0 at the trunk to 1 at the rim."""
    rim = T['rim']; n = len(rim)
    k0 = int(math.floor(k)) % n; k1 = (k0 + 1) % n; w = k - math.floor(k)
    a0 = rim[k0][0]
    a1 = rim[k1][0] + (2 * math.pi if k1 == 0 else 0)
    a = a0 + (a1 - a0) * w
    rs = rim[k0][1] * (1 - w) + rim[k1][1] * w
    hz = rim[k0][2] * (1 - w) + rim[k1][2] * w
    tipness = (1 - w) if rim[k0][3] else w
    rr = T['rin'] + (T['r'] * rs - T['rin']) * s
    if not under:
        # the top hangs (a curve bending down outward), its fronds' tips flicked up
        dz = -T['drop'] * hz * (0.55 * s + 0.45 * s * s) + flick * T['r'] * tipness * float(smooth(0.72, 1.0, s))
        # (each frond's spine over its notches: a crease from the trunk out, so a frond's two flanks take two lights)
        dz += T.get('ridge', 0.0) * T['r'] * (tipness - 0.5) * min(1.0, 1.6 * s)
    else:
        # the underside: from the rim straight back up to the trunk, th of the drop under the foot
        rim_dz = -T['drop'] * hz + flick * T['r'] * tipness + T.get('ridge', 0.0) * T['r'] * (tipness - 0.5)
        dz = rim_dz * s + (-T['th'] * T['drop']) * (1 - s)
    return np.array([math.cos(a) * rr, math.sin(a) * rr, T['z'] + dz])


def tier_mesh(b, T, lod, isl_top, isl_under):
    """One tier into Build b. lod 0: top rings at s .5 and .82, its underside a band from the rim to the trunk; 1: the
    rim to the axis, top and underside; 2 (and the shadow): its top alone."""
    n = len(T['rim'])
    K = n // 2
    rings_top = {0: [0.0, 0.5, 0.82, 1.0], 1: [0.0, 1.0], 2: [0.0, 1.0]}[lod]
    rings_under = {0: [1.0, 0.0], 1: [1.0, 0.0], 2: []}[lod]
    ext = T['ext']

    def uv_of(p, isl, under):
        u0, v0, sz = isl
        x, y = p[0], p[1]
        if under:
            x = -x
        return (u0 + (x / ext + 0.5) * sz[0], v0 + (y / ext + 0.5) * sz[1])

    rsm = float(np.mean([x[1] for x in T['rim']])); hzm = float(np.mean([x[2] for x in T['rim']]))

    def nrm_at(k, s, under):
        """(L1 W2 wild) The tier's smooth cone at this angle (the rim's mean radius and hang: no lobe, ridge or flick), bent
        up (the top) or down (the underside) by T's bend: one light a top, one shade an underside (rule 5)."""
        p = tier_point(T, k, s, under)
        ax = np.array([p[0], p[1], 0.0]); ax /= np.linalg.norm(ax) + 1e-9
        run = max(T['r'] * rsm - T['rin'], 1e-3)
        if not under:
            slope = -T['drop'] * hzm * (0.55 + 0.9 * min(max(s, 0.0), 1.0)) / run    # dz / d(radius)
            nn = np.array([-slope * ax[0], -slope * ax[1], 1.0]); nn /= np.linalg.norm(nn)
            nn = nn + np.array([0.0, 0.0, T.get('bend', 0.0)])
        else:
            slope = (-T['drop'] * hzm + T['th'] * T['drop']) / run
            nn = -np.array([-slope * ax[0], -slope * ax[1], 1.0]); nn /= np.linalg.norm(nn)
            nn = nn - np.array([0.0, 0.0, T.get('ubend', 0.0)])
        return nn / (np.linalg.norm(nn) + 1e-9)

    for under, rings, isl in ((False, rings_top, isl_top), (True, rings_under, isl_under)):
        if not rings:
            continue
        rows = []
        for s in rings:
            cnt = (K if lod == 0 else 1) if s == 0.0 else n    # the trunk ring: one point a lobe (lod 1, 2: the axis)
            row = []
            for i in range(cnt):
                k = i * n / cnt
                p = tier_point(T, k, s, under)
                row.append(len(b.v))
                b.v.append(p); b.n.append(nrm_at(k, s, under)); b.uv.append(uv_of(p, isl, under))
                b.c.append((1.0, s if not under else 0.25 * s, 0.0))
            rows.append(row)
        for ra, rb_ in zip(rows[:-1], rows[1:]):
            # two rings stitched round the tier by angle (their counts may differ)
            na, nb_ = len(ra), len(rb_)
            i = j = 0
            while i < na or j < nb_:
                fa = (i + 1) / na if i < na else 9
                fb = (j + 1) / nb_ if j < nb_ else 9
                if fa <= fb:
                    tri = (ra[i % na], ra[(i + 1) % na], rb_[j % nb_]); i += 1
                else:
                    tri = (ra[i % na], rb_[(j + 1) % nb_], rb_[j % nb_]); j += 1
                if len(set(tri)) < 3:
                    continue    # (a one-point ring's closing step: no face)
                # (wound so the top's front faces up and the underside's down: FRONT_FACING turns the normal)
                b.f.append((tri[0], tri[2], tri[1]))


def bark_tube(b, H, rb, z1, sides, rings, strip):
    """The trunk: a tapered tube from under the ground to z1 (inside the crown), its uvs in this size's bark strip."""
    u0, u1 = strip
    P, N, UV = [], [], []
    for k in range(rings + 1):
        t = k / rings
        z = -0.25 + (z1 + 0.25) * t
        rad = max(0.03, rb * (1 - 0.75 * z / H))
        flare = 1 + 0.45 * math.exp(-max(z, 0) / 0.3)
        rowP, rowN, rowU = [], [], []
        for i in range(sides + 1):
            a = i / sides * 2 * math.pi
            rowP.append(np.array([math.cos(a) * rad * flare, math.sin(a) * rad * flare, z]))
            rowN.append(np.array([math.cos(a), math.sin(a), 0.1]) / 1.005)
            rowU.append((u0 + (u1 - u0) * i / sides, min(0.995, 0.005 + (z + 0.25) / BARK_V)))
        P.append(rowP); N.append(rowN); UV.append(rowU)
    b.quad_grid(P, N, UV, sides, rings, [[(1.0, 0.0, 0.0)] * (sides + 1)] * (rings + 1))


def leader(b, H, z0, r, isl):
    """The leader: a five-sided spike over the top tier (its own small island)."""
    base = len(b.v)
    u0, v0, sz = isl
    for i in range(5):
        a = i / 5 * 2 * math.pi
        b.v.append(np.array([math.cos(a) * r, math.sin(a) * r, z0])); b.n.append(np.array([math.cos(a), math.sin(a), 0.5]) / 1.118)
        b.uv.append((u0 + (0.5 + 0.45 * math.cos(a)) * sz[0], v0 + (0.5 + 0.45 * math.sin(a)) * sz[1])); b.c.append((1.0, 0.6, 0.0))
    b.v.append(np.array([0.0, 0.0, H])); b.n.append(np.array([0.0, 0.0, 1.0]))
    b.uv.append((u0 + 0.5 * sz[0], v0 + 0.5 * sz[1])); b.c.append((1.0, 1.0, 0.0))
    for i in range(5):
        b.f.append((base + i, base + (i + 1) % 5, base + 5))


def tier_atlas(plans, A=2048, umax=BU, gap=10, under=0.35):
    """Islands for every size's tiers (tops at full density, undersides at `under` of it: the play camera sees a tier's
    top and only its underside's rim) and leaders, shelf-packed into u < umax at the largest density that fits.
    Returns ({(size, tier, part): (u0, v0, (du, dv))}, px per metre)."""
    items = []
    for sz, tiers in plans.items():
        for i, T in enumerate(tiers):
            items.append((sz, i, 'top', T['ext'], 1.0))
            items.append((sz, i, 'under', T['ext'], under))
        items.append((sz, -1, 'leader', 0.5, 1.0))
    return shelf_pack(items, A, umax, gap)


def shelf_pack(items, A=2048, umax=BU, gap=10):
    """Square islands (key..., side in m, density share) shelf-packed into u < umax at the largest px per metre that
    fits (a bisection). Returns ({key: (u0, v0, (du, dv))}, px per metre)."""
    W, Hh = umax * A - gap, A - gap

    def pack(ppm):
        order = sorted(items, key=lambda it: (-it[3] * it[4], it[:3]))
        x = y = gap; rowh = 0; out = {}
        for it in order:
            side = math.ceil(it[3] * it[4] * ppm)
            if x + side > W:
                x, y, rowh = gap, y + rowh + gap, 0
            if y + side > Hh:
                return None
            out[it[:3]] = (x / A, 1 - (y + side) / A, (side / A, side / A))
            x += side + gap; rowh = max(rowh, side)
        return out
    lo, hi = 10.0, 400.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if pack(mid):
            lo = mid
        else:
            hi = mid
    return pack(lo), lo


def spruce_tiered(H, R, seed, lod, tf, isl, strip, shadow=False):
    """The tiered spruce at lod 0, 1, 2 (or its shadow caster: every tier's top and a short trunk)."""
    b = Build()
    tiers = tier_plan(H, R, seed, tf)
    rb = 0.022 * H + 0.05
    # (the trunk up to the top tier, thin above the lower ones: MB4's spruce shows it between its tiers; round 1's stopped at
    # the fourth tier, so the upper tiers floated)
    z1 = tiers[-1]['z'] if lod < 2 and not shadow else tiers[0]['z'] + 0.2
    bark_tube(b, H, rb, z1, 4 if shadow else (6, 5, 4)[lod], 1 if shadow else (5, 3, 1)[lod], strip)
    b.nbark = len(b.f)
    for i, T in enumerate(tiers):
        if lod == 2 and not shadow and i % 2 and i != len(tiers) - 1:
            continue
        if lod == 2 and not shadow:
            T = dict(T, drop=T['drop'] * 1.5)    # (every other tier, hung lower to close the gaps; uvs are x, y: unchanged)
        tier_mesh(b, T, 2 if shadow else lod, isl[i][0], isl[i][1])
    leader(b, H, tiers[-1]['z'] - 0.1, 0.12, isl[-1])
    return b, tiers


PAINT_SRC = os.path.join(ROOT, 'godot', 'art', 'world', 'painted', '_src')


def to_blender(bpy, name, b, mats, mat_of=None):
    """A Build as a Blender object (its uvs, normals and colours as built); mat_of(face index) picks a material slot."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in b.v], [], b.f)
    assert len(me.polygons) == len(b.f), name    # (no face dropped: material slots and the bark count index them)
    uvl = me.uv_layers.new(name='UV')
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = b.uv[me.loops[li].vertex_index]
    me.normals_split_custom_set_from_vertices([tuple(n / (np.linalg.norm(n) + 1e-9)) for n in b.n])
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    for i, c in enumerate(b.c):
        ca.data[i].color = (c[0], c[1], c[2], c[3] if len(c) > 3 else 1.0)
    me.color_attributes.active_color = ca
    for m in mats:
        me.materials.append(m)
    if mat_of is not None:
        for p in me.polygons:
            p.material_index = mat_of(p.index)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob, sum(len(p.vertices) - 2 for p in me.polygons)


def export_gltf(bpy, out, glb=False, select=None):
    if select is not None:
        bpy.ops.object.select_all(action='DESELECT')
        for o in select:
            o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB' if glb else 'GLTF_SEPARATE', export_texture_dir='',
                              export_normals=True, export_tangents=False, export_materials='EXPORT',
                              export_image_format='AUTO', export_keep_originals=True, export_yup=True, export_apply=True,
                              export_vertex_color='ACTIVE', use_selection=select is not None)


def mesh_spruce_tiers():
    """The three tiered spruces (lod0-2 and the shadow caster, one material, Leaves_OwnSpruce, on spruce_atlas.png) and
    the painter's sheet (every size's lod0 side by side, materials 'foliage' and 'bark', the same uvs):
    godot/art/world/painted/_src/spruce_sheet.glb (tools/look/wild.py bakes and paints it into spruce_atlas.png)."""
    import bpy, json
    os.makedirs(OUT, exist_ok=True); os.makedirs(PAINT_SRC, exist_ok=True)
    plans = {sz: tier_plan(p['H'], p['R'], p['seed'], TIER[sz]) for sz, p in SPRUCE.items()}
    isl_all, ppm = tier_atlas(plans)
    print(f'spruce tiers: atlas {ppm:.1f} px/m (tops; undersides half)')
    strips = {sz: (BU + (k + 0.03) * (1 - BU) / 3, BU + (k + 0.97) * (1 - BU) / 3) for k, sz in enumerate(SPRUCE)}
    sheet = []
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for k, (sz, p) in enumerate(SPRUCE.items()):
        isl = [(isl_all[(sz, i, 'top')], isl_all[(sz, i, 'under')]) for i in range(len(plans[sz]))] + [isl_all[(sz, -1, 'leader')]]
        b, _ = spruce_tiered(p['H'], p['R'], p['seed'], 0, TIER[sz], isl, strips[sz])
        nbark = b.nbark
        b.v = [v + np.array([16.0 * k, 0.0, 0.0]) for v in b.v]
        sheet.append((b, nbark))
    mf, mb = bpy.data.materials.new('foliage'), bpy.data.materials.new('bark')
    obs = []
    for k, (b, nbark) in enumerate(sheet):
        ob, _ = to_blender(bpy, f'sheet_{k}', b, [mf, mb], lambda fi, nb=nbark: 1 if fi < nb else 0)
        obs.append(ob)
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    obs[0].name = 'lod0'
    export_gltf(bpy, os.path.join(PAINT_SRC, 'spruce_sheet.glb'), glb=True)
    img_path = os.path.join(OUT, 'spruce_atlas.png')
    report = {}
    for k, (sz, p) in enumerate(SPRUCE.items()):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        img = bpy.data.images.load(img_path)
        mat = bpy.data.materials.new('Leaves_OwnSpruce'); mat.use_nodes = True
        nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
        ti = nt.nodes.new('ShaderNodeTexImage'); ti.image = img
        nt.links.new(ti.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 1.0
        mat.use_backface_culling = False
        isl = [(isl_all[(sz, i, 'top')], isl_all[(sz, i, 'under')]) for i in range(len(plans[sz]))] + [isl_all[(sz, -1, 'leader')]]
        tris = []
        for lod in range(4):
            b, _ = spruce_tiered(p['H'], p['R'], p['seed'], min(lod, 2), TIER[sz], isl, strips[sz], shadow=lod == 3)
            _, t = to_blender(bpy, f'lod{lod}' if lod < 3 else 'shadow', b, [mat])
            tris.append(t)
        export_gltf(bpy, os.path.join(OUT, f'spruce_{sz}.gltf'))
        report[sz] = tris
        print(f'spruce_{sz}.gltf tris lod0/1/2/shadow: {tris}')
    print('REPORT', json.dumps(dict(spruce=report, ppm=round(ppm, 1))))


# ---------------------------------------------------------------- the clustered alder (L1 C3a: LOOK_BIBLE rule 9)
# FROM (b) LOOK_BIBLE rule 9 ("foliage is flat leaf clusters in two or three values, silhouette ink only"), MB4's grass
# panel's broad leaf masses and targets 04, 09 and 10's broadleaf crowns (a crown of a dozen chunky rounded masses, each
# a lit top over a dark underside, scalloped edges against the sky); (a) the play camera (23 m, 34 degrees down: a
# cluster 1-1.5 m across is 30-45 px at 1080, so its scallops and its two values read); (c) the sizes, the stems, the
# crown's oval (0.62 H, 0.38 H: flora_species.json's crown_lo/hi stay true), the bark strip (u > .75) and the material
# Leaves_OwnAlder are env_trees.py's own (E4). Each cluster is a closed flattened dome: a scalloped rim of 6-9 rounded
# lobes, its top domed up, its underside sagging under it, a hard rim between (the ink's silhouette and the painter's
# bevel stroke catch it). Every cluster of the three sizes has its own island (its top from above, its underside from
# below at 0.35 of the density), so lod1 and lod2, which keep a cluster's rim and lose only rings (lod2 the smaller
# clusters too), sample the same painted cluster. tools/look/wild.py alder bakes and paints the atlas.
CLUSTER = {
    # n: clusters; rc: a cluster's radius (share of R); hc: its dome's rise, hu: its underside's sag (shares of its radius);
    # notch: the scallops' cusp radius share; f: the cluster centres' place out in the crown's oval (share)
    'a': dict(n=13, rc=0.52, hc=0.34, hu=0.22, notch=0.58, f=(0.5, 0.74)),
    'b': dict(n=11, rc=0.56, hc=0.34, hu=0.22, notch=0.58, f=(0.5, 0.74)),
    'c': dict(n=14, rc=0.52, hc=0.32, hu=0.22, notch=0.58, f=(0.5, 0.74)),
}
CL_LOBES = (5, 7)
CL_SUB = 3          # rim points a lobe (its cusp, then two round its crown)
CL_DROOP = 0.12     # the rim under the dome's foot (share of the radius): a cluster hangs at its edge


def cluster_plan(H, R, seed, cf):
    """The crown's clusters: each a centre, a frame (its up tilted out from the crown), a radius, a rim."""
    rng = np.random.default_rng(seed * 11 + 5)
    zc, hz = 0.62 * H, 0.38 * H
    n = cf['n']
    out = []
    for i in range(n):
        # a golden-angle spiral down the oval from its top, the bottom left open (the stems show under the crown)
        zf = 0.92 - 1.62 * (i + 0.5) / n
        a = i * 2.39996 + rng.normal(0, 0.2)
        rxy = math.sqrt(max(0.0, 1 - zf * zf))
        o = np.array([rxy * math.cos(a), rxy * math.sin(a), zf])
        f = rng.uniform(*cf['f'])
        c = np.array([0, 0, zc]) + o * np.array([R, R, hz]) * f
        # (the masses at the crown's middle the biggest, its top and its foot smaller: the oval's silhouette)
        # (L1 W2 wild, rule 10 "big-medium-small" and the wave-2 crop of 05: equal clusters with shallow scallops read as hex
        # plates at play) every third cluster big, medium or small (1.25 / 0.95 / 0.7), the scallops cut to 0.58 of the radius
        r = cf['rc'] * R * (0.78 + 0.32 * rxy) * rng.uniform(0.92, 1.08) * (1.25, 0.95, 0.7)[i % 3]
        w = np.array([0, 0, 1.0]) + np.array([o[0], o[1], 0.0]) * 0.75 * rxy
        w /= np.linalg.norm(w)
        u = np.cross(w, np.array([math.cos(a + 1.3), math.sin(a + 1.3), 0.0])); u /= np.linalg.norm(u)
        v = np.cross(w, u)
        K = int(rng.integers(CL_LOBES[0], CL_LOBES[1] + 1))
        a0 = rng.uniform(0, 2 * math.pi)
        lob = rng.uniform(0.9, 1.08, K)
        wid = rng.uniform(0.75, 1.25, K); wid /= wid.sum() / K
        rim, acc = [], a0
        for k in range(K):
            span = 2 * math.pi / K * wid[k]
            for j in range(CL_SUB):
                ph = j / CL_SUB
                rs = cf['notch'] + (lob[k] - cf['notch']) * math.sin(math.pi * ph) ** 0.55 if j else cf['notch']
                rim.append((acc + span * ph, rs, 0.0, j > 0))
            acc += span
        ext = 2.0 * r * max(x[1] for x in rim) * 1.03
        out.append(dict(c=c, u=u, v=v, w=w, r=r, hc=cf['hc'], hu=cf['hu'], rim=rim, ext=ext, rxy=rxy))
    return out


def cluster_point(C, k, s, under=False):
    """A point of cluster C at rim index k (fractional), s 0 at its middle to 1 at its rim; and its local (x, y)."""
    rim = C['rim']; n = len(rim)
    k0 = int(math.floor(k)) % n; k1 = (k0 + 1) % n; wgt = k - math.floor(k)
    a0 = rim[k0][0]
    a1 = rim[k1][0] + (2 * math.pi if k1 == 0 else 0)
    a = a0 + (a1 - a0) * wgt
    rs = rim[k0][1] * (1 - wgt) + rim[k1][1] * wgt
    rr = C['r'] * rs * s
    x, y = math.cos(a) * rr, math.sin(a) * rr
    s2 = s * s
    rimz = -CL_DROOP * C['r'] * rs
    z = rimz * s2 + (C['hc'] if not under else -C['hu']) * C['r'] * (1 - s2) ** (0.8 if not under else 1.0)
    return C['c'] + C['u'] * x + C['v'] * y + C['w'] * z, x, y


def cluster_mesh(b, C, lod, isl_top, isl_under):
    """One cluster into Build b. lod 0: top rings at s .5 and .82 and its underside a fan to the middle; 1: its top fan
    alone; 2: its top fan on one rim point a lobe (each lobe's crown)."""
    n = len(C['rim'])
    rings_top = {0: [0.0, 0.5, 0.82, 1.0], 1: [0.0, 1.0], 2: [0.0, 1.0]}[lod]
    rings_under = {0: [1.0, 0.0], 1: [], 2: []}[lod]
    ext = C['ext']

    def nrm_at(k, s, under):
        s = min(max(s, 0.05), 0.95)
        du = cluster_point(C, k + 0.03, s, under)[0] - cluster_point(C, k - 0.03, s, under)[0]
        ds = cluster_point(C, k, s + 0.05, under)[0] - cluster_point(C, k, s - 0.05, under)[0]
        nn = np.cross(ds, du); nn /= np.linalg.norm(nn) + 1e-9
        if (np.dot(nn, C['w']) < 0) != under:
            nn = -nn
        return nn

    for under, rings, isl in ((False, rings_top, isl_top), (True, rings_under, isl_under)):
        if not rings:
            continue
        u0, v0, sz = isl
        rows = []
        for s in rings:
            cnt = 1 if s == 0.0 else (n // CL_SUB if lod == 2 else n)
            row = []
            for i in range(cnt):
                k = i * n / cnt + (1.5 if lod == 2 else 0.0)     # (lod 2: midway between a lobe's two crown points)
                p, x, y = cluster_point(C, k, s, under)
                if under:
                    x = -x
                row.append(len(b.v))
                b.v.append(p)
                b.n.append(C['w'] * (1 if not under else -1) if s == 0.0 else nrm_at(k, s, under))
                b.uv.append((u0 + (x / ext + 0.5) * sz[0], v0 + (y / ext + 0.5) * sz[1]))
                # (r how open: the crown's outer masses 1, its inner 0.75, an underside 0.7 of it; g out to the rim)
                op = (0.75 + 0.25 * C['rxy']) * (0.7 if under else 1.0)
                b.c.append((op, s if not under else 0.25 * s, 0.0))
            rows.append(row)
        for ra, rb_ in zip(rows[:-1], rows[1:]):
            na, nb_ = len(ra), len(rb_)
            i = j = 0
            while i < na or j < nb_:
                fa = (i + 1) / na if i < na else 9
                fb = (j + 1) / nb_ if j < nb_ else 9
                if fa <= fb:
                    tri = (ra[i % na], ra[(i + 1) % na], rb_[j % nb_]); i += 1
                else:
                    tri = (ra[i % na], rb_[(j + 1) % nb_], rb_[j % nb_]); j += 1
                if len(set(tri)) < 3:
                    continue    # (the middle's one-point ring's closing step: no face)
                # (wound so the top's front faces out along w, the underside's against it)
                fn = np.cross(b.v[tri[1]] - b.v[tri[0]], b.v[tri[2]] - b.v[tri[0]])
                if (np.dot(fn, C['w']) < 0) != under:
                    tri = (tri[0], tri[2], tri[1])
                b.f.append(tri)


def alder_clustered(H, R, seed, lod, stems, cf, isl, strip):
    """The clustered alder at lod 0, 1, 2: its stems and main branches (as E4's, in this size's bark sub-strip), its
    clusters (lod2: the bigger two thirds, each a little bigger)."""
    rng = np.random.default_rng(seed)
    b = Build()
    zc, hz = 0.62 * H, 0.38 * H
    sts = alder_stems(H, seed, stems)
    for pts, rad in sts:
        tube(b, pts, rad, (6, 5, 4)[lod], strip=strip)
    for pts, rad in sts:
        for i in range((int(rng.integers(3, 5)), 2, 0)[lod]):
            f = rng.uniform(0.42, 0.72)
            k = min(int(f * 7), 6); g = f * 7 - k
            p0 = pts[k] * (1 - g) + pts[k + 1] * g
            az, el = rng.uniform(0, 6.28), math.radians(rng.uniform(25, 50))
            d = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)])
            rr = R * math.sqrt(max(0.05, 1 - ((p0[2] - zc) / hz) ** 2))
            L = max(0.6, rr * rng.uniform(0.55, 0.75))
            r = 0.05 * math.sqrt(H / 8)
            tube(b, [p0, p0 + d * L * 0.5 + np.array([0, 0, 0.08 * L]), p0 + d * L], [r, r * 0.6, r * 0.3], (4, 3, 3)[lod],
                 occ=0.5, strip=strip)
    b.nbark = len(b.f)
    cl = cluster_plan(H, R, seed, cf)
    keep = sorted(range(len(cl)), key=lambda i: -cl[i]['r'])[:max(4, (2 * len(cl)) // 3)] if lod == 2 else range(len(cl))
    for i in sorted(keep):
        C = cl[i]
        if lod == 2:
            # (the kept masses a little bigger to close the gaps; the uvs are x / ext, so ext grows with them)
            C = dict(C, r=C['r'] * 1.12, ext=C['ext'] * 1.12)
        cluster_mesh(b, C, lod, isl[i][0], isl[i][1])
    return b


def mesh_alder_clusters():
    """The three clustered alders (lod0-2; the shadow caster stays E4's lumpy proxy, alder_proxy) on one material,
    Leaves_OwnAlder on alder_atlas.png, and the painter's sheet godot/art/world/painted/_src/alder_sheet.glb (every
    size's lod0 16 m apart, materials 'foliage' and 'bark', the same uvs)."""
    import bpy, json
    os.makedirs(OUT, exist_ok=True); os.makedirs(PAINT_SRC, exist_ok=True)
    plans = {sz: cluster_plan(p['H'], p['R'], p['seed'], CLUSTER[sz]) for sz, p in ALDER.items()}
    items = []
    for sz, cl in plans.items():
        for i, C in enumerate(cl):
            items.append((sz, i, 'top', C['ext'], 1.0))
            items.append((sz, i, 'under', C['ext'], 0.35))
    isl_all, ppm = shelf_pack(items)
    print(f'alder clusters: atlas {ppm:.1f} px/m (tops; undersides 0.35)')
    strips = {sz: (BU + (k + 0.03) * (1 - BU) / 3, BU + (k + 0.97) * (1 - BU) / 3) for k, sz in enumerate(ALDER)}
    isls = {sz: [(isl_all[(sz, i, 'top')], isl_all[(sz, i, 'under')]) for i in range(len(plans[sz]))] for sz in ALDER}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mf, mb = bpy.data.materials.new('foliage'), bpy.data.materials.new('bark')
    obs = []
    for k, (sz, p) in enumerate(ALDER.items()):
        b = alder_clustered(p['H'], p['R'], p['seed'], 0, p['stems'], CLUSTER[sz], isls[sz], strips[sz])
        b.v = [v + np.array([16.0 * k, 0.0, 0.0]) for v in b.v]
        ob, _ = to_blender(bpy, f'sheet_{k}', b, [mf, mb], lambda fi, nb=b.nbark: 1 if fi < nb else 0)
        obs.append(ob)
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    obs[0].name = 'lod0'
    export_gltf(bpy, os.path.join(PAINT_SRC, 'alder_sheet.glb'), glb=True)
    img_path = os.path.join(OUT, 'alder_atlas.png')
    report = {}
    for k, (sz, p) in enumerate(ALDER.items()):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        img = bpy.data.images.load(img_path)
        mat = bpy.data.materials.new('Leaves_OwnAlder'); mat.use_nodes = True
        nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
        ti = nt.nodes.new('ShaderNodeTexImage'); ti.image = img
        nt.links.new(ti.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 1.0
        mat.use_backface_culling = False
        tris = []
        for lod in range(4):
            if lod < 3:
                b = alder_clustered(p['H'], p['R'], p['seed'], lod, p['stems'], CLUSTER[sz], isls[sz], strips[sz])
            else:
                b = alder_proxy(p['H'], p['R'], p['seed'], p['stems'])
            _, t = to_blender(bpy, f'lod{lod}' if lod < 3 else 'shadow', b, [mat])
            tris.append(t)
        export_gltf(bpy, os.path.join(OUT, f'alder_{sz}.gltf'))
        report[sz] = tris
        print(f'alder_{sz}.gltf tris lod0/1/2/shadow: {tris}')
    print('REPORT', json.dumps(dict(alder=report, ppm=round(ppm, 1))))


# ---------------------------------------------------------------- the leaf clump (L1 lead 15 helper M; round 2 lead 16 helper M2)
# FROM the target's 09 bushes: at the play camera a bush is a lumpy MASS of leaf clusters, 3-5 big tone shapes, not
# leaves: each cluster a rounded lobe, a dark gap where two meet, the outline scalloped by the clusters and by a few
# single broad lobed leaves sticking out. So (round 1's 83 blades on a dome read as a spiky star ball: scrapped):
#   the mass   7-12 lobes (squashed balls 0.6-1.1 m across, a little lumpy, leaning) at unequal heights, each its OWN
#              vertices with the lobe's own smooth normals, pushed into one another: the crease between two is a hard
#              turn of the normal (the standing material's steps draw it as the gap). Faces wholly inside another lobe
#              are dropped. A lobe on the ground ends in a ring under it whose normals turn CL_FOOT degrees down.
#   rim leaves 18-30 broad lobed leaves on the mass's outer flanks and over its creases, the stem buried so 35-60% of
#              the leaf sticks out, lying between the tangent and the level (so the 50 degree camera sees it broad from
#              every side: the pieces are yawed in the game). A leaf keeps ONE normal, the lobe's where it comes out,
#              and the lobe's dab, so inside the mass it melts into its lobe and only its free part reads.
# Vertex data (the standing leaf route's contract): COLOR.b 1 on the mass, 0 on a leaf; COLOR.r 1 on the mass, on a
# leaf 1.0 / 0.8 / 0.45 by its normal's angle from up (35, 69.5); COLOR.g 0 on the mass, stem 0 to tip 1 on a leaf;
# COLOR.a the piece. UV: a lobe (and its leaves) samples ONE point of clump_dabs.png (lobes differ a step in value).
# Species `clump`, packed: clump_a, tuft_a, clump_b (the order is the piece id).
#     python tools/assets/env_trees.py tex --species clump                       clump_dabs.png
#     blender -b -P tools/assets/env_trees.py -- mesh --species clump            clump.gltf (lod0-2, shadow)
#     python tools/assets/env_trees.py sheet --species clump --out X.png         the proof picture and the numbers
CLUMP = {
    # lobes: (centre x, y, z; radii x, y, z; yaw). clump_a a kidney 3.2 x 2.6 m, 1.4 m tall (its notch at +y)
    'clump_a': {'seed': 11, 'leaves': 25, 'leaf': (0.50, 0.65), 'lobes': [
        (-1.12, 0.12, 0.20, 0.50, 0.44, 0.40, 15), (-0.78, -0.60, 0.26, 0.54, 0.46, 0.46, -20),
        (-0.02, -0.88, 0.18, 0.44, 0.40, 0.36, 5), (0.66, -0.62, 0.24, 0.55, 0.48, 0.44, 30),
        (1.18, 0.02, 0.18, 0.44, 0.40, 0.36, -10), (0.78, 0.74, 0.22, 0.48, 0.44, 0.40, 40),
        (-0.62, 0.80, 0.24, 0.52, 0.44, 0.42, -30), (0.05, 0.15, 0.25, 0.55, 0.50, 0.45, 0),      # (the ground ring, the heart)
        (-0.50, 0.02, 0.72, 0.55, 0.50, 0.44, 10), (0.42, 0.00, 0.60, 0.52, 0.48, 0.42, -25),
        (0.02, -0.38, 0.52, 0.46, 0.42, 0.38, 0),                                                   # (the second tier)
        (-0.30, 0.28, 1.00, 0.48, 0.44, 0.40, 20)]},                                                # (the top)
    'tuft_a': {'seed': 23, 'tuft': (4, 2)},
    'clump_b': {'seed': 37, 'leaves': 20, 'leaf': (0.50, 0.60), 'lobes': [
        (-0.62, 0.05, 0.18, 0.36, 0.33, 0.32, 20), (-0.25, -0.45, 0.18, 0.38, 0.33, 0.32, -15),
        (0.35, -0.42, 0.20, 0.40, 0.35, 0.34, 35), (0.66, 0.10, 0.18, 0.34, 0.32, 0.30, 0),
        (0.20, 0.45, 0.20, 0.38, 0.34, 0.32, -40), (-0.30, 0.42, 0.18, 0.34, 0.32, 0.30, 10),
        (-0.10, 0.00, 0.50, 0.42, 0.38, 0.36, 25), (0.28, 0.05, 0.42, 0.36, 0.34, 0.32, -20)]},
}
CL_SEG = {0: (12, 5), 1: (8, 3), 2: (6, 2)}       # a lobe's (segments round, rings pole to foot) a LOD
CL_SINK = 0.04        # a ground lobe's last ring sits this far under the ground
CL_FOOT = 20.0        # ... and its normals turn this far down off the level (the contact tone)
CL_LUMP = (0.07, 0.13)     # a lobe's outline off the ellipse (the share of its radius, two waves round it)
CL_LEAN = 0.18        # a lobe leans at most this (m sideways a m of height)
CL_WIDE = 0.92        # a blade's width over its length (x of CL_BLADE is in half-widths of 0.5: 0.98 x 0.92 = 0.9)
CL_OUT = (0.40, 0.58)      # the share of a rim leaf that sticks out of the mass
CL_EL = (22.0, 0.6, 8.0)   # a rim leaf's elevation (degrees) = [0] - [1] x its lobe normal's angle from up, +- [2]
CL_GAP = 0.32         # two rim leaves' middles are never nearer than this (m)
CL_JIT = 8.0          # a tuft leaf's normal off its own (degrees, at most)
# a blade a LOD: its outline (x across, y stem to tip) and triangles. lod0 a broad five-lobed leaf, the notches
# shallow (maple-hazel), a fan round its middle (14 triangles); lod1 an eight-corner blade (6); lod2 a kite (2)
CL_BLADE = {
    0: ([(0, 0), (0.45, 0.18), (0.49, 0.42), (0.37, 0.52), (0.44, 0.68), (0.33, 0.83), (0.19, 0.81), (0, 1.0),
         (-0.19, 0.81), (-0.33, 0.83), (-0.44, 0.68), (-0.37, 0.52), (-0.49, 0.42), (-0.45, 0.18), (0, 0.45)],
        [(14, i, (i + 1) % 14) for i in range(14)]),
    1: ([(0, 0), (0.47, 0.24), (0.45, 0.60), (0.24, 0.86), (0, 1.0), (-0.24, 0.86), (-0.45, 0.60), (-0.47, 0.24)], [(0, i, i + 1) for i in range(1, 7)]),
    2: ([(0, 0), (0.47, 0.40), (0, 1.0), (-0.47, 0.40)], [(0, 1, 2), (0, 2, 3)]),
}
_CL_UP = np.array([0.0, 0.0, 1.0])
_cl_cache = {}


def clump_lobes(prm):
    """A piece's lobes, seeded: dicts c, r, R (its yaw), lump (waves round it), lean, uv (its dab)."""
    rng = np.random.default_rng(prm['seed'] + 1)
    out = []
    for cx, cy, cz, rx, ry, rz, yaw in prm['lobes']:
        ya = math.radians(yaw)
        la, lm = rng.uniform(0, 2 * math.pi), rng.uniform(0, CL_LEAN)
        out.append({'c': np.array([cx, cy, cz], float), 'r': np.array([rx, ry, rz], float),
                    'R': np.array([[math.cos(ya), -math.sin(ya), 0], [math.sin(ya), math.cos(ya), 0], [0, 0, 1.0]]),
                    'lump': [(k, rng.uniform(*CL_LUMP), rng.uniform(0, 2 * math.pi)) for k in (3, 5)],
                    'lean': np.array([lm * math.cos(la), lm * math.sin(la)]),
                    'uv': (float(rng.uniform(0.04, 0.70)), float(rng.uniform(0.22, 0.96)))})
    return out


def lobe_pt(lb, th, ph):
    """Points of a lobe's surface (th from its top pole, ph round it; arrays): N x 3."""
    th, ph = np.atleast_1d(np.asarray(th, float)), np.atleast_1d(np.asarray(ph, float))
    m = 1 + sum(a * np.cos(k * (ph - t0)) for k, a, t0 in lb['lump'])
    s, z = np.sin(th), lb['r'][2] * np.cos(th)
    q = np.stack([lb['r'][0] * m * s * np.cos(ph) + lb['lean'][0] * z, lb['r'][1] * m * s * np.sin(ph) + lb['lean'][1] * z, z], -1)
    return lb['c'] + q @ lb['R'].T


def lobe_n(lb, th, ph):
    """The surface's own outward normals there (the same at every LOD)."""
    th, ph = np.atleast_1d(np.asarray(th, float)), np.atleast_1d(np.asarray(ph, float))
    e = 1e-3
    n = np.cross(lobe_pt(lb, th + e, ph) - lobe_pt(lb, th - e, ph), lobe_pt(lb, th, ph + e) - lobe_pt(lb, th, ph - e))
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-12)
    pole = np.sin(th) < 2e-3
    n[pole] = np.sign(np.cos(th[pole]))[:, None] * _CL_UP
    return n


def lobe_in(lb, P, k=1.0):
    """Which of the points P (N x 3) lie inside the lobe (grown k times)."""
    q = (np.atleast_2d(P) - lb['c']) @ lb['R']
    x, y = q[:, 0] - lb['lean'][0] * q[:, 2], q[:, 1] - lb['lean'][1] * q[:, 2]
    ph = np.arctan2(y / lb['r'][1], x / lb['r'][0])
    m = k * (1 + sum(a * np.cos(kk * (ph - t0)) for kk, a, t0 in lb['lump']))
    return (x / (lb['r'][0] * m)) ** 2 + (y / (lb['r'][1] * m)) ** 2 + (q[:, 2] / (lb['r'][2] * k)) ** 2 < 1.0


def clump_jitter(rng, n, deg):
    """n turned by up to deg degrees round a seeded axis across it."""
    ax = np.cross(n, rng.normal(size=3))
    ax /= np.linalg.norm(ax) + 1e-9
    a = math.radians(rng.uniform(0, deg))
    return n * math.cos(a) + np.cross(ax, n) * math.sin(a)


def clump_mass(b, lobes, lod):
    """The lobes' faces (tag 1) into b: a pole, rings, and a foot ring under the ground or a lower pole."""
    seg, rings = CL_SEG[lod]
    for li, lb in enumerate(lobes):
        cz, rz = lb['c'][2], lb['r'][2]
        ground = cz - rz < 0.0
        th_end = math.acos(max(-1.0, min(1.0, -(cz + CL_SINK) / rz))) if ground else math.pi
        nr = rings if ground else rings - 1
        TH = np.concatenate([[0.0], np.repeat(th_end * np.arange(1, nr + 1) / rings, seg)] + ([] if ground else [[math.pi]]))
        PH = np.concatenate([[0.0], np.tile(2 * math.pi * np.arange(seg) / seg, nr)] + ([] if ground else [[0.0]]))
        V, N = lobe_pt(lb, TH, PH), lobe_n(lb, TH, PH)
        if ground:
            h = N[-seg:, :2] / np.maximum(np.linalg.norm(N[-seg:, :2], axis=1, keepdims=True), 1e-9)
            f = math.radians(CL_FOOT)
            N[-seg:] = np.concatenate([h * math.cos(f), np.full((seg, 1), -math.sin(f))], 1)
        F = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
        for j in range(nr - 1):
            a0, b0 = 1 + j * seg, 1 + (j + 1) * seg
            for i in range(seg):
                i1 = (i + 1) % seg
                F += [(a0 + i, b0 + i, b0 + i1), (a0 + i, b0 + i1, a0 + i1)]
        if not ground:
            a0, bp = 1 + (nr - 1) * seg, 1 + nr * seg
            F += [(bp, a0 + (i + 1) % seg, a0 + i) for i in range(seg)]
        F = np.array(F)
        cen = V[F].mean(1)
        hv, hc = V[:, 2] < -CL_SINK - 0.01, cen[:, 2] < -CL_SINK - 0.01
        for lj, o2 in enumerate(lobes):
            if lj != li:
                hv |= lobe_in(o2, V, 0.985); hc |= lobe_in(o2, cen, 0.985)
        F = F[~(hv[F].all(1) & hc)]
        used = np.unique(F)
        re = -np.ones(len(V), int); re[used] = np.arange(len(used)) + len(b.v)
        for i in used:
            b.v.append(V[i]); b.n.append(N[i]); b.uv.append(lb['uv']); b.c.append((1.0, 0.0, 1.0))
        for f3 in F:
            b.f.append(tuple(int(re[i]) for i in f3)); b.tag.append(1)


def clump_plan(prm):
    """A piece's leaves, seeded, the same at every LOD: dicts stem, d (stem to tip), side, L, n (the baked normal), r, uv."""
    key = (prm['seed'], 'tuft' in prm)
    if key in _cl_cache:
        return _cl_cache[key]
    rng = np.random.default_rng(prm['seed'])
    leaves = []
    if 'tuft' in prm:
        outer, inner = prm['tuft']
        a0 = rng.uniform(0, 2 * math.pi)
        for ring, cnt, el, ln in ((0, outer, (10, 24), (0.44, 0.50)), (1, inner, (48, 62), (0.40, 0.46))):
            for i in range(cnt):
                az = a0 + ring * 0.9 + 2 * math.pi * (i + rng.uniform(-0.15, 0.15)) / cnt
                e = math.radians(rng.uniform(*el))
                o = np.array([math.cos(az), math.sin(az), 0.0])
                d = o * math.cos(e) + _CL_UP * math.sin(e)
                side = np.cross(_CL_UP, o)
                L = float(rng.uniform(*ln))
                stem = o * 0.03 + np.array([0, 0, 0.02])
                # the outer leaves' normal their own upper side's (near up: the top tone); the inner ones' 50 degrees off up
                t = e if ring == 0 else math.radians(50)
                n = clump_jitter(rng, _CL_UP * math.cos(t) - o * math.sin(t), CL_JIT if ring == 0 else 0.0)
                leaves.append({'stem': stem, 'd': d, 'side': side, 'L': L, 'n': n, 'r': 1.0 if n[2] > math.cos(math.radians(35)) else 0.8,
                               'uv': (float(rng.uniform(0.04, 0.70)), float(rng.uniform(0.22, 0.96)))})
        _cl_cache[key] = leaves
        return leaves
    lobes = clump_lobes(prm)
    cand = []
    for li, lb in enumerate(lobes):
        TH, PH = np.meshgrid(np.radians(np.arange(26.0, 104.0, 6.0)), 2 * math.pi * (np.arange(20) + rng.uniform(0, 1)) / 20)
        TH, PH = TH.ravel(), PH.ravel()
        P, N = lobe_pt(lb, TH, PH), lobe_n(lb, TH, PH)
        ok = (P[:, 2] > 0.10) & (N[:, 2] > math.cos(math.radians(88))) & (N[:, 2] < math.cos(math.radians(25)))
        for lj, o2 in enumerate(lobes):
            if lj != li:
                ok &= ~lobe_in(o2, P, 1.03)
        for p, n in zip(P[ok], N[ok]):
            al = math.degrees(math.acos(n[2]))
            o = np.array([n[0], n[1], 0.0]); o /= np.linalg.norm(o) + 1e-9
            e = math.radians(CL_EL[0] - CL_EL[1] * al + rng.uniform(-CL_EL[2], CL_EL[2]))
            roll = math.radians(rng.uniform(-14, 14))
            L, out = float(rng.uniform(*prm['leaf'])), float(rng.uniform(*CL_OUT))
            d = o * math.cos(e) + _CL_UP * math.sin(e)
            side = np.cross(_CL_UP, o)
            side = side * math.cos(roll) + np.cross(d, side) * math.sin(roll)
            stem = p - d * L * (1 - out)
            # the free part (its middle, its tip, its two upper lobes) clear of every lobe and over the ground
            fr = np.array([stem + d * L * y + side * L * CL_WIDE * x for x, y in ((0, 1 - 0.5 * out), (0, 1.0), (0.40, 0.74), (-0.40, 0.74))])
            if fr[:, 2].min() < 0.03 or any(lobe_in(o2, fr, 1.0).any() for o2 in lobes):
                continue
            cand.append({'stem': stem, 'd': d, 'side': side, 'L': L, 'n': n, 'mid': fr[0],
                         'r': 1.0 if al < 35 else 0.8 if al < 69.5 else 0.45, 'uv': lb['uv']})
    # the leaves: the candidates farthest from those already picked (a seeded weight breaks the lattice)
    if cand:
        mids = np.array([c['mid'] for c in cand])
        w = rng.uniform(0.7, 1.0, len(cand))
        pick = [int(rng.integers(len(cand)))]
        dmin = np.linalg.norm(mids - mids[pick[0]], axis=1)
        while len(pick) < prm['leaves']:
            i = int(np.argmax(dmin * w))
            if dmin[i] < CL_GAP:
                break
            pick.append(i); dmin = np.minimum(dmin, np.linalg.norm(mids - mids[i], axis=1))
        leaves = [cand[i] for i in pick]
    _cl_cache[key] = leaves
    return leaves


def clump_piece(prm, lod, proxy=False):
    """A clump or a tuft at a LOD (b.tag: 0 a leaf's face, 1 the mass's), or its shadow caster (the mass alone at lod 2;
    a tuft: a lump)."""
    b = Build()
    b.tag = []
    if proxy and 'tuft' in prm:
        lump(b, np.random.default_rng(prm['seed'] + 7), np.array([0, 0, 0.12]), 0.36, 0.17, nu=6, nv=3)
        return b
    if 'lobes' in prm:
        clump_mass(b, clump_lobes(prm), 2 if proxy else lod)
        if proxy:
            return b
    pts, tris = CL_BLADE[lod]
    for lf in clump_plan(prm):
        base = len(b.v)
        for x, y in pts:
            b.v.append(lf['stem'] + lf['side'] * x * lf['L'] * CL_WIDE + lf['d'] * y * lf['L'])
            b.n.append(lf['n']); b.uv.append(lf['uv']); b.c.append((lf['r'], float(y), 0.0))
        for t in tris:
            b.f.append(tuple(base + i for i in t)); b.tag.append(0)
    return b


def clump_tex():
    """clump_dabs.png: an opaque sheet of flat green-teal dabs (a lobe and its leaves sample ONE point of it: their own
    value, none inside), its foot band dark (round 1's hull; nothing samples it now)."""
    from PIL import Image
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from env_rocks import dab_sheet
    N = 256
    img = dab_sheet(N, '#5c8c70', 53, tile=2.0, scales=(0.5, 0.22), step=0.08)
    img[int(N * 0.88):] = img[int(N * 0.88):] * 0.38
    out = os.path.join(OUT, 'clump_dabs.png')
    Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(out)
    print(out)


def mesh_clump():
    import bpy
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mat = bpy.data.materials.new('Leaves_OwnClump')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    ti = nt.nodes.new('ShaderNodeTexImage'); ti.image = bpy.data.images.load(os.path.join(OUT, 'clump_dabs.png'))
    nt.links.new(ti.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.85
    mat.use_backface_culling = False
    tris = []
    for lod in range(4):
        b = Build()
        for v, (nm, prm) in enumerate(CLUMP.items()):
            pb = clump_piece(prm, min(lod, 2), proxy=lod == 3)
            pack_into(b, pb, (v + 0.5) / 8)
        tris.append(to_blender(bpy, f'lod{lod}' if lod < 3 else 'shadow', b, [mat])[1])
    out = os.path.join(OUT, 'clump.gltf')
    export_gltf(bpy, out)
    print(f'{out} tris lod0/1/2/shadow: {tris}')


CL_FIRE = (-0.83, -0.55)      # the sheet's fire: from the left and the camera's side (the stage's first clump)


def clump_view(b, pitch, ppm=78.0, pad=0.25, dabs=None, yaw=0.0, fire=None):
    """A piece (turned yaw degrees) drawn flat from 'pitch' degrees down (90: from above; the camera looks along +y),
    the baked normal carried to every pixel. Without 'fire': three steps of the normal's rise (n.up > 0.8 top, > 0.35
    body, else side: the numbers' classes). With it (a level direction TO the fire): the fire's side, the tops, the
    far side, as the target's bush. Magenta: the mass seen from inside (a hole). Returns the picture (H x W x 3) and
    the numbers (shares of the piece's pixels; 'rim': the outline's share made by leaves)."""
    P = np.array(b.v, float); N = np.array(b.n, float); C = np.array(b.c, float)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-9
    if yaw:
        ya = math.radians(yaw)
        Rz = np.array([[math.cos(ya), -math.sin(ya), 0], [math.sin(ya), math.cos(ya), 0], [0, 0, 1.0]])
        P, N = P @ Rz.T, N @ Rz.T
    a = math.radians(pitch)
    up = np.array([0, math.sin(a), math.cos(a)]); fw = np.array([0, math.cos(a), -math.sin(a)])
    sx = P[:, 0] * ppm; sy = -(P @ up) * ppm; dz = P @ fw
    x0 = sx.min() - pad * ppm; y0 = sy.min() - pad * ppm
    W = int(sx.max() - x0 + pad * ppm) + 1; H = int(sy.max() - y0 + pad * ppm) + 1
    sx -= x0; sy -= y0
    zb = np.full((H, W), 1e9); kind = np.zeros((H, W), np.uint8); val = np.ones((H, W)); nb = np.zeros((H, W, 3))
    for fi, f in enumerate(b.f):
        leaf = b.tag[fi] == 0
        tone = 1.0
        if dabs is not None:
            u, v = b.uv[f[0]]
            tone = float(dabs[int((1 - v) * (dabs.shape[0] - 1)), int(u * (dabs.shape[1] - 1))])
        for t in range(1, len(f) - 1):
            i0, i1, i2 = f[0], f[t], f[t + 1]
            xa, ya_, xb, yb, xc, yc = sx[i0], sy[i0], sx[i1], sy[i1], sx[i2], sy[i2]
            ar = (xb - xa) * (yc - ya_) - (xc - xa) * (yb - ya_)
            if abs(ar) < 1e-6:
                continue
            k = 1 if leaf else (3 if np.cross(P[i1] - P[i0], P[i2] - P[i0]) @ fw > 0 else 2)
            u0, u1 = max(0, int(min(xa, xb, xc))), min(W, int(max(xa, xb, xc)) + 2)
            v0, v1 = max(0, int(min(ya_, yb, yc))), min(H, int(max(ya_, yb, yc)) + 2)
            X, Y = np.meshgrid(np.arange(u0, u1) + 0.5, np.arange(v0, v1) + 0.5)
            w1 = ((X - xa) * (yc - ya_) - (xc - xa) * (Y - ya_)) / ar
            w2 = ((xb - xa) * (Y - ya_) - (X - xa) * (yb - ya_)) / ar
            w0 = 1 - w1 - w2
            z = w0 * dz[i0] + w1 * dz[i1] + w2 * dz[i2]
            m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0) & (z < zb[v0:v1, u0:u1])
            zb[v0:v1, u0:u1][m] = z[m]; kind[v0:v1, u0:u1][m] = k; val[v0:v1, u0:u1][m] = tone
            nb[v0:v1, u0:u1][m] = (w0[..., None] * N[i0] + w1[..., None] * N[i1] + w2[..., None] * N[i2])[m]
    nb /= np.maximum(np.linalg.norm(nb, axis=2, keepdims=True), 1e-9)
    on = kind > 0
    cls = np.where(on, np.where(nb[..., 2] > 0.8, 1, np.where(nb[..., 2] > 0.35, 2, 3)), 0)
    if fire is None:
        pal = np.array([[0.19, 0.21, 0.19], [0.56, 0.76, 0.50], [0.29, 0.50, 0.42], [0.15, 0.29, 0.30]])
        img = pal[cls] * val[..., None]
    else:
        lit = nb @ np.array([fire[0], fire[1], 0.0]) > 0.30
        pal = np.array([[0.19, 0.21, 0.19], [0.62, 0.72, 0.33], [0.32, 0.46, 0.31], [0.11, 0.23, 0.26]])
        img = pal[np.where(on, np.where(lit & (nb[..., 2] > -0.2), 1, np.where(nb[..., 2] > 0.55, 2, 3)), 0)] * val[..., None]
    img[kind == 3] = (1.0, 0.0, 1.0)
    edge = on & ~(np.roll(on, 1, 0) & np.roll(on, -1, 0) & np.roll(on, 1, 1) & np.roll(on, -1, 1))
    npx = max(1, int(on.sum()))
    num = {'top': float((cls == 1).sum()) / npx, 'body': float((cls == 2).sum()) / npx, 'side': float((cls == 3).sum()) / npx,
           'rim': float((edge & (kind == 1)).sum()) / max(1, int(edge.sum())), 'inside': float((kind == 3).sum()) / npx,
           'leafpx': float((kind == 1).sum()) / npx,
           'across': (float(P[:, 0].max() - P[:, 0].min()), float(P[:, 1].max() - P[:, 1].min())), 'tall': float(P[:, 2].max())}
    return np.clip(img, 0, 1), num


def clump_sheet(out):
    """The proof picture (a piece a row: from above in the numbers' classes; from the play camera's 50 degrees with
    the fire's tones at yaw 0, yaw 140, lod1, lod2) and the numbers."""
    from PIL import Image
    dp = os.path.join(OUT, 'clump_dabs.png')
    dabs = None
    if os.path.exists(dp):
        d = np.asarray(Image.open(dp).convert('L'), float) / 255
        dabs = d / d[: int(d.shape[0] * 0.8)].mean()
    rows = []
    for nm, prm in CLUMP.items():
        cells = []
        for lod, pitch, yaw, fire in ((0, 90, 0, None), (0, 50, 0, CL_FIRE), (0, 50, 140, CL_FIRE), (1, 50, 0, CL_FIRE), (2, 50, 0, CL_FIRE)):
            b = clump_piece(prm, lod)
            img, _ = clump_view(b, pitch, dabs=dabs, yaw=yaw, fire=fire)
            num = clump_view(b, pitch, dabs=None, yaw=yaw)[1]
            cells.append(img)
            nleaf = sum(1 for t in b.tag if t == 0) // len(CL_BLADE[lod][1])
            ntri = sum(len(f) - 2 for f in b.f)
            print(f"{nm} lod{lod} pitch {pitch} yaw {yaw}: leaves {nleaf} tris {ntri} (mass {sum(1 for t in b.tag if t == 1)}) "
                  f"top/body/side {num['top']:.2f}/{num['body']:.2f}/{num['side']:.2f} rim {num['rim']:.2f} leaf px {num['leafpx']:.2f} "
                  f"inside {num['inside']:.3f} across {num['across'][0]:.2f} x {num['across'][1]:.2f} tall {num['tall']:.2f}")
        pb = clump_piece(prm, 0, proxy=True)
        print(f'{nm} shadow tris {sum(len(f) - 2 for f in pb.f)}')
        h = max(c.shape[0] for c in cells)
        rows.append(np.concatenate([np.pad(c, ((0, h - c.shape[0]), (0, 8), (0, 0)), constant_values=0.19) for c in cells], 1))
    w = max(r.shape[1] for r in rows)
    sheet = np.concatenate([np.pad(r, ((0, 8), (0, w - r.shape[1]), (0, 0)), constant_values=0.19) for r in rows], 0)
    Image.fromarray((sheet * 255 + 0.5).astype(np.uint8)).save(out)
    print(out)


def mesh(species):
    import bpy
    if species == 'clump':
        return mesh_clump()
    if species == 'spruce' and arg('--form', 'tiers') == 'tiers':
        return mesh_spruce_tiers()   # (L1 C3a; --form real: E4's whorls of spray cards, kept to compare)
    if species == 'alder' and arg('--form', 'clusters') == 'clusters':
        return mesh_alder_clusters()   # (L1 C3a; --form real: E4's leaf-clump cards, kept to compare)
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
    if argv and argv[0] == 'tex' and species == 'clump':
        clump_tex()
    elif argv and argv[0] == 'sheet' and species == 'clump':
        clump_sheet(arg('--out', os.path.join(OUT, '_clump_sheet.png')))
    elif argv and argv[0] == 'tex':
        tex(species)
    elif argv and argv[0] == 'mesh':
        mesh(species)
    else:
        print(__doc__)
