"""Our own ground materials for the Godot terrain (shaders/terrain.gdshader).

    python tools/assets/env_ground.py [--only setts]

The seven CC0 Poly Haven sets that tools/assets/ground.py names are raw
material only: they are fetched (1K) into
survivorsunchained_inputs/raw_materials/ground/<asset>/ with their sha256 in
SOURCE.txt there, never into the repo. Each is rebuilt here into this
country's palette (a cold, damp northern forest): the photo's luminance
keeps its grain, but its mean colour, saturation and value are replaced by
ours, blended between two palette colours by our own tileable multi-octave
noise, which also works into the height, roughness and normal. The setts
are not a photo at all: jittered Voronoi stones in curved courses over an
8 m tile, our own tone, hue, wear, tilt and rounded height per stone, dark
dirty joints; cobblestone_05 gives only high-passed surface grain.

Writes godot/art/ground/:
  albedo.jpg, normal.jpg, arh.jpg  7 layers x 1024 (texture arrays; arh =
                                   R occlusion, G roughness, B height)
  setts_albedo.jpg, setts_normal.jpg, setts_arh.jpg
                                   3 variants x 2048 of the 8 m setts tile.
                                   Their outer stones are shared, so the
                                   shader can pick a variant per 8 m tile
                                   without cutting a stone.
  ground.json                      the layers and their tile sizes
"""
import argparse
import hashlib
import json
import colorsys
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'assets'))
import ground  # noqa: E402  (the raw sets' names and their download)

RAW = Path(r'C:\Users\munch\Desktop\survivorsunchained_inputs\raw_materials\ground')
OUT = ROOT / 'godot' / 'art' / 'ground'
N = 1024
SN = 1024            # setts px per tile
SETTS_M = 4.0        # setts tile, metres
VARIANTS = 3

AUTHORS = {
    'sparse_grass': 'Amal Kumar', 'forest_leaves_02': 'Rob Tuytel',
    'forest_ground_04': 'Rob Tuytel, Rico Cilliers', 'mud_forest': 'eye-candy.xyz',
    'cobblestone_05': 'Rob Tuytel', 'mossy_rock': 'Rob Tuytel', 'burned_ground_01': 'Rob Tuytel',
}

# name, raw asset, tile metres, palette A and B (sRGB 0-255), how much of the
# photo's own colour variation is kept (around our mean), luma contrast,
# our noise in value / height / roughness, roughness offset.
LAYERS = [
    # Meadow: muted olive-green to straw, never orange.
    ('grass', 'sparse_grass', 2.0, (64, 74, 48), (90, 89, 60), 0.22, 1.15, 0.10, 0.45, 0.06, 0.0),
    # Forest floor: brown litter, a little moss.
    ('leaves', 'forest_leaves_02', 3.0, (80, 66, 50), (64, 60, 46), 0.30, 0.95, 0.08, 0.25, 0.05, 0.0),
    # Trodden earth: neutral grey-brown, not pale gravel, not lilac.
    ('dirt', 'forest_ground_04', 3.15, (78, 70, 60), (66, 62, 56), 0.25, 1.0, 0.08, 0.30, 0.06, -0.02),
    # Mud: dark and wet.
    ('mud', 'mud_forest', 2.35, (48, 42, 35), (38, 35, 31), 0.20, 1.0, 0.07, 0.20, 0.08, -0.12),
    ('stone', None, SETTS_M, None, None, 0, 0, 0, 0, 0, 0),
    # Rock: grey, its moss kept.
    ('rock', 'mossy_rock', 3.0, (98, 98, 92), (84, 86, 78), 0.65, 1.0, 0.08, 0.20, 0.05, 0.0),
    # Blight: ash and char.
    ('blight', 'burned_ground_01', 1.5, (72, 70, 68), (46, 45, 44), 0.20, 1.05, 0.10, 0.25, 0.05, 0.0),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fetch_raw():
    ground.CACHE = RAW
    lines = []
    for _, asset in ground.LAYERS:
        f = ground.files(asset)
        lines.append(f'Poly Haven {asset} - https://polyhaven.com/a/{asset} (CC0; {AUTHORS[asset]})')
        for k in ('diff', 'nor', 'arm', 'disp'):
            lines.append(f'  {sha(f[k])} *{asset}/{f[k].name}')
    (RAW / 'SOURCE.txt').write_text(
        'Raw material only for tools/assets/env_ground.py (the Godot ground); not shipped.\n'
        'Fetched 1K from the Poly Haven API by tools/assets/ground.py:files().\nsha256:\n'
        + '\n'.join(lines) + '\n')


# Tileable noise ------------------------------------------------------------

def fbm(n, rng, cell, octaves=4, gain=0.55):
    """Periodic multi-octave noise over an n-px tile, features about `cell` px, -1..1."""
    out = np.zeros((n, n))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(cell / (2 ** o), 0.7)
        w = gaussian_filter(rng.standard_normal((n, n)), s, mode='wrap')
        out += amp * w / (w.std() + 1e-9)
        tot += amp
        amp *= gain
    out /= tot
    return np.clip(out / (3 * out.std()), -1, 1)


def luma(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def normal_from(h, px_m, strength=1.0):
    """OpenGL normal (green toward the image top) from a height in metres."""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / (2 * px_m) * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / (2 * px_m) * strength
    n = np.stack([-dx, dy, np.ones_like(h)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def udn(a, b):
    """Two tangent-space normals, detail added (UDN)."""
    n = np.stack([a[..., 0] + b[..., 0], a[..., 1] + b[..., 1], a[..., 2]], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def load(path, mode='RGB', size=N):
    im = Image.open(path)
    if im.mode in ('I;16', 'I;16B', 'I'):
        im = im.point(lambda v: v / 256).convert('L')
    im = im.convert(mode)
    if im.size != (size, size):
        im = im.resize((size, size), Image.LANCZOS)
    return np.asarray(im).astype(np.float64) / 255


# The photo layers ----------------------------------------------------------

def build_layer(spec, seed):
    name, asset, metres, ca, cb, keep, contrast, vn, hn, rn, roff = spec
    rng = np.random.default_rng(seed)
    d = RAW / asset
    alb = load(d / 'diff.jpg')
    nor = load(d / 'nor.png') * 2 - 1
    arm = load(d / 'arm.jpg')
    hgt = load(d / 'disp.png', 'L')
    lo, hi = np.percentile(hgt, [1, 99])
    hgt = np.clip((hgt - lo) / max(hi - lo, 1e-3), 0, 1)

    px_m = metres / N
    big = fbm(N, rng, N / 3, 3)          # a tile's broad colour drift
    mid = fbm(N, rng, N / 10, 4)         # value and height, about 0.3 m
    fine = fbm(N, rng, N / 40, 3)        # roughness and grain

    L = luma(alb)
    Lm = L.mean()
    chroma = alb - L[..., None]
    chroma -= chroma.reshape(-1, 3).mean(0)
    t = np.clip(0.5 + 0.5 * big + 0.25 * mid, 0, 1)[..., None]
    A = np.array(ca) / 255
    B = np.array(cb) / 255
    pal = A * (1 - t) + B * t
    pl = luma(pal)
    val = np.power(np.clip(L / Lm, 0, 4), contrast) * (1 + vn * mid + vn * 0.5 * fine)
    out = pal / pl[..., None] * (pl * val)[..., None] + chroma * keep
    out = np.clip(out, 0, 1)

    h = np.clip(hgt * (1 - hn) + (0.5 + 0.5 * mid) * hn * 0.8 + (0.5 + 0.5 * fine) * hn * 0.2, 0, 1)
    if name == 'grass':
        # Clumps that stand over a road's edge.
        clump = np.clip(fbm(N, rng, N / 14, 2) * 1.6, -1, 1)
        h = np.clip(h * 0.7 + (0.5 + 0.5 * clump) * 0.3, 0, 1)
    lo, hi = np.percentile(h, [1, 99])
    h = np.clip((h - lo) / max(hi - lo, 1e-3), 0, 1)

    rough = np.clip(arm[..., 1] + rn * fine + roff, 0.05, 1)
    ao = arm[..., 0]
    # Our noise's own relief, laid over the photo's normal (2 cm of it).
    n2 = normal_from((h - 0.5) * 0.02 * hn, px_m)
    n = udn(nor / np.linalg.norm(nor, axis=-1, keepdims=True), n2)
    return out, n, np.stack([ao, rough, h], -1)


# The setts -----------------------------------------------------------------
# Judge 3's restage (E3 F): a 4 m authored tile in three variants (the shader picks one per tile by a world-space hash;
# their border stones are shared, so the tiles meet clean), stones 18-30 cm with a few 35-45 cm, joints 2.4-3.4 cm.
# Two steps, so a restyle is a re-bake: setts_sources() lays the stones and writes their masks to tools/assets/setts_src/
# (height, stone id, tone, wear, mud, moss, grain), and bake_setts() turns those masks into albedo, normal and arh.
# Where the street's mud gathers (walls, the well, the stalls) is the shader's: it fills the joints and buries the stone
# edges by this tile's height (arh B: joints about 0.1, a stone's edge about 0.3, its top 0.6-0.95), and drops or sinks
# whole stones by their own random (normal B).

SRC = ROOT / 'tools' / 'assets' / 'setts_src'


def hash2(i, j, v):
    """Per-cell random generator: v = 0 is shared by every variant."""
    return np.random.default_rng((int(i) * 73856093) ^ (int(j) * 19349663) ^ (int(v) * 83492791) ^ 0x5E775)


def setts_layout(variant):
    """The courses (E9e): bands across the tile (shared by every variant, so tiles meet clean top and bottom), each
    cut into dressed setts 12-24 cm long; the stones within 0.35 m of the tile's left and right edges are shared too,
    the rest each variant's own, staggered off the course below. A few flags span two courses. Returns the course
    edges (z) and the stones: a list of dicts (course, u0, u1, the joints' tilts, the stone's own key)."""
    rs = np.random.default_rng(0x5E77)
    hk = rs.uniform(CRS_H[0], CRS_H[1], 64)
    n = int(round(SETTS_M / hk.mean()))
    hk = rs.uniform(CRS_H[0], CRS_H[1], n)
    zk = np.concatenate([[0.0], np.cumsum(hk / hk.sum() * SETTS_M)])
    rv = np.random.default_rng(1000 + variant)
    courses = []
    prev = None
    for k in range(n):
        r0 = hash2(k, 0, 0)
        o = r0.uniform(0.02, 0.2)
        L = lambda r: r.uniform(STONE_L[0], STONE_L[1])
        left = [o]
        while left[-1] < o + EDGE_SHARE:
            left.append(left[-1] + L(r0))
        right = [o + SETTS_M]
        while right[-1] > SETTS_M - EDGE_SHARE:
            right.append(right[-1] - L(r0))
        right = right[::-1]
        a, b = left[-1], right[0]
        m = max(1, int(round((b - a) / np.mean(STONE_L))))
        ls = rv.uniform(STONE_L[0], STONE_L[1], m)
        mid = list(a + np.cumsum(ls / ls.sum() * (b - a))[:-1])
        # Stagger: no joint within 4 cm of one in the course below.
        if prev is not None:
            for i, x in enumerate(mid):
                d = prev - x
                j = np.argmin(np.abs(d))
                if abs(d[j]) < STAGGER:
                    mid[i] = x - np.sign(d[j] or 1) * (STAGGER - abs(d[j]) + 0.01)
        js = np.array(left + mid + right)
        keep = np.concatenate([[True], np.diff(js) > 0.07])
        js = js[keep]
        js[-1] = o + SETTS_M
        tl = np.array([hash2(k, int(round(x * 1000)), 0 if (x < o + EDGE_SHARE + 0.3 or x > SETTS_M - EDGE_SHARE - 0.3) else variant + 1).normal(0, TILT) for x in js])
        tl[-1] = tl[0]
        courses.append(dict(z0=zk[k], z1=zk[k + 1], j=js, t=tl, o=o))
        prev = np.concatenate([js, js - SETTS_M, js + SETTS_M])
    stones = []
    for k, c in enumerate(courses):
        for i in range(len(c['j']) - 1):
            u0, u1 = c['j'][i], c['j'][i + 1]
            shared = u0 < c['o'] + EDGE_SHARE or u1 > SETTS_M - EDGE_SHARE
            stones.append(dict(k=k, k1=k, u0=u0, u1=u1, t0=c['t'][i], t1=c['t'][i + 1],
                               key=(k, int(round(u0 * 1000)), 0 if shared else variant + 1)))
    # The flags: a few big stones over two courses, in each variant's own middle.
    for f in range(FLAGS):
        for _ in range(40):
            k = int(rv.integers(2, n - 3))
            ua = rv.uniform(0.7, SETTS_M - 1.2)
            w = rv.uniform(FLAG_W[0], FLAG_W[1])
            c0, c1 = courses[k], courses[k + 1]
            ia = np.searchsorted(c0['j'], ua); ib = np.searchsorted(c0['j'], ua + w)
            if ia < 1 or ib >= len(c0['j']) or ib - ia < 1:
                continue
            a, b = c0['j'][ia], c0['j'][ib]
            if b - a < FLAG_W[0] * 0.8 or any(s.get('flag') and s['k'] in (k - 1, k, k + 1, k + 2) and s['u1'] > a - 0.3 and s['u0'] < b + 0.3 for s in stones):
                continue
            tt = 0.0
            stones[:] = [s for s in stones if not (s['k'] == k and s['u1'] > a + 0.005 and s['u0'] < b - 0.005)]
            for s in stones:
                if s['k'] == k and abs(s['u1'] - a) < 0.005:
                    s['t1'] = tt
                if s['k'] == k and abs(s['u0'] - b) < 0.005:
                    s['t0'] = tt
            # The course above, re-cut at the flag's edges (the stones it cuts keep their far joints and tilts).
            c = courses[k + 1]
            new = []
            for i in range(len(c['j']) - 1):
                u0, u1 = c['j'][i], c['j'][i + 1]
                if u1 <= a + 0.005 or u0 >= b - 0.005:
                    continue
                if u0 < a - 0.005:
                    new.append((u0, a, c['t'][i], tt))
                if u1 > b + 0.005:
                    new.append((b, u1, tt, c['t'][i + 1]))
            stones[:] = [s for s in stones if not (s['k'] == k + 1 and s['u0'] < b - 0.005 and s['u1'] > a + 0.005)]
            for u0, u1, t0, t1 in new:
                if u1 - u0 > 0.06:
                    stones.append(dict(k=k + 1, k1=k + 1, u0=u0, u1=u1, t0=t0, t1=t1, key=(k + 1, int(round(u0 * 1000)), variant + 1)))
            stones.append(dict(k=k, k1=k + 1, u0=a, u1=b, t0=tt, t1=tt, key=(k, 7000 + f, variant + 1), flag=True))
            break
    return courses, stones


def _stone_look(r, flag, cm):
    """One stone's own tone (sRGB 0-1), wear, tilt, crown and edge: granite greys, some browner, some blue-grey whin,
    a few pale or rosy accents (E9e r2: 90% within 10% of their course's mean value `cm`, the accents 7%; the big
    swings are the shader's 2-6 m layer now, not the stones' own, which read as tone noise)."""
    u = r.uniform(0, 1)
    acc = 0
    if u < 0.60:   # grey granite
        h, s, k = r.uniform(28, 45), r.uniform(0.05, 0.11), 1.0
    elif u < 0.78:  # a warmer, browner stone
        h, s, k = r.uniform(26, 36), r.uniform(0.13, 0.19), 0.98
    elif u < 0.93:  # dark whin, blue-grey
        h, s, k = r.uniform(200, 225), r.uniform(0.03, 0.06), 0.93
    elif u < 0.97:  # a pale one
        h, s, k, acc = r.uniform(32, 46), r.uniform(0.05, 0.09), 1.17, 1
    else:           # rosy granite
        h, s, k, acc = r.uniform(12, 22), r.uniform(0.10, 0.15), 1.0, 2
    if flag:
        h, s, k, acc = r.uniform(30, 42), r.uniform(0.07, 0.12), 1.03, 0
    v = 0.345 * cm * k * (1 + float(np.clip(r.normal(0, 0.035), -0.07, 0.07)))
    tone = np.array(colorsys.hsv_to_rgb(h / 360.0, s, float(np.clip(v, 0.2, 0.5))))
    # (E9e r2, the close camera: worn crowns 2-4 mm, each stone its own height (+-3-5 mm) and tilt (up to 2 degrees),
    # arrises rounded over 1-2 cm.)
    return dict(tone=tone, acc=acc, wear=r.uniform(0, 1) ** 1.3, tilt=np.clip(r.normal(0, 0.018, 2), -0.035, 0.035),
                lift=float(np.clip(r.normal(0, 0.0028), -0.005, 0.005)), top=r.uniform(0.85, 1.0),
                sid=r.uniform(0.1, 0.9), ins=r.uniform(INSET[0], INSET[1], 4), rad=r.uniform(0.012, 0.03) if r.uniform() > 0.12 else r.uniform(0.04, 0.06),
                cham=r.uniform(0.010, 0.020), grad=r.normal(0, 0.04, 2), crown=r.uniform(0.002, 0.004),
                etl=np.clip(r.normal(0, 0.045, 2), -0.08, 0.08))


def _demote_accents(look, S):
    """No two accent stones touching: a pale or rosy stone next to another accent turns plain grey granite."""
    pairs = set()
    for ax in (0, 1):
        for sh in (6, -6):
            a = S; b = np.roll(S, sh, axis=ax)
            d = a != b
            for x, y in zip(a[d].ravel(), b[d].ravel()):
                pairs.add((int(x), int(y)))
    nb = {}
    for x, y in pairs:
        nb.setdefault(x, set()).add(y)
    for i, l in enumerate(look):
        if l['acc'] and any(look[j]['acc'] for j in nb.get(i, ()) if j < i):
            v = colorsys.rgb_to_hsv(*l['tone'])[2] / (1.17 if l['acc'] == 1 else 1.0)
            l['tone'] = np.array(colorsys.hsv_to_rgb(36 / 360.0, 0.08, v)); l['acc'] = 0


def setts_sources(variant):
    """Lay variant `variant`'s stones and return its source masks (all SN x SN, float):
    height (metres), id (stone index), tone (RGB, each stone's own colour), wear (0-1, worn tops), mud (0-1, the dirt
    packed into the joints), moss (0-1, where moss grows in them), grain (-1..1, the stone's surface at 2-5 cm), sid
    (each stone's own random 0.1-0.9, 0 in the joints), stone (0-1, coverage)."""
    courses, stones = setts_layout(variant)
    px = SETTS_M / SN
    cpx = SN / SETTS_M
    g = (np.arange(SN) + 0.5) * px
    X, Z = np.meshgrid(g, g)
    e_t = np.minimum(np.minimum(g, SETTS_M - g), 0.6) / 0.6
    m = np.minimum(e_t[None, :], e_t[:, None])
    m = m * m * (3 - 2 * m)

    def mixed(cell_m, oct_, sd):
        return (fbm(SN, np.random.default_rng(sd), cell_m * cpx, oct_) * (1 - m)
                + fbm(SN, np.random.default_rng(sd + 1 + variant), cell_m * cpx, oct_) * m)
    # The courses bow (each variant its own way, straight at the tile's edge) and wander a little.
    ph = variant * 2.1
    ex = np.sin(np.pi * X / SETTS_M) * np.sin(np.pi * Z / SETTS_M)
    V = (Z + 0.025 * ex * np.sin(2 * np.pi * X / SETTS_M * (1 + variant % 2) + ph) + 0.012 * mixed(0.5, 2, 600)) % SETTS_M
    U = (X + 0.012 * ex * np.sin(2 * np.pi * Z / SETTS_M * 2 + ph)) % SETTS_M
    zk = np.array([c['z0'] for c in courses] + [SETTS_M])
    K = np.clip(np.searchsorted(zk, V, side='right') - 1, 0, len(courses) - 1)
    # Each pixel's stone: its course's stone between the (tilted) joints either side.
    sid_px = np.full((SN, SN), -1, int)
    by_course = {}
    for si, s in enumerate(stones):
        for kk in range(s['k'], s['k1'] + 1):
            by_course.setdefault(kk, []).append(si)
    for k, c in enumerate(courses):
        msk = K == k
        if not msk.any():
            continue
        lst = sorted(by_course.get(k, []), key=lambda si: stones[si]['u0'])
        u0 = np.array([stones[si]['u0'] for si in lst]); u1 = np.array([stones[si]['u1'] for si in lst])
        uu = U[msk].copy()
        uu = np.where(uu < c['o'], uu + SETTS_M, uu)
        vm = V[msk] - 0.5 * (c['z0'] + c['z1'])
        t0 = np.array([stones[si]['t0'] for si in lst]); t1 = np.array([stones[si]['t1'] for si in lst])
        i = np.clip(np.searchsorted(u0, uu, side='right') - 1, 0, len(lst) - 1)
        for _ in range(2):
            i = np.where(uu < u0[i] + t0[i] * vm, np.maximum(i - 1, 0), i)
            i = np.where(uu > u1[i] + t1[i] * vm, np.minimum(i + 1, len(lst) - 1), i)
        sid_px[msk] = np.array(lst)[i]
    ns = len(stones)
    cmean = [1 + float(np.clip(hash2(c_, 0, 77).normal(0, 0.03), -0.06, 0.06)) for c_ in range(len(courses))]
    look = [_stone_look(hash2(*s['key']), s.get('flag', False), cmean[s['k']]) for s in stones]
    _demote_accents(look, sid_px)
    # Per-pixel distance into its stone (a rounded box with its own insets, tilted sides).
    S = sid_px
    Uu = np.where(U < np.array([courses[s['k']]['o'] for s in stones])[S], U + SETTS_M, U)
    za = np.array([courses[s['k']]['z0'] for s in stones]); zb = np.array([courses[s['k1']]['z1'] for s in stones])
    vmid = np.array([0.5 * (courses[s['k']]['z0'] + courses[s['k']]['z1']) for s in stones])
    arr = lambda key: np.array([s[key] for s in stones])
    ins = np.array([l['ins'] for l in look]); rad = np.array([l['rad'] for l in look])
    vm = V - vmid[S]
    dl = Uu - (arr('u0')[S] + arr('t0')[S] * vm) - ins[S, 0]
    dr = (arr('u1')[S] + arr('t1')[S] * vm) - Uu - ins[S, 1]
    Vv = V.copy()
    # (A stone across the tile's top edge: its course is the last; V near 0 belongs to it only if K says so.)
    # (E9e r2: the long sides off true too, each its own few degrees, so no stone is a machined block.)
    etl = np.array([l['etl'] for l in look]); cu0 = 0.5 * (arr('u0') + arr('u1'))
    du = Uu - cu0[S]
    db = Vv - za[S] - ins[S, 2] - etl[S, 0] * du
    dt = zb[S] - Vv - ins[S, 3] - etl[S, 1] * du
    dx = np.minimum(dl, dr); dy = np.minimum(db, dt)
    r_ = rad[S]
    qx, qy = r_ - dx, r_ - dy
    edge = np.where(np.maximum(qx, qy) > 0, r_ - np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)), np.minimum(dx, dy))
    # Chipped, uneven arrises: a few mm over 2-6 cm.
    edge = edge + WOBBLE * fbm(SN, np.random.default_rng(500), cpx * 0.04, 3)
    stone = gaussian_filter((edge > 0).astype(float), 0.6, mode='wrap')
    cham = np.array([l['cham'] for l in look])[S]
    dome = np.clip(edge / cham, 0, 1)
    dome = 1 - (1 - dome) ** 2
    # In-stone position (for the crown, tilt and the value's slow drift over a stone).
    cu = 0.5 * (arr('u0') + arr('u1')); cv = 0.5 * (za + zb)
    hu = 0.5 * (arr('u1') - arr('u0')); hv = 0.5 * (zb - za)
    qu = (Uu - cu[S]) / hu[S]; qv = (V - cv[S]) / hv[S]
    tilt = np.array([l['tilt'] for l in look])[S]
    top = np.array([l['top'] for l in look])[S]
    crown = np.array([l['crown'] for l in look])[S]
    gr = mixed(0.035, 2, 400)
    fine = mixed(0.05, 3, 110)
    lift = np.array([l['lift'] for l in look])[S]
    body = TOP_H * top + lift + crown * (1 - 0.5 * np.clip(qu * qu + qv * qv, 0, 2)) + (tilt[..., 0] * qu * hu[S] + tilt[..., 1] * qv * hv[S])
    # (E9e r2: the stone's height falls to the joint's floor over its rounded arris and a 3 mm side, never a step: the
    # step drew a dark hairline round every stone at the close camera. The joints recessed 5-15 mm, their floors uneven.)
    jf = JOINT_D + 0.003 * mixed(0.15, 2, 120)
    h_m = np.where(edge > 0, dome * np.maximum(body, 0.002) + gr * 0.0006 + 0.0004 * fine,
                   -jf * np.clip(-edge / 0.003, 0, 1) + 0.0012 * fine)
    h_m = gaussian_filter(h_m, 0.5, mode='wrap')
    dirt = mixed(0.6, 4, 100)
    mud = np.clip(0.55 + 0.45 * mixed(0.12, 3, 200) + 0.3 * dirt, 0, 1) * (1 - stone)
    moss = np.clip((-dirt - 0.25) * 2.5, 0, 1) * np.clip(0.5 + 0.8 * mixed(0.08, 2, 210), 0, 1) * (1 - stone)
    h_m += mud * 0.002 * (1 - stone)
    # The tone: each stone's own, drifting a little across it, with a granite speckle and a weathered mottle.
    tone = np.array([l['tone'] for l in look])[S]
    grad = np.array([l['grad'] for l in look])[S]
    speck = fbm(SN, np.random.default_rng(700 + variant), 0.8, 1)
    mott = mixed(0.06, 2, 710)
    tone = tone * (1 + grad[..., 0:1] * qu[..., None] + grad[..., 1:2] * qv[..., None]) * (1 + 0.07 * speck[..., None] + 0.05 * mott[..., None])
    sidv = np.array([l['sid'] for l in look])
    sidm = np.where(stone > 0.5, sidv[S], 0.0)
    wearm = np.array([l['wear'] for l in look])[S] * dome * stone
    src = dict(height=h_m, id=S.astype(float), tone=np.clip(tone, 0, 1), wear=wearm, mud=mud, moss=moss, grain=gr, sid=sidm,
               stone=stone, dome=dome, edge=edge, joint=np.zeros_like(edge))
    if SIZES:
        st = edge > 0
        area = np.bincount(S.ravel(), weights=st.ravel().astype(float), minlength=ns) * px * px
        ok = area > 0.002
        eq = np.sqrt(4 * area[ok] / np.pi)
        ln = (arr('u1') - arr('u0'))[ok]
        print(f'  setts {variant}: stones {ok.sum()} ({ok.sum() / SETTS_M ** 2:.1f}/m2, {np.sqrt(ok.sum()) / SETTS_M:.2f}/m), courses {len(courses)}, '
              f'eq. diameter p5 {np.percentile(eq, 5):.3f} p50 {np.median(eq):.3f} p95 {np.percentile(eq, 95):.3f} max {eq.max():.3f}; '
              f'length p5 {np.percentile(ln, 5):.3f} p50 {np.median(ln):.3f} p95 {np.percentile(ln, 95):.3f}; joint share {1 - st.mean():.3f}', flush=True)
    return src


def bake_setts(src):
    """Albedo, normal and arh (R occlusion, G roughness, B height) from the sources; the look lives here."""
    px = SETTS_M / SN
    stone, dome, h_m, gr, wear = src['stone'], src['dome'], src['height'], src['grain'], src['wear']
    st = stone[..., None]
    lip = 1 - np.clip(dome / 0.25, 0, 1)                                     # the stone's last centimetre or so
    alb = src['tone'] * (1 + GRAIN * gr[..., None]) * (1 + 0.06 * wear[..., None])
    alb *= 1 - 0.10 * lip[..., None]
    # The joints: brown grit and packed dirt, moss where it is never swept.
    # (E9e: grit and sand nearer the stones' value, so the joints draw no dark outline round every stone.)
    grit = np.array([0.31, 0.28, 0.23])
    dirt = np.array([0.25, 0.21, 0.16])
    moss = np.array([0.16, 0.19, 0.10])
    mortar = grit + (dirt - grit) * src['mud'][..., None]
    mortar += (moss - mortar) * src['moss'][..., None] * 0.6
    alb = np.clip(alb * st + mortar * (1 - st), 0, 1)
    rough = (0.84 - 0.08 * wear) * stone + 0.95 * (1 - stone)   # (E9e r2: dry tops about 0.8, so a wet pool reads by its sheen)
    hn = np.clip((h_m + 0.006) / H_SPAN, 0, 1)
    ao = gaussian_filter(np.clip(1 - 0.18 * (1 - stone) - 0.06 * lip, 0, 1), 1.0, mode='wrap')
    n = normal_from(h_m, px, 1.0)
    # The normal's B carries each stone's own random (0.1-0.9; the shader rebuilds z from x and y).
    n[..., 2] = src['sid'] * 2 - 1
    STASH.update(i1=src['id'].astype(int), stone=stone, edge=src['edge'], joint=src['joint'], gr=gr, alb=alb)
    return alb, n, np.stack([ao, np.clip(rough, 0.05, 1), hn], -1)


def save_sources(variant, src):
    SRC.mkdir(parents=True, exist_ok=True)
    def u16(a, lo, hi, name):
        Image.fromarray(np.clip(np.round((a - lo) / (hi - lo) * 65535), 0, 65535).astype(np.uint16)).save(SRC / f'v{variant}_{name}.png')
    u16(src['height'], -0.006, H_SPAN - 0.006, 'height')   # metres, -6 to +18 mm
    Image.fromarray(src['id'].astype(np.uint16)).save(SRC / f'v{variant}_id.png')
    to8(src['tone']).save(SRC / f'v{variant}_tone.png')
    for k in ('wear', 'mud', 'moss', 'sid', 'stone', 'dome'):
        to8(src[k]).save(SRC / f'v{variant}_{k}.png')
    to8(src['grain'] * 0.5 + 0.5).save(SRC / f'v{variant}_grain.png')


def load_sources(variant):
    def f(name):
        return np.asarray(Image.open(SRC / f'v{variant}_{name}.png')).astype(float)
    src = {k: f(k) / 255 for k in ('wear', 'mud', 'moss', 'sid', 'stone', 'dome')}
    src['height'] = f('height') / 65535 * H_SPAN - 0.006
    src['id'] = f('id')
    src['tone'] = f('tone') / 255
    src['grain'] = f('grain') / 255 * 2 - 1
    src['edge'] = src['joint'] = None
    return src


def build_setts(variant, grain=None):
    src = setts_sources(variant)
    return bake_setts(src)


SIZES = '--sizes' in sys.argv
STASH = {}   # the last tile's stones, joints and grain (for a measuring script)
# E9e: dressed setts in courses (the Voronoi field read as a cartoon mosaic at the play camera).
CRS_H = (0.11, 0.155)   # a course's width across the street (m)
STONE_L = (0.12, 0.24)  # a sett's length along its course (m)
EDGE_SHARE = 0.35       # the stones within this of the tile's left and right edges are every variant's
STAGGER = 0.04          # no joint within this of one in the course below
TILT = 0.12             # a joint's lean off square (its slope)
FLAGS, FLAG_W = 3, (0.32, 0.5)   # big flags per variant tile, over two courses, and their length
INSET = (0.004, 0.010)  # each side's own set-back from its joint line (E9e r2: the joints 8-20 mm, plus the wobble)
TOP_H = 0.0075          # the dressed top's height over the joint's lip, reached over the stone's chamfer
JOINT_D = 0.0045        # the joint's floor under the lip (the stones' tops 5-15 mm over it)
H_SPAN = 0.024          # arh B: -6 to +18 mm (E9e r2; was +16, the per-stone heights and tilts need the room)
WOBBLE = 0.004
GRAIN = 0.10


def to8(a):
    return Image.fromarray(np.clip(np.round(a * 255), 0, 255).astype(np.uint8))


def nor8(n):
    return to8(n * 0.5 + 0.5)



# The painted setts (style r2, E3 job 1; the Godot flag --setts-paint) ------------------------------------------------
# A second layout and look beside the first (which stays as it is): an old cobbled square. Chunky, irregular cobbles
# (rough 4-6-sided cells of a power diagram, straight-ish edges, uneven corners), mostly 14-28 cm, about a tenth big
# ones at 30-45 cm, laid in loose wavy courses along x (never a running bond). Each stone a "pillow": a broad flat top,
# a rounded 3-5 cm bevel down to the gap, the top tilted 2-4 degrees (in the normal); its sun-side bevel lit and its far
# bevel dark in the albedo. Dark, narrow, deep gaps (1.5-3 cm); packed dark-brown mud where a stone is missing. Strong
# value between stones (about +/-16%: cream, warm grey, ochre, a few cool grey-blue), 2-3 broad strokes along each
# stone's long axis (+/-6%), no grain.
#   python tools/assets/env_ground.py --paint [--bake] [--sizes]
# writes setts_paint_{albedo,normal,arh}.jpg (3 variants x 1024, as the first) and its masks to tools/assets/setts_src_paint/.

SRC_PAINT = ROOT / 'tools' / 'assets' / 'setts_src_paint'
P_BAND = 0.55              # the tile's border band (m): its stones are shared by all variants, so tiles meet clean
P_ROW = (0.15, 0.23)       # a course's height (m)
P_STEP = (0.85, 1.30)      # a stone's slot along its course, over the course's height
P_JIT = (0.14, 0.16)       # the seeds' jitter (of the slot's width, of the course's height)
P_BIG_P = 0.14             # the big stones: their share, their slot's stretch, their power weight (m^2: they grow into
P_BIG = (1.55, 1.95)       # the courses beside)
P_BIG_W = (0.014, 0.026)
P_MISS_P = 0.035           # the missing stones (packed mud)
P_KK = 700.0               # corners' rounding (1/m)
P_JOINT = 0.0085           # a gap's half width (m), +/- P_JOINT_V along it: gaps 1.3-2.5 cm (wider at the corners)
P_JOINT_V = 0.0030
P_BEVEL = (0.030, 0.048)   # the rounded bevel (m), at most 0.38 of the stone's inradius
P_TOP_H = 0.013            # the top's height over the gap's floor (m)
P_TILT = (2.0, 4.0)        # the top's tilt (degrees), in the normal; a quarter of it in the height
P_WOBBLE = 0.004
P_SUN = np.array([0.866, -0.5])     # toward the sun in the tile (col, row): azimuth 330 (x = cos az, z = sin az; rows = z)
P_STROKE = 0.06                     # the strokes along a stone's long axis, +/-
P_STROKE_W = 0.065                  # their width (m): 2-3 to a stone
# The stones' palettes: (share, hue, saturation, value): warm grey, ochre, cream, a few cool grey-blue. (Lead 4's
# palette tweak toward the target's sunlit cream-grey: less red and a third less saturated, more and paler cream
# stones, under a warm key. Round 3 was ((0.34, 30, 0.12, 0.300), (0.30, 35, 0.27, 0.298), (0.24, 41, 0.13, 0.348),
# (0.12, 212, 0.08, 0.285)); the draws per stone are the same, so the layout doesn't move.)
P_PALETTE = ((0.36, 38.0, 0.08, 0.310), (0.24, 36.0, 0.18, 0.298), (0.26, 44.0, 0.10, 0.350), (0.14, 214.0, 0.07, 0.296))
# (Judge r2: the stones read as noise and the cream ones stayed bright in the shadows: half the spread, no cream outliers.)
P_VAL_SD = 0.08


def _pkey(key):
    return np.random.default_rng((key[0] * 73856093) ^ ((key[1] + 5000) * 19349663) ^ (key[2] * 83492791) ^ 0x51AB)


def setts_layout_paint(variant):
    """The seeds of a power diagram, in courses along x (their heights shared by every variant). A course inside the
    tile's border band, and a course's first and last P_BAND metres along x, come from one shared draw; the rest from
    the variant's. Returns seeds (x, z), keys (course, slot, variant or 0), weights, big, missing."""
    rz = np.random.default_rng(0x5E7A)
    hs = []
    while sum(hs) < SETTS_M - 0.15:
        hs.append(rz.uniform(*P_ROW))
    hs = np.array(hs) * SETTS_M / sum(hs)
    z0 = -hs[0] / 2 + np.concatenate([[0], np.cumsum(hs)[:-1]])          # course 0 straddles z = 0

    def win(c):                                                          # 0 in the border band, 1 well inside
        d = np.clip((np.minimum(c, SETTS_M - c) - P_BAND) / 0.6, 0, 1)
        return d * d * (3 - 2 * d)
    seeds, keys, wts, big, miss = [], [], [], [], []
    for j, h in enumerate(hs):
        shared = z0[j] < P_BAND or z0[j] + h > SETTS_M - P_BAND
        rs = np.random.default_rng(0x5E7B + 131 * j)
        rv = rs if shared else np.random.default_rng(0x5E7C + 131 * j + 7919 * (variant + 1))
        ph = rs.uniform(0, 2 * np.pi, 2)
        amp = rs.uniform(0.015, 0.04)                                    # the course's own wave (shared, periodic)

        def draw(r):
            b = r.uniform() < P_BIG_P
            return h * r.uniform(*P_STEP) * (r.uniform(*P_BIG) if b else 1.0), b
        w0, b0 = draw(rs)
        a = w0 * rs.uniform(0.25, 0.75)                                  # the slot across x = 0: [-a, w0 - a]
        fw, x = [], w0 - a
        while x < P_BAND:
            fw.append(draw(rs)); x += fw[-1][0]
        bw, xb = [], SETTS_M - a
        while xb > SETTS_M - P_BAND:
            bw.append(draw(rs)); xb -= bw[-1][0]
        gap = xb - x
        mw = []
        while sum(w for w, _ in mw) < gap - 0.6 * h:
            mw.append(draw(rv))
        sc = gap / max(sum(w for w, _ in mw), 1e-6)
        mw = [(w * sc, b) for w, b in mw]
        slots = [(w0, b0)] + fw + mw + bw[::-1]
        ks = ([(j, 0, 0)] + [(j, k + 1, 0) for k in range(len(fw))]
              + [(j, 1000 + k, 0 if shared else variant + 1) for k in range(len(mw))]
              + [(j, -k - 1, 0) for k in range(len(bw))][::-1])
        xl = -a
        for (w, b), key in zip(slots, ks):
            r = _pkey(key)
            xc = xl + w / 2 + r.uniform(-P_JIT[0], P_JIT[0]) * w
            zc = z0[j] + h / 2 + r.uniform(-P_JIT[1], P_JIT[1]) * h
            zc += amp * np.sin(4 * np.pi * xc / SETTS_M + ph[0]) + 0.5 * amp * np.sin(6 * np.pi * xc / SETTS_M + ph[1])
            if key[2]:
                # The courses bow in the middle of the tile, differently in each variant (not in the border band).
                zc += 0.05 * win(xc % SETTS_M) * win(zc % SETTS_M) * np.sin(2 * np.pi * xc / SETTS_M * (1 + variant % 2) + variant * 2.1)
            seeds.append((xc % SETTS_M, zc % SETTS_M)); keys.append(key)
            wts.append(r.uniform(*P_BIG_W) if b else r.uniform(-0.0015, 0.0015))
            big.append(b); miss.append((not b) and r.uniform() < P_MISS_P)
            xl += w
    return np.array(seeds), keys, np.array(wts), np.array(big), np.array(miss)


def setts_sources_paint(variant):
    """The painted layout's masks: height (metres), id, tone, wear, mud, moss, sid, stone, dome (the bevel's profile,
    0 at the gap, 1 on the flat top), lit (the bevel's sun side, 0-1), foot (its far side, 0-1), stroke (-1..1),
    narrow (a gap's narrowness, 0-1: 1 in the dark cracks, 0 in the mud of a missing stone). And hnorm, the normal's
    height (the tops' full tilt)."""
    from scipy.ndimage import maximum as lab_max, distance_transform_edt, maximum_filter
    s, keys, wt, big, miss = setts_layout_paint(variant)
    tree = cKDTree(s, boxsize=SETTS_M)
    px = SETTS_M / SN
    cpx = SN / SETTS_M
    g = (np.arange(SN) + 0.5) * px
    X, Z = np.meshgrid(g, g)
    e = np.minimum(np.minimum(g, SETTS_M - g), 0.6) / 0.6
    m = np.minimum(e[None, :], e[:, None])
    m = m * m * (3 - 2 * m)

    def mixed(cell_m, oct_, sd):
        return (fbm(SN, np.random.default_rng(sd), cell_m * cpx, oct_) * (1 - m)
                + fbm(SN, np.random.default_rng(sd + 1 + variant), cell_m * cpx, oct_) * m)
    P = np.stack([X.ravel(), Z.ravel()], -1)
    edge = np.zeros(len(P)); i1 = np.zeros(len(P), int); qa = np.zeros((len(P), 2))
    for c0 in range(0, len(P), 1 << 18):
        Pc = P[c0:c0 + (1 << 18)]
        d, idx = tree.query(Pc, k=10)
        o = np.argsort(d * d - wt[idx], 1)
        idx = np.take_along_axis(idx, o, 1)
        a = idx[:, 0]
        q = Pc - s[a]
        q -= SETTS_M * np.round(q / SETTS_M)
        es = []
        for c in range(1, 10):
            v = s[idx[:, c]] - s[a]
            v -= SETTS_M * np.round(v / SETTS_M)
            vl = np.maximum(np.linalg.norm(v, axis=1), 1e-6)
            es.append((vl * vl + wt[a] - wt[idx[:, c]]) / (2 * vl) - (q * v).sum(1) / vl)
        es = np.maximum(np.stack(es, 1), 0)
        edge[c0:c0 + len(Pc)] = -np.log(np.exp(-P_KK * es).sum(1)) / P_KK
        i1[c0:c0 + len(Pc)] = a; qa[c0:c0 + len(Pc)] = q
    ns = len(s)
    edge = np.maximum(edge.reshape(SN, SN), 0) + P_WOBBLE * 3 * mixed(0.05, 2, 500)
    i1 = i1.reshape(SN, SN); qa = qa.reshape(SN, SN, 2)
    jh = P_JOINT + P_JOINT_V * np.clip(3 * mixed(0.15, 2, 300), -1, 1)
    inr = np.asarray(lab_max(edge, i1, np.arange(ns)))
    tone = np.zeros((ns, 3)); wear = np.zeros(ns); tilt = np.zeros((ns, 2)); top = np.zeros(ns); sid = np.zeros(ns)
    phs = np.zeros((ns, 2)); bev = np.zeros(ns)
    pal_c = np.cumsum([p[0] for p in P_PALETTE])
    for k, key in enumerate(keys):
        r = np.random.default_rng((key[0] * 73856093) ^ ((key[1] + 5000) * 19349663) ^ (key[2] * 83492791) ^ 0x9A1)
        _, ph_, ps_, pv_ = P_PALETTE[min(int(np.searchsorted(pal_c, r.uniform())), len(P_PALETTE) - 1)]
        hh = (ph_ + np.clip(r.normal(0, 3.0), -7, 7)) / 360.0
        sat = ps_ * r.uniform(0.85, 1.15)
        val = pv_ * np.clip(r.normal(1.0, P_VAL_SD), 0.70, 1.34)
        tone[k] = colorsys.hsv_to_rgb(hh % 1.0, sat, val)
        wear[k] = r.uniform(0, 1) ** 1.5
        a = np.radians(r.uniform(*P_TILT)); th = r.uniform(0, 2 * np.pi)
        tilt[k] = np.tan(a) * np.array([np.cos(th), np.sin(th)])
        top[k] = r.uniform(0.85, 1.1)
        sid[k] = r.uniform(0.1, 0.9)
        phs[k] = r.uniform(0, 2 * np.pi, 2)
        bev[k] = min(r.uniform(*P_BEVEL), 0.38 * max(inr[k] - P_JOINT, 0.02))

    # Pillows: a rounded bevel from the gap, then a broad flat top, tilted (full in the normal, a quarter in the
    # height the shader reads, so the mud's levels hold).
    stn = (edge > jh) & ~miss[i1]
    stone = gaussian_filter(stn.astype(float), 0.7, mode='wrap')
    xb = np.clip((edge - jh) / bev[i1], 0, 1)
    dome = 1 - (1 - xb) ** 2.5
    ii = i1.ravel(); stf = stn.ravel().astype(float)
    cnt = np.bincount(ii, stf, ns) + 1e-9
    cu = np.bincount(ii, stf * qa[..., 0].ravel(), ns) / cnt
    cv = np.bincount(ii, stf * qa[..., 1].ravel(), ns) / cnt
    qu, qv = qa[..., 0] - cu[i1], qa[..., 1] - cv[i1]
    plane = qu * tilt[i1, 0] + qv * tilt[i1, 1]
    fine = mixed(0.05, 3, 110)
    dirt = mixed(0.6, 4, 100)
    hd = dome * P_TOP_H * top[i1]
    h_m = (hd + 0.25 * plane * dome) * stone
    h_nm = (hd + plane * dome) * stone
    # The gaps: narrow and deep (dark cracks) where stones meet; packed mud, nearly flush, where one is missing.
    jm = ~stn
    pd = SN // 8
    dt = distance_transform_edt(np.pad(jm, pd, mode='wrap'))[pd:-pd, pd:-pd] * px
    wid = maximum_filter(dt, size=5, mode='wrap') * 2                     # about the gap's full width (m)
    narrow = np.clip((0.050 - wid) / 0.015, 0, 1) * (1 - stone)
    mud = np.clip(0.55 + 0.45 * mixed(0.12, 3, 200) + 0.3 * dirt, 0, 1) * (1 - stone)
    jhgt = (-0.0055 + 0.0008 * fine) * narrow + (-0.0012 + 0.0010 * fine) * (1 - narrow)
    h_m = h_m + (1 - stone) * jhgt
    h_nm = h_nm + (1 - stone) * jhgt
    moss = np.clip((-dirt - 0.2) * 2.5, 0, 1) * np.clip(0.5 + 0.8 * mixed(0.08, 2, 210), 0, 1) * (1 - stone)

    # The bevel's sun side and its far side (image cols, rows).
    gx = (np.roll(hd, -1, 1) - np.roll(hd, 1, 1)) / (2 * px)
    gz = (np.roll(hd, -1, 0) - np.roll(hd, 1, 0)) / (2 * px)
    sl = np.hypot(gx, gz) + 1e-9
    face = -(gx * P_SUN[0] + gz * P_SUN[1]) / sl
    ramp = np.clip(sl / 0.12, 0, 1) * (dome < 0.999)
    lit = np.clip(face, 0, 1) * ramp * stone
    foot = np.clip(-face, 0, 1) * ramp * stone

    # The strokes: 2-3 broad bands along each stone's long axis (from its own moments), each one value, eased.
    sxx = np.bincount(ii, stf * qu.ravel() ** 2, ns) / cnt
    szz = np.bincount(ii, stf * qv.ravel() ** 2, ns) / cnt
    sxz = np.bincount(ii, stf * (qu * qv).ravel(), ns) / cnt
    ang = 0.5 * np.arctan2(2 * sxz, sxx - szz)
    ca, sa = np.cos(ang)[i1], np.sin(ang)[i1]
    um = qu * ca + qv * sa
    un = -qu * sa + qv * ca
    ph = phs[i1]
    tb = un / P_STROKE_W + 0.25 * np.sin(2 * np.pi * um / 0.22 + ph[..., 1]) + ph[..., 0]
    tab = np.random.default_rng(700).uniform(-1, 1, 4096)
    b0 = np.floor(tb).astype(int) + 211 * i1
    f = tb - np.floor(tb)
    f = np.clip((f - 0.25) / 0.5, 0, 1)
    f = f * f * (3 - 2 * f)
    stroke = (tab[b0 % 4096] * (1 - f) + tab[(b0 + 1) % 4096] * f) * stone

    sidm = np.where(stone > 0.5, sid[i1], 0.0)
    wearm = wear[i1] * dome * stone
    src = dict(height=h_m, hnorm=h_nm, id=i1.astype(float), tone=tone[i1], wear=wearm, mud=mud, moss=moss, sid=sidm,
               stone=stone, dome=dome, lit=lit, foot=foot, stroke=stroke, narrow=narrow)
    if SIZES:
        area = np.bincount(ii, stf, ns) * px * px
        ok = area > 0.0015
        eq = np.sqrt(4 * area[ok] / np.pi)
        asp = np.sqrt(np.maximum(sxx, 1e-9) / np.maximum(szz, 1e-9))
        asp = np.maximum(asp, 1 / asp)[ok]
        gw = wid[jm & (narrow > 0.99)]
        print(f'  setts paint {variant}: stones {len(eq)} (missing {int(miss.sum())}), eq. diameter p5 {np.percentile(eq, 5):.3f} '
              f'p50 {np.median(eq):.3f} p95 {np.percentile(eq, 95):.3f} max {eq.max():.3f}; '
              f'14-28 cm {100 * ((eq >= 0.14) & (eq <= 0.28)).mean():.0f}%, 30-45 cm {100 * ((eq >= 0.30) & (eq <= 0.45)).mean():.1f}%; '
              f'aspect p50 {np.median(asp):.2f} p95 {np.percentile(asp, 95):.2f}; area in stones {100 * stf.mean():.1f}%; '
              f'crack width p50 {100 * np.median(gw):.1f} cm; bevel p50 {100 * np.median(bev):.1f} cm; '
              f'flat top {100 * (stf * (dome.ravel() > 0.97)).sum() / stf.sum():.0f}%', flush=True)
    return src


def bake_setts_paint(src):
    """The painted look: albedo, normal and arh (R occlusion, G roughness, B height, the same ranges as the first)."""
    px = SETTS_M / SN
    stone, dome, h_m, wear = src['stone'], src['dome'], src['height'], src['wear']
    st = stone[..., None]
    k = (1 + 0.14 * src['lit'] - 0.16 * src['foot'] + P_STROKE * src['stroke'] + 0.05 * wear)
    alb = src['tone'] * k[..., None]
    # The gaps: dark brown in the cracks, packed dark-brown mud where a stone is missing; moss where never swept.
    crack = np.array([0.104, 0.091, 0.077])      # (round 3: 0.112, 0.084, 0.058; a near-neutral dark, as the target's gaps)
    packed = np.array([0.200, 0.158, 0.115])     # (0.205, 0.155, 0.104)
    deep = np.array([0.170, 0.133, 0.097])       # (0.175, 0.130, 0.088)
    moss = np.array([0.17, 0.20, 0.10])
    mortar = packed + (deep - packed) * src['mud'][..., None]
    mortar += (moss - mortar) * src['moss'][..., None] * 0.6
    mortar += (crack - mortar) * src['narrow'][..., None]
    alb = np.clip(alb * st + mortar * (1 - st), 0, 1)
    rough = (0.76 - 0.12 * wear) * stone + 0.96 * (1 - stone)
    hn = np.clip((h_m + 0.006) / 0.022, 0, 1)
    ao = np.clip(1 - 0.12 * (1 - stone) - 0.40 * src['narrow'] - 0.12 * (1 - dome) * stone, 0, 1)
    ao = gaussian_filter(ao, 1.0, mode='wrap')
    n = normal_from(src['hnorm'], px, 1.0)
    n[..., 2] = src['sid'] * 2 - 1
    STASH.update(i1=src['id'].astype(int), stone=stone, alb=alb)
    return alb, n, np.stack([ao, np.clip(rough, 0.05, 1), hn], -1)


def save_sources_paint(variant, src):
    SRC_PAINT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(np.round((src['height'] + 0.006) / 0.022 * 65535), 0, 65535).astype(np.uint16)).save(
        SRC_PAINT / f'v{variant}_height.png')
    Image.fromarray(np.clip(np.round((src['hnorm'] + 0.02) / 0.05 * 65535), 0, 65535).astype(np.uint16)).save(
        SRC_PAINT / f'v{variant}_hnorm.png')
    Image.fromarray(src['id'].astype(np.uint16)).save(SRC_PAINT / f'v{variant}_id.png')
    to8(src['tone']).save(SRC_PAINT / f'v{variant}_tone.png')
    for k in ('wear', 'mud', 'moss', 'sid', 'stone', 'dome', 'lit', 'foot', 'narrow'):
        to8(src[k]).save(SRC_PAINT / f'v{variant}_{k}.png')
    to8(src['stroke'] * 0.5 + 0.5).save(SRC_PAINT / f'v{variant}_stroke.png')


def load_sources_paint(variant):
    def f(name):
        return np.asarray(Image.open(SRC_PAINT / f'v{variant}_{name}.png')).astype(float)
    src = {k: f(k) / 255 for k in ('wear', 'mud', 'moss', 'sid', 'stone', 'dome', 'lit', 'foot', 'narrow')}
    src['height'] = f('height') / 65535 * 0.022 - 0.006
    src['hnorm'] = f('hnorm') / 65535 * 0.05 - 0.02
    src['id'] = f('id')
    src['tone'] = f('tone') / 255
    src['stroke'] = f('stroke') / 255 * 2 - 1
    return src


def main_paint(bake):
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = []
    for v in range(VARIANTS):
        src = load_sources_paint(v) if bake else setts_sources_paint(v)
        if not bake:
            save_sources_paint(v, src)
        tiles.append(bake_setts_paint(src))
    save_strip('setts_paint_albedo', [to8(t[0]) for t in tiles], SN)
    save_strip('setts_paint_normal', [nor8(t[1]) for t in tiles], SN)
    save_strip('setts_paint_arh', [to8(t[2]) for t in tiles], SN)


IMPORT = """[remap]

importer="2d_array_texture"
type="CompressedTexture2DArray"

[deps]

source_file="res://art/ground/{name}.jpg"

[params]

compress/mode=2
compress/high_quality=true
compress/lossy_quality=0.9
compress/hdr_compression=1
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
slices/horizontal=1
slices/vertical={layers}
"""


def save_strip(name, tiles, size):
    im = Image.new('RGB', (size, size * len(tiles)))
    for i, t in enumerate(tiles):
        im.paste(t, (0, i * size))
    im.save(OUT / f'{name}.jpg', quality=95, subsampling=0)
    imp = OUT / f'{name}.jpg.import'
    if not imp.exists():
        imp.write_text(IMPORT.format(name=name, layers=len(tiles)))
    print(f'{name}.jpg: {(OUT / f"{name}.jpg").stat().st_size / 1e6:.1f} MB', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', choices=['layers', 'setts'])
    ap.add_argument('--sizes', action='store_true', help='print the setts stone sizes')
    ap.add_argument('--bake', action='store_true', help='the setts: re-bake the maps from tools/assets/setts_src (no new layout)')
    ap.add_argument('--paint', action='store_true', help='the painted setts (--setts-paint) only: setts_paint_*.jpg')
    a = ap.parse_args()
    if a.paint:
        return main_paint(a.bake)
    OUT.mkdir(parents=True, exist_ok=True)
    setts = None
    if a.only != 'layers':
        setts = []
        for v in range(VARIANTS):
            src = load_sources(v) if a.bake else setts_sources(v)
            if not a.bake:
                save_sources(v, src)
            setts.append(bake_setts(src))
        save_strip('setts_albedo', [to8(s[0]) for s in setts], SN)
        save_strip('setts_normal', [nor8(s[1]) for s in setts], SN)
        save_strip('setts_arh', [to8(s[2]) for s in setts], SN)
        meta = json.loads((OUT / 'ground.json').read_text())
        meta['setts'] = {'metres': SETTS_M, 'variants': VARIANTS, 'px': SN}
        for l in meta['layers']:
            if l['name'] == 'stone':
                l['metres'] = SETTS_M
        (OUT / 'ground.json').write_text(json.dumps(meta, indent=1) + '\n')
    if a.only == 'setts':
        return
    fetch_raw()
    if setts is None:
        setts = [build_setts(0)]
    alb, nor, arh = [], [], []
    for k, spec in enumerate(LAYERS):
        if spec[1] is None:
            # The far copy of setts variant 0 (the shader reads the 2K variants).
            sa, sn, sh = setts[0]
            alb.append(to8(sa).resize((N, N), Image.LANCZOS))
            nor.append(nor8(sn).resize((N, N), Image.LANCZOS))
            arh.append(to8(sh).resize((N, N), Image.LANCZOS))
            continue
        o, n, r = build_layer(spec, 1000 + k)
        alb.append(to8(o)); nor.append(nor8(n)); arh.append(to8(r))
        print(f'  {spec[0]}: {spec[1]} rebuilt', flush=True)
    save_strip('albedo', alb, N)
    save_strip('normal', nor, N)
    save_strip('arh', arh, N)
    meta = {'by': 'tools/assets/env_ground.py (ours; CC0 Poly Haven sets as raw grain only)',
            'layers': [{'name': s[0], 'raw': s[1] or 'none (procedural; cobblestone_05 grain)', 'metres': s[2]} for s in LAYERS],
            'setts': {'metres': SETTS_M, 'variants': VARIANTS, 'px': SN}}
    (OUT / 'ground.json').write_text(json.dumps(meta, indent=1) + '\n')


if __name__ == '__main__':
    main()
