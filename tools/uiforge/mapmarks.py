"""The map's marks (icons/map/KIND.png): ink on a small disc of parchment, as a
Waystation clerk would mark a map, so they read on the paper of the big map
and on the dark of the minimap alike. Each keeps its hue (the legend and
the code use it) and has its own shape (never hue alone).
"""
from __future__ import annotations

import math
import os

import numpy as np

import forge as F

INK = {"quest": "#a8321e", "turn": "#a8321e", "danger": "#6a1a10", "mystery": "#5a3a7a",
       "exit": "#2a4a3a", "person": "#3a2414", "place": "#3a2414"}


def _cov(sd):
    return F.coverage(sd, 1.0)


def symbol(kind, xx, yy, c, R):
    """The ink shape (signed distance, positive inside) for a kind, centred at c, radius R."""
    x, y = xx - c, yy - c
    if kind == "quest":
        bar = F.sd_poly(xx, yy, [(c - R * 0.17, c - R * 0.62), (c + R * 0.17, c - R * 0.62), (c + R * 0.09, c + R * 0.18), (c - R * 0.09, c + R * 0.18)])
        dot = F.sd_circle(xx, yy, c, c + R * 0.45, R * 0.15)
        return np.maximum(bar, dot)
    if kind == "turn":
        # A pennant on a staff: the next step.
        staff = F.sd_box(xx, yy, c - R * 0.32, c + R * 0.02, R * 0.07, R * 0.62, R * 0.03)
        flag = F.sd_poly(xx, yy, [(c - R * 0.27, c - R * 0.60), (c + R * 0.52, c - R * 0.36), (c - R * 0.27, c - R * 0.08)])
        return np.maximum(staff, flag)
    if kind == "exit":
        # An arch, and the arrow going out through it.
        # A doorway (solid ink, round-headed) with the way out cut through it as an arrow.
        door = F.sd_box(xx, yy, c - R * 0.06, c + R * 0.05, R * 0.36, R * 0.55, R * 0.34)
        door = np.minimum(door, -(yy - (c + R * 0.58)))
        arrow = F.sd_poly(xx, yy, [(c + R * 0.02, c - R * 0.22), (c + R * 0.56, c + R * 0.12), (c + R * 0.02, c + R * 0.46)])
        shaft = F.sd_box(xx, yy, c - R * 0.16, c + R * 0.12, R * 0.20, R * 0.10, 0)
        cut = np.maximum(arrow, shaft)
        # The arrow itself in ink where it leaves the door, paper where it crosses it.
        return np.maximum(np.minimum(door, -cut), np.minimum(cut, -door))
    if kind == "danger":
        skull = np.maximum(F.sd_circle(xx, yy, c, c - R * 0.12, R * 0.48), F.sd_box(xx, yy, c, c + R * 0.30, R * 0.26, R * 0.22, R * 0.06))
        eyes = np.maximum(F.sd_circle(xx, yy, c - R * 0.19, c - R * 0.08, R * 0.13), F.sd_circle(xx, yy, c + R * 0.19, c - R * 0.08, R * 0.13))
        nose = F.sd_poly(xx, yy, [(c, c + R * 0.08), (c - R * 0.07, c + R * 0.2), (c + R * 0.07, c + R * 0.2)])
        teeth = np.maximum(F.sd_box(xx, yy, c - R * 0.09, c + R * 0.42, R * 0.025, R * 0.1, 0), F.sd_box(xx, yy, c + R * 0.09, c + R * 0.42, R * 0.025, R * 0.1, 0))
        return np.minimum(np.minimum(skull, -eyes), np.minimum(-nose, -teeth))
    if kind == "mystery":
        lid = np.minimum(F.sd_circle(xx, yy, c, c + R * 0.55, R * 0.9), F.sd_circle(xx, yy, c, c - R * 0.55, R * 0.9))
        ring = np.minimum(lid, -np.minimum(F.sd_circle(xx, yy, c, c + R * 0.55, R * 0.72), F.sd_circle(xx, yy, c, c - R * 0.55, R * 0.72)))
        pupil = F.sd_circle(xx, yy, c, c, R * 0.24)
        return np.maximum(ring, pupil)
    if kind == "person":
        head = F.sd_circle(xx, yy, c, c - R * 0.22, R * 0.24)
        body = np.minimum(F.sd_circle(xx, yy, c, c + R * 0.62, R * 0.50), -(yy - (c + R * 0.58)))
        return np.maximum(head, body)
    if kind == "place":
        # A gabled house with a lit window: a named place.
        roof = F.sd_poly(xx, yy, [(c, c - R * 0.62), (c + R * 0.58, c - R * 0.06), (c - R * 0.58, c - R * 0.06)])
        wall = F.sd_box(xx, yy, c, c + R * 0.24, R * 0.40, R * 0.32, 0)
        door = F.sd_box(xx, yy, c, c + R * 0.38, R * 0.11, R * 0.19, R * 0.05)
        return np.minimum(np.maximum(roof, wall), -door)
    raise KeyError(kind)


def mark(kind, size=64, ss=8, seed=0):
    S = size * ss
    xx, yy = F.grid(S, S)
    c = S / 2
    R = S * 0.47
    disc = F.sd_circle(xx, yy, c, c, R)
    rng_tex = F.fbm(S, S, scale=6 * ss, octaves=3, seed=seed + 11)
    blot = F.fbm(S, S, scale=2 * ss, octaves=2, seed=seed + 3)
    paper = F.hexc("#e8dcc0") * (1 + rng_tex[..., None] * 0.05)
    # Foxed, darker toward the rim.
    rim_dark = np.clip(1 - disc / (R * 0.35), 0, 1) ** 2
    paper = paper * (1 - rim_dark[..., None] * 0.35 * np.asarray([0.8, 0.9, 1.1], np.float32))
    ink = F.hexc(INK[kind])
    # The ink ring round the disc's edge and the symbol, the ink a little uneven.
    ring = _cov(R * 0.075 - np.abs(disc - R * 0.075))
    sym = _cov(symbol(kind, xx, yy, c, R * 0.92) + blot * ss * 0.25)
    inkm = np.maximum(ring, sym)
    density = 0.88 + 0.12 * blot
    col = paper * (1 - inkm[..., None] * density[..., None]) + ink * inkm[..., None] * density[..., None]
    # A dark hairline outside the disc so it holds on pale ground too.
    a = _cov(disc + 0.6 * ss)
    out = np.dstack([F.lin_to_srgb(np.clip(col, 0, 1)), a])
    return F.to_pil(F.downsample(out, (size, size)))


def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    made = {}
    for i, kind in enumerate(INK):
        made[kind] = mark(kind, seed=i)
        F.save(made[kind], os.path.join(out_dir, kind + ".png"))
    return made
