"""Frames modelled as reliefs (relief.py) where their shape is their own, not a strap round
a rectangle: the page's header band, the banner, the attribute pillar.

  header  (frames/header.png, 512x200, 256x100 shown, foot border 12, tiled along its
          length): the lintel across the top of every page. Lames of blackened iron lapped
          and riveted, and along its foot a heavier strap with the binders' wire and a nail
          every hand's width. Repeats every 512 px without a seam.
  banner  (frames/banner.png, 512x192, 256x96 shown, 24 14 24 14): a verdict or a name
          cut in metal: an oxblood-stained iron plate hung from two lamp-iron brackets.
  pillar  (frames/pillar.png, 424x728, 212x364 shown, drawn one to one): an attribute's
          stele: a round seat at its head for the medallion, its shaft for the words, a
          foot nailed down, brackets at its shoulders.

    python tools/uiforge/pieces.py [header banner pillar]
"""
from __future__ import annotations

import hashlib
import math
import os
import sys

import cv2
import numpy as np

import forge as F
import relief as RL
from medals import band_profile, smoothstep  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui")

IRON = ("hand-forged blackened iron, hammer marks, pitted and worn edges, soot in the hollows")


def paint(img, R, name, prompt, denoise, protect=None):
    import paintover as PO
    key = hashlib.sha1(np.ascontiguousarray((img * 255).astype(np.uint8)).tobytes()).hexdigest()[:8]
    small = np.isin(R.mat, [RL.IDS["gold"], RL.IDS["chain"]]).astype(np.float32)
    pr = cv2.dilate(small, np.ones((3, 3), np.uint8), iterations=max(1, R.ss // 2)) * 0.7
    lit = cv2.GaussianBlur((R.emit.max(axis=2) > 0.04).astype(np.float32), (0, 0), 1.5 * R.ss)
    pr = np.maximum(pr, np.clip(lit * 1.5, 0, 1))
    if protect is not None:
        pr = np.maximum(pr, protect)
    return PO.paint(img, prompt + ", isolated on a pure black background, seen straight on", f"{name}_{key}",
                    denoise=denoise, seed=11, keep_light=0.75, protect=pr)


def header(ss=2, samples=128):
    TW, H = 512, 200
    tiles = 3
    W = TW * tiles
    S = ss
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / S, R.yy / S
    foot_top = H - 24
    # The lames: plates lapped downward (each overlaps the one below), riveted at the laps.
    h = np.zeros_like(X)
    lames = [0, 62, 120]
    for i, y0 in enumerate(lames):
        y1 = lames[i + 1] + 6 if i + 1 < len(lames) else foot_top + 4
        # A lame: flat, its lower edge rounded over the next one.
        d_low = y1 - Y
        # Tilted out at its foot (it laps over the next), its lower edge rounded over.
        t = np.clip((Y - y0) / max(y1 - y0, 1), 0, 1)
        prof = 2.5 + 3.5 * t * np.sqrt(np.clip(d_low / 2.5, 0, 1))
        h = np.where((Y >= y0) & (Y < y1), np.maximum(h, prof), h)
    # The foot: a heavier strap, chamfered, the wire laid in it.
    foot = band_profile(-Y, -(foot_top - 0.0), -(H + 3.0), 12.0, outer_ch=3.5, inner_ch=2.0, shoulder=1.5)
    h = np.maximum(h, np.where(Y >= foot_top - 2, foot + 0.5, 0))
    yw = foot_top + 11.5
    groove = np.clip((3.0 - np.abs(Y - yw)) * S, 0, 1)
    h = h - groove * 1.2
    # A straight two-strand twist along the foot (periodic: whole turns per tile).
    pitch = TW / 56
    s = X / pitch
    d = Y - yw
    th_ = 4.6
    hgt = np.zeros_like(X)
    for k in (0.0, 0.5):
        u = ((d / th_) - (((s + k) % 1.0) - 0.5)) % 1.0 - 0.5
        hgt = np.maximum(hgt, np.sqrt(np.clip(1 - (u / 0.5) ** 2, 0, 1)))
    wm = np.clip((th_ / 2 - np.abs(d)) * S + 0.5, 0, 1)
    edge = np.sqrt(np.clip(1 - (d / (th_ / 2)) ** 2, 0, 1))
    wire_h = 11.0 + (hgt * 0.55 + edge * 0.45) * 3.0
    h = np.where(wm > 0.5, np.maximum(h, wire_h), h)
    shape = h.copy()
    # Rivets at the laps and nails along the foot, a hand's width apart (whole per tile).
    for i, y0 in enumerate(lames[1:]):
        for k in range(4 * tiles):
            x0 = (k + 0.5 + 0.5 * (i % 2)) * TW / 4
            dd = np.hypot(X - x0, Y - (y0 + 3.0))
            rv = np.sqrt(np.clip(1 - (dd / 3.2) ** 2, 0, 1)) * 2.4 + 6.0
            h = np.where(dd < 3.2, np.maximum(h, rv), h)
            shape = np.where(dd < 3.2, np.maximum(shape, rv), shape)
    for k in range(8 * tiles):
        x0 = (k + 0.5) * TW / 8
        dd = np.hypot(X - x0, Y - (foot_top + 5.0))
        rv = np.sqrt(np.clip(1 - (dd / 2.8) ** 2, 0, 1)) * 2.0 + 12.5
        h = np.where(dd < 2.6, np.maximum(h, rv), h)
        shape = np.where(dd < 2.6, np.maximum(shape, rv), shape)
    facet = F.facets(R.h, R.w, cell=16.0 * S, tilt=0.025, seed=41, soften=1.5 * S, elong=0.5) / S
    dents = RL.hammered(R, cell=7.0, depth=0.3, seed=42) / S
    h = h + (facet + dents) * (wm < 0.5) * (groove < 0.5)
    R.height = (h * S).astype(np.float32)
    R.shape_height = (shape * S).astype(np.float32)
    R.alpha = np.ones_like(X)
    R.mat[:] = RL.IDS["iron"]
    R.mat[wm > 0.5] = RL.IDS["gold"]
    # The lames darker toward the top (the band runs off the screen there).
    R.tint = (0.7 + 0.3 * np.clip(Y / foot_top, 0, 1))[..., None] * np.ones(3, np.float32)
    R.tint = R.tint.astype(np.float32)
    img = R.render("header", samples=samples, wear=1.1, grime=0.9, seed=43)
    img = paint(img, R, "header", "a long band of lapped plates of " + IRON + ", riveted, along its foot a heavier strap "
                "with a thin twisted gold wire inlaid and nails", 0.18)
    small = R.file_size(img)
    # The middle tile, its start blended from the tile after it so it repeats without a seam.
    mid = small[:, TW:2 * TW].copy()
    nxt = small[:, 2 * TW:3 * TW]
    b = 48
    ramp = np.linspace(0, 1, b, dtype=np.float32)[None, :, None]
    mid[:, :b] = nxt[:, :b] * (1 - ramp) + mid[:, :b] * ramp
    mid[..., 3] = 1.0
    return mid


def save(img, rel):
    F.save(F.to_pil(img), os.path.join(UI, rel))


BUILD = {
    "header": ("frames/header.png", header),
}


def build(name):
    rel, fn = BUILD[name]
    save(fn(), rel)


if __name__ == "__main__":
    for nm in sys.argv[1:] or list(BUILD):
        build(nm)
        print("built", nm, flush=True)
