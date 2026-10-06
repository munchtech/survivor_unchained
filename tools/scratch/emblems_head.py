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


