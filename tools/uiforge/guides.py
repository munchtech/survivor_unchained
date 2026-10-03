"""Guides: the exact geometry of a piece, forged and lit, for the local Krea to
paint over (img2img). The guide fixes what the game needs (where the border
lies, what overhangs, where the crest sits, what stays calm for text); the
painting gives it the hand. See pipeline.py for the whole path.
"""
from __future__ import annotations

import math

import numpy as np

import forge as F
import frames as FR
import ornament as O


def bracket(s, cx, cy, sx, sy, k, coin_size, arm, scroll_r, strap_mid, top, foil=True, ember=0.6):
    """A corner bracket: two arms along the edges from a coin at the corner, each ending
    in a scroll curling outward. (sx, sy) point into the frame. Returns the coin hole mask."""
    for axis in (0, 1):
        if axis == 0:
            a0 = (cx, cy + sy * strap_mid)
            a1 = (cx + sx * arm, cy + sy * strap_mid)
            # Scroll: curl outward (away from the inside: -sy).
            ccx, ccy = a1[0] + sx * scroll_r * 0.2, a1[1] - sy * scroll_r
            start_ang = math.atan2(a1[1] - ccy, a1[0] - ccx)
            turn = 1.15 * (1 if sx * sy > 0 else -1) * -1
        else:
            a0 = (cx + sx * strap_mid, cy)
            a1 = (cx + sx * strap_mid, cy + sy * arm)
            ccx, ccy = a1[0] - sx * scroll_r, a1[1] + sy * scroll_r * 0.2
            start_ang = math.atan2(a1[1] - ccy, a1[0] - ccx)
            turn = 1.15 * (1 if sx * sy > 0 else -1)
        curl = O.spiral(ccx, ccy, scroll_r, scroll_r * 0.25, start_ang, turn, 40)
        O.forged_bar(s, [a0, a1] + curl[1:], 9 * k, 3 * k, 4.5 * k, mat="iron", base=top)
    cov, hole = O.coin(s, cx, cy, coin_size, mat="iron", base=top + 1.0 * k, foil=foil, sigil=False)
    return hole


def broken_chain(s, cx, cy, k, link_len, link_w, thick, top, count=3, ember=1.0):
    """A short chain along the top edge, its middle link pried open: returns the ember light (linear)."""
    pts = []
    step = link_len * 0.78
    breaks = []
    for i in range(count):
        off = (i - (count - 1) / 2) * step
        horizontal = i % 2 == 0
        if horizontal:
            gap = 0.55 if i == count // 2 else 0.0
            _, br = O.link(s, cx + off, cy, link_len, link_w, thick, angle=0.0, gap=gap, gap_at=math.pi / 2, base=top)
            breaks += br
        else:
            # The links between are seen edge-on: a short bar.
            O.forged_bar(s, [(cx + off - link_len * 0.42, cy), (cx + off + link_len * 0.42, cy)], thick * 1.1, thick * 1.1, thick * 0.6, base=top + 0.5 * k)
    light = np.zeros((s.h, s.w, 3), np.float32)
    for (bx, by) in breaks:
        d = np.hypot(s.xx - bx, s.yy - by)
        core = np.exp(-(d / (thick * 0.55)) ** 2)
        halo = np.exp(-d / (thick * 1.8))
        light += core[..., None] * O.EMBER_HI * 2.5 * ember + halo[..., None] * O.EMBER * 0.9 * ember
    return light


def card_guide(out=14, body=(320, 452), strap=14, seed=3, crest=True, wire=True, top_coin=58, top_arm=88, top_scroll=15,
               low_coin=34, low_arm=40, low_scroll=8):
    """The draft card's frame: a forged strap round the card; at the top two big lamp-iron
    brackets (the card hangs from them, as the Waystation's signs hang) with the broken
    chain between them over the top edge; at the foot two small coins nailed, clear of
    the rarity and the key written there. Sizes in shown px (file = twice)."""
    W = (body[0] + 2 * out) * 2
    H = (body[1] + 2 * out) * 2
    st = FR.Style(out=out, strap=strap * 2, strap_h=7, wire=(strap * 2 * 0.55) if wire else None, wire_w=4.0, twist=6.0,
                  facet_cell=16, facet_tilt=0.06, centre_facets=0.0, rivets=0, seed=seed, radius=6, centre_tone="#141118")
    ss = 1

    def post(s, m, st_, k, tx):
        top = st_.strap_h * k
        inset = out * 2 * k
        light = np.zeros((s.h, s.w, 3), np.float32)
        holes = np.zeros((s.h, s.w), np.float32)
        mid = strap * 0.55 * k
        for (cx, cy, sx, sy) in ((inset, inset, 1, 1), (s.w - inset, inset, -1, 1)):
            holes = np.maximum(holes, bracket(s, cx, cy, sx, sy, k, top_coin * k, top_arm * k, top_scroll * k, mid, top))
        for (cx, cy, sx, sy) in ((inset, s.h - inset, 1, -1), (s.w - inset, s.h - inset, -1, -1)):
            holes = np.maximum(holes, bracket(s, cx, cy, sx, sy, k, low_coin * k, low_arm * k, low_scroll * k, mid, top))
        light += holes[..., None] * (O.EMBER_DEEP * 0.9 + O.EMBER * 0.25)
        if crest:
            light += broken_chain(s, s.w / 2, inset + 3 * k, k, 52 * k, 28 * k, 9 * k, top + 1 * k)
        return light

    return FR.frame(W, H, (out + strap + 4,) * 4, st, ss=ss, post=post)
