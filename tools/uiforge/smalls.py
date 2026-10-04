"""Small painted frames (slots, the skill socket, chips, toasts, pills, buttons,
tooltips, tabs, paper, the hint, the map's frame): painted over guides2 on
the local Krea at four to sixteen times their shown size, then fitted here.
"""
from __future__ import annotations

import cv2
import numpy as np

import cut as C
import forge as F
import nineslice as N
import painted as P


def fit(src, dst, size, margins, strap, tone=None, tile=False, keep=0.45, grade=True, darken=1.0, mask=None,
        solid_inside=True, sigma=None, holes=None, hole_kind=("#4a1a0a", "#ff8a3a"), hole_light=0.45, crop=False):
    """size: file px (W, H); margins: shown px (L, T, R, B); strap: shown px from the edge to
    the border's inner edge (the middle beyond it is calmed to `tone`). crop: the painting
    holds the piece with room round it (a text-to-image result): cut to the piece first."""
    W, H = size
    big = P.load(src)
    mbig = C.birefnet_mask(src) if mask is None else mask
    if crop:
        ys, xs = np.nonzero(mbig > 0.5)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        big, mbig = big[y0:y1, x0:x1], mbig[y0:y1, x0:x1]
    rgb = cv2.resize(big, (W, H), interpolation=cv2.INTER_AREA)
    m = cv2.resize(mbig, (W, H), interpolation=cv2.INTER_AREA)
    a = P.silhouette(m)
    if solid_inside:
        s2 = int(strap * 2 * 0.6)
        a[s2:H - s2, s2:W - s2] = 1
    if grade:
        rgb = C.grade(np.dstack([rgb, a]))[..., :3]
    if darken != 1.0:
        rgb = F.lin_to_srgb(F.srgb_to_lin(rgb) * darken)
    if tone:
        s2 = int(strap * 2)
        region = np.zeros((H, W), np.float32)
        region[s2:H - s2, s2:W - s2] = 1
        rgb = P.calm(rgb, region, tone, keep=keep, low=0.03, sigma=sigma or max(2, min(W, H) / 40), feather=2)
    if holes:
        hm = np.zeros((H, W), np.float32)
        lum = rgb.mean(axis=2)
        for (cx, cy, r) in holes:
            yy, xx = np.mgrid[0:H, 0:W]
            hm = np.maximum(hm, ((np.hypot(xx - cx, yy - cy) < r) & (lum < 0.14)).astype(np.float32))
        rgb = P.ember_holes(rgb, hm, hole_light, *hole_kind)
    img = np.dstack([rgb, a])
    if tile:
        img = N.tileable(img, tuple(v * 2 for v in margins), blend=max(4, min(W, H) // 24))
    P.save_rgba(img[..., :3], img[..., 3], dst)
    return img
