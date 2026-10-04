"""The HUD's two medallions, modelled as reliefs (relief.py) and rendered in Blender.

  level  (hud/medal_level.png, 116 square, 58 shown round the 46 px medal): the Legion's
         seal. A ring of drawn iron bent round and forge-welded at its foot, planished flat
         with its edges chamfered; the binders' twisted wire laid round it; at its inner edge
         the seven notches the binders' keys fit, opening into a deep well where the code
         writes the level, the Morrow's ember smouldering at the well's foot and leaking up
         into the notches.
  heart  (hud/medal_heart.png, 128 square, 64 shown round the 41 px medal): the heart's
         setting. In the story each link of the chain is anchored in a heart, a cut stone;
         the survivor's is held in a forged bezel by three iron claws, a staple at its head
         holding a link of the chain. The stone itself is the heart icon the code lays in
         the middle (icons/glyph_color/heart.png, 22 px shown), cut to match.

    python tools/uiforge/medals.py [level heart]
"""
from __future__ import annotations

import math
import os
import sys

import cv2
import numpy as np

import forge as F
import relief as RL

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui")


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def band_profile(r, r_out, r_in, top, outer_ch=2.6, inner_ch=2.4, shoulder=1.6):
    """A planished bar's section across a ring (file px): chamfered both edges, flat on top,
    the chamfers' shoulders rounded so they catch the light as a line, not a facet."""
    # Distance in from each edge.
    do = r_out - r
    di = r - r_in
    def edge(d, ch):
        t = np.clip(d / ch, 0, 1)
        # A chamfer rising to 80%, then a rounded shoulder to the top.
        lo = np.clip(d / ch, 0, 1) * 0.8
        hi = 0.8 + 0.2 * np.sqrt(np.clip(1 - (1 - np.clip((d - ch) / shoulder, 0, 1)) ** 2, 0, 1))
        return np.where(d < ch, lo, hi) * (d > 0)
    return np.minimum(edge(do, outer_ch), edge(di, inner_ch)) * top


def level(ss=8, samples=160):
    W = 116
    c = W / 2
    S = ss
    R = RL.Relief(W, W, ss)
    r, th = R.polar(c, c)
    X, Y = R.xx / S, R.yy / S
    r_out = 55.6 + RL.ragged(th, 0.45, seed=3, lobes=(3, 5, 8, 13))
    r_in = 30.2          # the band's inner edge
    r_plate = 28.4       # the well's plate, set in with a gap round it
    top = 6.0
    cover = np.clip((r_out - r) * S + 0.5, 0, 1)
    # The band: a little crowned across its width so it takes the light as a gradient.
    h = band_profile(r, r_out, r_in, top, outer_ch=2.4, inner_ch=1.8, shoulder=0.8)
    crown = np.sin(np.clip((r - r_in) / (r_out - r_in), 0, 1) * math.pi) * 1.3
    h = h + crown * (h > 0)
    # The weld at the foot: where the bar's two ends were hammered together, a seam across
    # the band, the iron a little upset (thicker) either side of it.
    a_seam = math.pi + 0.06
    across = np.angle(np.exp(1j * (th - a_seam))) * r  # arc distance from the seam (file px)
    on_band = smoothstep(0.7, 0.95, h / top)
    h = h + np.exp(-(across / 3.2) ** 2) * 0.6 * on_band
    seam = np.exp(-(across / 0.45) ** 2) * (r > r_in + 1.5) * (r < r_out - 1.5)
    h = h - seam * 1.2
    # The wire's groove and the wire, round the outer half of the band.
    r_wire = 47.6
    groove = np.clip((2.0 - np.abs(r - r_wire)) * S, 0, 1)
    h = h - groove * 1.0
    wh, wm = RL.rope(R, c, c, r_wire, 3.2, 2.9, 2.3)
    h = np.maximum(h, np.where(wm > 0.5, top + 0.2 + wh / S, -99))
    # The seven notches cut into the band's inner edge (where the binders' keys would bite),
    # short, square-ended, down to the gap's floor. The first at the top.
    notch = np.zeros_like(r)
    depth_in = np.zeros_like(r)  # 0 at the mouth, 1 at the notch's end
    r_end = 35.2
    for k in range(7):
        a = k * 2 * math.pi / 7
        ux, uy = math.sin(a), -math.cos(a)
        # Along and across the notch's axis.
        al = (X - c) * ux + (Y - c) * uy
        ac = -(X - c) * uy + (Y - c) * ux
        sd = np.minimum(2.3 - np.abs(ac), r_end - al)
        m = np.clip(sd * S + 0.5, 0, 1) * (al > r_plate - 1)
        notch = np.maximum(notch, m)
        depth_in = np.where(m > 0.5, np.clip((al - r_in) / (r_end - r_in), 0, 1), depth_in)
    shape = h.copy()
    # Hammer: planished facets on the band's top (they change the light, not the form).
    facet = F.facets(R.h, R.w, cell=7.0 * S, tilt=0.022, seed=4, soften=1.2 * S) / S
    dents = RL.hammered(R, cell=3.6, depth=0.16, seed=5) / S
    h = h + (facet + dents) * on_band * (1 - groove)
    # The gap and the notches: down to the base, where the ember is.
    gap = (r >= r_plate) & (r < r_in + 0.5)
    hole = np.maximum(notch, gap.astype(np.float32))
    holeb = cv2.GaussianBlur(hole, (0, 0), 0.35 * S)
    h = h * (1 - holeb)
    shape = shape * (1 - holeb)
    # The well's plate: a dark disc set into the ring, its edge rounded, a shallow dish.
    plate = r < r_plate
    pe = np.sqrt(np.clip(1 - (1 - np.clip((r_plate - r) / 1.4, 0, 1)) ** 2, 0, 1))
    dish = (2.4 - 0.6 * (1 - (r / r_plate) ** 2)) * pe
    h = np.where(plate, dish + dents * 0.5, h)
    shape = np.where(plate, dish, shape)
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = (shape * S * cover).astype(np.float32)
    R.alpha = cover
    R.mat[:] = RL.IDS["iron"]
    R.mat[plate] = RL.IDS["iron_dark"]
    R.mat[hole > 0.5] = RL.IDS["ember"]
    R.mat[wm > 0.5] = RL.IDS["gold"]
    # The ember below: seen through the gap round the plate (thick at the foot where it has
    # settled, a thread up the sides, out at the top) and in each notch (hot at the mouth,
    # dull at the end). Never even: it breathes along its length.
    n = F.fbm(R.h, R.w, scale=R.w / 9, octaves=4, seed=9) * 0.5 + 0.5
    nf = F.fbm(R.h, R.w, scale=R.w / 30, octaves=3, seed=10) * 0.5 + 0.5
    low = np.clip(0.5 - 0.5 * np.cos(th), 0, 1)  # 0 at the top, 1 at the foot
    # Breaks: lengths of the gap where the coals have gone dark.
    breaks = smoothstep(0.38, 0.62, F.fbm(R.h, R.w, scale=R.w / 14, octaves=3, seed=11) * 0.5 + 0.5)
    g_gap = gap * (low ** 2.6) * (0.25 + 1.2 * n) * (0.55 + 0.7 * nf) * (0.25 + 0.75 * breaks)
    # In a notch the light comes from below its mouth, where the gap runs under it.
    g_notch = (notch > 0.5) * np.exp(-(depth_in / 0.28) ** 2) * (0.15 + 0.85 * low ** 1.4) * (0.6 + 0.6 * nf)
    glow = np.maximum(g_gap, g_notch)
    hot, deep = F.hexc("#ff8a2a"), F.hexc("#b02404")
    R.emit = (glow[..., None] * (hot * 1.2 + deep * 1.0) * 1.3).astype(np.float32)
    # Heat in the iron about the openings: a dull red in the black, close to them.
    heat = cv2.GaussianBlur(glow.astype(np.float32), (0, 0), 0.9 * S) * (1 - hole) * 0.5
    R.emit += (heat[..., None] * deep * 0.6).astype(np.float32)
    # The plate darkens toward its middle so the number reads.
    R.tint = np.where(plate[..., None], (0.55 + 0.45 * (r / r_plate) ** 2)[..., None], 1.0).astype(np.float32)
    img = R.render("medal_level", samples=samples, wear=1.3, grime=0.8, seed=2)
    return R, img


def stadium_sd(X, Y, cx, cy, length, width, angle=0.0):
    """Distance to a chain link's centre line (a stadium), file px."""
    ca, sa = math.cos(angle), math.sin(angle)
    u = (X - cx) * ca + (Y - cy) * sa
    v = -(X - cx) * sa + (Y - cy) * ca
    st = max(length - width, 0) / 2
    r = width / 2
    uu = np.clip(np.abs(u) - st, 0, None)
    return np.abs(np.hypot(uu, v) - r)


def heart_pts(cx, cy, s, n=240, plump=1.0):
    """The classic heart curve (x = 16 sin^3 t, y = 13 cos t - 5 cos 2t - 2 cos 3t - cos 4t),
    half-width `s` (file px), centred on its bounding box, point down."""
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = 16 * np.sin(t) ** 3
    y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    y = y - (y.max() + y.min()) / 2
    x = np.sign(x) * np.abs(x / 16) ** (1 / plump) * 16
    k = s / 16
    return [(cx + a * k, cy + b * k) for a, b in zip(x, y)]


def heart_sd(X, Y, cx, cy, s, plump=1.0):
    """Signed distance (positive inside, file px) to the heart of half-width s."""
    return F.sd_poly(X, Y, heart_pts(cx, cy, s, plump=plump))


# The stone: its half-width in the medal's file px (the icon is drawn 22 px shown = 44 file
# px over the medal's middle; the heart fills 84% of the icon's width).
STONE = 44 * 0.84 / 2
CHAIN = 16  # links round the heart (0: none)


def heart(ss=8, samples=160):
    W = 128
    c = W / 2
    S = ss
    R = RL.Relief(W, W, ss)
    r, th = R.polar(c, c)
    X, Y = R.xx / S, R.yy / S
    r_out = 60.5 + RL.ragged(th, 0.45, seed=7, lobes=(3, 5, 8, 13))
    top = 6.0
    cover = np.clip((r_out - r) * S + 0.5, 0, 1)
    # A round bezel with a heart-shaped hole the stone sits in.
    hole = heart_sd(X, Y, c, c, STONE + 2.6)
    do = r_out - r
    di = -hole

    def edge(d, ch, shoulder):
        lo = np.clip(d / ch, 0, 1) * 0.8
        hi = 0.8 + 0.2 * np.sqrt(np.clip(1 - (1 - np.clip((d - ch) / shoulder, 0, 1)) ** 2, 0, 1))
        return np.where(d < ch, lo, hi) * (d > 0)
    h = np.minimum(edge(do, 2.4, 0.9), edge(di, 2.0, 0.8)) * top
    span = np.clip(di / np.maximum(di + do, 1e-3), 0, 1)
    h = h + np.sin(span * math.pi) * 1.4 * (h > 0)
    on_band = smoothstep(0.7, 0.95, h / top)
    # The wire, round the outer part of the bezel.
    r_wire = 52.0
    groove = np.clip((2.0 - np.abs(r - r_wire)) * S, 0, 1)
    h = h - groove * 1.0
    wh, wm = RL.rope(R, c, c, r_wire, 3.2, 2.9, 2.3)
    h = np.maximum(h, np.where(wm > 0.5, top + 0.3 + wh / S, -99))
    # The hole's floor, under the stone and the dark gap round it.
    well = hole > 0
    h = np.where(well, 0.8, h)
    shape = h.copy()
    # Three claws over the lip to the stone's edge: at its two lobes and its point.
    claws = np.zeros_like(r)
    claw_h = np.zeros_like(r)
    stone_sd = heart_sd(X, Y, c, c, STONE)
    for (px, py) in ((c - STONE * 0.86, c - STONE * 0.42), (c + STONE * 0.86, c - STONE * 0.42), (c, c + STONE * 0.92)):
        ux, uy = px - c, py - c
        L = math.hypot(ux, uy)
        ux, uy = ux / L, uy / L
        al = (X - px) * ux + (Y - py) * uy      # outward from the stone's edge
        ac = -(X - px) * uy + (Y - py) * ux
        t = np.clip(al / 7.0, 0, 1)
        half = 1.9 + 1.6 * t
        sd = np.minimum(half - np.abs(ac), np.minimum(al + 0.2, 7.5 - al))
        m = np.clip(sd * S + 0.5, 0, 1) * (stone_sd < 0.2)
        across = np.sqrt(np.clip(1 - (ac / np.maximum(half, 0.1)) ** 2, 0, 1))
        prof = (top + 1.6 - 1.0 * (1 - t)) * (0.6 + 0.4 * across)
        claws = np.maximum(claws, m)
        claw_h = np.maximum(claw_h, prof * m)
    h = np.where(claws > 0.5, np.maximum(h, claw_h), h)
    shape = np.where(claws > 0.5, np.maximum(shape, claw_h), shape)
    # The chain coiled round the heart in a channel cut in the bezel: links alternately lying
    # flat and standing on edge, and at the head one link pried open, the ember at its break.
    if CHAIN:
        rc = 36.0
        ch_w = 6.2
        chan = np.clip((ch_w - np.abs(r - rc)) * S, 0, 1) * (hole < -3.0)
        h = h * (1 - chan) + 1.6 * chan
        shape = shape * (1 - chan) + 1.6 * chan
        N = CHAIN
        link_h = np.zeros_like(r)
        link_m = np.zeros_like(r)
        brk = np.zeros_like(r)
        for i in range(N):
            a = 2 * math.pi * i / N
            lx, ly = c + math.sin(a) * rc, c - math.cos(a) * rc
            tang = a  # along the circle (file y down)
            if i % 2 == 0:
                d = stadium_sd(X, Y, lx, ly, 16.5, 8.6, angle=tang)
                rr_ = 1.75
                hh = np.sqrt(np.clip(1 - (d / rr_) ** 2, 0, 1)) * rr_ + 2.4
                if i == 0:
                    # The open link: its outer side cut through, the ends sprung apart.
                    ca, sa = math.cos(tang), math.sin(tang)
                    v = -(X - lx) * sa + (Y - ly) * ca
                    u = (X - lx) * ca + (Y - ly) * sa
                    cut = (np.abs(u) < 2.2) & (v < 0)
                    hh = np.where(cut, 0, hh)
                    brk = np.exp(-((u / 1.4) ** 2 + ((v + 4.3) / 1.2) ** 2))
            else:
                ca, sa = math.cos(tang), math.sin(tang)
                u = (X - lx) * ca + (Y - ly) * sa
                v = -(X - lx) * sa + (Y - ly) * ca
                d = np.hypot(np.clip(np.abs(u) - 6.0, 0, None), v)
                rr_ = 1.75
                hh = np.sqrt(np.clip(1 - (d / rr_) ** 2, 0, 1)) * rr_ + 4.6
            m = (hh > 2.41) * np.clip((rr_ - d) * S + 0.5, 0, 1)
            link_h = np.maximum(link_h, hh * m)
            link_m = np.maximum(link_m, m)
        h = np.where(link_m > 0.5, np.maximum(h, link_h), h)
        shape = np.where(link_m > 0.5, np.maximum(shape, link_h), shape)
        chain_m = link_m
    else:
        chain_m = np.zeros_like(r)
        brk = np.zeros_like(r)
    facet = F.facets(R.h, R.w, cell=7.0 * S, tilt=0.022, seed=14, soften=1.2 * S) / S
    dents = RL.hammered(R, cell=3.6, depth=0.16, seed=15) / S
    h = h + (facet + dents) * on_band * (1 - groove) * (claws < 0.5) * (chain_m < 0.5)
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = (shape * S * cover).astype(np.float32)
    R.alpha = cover
    R.mat[:] = RL.IDS["iron"]
    R.mat[well] = RL.IDS["iron_dark"]
    R.mat[wm > 0.5] = RL.IDS["gold"]
    R.mat[chain_m > 0.5] = RL.IDS["chain"]
    # The stone's light in the gap round it: blood red, in the dark.
    n = F.fbm(R.h, R.w, scale=R.w / 9, octaves=4, seed=19) * 0.5 + 0.5
    halo = well * np.exp(-(np.clip(-stone_sd, 0, None) / 1.6)) * (0.5 + 0.7 * n)
    R.emit = (halo[..., None] * (F.hexc("#e01810") * 0.5 + F.hexc("#5a0408") * 0.4)).astype(np.float32)
    R.emit += (brk[..., None] * F.hexc("#ff8a2a") * 3.0).astype(np.float32)
    R.tint = np.where(well[..., None], np.array([0.6, 0.32, 0.32], np.float32), 1.0).astype(np.float32)
    if CHAIN:
        floor = (chan > 0.5) & (chain_m < 0.5)
        R.tint = np.where(floor[..., None], 0.4, R.tint).astype(np.float32)
    img = R.render("medal_heart", samples=samples, wear=1.3, grime=0.8, seed=6)
    return R, img


def stone(ss=4, samples=192):
    """The heart-stone (icons/glyph_color/heart.png, 256 square, drawn 22 px over the heart
    medallion): blood-red, cut in facets, lit from inside."""
    W = 256
    c = W / 2
    S = ss
    R = RL.Relief(W, W, ss)
    X, Y = R.xx / S, R.yy / S
    s_ = W * 0.84 / 2
    sd = heart_sd(X, Y, c, c, s_)
    cover = np.clip(sd * S + 0.5, 0, 1)
    # A cabochon over the heart, then cut: the lower envelope of planes tangent to it at a
    # scatter of points is a convex stone of flat facets.
    edge = 50.0
    hgt = 40.0
    # The stone's crown is cut over the heart's convex hull (a heart-cut stone is a convex
    # stone with the cleft cut into it), so the facets' planes meet as a gem's do.
    hull = cv2.convexHull(np.array(heart_pts(c, c, s_, n=600), np.float32)).reshape(-1, 2)
    hsd = F.sd_poly(X, Y, [tuple(p) for p in hull])
    dome = np.sqrt(np.clip(hsd / edge, 0, 1) * (2 - np.clip(hsd / edge, 0, 1))) * hgt + np.clip(hsd - edge, 0, None) * 0.18
    dome = cv2.GaussianBlur(dome.astype(np.float32), (0, 0), 2.0 * S)
    gy, gx = np.gradient(dome, 1.0 / S)
    # The cut: a table on top, then two rings of facets round the girdle, set along the
    # heart's own outline so the stone is cut to its shape (a brilliant, not a pebble).
    outline = np.array(heart_pts(c, c, s_, n=600))
    seg = np.hypot(*np.diff(np.vstack([outline, outline[:1]]), axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    pts = []
    for ring, (inset, count, phase) in enumerate(((6.0, 28, 0.0), (16.0, 22, 0.5), (29.0, 16, 0.25), (44.0, 10, 0.75))):
        for k in range(count):
            L = (k + phase) / count * cum[-1]
            j = int(np.searchsorted(cum, L) % len(outline))
            px0, py0 = outline[j]
            # Step inward along the sd's gradient until `inset` deep.
            ix, iy = int(px0 * S), int(py0 * S)
            for _ in range(400):
                ix = int(np.clip(ix, 1, R.w - 2)); iy = int(np.clip(iy, 1, R.h - 2))
                if sd[iy, ix] >= inset:
                    break
                gxs = sd[iy, ix + 1] - sd[iy, ix - 1]
                gys = sd[iy + 1, ix] - sd[iy - 1, ix]
                nn = math.hypot(gxs, gys) + 1e-6
                ix += int(round(gxs / nn * 2)); iy += int(round(gys / nn * 2))
            pts.append((ix, iy))
    facet = np.full_like(dome, 1e9)
    for (px_, py_) in pts:
        hp = dome[py_, px_]
        plane = hp + gx[py_, px_] * (X - px_ / S) + gy[py_, px_] * (Y - py_ / S)
        facet = np.minimum(facet, plane)
    # The table: flat across the top.
    facet = np.minimum(facet, dome.max() - 2.5)
    h = np.where(cover > 0, np.minimum(facet, dome + 6.0), 0)
    h = np.clip(h, 0, None)
    R.height = (h * S).astype(np.float32)
    R.shape_height = R.height
    R.alpha = cover
    R.mat[:] = RL.IDS["stone"]
    # Lit from inside: brightest low and in the middle, as blood held up to a lamp.
    t = np.clip(sd / s_, 0, 1)
    n = F.fbm(R.h, R.w, scale=R.w / 6, octaves=4, seed=21) * 0.5 + 0.5
    core = np.exp(-(((X - c) / (s_ * 0.55)) ** 2 + ((Y - c - s_ * 0.12) / (s_ * 0.6)) ** 2))
    glow = (0.05 + 0.8 * core ** 1.5) * (0.6 + 0.6 * n) * smoothstep(0.0, 0.25, t)
    R.emit = (glow[..., None] * (F.hexc("#ff2a1a") * 0.5 + F.hexc("#8a0610") * 0.5)).astype(np.float32)
    img = R.render("heart_stone", samples=samples, wear=0.3, grime=0.0, seed=8)
    return R, img


IRON = ("hand-forged blackened iron, hammer marks, pitted and worn edges, soot in the hollows, a thin twisted gold "
        "wire inlaid round it")
PAINT = {
    "level": ("a round forged iron seal medallion of " + IRON + ", seven square notches round a dark round well, molten "
              "ember glowing deep in the gap at its foot, isolated on a pure black background, seen straight on", 0.30),
    "heart": ("a round forged iron bezel of " + IRON + ", an iron chain coiled round a heart-shaped hollow in it, one "
              "link pried open at the top with ember at the break, isolated on a pure black background, seen straight on", 0.28),
    "stone": ("a heart-shaped cut ruby, blood red, facets catching the light, glowing deep inside, isolated on a pure "
              "black background, seen straight on", 0.26),
}


def finish(name, img, R, calm_r=None, c=None):
    """The render given its hand (paintover.py at the piece's denoise), the middle kept as
    rendered where the code writes over it, then down to the file size."""
    import paintover as PO
    prompt, dn = PAINT[name]
    # Small exact parts (the wire, the chain's links) keep most of their render: a painting
    # melts them. The middle the code writes over keeps all of it.
    small = np.isin(R.mat, [RL.IDS["gold"], RL.IDS["chain"]]).astype(np.float32)
    protect = cv2.dilate(small, np.ones((3, 3), np.uint8), iterations=R.ss // 2) * 0.7
    if calm_r:
        r, _ = R.polar(c, c)
        protect = np.maximum(protect, np.clip((calm_r - r) / 2.0, 0, 1)).astype(np.float32)
    # The painting is cached by the render's content, so a changed model is painted afresh.
    import hashlib
    key = hashlib.sha1(np.ascontiguousarray((img * 255).astype(np.uint8)).tobytes()).hexdigest()[:8]
    p = PO.paint(img, prompt, f"medal_{name}_{key}", denoise=dn, seed=11, keep_light=0.75, protect=protect)
    return R.file_size(p)


def save(img, rel):
    path = os.path.join(UI, rel)
    F.save(F.to_pil(img), path)


BUILD = {
    "level": lambda: ("hud/medal_level.png", level, dict(calm_r=25.0, c=58.0)),
    "heart": lambda: ("hud/medal_heart.png", heart, dict(calm_r=24.0, c=64.0)),
    "stone": lambda: ("icons/glyph_color/heart.png", stone, dict()),
}


def build(name):
    rel, fn, kw = BUILD[name]()
    R, img = fn()
    save(finish(name, img, R, **kw), rel)


if __name__ == "__main__":
    for nm in sys.argv[1:] or list(BUILD):
        build(nm)
        print("built", nm, flush=True)
