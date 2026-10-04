"""Round painted pieces: the level and heart medallions, the art's ring of
seven links, the minimap's rim. Cut, centred on their own circle, sized so
their rim lands where the code draws round them, middles calmed (the level
number sits there) or opened (the art's icon, its countdown and the
readiness arc show through), the house grade.
"""
from __future__ import annotations

import cv2
import numpy as np

import cut as C
import forge as F
import painted as P


def circle_of(mask, thr=0.5):
    """Centre and outer radius of a round piece from its mask."""
    m = (mask > thr).astype(np.uint8)
    ys, xs = np.nonzero(m)
    cy, cx = ys.mean(), xs.mean()
    # The outer radius: the 98th percentile of distances of the mask's pixels.
    r = np.percentile(np.hypot(ys - cy, xs - cx), 99.0)
    return cx, cy, r


def fit_round(src, size, rim_at=1.0, open_below=None, calm_below=None, calm_tone="#120e12", ember_rim=0.0,
              mask=None, grade=True, feather=0.012, extra=None):
    """A round piece at `size` (file px, square), its outer rim at `rim_at` of the half size.
    open_below: alpha 0 inside this share of the half size (soft edge).
    calm_below: the middle inside this share calmed to `calm_tone` (for a number on it)."""
    rgb = P.load(src)
    mask = C.birefnet_mask(src) if mask is None else mask
    cx, cy, r = circle_of(mask)
    # Crop the square round the circle with the rim where it should land.
    half = r / rim_at
    S = size
    # Sample by affine map: out pixel (u, v) -> src (cx + (u - S/2) * half/(S/2), ...)
    k = half / (S / 2)
    M = np.float32([[k, 0, cx - k * S / 2], [0, k, cy - k * S / 2]])
    # Supersample: work at 4x then area-filter.
    SS = S * 4
    M4 = np.float32([[k / 4, 0, cx - k * S / 2], [0, k / 4, cy - k * S / 2]])
    big = cv2.warpAffine(np.dstack([rgb, mask]), M4, (SS, SS), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    yy, xx = np.mgrid[0:SS, 0:SS].astype(np.float32)
    rr = np.hypot(xx - SS / 2 + 0.5, yy - SS / 2 + 0.5) / (SS / 2)
    a = P.silhouette(big[..., 3])
    # Solid inside its own rim (the mask can lose the dark middle).
    a = np.maximum(a, (rr < rim_at * 0.97).astype(np.float32))
    col = big[..., :3]
    if calm_below:
        reg = np.clip((calm_below - rr) / feather / 4, 0, 1)
        col = P.calm(col, reg, calm_tone, keep=0.35, low=0.04, sigma=12, feather=0)
    if ember_rim > 0 and calm_below:
        # A smoulder round the inside of the rim, brightest at the bottom (the ember settles).
        n = F.fbm(SS, SS, scale=SS / 10, octaves=3, seed=5)
        ring = np.exp(-((rr - calm_below + 0.02) / 0.035) ** 2) * np.clip(0.25 + 0.75 * (yy / SS - 0.35) * 1.8, 0, 1)
        ring = ring * np.clip(0.5 + n * 1.2, 0, 1.4)
        lin = F.srgb_to_lin(col) + ring[..., None] * (F.hexc("#ff6a1a") * 0.35 + F.hexc("#7a1c08") * 0.4) * ember_rim
        col = F.lin_to_srgb(lin)
    if open_below:
        a = a * np.clip((rr - open_below) / feather, 0, 1)
    a = a * np.clip((1.0 - rr) / 0.01, 0, 1)
    out = np.dstack([col, a])
    if extra:
        out = extra(out, rr)
    if grade:
        out = C.grade(out)
    return F.to_pil(F.downsample(out, (S, S)))
