"""The den dungeon's floor decals: one painted atlas of the litter on the den's earth, ours from nothing (no photo or scan).

    python tools/look/den_decals.py build   -> godot/art/dungeon/den/decals.png (+ decals.json, the cells)
    python tools/look/den_decals.py check   -> rebuilt to a temp dir and compared byte for byte; every rect inside the
                                               atlas, padded and non-overlapping; nothing outside the cells

FROM the owner-approved den targets (den_room.png, den_boss.png, "Yes, build", 15 Nov): bones, rib cages, a wolf skull,
a deer skull with antlers, flayed hides, fur tufts, twigs, dead leaves, blood, root runners and pebbles, painted cel
(Marvel Rivals kind): each object two or three flat values (a lit side toward the painted light, a mid, a shade side),
a dark warm ink outline and a cast-shade edge on the side away from the light (an opaque dark-earth band, so the decal
works under alpha scissor); no gradients, no noise. Bone is the brightest thing on the floor and never white (its lit
value about linear luminance 0.5).

The painted light is ground.json "light" (the same as the den floor's). Each decal is drawn at 2x (512 px per metre),
box-reduced (straight alpha, a 1 px alpha ramp: the edges anti-aliased, never blurred) and packed into a 2048 atlas at
PX_PER_M = 256, its long axis horizontal in its cell (the game rotates them; the painted light turns with a decal, so
keep the turn inside about +-60 degrees for the lit side to stay toward the light). Nothing is drawn under 3 cm
(a stroke's body plus its ink). Deterministic: every decal is seeded by its kind and variant.
"""
import json, math, os, shutil, sys, tempfile, zlib

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "godot", "art", "dungeon", "den")
GROUND = os.path.join(ROOT, "godot", "data", "look", "ground.json")
VERSION = 1
PX_PER_M = 256          # the atlas
S = 2                   # drawn at S x, box-reduced
P = PX_PER_M * S        # px per metre while drawing
ATLAS = 2048
PAD = 10                # px between cells (>= 8) and from the atlas' border

# ---- the palette (sRGB albedo; [lit, mid, shade] for a shaded body) --------------------------------------------------
INK = "#26170f"         # the dark warm ink
CAST = "#3b2a1f"        # the cast-shade edge: the den earth in its own shadow
BONE = ("#c6bba0", "#a69a80", "#7f705a")          # lit ~ linear Y 0.50 (the cap), never white
ANTLER = ("#b09c7a", "#8f7b5c", "#665540")
HOLE = "#2e1d15"        # eye sockets, nasal openings
FUR = ("#aaa397", "#878077", "#5f5951")
FUR_INK = "#433b35"
FLESH = ("#6e2a20", "#57201a", "#3d1410")
FLESH_INK = "#2a0f0b"
SINEW = "#8a4a3a"
BLOOD = {"edge": "#380e0b", "body": "#4c1410", "mottle": "#5b1a13", "drop": "#4e1510"}
ROOT_C = ("#7c5439", "#573b28", "#3a2519")
BARK = "#4c301f"
TWIG = ("#7d5c41", "#584130", "#3b2a1f")
LEAF = [("#a8683a", "#8a522d", "#663b21"), ("#ad7840", "#8f5f31", "#6b4423"), ("#8e6542", "#73502f", "#553a22")]
LEAF_INK = "#2f1a10"
STONE = [("#8f8576", "#6e6558", "#4c443b"), ("#857d72", "#666054", "#463f37"), ("#968a78", "#746a5b", "#50473c")]

# ---- the list: kind, variants (each its longest extent in metres), the frequency hint per kind ------------------------
KINDS = [
    ("bone",       [0.32, 0.42, 0.5, 0.58, 0.36, 0.46], 1.0),
    ("ribcage",    [0.85, 1.05, 0.95], 0.35),
    ("wolf_skull", [0.3], 0.25),
    ("deer_skull", [0.8], 0.12),
    ("hide",       [1.15, 1.35], 0.15),
    ("fur",        [0.34, 0.42, 0.52, 0.46], 0.8),
    ("twigs",      [0.45, 0.62, 0.78, 0.55], 0.8),
    ("leaves",     [0.26, 0.34, 0.4, 0.3], 1.0),
    ("blood",      [0.65, 0.9, 1.15, 0.8], 0.5),
    ("root",       [1.6, 2.2, 2.9, 1.9], 0.6),
    ("pebbles",    [0.26, 0.32, 0.3], 0.9),
]


def seed_of(*k): return zlib.crc32(repr(k).encode()) & 0x7fffffff


def rgb(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255.0


def light2():
    L = np.array(json.load(open(GROUND, encoding="utf-8"))["light"], float)
    return L / np.linalg.norm(L)


LIGHT = light2()                                        # toward the light, image coords (x right, y down)
LIGHT3 = np.array([LIGHT[0], LIGHT[1], 1.0]) / math.sqrt(2.0)


def rot(pts, a):
    c, s = math.cos(a), math.sin(a)
    p = np.asarray(pts, float).reshape(-1, 2)
    return np.stack([p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c], 1)


def bez(p0, p1, p2, n=24, p3=None):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.asarray(v, float) for v in (p0, p1, p2))
    if p3 is None:
        return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2
    p3 = np.asarray(p3, float)
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


# ---- the painter -------------------------------------------------------------------------------------------------------
class Pad:
    """One decal's drawing surface at 2x, its origin at the centre, in metres."""

    def __init__(self, wm, hm):
        self.W = int(math.ceil(wm * P / 2)) * 2
        self.H = int(math.ceil(hm * P / 2)) * 2
        self.c = np.array([self.W / 2, self.H / 2])
        self.col = np.zeros((self.H, self.W, 3), np.float32)
        self.a = np.zeros((self.H, self.W), np.float32)
        self.parts = []

    def px(self, pts): return np.asarray(pts, float).reshape(-1, 2) * P + self.c

    def mask(self): return Mask(self)

    def add(self, m, cols=None, ink=INK, ink_m=0.008, prof="round", k=1.0, bevel_m=0.01, tl=0.80, ts=0.58, cast=True,
            details=(), flat=None):
        """A part: its mask, a shaded body ([lit, mid, shade]) or a flat color, its ink, its details (flat shapes)."""
        self.parts.append(dict(m=m, cols=cols, ink=ink, ink_m=ink_m, prof=prof, k=k, bevel_m=bevel_m, tl=tl, ts=ts,
                               cast=cast, details=list(details), flat=flat))

    def paint(self, m, h):
        self.col[m] = rgb(h)
        self.a[m] = 1.0

    def render(self, cast_m):
        cm = np.zeros((self.H, self.W), bool)
        for pt in self.parts:
            if pt["cast"]:
                cm |= dilate(pt["m"], pt["ink_m"] * P) if pt["ink"] else pt["m"]
        if cast_m > 0 and cm.any():
            d = -LIGHT * cast_m * P
            sh = np.zeros_like(cm)
            dx, dy = int(round(d[0])), int(round(d[1]))
            sh[max(dy, 0):self.H + min(dy, 0), max(dx, 0):self.W + min(dx, 0)] = \
                cm[max(-dy, 0):self.H + min(-dy, 0), max(-dx, 0):self.W + min(-dx, 0)]
            self.paint(dilate(sh, 0.003 * P), CAST)
        for pt in self.parts:
            m = pt["m"]
            if not m.any():
                continue
            if pt["ink"]:
                self.paint(dilate(m, pt["ink_m"] * P), pt["ink"])
            if pt["flat"]:
                self.paint(m, pt["flat"])
            else:
                lit, mid, shd = pt["cols"]
                dot = shade_dot(m, pt["prof"], pt["k"], pt["bevel_m"] * P)
                self.paint(m, mid)
                self.paint(m & (dot >= pt["tl"]), lit)
                self.paint(m & (dot < pt["ts"]), shd)
            for dm, h in pt["details"]:
                self.paint(dm & m if pt.get("clip", True) else dm, h)

    def reduce(self):
        """Crop to the painted bbox (+2 px), box-reduce S x premultiplied, straight alpha out, the RGB under the clear
        pixels filled from the nearest painted one (no dark or light fringe under filtering)."""
        ys, xs = np.nonzero(self.a > 0)
        y0, y1 = max(ys.min() - 2 * S, 0), min(ys.max() + 2 * S + 1, self.H)
        x0, x1 = max(xs.min() - 2 * S, 0), min(xs.max() + 2 * S + 1, self.W)
        y0 -= y0 % S; x0 -= x0 % S
        y1 += (-(y1 - y0)) % S; x1 += (-(x1 - x0)) % S
        col = np.zeros((y1 - y0, x1 - x0, 3), np.float32)
        a = np.zeros((y1 - y0, x1 - x0), np.float32)
        hh, ww = min(y1, self.H) - y0, min(x1, self.W) - x0
        col[:hh, :ww] = self.col[y0:y0 + hh, x0:x0 + ww]
        a[:hh, :ww] = self.a[y0:y0 + hh, x0:x0 + ww]
        h, w = a.shape[0] // S, a.shape[1] // S
        pa = (col * a[..., None]).reshape(h, S, w, S, 3).mean((1, 3))
        aa = a.reshape(h, S, w, S).mean((1, 3))
        c = np.where(aa[..., None] > 0, pa / np.maximum(aa[..., None], 1e-6), 0)
        a8 = np.clip(aa * 255 + 0.5, 0, 255).astype(np.uint8)
        c8 = np.clip(c * 255 + 0.5, 0, 255).astype(np.uint8)
        if (a8 == 0).any():
            _, (iy, ix) = ndimage.distance_transform_edt(a8 == 0, return_indices=True)
            c8 = c8[iy, ix]
        return np.dstack([c8, a8])


class Mask:
    def __init__(self, pad):
        self.p = pad
        self.im = Image.new("L", (pad.W, pad.H), 0)
        self.d = ImageDraw.Draw(self.im)

    def poly(self, pts):
        self.d.polygon([tuple(q) for q in self.p.px(pts)], fill=255)
        return self

    def circle(self, c, r):
        q = self.p.px(c)[0]
        R = r * P
        self.d.ellipse([q[0] - R, q[1] - R, q[0] + R, q[1] + R], fill=255)
        return self

    def ellipse(self, c, rx, ry, a=0.0, n=28):
        t = np.linspace(0, 2 * math.pi, n, endpoint=False)
        return self.poly(rot(np.stack([rx * np.cos(t), ry * np.sin(t)], 1), a) + c)

    def stroke(self, pts, w):
        """A variable-width stroke (w in metres at each point), round-jointed, so a tapered stroke ends in a point."""
        pts = np.asarray(pts, float)
        w = np.broadcast_to(np.asarray(w, float), (len(pts),))
        t = np.gradient(pts, axis=0)
        t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-12
        n = np.stack([-t[:, 1], t[:, 0]], 1) * (w[:, None] / 2)
        for i in range(len(pts) - 1):
            self.poly([pts[i] + n[i], pts[i + 1] + n[i + 1], pts[i + 1] - n[i + 1], pts[i] - n[i]])
        for i in range(len(pts)):
            if w[i] > 0.004:
                self.circle(pts[i], w[i] / 2)
        return self

    @property
    def m(self): return np.asarray(self.im) > 127


def _bbox(m, pad):
    ys, xs = np.nonzero(m)
    if len(ys) == 0:
        return None
    return (max(ys.min() - pad, 0), min(ys.max() + pad + 1, m.shape[0]),
            max(xs.min() - pad, 0), min(xs.max() + pad + 1, m.shape[1]))


def dilate(m, r):
    out = np.zeros_like(m)
    b = _bbox(m, int(math.ceil(r)) + 2)
    if b is None:
        return out
    y0, y1, x0, x1 = b
    out[y0:y1, x0:x1] = ndimage.distance_transform_edt(~m[y0:y1, x0:x1]) <= r
    return out


def shade_dot(m, prof, k, bevel_px):
    """n . light over the part, its height a rounded profile (a local radius, so a tapered stroke stays round) or a
    bevel (a flat top inside a slope band of bevel_px), smoothed by 1.2 px so the bands' edges are clean curves."""
    dot = np.full(m.shape, LIGHT3[2], np.float32)
    y0, y1, x0, x1 = _bbox(m, 6)
    mm = m[y0:y1, x0:x1]
    d = ndimage.distance_transform_edt(mm)
    if prof == "round":
        R = ndimage.maximum_filter(d, size=int(2 * d.max()) + 1)
        R = np.maximum(ndimage.uniform_filter(R, size=5), 1.0)
        t = np.clip(d / R, 0, 1)
        h = k * R * np.sqrt(1 - (1 - t) ** 2)
    else:
        h = k * np.minimum(d, bevel_px)
    h = ndimage.gaussian_filter(h, 1.2)
    gy, gx = np.gradient(h)
    n = np.stack([-gx, -gy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    dot[y0:y1, x0:x1] = n @ LIGHT3
    return dot


# ---- the kinds ---------------------------------------------------------------------------------------------------------
def k_bone(L, g, v):
    pad = Pad(L * 1.2 + 0.12, L * 0.55 + 0.12)
    bend = g.uniform(-0.05, 0.05)
    xs = np.linspace(-L / 2, L / 2, 25)
    spine = np.stack([xs, bend * L * (1 - (2 * xs / L) ** 2)], 1)
    kw = L * g.uniform(0.2, 0.25)
    sw = max(L * g.uniform(0.095, 0.115), 0.032)
    inset = kw * 0.42
    core = spine[(xs > -L / 2 + inset) & (xs < L / 2 - inset)]
    tt = np.linspace(-1, 1, len(core))
    m = pad.mask().stroke(core, sw * (1 - 0.14 * (1 - tt ** 2)))
    broken = v == 4
    for e, sgn in ((spine[0], -1), (spine[-1], 1)):
        e = e + np.array([-sgn * 0.0, 0]) + np.array([-sgn * inset, 0]) * 0
        c = e + np.array([-sgn * kw * 0.5, 0])
        if broken and sgn > 0:      # a split shaft: a jagged point
            tip = c + np.array([kw * 0.55, g.uniform(-0.3, 0.3) * sw])
            m.poly([c + [0, -sw * 0.55], c + [kw * 0.15, -sw * 0.3], tip, c + [kw * 0.25, sw * 0.2],
                    c + [kw * 0.05, sw * 0.55]])
            continue
        if (v + (sgn > 0)) % 2 == 0:  # two condyles
            m.circle(c + [0, -kw * 0.24], kw * 0.32).circle(c + [0, kw * 0.24], kw * 0.32)
            m.ellipse(c + [-sgn * kw * 0.12, 0], kw * 0.3, kw * 0.36)
        else:                          # a round head on a short neck, a small knob beside it
            m.circle(c + [sgn * kw * 0.04, -kw * 0.06], kw * 0.38).circle(c + [-sgn * kw * 0.12, kw * 0.26], kw * 0.2)
    mm = m.m
    # the notch between condyles and a nutrient line, in the shade color (detail)
    det = pad.mask()
    if not broken:
        det.stroke([spine[-1] + [-kw * 0.04, 0], spine[-1] + [-kw * 0.38, 0]], 0.012)
    pad.add(mm, BONE, tl=0.79, ts=0.6, details=[(det.m, BONE[2])])
    return pad, 0.012


def vertebra(c, a, b, ang):
    poly = [(-a / 2, -0.8 * b), (-0.22 * a, -b), (-0.12 * a, -1.75 * b), (0.16 * a, -1.75 * b), (0.26 * a, -b),
            (a / 2, -0.8 * b), (a / 2, 0.8 * b), (0.26 * a, b), (0.16 * a, 1.75 * b), (-0.12 * a, 1.75 * b),
            (-0.22 * a, b), (-a / 2, 0.8 * b)]
    return rot(poly, ang) + c


def k_ribcage(L, g, v):
    both = v == 1
    rl = L * g.uniform(0.34, 0.4)
    pad = Pad(L * 1.15 + 0.15, (2 * rl if both else rl) + 0.35)
    y0 = 0.0 if both else rl * 0.45
    xs = np.linspace(-L / 2, L / 2, 200)
    ys = y0 + 0.03 * L * np.sin(xs / L * 2.4 + g.uniform(0, 6))
    spine = np.stack([xs, ys], 1)
    tg = np.gradient(spine, axis=0)
    # ribs from the front 60% (toward +x), longest first, curving back (toward -x) like ")" lying down
    nrib = 5 if not both else 4
    sides = (-1, 1) if both else (-1,)
    ribs = []
    for i in range(nrib):
        x = L / 2 - L * 0.14 - i * L * 0.105 + g.uniform(-0.01, 0.01)
        j = int(np.argmin(abs(xs - x)))
        s = spine[j]
        for sd in sides:
            l = rl * (1 - 0.08 * i) * g.uniform(0.8, 1.05) * (0.55 if g.uniform() < 0.15 else 1.0)
            arc = rot(bez([0, 0], [0.12 * l, sd * 0.85 * l], [-0.22 * l, sd * 1.0 * l], 20), g.uniform(-0.14, 0.14)) + s
            ribs.append((sd, arc, np.linspace(0.042, 0.03, 20)))
    for sd, arc, w in ribs:
        if sd > 0:
            pad.add(pad.mask().stroke(arc, w).m, BONE, tl=0.79, ts=0.6)
    # vertebrae, shrinking toward the tail (-x)
    x = -L / 2 + 0.02
    while x < L / 2 - 0.03:
        f = 0.55 + 0.45 * (x + L / 2) / L
        a, b = 0.05 * max(f, 0.62), 0.021 * max(f, 0.75)
        j = int(np.argmin(abs(xs - x)))
        ang = math.atan2(tg[j, 1], tg[j, 0])
        pad.add(pad.mask().poly(vertebra(spine[j], a, b, ang)).m, BONE, ink_m=0.006, prof="bevel", bevel_m=0.008,
                tl=0.78, ts=0.62)
        x += a * 1.12
    # the skull end: a blunt broken stub
    for sd, arc, w in ribs:
        if sd < 0:
            pad.add(pad.mask().stroke(arc, w).m, BONE, tl=0.79, ts=0.6)
    return pad, 0.012


def skull_outline(prof, length, n=60):
    xs, hw = np.array(prof, float).T
    t = np.linspace(xs[0], xs[-1], n)
    w = np.interp(t, xs, hw)
    w = np.convolve(np.pad(w, 2, mode="edge"), np.ones(5) / 5, "valid")
    w[0] = w[-1] * 0 if prof[0][1] == 0 else w[0]
    top = np.stack([t, -w], 1)
    bot = np.stack([t, w], 1)[::-1]
    return np.concatenate([top, bot]) * length


def k_wolf_skull(L, g, v):
    pad = Pad(L * 1.3 + 0.1, L * 1.0 + 0.1)
    prof = [(-0.5, 0.0), (-0.47, 0.11), (-0.4, 0.17), (-0.26, 0.2), (-0.1, 0.205), (0.0, 0.29), (0.08, 0.31),
            (0.14, 0.25), (0.19, 0.15), (0.35, 0.12), (0.47, 0.1), (0.5, 0.05)]
    sk = skull_outline(prof, L)
    m = pad.mask().poly(sk).m
    holes = pad.mask()
    for sd in (-1, 1):
        holes.ellipse(np.array([0.06, sd * 0.215]) * L, 0.075 * L, 0.06 * L, sd * 0.35)
    holes.poly(np.array([(0.42, -0.04), (0.5, -0.03), (0.5, 0.03), (0.42, 0.04)]) * L)
    crest = pad.mask().stroke(np.array([(-0.46, 0), (-0.12, 0)]) * L, 0.01)
    fangs = pad.mask()
    for sd in (-1, 1):
        b = np.array([0.47, sd * 0.085]) * L
        fangs.poly([b + [-0.012, 0], b + [0.012, 0], b + [0.03, sd * 0.012]])
    pad.add(m | fangs.m, BONE, prof="round", k=0.7, tl=0.78, ts=0.6,
            details=[(dilate(holes.m, 0.004 * P), INK), (holes.m, HOLE), (crest.m, BONE[2])])
    return pad, 0.012


def k_deer_skull(L, g, v):
    pad = Pad(L * 1.2 + 0.1, L * 0.95 + 0.1)
    Sk = 0.3
    ox = L / 2 - Sk / 2
    prof = [(-0.5, 0.0), (-0.46, 0.12), (-0.36, 0.17), (-0.16, 0.19), (-0.02, 0.24), (0.08, 0.22), (0.16, 0.13),
            (0.32, 0.1), (0.46, 0.075), (0.5, 0.04)]
    sk = skull_outline(prof, Sk) + [ox, 0]
    # antlers from the pedicles, sweeping back (-x) and out, the tines toward the front and out
    for sd in (-1, 1):
        p0 = np.array([ox - 0.33 * Sk, sd * 0.1 * Sk])
        s = g.uniform(0.92, 1.06)
        beam = bez(p0, p0 + [-0.06, sd * 0.13 * s], p0 + [-0.3 * s, sd * 0.2 * s], 30, p3=p0 + [-0.5 * s, sd * 0.24 * s])
        m = pad.mask().stroke(beam, np.linspace(0.045, 0.03, 30))
        for tt, ln, ang in ((0.22, 0.12, 0.2), (0.5, 0.15, 0.5), (0.78, 0.11, 0.8)):
            j = int(tt * 29)
            dvec = beam[j + 1] - beam[j]
            dvec /= np.linalg.norm(dvec)
            ang += g.uniform(-0.25, 0.25)
            dd = np.array([0.55 + 0.25 * ang, sd * (1.0 - 0.3 * ang)])
            dd /= np.linalg.norm(dd)
            ln *= g.uniform(0.85, 1.12)
            tine = bez(beam[j], beam[j] + dd * ln * 0.55, beam[j] + dd * ln + [0.03, 0], 12)
            m.stroke(tine, np.linspace(0.034, 0.012, 12))
        e = beam[-1]                         # the beam's end forks
        m.stroke(bez(e, e + [-0.03, sd * 0.05], e + [-0.02, sd * 0.1], 10), np.linspace(0.03, 0.012, 10))
        pad.add(m.m, ANTLER, tl=0.79, ts=0.6)
    holes = pad.mask()
    for sd in (-1, 1):
        holes.ellipse(np.array([ox + 0.0 * Sk, sd * 0.2 * Sk]), 0.07 * Sk, 0.05 * Sk, sd * 0.3)
    holes.poly(np.array([(0.3, -0.03), (0.5, -0.02), (0.5, 0.02), (0.3, 0.03)]) * Sk + [ox, 0])
    crest = pad.mask().stroke(np.array([(-0.45, 0), (-0.1, 0)]) * Sk + [ox, 0], 0.01)
    pad.add(pad.mask().poly(sk).m, BONE, k=0.7, tl=0.78, ts=0.6,
            details=[(dilate(holes.m, 0.004 * P), INK), (holes.m, HOLE), (crest.m, BONE[2])])
    return pad, 0.012


def blob(n, rx, ry, g, amp=0.12, lobes=()):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    r = np.ones(n)
    for f in (2, 3, 5):
        r += amp / f * 2 * np.sin(f * t + g.uniform(0, 6.3))
    for a0, ext, wd in lobes:
        dd = np.angle(np.exp(1j * (t - a0)))
        r += ext * np.exp(-(dd / wd) ** 2)
    return np.stack([rx * r * np.cos(t), ry * r * np.sin(t)], 1)


def fur_strands(pad, base, dirs, lens, g, widths=0.03):
    """Pointed strands from base points along dirs: three layers (a dark under-layer pushed away from the light, the body,
    a lit top layer of shorter strands on the light's side) as flat colors."""
    lay = [pad.mask(), pad.mask(), pad.mask()]
    for b, d, ln in zip(base, dirs, lens):
        bend = g.uniform(-0.25, 0.25)
        nrm = np.array([-d[1], d[0]])
        for li, (off, sc) in enumerate(((-LIGHT * 0.012, 1.08), (np.zeros(2), 1.0), (LIGHT * 0.01, 0.62))):
            if li == 2 and (d @ LIGHT) < -0.2 and g.uniform() < 0.7:
                continue
            l = ln * sc
            pts = bez(b + off, b + off + d * l * 0.5 + nrm * bend * l * 0.2, b + off + d * l + nrm * bend * l * 0.5, 10)
            lay[li].stroke(pts, np.linspace(widths, 0.003, 10))
    return [x.m for x in lay]


def k_fur(L, g, v):
    pad = Pad(L * 1.25 + 0.1, L * 0.8 + 0.1)
    core_l = L * 0.55
    xs = np.linspace(-core_l / 2, core_l / 2, 30)
    bend = g.uniform(-0.06, 0.06)
    spine = np.stack([xs, bend * L * (1 - (2 * xs / core_l) ** 2)], 1)
    core_w = L * 0.2
    core = pad.mask().stroke(spine, core_w * np.sin(np.linspace(0.25, 2.9, 30)) ** 0.6).m
    base, dirs, lens = [], [], []
    swept = v % 2 == 1     # a lock combed one way (den_boss) or a flat patch radiating (den_room)
    n = int(60 + 110 * L)
    for _ in range(n):
        j = int(g.integers(30))
        u = (j / 29) * 2 - 1
        lat = g.uniform(-1, 1)
        b = spine[j] + np.array([0, lat * core_w * 0.4 * math.sin(0.25 + (u + 1) / 2 * 2.65) ** 0.6])
        if swept:
            ang = lat * 0.75 + u * 0.15 + g.uniform(-0.2, 0.2)
            if u < -0.6 and g.uniform() < 0.4:
                ang = math.pi + lat * 0.8
            ln = L * g.uniform(0.18, 0.36) * (1.15 - 0.3 * abs(lat))
        else:
            ang = math.atan2(lat * 0.8 + g.uniform(-0.3, 0.3), u * 1.6 + g.uniform(-0.3, 0.3))
            ln = L * g.uniform(0.12, 0.26) * (1 + 0.35 * abs(math.cos(ang)))
        base.append(b)
        dirs.append(np.array([math.cos(ang), math.sin(ang)]))
        lens.append(ln)
    under, body, top = fur_strands(pad, base, dirs, lens, g, widths=0.026)
    pad.add(under | dilate(core, 0.008 * P), flat=FUR[2], ink=FUR_INK, ink_m=0.004)
    pad.add(body | core, flat=FUR[1], ink=None, cast=False)
    pad.add(top, flat=FUR[0], ink=None, cast=False)
    return pad, 0.008


def k_hide(L, g, v):
    pad = Pad(L * 1.25 + 0.15, L * 0.95 + 0.15)
    lobes = [(a0 + g.uniform(-0.3, 0.3), g.uniform(0.15, 0.4), g.uniform(0.1, 0.2))
             for a0 in (0.6, 2.5, 3.75, 5.7)] + [(g.uniform(0, 6.3), 0.12, 0.08) for _ in range(5)]
    out = blob(120, L * 0.4, L * 0.24, g, 0.14, lobes=lobes)
    tear = np.linspace(0, 1, len(out))
    out = out * (1 + 0.035 * np.sign(np.sin(tear * 2 * math.pi * 23 + g.uniform(0, 6))))[:, None]  # torn, ragged edge
    hide = pad.mask().poly(out).m
    base, dirs, lens = [], [], []
    # the fur mass: a swept lock over the hide's +x end (fur side partly turned up), its strands combed out past the edge
    fc, frx, fry = np.array([0.17 * L, 0.06 * L]), 0.15 * L, 0.11 * L
    fur_core = pad.mask().ellipse(fc, frx, fry, g.uniform(-0.2, 0.2)).m
    for _ in range(int(120 * L)):
        r_, a_ = math.sqrt(g.uniform()), g.uniform(0, 2 * math.pi)
        b = fc + [r_ * frx * math.cos(a_), r_ * fry * math.sin(a_)]
        lat = (b[1] - fc[1]) / fry
        ang = 0.25 + lat * 0.7 + g.uniform(-0.25, 0.25)
        base.append(b)
        dirs.append(np.array([math.cos(ang), math.sin(ang)]))
        lens.append(L * g.uniform(0.1, 0.22))
    under, body, top = fur_strands(pad, base, dirs, lens, g, widths=0.026)
    streaks = pad.mask()
    for _ in range(4):
        a0 = g.uniform(-0.3, 0.3)
        c0 = np.array([g.uniform(-0.25, 0.2) * L, g.uniform(-0.12, 0.08) * L])
        pts = bez(c0, c0 + rot([[0.12 * L, 0.03 * L]], a0)[0], c0 + rot([[0.24 * L, -0.01 * L]], a0)[0], 12)
        streaks.stroke(pts, np.linspace(0.035, 0.012, 12))
    sinew = pad.mask()
    for _ in range(3):
        c0 = np.array([g.uniform(-0.2, 0.25) * L, g.uniform(-0.14, 0.05) * L])
        sinew.ellipse(c0, g.uniform(0.03, 0.05), g.uniform(0.018, 0.026), g.uniform(-0.4, 0.4))
    pad.add(hide, FLESH, ink=FLESH_INK, ink_m=0.009, k=0.3, tl=0.75, ts=0.64,
            details=[(streaks.m, FLESH[2]), (sinew.m, SINEW)])
    pad.add(under | dilate(fur_core, 0.008 * P), flat=FUR[2], ink=FUR_INK, ink_m=0.004)
    pad.add(body | fur_core, flat=FUR[1], ink=None, cast=False)
    pad.add(top, flat=FUR[0], ink=None, cast=False)
    # ribs out of the flesh at the -x end, curving back over it
    for i in range(4):
        s = np.array([-L * 0.2 + i * L * 0.075, -L * 0.02 + i * 0.01])
        l = L * (0.3 - 0.03 * i) * g.uniform(0.9, 1.05)
        arc = bez(s, s + [-0.25 * l, -0.75 * l], s + [-0.75 * l, -0.75 * l], 20)
        pad.add(pad.mask().stroke(arc, np.linspace(0.04, 0.03, 20)).m, BONE, tl=0.79, ts=0.6)
    return pad, 0.01


def k_twigs(L, g, v):
    pad = Pad(L * 1.2 + 0.1, L * 0.7 + 0.1)
    n = 7
    ang = np.cumsum(g.uniform(-0.22, 0.22, n)) * 0.6
    seg = L * 0.86 / n
    pts = [np.array([-L * 0.43, 0.0])]
    for a in ang:
        pts.append(pts[-1] + seg * np.array([math.cos(a), math.sin(a)]))
    pts = np.array(pts)
    pts -= pts.mean(0) * [0, 1]
    m = pad.mask().stroke(pts, np.linspace(0.036, 0.026, len(pts)))
    nb = 2 + (v % 2)
    for i in range(nb):
        j = 2 + int((i + g.uniform(0.2, 0.8)) / nb * (n - 3))
        sd = 1 if (i + v) % 2 == 0 else -1
        a = ang[min(j, n - 1)] + sd * g.uniform(0.45, 0.8)
        ln = L * g.uniform(0.18, 0.32)
        b = pts[j]
        e = b + ln * np.array([math.cos(a), math.sin(a)])
        mid = (b + e) / 2 + rot([[0, sd * ln * 0.06]], a)[0]
        br = bez(b, mid, e, 10)
        m.stroke(br, np.linspace(0.028, 0.024, 10))
        if g.uniform() < 0.5:
            a2 = a - sd * 0.6
            m.stroke([br[6], br[6] + ln * 0.4 * np.array([math.cos(a2), math.sin(a2)])], [0.024, 0.022])
    pad.add(m.m, TWIG, ink_m=0.006, tl=0.79, ts=0.6)
    return pad, 0.01


def leaf_poly(c, ln, a, kind, g):
    t = np.linspace(0, 1, 40)
    if kind == 0:   # lobed (oak-like)
        hw = 0.33 * ln * np.sin(np.pi * t) ** 0.8 * (1 + 0.32 * np.sin(t * 2 * math.pi * 3.5 + 0.5))
    else:           # pointed (a willow/beech-like oval)
        hw = 0.27 * ln * np.sin(np.pi * t ** 0.8) ** 0.9
    x = (t - 0.5) * ln
    top = np.stack([x, -hw], 1)
    bot = np.stack([x, hw * g.uniform(0.85, 1.0)], 1)[::-1]
    return rot(np.concatenate([top, bot]), a) + c


def k_leaves(L, g, v):
    pad = Pad(L * 1.3 + 0.1, L * 1.0 + 0.1)
    n = 3 + int(g.integers(5)) if v != 0 else 4
    placed = []
    for i in range(n):
        for _ in range(40):
            c = np.array([g.uniform(-0.36, 0.36) * L, g.uniform(-0.2, 0.2) * L])
            if all(np.linalg.norm(c - q) > 0.06 for q in placed):
                break
        placed.append(c)
    for i, c in enumerate(placed):
        ln = g.uniform(0.095, 0.14)
        a = g.uniform(0, 2 * math.pi)
        kind = int(g.integers(2))
        poly = leaf_poly(c, ln, a, kind, g)
        lm = pad.mask().poly(poly).m
        d = np.array([math.cos(a), math.sin(a)])
        nrm = np.array([-d[1], d[0]])
        half = pad.mask().poly([c + d * ln, c + d * ln + nrm * ln * (1 if nrm @ LIGHT > 0 else -1),
                                c - d * ln + nrm * ln * (1 if nrm @ LIGHT > 0 else -1), c - d * ln]).m
        vein = pad.mask().stroke([c - d * ln * 0.62, c + d * ln * 0.42], 0.007).m
        cols = LEAF[int(g.integers(len(LEAF)))]
        pad.add(lm, flat=cols[1], ink=LEAF_INK, ink_m=0.005, details=[(half, cols[0]), (vein, cols[2])])
    return pad, 0.007


def k_blood(L, g, v):
    pad = Pad(L * 1.35 + 0.1, L * 1.0 + 0.1)
    yy, xx = np.mgrid[0:pad.H, 0:pad.W]
    X, Y = (xx - pad.c[0]) / P, (yy - pad.c[1]) / P
    f = np.zeros_like(X)
    c = np.array([-0.22 * L, 0.0])
    for i in range(16 + int(L * 12)):        # a smear: blotches along a wandering walk, big near its start
        c = c + np.array([g.uniform(0.0, 0.07), g.uniform(-0.06, 0.06)]) * L
        if c[0] > 0.2 * L or abs(c[1]) > 0.16 * L:
            c = np.array([g.uniform(-0.25, 0.05) * L, g.uniform(-0.1, 0.1) * L])
        r = g.uniform(0.03, 0.075) * L * (1.3 if i < 4 else 1.0)
        f += np.exp(-((X - c[0]) ** 2 + (Y - c[1]) ** 2) / (r * r))
    nz = ndimage.gaussian_filter(g.standard_normal(X.shape).astype(np.float32), 0.025 * P)
    nz /= nz.std() + 1e-9
    pool = ndimage.binary_fill_holes(f * (1 + 0.45 * nz) > 0.62)
    # spatter: drops thrown toward +x, some drawn out into teardrops away from the pool
    drops = pad.mask()
    for _ in range(int(14 + 18 * L)):
        ang = g.normal(0, 0.65)
        dist = g.uniform(0.25, 0.62) * L
        c = np.array([math.cos(ang) * dist, math.sin(ang) * dist * 0.75])
        r = g.uniform(0.016, 0.03)
        if g.uniform() < 0.35:
            d = c / (np.linalg.norm(c) + 1e-9)
            drops.stroke([c, c + d * r * 2.4], [2 * r, 0.006])
        else:
            drops.circle(c, r)
    dm = drops.m & ~pool
    inner = ~dilate(~pool, 0.012 * P) & pool
    f2 = np.zeros_like(X)
    for _ in range(4):
        cx, cy = g.uniform(-0.25, 0.15) * L, g.uniform(-0.1, 0.1) * L
        r = g.uniform(0.04, 0.08) * L
        f2 += np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (r * r))
    mott = (f2 > 0.6) & ~dilate(~pool, 0.03 * P)
    pad.add(pool, flat=BLOOD["edge"], ink=None, cast=False, details=[(inner, BLOOD["body"]), (mott, BLOOD["mottle"])])
    pad.add(dm, flat=BLOOD["drop"], ink=None, cast=False)
    return pad, 0.0


def k_root(L, g, v):
    W = [0.11, 0.08, 0.12, 0.065][v % 4]
    pad = Pad(L * 1.1 + 0.2, L * 0.5 + 0.2)
    n = 80
    t = np.linspace(0, 1, n)
    # a gnarled path: a walk of 7-10 straight runs with sharp turns, rounded once (Chaikin), resampled evenly
    k = int(g.integers(7, 11))
    ang = np.clip(np.cumsum(g.uniform(-0.8, 0.8, k)) * 0.8, -0.85, 0.85)
    ang -= ang.mean()
    walk = np.concatenate([[[0.0, 0.0]], np.cumsum(np.stack([np.cos(ang), np.sin(ang)], 1) * (L / k), 0)])
    for _ in range(3):
        q = np.stack([0.75 * walk[:-1] + 0.25 * walk[1:], 0.25 * walk[:-1] + 0.75 * walk[1:]], 1).reshape(-1, 2)
        walk = np.concatenate([walk[:1], q, walk[-1:]])
    seglen = np.r_[0, np.cumsum(np.linalg.norm(np.diff(walk, axis=0), axis=1))]
    walk = np.stack([np.interp(t * seglen[-1], seglen, walk[:, i]) for i in (0, 1)], 1)
    a0 = math.atan2(*(walk[-1] - walk[0])[::-1])
    main = rot(walk - walk.mean(0), -a0) * (L / max(np.ptp(rot(walk, -a0)[:, 0]), 1e-6))
    # thick where it comes up out of the earth (t=0), swelling over the first tenth, tapering to the tip
    w = W * (1 - 0.7 * t ** 0.8) * (0.6 + 0.4 * np.clip(t / 0.1, 0, 1) ** 0.5)
    w = np.maximum(w, 0.032)
    tg = np.gradient(main, axis=0)
    lips = pad.mask()
    lip = lambda j, sgn: lips.ellipse(main[j] + sgn * tg[j] / np.linalg.norm(tg[j]) * 0.012, 0.03, w[j] * 0.9,
                                      math.atan2(tg[j, 1], tg[j, 0]))
    lip(0, -1)
    if v % 2 == 0:      # it dives under the earth for a stretch and comes up again: narrowing into the cuts, earth over the ends
        jg = int(n * g.uniform(0.42, 0.5))
        gs = max(int(g.uniform(0.13, 0.2) / (L / n)), 3)
        a_, b_ = jg - gs // 2, jg + gs - gs // 2
        nar = np.clip(np.minimum(abs(np.arange(n) - a_), abs(np.arange(n) - b_)) / 4.0, 0.55, 1.0)
        m = pad.mask().stroke(main[:a_ + 1], (w * nar)[:a_ + 1]).stroke(main[b_:], (w * nar)[b_:])
        lip(a_, 1)
        lip(b_, -1)
    else:
        m = pad.mask().stroke(main, w)
    nf = 1 + int(v % 2 == 0)
    for i in range(nf):
        j = int(n * (0.3 + 0.35 * i + g.uniform(-0.05, 0.05)))
        a0 = math.atan2(tg[j, 1], tg[j, 0])
        sd = 1 if (i + v) % 2 else -1
        a = a0 + sd * g.uniform(0.35, 0.6)
        ln = L * g.uniform(0.25, 0.42)
        b = main[j]
        e = b + ln * np.array([math.cos(a), math.sin(a)])
        mid = (b + e) / 2 + rot([[0, -sd * ln * 0.12]], a)[0]
        br = bez(b, mid, e, 30)
        m.stroke(br, np.maximum(np.linspace(w[j] * 0.62, 0.032, 30), 0.032))
    for i in range(2 + int(L > 2.0)):        # short rootlets off the thin half
        j = int(n * g.uniform(0.58, 0.88))
        a0 = math.atan2(tg[j, 1], tg[j, 0])
        sd = -1 if (i + v) % 2 else 1
        a = a0 + sd * g.uniform(0.6, 1.0)
        ln = g.uniform(0.12, 0.24)
        b = main[j]
        e = b + ln * np.array([math.cos(a), math.sin(a)])
        m.stroke(bez(b, (b + e) / 2 + rot([[0, sd * ln * 0.15]], a)[0], e, 10), 0.032)
    mm = m.m
    # bark: a few long darker streaks along the body (in its mid and lit bands only, clipped to the root)
    bark = pad.mask()
    for _ in range(int(L * 4)):
        j0 = int(g.integers(4, n - 14))
        ln = int(g.integers(5, 12))
        off = g.uniform(-0.18, 0.12)
        nn = np.stack([-tg[:, 1], tg[:, 0]], 1)
        nn /= np.linalg.norm(nn, axis=1, keepdims=True)
        seg = main[j0:j0 + ln] + nn[j0:j0 + ln] * (off * w[j0:j0 + ln])[:, None]
        bark.stroke(seg, 0.009)
    bm = bark.m & ~dilate(~mm, 0.012 * P)
    pad.add(mm, ROOT_C, ink_m=0.009, k=0.55, tl=0.76, ts=0.62, details=[(bm, BARK), (lips.m, CAST)])
    return pad, 0.008


def k_pebbles(L, g, v):
    pad = Pad(L * 1.3 + 0.1, L * 1.0 + 0.1)
    n = 3 + int(g.integers(4))
    placed = []
    for i in range(n):
        r = g.uniform(0.022, 0.05) if i else 0.05
        for _ in range(60):
            c = np.array([g.uniform(-0.38, 0.38) * L, g.uniform(-0.22, 0.22) * L])
            if all(np.linalg.norm(c - q) > r + rq + 0.02 for q, rq in placed):
                break
        placed.append((c, r))
    for c, r in sorted(placed, key=lambda q: q[0] @ LIGHT, reverse=True):
        k = int(g.integers(6, 9))
        t = np.sort(g.uniform(0, 2 * math.pi, k))
        rr = r * g.uniform(0.8, 1.1, k)
        pts = np.stack([rr * np.cos(t), rr * np.sin(t) * g.uniform(0.6, 0.85)], 1)
        pts = rot(pts, g.uniform(0, math.pi)) + c
        cols = STONE[int(g.integers(len(STONE)))]
        pad.add(pad.mask().poly(pts).m, cols, ink_m=0.006, prof="bevel", bevel_m=r * 0.35, tl=0.66, ts=0.5)
    return pad, 0.012


DRAW = {"bone": k_bone, "ribcage": k_ribcage, "wolf_skull": k_wolf_skull, "deer_skull": k_deer_skull, "hide": k_hide,
        "fur": k_fur, "twigs": k_twigs, "leaves": k_leaves, "blood": k_blood, "root": k_root, "pebbles": k_pebbles}


# ---- build ---------------------------------------------------------------------------------------------------------------
def cells():
    out = []
    for kind, sizes, wt in KINDS:
        for v, L in enumerate(sizes):
            g = np.random.default_rng(seed_of("den_decals", VERSION, kind, v))
            pad, cast_m = DRAW[kind](L, g, v)
            pad.render(cast_m)
            out.append((kind, v, wt / len(sizes), pad.reduce()))
    return out


def pack(items):
    """Shelves, tallest first (stable), PAD px apart and from the border."""
    order = sorted(range(len(items)), key=lambda i: (-items[i].shape[0], i))
    x, y, shelf, rects = PAD, PAD, 0, {}
    for i in order:
        h, w = items[i].shape[:2]
        if x + w + PAD > ATLAS:
            x, y, shelf = PAD, y + shelf + PAD, 0
        if y + h + PAD > ATLAS:
            raise SystemExit("den_decals: the atlas is full")
        rects[i] = (x, y, w, h)
        x += w + PAD
        shelf = max(shelf, h)
    return [rects[i] for i in range(len(items))]


def build(out_dir):
    cs = cells()
    rects = pack([c[3] for c in cs])
    atlas = np.zeros((ATLAS, ATLAS, 4), np.uint8)
    dec = []
    for (kind, v, wt, img), (x, y, w, h) in zip(cs, rects):
        atlas[y:y + h, x:x + w] = img
        dec.append({"kind": kind, "variant": v, "rect": [x, y, w, h],
                    "metres": [round(w / PX_PER_M, 3), round(h / PX_PER_M, 3)], "weight": round(wt, 4)})
    # under the clear pixels between cells: the ink color (no fringe from any mip)
    clear = atlas[..., 3] == 0
    inside = np.zeros_like(clear)
    for x, y, w, h in rects:
        inside[y:y + h, x:x + w] = True
    atlas[clear & ~inside, :3] = (rgb(INK) * 255 + 0.5).astype(np.uint8)
    os.makedirs(out_dir, exist_ok=True)
    Image.fromarray(atlas, "RGBA").save(os.path.join(out_dir, "decals.png"), optimize=False, compress_level=9)
    man = {"what": "The den floor's painted decals (tools/look/den_decals.py, VERSION %d): straight alpha, edges a 1 px "
                   "alpha ramp; each decal's long axis horizontal in its rect, the painted light from the rect's top "
                   "(ground.json light); rect = [x, y, w, h] px, metres = [w, h]; weight = a frequency hint (per kind, "
                   "split over its variants)." % VERSION,
           "version": VERSION, "size": [ATLAS, ATLAS], "px_per_m": PX_PER_M, "light": [round(float(c), 4) for c in LIGHT],
           "decals": dec}
    with open(os.path.join(out_dir, "decals.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(man, f, indent=1)
        f.write("\n")
    return man


def check():
    ok = True
    man = json.load(open(os.path.join(OUT, "decals.json"), encoding="utf-8"))
    im = np.asarray(Image.open(os.path.join(OUT, "decals.png")))
    rs = [d["rect"] for d in man["decals"]]
    inside = np.zeros(im.shape[:2], bool)
    for i, (x, y, w, h) in enumerate(rs):
        if x < PAD or y < PAD or x + w > ATLAS - PAD or y + h > ATLAS - PAD:
            print("FAIL rect %d outside the atlas' padded border: %s" % (i, rs[i])); ok = False
        for j in range(i):
            X, Y, Wd, Hd = rs[j]
            if x < X + Wd + 8 and X < x + w + 8 and y < Y + Hd + 8 and Y < y + h + 8:
                print("FAIL rects %d and %d overlap or sit under 8 px apart" % (i, j)); ok = False
        inside[y:y + h, x:x + w] = True
    if im[~inside, 3].any():
        print("FAIL painted pixels outside the cells"); ok = False
    d = tempfile.mkdtemp()
    try:
        build(d)
        for fn in ("decals.png", "decals.json"):
            if open(os.path.join(d, fn), "rb").read() != open(os.path.join(OUT, fn), "rb").read():
                print("FAIL %s differs from a rebuild (stale or hand-touched)" % fn); ok = False
    finally:
        shutil.rmtree(d, ignore_errors=True)
    kinds = {}
    for dd in man["decals"]:
        kinds[dd["kind"]] = kinds.get(dd["kind"], 0) + 1
    print("den_decals: %d decals, %s, %d px per metre: %s" % (len(rs), "ok" if ok else "FAILED", man["px_per_m"], kinds))
    return ok


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        m = build(OUT)
        print("den_decals: wrote %d decals to %s" % (len(m["decals"]), os.path.relpath(OUT, ROOT)))
    elif cmd == "check":
        sys.exit(0 if check() else 1)
    else:
        print(__doc__)
        sys.exit(2)
