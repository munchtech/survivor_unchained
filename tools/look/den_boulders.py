"""The den's boulders as PAINTINGS seen from the play camera (dungeon lead 6's helper, 15 Nov).

    python tools/look/den_boulders.py build      # the atlases + boulders.json
    python tools/look/den_boulders.py preview    # a 1:1 sheet beside den_room.png's boulders (scratch, --out <png>)
    python tools/look/den_boulders.py check      # the numbers: lit/shade against the target, alpha, depth, hull cover

Why paintings: the den's walls only came right as paintings projected along the fixed play camera (dungeon_wall.gdshader,
the den branch); boulders painted on meshes in 3D (den_rocks.py, retired) read as pale pillows. The camera never turns in
a dungeon (yaw 0 looking north, pitch 62 down, fov 34, ~73 px/m at 1080p), so a boulder is painted ONCE as that camera
sees it and drawn as a camera-facing card that writes its own painted depth (shaders/den_boulder.gdshader).

Each boulder is a form in code (an ellipsoid cut by a few broad planes, or two of them leaning together), cast along the
camera's view (exact, per pixel: the face it hits, its point, its normal, its depth), then PAINTED in 2D at 5.3x the
game's pixel: every face's value from the key (the image's upper left, rigs.json den az 243: a lit band on the planes
that face it, a cooler shade side), worn soft edges between the planes; the light through the roots as angular diagonal
shards (a step up) and root shadows (a step down); knife-chip strokes 2-4 game px wide laid along each face and the
knife's diagonal, each painting ONE snapped value step (so a plane breaks into 2-3 painted values) and a hue that follows
the value (warm ochre in the light, warm grey in the mids and shade, olive-brown in regions), never crossing a plane
break; a little dull olive-brown moss on up-facing tops only; sparse short cracks with a lit lip; the foot grimed; ink on
the silhouette (heavier at the foot) and, lightly, on the real plane breaks. Pass 3 (round 7): darker (the check's lit
and shade medians on the target's), visible strokes, dull moss, two big forms ("size": "big", 2.6-2.9 m wide, 2 m tall)
beside the six companions ("small"; the game places them smaller). FROM den_room.png: the colours
by number (its boulders' lit (132,102,77) and shade (41,36,34), sRGB, measured), the forms by eye (bulky, boxy, broad
tilted planes; one pair leaning together). No photo, scan, model or paid credit: drawn in code. Deterministic.

Outputs (godot/art/dungeon/den/): boulders_paint.png (sRGB colour + alpha), boulders_form.png (the painted surface's normal
xyz in the camera's basis + its depth along the view in alpha), boulders.json (each boulder's atlas rect, card size and
pivot, and its shadow hull: vertices and triangles of the form, for the shadow caster).
"""
import json, math, os, sys, zlib

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "godot", "art", "dungeon", "den")
TARGET = r"C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord12\dungeon_concepts\den_room.png"

# ---- the camera (DungeonDress places boulders at yaw 0, so a boulder's own axes are the world's)
R = np.array([1.0, 0.0, 0.0])                                   # screen right
U = np.array([0.0, math.cos(math.radians(62)), -math.sin(math.radians(62))])   # screen up (0, 0.469, -0.883)
F = np.cross(U, R)                                              # the view (into the screen): (0, -0.883, -0.469)
DIAG = math.radians(-28)  # the knife's lean (screen, from the right toward down): den_room.png's chips run diagonal
GAME_PPM = 73.0          # the game's pixels per metre at 1080p (the play camera at the den's floor)
SS = 2                   # the painting is cast and painted at 2x the stored resolution, then box-filtered (its anti-alias)
PPM = 192                # stored pixels per metre (2.6x the game's: crisp after the mips)
IPPM = PPM * SS          # internal
DMAX = 2.5               # depth stored as d / DMAX * 0.5 + 0.5 (metres along the view from the card)

# ---- the look (sRGB). The ramp is the value a face takes by its turn to the key (n.L); lit and shade FROM den_room.png.
LOOK = dict(
    ramp=[  # (n.L, sRGB)
        (-1.00, (34, 32, 34)),
        (-0.30, (42, 39, 38)),
        (0.00, (50, 45, 42)),      # the shade (den_room.png's boulders' shade side, measured (41, 36, 34))
        (0.20, (66, 59, 52)),
        (0.40, (90, 77, 63)),
        (0.60, (112, 89, 68)),     # the lit band (den_room.png's boulders' lit planes, measured (132, 102, 77))
        (0.82, (132, 102, 76)),
        (1.00, (142, 110, 80)),
    ],
    key=(-0.62, 0.74, 0.25),   # toward the key as den_room.png's boulders show it: up, the image's left, a little front
    # the hues a stroke may take (the target's stone: warm ochre in the light, cool grey and olive-brown between)
    # the hue follows the value as in the target (the light warm, the mids and shade cool grey), olive-brown in regions
    hues=dict(umber=(108, 76, 52), grey=(84, 82, 82), olive=(90, 85, 66)),
    hue_w=(0.35, 0.7),         # a mid or shade stroke's pull to the grey (share, uniform between); the olive's at most
    dapple=0.34, dapple_base=0.19,              # the light through the roots: angular diagonal shards of light across the lit planes (n.L)
    shard_m=((0.3, 0.8), (0.07, 0.18), 0.4),
    shadow_share=0.1,          # the share the roots' shadow shards drop a step   # a shard's length and width (metres) and the share of the face it lights
    level=0.15,                # the value step a stroke paints in (n.L): each plane breaks into a few painted values
    level_jit=0.6,             # a stroke's jitter in steps (so strokes interleave at a value's edge and a plane holds 2-3 values)
    moss=(86, 78, 56), moss_k=0.8,   # the moss: olive-brown, low saturation, at the stone's value x moss_k
    moss_up=(0.62, 0.9),       # the face's up share where the moss begins and is whole (up-facing tops only)
    moss_gate=(0.6, 0.7),      # the noise gate (patches, not a blanket)
    crack=((0.9, 1.4), (5.0, 12.0), 3.5, 0.6, 0.25),   # width, length (game px), per square metre, the dark, the lip's lift
    ink=(20, 16, 14), ink_px=(2.6, 1.7),        # the silhouette ink (game px): at the foot, at the crown
    crease=(30, 24, 21), crease_px=1.2, crease_a=0.35, crease_deg=(34.0, 56.0),   # the inner breaks (only the real ones)
    edge_light=0.1, edge_px=1.0,                # the lit side of a break, lifted
    foot_m=0.55, foot_dark=0.45,                 # grime and occlusion at the foot
    # stroke layers: length, width (game px), coverage. 2-4 game px wide (3-5 cm at 73 px/m), 2.5-3.5x as long
    dab_px=[(14.0, 4.0, 1.0), (10.0, 3.0, 1.0), (7.0, 2.2, 0.55)],
)

# ---- the forms: a dome (an ellipsoid whose middle sits cy of its height radius above the floor) cut by a box of broad
# planes: a top, four sides, four upright corners and four top chamfers, each jittered by the seed (azimuth 0 faces the
# camera (+z, south), +90 the image's right (+x); tilt up from horizontal; cut a share of the dome's reach along it).
# Sizes in metres (w across, h up, d deep). FROM den_room.png by eye: bulky, boxy, broad tilted planes, worn corners.
FORMS = [
    dict(name="block", seed=11, size=(3.0, 1.7, 2.2), cy=0.12, top=(-20, 80, 0.22), side=0.26, corner=0.2, chamfer=0.17, twist=8),
    dict(name="slab", seed=23, size=(3.1, 1.2, 2.2), cy=0.08, top=(10, 84, 0.30), side=0.22, corner=0.18, chamfer=0.2, twist=-12),
    dict(name="tall", seed=37, size=(1.9, 2.0, 1.7), cy=0.14, top=(-60, 68, 0.2), side=0.24, corner=0.2, chamfer=0.16, twist=20),
    dict(name="round", seed=41, size=(2.2, 1.45, 1.9), cy=0.16, top=(30, 78, 0.14), side=0.16, corner=0.12, chamfer=0.12, twist=-25),
    dict(name="wedge", seed=53, size=(2.6, 1.6, 2.0), cy=0.1, top=(-75, 58, 0.26), side=0.22, corner=0.2, chamfer=0.14, twist=35),
    dict(name="pair", seed=67, parts=[
        dict(size=(1.9, 1.5, 1.7), at=(-0.55, 0.0, 0.15), cy=0.12, top=(-15, 78, 0.2), side=0.22, corner=0.18, chamfer=0.15, twist=10),
        dict(size=(1.6, 1.2, 1.5), at=(0.78, 0.0, -0.1), cy=0.12, top=(25, 74, 0.2), side=0.22, corner=0.18, chamfer=0.15, twist=-20)]),
    # the two big ones (round 7): taller than the heroine (1.75 m), broad and blocky like den_room.png's big stones (its
    # upper-left and upper-middle ones): a broad tilted top, near-upright sides cut deep, worn corners. Painted at their own
    # size so the game never upscales them.
    dict(name="bigblock", size_class="big", seed=79, size=(3.35, 2.25, 2.0), cy=0.1, top=(-25, 78, 0.16), side=0.3,
         corner=0.24, chamfer=0.17, twist=6),
    dict(name="bigtilt", size_class="big", seed=83, size=(3.3, 2.3, 1.9), cy=0.12, top=(40, 70, 0.18), side=0.28,
         corner=0.22, chamfer=0.2, twist=-18),
]
SINK = 0.12          # metres of each form under the floor (the floor rolls; the foot hides in it)


def srgb_to_lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def lin_to_srgb(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
def lin(rgb): return srgb_to_lin(np.asarray(rgb, np.float64) / 255.0)
def smoothstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def unit(v): v = np.asarray(v, np.float64); return v / np.linalg.norm(v)


def vnoise3(p, scale, salt):
    """Smooth value noise in [0, 1] on 3D points p (..., 3) at 'scale' metres."""
    q = p / scale + salt * 17.13
    i = np.floor(q).astype(np.int64); f = q - i
    f = f * f * (3 - 2 * f)
    def h(ix, iy, iz):
        n = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (salt * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177
        return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * (f[..., 2] if dz else 1 - f[..., 2])
                out = out + w * h(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz)
    return out


def fbm(p, scale, salt, oct=3):
    a, s, t, n = 1.0, scale, 0.0, 0.0
    for k in range(oct):
        t += a * vnoise3(p, s, salt + k); n += a; a *= 0.5; s *= 0.5
    return t / n


# ---- the form ----

def part_planes(part, seed):
    """A convex part: ellipsoid centre and radii, and its planes (unit normal n, offset d: inside where n.p <= d)."""
    w, h, d = part["size"]
    at = np.array(part.get("at", (0, 0, 0)), np.float64)
    rad = np.array([w / 2, h / (1 + part["cy"]) * 1.0, d / 2])
    # the ellipsoid's centre sits cy of its y radius above the floor; it reaches h above the floor (before the cuts)
    ry = (h + SINK) / (1 + part["cy"])
    rad[1] = ry
    c = at + np.array([0.0, part["cy"] * ry - SINK, 0.0])
    rng = np.random.default_rng(seed)
    tw = part.get("twist", 0)
    planes = [part["top"]]
    for k in range(4):
        planes.append((tw + 90 * k + rng.uniform(-12, 12), rng.uniform(4, 16), part["side"] + rng.uniform(-0.05, 0.05)))
        if rng.random() < 0.85:
            planes.append((tw + 45 + 90 * k + rng.uniform(-15, 15), rng.uniform(8, 25), part["corner"] + rng.uniform(-0.05, 0.05)))
        if rng.random() < 0.8:
            planes.append((tw + 90 * k + rng.uniform(-20, 20), rng.uniform(35, 55), part["chamfer"] + rng.uniform(-0.05, 0.05)))
    P = []
    for az, tilt, cut in planes:
        az = math.radians(az + rng.uniform(-4, 4)); tl = math.radians(tilt + rng.uniform(-3, 3))
        # azimuth 0 faces the camera (+z, south), +90 the image's right (+x)
        n = unit([math.sin(az) * math.cos(tl), math.sin(tl), math.cos(az) * math.cos(tl)])
        # the ellipsoid's support along n, cut back by 'cut' of it
        sup = math.sqrt(float(np.sum((rad * n) ** 2)))
        P.append((n, float(n @ c) + sup * (1 - cut)))
    P.append((np.array([0.0, -1.0, 0.0]), SINK))      # the floor (y >= -SINK)
    return c, rad, P


def parts_of(form):
    if "parts" in form:
        return [part_planes(p, form["seed"] + 7 * k) for k, p in enumerate(form["parts"])]
    return [part_planes(form, form["seed"])]


def cast_part(o, part):
    """Orthographic rays o + t F against one convex part: entry t, exit t, the entering face (0 ellipsoid, 1.. planes)."""
    c, rad, P = part
    oc = (o - c) / rad; fr = F / rad
    A = fr @ fr; B = 2 * (oc @ fr); C = np.sum(oc * oc, -1) - 1
    disc = B * B - 4 * A * C
    ok = disc > 0
    sq = np.sqrt(np.maximum(disc, 0))
    t0 = np.where(ok, (-B - sq) / (2 * A), np.inf); t1 = np.where(ok, (-B + sq) / (2 * A), -np.inf)
    entry, exit_, face = t0.copy(), t1.copy(), np.zeros(o.shape[:-1], np.int32)
    for k, (n, d) in enumerate(P):
        nf = float(n @ F); no = o @ n
        if abs(nf) < 1e-9:
            out = no > d
            exit_ = np.where(out, -np.inf, exit_)
            continue
        t = (d - no) / nf
        if nf < 0:
            m = t > entry; face = np.where(m, k + 1, face); entry = np.maximum(entry, t)
        else:
            exit_ = np.minimum(exit_, t)
    hit = ok & (entry < exit_)
    return np.where(hit, entry, np.inf), face


def surface(form, ppm):
    """Cast the form on a grid of ppm px/m in the camera's (R, U) plane. Returns the grid, hit mask, point, normal,
    face id (part * 32 + face), the bevelled normal and the extent."""
    parts = parts_of(form)
    # the extent: every part's ellipsoid box projected
    corners = []
    for c, rad, P in parts:
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    corners.append(c + rad * [sx, sy, sz])
    corners = np.array(corners)
    xs, ys = corners @ R, corners @ U
    pad = 0.12
    x0, x1 = xs.min() - pad, xs.max() + pad; y0, y1 = ys.min() - pad, ys.max() + pad
    W = int(math.ceil((x1 - x0) * ppm / 8) * 8); H = int(math.ceil((y1 - y0) * ppm / 8) * 8)
    gx = x0 + (np.arange(W) + 0.5) / ppm; gy = y1 - (np.arange(H) + 0.5) / ppm
    X, Y = np.meshgrid(gx, gy)
    o = X[..., None] * R + Y[..., None] * U - F * 8.0
    best = np.full(X.shape, np.inf); fid = np.zeros(X.shape, np.int32)
    for k, part in enumerate(parts):
        t, face = cast_part(o, part)
        m = t < best
        best = np.where(m, t, best); fid = np.where(m, k * 32 + face, fid)
    hit = np.isfinite(best)
    p = o + np.where(hit, best, 0)[..., None] * F
    # normals: the entering face's, bevelled toward any other face within a few cm (a stone's worn edge)
    nrm = np.zeros(p.shape); bev = np.zeros(p.shape)
    for k, (c, rad, P) in enumerate(parts):
        mk = hit & (fid // 32 == k)
        if not mk.any():
            continue
        q = (p[mk] - c) / rad
        ne = q / rad; ne /= np.linalg.norm(ne, axis=-1, keepdims=True)
        f = fid[mk] % 32
        n0 = ne.copy()
        for j, (n, d) in enumerate(P):
            n0[f == j + 1] = n
        acc = n0.copy()
        # slack to every other face: ellipsoid in metres approx (1 - |q|) * mean radius
        se = (1 - np.linalg.norm(q, axis=-1)) * float(np.mean(rad))
        b = 0.16             # the worn edge: den_room.png's stones are rounded boxes, broad planes meeting soft
        we = np.where(f != 0, np.clip(1 - se / b, 0, 1) ** 2, 0)
        acc += 0.6 * we[:, None] * ne
        for j, (n, d) in enumerate(P):
            s = d - p[mk] @ n
            wj = np.where(f != j + 1, np.clip(1 - s / b, 0, 1) ** 2, 0)
            acc += 0.6 * wj[:, None] * n
        nrm[mk] = n0; bev[mk] = acc / np.linalg.norm(acc, axis=-1, keepdims=True)
    return dict(W=W, H=H, x0=x0, y1=y1, hit=hit, p=p, n=nrm, nb=bev, fid=fid, parts=parts)


# ---- the painting ----

def ramp(v):
    xs = np.array([a for a, _ in LOOK["ramp"]]); cs = np.array([lin(c) for _, c in LOOK["ramp"]])
    return np.stack([np.interp(v, xs, cs[:, k]) for k in range(3)], -1)


LUMA = np.array([0.2126, 0.7152, 0.0722])


def hue_of(rgb):
    h = lin(rgb); return h / (h @ LUMA)


def lens(cx, cy, ang, ln, wd, rng):
    """Brush dabs: knife chips, boxy with worn ends, slightly asymmetric and ragged (n x 10 points)."""
    a = np.linspace(0, 2 * np.pi, 10, endpoint=False)
    n = len(cx)
    sk = rng.uniform(-0.3, 0.3, (n, 1))
    ca_, sa_ = np.cos(a)[None], np.sin(a)[None]
    u = np.sign(ca_) * np.abs(ca_) ** 0.6 * ln[:, None] / 2 * rng.uniform(0.85, 1.1, (n, 10))
    v = np.sign(sa_) * np.abs(sa_) ** 0.6 * wd[:, None] / 2 * (1 + sk * ca_) * rng.uniform(0.8, 1.15, (n, 10))
    ca, sa = np.cos(ang)[:, None], np.sin(ang)[:, None]
    return np.stack([cx[:, None] + u * ca - v * sa, cy[:, None] + u * sa + v * ca], -1)


def shards(H, W, salt, share):
    """The light through the roots: angular diagonal shards (knife chips at the scale of a hand) in the card's plane,
    1 lit, 0 unlit, crisp-edged (the strokes break their edges)."""
    (l0, l1), (w0, w1), _ = LOOK["shard_m"]
    rng = np.random.default_rng(salt + 101)
    n = int(share * H * W / (IPPM ** 2 * (l0 + l1) / 2 * (w0 + w1) / 2 * 0.8)) + 1
    cx = rng.uniform(0, W, n); cy = rng.uniform(0, H, n)
    ang = DIAG + rng.normal(0, 0.22, n)
    polys = lens(cx, cy, ang, rng.uniform(l0, l1, n) * IPPM, rng.uniform(w0, w1, n) * IPPM, rng)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for k in range(n):
        d.polygon([tuple(q) for q in polys[k]], fill=255)
    return np.asarray(im, np.float64) / 255.0


def paint(form):
    S = surface(form, IPPM)
    # crop to the hit box (+ a margin), aligned to SS
    ys_, xs_ = np.nonzero(S["hit"])
    m = 10 * SS
    y0 = max(0, (ys_.min() - m) // SS * SS); y1 = min(S["H"], -(-(ys_.max() + m) // SS) * SS)
    x0 = max(0, (xs_.min() - m) // SS * SS); x1 = min(S["W"], -(-(xs_.max() + m) // SS) * SS)
    for k in ("hit", "p", "n", "nb", "fid"):
        S[k] = S[k][y0:y1, x0:x1]
    S["x0"] += x0 / IPPM; S["y1"] -= y0 / IPPM; S["H"], S["W"] = S["hit"].shape
    hit, p, n, nb, fid = S["hit"], S["p"], S["n"], S["nb"], S["fid"]
    H, W = hit.shape
    salt = form["seed"]
    L = unit(LOOK["key"])
    sc = IPPM / GAME_PPM                       # internal px per game px
    ph = p[hit]

    def field(fn):                             # a noise on the hit points only, scattered back
        out = np.zeros((H, W)); out[hit] = fn(ph); return out

    # value: each face's turn to the key (the bevel's softened); the light falls off a little down the stone; hard-edged
    # dapples across a face (the target's planes are lit in patches), weaker in the shade
    v0 = np.einsum("ijk,k->ij", nb, L)
    yb = np.where(hit, p[..., 1], 0.0)
    top = max(float(yb[hit].max()), 0.5)
    v0 = v0 + 0.08 * (yb / top - 0.5)
    dk = LOOK["dapple"]
    # light shards lift a plane a step, shadow shards (the roots' shadows) drop it one: a lit top stays mostly lit with
    # dark gaps, a mid side stays mid with a few lights (den_room.png's left and upper-middle stones)
    dap = shards(H, W, salt, LOOK["shard_m"][2]) - shards(H, W, salt + 50, LOOK["shadow_share"])
    v = v0 + (dk * dap - LOOK["dapple_base"]) * (0.35 + 0.65 * np.clip(v0 / 0.6, 0, 1)) + 0.12 * (field(lambda q: fbm(q, 0.15, salt + 2)) - 0.5)
    lev = LOOK["level"]
    quant = lambda x: np.round(x / lev) * lev
    # the hue fields: broad regions where the stone leans warm, grey or olive-brown (a stroke picks one by them + chance)
    hnames = list(LOOK["hues"])
    hf = np.stack([field(lambda q, k=k: fbm(q, 0.35, salt + 3 + k)) for k in range(len(hnames))], -1)
    hcol = np.array([hue_of(LOOK["hues"][h]) for h in hnames])
    # moss: on what faces up, in patches (never a stripe: the gate's noise is 2D on the face, the up share whole only on tops)
    up = nb[..., 1]
    mg = field(lambda q: fbm(q, 0.4, salt + 9) * 0.7 + fbm(q, 0.1, salt + 10) * 0.3)
    moss = smoothstep(*LOOK["moss_up"], up) * smoothstep(*LOOK["moss_gate"], mg + 0.1 * (form.get("moss", 0.7) - 0.7))
    moss_hue = hue_of(LOOK["moss"]) * LOOK["moss_k"]
    # the underpaint (what shows between strokes): the quantised value, the moss over it
    canvas = ramp(quant(v))
    canvas = canvas * (1 - moss[..., None]) + ((canvas @ LUMA)[..., None] * moss_hue) * moss[..., None]
    # strokes: knife chips laid along each face (its strike on screen, turned a little per face), each painting ONE value
    # step (the value at its middle jittered by about half a step, then snapped), a hue pulled from the stone's three,
    # moss where the cap is; never crossing a face's edge (a dab paints only the face its middle is on)
    st = np.cross(n, np.array([0.0, 1.0, 0.0]))
    stn = np.linalg.norm(st, axis=-1)
    st = np.where((stn > 0.2)[..., None], st, R)
    sang = np.arctan2(-(st @ U), st @ R)
    rng = np.random.default_rng(salt)
    face_turn = rng.normal(0, 0.45, 4 * 32)
    ids = Image.new("I", (W, H), -1)
    draw = ImageDraw.Draw(ids)
    C, Fi, Mz = [], [], []
    for (ln, wd, cover) in LOOK["dab_px"]:
        ln *= sc; wd *= sc
        step = wd * 1.25
        gy, gx = np.meshgrid(np.arange(step / 2, H, step), np.arange(step / 2, W, step), indexing="ij")
        cx = (gx + rng.uniform(-0.5, 0.5, gx.shape) * step).ravel(); cy = (gy + rng.uniform(-0.5, 0.5, gy.shape) * step).ravel()
        keep = rng.random(cx.shape) < cover
        ix = np.clip(cx, 0, W - 1).astype(int); iy = np.clip(cy, 0, H - 1).astype(int)
        keep &= hit[iy, ix]
        cx, cy, ix, iy = cx[keep], cy[keep], ix[keep], iy[keep]
        o_ = rng.permutation(len(cx)); cx, cy, ix, iy = cx[o_], cy[o_], ix[o_], iy[o_]
        nd = len(cx)
        f_ = fid[iy, ix]
        # a stroke is axial (its angle and angle + pi are the same stroke): blend the strike and the knife's lean doubled
        a2 = 0.45 * np.exp(2j * sang[iy, ix]) + 0.55 * np.exp(2j * DIAG)
        ang = np.angle(a2) / 2 + face_turn[f_ % len(face_turn)] + rng.normal(0, 0.25, nd)
        c0 = ramp(quant(v[iy, ix] + rng.normal(0, LOOK["level_jit"], nd) * lev))
        lv = quant(v[iy, ix])
        warm = smoothstep(0.3, 0.62, lv)[:, None]
        wg = (1 - warm) * rng.uniform(*LOOK["hue_w"], (nd, 1))                   # the mids and the shade: cool grey
        wo = smoothstep(0.5, 0.7, hf[iy, ix, 2])[:, None] * rng.uniform(0, LOOK["hue_w"][1], (nd, 1)) * (1 - 0.5 * warm)
        wu = warm * smoothstep(0.45, 0.7, hf[iy, ix, 0])[:, None] * rng.uniform(0, 0.4, (nd, 1))   # deeper ochre
        lum0 = (c0 @ LUMA)[:, None]
        c0 = c0 * (1 - wg - wo - wu) + lum0 * (hcol[1] * wg + hcol[2] * wo + hcol[0] * wu)
        mz = rng.random(nd) < moss[iy, ix]
        c0[mz] = (c0[mz] @ LUMA)[:, None] * moss_hue[None] * rng.uniform(0.85, 1.15, (int(mz.sum()), 1))
        c0 = c0 * (1 + rng.normal(0, 0.03, (nd, 3)))
        polys = lens(cx, cy, ang, ln * rng.uniform(0.75, 1.25, nd), wd * rng.uniform(0.8, 1.2, nd), rng)
        base = len(C)
        C.extend(c0); Fi.extend(f_); Mz.extend(mz)
        for k in range(nd):
            draw.polygon([tuple(q) for q in polys[k]], fill=base + k)
    idm = np.array(ids, np.int64)
    C = np.array(C); Fi = np.array(Fi)
    same = (idm >= 0) & hit
    same[same] = Fi[idm[same]] == fid[same]
    canvas[same] = C[idm[same]]
    mossy = moss > 0.5
    mossy[same] = np.array(Mz)[idm[same]]
    moss_share = float(mossy[hit].mean())          # the painted share of the boulder that is moss
    # cracks and chip edges: short broken dark lines (the target's knife-cut chips), each with a lit lip on its key side
    cw_, cl_, cden, cdark, clift = LOOK["crack"]
    crng = np.random.default_rng(salt + 202)
    ncr = int(cden * hit.sum() / IPPM ** 2)
    ys_c, xs_c = np.nonzero(hit)
    sel = crng.integers(0, len(ys_c), ncr)
    cim = Image.new("L", (W, H), 0); lim = Image.new("L", (W, H), 0)
    cd_, ld_ = ImageDraw.Draw(cim), ImageDraw.Draw(lim)
    off = np.array([-0.7, -0.7]) * cw_[1] * sc          # the lip: toward the key (the image's upper left)
    for k in range(ncr):
        x_, y_ = float(xs_c[sel[k]]), float(ys_c[sel[k]])
        a_ = (DIAG if crng.random() < 0.6 else sang[ys_c[sel[k]], xs_c[sel[k]]]) + crng.normal(0, 0.5)
        L_ = crng.uniform(*cl_) * sc; segs = crng.integers(1, 3)
        pts = [(x_, y_)]
        for _ in range(segs):
            a_ += crng.normal(0, 0.15)
            x_ += math.cos(a_) * L_ / segs; y_ += math.sin(a_) * L_ / segs; pts.append((x_, y_))
        wpx = max(1, int(round(crng.uniform(*cw_) * sc)))
        ld_.line([(px + off[0], py + off[1]) for px, py in pts], fill=255, width=wpx)
        cd_.line(pts, fill=255, width=wpx)
    cm = np.asarray(cim, np.float64) / 255.0 * hit
    lm = np.asarray(lim, np.float64) / 255.0 * hit * (1 - cm) * np.clip((v - 0.2) / 0.4, 0, 1)
    canvas = canvas * (1 + clift * lm[..., None])
    canvas = canvas * (1 - cm[..., None]) + canvas * cdark * cm[..., None]
    # the foot: grime and occlusion
    foot = smoothstep(-SINK, LOOK["foot_m"], yb)
    canvas = canvas * (LOOK["foot_dark"] + (1 - LOOK["foot_dark"]) * foot)[..., None]
    # breaks: a face meeting another at a real angle; its lit side lifted in a thin edge, the break inked (broken)
    breaks = np.zeros((H, W)); lit_side = np.zeros((H, W), bool)
    vflat = np.einsum("ijk,k->ij", n, L)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        sh = lambda x: np.roll(np.roll(x, -dy, 0), -dx, 1)
        e = hit & sh(hit) & (fid != sh(fid))
        angd = np.degrees(np.arccos(np.clip(np.sum(n * sh(n), -1), -1, 1)))
        breaks = np.maximum(breaks, smoothstep(*LOOK["crease_deg"], angd) * e)
        vb = sh(vflat)
        lit_side |= e & (vflat > vb + 0.15)
        lit_side |= np.roll(np.roll(e & (vb > vflat + 0.15), dy, 0), dx, 1)
    dist_b, (iy, ix) = ndimage.distance_transform_edt(breaks < 0.5, return_indices=True)
    brk = breaks[iy, ix]
    gap = smoothstep(0.3, 0.55, field(lambda q: fbm(q, 0.22, salt + 12)))
    cw = LOOK["crease_px"] * sc * (0.6 + 0.8 * field(lambda q: fbm(q, 0.3, salt + 13)))
    crease = (1 - smoothstep(cw * 0.5, cw * 0.5 + 1.5, dist_b)) * brk * gap * LOOK["crease_a"] * hit
    dist_l = ndimage.distance_transform_edt(~lit_side)
    lift = (1 - smoothstep(LOOK["edge_px"] * sc, LOOK["edge_px"] * sc + 2, dist_l)) * (dist_b > cw * 0.5) * hit
    canvas = canvas * (1 + LOOK["edge_light"] * lift[..., None])
    canvas = canvas * (1 - crease[..., None]) + lin(LOOK["crease"]) * crease[..., None]
    # the silhouette ink: heavier at the foot, wobbling
    dist_s = ndimage.distance_transform_edt(hit)
    yt = np.clip((yb + SINK) / (top + SINK), 0, 1)
    iw = (LOOK["ink_px"][0] * (1 - yt) + LOOK["ink_px"][1] * yt) * sc * (0.75 + 0.5 * field(lambda q: fbm(q, 0.4, salt + 14)))
    ink = (1 - smoothstep(iw - 1.5, iw + 1.5, dist_s)) * hit
    canvas = canvas * (1 - ink[..., None]) + lin(LOOK["ink"]) * ink[..., None]

    # store at 1/SS: box filter in linear light, alpha the mask's coverage
    def down(x):
        s_ = x.shape
        return x.reshape(s_[0] // SS, SS, s_[1] // SS, SS, *s_[2:]).mean(axis=(1, 3))
    a = down(hit.astype(np.float64))
    rgb = down(canvas * hit[..., None]) / np.maximum(a, 1e-6)[..., None]
    # the form channel: normal in the camera's basis (right, up, toward the camera), depth along the view from the card
    pivot = card_pivot(S)
    nc = np.stack([n @ R, n @ U, -(n @ F)], -1)
    dep = np.where(hit, (p - pivot) @ F, 0.0)
    ncs = down(nc * hit[..., None]) / np.maximum(a, 1e-6)[..., None]
    deps = down(dep * hit) / np.maximum(a, 1e-6)
    # every empty texel takes its nearest painted one's colour, normal and depth (mip-safe)
    _, (iy, ix) = ndimage.distance_transform_edt(~(a > 0), return_indices=True)
    rgb, ncs, deps = rgb[iy, ix], ncs[iy, ix], deps[iy, ix]
    return dict(S=S, rgb=rgb, a=a, n=ncs, d=deps, pivot=pivot, hull=hull(S["parts"]), moss=moss_share)


def card_pivot(S):
    """The card's point: the form's middle (its points' mean), so the card sits in the boulder (least parallax)."""
    p = S["p"][S["hit"]]
    return p.mean(0)


def hull(parts, nu=20, nv=12, grow=0.0):
    """The shadow caster: each convex part as a UV sphere pushed out to the part's surface from its centre."""
    V, I = [], []
    for c, rad, P in parts:
        base = len(V)
        cc = c.copy(); cc[1] = max(cc[1], 0.1)
        for j in range(nv + 1):
            th = math.pi * j / nv
            for i in range(nu):
                ph = 2 * math.pi * i / nu
                dvec = np.array([math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)])
                # the ray from cc along dvec to the part's boundary: min of the ellipsoid and the planes
                q0 = (cc - c) / rad; dq = dvec / rad
                A = dq @ dq; B = 2 * q0 @ dq; C = q0 @ q0 - 1
                t = (-B + math.sqrt(max(B * B - 4 * A * C, 0))) / (2 * A)
                for n, d in P:
                    nd = float(n @ dvec)
                    if nd > 1e-9:
                        t = min(t, (d - float(n @ cc)) / nd)
                V.append(list(map(float, cc + dvec * (t + grow))))
        for j in range(nv):
            for i in range(nu):
                a = base + j * nu + i; b = base + j * nu + (i + 1) % nu
                c2 = a + nu; d2 = b + nu
                I += [a, c2, b, b, c2, d2]
    return dict(v=[round(x, 4) for p in V for x in p], i=I)


def pack(items, aw=2048):
    """Shelf-pack the paintings' sizes into an atlas aw wide."""
    x = y = sh = 0; rects = []
    for w, h in items:
        if x + w > aw:
            x = 0; y += sh + 4; sh = 0
        rects.append((x, y, w, h)); x += w + 4; sh = max(sh, h)
    return rects, y + sh


def build():
    os.makedirs(OUT, exist_ok=True)
    res = [paint(f) for f in FORMS]
    rects, ah = pack([(r["rgb"].shape[1], r["rgb"].shape[0]) for r in res])
    ah = int(2 ** math.ceil(math.log2(ah)))
    AW = 2048
    assert ah <= 2048, f"atlas {AW}x{ah} over 2048x2048"
    paint_img = np.zeros((ah, AW, 4)); form_img = np.zeros((ah, AW, 4))
    form_img[..., :3] = 0.5; form_img[..., 3] = 0.5
    meta = dict(source="tools/look/den_boulders.py", ppm=PPM, dmax=DMAX, sink=SINK, atlas=[AW, ah],
                basis=dict(right=list(R), up=[round(x, 6) for x in U], view=[round(x, 6) for x in F]), boulders=[])
    for f, r, (x, y, w, h) in zip(FORMS, res, rects):
        paint_img[y:y + h, x:x + w, :3] = lin_to_srgb(r["rgb"]); paint_img[y:y + h, x:x + w, 3] = r["a"]
        form_img[y:y + h, x:x + w, :3] = np.clip(r["n"] * 0.5 + 0.5, 0, 1)
        form_img[y:y + h, x:x + w, 3] = np.clip(r["d"] / DMAX * 0.5 + 0.5, 0, 1)
        S = r["S"]; pv = r["pivot"]
        hp = S["p"][S["hit"]]
        meta["boulders"].append(dict(
            name=f["name"], size=f.get("size_class", "small"), rect=[x, y, w, h], moss=round(r["moss"], 4),
            # the card in the boulder's frame: its lower-left corner's (right, up) in metres and its size; the pivot (the
            # card's plane point) in boulder space
            card=[round(S["x0"], 4), round(S["y1"] - h / PPM, 4), round(w / PPM, 4), round(h / PPM, 4)],
            pivot=[round(float(v), 4) for v in pv],
            foot=[round(float(hp[:, 0].min()), 3), round(float(hp[:, 0].max()), 3), round(float(hp[:, 2].min()), 3),
                  round(float(hp[:, 2].max()), 3), round(float(hp[:, 1].max()), 3)],
            hull=r["hull"]))
    Image.fromarray((np.clip(paint_img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, "boulders_paint.png"), optimize=True)
    Image.fromarray((np.clip(form_img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, "boulders_form.png"), optimize=True)
    with open(os.path.join(OUT, "boulders.json"), "w") as fh:
        json.dump(meta, fh, separators=(",", ":"))
    print("wrote", len(res), "boulders, atlas", AW, "x", ah)
    return meta


# ---- preview and check ----

def target_crops():
    im = Image.open(TARGET).convert("RGB")
    s = im.width / 1672
    boxes = [(220, 80, 480, 300), (1140, 130, 1520, 370), (800, 0, 1015, 180), (440, 620, 620, 800)]
    return [im.crop(tuple(int(v * s) for v in b)) for b in boxes]


TARGET_LIT, TARGET_SHADE = (132, 102, 77), (41, 36, 34)     # den_room.png's boulders, measured (sRGB)
PREVIEW_FLOOR = (96, 68, 50)                                  # the den floor as the game shows it (sRGB, about)


def preview(out):
    """The boulders at the game's scale (73 px/m) on the den floor, four to a row, beside den_room.png's boulders at the
    frame's 1:1 (its 1672 px scaled to 1080p); and a 2x nearest zoom of a big one and a small one (the strokes)."""
    meta = json.load(open(os.path.join(OUT, "boulders.json")))
    pimg = Image.open(os.path.join(OUT, "boulders_paint.png")).convert("RGBA")
    k = GAME_PPM / PPM
    tiles = []
    for b in meta["boulders"]:
        x, y, w, h = b["rect"]
        t = pimg.crop((x, y, x + w, y + h)).resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
        bg = Image.new("RGBA", t.size, PREVIEW_FLOOR + (255,)); bg.alpha_composite(t); tiles.append(bg.convert("RGB"))
    big = [t for t, b in zip(tiles, meta["boulders"]) if b.get("size") == "big"]
    small = [t for t, b in zip(tiles, meta["boulders"]) if b.get("size") != "big"]
    tc = target_crops()
    tc = [t.resize((round(t.width * 1920 / 1672), round(t.height * 1920 / 1672)), Image.LANCZOS) for t in tc]
    rows = [big + small[:2], small[2:], tc]
    Wd = max(sum(t.width + 8 for t in r) for r in rows)
    hh = sum(max(t.height for t in r) + 8 for r in rows)
    sheet = Image.new("RGB", (Wd, hh), (20, 20, 20)); yy = 0
    for r in rows:
        xx = 0
        for t in r:
            sheet.paste(t, (xx, yy)); xx += t.width + 8
        yy += max(t.height for t in r) + 8
    sheet.save(out)
    pair = (big[:1] or tiles[:1]) + small[:1]
    z = Image.new("RGB", (sum(t.width * 2 + 8 for t in pair), max(t.height for t in pair) * 2), (20, 20, 20)); xx = 0
    for t in pair:
        z.paste(t.resize((t.width * 2, t.height * 2), Image.NEAREST), (xx, 0)); xx += t.width * 2 + 8
    z.save(out.replace(".png", "_zoom.png"))
    print("preview", out)


def check():
    """Per boulder: the lit band (median of its brightest 20%) and the shade (median of its darkest 20%) against
    den_room.png's measured boulders, the whole median, the painted moss share and the green-dominant share (G > R, the
    in-game complaint), its size in metres; and the atlas's hygiene (nothing on a rect's edge, depth inside DMAX)."""
    meta = json.load(open(os.path.join(OUT, "boulders.json")))
    pimg = np.asarray(Image.open(os.path.join(OUT, "boulders_paint.png")).convert("RGBA")).astype(np.float64)
    fimg = np.asarray(Image.open(os.path.join(OUT, "boulders_form.png")).convert("RGBA")).astype(np.float64)
    ok = True
    print(f"atlas {meta['atlas'][0]}x{meta['atlas'][1]}; target lit {TARGET_LIT} shade {TARGET_SHADE}")
    for b in meta["boulders"]:
        x, y, w, h = b["rect"]
        t = pimg[y:y + h, x:x + w]
        m = t[..., 3] > 250
        px = t[..., :3][m]
        lum = px @ LUMA
        hi = np.median(px[lum >= np.percentile(lum, 80)], 0); lo = np.median(px[lum <= np.percentile(lum, 20)], 0)
        md = np.median(px, 0)
        green = float(np.mean(px[:, 1] > px[:, 0]))
        ft = b["foot"]
        edge_a = np.concatenate([t[0, :, 3], t[-1, :, 3], t[:, 0, 3], t[:, -1, 3]]).max()
        dp = fimg[y:y + h, x:x + w, 3][m]
        clip = float(np.mean((dp <= 1) | (dp >= 254)))
        print(f"{b['name']:8s} {b.get('size', '?'):5s} lit {hi.round().astype(int)} shade {lo.round().astype(int)} "
              f"median {md.round().astype(int)} moss {b.get('moss', 0):.1%} green {green:.1%} "
              f"{ft[1] - ft[0]:.2f}w x {ft[4]:.2f}h x {ft[3] - ft[2]:.2f}d m  edge-a {edge_a:.0f} depth-clip {clip:.1%}")
        ok &= bool(edge_a == 0) and clip < 0.001 and "size" in b
    print("check", "OK" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        build(); check()
    elif cmd == "preview":
        out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(OUT, "_boulders_preview.png")
        preview(out)
    elif cmd == "check":
        sys.exit(0 if check() else 1)
