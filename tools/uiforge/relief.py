"""Reliefs: pieces modelled as a height field in numpy and rendered in Blender
(blender_relief.py) under the house light. For what is seen straight on and must be
exact: the medallions, the logo's letters, emblems.

A piece is drawn on a `Relief` at its render resolution (file px x ss): its height (render
px), a material per pixel (iron, gold, ember, stone ...), its coverage, and any light of its
own. `Relief.paint()` turns the materials into albedo, metalness and roughness with the
wear of use (bright on the edges the hand rubs, grime in the hollows); `render()` lights it.
"""
from __future__ import annotations

import os
import subprocess

import cv2
import numpy as np
from PIL import Image

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BLENDER = os.environ.get("BLENDER", r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe")
CACHE = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "relief")

# Materials: albedo (sRGB hex), metalness, roughness, worn albedo (the rubbed edges), wear amount.
MATS = {
    "iron": ("#1c1922", 0.85, 0.50, "#9a96a4", 0.9),
    "iron_dark": ("#141118", 0.7, 0.55, "#4a4652", 0.4),
    "chain": ("#34303a", 0.9, 0.34, "#c4c0cc", 1.0),
    "gold": ("#c9a256", 1.0, 0.30, "#f4dca0", 0.6),
    "gold_dim": ("#8a6a36", 1.0, 0.42, "#c9a256", 0.5),
    "soot": ("#0c0a0e", 0.2, 0.8, "#1a161c", 0.0),
    "stone": ("#3a0608", 0.0, 0.12, "#7a1a18", 0.3),
    "bone": ("#b8ab90", 0.0, 0.55, "#e6dcc4", 0.4),
    "ember": ("#2a0c04", 0.0, 0.7, "#2a0c04", 0.0),
    "glass": ("#000000", 0.0, 0.03, "#000000", 0.0),
    "leather": ("#3a1a12", 0.0, 0.55, "#6a3e2a", 0.6),
    "silk": ("#ece4d2", 0.0, 0.32, "#f6f0e2", 0.0),
    "paper": ("#d2ccbc", 0.0, 0.92, "#e2dccc", 0.0),
}
IDS = {k: i for i, k in enumerate(MATS)}


class Relief:
    def __init__(self, W, H, ss=8):
        """W, H in file px; everything below is at render resolution (W*ss, H*ss)."""
        self.fw, self.fh, self.ss = W, H, ss
        self.w, self.h = W * ss, H * ss
        self.height = np.zeros((self.h, self.w), np.float32)
        self.mat = np.zeros((self.h, self.w), np.int32)
        self.alpha = np.zeros((self.h, self.w), np.float32)
        self.emit = np.zeros((self.h, self.w, 3), np.float32)
        self.tint = np.ones((self.h, self.w, 3), np.float32)
        self.shape_height = None
        self.xx, self.yy = F.grid(self.h, self.w)

    def px(self, v):
        """File px to render px."""
        return v * self.ss

    def polar(self, cx, cy):
        """Radius (file px) and angle (0 at the top, clockwise) about a file-px centre."""
        dx = self.xx / self.ss - cx
        dy = self.yy / self.ss - cy
        return np.hypot(dx, dy), np.arctan2(dx, -dy)

    def put(self, mask, height=None, mat=None, mode="max"):
        """Lay a part: where `mask` (0..1) covers, the height is raised to (max) or set to the
        part's height, and the material becomes the part's."""
        m = np.clip(mask, 0, 1).astype(np.float32)
        if height is not None:
            if mode == "max":
                self.height = np.where(m > 0.5, np.maximum(self.height, height), self.height)
            elif mode == "set":
                self.height = self.height * (1 - m) + height * m
            elif mode == "add":
                self.height = self.height + height * m
        if mat is not None:
            self.mat = np.where(m > 0.5, IDS[mat], self.mat)
        self.alpha = np.maximum(self.alpha, m)

    def paint(self, wear=1.0, grime=1.0, seed=0, grain=1.0):
        """Albedo, metalness and roughness from the materials, worn by the relief's shape."""
        ss = self.ss
        # Wear and grime follow the piece's forms, not its hammer marks (shape_height, when set).
        src = self.shape_height if getattr(self, "shape_height", None) is not None else self.height
        # Curvature in file px (heights and distances are in render px: h'' scales as 1/ss), so
        # a piece wears the same at any supersampling.
        hb = cv2.GaussianBlur(src, (0, 0), 0.8 * ss)
        curv = cv2.Laplacian(hb, cv2.CV_32F, ksize=3) * ss
        convex = np.clip(-curv * 1.2, 0, 1)           # rubbed bright
        cavity = np.clip(curv * 0.8, 0, 1)            # grime settles
        n1 = F.fbm(self.h, self.w, scale=self.w / 6, octaves=4, seed=seed)
        n2 = F.fbm(self.h, self.w, scale=self.w / 40, octaves=3, seed=seed + 1)
        base = np.zeros((self.h, self.w, 3), np.float32)
        metal = np.zeros((self.h, self.w), np.float32)
        rough = np.zeros((self.h, self.w), np.float32)
        for name, i in IDS.items():
            sel = self.mat == i
            if not sel.any():
                continue
            col, mt, rg, worn, wr = MATS[name]
            w_ = np.clip(convex * wear * wr * (0.7 + 0.6 * n2), 0, 1)
            c = F.hexc(col) * (1 - w_[..., None]) + F.hexc(worn) * w_[..., None]
            # Paper and glass are even: no blotches (their grain is in their own maps).
            g_ = grain * (0.1 if name in ("paper", "glass", "silk") else 1.0)
            c = c * (1 + 0.25 * n1[..., None] * g_)
            base[sel] = c[sel]
            metal[sel] = mt
            rough[sel] = np.clip(rg + 0.12 * n2 * grain - 0.22 * w_, 0.04, 1)[sel]
        g = np.clip(cavity * grime * (0.7 + 0.5 * n1), 0, 0.85)
        base *= (1 - g[..., None])
        rough = np.clip(rough + g * 0.3, 0, 1)
        base *= self.tint
        return base, metal, rough

    def render(self, name, samples=128, **paint):
        base, metal, rough = self.paint(**paint)
        os.makedirs(CACHE, exist_ok=True)
        npz = os.path.join(CACHE, name + ".npz")
        out = os.path.join(CACHE, name + ".png")
        np.savez(npz, height=self.height, alpha=self.alpha, base=base, metal=metal, rough=rough, emit=self.emit)
        r = subprocess.run([BLENDER, "-b", "-P", os.path.join(HERE, "blender_relief.py"), "--", npz, out, str(samples)],
                           capture_output=True, text=True, timeout=1800)
        if not os.path.exists(out) or "Traceback" in r.stdout + r.stderr:
            raise RuntimeError((r.stdout + r.stderr)[-3000:])
        img = np.asarray(Image.open(out).convert("RGBA"), np.float32) / 255
        return img  # render resolution, straight alpha

    def file_size(self, img):
        return F.downsample(img, (self.fw, self.fh))


# ------------------------------------------------------------- shaping --

def hammered(R: Relief, cell=6.0, depth=0.5, seed=0):
    """Hammer dents over the whole canvas (file px cell, render px depth per file px)."""
    return F.worley_dents(R.h, R.w, cell=cell * R.ss, depth=depth * R.ss, seed=seed)


def ragged(theta, amount=1.0, seed=0, lobes=(7, 13, 29, 61)):
    """An edge that wanders round a circle (file px), as drawn-out iron's does."""
    rng = np.random.default_rng(seed)
    out = np.zeros_like(theta)
    for i, k in enumerate(lobes):
        out += np.sin(theta * k + rng.uniform(0, 6.283)) * amount / (1.6 ** i)
    return out


def rope(R: Relief, cx, cy, radius, thick, pitch, height, turns=None):
    """A two-strand twisted wire laid round a circle (file px). Returns (height, mask) at
    render res: each strand a round ridge crossing the centre line at a slant."""
    r, th = R.polar(cx, cy)
    L = 2 * np.pi * radius
    n = turns or max(3, int(round(L / pitch)))
    s = th / (2 * np.pi) * n  # turns along the wire
    d = r - radius            # across the wire (file px)
    hw = thick / 2
    hgt = np.zeros_like(r)
    for k in (0.0, 0.5):
        # Strand phase: where across the wire this strand sits at each point along it.
        ph = (s + k) % 1.0
        # A slanted strand: distance across a 45-degree twisted band.
        u = ((d / thick) - (ph - 0.5)) % 1.0 - 0.5  # repeats every strand pitch
        prof = np.sqrt(np.clip(1 - (u / 0.5) ** 2, 0, 1))
        hgt = np.maximum(hgt, prof)
    inside = np.clip((hw - np.abs(d)) * R.ss + 0.5, 0, 1)
    edge = np.sqrt(np.clip(1 - (d / hw) ** 2, 0, 1))
    return (hgt * 0.55 + edge * 0.45) * height * R.ss * inside, inside


def coin(R: Relief, x, y, size, base, hole=0.34, thick=None, rot=45.0):
    """The binders' square coin set on its point (file px), a round hole through it with a
    raised lip. Returns (height in file px, coin mask, hole mask) at render res; the caller
    lays them (max) and lights the hole."""
    X, Y = R.xx / R.ss, R.yy / R.ss
    a = math.radians(rot)
    u = (X - x) * math.cos(a) + (Y - y) * math.sin(a)
    v = -(X - x) * math.sin(a) + (Y - y) * math.cos(a)
    half = size / 2
    # A square with slightly rounded corners, its faces bevelled toward the edges.
    rc = size * 0.08
    qx, qy = np.abs(u) - (half - rc), np.abs(v) - (half - rc)
    sd = -(np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rc)
    th = thick if thick is not None else size * 0.16
    bev = size * 0.12
    face = np.clip(sd / bev, 0, 1)
    face = np.sqrt(1 - (1 - face) ** 2)
    d = np.hypot(X - x, Y - y)
    hr = size * hole / 2
    lip = np.exp(-((d - hr * 1.25) / (size * 0.05)) ** 2) * size * 0.05
    h = base + th * face + lip
    mask = np.clip(sd * R.ss + 0.5, 0, 1)
    hole_m = np.clip((hr - d) * R.ss + 0.5, 0, 1)
    h = np.where(hole_m > 0.5, base - th * 0.5, h)
    return h, mask, hole_m


def bar(R: Relief, pts, w0, w1, flat=True):
    """A drawn bar of iron along a polyline (file px), `w0` wide at its start tapering to `w1`.
    Returns (height in file px above what it lies on, mask) at render res. Flat on top like
    drawn strap iron (flat=True) or round like a rod."""
    X, Y = R.xx / R.ss, R.yy / R.ss
    pts = np.asarray(pts, np.float32)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    widths = w0 + (w1 - w0) * cum / max(cum[-1], 1e-6)
    best = np.full(X.shape, 1e9, np.float32)
    wbest = np.full(X.shape, w1, np.float32)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        ex_, ey_ = bx - ax, by - ay
        tt = np.clip(((X - ax) * ex_ + (Y - ay) * ey_) / (ex_ * ex_ + ey_ * ey_ + 1e-9), 0, 1)
        d = np.hypot(X - ax - ex_ * tt, Y - ay - ey_ * tt)
        w = widths[i] + (widths[i + 1] - widths[i]) * tt
        closer = d < best
        best = np.where(closer, d, best)
        wbest = np.where(closer, w, wbest)
    half = wbest / 2
    m = np.clip((half - best) * R.ss + 0.5, 0, 1)
    prof = np.sqrt(np.clip(1 - (best / np.maximum(half, 0.1)) ** 2, 0, 1))
    if flat:
        prof = np.minimum(1.0, 1.7 * prof)
    return (prof * half * 0.9 * (m > 0)).astype(np.float32), m


import math  # noqa: E402


def save_file(img, path):
    F.save(F.to_pil(img), path)
