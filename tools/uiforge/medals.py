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


def chain_round(R, c, rc, n, link_len, link_w, wire, base, open_at=0, gap=2.2):
    """A chain coiled round a circle (file px): `n` links (even), alternately lying flat and
    standing on edge, the flat link at `open_at` pried open on its outer side. Returns
    (height in file px, mask, the break's glow) at render res."""
    X, Y = R.xx / R.ss, R.yy / R.ss
    link_h = np.zeros(X.shape, np.float32)
    link_m = np.zeros(X.shape, np.float32)
    brk = np.zeros(X.shape, np.float32)
    for i in range(n):
        a = 2 * math.pi * i / n
        lx, ly = c + math.sin(a) * rc, c - math.cos(a) * rc
        ca, sa = math.cos(a), math.sin(a)
        u = (X - lx) * ca + (Y - ly) * sa
        v = -(X - lx) * sa + (Y - ly) * ca
        if i % 2 == 0:
            d = stadium_sd(X, Y, lx, ly, link_len, link_w, angle=a)
            hh = np.sqrt(np.clip(1 - (d / wire) ** 2, 0, 1)) * wire + base
            if open_at is not None and i == open_at:
                # Pried open: its outer side cut through, the ends sprung apart.
                cut = (np.abs(u) < gap) & (v < 0)
                hh = np.where(cut, 0, hh)
                brk = np.exp(-((u / (gap * 0.65)) ** 2 + ((v + link_w / 2) / (wire * 0.7)) ** 2)).astype(np.float32)
        else:
            # On edge: seen from above, a bar the length of the link's inside, standing taller.
            d = np.hypot(np.clip(np.abs(u) - (link_len - link_w) * 0.62, 0, None), v)
            hh = np.sqrt(np.clip(1 - (d / wire) ** 2, 0, 1)) * wire + base + link_w * 0.25
        m = (hh > base + 0.01) * np.clip((wire - d) * R.ss + 0.5, 0, 1)
        link_h = np.maximum(link_h, hh * m)
        link_m = np.maximum(link_m, m)
    return link_h, link_m, brk


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
        link_h, link_m, brk = chain_round(R, c, rc, CHAIN, 16.5, 8.6, 1.75, 2.4)
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


def ring(ss=2, samples=128):
    """The medallion's ring (medallion/ring.png, 440 square, shown 44-220 round every
    medallion): the Legion's seal again, open in the middle for the code's core. Its band from
    80% of the half size out, drawn iron with chamfered edges, forge-welded at the foot; the
    binders' wire sunk in a channel at 88% (where the code runs the progress arc, so a filling
    arc lies in the wire's bed); seven notches in its inner edge, through which the core's
    colour shows. Bold enough to read at 44 px: the bright chamfers and the wire carry it."""
    W = 440
    c = W / 2
    S = ss
    R = RL.Relief(W, W, ss)
    r, th = R.polar(c, c)
    X, Y = R.xx / S, R.yy / S
    r_out = 218.5 + RL.ragged(th, 1.3, seed=23, lobes=(3, 5, 8, 13))
    r_in = 0.79 * c
    top = 16.0
    cover = np.clip((r_out - r) * S + 0.5, 0, 1) * np.clip((r - 0.78 * c) * S + 0.5, 0, 1)
    h = band_profile(r, r_out, r_in, top, outer_ch=7.0, inner_ch=5.0, shoulder=3.0)
    crown = np.sin(np.clip((r - r_in) / (r_out - r_in), 0, 1) * math.pi) * 3.0
    h = h + crown * (h > 0)
    on_band = smoothstep(0.7, 0.95, h / top)
    # The weld at the foot.
    across = np.angle(np.exp(1j * (th - math.pi - 0.05))) * r
    h = h + np.exp(-(across / 9.0) ** 2) * 1.6 * on_band
    seam = np.exp(-(across / 1.3) ** 2) * (r > r_in + 4) * (r < r_out - 4)
    h = h - seam * 3.5
    # The channel at 88% (of the code's radius, size/2 - 3 shown) and the wire in it.
    r_wire = 0.88 * (c - 6)
    chw = 8.5
    chan = np.clip((chw - np.abs(r - r_wire)) * S / 2, 0, 1)
    chan_floor = top - 6.0
    h = np.where(chan > 0, h * (1 - chan) + chan_floor * chan, h)
    wh, wm = RL.rope(R, c, c, r_wire, 9.0, 8.0, 5.5)
    h = np.maximum(h, np.where(wm > 0.5, chan_floor + wh / S, -99))
    shape = h.copy()
    facet = F.facets(R.h, R.w, cell=30.0 * S, tilt=0.02, seed=24, soften=3.0 * S) / S
    dents = RL.hammered(R, cell=12.0, depth=0.35, seed=25) / S
    h = h + (facet * 2.0 + dents) * on_band * (1 - chan)
    # The binders' coins nailed on at the four diagonals, ember asleep in their holes.
    coins = np.zeros_like(r)
    holes = np.zeros_like(r)
    glow_c = np.zeros_like(r)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x0, y0 = c + math.sin(a) * r_wire, c - math.cos(a) * r_wire
        ch_, cm, hm = RL.coin(R, x0, y0, 34.0, top - 1.0, hole=0.36, rot=45.0)
        dh = np.hypot(X - x0, Y - y0) / (34.0 * 0.36 / 2)
        glow_c = np.maximum(glow_c, hm * np.exp(-dh ** 2 * 1.6))
        h = np.where(cm > 0.5, np.maximum(h, ch_), h)
        shape = np.where(cm > 0.5, np.maximum(shape, ch_), shape)
        coins = np.maximum(coins, cm)
        holes = np.maximum(holes, hm)
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = (shape * S * cover).astype(np.float32)
    R.alpha = cover
    R.mat[:] = RL.IDS["iron"]
    R.mat[(wm > 0.5) & (coins < 0.5)] = RL.IDS["gold"]
    R.mat[holes > 0.5] = RL.IDS["ember"]
    R.tint = np.where((chan > 0.5)[..., None] & (wm < 0.5)[..., None] & (coins < 0.5)[..., None], 0.45, 1.0).astype(np.float32)
    n = F.fbm(R.h, R.w, scale=R.w / 20, octaves=3, seed=27) * 0.5 + 0.5
    R.emit = (glow_c * (0.5 + 0.6 * n))[..., None] * (F.hexc("#ff6a1a") * 0.9 + F.hexc("#8a1c04") * 0.5)
    R.emit = R.emit.astype(np.float32)
    img = R.render("medal_ring", samples=samples, wear=1.3, grime=0.9, seed=26)
    return R, img


def scroll_arm(R, c, r_arm, a0, a1, curl, w0, w1, sgn):
    """A lamp-iron's arm laid along a circle (file px) from angle a0 to a1 (0 at the top,
    clockwise; sgn the side), then curling outward in a scroll of radius `curl`. Returns its
    distance field's (height, mask) as a drawn bar, thick at its root, thin at its end."""
    X, Y = R.xx / R.ss, R.yy / R.ss
    pts, widths = [], []
    n1 = 36
    for t in np.linspace(0, 1, n1):
        a = sgn * (a0 + (a1 - a0) * t)
        pts.append((c + math.sin(a) * r_arm, c - math.cos(a) * r_arm))
        widths.append(w0 + (w1 - w0) * 0.6 * t)
    a_end = sgn * a1
    # The curl's centre: outward of the arm's end, so it turns away from the vessel.
    ccx, ccy = c + math.sin(a_end) * (r_arm + curl), c - math.cos(a_end) * (r_arm + curl)
    ex, ey = pts[-1]
    b0 = math.atan2(ey - ccy, ex - ccx)
    for t in np.linspace(0, 1, 30)[1:]:
        b = b0 + sgn * 1.35 * 2 * math.pi * t
        rr = curl * (1 - 0.72 * t)
        pts.append((ccx + math.cos(b) * rr, ccy + math.sin(b) * rr))
        widths.append(w0 + (w1 - w0) * (0.6 + 0.4 * t))
    pts = np.array(pts, np.float32)
    widths = np.array(widths, np.float32)
    # Distance and the nearest point's width, by brute force over the segments.
    best = np.full(X.shape, 1e9, np.float32)
    wbest = np.full(X.shape, w1, np.float32)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        ex_, ey_ = bx - ax, by - ay
        tt = np.clip(((X - ax) * ex_ + (Y - ay) * ey_) / (ex_ * ex_ + ey_ * ey_ + 1e-9), 0, 1)
        d = np.hypot(X - ax - ex_ * tt, Y - ay - ey_ * tt)
        w = widths[i] + (widths[i + 1] - widths[i]) * tt
        closer = d < best
        best = np.where(closer, d, best)
        wbest = np.where(closer, w, wbest)
    half = wbest / 2
    m = np.clip((half - best) * R.ss + 0.5, 0, 1)
    # Drawn strap iron: flat on top, its edges rounded.
    h = np.minimum(1.0, 1.7 * np.sqrt(np.clip(1 - (best / np.maximum(half, 0.1)) ** 2, 0, 1))) * half * 0.9
    return h * (m > 0), m


def globe_rim(ss=4, samples=160):
    """The health globe's rim (hud/globe_rim.png, 288 square, 144 shown round the 66 px
    liquid): the heart's setting grown into a vessel. A forged band the glass is set in, the
    binders' chain coiled round it in a channel (in the story each link of the chain is
    anchored in a heart), and at its head the link pried open with the ember at the break,
    held in a lamp-iron collar whose scrolled arms run down the band either side. Its
    middle open."""
    W = 288
    c = W / 2
    S = ss
    R = RL.Relief(W, W, ss)
    r, th = R.polar(c, c)
    X, Y = R.xx / S, R.yy / S
    r_out = 141.0 + RL.ragged(th, 0.8, seed=31, lobes=(3, 5, 8, 13))
    r_in = 0.835 * c          # reaches in over the liquid's edge
    top = 9.0
    cover = np.clip((r_out - r) * S + 0.5, 0, 1) * np.clip((r - r_in + 1.5) * S + 0.5, 0, 1)
    h = band_profile(r, r_out, r_in, top, outer_ch=4.0, inner_ch=3.0, shoulder=1.6)
    span = np.clip((r - r_in) / (r_out - r_in), 0, 1)
    h = h + np.sin(span * math.pi) * 1.6 * (h > 0)
    on_band = smoothstep(0.7, 0.95, h / top)
    # The channel the chain lies in.
    rc = (r_in + 141.0) / 2 + 0.5
    chw = 8.2
    chan = np.clip((chw - np.abs(r - rc)) * S / 2, 0, 1)
    floor = 2.5
    h = h * (1 - chan) + floor * chan
    shape = h.copy()
    link_h, link_m, brk = chain_round(R, c, rc, 40, 21.0, 11.5, 2.5, floor + 0.6, open_at=0, gap=3.2)
    # The lamp-iron collar at the head: a forged block across the band, the open link set
    # proud on it, nailed either side.
    al = c - Y              # up from the centre
    ac = X - c
    cap_sd = np.minimum(14.0 - np.abs(ac), np.minimum(al - (r_in - 1.0), 144.5 - al))
    cap = np.clip(cap_sd * S + 0.5, 0, 1)
    cap_h = top + 2.0 + np.sqrt(np.clip(cap_sd / 3.0, 0, 1)) * 1.8
    h = np.where(cap > 0.5, np.maximum(h, cap_h), h)
    shape = np.where(cap > 0.5, np.maximum(shape, cap_h), shape)
    # The chain: on the collar the open link rides on top of it.
    on_cap = (cap > 0.5) & (np.abs(ac) < 15.0)
    link_h = np.where(on_cap & (link_m > 0.5), link_h - (floor + 0.6) + cap_h.max() - 0.6, link_h)
    h = np.where(link_m > 0.5, np.maximum(h, link_h), h)
    shape = np.where(link_m > 0.5, np.maximum(shape, link_h), shape)
    # The arms: from the collar along the band's outer edge, curling outward at the end.
    arms_m = np.zeros_like(r)
    for sgn in (-1, 1):
        ah, am = scroll_arm(R, c, rc, math.radians(5), math.radians(17), 5.0, 7.0, 3.0, sgn)
        ah = ah + top + 0.8
        h = np.where(am > 0.5, np.maximum(h, ah), h)
        shape = np.where(am > 0.5, np.maximum(shape, ah), shape)
        arms_m = np.maximum(arms_m, am)
    for sx in (-1, 1):
        x0, y0 = c + sx * 9.5, c - (r_in + 5.0)
        d = np.hypot(X - x0, Y - y0)
        rv = np.sqrt(np.clip(1 - (d / 2.5) ** 2, 0, 1)) * 1.6 + cap_h.max()
        h = np.where(d < 2.5, np.maximum(h, rv), h)
        shape = np.where(d < 2.5, np.maximum(shape, rv), shape)
    facet = F.facets(R.h, R.w, cell=10.0 * S, tilt=0.022, seed=32, soften=1.5 * S) / S
    dents = RL.hammered(R, cell=5.0, depth=0.22, seed=33) / S
    plain = (link_m < 0.5) & (arms_m < 0.5)
    h = h + (facet + dents) * on_band * (1 - chan) * plain
    cover = np.maximum(cover, np.maximum(cap, arms_m))
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = (shape * S * cover).astype(np.float32)
    R.alpha = cover
    R.mat[:] = RL.IDS["iron"]
    R.mat[link_m > 0.5] = RL.IDS["chain"]
    R.tint = np.where(((chan > 0.5) & (link_m < 0.5) & (cap < 0.5))[..., None], 0.4, 1.0).astype(np.float32)
    n = F.fbm(R.h, R.w, scale=R.w / 12, octaves=3, seed=34) * 0.5 + 0.5
    emit = (brk * (0.8 + 0.5 * n))[..., None] * (F.hexc("#ff8a2a") * 2.2 + F.hexc("#c02a06") * 0.8)
    heat = cv2.GaussianBlur(brk, (0, 0), 3.0 * S) * 0.5
    R.emit = (emit + heat[..., None] * F.hexc("#c02a06") * 0.5).astype(np.float32)
    img = R.render("globe_rim", samples=samples, wear=1.3, grime=0.9, seed=35)
    return R, img


def globe_glass(ss=4, samples=0):
    """The globe's glass (hud/globe_glass.png, 288 square): only the light on it, painted
    as a painter paints glass: the room's window caught upper left (four leaded panes, as
    the Waystation's), a softer bloom round it, a thin rim of the cool light along the lower
    right edge, a faint brightening all round the edge where glass turns away. The rest
    clear, so the liquid and the number show."""
    W = 288
    c = W / 2
    S = ss
    R = RL.Relief(W, W, ss)
    X, Y = R.xx / S, R.yy / S
    rad = 0.917 * c
    dx, dy = (X - c) / rad, (Y - c) / rad
    rr = np.hypot(dx, dy)
    inside = np.clip((1 - rr) * rad * S + 0.5, 0, 1)
    # The window: a small curved quad upper left, its panes split by lead, bent to the dome.
    # Coordinates on the dome: map to a sphere's tangent near the highlight.
    hx, hy, ang = -0.40, -0.44, math.radians(-40)
    u = (dx - hx) * math.cos(ang) + (dy - hy) * math.sin(ang)
    v = -(dx - hx) * math.sin(ang) + (dy - hy) * math.cos(ang)
    # Curved: the window's edges bow with the glass.
    v = v + 1.4 * u * u
    win_w, win_h = 0.13, 0.085
    soft = 0.03
    win = np.clip((win_w - np.abs(u)) / soft, 0, 1) * np.clip((win_h - np.abs(v)) / soft, 0, 1)
    lead = np.clip((0.012 - np.abs(u)) / 0.012, 0, 1) + np.clip((0.010 - np.abs(v)) / 0.010, 0, 1)
    win = win * (1 - np.clip(lead, 0, 1) * 0.6)
    # Brighter toward its upper left corner (the light's direction).
    win = win * (0.75 + 0.25 * np.clip(-(u + v) / 0.2 + 0.5, 0, 1))
    bloom = np.exp(-((u / 0.30) ** 2 + (v / 0.20) ** 2)) * 0.14
    # The rim: a thin crescent of cool light inside the lower right edge.
    a = np.arctan2(dx, -dy)  # 0 at the top, clockwise
    side = np.clip(np.cos(a - math.radians(135)), 0, 1) ** 2.5
    rim = np.exp(-((rr - 0.865) / 0.022) ** 2) * side * 0.5
    a_hl = np.clip(win * 0.5 + bloom + rim, 0, 0.9) * inside
    # Where the glass turns away it darkens what is behind it: a little shade at the edge.
    shade = np.clip((rr - 0.55) / 0.36, 0, 1) ** 2.2 * 0.38 * inside
    warm = F.hexc("#fff0dc", lin=False)
    cool = F.hexc("#c8d4ff", lin=False)
    mixw = np.clip((win * 0.5 + bloom) / np.maximum(a_hl / np.maximum(inside, 1e-3), 1e-4), 0, 1)
    col = warm[None, None, :] * mixw[..., None] + cool[None, None, :] * (1 - mixw[..., None])
    # Light over shade: the shade is black at its own coverage, the light laid on it.
    a = a_hl + shade * (1 - a_hl)
    col = col * (a_hl / np.maximum(a, 1e-4))[..., None]
    img = np.dstack([col, a]).astype(np.float32)
    return R, img


IRON = ("hand-forged blackened iron, hammer marks, pitted and worn edges, soot in the hollows, a thin twisted gold "
        "wire inlaid round it")
PAINT = {
    "level": ("a round forged iron seal medallion of " + IRON + ", seven square notches round a dark round well, molten "
              "ember glowing deep in the gap at its foot, isolated on a pure black background, seen straight on", 0.30),
    "heart": ("a round forged iron bezel of " + IRON + ", an iron chain coiled round a heart-shaped hollow in it, one "
              "link pried open at the top with ember at the break, isolated on a pure black background, seen straight on", 0.28),
    "ring": ("a round forged iron ring of " + IRON + " in a channel, seven small square notches in its inner edge, "
             "the middle empty and black, isolated on a pure black background, seen straight on", 0.26),
    "globe_rim": ("a round forged iron rim of " + IRON.replace(", a thin twisted gold wire inlaid round it", "") +
                  ", an iron chain coiled round it in a channel, at its top a forged iron collar holding a chain link "
                  "pried open with molten ember at the break, the middle empty and black, isolated on a pure black "
                  "background, seen straight on", 0.26),
    "stone": ("a heart-shaped cut ruby, blood red, facets catching the light, glowing deep inside, isolated on a pure "
              "black background, seen straight on", 0.26),
}


def finish(name, img, R, calm_r=None, c=None):
    """The render given its hand (paintover.py at the piece's denoise), the middle kept as
    rendered where the code writes over it, then down to the file size."""
    if name not in PAINT:
        return R.file_size(img)
    import paintover as PO
    prompt, dn = PAINT[name]
    # Small exact parts (the wire, the chain's links) keep most of their render: a painting
    # melts them. The middle the code writes over keeps all of it.
    small = np.isin(R.mat, [RL.IDS["gold"], RL.IDS["chain"]]).astype(np.float32)
    protect = cv2.dilate(small, np.ones((3, 3), np.uint8), iterations=R.ss // 2) * 0.7
    # And the light: the painting would put out an ember it does not understand.
    lit = cv2.GaussianBlur((R.emit.max(axis=2) > 0.04).astype(np.float32), (0, 0), 1.5 * R.ss)
    protect = np.maximum(protect, np.clip(lit * 1.5, 0, 1))
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
    "ring": lambda: ("medallion/ring.png", ring, dict()),
    "globe_rim": lambda: ("hud/globe_rim.png", globe_rim, dict()),
    "globe_glass": lambda: ("hud/globe_glass.png", globe_glass, dict()),
}


def build(name):
    rel, fn, kw = BUILD[name]()
    R, img = fn()
    save(finish(name, img, R, **kw), rel)


if __name__ == "__main__":
    for nm in sys.argv[1:] or list(BUILD):
        build(nm)
        print("built", nm, flush=True)
