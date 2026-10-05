"""Small lights for words that need no box (the owner: pickups "transparent and stylized"; tips
with no panel): an ember's burst that a toast or a tip comes out of, a glint as it settles, and
the amber pointer for a Legendary's pillar off screen.

    python tools/uiforge/embers.py        # into tools/comfy/out/uiforge/embers/, then kit.py --apply

  hud/spark.png              8 frames of 48x48 shown in a strip (768x96 file): a coal's burst,
                             white-hot at its heart, sparks flung out, slowing and cooling to red
  hud/glint.png              32x32 shown: a thin four-pointed glint, white (the code tints it)
  hud/pointer_legendary.png  40x40 shown, pointing right: an amber chevron struck in gold, ember
                             light round it (turn it to the edge it sits on)
"""
from __future__ import annotations

import math
import os

import cv2
import numpy as np

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "embers")


def temp_colour(t):
    """A spark's colour by its heat (1 white-hot, 0 dull red)."""
    stops = [(0.0, (0.45, 0.06, 0.02)), (0.35, (0.95, 0.32, 0.06)), (0.7, (1.0, 0.68, 0.25)), (1.0, (1.0, 0.95, 0.82))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if t <= b:
            u = (t - a) / (b - a)
            return np.array(ca) * (1 - u) + np.array(cb) * u
    return np.array(stops[-1][1])


def spark(frames=8, S=48, ss=4, seed=5):
    """hud/spark.png: a burst like a coal cracking, frames left to right."""
    n = S * 2 * ss
    rng = np.random.default_rng(seed)
    N = 16
    ang = rng.uniform(0, 2 * math.pi, N)
    spd = rng.uniform(0.55, 1.0, N) * n * 0.46
    up = rng.uniform(0.0, 0.12, N) * n          # sparks rise a little, as hot things do
    life = rng.uniform(0.55, 1.0, N)
    strip = []
    c = n / 2

    def pos(i, t):
        d = spd[i] * (1 - math.exp(-t * 3.2)) / (1 - math.exp(-3.2))
        return c + math.cos(ang[i]) * d, c + math.sin(ang[i]) * d - up[i] * t * t

    for f in range(frames):
        t = (f + 1) / frames
        tp = max(0.0, (f + 0.25) / frames)
        light = np.zeros((n, n), np.float32)
        col = np.zeros((n, n, 3), np.float32)
        # The heart: a flash that is gone by the third frame.
        core = max(0.0, 1 - t * 2.6)
        if core > 0:
            yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
            g = np.exp(-((xx - c) ** 2 + (yy - c) ** 2) / (2 * (n * (0.06 + 0.1 * t)) ** 2)) * core
            light = np.maximum(light, g)
            col += g[..., None] * temp_colour(min(1, 0.6 + core))
        for i in range(N):
            if t > life[i]:
                continue
            heat = 1 - t / life[i]
            x0, y0 = pos(i, tp)
            x1, y1 = pos(i, t)
            m = np.zeros((n, n), np.float32)
            cv2.line(m, (int(x0 * 16), int(y0 * 16)), (int(x1 * 16), int(y1 * 16)), 1.0, max(1, int(ss * (1.2 + 1.6 * heat))),
                     cv2.LINE_AA, shift=4)
            m = cv2.GaussianBlur(m, (0, 0), ss * 0.6) * (0.4 + 0.6 * heat)
            light = np.maximum(light, m)
            col += m[..., None] * temp_colour(heat)
        glow = cv2.GaussianBlur(light, (0, 0), ss * 4) * 0.5
        a = np.clip(light + glow, 0, 1)
        rgb = np.clip((col + glow[..., None] * np.array([1.0, 0.45, 0.12])) / np.maximum(a[..., None], 1e-4), 0, 1)
        # Faded to nothing at the cell's edge, so frames never show their square.
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        edge = np.clip(np.minimum(np.minimum(xx, n - 1 - xx), np.minimum(yy, n - 1 - yy)) / (n * 0.08), 0, 1)
        img = np.dstack([rgb, a * edge])
        strip.append(F.downsample(img, (S * 2, S * 2)))
    return np.concatenate(strip, 1).astype(np.float32)


def glint(S=32, ss=4):
    """hud/glint.png: a thin four-pointed glint, the long arms across, short ones up and down,
    fainter diagonals; white, soft-tipped."""
    n = S * 2 * ss
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    u, v = (xx + 0.5) / n * 2 - 1, (yy + 0.5) / n * 2 - 1
    r = np.hypot(u, v)

    def arm(a, b, length, width):
        return np.exp(-(b / width) ** 2) * np.clip(1 - np.abs(a) / length, 0, 1) ** 2.2
    g = arm(u, v, 0.98, 0.025) + arm(v, u, 0.72, 0.025)
    d1, d2 = (u + v) / math.sqrt(2), (u - v) / math.sqrt(2)
    g += 0.35 * (arm(d1, d2, 0.42, 0.02) + arm(d2, d1, 0.42, 0.02))
    g += np.exp(-(r / 0.07) ** 2)
    g = np.clip(g, 0, 1)
    img = np.dstack([np.ones((n, n, 3), np.float32), g])
    return F.downsample(img, (S * 2, S * 2)).astype(np.float32)


def pointer(S=40, ss=4):
    """hud/pointer_legendary.png, pointing right: a chevron struck in gold, a bevel catching the
    house light, amber ember light round it, so it reads at the screen's edge over anything."""
    n = S * 2 * ss
    s = F.Surface(n, n)
    xx, yy = s.xx / n * S, s.yy / n * S          # shown px
    cx, cy = S * 0.52, S / 2
    # A chevron: two arms meeting at a point on the right.
    def seg_sd(px, py, ax, ay, bx, by, w):
        dx, dy = bx - ax, by - ay
        t = np.clip(((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy), 0, 1)
        return w - np.hypot(px - ax - t * dx, py - ay - t * dy)
    tip = (cx + 7.5, cy)
    sd = np.maximum(seg_sd(xx, yy, cx - 6.5, cy - 10, *tip, 3.4), seg_sd(xx, yy, cx - 6.5, cy + 10, *tip, 3.4))
    cov = np.clip(sd * n / S + 0.5, 0, 1)
    h = np.sqrt(np.clip(sd / 3.4, 0, 1)) * 3.0 * n / S
    s.height = h.astype(np.float32)
    s.paint(cov, F.Mat(tuple(F.hexc("#ffb040") * 0.9), 1.0, 0.28))
    s.alpha = cov
    lin = s.shade(normal_strength=1.0, ao=0.2, shadow=0.0)
    rgb = F.lin_to_srgb(np.clip(lin, 0, 1))
    glow = cv2.GaussianBlur(cov, (0, 0), n / S * 3.2) * 1.15
    a = np.clip(cov + glow * (1 - cov), 0, 1)
    amber = np.array([1.0, 0.62, 0.18], np.float32)
    out = (rgb * cov[..., None] + amber * (glow * (1 - cov))[..., None]) / np.maximum(a[..., None], 1e-4)
    return F.downsample(np.dstack([out, a]), (S * 2, S * 2)).astype(np.float32)


MAKE = {"hud/spark.png": spark, "hud/glint.png": glint, "hud/pointer_legendary.png": pointer}


def build():
    for rel, fn in MAKE.items():
        p = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        F.save(F.to_pil(np.clip(fn(), 0, 1)), p)
        print("embers", rel, flush=True)


if __name__ == "__main__":
    build()
