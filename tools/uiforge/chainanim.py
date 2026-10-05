"""The tab chain in motion, as a reference for the game's code and to judge at 1:1: the book's
tabs sit along a chain; the chosen tab's link is heated through; choosing another slides the
chain link by link until that link sits under it, then the chain sways and settles.

Everything the code needs is here and small (UI design builds it in the game):
  * links are laid every `pitch` px along a shallow sag between the row's ends, alternately
    flat and on edge, each link keeping its own sprite as it travels (its variant comes from
    its own index along the chain, not its place on the screen);
  * the row's ends fade over `fade` px, as a chain running on out of sight;
  * the slide is a damped spring on the chain's phase (stiff, a little under-damped), so it
    overshoots by a fraction of a link and comes back;
  * the sway: the sag's depth springs too, kicked by the slide's speed, so the chain dips as it
    runs and bobs once as it stops.

    python tools/uiforge/chainanim.py [--from 1 --to 3] [--scale 1]   # frames into chain/anim/
"""
from __future__ import annotations

import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CH = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "chain")


def sprites():
    meta = json.load(open(os.path.join(CH, "links", "chain.json")))
    d = os.path.join(CH, "sprites", "chain")

    def ld(n):
        return np.asarray(Image.open(os.path.join(d, n + ".png")).convert("RGBA"), np.float32) / 255
    flats = [ld(f"face_{k}") for k in range(meta["variants"])]
    edges = [ld(f"edge_{k}") for k in range(meta["variants"])]
    return meta, flats, edges, ld(MARK)


# The chosen tab's link: "open" (pried, ember in the break: the emblem) or "hot" (heated through).
MARK = "open"


class Spring:
    """x'' = k (target - x) - c x' (per second)."""

    def __init__(self, x, k=170.0, c=17.0):
        self.x, self.v, self.k, self.c = x, 0.0, k, c

    def step(self, target, dt):
        a = self.k * (target - self.x) - self.c * self.v
        self.v += a * dt
        self.x += self.v * dt
        return self.x


_small = {}


def lay(canvas, s, sprite, cx, cy, ang, alpha):
    """Draw a sprite (made at 2x) centred at (cx, cy) shown px, turned by ang radians: brought
    to its screen size first with an area filter (as mipmaps would), then placed."""
    key = (id(sprite), s)
    if key not in _small:
        pm0 = np.dstack([sprite[..., :3] * sprite[..., 3:4], sprite[..., 3:4]])
        _small[key] = cv2.resize(pm0, (max(1, round(sprite.shape[1] * s / 2)), max(1, round(sprite.shape[0] * s / 2))),
                                 interpolation=cv2.INTER_AREA)
    pm = _small[key]
    h, w = pm.shape[:2]
    sw, sh = w, h
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -math.degrees(ang), 1.0)
    M[0, 2] += cx * s - w / 2
    M[1, 2] += cy * s - h / 2
    out = cv2.warpAffine(pm, M, (canvas.shape[1], canvas.shape[0]), flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    a = out[..., 3:4] * alpha
    canvas[..., :3] = canvas[..., :3] * (1 - a) + out[..., :3] * alpha
    return sw, sh


def frame(bg, s, meta, flats, edges, hot, x0, x1, y0, phase, sag, hot_index, fade=36.0):
    """One picture: the chain between x0 and x1 (shown px) at height y0, its links shifted by
    `phase` px, sagging `sag` px at its middle; the link numbered `hot_index` heated."""
    img = bg.copy()
    p = meta["pitch"]
    n0 = int(math.floor((x0 - phase) / p)) - 1
    n1 = int(math.ceil((x1 - phase) / p)) + 1
    mid, half = (x0 + x1) / 2, (x1 - x0) / 2

    def y_at(x):
        t = (x - mid) / half
        return y0 + sag * (1 - t * t)

    order = []
    for n in range(n0, n1 + 1):
        x = phase + n * p
        if x < x0 - p or x > x1 + p:
            continue
        a = np.clip(min(x - x0, x1 - x) / fade, 0, 1) ** 1.3
        if a <= 0:
            continue
        ang = math.atan2(y_at(x + 1) - y_at(x - 1), 2)
        flat = n % 2 == 0
        if n == hot_index:
            spr = hot
        else:
            v = (n * 7 + 3) % len(flats)
            spr = flats[v] if flat else edges[v]
        order.append((0 if flat else 1, x, y_at(x), ang, a, spr))
    # Flat links first; those on edge pass through them and lie over their ends.
    for _, x, y, ang, a, spr in sorted(order, key=lambda o: o[0]):
        lay(img, s, spr, x, y, ang, a)
    return img


def run(tabs, frm=1, to=3, scale=1.0, fps=60, secs=1.1, bg=None, y0=58.0, x0=30.0, x1=560.0, out=None, bg_after=None):
    meta, flats, edges, hot = sprites()
    _small.clear()                      # (keyed by the sprites' ids, which a new load reuses)
    p = meta["pitch"]
    s = scale
    if bg is None:
        bg = np.zeros((int(100 * s), int(620 * s), 4), np.float32)
        bg[..., :3] = [0.09, 0.07, 0.07]
        bg[..., 3] = 1
    hot_index = 0
    # Where the heated link must sit: under the chosen tab's middle.
    ph = Spring(tabs[frm] - hot_index * p)
    sg = Spring(3.0, k=120.0, c=7.0)
    frames = []
    dt = 1.0 / fps
    for i in range(int(secs * fps)):
        target = tabs[to] - hot_index * p if i >= 4 else tabs[frm] - hot_index * p
        x = ph.step(target, dt)
        # The sag dips with the chain's speed and springs back.
        sg.step(3.0 + min(abs(ph.v) / 260.0, 1.0) * 3.5, dt)
        b = bg_after if (bg_after is not None and i >= 4) else bg
        frames.append(frame(b, s, meta, flats, edges, hot, x0, x1, y0, x, sg.x, hot_index))
    if out:
        os.makedirs(out, exist_ok=True)
        for i, f in enumerate(frames):
            F.save(F.to_pil(np.clip(f, 0, 1)), os.path.join(out, f"f{i:03d}.png"))
    return frames


if __name__ == "__main__":
    a = sys.argv[1:]
    frm = int(a[a.index("--from") + 1]) if "--from" in a else 1
    to = int(a[a.index("--to") + 1]) if "--to" in a else 3
    scale = float(a[a.index("--scale") + 1]) if "--scale" in a else 1.0
    tabs = [76, 166, 256, 350, 452]
    fr = run(tabs, frm, to, scale, out=os.path.join(CH, "anim"))
    print(len(fr), "frames")
