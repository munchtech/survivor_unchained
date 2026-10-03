"""The smallest forged pieces, made exactly rather than painted (a painting
cannot hold its shape at 24 pixels): keycaps, the bars' grooves, the gold
segment, the chosen row, the survivor's arrow on the minimap.
"""
from __future__ import annotations

import math

import numpy as np

import forge as F
import frames as FR
import ornament as O
import buttons as B


def keycap(W=48, H=48):
    st = B.small_style(strap=3.5, strap_h=3.0, bevel_out=2.0, bevel_in=1.0, chamfer=3, radius=2, wire=5.2, wire_w=1.4,
                       centre_tone="#0f0d12", wire_mat="gold_dim", wear=0.6, seed=31)
    return FR.frame(W, H, (6, 6, 6, 6), st, ss=6)


def track(W=128, H=32, margins=(8, 6, 8, 6), boss=False):
    """A bar's groove: an iron lip round a sunk dark channel, small gold caps at its ends."""
    st = B.small_style(strap=4.5, strap_h=3.5, bevel_out=1.6, bevel_in=1.6, chamfer=0, radius=6, wire=None,
                       centre_tone="#0c0809", wear=0.6, seed=33, centre_drop=3.0)
    st.rivets = 0

    def post(s, m, st_, k, tx):
        # Gold caps at the two ends (in the corner squares' height, on the left and right edges).
        for cx in (5 * k, s.w - 5 * k):
            sd = F.sd_box(s.xx, s.yy, cx, s.h / 2, 2.6 * k, s.h / 2 - 3 * k, 1.5 * k)
            cov = F.coverage(sd, 1.0)
            O.put(s, cov, F.bevel(sd, 1.2 * k, 2.0 * k) + st_.strap_h * k, "gold_dim")
        return None
    return FR.frame(W, H, margins, st, ss=6, post=post)


def segment_on(W=128, H=48):
    """The chosen option in a row: a small plate of gold leaf over iron (dark text sits on it)."""
    st = B.small_style(strap=3.0, strap_h=2.5, bevel_out=1.6, bevel_in=1.0, chamfer=5, radius=2, wire=None,
                       strap_mat="gold_dim", centre_mat="gold", centre_tone="#d0a858", wear=0.3, seed=35)
    return FR.frame(W, H, (10, 8, 10, 8), st, ss=4)


def row_on(W=512, H=96):
    """A chosen line in a list: warm dark bronze, a gold edge, the ember awake at both ends."""
    st = B.small_style(strap=4.0, strap_h=3.0, bevel_out=1.6, bevel_in=1.2, chamfer=6, radius=2, wire=7.0, wire_w=2.0,
                       strap_mat="bronze", centre_mat="iron_dark", centre_tone="#3a2614", wear=0.5, seed=37)
    st.strap_tint = (0.75, 0.68, 0.62)

    def post(s, m, st_, k, tx):
        # Ember at both ends, rising from the edges (in the corner squares, so it never stretches).
        light = np.zeros((s.h, s.w, 3), np.float32)
        for cx in (0, s.w):
            d = np.abs(s.xx - cx) / (14 * k)
            light += (np.exp(-d * d) * 0.35)[..., None] * O.EMBER
        return light
    return FR.frame(W, H, (12, 10, 12, 10), st, ss=3, post=post)


def you_arrow(size=48, ss=8):
    """The survivor on the minimap: a blood-red arrowhead edged in iron, pointing up."""
    S = size * ss
    s = F.Surface(S, S)
    c = S / 2
    pts = [(c, S * 0.06), (S * 0.84, S * 0.86), (c, S * 0.66), (S * 0.16, S * 0.86)]
    sd = F.sd_poly(s.xx, s.yy, pts)
    cov = F.coverage(sd, 1.0)
    rim = np.clip(sd / (S * 0.07), 0, 1)
    h = np.sqrt(rim) * S * 0.04 + np.clip(sd / (S * 0.2), 0, 1) * S * 0.03
    s.height = h.astype(np.float32)
    s.alpha = cov
    s.paint(cov, "iron")
    inner = F.coverage(sd - S * 0.06, 1.0)
    s.paint(inner, F.Mat(tuple(F.hexc("#c8321e")), 0.2, 0.3))
    lin = s.shade(normal_strength=1.0, ao=0.4, shadow=0.0) * 1.6 + inner[..., None] * F.hexc("#b8321e") * 0.25
    img = np.dstack([F.lin_to_srgb(np.clip(lin, 0, 1)), cov])
    small = F.downsample(img, (size, size))
    # A dark rim so it holds on pale parchment.
    import cv2
    a = small[..., 3]
    grown = cv2.dilate((a * 255).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32) / 255
    rim_a = np.clip(grown - a, 0, 1) * 0.8
    out_a = a + rim_a * (1 - a)
    rgb = (small[..., :3] * a[..., None] + np.array([0.05, 0.03, 0.03]) * (rim_a * (1 - a))[..., None]) / np.maximum(out_a[..., None], 1e-4)
    return F.to_pil(np.dstack([rgb, out_a]))
