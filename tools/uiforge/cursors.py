"""The pointer (cursors/*.png, 32 by 32, shown as drawn): forged, not drawn.
The arrow is a strap's spear end in blackened iron with its lit edge in gold;
the hand an iron gauntlet's pointing finger; the refusal an iron ring barred
in blood. Each has a dark rim a pixel wide so it holds on bright cobbles and
on black plates alike.
"""
from __future__ import annotations

import os

import cv2
import numpy as np

import forge as F
import svgglyph as G

POINTER = "M3 2 L3 24.5 L8.6 19.4 L12.6 28.6 L16.6 26.8 L12.7 17.8 L20.4 17.8 Z"
HAND = ("M11 1.6 C12.5 1.6 13.4 2.6 13.4 4.1 L13.4 12.2 C14.1 11 16.6 11 17.1 12.7 C17.7 11.6 20.1 11.6 20.6 13.3 "
        "C21.3 12.5 23.6 12.9 23.6 14.7 L23.6 21.2 C23.6 25.4 21.1 29.2 16.6 29.2 L13.1 29.2 C10.6 29.2 9.1 27.7 7.9 25.7 "
        "L4.3 19.6 C3.5 18.1 4.7 16.7 6.1 17.4 L8.6 19.6 L8.6 4.1 C8.6 2.6 9.5 1.6 11 1.6 Z")
HAND_CUTS = ["M13.4 12.4 L13.4 17.5", "M17.1 12.8 L17.1 17.5", "M20.6 13.4 L20.6 17.5"]


def _poly_mask(d, S, unit):
    m = np.zeros((S, S), np.uint8)
    for pts, closed in G.subpaths(d):
        P = np.round(np.asarray(pts) * unit * 16).astype(np.int32)
        cv2.fillPoly(m, [P], 255, cv2.LINE_AA, shift=4)
    return m.astype(np.float32) / 255


def _line_mask(d, S, unit, w):
    m = np.zeros((S, S), np.uint8)
    for pts, closed in G.subpaths(d):
        P = np.round(np.asarray(pts) * unit * 16).astype(np.int32)
        cv2.polylines(m, [P], closed, 255, max(1, int(w * unit)), cv2.LINE_AA, shift=4)
    return m.astype(np.float32) / 255


def _forge(mask, S, mat="pewter", gold_edge=True, cuts=None):
    d = cv2.distanceTransform((mask > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    h = np.sqrt(np.clip(d / (S * 0.05), 0, 1)) * S * 0.03
    s = F.Surface(S, S)
    s.height = h.astype(np.float32)
    s.paint(np.ones((S, S), np.float32), mat)
    if cuts is not None:
        s.height -= cuts * S * 0.02
    if gold_edge:
        # The edges facing the light, gilded: where the bevel faces up and left.
        gy, gx = np.gradient(h)
        lit = np.clip((gx + gy) / (np.abs(gx) + np.abs(gy) + 1e-4), 0, 1) * (d < S * 0.04) * (mask > 0.5)
        s.paint(lit.astype(np.float32), "gold")
    lin = s.shade(normal_strength=1.0, ao=0.4, shadow=0.0) * 1.9
    srgb = F.lin_to_srgb(np.clip(lin, 0, 1))
    return srgb


def _finish(rgb, mask, S, size=32, rim=True):
    img = np.dstack([rgb, mask])
    small = F.downsample(img, (size, size))
    if rim:
        a = small[..., 3]
        grown = cv2.dilate((a * 255).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32) / 255
        rim_a = np.clip(grown - a, 0, 1)
        dark = np.array([0.04, 0.03, 0.05], np.float32)
        out_a = a + rim_a * 0.9 * (1 - a)
        rgb2 = (small[..., :3] * a[..., None] + dark * (rim_a * 0.9 * (1 - a))[..., None]) / np.maximum(out_a[..., None], 1e-4)
        small = np.dstack([rgb2, out_a])
    return F.to_pil(small)


def pointer(size=32, ss=8):
    S = size * ss
    m = _poly_mask(POINTER, S, ss)
    return _finish(_forge(m, S), m, S, size)


def hand(size=32, ss=8):
    S = size * ss
    m = _poly_mask(HAND, S, ss)
    cuts = np.zeros((S, S), np.float32)
    for c in HAND_CUTS:
        cuts = np.maximum(cuts, _line_mask(c, S, ss, 0.9))
    rgb = _forge(m, S, cuts=cuts)
    rgb = rgb * (1 - cuts[..., None] * 0.6)
    return _finish(rgb, m, S, size)


def forbidden(size=32, ss=8):
    S = size * ss
    xx, yy = F.grid(S, S)
    c = S / 2
    r = np.hypot(xx - c, yy - c)
    ring = F.coverage(np.minimum(S * 0.40 - r, r - S * 0.27), 1.0)
    u = ((xx - c) + (yy - c)) / np.sqrt(2)
    bar = F.coverage(np.minimum(S * 0.07 - np.abs(((xx - c) - (yy - c)) / np.sqrt(2)), S * 0.30 - np.abs(u)), 1.0)
    m = np.maximum(ring, bar)
    s = F.Surface(S, S)
    d = cv2.distanceTransform((m > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    s.height = (np.sqrt(np.clip(d / (S * 0.04), 0, 1)) * S * 0.03).astype(np.float32)
    s.paint(np.ones((S, S), np.float32), "iron")
    s.paint(bar, F.Mat(tuple(F.hexc("#c8323a")), 0.3, 0.3))
    s.paint(ring * 0.6, F.Mat(tuple(F.hexc("#a8281e")), 0.6, 0.35))
    lin = s.shade(normal_strength=1.0, ao=0.4, shadow=0.0) * 1.4
    return _finish(F.lin_to_srgb(np.clip(lin, 0, 1)), m, S, size)


def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    made = {"pointer": pointer(), "hand": hand(), "forbidden": forbidden()}
    for k, im in made.items():
        F.save(im, os.path.join(out_dir, k + ".png"))
    return made
