"""Paint for the heroine's face, laid out on her head's own paint.

Each design is drawn flat, on a sheet that is her face unrolled round her
head (a cylinder about her head's upright axis: across, the arc round it;
down, her height), where it is easy to draw a stripe from temple to temple
or a line under an eye. This tool then lays each design onto her head's own
UV layout (art/people/head_tex/heroine_head.jpg), so the game draws it over
her skin as a pass of its own (shaders/heroine_paint.gdshader, People.HerPaint)
and it moves with her face as it is shaped and speaks.

It reads her head from art/people/heroine.glb, so it is run again whenever
her head is rebuilt (its UVs may change):

    python tools/assets/heroine_paint.py            # every design, and her brows
    python tools/assets/heroine_paint.py woad kohl  # only those
    python tools/assets/heroine_paint.py --sheet out.png   # her face unrolled, to draw against
    PAINT_PREVIEW=<folder>: each design also saved over her face, on the sheet

Out: godot/art/people/paint/<id>.png (her UV layout, transparent but for the
paint), and godot/art/people/paint/brows.png: her painted brows found in her
head's paint, so the game can dye them the colour of her hair (grey: how dark
each hair is, alpha: how much brow there is).
"""
import json
import os
import struct
import sys

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GLB = os.path.join(ROOT, 'godot', 'art', 'people', 'heroine.glb')
HEAD_TEX = os.path.join(ROOT, 'godot', 'art', 'people', 'head_tex', 'heroine_head.jpg')
OUT = os.path.join(ROOT, 'godot', 'art', 'people', 'paint')
CACHE = os.path.join(os.environ.get('TEMP', '/tmp'), 'heroine_paint_cache')

UV_SIZE = 2048            # the paint's size on her UV layout
MM = 0.00016              # the sheet: metres a pixel
R = 0.095                 # the cylinder's radius (her head's, about)
S_RANGE = (-0.165, 0.165) # across the sheet: arc round her head, + toward her left
Y_RANGE = (1.60, 1.89)    # down the sheet: her height (top first)
W = int(round((S_RANGE[1] - S_RANGE[0]) / MM))
H = int(round((Y_RANGE[1] - Y_RANGE[0]) / MM))
Z0 = 0.0                  # the cylinder's axis, front to back (set from her head)


# ------------------------------------------------------------ her head --

def read_glb(path):
    with open(path, 'rb') as f:
        f.read(12)
        n, _ = struct.unpack('<II', f.read(8))
        doc = json.loads(f.read(n))
        n2, _ = struct.unpack('<II', f.read(8))
        blob = f.read(n2)
    return doc, blob


def accessor(doc, blob, i):
    a = doc['accessors'][i]
    bv = doc['bufferViews'][a['bufferView']]
    comps = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    item = np.dtype(dt).itemsize * comps
    stride = bv.get('byteStride', item)
    raw = np.frombuffer(blob, np.uint8, count=stride * (a['count'] - 1) + item, offset=off)
    rows = np.lib.stride_tricks.as_strided(raw, (a['count'], item), (stride, 1))
    return np.ascontiguousarray(rows).view(dt).reshape(a['count'], comps)


def mesh(doc, blob, name):
    m = next(x for x in doc['meshes'] if x['name'] == name)
    p = m['primitives'][0]
    at = p['attributes']
    P = accessor(doc, blob, at['POSITION']).astype(np.float64)
    UV = accessor(doc, blob, at['TEXCOORD_0']).astype(np.float64) if 'TEXCOORD_0' in at else None
    F = accessor(doc, blob, p['indices']).reshape(-1, 3).astype(np.int64)
    return P, UV, F


def sheet_xy(P):
    """Each point's place on the sheet, in pixels (x across, y down)."""
    th = np.arctan2(P[:, 0], P[:, 2] - Z0)
    s = th * R
    return np.c_[(s - S_RANGE[0]) / MM, (Y_RANGE[1] - P[:, 1]) / MM]


def raster(V2, attrs, F, w, h, depth=None, keep=None):
    """Triangles drawn into a w x h grid (V2 their corners' pixels), each pixel
    given its triangle's attributes there; where they overlap, the greatest
    depth wins. Returns the attributes and where anything was drawn."""
    out = np.zeros((h, w, attrs.shape[1]), np.float32)
    zb = np.full((h, w), -np.inf, np.float32)
    for t in F if keep is None else F[keep]:
        a, b, c = V2[t]
        x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
        x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, w - 1), min(y1, h - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
        l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
        l2 = 1 - l0 - l1
        inside = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
        if not inside.any():
            continue
        val = l0[..., None] * attrs[t[0]] + l1[..., None] * attrs[t[1]] + l2[..., None] * attrs[t[2]]
        z = l0 * depth[t[0]] + l1 * depth[t[1]] + l2 * depth[t[2]] if depth is not None else np.zeros_like(l0)
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        win = inside & (z > sub)
        sub[win] = z[win]
        out[y0:y1 + 1, x0:x1 + 1][win] = val[win]
    return out, np.isfinite(zb)


def maps():
    """Her head unrolled (the sheet: her paint seen on it) and its way back
    (each texel of her UV layout: where it lies on the sheet), kept between
    runs for as long as heroine.glb is unchanged."""
    global Z0
    os.makedirs(CACHE, exist_ok=True)
    stamp = os.path.join(CACHE, 'stamp.txt')
    key = f'{os.path.getsize(GLB)}:{os.path.getmtime(GLB)}:{UV_SIZE}:{MM}:{R}'
    doc, blob = read_glb(GLB)
    P, UV, F = mesh(doc, blob, 'HeroineHead')
    E, _, _ = mesh(doc, blob, 'HeroineEyes')
    # The cylinder's axis: upright, through the middle of her head, front to back.
    Z0 = (P[:, 2].min() + P[:, 2].max()) / 2
    eyes = [E[E[:, 0] > 0].mean(0), E[E[:, 0] < 0].mean(0)]
    if os.path.exists(stamp) and open(stamp).read() == key:
        z = np.load(os.path.join(CACHE, 'maps.npz'))
        return z['ref'], z['back'], z['valid'], [z['eye_r'], z['eye_l']]
    xy = sheet_xy(P)
    # Only her face and the sides of her head: within reach of the sheet.
    th = np.arctan2(P[:, 0], P[:, 2] - Z0)
    rad = np.hypot(P[:, 0], P[:, 2] - Z0)
    keep = (np.abs(th[F]).max(1) < np.radians(105)) & (P[F, 1].min(1) > Y_RANGE[0] - 0.01)
    # The sheet: her paint at each of its pixels (the outermost surface wins: lips over teeth, a nose over its cheek).
    uvs, drawn = raster(xy, UV.astype(np.float32), F, W, H, depth=rad, keep=keep)
    tex = np.asarray(Image.open(HEAD_TEX).convert('RGB'), np.float32) / 255
    th_, tw_ = tex.shape[:2]
    ref = cv2.remap(tex, (uvs[..., 0] * tw_ - 0.5).astype(np.float32), (uvs[..., 1] * th_ - 0.5).astype(np.float32), cv2.INTER_LINEAR)
    ref[~drawn] = 0
    # The way back: each texel of her UV layout, its place on the sheet (and whether it has one).
    uvpx = np.c_[UV[:, 0] * UV_SIZE, UV[:, 1] * UV_SIZE]
    back, valid = raster(uvpx, xy.astype(np.float32), F, UV_SIZE, UV_SIZE, depth=None, keep=keep)
    # (her left eye, +x, is on the sheet's right, as she is seen)
    eye_l, eye_r = (sheet_xy(e[None])[0] for e in eyes)
    np.savez_compressed(os.path.join(CACHE, 'maps.npz'), ref=ref, back=back, valid=valid, eye_l=eye_l, eye_r=eye_r)
    open(stamp, 'w').write(key)
    return ref, back, valid, [eye_r, eye_l]


def to_uv(design, back, valid):
    """A design drawn on the sheet (RGBA, float), laid onto her UV layout."""
    rgba = cv2.remap(design, back[..., 0], back[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    rgba[~valid] = 0
    # (bled a few texels past each island's edge, so the seams never show a line)
    filled = rgba[..., 3] > 0
    out = rgba.copy()
    for _ in range(4):
        grown = cv2.dilate(out, np.ones((3, 3), np.uint8))
        out = np.where(filled[..., None], out, grown)
        filled = out[..., 3] > 0
    return out


def save(rgba, name):
    os.makedirs(OUT, exist_ok=True)
    img = np.clip(rgba, 0, 1)
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(OUT, name + '.png'), optimize=True)


# --------------------------------------------------------- her features --
# Where things are on the sheet (pixels, x across from her right to her left
# as she is seen, y down), found in her own paint: her eyes' openings (the
# eyeball's socket is painted red), her lips (their own pink), her brows
# (darker than the skin round them), and points read off the sheet by eye.

# Read off her sheet by eye (--sheet): each brow from its tail to its head (her
# right, then her left), her cheekbones' high points, her temples, the line
# down her middle.
BROW_R = [(600, 840), (700, 800), (800, 790), (900, 805), (970, 835)]
BROW_L = [(1135, 830), (1240, 795), (1350, 775), (1450, 790), (1520, 825)]
CHEEK_R, CHEEK_L = (700, 1060), (1400, 1060)
TEMPLE_R, TEMPLE_L = (420, 840), (1680, 830)
MID = 1049


def blur(a, s):
    return cv2.GaussianBlur(a, (0, 0), s)


def features(ref, eyes):
    f = {}
    rgb = np.clip(ref, 0, 1)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    # The eyes' openings: the socket's red, round each eye's middle (her right, then her left).
    holes = []
    for e in eyes:
        cx, cy = int(e[0]), int(e[1])
        red = ((r - g) > 0.22) & ((r - b) > 0.2) & (r > 0.6)
        box = np.zeros_like(red)
        box[cy - 70:cy + 60, cx - 140:cx + 140] = True
        m = (red & box).astype(np.uint8)
        n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
        k = lab[cy, cx] if lab[cy, cx] > 0 else 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        hole = cv2.morphologyEx((lab == k).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        hole = blur(hole.astype(np.float32), 5) > 0.5
        holes.append(hole)
    f['holes'] = holes
    # Her lips: redder than the skin round them, under her nose.
    box = np.zeros(lum.shape, bool)
    box[1225:1375, 830:1270] = True
    redness = blur((r - g).astype(np.float32), 1.5)
    skin = np.median(redness[1380:1440, 900:1200])
    lips = ((redness > skin + 0.06) & box).astype(np.uint8)
    lips = cv2.morphologyEx(lips, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(lips)
    keep = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > 2000]
    lips = np.isin(lab, keep).astype(np.uint8)
    lips = cv2.morphologyEx(lips, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    f['lips'] = lips.astype(bool)
    # Her brows: darker than the skin a little way off, and redder, along each brow's arc.
    local = blur(lum.astype(np.float32), 14)
    dark = np.clip((local - lum) / 0.16, 0, 1) * np.clip((r - b - 0.08) / 0.15, 0, 1)
    band = np.zeros(lum.shape, np.uint8)
    for arc in (BROW_R, BROW_L):
        cv2.polylines(band, [np.int32(spline(arc, 60))], False, 1, 70)
    band = blur(band.astype(np.float32), 8)
    f['brows'] = np.clip(dark * band, 0, 1).astype(np.float32)
    return f


# ------------------------------------------------------------- brushes --
# Paint laid down as a brush or a finger lays it: dabs along a stroke, its
# width rising and falling, the bristles' streaks running along it, the
# paint thinning toward its end, its edge broken where it is dry.

def noise(shape, scale, seed):
    """Smooth noise, about 0..1, features about `scale` pixels."""
    rng = np.random.default_rng(seed)
    small = rng.random((max(2, int(shape[0] / scale) + 3), max(2, int(shape[1] / scale) + 3))).astype(np.float32)
    big = cv2.resize(small, (shape[1] + int(scale) * 3, shape[0] + int(scale) * 3), interpolation=cv2.INTER_CUBIC)
    return np.clip(big[:shape[0], :shape[1]], 0, 1)


def spline(pts, n):
    """A smooth line through the points (Catmull-Rom), about n samples."""
    P = np.array(pts, np.float64)
    P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    segs = len(P) - 3
    for i in range(segs):
        p0, p1, p2, p3 = P[i:i + 4]
        for t in np.linspace(0, 1, max(2, n // segs), endpoint=i == segs - 1):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def stroke(shape, pts, width, dry=0.0, streaks=0.6, soft=0.35, seed=0, taper=(0.15, 0.25), streak_px=3.0, edge=0.25):
    """One stroke's coverage (0..1): `width` its widest (pixels, or a list
    along it), `dry` how much its paint breaks up toward its end, `streaks`
    the bristles' lines along it (their spacing `streak_px`), `soft` its
    edge's softness, `taper` how much of each end narrows, `edge` how ragged."""
    rng = np.random.default_rng(seed)
    line = spline(pts, 400)
    seg = np.linalg.norm(np.diff(line, axis=0), axis=1)
    arc = np.r_[0, np.cumsum(seg)]
    L = arc[-1]
    t = arc / L
    wv = np.interp(t, np.linspace(0, 1, len(width)), width) if np.ndim(width) else np.full(len(arc), float(width))
    tap = np.minimum(np.clip(t / max(taper[0], 1e-3), 0, 1), np.clip((1 - t) / max(taper[1], 1e-3), 0, 1))
    wv = wv * (0.25 + 0.75 * np.sqrt(tap))
    cov = np.zeros(shape, np.float32)
    # The bristles: a pattern across the stroke, some of them dry; and a wander along it.
    across = cv2.GaussianBlur(rng.random(512).astype(np.float32)[None], (0, 0), 1.2)[0]
    along = cv2.GaussianBlur(rng.random(4096).astype(np.float32)[None], (0, 0), 20)[0]
    along = (along - along.mean()) / (along.std() + 1e-6) * 0.15 + 0.5
    step = max(1.0, wv.min() * 0.18)
    s = 0.0
    while s <= L:
        i = min(np.searchsorted(arc, s), len(line) - 1)
        c = line[i]
        tg = line[min(i + 1, len(line) - 1)] - line[max(i - 1, 0)]
        tg = tg / (np.linalg.norm(tg) + 1e-9)
        nm = np.array([-tg[1], tg[0]])
        rad = wv[i] / 2
        x0, x1 = int(c[0] - rad - 3), int(c[0] + rad + 4)
        y0, y1 = int(c[1] - rad - 3), int(c[1] + rad + 4)
        x0c, y0c, x1c, y1c = max(x0, 0), max(y0, 0), min(x1, shape[1]), min(y1, shape[0])
        if x1c > x0c and y1c > y0c:
            xs, ys = np.meshgrid(np.arange(x0c, x1c) + 0.5, np.arange(y0c, y1c) + 0.5)
            dx, dy = xs - c[0], ys - c[1]
            v = dx * nm[0] + dy * nm[1]
            u = dx * tg[0] + dy * tg[1]
            d = np.sqrt(u * u + v * v) / max(rad, 1e-3)
            # its edge broken a little, wandering along it
            k = ((v / streak_px) + 256).astype(int) % 512
            jag = (along[int(s * 0.5) % 4096] - 0.5) * edge + (across[(k * 3) % 512] - 0.5) * edge * 0.6
            prof = np.clip((1 - d + jag) / max(soft, 1e-3), 0, 1)
            # the bristles' streaks, along it; dry toward its end
            dryness = dry * (np.clip(t[i] * 1.3 - 0.15, 0, 1) + 0.25)
            br = 1 - dryness * np.clip((0.62 - across[k]) * 3.2, 0, 1)
            br = br * (1 - streaks * 0.25 * (1 - across[(k * 7) % 512]))
            cov[y0c:y1c, x0c:x1c] = np.maximum(cov[y0c:y1c, x0c:x1c], prof * br)
        s += step
    return cov


def layer(shape):
    return np.zeros(shape + (4,), np.float32)


DETAIL = None   # her skin's grain (its light about its local mean), set from her paint


def lay(dst, cov, colour, alpha=1.0, grain=None, through=0.0):
    """Paint of a colour laid over what is there, as much as `cov` says; laid
    thin (`through`), her skin's grain (pores, freckles, the lines of her lips)
    shows in it."""
    a = np.clip(cov * alpha, 0, 1)
    if grain is not None:
        a = a * grain
    col = np.array(colour, np.float32)[None, None, :3]
    if through > 0 and DETAIL is not None:
        col = col * (1 + (DETAIL[..., None] - 1) * through)
    out_a = a + dst[..., 3] * (1 - a)
    rgb = (col * a[..., None] + dst[..., :3] * dst[..., 3:4] * (1 - a[..., None])) / np.maximum(out_a[..., None], 1e-6)
    dst[..., :3] = rgb
    dst[..., 3] = out_a
    return dst


def hexc(h):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def pigment(shape, seed, scale=24, amount=0.25):
    """Paint is never one flat colour: thicker and thinner, a grain to it."""
    n = noise(shape, scale, seed) * 0.6 + noise(shape, scale / 4, seed + 1) * 0.4
    return (1 - amount + amount * n).astype(np.float32)


# -------------------------------------------------------------- designs --
# Sizes on the sheet: a pixel is 0.16 mm, so a fingertip's track is about 90
# pixels wide, a fine brush's line 6 to 10, an eye's opening about 185 long.

def ring_dist(hole):
    """Distance (pixels) from an eye's opening, outside it; inside it, 0."""
    return cv2.distanceTransform((~hole).astype(np.uint8), cv2.DIST_L2, 5)


def kohl(shape, f, smoky=1.0, seed=11):
    """Soot and tallow round the eyes: smoked out over the lids and toward the
    outer corners, under the lower lashes too; a dark line hard along the
    upper lashes, drawn out to a point toward the temple."""
    L = layer(shape)
    ink = hexc('#140d0c')
    for side, hole in enumerate(f['holes']):
        dist = ring_dist(hole)
        ys, xs = np.nonzero(hole)
        cy = ys.mean()
        yy = np.arange(shape[0], dtype=np.float32)[:, None] - cy
        top = np.clip(-yy / 30, 0, 1)
        # (her right eye's outer corner is toward the sheet's left, her left eye's toward its right)
        outer = 1 if side == 1 else -1
        xx = (np.arange(shape[1], dtype=np.float32)[None, :] - xs.mean()) * outer
        # The smoke: up over the lid to the crease, out toward the outer corner, a little under.
        reach = 22 + 58 * top + 34 * np.clip(xx / 80, 0, 1) * (0.4 + 0.6 * top)
        smoke = (np.clip(1 - dist / reach, 0, 1) ** 1.25 * (dist > 0)).astype(np.float32)
        smoke = blur(smoke, 7) * smoky
        lay(L, smoke, ink, 0.86, pigment(shape, seed + side, 26, 0.3))
        # The line along the upper lashes, thickening toward the outer corner; the lower ones smudged.
        thick = 7 + 6 * np.clip(xx / 80, 0, 1)
        upper = ((dist > 0) & (dist < thick) & (yy < 6)).astype(np.float32)
        lower = ((dist > 0) & (dist < 7) & (yy >= 6)).astype(np.float32)
        line = np.clip(blur(upper, 1.4) * 1.0 + blur(lower, 2.5) * 0.7, 0, 1)
        lay(L, line, ink, 1.0)
        # The wing: from the outer corner of the upper lid, up and out to a point.
        corner_x = xs.max() if outer > 0 else xs.min()
        near = np.abs(xs - corner_x) < 8
        cyc = ys[near].mean() if near.any() else cy
        pts = [(corner_x - outer * 40, cyc - 14), (corner_x - outer * 4, cyc - 6), (corner_x + outer * 40, cyc - 22), (corner_x + outer * 78, cyc - 44)]
        wing = stroke(shape, pts, [14, 14, 9, 1.0], dry=0.0, streaks=0.0, soft=0.22, seed=seed + 5 + side, taper=(0.02, 0.7), edge=0.04)
        lay(L, wing, ink, 1.0)
    return L


def rouge(shape, f, seed=21):
    """Kohl, and her lips stained the red of crushed rosehip (their lines kept),
    a flush high on her cheeks."""
    L = kohl(shape, f, smoky=0.8, seed=seed)
    lips = blur(f['lips'].astype(np.float32), 2.0)
    lay(L, lips, hexc('#8a1020'), 0.9, pigment(shape, seed, 14, 0.12), through=0.6)
    for c in (CHEEK_R, CHEEK_L):
        flush = np.zeros(shape, np.float32)
        cv2.ellipse(flush, (int(c[0]), int(c[1] - 30)), (130, 64), -14 if c[0] > MID else 14, 0, 360, 1.0, -1)
        lay(L, blur(flush, 44), hexc('#b8343c'), 0.2)
    return L


def woad(shape, f, seed=31):
    """The old blue of the hill people: the left half of her face painted, brow
    to jaw, solid but for the brush's grain; its edge brushed down her middle
    and broken where the brush ran dry; chalky, the skin's grain through it."""
    L = layer(shape)
    blue = hexc('#21407e')
    grain = pigment(shape, seed, 16, 0.14)
    h, w = shape
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    wob = noise((h, 1), 90, seed)[:, :1] * 30 - 15
    edge = MID + 6 + wob
    # The half: right of her middle (her left), from her brow's top to under her jaw.
    inside = np.clip((xx - edge) / 6, 0, 1) * np.clip((yy - 640) / 50, 0, 1) * np.clip((1560 - yy) / 60, 0, 1)
    # The brush's strokes, down her face: streaks of thicker and thinner paint;
    # at the edge, the bristles' lines broken where the brush ran dry.
    streak = noise((h, w), 14, seed + 1)
    streak = cv2.resize(cv2.resize(streak, (w, h // 10)), (w, h))
    bristle = cv2.resize(cv2.resize(noise((h, w), 3, seed + 3), (w, h // 24)), (w, h))
    near_edge = np.clip(1 - (xx - edge) / 46, 0, 1)
    broken = np.clip((bristle - 0.62 * near_edge) / 0.12 + 0.5, 0, 1) ** 0.6
    fill = inside * (0.86 + 0.14 * streak) * (1 - near_edge * (1 - broken))
    lay(L, fill.astype(np.float32), blue, 0.95, grain, through=0.25)
    return L


def ochre(shape, f, seed=41):
    """A band of red earth across the eyes, temple to temple, laid on with two
    fingers drawn from her right temple to her left: thick where they began,
    thinning and breaking up as the earth ran out."""
    L = layer(shape)
    red = hexc('#7e2a14')
    grain = pigment(shape, seed, 20, 0.3)
    ey = (f['holes'][0].nonzero()[0].mean() + f['holes'][1].nonzero()[0].mean()) / 2
    # (the two fingers' tracks one band: where they overlap it is no thicker)
    cov = np.zeros(shape, np.float32)
    for k, dy in enumerate((-26, 24)):
        pts = [(TEMPLE_R[0] + 30, ey + dy + 26), (650, ey + dy - 2), (MID, ey + dy - 12), (1450, ey + dy - 2), (TEMPLE_L[0] - 30, ey + dy + 24)]
        c = stroke(shape, pts, [92, 98, 96, 92, 70], dry=0.55, streaks=0.5, soft=0.3, seed=seed + k, taper=(0.04, 0.12), streak_px=8, edge=0.45)
        cov = np.maximum(cov, c)
    lay(L, cov, red, 0.92, grain, through=0.45)
    return L


def ash(shape, f, seed=51):
    """Grey from a dead fire, thumbed under each eye and dragged down the cheek:
    thick where the thumb pressed, smeared thin as it was drawn down."""
    L = layer(shape)
    grey = hexc('#a6a19a')
    for side, hole in enumerate(f['holes']):
        ys, xs = np.nonzero(hole)
        out = 1 if side == 1 else -1
        x, y = xs.mean() + out * 10, ys.max() + 18
        pts = [(x - out * 60, y + 4), (x, y + 18), (x + out * 30, y + 120), (x + out * 46, y + 230)]
        c = stroke(shape, pts, [96, 110, 92, 40], dry=0.6, streaks=0.5, soft=0.45, seed=seed + side, taper=(0.08, 0.6), streak_px=11, edge=0.55)
        lay(L, c, grey, 1.0, pigment(shape, seed + 5, 9, 0.5), through=0.5)
    return L


def blood(shape, f, seed=61):
    """Three fingers of blood drawn down over her left eye, brow to jaw: dark
    where it pooled at the start, thinning as the fingers dragged, darker
    at its edges where it dried first."""
    L = layer(shape)
    ys, xs = np.nonzero(f['holes'][1])
    cx = xs.mean()
    for k, off in enumerate((-92, 0, 90)):
        x = cx + off
        pts = [(x - 4, 690), (x, 800), (x + 8, 960), (x + 20, 1130), (x + 30, 1290)]
        c = stroke(shape, pts, [60, 66, 60, 52, 18], dry=0.6, streaks=0.4, soft=0.24, seed=seed + k, taper=(0.03, 0.5), streak_px=6, edge=0.45)
        lay(L, c, hexc('#5c0a0c'), 0.9, pigment(shape, seed + 7 + k, 12, 0.3), through=0.4)
        rim = np.clip(c * (1 - c) * 4, 0, 1) * (c > 0.05)
        lay(L, blur(rim.astype(np.float32), 2.0), hexc('#2e0405'), 0.3)
    return L


def gilt(shape, f, seed=71):
    """Flakes of gold leaf over her cheekbones and down the bridge of her nose:
    torn edges, the larger laid close on the bone, smaller scattered further out."""
    L = layer(shape)
    rng = np.random.default_rng(seed)
    gold = hexc('#d9aa4c')
    spots = []
    for c in (CHEEK_R, CHEEK_L):
        out = 1 if c[0] > MID else -1
        for _ in range(34):
            r = rng.random() ** 1.3
            a = rng.uniform(0, 2 * np.pi)
            spots.append((c[0] + out * 20 + np.cos(a) * r * 190, c[1] - 40 + np.sin(a) * r * 80 - out * np.cos(a) * r * 30, 10 + 42 * (1 - r) ** 1.5 * rng.uniform(0.4, 1)))
    for _ in range(12):
        spots.append((MID + rng.normal(0, 16), rng.uniform(900, 1080), 8 + 22 * rng.random()))
    for x, y, s in spots:
        n = rng.integers(6, 11)
        ang = np.sort(rng.uniform(0, 2 * np.pi, n))
        rad = s * rng.uniform(0.45, 1.0, n)
        squash = rng.uniform(0.55, 1.0)
        rot = rng.uniform(0, np.pi)
        px, py = np.cos(ang) * rad, np.sin(ang) * rad * squash
        poly = np.c_[x + px * np.cos(rot) - py * np.sin(rot), y + px * np.sin(rot) + py * np.cos(rot)].astype(np.int32)
        m = np.zeros(shape, np.uint8)
        cv2.fillPoly(m, [poly], 1, cv2.LINE_AA)
        tone = rng.uniform(0.82, 1.08)
        lay(L, m.astype(np.float32), [g * tone for g in gold], 1.0)
    return L


DESIGNS = {'kohl': kohl, 'rouge': rouge, 'woad': woad, 'ochre': ochre, 'ash': ash, 'blood': blood, 'gilt': gilt}


def brows_layer(shape, f):
    """Her painted brows, found: grey how dark each hair is, alpha how much brow."""
    a = np.clip(f['brows'] * 1.6, 0, 1)
    L = layer(shape)
    L[..., 0] = L[..., 1] = L[..., 2] = np.clip(a * 1.2, 0, 1)
    L[..., 3] = blur(a, 1.0)
    return L


def preview(ref, L):
    """A design over her face on the sheet (to look at)."""
    a = L[..., 3:4]
    return np.clip(ref * (1 - a) + L[..., :3] * a, 0, 1)


if __name__ == '__main__':
    ref, back, valid, eyes = maps()
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--sheet' in sys.argv:
        img = (np.clip(ref, 0, 1) * 255).astype(np.uint8)
        for e in eyes:
            cv2.circle(img, tuple(int(v) for v in e), 6, (0, 255, 0), 2)
        out = args[0] if args else 'sheet.png'
        Image.fromarray(img).save(out)
        print('sheet', img.shape, 'eyes', [e.round(1).tolist() for e in eyes])
        sys.exit()
    shape = ref.shape[:2]
    f = features(ref, eyes)
    lum = (ref @ np.array([0.3, 0.59, 0.11], np.float32)).astype(np.float32)
    DETAIL = np.clip(lum / np.maximum(blur(lum, 12), 1e-3), 0.6, 1.4)
    look = os.environ.get('PAINT_PREVIEW')
    for name in args or list(DESIGNS) + ['brows']:
        L = brows_layer(shape, f) if name == 'brows' else DESIGNS[name](shape, f)
        if look:
            os.makedirs(look, exist_ok=True)
            Image.fromarray((preview(ref, L) * 255).astype(np.uint8)).save(os.path.join(look, name + '.jpg'), quality=90)
        save(to_uv(L, back, valid), name)
        print('painted', name)
