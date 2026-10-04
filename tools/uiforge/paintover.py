"""The paint-over: a Blender render (exact geometry, the house light) given the hand
of the rest of the interface on the local Krea (darkbrush LoRA, img2img at a low
denoise), then put back on the render's own silhouette, so nothing moves:

  1. the render composited on black, upscaled to about a megapixel;
  2. img2img at `denoise` (0.25-0.4: the paint follows the forms, adds hammer
     marks, grime and brushwork, invents nothing);
  3. the painting's light laid over the render's: its detail (high frequencies)
     and colour, the render's large shading (so the light stays one light) and
     the render's alpha exactly;
  4. back to the file size.
"""
from __future__ import annotations

import os

import cv2
import numpy as np
from PIL import Image

import forge as F
import krea

OUT = os.path.join(krea.OUT, "paintover")


def paint(rgba, prompt, name, denoise=0.32, seed=1, target=1024, detail=1.0, keep_light=0.6, n=1, pick=0, protect=None):
    """rgba: float (H, W, 4) at file size. Returns float RGBA at file size."""
    os.makedirs(OUT, exist_ok=True)
    H, W = rgba.shape[:2]
    k = target / max(W, H)
    bw, bh = int(round(W * k / 16)) * 16, int(round(H * k / 16)) * 16
    on_black = rgba[..., :3] * rgba[..., 3:4]
    big = cv2.resize(on_black, (bw, bh), interpolation=cv2.INTER_CUBIC)
    guide = os.path.join(OUT, f"{name}_guide.png")
    Image.fromarray((np.clip(big, 0, 1) * 255 + 0.5).astype(np.uint8)).save(guide)
    outs = krea.i2i(guide, prompt + ". " + krea.STYLE, denoise=denoise, seed=seed, n=n, tag=f"po_{name}", out=OUT)
    painted = np.asarray(Image.open(outs[pick]).convert("RGB"), np.float32) / 255
    painted = cv2.resize(painted, (W, H), interpolation=cv2.INTER_AREA)
    base = rgba[..., :3]
    a = rgba[..., 3:4]
    # Un-premultiply the painting against the render's alpha at the soft edges.
    painted = np.where(a > 0.05, np.clip(painted / np.maximum(a, 0.05), 0, 1), base)
    # Large shading from the render (one light), detail and hue from the painting.
    s = max(2.0, min(W, H) / 64)
    lb = cv2.GaussianBlur(F.srgb_to_lin(base), (0, 0), s)
    lp = cv2.GaussianBlur(F.srgb_to_lin(painted), (0, 0), s)
    lin_p = F.srgb_to_lin(painted)
    mixed = lin_p * (1 - keep_light) + (lin_p / np.maximum(lp, 1e-4) * lb) * keep_light
    detail_only = lin_p - lp
    mixed = mixed + detail_only * (detail - 1.0)
    rgb = F.lin_to_srgb(np.clip(mixed, 0, 1))
    if protect is not None:
        # Where a piece is too small for the painting to keep (a link, a stone), the render stays.
        m = cv2.GaussianBlur(protect.astype(np.float32), (0, 0), 1.5)[..., None]
        rgb = rgb * (1 - m) + base * m
    out = np.dstack([rgb, rgba[..., 3]])
    return out.astype(np.float32)
