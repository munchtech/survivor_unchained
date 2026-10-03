"""Every painted pick fitted into godot/art/ui/ (see picks below: each a raw
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
    smalls.fit(raw("small_paper", "small_paper_708_1.png"), ui("frames", "paper.png"), (1024, 1024), (32, 32, 32, 32), 28,
               tone="#e4d6b6", tile=True, keep=0.55, darken=1.0, sigma=14)


def f_hint():
    smalls.fit(raw("small_hint", "small_hint_709_1.png"), ui("frames", "hint.png"), (512, 256), (40, 40, 40, 40), 30,
               tone="#e6d6b0", tile=True, keep=0.55, sigma=10)


def f_tooltip():
    for name, src, worn in (("tooltip", "small_tooltip_706_0.png", False), ("tooltip_worn", "small_tooltip_706_0.png", True)):
        img = smalls.fit(raw("small_tooltip", src), ui("frames", name + ".png"), (256, 256), (16, 16, 16, 16), 13,
                         tone="#100e13", tile=True, keep=0.35, darken=0.75)
        if worn:
            # The worn thing's card: the same, quieter: its gold become pewter.
            rgb, a = img[..., :3], img[..., 3]
            grey = rgb.mean(axis=2, keepdims=True)
            warm = np.clip((rgb[..., 0:1] - rgb[..., 2:3]) * 4, 0, 1)
            rgb = rgb * (1 - warm) + (grey * np.array([0.92, 0.94, 1.0])) * warm * 0.85
            P.save_rgba(rgb, a, ui("frames", name + ".png"))


def f_toast():
    smalls.fit(raw("small_toast", "small_toast_703_1.png"), ui("frames", "toast.png"), (256, 96), (14, 10, 10, 10), 9,
               tone="#121016", tile=True, keep=0.35, darken=0.8)


def f_prompt():
    smalls.fit(raw("small_prompt", "small_prompt_704_1.png"), ui("frames", "prompt.png"), (256, 80), (22, 12, 22, 12), 8,
               tone="#141117", tile=True, keep=0.3, darken=0.8)


def f_chip():
    smalls.fit(raw("small_chip", "small_chip_702_0.png"), ui("frames", "chip.png"), (64, 64), (8, 8, 8, 8), 6,
               tone="#0f0d12", tile=False, keep=0.3, darken=0.75)


def f_wslot():
    smalls.fit(raw("small_wslot", "small_wslot_701_1.png"), ui("frames", "weapon_slot.png"), (134, 134), (12, 12, 12, 12), 10,
               tone="#121016", tile=False, keep=0.35, darken=0.75)


def f_mapframe():
    smalls.fit(raw("map_frame", "map_frame_805_0.png"), ui("frames", "map_frame.png"), (256, 256), (20, 20, 20, 20), 26,
               tone=None, tile=True, darken=0.9, crop=True)


def f_buttons():
    """Seven states from one painted plate, changed as metal changes."""
    src = raw("small_button", "small_button_705_1.png")
    W, H = 192, 64
    base = smalls.fit(src, ui("frames", "button.png"), (W, H), (12, 10, 12, 10), 7, tone="#221e28", tile=True, keep=0.3, darken=0.85)
    rgb0, a = base[..., :3].copy(), base[..., 3].copy()
    yy, xx = np.mgrid[0:H, 0:W]
    edge = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy)).astype(np.float32)
    rim = np.clip(1 - (edge - 10) / 4, 0, 1)                    # the strap
    inner = np.clip(1 - np.abs(edge - 15) / 3, 0, 1)            # just inside it
    warm = np.clip((rgb0[..., 0] - rgb0[..., 2]) * 5, 0, 1) * rim  # the gold wire
    lin0 = F.srgb_to_lin(rgb0)

    def save(name, lin, alpha=a):
        img = np.dstack([F.lin_to_srgb(np.clip(lin, 0, 1)), alpha])
        img = N.tileable(img, (24, 20, 24, 20), blend=6)
        P.save_rgba(img[..., :3], img[..., 3], ui("frames", name + ".png"))

    def tone(lin, hexcol, amount=1.0):
        t = F.hexc(hexcol)
        c = 1 - rim
        cur = np.median(lin[c > 0.9], axis=0)
        return lin * (1 - c[..., None]) + lin * (t / np.maximum(cur, 1e-4)) * c[..., None]

    ember = F.hexc("#ff8a3a")
    hot = F.hexc("#ffd07a")
    save("button", lin0)
    save("button_hover", tone(lin0 * (1 + rim[..., None] * 0.45), "#2c2732") + inner[..., None] * ember * 0.10 + warm[..., None] * hot * 0.25)
    top_shadow = np.clip(1 - (yy - 14) / 14, 0, 1) * (1 - rim)
    save("button_pressed", tone(lin0 * (1 + rim[..., None] * 0.2), "#19161d") * (1 - top_shadow[..., None] * 0.5) + warm[..., None] * hot * 0.2)
    grey = lin0.mean(axis=2, keepdims=True)
    save("button_disabled", tone(grey * 0.55 + lin0 * 0.15, "#16141a"))
    bronze = np.array([1.25, 0.82, 0.5], np.float32)
    pl = lin0 * (1 + rim[..., None] * (bronze - 1) * 0.9)
    save("button_primary", tone(pl, "#3a230e") + warm[..., None] * ember * 0.5 + inner[..., None] * ember * 0.10)
    save("button_primary_hover", tone(pl * (1 + rim[..., None] * 0.35), "#4a2c12") + warm[..., None] * hot * 0.9 + inner[..., None] * ember * 0.22)
    save("button_primary_pressed", tone(pl * 1.1, "#3e2410") * (1 - top_shadow[..., None] * 0.45) + warm[..., None] * hot * 1.2 + inner[..., None] * ember * 0.3)


def f_tabs():
    """The book's tabs: the Waystation ledger's stitched leather; the open page's lit."""
    src = raw("tab", "tab_806_1.png")
    img = smalls.fit(src, ui("frames", "tab.png"), (160, 72), (14, 10, 14, 6), 8, tone="#24160f", tile=False, keep=0.5,
                     darken=0.8, crop=True)
    rgb, a = img[..., :3], img[..., 3]
    lin = F.srgb_to_lin(rgb)
    H, W = a.shape
    yy, xx = np.mgrid[0:H, 0:W]
    glow = np.clip(1 - yy / (H * 0.9), 0, 1) ** 2
    lin_on = lin * np.array([1.5, 1.25, 1.0]) + glow[..., None] * F.hexc("#ff8a3a") * 0.08
    P.save_rgba(F.lin_to_srgb(np.clip(lin_on, 0, 1)), a, ui("frames", "tab_on.png"))


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
