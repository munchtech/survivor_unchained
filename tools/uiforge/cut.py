"""Cutting painted pieces from their black backgrounds, and the clean-up every
painted piece gets before it is fitted: alpha that holds the thing and its
glow, edges without a dark fringe, the house grade (blackened iron cooled
toward violet, gold kept warm, ember kept hot).
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
sys.path.insert(0, os.path.join(ROOT, "tools", "comfy"))
CACHE = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "_masks")


def birefnet_mask(path):
    """BiRefNet's mask for a picture (cached beside the raw results)."""
    os.makedirs(CACHE, exist_ok=True)
    key = os.path.join(CACHE, os.path.basename(os.path.dirname(path)) + "__" + os.path.basename(path))
    if os.path.exists(key) and os.path.getmtime(key) > os.path.getmtime(path):
        return np.asarray(Image.open(key).convert("L"), np.float32) / 255
    import comfy
    name = comfy.upload(path)
    api = {
        "1": {"class_type": "LoadImage", "inputs": {"image": name}},
        "2": {"class_type": "LoadBackgroundRemovalModel", "inputs": {"bg_removal_name": "birefnet.safetensors"}},
        "3": {"class_type": "RemoveBackground", "inputs": {"bg_removal_model": ["2", 0], "image": ["1", 0]}},
        "4": {"class_type": "MaskToImage", "inputs": {"mask": ["3", 0]}},
        "5": {"class_type": "SaveImage", "inputs": {"images": ["4", 0], "filename_prefix": "uiforge_mask"}},
    }
    out = comfy.run(api, CACHE)
    m = Image.open(out[0]).convert("L")
    img = Image.open(path)
    if m.size != img.size:
        m = m.resize(img.size, Image.LANCZOS)
    m.save(key)
    for f in out:
        if os.path.abspath(f) != os.path.abspath(key) and os.path.exists(f):
            os.remove(f)
    return np.asarray(m, np.float32) / 255


def light_alpha(rgb, black=0.035, full=0.16):
    """Alpha from how far a pixel stands out of a black ground (for glows and thin lines)."""
    v = rgb.max(axis=2)
    return np.clip((v - black) / (full - black), 0, 1)


def cutout(path, mode="mask+glow", grow=0.0, choke=0.0, black=0.035):
    """RGBA (float 0..1) of a painted piece on black.

    mask: BiRefNet only. glow: brightness only. mask+glow: the solid thing from the
    mask, its light (embers, glints) kept where the mask lost it."""
    img = np.asarray(Image.open(path).convert("RGB"), np.float32) / 255
    a = None
    if "mask" in mode:
        a = birefnet_mask(path)
        if choke > 0:
            a = np.clip((a - choke) / (1 - choke), 0, 1)
    if "glow" in mode:
        g = light_alpha(img, black=black)
        # Only warm light counts as glow outside the mask (embers), not grey smoke.
        r, gg, b = img[..., 0], img[..., 1], img[..., 2]
        warm = np.clip((r - b) * 4, 0, 1)
        g = g * (warm if a is not None else 1)
        a = g if a is None else np.maximum(a, g)
    # The solid thing keeps its painted colour (its dark edge is its own shading); light
    # outside it (a glow on black) is un-premultiplied so it stays bright over anything.
    rgb = img
    if "glow" in mode and "mask" in mode:
        m = birefnet_mask(path)
        glow_only = np.clip(a - m, 0, 1)[..., None] > 0.02
        rgb = np.where(glow_only, np.clip(img / np.maximum(a[..., None], 0.05), 0, 1), img)
    elif mode == "glow":
        rgb = np.clip(img / np.maximum(a[..., None], 0.05), 0, 1)
    return np.dstack([rgb, a]).astype(np.float32)


def bbox(a, thr=0.06, pad=2):
    ys, xs = np.nonzero(a[..., 3] > thr)
    if len(xs) == 0:
        return 0, 0, a.shape[1], a.shape[0]
    return max(0, xs.min() - pad), max(0, ys.min() - pad), min(a.shape[1], xs.max() + 1 + pad), min(a.shape[0], ys.max() + 1 + pad)


def grade(rgba, iron_tint=(0.94, 0.93, 1.04), shadows=0.92, contrast=1.06, sat=0.92):
    """The house grade for painted iron: cooled a touch toward violet in the darks,
    deepened, gold and ember left warm (saturated warm pixels are spared)."""
    rgb = rgba[..., :3].copy()
    lum = rgb.mean(axis=2, keepdims=True)
    warm = np.clip((rgb[..., 0:1] - rgb[..., 2:3]) * 3, 0, 1)  # gold, ember
    cool = rgb * np.asarray(iron_tint, np.float32)
    rgb = rgb * warm + cool * (1 - warm)
    rgb = np.clip((rgb - 0.5) * contrast + 0.5, 0, 1)
    rgb = rgb ** (1 / shadows) if shadows != 1 else rgb
    grey = rgb.mean(axis=2, keepdims=True)
    rgb = grey + (rgb - grey) * (sat + (1 - sat) * warm)
    out = rgba.copy()
    out[..., :3] = np.clip(rgb, 0, 1)
    return out


def to_img(rgba):
    return F.to_pil(rgba)
