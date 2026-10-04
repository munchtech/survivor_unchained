"""Pieces made of light rather than metal: the focus ring (hot iron's glow
round whatever has focus, its corners bracketed like the plates' corners),
and the ember and moonlight that fill the bars.
"""
from __future__ import annotations

import math

import numpy as np

import forge as F
import frames as FR


def _out(lin, alpha_from_light=True):
    """Light on transparency: alpha from brightness, colour un-premultiplied."""
    srgb = F.lin_to_srgb(np.clip(lin, 0, None))
    a = np.clip(srgb.max(axis=2), 0, 1)
    rgb = np.clip(srgb / np.maximum(a[..., None], 1e-4), 0, 1)
    return np.dstack([rgb, a])


def focus_ring(W=128, H=128, line_at=9.0, ss=4):
    """Ember-gold line, empty middle, brighter L brackets at the corners and a spark at each."""
    w, h = W * ss, H * ss
    k = ss
    xx, yy = F.grid(h, w)
    sd = F.sd_box(xx, yy, w / 2, h / 2, w / 2 - line_at * k, h / 2 - line_at * k, 5 * k)
    dist = np.abs(sd)
    core = np.exp(-(dist / (1.2 * k)) ** 2)
    # Glow mostly outward (the light falls on the plate round the thing), little inward.
    inward = sd > 0
    glow = np.exp(-dist / np.where(inward, 2.2 * k, 4.0 * k))
    wide = np.exp(-dist / (8 * k)) * np.where(inward, 0.0, 0.45)
    hot = F.hexc("#fff2d8")
    gold = F.hexc("#ffc46a")
    ember = F.hexc("#ff8a3a")
    lin = core[..., None] * (hot * 0.7 + gold * 0.9) + glow[..., None] * gold * 0.55 + wide[..., None] * ember * 0.35
    # Corner brackets: the line thickened for 11 shown px each way from every corner.
    L = 22 * k
    cx0, cy0 = line_at * k, line_at * k
    br = np.zeros((h, w), np.float32)
    for (cx, cy, sx, sy) in ((cx0, cy0, 1, 1), (w - cx0, cy0, -1, 1), (cx0, h - cy0, 1, -1), (w - cx0, h - cy0, -1, -1)):
        along_x = (sx * (xx - cx) >= -1 * k) & (sx * (xx - cx) <= L)
        along_y = (sy * (yy - cy) >= -1 * k) & (sy * (yy - cy) <= L)
        near = (along_x & (np.abs(yy - cy) < 6 * k)) | (along_y & (np.abs(xx - cx) < 6 * k))
        t = np.clip(1 - np.maximum(sx * (xx - cx), sy * (yy - cy)) / L, 0, 1)
        br = np.maximum(br, near * t)
        # A spark: a small four-pointed star at the corner, outside the line.
        px, py = cx - sx * 3.5 * k, cy - sy * 3.5 * k
        dx, dy = np.abs(xx - px), np.abs(yy - py)
        star = np.exp(-(dx * dy) / (1.2 * k * k)) * np.exp(-(dx + dy) / (5 * k))
        lin += star[..., None] * hot * 1.2
    thick = np.exp(-(dist / (2.2 * k)) ** 2) * br
    lin += thick[..., None] * (hot * 0.9 + gold * 0.6) + (glow * br)[..., None] * gold * 0.5
    img = _out(lin)
    return F.to_pil(F.downsample(img, (W, H)))


def flow_noise(h, w, scale, seed, stretch=3.0, octaves=4):
    """Noise stretched along x (flowing), periodic in x."""
    hh = int(h)
    n = F.fbm(hh, int(w), scale=scale, octaves=octaves, seed=seed)
    return n


def ember_fill(W=512, H=20, ss=4, seed=3):
    """Molten ember seen through the bar: hot flowing light under drifting plates of dark
    slag, each plate's edge glowing where it meets the melt. Seamless left to right."""
    w, h = W * ss, H * ss
    # Noise made on a tall canvas and sampled every 4th row: stretched along the flow.
    flow = F.fbm(h * 6, w, scale=26 * ss, octaves=5, seed=seed)[::6][:h]
    slag = F.fbm(h * 5, w, scale=16 * ss, octaves=4, seed=seed + 1)[::5][:h]
    y = (np.arange(h)[:, None] + 0.5) / h
    # A glowing channel: hottest along its middle, cooling to deep red at its walls.
    channel = np.clip(1 - np.abs(y - 0.48) * 2.1, 0, 1) ** 0.8
    crust = np.clip((slag - 0.38) * 4.0, 0, 1) * (1 - channel * 0.6)  # slag drifts at the walls
    edge = np.exp(-((slag - 0.38) / 0.05) ** 2)            # the slag's glowing rim
    heat = np.clip(0.05 + 0.9 * channel ** 1.3 + 0.25 * flow, 0, 1)
    deep = F.hexc("#3a0c04")
    red = F.hexc("#a8200e")
    mid = F.hexc("#ff6a14")
    hot = F.hexc("#ffc860")
    hh = heat[..., None]
    melt = np.where(hh < 0.3, deep + (red - deep) * (hh / 0.3),
                    np.where(hh < 0.7, red + (mid - red) * ((hh - 0.3) / 0.4), mid + (hot - mid) * ((hh - 0.7) / 0.3)))
    slag_col = deep * (0.8 + 0.6 * flow[..., None])
    lin = melt * (1 - crust[..., None]) + slag_col * crust[..., None]
    lin += edge[..., None] * hot * 0.9 * (1 - crust[..., None] * 0.5)
    # The light catching the top of the melt.
    lin += (np.exp(-y / 0.08) * 0.12)[..., None] * hot
    srgb = F.lin_to_srgb(np.clip(lin, 0, 1))
    img = np.dstack([srgb, np.ones((h, w))])
    return F.to_pil(F.downsample(img, (W, H)))


def experience_fill(W=512, H=20, ss=4, seed=5):
    """Moonlight on the Low Ford: pale blue water light, slow ripples and a few motes."""
    w, h = W * ss, H * ss
    n = F.fbm(h * 4, w, scale=30 * ss, octaves=4, seed=seed)[::4][:h]
    rip = F.fbm(h * 6, w, scale=8 * ss, octaves=2, seed=seed + 1)[::6][:h]
    y = (np.arange(h)[:, None] + 0.5) / h
    t = np.clip(0.45 + 0.3 * n + 0.15 * rip - (y - 0.4) * 0.5, 0, 1)
    lo = F.hexc("#2a4a6e")
    mid = F.hexc("#86b0d8")
    hi = F.hexc("#d8ecff")
    lin = np.where(t[..., None] < 0.55, lo + (mid - lo) * (t[..., None] / 0.55), mid + (hi - mid) * ((t[..., None] - 0.55) / 0.45))
    rng = np.random.default_rng(seed)
    xx, yy = F.grid(h, w)
    for _ in range(9):
        px, py = rng.random() * w, (0.2 + rng.random() * 0.6) * h
        for ox in (-w, 0, w):
            d = np.hypot(xx - px - ox, yy - py)
            lin += (np.exp(-(d / (1.0 * ss)) ** 2) * 0.5 + np.exp(-d / (4 * ss)) * 0.12)[..., None] * hi
    lin += (np.exp(-y / 0.08) * 0.3)[..., None] * hi
    srgb = F.lin_to_srgb(np.clip(lin, 0, 1))
    return F.to_pil(F.downsample(np.dstack([srgb, np.ones((h, w))]), (W, H)))


def health_fill(W=512, H=48, ss=4, seed=7):
    """Blood: deep and glossy, brighter at the top edge, slow dark swirls in it."""
    w, h = W * ss, H * ss
    n = F.fbm(h * 3, w, scale=34 * ss, octaves=4, seed=seed)[::3][:h]
    y = (np.arange(h)[:, None] + 0.5) / h
    deep = F.hexc("#3a0508")
    mid = F.hexc("#a01822")
    hi = F.hexc("#e8444a")
    t = np.clip(0.75 - y * 0.6 + n * 0.18, 0, 1)
    lin = np.where(t[..., None] < 0.5, deep + (mid - deep) * (t[..., None] / 0.5), mid + (hi - mid) * ((t[..., None] - 0.5) / 0.5))
    # The gloss: a soft bright band near the top, and a thin specular line.
    gloss = np.exp(-((y - 0.16) / 0.07) ** 2) * (0.55 + 0.25 * n)
    lin += gloss[..., None] * F.hexc("#ff8a8a") * 0.55
    lin += np.exp(-((y - 0.06) / 0.02) ** 2)[..., None] * F.hexc("#ffd0c8") * 0.35
    srgb = F.lin_to_srgb(np.clip(lin, 0, 1))
    return F.to_pil(F.downsample(np.dstack([srgb, np.ones((h, w))]), (W, H)))
