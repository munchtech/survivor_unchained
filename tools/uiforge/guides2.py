"""More guides: the small frames (slots, chips, toasts, pills, tabs, buttons,
tooltips), the minimap's round rim, sheets of paper. Each fixes geometry for
the Krea to paint over; see guides.py.
"""
from __future__ import annotations

import math

import numpy as np

import forge as F
import frames as FR
import ornament as O


def generic(W, H, scale=4, strap=6, wire=True, corners="coin", corner_size=10, radius=3, out=0, recess=False,
            centre_tone="#16131a", strap_mat="iron", centre_mat="iron_dark", chamfer=0, seed=9, inset_coins=True):
    """A small frame at `scale` times its shown size (W, H shown px): a strap round a calm
    middle, coins or rivets at the corners. Sizes in shown px."""
    k = scale
    st = FR.Style(out=out * scale / 2, strap=strap * k, strap_h=2.5 * k, bevel_out=1.6 * k, bevel_in=1.2 * k,
                  wire=(strap * k * 0.55) if wire else None, wire_w=1.1 * k, twist=2.2 * k, facet_cell=5 * k,
                  facet_tilt=0.04, centre_facets=0.0, rivets=0, seed=seed, radius=radius * k, chamfer=chamfer * k,
                  centre_tone=centre_tone, strap_mat=strap_mat, centre_mat=centre_mat, pressed=recess)

    def post(s, m, st_, kk, tx):
        top = st_.strap_h
        inset = out * k
        light = np.zeros((s.h, s.w, 3), np.float32)
        if corners == "coin":
            holes = np.zeros((s.h, s.w), np.float32)
            off = corner_size * k * 0.42 if inset_coins else 0
            for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                cx = (inset + off) if sx > 0 else (s.w - inset - off)
                cy = (inset + off) if sy > 0 else (s.h - inset - off)
                _, hole = O.coin(s, cx, cy, corner_size * k, mat="iron", base=top + 0.5 * k, foil=True, sigil=False)
                holes = np.maximum(holes, hole)
            light += holes[..., None] * (O.EMBER_DEEP * 0.9 + O.EMBER * 0.25)
        elif corners == "rivet":
            a = strap * k * 0.5 + inset
            for (cx, cy) in ((a, a), (s.w - a, a), (a, s.h - a), (s.w - a, s.h - a)):
                O.rivet(s, cx, cy, corner_size * k * 0.5, base=top - 0.3 * k)
        return light

    return FR.frame(W * scale, H * scale, ((strap + out + 2) * scale / 2,) * 4, st, ss=1, post=post)


def ring(size=240, band=20, scale=4, coins=4, north=True, seed=6):
    """The minimap's rim: a forged band round an empty middle, coins at the four quarters,
    a forged arrowhead standing out of the band at the north. size, band in shown px."""
    S = size * scale
    s = F.Surface(S, S)
    c = S / 2
    R = S / 2 - 8 * scale
    r_in = R - band * scale
    rr = np.hypot(s.xx - c, s.yy - c)
    ang = np.arctan2(s.yy - c, s.xx - c)
    sd = np.minimum(R - rr, rr - r_in)
    cov = F.coverage(sd, 1.0)
    h = F.bevel(sd, 3 * scale, 7 * scale) + F.facets(S, S, cell=7 * scale, tilt=0.05, seed=seed, soften=2) * cov
    O.put(s, cov, h, "iron")
    for rad in (R - band * scale * 0.28, R - band * scale * 0.74):
        dist = np.abs(rr - rad)
        tw = 0.5 + 0.5 * np.cos(ang * rad / (2.5 * scale) + (rr - rad) / scale)
        wire = F.coverage(1.2 * scale - dist, 1.0)
        s.height = s.height + wire * (2 * scale + tw * 1.2 * scale)
        s.paint(wire, "gold")
    light = np.zeros((S, S, 3), np.float32)
    mid = (R + r_in) / 2
    for i in range(coins):
        a = -math.pi / 2 + i * 2 * math.pi / coins
        cx, cy = c + math.cos(a) * mid, c + math.sin(a) * mid
        if north and i == 0:
            tip = (c, c - R - 7 * scale)
            pts = [tip, (c + 10 * scale, cy - 2 * scale), (c, cy - 6 * scale), (c - 10 * scale, cy - 2 * scale)]
            sdp = F.sd_poly(s.xx, s.yy, pts)
            cp = F.coverage(sdp, 1.0)
            O.put(s, cp, F.bevel(sdp, 3 * scale, 6 * scale) + 8 * scale, "iron")
        _, hole = O.coin(s, cx, cy, 17 * scale, mat="iron", base=9 * scale, foil=True, sigil=False)
        light += hole[..., None] * (O.EMBER_DEEP * 0.9 + O.EMBER * 0.25)
    lin = s.shade(normal_strength=1.0, ao=0.7, shadow=0.5, light_elev=35) + light
    return s.finish(lin)


def paper(W, H, scale=2, deckle=10, corners=True, seed=4, tone="#e4d6b6"):
    """A sheet of the Waystation's ledger paper: cream, a deckled darker rim, small iron
    corner caps riveted on (for the Krea to paint over)."""
    S_w, S_h = W * scale, H * scale
    s = F.Surface(S_w, S_h)
    n = F.fbm(S_h, S_w, scale=6 * scale, octaves=4, seed=seed)
    sd = F.sd_box(s.xx, s.yy, S_w / 2, S_h / 2, S_w / 2 - 3 * scale, S_h / 2 - 3 * scale, 2 * scale) + n * deckle * 0.25 * scale
    cov = F.coverage(sd, 1.0)
    rim = np.clip(1 - sd / (deckle * scale), 0, 1)
    alb = F.hexc(tone) * (1 - rim[..., None] * 0.45 * np.array([0.9, 1.0, 1.2])) * (1 + n[..., None] * 0.04)
    s.albedo = alb.astype(np.float32)
    s.metal[:] = 0
    s.rough[:] = 0.9
    s.height = (F.blur(n, 2 * scale) * 0.6 * scale).astype(np.float32)
    s.alpha = cov
    light = np.zeros((S_h, S_w, 3), np.float32)
    if corners:
        L = 18 * scale
        for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            cx = 4 * scale if sx > 0 else S_w - 4 * scale
            cy = 4 * scale if sy > 0 else S_h - 4 * scale
            tri = F.sd_poly(s.xx, s.yy, [(cx, cy), (cx + sx * L, cy), (cx, cy + sy * L)])
            ct = F.coverage(tri, 1.0)
            O.put(s, ct, F.bevel(tri, 1.5 * scale, 2.5 * scale) + 1.5 * scale, "iron")
            O.rivet(s, cx + sx * L * 0.3, cy + sy * L * 0.3, 1.8 * scale, base=4 * scale)
    lin = s.shade(normal_strength=1.0, ao=0.5, shadow=0.3, light_elev=40) + light
    return s.finish(lin)
