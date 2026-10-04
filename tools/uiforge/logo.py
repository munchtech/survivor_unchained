"""The title's logo (title/logo.png) modelled as a relief: SURVIVOR over UNCHAINED in the
game's own capitals (Cinzel, at its heaviest), cut from forged steel with a deep chamfer that
takes the light, lightly planished, the edges worn bright; between
the words the binders' seven-link chain, its middle link pried open and the Morrow's ember
awake in the break, the chain's ends made fast to strap iron that runs out under the words
and ends in the binders' square-holed coins. Rendered in Blender under the house light, then
given the hand on the local Krea, kept exact where it is small or burns.

The painted logo it replaces was read from words alone: its letters wandered (the U, the H,
the A were not true shapes). These are the font's.

    python tools/uiforge/logo.py           # render, paint, write godot/art/ui/title/logo.png
"""
from __future__ import annotations

import hashlib
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import forge as F
import relief as RL

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui")
# Cinzel's variable font (OFL, google/fonts) at weight 900: the game's display face, with a
# title's weight (at 600 and wide-set it read like a book's cover, not a game's name).
FONT = os.path.join(HERE, "fonts", "Cinzel-wght.ttf")
WEIGHT = 900

W, H = 1400, 440          # file px (shown at half: 700 x 220)
CX = 708                  # the words' middle, a little right of the file's (the old logo's place)

# Each line: its text, cap height (file px), tracking (file px), the baseline's y, and the
# letters drawn taller (each word's first, as a carved title would have it).
LINES = (
    ("SURVIVOR", 124, -3, 156, {0: 1.16}),
    ("UNCHAINED", 98, 0, 388, {0: 1.16}),
)
CHAIN_Y = 230             # the chain's middle
LINK_L, LINK_W, WIRE = 106, 50, 9.2   # a link's outer length and width, the wire's half-thickness
PITCH = 82                # link to link


def font(size):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([WEIGHT])
    return f


def text_mask(ss):
    """The words at render resolution (1 inside), and each letter's own box for its grain."""
    img = Image.new("L", (W * ss, H * ss), 0)
    d = ImageDraw.Draw(img)
    for text, cap, track, base, big in LINES:
        # The font's size for this cap height (Cinzel's capitals stand ~0.7 of the em).
        f0 = font(100)
        hcap = f0.getbbox("H")[3] - f0.getbbox("H")[1]
        sizes = [cap * big.get(i, 1.0) / hcap * 100 for i in range(len(text))]
        fonts = [font(int(round(s * ss))) for s in sizes]
        widths = [f.getbbox(ch)[2] - f.getbbox(ch)[0] for f, ch in zip(fonts, text)]
        total = sum(widths) + track * ss * (len(text) - 1)
        x = CX * ss - total / 2
        for ch, f, wd in zip(text, fonts, widths):
            bb = f.getbbox(ch)
            # Every letter stands on the line (its bottom on the baseline).
            d.text((x - bb[0], base * ss - bb[3]), ch, font=f, fill=255)
            x += wd + track * ss
    return np.asarray(img, np.float32) / 255


def signed(mask, ss):
    """Signed distance in file px, positive inside."""
    m = (mask > 0.5).astype(np.uint8)
    din = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    dout = cv2.distanceTransform(1 - m, cv2.DIST_L2, 5)
    return (din - dout) / ss


def stadium(X, Y, cx, cy, length, width, angle=0.0):
    """Distance from a link's centre line (a stadium's spine ring), file px."""
    c, s = math.cos(angle), math.sin(angle)
    u = (X - cx) * c + (Y - cy) * s
    v = -(X - cx) * s + (Y - cy) * c
    r = width / 2
    half = length / 2 - r
    du = np.clip(np.abs(u) - half, 0, None)
    return np.abs(np.hypot(du, v) - r), u, v


def build(ss=3, samples=128, denoise=0.22):
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / ss, R.yy / ss
    # --- the letters: a chamfered edge to a planished face.
    tm = text_mask(ss)
    sd = signed(tm, ss)
    cover = np.clip(sd * ss + 0.5, 0, 1)
    # A deep chamfer (45 degrees, 6 px) to a face crowned a little: the chamfer takes the
    # light as a bright edge, the face holds the planishing.
    top, ch = 9.0, 6.0
    t = np.clip(sd / ch, 0, 1)
    crown = np.clip((sd - ch) / 10.0, 0, 1) * 1.6
    letters = (t * top + crown) * (sd > 0)
    shape = letters.copy()
    facet = F.facets(R.h, R.w, cell=22.0 * ss, tilt=0.012, seed=41, soften=2.0 * ss) / ss
    dents = RL.hammered(R, cell=6.0, depth=0.12, seed=42) / ss
    face = np.clip((sd - ch) / 1.5, 0, 1)
    letters = letters + (facet + dents) * face
    h = letters
    mat = np.full(X.shape, RL.IDS["steel"], np.int32)
    alpha = cover
    # --- the chain: seven links, flat and on edge by turns, the middle (flat) one pried open.
    xs = [CX + (i - 3) * PITCH for i in range(7)]
    chain_h = np.zeros(X.shape, np.float32)
    chain_m = np.zeros(X.shape, np.float32)
    brk = np.zeros(X.shape, np.float32)
    base = 4.0
    for i, lx in enumerate(xs):
        if i == 3:
            # The middle one lies flat and is broken: its top side cut through and sprung.
            dist, u, v = stadium(X, Y, lx, CHAIN_Y, LINK_L + 6, LINK_W + 10)
            hh = np.sqrt(np.clip(1 - (dist / WIRE) ** 2, 0, 1)) * WIRE + base + 1
            m = np.clip((WIRE - dist) * ss + 0.5, 0, 1)
            gap = (np.abs(u) < 10) & (v < 0)
            # The two ends bent up and apart a little where they were pried.
            lift = np.exp(-((np.abs(u) - 10) / 6) ** 2) * (v < 0) * 3.0
            hh = np.where(gap, 0, hh + lift)
            m = np.where(gap, 0, m)
            brk = np.exp(-((X - lx) ** 2 / (2 * 11.0 ** 2) + (Y - (CHAIN_Y - (LINK_W + 10) / 2)) ** 2 / (2 * 8.0 ** 2)))
        elif i % 2 == 1:
            dist, u, v = stadium(X, Y, lx, CHAIN_Y, LINK_L, LINK_W)
            hh = np.sqrt(np.clip(1 - (dist / WIRE) ** 2, 0, 1)) * WIRE + base
            m = np.clip((WIRE - dist) * ss + 0.5, 0, 1)
        else:
            # On edge: a bar the length of the link, standing taller, its ends round.
            dd = np.hypot(np.clip(np.abs(X - lx) - (LINK_L / 2 - WIRE), 0, None), Y - CHAIN_Y)
            hh = np.sqrt(np.clip(1 - (dd / (WIRE * 1.05)) ** 2, 0, 1)) * WIRE * 1.05 + base + LINK_W * 0.22
            m = np.clip((WIRE * 1.05 - dd) * ss + 0.5, 0, 1)
        chain_h = np.maximum(chain_h, hh * (m > 0.02))
        chain_m = np.maximum(chain_m, m)
    # --- strap iron from the chain's ends out under the words, each ending in a coin.
    left_end = xs[0] - LINK_L / 2 + 6
    right_end = xs[-1] + LINK_L / 2 - 6
    x_out = 330
    strap_h = np.zeros(X.shape, np.float32)
    strap_m = np.zeros(X.shape, np.float32)
    for sx, x_in in ((-1, left_end), (1, right_end)):
        xo = CX + sx * (CX - x_out) if sx < 0 else CX + (CX - x_out)
        pts = [(x_in, CHAIN_Y), ((x_in + xo) / 2, CHAIN_Y + 1), (xo, CHAIN_Y)]
        bh, bm = RL.bar(R, pts, 18, 8)
        strap_h = np.maximum(strap_h, (bh + 2.5) * (bm > 0.02))
        strap_m = np.maximum(strap_m, bm)
    coin_holes = np.zeros(X.shape, np.float32)
    coin_h = np.zeros(X.shape, np.float32)
    coin_m = np.zeros(X.shape, np.float32)
    for x0 in (x_out, 2 * CX - x_out):
        hh, cm, hm = RL.coin(R, x0, CHAIN_Y, 40, 3.0)
        coin_h = np.maximum(coin_h, hh * (cm > 0.02))
        coin_m = np.maximum(coin_m, cm)
        coin_holes = np.maximum(coin_holes, hm)
    # Lay the chain, straps and coins under the letters where they cross (the letters on top).
    under = np.maximum.reduce([strap_h * (strap_m > 0.5), chain_h * (chain_m > 0.5), coin_h * (coin_m > 0.5)])
    under_m = np.maximum.reduce([strap_m, chain_m, coin_m])
    h = np.where(cover > 0.5, np.maximum(h, under * 0), np.maximum(h, under))
    shape = np.where(cover > 0.5, shape, np.maximum(shape, under))
    alpha = np.maximum(alpha, under_m)
    mat = np.where((under_m > 0.5) & (cover < 0.5), RL.IDS["chain"], mat)
    mat = np.where((strap_m > 0.5) & (cover < 0.5) & (chain_m < 0.5), RL.IDS["iron"], mat)
    mat = np.where((coin_m > 0.5) & (cover < 0.5), RL.IDS["gold_dim"], mat)
    mat = np.where((coin_holes > 0.5) & (cover < 0.5), RL.IDS["ember"], mat)
    R.height = (h * ss).astype(np.float32)
    R.shape_height = (shape * ss).astype(np.float32)
    R.alpha = alpha.astype(np.float32)
    R.mat = mat
    # --- the ember: awake in the break, asleep in the coins' holes.
    hot, deep = F.hexc("#ffb050"), F.hexc("#c03008")
    n = F.fbm(R.h, R.w, scale=R.w / 60, octaves=3, seed=44) * 0.5 + 0.5
    core = np.clip(brk * 1.8, 0, 1)
    R.emit = (core[..., None] * (hot * 3.2 + deep * 1.4) * (0.75 + 0.5 * n[..., None])).astype(np.float32)
    R.alpha = np.maximum(R.alpha, core)
    R.emit += (coin_holes * (cover < 0.5))[..., None] * (deep * 1.4 + hot * 0.5) * (0.6 + 0.6 * n[..., None])
    # Sparks lifting from the break.
    rng = np.random.default_rng(45)
    for k in range(14):
        sx_ = CX + rng.normal(0, 26)
        sy_ = CHAIN_Y - (LINK_W + 10) / 2 - rng.uniform(6, 70)
        r_ = rng.uniform(0.8, 1.8)
        spark = np.exp(-((X - sx_) ** 2 + (Y - sy_) ** 2) / (2 * r_ ** 2))
        R.emit += (spark[..., None] * hot * rng.uniform(1.0, 2.2)).astype(np.float32)
        R.alpha = np.maximum(R.alpha, np.clip(spark * 1.5, 0, 1))
    # The break's light on the iron near it (a warm cast, strongest on what faces it).
    near = np.exp(-((X - CX) ** 2 / (2 * 230.0 ** 2) + (Y - CHAIN_Y) ** 2 / (2 * 100.0 ** 2)))
    R.tint = (1 + near[..., None] * (F.hexc("#ffb070") / F.hexc("#ffb070").max() - 0.6) * 0.8).astype(np.float32)
    img = R.render("logo", samples=samples, wear=1.5, grime=0.9, seed=46)
    return R, img


def finish(R, img, denoise=0.22):
    import paintover as PO
    small = np.isin(R.mat, [RL.IDS["chain"], RL.IDS["gold_dim"], RL.IDS["ember"]]).astype(np.float32)
    protect = cv2.dilate(small, np.ones((3, 3), np.uint8), iterations=R.ss) * 0.75
    lit = cv2.GaussianBlur((R.emit.max(axis=2) > 0.04).astype(np.float32), (0, 0), 1.5 * R.ss)
    protect = np.maximum(protect, np.clip(lit * 1.5, 0, 1))
    key = hashlib.sha1(np.ascontiguousarray((img * 255).astype(np.uint8)).tobytes()).hexdigest()[:8]
    prompt = ("the title of a dark fantasy game, SURVIVOR UNCHAINED, letters cut from hand-forged blackened iron, "
              "planished with hammer marks, worn bright on their edges, a heavy iron chain between the words, its "
              "middle link broken open with a glowing orange ember in the break, sparks")
    big = F.downsample(img, (W * 2, H * 2)) if R.ss > 2 else img
    pr = cv2.resize(protect, (big.shape[1], big.shape[0]), interpolation=cv2.INTER_AREA)
    p = PO.paint(big, prompt, f"logo_{key}", denoise=denoise, seed=12, keep_light=0.75, protect=pr, target=1536)
    return glow(F.downsample(p, (W, H)))


def glow(img):
    """The break's light thrown on the air round it: a warm glow laid under and beside the
    iron, falling off softly (it needs no surface; its alpha is its light)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    by = CHAIN_Y - (LINK_W + 10) / 2
    g = (np.exp(-((xx - CX) ** 2 / (2 * 46.0 ** 2) + (yy - by) ** 2 / (2 * 34.0 ** 2))) * 0.85
         + np.exp(-((xx - CX) ** 2 / (2 * 150.0 ** 2) + (yy - by) ** 2 / (2 * 80.0 ** 2))) * 0.35)
    col = np.array([1.0, 0.52, 0.16], np.float32)
    a = img[..., 3]
    ga = np.clip(g, 0, 1) * (1 - a)
    out_a = a + ga
    rgb = (img[..., :3] * a[..., None] + col * ga[..., None]) / np.maximum(out_a[..., None], 1e-4)
    return np.dstack([rgb, out_a]).astype(np.float32)


def main():
    R, img = build()
    out = finish(R, img)
    path = os.path.join(UI, "title", "logo.png")
    F.save(F.to_pil(out), path)
    print(path)


if __name__ == "__main__":
    main()
