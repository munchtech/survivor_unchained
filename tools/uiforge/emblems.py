"""Skill and art icons as modelled emblems (icons/glyph_color/KEY.png), for the ones the
painted family left soft or put a person in: each is drawn as shapes (signed distances in
a 100-unit square, y down), given heights, materials and a grain, lit by the house's
matcaps with its own light where it burns, and set on black in its school's glow: that is
the guide. The local Krea paints over the guide at a middling denoise (the hand, the
brushwork, the light's variety), and the icon is cut on the guide's own silhouette, so its
shape stays exact and reads at 17 px.

The thing itself, never a person: a hand mirror, an empty hood, a lamp of the Ford.
The world shows in what they are made of: the binders' twisted wire and square-holed
coin, the Waystation's lamp-iron, the Morrow's ember, the Order's dawn.

    python tools/uiforge/emblems.py [KEY ...]      # guides and paintings, one by one
    python tools/uiforge/emblems.py --many [KEY ...]  # all paintings in one queued graph
    python tools/uiforge/emblems.py --guides KEY   # guides only (no GPU)
    python tools/uiforge/emblems.py --fit [KEY ...]   # write the picked icons (PICKS)
"""
from __future__ import annotations

import math
import os
import sys

import cv2
import numpy as np
from PIL import Image

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui", "icons", "glyph_color")
RAW = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "emblems")
N = 1024          # the guide's size
K = N / 100.0     # px per unit

# The schools' light (brief 5.1): the hot core and the glow round it.
SCHOOL = {
    "physical": ("#fff4e0", "#e8dcc4"), "fire": ("#ffe0a0", "#ff6a1a"), "frost": ("#f0fbff", "#6ab8ff"),
    "storm": ("#f4f6ff", "#7a98ff"), "nature": ("#eaffd0", "#5ac83a"), "arcane": ("#ffe6ff", "#b25aff"),
    "holy": ("#fff6d0", "#ffc040"), "shadow": ("#e8dcff", "#7a4adf"), "blood": ("#ffc0b0", "#c41414"),
}
# How much the whole shape glows (not its burning parts): steel and shadow do not burn, and a
# dark thing in a fog of its own colour loses its edge (the first wraith).
HALO = {"physical": 0.10, "shadow": 0.06, "blood": 0.16}


# ------------------------------------------------------------------ shapes --
# Signed distances in units, positive inside.

def grid():
    xx, yy = F.grid(N, N)
    return xx / K, yy / K


X0, Y0 = grid()   # the square's own units
X, Y = X0, Y0     # the design's units (see frame)
Z, CX, CY = 1.0, 50.0, 50.0


def frame(zoom=1.0, cx=50.0, cy=50.0):
    """Show the design `zoom` times its size with its point (cx, cy) at the middle: a design
    drawn too big for the glow's circle is fitted without redrawing it."""
    global X, Y, Z, CX, CY
    Z, CX, CY = zoom, cx, cy
    X = cx + (X0 - 50) / zoom
    Y = cy + (Y0 - 50) / zoom


def circle(cx, cy, r):
    return r - np.hypot(X - cx, Y - cy)


def ellipse(cx, cy, rx, ry, rot=0.0):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    u = ((X - cx) * c + (Y - cy) * s) / rx
    v = (-(X - cx) * s + (Y - cy) * c) / ry
    return (1 - np.hypot(u, v)) * min(rx, ry)


def poly(pts):
    return F.sd_poly(X, Y, [(x, y) for x, y in pts])


def union(*ds):
    return np.maximum.reduce(ds)


def soft_union(ds, k=4.0):
    """A billowing union (smoke, cloud, cloth): the joins filled in smoothly."""
    out = ds[0]
    for d in ds[1:]:
        out = F.smin(out, d, k)
    return out


def cut(a, b):
    return np.minimum(a, -b)


def inter(a, b):
    return np.minimum(a, b)


def stroke(pts, w0, w1=None, cap=True):
    """A tapering stroke along a polyline: half-width w0/2 at its start to w1/2 at its end."""
    w1 = w0 if w1 is None else w1
    pts = np.asarray(pts, np.float32)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    L = max(cum[-1], 1e-6)
    best = np.full(X.shape, 1e9, np.float32)
    wb = np.full(X.shape, w1, np.float32)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        ex, ey = bx - ax, by - ay
        t = np.clip(((X - ax) * ex + (Y - ay) * ey) / (ex * ex + ey * ey + 1e-9), 0, 1)
        d = np.hypot(X - ax - ex * t, Y - ay - ey * t)
        w = w0 + (w1 - w0) * (cum[i] + seg[i] * t) / L
        c = d < best
        best = np.where(c, d, best)
        wb = np.where(c, w, wb)
    return wb / 2 - best


def swell(pts, w_mid, w_end=0.4):
    """A stroke thick in its middle and fine at both ends (a crescent, a rag, a wisp)."""
    pts = list(pts)
    h = len(pts) // 2
    return union(stroke(pts[:h + 1], w_end, w_mid), stroke(pts[h:], w_mid, w_end))


def bez(p0, p1, p2, p3, n=40):
    return F.bezier(p0, p1, p2, p3, n)


def arc(cx, cy, r, a0, a1, n=48):
    """Points along a circle, angles in degrees, 0 at the top, clockwise."""
    return [(cx + r * math.sin(math.radians(a)), cy - r * math.cos(math.radians(a))) for a in np.linspace(a0, a1, n)]


def ellipse_pts(cx, cy, rx, ry, rot_=0.0, n=96):
    pts = [(cx + rx * math.sin(t), cy - ry * math.cos(t)) for t in np.linspace(0, 2 * math.pi, n)]
    return rot(pts, rot_, cx, cy)


def rot(pts, ang, cx=50, cy=50):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def crack_web(cx, cy, rx, ry, rot_, n=7, seed=3, rings=(0.38, 0.7)):
    """Glass broken from a point: cracks running out to the rim, and broken rings between
    them. Returns polylines (design units)."""
    rng = np.random.default_rng(seed)
    c, s_ = math.cos(math.radians(rot_)), math.sin(math.radians(rot_))
    angs = np.sort(np.linspace(0, 2 * math.pi, n, endpoint=False) + rng.uniform(-0.3, 0.3, n) + rng.uniform(0, 1))
    radials = []
    for a in angs:
        ca, sa = math.cos(a), math.sin(a)
        R = 1 / math.sqrt((ca / rx) ** 2 + (sa / ry) ** 2)
        pts = []
        for f in np.linspace(0.06, 1.02, 7):
            j = a + rng.uniform(-0.1, 0.1) * (f > 0.1)
            lx, ly = R * f * math.cos(j), R * f * math.sin(j)
            pts.append((cx + lx * c - ly * s_, cy + lx * s_ + ly * c))
        radials.append(pts)
    lines = list(radials)
    for f in rings:
        k = int(f * 6)
        for i in range(len(radials)):
            if rng.random() < 0.7:
                a, b = radials[i][k], radials[(i + 1) % len(radials)][k]
                mid = ((a[0] + b[0]) / 2 + rng.uniform(-1, 1), (a[1] + b[1]) / 2 + rng.uniform(-1, 1))
                lines.append([a, mid, b])
    return lines


def resample(pts, step):
    """Points every `step` units along a polyline."""
    pts = np.asarray(pts, np.float32)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    s = np.arange(0, cum[-1], step)
    return np.stack([np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])], 1)


def cov(sd):
    return np.clip(sd * K * Z + 0.5, 0, 1).astype(np.float32)


def _at(sd, xr, yr):
    """A field sampled at other coordinates (to rotate or move a shape made at its place)."""
    mx = ((50 + (xr - CX) * Z) * K).astype(np.float32)
    my = ((50 + (yr - CY) * Z) * K).astype(np.float32)
    return cv2.remap(sd.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=-50)


def rotated(sd, ang, cx=50, cy=50):
    c_, s_ = math.cos(math.radians(-ang)), math.sin(math.radians(-ang))
    xr = cx + (X - cx) * c_ - (Y - cy) * s_
    yr = cy + (X - cx) * s_ + (Y - cy) * c_
    return _at(sd, xr, yr)


def heart_shape(cx, cy, s):
    t = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    x = 16 * np.sin(t) ** 3
    y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    y = y - (y.max() + y.min()) / 2
    return poly([(cx + a * s / 16, cy + b * s / 16) for a, b in zip(x, y)])


def flame_tongue(x, y, w, h, lean=0.0):
    """A flame standing on (x, y): w wide at its foot, h tall, its tip leaning by `lean`."""
    return poly([(x - w / 2, y), (x - w * 0.55, y - h * 0.35), (x - w * 0.2 + lean * 0.4, y - h * 0.7), (x + lean, y - h),
                 (x + w * 0.15 + lean * 0.5, y - h * 0.6), (x + w * 0.55, y - h * 0.3), (x + w / 2, y)])


def star(cx, cy, r0, r1, n, ang=0.0):
    pts = []
    for k in range(2 * n):
        r = r0 if k % 2 == 0 else r1
        a = math.radians(ang + k * 180 / n)
        pts.append((cx + r * math.sin(a), cy - r * math.cos(a)))
    return poly(pts)


def rock(cx, cy, s, seed, n=7):
    rng = np.random.default_rng(seed)
    return poly([(cx + s * math.cos(t) * (0.7 + 0.45 * rng.random()), cy + s * math.sin(t) * (0.7 + 0.45 * rng.random()))
                 for t in np.linspace(0, 2 * math.pi, n + 1)[:-1] + rng.random()])


def mat(hexs, metal=0.0, rough=0.6):
    return F.Mat(tuple(F.hexc(hexs)), metal, rough)


# --------------------------------------------------------------- the forge --

_GRAIN = {}


def grain_field(kind):
    """The surface's grain in [-1, 1]: `rough` (stone, cloth, bone), `hammer` (planished
    metal), `fine` (leather, clay)."""
    if kind not in _GRAIN:
        if kind == "hammer":
            g = F.facets(N, N, cell=34, tilt=0.5, seed=7)
            g = g / (np.abs(g).max() + 1e-6)
        elif kind == "cloud":
            g = F.fbm(N, N, scale=110, octaves=4, gain=0.6, seed=13)
        elif kind == "fine":
            g = F.fbm(N, N, scale=10, octaves=3, seed=11)
        else:
            g = F.fbm(N, N, scale=36, octaves=5, seed=5)
        _GRAIN[kind] = g.astype(np.float32)
    return _GRAIN[kind]


class Emblem:
    """Layers laid in order: each a shape, a material and a profile. Light (emission) can be
    laid on any of them, and a glow round the whole."""

    def __init__(self, school, zoom=1.0, at=(50, 50)):
        frame(zoom, *at)
        self.school = school
        self.s = F.Surface(N, N)
        self.light = np.zeros((N, N), np.float32)   # how hot each pixel burns (0..)
        self.glow = 1.0

    def lay(self, sd, mat_, height=3.0, bevel=2.0, round_=True, tint=None, light=0.0, z=None, grain=0.0, kind="rough",
            hue=None, soft=0.0):
        """`height` and `bevel` in units; the part's top at its height, its edge rounded over
        `bevel`; laid over what is there (z: the base it rises from, default what is under).
        `grain` (units) roughens its face with the surface's grain of `kind`. `soft` (units)
        feathers its edge (smoke, mist): it fades out over that width instead of ending."""
        c = cov(sd) if not soft else np.clip(sd / soft, 0, 1).astype(np.float32)
        t = np.clip(sd / bevel, 0, 1)
        prof = np.sqrt(1 - (1 - t) ** 2) if round_ else t
        base = self.s.height if z is None else np.full_like(self.s.height, z * K * Z)
        h = base + prof * height * K * Z
        if grain:
            h = h + grain_field(kind) * grain * K * Z * prof
        self.s.height = np.where(c > (0.02 if soft else 0.5), np.maximum(self.s.height if z is None else h * 0, h), self.s.height)
        if isinstance(mat_, str) and mat_.startswith("glow"):
            core, edge = (hue, hue) if hue else SCHOOL[self.school]
            # A burning thing: white-hot inside, its colour at its edge.
            k = np.clip(sd / (bevel * 2.5), 0, 1)
            col = F.hexc(edge) * (1 - k[..., None]) + F.hexc(core) * k[..., None]
            self.s.paint(c, F.Mat((0.02, 0.02, 0.02), 0.0, 0.6))
            self.s.emit = self.s.emit * (1 - c[..., None]) + col * c[..., None] * (light or 1.6)
            self.light = np.maximum(self.light, c * (light or 1.6))
        else:
            m = F.MATS[mat_] if isinstance(mat_, str) else mat_
            if tint is not None:
                m = F.Mat(tuple(np.asarray(m.albedo) * np.asarray(tint)), m.metal, m.rough)
            self.s.paint(c, m)
            if light:
                core, edge = SCHOOL[self.school]
                self.s.emit = self.s.emit * (1 - c[..., None]) + F.hexc(edge) * c[..., None] * light
                self.light = np.maximum(self.light, c * light)
        self.s.alpha = np.maximum(self.s.alpha, c)
        return c

    def rope(self, pts, w, mat_="gold", height=2.0, z=None, light=0.0):
        """The binders' twisted wire along a path: beads leaning across it, each catching the light."""
        P = resample(pts, w * 0.62)
        # One union of all the beads, each worked out only round itself (a full-canvas field per
        # bead made a frame's wire take minutes); a round profile of the union is each bead's own.
        sd = np.full(X.shape, -50.0, np.float32)
        rad = w + 1.0
        for i in range(len(P)):
            a, b = P[max(i - 1, 0)], P[min(i + 1, len(P) - 1)]
            ang = math.radians(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) + 55)
            px = 50 + (P[i][0] - CX) * Z
            py = 50 + (P[i][1] - CY) * Z
            x0, x1 = max(int((px - rad * Z) * K), 0), min(int((px + rad * Z) * K) + 2, N)
            y0, y1 = max(int((py - rad * Z) * K), 0), min(int((py + rad * Z) * K) + 2, N)
            if x0 >= x1 or y0 >= y1:
                continue
            xs, ys = X[y0:y1, x0:x1] - P[i][0], Y[y0:y1, x0:x1] - P[i][1]
            c, s = math.cos(ang), math.sin(ang)
            u = (xs * c + ys * s) / (w * 0.62)
            v = (-xs * s + ys * c) / (w * 0.36)
            sd[y0:y1, x0:x1] = np.maximum(sd[y0:y1, x0:x1], (1 - np.hypot(u, v)) * w * 0.36)
        self.lay(sd, mat_, height, w * 0.34, z=z, light=light)

    def guide(self):
        """The lit emblem on black with its school's glow round it (linear -> sRGB, float)."""
        lin = self.s.shade(normal_strength=1.0, ao=0.5, shadow=0.45)
        core, edge = SCHOOL[self.school]
        a = self.s.alpha
        # Rim of the school's light on the emblem's edges (as if it stood in its own glow).
        er = cv2.GaussianBlur(a, (0, 0), 6)
        rim = np.clip(a - er, 0, 1) * 1.4
        lin = lin + rim[..., None] * F.hexc(edge) * 0.5
        # The glow: from the burning parts strongly, from the whole shape softly.
        g = cv2.GaussianBlur(self.light, (0, 0), 28) * 1.2 + cv2.GaussianBlur(self.light, (0, 0), 90) * 0.9
        halo = cv2.GaussianBlur(a, (0, 0), 60) * HALO.get(self.school, 0.3) * self.glow
        # What burns spills a little light on the thing itself; the halo stays outside it, so
        # the thing keeps its own colours and its edge (the first lamp and mirror drowned).
        a3 = a[..., None]
        out = lin * a3 + g[..., None] * F.hexc(edge) * (1 - a3 * 0.75) + halo[..., None] * F.hexc(edge) * (1 - a3)
        # Fade to black before the edges, the silhouette with it (so nothing is cut square).
        r = np.hypot(X0 - 50, Y0 - 50) / 50
        fade = np.clip((1.0 - r) / 0.08, 0, 1)
        out = out * fade[..., None]
        x = np.clip(out, 0, None)
        y = np.where(x < 0.8, x, 0.8 + 0.2 * (1 - np.exp(-(x - 0.8) / 0.2)))
        return F.lin_to_srgb(np.clip(y, 0, 1)).astype(np.float32), a * fade


# ----------------------------------------------------------------- designs --

def d_mirror():
    """Mirror Step: a hand mirror of the binders' gold, its dark glass broken from one blow
    and a piece of it flying loose (a reflection bursts when it breaks)."""
    e = Emblem("arcane", 0.9, (50, 50))
    a = -24

    def R(pts):
        return rot(pts, a, 46, 40)

    glass = ellipse(46, 40, 21, 27, a)
    frame = cut(ellipse(46, 40, 27, 33, a), ellipse(46, 40, 21.5, 27.5, a))
    e.lay(stroke(R([(46, 72), (46, 95)]), 9.5, 7.5), "leather", 4, 3.5, grain=0.5, kind="fine")
    for y in (79, 85, 91):
        e.rope(R([(41.5, y), (51, y)]), 2.0, "gold_dim", 4.6)
    e.lay(circle(*R([(46, 97)])[0], 5.2), "gold_dim", 5, 3, grain=0.4, kind="hammer")
    e.lay(stroke(R([(46, 70), (46, 75)]), 14), "gold_dim", 5, 2, grain=0.4, kind="hammer")
    # Dark glass with the other side's light deep in it; the cracks let it out.
    e.lay(glass, mat("#140a20", 0.0, 0.04), 2, 8, light=0.1)
    e.lay(ellipse(*R([(36, 24)])[0], 4, 9, a - 20), mat("#d8c8ff", 0.0, 0.1), 0.5, 1, z=2, light=0.25)
    hit = R([(52, 48)])[0]
    for i, line in enumerate(crack_web(hit[0], hit[1], 21, 27, a, n=8, seed=4)):
        w = 1.8 if i < 8 else 1.0
        e.lay(inter(stroke(line, w, w * 0.45), glass), "glow", 0.5, 0.6, light=2.0 if i < 8 else 1.4, z=2)
    e.lay(circle(hit[0], hit[1], 2.2), "glow", 0.5, 1, light=2.6, z=2)
    hole = poly([(hit[0] + 1, hit[1] + 2), (hit[0] + 9, hit[1] + 3), (hit[0] + 6, hit[1] + 10)])
    e.lay(hole, mat("#030105", 0.0, 0.9), 0.3, 0.5, z=0.5)
    e.lay(frame, "gold", 5, 2.5, grain=0.35, kind="hammer")
    e.rope(ellipse_pts(46, 40, 24.2, 30.2, a, 160), 2.1, "gold", 6.2)
    for t in (45, 135, 225, 315):
        p = R([(46 + 24 * math.sin(math.radians(t)), 40 - 30 * math.cos(math.radians(t)))])[0]
        e.lay(circle(p[0], p[1], 2.8), "gold", 8, 2)
    shard = poly([(76, 70), (88, 64), (84, 80)])
    e.lay(shard, mat("#2a1440", 0.0, 0.05), 2, 2, round_=False, light=0.3)
    e.lay(stroke([(77, 70), (87, 65)], 1.2), "glow", 0.5, 0.5, light=1.8, z=2)
    for x, y, r in ((70, 64, 1.1), (92, 74, 0.9), (80, 86, 0.8)):
        e.lay(circle(x, y, r), "glow", 0.5, 0.5, light=1.6)
    return e


def d_wraith():
    """Wraith Walk: an empty hood and its shroud, the hem torn to rags that stream aside
    and thin into the barrow's light, two points of light where a face should be."""
    e = Emblem("shadow", 0.95, (50, 51))
    cloth = mat("#201a2c", 0.0, 0.7)
    body = poly([(50, 6), (60, 12), (67, 24), (70, 38), (76, 48), (84, 60), (82, 70), (90, 80), (78, 80), (80, 92), (68, 84),
                 (62, 96), (56, 84), (46, 94), (42, 82), (32, 90), (32, 78), (20, 84), (24, 70), (16, 62), (24, 48), (30, 38),
                 (33, 24), (40, 12)])
    e.lay(body, cloth, 6, 9, grain=0.7, kind="cloud")
    # Folds falling from the shoulders into the rags.
    for pts in ([(36, 50), (32, 66), (28, 80)], [(44, 60), (42, 74), (40, 86)], [(56, 62), (58, 76), (60, 88)],
                [(64, 50), (70, 64), (76, 76)]):
        e.lay(stroke(pts, 3.2, 0.6), mat("#0a080e", 0.0, 0.8), 0.3, 1.6, z=5.6)
        e.lay(stroke([(x + 2.2, y) for x, y in pts], 2.0, 0.4), mat("#3c3252", 0.0, 0.6), 6.6, 1.0)
    # The hood's opening, its rolled edge, and the dark inside it.
    e.lay(cut(ellipse(50, 34, 14, 18), ellipse(50, 35.5, 10, 14)), mat("#3c3252", 0.0, 0.6), 8, 2.6, grain=0.3, kind="cloud")
    e.lay(ellipse(50, 35.5, 10, 14), mat("#000000", 0.0, 0.9), 0.5, 1, z=0.5)
    for x in (45.8, 54.2):
        e.lay(ellipse(x, 33, 2.0, 1.2, -10 if x < 50 else 10), "glow", 1, 1, light=2.6, z=1)
    # Where the rags end they are not cloth any more but light.
    for x, y, dx, dy in ((90, 80, 1, 0.3), (80, 92, 0.5, 1), (62, 96, 0, 1), (46, 94, -0.2, 1), (32, 90, -0.5, 1),
                         (20, 84, -1, 0.6), (16, 62, -1, 0)):
        e.lay(stroke([(x - dx * 7, y - dy * 7), (x + dx * 3, y + dy * 3)], 1.8, 0.2), "glow", 0.5, 0.6, light=0.9)
    return e


def d_leap():
    """Crashing Leap: the leap's arc coming down hard, the ground split open where it lands,
    slabs of it thrust up and lit from the break, stones thrown."""
    e = Emblem("physical", 0.94, (50, 50))
    e.glow = 0.5
    gx, gy = 56, 74
    stone = mat("#9a8a70", 0.0, 0.75)
    e.lay(ellipse(gx - 2, gy + 4, 42, 12), mat("#3a3228", 0.0, 0.9), 2, 3, grain=1.0)
    e.lay(ellipse(gx, gy + 1, 22, 6.5), "glow", 1, 3, light=2.6, hue="#ffc070")
    for ang in range(-80, 81, 20):
        a = math.radians(ang)
        e.lay(stroke([(gx + 6 * math.sin(a), gy - 2), (gx + 22 * math.sin(a), gy - 16 * math.cos(a) - 2)], 2.6, 0.3), "glow", 1, 1,
              light=1.6, hue="#ffd890")
    for ang in (-100, -60, -25, 15, 50, 85, 120, 160, -150):
        a = math.radians(ang)
        pts = [(gx + 8 * math.sin(a), gy + 1 + 2.4 * math.cos(a)), (gx + 22 * math.sin(a), gy + 1 + 6.5 * math.cos(a) + 1),
               (gx + 38 * math.sin(a), gy + 1 + 11 * math.cos(a))]
        e.lay(stroke(pts, 2.0, 0.4), "glow", 0.5, 0.6, light=1.2, z=2.5, hue="#ff9a40")
    # The slabs: the ground's own plates, broken and stood up on end round the break.
    # Each slab: a broken plate heaved up and tipped out from the break, no two alike.
    for j, (dx, dy, h, w, tip) in enumerate(((-22, 3, 14, 16, -38), (-8, -2, 22, 12, -14), (12, -1, 18, 14, 22),
                                             (27, 4, 12, 15, 48))):
        bx, by = gx + dx, gy + dy
        c_, s_ = math.cos(math.radians(tip)), math.sin(math.radians(tip))
        rng = np.random.default_rng(j + 5)
        local = [(-w / 2, 0), (-w / 2 + rng.uniform(-2, 1), -h * 0.6), (-w * 0.15 + rng.uniform(-2, 2), -h),
                 (w * 0.25 + rng.uniform(-2, 2), -h * rng.uniform(0.75, 0.95)), (w / 2, -h * rng.uniform(0.3, 0.6)), (w / 2, 0)]
        pts = [(bx + x * c_ - y * s_, by + x * s_ + y * c_) for x, y in local]
        e.lay(poly(pts), stone, 5, 2.2, round_=False, grain=1.0)
        e.lay(stroke(pts[1:4], 1.4, 0.8), mat("#e0d0b0", 0.0, 0.6), 5.4, 0.6)
    for j, (dx, dy, sz) in enumerate(((-34, -18, 3.4), (-20, -32, 2.8), (32, -24, 3.6), (18, -36, 2.4), (40, -10, 2.6),
                                      (-6, -40, 2.0), (6, -30, 1.8))):
        e.lay(rock(gx + dx, gy + dy, sz, 30 + j), stone, 3, 1.5, grain=0.6)
    # The leap: an arc of rushing air from the take-off to the blow.
    path = bez((8, 66), (10, 14), (44, 0), (gx - 2, gy - 16), 60)
    e.lay(stroke(path, 0.6, 8.0), "glow", 1, 3, light=1.0)
    P = np.asarray(path, np.float32)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Nn = np.stack([-T[:, 1], T[:, 0]], 1)
    for off in (-6, 6):
        side = P[8:-6] + Nn[8:-6] * off * np.linspace(0.3, 1, len(P) - 14)[:, None]
        e.lay(stroke(side.tolist(), 0.4, 2.2), "glow", 0.5, 1, light=0.55)
    return e


def d_leap2():
    """Crashing Leap, second concept (the first was a grey arc on a dark disc at 90 px): the
    blow itself. A bold hard-edged arc of rushing air comes down steep from the upper left
    into the ground; where it lands the ground breaks, its cracks running out lit gold from a
    small white-hot burst, and a crown of near-black slabs stands up round the break, black
    against the light. Value first: no halo and no fan of rays (they fogged the first guide
    into cream); the dark is kept dark so the light reads as light."""
    e = Emblem("physical", 0.96, (50, 52))
    e.glow = 0.0
    gx, gy = 58, 76
    ground = mat("#1c1714", 0.0, 0.9)
    slab = mat("#17120f", 0.0, 0.85)
    rim = mat("#ffcf80", 0.0, 0.5)
    e.lay(ellipse(gx - 4, gy + 6, 44, 11), ground, 2, 3, grain=1.0)
    # The broken ground: cracks running out from the blow, lit from inside.
    for i, line in enumerate(crack_web(gx, gy + 3, 36, 8.5, 0, n=9, seed=21, rings=(0.45,))):
        w = 1.5 if i < 9 else 0.9
        e.lay(stroke(line, w, w * 0.4), "glow", 0.4, 0.5, light=1.3 if i < 9 else 0.9, hue="#ffb24a", z=2.2)
    # The burst: small and white-hot at the root, a few short hard spikes.
    e.lay(ellipse(gx, gy, 9, 3.4), "glow", 1, 2, light=2.6, hue="#fff4d8")
    for ang in (-52, -24, 0, 22, 48):
        a = math.radians(ang)
        L = 13 - abs(ang) * 0.06
        e.lay(stroke([(gx + 2 * math.sin(a), gy - 1), (gx + L * math.sin(a), gy - 1 - L * math.cos(a))], 2.4, 0.2),
              "glow", 1, 1.2, light=2.0, hue="#ffe2a0")
    # The crown of slabs, near-black against the light, each lit only at its rim.
    for j, (dx, dy, h, w, tip) in enumerate(((-24, 4, 15, 13, -40), (-12, 0, 24, 12, -18), (2, -2, 28, 11, -4),
                                             (15, 0, 22, 12, 16), (27, 4, 14, 13, 42))):
        bx, by = gx + dx, gy + dy
        c_, s_ = math.cos(math.radians(tip)), math.sin(math.radians(tip))
        rng = np.random.default_rng(j + 11)
        local = [(-w / 2, 0), (-w / 2 + rng.uniform(-1.5, 1), -h * 0.62), (-w * 0.1 + rng.uniform(-2, 2), -h),
                 (w * 0.3 + rng.uniform(-1.5, 1.5), -h * rng.uniform(0.78, 0.94)), (w / 2, -h * rng.uniform(0.35, 0.55)), (w / 2, 0)]
        pts = [(bx + x * c_ - y * s_, by + x * s_ + y * c_) for x, y in local]
        e.lay(poly(pts), slab, 6, 2.0, round_=False, grain=1.2)
        e.lay(stroke(pts[1:5], 0.9, 0.5), rim, 6.4, 0.5, light=0.5)
    for j, (dx, dy, sz) in enumerate(((-30, -22, 3.2), (-18, -34, 2.6), (30, -26, 3.4), (20, -38, 2.2), (38, -12, 2.4))):
        e.lay(rock(gx + dx, gy + dy, sz, 40 + j), slab, 3, 1.4, grain=0.6)
    # The leap: a crescent of rushing air, thin where it left the ground, full and hard-edged
    # where it comes down; two speed lines beside it.
    path = bez((10, 70), (6, 18), (40, 2), (gx - 3, gy - 12), 72)
    e.lay(stroke(path, 0.8, 11.0), mat("#e8e0d4", 0.0, 0.35), 4, 2.4, light=0.15)
    e.lay(stroke(path[20:], 0.6, 4.0), "glow", 0.5, 1.5, light=1.4, z=4.2, hue="#fff4e0")
    P = np.asarray(path, np.float32)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Nn = np.stack([-T[:, 1], T[:, 0]], 1)
    for off, w in ((-9.5, 2.0), (-14.5, 1.3)):
        side = P[22:-10] + Nn[22:-10] * off * np.linspace(0.4, 1, len(P) - 32)[:, None]
        e.lay(stroke(side.tolist(), 0.3, w), mat("#d8d0c4", 0.0, 0.4), 3, 1, light=0.3)
    return e


def d_blink():
    """Blink: a rift torn in the air, rimed at its edges, ice shards bursting from it."""
    e = Emblem("frost", 0.95, (50, 52))
    for ang, L, w in ((-60, 34, 7), (-28, 30, 6), (28, 31, 6), (62, 34, 7), (-100, 26, 5), (100, 27, 5), (180, 18, 5),
                      (150, 22, 4.5), (-150, 22, 4.5)):
        a = math.radians(ang)
        ux, uy = math.sin(a), -math.cos(a)
        p0 = (50 + ux * 12, 52 + uy * 18)
        p1 = (50 + ux * (12 + L), 52 + uy * (18 + L))
        n = (-uy, ux)
        shard = poly([p1, (p0[0] + n[0] * w / 2, p0[1] + n[1] * w / 2), (p0[0] - n[0] * w / 2, p0[1] - n[1] * w / 2)])
        e.lay(shard, mat("#c8e8ff", 0.0, 0.08), 3, 2, round_=False, grain=0.3)
        e.lay(stroke([p0, p1], 0.8, 0.2), mat("#ffffff", 0.0, 0.05), 3.4, 0.4, light=0.4)
    rift = poly([(50, 8), (55, 22), (52, 30), (59, 44), (55, 54), (60, 70), (52, 82), (50, 96), (47, 82), (41, 70),
                 (46, 56), (40, 44), (47, 32), (44, 20)])
    e.lay(cut(rift, poly([(50, 18), (52, 30), (56, 44), (52, 56), (56, 70), (50, 86), (45, 70), (49, 56), (44, 44), (49, 30)])),
          mat("#e0f4ff", 0.0, 0.06), 4, 1.5, light=0.5)
    e.lay(rift, "glow", 2, 4, light=2.0)
    return e


def d_smoke():
    """Smoke Bomb: a clay smoke-pot of the Dig, burst open, its smoke boiling up and out."""
    e = Emblem("shadow", 0.92, (50, 48))
    puffs = [(50, 56, 8), (43, 47, 10), (57, 41, 11), (45, 30, 12), (61, 24, 10), (34, 21, 9), (52, 13, 9), (71, 15, 6.5),
             (29, 35, 7), (68, 34, 7.5), (38, 10, 5), (78, 26, 4.5)]
    cloud = soft_union([circle(x, y, r) for x, y, r in puffs], 7)
    e.lay(cloud, mat("#a49cb4", 0.0, 0.95), 4, 18, grain=3.0, kind="cloud", soft=3.0)
    # Light on the crowns of the billows, from the upper left; the pot's light in their feet.
    for x, y, r in puffs:
        e.lay(circle(x - r * 0.3, y - r * 0.35, r * 0.6), mat("#d0c8e0", 0.0, 0.95), 0.8, r * 0.6, soft=r * 0.5)
    e.lay(soft_union([circle(50, 56, 8), circle(43, 47, 7)], 4), mat("#b08ad8", 0.0, 0.9), 0.5, 6, soft=5, light=0.5)
    pot = circle(50, 76, 16)
    e.lay(pot, mat("#5a3424", 0.0, 0.6), 8, 10, grain=0.6, kind="fine")
    lip = poly([(37, 66), (40, 59), (44, 63), (48, 57), (53, 62), (58, 57), (62, 62), (64, 66), (60, 68), (40, 68)])
    e.lay(lip, mat("#7a4a32", 0.0, 0.6), 8.5, 1.5, grain=0.4, kind="fine")
    e.lay(ellipse(50, 64.5, 10, 2.4), "glow", 1, 1, light=1.8, z=8)
    e.lay(stroke([(35, 75), (65, 75)], 2.4), mat("#2a1810", 0.0, 0.7), 1, 1, z=7.6)
    for crk in ([(42, 82), (46, 76), (44, 72), (50, 68)], [(58, 88), (60, 80), (64, 77)]):
        e.lay(stroke(crk, 1.8, 0.8), "glow", 0.5, 0.6, light=1.3, z=8)
    return e


def d_echo():
    """Echo Step: a step that comes back: a trail of light going round to the mark it left,
    the mark a binders' coin, and the trail's own fainter echoes."""
    e = Emblem("arcane", 0.9, (50, 52))
    cx, cy, r = 50, 52, 33
    for k, (rr, li) in enumerate(((r + 7, 0.35), (r + 13, 0.2))):
        e.lay(stroke(arc(cx, cy, rr, 235, 470, 80), 0.6, 2.4 - k * 0.6), "glow", 0.5, 1, light=li)
    path = arc(cx, cy, r, 225, 500, 120)
    e.lay(stroke(path, 1.0, 7.5), "glow", 1, 2.5, light=1.6)
    th = math.radians(500)
    px, py = cx + r * math.sin(th), cy - r * math.cos(th)
    dx, dy = math.cos(th), math.sin(th)
    nx, ny = math.sin(th), -math.cos(th)
    head = poly([(px + dx * 13, py + dy * 13), (px + nx * 9, py + ny * 9), (px - nx * 9, py - ny * 9)])
    e.lay(head, "glow", 1, 2, light=1.9)
    # The mark: the binders' square-holed coin, standing where the step began.
    th0 = math.radians(205)
    mx, my = cx + r * math.sin(th0), cy - r * math.cos(th0)
    e.lay(circle(mx, my, 12), "gold", 5, 2.5, grain=0.5, kind="hammer")
    e.rope(arc(mx, my, 10, 0, 360, 80), 1.8, "gold_dim", 6)
    e.lay(poly([(mx - 4, my - 4), (mx + 4, my - 4), (mx + 4, my + 4), (mx - 4, my + 4)]), "glow", 1, 1.5, light=2.2, z=3)
    return e


def d_feint():
    """Fen Step: the thrust that meets nothing: a blade standing point up, and the way the body
    went round it, over its point and down the far side, in a streak of fen-mist."""
    e = Emblem("physical", 0.92, (50, 50))
    path = bez((18, 78), (8, 20), (82, 0), (82, 62), 60)
    e.lay(stroke(path[:-4], 0.6, 7.0), "glow", 1, 2.5, light=1.1)
    P = np.asarray(path, np.float32)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Nn = np.stack([-T[:, 1], T[:, 0]], 1)
    for off, w, li in ((-6.5, 2.4, 0.6), (-12, 1.4, 0.4)):
        side = P[6:-10] + Nn[6:-10] * off * np.linspace(0.2, 1, len(P) - 16)[:, None]
        e.lay(stroke(side.tolist(), 0.3, w), "glow", 0.5, 1, light=li)
    tip, back = P[-1], P[-6]
    d = (tip - back) / np.linalg.norm(tip - back)
    n = np.array([-d[1], d[0]])
    e.lay(poly([tuple(tip + d * 7), tuple(back + n * 8), tuple(back - n * 8)]), "glow", 1, 2, light=1.5)
    e.lay(poly([(50, 22), (54.5, 32), (54, 66), (46, 66), (45.5, 32)]), "steel", 5, 3, grain=0.3, kind="hammer")
    e.lay(stroke([(50, 30), (50, 62)], 1.4), "iron_dark", 5.5, 0.6)
    e.lay(stroke([(36, 68), (64, 68)], 5), "gold_dim", 6, 2.4, grain=0.4, kind="hammer")
    for x in (36, 64):
        e.lay(circle(x, 68, 3.2), "gold_dim", 6.5, 2)
    e.lay(stroke([(50, 70), (50, 84)], 5.6, 5), "leather", 5, 3, grain=0.5, kind="fine")
    e.rope([(50, 71), (50, 83)], 2.0, "gold_dim", 6)
    e.lay(circle(50, 88, 4), "gold_dim", 6, 2.5, grain=0.4, kind="hammer")
    return e


def d_hourglass():
    """Time Slip: an hourglass of the binders, its posts their twisted wire, its sand stopped
    in the air between the bulbs."""
    e = Emblem("arcane")
    glass = poly([(32, 15), (68, 15), (68, 22), (53, 48), (53, 52), (68, 78), (68, 85), (32, 85), (32, 78), (47, 52), (47, 48),
                  (32, 22)])
    e.lay(glass, mat("#2e2042", 0.0, 0.05), 3, 4)
    e.lay(poly([(37, 24), (63, 24), (51, 44), (49, 44)]), "glow", 1, 2, light=1.3, z=3)
    e.lay(poly([(36, 82), (64, 82), (58, 72), (50, 68), (42, 72)]), "glow", 1, 2, light=1.3, z=3)
    for i, y in enumerate((50, 55, 60, 64)):
        e.lay(circle(50, y, 1.3 - i * 0.12), "glow", 1, 0.8, light=2.0, z=3)
    e.lay(stroke([(35, 20), (40, 34)], 1.6, 0.6), mat("#e8d8ff", 0.0, 0.1), 3.6, 0.6, light=0.3)
    for x in (28, 72):
        e.rope([(x, 14), (x, 86)], 4.4, "gold_dim", 5)
    for y in (12, 88):
        e.lay(stroke([(25, y), (75, y)], 7.5), "gold", 6, 3, grain=0.4, kind="hammer")
        for x in (28, 72):
            e.lay(circle(x, y, 3), "gold", 8, 2)
    return e


def d_embers():
    """Cinder Trail: a coal of the Morrow's ember running, cracked molten, the ground burning
    behind it in a trail of smaller coals and flame."""
    e = Emblem("fire", 0.95, (52, 50))
    trail = bez((8, 92), (22, 86), (40, 70), (58, 52), 30)
    e.lay(stroke(trail, 2.0, 12), "glow", 1, 3, light=0.9)
    for (t, s, h) in ((0.25, 3.2, 10), (0.5, 4.2, 15), (0.75, 5.4, 20)):
        x, y = trail[int(t * 29)]
        e.lay(rock(x, y, s, int(t * 40)), mat("#1a0c08", 0.0, 0.7), 3, 2, grain=0.5)
        e.lay(flame_tongue(x, y - s * 0.3, s * 2.2, h, lean=-2), "glow", 1, 2, light=1.5)
    coal = poly([(48, 46), (54, 30), (68, 22), (84, 26), (90, 40), (84, 56), (68, 62), (54, 58)])
    e.lay(coal, mat("#1c0d08", 0.0, 0.65), 7, 5, grain=0.9)
    for crk in ([(56, 34), (64, 40), (62, 50), (70, 56)], [(64, 40), (74, 36), (82, 30)], [(74, 36), (78, 46), (86, 48)],
                [(62, 50), (54, 52)], [(78, 46), (72, 54)]):
        e.lay(stroke(crk, 2.6, 1.2), "glow", 0.5, 0.8, light=2.2, z=6)
    for x, y, r in ((72, 12, 1.2), (86, 14, 0.9), (60, 14, 0.8), (92, 26, 0.8)):
        e.lay(circle(x, y, r), "glow", 0.5, 0.5, light=1.8)
    e.lay(flame_tongue(70, 26, 16, 18, lean=4), "glow", 1, 2, light=1.4)
    return e


def d_aegis():
    """Bulwark: a kite shield of the Order, the dawn rising on its face, a ward of dawn-gold
    round it."""
    e = Emblem("holy")
    e.lay(stroke(arc(50, 50, 43, 0, 360, 128), 2.6), "glow", 1, 1.2, light=0.9)
    kite = poly([(50, 92), (22, 52), (24, 16), (50, 8), (76, 16), (78, 52)])
    e.lay(kite, "steel", 5, 3, grain=0.5, kind="hammer")
    inner = poly([(50, 84), (28, 51), (30, 20), (50, 14), (70, 20), (72, 51)])
    e.lay(cut(kite, inner), "gold", 6.5, 2, grain=0.3, kind="hammer")
    for x, y in ((24, 17), (76, 17), (50, 9), (22, 52), (78, 52), (50, 90)):
        e.lay(circle(x, y, 2.2), "gold", 8, 1.5)
    # The dawn: a half sun on the horizon, its rays.
    e.lay(stroke([(30, 56), (70, 56)], 2.6), "gold", 7, 1.5)
    sun = inter(circle(50, 56, 11), poly([(30, 30), (70, 30), (70, 55), (30, 55)]))
    e.lay(sun, "glow", 2, 3, light=1.8, z=6.5)
    for ang in (-75, -50, -25, 0, 25, 50, 75):
        a = math.radians(ang)
        e.lay(stroke([(50 + 14 * math.sin(a), 56 - 14 * math.cos(a)), (50 + 24 * math.sin(a), 56 - 24 * math.cos(a))], 2.6, 0.6),
              "glow", 1, 1, light=1.4, z=6.5)
    return e


def d_howl():
    """War Cry: a carter's war horn, bound in iron, its call going out in red."""
    e = Emblem("blood", 0.95, (50, 50))
    horn = stroke(bez((22, 78), (26, 40), (52, 22), (70, 30), 40), 6, 24)
    e.lay(horn, "bone", 5, 5, grain=0.7)
    for (a, b) in (((22, 64), (35, 70)), ((31, 44), (43, 53)), ((48, 29), (55, 43))):
        e.lay(stroke([a, b], 3.4), "iron", 7, 1.5, grain=0.3, kind="hammer")
    e.lay(ellipse(70, 30, 6, 12, -28), mat("#050000", 0.0, 0.8), 6, 1)
    for i, r in enumerate((14, 22, 30)):
        e.lay(stroke(arc(70, 30, r, 25, 125), 3.4 - i * 0.6), "glow", 1, 1.2, light=1.6 - i * 0.35)
    e.lay(stroke([(18, 82), (14, 90)], 5, 4), "gold_dim", 5, 2)
    e.rope(bez((20, 80), (8, 70), (10, 50), (24, 46), 30), 2.0, "leather", 4)
    return e


def d_expand():
    """Ford Lamp: a lamp of the Waystation's lamp-iron, its light thrown wide round it."""
    e = Emblem("holy")
    for k in range(16):
        a = k * 22.5
        e.lay(stroke(arc(50, 50, 42, a - 7, a + 7, 10), 2.0, 2.0), "glow", 1, 1, light=0.45)
    e.lay(poly([(37, 34), (63, 34), (62, 70), (38, 70)]), "glow", 2, 6, light=0.8)
    e.lay(flame_tongue(50, 66, 13, 26, lean=1), "glow", 2, 3, light=2.0, z=2)
    for x0, x1 in ((36, 37), (50, 50), (64, 63)):
        e.lay(stroke([(x0, 32), (x1, 72)], 2.6), "iron", 6, 1.2, grain=0.4, kind="hammer")
    e.lay(poly([(32, 34), (68, 34), (60, 22), (40, 22)]), "iron", 6, 2, grain=0.5, kind="hammer")
    e.lay(stroke([(30, 34), (70, 34)], 3.6), "iron_dark", 7, 1.5)
    e.lay(cut(circle(50, 14, 7.5), circle(50, 14, 4.6)), "iron", 6, 1.4, grain=0.4, kind="hammer")
    e.lay(poly([(30, 72), (70, 72), (64, 82), (36, 82)]), "iron", 6, 2, grain=0.5, kind="hammer")
    e.lay(stroke([(28, 72), (72, 72)], 3.6), "iron_dark", 7, 1.5)
    for sx in (-1, 1):
        e.lay(stroke([(50 + sx * 17, 28), (50 + sx * 24, 24), (50 + sx * 27, 19), (50 + sx * 24, 15), (50 + sx * 21, 18)],
                     2.2, 1.2), "iron", 6, 1)
    e.lay(circle(50, 87, 2.4), "gold_dim", 6, 1.5)
    return e


def d_retaura():
    """Morning Light: the Order's dawn burning round you: flames standing all round a ring."""
    e = Emblem("holy", 0.88, (50, 50))
    e.lay(cut(circle(50, 50, 30), circle(50, 50, 23)), "gold", 4, 2, grain=0.4, kind="hammer")
    e.rope(arc(50, 50, 26.5, 0, 360, 160), 2.4, "gold_dim", 5.4)
    for k in range(12):
        sd = flame_tongue(50, 22, 9, 16 + 7 * (k % 2), lean=1.5)
        e.lay(rotated(sd, k * 30), "glow", 1, 2, light=1.5)
    e.lay(cut(circle(50, 50, 21), circle(50, 50, 17)), "glow", 1, 1, light=0.7)
    return e


def d_frostaura():
    """The Ford's Cold: a ring of the Low Ford's rime, ice needles standing out all round."""
    e = Emblem("frost", 0.95, (50, 50))
    e.lay(cut(circle(50, 50, 24), circle(50, 50, 19)), mat("#c8e8ff", 0.0, 0.08), 3, 2, grain=0.4)
    needle = poly([(50, 4), (54, 24), (50, 28), (46, 24)])
    small = poly([(50, 12), (52.5, 25), (50, 27), (47.5, 25)])
    for k in range(16):
        e.lay(rotated(needle if k % 2 == 0 else small, k * 22.5), mat("#d8f0ff", 0.0, 0.05), 3, 2, round_=False, light=0.25)
    e.lay(cut(circle(50, 50, 18), circle(50, 50, 15)), "glow", 1, 1, light=0.9)
    return e


def d_pyre():
    """Pyre Burst: logs crossed and stacked, a tall fire on them."""
    e = Emblem("fire", 0.88, (50, 50))
    for (a, b, w) in (((14, 86), (86, 72), 9), ((16, 72), (84, 86), 9), ((22, 66), (78, 66), 8)):
        e.lay(stroke([a, b], w), "wood", 5, 4, grain=0.8)
        e.lay(circle(b[0], b[1], w / 2 - 0.5), mat("#8a5a34", 0.0, 0.7), 5.5, 2, grain=0.4)
    e.lay(flame_tongue(50, 66, 46, 58, lean=-2), "glow", 2, 6, light=1.6)
    e.lay(flame_tongue(36, 64, 18, 30, lean=-4), "glow", 2, 3, light=1.8)
    e.lay(flame_tongue(64, 64, 20, 34, lean=3), "glow", 2, 3, light=1.8)
    return e


def d_risen():
    """Grave Call: a headstone leaning and split, the barrow's light pouring out of it, and a
    hand of bone reaching up out of the earth before it."""
    e = Emblem("shadow", 0.9, (52, 54))
    e.lay(ellipse(50, 90, 44, 9), mat("#2a2420", 0.0, 0.9), 3, 4, grain=1.0)
    stone = union(poly([(34, 88), (34, 34), (78, 34), (78, 88)]), circle(56, 34, 22))
    left = inter(stone, poly([(0, 0), (58, 0), (52, 30), (60, 46), (50, 64), (56, 100), (0, 100)]))
    right = inter(stone, poly([(100, 0), (60, 0), (54, 30), (62, 46), (52, 64), (58, 100), (100, 100)]))
    e.lay(rotated(left, -4, 34, 88), mat("#56525e", 0.0, 0.7), 6, 3, grain=1.0)
    e.lay(rotated(right, 8, 78, 88), mat("#56525e", 0.0, 0.7), 6, 3, grain=1.0)
    e.lay(stroke([(58, 12), (53, 30), (61, 46), (51, 64), (57, 90)], 4.5, 2.5), "glow", 1, 1.5, light=2.0)
    # The hand: wrist out of the earth, palm, five fingers splayed and hooked.
    bone = "bone"
    e.lay(stroke([(28, 96), (27, 76)], 3.6, 3.0), bone, 5, 1.6, grain=0.3)
    e.lay(stroke([(31, 96), (31, 76)], 2.8, 2.4), bone, 5, 1.4, grain=0.3)
    e.lay(ellipse(29, 70, 6.5, 6), bone, 5.5, 2.5, grain=0.3)
    for (x0, y0), (x1, y1), (x2, y2) in (((24, 68), (17, 60), (16, 52)), ((26, 64), (23, 52), (24, 44)),
                                           ((29, 63), (30, 50), (33, 43)), ((32, 64), (37, 53), (41, 48)),
                                           ((34, 70), (41, 66), (44, 60))):
        e.lay(stroke([(x0, y0), (x1, y1)], 2.4, 2.0), bone, 6, 1.1)
        e.lay(stroke([(x1, y1), (x2, y2)], 2.0, 1.2), bone, 6, 1.0)
        e.lay(circle(x1, y1, 1.4), bone, 6.5, 1.0)
    for x, y in ((20, 92), (38, 94), (34, 88)):
        e.lay(rock(x, y, 2.4, int(x)), mat("#3a322a", 0.0, 0.9), 4, 1.5)
    return e


def d_herd():
    """Spirit Herd: a stag's skull and its great antlers in the Verge's green fire."""
    e = Emblem("nature", 0.82, (50, 48))
    for sx in (-1, 1):
        beam = bez((50 + sx * 8, 38), (50 + sx * 26, 30), (50 + sx * 42, 22), (50 + sx * 44, 2), 30)
        e.lay(stroke(beam, 7, 3.0), "bone", 4, 2.5, grain=0.6)
        for (t, dx, dy) in ((0.1, 6, -12), (0.35, -2, -22), (0.58, 8, -18), (0.8, 10, -10)):
            p = beam[int(t * 29)]
            e.lay(stroke([p, (p[0] + sx * dx * 0.4, p[1] + dy * 0.6), (p[0] + sx * dx, p[1] + dy)], 4.6, 1.2), "bone", 4, 2,
                  grain=0.5)
        e.lay(stroke(beam[:4], 9, 7), "bone", 4.6, 3, grain=0.9)
    skull = poly([(50, 90), (43, 74), (38, 52), (40, 40), (50, 34), (60, 40), (62, 52), (57, 74)])
    e.lay(skull, "bone", 6, 5, grain=0.8)
    for x in (43.5, 56.5):
        e.lay(ellipse(x, 50, 3.6, 4.6), mat("#020402", 0.0, 0.9), 1, 1, z=5)
        e.lay(ellipse(x, 50, 2.2, 3.0), "glow", 1, 1.5, light=2.2, z=5)
    e.lay(stroke([(50, 60), (50, 80)], 1.2), mat("#4a4234", 0.0, 0.8), 6.4, 0.6)
    for x in (47, 53):
        e.lay(ellipse(x, 84, 1.4, 2.6), mat("#0a0806", 0.0, 0.8), 6.2, 0.6)
    e.glow = 1.2
    return e


def d_tether():
    """Grave Tether: a tendril of the barrow's shadow hooked into a heart, what it takes
    running back along it in drops of red."""
    e = Emblem("shadow", 0.92, (54, 52))
    e.lay(heart_shape(62, 58, 26), mat("#7a0c18", 0.0, 0.25), 7, 9, grain=0.5, kind="fine", light=0.35)
    e.lay(stroke(bez((54, 42), (50, 52), (54, 64), (62, 74), 20), 1.4, 0.6), mat("#2a0206", 0.0, 0.4), 7.6, 0.6)
    e.lay(ellipse(55, 47, 2.4, 4, -30), mat("#ff9a9a", 0.0, 0.1), 0.4, 1, z=7.2)
    t1 = bez((10, 14), (34, 6), (24, 46), (50, 54), 40)
    e.lay(stroke(t1, 4.0, 9.0), mat("#1c1428", 0.0, 0.6), 4.5, 3, grain=0.4, light=0.15)
    e.lay(stroke(t1, 1.0, 3.0), "glow", 0.5, 1.2, light=1.4, z=4.5)
    e.lay(poly([(44, 48), (60, 54), (56, 58), (50, 62)]), mat("#1c1428", 0.0, 0.5), 7.8, 1.5, light=0.2)
    t2 = bez((8, 46), (22, 40), (30, 70), (48, 70), 40)
    e.lay(stroke(t2, 1.6, 4.2), mat("#1c1428", 0.0, 0.6), 4, 2, grain=0.4)
    e.lay(stroke(t2, 0.4, 1.6), "glow", 0.5, 1, light=1.1, z=4)
    for i in (8, 18, 28):
        x, y = t1[i]
        e.lay(circle(x, y, 1.7), "glow", 1, 1, light=2.0, z=5, hue="#ff3a2a")
    for i in (12, 26):
        x, y = t2[i]
        e.lay(circle(x, y, 1.2), "glow", 1, 1, light=1.8, z=5, hue="#ff3a2a")
    return e


def d_umbral():
    """Umbral Bolt: a bolt of shadow tearing straight through, barbed in black iron, the dark
    streaming behind it and the air torn round it in rings."""
    e = Emblem("shadow", 0.92, (48, 52))
    o, d, n = np.array([60.0, 40.0]), np.array([1, -1]) / math.sqrt(2), np.array([1, 1]) / math.sqrt(2)

    def P(*uv):
        return [tuple(o + u * d + v * n) for u, v in uv]

    dark = mat("#141020", 0.4, 0.4)
    e.lay(poly(P((-24, 0), (-66, -14), (-56, -3), (-70, 0), (-56, 3), (-66, 14))), mat("#1a1428", 0.0, 0.8), 3, 5, grain=1.2,
          light=0.15)
    for v in (-1, 1):
        e.lay(stroke(P((-26, 4 * v), (-64, 13 * v)), 1.6, 0.3), "glow", 0.5, 0.8, light=0.9)
    e.lay(stroke(P((-28, 0), (-70, 0)), 1.4, 0.3), "glow", 0.5, 0.8, light=0.7)
    for u, r in ((-14, 12), (-30, 9)):
        c = P((u, 0))[0]
        e.lay(cut(ellipse(c[0], c[1], 3.4, r, -45), ellipse(c[0], c[1], 2.0, r - 2.0, -45)), "glow", 0.5, 0.6, light=0.9)
    e.lay(stroke(P((-40, 0), (-4, 0)), 5.6), dark, 5, 2.4, grain=0.4, kind="hammer")
    for v in (-1, 1):
        e.lay(poly(P((-42, 0), (-36, 8 * v), (-26, 8 * v), (-30, 0))), mat("#241a34", 0.0, 0.7), 5.5, 1.5, grain=0.6)
    head = poly(P((30, 0), (2, -13), (7, -4.5), (-6, -4), (-6, 4), (7, 4.5), (2, 13)))
    e.lay(head, mat("#141020", 0.6, 0.3), 7, 4, grain=0.4, kind="hammer", light=0.12)
    for v in (-1, 1):
        e.lay(stroke(P((29, 0), (3, 12 * v)), 2.8, 1.4), "glow", 1, 0.8, light=2.2, z=7)
    e.lay(stroke(P((24, 0), (-2, 0)), 1.8, 0.6), "glow", 1, 0.6, light=1.6, z=7)
    e.lay(stroke(P((-6, 0), (-40, 0)), 1.6, 0.4), "glow", 1, 0.6, light=1.2, z=5)
    return e


def d_consecrate():
    """Consecration: the Legion's seal burned gold into the stone, seven notches round it,
    the light rising from it."""
    e = Emblem("holy", 0.95, (50, 54))
    e.lay(ellipse(50, 60, 46, 26), mat("#3a342c", 0.0, 0.9), 2, 3, grain=1.2)
    for k in range(6):
        a = k * 60 + 20
        e.lay(stroke([(50, 60), (50 + 46 * math.sin(math.radians(a)), 60 - 26 * math.cos(math.radians(a)))], 0.8),
              mat("#151210", 0.0, 0.9), 0.5, 0.4, z=1.8)
    ring = cut(ellipse(50, 60, 40, 22), ellipse(50, 60, 32, 16.5))
    e.lay(ring, "glow", 1, 2, light=1.5, z=2)
    for k in range(7):
        a = math.radians(k * 360 / 7)
        x, y = 50 + 36 * math.sin(a), 60 - 19.2 * math.cos(a)
        e.lay(ellipse(x, y, 3.2, 2.4), mat("#080604", 0.0, 0.8), 1.2, 0.5, z=2.5)
    e.lay(ellipse(50, 60, 11, 6), "glow", 1, 2, light=1.3, z=2)
    for x, h in ((50, 54), (38, 34), (62, 36), (26, 20), (74, 22)):
        e.lay(stroke([(x, 58), (x, 58 - h)], 3.2, 0.4), "glow", 1, 1, light=1.0)
    return e


def d_drain():
    """Bloodthirst: a thread of red life poured into an iron goblet."""
    e = Emblem("blood", 0.85, (56, 48))
    cup = union(poly([(30, 30), (70, 30), (64, 50), (54, 58), (46, 58), (36, 50)]), stroke([(50, 58), (50, 80)], 6),
                ellipse(50, 84, 16, 5))
    e.lay(cup, "iron", 5, 4, grain=0.6, kind="hammer")
    e.rope([(31, 40), (69, 40)], 2.2, "gold_dim", 6.6)
    e.rope([(44, 68), (56, 68)], 2.2, "gold_dim", 6.6)
    e.lay(cut(ellipse(50, 31, 20, 4.5), ellipse(50, 31, 18, 3.2)), "gold", 6, 1.5)
    e.lay(ellipse(50, 31.5, 17.5, 3), "glow", 1, 1, light=1.4, z=4)
    stream = bez((90, 8), (74, 6), (58, 12), (52, 30), 30)
    e.lay(stroke(stream, 2.4, 5.4), "glow", 1, 2, light=1.8)
    for x, y, r in ((84, 22, 1.8), (72, 26, 1.4), (63, 22, 1.1)):
        e.lay(circle(x, y, r), "glow", 1, 1, light=1.5)
    return e


def d_static():
    """Static Charge: a conduit of the binders' twisted iron, the charge crawling up it and
    leaping from its tip."""
    e = Emblem("storm", 0.9, (50, 50))
    foot = poly([(36, 94), (64, 94), (58, 86), (42, 86)])
    e.lay(foot, "iron", 5, 2, grain=0.5, kind="hammer")
    e.rope([(50, 88), (50, 24)], 6.0, "iron", 6)
    e.lay(circle(50, 18, 5.5), "gold", 7, 3, grain=0.3, kind="hammer")
    # The charge: a bolt wound round the rod, and the spark off its tip.
    t = np.linspace(0, 3.2 * math.pi, 22)
    coil = [(50 + 9 * math.sin(v) + (2.5 if i % 2 else -2.5), 84 - v / (3.2 * math.pi) * 60) for i, v in enumerate(t)]
    e.lay(stroke(coil, 2.0, 3.0), "glow", 1, 1.2, light=1.6, z=6)
    for pts in ([(54, 14), (64, 10), (62, 6), (76, 2)], [(46, 14), (34, 8), (38, 4), (26, 0)], [(55, 20), (68, 22), (66, 16), (82, 18)],
                [(45, 21), (32, 24), (34, 18), (18, 22)]):
        e.lay(stroke(pts, 2.6, 0.6), "glow", 1, 1, light=1.8)
    e.lay(circle(50, 17, 3), "glow", 1, 1.5, light=2.6, z=7)
    return e


def d_book():
    """Wayfinder's Chart: a chart half unrolled, the way across it in light, a compass star."""
    e = Emblem("arcane", 0.95, (51, 51))
    sheet = poly([(20, 26), (80, 22), (82, 78), (22, 82)])
    e.lay(sheet, F.MATS["parchment"], 2, 2, grain=0.6, kind="fine", tint=(0.62, 0.56, 0.48))
    # Rolled at the head and the foot.
    e.lay(stroke([(16, 24), (84, 19)], 10), F.MATS["parchment"], 5, 5, grain=0.4, kind="fine", tint=(0.55, 0.48, 0.4))
    e.lay(stroke([(18, 84), (86, 79)], 10), F.MATS["parchment"], 5, 5, grain=0.4, kind="fine", tint=(0.55, 0.48, 0.4))
    for x, y in ((14, 24), (86, 19), (16, 84), (88, 79)):
        e.lay(circle(x, y, 3.6), "wood", 6, 2)
    # The country drawn on it, faint: a river and hills.
    e.lay(stroke(bez((26, 60), (40, 50), (48, 70), (78, 58), 30), 1.4), mat("#3a2a1c", 0.0, 0.9), 0.3, 0.3, z=2)
    for x, y in ((32, 42), (40, 38), (70, 70)):
        e.lay(stroke([(x - 4, y + 2), (x, y - 2), (x + 4, y + 2)], 1.2), mat("#3a2a1c", 0.0, 0.9), 0.3, 0.3, z=2)
    # The way across, in light, from the foot to the star.
    way = bez((30, 74), (36, 60), (48, 64), (60, 44), 40)
    for i in range(0, 36, 6):
        e.lay(stroke(way[i:i + 4], 2.2), "glow", 0.5, 0.8, light=1.5, z=2)
    e.lay(star(62, 40, 13, 3.6, 4), "gold", 4, 2, z=2)
    e.lay(star(62, 40, 8, 2.4, 4, 45), "gold_dim", 4.6, 1.6, z=2)
    e.lay(circle(62, 40, 3), "glow", 1, 1.5, light=2.2, z=5)
    return e


def feather(e, root, ang, length, width, m, z=None):
    """One feather: a long blade of vane round its quill, from `root` at `ang` (0 up, clockwise)."""
    a = math.radians(ang)
    ux, uy = math.sin(a), -math.cos(a)
    tip = (root[0] + ux * length, root[1] + uy * length)
    mid = ((root[0] + tip[0]) / 2, (root[1] + tip[1]) / 2)
    e.lay(ellipse(mid[0], mid[1], width / 2, length / 2, ang), m, 3, width * 0.4, grain=0.4, kind="fine", z=z)
    e.lay(stroke([root, tip], 0.9, 0.3), mat("#8a8070", 0.0, 0.5), 3.4, 0.4, z=z)


def caltrop(e, cx, cy, s):
    """A snare of the road: four iron spikes, one always up."""
    for ang in (0, 120, 240):
        a = math.radians(ang)
        e.lay(poly([(cx + s * math.sin(a), cy + s * 0.45 * math.cos(a)), (cx + s * 0.22 * math.sin(a + 1.6), cy),
                    (cx + s * 0.22 * math.sin(a - 1.6), cy)]), "iron", 3, 1, round_=False, grain=0.3, kind="hammer")
    e.lay(poly([(cx, cy - s * 1.1), (cx - s * 0.2, cy), (cx + s * 0.2, cy)]), "iron", 4, 1, round_=False)
    e.lay(stroke([(cx, cy - s * 1.0), (cx, cy - s * 0.4)], 0.5), "steel", 4.4, 0.3)


def d_boot():
    """Sprint: a road boot of the Waystation's leather, iron-shod, driving forward, the road's
    dust kicked up behind it and the wind of it streaming back."""
    e = Emblem("physical", 0.94, (52, 50))
    for y, x0, w, li in ((30, 6, 2.6, 0.7), (44, 2, 3.2, 0.9), (58, 8, 2.4, 0.6), (70, 16, 1.8, 0.5)):
        e.lay(stroke([(x0, y + 4), (x0 + 30, y)], 0.3, w), "glow", 0.5, 1, light=li)
    e.lay(soft_union([circle(30, 80, 7), circle(22, 76, 5), circle(38, 84, 5), circle(16, 72, 3.5)], 4),
          mat("#8a7a62", 0.0, 0.9), 2, 7, grain=1.6, kind="cloud", soft=3)
    boot = rotated(poly([(40, 12), (64, 12), (64, 54), (66, 60), (84, 64), (90, 70), (88, 78), (40, 78), (38, 62)]), -12, 60, 70)
    e.lay(boot, "leather", 6, 5, grain=0.7, kind="fine")
    e.lay(rotated(stroke([(38, 16), (66, 16)], 5), -12, 60, 70), mat("#5a3a26", 0.0, 0.6), 7, 2, grain=0.5, kind="fine")
    e.lay(rotated(poly([(38, 76), (90, 76), (88, 82), (40, 82)]), -12, 60, 70), "iron", 6.5, 1.5, grain=0.4, kind="hammer")
    e.lay(rotated(poly([(38, 82), (52, 82), (52, 88), (40, 88)]), -12, 60, 70), "iron", 6.5, 1.5, grain=0.4, kind="hammer")
    for y in (26, 34, 42, 50):
        e.lay(rotated(stroke([(56, y), (64, y + 3)], 1.4), -12, 60, 70), mat("#c8b090", 0.0, 0.6), 7.4, 0.6)
    e.lay(rotated(stroke([(40, 58), (66, 58)], 3.6), -12, 60, 70), mat("#2a1810", 0.0, 0.6), 7.2, 1.2)
    e.lay(rotated(poly([(44, 55), (50, 55), (50, 61), (44, 61)]), -12, 60, 70), "gold_dim", 8, 1, grain=0.3, kind="hammer")
    for x in (46, 58, 70, 82):
        e.lay(rotated(circle(x, 79, 1.1), -12, 60, 70), "steel", 7.6, 0.6)
    return e


def d_horns():
    """Bull Rush: a forged iron bull-helm coming straight at you, its great horns lowered,
    a ring of the binders' gold through its nose, the road's dust thrown up either side."""
    e = Emblem("physical", 0.92, (50, 50))
    for sx in (-1, 1):
        e.lay(soft_union([circle(50 + sx * 26, 82, 8), circle(50 + sx * 36, 76, 6), circle(50 + sx * 18, 86, 5)], 4),
              mat("#8a7a62", 0.0, 0.9), 2, 7, grain=1.6, kind="cloud", soft=3)
    for sx in (-1, 1):
        horn = bez((50 + sx * 16, 40), (50 + sx * 34, 36), (50 + sx * 44, 22), (50 + sx * 34, 8), 40)
        e.lay(stroke(horn, 10, 2.0), "bone", 6, 5, grain=0.6)
        for t in (0.15, 0.3):
            p, q = horn[int(t * 39)], horn[int(t * 39) + 2]
            e.lay(stroke([p, q], 9.6 - t * 10), mat("#a89878", 0.0, 0.6), 6.4, 0.6)
    e.lay(ellipse(50, 50, 21, 25), "iron", 6, 6, grain=0.6, kind="hammer")
    e.lay(stroke([(50, 26), (50, 70)], 6, 4.4), "iron_dark", 7, 2, grain=0.4, kind="hammer")
    for sx in (-1, 1):
        e.lay(ellipse(50 + sx * 10, 50, 6.5, 2.2, sx * -10), mat("#020102", 0.0, 0.9), 0.5, 0.6, z=6)
        for y in (34, 42, 58, 64):
            e.lay(circle(50 + sx * 5.5, y, 1.2), "steel", 8, 0.6)
        e.lay(circle(50 + sx * 15, 40, 4.5), "gold_dim", 7.5, 2, grain=0.3, kind="hammer")
    e.lay(cut(circle(50, 76, 7), circle(50, 76, 4.4)), "gold", 9, 1.5, grain=0.3, kind="hammer")
    return e


def d_chain():
    """Grapple Chain: the binders' chain flung out, its links running to an iron grapple
    whose hooks are about to bite."""
    e = Emblem("physical", 0.9, (50, 52))
    path = bez((12, 92), (22, 64), (40, 74), (54, 50), 80)
    P = resample(path, 9.6)
    for i, (x, y) in enumerate(P):
        a, b = P[max(i - 1, 0)], P[min(i + 1, len(P) - 1)]
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if i % 2 == 0:
            e.lay(cut(ellipse(x, y, 7.4, 4.8, ang), ellipse(x, y, 4.6, 2.0, ang)), "iron", 4, 1.8, grain=0.5, kind="hammer")
        else:
            e.lay(ellipse(x, y, 7.4, 2.0, ang), "iron", 5, 1.2, grain=0.4, kind="hammer")
    e.lay(cut(circle(57, 46, 5), circle(57, 46, 2.6)), "iron", 5.5, 1.4, grain=0.4, kind="hammer")
    e.lay(stroke([(60, 43), (74, 29)], 6, 5), "iron", 6, 2.2, grain=0.5, kind="hammer")
    for ang in (-75, 15, 105):
        a = math.radians(ang)
        c, s_ = math.cos(a), math.sin(a)
        b0 = (74 + 2 * c, 29 + 2 * s_)
        hook = bez(b0, (b0[0] + 16 * c, b0[1] + 16 * s_), (b0[0] + 18 * c + 9 * s_, b0[1] + 18 * s_ - 9 * c),
                   (b0[0] + 9 * c + 10 * s_, b0[1] + 9 * s_ - 10 * c), 30)
        e.lay(stroke(hook, 5.0, 1.2), "steel", 6.5, 1.8, grain=0.3, kind="hammer")
    e.lay(circle(74, 29, 5), "iron_dark", 7, 2)
    for x, y in ((84, 40), (66, 14), (88, 22)):
        e.lay(stroke([(x - 4, y + 2), (x + 2, y - 2)], 1.4, 0.3), "glow", 0.5, 0.6, light=1.4)
    return e


def d_shield():
    """Shield Bash: a round shield of the Watch, planked and iron-rimmed, driven into what is
    in front of it, the blow going out from its face."""
    e = Emblem("physical", 0.94, (52, 50))
    for k, (r, w, li) in enumerate(((30, 4.4, 1.2), (38, 3.0, 0.8), (45, 1.8, 0.5))):
        e.lay(stroke(arc(52, 50, r, 30, 150, 50), w, w * 0.6), "glow", 1, 1.4, light=li)
    sh = ellipse(42, 50, 24, 34)
    e.lay(sh, "wood", 5, 6, grain=0.9)
    for x in (30, 38, 46, 54):
        e.lay(inter(stroke([(x, 10), (x, 90)], 1.0), sh), mat("#120a06", 0.0, 0.8), 0.4, 0.4, z=4.6)
    e.lay(cut(ellipse(42, 50, 24, 34), ellipse(42, 50, 20, 30)), "iron", 6.4, 1.8, grain=0.5, kind="hammer")
    for t in range(0, 360, 36):
        a = math.radians(t)
        e.lay(circle(42 + 22 * math.sin(a), 50 - 32 * math.cos(a), 1.3), "steel", 7.4, 0.8)
    e.lay(ellipse(44, 50, 9, 12), "steel", 9, 6, grain=0.4, kind="hammer")
    e.lay(stroke([(30, 50), (34, 50)], 3), "iron", 6.4, 1)
    e.lay(ellipse(47, 46, 2.2, 3.6, 20), mat("#ffffff", 0.0, 0.1), 0.6, 1, z=9, light=0.4)
    return e


def d_mark():
    """Mark Prey: the hunter's mark daubed in red on the quarry's hide, and the arrow already
    in it."""
    e = Emblem("blood", 0.94, (50, 50))
    e.lay(ellipse(48, 52, 34, 32), mat("#4a3424", 0.0, 0.85), 2, 3, grain=1.0, kind="fine")
    ring = cut(circle(48, 52, 24), circle(48, 52, 18.5))
    e.lay(ring, "glow", 0.6, 1.5, light=1.4, z=2)
    for a, b in (((48, 22), (48, 36)), ((48, 68), (48, 82)), ((18, 52), (32, 52)), ((64, 52), (78, 52))):
        e.lay(stroke([a, b], 3.4, 1.4), "glow", 0.6, 1.2, light=1.4, z=2)
    for x, y0, L in ((40, 74, 8), (58, 72, 10), (30, 64, 6)):
        e.lay(stroke([(x, y0), (x + 0.4, y0 + L)], 2.2, 0.8), "glow", 0.6, 1, light=1.1, z=2)
    e.lay(stroke([(48, 52), (84, 16)], 2.8), "wood", 5, 1.4, grain=0.4)
    for sx in (-1, 1):
        e.lay(poly([(78, 22), (88 + sx * 4, 6 - sx * 4), (92 + sx * 2, 10 - sx * 2), (84, 26)]) if sx > 0 else
              poly([(78, 22), (72, 6), (78, 4), (84, 16)]), mat("#c8b8a0", 0.0, 0.7), 5.4, 1.2, grain=0.4, kind="fine")
    e.lay(stroke([(84, 16), (90, 10)], 2.2), mat("#6a1010", 0.0, 0.7), 5.6, 1)
    e.lay(circle(48, 52, 4.6), mat("#1a0c06", 0.0, 0.8), 3, 1.5, z=2)
    e.lay(circle(48, 52, 2.4), "glow", 1, 1, light=2.0, z=5)
    return e


def d_wing():
    """Vault: a heron's wing of the fen thrown up in the spring away, and the snares left on
    the ground where you stood."""
    e = Emblem("physical", 0.92, (50, 50))
    for x, y, sz in ((28, 88, 6), (50, 92, 5.4), (72, 87, 6)):
        caltrop(e, x, y, sz)
    pale, grey, dark = mat("#e4dcd0", 0.0, 0.6), mat("#a8a298", 0.0, 0.6), mat("#5a5650", 0.0, 0.6)
    arm = bez((22, 74), (30, 40), (52, 18), (86, 14), 40)
    # Primaries from the far end of the arm, longest at the tip; the secondaries nearer in.
    for k in range(16):
        t = 0.28 + k * 0.045
        root = arm[min(int(t * 39), 39)]
        length = 22 + 24 * t ** 1.4
        ang = 196 - 50 * t
        m = dark if k >= 12 else (grey if k >= 8 else pale)
        feather(e, root, ang, length, 8.5, m)
    e.lay(stroke(arm, 8, 4.4), pale, 5.5, 3.5, grain=0.6, kind="fine")
    for k in range(10):
        t = 0.1 + k * 0.07
        root = arm[int(t * 39)]
        feather(e, (root[0] - 1, root[1] + 2), 200 - 40 * t, 12, 6.5, pale)
    for x, y0 in ((14, 14), (8, 32), (22, 4)):
        e.lay(stroke([(x + 4, y0 + 24), (x, y0)], 2.0, 0.3), "glow", 0.5, 1, light=0.6)
    return e


DESIGNS = {k[2:]: f for k, f in globals().items() if k.startswith("d_")}

SUBJECT = {
    "mirror": "an ornate hand mirror with a twisted gold wire frame and a leather-wrapped handle, its dark glass "
              "shattered from one point in a web of cracks glowing violet, a shard of glass flying away",
    "wraith": "an empty hooded shroud of tattered dark cloth floating, its torn hem streaming into rags that dissolve "
              "into violet light, a black void inside the hood with two small glowing violet eyes",
    "leap": "a streak of rushing air arcing high and crashing down into the ground, the ground split open in a "
            "glowing crater, broken slabs of stone thrust up on end round it, stones and dust thrown up",
    "leap2": "a bold hard-edged crescent streak of rushing white air sweeping down steeply from the upper left and "
             "crashing into the ground, the ground bursting open in a fan of blazing gold-white light, a crown of dark "
             "broken stone slabs thrust up on end round the break and black against the light, a ring of dust and "
             "light running out along the ground, stones thrown up",
    "blink": "a jagged rift torn in the air glowing white-blue, its edges rimed with frost, ice shards bursting out of it",
    "smoke": "a cracked round clay pot burst open at the top, thick billowing pale grey smoke boiling up out of it, "
             "violet light glowing from inside the pot",
    "echo": "a looping trail of violet light curving round in a circle back to where it began, ending in an arrowhead, "
            "a gold coin with a square hole glowing at its start",
    "feint": "a steel dagger thrusting up, a curved arrow of pale mist sweeping round past its point",
    "hourglass": "an hourglass with gold posts of twisted wire, violet glowing sand stopped in mid air between the bulbs",
    "embers": "a cracked molten coal of ember running, glowing orange cracks in its black crust, a trail of burning "
              "ground and small flames behind it",
    "aegis": "a steel kite shield with a gold rim and a rising golden sun on its face, a ring of golden ward light round it",
    "howl": "a curved bone war horn bound with iron bands, its call going out in red rings of sound",
    "expand": "an old forged black iron lantern with a ring handle and scrolled arms, a bright golden flame inside its "
              "glass panes, its light thrown wide in a ring of rays round it",
    "retaura": "a ring of golden holy flames standing all round a gold ring",
    "frostaura": "a ring of sharp ice needles standing outward all round an empty circle, frost",
    "pyre": "a pyre of crossed logs with a tall fire burning on it",
    "risen": "a leaning gravestone split in two, violet light pouring out of the crack, a skeletal hand of bone "
             "reaching up out of the earth before it",
    "herd": "a stag's skull with great branching antlers, green spirit fire in its eye sockets",
    "tether": "a dark red heart pierced by a hooked tendril of black shadow with violet light along it, red drops of "
              "blood running back along the tendril",
    "umbral": "a black iron crossbow bolt of shadow tearing forward, violet light along its barbed edge, dark streaks "
              "and torn rings of air behind it",
    "consecrate": "a glowing golden seal with seven notches burned into dark cracked stone ground, rays of light rising "
                  "from it",
    "drain": "a thread of glowing red blood pouring into an iron goblet bound with gold wire",
    "boot": "a worn leather road boot with an iron-shod sole and a buckled strap, driving forward, dust kicked up behind "
            "it, streaks of wind streaming back",
    "horns": "a forged black iron bull helm seen from the front with great curved bone horns lowered and a gold ring "
             "through its nose, streaks of rushing air round it",
    "chain": "an iron chain flung out in a curve, its end a three-hooked iron grappling hook about to bite",
    "shield": "a round wooden shield with an iron rim, rivets and a steel boss, driven forward, a blast of force going "
              "out from its face",
    "mark": "a hunter's mark daubed in glowing red paint on dark hide, a ringed cross, red drips, a fletched arrow "
            "driven into its centre",
    "wing": "a single raised grey heron's wing, long flight feathers spread, three iron caltrops lying on the ground "
            "below it",
    "static": "a twisted iron rod with a gold ball at its tip, blue-white lightning crawling up round it and leaping "
              "from its tip",
    "book": "an old parchment map half unrolled between two rolls, a glowing violet route across it leading to a gold "
            "compass star",
}


LOOK = ("A single bold painted emblem for a dark fantasy game skill icon, hand-painted with painterly brushwork, "
        "one strong clear silhouette, dramatic light from the upper left, its glow fading to pure black at the edges, on a pure "
        "black background, no frame, no border, no text: ")

# The painting each icon is cut from, chosen by eye at 128, 44 and 17 px against the old
# icon: KEY -> (denoise in hundredths, seed, place).
PICKS: dict[str, tuple[int, int, int]] = {
    "mirror": (62, 1300, 0), "wraith": (62, 1300, 0), "blink": (62, 1300, 0),
    "echo": (62, 1300, 0), "hourglass": (62, 1300, 1), "embers": (62, 1300, 0),
    "aegis": (62, 1300, 1), "howl": (62, 1300, 0), "expand": (50, 1300, 1), "retaura": (50, 1300, 1),
    "frostaura": (62, 1300, 0), "pyre": (62, 1300, 0), "risen": (50, 1300, 1), "herd": (62, 1300, 0),
    "tether": (62, 1300, 0), "consecrate": (50, 1300, 1), "drain": (50, 1300, 1),
    "static": (62, 1300, 0), "book": (62, 1300, 0),
    # Second pass: feint round its blade, smoke and the bolt lifted off the dark, leap's impact.
    "feint": (65, 1330, 1), "smoke": (55, 1330, 1), "umbral": (65, 1330, 0), "leap": (55, 1330, 1),
    # The other arts, brought into the family.
    "boot": (65, 1330, 0), "horns": (65, 1330, 1), "chain": (65, 1330, 0), "shield": (55, 1330, 1),
    "mark": (55, 1330, 0), "wing": (65, 1330, 0),
}


def make_guide(key):
    e = DESIGNS[key]()
    rgb, a = e.guide()
    os.makedirs(RAW, exist_ok=True)
    p = os.path.join(RAW, f"{key}_guide.png")
    Image.fromarray((rgb * 255 + 0.5).astype(np.uint8)).save(p)
    np.save(os.path.join(RAW, f"{key}_mask.npy"), a)
    return p, a, e.school


# Colours of its own where the school's words would drain it (steel's "cold white" painted the
# leap's stone and dust as a grey blur).
COLOURS = {"leap": "warm brown stone and dust colours lit hot gold and white from the impact",
           "leap2": "near-black stone slabs against blazing gold and white light, the streak of air bright white, strong "
                    "contrast between dark and light"}


def prompt(key, school):
    import icons
    import krea
    return LOOK + SUBJECT[key] + ", " + COLOURS.get(key, icons.SCHOOL.get(school, "")) + ". " + krea.STYLE


def paint(key, denoise=0.5, seed=1200, n=3):
    import krea
    p, a, school = make_guide(key)
    outs = krea.i2i(p, prompt(key, school), denoise=denoise, seed=seed, n=n, tag=f"em_{key}_{int(denoise * 100)}", out=RAW)
    return outs, a


def paint_many(keys, denoise=0.5, seed=1200, n=3, guides=True):
    """All their paintings in one queued graph (the GPU is shared: one place in the queue)."""
    import krea
    jobs = []
    for k in keys:
        if guides or not os.path.exists(os.path.join(RAW, f"{k}_guide.png")):
            p, a, school = make_guide(k)
        else:
            p, school = os.path.join(RAW, f"{k}_guide.png"), DESIGNS[k]().school
        jobs.append((f"em_{k}_{int(denoise * 100)}", p, prompt(k, school), denoise, seed))
    return krea.i2i_many(jobs, n=n, out=RAW)


def src(key):
    dn, seed, j = PICKS[key]
    return os.path.join(RAW, f"em_{key}_{dn}_{seed}_{j}.png")


def fit(key, src_=None, dst=None):
    import icons
    src_ = src_ or src(key)
    a = np.load(os.path.join(RAW, f"{key}_mask.npy"))
    img = Image.open(src_)
    if img.size[0] != N:
        a = cv2.resize(a, img.size, interpolation=cv2.INTER_AREA)
    # The guide's silhouette, a little grown so the painting's own edge is kept.
    m = cv2.dilate(a, np.ones((3, 3), np.uint8), iterations=max(1, img.size[0] // 512))
    dst = dst or os.path.join(UI, key + ".png")
    return icons.fit(src_, dst, mask=m)


def build(keys=None):
    """Every picked emblem into the game's icons (after the painted family: these replace theirs)."""
    for k in keys or list(PICKS):
        if not os.path.exists(os.path.join(RAW, f"{k}_mask.npy")):
            make_guide(k)
        fit(k)
    print("emblems", len(keys or PICKS))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--guides":
        for k in args[1:] or list(DESIGNS):
            print(make_guide(k)[0])
    elif args and args[0] == "--many":
        for k, v in paint_many(args[1:] or list(DESIGNS)).items():
            print(k, len(v))
    elif args and args[0] == "--fit":
        build(args[1:] or None)
    else:
        for k in args or list(DESIGNS):
            print(k, paint(k)[0])
