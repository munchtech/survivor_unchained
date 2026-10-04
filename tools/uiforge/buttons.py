"""Buttons, segments, tabs, rows, keycaps, chips, toasts, prompts, tooltips:
the small forged frames. All one construction (frames.frame): a plate of
blackened iron with its corners cut as a smith cuts a strap's end, a crisp
bevelled edge, a fine gold wire set inside it, a rivet in each corner. The
states differ as metal does: lit (hover), pressed in, tarnished (disabled);
and the one thing to do has the ember awake in its seam (primary).
"""
from __future__ import annotations

import numpy as np

import forge as F
import frames as FR
import ornament as O


def corner_rivets(r=2.6, at=(9, 9), mat="iron"):
    def post(s, m, st, k, tx):
        inset = st.out * 2 * k
        top = st.strap_h * k
        ax, ay = at[0] * k + inset, at[1] * k + inset
        for (cx, cy) in ((ax, ay), (s.w - ax, ay), (ax, s.h - ay), (s.w - ax, s.h - ay)):
            O.rivet(s, cx, cy, r * k, mat=mat, base=top - 0.6 * k)
        return None
    return post


def small_style(**kw):
    st = FR.Style(out=0, strap=6, strap_h=4.0, bevel_out=2.4, bevel_in=1.6, chip=0.25, radius=2, chamfer=7,
                  centre_drop=1.0, wire=8.5, wire_w=2.2, twist=1000.0, facet_cell=9, facet_tilt=0.0,
                  centre_facets=0.0, grain=0.06, rivets=0, seed=21, wear=0.8,
                  centre_tone="#221e28", strap_mat="iron", centre_mat="iron_dark")
    st.extra["edge_wobble"] = 0.15
    for a, v in kw.items():
        setattr(st, a, v)
    return st


def ember_wire(st, strength):
    """The wire itself lit: ember light along it (for the primary action)."""
    def light(s, m, st_, k, tx, base_post=None):
        return None
    return light


def button(state="normal", primary=False, W=192, H=64, margins=(12, 10, 12, 10), seed=21):
    """state: normal, hover, pressed, disabled."""
    st = small_style(seed=seed)
    wire_glow = 0.0
    if primary:
        st.strap_mat = "bronze"
        st.centre_tone = "#3a230e"
        st.wire_mat = "gold"
        st.strap_tint = (0.62, 0.55, 0.5)
        wire_glow = 0.55
        st.ember_seam = 0.10
    if state == "hover":
        st.centre_tone = "#2a2530" if not primary else "#4a2c12"
        st.strap_tint = tuple(v * 1.35 for v in (st.strap_tint or (1, 1, 1)))
        st.ember_seam = 0.16 if not primary else 0.22
        wire_glow = 0.25 if not primary else 0.9
    elif state == "pressed":
        st.pressed = True
        st.centre_tone = "#19161d" if not primary else "#3e2410"
        st.ember_seam = 0.08 if not primary else 0.35
        wire_glow = 0.2 if not primary else 1.2
    elif state == "disabled":
        st.strap_mat = "iron_dark"
        st.wire_mat = "pewter"
        st.centre_tone = "#16141a"
        st.wear = 0.1
        st.strap_tint = (0.75, 0.75, 0.78)
    rivet = corner_rivets(r=2.2, at=(6.5, 6.5), mat="bronze" if primary else "iron")

    def post(s, m, st_, k, tx):
        rivet(s, m, st_, k, tx)
        if wire_glow <= 0 or st_.wire is None:
            return None
        inset = st_.out * 2 * k
        d = F.sd_box(s.xx, s.yy, s.w / 2, s.h / 2, s.w / 2 - inset - 0.5 * k, s.h / 2 - inset - 0.5 * k, st_.radius * k)
        if st_.chamfer > 0:
            import math
            hw, hh = s.w / 2 - inset - 0.5 * k, s.h / 2 - inset - 0.5 * k
            d = np.minimum(d, (hw + hh - st_.chamfer * k - np.abs(s.xx - s.w / 2) - np.abs(s.yy - s.h / 2)) / math.sqrt(2))
        dist = np.abs(d - st_.wire * k)
        core = np.exp(-(dist / (1.4 * k)) ** 2)
        halo = np.exp(-dist / (4.0 * k))
        col = O.EMBER_HI * 1.1 if primary else F.hexc("#f3d9a0") * 0.6
        return (core[..., None] * col + halo[..., None] * O.EMBER * 0.35) * wire_glow
    img = FR.frame(W, H, margins, st, ss=4, post=post)
    if state == "disabled":
        a = np.asarray(img, np.float32) / 255
        grey = a[..., :3].mean(axis=2, keepdims=True)
        a[..., :3] = (grey * 0.7 + a[..., :3] * 0.3) * 0.85
        img = F.to_pil(a)
    return img
