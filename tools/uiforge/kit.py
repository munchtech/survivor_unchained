"""The reduced kit, given its material (the owner, on the ornate pages: "those borders are just
ugly, adding more of them doesn't make them better"; "ai looking", "not rooted in ui research";
the coordinator, on the first reduced kit: "plain to a fault", a generic web dark mode).

One frame per screen, the outer window. Inside it the hierarchy comes from spacing, type, tonal
surfaces and thin pressed rules; the world comes from the material, not from ornament:

  ground    page/morocco.png: the binders' dark goatskin, the panels' surface. A pebble grain
            between fine creases, a few long soft creases, the dye uneven (oxblood where it
            took, browner where it didn't). Exactly periodic over 512 shown px, and drawn by
            UiArt tiled at 1:1 under a frame's edge, so its grain never stretches with the
            frame; each frame starts at its own place in it, so like panels differ.
  edges     frames/*.png nine-slices over the ground: only light and shade. A raised piece
            has its skived edge turned down, lit along its top and left (the light is from the
            upper left everywhere), worn bright where hands rub (its top, its corners), dark
            along its foot, a soft shadow under it. A sunk one (a well, a slot) is pressed in:
            the rim's shade falls inside its top and left, its far walls take the light.
  rule      a line blind-tooled into the surface: dark, with the light on its lower wall.

Everything is drawn flat in numpy at twice its shown size; nothing here wants a render except
the bands (pages.header_plain, pages.footer_plain).

    python tools/uiforge/kit.py            # into tools/comfy/out/uiforge/kit/ (to judge)
    python tools/uiforge/kit.py --apply    # over the named art in godot/art/ui/
    python tools/uiforge/kitboard.py       # the kit on a page, at 1:1, to judge it whole
"""
from __future__ import annotations

import math
import os
import shutil
import sys
from dataclasses import dataclass

import cv2
import numpy as np

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui")
OUT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "kit")
K = 2.0                                   # file px per shown px

LIGHT = np.array([-0.6, -0.8], np.float32)  # toward the light, in the image plane (upper left)
WARM = F.hexc("#e6cca4", lin=False)         # the light's colour on an edge
SOOT = F.hexc("#060405", lin=False)         # the darkest shade, never pure black
RARITY = ["#c8c0b0", "#6fd46a", "#5aa8ff", "#c070ff", "#ffb040", "#ff6a3a"]
EMBER = F.hexc("#ff8a3a", lin=False)


@dataclass
class Slice:
    """What UiArt.Frames says of a piece (shown px), and the ground drawn under it at 1:1."""
    file: str
    L: int
    T: int
    R: int
    B: int
    tile: bool = False
    out: int = 0
    ground: str | None = None
    tint: tuple = (1, 1, 1, 1)
    inset: float = 0.0


# --------------------------------------------------------------------------- helpers --

def periodic1(x, P, seed, lo=2, hi=24, octaves=6):
    """1D noise in about -1..1, exactly periodic over P (whole-number frequencies)."""
    rng = np.random.default_rng(seed)
    out = np.zeros_like(x, np.float32)
    amp, tot = 1.0, 0.0
    for k in np.geomspace(lo, hi, octaves):
        n = max(1, int(round(k)))
        ph = rng.uniform(0, 2 * math.pi)
        out += amp * np.sin(2 * math.pi * n * x / P + ph)
        tot += amp
        amp *= 0.7
    return out / tot * 1.6


def worley(n, m, cell, seed):
    """F1, F2 of a periodic cell noise on an n x m canvas (px)."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    k = max(4, int(n * m / (cell * cell)))
    pts = rng.random((k, 2)) * [m, n]
    tree = cKDTree(pts, boxsize=[m, n])
    yy, xx = np.mgrid[0:n, 0:m]
    q = np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], 1) % [m, n]
    d, _ = tree.query(q, k=2)
    return d[:, 0].reshape(n, m).astype(np.float32), d[:, 1].reshape(n, m).astype(np.float32)


def shade(h, spec=0.0, rough=20.0, Lz=0.9):
    """A height field (file px) lit from the upper left: diffuse as a ratio to flat, specular."""
    gy, gx = np.gradient(h)
    nx, ny, nz = -gx, -gy, np.ones_like(h)
    inv = 1 / np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx * inv, ny * inv, nz * inv
    L = np.array([LIGHT[0], LIGHT[1], Lz], np.float32)
    L /= np.linalg.norm(L)
    d = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1) / L[2]
    Hv = L + np.array([0, 0, 1], np.float32)
    Hv /= np.linalg.norm(Hv)
    s = np.clip(nx * Hv[0] + ny * Hv[1] + nz * Hv[2], 0, 1) ** rough * spec
    return d, s


def box_sd(W, H, x0, y0, x1, y1, r):
    """Signed distance (shown px, positive inside) to a rounded box given in shown px, on a
    file of W x H file px."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x, y = (xx + 0.5) / K, (yy + 0.5) / K
    cx, cy, hw, hh = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    qx = np.abs(x - cx) - (hw - r)
    qy = np.abs(y - cy) - (hh - r)
    out = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    return -out, x, y


def outward(sd):
    """The unit outward normal of a distance field (image plane)."""
    gy, gx = np.gradient(sd)
    n = np.sqrt(gx * gx + gy * gy) + 1e-6
    return -gx / n, -gy / n


def layer(light, dark, light_col=WARM, dark_col=SOOT):
    """Light and shade as one straight-alpha overlay (light and dark coverages, 0..1)."""
    light, dark = np.clip(light, 0, 1), np.clip(dark, 0, 1)
    a = np.clip(light + dark * (1 - light), 0, 1)
    rgb = (light[..., None] * light_col + (dark * (1 - light))[..., None] * dark_col) / np.maximum(a[..., None], 1e-4)
    return np.dstack([rgb, a]).astype(np.float32)


def under(top, bottom):
    """Straight-alpha `top` over `bottom`."""
    ta, ba = top[..., 3:4], bottom[..., 3:4]
    a = ta + ba * (1 - ta)
    rgb = (top[..., :3] * ta + bottom[..., :3] * ba * (1 - ta)) / np.maximum(a, 1e-4)
    return np.concatenate([rgb, a], -1)


def colour(c, lin=False):
    return F.hexc(c, lin=lin) if isinstance(c, str) else np.asarray(c, np.float32)


# ---------------------------------------------------------------------------- ground --

def morocco(N=512, seed=1, tone="#221b19"):
    """The panels' ground (page/morocco.png, N*2 file px square, N shown, periodic): the binders'
    goatskin, dyed nearly black. Its grain is the 'pin-head' of goat morocco, small rounded
    pebbles between fine creases, gathered here and there into a coarser boarding; a few long
    soft creases; the dye oxblood where it took and browner where it didn't. Lit from the upper
    left, a little sheen on the pebbles' crowns. Opaque: a frame's ground tint sets how much
    of the page shows through it."""
    n = int(N * K)
    f1, f2 = worley(n, n, 3.4 * K, seed)
    pebble = np.clip((f2 - f1) / (1.6 * K), 0, 1) ** 0.55          # 0 in a crease, 1 on a crown
    f1b, f2b = worley(n, n, 10.0 * K, seed + 7)
    board = np.clip((f2b - f1b) / (4.0 * K), 0, 1) ** 0.8
    flow = F.fbm(n, n, scale=90 * K, octaves=3, seed=seed + 2)
    crease = (1 - np.abs(F.fbm(n, n, scale=150 * K, octaves=2, seed=seed + 3))) ** 10
    # How strongly the grain stands varies over the skin (it is flatter where it was stretched).
    stand = 0.6 + 0.4 * (F.fbm(n, n, scale=120 * K, octaves=2, seed=seed + 8) * 0.5 + 0.5)
    h = (pebble * 0.55 + board * 0.45) * stand * K * 0.5 + flow * 3.0 * K - crease * 0.5 * K
    d, s = shade(h, spec=0.10, rough=14)
    took = np.clip(F.fbm(n, n, scale=170 * K, octaves=4, seed=seed + 4) * 0.7 + 0.5, 0, 1)[..., None]
    mott = F.fbm(n, n, scale=28 * K, octaves=3, seed=seed + 5)[..., None]
    ox, brown = F.hexc("#251a19"), F.hexc("#221c17")
    col = (ox * took + brown * (1 - took)) * (1 + 0.06 * mott)
    lin = col * d[..., None] + s[..., None] * F.hexc("#6a5244")
    # Its mean held to `tone`: a step above the page and a little warmer, never brown.
    lin = lin * (F.hexc(tone) / lin.reshape(-1, 3).mean(0))
    rgb = F.lin_to_srgb(lin)
    return np.dstack([rgb, np.ones((n, n), np.float32)]).astype(np.float32)


# ----------------------------------------------------------------------------- edges --

def raised(Ws, Hs, out=6, r=1.5, mid=None, seed=21, wear=1.0, lift=1.0, shadow=0.5, glow=None, glow_a=0.0):
    """A raised piece's edge (the middle clear: the ground shows there). Ws x Hs shown, with
    `out` px of margin for its shadow; the margin's middle `mid` repeats (periodic wear)."""
    W, H = int(Ws * K), int(Hs * K)
    x0, y0, x1, y1 = out, out, Ws - out, Hs - out
    sd, x, y = box_sd(W, H, x0, y0, x1, y1, r)
    nx, ny = outward(sd)
    # The skived edge turned down over 2.2 px: its slope faces the light along the top and left.
    t = np.clip(1 - sd / 2.2, 0, 1) * (sd > -0.5)
    facing = nx * LIGHT[0] + ny * LIGHT[1]              # +1 where the edge faces the light
    slope = t ** 1.6
    # Wear along each edge: periodic over the repeating middle (so the slice repeats cleanly),
    # brighter toward the corners where hands rub.
    P = mid if mid else (Ws - 2 * out)
    wx = periodic1(x - x0, P, seed) * 0.5 + 0.5
    wy = periodic1(y - y0, P, seed + 1) * 0.5 + 0.5
    along = np.clip(np.where(np.abs(ny) > np.abs(nx), wx, wy), 0, 1)
    corner = np.exp(-np.minimum.reduce([np.hypot(x - x0, y - y0), np.hypot(x - x1, y - y0),
                                        np.hypot(x - x0, y - y1), np.hypot(x - x1, y - y1)]) / 10.0)
    worn = np.clip(0.35 + 0.9 * along ** 1.5 + 0.6 * corner, 0, 1.6) * wear
    lit = np.clip(facing, 0, 1) * slope * (0.10 + 0.12 * worn) * lift
    # The crown of the edge, rubbed pale where it is worn (on the lit edges most).
    crown = np.clip(1 - np.abs(sd - 0.6) / 0.6, 0, 1) * (0.05 + 0.10 * worn) * np.clip(facing, 0, 1) ** 0.7 * lift
    dark = np.clip(-facing, 0, 1) * slope * 0.55
    img = layer(lit + crown, dark)
    inside = np.clip(sd * K + 0.5, 0, 1)
    img[..., 3] *= inside
    if glow is not None and glow_a > 0:
        # A colour rising from the foot inside (the primary's ember).
        g = np.clip(1 - (y1 - y) / ((y1 - y0) * 0.7), 0, 1) ** 1.6 * glow_a * inside
        line = np.clip(1 - np.abs((y1 - y) - 1.2) / 0.8, 0, 1) * inside * glow_a * 1.6
        img = under(np.dstack([np.broadcast_to(colour(glow), img.shape[:2] + (3,)), np.clip(line, 0, 1)]),
                    under(img, np.dstack([np.broadcast_to(colour(glow), img.shape[:2] + (3,)), g])))
    # Its shadow on the page: soft, down and a little right, and a firm contact line.
    if shadow > 0:
        m = (sd > 0).astype(np.float32)
        sh = cv2.GaussianBlur(m, (0, 0), 2.0 * K)
        sh = np.roll(np.roll(sh, int(1.5 * K), 0), int(0.6 * K), 1) * shadow
        contact = np.clip(1 - np.abs(sd + 0.5) / 0.7, 0, 1) * 0.5 * (sd < 0)
        sh = np.maximum(sh, contact) * (1 - inside)
        img = under(img, np.dstack([np.broadcast_to(SOOT, img.shape[:2] + (3,)), sh]))
    return img.astype(np.float32)


def sunk(Ws, Hs, r=1.5, depth=1.0, mid=None, seed=31, rim=1.0, line=None, line_a=0.0, glow=None, glow_a=0.0):
    """A pressed-in piece's edge (a well, a slot): the rim's shade falls inside its top and
    left, its far walls (foot and right) take the light. `line` lays a hairline of a colour
    just inside (a filled slot's rarity), `glow` a colour rising from its foot."""
    W, H = int(Ws * K), int(Hs * K)
    sd, x, y = box_sd(W, H, 0, 0, Ws, Hs, r)
    nx, ny = outward(sd)
    inside = np.clip(sd * K + 0.5, 0, 1)
    facing = (nx * LIGHT[0] + ny * LIGHT[1])           # +1 on the walls nearest the light
    # The inner wall: the near walls (top, left) in shade, the far ones (foot, right) lit.
    wall = np.clip(1 - sd / 1.6, 0, 1) ** 1.3 * inside
    P = mid if mid else Ws
    wx = periodic1(x, P, seed) * 0.5 + 0.5
    wy = periodic1(y, P, seed + 1) * 0.5 + 0.5
    along = np.clip(np.where(np.abs(ny) > np.abs(nx), wx, wy), 0, 1)
    lit = np.clip(-facing, 0, 1) * wall * (0.10 + 0.10 * along) * rim
    dark = np.clip(facing, 0, 1) * wall * 0.6 * depth
    # The rim's shadow cast in, deeper under the top than the left.
    cast = (np.clip(1 - y / 6.0, 0, 1) ** 1.6 * 0.42 + np.clip(1 - x / 4.0, 0, 1) ** 1.6 * 0.22) * inside * depth
    img = layer(lit, np.clip(dark + cast, 0, 0.85))
    if glow is not None and glow_a > 0:
        g = np.clip(1 - (Hs - y) / (Hs * 0.62), 0, 1) ** 1.5 * glow_a * inside
        img = under(img, np.dstack([np.broadcast_to(colour(glow), img.shape[:2] + (3,)), g]))
    if line is not None and line_a > 0:
        hl = np.clip(1 - np.abs(sd - 1.6) / 0.55, 0, 1) * line_a
        img = under(np.dstack([np.broadcast_to(colour(line), img.shape[:2] + (3,)), hl]), img)
    return img.astype(np.float32)


def rule_h(Ws=128, Hs=6, end=28):
    """A rule tooled blind into the surface, across: a dark groove one px wide with the light
    on its lower wall, fading over its ends (the slice's ends)."""
    W, H = int(Ws * K), int(Hs * K)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    y, x = (yy + 0.5) / K, (xx + 0.5) / K
    c = Hs / 2
    fade = np.clip(x / end, 0, 1) ** 1.3 * np.clip((Ws - x) / end, 0, 1) ** 1.3
    groove = np.clip(1 - np.abs(y - (c - 0.25)) / 0.6, 0, 1) * 0.55
    wall = np.clip(1 - np.abs(y - (c + 0.75)) / 0.5, 0, 1) * 0.10
    return layer(wall * fade, groove * fade)


def rule_v(Ws=6, Hs=128, end=28):
    """The same rule, down: the light on its right wall."""
    W, H = int(Ws * K), int(Hs * K)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    y, x = (yy + 0.5) / K, (xx + 0.5) / K
    c = Ws / 2
    fade = np.clip(y / end, 0, 1) ** 1.3 * np.clip((Hs - y) / end, 0, 1) ** 1.3
    groove = np.clip(1 - np.abs(x - (c - 0.25)) / 0.6, 0, 1) * 0.55
    wall = np.clip(1 - np.abs(x - (c + 0.75)) / 0.5, 0, 1) * 0.10
    return layer(wall * fade, groove * fade)


def underline(Ws=96, Hs=34, col=EMBER, end=16, glow=0.10, a=0.95):
    """The open tab's mark: an ember line under its words, fading at its ends, and the faint
    light it throws up behind them. Nothing else: the other tabs are words alone."""
    W, H = int(Ws * K), int(Hs * K)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    y, x = (yy + 0.5) / K, (xx + 0.5) / K
    fade = np.clip(x / end, 0, 1) ** 1.2 * np.clip((Ws - x) / end, 0, 1) ** 1.2
    line = np.clip(1 - np.abs(y - (Hs - 2.5)) / 1.0, 0, 1) * fade * a
    halo = np.exp(-((Hs - 2.5 - y) / 9.0) ** 2) * fade * glow * (y < Hs - 2)
    a = np.clip(line + halo, 0, 1)
    rgb = np.broadcast_to(colour(col), (H, W, 3)).copy()
    rgb = rgb * (1 - line[..., None] * 0.3) + np.array([1.0, 0.85, 0.6], np.float32) * line[..., None] * 0.3
    return np.dstack([rgb, a]).astype(np.float32)


def clear(Ws, Hs):
    return np.zeros((int(Hs * K), int(Ws * K), 4), np.float32)


# ----------------------------------------------------------------------------- rings --

def ring(S=220, w=6.0, seed=41):
    """A slim forged ring (medallion/ring.png, S*2 file px, S shown): a plain iron band with a
    rounded crown, lit from the upper left and worn bright on its crown; nothing on it. The
    code keeps its colour as a hairline inside it and its number in the middle."""
    n = int(S * K)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    x, y = (xx + 0.5) / K - S / 2, (yy + 0.5) / K - S / 2
    r = np.hypot(x, y)
    R = S / 2 - 3.0
    across = (r - (R - w / 2)) / (w / 2)   # -1 inner edge, +1 outer edge
    cov = np.clip((1 - np.abs(across)) * (w / 2) * K + 0.5, 0, 1)
    prof = np.sqrt(np.clip(1 - across ** 2, 0, 1))
    th = np.arctan2(y, x)
    ham = periodic1(th / (2 * math.pi) * 1000, 1000, seed, lo=6, hi=60) * 0.15
    h = (prof * w * 0.5 + ham) * K
    dd, s = shade(h, spec=0.5, rough=30, Lz=1.2)
    base = F.hexc("#2a2630")
    wear = np.clip(prof - 0.75, 0, 1) * 4 * (0.6 + 0.4 * (periodic1(th / (2 * math.pi) * 1000, 1000, seed + 3, lo=3, hi=20) * 0.5 + 0.5))
    col = base * (1 + wear[..., None] * 0.8) * dd[..., None] + s[..., None] * F.hexc("#c8c0d0") * 0.6
    rgb = F.lin_to_srgb(col)
    # A soft shadow under the ring, inside and out.
    sh = cv2.GaussianBlur(cov, (0, 0), 1.5 * K)
    sh = np.roll(sh, int(1.2 * K), 0) * 0.55
    img = under(np.dstack([rgb, cov]), np.dstack([np.broadcast_to(SOOT, rgb.shape), sh * (1 - cov)]))
    return img.astype(np.float32)


def disc(S=40, w=2.2, metal="#2a2630", fill=None, glow=None, glow_a=0.0, sunk_=False, seed=43):
    """A round piece S shown px: a slim ring of iron (or of a colour, `metal`), and inside it
    a `fill` tone domed a little (a taken node, a round button) or pressed in (`sunk_`, a dim
    dot); `glow` lights it from outside (the next node, a round button with points to spend)."""
    n = int(S * K)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    x, y = (xx + 0.5) / K - S / 2, (yy + 0.5) / K - S / 2
    r = np.hypot(x, y)
    pad = 4.0 if glow is not None else 1.5
    R = S / 2 - pad
    inside = np.clip((R - w - r) * K + 0.5, 0, 1)
    img = np.zeros((n, n, 4), np.float32)
    if glow is not None and glow_a > 0:
        g = np.exp(-np.clip(r - R, 0, None) ** 2 / (2 * (pad * 0.55) ** 2)) * (r > R - w) * glow_a
        img = under(np.dstack([np.broadcast_to(colour(glow), (n, n, 3)), g]), img)
    if fill is not None:
        q = np.clip(r / (R - w), 0, 1)
        dome = np.sqrt(np.clip(1 - q ** 2, 0, 1)) * (R - w) * (0.12 if not sunk_ else -0.25)
        d, sp = shade(dome * K, spec=0.06, rough=8)
        lin = F.hexc(fill) * d[..., None] + sp[..., None] * F.hexc("#806a5c")
        if sunk_:
            lin = lin * (0.55 + 0.45 * np.clip((y + (R - w)) / (2 * (R - w)), 0, 1))[..., None]
        img = under(np.dstack([F.lin_to_srgb(lin), inside]), img)
    if w > 0:
        across = (r - (R - w / 2)) / (w / 2)
        cov = np.clip((1 - np.abs(across)) * (w / 2) * K + 0.5, 0, 1)
        prof = np.sqrt(np.clip(1 - across ** 2, 0, 1))
        d, sp = shade(prof * w * 0.5 * K, spec=0.5, rough=30, Lz=1.2)
        lin = F.hexc(metal) * d[..., None] + sp[..., None] * (F.hexc("#c8c0d0") * 0.5 if glow is None else F.hexc(metal) * 1.5)
        img = under(np.dstack([F.lin_to_srgb(lin), cov]), img)
    # Its shadow under it.
    body = np.clip((R - r) * K + 0.5, 0, 1)
    sh = np.roll(cv2.GaussianBlur(body, (0, 0), 1.2 * K), int(1.0 * K), 0) * 0.5 * (1 - body)
    return under(img, np.dstack([np.broadcast_to(SOOT, (n, n, 3)), sh])).astype(np.float32)


# ----------------------------------------------------------------------------- bands --

def binding(TW, H, leather, rail, fillets, shadow, nails=256.0, seed=51, ss=2, tone="#181112", iron="#28242a", tilt=0.010, rough=0.27, cell=48.0, dent=0.015, rubk=4.2):
    """A band of the day's book's binding (the screen's one frame), tiled along: TW x H file
    px; spans below in shown px. The panels' goatskin, darker, over a padded board, a fillet
    blind-tooled into it at each of `fillets`; at `rail` a strap of forged iron, its edges a
    little uneven as drawn under the hammer, its face planished in broad soft facets (no
    glitter), its top chamfer catching the light and worn bright in places; a domed nail every
    `nails` px. `shadow` 'below' or 'above' (the side the page is on)."""
    W, Hh = TW * ss, H * ss
    k = K * ss                                   # canvas px per shown px
    yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float32)
    x, y = (xx + 0.5) / k, (yy + 0.5) / k        # shown px
    l0, l1 = leather
    r0, r1 = rail
    P = TW / K
    # The goatskin: the panels' own, its tone darker; lit as the board pads it, the fillets
    # pressed in, its edge turned down onto the rail.
    skin = morocco(N=int(TW / K), seed=seed, tone=tone)
    skin = cv2.resize(skin, (W, W), interpolation=cv2.INTER_LINEAR)[:Hh]
    pad = np.clip(np.sin(np.clip((y - l0) / (l1 - l0), 0, 1) * math.pi), 0, 1) ** 0.6 * 2.0
    tool = np.zeros_like(x)
    for yf in fillets:
        tool = np.maximum(tool, np.clip(1 - np.abs(y - yf) / 0.6, 0, 1) ** 1.5)
    if shadow == "below":
        turn = np.clip((y - (r0 - 2.2)) / 2.2, 0, 1) ** 2 * 1.4
    else:
        turn = np.clip(((r1 + 2.2) - y) / 2.2, 0, 1) ** 2 * 1.4
    d, _ = shade((pad - tool * 0.45 - turn) * k)
    lin = F.srgb_to_lin(skin[..., :3]) * d[..., None]
    lea = np.dstack([F.lin_to_srgb(lin), ((y >= l0) & (y < l1)).astype(np.float32)])
    # The rail: forged strap, lit by the house's matcaps (its metal wants their reflections).
    S = F.Surface(W, Hh)
    wob0 = periodic1(x, P, seed, lo=3, hi=40) * 0.22
    wob1 = periodic1(x, P, seed + 1, lo=3, hi=40) * 0.22
    top, foot = r0 + wob0, r1 + wob1
    on_rail = ((y >= top) & (y < foot)).astype(np.float32)
    t = np.clip((y - top) / (foot - top), 0, 1)
    ch = 1.7 / (r1 - r0)
    prof = np.minimum(np.clip(t / ch, 0, 1), np.clip((1 - t) / ch, 0, 1)) ** 0.7
    crown = np.sin(t * math.pi) * 0.35
    plan = F.facets(Hh, W, cell=cell * k, tilt=tilt, seed=seed + 2, soften=5.0 * ss) / k
    dents = F.worley_dents(Hh, W, cell=5.0 * k, depth=dent * k, seed=seed + 3) / k
    h = (6.0 + prof * 2.4 + crown + (plan + dents) * prof) * k
    nail = np.zeros_like(x)
    if nails:
        for n0 in np.arange(nails / 2, P + nails, nails):
            dd = np.hypot(((x - n0 + P / 2) % P) - P / 2, y - (r0 + r1) / 2)
            m = dd < 2.0
            h = np.where(m, np.maximum(h, (8.8 + np.sqrt(np.clip(1 - (dd / 2.0) ** 2, 0, 1)) * 1.3) * k), h)
            nail = np.maximum(nail, m.astype(np.float32))
    S.height = (h * on_rail).astype(np.float32)
    # Its top chamfer rubbed bright in places (where hands and the page have worn it).
    rub = np.clip(1 - np.abs(t - ch * 0.5) / (ch * 0.7), 0, 1) * np.clip(periodic1(x, P, seed + 8, lo=2, hi=30) * 0.6 + 0.6, 0, 1.3)
    mott = F.fbm(Hh, W, scale=30 * k, octaves=3, seed=seed + 7) * 0.5 + 0.5
    S.paint(on_rail, F.Mat(tuple(F.hexc(iron)), 0.7, rough), albedo_mul=(0.8 + 0.4 * mott) * (1 + rub * rubk))
    S.paint(nail * on_rail, F.Mat(tuple(F.hexc("#3c3742")), 0.75, 0.34))
    S.alpha = on_rail
    rl = S.shade(normal_strength=1.0, ao=0.4, shadow=0.0)
    rimg = np.asarray(S.finish(rl), np.float32) / 255
    img = under(rimg, lea)
    img = F.downsample(img, (TW, H))
    # The shadow the band lays on the page.
    ys = (np.arange(H, dtype=np.float32) / K)[:, None]
    if shadow == "below":
        sh = np.clip(1 - (ys - r1) / 3.5, 0, 1) ** 1.3 * 0.75 * (ys >= r1)
    else:
        sh = np.clip(1 - (r0 - ys) / 4.0, 0, 1) ** 1.5 * 0.5 * (ys < r0)
    sh = np.broadcast_to(sh, img.shape[:2])
    return under(img, np.dstack([np.broadcast_to(SOOT, img.shape[:2] + (3,)), sh])).astype(np.float32)


def header():
    """frames/header.png, 1024x200 file (512x100 shown), slice 0 0 0 12, tiled along. The page
    writes on it down to y 80 (the tabs, the title, its line), so it is plain there: one blind
    fillet near the screen's edge and one over the rail; the rail at y 84-96."""
    return binding(1024, 200, (0.0, 86.0), (84.0, 96.0), (5.0, 79.5), "below")


def footer():
    """frames/footer.png, 1024x136 file (512x68 shown), slice 0 12 0 0, tiled along, laid at
    y 1016: its top 16 quiet but for a soft seat shade, the rail at 16-28, a blind fillet under
    it, the goatskin where the prompts are written (y 28-60, the screen's 1044-1076)."""
    return binding(1024, 136, (26.0, 68.0), (16.0, 28.0), (32.0,), "above")


# ------------------------------------------------------------------------- the frame --

def wrap_sample(tile, H, W, ox, oy):
    """A periodic tile read over an H x W canvas from offset (ox, oy) (canvas px), wrapping."""
    th, tw = tile.shape[:2]
    ys = (np.arange(H) + oy) % th
    xs = (np.arange(W) + ox) % tw
    return tile[ys[:, None], xs[None, :]]


def side(m=48, out=8, P=256, border=12.0, seed=61, tone="#161011", ss=2):
    """The side panel's one frame (frames/side.png): the leaf bound in the binders' goatskin,
    a border `border` px wide turned over the board's edge, a fillet blind-tooled round it,
    and at each corner a plain cap of forged iron, as heavy books wear them, nailed once.
    Its middle is clear: the page's vellum is laid there at 1:1 by UiArt (its Ground). Slice
    `m` each side with `out` of it past the control; the middle repeats over `P`."""
    Ws = 2 * m + P
    n = int(Ws * K * ss)
    k = K * ss
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    x, y = (xx + 0.5) / k, (yy + 0.5) / k
    x0, x1 = out, Ws - out
    sd = np.minimum(np.minimum(x - x0, x1 - x), np.minimum(y - x0, x1 - y))   # distance in from the edge
    # The goatskin border: its outer edge rounded over, flat, the fillet pressed in, its inner
    # edge (the turn-in) standing a little above the vellum and shading it.
    skin = morocco(N=P, seed=seed, tone=tone)
    skin = cv2.resize(skin, (int(P * k), int(P * k)), interpolation=cv2.INTER_LINEAR)
    skin = wrap_sample(skin, n, n, int(-m * k) % int(P * k), int(-m * k) % int(P * k))
    on = (sd >= 0) & (sd < border)
    roundover = np.sqrt(np.clip(sd / 2.2, 0, 1))
    turn = np.sqrt(np.clip((border - sd) / 1.4, 0, 1))
    fillet = np.clip(1 - np.abs(sd - 7.0) / 0.6, 0, 1) ** 1.5
    h = (roundover * turn * 1.6 - fillet * 0.35) * k
    d, _ = shade(np.where(on, h, 0))
    lin = F.srgb_to_lin(skin[..., :3]) * d[..., None] * (1 - fillet[..., None] * 0.25)
    lea = np.dstack([F.lin_to_srgb(lin), np.clip(np.minimum(sd * k + 0.5, (border - sd) * k + 0.5), 0, 1) * (sd > -1)])
    # The turn-in's shade on the vellum inside it.
    inner = np.clip(1 - (sd - border) / 5.0, 0, 1) ** 1.6 * (sd >= border) * 0.55
    img = under(lea, np.dstack([np.broadcast_to(SOOT, (n, n, 3)), inner]))
    # The corner caps: an L of strap iron over each corner, its legs ending round, one nail.
    S = F.Surface(n, n)
    leg, wid = 34.0, border + 2.0
    cap = np.zeros((n, n), np.float32)
    cap_h = np.zeros((n, n), np.float32)
    nails = np.zeros((n, n), np.float32)
    for cx, cy, sx, sy in ((x0, x0, 1, 1), (x1, x0, -1, 1), (x0, x1, 1, -1), (x1, x1, -1, -1)):
        u, v = (x - cx) * sx, (y - cy) * sy                     # in from the corner
        wob = periodic1(u + v, 400, seed + int(cx + cy), lo=4, hi=30) * 0.25
        a = (u >= -0.3) & (v >= -0.3)
        # Each leg: a strap `wid` wide running `leg` along an edge, its end rounded.
        s1 = np.minimum(wid + wob - v, leg - u)                  # along the top/foot
        e1 = np.hypot(np.maximum(u - (leg - wid / 2), 0), np.maximum(v - wid / 2, 0) * 0) * 0
        r1 = np.where(u > leg - wid / 2, wid / 2 - np.hypot(u - (leg - wid / 2), v - wid / 2), wid + wob - v)
        r2 = np.where(v > leg - wid / 2, wid / 2 - np.hypot(v - (leg - wid / 2), u - wid / 2), wid + wob - u)
        legs = np.maximum(np.minimum(r1, v + 0.3), np.minimum(r2, u + 0.3))
        csd = np.where(a, legs, -1)
        m_ = np.clip(csd * k * 0.5 + 0.5, 0, 1)
        prof = np.clip(csd / 1.6, 0, 1) ** 0.6
        hh = (3.0 + prof * 1.4) * k
        cap = np.maximum(cap, m_)
        cap_h = np.where(m_ > 0.5, np.maximum(cap_h, hh), cap_h)
        dd = np.hypot(u - wid / 2 - 1.0, v - wid / 2 - 1.0)
        nm = dd < 2.2
        cap_h = np.where(nm & (m_ > 0.5), np.maximum(cap_h, (4.6 + np.sqrt(np.clip(1 - (dd / 2.2) ** 2, 0, 1)) * 1.2) * k), cap_h)
        nails = np.maximum(nails, (nm & (m_ > 0.5)).astype(np.float32))
    plan = F.facets(n, n, cell=10.0 * k, tilt=0.03, seed=seed + 2, soften=2.0 * ss) / k
    dents = F.worley_dents(n, n, cell=4.0 * k, depth=0.06 * k, seed=seed + 3) / k
    S.height = ((cap_h + (plan + dents) * k * 0.0 + (plan + dents) * k * (nails < 0.5)) * (cap > 0.02)).astype(np.float32)
    mott = F.fbm(n, n, scale=20 * k, octaves=3, seed=seed + 7) * 0.5 + 0.5
    S.paint(cap, F.Mat(tuple(F.hexc("#2a2530")), 0.7, 0.42), albedo_mul=0.8 + 0.4 * mott)
    S.paint(nails, F.Mat(tuple(F.hexc("#3c3742")), 0.75, 0.34))
    S.alpha = cap
    capimg = np.asarray(S.finish(S.shade(normal_strength=1.0, ao=0.4, shadow=0.0)), np.float32) / 255
    # The caps' shadow on the leather and the vellum.
    csh = np.roll(np.roll(cv2.GaussianBlur(cap, (0, 0), 1.6 * k), int(1.2 * k), 0), int(0.6 * k), 1) * 0.6 * (1 - cap)
    img = under(capimg, under(np.dstack([np.broadcast_to(SOOT, (n, n, 3)), csh]), img))
    # The whole frame's shadow on the world beyond it.
    body = (sd > 0).astype(np.float32)
    osh = np.roll(cv2.GaussianBlur(body, (0, 0), 3.0 * k), int(2.0 * k), 0) * 0.6 * (sd <= 0)
    img = under(img, np.dstack([np.broadcast_to(SOOT, (n, n, 3)), osh]))
    return F.downsample(img, (int(Ws * K), int(Ws * K))).astype(np.float32)


def grain(N=512, seed=91):
    """The backdrop's grain (page/backdrop_grain.png, N file px, tiled): a film's grain over the
    world, fine and faint, light and dark in equal measure. No specks: over the page's vellum,
    bright specks read as stars or dust on the screen."""
    g = F.fbm(N, N, scale=1.3, octaves=2, seed=seed)
    g = g / (np.abs(g).max() + 1e-6)
    coarse = F.fbm(N, N, scale=60, octaves=3, seed=seed + 1) * 0.5 + 0.5
    a = np.abs(g) * (0.045 + 0.02 * coarse)
    rgb = np.where((g > 0)[..., None], np.array([0.92, 0.86, 0.78], np.float32), np.array([0.02, 0.015, 0.02], np.float32))
    return np.dstack([rgb, np.clip(a, 0, 1)]).astype(np.float32)


# Materials painted on the local Krea (no LoRA: a material, not a painting), to set beside
# the drawn ones and take whichever reads truer at 1:1.
MATERIALS = {
    "vellum": "extreme close-up macro photograph filling the whole frame with the surface of black-dyed calfskin "
              "vellum, matte, faint hair follicle pores in small groups, faint branching veins in the skin, gentle "
              "cockle, the dye slightly uneven, soft even light from the upper left, flat top-down view, no objects, "
              "no text",
    "goatskin": "extreme close-up macro photograph filling the whole frame with black-dyed morocco goatskin "
                "bookbinding leather, fine pin-head pebble grain, a soft sheen, slightly uneven dye with a hint of "
                "oxblood, soft even light from the upper left, flat top-down view, no objects, no text",
}


def paint_materials(seed=1400, n=4):
    import krea
    jobs = [(k, p, seed) for k, p in MATERIALS.items()]
    return krea.t2i_many(jobs, size=(1024, 1024), lora=0.0, tag="materials", n=n)


# ---------------------------------------------------------------------------- pieces --

G = "page/morocco.png"
# What each piece is, by the name the code asks for (UiArt.Frames), at the size its slice wants.
SLICES = {
    "panel": Slice("frames/panel.png", 14, 14, 14, 14, True, 6, G, (1, 1, 1, 0.88)),
    "slab": Slice("frames/slab.png", 14, 14, 14, 14, True, 6, G, (1, 1, 1, 0.88)),
    "pillar": Slice("frames/pillar.png", 14, 14, 14, 14, True, 6, G, (1, 1, 1, 0.88)),
    "hero_plate": Slice("frames/hero_plate.png", 14, 14, 14, 14, True, 6, G, (0.8, 0.8, 0.8, 0.7)),
    "tooltip": Slice("frames/tooltip.png", 14, 14, 14, 14, True, 6, G, (1, 1, 1, 0.97)),
    "well": Slice("frames/well.png", 10, 10, 10, 10, True, 0, G, (0.45, 0.42, 0.45, 0.75)),
    "slot": Slice("frames/slot.png", 10, 10, 10, 10, False, 0, G, (0.66, 0.63, 0.66, 0.86)),
    **{f"slot_{i}": Slice(f"frames/slot_{nm}.png", 10, 10, 10, 10, False, 0, G, (0.55, 0.52, 0.55, 0.85))
       for i, nm in enumerate(["common", "uncommon", "rare", "epic", "legendary", "relic"])},
    "button": Slice("frames/button.png", 12, 10, 12, 10, True, 0, G, (1.15, 1.12, 1.1, 0.92)),
    "button_hover": Slice("frames/button_hover.png", 12, 10, 12, 10, True, 0, G, (1.4, 1.34, 1.3, 0.95)),
    "button_pressed": Slice("frames/button_pressed.png", 12, 10, 12, 10, True, 0, G, (0.75, 0.72, 0.72, 0.92)),
    "button_disabled": Slice("frames/button_disabled.png", 12, 10, 12, 10, True, 0, G, (0.7, 0.7, 0.7, 0.5)),
    "button_primary": Slice("frames/button_primary.png", 12, 10, 12, 10, True, 0, G, (1.3, 1.1, 1.0, 0.95)),
    "button_primary_hover": Slice("frames/button_primary_hover.png", 12, 10, 12, 10, True, 0, G, (1.5, 1.25, 1.1, 0.97)),
    "button_primary_pressed": Slice("frames/button_primary_pressed.png", 12, 10, 12, 10, True, 0, G, (0.9, 0.78, 0.72, 0.95)),
    "chip": Slice("frames/chip.png", 8, 8, 8, 8, False, 0, G, (1.1, 1.08, 1.05, 0.85)),
    "keycap": Slice("frames/keycap.png", 6, 6, 6, 6, False, 0, G, (0.55, 0.52, 0.55, 0.9)),
    "tab": Slice("frames/tab.png", 14, 10, 14, 6),
    "tab_on": Slice("frames/tab_on.png", 18, 10, 18, 6, True),
    "tab_hover": Slice("frames/tab_hover.png", 18, 10, 18, 6, True),
    "tab_pressed": Slice("frames/tab_pressed.png", 18, 10, 18, 6, True),
    "side": Slice("frames/side.png", 48, 48, 48, 48, True, 8, "page/vellum.png", (1, 1, 1, 0.96)),
    "price": Slice("frames/price.png", 6, 6, 6, 6, False, 0, G, (0.5, 0.48, 0.5, 0.92)),
    "row": Slice("frames/row.png", 10, 10, 10, 10, True, 0, G, (0.7, 0.68, 0.7, 0.85)),
    "row_on": Slice("frames/row_on.png", 10, 10, 10, 10, True, 0, G, (0.8, 0.74, 0.72, 0.9)),
    "rule_h": Slice("frames/rule_h.png", 28, 0, 28, 0, True),
    "rule_v": Slice("frames/rule_v.png", 0, 28, 0, 28, True),
}

MAKE = {
    "page/morocco.png": morocco,
    "page/backdrop_grain.png": grain,
    "frames/panel.png": lambda: raised(220, 220, out=6, mid=192),
    "frames/slab.png": lambda: raised(220, 220, out=6, mid=192),
    "frames/pillar.png": lambda: raised(220, 220, out=6, mid=192),
    "frames/hero_plate.png": lambda: raised(220, 220, out=6, mid=192, wear=0.7),
    "frames/tooltip.png": lambda: raised(220, 220, out=6, mid=192, shadow=0.8),
    "frames/well.png": lambda: sunk(212, 212, mid=192, depth=1.0),
    "frames/slot.png": lambda: sunk(80, 80, depth=0.8, rim=1.8),
    **{f"frames/slot_{nm}.png": (lambda i=i: sunk(80, 80, depth=0.9, line=RARITY[i], line_a=[0.22, 0.6, 0.7, 0.75, 0.8, 0.85][i],
                                                   glow=RARITY[i], glow_a=[0.0, 0.10, 0.14, 0.16, 0.2, 0.24][i]))
       for i, nm in enumerate(["common", "uncommon", "rare", "epic", "legendary", "relic"])},
    "frames/button.png": lambda: raised(96, 40, out=0, mid=72, shadow=0, wear=0.9),
    "frames/button_hover.png": lambda: raised(96, 40, out=0, mid=72, shadow=0, wear=1.2, lift=1.4),
    "frames/button_pressed.png": lambda: sunk(96, 40, mid=72, depth=0.8),
    "frames/button_disabled.png": lambda: raised(96, 40, out=0, mid=72, shadow=0, wear=0.3, lift=0.4),
    "frames/button_primary.png": lambda: raised(96, 40, out=0, mid=72, shadow=0, wear=1.0, glow=EMBER, glow_a=0.16),
    "frames/button_primary_hover.png": lambda: raised(96, 40, out=0, mid=72, shadow=0, wear=1.2, lift=1.4, glow=EMBER, glow_a=0.24),
    "frames/button_primary_pressed.png": lambda: sunk(96, 40, mid=72, depth=0.8, glow=EMBER, glow_a=0.14),
    "frames/chip.png": lambda: raised(32, 32, out=0, r=7.5, mid=16, shadow=0, wear=0.6, lift=0.8),
    "frames/keycap.png": lambda: sunk(24, 24, r=2.5, depth=0.7, mid=12),
    "frames/tab.png": lambda: clear(64, 34),
    "frames/tab_on.png": lambda: underline(96, 34),
    "frames/tab_hover.png": lambda: underline(96, 34, col=F.hexc("#b8ab98", lin=False), glow=0.0, a=0.35),
    "frames/tab_pressed.png": lambda: underline(96, 34, col=F.hexc("#d8c8b0", lin=False), glow=0.0, a=0.55),
    "frames/rule_h.png": rule_h,
    "frames/rule_v.png": rule_v,
    "medallion/ring.png": ring,
    "frames/header.png": header,
    "frames/side.png": side,
    "frames/price.png": lambda: raised(24, 20, out=0, r=2.5, mid=8, shadow=0, wear=0.5, lift=0.6),
    "frames/row.png": lambda: sunk(64, 40, mid=40, depth=0.5, rim=0.6),
    "frames/row_on.png": lambda: sunk(64, 40, mid=40, depth=0.5, rim=0.6, line=EMBER, line_a=0.75, glow=EMBER, glow_a=0.07),
    "nodes/taken.png": lambda: disc(40, 2.2, fill="#2b211e"),
    "nodes/next.png": lambda: disc(44, 2.4, metal="#ff8a3a", fill="#1c1513", glow="#ff7a2a", glow_a=0.35),
    "nodes/later.png": lambda: disc(14, 0.0, fill="#1a1415", sunk_=True),
    "nodes/round.png": lambda: disc(34, 1.8, fill="#241c1a"),
    "nodes/round_hover.png": lambda: disc(34, 1.8, metal="#4a4250", fill="#30251f"),
    "nodes/round_spend.png": lambda: disc(38, 2.0, metal="#ff8a3a", fill="#241c1a", glow="#ff7a2a", glow_a=0.25),
    "frames/footer.png": footer,
}


def plain_bands():
    """The outer window's bands worn plain (pages.binding without gilt or wire; a render)."""
    import pages
    return {"frames/header.png": pages.header_plain, "frames/footer.png": pages.footer_plain}


def column(Ws=128, Hs=512):
    """A page's column (Style.Column): no rules, only a faint shade under its head falling away
    down it, soft at its sides, so the words have a little dark behind them."""
    W, H = int(Ws * K), int(Hs * K)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    y, x = yy / K, xx / K
    a = (0.30 * np.clip(1 - y / (Hs * 0.85), 0, 1) ** 1.2) * np.clip(np.minimum(x, Ws - x) / 10, 0, 1)
    rgb = np.broadcast_to(np.array([0.025, 0.02, 0.03], np.float32), (H, W, 3))
    return np.dstack([rgb, a]).astype(np.float32)


SLICES.update({
    "column": Slice("frames/column.png", 12, 16, 12, 8),
    # Overlay.Dividers lays a 24-wide rail down each gap: the pressed rule down its middle.
    "column_divider": Slice("frames/column_divider.png", 0, 28, 0, 28, True),
})
MAKE.update({
    "frames/column.png": column,
    "frames/column_divider.png": lambda: rule_v(24, 128),
})
CHAIN_ART = ([f"chain/{pre}{kind}_{k}.png" for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(6)] +
             ["chain/open.png", "ornaments/title_chain_l.png", "ornaments/title_chain_r.png"])
# Pieces the kit once made and no longer does (removed from the game on --apply).
GONE = ["chain/hot.png"]
# Ornament the kit does without (moved aside on --apply, so the code's fallback is nothing).
DROP = ["frames/column_divider_stone.png"]


def csharp(name, s: Slice):
    """The slice as a line of UiArt.Frames."""
    args = [f'"{s.file}"', str(s.L), str(s.T), str(s.R), str(s.B)]
    if s.tile:
        args.append("Tile: true")
    if s.out:
        args.append(f"Out: {s.out}")
    if s.ground:
        args.append(f'Ground: "{s.ground}"')
        r, g, b, a = s.tint
        args.append(f"Tint: new Color({r:g}f, {g:g}f, {b:g}f, {a:g}f)")
    return f'        ["{name}"] = new({", ".join(args)}),'


def patch_frames():
    """Write the kit's slices into UiArt.Frames: a line that names a kit piece is replaced, a
    new one is added before the table's end. The art and its margins go in together."""
    import re
    p = os.path.join(ROOT, "godot", "src", "Ui", "UiArt.cs")
    src = open(p, encoding="utf-8").read()
    start = src.index("public static readonly Dictionary<string, Slice> Frames = new()")
    end = src.index("    };", start)
    table = src[start:end]
    added = []
    for name, s in SLICES.items():
        line = csharp(name, s)
        pat = re.compile(r'^        \["' + re.escape(name) + r'"\] = new\(.*\),$', re.M)
        if pat.search(table):
            table = pat.sub(lambda _m: line, table)
        else:
            added.append(line)
    if added:
        table = table.rstrip() + "\n        // The reduced kit's own pieces (tools/uiforge/kit.py).\n" + "\n".join(added) + "\n"
    open(p, "w", encoding="utf-8", newline="\n").write(src[:start] + table + src[end:])
    print("UiArt.Frames:", len(SLICES), "kit slices,", len(added), "added")


def apply():
    """Lay the judged pieces (as made into OUT) over the game's art, drop what the kit does
    without, and write the slices. Undo with git (checkout godot/art/ui and UiArt.cs)."""
    for rel in MAKE:
        srcp = os.path.join(OUT, rel)
        if not os.path.exists(srcp):
            raise SystemExit(f"{rel} not made: run kit.py first")
        dst = os.path.join(UI, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(srcp, dst)
    # The chain's pieces (chain.py): the tab chain's links and the title's broken chain.
    ch = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "chain")
    for rel in CHAIN_ART:
        srcp = os.path.join(ch, "sprites", rel) if rel.startswith("chain/") else os.path.join(ch, rel)
        if not os.path.exists(srcp):
            raise SystemExit(f"{rel} not made: run chain.py first")
        dst = os.path.join(UI, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(srcp, dst)
    shutil.copyfile(os.path.join(ch, "links", "chain.json"), os.path.join(UI, "chain", "chain.json"))
    for rel in GONE:
        for q in (os.path.join(UI, rel), os.path.join(UI, rel) + ".import"):
            if os.path.exists(q):
                os.remove(q)
    for rel in DROP:
        for q in (os.path.join(UI, rel), os.path.join(UI, rel) + ".import"):
            if os.path.exists(q):
                os.makedirs(os.path.join(OUT, "dropped"), exist_ok=True)
                shutil.move(q, os.path.join(OUT, "dropped", os.path.basename(q)))
    patch_frames()
    print("applied", len(MAKE), "pieces")


def main(only=None):
    todo = {k: v for k, v in MAKE.items() if not only or any(o in k for o in only)}
    for rel, fn in todo.items():
        p = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        F.save(F.to_pil(np.clip(fn(), 0, 1)), p)
        print("kit", rel, flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--apply" in a:
        apply()
    else:
        main([x for x in a if not x.startswith("--")])
