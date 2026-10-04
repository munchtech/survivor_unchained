"""The Waystation's ledger paper (frames/paper.png, frames/hint.png): laid paper of
rag, its fibres and chain lines, foxed at the rims, the edge deckled by hand; on
the ledger page small iron corner caps riveted on (the same forged iron and
light as the plates), on the hint a square nail at the top left and a drop of
red wax. Every texture repeats over the space between the margins, so a page
of any size tiles without a seam.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

import forge as F
import frames as FR
import ornament as O

PAPER = "#e4d6b6"


def _periodic(arr_fn, W, H, m, seed):
    l, t, r, b = m
    P, Q = W - l - r, H - t - b
    return FR.periodic_offset(arr_fn(Q, P, seed), W, H, l, t, P, Q)


def sheet(W, H, margins_shown, ss=2, seed=3, corners=True, nail=False, wax=False, tone=PAPER):
    m = [v * 2 * ss for v in margins_shown]
    w, h = W * ss, H * ss
    k = ss
    fib = _periodic(lambda q, p, s: F.fbm(q, p, scale=1.4 * k, octaves=3, seed=s), w, h, m, seed)
    cloud = _periodic(lambda q, p, s: F.fbm(q, p, scale=40 * k, octaves=4, seed=s), w, h, m, seed + 1)
    fox = _periodic(lambda q, p, s: F.fbm(q, p, scale=9 * k, octaves=3, seed=s), w, h, m, seed + 2)
    tear = _periodic(lambda q, p, s: F.fbm(q, p, scale=11 * k, octaves=5, seed=s), w, h, m, seed + 3)
    # Fibres: short strokes, more along than across (laid paper).
    strokes = _periodic(lambda q, p, s: F.fbm(q * 3, p, scale=2.0 * k, octaves=2, seed=s)[::3][:q], w, h, m, seed + 4)
    xx, yy = F.grid(h, w)
    inset = 7 * k
    d = F.sd_box(xx, yy, w / 2, h / 2, w / 2 - inset, h / 2 - inset, 2 * k)
    # The deckle: the edge eaten in by a torn, fibrous line.
    d = d + tear * 6.0 * k + fib * 0.9 * k
    a = np.clip(d / (0.8 * k) + 0.5, 0, 1)
    # Colour: cream, clouded, fibres; browning toward the rim (within the margin).
    base = F.hexc(tone)
    col = base * (1 + cloud[..., None] * 0.045 + fib[..., None] * 0.03 + strokes[..., None] * 0.025)
    rim = np.clip(1 - d / (34 * k), 0, 1) ** 2.2
    brown = F.hexc("#9a6a32")
    col = col * (1 - rim[..., None] * 0.55) + brown * rim[..., None] * 0.22
    # Foxing: rust spots near the rims only.
    spots = np.clip((fox - 0.25) * 3, 0, 1) * np.clip(1 - d / (44 * k), 0, 1)
    col = col * (1 - spots[..., None] * 0.25 * np.array([0.6, 0.8, 1.1]))
    # A burnt, darker lip right at the torn edge.
    lip = np.clip(1 - d / (3.0 * k), 0, 1) * a
    col = col * (1 - lip[..., None] * 0.55)
    s = F.Surface(w, h)
    s.albedo = col.astype(np.float32)
    s.metal[:] = 0
    s.rough[:] = 0.9
    # A little relief: the fibres and a slight cockle.
    s.height = (fib * 0.05 * k + cloud * 0.25 * k).astype(np.float32)
    s.alpha = a
    iron = np.zeros((h, w), np.float32)
    if corners:
        L = 44 * k
        for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            cx = inset if sx > 0 else w - inset
            cy = inset if sy > 0 else h - inset
            tri = F.sd_poly(s.xx, s.yy, [(cx, cy), (cx + sx * L, cy), (cx, cy + sy * L)])
            # A folded-over cap: its hypotenuse edge a little rounded.
            cov = F.coverage(tri, 1.0)
            O.put(s, cov, F.bevel(tri, 1.4 * k, 2.6 * k) + 1.5 * k, "iron")
            iron = np.maximum(iron, cov)
            O.rivet(s, cx + sx * L * 0.28, cy + sy * L * 0.28, 3.4 * k, base=4 * k)
    if nail:
        cx, cy = 26 * k, 26 * k
        _, hole = O.coin(s, cx, cy, 26 * k, mat="iron", base=2 * k, foil=False, sigil=False, hole=0.0001)
        O.rivet(s, cx, cy, 5.0 * k, base=4 * k)
    wax_light = None
    if wax:
        cx, cy = w - 34 * k, h - 32 * k
        n = F.fbm(h, w, scale=3 * k, octaves=3, seed=seed + 9)
        sd = F.sd_circle(s.xx, s.yy, cx, cy, 17 * k) + n * 3.5 * k
        cov = F.coverage(sd, 1.0)
        dome = np.sqrt(np.clip(sd / (17 * k), 0, 1)) * 4 * k
        # The seal's stamp: a square coin pressed into it.
        u, v = s.xx - cx, s.yy - cy
        stamp = np.abs(np.abs(u) + np.abs(v) - 9 * k) < 1.3 * k
        dome = dome - stamp * 0.8 * k
        O.put(s, cov, dome + 0.5 * k, F.Mat(tuple(F.hexc("#8a1a14")), 0.0, 0.25))
    lin = s.shade(normal_strength=0.8, ao=0.4, shadow=0.35, light_elev=42)
    # The middle set to the paper's tone (the ink colours were chosen for it).
    ml, mt, mr, mb = m
    sel = lin[mt:h - mb, ml:w - mr]
    cur = np.median(sel.reshape(-1, 3), axis=0)
    gain = np.clip(F.hexc(tone) / np.maximum(cur, 1e-4), 0.5, 2.0)
    paper_only = (1 - iron)[..., None]
    lin = lin * (1 + (gain - 1) * paper_only * 0.9)
    img = np.dstack([F.lin_to_srgb(np.clip(lin, 0, 1)), np.maximum(a, s.alpha)])
    return F.downsample(img, (W, H))


def make(W, H, margins, seed, prompt, tone, name, **kw):
    """The sheet, painted over on the local Krea (its foxing and deckle given a hand), its
    middle calmed back to the paper's tone, made to tile."""
    import paintover as PO
    import painted as P
    import nineslice as N
    base = sheet(W, H, margins, seed=seed, tone=tone, **kw)
    out = PO.paint(base, prompt, name, denoise=0.38, seed=21, keep_light=0.4)
    m = [v * 2 for v in margins]
    region = np.zeros((H, W), np.float32)
    region[m[1] + 8:H - m[3] - 8, m[0] + 8:W - m[2] - 8] = 1
    out[..., :3] = P.calm(out[..., :3], region, tone, keep=0.7, low=0.05, sigma=10, feather=10)
    return N.tileable(out, tuple(m), blend=16)


PAPER_PROMPT = ("an old sheet of ledger parchment, warm cream, foxed and browned at the deckled edges, small blackened iron corner "
                "caps riveted on the four corners, the middle clean and even, flat lay, isolated on black")
HINT_PROMPT = ("a small note of old parchment, warm cream, browned at the deckled edges, pinned at the top left by a square iron "
               "nail, a drop of red sealing wax at the bottom right, the middle clean, flat lay, isolated on black")


def build(ui):
    import os
    F.save(F.to_pil(make(512, 512, (32, 32, 32, 32), 3, PAPER_PROMPT, "#e4d6b6", "paper")), os.path.join(ui, "frames", "paper.png"))
    F.save(F.to_pil(make(512, 256, (40, 40, 40, 40), 5, HINT_PROMPT, "#e6d6b0", "hint", corners=False, nail=True, wax=True)),
           os.path.join(ui, "frames", "hint.png"))
