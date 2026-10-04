"""The page's own pieces, for the layout where the live world lies blurred and warmed behind
every page and the columns have no frames (the owner: the old plates looked "drab and low
effort and low def"). Iron only where it carries weight; leather and light elsewhere. Each is
modelled as a relief (relief.py, Blender, the house light) at twice its shown size or more,
then given the hand by a light paint-over; nothing is upscaled.

  header         frames/header.png, 1024x200 (512x100 shown), slice 0 0 0 12, tiled along:
                 the band across every page's head. Worked oxblood leather, darkening to the
                 screen's edge, blind-tooled along the top (a double rule, punched lozenges)
                 and with one fine rule over the rail, so it is calm where the page writes
                 (the tabs, the title, its line, down to y 80); at its foot a slim forged rail
                 with the binders' twisted wire laid in it and a nail every hand's width.
  backdrop_grain page/backdrop_grain.png, 512x512, tiled: grain and dust over the blurred world
                 (light and dark specks at low alpha; never a fill).
  backdrop_edges page/backdrop_edges.png, 1920x1080, stretched: smoke drifting in from the
                 edges and the ember's light low along the foot; clear in the middle.

    python tools/uiforge/pages.py [header ...]
"""
from __future__ import annotations

import math
import os
import sys

import cv2
import numpy as np

import forge as F
import relief as RL
from pieces import paint, save

K = 2.0   # file px per shown px
# The renders are crisp at twice their size already; a paint-over on a strip a band's height
# softens it (the painting is made at a megapixel), so the header keeps its render.
PAINT = False


def periodic_middle(img, TW, blend=48):
    """The middle of three rendered tiles, its start cross-faded from the tile after it, so it
    repeats without a seam (the light at a render's ends sees nothing past them)."""
    mid = img[:, TW:2 * TW].copy()
    nxt = img[:, 2 * TW:3 * TW]
    ramp = np.linspace(0, 1, blend, dtype=np.float32)[None, :, None]
    mid[:, :blend] = nxt[:, :blend] * (1 - ramp) + mid[:, :blend] * ramp
    return mid


def header(ss=2, samples=160):
    TW, H = 1024, 200
    tiles = 3
    W = TW * tiles
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / ss, R.yy / ss
    y = Y / K                                    # shown px, down
    # The page writes across the band down to y 80 (the tabs, the title, its line under it),
    # so the rail is at the very foot and the tooling keeps to where nothing is written.
    rail0, rail1 = 85.0, 97.0                    # the rail's top and foot, shown px
    leather = y < rail0 + 1
    # The leather: a thick hide, its surface pebbled, a few long soft creases along the band.
    pebble = F.fbm(R.h, R.w, scale=2.6 * K * ss, octaves=3, seed=81) / ss
    crease = F.fbm(R.h, R.w, scale=60 * K * ss, octaves=3, seed=82) / ss
    h = 4.0 * K + pebble * 0.55 * K + crease * 1.6 * K
    # Its edge turned down over the rail.
    h = h - np.clip((y - (rail0 - 3)) / 3, 0, 1) ** 2 * 2.0 * K
    # Blind tooling: a fine rule pressed in just above the rail, and along the top (where the
    # band leaves the screen) a double rule with a row of punched lozenges between, the
    # binders' square set on its point, every 16 px.
    tool = np.zeros_like(X)
    for yr, wd in ((81.5, 0.5), (4.0, 0.6), (15.0, 0.6)):
        tool = np.maximum(tool, np.clip((wd - np.abs(y - yr)) * K * ss * 0.5 + 0.5, 0, 1))
    xs = X / K
    u = ((xs + 8.0) % 16.0) - 8.0
    loz = np.clip((2.4 - (np.abs(u) + np.abs(y - 9.5))) * K * ss * 0.5 + 0.5, 0, 1)
    dot = np.clip((0.7 - np.hypot(u, y - 9.5)) * K * ss * 0.5 + 0.5, 0, 1)
    tool = np.maximum(tool, loz * (1 - dot * 0.7))
    h = h - tool * 1.1 * K
    h = np.where(leather, h, 0)
    shape_h = np.where(leather, 4.0 * K - tool * 1.1 * K, 0)
    # The rail: a slim bar, round-topped, its upper edge chamfered to take the light.
    t = np.clip((y - rail0) / (rail1 - rail0), 0, 1)
    rail_prof = (np.clip(np.sin(t * math.pi), 0, 1) ** 0.55) * 4.0 * K + 5.0 * K
    on_rail = (y >= rail0) & (y < rail1)
    facet = F.facets(R.h, R.w, cell=12.0 * K * ss, tilt=0.02, seed=83, soften=1.2 * ss, elong=0.4) / ss
    dents = RL.hammered(R, cell=4.0 * K, depth=0.12 * K, seed=84) / ss
    rail_h = rail_prof + (facet + dents) * K * 0.6
    h = np.where(on_rail, rail_h, h)
    shape_h = np.where(on_rail, rail_prof, shape_h)
    # The binders' twisted wire in a groove along the rail's crown.
    yw = (rail0 + rail1) / 2
    groove = np.clip((1.9 - np.abs(y - yw)) * K * ss * 0.5 + 0.5, 0, 1) * on_rail
    h = h - groove * 1.2 * K
    pitch = 3.2 * K
    d = (Y - yw * K)
    th_ = 3.0 * K
    tw = np.zeros_like(X)
    for k0 in (0.0, 0.5):
        uu = ((d / th_) - ((((X / pitch) + k0) % 1.0) - 0.5)) % 1.0 - 0.5
        tw = np.maximum(tw, np.sqrt(np.clip(1 - (uu / 0.5) ** 2, 0, 1)))
    wm = np.clip((th_ / 2 - np.abs(d)) * ss + 0.5, 0, 1)
    edge = np.sqrt(np.clip(1 - (d / (th_ / 2)) ** 2, 0, 1))
    wire_h = 8.2 * K + (tw * 0.55 + edge * 0.45) * 1.6 * K
    h = np.where(wm > 0.5, np.maximum(h, wire_h), h)
    shape_h = np.where(wm > 0.5, np.maximum(shape_h, wire_h), shape_h)
    # A domed nail through the rail every 64 px, and through the leather above it at the
    # half-way point (the hide held down), smaller.
    nails = np.zeros_like(X)
    for k0 in range(int(W / K / 64)):
        for (nx, ny, r, top) in (((k0 + 0.5) * 64, rail0 + 2.6, 2.1, 10.5),):
            dd = np.hypot(xs - nx, y - ny)
            dome = np.sqrt(np.clip(1 - (dd / r) ** 2, 0, 1)) * 1.4 * K + top * K
            m = dd < r
            h = np.where(m, np.maximum(h, dome), h)
            shape_h = np.where(m, np.maximum(shape_h, dome), shape_h)
            nails = np.maximum(nails, m.astype(np.float32))
    R.height = (h * ss).astype(np.float32)
    R.shape_height = (shape_h * ss).astype(np.float32)
    R.alpha = (y < rail1).astype(np.float32)
    R.mat[:] = RL.IDS["leather"]
    R.mat[on_rail] = RL.IDS["iron"]
    R.mat[(nails > 0.5)] = RL.IDS["iron"]
    R.mat[wm > 0.5] = RL.IDS["gold"]
    # The leather's colour: oxblood, blotched as a hide is, darkest toward the screen's edge
    # (the band runs off it) and in the tooling.
    cloud = F.fbm(R.h, R.w, scale=180 * K * ss, octaves=4, seed=85) * 0.5 + 0.5
    fall = 0.5 + 0.5 * np.clip(y / rail0, 0, 1) ** 0.8
    tint = np.where(leather, (0.55 + 0.4 * cloud) * fall * (1 - tool * 0.35), 1.0)
    R.tint = (tint[..., None] * np.ones(3, np.float32)).astype(np.float32)
    # The rail's iron a little warmer than the house's (its cool rim went navy over the warm page).
    R.tint = np.where(on_rail[..., None], R.tint * np.array([1.0, 0.94, 0.84], np.float32), R.tint).astype(np.float32)
    img = R.render("page_header", samples=samples, wear=1.1, grime=0.8, seed=86)
    if PAINT:
        img = paint(img, R, "page_header", "a long band of dark oxblood leather, pebbled grain, blind-tooled with a "
                    "double rule and a row of small punched lozenges, along its foot a slim rail of hand-forged "
                    "blackened iron with a thin twisted gold wire inlaid and domed nails", 0.16)
    small = R.file_size(img)
    band = periodic_middle(small, TW)
    # The shadow the band casts on the page below its rail (the slice's foot).
    out = np.zeros((H, TW, 4), np.float32)
    out[...] = band
    yy = (np.arange(H, dtype=np.float32) / K)[:, None]
    sh = np.clip(1 - (yy - rail1) / 3.0, 0, 1) ** 1.2 * 0.75 * (yy >= rail1)
    a = out[..., 3]
    out[..., :3] = out[..., :3] * a[..., None]
    out[..., 3] = np.maximum(a, sh)
    out[..., :3] = np.where(out[..., 3:4] > 1e-4, out[..., :3] / np.maximum(out[..., 3:4], 1e-4), 0)
    return out


def backdrop_grain(N=512):
    """Grain and dust, tileable: light specks and dark ones at a low alpha, so the blurred
    world behind has a surface (a film's grain, ash in the air) and never a fill."""
    g = F.fbm(N, N, scale=1.6, octaves=2, seed=91)
    g = g / (np.abs(g).max() + 1e-6)
    coarse = F.fbm(N, N, scale=40, octaves=3, seed=92) * 0.5 + 0.5
    amp = 0.10 + 0.05 * coarse
    a = np.abs(g) * amp
    light = g > 0
    rgb = np.where(light[..., None], np.array([1.0, 0.92, 0.82], np.float32), np.array([0.02, 0.015, 0.01], np.float32))
    # Ash: a few soft specks, warm, a little bigger than the grain.
    rng = np.random.default_rng(93)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    for _ in range(70):
        cx, cy, r = rng.uniform(0, N), rng.uniform(0, N), rng.uniform(0.6, 1.8)
        dx = (xx - cx + N / 2) % N - N / 2
        dy = (yy - cy + N / 2) % N - N / 2
        sp = np.exp(-(dx * dx + dy * dy) / (2 * r * r)) * rng.uniform(0.12, 0.3)
        a = np.maximum(a, sp)
        rgb = np.where((sp > a * 0.9)[..., None], np.array([0.85, 0.72, 0.6], np.float32), rgb)
    return np.dstack([rgb, np.clip(a, 0, 1)]).astype(np.float32)


def backdrop_edges(W=1920, H=1080):
    """Smoke drifting in from the edges, thickest in the corners, and the ember's light low
    along the foot; clear in the middle where the page is read. Made at half and enlarged:
    there is nothing sharp in it."""
    w, h = W // 2, H // 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h
    # Smoke: warped noise, so it curls instead of blotting.
    wx = F.fbm(h, w, scale=180, octaves=3, seed=94) * 40
    wy = F.fbm(h, w, scale=180, octaves=3, seed=95) * 40
    base = F.fbm(h, w, scale=120, octaves=5, seed=96)
    smoke = cv2.remap(base.astype(np.float32), (xx + wx).astype(np.float32), (yy + wy).astype(np.float32), cv2.INTER_LINEAR,
                      borderMode=cv2.BORDER_WRAP)
    smoke = np.clip(smoke * 0.5 + 0.5, 0, 1) ** 1.6
    edge = np.clip(1 - np.minimum(np.minimum(u, 1 - u) / 0.22, np.minimum(v, 1 - v) / 0.3), 0, 1) ** 1.3
    corner = np.clip(1 - np.hypot(np.minimum(u, 1 - u) / 0.35, np.minimum(v, 1 - v) / 0.45), 0, 1)
    dens = np.clip(smoke * (edge * 0.8 + corner * 0.6), 0, 1)
    a_smoke = dens * 0.55
    # Low: the ember's light along the foot, in pools, and lighting the smoke that lies there.
    pools = F.fbm(h, w, scale=260, octaves=2, seed=97) * 0.5 + 0.5
    low = np.clip((v - 0.62) / 0.38, 0, 1) ** 1.8 * (0.5 + 0.7 * pools)
    ember = np.array([1.0, 0.45, 0.12], np.float32)
    dark = np.array([0.07, 0.05, 0.045], np.float32)
    lit = np.array([0.42, 0.24, 0.14], np.float32)
    smoke_col = dark * (1 - low[..., None]) + lit * low[..., None]
    a_ember = low * 0.22
    a = a_smoke + a_ember * (1 - a_smoke)
    rgb = (smoke_col * a_smoke[..., None] + ember * (a_ember * (1 - a_smoke))[..., None]) / np.maximum(a[..., None], 1e-4)
    img = np.dstack([rgb, a]).astype(np.float32)
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC).clip(0, 1)


def ember_light(R, hole_mask, cx, cy, size, seed):
    """The ember asleep in a coin's hole: a coal deep in the dark, hot where it is not crusted
    over, dull red at the hole's rim, black between (never a flat orange disc)."""
    X, Y = R.xx / R.ss, R.yy / R.ss
    n = F.fbm(R.h, R.w, scale=max(4, R.w / 14), octaves=3, seed=seed) * 0.5 + 0.5
    d = np.hypot(X - cx, Y - (cy + size * 0.04)) / (size * 0.15)
    core = np.exp(-d ** 2 * 1.6)
    crust = np.clip((n - 0.38) * 3.0, 0, 1)
    hot = hole_mask * core * crust
    dull = hole_mask * np.exp(-d ** 2 * 0.5) * 0.35
    return (hot[..., None] * F.hexc("#ffa040") * 1.6 + dull[..., None] * F.hexc("#9a2004")).astype(np.float32)


def column_divider(ss=4, samples=128):
    """The rule between a page's columns (frames/column_divider.png, 48x1120, 24x560 shown,
    slice 0 24 0 24, the middle tiled): a rod of the binders' twisted iron, two strands, with a
    forged collar every 128 px; its ends fade into the page. The slice repeats only the middle
    (512 shown), so the twist and the collars are periodic over exactly that, and the ends
    carry on the same pattern. The stone at its middle is a piece of its own."""
    TW, END, PER = 48, 48, 1024            # file px: width, each end, the repeating middle
    TH = PER + 2 * END
    PAD = 256                              # rendered past both ends, cropped (the light's edge)
    R = RL.Relief(TW, TH + 2 * PAD, ss)
    X, Y = R.xx / ss, R.yy / ss
    Yp = Y - PAD - END                     # 0 where the repeating middle starts
    cx = TW / 2
    across = X - cx
    th = 4.6 * K
    pitch = PER / 98.0
    s_ = Yp / pitch
    tw = np.zeros_like(X)
    for k0 in (0.0, 0.5):
        uu = ((across / th) - (((s_ + k0) % 1.0) - 0.5)) % 1.0 - 0.5
        tw = np.maximum(tw, np.sqrt(np.clip(1 - (uu / 0.5) ** 2, 0, 1)))
    rod_m = np.clip((th / 2 - np.abs(across)) * ss + 0.5, 0, 1)
    edge = np.sqrt(np.clip(1 - (across / (th / 2)) ** 2, 0, 1))
    h = (tw * 0.55 + edge * 0.45) * 2.6 * K * (rod_m > 0.02)
    shape = edge * 2.6 * K * (rod_m > 0.02)
    # A collar every 128 px: a short forged band round the rod, its edges chamfered.
    col = np.zeros_like(X)
    for k0 in range(-2, int((TH + 2 * PAD) / K / 128) + 2):
        yc = (k0 + 0.5) * 128 * K
        dy = np.abs(Yp - yc)
        band = (np.abs(across) < 4.6 * K) & (dy < 3.2 * K)
        prof = np.sqrt(np.clip(1 - (across / (4.6 * K)) ** 2, 0, 1)) * 3.4 * K * np.clip((3.2 * K - dy) / (1.0 * K), 0, 1) ** 0.5
        h = np.where(band, np.maximum(h, prof), h)
        shape = np.where(band, np.maximum(shape, prof), shape)
        col = np.maximum(col, band.astype(np.float32))
    dents = RL.hammered(R, cell=2.5 * K, depth=0.08 * K, seed=101) / ss
    h = h + dents * (col > 0.5)
    R.height = (h * ss).astype(np.float32)
    R.shape_height = (shape * ss).astype(np.float32)
    R.alpha = np.maximum(rod_m, col).astype(np.float32)
    R.mat[:] = RL.IDS["iron"]
    R.mat[col > 0.5] = RL.IDS["gold_dim"]
    R.tint = np.ones((R.h, R.w, 3), np.float32) * np.array([1.0, 0.95, 0.86], np.float32)
    img = R.render("page_divider", samples=samples, wear=1.4, grime=0.7, seed=102)
    small = R.file_size(img)
    mid = small[PAD:PAD + TH].copy()
    # A soft shadow either side, so it lies on the page and is not pasted on it.
    a = mid[..., 3]
    sh = cv2.GaussianBlur(a, (0, 0), 3.0 * K) * 0.45
    sh = np.roll(sh, int(1.5 * K), axis=1)
    out_a = a + sh * (1 - a)
    rgb = mid[..., :3] * a[..., None] / np.maximum(out_a[..., None], 1e-4)
    out = np.dstack([rgb, out_a]).astype(np.float32)
    # The ends fade (the slice's 24 px top and bottom are the ends, the middle repeats).
    yy = np.arange(TH, dtype=np.float32)[:, None] / K
    fade = np.clip(yy / 24.0, 0, 1) * np.clip((TH / K - yy) / 24.0, 0, 1)
    out[..., 3] *= fade ** 1.5
    return out


def coin_piece(size_shown, ss=8, samples=160, name="coin", rot=45.0, glow=1.0):
    """A binders' coin by itself, set on its point, its hole lit by the sleeping ember."""
    W = int(size_shown * K)
    R = RL.Relief(W, W, ss)
    c = W / 2
    # Set on its point the square's diagonal is what must fit: 0.62 of the side leaves a margin.
    hh, cm, hm = RL.coin(R, c, c, W * 0.62, 1.0, hole=0.36, rot=rot)
    R.height = (hh * cm * ss).astype(np.float32)
    R.shape_height = R.height.copy()
    R.alpha = cm.astype(np.float32)
    R.mat[:] = RL.IDS["gold_dim"]
    R.mat[hm > 0.5] = RL.IDS["ember"]
    R.emit = ember_light(R, hm, c, c, W * 0.62, seed=103) * glow
    img = R.render(f"page_{name}", samples=samples, wear=1.3, grime=0.8, seed=104)
    return R.file_size(img)


def periodic(R, m, P, fn):
    """A surface field that repeats every P file px from m in from the edge both ways: what a
    nine-slice repeats is exactly one period of it, so its strips and middle tile with no seam
    and need no blending."""
    ss = R.ss
    base = fn(P * ss, P * ss)
    yy = (np.arange(R.h) - m * ss) % (P * ss)
    xx = (np.arange(R.w) - m * ss) % (P * ss)
    return base[yy[:, None], xx[None, :]]


def frame_sd(X, Y, x0, y0, x1, y1):
    return np.minimum(np.minimum(X - x0, x1 - X), np.minimum(Y - y0, y1 - Y))


def along_edge(X, Y, W, H):
    """A coordinate along whichever edge is nearest (for the wire's twist and the nails)."""
    return np.where(np.minimum(X, W - X) < np.minimum(Y, H - Y), Y, X)


def twist(R, across, along, th, pitch, base, height):
    s_ = along / pitch
    tw = np.zeros_like(across)
    for k0 in (0.0, 0.5):
        uu = ((across / th) - (((s_ + k0) % 1.0) - 0.5)) % 1.0 - 0.5
        tw = np.maximum(tw, np.sqrt(np.clip(1 - (uu / 0.5) ** 2, 0, 1)))
    m = np.clip((th / 2 - np.abs(across)) * R.ss + 0.5, 0, 1)
    edge = np.sqrt(np.clip(1 - (across / (th / 2)) ** 2, 0, 1))
    return base + (tw * 0.55 + edge * 0.45) * height, m


def hero_plate(ss=2, samples=160):
    """The heavy frame round the figure on a page (frames/hero_plate.png, 512x512, 256x256
    shown, slice 56 each side, Tile, Out 12; the middle clear). Strap iron, chamfered and
    planished, the binders' twisted wire laid in a channel along it and nailed either side;
    at each corner a forged block with a binders' coin, its ember asleep, and a lamp-iron
    bracket's scrolls running out along both edges; inside, a bead and a shadow, so the
    figure stands back in it."""
    W = H = 512
    o, m = 24, 112                  # the overhang past the control, the slice margin (file px)
    P = W - 2 * m
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / ss, R.yy / ss
    sd = frame_sd(X, Y, o, o, W - o, H - o)
    strap_w = 36.0
    on = (sd >= 0) & (sd < strap_w + 4)
    # The strap: outer chamfer, a crowned face, the channel, an inner chamfer down to a bead.
    t_out = np.clip(sd / 5.0, 0, 1)
    t_in = np.clip((strap_w - sd) / 5.0, 0, 1)
    face = 10.0 + 1.2 * np.sin(np.clip(sd / strap_w, 0, 1) * math.pi)
    h = np.where(sd < strap_w, np.minimum(t_out, t_in) * face, 0)
    bead = np.exp(-((sd - (strap_w + 1.5)) / 1.6) ** 2) * 3.0
    h = np.maximum(h, bead * (sd > strap_w - 2))
    across = sd - strap_w / 2
    groove = np.clip((4.0 - np.abs(across)) * ss * 0.5 + 0.5, 0, 1) * (sd > 0) * (sd < strap_w)
    h = h - groove * 2.4
    along = along_edge(X, Y, W, H)
    wh, wm = twist(R, across, along - m, 6.0, P / 30.0, 8.6, 3.0)
    h = np.where((wm > 0.5) & on, np.maximum(h, wh), h)
    shape = h.copy()
    # Nails either side of the wire, one every 48 px along (six to a repeat).
    nails = np.zeros_like(X)
    for side in (7.0, strap_w - 7.0):
        u = ((along - m) % 48.0) - 24.0
        dd = np.hypot(u, sd - side)
        dome = np.sqrt(np.clip(1 - (dd / 2.8) ** 2, 0, 1)) * 2.2 + face
        nm = (dd < 2.8) & on
        h = np.where(nm, np.maximum(h, dome), h)
        shape = np.where(nm, np.maximum(shape, dome), shape)
        nails = np.maximum(nails, nm.astype(np.float32))
    # Planishing and dents, periodic over the repeat.
    facet = periodic(R, m, P, lambda a, b: F.facets(a, b, cell=20.0 * ss, tilt=0.02, seed=111, soften=1.5 * ss)) / ss
    dents = periodic(R, m, P, lambda a, b: F.worley_dents(a, b, cell=7.0 * ss, depth=0.26 * ss, seed=112)) / ss
    plain = on & (wm < 0.5) & (nails < 0.5)
    h = h + (facet + dents) * plain
    # The corners: a forged block over the strap, the coin on it, the bracket's scrolls.
    import chrome as CH
    blocks = np.zeros_like(X)
    coins = np.zeros_like(X)
    holes = np.zeros_like(X)
    arms = np.zeros_like(X)
    glow = np.zeros((R.h, R.w, 3), np.float32)
    for cx, cy, sx, sy in ((o + 26, o + 26, 1, 1), (W - o - 26, o + 26, -1, 1), (o + 26, H - o - 26, 1, -1),
                           (W - o - 26, H - o - 26, -1, -1)):
        for pts in CH.bracket_scrolls(cx, cy, sx, sy, 36, 9.0, 0):
            bh, bm = RL.bar(R, pts, 9.0, 3.6)
            bh = bh + 12.0
            h = np.where(bm > 0.5, np.maximum(h, bh), h)
            shape = np.where(bm > 0.5, np.maximum(shape, bh), shape)
            arms = np.maximum(arms, bm)
        bsd = np.minimum(29.0 - np.abs(X - cx), 29.0 - np.abs(Y - cy))
        bsd = np.minimum(bsd, (40.0 - (np.abs(X - cx) + np.abs(Y - cy))) / math.sqrt(2))
        blk = bsd > 0
        bprof = 12.5 + np.clip(bsd / 4.0, 0, 1) * 2.0
        h = np.where(blk, np.maximum(h, bprof), h)
        shape = np.where(blk, np.maximum(shape, bprof), shape)
        blocks = np.maximum(blocks, blk.astype(np.float32))
        chh, cm, hm = RL.coin(R, cx, cy, 30.0, 14.5, hole=0.36)
        h = np.where(cm > 0.5, np.maximum(h, chh), h)
        shape = np.where(cm > 0.5, np.maximum(shape, chh), shape)
        coins = np.maximum(coins, cm)
        holes = np.maximum(holes, hm)
        glow += ember_light(R, hm, cx, cy, 30.0, seed=113 + int(cx))
    bd = RL.hammered(R, cell=5.0, depth=0.22, seed=117) / ss
    h = h + bd * (blocks > 0.5) * (coins < 0.5)
    cover = np.clip(sd * ss + 0.5, 0, 1) * (sd < strap_w + 4)
    cover = np.maximum.reduce([cover, arms, (blocks > 0.5).astype(np.float32), coins])
    R.height = (h * ss * (cover > 0.02)).astype(np.float32)
    R.shape_height = (shape * ss * (cover > 0.02)).astype(np.float32)
    R.alpha = cover.astype(np.float32)
    R.mat[:] = RL.IDS["iron"]
    R.mat[(wm > 0.5) & on & (blocks < 0.5)] = RL.IDS["gold"]
    R.mat[coins > 0.5] = RL.IDS["gold_dim"]
    R.mat[holes > 0.5] = RL.IDS["ember"]
    R.tint = (np.ones((R.h, R.w, 3), np.float32) * np.array([1.0, 0.96, 0.9], np.float32)).astype(np.float32)
    R.emit = glow
    img = R.render("page_hero_plate", samples=samples, wear=1.3, grime=0.9, seed=118)
    small = R.file_size(img)
    # The shadow inside: the figure stands back in the frame.
    sdf = frame_sd(*np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5), o, o, W - o, H - o)
    sh = np.clip(1 - (sdf - (strap_w + 3)) / 26.0, 0, 1) ** 1.8 * 0.6 * (sdf > strap_w + 1)
    a = small[..., 3]
    out_a = a + sh * (1 - a)
    rgb = small[..., :3] * a[..., None] / np.maximum(out_a[..., None], 1e-4)
    return np.dstack([rgb, out_a]).astype(np.float32)


def card_light(ss=3, samples=160):
    """A lighter frame for cards and tooltips (frames/card_light.png, 320x320, 160x160 shown,
    slice 20 each side, Tile): a dark vellum, a little translucent, blind-tooled with a fine
    line; round its edge a slim bead of iron, and at the corners small forged caps nailed
    through. Quiet behind words."""
    W = H = 320
    m = 40
    P = W - 2 * m
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / ss, R.yy / ss
    sd = frame_sd(X, Y, 0, 0, W, H)
    bead_w = 9.0
    bead = np.where(sd < bead_w, np.sqrt(np.clip(1 - ((sd - bead_w / 2) / (bead_w / 2)) ** 2, 0, 1)) * 5.0 + 1.0, 0)
    fibre = periodic(R, m, P, lambda a, b: F.fbm(a, b, scale=1.4 * ss * K, octaves=2, seed=121)) / ss
    cockle = periodic(R, m, P, lambda a, b: F.fbm(a, b, scale=40 * ss * K, octaves=3, seed=122)) / ss
    vellum = sd >= bead_w
    h = np.where(vellum, 1.2 + fibre * 0.12 + cockle * 0.5, bead)
    tool = np.clip((0.8 - np.abs(sd - 17.0)) * ss * 0.5 + 0.5, 0, 1)
    h = h - tool * 0.6
    shape = np.where(vellum, 1.2 - tool * 0.6, bead)
    dents = periodic(R, m, P, lambda a, b: F.worley_dents(a, b, cell=4.0 * ss, depth=0.18 * ss, seed=123)) / ss
    h = h + dents * (~vellum)
    caps = np.zeros_like(X)
    for cx, cy, sx, sy in ((0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1), (W, H, -1, -1)):
        u, v = (X - cx) * sx, (Y - cy) * sy
        cap = ((u < 30) & (v < 13)) | ((u < 13) & (v < 30))
        csd = np.minimum(np.where(u < 13, 30 - v, 13 - v), np.where(v < 13, 30 - u, 13 - u))
        cprof = 6.5 + np.clip(csd / 2.5, 0, 1) * 1.6
        h = np.where(cap, np.maximum(h, cprof), h)
        shape = np.where(cap, np.maximum(shape, cprof), shape)
        caps = np.maximum(caps, cap.astype(np.float32))
        dd = np.hypot(u - 6.5, v - 6.5)
        nail = dd < 2.6
        h = np.where(nail, np.maximum(h, 8.3 + np.sqrt(np.clip(1 - (dd / 2.6) ** 2, 0, 1)) * 1.6), h)
    R.height = (h * ss).astype(np.float32)
    R.shape_height = (shape * ss).astype(np.float32)
    R.alpha = np.ones_like(X, np.float32)
    R.mat[:] = RL.IDS["iron"]
    R.mat[vellum & (caps < 0.5)] = RL.IDS["paper"]
    cloud = periodic(R, m, P, lambda a, b: F.fbm(a, b, scale=60 * ss * K, octaves=4, seed=124)) * 0.5 + 0.5
    vt = (0.115 + 0.05 * cloud) * (1 - tool * 0.3)
    tint = np.where(vellum[..., None] & (caps[..., None] < 0.5), vt[..., None] * np.array([1.0, 0.86, 0.7], np.float32), 1.0)
    R.tint = tint.astype(np.float32)
    img = R.render("page_card_light", samples=samples, wear=1.2, grime=0.6, seed=125)
    small = R.file_size(img)
    # The vellum a little translucent, so the world behind is felt and not seen.
    sdf = frame_sd(*np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5), 0, 0, W, H)
    small[..., 3] = np.where(sdf > bead_w + 1, 0.93, small[..., 3])
    return small


def column_divider_stone():
    """The stone at a divider's middle (frames/column_divider_stone.png, 64x64, 32x32 shown)."""
    return coin_piece(32, name="divider_stone")


def section_mark():
    """Before a section's title on its baseline (ornaments/section_mark.png, 24x24, 12x12
    shown): a small binders' coin, its ember barely awake."""
    return coin_piece(12, ss=16, name="section_mark", glow=0.8)


BUILD = {
    "header": ("frames/header.png", header),
    "column_divider": ("frames/column_divider.png", column_divider),
    "column_divider_stone": ("frames/column_divider_stone.png", column_divider_stone),
    "section_mark": ("ornaments/section_mark.png", section_mark),
    "hero_plate": ("frames/hero_plate.png", hero_plate),
    "card_light": ("frames/card_light.png", card_light),
    "backdrop_grain": ("page/backdrop_grain.png", backdrop_grain),
    "backdrop_edges": ("page/backdrop_edges.png", backdrop_edges),
}


def build(name):
    rel, fn = BUILD[name]
    save(fn(), rel)


if __name__ == "__main__":
    for nm in sys.argv[1:] or list(BUILD):
        build(nm)
        print("built", nm, flush=True)
