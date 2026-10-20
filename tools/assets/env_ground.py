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
    """Seeds, their keys and their weights (a power diagram: a weighted stone takes ground from its neighbours)."""
    cols, rows = COLS, ROWS
    dx, dz = SETTS_M / cols, SETTS_M / rows
    seeds, keys, wts = [], [], []
    for j in range(rows):
        for i in range(cols):
            border = i in (0, cols - 1) or j in (0, rows - 1)
            r = hash2(i, j, 0 if border else variant + 1)
            x = (i + 0.5 * (j & 1) + r.uniform(-JIT, JIT)) * dx
            z = (j + r.uniform(-JIT * 0.9, JIT * 0.9)) * dz
            w = 0.0
            if not border:
                # The courses bow, differently in each variant, straight at the tile's edge.
                ph = variant * 2.1
                ex = np.sin(np.pi * x / SETTS_M) * np.sin(np.pi * z / SETTS_M)
                z += 0.07 * ex * np.sin(2 * np.pi * x / SETTS_M * (1 + variant % 2) + ph)
                x += 0.03 * ex * np.sin(2 * np.pi * z / SETTS_M * 2 + ph)
                u = r.uniform(0, 1)
                w = BIG_W * r.uniform(0.8, 1.15) if u < BIG_P else (-SMALL_W * r.uniform(0.5, 1.0) if u > 1 - SMALL_P else 0.0)
            seeds.append((x % SETTS_M, z % SETTS_M))
            keys.append((i, j, 0 if border else variant + 1))
            wts.append(w)
    return np.array(seeds), keys, np.array(wts)


def setts_sources(variant):
    """Lay variant `variant`'s stones and return its source masks (all SN x SN, float):
    height (metres), id (stone index), tone (RGB, each stone's own colour), wear (0-1, worn tops), mud (0-1, the dirt
    packed into the joints), moss (0-1, where moss grows in them), grain (-1..1, the stone's surface at 2-5 cm), sid
    (each stone's own random 0.1-0.9, 0 in the joints), stone (0-1, coverage)."""
    s, keys, wt = setts_layout(variant)
    tree = cKDTree(s, boxsize=SETTS_M)
    px = SETTS_M / SN
    cpx = SN / SETTS_M                               # px per metre
    g = (np.arange(SN) + 0.5) * px
    X, Z = np.meshgrid(g, g)
    P = np.stack([X.ravel(), Z.ravel()], -1)
    edge = np.zeros(len(P)); i1 = np.zeros(len(P), int); qa = np.zeros((len(P), 2))
    for c0 in range(0, len(P), 1 << 19):
        Pc = P[c0:c0 + (1 << 19)]
        d, idx = tree.query(Pc, k=8)
        pw = d * d - wt[idx]
        o = np.argsort(pw, 1)
        idx = np.take_along_axis(idx, o, 1)
        a = idx[:, 0]
        q = Pc - s[a]
        q -= SETTS_M * np.round(q / SETTS_M)
        es = []
        for c in range(1, 8):
            v = s[idx[:, c]] - s[a]
            v -= SETTS_M * np.round(v / SETTS_M)
            vl = np.maximum(np.linalg.norm(v, axis=1), 1e-6)
            es.append((vl * vl + wt[a] - wt[idx[:, c]]) / (2 * vl) - (q * v).sum(1) / vl)
        es = np.maximum(np.stack(es, 1), 0)
        edge[c0:c0 + len(Pc)] = -np.log(np.exp(-KK * es).sum(1)) / KK
        i1[c0:c0 + len(Pc)] = a; qa[c0:c0 + len(Pc)] = q
    edge = np.maximum(edge.reshape(SN, SN), 0)
    # The joints wobble (no ruler-straight sides): about 4 mm over 4-6 cm.
    edge = edge + WOBBLE * fbm(SN, np.random.default_rng(500), cpx * 0.05, 2)
    q = qa.reshape(SN, SN, 2)
    i1 = i1.reshape(SN, SN)

    # Per stone: one hue within 6 degrees, saturation within 10%, value SD about 10%.
    ns = len(s)
    tone = np.zeros((ns, 3)); wear = np.zeros(ns); tilt = np.zeros((ns, 2)); top = np.zeros(ns); sid = np.zeros(ns)
    for k, key in enumerate(keys):
        r = hash2(*key)
        h = (STONE_HSV[0] + np.clip(r.normal(0, 3.0), -6, 6)) / 360.0
        sat = STONE_HSV[1] * r.uniform(0.9, 1.1)
        val = STONE_HSV[2] * np.clip(r.normal(1.0, 0.10), 0.8, 1.22)
        tone[k] = colorsys.hsv_to_rgb(h, sat, val)
        wear[k] = r.uniform(0, 1) ** 1.5
        tilt[k] = r.normal(0, 0.03, 2)
        top[k] = r.uniform(0.75, 1.0)
        sid[k] = r.uniform(0.1, 0.9)

    # Each variant's own noise in the middle, one shared field toward the tile's edge, so tiles meet clean.
    e = np.minimum(np.minimum(g, SETTS_M - g), 0.6) / 0.6
    m = np.minimum(e[None, :], e[:, None])
    m = m * m * (3 - 2 * m)
    def mixed(cell_m, oct_, sd):
        return (fbm(SN, np.random.default_rng(sd), cell_m * cpx, oct_) * (1 - m)
                + fbm(SN, np.random.default_rng(sd + 1 + variant), cell_m * cpx, oct_) * m)
    dirt = mixed(0.6, 4, 100)                   # where the dirt lies, about 0.6 m
    fine = mixed(0.05, 3, 110)
    # Joints 2.4-3.4 cm wide, varying along their length (about 0.15 m), wider where the dirt lies.
    jv = mixed(0.15, 2, 300)
    joint = (JOINT_HALF + 0.0045 * jv) * (1 + 0.15 * np.clip(dirt, 0, 1))
    dome = np.clip((edge - joint) / DOME_R, 0, 1)
    dome = 1 - (1 - dome) ** 2
    stone = gaussian_filter((edge > joint).astype(float), 0.7, mode='wrap')
    gr = mixed(0.035, 2, 400)                   # grain at 2-5 cm
    h_m = (dome * DOME_H * top[i1] + (q * tilt[i1]).sum(-1) * stone + gr * 0.0006 * stone + 0.0006 * fine)
    h_m = h_m * stone + (1 - stone) * (-0.004 + 0.0025 * fine)
    # The dirt packed into the joints (a little proud of their floor where it is thick) and the moss in it.
    mud = np.clip(0.55 + 0.45 * mixed(0.12, 3, 200) + 0.3 * dirt, 0, 1) * (1 - stone)
    moss = np.clip((-dirt - 0.25) * 2.5, 0, 1) * np.clip(0.5 + 0.8 * mixed(0.08, 2, 210), 0, 1) * (1 - stone)
    h_m += mud * 0.002 * (1 - stone)
    sidm = np.where(stone > 0.5, sid[i1], 0.0)
    wearm = wear[i1] * dome * stone
    src = dict(height=h_m, id=i1.astype(float), tone=tone[i1], wear=wearm, mud=mud, moss=moss, grain=gr, sid=sidm,
               stone=stone, dome=dome, edge=edge, joint=joint)
    if SIZES:
        area = np.bincount(i1.ravel(), weights=(edge > joint).ravel().astype(float), minlength=ns) * px * px
        eq = np.sqrt(4 * area[area > 0.002] / np.pi)
        # The widest extent of each stone (its Feret width along x, z and both diagonals).
        st = (edge > joint)
        ids = i1[st]
        co = np.stack(np.nonzero(st), -1).astype(float) * px - s[ids][:, ::-1]
        co -= SETTS_M * np.round(co / SETTS_M)          # (round the stone's seed, so a stone across the tile's edge is whole)
        wmax = np.zeros(ns)
        for a in (np.array([1, 0]), np.array([0, 1]), np.array([1, 1]) / 2 ** 0.5, np.array([1, -1]) / 2 ** 0.5):
            pr = co @ a
            lo = np.full(ns, 1e9); hi = np.full(ns, -1e9)
            np.minimum.at(lo, ids, pr); np.maximum.at(hi, ids, pr)
            wmax = np.maximum(wmax, hi - lo)
        wm = wmax[area > 0.002]
        print(f'  setts {variant}: stones {len(eq)}, eq. diameter p5 {np.percentile(eq, 5):.3f} p50 {np.median(eq):.3f} '
              f'p95 {np.percentile(eq, 95):.3f} max {eq.max():.3f}; 35-45 cm {100 * ((eq > 0.33) & (eq < 0.46)).mean():.1f}%; '
              f'width p50 {np.median(wm):.3f} p99 {np.percentile(wm, 99):.3f} max {wm.max():.3f} m', flush=True)
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
    grit = np.array([0.28, 0.23, 0.17])
    dirt = np.array([0.22, 0.18, 0.13])
    moss = np.array([0.16, 0.19, 0.10])
    mortar = grit + (dirt - grit) * src['mud'][..., None]
    mortar += (moss - mortar) * src['moss'][..., None] * 0.6
    alb = np.clip(alb * st + mortar * (1 - st), 0, 1)
    rough = (0.72 - 0.15 * wear) * stone + 0.95 * (1 - stone)
    hn = np.clip((h_m + 0.006) / 0.022, 0, 1)
    ao = gaussian_filter(np.clip(1 - 0.25 * (1 - stone) - 0.1 * lip, 0, 1), 1.0, mode='wrap')
    n = normal_from(h_m, px, 1.0)
    # The normal's B carries each stone's own random (0.1-0.9; the shader rebuilds z from x and y).
    n[..., 2] = src['sid'] * 2 - 1
    STASH.update(i1=src['id'].astype(int), stone=stone, edge=src['edge'], joint=src['joint'], gr=gr, alb=alb)
    return alb, n, np.stack([ao, np.clip(rough, 0.05, 1), hn], -1)


def save_sources(variant, src):
    SRC.mkdir(parents=True, exist_ok=True)
    def u16(a, lo, hi, name):
        Image.fromarray(np.clip(np.round((a - lo) / (hi - lo) * 65535), 0, 65535).astype(np.uint16)).save(SRC / f'v{variant}_{name}.png')
    u16(src['height'], -0.006, 0.016, 'height')            # metres, -6 to +16 mm
    Image.fromarray(src['id'].astype(np.uint16)).save(SRC / f'v{variant}_id.png')
    to8(src['tone']).save(SRC / f'v{variant}_tone.png')
    for k in ('wear', 'mud', 'moss', 'sid', 'stone', 'dome'):
        to8(src[k]).save(SRC / f'v{variant}_{k}.png')
    to8(src['grain'] * 0.5 + 0.5).save(SRC / f'v{variant}_grain.png')


def load_sources(variant):
    def f(name):
        return np.asarray(Image.open(SRC / f'v{variant}_{name}.png')).astype(float)
    src = {k: f(k) / 255 for k in ('wear', 'mud', 'moss', 'sid', 'stone', 'dome')}
    src['height'] = f('height') / 65535 * 0.022 - 0.006
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
COLS, ROWS = 17, 19   # about 0.235 m x 0.21 m cells before the weights
JIT = 0.30
KK = 70.0             # the corners' rounding (1/m)
BIG_P, BIG_W = 0.05, 0.03      # a few big stones (35-45 cm) and their power weight (m^2)
SMALL_P, SMALL_W = 0.08, 0.005
JOINT_HALF = 0.013    # half a joint (2.2-3.2 cm full)
DOME_H = 0.010        # each stone's dome, to DOME_R in from its joint
DOME_R = 0.06
WOBBLE = 0.004
GRAIN = 0.12          # grain at 2-5 cm: plus or minus about 5% luma
STONE_HSV = (34.0, 0.16, 0.33)   # the stones' one hue (degrees), saturation and value


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
P_WOBBLE = 0.003
P_SUN = np.array([0.866, -0.5])     # toward the sun in the tile (col, row): azimuth 330 (x = cos az, z = sin az; rows = z)
P_STROKE = 0.06                     # the strokes along a stone's long axis, +/-
P_STROKE_W = 0.065                  # their width (m): 2-3 to a stone
# The stones' palettes: (share, hue, saturation, value): warm grey, ochre, cream, a few cool grey-blue.
P_PALETTE = ((0.34, 30.0, 0.12, 0.300), (0.30, 35.0, 0.27, 0.298), (0.24, 41.0, 0.13, 0.348), (0.12, 212.0, 0.08, 0.285))
P_VAL_SD = 0.16


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
    crack = np.array([0.112, 0.084, 0.058])
    packed = np.array([0.205, 0.155, 0.104])
    deep = np.array([0.175, 0.130, 0.088])
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
