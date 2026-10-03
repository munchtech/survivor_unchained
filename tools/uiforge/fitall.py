"""Every painted pick fitted into godot/art/ui/ (the metal chrome is chrome.py; paper is
paper.py, called from here) (see picks below: each a raw
Krea result named by its batch, seed and place, remade by batch.py, icons.py
or items.py if missing).

    python tools/uiforge/fitall.py [NAME ...]
"""
from __future__ import annotations

import os
import sys

import cv2
import numpy as np
from PIL import Image

import cut as C
import forge as F
import nineslice as N
import painted as P
import rounds
import smalls

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui")
RAW = os.path.join(ROOT, "tools", "comfy", "out", "uiforge")


def raw(*p):
    return os.path.join(RAW, *p)


def ui(*p):
    path = os.path.join(UI, *p)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


# ------------------------------------------------------------------ frames --

def f_paper():
    """Paper and the hint note: made in paper.py (laid paper, foxing, a hand-torn deckle,
    iron caps, a nail and wax), painted over, calmed, tiled."""
    import paper
    paper.build(UI)


def f_mapframe():
    """The atlas's wooden frame, laid over the map (MapScreen): its middle open."""
    img = smalls.fit(raw("map_frame", "map_frame_805_0.png"), ui("frames", "map_frame.png"), (256, 256), (20, 20, 20, 20), 26,
                     tone=None, tile=True, darken=0.9, crop=True)
    a = img[..., 3].copy()
    yy, xx = np.mgrid[0:256, 0:256]
    edge = np.minimum(np.minimum(xx, 255 - xx), np.minimum(yy, 255 - yy)).astype(np.float32)
    a *= np.clip((38 - edge) / 2.0, 0, 1)
    P.save_rgba(img[..., :3], a, ui("frames", "map_frame.png"))


# ------------------------------------------------------------- round, cut --

def f_minimap():
    rounds.fit_round(raw("small_ring", "small_ring_707_1.png"), 480, rim_at=0.97, open_below=0.835).save(ui("minimap", "frame.png"))


def f_medals():
    rounds.fit_round(raw("medal", "medal_31.png"), 140, rim_at=0.98, calm_below=0.5, ember_rim=0.6).save(ui("hud", "medal_level.png"))
    rounds.fit_round(raw("many1", "medal_heart_321_0.png"), 128, rim_at=0.98).save(ui("hud", "medal_heart.png"))
    rounds.fit_round(raw("many1", "ring_art_322_0.png"), 220, rim_at=0.99, open_below=0.78).save(ui("hud", "ring_art.png"))


def cut_fit(src, dst, size, mode="mask+glow", fade_x=0.0, ember_at=None, ember=0.0):
    """A cut piece centred in its box at its largest; fade_x softens the ends (a chain running off)."""
    rgba = C.cutout(src, mode=mode)
    x0, y0, x1, y1 = C.bbox(rgba, thr=0.08, pad=4)
    rgba = rgba[y0:y1, x0:x1]
    h, w = rgba.shape[:2]
    if fade_x > 0:
        xs = np.linspace(0, 1, w)
        f = np.clip(np.minimum(xs, 1 - xs) / fade_x, 0, 1)
        rgba[..., 3] *= f[None, :]
    if ember_at is not None:
        cx, cy = ember_at[0] * w, ember_at[1] * h
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.hypot(xx - cx, yy - cy) / max(h, 1)
        lin = F.srgb_to_lin(rgba[..., :3]) + (np.exp(-(d / 0.18) ** 2) * ember)[..., None] * F.hexc("#ff8a3a")
        g = np.exp(-(d / 0.35) ** 2) * ember * 0.6
        rgba[..., :3] = F.lin_to_srgb(np.clip(lin, 0, 1))
        rgba[..., 3] = np.maximum(rgba[..., 3], g)
    rgba = C.grade(rgba)
    W, H = size
    k = min(W / w, H / h)
    nw, nh = max(1, int(w * k)), max(1, int(h * k))
    small = F.downsample(rgba, (nw, nh)) if k < 1 else cv2.resize(rgba, (nw, nh), interpolation=cv2.INTER_CUBIC)
    out = np.zeros((H, W, 4), np.float32)
    ox, oy = (W - nw) // 2, (H - nh) // 2
    out[oy:oy + nh, ox:ox + nw] = small
    P.save_rgba(out[..., :3], out[..., 3], dst)


def extend_fit(src, dst, size, centre=0.34, ember=0.0):
    """A long painted ornament fitted to a wider box: cut, scaled to the box's height, its
    middle (`centre` of its width: the coin or link) kept as painted and its two arms
    drawn out to reach the ends, as a smith draws a bar longer."""
    rgba = C.cutout(src, mode="mask+glow")
    x0, y0, x1, y1 = C.bbox(rgba, thr=0.08, pad=4)
    rgba = C.grade(rgba[y0:y1, x0:x1])
    W, H = size
    h, w = rgba.shape[:2]
    k = H / h
    big = cv2.resize(rgba, (max(1, int(w * k)), H), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    bw = big.shape[1]
    c0, c1 = int(bw * (0.5 - centre / 2)), int(bw * (0.5 + centre / 2))
    mid = big[:, c0:c1]
    side = (W - mid.shape[1]) // 2
    left = cv2.resize(big[:, :c0], (side, H), interpolation=cv2.INTER_CUBIC)
    right = cv2.resize(big[:, c1:], (W - side - mid.shape[1], H), interpolation=cv2.INTER_CUBIC)
    out = np.concatenate([left, mid, right], axis=1)
    if ember > 0:
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.hypot((xx - W / 2) / H, (yy - H / 2) / H)
        lin = F.srgb_to_lin(out[..., :3]) + (np.exp(-(d / 0.35) ** 2) * ember)[..., None] * F.hexc("#ff8a3a") * out[..., 3:4]
        out[..., :3] = F.lin_to_srgb(np.clip(lin, 0, 1))
    P.save_rgba(out[..., :3], np.clip(out[..., 3], 0, 1), dst)


def f_bosscasing():
    """The boss's bar: a channel of black iron with red-gold trim, a horned ram's skull at
    each end (bars/casing_boss.png, over the bar by GameHud.Casing). The painting's
    channel interior is mapped onto the bar's 16 px; the skulls lie wholly outside it."""
    src = raw("boss_track", "boss_track_804_2.png")
    rgb = P.load(src)
    m = C.birefnet_mask(src)
    # The painting: channel interior rows 260..320, skulls from x 83 to 320 and 1040 to 1262.
    x0, x1, y0, y1 = 80, 1280, 170, 410
    k = 32 / 60  # interior 60 painting px -> 32 file px (16 shown)
    crop = np.dstack([rgb[y0:y1, x0:x1], P.silhouette(m[y0:y1, x0:x1])])
    W, H = int(round((x1 - x0) * k)), 128
    img = cv2.resize(crop, (W, H), interpolation=cv2.INTER_AREA)
    img = C.grade(img)
    # The interior is open: the bar's own fill shows through.
    top, bot = int(round((260 - y0) * k)), int(round((320 - y0) * k))
    L = 128
    a = img[..., 3]
    yy, xx = np.mgrid[0:H, 0:W]
    inside = (yy >= top + 1) & (yy < bot - 1) & (xx >= L - 4) & (xx < W - L + 4)
    a[inside] = 0
    img[..., 3] = a
    # The channel between the skulls made to tile: a period from the painting's middle.
    mid = img[:, L:W - L]
    img = np.concatenate([img[:, :L], N.periodic_centre(mid) * 0 + mid, img[:, W - L:]], axis=1)
    img = N.tileable(img, (L, top, L, H - bot), blend=10)
    img[..., 3] = np.where(inside, 0, img[..., 3])
    P.save_rgba(img[..., :3], img[..., 3], ui("bars", "casing_boss.png"))


def f_logo():
    cut_fit(raw("logo_c", "logo_c_801_2.png"), ui("title", "logo.png"), (1400, 440), fade_x=0.06)


def f_rule():
    extend_fit(raw("rule", "rule_803_0.png"), ui("ornaments", "rule.png"), (960, 24), centre=0.3, ember=0.6)


def f_flourish():
    extend_fit(raw("divider", "divider_42.png"), ui("ornaments", "flourish.png"), (720, 64), centre=0.36)


GROUPS = {n[2:]: f for n, f in globals().items() if n.startswith("f_")}

if __name__ == "__main__":
    for n in sys.argv[1:] or list(GROUPS):
        GROUPS[n]()
        print(n, flush=True)
