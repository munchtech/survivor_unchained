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
that face it, a cooler shade side), broad mottles, directional value strokes laid along each face (overlapping lens dabs,
never crossing a plane break), an olive moss cap on what faces up, the foot grimed, ink on the silhouette (heavier at the
foot) and on the main plane breaks (broken), a thin light edge on the lit side of a break. FROM den_room.png: the colours
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
GAME_PPM = 73.0          # the game's pixels per metre at 1080p (the play camera at the den's floor)
SS = 2                   # the painting is cast and painted at 2x the stored resolution, then box-filtered (its anti-alias)
PPM = 192                # stored pixels per metre (2.6x the game's: crisp after the mips)
IPPM = PPM * SS          # internal
DMAX = 2.5               # depth stored as d / DMAX * 0.5 + 0.5 (metres along the view from the card)

# ---- the look (sRGB). The ramp is the value a face takes by its turn to the key (n.L); lit and shade FROM den_room.png.
LOOK = dict(
    ramp=[  # (n.L, sRGB)
        (-1.00, (26, 25, 28)),
        (-0.30, (33, 31, 32)),
        (0.00, (41, 36, 34)),      # the shade (den_room.png's boulders' shade side, measured)
        (0.22, (52, 45, 40)),
        (0.42, (82, 66, 53)),
        (0.60, (132, 102, 77)),    # the lit band (den_room.png's boulders' lit planes, measured)
        (0.82, (152, 118, 86)),
        (1.00, (160, 125, 90)),
    ],
    band_pull=0.5,             # how far a face's value is pulled to its painted band's middle (flat planes, painted steps)
    key=(-0.62, 0.74, 0.12),   # toward the key as den_room.png's boulders show it: up, the image's left, a little front
    olive=(96, 100, 60), grey=(92, 92, 92), umber=(92, 66, 48),    # the hues the target's stone wanders between
    hue_w=(0.45, 0.35, 0.4),   # their shares at most
    dapple=(0.16, 0.38),       # the broad lit/unlit patches across a face (value, metres): the target's dappled planes
    moss=(72, 80, 44), moss_k=0.68,   # the moss's hue (sRGB, at the stone's value x moss_k)
    moss_up=(0.45, 0.8),       # the face's up share where the cap begins and is whole
    moss_gate=(0.56, 0.66),      # the noise gate (patches, not a blanket)
    ink=(20, 16, 14), ink_px=(2.6, 1.7),        # the silhouette ink (game px): at the foot, at the crown
    crease=(28, 22, 19), crease_px=1.4, crease_a=0.85, crease_deg=(20.0, 38.0),   # the inner breaks
    edge_light=0.22, edge_px=1.2,                # the lit side of a break, lifted
    foot_m=0.5, foot_dark=0.5,                   # grime and occlusion at the foot
    dab_px=[(15.0, 6.0, 1.0), (11.0, 4.5, 0.8), (7.5, 3.2, 0.55)],   # stroke layers: length, width (game px), coverage
    dab_jit=0.13,              # a stroke's value jitter (share)
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
        b = 0.07
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
    """Brush dabs: lens shapes, slightly asymmetric, ends tapered (n x 10 points)."""
    a = np.linspace(0, 2 * np.pi, 10, endpoint=False)
    n = len(cx)
    sk = rng.uniform(-0.25, 0.25, (n, 1))
    u = np.cos(a)[None] * ln[:, None] / 2
    v = np.sin(a)[None] * wd[:, None] / 2 * (1 + sk * np.cos(a)[None]) * rng.uniform(0.85, 1.15, (n, 10))
    ca, sa = np.cos(ang)[:, None], np.sin(ang)[:, None]
    return np.stack([cx[:, None] + u * ca - v * sa, cy[:, None] + u * sa + v * ca], -1)


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

    # value: each face's turn to the key (the bevel's softened), pulled toward its band's middle; the light falls off a
    # little down the stone; broad dapples across a face (the target's planes are lit in patches)
    v = np.einsum("ijk,k->ij", nb, L)
    yb = np.where(hit, p[..., 1], 0.0)
    top = max(float(yb[hit].max()), 0.5)
    v = v + 0.08 * (yb / top - 0.5)
    bands = np.array([-0.15, 0.12, 0.32, 0.52, 0.72])
    mids = np.array([-0.35, 0.0, 0.22, 0.42, 0.62, 0.84])
    v = v + LOOK["band_pull"] * (mids[np.searchsorted(bands, v)] - v)
    dk, ds = LOOK["dapple"]
    v = v + 2 * dk * (field(lambda q: fbm(q, ds, salt + 1)) - 0.5) + 0.07 * (field(lambda q: fbm(q, 0.12, salt + 2)) - 0.5)
    col = ramp(v)
    lum = col @ LUMA
    for hue, w_max, sk in ((LOOK["olive"], LOOK["hue_w"][0], 3), (LOOK["grey"], LOOK["hue_w"][1], 4), (LOOK["umber"], LOOK["hue_w"][2], 5)):
        w = smoothstep(0.5, 0.72, field(lambda q: fbm(q, 0.5, salt + sk))) * w_max
        col = col * (1 - w[..., None]) + (lum[..., None] * hue_of(hue)) * w[..., None]
    # moss: on what faces up, in patches: the stone's own value turned olive (so it lies under the same light)
    up = nb[..., 1]
    mg = field(lambda q: fbm(q, 0.4, salt + 9) * 0.7 + fbm(q, 0.1, salt + 10) * 0.3)
    moss = smoothstep(*LOOK["moss_up"], up) * smoothstep(*LOOK["moss_gate"], mg + 0.1 * (form.get("moss", 0.7) - 0.7))
    lum = col @ LUMA
    moss_col = lum[..., None] * hue_of(LOOK["moss"]) * LOOK["moss_k"]
    canvas = col * (1 - moss[..., None]) + moss_col * moss[..., None]
    # strokes: lens dabs laid along each face's strike (its horizontal on screen), each the field's colour at its middle
    # with a value jitter, never crossing a face's edge (a dab paints only the face its middle is on)
    st = np.cross(n, np.array([0.0, 1.0, 0.0]))
    stn = np.linalg.norm(st, axis=-1)
    st = np.where((stn > 0.2)[..., None], st, R)
    sang = np.arctan2(-(st @ U), st @ R)
    rng = np.random.default_rng(salt)
    ids = Image.new("I", (W, H), -1)
    draw = ImageDraw.Draw(ids)
    C, Fi = [], []
    for (ln, wd, cover) in LOOK["dab_px"]:
        ln *= sc; wd *= sc
        step = wd * 1.2
        gy, gx = np.meshgrid(np.arange(step / 2, H, step), np.arange(step / 2, W, step), indexing="ij")
        cx = (gx + rng.uniform(-0.5, 0.5, gx.shape) * step).ravel(); cy = (gy + rng.uniform(-0.5, 0.5, gy.shape) * step).ravel()
        keep = rng.random(cx.shape) < cover
        ix = np.clip(cx, 0, W - 1).astype(int); iy = np.clip(cy, 0, H - 1).astype(int)
        keep &= hit[iy, ix]
        cx, cy, ix, iy = cx[keep], cy[keep], ix[keep], iy[keep]
        nd = len(cx)
        ang = sang[iy, ix] + rng.normal(0, 0.3, nd)
        c0 = canvas[iy, ix] * (1 + rng.normal(0, LOOK["dab_jit"], (nd, 1))) * (1 + rng.normal(0, 0.03, (nd, 3)))
        polys = lens(cx, cy, ang, ln * rng.uniform(0.75, 1.25, nd), wd * rng.uniform(0.8, 1.2, nd), rng)
        base = len(C)
        C.extend(c0); Fi.extend(fid[iy, ix])
        for k in range(nd):
            draw.polygon([tuple(q) for q in polys[k]], fill=base + k)
    idm = np.array(ids, np.int64)
    C = np.array(C); Fi = np.array(Fi)
    same = (idm >= 0) & hit
    same[same] = Fi[idm[same]] == fid[same]
    canvas[same] = C[idm[same]]
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
    return dict(S=S, rgb=rgb, a=a, n=ncs, d=deps, pivot=pivot, hull=hull(S["parts"]))


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
            name=f["name"], rect=[x, y, w, h],
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


def preview(out):
    meta = json.load(open(os.path.join(OUT, "boulders.json")))
    pimg = Image.open(os.path.join(OUT, "boulders_paint.png")).convert("RGBA")
    k = GAME_PPM / PPM
    floor = (96, 72, 58)
    tiles = []
    for b in meta["boulders"]:
        x, y, w, h = b["rect"]
        t = pimg.crop((x, y, x + w, y + h)).resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
        bg = Image.new("RGBA", t.size, floor + (255,)); bg.alpha_composite(t); tiles.append(bg.convert("RGB"))
    tc = target_crops()
    tc = [t.resize((round(t.width * 1920 / 1672), round(t.height * 1920 / 1672)), Image.LANCZOS) for t in tc]
    Wd = 1600
    rows = [tiles[:3], tiles[3:], tc]
    hh = sum(max(t.height for t in r) + 8 for r in rows)
    sheet = Image.new("RGB", (Wd, hh), (20, 20, 20)); yy = 0
    for r in rows:
        xx = 0
        for t in r:
            sheet.paste(t, (xx, yy)); xx += t.width + 8
        yy += max(t.height for t in r) + 8
    sheet.save(out)
    # a 2x zoom of the first two (pixel-exact, nearest) to see the strokes
    z = Image.new("RGB", (tiles[0].width * 2 + tiles[1].width * 2 + 8, max(tiles[0].height, tiles[1].height) * 2), (20, 20, 20))
    z.paste(tiles[0].resize((tiles[0].width * 2, tiles[0].height * 2), Image.NEAREST), (0, 0))
    z.paste(tiles[1].resize((tiles[1].width * 2, tiles[1].height * 2), Image.NEAREST), (tiles[0].width * 2 + 8, 0))
    z.save(out.replace(".png", "_zoom.png"))
    print("preview", out)


def check():
    meta = json.load(open(os.path.join(OUT, "boulders.json")))
    pimg = np.asarray(Image.open(os.path.join(OUT, "boulders_paint.png")).convert("RGBA")).astype(np.float64)
    ok = True
    for b in meta["boulders"]:
        x, y, w, h = b["rect"]
        t = pimg[y:y + h, x:x + w]
        m = t[..., 3] > 250
        lum = t[..., :3] @ np.array([0.2126, 0.7152, 0.0722])
        v = lum[m]
        hi = t[..., :3][m][v >= np.percentile(v, 85)].mean(0); lo = t[..., :3][m][v <= np.percentile(v, 20)].mean(0)
        edge_a = np.concatenate([t[0, :, 3], t[-1, :, 3], t[:, 0, 3], t[:, -1, 3]]).max()
        print(f"{b['name']:6s} lit(p85+) {hi.round().astype(int)} shade(p20-) {lo.round().astype(int)} size {w / PPM:.2f}x{h / PPM:.2f} m"
              f" rect-edge alpha {edge_a:.0f}")
        ok &= edge_a == 0
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
