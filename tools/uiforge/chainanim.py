"""The tab chain in motion, as a reference for the game's code (ChainTabs) and to judge at 1:1:
the book's tabs sit along a heavy forged chain; under the chosen tab five links are heated,
the middle one pried open, cooling to dull red outward, a little ember light on the band under
them; choosing another tab drags the chain link by link until that heat sits under it, the
chain sagging as it runs and swinging as it stops.

Its feel comes from art/ui/chain/chain.json, as the game's does (made by chain.links):
  pitch, fade, run       link spacing; the ends fade over `fade` px, `run` px past the end tabs
  heat                   links each side of the middle that glow (heat 1 at the middle, falling
                         to 1 - k/(heat+1) at the ends)
  slide [k, c]           the spring on the chain's phase: x'' = k (target - x) - c x'
  sag_spring [k, c]      the spring on its sag, toward sag_rest + min(|v| / sag_speed, 1) * sag_dip

    python tools/uiforge/chainanim.py      # frames into tools/comfy/out/uiforge/chain/anim/
"""
from __future__ import annotations

import json
import math
import os

import cv2
import numpy as np
from PIL import Image

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CH = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "chain")
HEAT = [(0.0, "#7a2410"), (0.5, "#ff7a26"), (1.0, "#ffc070")]   # dull at the ends, bright at the heart


def heat_colour(h):
    for (a, ca), (b, cb) in zip(HEAT, HEAT[1:]):
        if h <= b:
            t = (h - a) / (b - a)
            return F.hexc(ca, lin=False) * (1 - t) + F.hexc(cb, lin=False) * t
    return F.hexc(HEAT[-1][1], lin=False)


def sprites():
    meta = json.load(open(os.path.join(CH, "links", "chain.json")))
    d = os.path.join(CH, "sprites", "chain")

    def ld(n):
        return np.asarray(Image.open(os.path.join(d, n + ".png")).convert("RGBA"), np.float32) / 255
    v = meta["variants"]
    S = {f"{pre}{kind}_{k}": ld(f"{pre}{kind}_{k}") for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(v)}
    S["open"] = ld("open")
    return meta, S


class Spring:
    """x'' = k (target - x) - c x' (per second)."""

    def __init__(self, x, k, c):
        self.x, self.v, self.k, self.c = x, 0.0, k, c

    def step(self, target, dt):
        a = self.k * (target - self.x) - self.c * self.v
        self.v += a * dt
        self.x += self.v * dt
        return self.x


_small = {}


def shrink(name, spr, s):
    """A sprite made at 2x brought to its screen size with an area filter (as mipmaps would)."""
    key = (name, s)
    if key not in _small:
        pm = np.dstack([spr[..., :3] * spr[..., 3:4], spr[..., 3:4]])
        _small[key] = cv2.resize(pm, (max(1, round(spr.shape[1] * s / 2)), max(1, round(spr.shape[0] * s / 2))),
                                 interpolation=cv2.INTER_AREA)
    return _small[key]


def lay(canvas, pm, cx, cy, ang, alpha, s):
    """Draw a premultiplied sprite centred at (cx, cy) shown px, turned by ang radians."""
    h, w = pm.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -math.degrees(ang), 1.0)
    M[0, 2] += cx * s - w / 2
    M[1, 2] += cy * s - h / 2
    out = cv2.warpAffine(pm, M, (canvas.shape[1], canvas.shape[0]), flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    a = out[..., 3:4] * alpha
    canvas[..., :3] = canvas[..., :3] * (1 - a) + out[..., :3] * alpha


def glow(canvas, cx, cy, rx, ry, col, strength, s):
    """Light added over the band: a soft ellipse of a colour."""
    H, W = canvas.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx / s - cx) / rx) ** 2 + ((yy / s - cy) / ry) ** 2)) * strength
    canvas[..., :3] = np.clip(canvas[..., :3] + g[..., None] * np.asarray(col, np.float32), 0, 1)


def frame(bg, s, meta, S, x0, x1, y0, phase, sag, chosen, t, flicker_seed=7):
    """One picture: the chain between x0 and x1 (shown px) at height y0, its links shifted by
    `phase` px, sagging `sag` px at its middle; links near index `chosen` heated."""
    img = bg.copy()
    p, fade, heat = meta["pitch"], meta["fade"], meta["heat"]
    var = meta["variants"]
    n0 = int(math.floor((x0 - phase) / p)) - 1
    n1 = int(math.ceil((x1 - phase) / p)) + 1
    mid, half = (x0 + x1) / 2, (x1 - x0) / 2

    def y_at(x):
        u = (x - mid) / half
        return y0 + sag * (1 - u * u)

    # The ember's light on the band under the heated links, flickering a little.
    cx = phase + chosen * p
    fl = 1 + 0.12 * math.sin(t * 23 + flicker_seed) + 0.08 * math.sin(t * 37.3 + 1.7 * flicker_seed)
    glow(img, cx, y_at(cx) + 5, p * (heat + 0.9), 9, heat_colour(0.55), 0.14 * fl, s)
    order = []
    for n in range(n0, n1 + 1):
        x = phase + n * p
        a = np.clip(min(x - x0, x1 - x) / fade, 0, 1) ** 1.3
        if a <= 0:
            continue
        ang = math.atan2(y_at(x + 1) - y_at(x - 1), 2)
        kind = "face" if n % 2 == 0 else "edge"
        k = (n * 7 + 3) % var
        d = abs(n - chosen)
        h = 1 - d / (heat + 1) if d <= heat else 0.0
        order.append((0 if kind == "face" else 1, n, x, y_at(x), ang, a, kind, k, h))
    # Face-on links first; those on edge pass through them and lie over their ends.
    for _, n, x, y, ang, a, kind, k, h in sorted(order, key=lambda o: o[0]):
        if n == chosen:
            lay(img, shrink("open", S["open"], s), x, y, ang, a, s)
        else:
            lay(img, shrink(f"{kind}_{k}", S[f"{kind}_{k}"], s), x, y, ang, a, s)
            if h > 0:
                # Cold to warm to hot: the same link drawn in each state.
                if h < 0.6:
                    lay(img, shrink(f"warm_{kind}_{k}", S[f"warm_{kind}_{k}"], s), x, y, ang, a * h / 0.6, s)
                else:
                    lay(img, shrink(f"warm_{kind}_{k}", S[f"warm_{kind}_{k}"], s), x, y, ang, a, s)
                    lay(img, shrink(f"hot_{kind}_{k}", S[f"hot_{kind}_{k}"], s), x, y, ang, a * (h - 0.6) / 0.4, s)
        if h > 0:
            glow(img, x, y, p * 0.7, p * 0.45, heat_colour(h), 0.24 * h * fl, s)
    return img


def run(tabs, frm=1, to=3, scale=1.0, fps=60, secs=1.4, bg=None, y0=60.0, x0=None, x1=None, out=None, bg_after=None):
    meta, S = sprites()
    _small.clear()
    p = meta["pitch"]
    s = scale
    x0 = tabs[0] - meta["run"] if x0 is None else x0
    x1 = tabs[-1] + meta["run"] if x1 is None else x1
    if bg is None:
        bg = np.zeros((int(100 * s), int(620 * s), 4), np.float32)
        bg[..., :3] = [0.09, 0.07, 0.07]
        bg[..., 3] = 1
    chosen = 0
    ph = Spring(tabs[frm] - chosen * p, *meta["slide"])
    rest, dip, speed = meta["sag_rest"], meta["sag_dip"], meta["sag_speed"]
    sg = Spring(rest, *meta["sag_spring"])
    frames = []
    dt = 1.0 / fps
    for i in range(int(secs * fps)):
        target = tabs[to] - chosen * p if i >= 4 else tabs[frm] - chosen * p
        x = ph.step(target, dt)
        sg.step(rest + min(abs(ph.v) / speed, 1.0) * dip, dt)
        b = bg_after if (bg_after is not None and i >= 4) else bg
        frames.append(frame(b, s, meta, S, x0, x1, y0, x, sg.x, chosen, i * dt))
    if out:
        os.makedirs(out, exist_ok=True)
        for i, f in enumerate(frames):
            F.save(F.to_pil(np.clip(f, 0, 1)), os.path.join(out, f"f{i:03d}.png"))
    return frames


if __name__ == "__main__":
    fr = run([76, 167, 256, 358, 460], 1, 3, out=os.path.join(CH, "anim"))
    print(len(fr), "frames")
