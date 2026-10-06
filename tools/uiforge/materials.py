"""Painted materials made into grounds: a Krea macro of a material (kit.MATERIALS) has its
painted light taken out (divided by its own heavy blur, so no vignette or hot spot is left),
is made exactly periodic (laid over itself shifted half a tile, each kept where the other
has its seam), and graded to the tone the kit holds the ground at.

    python tools/uiforge/materials.py goatskin 1 page/morocco.png "#221b19" 0.9
"""
from __future__ import annotations

import os
import sys

import cv2
import numpy as np
from PIL import Image

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "materials")
OUT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "kit")


def flatten(lin, sigma):
    """The material without the painting's light: each channel over its own heavy blur."""
    low = cv2.GaussianBlur(lin, (0, 0), sigma)
    return lin / np.maximum(low, 1e-4) * low.reshape(-1, 3).mean(0)


def seamless(img, border=0.18):
    """Exactly periodic: the picture and itself shifted half a tile, cross-faded so each is
    kept where the other has its seam (the edges, and the shifted one's middle)."""
    h, w = img.shape[:2]
    rolled = np.roll(np.roll(img, h // 2, 0), w // 2, 1)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = np.minimum(xx, w - 1 - xx) / (w * border)
    dy = np.minimum(yy, h - 1 - yy) / (h * border)
    wgt = np.clip(np.minimum(dx, dy), 0, 1)
    wgt = (wgt * wgt * (3 - 2 * wgt))[..., None]
    return img * wgt + rolled * (1 - wgt)


def ground(name, take, tone, contrast=1.0, size=1024, sigma=60):
    src = os.path.join(RAW, f"{name}_1400_{take}.png")
    img = np.asarray(Image.open(src).convert("RGB"), np.float32) / 255
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    lin = F.srgb_to_lin(img)
    lin = flatten(lin, sigma)
    lin = seamless(lin)
    # Its variation scaled about its mean, then held to the tone.
    m = lin.reshape(-1, 3).mean(0)
    lin = m + (lin - m) * contrast
    lin = np.clip(lin, 0, None) * (F.hexc(tone) / np.maximum(lin.reshape(-1, 3).mean(0), 1e-6))
    rgb = F.lin_to_srgb(np.clip(lin, 0, 1))
    return np.dstack([rgb, np.ones((size, size), np.float32)]).astype(np.float32)


if __name__ == "__main__":
    name, take, rel, tone = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    contrast = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
    img = ground(name, take, tone, contrast)
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    F.save(F.to_pil(img), p)
    print(p, img[..., :3].reshape(-1, 3).mean(0).round(3), img[..., :3].reshape(-1, 3).std(0).round(4))
