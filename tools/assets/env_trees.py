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
    """One branch spray in a CW x CH cell: rgb (sRGB 0-1), alpha, height. Drawn as strokes at one
    brush scale (a needle stroke, about 4 px wide at 512): a dark mass along each twig first, then
    its needles over it, lighter toward the tips; drawn at twice the size and halved (smooth edges)."""
    import cv2
    rng = np.random.default_rng(seed)
    S = 2
    W, H = CW * S, CH * S
    col = np.zeros((H, W, 3), np.uint8)
    al = np.zeros((H, W), np.uint8)
    hg = np.zeros((H, W), np.uint8)
    pal = [srgb(h) for h in ('#0c1914', '#163026', '#244536', '#3a5f47', '#5a7d58')]

    def shade(v):
        v = float(np.clip(v, 0, 0.999)) * (len(pal) - 1)
        i = int(v); f = v - i
        return pal[i] * (1 - f) + pal[i + 1] * f

    bx, by = W / 2 + rng.uniform(-12, 12) * S, H - 10 * S
    tx, ty = W / 2 + rng.uniform(-50, 50) * S, 20 * S
    bend = rng.uniform(-40, 40) * S

    def axis(t):
        return np.array([bx + (tx - bx) * t + bend * math.sin(math.pi * t), by + (ty - by) * t])

    twigs = []  # (points Nx2, base value, needle length px, order)

    def path(p0, ang, length, curl, n=24):
        pts = [np.array(p0, np.float64)]
        for i in range(n):
            a = ang + curl * (i / n)
            pts.append(pts[-1] + np.array([math.cos(a), math.sin(a)]) * length / n)
        return np.array(pts)

    k, t = 0, 0.05
    while t < 0.94:
        side = 1 if k % 2 == 0 else -1
        p, q = axis(t), axis(min(t + 0.01, 1))
        ad = math.atan2(q[1] - p[1], q[0] - p[0])
        env = math.sin(math.pi * min(1.0, 0.18 + 0.95 * t)) ** 0.7 * (1 - 0.45 * t)
        ln = W * 0.5 * env * rng.uniform(0.85, 1.05)
        if ln > 16 * S:
            pts = path(p, ad + side * math.radians(rng.uniform(44, 58)), ln, side * math.radians(rng.uniform(-14, 4)))
            twigs.append((pts, 0.12 + 0.25 * t, (36 - 12 * t) * S, 1 + t))
            if ln > 80 * S:
                for f in (0.38, 0.66):
                    sp = pts[int(f * (len(pts) - 1))]
                    twigs.append((path(sp, ad + side * math.radians(rng.uniform(70, 95)), ln * 0.34, 0, 8), 0.3 + 0.3 * t, 28 * S, 1.2 + t))
        t += rng.uniform(0.034, 0.044)
        k += 1
    twigs.append((np.array([axis(i / 40) for i in range(41)]), 0.1, 38 * S, 3))
    twigs.sort(key=lambda tw: tw[3])
    # (every twig's dark mass first, then every twig's needles: no mass is laid over needles)
    for pts, v0, nl, order, mass in [tw + (m,) for m in (True, False) for tw in twigs]:
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        L = seg.sum()
        cum = np.concatenate([[0], np.cumsum(seg)])
        # the dark mass under the needles (the shadowed inside of the clump)
        for i in range(len(pts) - 1 if mass else 0):
            s = cum[i] / L
            w = int(nl * (1.35 - 0.6 * s))
            c = (shade(v0 - 0.2) * 255).astype(int).tolist()
            a, b = tuple(int(x) for x in pts[i]), tuple(int(x) for x in pts[i + 1])
            cv2.line(col, a, b, c, w, cv2.LINE_AA); cv2.line(al, a, b, 255, w, cv2.LINE_AA)
            cv2.line(hg, a, b, int(60 + 30 * order), w, cv2.LINE_AA)
        # the needles: forward-raking strokes both sides, base to tip
        step = 3.2 * S
        for d0 in (np.arange(0, L, step) if not mass else []):
            s = d0 / L
            i = min(np.searchsorted(cum, d0) - 1, len(pts) - 2)
            i = max(i, 0)
            f = (d0 - cum[i]) / max(seg[i], 1e-6)
            p = pts[i] + (pts[i + 1] - pts[i]) * f
            dirv = (pts[i + 1] - pts[i]) / max(seg[i], 1e-6)
            ang0 = math.atan2(dirv[1], dirv[0])
            for side in (-1, 1):
                a = ang0 + side * math.radians(rng.uniform(38, 66))
                ln = nl * (1 - 0.45 * s) * rng.uniform(0.75, 1.15)
                e = p + np.array([math.cos(a), math.sin(a)]) * ln
                # lit toward the needle tips and the twig's tip; a cooler top light in places
                v = v0 + 0.55 * s ** 0.8 + rng.normal(0, 0.06) + 0.08 * (side > 0)
                c = (shade(v) * 255).astype(int).tolist()
                pa, pe = tuple(int(x) for x in p), tuple(int(x) for x in e)
                cv2.line(col, pa, pe, c, int(4.2 * S), cv2.LINE_AA)
                cv2.line(al, pa, pe, 255, int(4.2 * S), cv2.LINE_AA)
                cv2.line(hg, pa, pe, int(90 + 30 * order + 40 * s), int(4.2 * S), cv2.LINE_AA)
    col = cv2.resize(col, (CW, CH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    al = cv2.resize(al, (CW, CH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    hg = cv2.resize(hg, (CW, CH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    # the cut-out's colour premultiplied by its coverage: unmultiply
    col = col / np.maximum(al, 1e-3)[..., None] * (al > 0)[..., None]
    col = np.clip(col, 0, 1)
    ys = np.mgrid[0:CH, 0:CW][0].astype(np.float32)
    col *= (0.72 + 0.28 * smooth(0, 0.6, 1 - ys / CH))[..., None]
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
        self.v, self.n, self.uv, self.f = [], [], [], []

    def quad_grid(self, P, N, UV, nu, nv):
        """P, N, UV: (nv+1) x (nu+1) arrays of points, normals, uvs; faces between them."""
        base = len(self.v)
        for j in range(nv + 1):
            for i in range(nu + 1):
                self.v.append(P[j][i]); self.n.append(N[j][i]); self.uv.append(UV[j][i])
        w = nu + 1
        for j in range(nv):
            for i in range(nu):
                a = base + j * w + i
                self.f.append((a, a + 1, a + w + 1, a + w))


def crown_normal(p, cn, d, H):
    """Out from the trunk and up, a little of the card's own: the crown shades as one mass."""
    r = np.array([p[0], p[1], 0.0])
    ln = np.linalg.norm(r)
    r = r / ln if ln > 0.15 else np.array([d[0], d[1], 0.0]) / max(np.linalg.norm(d[:2]), 1e-6)
    t = np.clip(p[2] / H, 0, 1)
    n = r * 0.7 + np.array([0, 0, 0.6 + 0.3 * t]) + cn * 0.3
    return n / np.linalg.norm(n)


def card(b, c0, d, length, width, roll, arch, droop, j, H, segs_l=2, segs_w=2):
    """A spray card from c0 along d (its foot at c0), bent: arched across, drooping along."""
    side, up = frame(d)
    cr, sr = math.cos(roll), math.sin(roll)
    side, up = side * cr + up * sr, up * cr - side * sr
    u0, v0, du, dv = cell_uv(j)
    P, N, UV = [], [], []
    for jl in range(segs_l + 1):
        s = jl / segs_l
        rowP, rowN, rowU = [], [], []
        for iw in range(segs_w + 1):
            w = iw / segs_w * 2 - 1
            p = c0 + d * length * s + side * (w * width / 2) + up * (arch * (1 - w * w) * width - droop * s * s * length - 0.12 * width * w * w)
            rowP.append(p)
            rowN.append(crown_normal(p, up, d, H))
            rowU.append((u0 + (w + 1) / 2 * du * 0.96 + du * 0.02, v0 + s * dv * 0.97 + dv * 0.015))
        P.append(rowP); N.append(rowN); UV.append(rowU)
    b.quad_grid(P, N, UV, segs_w, segs_l)


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
    b.quad_grid(P, N, UV, sides, rings)


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
                ln = seg * 1.3
                wd = ln * (0.56 if lod == 0 else 0.62) * rng.uniform(0.9, 1.1)
                card(b, p - dd * seg * 0.12, dd, ln, wd, rng.normal(0, 0.3), 0.12, 0.08 + 0.1 * (1 - t), int(rng.integers(0, 6)), H,
                     segs_l=(2, 1, 1)[lod], segs_w=(2, 1, 1)[lod])
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
        b.quad_grid(P, N, UV, 1, 1)
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
        for lod in range(3):
            b = spruce(prm['H'], prm['R'], prm['seed'], lod)
            me = bpy.data.meshes.new(f'lod{lod}')
            me.from_pydata([tuple(p) for p in b.v], [], b.f)
            uvl = me.uv_layers.new(name='UV')
            for poly in me.polygons:
                for li in poly.loop_indices:
                    uvl.data[li].uv = b.uv[me.loops[li].vertex_index]
            me.normals_split_custom_set_from_vertices([tuple(n) for n in b.n])
            me.materials.append(mat)
            ob = bpy.data.objects.new(f'lod{lod}', me)
            bpy.context.scene.collection.objects.link(ob)
            tris.append(sum(len(p.vertices) - 2 for p in me.polygons))
        out = os.path.join(OUT, f'{species}_{size}.gltf')
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLTF_SEPARATE', export_texture_dir='', export_normals=True,
                                  export_tangents=False, export_materials='EXPORT', export_image_format='AUTO',
                                  export_keep_originals=True, export_yup=True, export_apply=True)
        print(f'{out} tris lod0/1/2: {tris}')


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    species = arg('--species', 'spruce')
    if argv and argv[0] == 'tex':
        tex(species)
    elif argv and argv[0] == 'mesh':
        mesh(species)
    else:
        print(__doc__)
