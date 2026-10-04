"""Fitting painted pieces (raw Krea results) into the files the game loads.

Every painted piece is cleaned here, never shipped raw: its silhouette cut
(BiRefNet, holes filled), its middle calmed where text sits (the painterly
blotches taken out, the brush texture kept), pieces that would collide with
what the code draws moved or removed, the light under the coins' holes set
to the house ember, and the house grade applied.
"""
from __future__ import annotations

import math
import os

import cv2
import numpy as np
from PIL import Image

import cut as C
import forge as F


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), np.float32) / 255


def silhouette(mask, thr=0.5):
    """Alpha from a BiRefNet mask: everything enclosed by the frame filled, the outer edge soft."""
    m = (mask > thr).astype(np.uint8)
    # Everything reachable from the border through background is outside.
    n, lab = cv2.connectedComponents((1 - m).astype(np.uint8), connectivity=4)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    border = border[border > 0]
    out = np.isin(lab, border)
    return np.where(out, mask, 1.0).astype(np.float32)


def calm(rgb, region, tone, keep=0.45, low=0.08, sigma=10, feather=8):
    """Inside `region` (0..1): the large blotches replaced by an even `tone` (sRGB hex),
    the brush texture kept at `keep`, a whisper (`low`) of the original's large forms."""
    lin = F.srgb_to_lin(rgb)
    b = np.dstack([cv2.GaussianBlur(lin[..., i], (0, 0), sigma) for i in range(3)])
    detail = lin - b
    t = F.hexc(tone)
    target = t + detail * keep * (t.mean() / max(b.mean(), 1e-4)) ** 0.5 + (b - b.mean(axis=(0, 1))) * low
    r = cv2.GaussianBlur(region.astype(np.float32), (0, 0), feather)[..., None] if feather else region[..., None]
    out = lin * (1 - r) + np.clip(target, 0, None) * r
    return F.lin_to_srgb(out)


def ember_holes(rgb, holes, strength=0.6, deep="#4a1a0a", hot="#ff8a3a"):
    """The coins' holes lit from beneath: dark, with a dull ember deep in them, a hot
    point at the middle (asleep: never a flat fill, which reads as a sign)."""
    lin = F.srgb_to_lin(rgb)
    h = cv2.GaussianBlur(holes.astype(np.float32), (0, 0), 1.0)
    inner = cv2.erode(holes.astype(np.float32), np.ones((3, 3), np.uint8), iterations=2)
    core = cv2.GaussianBlur(inner, (0, 0), 2.5)
    deep = F.hexc(deep)
    hot = F.hexc(hot)
    lin = lin * (1 - h[..., None] * 0.8) + (h[..., None] * deep * 0.25 + (core ** 4)[..., None] * hot * 0.45) * strength
    return F.lin_to_srgb(lin)


def heal(rgb, region, prompt, denoise=0.5, seed=77, pad=96, tag="heal", feather=6):
    """Let the Krea repaint a region (a seam, a removed piece's ghost) in the painting's own
    hand: the box round it painted over at `denoise`, laid back through a feathered mask."""
    import os
    import krea
    ys, xs = np.nonzero(region > 0.5)
    if len(xs) == 0:
        return rgb
    h, w = region.shape
    x0, x1 = max(0, xs.min() - pad), min(w, xs.max() + pad)
    y0, y1 = max(0, ys.min() - pad), min(h, ys.max() + pad)
    crop = rgb[y0:y1, x0:x1]
    # The Krea likes sizes in 16s and about a megapixel: scale the crop up to it.
    k = max(1.0, 768 / max(crop.shape[:2]))
    cw, ch = int(round(crop.shape[1] * k / 16)) * 16, int(round(crop.shape[0] * k / 16)) * 16
    big = cv2.resize(crop, (cw, ch), interpolation=cv2.INTER_CUBIC)
    os.makedirs(os.path.join(krea.OUT, "heal"), exist_ok=True)
    gpath = os.path.join(krea.OUT, "heal", f"guide_{tag}_{seed}.png")
    Image.fromarray((np.clip(big, 0, 1) * 255).astype(np.uint8)).save(gpath)
    out = krea.i2i(gpath, prompt, denoise=denoise, seed=seed, n=1, tag=f"heal_{tag}", out=os.path.join(krea.OUT, "heal"), front=True)
    painted = np.asarray(Image.open(out[0]).convert("RGB"), np.float32) / 255
    painted = cv2.resize(painted, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    m = cv2.GaussianBlur(cv2.dilate(region[y0:y1, x0:x1].astype(np.float32), np.ones((5, 5), np.uint8)), (0, 0), feather)[..., None]
    m = np.clip(m * 1.5, 0, 1)
    res = rgb.copy()
    res[y0:y1, x0:x1] = crop * (1 - m) + painted * m
    return res


def paste(dst_rgb, dst_a, piece_rgba, cx, cy, size, shadow=4):
    """A cut piece (RGBA float) scaled to `size` (its larger side) and laid centred at (cx, cy)."""
    ph, pw = piece_rgba.shape[:2]
    k = size / max(ph, pw)
    nw, nh = max(1, int(round(pw * k))), max(1, int(round(ph * k)))
    small = cv2.resize(piece_rgba, (nw, nh), interpolation=cv2.INTER_AREA)
    x0, y0 = int(round(cx - nw / 2)), int(round(cy - nh / 2))
    H, W = dst_a.shape
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + nw), min(H, y0 + nh)
    if xb <= xa or yb <= ya:
        return dst_rgb, dst_a
    s = small[ya - y0:yb - y0, xa - x0:xb - x0]
    a = s[..., 3:4]
    if shadow:
        sh = np.zeros((H, W), np.float32)
        sx, sy = int(shadow * 0.5), int(shadow * 0.8)
        xa2, ya2, xb2, yb2 = min(W, xa + sx), min(H, ya + sy), min(W, xb + sx), min(H, yb + sy)
        sh[ya2:yb2, xa2:xb2] = a[: yb2 - ya2, : xb2 - xa2, 0]
        sh = cv2.GaussianBlur(sh, (0, 0), shadow * 0.6) * 0.7
        dst_rgb = dst_rgb * (1 - sh[..., None])
        dst_a = np.maximum(dst_a, sh * 0.8)
    region = dst_rgb[ya:yb, xa:xb]
    dst_rgb[ya:yb, xa:xb] = region * (1 - a) + s[..., :3] * a
    dst_a[ya:yb, xa:xb] = np.maximum(dst_a[ya:yb, xa:xb], a[..., 0])
    return dst_rgb, dst_a


def piece(rgb, mask, box):
    """A piece of a painting (x0, y0, x1, y1) as RGBA, alpha from the mask."""
    x0, y0, x1, y1 = box
    return np.dstack([rgb[y0:y1, x0:x1], mask[y0:y1, x0:x1]]).astype(np.float32)


def save_rgba(rgb, a, path):
    F.save(F.to_pil(np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])), path)
