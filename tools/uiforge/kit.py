"""The reduced kit (the owner, on the ornate pages: "those borders are just ugly, adding more
of them doesn't make them better"; "ai looking", "not rooted in ui research"). One frame per
screen, the outer window, worn and plain; inside it only quiet tonal panels, recessed tiles
and thin rules, so the material and the words carry the page and ember is kept for meaning.

Each piece is drawn flat in numpy at twice its shown size (nothing here wants a render): a
panel is a tone laid over the page's vellum, translucent, so the vellum's grain shows through
it at its own scale instead of a texture stretched with the slice.

    python tools/uiforge/kit.py            # into tools/comfy/out/uiforge/kit/ (to judge)
    python tools/uiforge/kit.py --apply    # over the named frames in godot/art/ui/

  tonal     a raised panel: a shade lighter than the page, a soft light along its top edge,
            a hairline barely there, a soft shadow under it (pillars, slabs, the figure's panel)
  recessed  a sunk tile: darker than the page, shaded under its top edge, a faint light along
            its foot, no border (wells: empty trait places, empty slots)
  column    a page's column: only a faint shade under its head, falling away; no rules
  rule      the gutter between columns: a single thin rule fading at both ends
"""
from __future__ import annotations

import os
import shutil
import sys

import numpy as np

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui")
OUT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "kit")
K = 2.0

# The page's ground is about #191517; a raised panel sits a step above it, a sunk one a step below.
RAISED = np.array([0.20, 0.18, 0.21], np.float32)     # sRGB, laid at RAISED_A over the vellum
RAISED_A = 0.42
SUNK = np.array([0.03, 0.026, 0.035], np.float32)
SUNK_A = 0.5
HAIR = np.array([0.80, 0.72, 0.60], np.float32)       # warm grey, the faintest line


def box_sd(W, H, inset, r):
    """Signed distance (shown px, positive inside) to a rounded box `inset` in from the file's edge."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x, y = (xx + 0.5) / K, (yy + 0.5) / K
    w, h = W / K, H / K
    qx = np.abs(x - w / 2) - (w / 2 - inset - r)
    qy = np.abs(y - h / 2) - (h / 2 - inset - r)
    out = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    return -out, x, y


def over(dst, rgb, a):
    """Lay colour `rgb` at coverage `a` over the straight-alpha RGBA `dst`."""
    a = a[..., None] if a.ndim == 2 else a
    da = dst[..., 3:4]
    oa = a + da * (1 - a)
    col = (np.broadcast_to(rgb, dst[..., :3].shape) * a + dst[..., :3] * da * (1 - a)) / np.maximum(oa, 1e-4)
    return np.concatenate([col, oa], -1)


def tonal(Ws, Hs, out=0, radius=2.0, lift_px=40.0):
    """A raised tonal panel, Ws x Hs shown px, with `out` px of clear margin for a slice that
    reaches past its control. The light along its top keeps within `lift_px`, inside the
    slice's top margin, so a tiled middle stays even."""
    W, H = int(Ws * K), int(Hs * K)
    sd, x, y = box_sd(W, H, out, radius)
    img = np.zeros((H, W, 4), np.float32)
    # Its soft shadow on the page, down and a little right.
    sh_sd, _, _ = box_sd(W, H, out, radius)
    sh = np.clip((np.roll(np.roll(sh_sd, int(2 * K), 0), int(1 * K), 1) + 4) / 6, 0, 1) * 0.35 * (sd < 0.5)
    img = over(img, np.zeros(3, np.float32), sh)
    inside = np.clip(sd * K + 0.5, 0, 1)
    # The tone: a little lighter toward its top, as if the page's light fell on it.
    top = y - out
    lift = 1.0 + 0.08 * np.clip(1 - top / lift_px, 0, 1)
    img = over(img, np.clip(RAISED * lift[..., None], 0, 1), inside * RAISED_A)
    # Light along its top edge, a hairline round it barely there.
    edge_light = np.clip(1 - np.abs(top - 0.75) / 0.75, 0, 1) * (sd > 0) * np.clip((Ws - 2 * out - 2 * radius - np.abs(x - Ws / 2) * 2) / 8, 0, 1)
    img = over(img, HAIR, edge_light * 0.16)
    hair = np.clip(1 - np.abs(sd - 0.5) / 0.6, 0, 1)
    img = over(img, HAIR, hair * 0.07)
    return img


def recessed(Ws, Hs, radius=2.0):
    """A sunk tile: darker than the page, its top edge casting a shade into it, a faint light
    along its foot where the page's edge turns; no border."""
    W, H = int(Ws * K), int(Hs * K)
    sd, x, y = box_sd(W, H, 0, radius)
    inside = np.clip(sd * K + 0.5, 0, 1)
    img = np.zeros((H, W, 4), np.float32)
    img = over(img, SUNK, inside * SUNK_A)
    shade = np.clip(1 - y / 7.0, 0, 1) ** 1.5 * 0.45 + np.clip(1 - x / 5.0, 0, 1) ** 1.5 * 0.25
    img = over(img, np.zeros(3, np.float32), inside * np.clip(shade, 0, 0.6))
    foot = np.clip(1 - np.abs((Hs - y) - 0.75) / 0.75, 0, 1) * inside
    img = over(img, HAIR, foot * 0.07)
    return img


def column(Ws=128, Hs=512):
    """A column: a faint shade under its head, falling away down it, soft at its sides."""
    W, H = int(Ws * K), int(Hs * K)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    y, x = yy / K, xx / K
    a = (0.30 * np.clip(1 - y / (Hs * 0.85), 0, 1) ** 1.2) * np.clip(np.minimum(x, Ws - x) / 10, 0, 1)
    img = np.zeros((H, W, 4), np.float32)
    return over(img, np.array([0.025, 0.02, 0.03], np.float32), a)


def rule(Ws=24, Hs=560, end=24):
    """The gutter's rule: one thin line, warm grey, fading over the slice's ends."""
    W, H = int(Ws * K), int(Hs * K)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    y, x = yy / K, (xx + 0.5) / K
    line = np.clip(1 - np.abs(x - Ws / 2) / 0.6, 0, 1)
    fade = np.clip(y / end, 0, 1) * np.clip((Hs - y) / end, 0, 1)
    img = np.zeros((H, W, 4), np.float32)
    return over(img, HAIR, line * fade * 0.16)


# What each piece replaces, at the size its slice in UiArt.cs expects (shown px).
PIECES = {
    "frames/pillar.png": lambda: tonal(212, 364, out=12),        # 188 x 340 control, Out 12
    "frames/slab.png": lambda: tonal(64, 64, lift_px=10),
    "frames/well.png": lambda: recessed(64, 64),
    "frames/slot.png": lambda: recessed(64, 64, radius=1.5),
    "frames/hero_plate.png": lambda: tonal(256, 256, out=12),    # Out 12
    "frames/column.png": column,
    "frames/column_divider.png": rule,
}
# Pieces the kit has no place for: ornament that the reduced page does without.
DROP = ["frames/column_divider_stone.png"]


def plain_bands():
    """The outer window's bands worn plain (pages.binding without gilt or wire; a render)."""
    import pages
    return {"frames/header.png": pages.header_plain, "frames/footer.png": pages.footer_plain}


def main(apply=False):
    dst_root = UI if apply else OUT
    for rel, fn in {**PIECES, **plain_bands()}.items():
        p = os.path.join(dst_root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        F.save(F.to_pil(np.clip(fn(), 0, 1)), p)
        print("kit", rel)
    if apply:
        for rel in DROP:
            for p in (os.path.join(UI, rel), os.path.join(UI, rel) + ".import"):
                if os.path.exists(p):
                    os.makedirs(os.path.join(OUT, "dropped"), exist_ok=True)
                    shutil.move(p, os.path.join(OUT, "dropped", os.path.basename(p)))
                    print("dropped", rel)


if __name__ == "__main__":
    main("--apply" in sys.argv[1:])
