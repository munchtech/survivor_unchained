"""The plates every screen sits on (frames/plate.png and its kin), painted over
guides.plate_guide at twice their file size, then fitted here: halved, the
middle calmed to the tone the text was chosen for, the coins' holes lit from
beneath, and made to tile (nineslice.tileable) so the strap repeats along a
plate of any size without a seam.
"""
from __future__ import annotations

import cv2
import numpy as np

import cut as C
import forge as F
import nineslice as N
import painted as P


def fit(src, dst, size=(512, 512), out=12, corner=64, strap_in=64, tone="#16131a", hole_r=9, hole_light=0.5,
        keep=0.45, grade=True, mask=None):
    """size: file px; out, corner: shown px (the slice margin is `corner`, of which `out`
    lies past the control); strap_in: file px from the file's edge to the strap's inner edge."""
    W, H = size
    rgb_big = P.load(src)
    mask_big = C.birefnet_mask(src) if mask is None else mask
    rgb = cv2.resize(rgb_big, (W, H), interpolation=cv2.INTER_AREA)
    mask = cv2.resize(mask_big, (W, H), interpolation=cv2.INTER_AREA)
    a = P.silhouette(mask)
    if grade:
        # The house grade first: the calm middle is then set to its tone exactly.
        rgb = C.grade(np.dstack([rgb, a]))[..., :3]
    o = out * 2
    body = np.zeros((H, W), np.float32)
    body[o + 6:H - o - 6, o + 6:W - o - 6] = 1
    a = np.maximum(a, body)
    # The middle, calm.
    region = np.zeros((H, W), np.float32)
    region[strap_in:H - strap_in, strap_in:W - strap_in] = 1
    rgb = P.calm(rgb, region, tone, keep=keep, low=0.04, sigma=7, feather=2)
    # The coins' holes at the four corners.
    holes = np.zeros((H, W), np.float32)
    c = corner * 2
    for (x0, y0) in ((0, 0), (W - c, 0), (0, H - c), (W - c, H - c)):
        sub_m = mask[y0:y0 + c, x0:x0 + c]
        sub_l = rgb[y0:y0 + c, x0:x0 + c].mean(axis=2)
        # The coin sits on the corner point (o, o) from the file's corner.
        px = o if x0 == 0 else c - o
        py = o if y0 == 0 else c - o
        yy, xx = np.mgrid[0:c, 0:c]
        rr = np.hypot(xx - px, yy - py)
        hole = (rr < hole_r) & (sub_l < 0.12) & (sub_m > 0.3)
        holes[y0:y0 + c, x0:x0 + c] = np.maximum(holes[y0:y0 + c, x0:x0 + c], hole)
    rgb = P.ember_holes(rgb, holes, hole_light)
    img = np.dstack([rgb, a])
    img = N.tileable(img, (c, c, c, c), blend=12)
    P.save_rgba(img[..., :3], img[..., 3], dst)
    return img
