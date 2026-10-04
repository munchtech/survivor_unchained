"""Skill and art icons as modelled emblems (icons/glyph_color/KEY.png), for the ones the
painted family left soft or put a person in: each is drawn as shapes (signed distances in
a 100-unit square, y down), given heights and materials, lit by the house's matcaps with
its own light where it burns, and set on black in its school's glow: that is the guide.
The local Krea paints over the guide at a middling denoise (the hand, the brushwork, the
light's variety), and the icon is cut on the guide's own silhouette, so its shape stays
exact and reads at 17 px.

The thing itself, never a person: a hand mirror, an empty hood, a rift in the frost.

    python tools/uiforge/emblems.py [KEY ...]      # guides, paintings, icons
    python tools/uiforge/emblems.py --guides KEY   # guides only (no GPU)
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


# ------------------------------------------------------------------ shapes --
# Signed distances in units, positive inside.

def grid():
    xx, yy = F.grid(N, N)
    return xx / K, yy / K


X, Y = grid()


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


def bez(p0, p1, p2, p3, n=40):
    return F.bezier(p0, p1, p2, p3, n)


def arc(cx, cy, r, a0, a1, n=48):
    """Points along a circle, angles in degrees, 0 at the top, clockwise."""
    return [(cx + r * math.sin(math.radians(a)), cy - r * math.cos(math.radians(a))) for a in np.linspace(a0, a1, n)]


def rot(pts, ang, cx=50, cy=50):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def cov(sd):
    return np.clip(sd * K + 0.5, 0, 1).astype(np.float32)


# --------------------------------------------------------------- the forge --

class Emblem:
    """Layers laid in order: each a shape, a material and a profile. Light (emission) can be
    laid on any of them, and a glow round the whole."""

    def __init__(self, school):
        self.school = school
        self.s = F.Surface(N, N)
        self.light = np.zeros((N, N), np.float32)   # how hot each pixel burns (0..)
        self.glow = 1.0

    def lay(self, sd, mat, height=3.0, bevel=2.0, round_=True, tint=None, light=0.0, z=None):
        """`height` and `bevel` in units; the part's top at its height, its edge rounded over
        `bevel`; laid over what is there (z: the base it rises from, default what is under)."""
        c = cov(sd)
        t = np.clip(sd / bevel, 0, 1)
        prof = np.sqrt(1 - (1 - t) ** 2) if round_ else t
        base = self.s.height if z is None else np.full_like(self.s.height, z * K)
        h = base + prof * height * K
        self.s.height = np.where(c > 0.5, np.maximum(self.s.height if z is None else h * 0, h), self.s.height)
        if isinstance(mat, str) and mat.startswith("glow"):
            core, edge = SCHOOL[self.school]
            # A burning thing: white-hot inside, its colour at its edge.
            k = np.clip(sd / (bevel * 2.5), 0, 1)
            col = F.hexc(edge) * (1 - k[..., None]) + F.hexc(core) * k[..., None]
            self.s.paint(c, F.Mat((0.02, 0.02, 0.02), 0.0, 0.6))
            self.s.emit = self.s.emit * (1 - c[..., None]) + col * c[..., None] * (light or 1.6)
            self.light = np.maximum(self.light, c * (light or 1.6))
        else:
            m = F.MATS[mat] if isinstance(mat, str) else mat
            if tint is not None:
                m = F.Mat(tuple(np.asarray(m.albedo) * np.asarray(tint)), m.metal, m.rough)
            self.s.paint(c, m)
            if light:
                core, edge = SCHOOL[self.school]
                self.s.emit = self.s.emit * (1 - c[..., None]) + F.hexc(edge) * c[..., None] * light
                self.light = np.maximum(self.light, c * light)
        self.s.alpha = np.maximum(self.s.alpha, c)
        return c

    def guide(self):
        """The lit emblem on black with its school's glow round it (linear -> sRGB, float)."""
        lin = self.s.shade(normal_strength=1.0, ao=0.5, shadow=0.45)
        core, edge = SCHOOL[self.school]
        a = self.s.alpha
        # Rim of the school's light on the emblem's edges (as if it stood in its own glow).
        er = cv2.GaussianBlur(a, (0, 0), 6)
        rim = np.clip(a - er, 0, 1) * 1.4 + np.clip(er - a, 0, 1) * 0
        lin = lin + rim[..., None] * F.hexc(edge) * 0.5
        # The glow: from the burning parts strongly, from the whole shape softly.
        g = cv2.GaussianBlur(self.light, (0, 0), 28) * 1.2 + cv2.GaussianBlur(self.light, (0, 0), 90) * 0.9
        # The whole shape's halo: faint for steel (it does not burn), stronger for magic.
        halo = 0.12 if self.school == "physical" else 0.35
        g = g + cv2.GaussianBlur(a, (0, 0), 60) * halo * self.glow
        glow = g[..., None] * F.hexc(edge)
        out = lin * a[..., None] + glow * (1 - a[..., None] * 0.6)
        # Fade to black well before the edges.
        r = np.hypot(X - 50, Y - 50) / 50
        out = out * np.clip((1.02 - r) / 0.18, 0, 1)[..., None]
        x = np.clip(out, 0, None)
        y = np.where(x < 0.8, x, 0.8 + 0.2 * (1 - np.exp(-(x - 0.8) / 0.2)))
        return F.lin_to_srgb(np.clip(y, 0, 1)).astype(np.float32), a


# ----------------------------------------------------------------- designs --

def d_mirror():
    """Mirror Step: a hand mirror, its glass cracked across, violet light in the glass."""
    e = Emblem("arcane")
    a = -24
    glass = ellipse(46, 40, 21, 27, a)
    frame = cut(ellipse(46, 40, 27, 33, a), ellipse(46, 40, 21.5, 27.5, a))
    hp = rot([(46, 72), (46, 95)], a, 46, 40)
    handle = stroke(hp, 9.5, 7.5)
    knob = circle(*rot([(46, 97)], a, 46, 40)[0], 5.2)
    collar = stroke(rot([(46, 70), (46, 75)], a, 46, 40), 14)
    e.lay(handle, "leather", 4, 3.5)
    e.lay(knob, "gold_dim", 5, 3)
    e.lay(collar, "gold_dim", 5, 2)
    # Dark glass with the other side's light deep in it; the crack lets it out.
    e.lay(glass, F.Mat(tuple(F.hexc("#2a1440")), 0.0, 0.04), 2, 8, light=0.45)
    e.lay(ellipse(*rot([(38, 28)], a, 46, 40)[0], 5, 9, a - 20), F.Mat(tuple(F.hexc("#e8d8ff")), 0.0, 0.1), 0.5, 1,
          z=2, light=0.6)
    cr = rot([(30, 22), (40, 34), (37, 41), (50, 50), (47, 57), (60, 66)], a, 46, 40)
    e.lay(stroke(cr, 3.0, 1.2), "glow", 0.5, 0.8, light=2.4, z=2)
    e.lay(stroke(rot([(40, 34), (52, 30), (60, 26)], a, 46, 40), 2.0, 0.6), "glow", 0.5, 0.6, light=2.0, z=2)
    e.lay(frame, "gold", 5, 2.5)
    # Four studs on the frame.
    for t in (45, 135, 225, 315):
        p = rot([(46 + 24 * math.sin(math.radians(t)), 40 - 30 * math.cos(math.radians(t)))], a, 46, 40)[0]
        e.lay(circle(p[0], p[1], 2.6), "gold", 7, 2)
    return e


def d_wraith():
    """Wraith Walk: an empty hood and its shroud, torn to rags that stream behind it, two
    points of light where a face should be."""
    e = Emblem("shadow")
    hood = poly([(50, 6), (64, 14), (73, 30), (78, 48), (84, 62), (78, 70), (86, 82), (74, 80), (72, 92), (63, 84),
                 (57, 96), (50, 84), (42, 95), (37, 83), (27, 90), (28, 78), (14, 84), (21, 70), (16, 62), (22, 48),
                 (27, 30), (36, 14)])
    e.lay(hood, F.Mat(tuple(F.hexc("#1a1424")), 0.0, 0.7), 5, 6)
    # The hood's fold: a raised edge round the opening.
    lip = cut(ellipse(50, 40, 17, 21), ellipse(50, 41, 13, 17))
    e.lay(lip, F.Mat(tuple(F.hexc("#2a2238")), 0.0, 0.6), 7, 2)
    face = ellipse(50, 42, 13, 17)
    e.lay(face, F.Mat((0.0, 0.0, 0.0), 0.0, 0.9), 0.5, 1, z=0.5)
    for x in (44.5, 55.5):
        e.lay(ellipse(x, 40, 2.4, 1.5, -12 if x < 50 else 12), "glow", 1, 1, light=2.4, z=1)
    e.glow = 1.4
    return e


def d_leap():
    """Crashing Leap: a heavy iron wedge driven down into the ground, the ground breaking
    in a ring and stones thrown up either side."""
    e = Emblem("physical")
    ring = cut(ellipse(50, 80, 42, 11), ellipse(50, 79, 34, 7))
    e.lay(ring, F.Mat(tuple(F.hexc("#8a7a62")), 0.0, 0.8), 2, 2)
    rng = np.random.default_rng(3)
    for sx in (-1, 1):
        for j, (dx, dy, s) in enumerate(((20, -6, 5.5), (30, -14, 4.2), (36, -3, 3.4), (14, -16, 3.0))):
            cx, cy = 50 + sx * dx, 74 + dy
            pts = [(cx + s * math.cos(t) * (0.7 + 0.5 * rng.random()), cy + s * math.sin(t) * (0.7 + 0.5 * rng.random()))
                   for t in np.linspace(0, 2 * math.pi, 7)[:-1]]
            e.lay(poly(pts), F.Mat(tuple(F.hexc("#9a8a70")), 0.0, 0.7), 3, 2)
    wedge = poly([(50, 82), (30, 46), (38, 46), (38, 8), (62, 8), (62, 46), (70, 46)])
    e.lay(wedge, "steel", 6, 5)
    # A groove down the middle (the fuller), and motion lines above.
    e.lay(stroke([(50, 14), (50, 52)], 3.2), "iron_dark", 4, 1.2, round_=False)
    for x in (24, 76):
        e.lay(stroke([(x, 6), (x, 34)], 2.6, 0.4), "glow", 1, 1, light=1.0)
    # The impact: light where the point meets the ground.
    e.lay(ellipse(50, 80, 9, 3.2), "glow", 1, 1.5, light=2.2)
    return e


def d_blink():
    """Blink: a rift torn in the air, rimed at its edges, ice shards bursting from it."""
    e = Emblem("frost")
    for ang, L, w in ((-60, 34, 7), (-28, 30, 6), (28, 31, 6), (62, 34, 7), (-100, 26, 5), (100, 27, 5), (180, 18, 5),
                      (150, 22, 4.5), (-150, 22, 4.5)):
        a = math.radians(ang)
        ux, uy = math.sin(a), -math.cos(a)
        p0 = (50 + ux * 12, 52 + uy * 18)
        p1 = (50 + ux * (12 + L), 52 + uy * (18 + L))
        n = (-uy, ux)
        shard = poly([p1, (p0[0] + n[0] * w / 2, p0[1] + n[1] * w / 2), (p0[0] - n[0] * w / 2, p0[1] - n[1] * w / 2)])
        e.lay(shard, F.Mat(tuple(F.hexc("#c8e8ff")), 0.0, 0.08), 3, 2, round_=False)
    rift = poly([(50, 8), (55, 22), (52, 30), (59, 44), (55, 54), (60, 70), (52, 82), (50, 96), (47, 82), (41, 70),
                 (46, 56), (40, 44), (47, 32), (44, 20)])
    e.lay(rift, "glow", 2, 4, light=2.0)
    return e


def d_smoke():
    """Smoke: a firepot of the Dig's clay, cracked, smoke boiling up out of it."""
    e = Emblem("shadow")
    smoke = union(circle(50, 34, 16), circle(33, 42, 12), circle(67, 40, 13), circle(42, 20, 11), circle(60, 18, 10),
                  circle(28, 28, 8), circle(73, 26, 8), circle(50, 8, 7))
    e.lay(smoke, F.Mat(tuple(F.hexc("#6a6278")), 0.0, 0.9), 6, 9)
    # Curls cut into the smoke (where one billow overlaps the next).
    for cx, cy, r, a0, a1 in ((50, 34, 11, 200, 340), (33, 42, 8, 180, 320), (67, 40, 9, 20, 160), (42, 20, 7, 200, 330)):
        e.lay(stroke(arc(cx, cy, r, a0, a1), 1.6, 0.6), F.Mat(tuple(F.hexc("#2a2432")), 0.0, 0.9), 6, 0.5, z=5.5)
    pot = ellipse(50, 72, 20, 19)
    e.lay(pot, F.Mat(tuple(F.hexc("#5a3a2a")), 0.0, 0.6), 7, 9)
    e.lay(stroke([(36, 64), (64, 64)], 2.2), F.Mat(tuple(F.hexc("#3a2418")), 0.0, 0.7), 1, 1, z=6.2)
    neck = poly([(42, 50), (58, 50), (61, 56), (39, 56)])
    e.lay(neck, F.Mat(tuple(F.hexc("#6a4632")), 0.0, 0.6), 7, 2)
    for crk in ([(44, 76), (48, 70), (46, 66), (52, 60)], [(58, 84), (60, 76), (64, 72)]):
        e.lay(stroke(crk, 1.8, 0.8), "glow", 0.5, 0.6, light=1.4, z=6.5)
    e.lay(ellipse(50, 51, 7, 2), "glow", 1, 1, light=1.6)
    return e


def d_echo():
    """Echo Step: a sign struck once and heard three times: a bright diamond and the
    rings it sends out, each fainter."""
    e = Emblem("arcane")
    for i, (r, w, li) in enumerate(((44, 3.0, 0.5), (34, 4.0, 0.8), (24, 5.0, 1.2))):
        ring_ = stroke(arc(36, 50, r, 30, 150), w, w)
        e.lay(ring_, "glow", 1, 1.2, light=li)
    e.lay(poly([(36, 34), (48, 50), (36, 66), (24, 50)]), "gold", 6, 4)
    e.lay(poly([(36, 40), (44, 50), (36, 60), (28, 50)]), "glow", 2, 3, light=2.0)
    return e


def d_feint():
    """Feint: a blade's thrust turned aside: a dagger, and the sweep that slips round it."""
    e = Emblem("physical")
    sweep = bez((78, 84), (96, 52), (82, 18), (52, 12), 40)
    e.lay(stroke(sweep, 3.0, 9.0), "glow", 1, 3, light=1.1)
    head = poly([(40, 12), (56, 2), (56, 22)])
    e.lay(head, "glow", 1, 3, light=1.4)
    blade = poly([(26, 88), (22, 84), (58, 36), (64, 30), (62, 40)])
    e.lay(blade, "steel", 5, 3)
    e.lay(stroke([(24, 86), (58, 38)], 1.2), "iron_dark", 5.5, 0.6)
    guard = stroke([(14, 70), (34, 90)], 5.5)
    e.lay(guard, "gold_dim", 6, 2.5)
    grip = stroke([(22, 82), (10, 96)], 6, 5)
    e.lay(grip, "leather", 5, 3)
    return e


def d_hourglass():
    """Time Slip: an hourglass, its sand stopped in the air between the bulbs."""
    e = Emblem("arcane")
    for y in (10, 90):
        e.lay(stroke([(24, y), (76, y)], 7), "gold", 6, 3)
    for x in (27, 73):
        e.lay(stroke([(x, 12), (x, 88)], 4.2), "gold_dim", 5, 2)
    glass = union(poly([(32, 15), (68, 15), (68, 22), (53, 48), (53, 52), (68, 78), (68, 85), (32, 85), (32, 78),
                        (47, 52), (47, 48), (32, 22)]))
    e.lay(glass, F.Mat(tuple(F.hexc("#3a2a50")), 0.0, 0.05), 3, 4)
    sand_top = poly([(37, 24), (63, 24), (51, 44), (49, 44)])
    sand_bot = poly([(36, 82), (64, 82), (58, 72), (50, 68), (42, 72)])
    e.lay(sand_top, "glow", 1, 2, light=1.3, z=3)
    e.lay(sand_bot, "glow", 1, 2, light=1.3, z=3)
    for i, y in enumerate((50, 55, 60, 64)):
        e.lay(circle(50, y, 1.3 - i * 0.12), "glow", 1, 0.8, light=2.0, z=3)
    return e


def d_embers():
    """Cinder Trail: three coals of the Morrow's ember laid along the ground, each burning."""
    e = Emblem("fire")
    path = [(18, 82), (40, 68), (66, 56), (84, 34)]
    for (x, y), s in zip(path, (5, 7, 9, 11)):
        coal = poly([(x - s, y + s * 0.4), (x - s * 0.6, y - s * 0.4), (x + s * 0.2, y - s * 0.6), (x + s, y - s * 0.1),
                     (x + s * 0.7, y + s * 0.6), (x - s * 0.3, y + s * 0.7)])
        e.lay(coal, F.Mat(tuple(F.hexc("#1a0c08")), 0.0, 0.7), 3, 2)
        e.lay(stroke([(x - s * 0.6, y), (x, y - s * 0.2), (x + s * 0.5, y + s * 0.2)], s * 0.22, s * 0.1), "glow", 0.5, 0.5,
              light=1.8, z=2.5)
        fl = poly([(x - s * 0.7, y - s * 0.3), (x - s * 0.2, y - s * 2.6), (x + s * 0.1, y - s * 1.4), (x + s * 0.5, y - s * 3.6),
                   (x + s * 0.8, y - s * 0.4)])
        e.lay(fl, "glow", 1, 2, light=1.6)
    return e


DESIGNS = {k[2:]: f for k, f in globals().items() if k.startswith("d_")}

SUBJECT = {
    "mirror": "a hand mirror with a gold frame and a leather handle, its oval glass cracked across, glowing violet light inside the glass",
    "wraith": "an empty hooded shroud of tattered dark cloth streaming in rags, a black void where a face should be, two small glowing violet eyes",
    "leap": "a heavy iron wedge driven down into the ground, the ground cracking in a ring, stones thrown up, dust",
    "blink": "a jagged rift torn in the air glowing white-blue, ice shards bursting out of it",
    "smoke": "a cracked clay firepot with thick grey-violet smoke boiling up out of it",
    "echo": "a glowing violet diamond rune sending out three fading rings of light",
    "feint": "a steel dagger and a curved sweep of light slipping round its point",
    "hourglass": "a gold-framed hourglass, violet glowing sand stopped in mid air between the bulbs",
    "embers": "three burning coals of molten ember in a trail on the ground, flames rising from each",
}

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


def d_aegis():
    """Shielded: a kite shield of the Order, a ward of dawn-gold round it."""
    e = Emblem("holy")
    e.lay(stroke(arc(50, 50, 42, 0, 360, 96), 3.0), "glow", 1, 1.2, light=1.0)
    kite = poly([(50, 90), (24, 52), (26, 18), (50, 10), (74, 18), (76, 52)])
    e.lay(kite, "steel", 5, 3)
    e.lay(cut(kite, poly([(50, 82), (30, 51), (32, 22), (50, 16), (68, 22), (70, 51)])), "gold", 6.5, 2)
    e.lay(stroke([(50, 20), (50, 76)], 4), "gold", 6.5, 2)
    e.lay(stroke([(34, 40), (66, 40)], 4), "gold", 6.5, 2)
    e.lay(circle(50, 40, 5), "glow", 2, 2, light=1.8, z=6.5)
    return e


def d_howl():
    """War cry: a carter's war horn, iron-banded, its call going out in red."""
    e = Emblem("blood")
    horn = stroke(bez((22, 78), (26, 40), (52, 22), (70, 30), 40), 6, 24)
    e.lay(horn, "bone", 5, 5)
    for (a, b) in (((24, 64), (34, 70)), ((32, 44), (42, 52)), ((48, 30), (54, 42))):
        e.lay(stroke([a, b], 3.2), "iron", 7, 1.5)
    e.lay(ellipse(70, 30, 6, 12, -28), F.Mat((0.02, 0.0, 0.0), 0.0, 0.8), 6, 1)
    for i, r in enumerate((14, 22, 30)):
        e.lay(stroke(arc(70, 30, r, 25, 125), 3.4 - i * 0.6), "glow", 1, 1.2, light=1.6 - i * 0.35)
    e.lay(stroke([(18, 82), (14, 90)], 5, 4), "gold_dim", 5, 2)
    return e


def d_expand():
    """Wider reach: a bright orb, four arrowheads driven outward from it."""
    e = Emblem("arcane")
    e.lay(circle(50, 50, 13), "glow", 2, 6, light=1.8)
    e.lay(stroke(arc(50, 50, 22, 0, 360, 96), 2.4), "glow", 1, 1, light=0.8)
    for ang in (45, 135, 225, 315):
        pts = rot([(50, 5), (69, 27), (58, 27), (58, 33), (42, 33), (42, 27), (31, 27)], ang)
        e.lay(poly(pts), "gold", 5, 2.5)
    return e


def d_retaura():
    """A ring of the Order's fire round you: flames standing all round an empty ring."""
    e = Emblem("holy")
    e.lay(cut(circle(50, 50, 30), circle(50, 50, 23)), "gold", 4, 2)
    for k in range(12):
        a = k * 30
        sd = flame_tongue(50, 22, 9, 16 + 7 * (k % 2), lean=1.5)
        e.lay(rotated(sd, a), "glow", 1, 2, light=1.5)
    e.lay(cut(circle(50, 50, 21), circle(50, 50, 17)), "glow", 1, 1, light=0.7)
    return e


def _at(sd, xr, yr):
    """A field sampled at other coordinates (to rotate or move a shape made at its place)."""
    mx = (xr * K).astype(np.float32)
    my = (yr * K).astype(np.float32)
    return cv2.remap(sd.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=-50)


def rotated(sd, ang, cx=50, cy=50):
    c_, s_ = math.cos(math.radians(-ang)), math.sin(math.radians(-ang))
    xr = cx + (X - cx) * c_ - (Y - cy) * s_
    yr = cy + (X - cx) * s_ + (Y - cy) * c_
    return _at(sd, xr, yr)


def d_frostaura():
    """A ring of the Low Ford's rime: ice needles standing out all round."""
    e = Emblem("frost")
    e.lay(cut(circle(50, 50, 24), circle(50, 50, 19)), F.Mat(tuple(F.hexc("#c8e8ff")), 0.0, 0.08), 3, 2)
    needle = poly([(50, 4), (54, 24), (50, 28), (46, 24)])
    small = poly([(50, 12), (52.5, 25), (50, 27), (47.5, 25)])
    for k in range(16):
        e.lay(rotated(needle if k % 2 == 0 else small, k * 22.5), F.Mat(tuple(F.hexc("#d8f0ff")), 0.0, 0.05), 3, 2,
              round_=False, light=0.25)
    e.lay(cut(circle(50, 50, 18), circle(50, 50, 15)), "glow", 1, 1, light=0.9)
    return e


def d_pyre():
    """A pyre: logs crossed and stacked, a tall fire on them."""
    e = Emblem("fire")
    for (a, b, w) in (((14, 86), (86, 72), 9), ((16, 72), (84, 86), 9), ((22, 66), (78, 66), 8)):
        e.lay(stroke([a, b], w), "wood", 5, 4)
        e.lay(circle(b[0], b[1], w / 2 - 0.5), F.Mat(tuple(F.hexc("#8a5a34")), 0.0, 0.7), 5.5, 2)
    e.lay(flame_tongue(50, 66, 46, 58, lean=-2), "glow", 2, 6, light=1.6)
    e.lay(flame_tongue(36, 64, 18, 30, lean=-4), "glow", 2, 3, light=1.8)
    e.lay(flame_tongue(64, 64, 20, 34, lean=3), "glow", 2, 3, light=1.8)
    return e


def d_risen():
    """The risen: a grave's stone split, the barrow's violet light pouring out of the crack."""
    e = Emblem("shadow")
    mound = ellipse(50, 88, 40, 9)
    e.lay(mound, F.Mat(tuple(F.hexc("#2a2420")), 0.0, 0.9), 3, 4)
    stone = union(poly([(28, 88), (28, 34), (72, 34), (72, 88)]), circle(50, 34, 22))
    left = inter(stone, poly([(0, 0), (52, 0), (46, 30), (54, 46), (44, 64), (50, 100), (0, 100)]))
    right = inter(stone, poly([(100, 0), (54, 0), (48, 30), (56, 46), (46, 64), (52, 100), (100, 100)]))
    e.lay(rotated(left, -6, 30, 88), F.Mat(tuple(F.hexc("#5a5664")), 0.0, 0.7), 6, 3)
    e.lay(rotated(right, 5, 70, 88), F.Mat(tuple(F.hexc("#5a5664")), 0.0, 0.7), 6, 3)
    e.lay(stroke([(52, 10), (47, 30), (55, 46), (45, 64), (51, 90)], 4.5, 2.5), "glow", 1, 1.5, light=2.2)
    return e


def d_herd():
    """The spirit herd: a stag's skull and its great antlers in the Verge's green fire."""
    e = Emblem("nature")
    for sx in (-1, 1):
        beam = bez((50 + sx * 9, 40), (50 + sx * 22, 30), (50 + sx * 36, 22), (50 + sx * 40, 6), 30)
        e.lay(stroke(beam, 6.5, 3.0), "bone", 4, 2.5)
        for (t, dx, dy) in ((0.12, 10, -6), (0.38, -3, -20), (0.62, 9, -15), (0.85, 12, -6)):
            p = beam[int(t * 29)]
            e.lay(stroke([p, (p[0] + sx * dx * 0.5, p[1] + dy * 0.6), (p[0] + sx * dx, p[1] + dy)], 4.4, 1.4), "bone", 4, 2)
    skull = poly([(50, 82), (40, 64), (36, 44), (42, 34), (50, 32), (58, 34), (64, 44), (60, 64)])
    e.lay(skull, "bone", 6, 5)
    for x in (43.5, 56.5):
        e.lay(ellipse(x, 47, 3.6, 4.6), "glow", 1, 1.5, light=2.2, z=3)
    e.lay(stroke([(47, 74), (53, 74)], 2.2), F.Mat((0.05, 0.04, 0.03), 0.0, 0.8), 6.2, 0.6)
    e.glow = 1.3
    return e


def d_tether():
    """A tether: a dark coil wound round a heart, drawing it."""
    e = Emblem("shadow")
    e.lay(heart_shape(50, 52, 30), F.Mat(tuple(F.hexc("#b01828")), 0.0, 0.2), 6, 8, light=0.8)
    for y0, y1 in ((24, 44), (40, 62), (58, 78)):
        e.lay(stroke(bez((12, y0), (40, y0 - 10), (60, y1 + 10), (90, y1), 30), 4.6), "glow", 1, 1.5, light=1.4, z=6)
    e.lay(stroke(bez((86, 76), (94, 64), (94, 40), (80, 26), 30), 3.2, 1.2), "glow", 1, 1.2, light=1.0)
    return e


def d_umbral():
    """An umbral bolt: a spearhead of shadow tearing forward, the dark streaming behind it."""
    e = Emblem("shadow")
    # The dark streaming behind it, down and to the left.
    for (a, b, w) in (((10, 92), (40, 62), 5), ((8, 76), (34, 58), 3), ((24, 96), (44, 70), 3)):
        e.lay(stroke([a, b], 1, w), "glow", 1, 1, light=0.9)
    head = poly(rot([(50, 6), (64, 40), (56, 36), (54, 70), (46, 70), (44, 36), (36, 40)], 55))
    e.lay(head, F.Mat(tuple(F.hexc("#141020")), 0.6, 0.3), 6, 4, light=0.2)
    edge = poly(rot([(50, 10), (60, 38), (50, 32), (40, 38)], 55))
    e.lay(edge, "glow", 1, 2, light=1.6, z=6)
    return e


def d_consecrate():
    """Consecrated ground: the Legion's seal burned gold into the stone, seven notches round it."""
    e = Emblem("holy")
    ring = cut(ellipse(50, 56, 42, 26), ellipse(50, 56, 33, 19))
    e.lay(ring, "glow", 1, 2, light=1.5)
    for k in range(7):
        a = math.radians(k * 360 / 7)
        x, y = 50 + 37.5 * math.sin(a), 56 - 22.5 * math.cos(a)
        e.lay(ellipse(x, y, 3.2, 2.4), F.Mat((0.03, 0.02, 0.01), 0.0, 0.8), 1.2, 0.5, z=0.5)
    e.lay(ellipse(50, 56, 12, 7), "glow", 1, 2, light=1.2)
    for x, h in ((50, 46), (38, 30), (62, 32), (26, 18), (74, 20)):
        e.lay(stroke([(x, 54), (x, 54 - h)], 3.2, 0.5), "glow", 1, 1, light=1.1)
    return e


def d_drain():
    """Drain: a thread of red life poured into an iron goblet."""
    e = Emblem("blood")
    cup = union(poly([(30, 30), (70, 30), (64, 50), (54, 58), (46, 58), (36, 50)]), stroke([(50, 58), (50, 80)], 6),
                ellipse(50, 84, 16, 5))
    e.lay(cup, "iron", 5, 4)
    e.lay(cut(ellipse(50, 31, 20, 4.5), ellipse(50, 31, 18, 3.2)), "gold", 6, 1.5)
    e.lay(ellipse(50, 31.5, 17.5, 3), "glow", 1, 1, light=1.4, z=4)
    stream = bez((90, 8), (74, 6), (58, 12), (52, 30), 30)
    e.lay(stroke(stream, 2.4, 5.4), "glow", 1, 2, light=1.8)
    for x, y, r in ((84, 22, 1.8), (72, 26, 1.4), (63, 22, 1.1)):
        e.lay(circle(x, y, r), "glow", 1, 1, light=1.5)
    return e


def d_static():
    """Static: two iron studs, a spark leaping between them."""
    e = Emblem("storm")
    for x, y in ((22, 72), (78, 30)):
        e.lay(circle(x, y, 10), "iron", 5, 4)
        e.lay(circle(x, y, 4), "gold", 7, 2)
    bolt = [(26, 66), (36, 58), (32, 52), (48, 46), (44, 40), (60, 38), (56, 32), (74, 34)]
    e.lay(stroke(bolt, 5, 3), "glow", 1, 1.5, light=2.0)
    e.lay(stroke([(48, 46), (56, 56), (62, 54)], 2.4, 0.8), "glow", 1, 1, light=1.4)
    e.lay(stroke([(36, 58), (32, 40)], 2.0, 0.6), "glow", 1, 1, light=1.2)
    return e


def d_book():
    """A tome of the Order: worn leather, iron corners, an ember set in its cover."""
    e = Emblem("arcane")
    cover = poly([(24, 14), (76, 14), (80, 18), (80, 86), (76, 90), (24, 90), (20, 86), (20, 18)])
    e.lay(cover, "leather", 6, 3)
    e.lay(stroke([(22, 18), (22, 86)], 6), F.Mat(tuple(F.hexc("#2a160e")), 0.0, 0.6), 7, 2)
    for x, y, sx, sy in ((22, 16, 1, 1), (78, 16, -1, 1), (22, 88, 1, -1), (78, 88, -1, -1)):
        e.lay(poly([(x, y), (x + sx * 13, y), (x, y + sy * 13)]), "iron", 7, 1.5)
    e.lay(cut(poly([(50, 30), (66, 52), (50, 74), (34, 52)]), poly([(50, 36), (61, 52), (50, 68), (39, 52)])), "gold", 7.5, 1.5)
    e.lay(circle(50, 52, 6.5), "glow", 2, 2.5, light=2.0, z=6)
    e.lay(stroke([(80, 46), (90, 46), (90, 58), (80, 58)], 3), "iron", 6, 1.5)
    return e


DESIGNS = {k[2:]: f for k, f in globals().items() if k.startswith("d_")}

SUBJECT.update({
    "aegis": "a steel kite shield with a gold cross and rim, a ring of golden ward light round it",
    "howl": "a curved bone war horn bound with iron bands, its call going out in red rings of sound",
    "expand": "a glowing violet orb with four gold arrowheads driven outward from it",
    "retaura": "a ring of golden holy flames standing all round an empty circle",
    "frostaura": "a ring of sharp ice needles standing outward all round an empty circle, frost",
    "pyre": "a pyre of crossed logs with a tall fire burning on it",
    "risen": "a gravestone split in two, violet light pouring out of the crack",
    "herd": "a stag's skull with great branching antlers, green spirit fire in its eyes",
    "tether": "a dark red heart bound by coils of glowing violet shadow",
    "umbral": "a black spearhead of shadow tearing forward, violet light along its edge, dark streaks behind it",
    "consecrate": "a glowing golden seal burned into dark stone ground, seven notches round it, rays rising from it",
    "drain": "a thread of glowing red blood pouring into an iron goblet",
    "static": "two iron studs with a crackling blue spark of lightning leaping between them",
    "book": "an old leather tome with iron corners and a glowing violet ember set in a gold diamond on its cover",
})


LOOK = ("A single bold painted emblem for a dark fantasy game skill icon, in the style of Diablo IV skill icons, hand painted, "
        "one strong clear silhouette, dramatic light from the upper left, its glow fading to pure black at the edges, on a pure "
        "black background, no frame, no border, no text: ")


def make_guide(key):
    e = DESIGNS[key]()
    rgb, a = e.guide()
    os.makedirs(RAW, exist_ok=True)
    p = os.path.join(RAW, f"{key}_guide.png")
    Image.fromarray((rgb * 255 + 0.5).astype(np.uint8)).save(p)
    np.save(os.path.join(RAW, f"{key}_mask.npy"), a)
    return p, a, e.school


def paint(key, denoise=0.5, seed=1200, n=3):
    import krea
    import icons
    p, a, school = make_guide(key)
    prompt = LOOK + SUBJECT[key] + ", " + icons.SCHOOL.get(school, "") + ". " + krea.STYLE
    outs = krea.i2i(p, prompt, denoise=denoise, seed=seed, n=n, tag=f"em_{key}_{int(denoise * 100)}", out=RAW)
    return outs, a


def paint_many(keys, denoise=0.5, seed=1200, n=3):
    """All their paintings in one queued graph (the GPU is shared: one place in the queue)."""
    import krea
    import icons
    jobs = []
    for k in keys:
        p, a, school = make_guide(k)
        prompt = LOOK + SUBJECT[k] + ", " + icons.SCHOOL.get(school, "") + ". " + krea.STYLE
        jobs.append((f"em_{k}_{int(denoise * 100)}", p, prompt, denoise, seed))
    return krea.i2i_many(jobs, n=n, out=RAW)


def fit(key, src, dst=None):
    import icons
    a = np.load(os.path.join(RAW, f"{key}_mask.npy"))
    img = Image.open(src)
    if img.size[0] != N:
        a = cv2.resize(a, img.size, interpolation=cv2.INTER_AREA)
    # The guide's silhouette, a little grown so the painting's own edge is kept.
    m = cv2.dilate(a, np.ones((3, 3), np.uint8), iterations=max(1, img.size[0] // 512))
    dst = dst or os.path.join(UI, key + ".png")
    return icons.fit(src, dst, mask=m)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--guides":
        for k in args[1:] or list(DESIGNS):
            print(make_guide(k)[0])
    elif args and args[0] == "--many":
        for k, v in paint_many(args[1:] or list(DESIGNS)).items():
            print(k, len(v))
    else:
        for k in args or list(DESIGNS):
            print(k, paint(k)[0])
