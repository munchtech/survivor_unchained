"""The chain: the game's motif (Survivor *Unchained*), placed once per screen where it means
something, never as a border. A length of forged chain hung from two staples, sagging under
its own weight, one link pried open at its lowest point with ember in the break: the chain
that held the day's book shut, broken. Modelled in Blender (blender_chainline.py) under the
house light, its shadow caught on the page.

    python tools/uiforge/chain.py [swag ...]       # into tools/comfy/out/uiforge/chain/

  swag   frames/chain_swag.png: laid under a page's title, its staples on the head band's rail
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import cv2
import numpy as np
from PIL import Image

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BLENDER = os.environ.get("BLENDER", r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe")
OUT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "chain")


def render(spec, name):
    """Render a spec; returns float RGBA at the spec's file size. A run that fails must not hand
    back an older picture, so the old one is removed first and the new one's time checked."""
    os.makedirs(OUT, exist_ok=True)
    sp = os.path.join(OUT, name + ".json")
    out = os.path.join(OUT, name + ".png")
    json.dump(spec, open(sp, "w", encoding="utf-8"), indent=1)
    if os.path.exists(out):
        os.remove(out)
    t0 = time.time()
    r = subprocess.run([BLENDER, "-b", "-P", os.path.join(HERE, "blender_chainline.py"), "--", sp, out],
                       capture_output=True, text=True, timeout=1800)
    if not os.path.exists(out) or os.path.getmtime(out) < t0 or "Traceback" in r.stdout + r.stderr:
        raise RuntimeError((r.stdout + r.stderr)[-3000:])
    img = np.asarray(Image.open(out).convert("RGBA"), np.float32) / 255
    W, H = spec["size"]
    if img.shape[1] != W:
        img = F.downsample(img, (W, H))
    return img


def ember_glow(img, strength=1.0):
    """The break's light thrown on what is round it: a soft orange bloom from the hot pixels."""
    rgb, a = img[..., :3], img[..., 3]
    hot = np.clip((rgb[..., 0] - 0.55) * 2.5, 0, 1) * np.clip(rgb[..., 0] - rgb[..., 2] - 0.3, 0, 1) * 3 * a
    g = cv2.GaussianBlur(hot, (0, 0), 6) * 0.9 + cv2.GaussianBlur(hot, (0, 0), 18) * 0.6
    g = np.clip(g * strength, 0, 1)
    col = np.array([1.0, 0.45, 0.12], np.float32)
    out_a = a + g * (1 - a)
    out = (rgb * a[..., None] + col * (g * (1 - a))[..., None]) / np.maximum(out_a[..., None], 1e-4)
    return np.dstack([out, out_a]).astype(np.float32)


def swag(samples=64):
    """frames/chain_swag.png, 1200x150 file (600x75 shown): two staples on the rail 530 shown
    apart, the chain sagging 22 shown between them, its lowest link pried open."""
    spec = {"size": [1200, 150], "ss": 2, "samples": samples,
            "link": {"length": 34, "width": 20, "wire": 2.8},
            "chains": [{"from": [70, 20], "to": [1130, 20], "sag": 44, "open": "middle", "gap": 8}],
            "staples": [{"x": 70, "y": 16}, {"x": 1130, "y": 16}],
            "ember": 6.0}
    return ember_glow(render(spec, "swag"))


def band(samples=48, span=320, sag=10.0, broken_sag=15.0, rail_y=14.0):
    """frames/chain_band.png, 3840x80 file (1920x40 shown, laid at the page's y 76 so its
    rail_y falls on the head band's rail): the chain hung along the rail from a staple every
    `span` px, sagging `sag` between them, and under the title (the screen's middle) the swag
    sags further where its lowest link is pried open, ember in the break."""
    W, H = 1920, 40
    chains, staples = [], []
    x = W / 2 - span / 2 - span * 3
    while x < W + span:
        mid = abs((x + span / 2) - W / 2) < 1
        chains.append({"from": [x * 2, rail_y * 2], "to": [(x + span) * 2, rail_y * 2],
                       "sag": (broken_sag if mid else sag) * 2, "open": "middle" if mid else [], "gap": 9})
        if 0 <= x <= W:
            staples.append({"x": x * 2, "y": rail_y * 2 - 2})
        x += span
    spec = {"size": [W * 2, H * 2], "ss": 2, "samples": samples,
            "link": {"length": 32, "width": 19, "wire": 2.6}, "chains": chains, "staples": staples, "ember": 6.0}
    return ember_glow(render(spec, "band"))


def title(side="r", samples=64, length=240, link=(28, 16, 2.3), gap=9.0, fade=80.0):
    """ornaments/title_chain_SIDE.png, length x 40 shown: the chain either side of a page's
    title, as if the name had broken it. It runs in from beyond the plaque, fading as it goes
    out, and ends at the title in a link pried open at its end, ember in the break. Rendered for
    each side, so both are lit from the upper left (a mirrored one would cast its shadow the
    wrong way)."""
    W, H = int(length), 40
    y = H / 2
    near, far = (12.0, W + 30.0) if side == "r" else (W - 12.0, -30.0)
    spec = {"size": [W * 2, H * 2], "ss": 2, "samples": samples,
            "link": {"length": link[0] * 2, "width": link[1] * 2, "wire": link[2] * 2},
            "chains": [{"from": [min(near, far) * 2, y * 2], "to": [max(near, far) * 2, y * 2], "sag": 4,
                        "open": "first" if side == "r" else "last", "gap": gap * 2, "where": "end"}],
            "staples": [], "ember": 6.0}
    img = ember_glow(render(spec, f"title_{side}"))
    # Its outer end fades into the band, as a chain running on out of sight.
    x = (np.arange(img.shape[1], dtype=np.float32) + 0.5) / 2
    d = (W - x) if side == "r" else x
    img[..., 3] *= np.clip(d / fade, 0, 1) ** 1.4
    return img


MAKE = {"swag": ("frames/chain_swag.png", swag), "band": ("frames/chain_band.png", band),
        "title_r": ("ornaments/title_chain_r.png", lambda: title("r")),
        "title_l": ("ornaments/title_chain_l.png", lambda: title("l"))}


if __name__ == "__main__":
    for k in sys.argv[1:] or list(MAKE):
        rel, fn = MAKE[k]
        img = fn()
        p = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        F.save(F.to_pil(np.clip(img, 0, 1)), p)
        print("chain", rel, flush=True)
