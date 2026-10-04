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
    lames = [0]
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
    yw = foot_top + 13.0
    groove = np.clip((3.6 - np.abs(Y - yw)) * S, 0, 1)
    h = h - groove * 1.2
    # A straight two-strand twist along the foot (periodic: whole turns per tile).
    pitch = TW / 56
    s = X / pitch
    d = Y - yw
    th_ = 6.0
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
        rv = np.sqrt(np.clip(1 - (dd / 3.0) ** 2, 0, 1)) * 2.2 + 12.5
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
    R.tint = (0.7 + 0.3 * np.clip(Y / foot_top, 0, 1) + 0.35 * (Y >= foot_top))[..., None] * np.ones(3, np.float32)
    R.tint = R.tint.astype(np.float32)
    img = R.render("header", samples=samples, wear=1.1, grime=0.9, seed=43)
    img = paint(img, R, "header", "a long plain band of " + IRON + ", along its foot a heavier strap "
                "with a thin twisted gold wire inlaid and nails", 0.15)
    small = R.file_size(img)
    # The middle tile, its start blended from the tile after it so it repeats without a seam.
    mid = small[:, TW:2 * TW].copy()
    nxt = small[:, 2 * TW:3 * TW]
    b = 48
    ramp = np.linspace(0, 1, b, dtype=np.float32)[None, :, None]
    mid[:, :b] = nxt[:, :b] * (1 - ramp) + mid[:, :b] * ramp
    mid[..., 3] = 1.0
    return mid


def rect_sd(X, Y, x0, y0, x1, y1, ch_top=0.0, ch_bot=0.0):
    """Signed distance inside a rectangle (file px) with its top and bottom corners cut."""
    d = np.minimum(np.minimum(X - x0, x1 - X), np.minimum(Y - y0, y1 - Y))
    if ch_top:
        d = np.minimum(d, ((X - x0) + (Y - y0) - ch_top) / math.sqrt(2))
        d = np.minimum(d, ((x1 - X) + (Y - y0) - ch_top) / math.sqrt(2))
    if ch_bot:
        d = np.minimum(d, ((X - x0) + (y1 - Y) - ch_bot) / math.sqrt(2))
        d = np.minimum(d, ((x1 - X) + (y1 - Y) - ch_bot) / math.sqrt(2))
    return d


def straight_rope(R, pts_sd, th, pitch, base, height):
    """The binders' twist along any line given its signed distance field (0 on the line) and a
    coordinate along it: here the caller passes (across, along)."""
    across, along = pts_sd
    s = along / pitch
    hgt = np.zeros_like(across)
    for k in (0.0, 0.5):
        u = ((across / th) - (((s + k) % 1.0) - 0.5)) % 1.0 - 0.5
        hgt = np.maximum(hgt, np.sqrt(np.clip(1 - (u / 0.5) ** 2, 0, 1)))
    m = np.clip((th / 2 - np.abs(across)) * R.ss + 0.5, 0, 1)
    edge = np.sqrt(np.clip(1 - (across / (th / 2)) ** 2, 0, 1))
    return base + (hgt * 0.55 + edge * 0.45) * height, m


def pillar(ss=2, samples=128):
    """The attribute's stele (frames/pillar.png, 424x728, drawn one to one over a 188x340
    control, reaching 12 past it): a narrow standing plate of planished iron, its strap and
    the binders' wire round it; at its head a round seat (a raised collar) for the 120 px
    medallion 10-130 px down; its shaft plain for the name and words; its foot a plinth
    nailed with two of the binders' coins; lamp-iron brackets at its shoulders whose arms
    run along the top and down the sides and curl outward past it. Neutral iron: the code
    draws an ember hairline when points wait."""
    W, H = 424, 728
    o = 24
    S = ss
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / S, R.yy / S
    x0, y0, x1, y1 = o, o, W - o, H - o
    sd = rect_sd(X, Y, x0, y0, x1, y1, ch_top=22, ch_bot=10)
    cover = np.clip(sd * S + 0.5, 0, 1)
    top = 8.0
    bw = 22.0
    # The strap round its edge: chamfered out, a step down to the face inside.
    def edge(d, ch, sh):
        lo = np.clip(d / ch, 0, 1) * 0.8
        hi = 0.8 + 0.2 * np.sqrt(np.clip(1 - (1 - np.clip((d - ch) / sh, 0, 1)) ** 2, 0, 1))
        return np.where(d < ch, lo, hi) * (d > 0)
    strap = edge(sd, 3.5, 1.5) * np.where(sd < bw, 1.0, 0.0) * top
    inner = sd - bw
    face = 4.0 + 0.6 * np.clip(inner / 30, 0, 1)
    step = np.clip(inner / 2.0, 0, 1)
    h = np.where(sd < bw, strap, top * (1 - step) + face * step)
    h = np.where(sd < bw - 0.5, h, np.minimum(h, np.maximum(face, top * (1 - step))))
    # The wire along the strap's middle.
    across = sd - bw / 2
    along = np.where(np.abs(X - W / 2) * (y1 - y0) > np.abs(Y - H / 2) * (x1 - x0), Y, X)
    wh, wm = straight_rope(R, (across, along), 5.2, 8.0, top - 1.0, 2.6)
    groove = np.clip((3.2 - np.abs(across)) * S / 2, 0, 1) * (sd > 0)
    h = h - groove * 1.2
    h = np.where(wm > 0.5, np.maximum(h, wh), h)
    shape = h.copy()
    # The seat at the head: a raised collar round the medallion's place.
    cx, cy = W / 2, o + 20 + 120
    rr = np.hypot(X - cx, Y - cy)
    r_in, r_out = 119.0, 143.0
    collar = band_profile(rr, r_out, r_in, top + 5.0, outer_ch=4.5, inner_ch=3.0, shoulder=2.0)
    collar = collar + np.sin(np.clip((rr - r_in) / (r_out - r_in), 0, 1) * math.pi) * 1.2 * (collar > 0)
    ch_m = (rr > r_in) & (rr < r_out)
    h = np.where(ch_m, np.maximum(h, collar), h)
    # The seat's floor inside the collar: sunk, dark (the medallion covers most of it).
    seat = rr <= r_in
    h = np.where(seat, 2.5, h)
    rw, rm = RL.rope(R, cx, cy, (r_in + r_out) / 2, 5.0, 7.0, 2.6)
    cgroove = np.clip((3.0 - np.abs(rr - (r_in + r_out) / 2)) * S / 2, 0, 1)
    h = np.where(ch_m, h - cgroove * 1.2, h)
    h = np.where(rm > 0.5, np.maximum(h, top + 3.6 + rw / S), h)
    shape = np.where(ch_m | seat, h, shape)
    # The foot: a plinth across the shaft, nailed with two coins.
    py0 = y1 - 70
    plinth_sd = np.minimum(Y - py0, sd)
    plinth = edge(plinth_sd, 3.0, 1.2) * (top + 2.5)
    pm = (Y > py0) & (sd > 0)
    h = np.where(pm, np.maximum(h, plinth), h)
    shape = np.where(pm, np.maximum(shape, plinth), shape)
    coins = np.zeros_like(X)
    holes = np.zeros_like(X)
    glow = np.zeros_like(X)
    for cxp in (x0 + 34, x1 - 34):
        cyp = y1 - 34
        chh, cm, hm = RL.coin(R, cxp, cyp, 30.0, top + 2.5, hole=0.36)
        h = np.where(cm > 0.5, np.maximum(h, chh), h)
        shape = np.where(cm > 0.5, np.maximum(shape, chh), shape)
        coins = np.maximum(coins, cm)
        holes = np.maximum(holes, hm)
        dh = np.hypot(X - cxp, Y - cyp) / (30 * 0.36 / 2)
        glow = np.maximum(glow, hm * np.exp(-dh ** 2 * 1.6))
    # The brackets at the shoulders: a coin at each top corner, arms along the top and down the
    # side, curling back outward past the stele.
    import chrome as CH
    arms = np.zeros_like(X)
    for cxp, sx in ((x0 + 10, 1), (x1 - 10, -1)):
        cyp = y0 + 10
        chh, cm, hm = RL.coin(R, cxp, cyp, 40.0, top + 1.0, hole=0.34)
        for pts in CH.bracket_scrolls(cxp, cyp, sx, 1, 54, 10, 0):
            bh, bm = RL.bar(R, pts, 12.0, 4.0)
            bh = bh + top + 0.5
            h = np.where(bm > 0.5, np.maximum(h, bh), h)
            shape = np.where(bm > 0.5, np.maximum(shape, bh), shape)
            arms = np.maximum(arms, bm)
        h = np.where(cm > 0.5, np.maximum(h, chh), h)
        shape = np.where(cm > 0.5, np.maximum(shape, chh), shape)
        coins = np.maximum(coins, cm)
        holes = np.maximum(holes, hm)
        dh = np.hypot(X - cxp, Y - cyp) / (40 * 0.34 / 2)
        glow = np.maximum(glow, hm * np.exp(-dh ** 2 * 1.6))
    facet = F.facets(R.h, R.w, cell=18.0 * S, tilt=0.022, seed=51, soften=1.5 * S) / S
    dents = RL.hammered(R, cell=7.0, depth=0.3, seed=52) / S
    plain = (wm < 0.5) & (rm < 0.5) & (coins < 0.5) & (arms < 0.5)
    h = h + (facet + dents) * plain
    cover = np.maximum(cover, np.maximum(coins, arms))
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = (shape * S * cover).astype(np.float32)
    R.alpha = cover
    R.mat[:] = RL.IDS["iron"]
    R.mat[(wm > 0.5) | (rm > 0.5)] = RL.IDS["gold"]
    R.mat[holes > 0.5] = RL.IDS["ember"]
    # The face a little darker than the strap, darker still in the seat.
    face_t = np.where((sd > bw + 2) & ~ch_m & ~pm, 0.72, 1.0)
    face_t = np.where(seat, 0.45, face_t)
    R.tint = (face_t[..., None] * np.ones(3, np.float32)).astype(np.float32)
    n = F.fbm(R.h, R.w, scale=R.w / 10, octaves=3, seed=53) * 0.5 + 0.5
    R.emit = ((glow * (0.5 + 0.6 * n))[..., None] * (F.hexc("#ff6a1a") * 0.9 + F.hexc("#8a1c04") * 0.5)).astype(np.float32)
    img = R.render("pillar", samples=samples, wear=1.2, grime=0.9, seed=54)
    img = paint(img, R, "pillar", "a tall narrow standing plate of " + IRON + ", a thin twisted gold wire inlaid round its "
                "edge, a round raised collar at its head, a plinth at its foot with two square iron coins, curled iron "
                "brackets at its top corners, its face plain and flat", 0.24,
                protect=((sd > bw + 6) & ~ch_m & ~seat & ~pm).astype(np.float32) * 0.6)
    return R.file_size(img)


def iron_card(name, W, H, o, margins, border=22.0, chamfer=10.0, crest=0.0, coin=34.0, brackets=0.0,
              oxblood=False, prompt="", denoise=0.24, ss=2, samples=128):
    """A forged card or plate as a nine-slice that repeats (UiArt Tile): a strap round it with
    the binders' wire, a binders' coin at each corner (the ember asleep in its hole), lamp-iron
    brackets at its top corners if `brackets` (their arms' length), a crest plate lapped over
    its head `crest` px deep if asked (the code tints it), a plain face. Everything that is
    one-off sits in the corners (inside `margins`, file px); the strips between repeat."""
    S = ss
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / S, R.yy / S
    x0, y0, x1, y1 = o, o, W - o, H - o
    sd = rect_sd(X, Y, x0, y0, x1, y1, ch_top=chamfer, ch_bot=chamfer)
    cover = np.clip(sd * S + 0.5, 0, 1)
    top = 8.0

    def edge(d, ch, sh):
        lo = np.clip(d / ch, 0, 1) * 0.8
        hi = 0.8 + 0.2 * np.sqrt(np.clip(1 - (1 - np.clip((d - ch) / sh, 0, 1)) ** 2, 0, 1))
        return np.where(d < ch, lo, hi) * (d > 0)
    inner = sd - border
    step = np.clip(inner / 2.0, 0, 1)
    face = 4.2
    h = np.where(sd < border, edge(sd, 3.5, 1.5) * top, top * (1 - step) + face * step)
    across = sd - border / 2
    along = np.where(np.abs(X - W / 2) * (y1 - y0) > np.abs(Y - H / 2) * (x1 - x0), Y, X)
    wh, wm = straight_rope(R, (across, along), 5.0, 8.0, top - 1.0, 2.5)
    groove = np.clip((3.0 - np.abs(across)) * S / 2, 0, 1) * (sd > 0)
    h = h - groove * 1.2
    h = np.where(wm > 0.5, np.maximum(h, wh), h)
    shape = h.copy()
    crest_m = np.zeros_like(X, bool)
    if crest:
        # The crest: a plate lapped over the card's head, its lower edge rounded over the face.
        cy1 = y0 + crest
        csd = np.minimum(np.minimum(X - (x0 + border - 2), (x1 - border + 2) - X), cy1 - Y)
        crest_m = (csd > 0) & (Y > y0 + border - 2)
        prof = face + 1.0 + 2.6 * np.sqrt(np.clip(csd / 2.5, 0, 1))
        h = np.where(crest_m, np.maximum(h, prof), h)
        shape = np.where(crest_m, np.maximum(shape, prof), shape)
        # Rivets along its foot, at the corners only (the middle repeats).
        for rx in (x0 + border + 16, x1 - border - 16):
            dd = np.hypot(X - rx, Y - (cy1 - 7))
            rv = np.sqrt(np.clip(1 - (dd / 3.0) ** 2, 0, 1)) * 2.0 + face + 3.6
            h = np.where(dd < 3.0, np.maximum(h, rv), h)
            shape = np.where(dd < 3.0, np.maximum(shape, rv), shape)
    coins = np.zeros_like(X)
    holes = np.zeros_like(X)
    glow = np.zeros_like(X)
    arms = np.zeros_like(X)
    import chrome as CH
    for cx, cy, sx, sy in ((x0 + 8, y0 + 8, 1, 1), (x1 - 8, y0 + 8, -1, 1), (x0 + 8, y1 - 8, 1, -1), (x1 - 8, y1 - 8, -1, -1)):
        if brackets and sy == 1:
            for pts in CH.bracket_scrolls(cx, cy, sx, sy, brackets, brackets * 0.18, 0):
                bh, bm = RL.bar(R, pts, coin * 0.3, coin * 0.1)
                bh = bh + top + 0.5
                h = np.where(bm > 0.5, np.maximum(h, bh), h)
                shape = np.where(bm > 0.5, np.maximum(shape, bh), shape)
                arms = np.maximum(arms, bm)
        chh, cm, hm = RL.coin(R, cx, cy, coin, top + 1.0, hole=0.34)
        h = np.where(cm > 0.5, np.maximum(h, chh), h)
        shape = np.where(cm > 0.5, np.maximum(shape, chh), shape)
        coins = np.maximum(coins, cm)
        holes = np.maximum(holes, hm)
        dh = np.hypot(X - cx, Y - cy) / (coin * 0.34 / 2)
        glow = np.maximum(glow, hm * np.exp(-dh ** 2 * 1.6))
    facet = F.facets(R.h, R.w, cell=18.0 * S, tilt=0.02, seed=61, soften=1.5 * S) / S
    dents = RL.hammered(R, cell=7.0, depth=0.28, seed=62) / S
    plain = (wm < 0.5) & (coins < 0.5) & (arms < 0.5)
    h = h + (facet + dents) * plain
    cover = np.maximum(cover, np.maximum(coins, arms))
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = (shape * S * cover).astype(np.float32)
    R.alpha = cover
    R.mat[:] = RL.IDS["iron"]
    R.mat[wm > 0.5] = RL.IDS["gold"]
    R.mat[holes > 0.5] = RL.IDS["ember"]
    face_m = (sd > border + 2) & ~crest_m
    t = np.where(face_m, 0.72, 1.0)
    # The crest a shade paler, so the code's tint reads on it.
    t = np.where(crest_m, 1.25, t)
    tint = t[..., None] * np.ones(3, np.float32)
    if oxblood:
        # Oxblood stain soaked into the iron, uneven, darkest in the hollows.
        n = F.fbm(R.h, R.w, scale=R.w / 5, octaves=5, seed=63) * 0.5 + 0.5
        stain = (np.clip(0.45 + 0.7 * n, 0, 1) * np.where(face_m, 1.0, 0.3))[..., None]
        ox = np.array([2.3, 0.75, 0.6], np.float32)
        tint = tint * (1 - stain + stain * ox) * np.where(face_m, 1.25, 1.0)[..., None]
    R.tint = tint.astype(np.float32)
    n2 = F.fbm(R.h, R.w, scale=R.w / 10, octaves=3, seed=64) * 0.5 + 0.5
    R.emit = ((glow * (0.5 + 0.6 * n2))[..., None] * (F.hexc("#ff6a1a") * 0.9 + F.hexc("#8a1c04") * 0.5)).astype(np.float32)
    img = R.render(name, samples=samples, wear=1.2, grime=0.9, seed=65)
    # The face and the crest keep most of their render: plain, so words and the code's tint sit on them.
    img = paint(img, R, name, prompt, denoise, protect=((face_m | crest_m).astype(np.float32) * 0.6))
    small = R.file_size(img)
    import nineslice as N
    l, t_, r_, b = margins
    small = N.tileable(small, (l, t_, r_, b), blend=max(4, min(l, t_) // 10))
    return small


def crest_card():
    return iron_card("crest_card", 600, 700, 20, (80, 144, 80, 80), crest=116, coin=36, brackets=40,
                     prompt="an empty tall card of " + IRON + ", a thin twisted gold wire inlaid round its edge, a plain "
                     "paler iron crest plate riveted across its head, square iron coins with round holes at the corners, "
                     "curled iron brackets at its top corners, its face plain and flat")


def crest_row():
    # A row has no room for a crest plate: the code's tint across its top is its crest.
    return iron_card("crest_row", 600, 184, 16, (80, 72, 80, 56), border=18, chamfer=8, coin=28, denoise=0.2,
                     prompt="an empty wide low plate of " + IRON + ", a thin twisted gold wire inlaid round its edge, "
                     "small square iron coins at the corners, its face plain and flat")


def banner():
    return iron_card("banner", 512, 192, 8, (48, 28, 48, 28), border=18, chamfer=8, coin=30, brackets=30, oxblood=True,
                     prompt="an empty wide plate of hand-forged iron stained dark oxblood red, hammer marks, worn edges, a thin "
                     "twisted gold wire inlaid round its edge, square iron coins at the corners, curled iron brackets "
                     "at its top corners, its face plain and flat")


def book(samples=96):
    """The Journal lying open (book/open.png, 3400x1704, 1700x852 shown): the survivor's
    ledger in a cover of oxblood leather worn at its edges, blind-tooled with a double line,
    its corners shod in the house's iron caps each nailed with a binders' coin. Two pages of
    laid rag paper curving down into the gutter, where the stitching shows, the page block's
    edges stacked along the outer sides and the foot. The pages are blank and even where the
    words go (78 in from the cover's outer edges, 34 from the spine, 68 from top and foot)."""
    W, H = 3400, 1704
    S = 1
    R = RL.Relief(W, H, S)
    X, Y = R.xx, R.yy
    k = 2.0  # file px per shown px
    cx = W / 2
    # The cover.
    cov = rect_sd(X, Y, 0, 0, W, H)
    cover_h = np.clip(cov / (4 * k), 0, 1) ** 0.6 * 7 * k
    # The page block: inset from the cover's edges, two pages meeting at the gutter.
    m_out, m_tb = 34 * k, 26 * k
    blk = rect_sd(X, Y, m_out, m_tb, W - m_out, H - m_tb)
    page = blk > 0
    gd = np.abs(X - cx)                       # from the gutter
    # The pages' surface: down into the gutter, up to a crown, rolling off at the outer edge.
    # Like a cylinder near the spine: the leaf bends down into the fold.
    rise = 1 - np.exp(-(gd / (150 * k)) ** 1.3)
    roll = np.clip(blk / (14 * k), 0, 1) ** 0.5
    page_h = (8 * k + 26 * k * rise) * (0.86 + 0.14 * roll)
    # The block's edge: stacked leaves along the outer sides and the foot, a step per leaf.
    leaves = np.clip(-blk / (3.0 * k), 0, 1)
    stack = (blk > -6 * k) & (blk <= 0) & ((np.abs(X - cx) > W / 2 - m_out - 2 * k) | (Y > H - m_tb - 2 * k))
    stack_h = 9 * k - np.floor(np.clip(-blk, 0, None) / (1.2 * k)) * 0.8 * k
    h = cover_h.copy()
    h = np.where(stack, np.maximum(h, stack_h), h)
    h = np.where(page, np.maximum(h, page_h), h)
    # The gutter: a deep fold and the sewing (four stitches of linen thread).
    fold = np.exp(-(gd / (4 * k)) ** 2) * 5 * k
    h = np.where(page, h - fold, h)
    stitch = np.zeros_like(X)
    for sy in (0.2, 0.4, 0.6, 0.8):
        y0 = m_tb + (H - 2 * m_tb) * sy
        d = np.hypot(np.clip(np.abs(Y - y0) - 9 * k, 0, None), X - cx)
        stitch = np.maximum(stitch, np.clip((1.1 * k - d) / (0.5 * k), 0, 1))
    h = np.where(stitch > 0, np.maximum(h, 3 * k + stitch * 1.0 * k), h)
    # The tooling: a double line pressed into the leather round the cover.
    t1 = np.abs(cov - 9 * k) < 0.9 * k
    t2 = np.abs(cov - 13 * k) < 0.6 * k
    tool = (t1 | t2) & ~page & ~stack
    h = np.where(tool, h - 1.6 * k, h)
    shape = h.copy()
    # The iron caps at the cover's corners, each a forged triangle with a coin nailed through.
    caps = np.zeros_like(X)
    holes = np.zeros_like(X)
    glow = np.zeros_like(X)
    for (sx, sy, x0, y0) in ((1, 1, 0, 0), (-1, 1, W, 0), (1, -1, 0, H), (-1, -1, W, H)):
        u = (X - x0) * sx
        v = (Y - y0) * sy
        L = 70 * k
        tri = (u + v < L) & (u > -2) & (v > -2)
        dtri = np.minimum(np.minimum(u, v), (L - u - v) / math.sqrt(2))
        cap_h = 10 * k + np.clip(dtri / (3 * k), 0, 1) * 3 * k
        h = np.where(tri, np.maximum(h, cap_h), h)
        shape = np.where(tri, np.maximum(shape, cap_h), shape)
        caps = np.maximum(caps, tri.astype(np.float32))
        ccx, ccy = x0 + sx * 20 * k, y0 + sy * 20 * k
        chh, cm, hm = RL.coin(R, ccx, ccy, 22 * k, 12.5 * k, hole=0.34)
        h = np.where(cm > 0.5, np.maximum(h, chh), h)
        shape = np.where(cm > 0.5, np.maximum(shape, chh), shape)
        caps = np.maximum(caps, cm)
        holes = np.maximum(holes, hm)
        dh = np.hypot(X - ccx, Y - ccy) / (22 * k * 0.34 / 2)
        glow = np.maximum(glow, hm * np.exp(-dh ** 2 * 1.6))
    # Grain: the leather's pebble, the paper's fibre (fine, so the pages stay even).
    grain_l = F.fbm(H, W, scale=3.0 * k, octaves=3, seed=71)
    grain_p = F.fbm(H, W, scale=1.2 * k, octaves=2, seed=72)
    cockle = F.fbm(H, W, scale=90 * k, octaves=3, seed=73)
    leather = ~page & ~stack & (caps < 0.5)
    h = h + np.where(leather, grain_l * 0.6 * k, 0) + np.where(page, grain_p * 0.08 * k + cockle * 0.35 * k, 0)
    R.height = h.astype(np.float32)
    R.shape_height = shape.astype(np.float32)
    R.alpha = np.ones_like(X)
    R.mat[:] = RL.IDS["leather"]
    R.mat[page | stack] = RL.IDS["paper"]
    R.mat[(caps > 0.5)] = RL.IDS["iron"]
    R.mat[holes > 0.5] = RL.IDS["ember"]
    R.mat[stitch > 0.5] = RL.IDS["bone"]
    # Colour: the leather blotched and darkest in its hollows; the paper cream, browning only
    # at its rims (away from the words), the stacked edges a little darker.
    cloud = F.fbm(H, W, scale=120 * k, octaves=4, seed=74) * 0.5 + 0.5
    t = np.ones((H, W), np.float32)
    t = np.where(leather, 0.75 + 0.5 * cloud, t)
    rim = np.clip(1 - blk / (30 * k), 0, 1) ** 2 * page
    # The gutter's shade: the leaves bend away from the light into the fold.
    gut = np.exp(-(gd / (55 * k)) ** 1.4)
    t = np.where(page, (1 - 0.18 * rim) * (0.985 + 0.03 * cloud) * (1 - 0.5 * gut), t)
    t = np.where(stack, 0.62, t)
    tint = t[..., None] * np.ones(3, np.float32)
    tint = np.where(page[..., None], tint * (1 - rim[..., None] * np.array([0.0, 0.08, 0.2], np.float32)), tint)
    # Laid paper: the chain lines (a faint darker line every 26 px shown, across the leaf) and
    # the laid lines (finer, along it), and flecks of rag; ivory, not pink.
    wob = F.fbm(H, W, scale=200 * k, octaves=2, seed=78) * 3 * k
    chain = np.exp(-(((X - cx + wob) % (52 * k) - 26 * k) / (1.6 * k)) ** 2) * 0.014
    laid = (0.5 + 0.5 * np.sin(Y / (1.6 * k) * math.pi)) * 0.012
    fleck = np.clip(F.fbm(H, W, scale=0.8 * k, octaves=1, seed=77) - 0.75, 0, 1) * 0.25
    tint = np.where(page[..., None], tint * (1 - chain - laid - fleck)[..., None] * np.array([0.985, 1.02, 0.93], np.float32), tint)
    R.tint = tint.astype(np.float32)
    n2 = F.fbm(H, W, scale=W / 40, octaves=3, seed=75) * 0.5 + 0.5
    R.emit = ((glow * (0.5 + 0.6 * n2))[..., None] * (F.hexc("#ff6a1a") * 0.9 + F.hexc("#8a1c04") * 0.5)).astype(np.float32)
    img = R.render("book_open", samples=samples, wear=1.0, grime=0.8, seed=76)
    return R, img, page


def book_final():
    R, img, page = book()
    import paintover as PO
    key = hashlib.sha1(np.ascontiguousarray((img[::4, ::4] * 255).astype(np.uint8)).tobytes()).hexdigest()[:8]
    # The pages keep their render (blank and even, where the words go); the cover takes the hand.
    protect = cv2.GaussianBlur(page.astype(np.float32), (0, 0), 6) * 0.85
    lit = cv2.GaussianBlur((R.emit.max(axis=2) > 0.04).astype(np.float32), (0, 0), 3)
    protect = np.maximum(protect, np.clip(lit * 1.5, 0, 1))
    out = PO.paint(img, "an open old leather-bound ledger seen from above, dark oxblood leather cover worn at the "
                   "edges, blind-tooled lines, forged iron corner caps with square coins, two blank cream laid paper pages, "
                   "isolated on a pure black background", f"book_{key}", denoise=0.24, seed=11, target=2048,
                   keep_light=0.75, protect=protect)
    return out


def ribbon(ss=4, samples=128):
    """A section's ribbon in the Journal (book/ribbon.png, 264x172, stretched to 132x66-86):
    a length of pale ivory silk laid over the book's head, its foot cut in a swallowtail, a
    soft fold or two along it, its edges turned and stitched. The code dyes it the section's
    colour and casts its shadow, so it is painted pale and even."""
    W, H = 264, 172
    S = ss
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / S, R.yy / S
    side = 8.0
    notch = 30.0
    # The swallowtail: the foot cut in a V from both corners up to the middle.
    foot = H - 2 - notch * (1 - np.abs(X - W / 2) / (W / 2 - side))
    sd = np.minimum(np.minimum(X - side, W - side - X), np.minimum(Y + 50, foot - Y))
    cover = np.clip(sd * S + 0.5, 0, 1)
    # Folds along its length, a slight belly, the turned hems at its sides.
    u = (X - side) / (W - 2 * side)
    folds = 2.2 * np.sin(u * math.pi * 2.0 + 0.6) + 1.2 * np.sin(u * math.pi * 5.0 + 1.3)
    belly = 5.0 * np.sin(np.clip(u, 0, 1) * math.pi)
    hem = np.exp(-(np.clip(sd, 0, None) / 2.2) ** 2) * 1.6
    h = 6.0 + folds + belly + hem
    # The stitch line just inside each side.
    for xs in (side + 5.5, W - side - 5.5):
        st = (np.abs(X - xs) < 0.7) & ((Y % 6.0) < 3.6) & (Y < foot - 4)
        h = np.where(st, h - 0.6, h)
    weave = F.fbm(R.h, R.w, scale=0.6 * S, octaves=1, seed=81) * 0.08
    h = h + weave * (sd > 0)
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = R.height
    R.alpha = cover
    R.mat[:] = RL.IDS["silk"]
    img = R.render("ribbon", samples=samples, wear=0.0, grime=0.3, seed=82, grain=0.2)
    return R.file_size(img)


def plaque_rule(ss=8, samples=128):
    """The rule beside a page's name (ornaments/plaque_rule.png, 480x24, drawn to the title's
    right and mirrored to its left, stretched 90-180 px): at its left end, toward the words,
    a binders' coin with the ember asleep in it; from it the twisted gold wire runs out,
    thinning, and ends in a small knop."""
    W, H = 480, 24
    S = ss
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / S, R.yy / S
    cy = H / 2
    x0, x1 = 22.0, W - 8.0
    t = np.clip((X - x0) / (x1 - x0), 0, 1)
    th = 7.0 - 3.6 * t
    across = Y - cy
    s_ = X / 3.2
    hgt = np.zeros_like(X)
    for k in (0.0, 0.5):
        uu = ((across / th) - (((s_ + k) % 1.0) - 0.5)) % 1.0 - 0.5
        hgt = np.maximum(hgt, np.sqrt(np.clip(1 - (uu / 0.5) ** 2, 0, 1)))
    wm = np.clip((th / 2 - np.abs(across)) * S + 0.5, 0, 1) * (X > x0 - 4) * (X < x1)
    edge = np.sqrt(np.clip(1 - (across / (th / 2)) ** 2, 0, 1))
    h = np.where(wm > 0.5, (hgt * 0.55 + edge * 0.45) * th * 0.6 + 1.0, 0)
    # The knop at the far end.
    dk = np.hypot(X - x1, Y - cy)
    knop = np.clip((3.0 - dk) * S + 0.5, 0, 1)
    h = np.where(knop > 0.5, np.maximum(h, np.sqrt(np.clip(1 - (dk / 3.0) ** 2, 0, 1)) * 3.0 + 1.0), h)
    chh, cm, hm = RL.coin(R, 12.0, cy, 18.0, 1.0, hole=0.38)
    h = np.where(cm > 0.5, np.maximum(h, chh), h)
    cover = np.maximum(np.maximum(wm, knop), cm)
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = R.height
    R.alpha = cover
    R.mat[:] = RL.IDS["gold"]
    R.mat[cm > 0.5] = RL.IDS["iron"]
    R.mat[hm > 0.5] = RL.IDS["ember"]
    dh = np.hypot(X - 12.0, Y - cy) / (18 * 0.38 / 2)
    glow = hm * np.exp(-dh ** 2 * 1.4)
    R.emit = (glow[..., None] * (F.hexc("#ff7a22") * 1.4 + F.hexc("#a02404") * 0.6)).astype(np.float32)
    img = R.render("plaque_rule", samples=samples, wear=0.8, grime=0.5, seed=83)
    return R.file_size(img)


def save(img, rel):
    F.save(F.to_pil(img), os.path.join(UI, rel))


BUILD = {
    "header": ("frames/header.png", header),
    "pillar": ("frames/pillar.png", pillar),
    "crest_card": ("frames/crest_card.png", crest_card),
    "crest_row": ("frames/crest_row.png", crest_row),
    "banner": ("frames/banner.png", banner),
    "book": ("book/open.png", book_final),
    "ribbon": ("book/ribbon.png", ribbon),
    "plaque_rule": ("ornaments/plaque_rule.png", plaque_rule),
}


def build(name):
    rel, fn = BUILD[name]
    save(fn(), rel)


if __name__ == "__main__":
    for nm in sys.argv[1:] or list(BUILD):
        build(nm)
        print("built", nm, flush=True)
