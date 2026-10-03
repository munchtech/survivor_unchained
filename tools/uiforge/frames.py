"""Forged frames: plates, tooltips, buttons, slots, cards, tabs, bars.

One construction for all of them (the house style, docs/UI_ART_STYLE.md):

  - a strap of blackened iron drawn out under the hammer: flat facets, chipped
    edges, bevelled to both sides, riveted where the strap repeats;
  - a twisted gold wire set in a groove along it (the binders' gold);
  - a quiet hammered centre, sunk a little, tone-matched to the fallback
    (#16131a), because text colours were chosen for it;
  - corner pieces (forged brackets and coins, painted on the local Krea and
    cut out, or forged here) laid on top inside the corner squares;
  - every texture periodic over the space between the margins, so a frame
    tiles (UiArt.Slice Tile) without a seam.

Sizes are FILE pixels (twice the shown size); the canvas is supersampled
`ss` times again and area-filtered down at the end.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import cv2
import numpy as np
from PIL import Image

import forge as F
import ornament as O


@dataclass
class Style:
    out: float = 0             # overhang (shown px) beyond the control, inside the file
    strap: float = 24          # strap width (file px) from the frame's edge
    strap_h: float = 6         # strap thickness
    bevel_out: float = 3.5     # outer bevel width
    bevel_in: float = 3.0      # inner bevel width
    chip: float = 1.2          # how ragged the strap's edges are (file px)
    radius: float = 5          # outer corner radius
    chamfer: float = 0         # cut corners (file px), as a smith cuts a strap's end
    centre_drop: float = 2.0   # how far the centre sits below the strap's top
    wire: float | None = 12    # twisted wire: distance from the outer edge (None: no wire)
    wire_w: float = 3.2
    wire_mat: str = "gold"
    twist: float = 5.0         # twist period (file px)
    centre_tone: str | None = "#16131a"
    centre_alpha: float = 1.0
    strap_mat: str = "iron"
    centre_mat: str = "iron_dark"
    facet_cell: float = 16
    facet_tilt: float = 0.30
    centre_facets: float = 0.10
    grain: float = 0.12
    wear: float = 0.6
    rivets: int = 1            # rivets per tiled edge segment (0: none)
    rivet_r: float = 3.4
    seed: int = 7
    ember_seam: float = 0.0    # ember light along the inside of the strap (primary, hover)
    ember_col: str = "#ff8a3a"
    strap_tint: tuple | None = None
    pressed: bool = False
    paint: float = 0.0         # strength of the painter's filter on the result
    extra: dict = field(default_factory=dict)


def periodic_offset(arr, W, H, ml, mt, P, Q):
    """A texture of period (P, Q) laid so the area between the margins starts its period."""
    reps_x = W // P + 3
    reps_y = H // Q + 3
    big = np.tile(arr, (reps_y, reps_x))
    ox = (P - (ml % P)) % P
    oy = (Q - (mt % Q)) % Q
    return big[oy:oy + H, ox:ox + W]


def textures(W, H, m, st: Style, ss):
    """Facets, grain and colour wander, periodic between the margins."""
    ml, mt, mr, mb = m
    P, Q = max(8, W - ml - mr), max(8, H - mt - mb)
    rng = st.seed
    out = dict(
        facets=F.facets(Q, P, cell=st.facet_cell * ss, tilt=st.facet_tilt, seed=rng, soften=0.7 * ss),
        cfacets=F.facets(Q, P, cell=st.facet_cell * ss * 2.2, tilt=st.facet_tilt, seed=rng + 9, soften=1.5 * ss),
        grain=F.fbm(Q, P, scale=2.5 * ss, octaves=3, seed=rng + 1),
        wander=F.fbm(Q, P, scale=60.0 * ss, octaves=3, seed=rng + 2),
        blotch=F.fbm(Q, P, scale=18.0 * ss, octaves=4, seed=rng + 3),
        chip=F.fbm(Q, P, scale=5.0 * ss, octaves=3, seed=rng + 5),
    )
    return {k: periodic_offset(v, W, H, ml, mt, P, Q) for k, v in out.items()}, (P, Q)


def edge_coords(xx, yy, w, h, inset):
    """For each pixel: distance along its nearest edge (u) and which edge (0 top, 1 right, 2 bottom, 3 left)."""
    dl, dr = xx - inset, (w - inset) - xx
    dt, db = yy - inset, (h - inset) - yy
    stack = np.stack([dt, dr, db, dl])
    which = np.argmin(stack, axis=0)
    u = np.where((which == 0) | (which == 2), xx, yy)
    return u, which


def frame(W, H, margins, st: Style, ss=2, post=None, pieces=()):
    """A forged frame at file size (W, H) with nine-slice margins (shown px).

    `pieces`: painted corner pieces laid on after shading: dicts with
    img (RGBA PIL), corner ('tl', 'tr', 'bl', 'br' or 'all'), box (x, y, w, h in
    file px for the top-left corner; mirrored for the others unless 'mirror'
    is False), shadow (file px)."""
    m_file = [v * 2 for v in margins]
    w, h = W * ss, H * ss
    m = [int(round(v * ss)) for v in m_file]
    k = ss
    s = F.Surface(w, h)
    xx, yy = s.xx, s.yy
    tx, (P, Q) = textures(w, h, m, st, ss)
    inset = st.out * 2 * k

    # The frame's body and the distance in from its (forged, ragged) edge.
    sd_out = F.sd_box(xx, yy, w / 2, h / 2, w / 2 - inset - 0.5 * k, h / 2 - inset - 0.5 * k, st.radius * k)
    if st.chamfer > 0:
        hw, hh = w / 2 - inset - 0.5 * k, h / 2 - inset - 0.5 * k
        cut = (hw + hh - st.chamfer * k - np.abs(xx - w / 2) - np.abs(yy - h / 2)) / math.sqrt(2)
        sd_out = np.minimum(sd_out, cut)
    sd_out = sd_out + tx["wander"] * st.extra.get("edge_wobble", 0.6) * k + tx["chip"] * st.chip * k * 0.6
    d = sd_out
    s.alpha = F.coverage(d, 1.0)

    # The strap: a bevel up from the outer edge, a faceted top, a bevel down to the centre.
    S = st.strap * k
    inner_d = S + tx["chip"] * st.chip * k * 0.5
    up = np.clip(d / (st.bevel_out * k), 0, 1)
    up = np.sqrt(up)
    down = np.clip((inner_d - d) / (st.bevel_in * k), 0, 1)
    top = st.strap_h * k
    centre_h = top - st.centre_drop * k - (1.5 * k if st.pressed else 0)
    strap_h = top * np.minimum(up, 1.0)
    on_strap = (d < inner_d).astype(np.float32)
    hgt = np.where(d < inner_d - st.bevel_in * k, strap_h, centre_h + (strap_h - centre_h) * down)
    hgt = np.where(d >= inner_d, centre_h, hgt)
    strap_soft = np.clip((inner_d - d) / (1.5 * k) + 0.5, 0, 1)

    # Hammer facets: bold on the strap, faint in the centre; grain everywhere.
    hgt = hgt + tx["facets"] * k * strap_soft * up + tx["cfacets"] * k * st.centre_facets * (1 - strap_soft)
    hgt = hgt + tx["grain"] * st.grain * k

    # The twisted wire in its groove.
    wire_cov = np.zeros_like(d)
    if st.wire is not None:
        u, which = edge_coords(xx, yy, w, h, inset)
        dist = np.abs(d - st.wire * k)
        half = st.wire_w * 0.5 * k
        groove = np.clip(1 - dist / (half + 1.0 * k), 0, 1)
        hgt = hgt - groove * 1.2 * k
        # Twist: diagonal ridges along the wire, a whole number per tile.
        n = max(1, round(P / (st.twist * k)))
        per = P / n
        # Along u, with the across-distance slanting the ridges (opposite on opposite edges keeps the lay consistent).
        across = (d - st.wire * k)
        phase = (u + across * 1.2) / per
        tw = 0.5 + 0.5 * np.cos(phase * 2 * math.pi)
        prof = np.sqrt(np.clip(1 - (dist / max(half, 1e-3)) ** 2, 0, 1))
        hgt = hgt + prof * (0.9 * k + tw * 0.7 * k) * (dist < half)
        wire_cov = F.coverage(half - dist, 1.0)

    # Materials.
    wander = 1 + tx["wander"] * 0.10 + tx["blotch"] * 0.07
    s.paint(np.ones_like(d), st.centre_mat, albedo_mul=wander)
    tint = wander if st.strap_tint is None else wander[..., None] * np.asarray(st.strap_tint, np.float32)
    s.paint(strap_soft, st.strap_mat, albedo_mul=tint)
    s.height = hgt.astype(np.float32)

    # Rivets along each edge, one (or more) per tiled segment, centred in it.
    if st.rivets and st.strap > 8:
        ml, mt, mr, mb = m
        rr = st.rivet_r * k
        mid = (st.wire * k + inner_d.mean()) / 2 if st.wire is not None else S * 0.5
        mid = st.extra.get("rivet_at", mid / k) * k
        for i in range(st.rivets):
            fx = ml + P * (i + 0.5) / st.rivets
            fy = mt + Q * (i + 0.5) / st.rivets
            for (cx, cy) in ((fx, inset + mid), (fx, h - inset - mid), (inset + mid, fy), (w - inset - mid, fy)):
                O.rivet(s, cx, cy, rr, mat="iron", base=top - 0.5 * k)

    if st.wire is not None:
        s.paint(wire_cov, st.wire_mat)

    light = None
    if post:
        light = post(s, m, st, k, tx)

    # Edge wear: convex edges show bright steel; cavities hold grime.
    curv = cv2.Laplacian(F.blur(s.height, 1.0 * k), cv2.CV_32F, ksize=3)
    convex = np.clip(-curv / (0.8 * k) - 0.1, 0, 1) * (0.5 + 0.5 * np.clip(tx["blotch"] + 0.5, 0, 1))
    concave = np.clip(curv / (0.8 * k), 0, 1)
    iron = (s.metal < 0.95).astype(np.float32) * (1 - wire_cov)
    wear = convex * st.wear * iron
    s.albedo = s.albedo * (1 - wear[..., None]) + np.asarray(F.MATS["steel"].albedo) * 0.6 * wear[..., None]
    s.rough = s.rough * (1 - wear * 0.45)
    s.metal = np.maximum(s.metal, wear * 0.9)
    grime = concave * 0.45 * iron
    s.albedo *= (1 - grime[..., None] * np.array([0.5, 0.55, 0.62], np.float32))

    lin = s.shade(normal_strength=1.0, ao=0.8, shadow=0.6, light_elev=32)

    # The flat centre's tone matched to what the text colours were chosen for.
    ml, mt, mr, mb = m
    if st.centre_tone:
        cen = lin[mt + 2 * k:h - mb - 2 * k, ml + 2 * k:w - mr - 2 * k]
        cm = np.clip((d - inner_d) / (5 * k), 0, 1)
        sel = cm[mt + 2 * k:h - mb - 2 * k, ml + 2 * k:w - mr - 2 * k] > 0.99
        if cen.size and sel.any():
            cur = np.median(cen[sel], axis=0)
            gain = np.clip(F.hexc(st.centre_tone) / np.maximum(cur, 1e-5), 0.1, 10.0)
            lin = lin * (1 + (gain - 1) * cm[..., None])

    if st.ember_seam > 0:
        lin = lin + ember_seam(d, inner_d, k, st) * s.alpha[..., None]
    if light is not None:
        lin = lin + light

    img = np.asarray(s.finish(lin), np.float32) / 255
    if st.paint > 0:
        painted = F.kuwahara(img[..., :3], r=max(2, int(1.5 * k)))
        img[..., :3] = img[..., :3] * (1 - st.paint) + painted * st.paint
    img[..., 3] *= np.where(d >= inner_d + 2 * k, st.centre_alpha, 1.0)
    out = F.to_pil(F.downsample(img, (W, H)))
    for p in pieces:
        out = lay_piece(out, p)
    return out


def ember_seam(d, inner_edge, k, st):
    """Ember light rising along the inside of the strap (linear RGB to add)."""
    col = F.hexc(st.ember_col)
    hot = F.hexc("#ffd07a")
    dist = d - inner_edge
    core = np.exp(-np.maximum(dist, 0) / (2.5 * k)) * (dist > -1.5 * k)
    halo = np.exp(-np.maximum(dist, 0) / (10 * k)) * (dist > -1.5 * k)
    return (core[..., None] * hot * 1.4 + halo[..., None] * col * 0.6) * st.ember_seam


# ------------------------------------------------------------------ pieces --

def lay_piece(base: Image.Image, p):
    """A painted piece (RGBA) laid in the frame's corners, with a contact shadow."""
    img = p["img"]
    x, y, bw, bh = p["box"]
    corners = p.get("corner", "all")
    corners = ["tl", "tr", "bl", "br"] if corners == "all" else ([corners] if isinstance(corners, str) else corners)
    W, H = base.size
    piece = img.resize((bw, bh), Image.LANCZOS)
    for c in corners:
        im = piece
        px, py = x, y
        if c in ("tr", "br"):
            im = im.transpose(Image.FLIP_LEFT_RIGHT) if p.get("mirror", True) else im
            px = W - x - bw
        if c in ("bl", "br"):
            im = im.transpose(Image.FLIP_TOP_BOTTOM) if p.get("mirror", True) else im
            py = H - y - bh
        if p.get("relight", True) and c != "tl":
            im = relight(im, c)
        sh = p.get("shadow", 3)
        if sh:
            a = np.asarray(im, np.float32)[..., 3] / 255
            a = F.blur(a, sh * 0.8)
            layer = np.zeros((H, W), np.float32)
            ox, oy = int(sh * 0.6), int(sh * 0.9)
            x0, y0 = px + ox, py + oy
            xa, ya = max(0, x0), max(0, y0)
            xb, yb = min(W, x0 + bw), min(H, y0 + bh)
            if xb > xa and yb > ya:
                layer[ya:yb, xa:xb] = a[ya - y0:yb - y0, xa - x0:xb - x0]
            b = np.asarray(base, np.float32) / 255
            dark = layer * p.get("shadow_strength", 0.7)
            b[..., :3] *= (1 - dark[..., None])
            b[..., 3] = np.maximum(b[..., 3], dark * 0.85)
            base = F.to_pil(b)
        base = base.copy()
        base.alpha_composite(im, (px, py))
    return base


def relight(im: Image.Image, corner):
    """A piece painted lit from the upper left, mirrored into another corner, keeps the
    light from the upper left: its shading is re-mirrored (light and dark swapped across
    the mirrored axis), approximated by flipping the luminance gradient."""
    a = np.asarray(im, np.float32) / 255
    rgb, al = a[..., :3], a[..., 3]
    lum = rgb.mean(axis=2)
    low = F.blur(lum, 6)
    detail = lum - low
    # Flip the large-scale shading back along the mirrored axes.
    flip = low
    if corner in ("tr", "br"):
        flip = flip[:, ::-1]
    if corner in ("bl", "br"):
        flip = flip[::-1, :]
    target = flip + detail
    gain = np.clip((target + 0.02) / (lum + 0.02), 0.4, 2.2)
    rgb = np.clip(rgb * gain[..., None], 0, 1)
    return F.to_pil(np.dstack([rgb, al]))
