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


def rule(W=960, H=24, ss=4, flourish=False):
    """The divider: a bar of iron drawn out thin under the hammer, tapering to points at
    both ends, a gold wire wound round it; at its middle the binders' square coin, its
    hole lit by the sleeping ember (the flourish: one link of the chain pried open
    beside it, the ember at the break)."""
    w, h = W * ss, H * ss
    s = F.Surface(w, h)
    k = ss
    cy = h / 2
    coin = (10 if not flourish else 15) * k
    thick0 = (5.0 if not flourish else 6.5) * k
    for side in (-1, 1):
        x0 = w / 2 + side * coin * 0.4
        x1 = w / 2 + side * (w / 2 - 6 * k)
        pts = [(x0 + (x1 - x0) * t, cy) for t in np.linspace(0, 1, 40)]
        if flourish:
            end = pts[-8]
            curl = O.spiral(end[0], cy - 6 * k, 6 * k, 1.4 * k, math.pi / 2, -side * 1.1, 30)
            pts = pts[:-8] + curl
        O.forged_bar(s, pts, thick0, 0.7 * k, thick0 * 0.6, mat="iron", base=0, facet=0.2)
        L = abs(x1 - x0)
        n = int(L / (4.5 * k))
        for i in range(n):
            t = i / n
            if t > 0.8:
                break
            x = x0 + (x1 - x0) * t
            wd = thick0 * (1 - t) + 0.7 * k * t
            dl = F.sd_segment(s.xx, s.yy, (x - 1.3 * k, cy - wd * 0.55), (x + 1.3 * k, cy + wd * 0.55))
            cov = F.coverage(0.7 * k - dl, 1.0) * np.clip((0.8 - t) / 0.3, 0, 1)
            s.height = s.height + cov * 1.0 * k
            s.paint(cov, "gold")
    _, hole = O.coin(s, w / 2, cy, coin * 2, mat="iron", base=1.0 * k, foil=True, sigil=False)
    lin = s.shade(normal_strength=1.0, ao=0.4, shadow=0.3, light_elev=40) * 1.7
    core = F.blur(hole, 1.2 * k)
    glow = (core ** 2)[..., None] * O.EMBER_HI * 1.2 + F.blur(hole, 4 * k)[..., None] * O.EMBER * 0.5
    lin = lin * (1 - hole[..., None] * 0.7) + glow
    srgb = F.lin_to_srgb(np.clip(lin, 0, 1))
    ga = np.clip(F.lin_to_srgb(np.clip(glow, 0, 1)).max(axis=2), 0, 1) * (1 - s.alpha)
    a = np.maximum(s.alpha, ga * 0.8)
    return F.to_pil(F.downsample(np.dstack([srgb, a]), (W, H)))


def casing(W=128, H=48, margins=(12, 8, 12, 8)):
    """The iron round a bar (GameHud.Casing): a forged strap with the twisted wire, lying
    6 shown px outside the groove and 1 over its edge, its middle open; small end caps
    with a rivet, mostly outside the bar so they hide little of the fill."""
    st = B.small_style(strap=14.0, strap_h=4.0, bevel_out=2.6, bevel_in=2.0, chamfer=3, radius=3, wire=6.5, wire_w=2.2,
                       twist=4.0, centre_tone=None, wear=0.6, seed=43)
    st.twist = 4.0
    st.centre_alpha = 0.0

    def post(s, m, st_, k, tx):
        for cx in (5.5 * k, s.w - 5.5 * k):
            sd = F.sd_box(s.xx, s.yy, cx, s.h / 2, 5 * k, s.h / 2 - 1 * k, 2 * k)
            cov = F.coverage(sd, 1.0)
            O.put(s, cov, F.bevel(sd, 1.5 * k, 2.5 * k) + st_.strap_h * k, "iron")
            O.rivet(s, cx, s.h / 2, 2.0 * k, base=st_.strap_h * k + 2.5 * k)
        return None
    return FR.frame(W, H, margins, st, ss=4, post=post)


RARITY_COL =["#c8c0b0", "#6fd46a", "#5aa8ff", "#c070ff", "#ffb040", "#ff6a3a"]


def slot(rarity=None, W=160, H=160, ss=4, seed=41):
    """A recessed well in blackened iron: a hammered rim lit from the upper left, the well
    sunk below it. With a rarity, its inner edge carries the rarity's colour and its
    corners the rarity's mark (shape as well as hue): thorns for the Verge, rime for the
    Ford, cut stones for the binders, flame points for the Order, cracks leaking ember for
    the Morrow's relics."""
    st = B.small_style(strap=9.0, strap_h=3.4, bevel_out=2.4, bevel_in=3.2, chamfer=4, radius=2, wire=None,
                       centre_tone="#0d0b10", wear=0.55, seed=seed, centre_drop=3.4)
    st.facet_tilt = 0.035
    st.facet_cell = 7
    col = F.hexc(RARITY_COL[rarity]) if rarity is not None else None

    def post(s, m, st_, k0, tx):
        light = np.zeros((s.h, s.w, 3), np.float32)
        k = k0
        inner = 9.0 * k
        km = k * 1.6  # the corner marks, larger than the rim so they read as shapes
        d = F.sd_box(s.xx, s.yy, s.w / 2, s.h / 2, s.w / 2 - 0.5 * k, s.h / 2 - 0.5 * k, 2 * k)
        cut = (s.w / 2 + s.h / 2 - 1 * k - 4 * k - np.abs(s.xx - s.w / 2) - np.abs(s.yy - s.h / 2)) / math.sqrt(2)
        d = np.minimum(d, cut)
        if rarity is None:
            # A rivet in each corner of the empty well's rim.
            for (cx, cy) in ((4.5 * k, 4.5 * k), (s.w - 4.5 * k, 4.5 * k), (4.5 * k, s.h - 4.5 * k), (s.w - 4.5 * k, s.h - 4.5 * k)):
                O.rivet(s, cx, cy, 1.9 * k, base=st_.strap_h * k - 0.3 * k)
            return light
        # The rarity's line: a fine inlay at the rim's inner edge, glowing a little.
        line = np.exp(-((d - inner + 0.6 * k) / (0.9 * k)) ** 2)
        s.paint(line * 1.0, F.Mat(tuple(col), 0.6 if rarity < 4 else 1.0, 0.35))
        light += line[..., None] * col * (0.18 + 0.05 * rarity)
        corners = ((0, 0, 1, 1), (s.w, 0, -1, 1), (0, s.h, 1, -1), (s.w, s.h, -1, -1))
        for (cx, cy, sx, sy) in corners:
            if rarity == 0:
                O.rivet(s, cx + sx * 4.5 * k, cy + sy * 4.5 * k, 1.9 * k, base=st_.strap_h * k - 0.3 * k)
            elif rarity == 1:
                # Thorns: three hooked points growing off the corner along the rim.
                for (ax, ay, L) in ((1, 0.25, 9), (0.25, 1, 9), (0.8, 0.8, 7)):
                    bx, by = cx + sx * 3 * k, cy + sy * 3 * k
                    tip = (bx + sx * ax * L * km, by + sy * ay * L * km)
                    nrm = (-(ay) * sy, ax * sx)
                    base1 = (bx + nrm[0] * 1.6 * km, by + nrm[1] * 1.6 * k)
                    base2 = (bx - nrm[0] * 1.6 * km, by - nrm[1] * 1.6 * km)
                    sd = F.sd_poly(s.xx, s.yy, [tip, base1, base2])
                    cv = F.coverage(sd, 1.0)
                    O.put(s, cv, F.bevel(sd, 0.8 * k, 1.6 * k) + st_.strap_h * k, F.Mat(tuple(F.hexc("#3a5a22")), 0.0, 0.5))
            elif rarity == 2:
                # Rime: a cluster of ice needles at the corner.
                for ang, L in ((0.15, 10), (0.55, 13), (0.95, 9), (1.35, 11)):
                    a0 = ang * (math.pi / 2) / 1.5
                    ux, uy = math.cos(a0) * sx, math.sin(a0) * sy
                    bx, by = cx + sx * 2.5 * k, cy + sy * 2.5 * k
                    tip = (bx + ux * L * km, by + uy * L * km)
                    sd = F.sd_poly(s.xx, s.yy, [tip, (bx - uy * 1.3 * km, by + ux * 1.3 * km), (bx + uy * 1.3 * km, by - ux * 1.3 * km)])
                    cv = F.coverage(sd, 1.0)
                    O.put(s, cv, F.bevel(sd, 0.6 * k, 1.4 * k) + st_.strap_h * k, F.Mat(tuple(F.hexc("#bfe4ff")), 0.0, 0.15))
                    light += cv[..., None] * col * 0.25
            elif rarity == 3:
                # A cut stone, square, set on its point at the corner.
                gx, gy = cx + sx * 7 * k, cy + sy * 7 * k
                dx, dy = s.xx - gx, s.yy - gy
                sd = 4.2 * km - (np.abs(dx) + np.abs(dy)) / math.sqrt(2)
                cv = F.coverage(sd, 1.0)
                facet = np.clip(sd / (4.2 * km), 0, 1)
                O.put(s, cv, facet * 2.2 * k + st_.strap_h * k, F.Mat(tuple(col), 0.0, 0.08))
                light += (cv * (0.3 + 0.5 * facet))[..., None] * col * 0.45
            elif rarity == 4:
                # Flame points: three tongues of wrought gold licking along the rim.
                for (ax, ay, L) in ((1, 0.15, 12), (0.15, 1, 12), (0.75, 0.75, 9)):
                    bx, by = cx + sx * 2.5 * k, cy + sy * 2.5 * k
                    pts = []
                    for t in np.linspace(0, 1, 9):
                        w = (1 - t) * 2.0 * km
                        wob = math.sin(t * math.pi * 1.5) * 1.4 * km
                        px = bx + sx * ax * L * km * t + (-ay * sy) * wob
                        py = by + sy * ay * L * km * t + (ax * sx) * wob
                        pts.append((px, py, w))
                    left = [(x + (-ay * sy) * w, y + (ax * sx) * w) for x, y, w in pts]
                    right = [(x - (-ay * sy) * w, y - (ax * sx) * w) for x, y, w in pts][::-1]
                    sd = F.sd_poly(s.xx, s.yy, left + right)
                    cv = F.coverage(sd, 1.0)
                    O.put(s, cv, F.bevel(sd, 0.8 * k, 1.6 * k) + st_.strap_h * k, "gold")
                    light += cv[..., None] * F.hexc("#ffb040") * 0.15
            elif rarity == 5:
                # The rim cracked, ember leaking from the cracks.
                pass
        if rarity == 5:
            band = np.clip((inner - d) / (2 * k), 0, 1) * np.clip(d / (1.5 * k), 0, 1)
            veins = O.cracks(s, band, seed=seed + 7, count=10, length=22 * k, step=1.0 * k, width=0.8 * k, depth=0.8 * k)
            light += O.vein_light(veins, awake=1.0, spread=1.5 * k) * 0.8
        return light

    return FR.frame(W, H, (10, 10, 10, 10), st, ss=ss, post=post)


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
