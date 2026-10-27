"""The Drowned Girl HUD, piece 1 (UI 16): cut her bronze figure for the life orb (--hud drowned).

    python tools/uiforge/dg_figure_cut.py [--check out.png]

Source: a Krea 2 turbo painting (tools/comfy/ui_assets.json "hud_dg_figure"), its BiRefNet cut beside it, in
survivorsunchained_inputs/ui16_dg_src/. The painted glass orb is fitted with a circle and cut out of the figure
(hud_orb.gdshader theme 3 draws the live orb there, under her fingers); what of her hand lies over the glass
stays as the casing in front of it. The figure is graded to mid-low value bronze (unsaturated against the blood),
scaled so the glass is ORB_D px across at 1080 (the art at 2x), and cropped from above her head to HEAD_H px
below it (the screen's foot cuts the rest). Writes godot/art/ui/lamp_life/drowned/lamp_cold.png and lamp_geo.json.

dg2 (the judge: the hand weak, the thumb over the bottom band, the bronze olive and dim): the source is seed 6305
with its hand and forearm inpainted from d1b's cradle (dg2_hand.png, Krea 2 turbo masked img2img over a guide
of d1b's hand; face and hair untouched), the palm under the glass. Her hand inside the glass's circle is KEPT in
lamp_cold (behind the glass: hud_dg_orb.gdshader draws the glass over it and shows it darkened through the
empty glass), so nothing of her covers the glass and its lowest quarter is always clear. lamp_mask.png: R her
parts over the glass (none), G her hand and forearm (held at full when the figure fades). The grade warms the
highlights (brow, nose, lips, knuckles, hair crests), deepens the verdigris and tones down the shoulder's hot spot.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = r"C:\Users\munch\Desktop\survivorsunchained_inputs\ui16_dg_src"
SEED = 6305
NAME = "dg2_hand"          # the inpainted source (and NAME_cut.png, its BiRefNet cut)
GLASS = (178.9, 167.8, 139.8)  # seed 6305's glass (the inpaint kept its upper half): centre, radius
OUT = os.path.join(WT, "godot", "art", "ui", "lamp_life", "drowned")

ORB_D = 120.0       # the glass across at 1080
HEAD_H = 262.0      # her head's top to the screen's foot at 1080
PAD = 6             # clear round her in the quad, 1080 px
RIGHT_X = 770.0     # the quad's right edge on the screen (the hair runs on under the draught's glass)
BAR_LINE = 930.0    # the bar's top line: above it, she fades when something is behind her
CHAIN_Y = 1047.0    # the chain's row (the ring orb's eye)
GRADE = dict(value=0.80, sat=0.86, gamma=1.06)
SHOULDER = (530.0, 560.0, 70.0)   # the hot spot on her shoulder (source px): toned down


def fit_circle(alpha, box):
    """The glass's edge against the black: on each row of its upper part (above her fingers) the run that starts
    at its left edge ends at its right (where it meets her lips, the run's end is her lips: those rows are the
    outliers dropped); a least-squares circle through both ends."""
    x0, y0, x1, y1 = box
    pts = []
    for y in range(y0, y0 + int(0.55 * (y1 - y0))):
        row = alpha[y, max(x0 - 20, 0):] > 0.5
        on = np.nonzero(row)[0]
        if not len(on):
            continue
        a = on[0]
        off = np.nonzero(~row[a:])[0]
        if not len(off):
            continue
        pts += [(a + max(x0 - 20, 0), y), (a + off[0] + max(x0 - 20, 0), y)]
    P = np.array(pts, float)
    for _ in range(3):
        A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]
        cx, cy, c = np.linalg.lstsq(A, P[:, 0] ** 2 + P[:, 1] ** 2, rcond=None)[0]
        r = np.sqrt(c + cx * cx + cy * cy)
        res = np.abs(np.hypot(P[:, 0] - cx, P[:, 1] - cy) - r)
        P = P[res < max(1.5, 2.5 * np.median(res))]
    return cx, cy, float(r), len(P)


def main():
    check = sys.argv[sys.argv.index("--check") + 1] if "--check" in sys.argv else None
    rgb = np.asarray(Image.open(os.path.join(SRC, f"{NAME}.png")).convert("RGB"), np.float32) / 255
    alpha = np.asarray(Image.open(os.path.join(SRC, f"{NAME}_cut.png")).convert("RGBA"), np.float32)[..., 3] / 255
    H, W = alpha.shape
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    cx, cy, r = GLASS
    print(f"glass: centre ({cx:.1f}, {cy:.1f}) r {r:.1f}")
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.hypot(xx - cx, yy - cy)
    inside = d < r + 1.5
    # her bronze (even lit red by the glass, under ~2.4 red over green; never the smoked glass's violet)
    bronze = (R / (G + 0.03) < 2.4) & (B < 0.92 * G) & (alpha > 0.5) & (np.maximum(R, G) > 0.06)
    glint = (np.min(rgb, axis=2) > 0.55)
    # her hand inside the circle: the bronze there joined to the hand below it (the painted speculars float free)
    cand = ndimage.binary_opening(inside & bronze & ~glint, iterations=2)
    lab, n = ndimage.label(cand | (bronze & ~inside & (d < r + 40)))
    ring = (d > r + 2) & (d < r + 6) & (yy > cy) & bronze
    keep = set(np.unique(lab[ring])) - {0}
    hand_in = inside & np.isin(lab, list(keep)) & cand
    hand_in = ndimage.binary_dilation(ndimage.binary_fill_holes(ndimage.binary_closing(hand_in, iterations=2)), iterations=1) & inside
    hs = ndimage.gaussian_filter(hand_in.astype(np.float32), 1.2)
    glass = np.clip((r + 1.5 - d) / 1.5, 0, 1)
    hole = glass * (1 - np.clip(hs * 1.6 - 0.3, 0, 1))
    # (the painted blood's glow spilt past the glass onto the black: not her)
    spill = (~inside) & (R > 1.8 * G) & (R > 1.5 * B) & ~bronze
    a = alpha * (1 - hole) * (1 - ndimage.gaussian_filter(spill.astype(np.float32), 1.0))
    # her hand and forearm (held at full in the fade): left of her neck and chest, below the glass's middle
    bnd = np.interp(yy, [0, 520, 600, 660, 768], [300, 292, 268, 255, 250])
    held = ndimage.gaussian_filter(((xx < bnd) & (yy > cy) & (a > 0.05)).astype(np.float32), 2.0)
    # grade: warm bronze, the blood still reads first
    lum = (0.3 * R + 0.59 * G + 0.11 * B)[..., None]
    g = lum + (rgb - lum) * GRADE["sat"]
    g = np.clip(g, 0, 1) ** GRADE["gamma"] * GRADE["value"]
    gl = (0.3 * g[..., 0] + 0.59 * g[..., 1] + 0.11 * g[..., 2])[..., None]
    # (the highlights warmed toward old gold: brow, nose, lips, knuckles, the hair's crests)
    hi = np.clip((gl - 0.30) / 0.35, 0, 1)
    g = g * (1 + hi * np.array([0.16, 0.04, -0.14]))
    # (the verdigris deepened: where green leads red, darker and a richer blue-green)
    green = np.clip((G - R) * 6.0 + 0.2, 0, 1)[..., None] * (1 - hi)
    g = g * (1 - green) + g * np.array([0.62, 0.86, 0.84]) * green
    # (the shoulder's hot spot toned down)
    sx, sy, sr = SHOULDER
    sm = np.exp(-((xx - sx) ** 2 + (yy - sy) ** 2) / (2 * sr * sr))[..., None]
    gl = (0.3 * g[..., 0] + 0.59 * g[..., 1] + 0.11 * g[..., 2])[..., None]
    over = np.clip(gl - 0.42, 0, None)
    g = g - sm * over * 0.55 * (g / np.maximum(gl, 1e-3))
    g = np.clip(g, 0, 1)

    # the scale: the glass ORB_D across at 1080, the art at 2x
    s = ORB_D / (2 * r)             # source px -> 1080 px
    rows = np.nonzero(alpha.max(axis=1) > 0.5)[0]
    head_top = rows[0]
    cols = np.nonzero(alpha.max(axis=0) > 0.5)[0]
    left = cols[0]
    x0 = left - PAD / s
    y0 = head_top - PAD / s
    y1 = head_top + HEAD_H / s
    x1 = W
    cw, ch = (x1 - x0) * s, (y1 - y0) * s
    cw2, ch2 = int(round(cw * 2)), int(round(ch * 2))
    rgba = np.dstack([g, a]).astype(np.float32)
    # premultiply for the resample, then back
    pm = np.dstack([rgba[..., :3] * rgba[..., 3:], rgba[..., 3:]])
    im = Image.fromarray((np.clip(pm, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    box = (x0, y0, x0 + cw2 / (2 * s), y0 + ch2 / (2 * s))
    im = im.transform((cw2, ch2), Image.EXTENT, box, Image.BICUBIC) if False else \
        im.resize((cw2, ch2), Image.LANCZOS, box=box)
    o = np.asarray(im, np.float32) / 255
    oa = o[..., 3:]
    orgb = np.where(oa > 1e-3, o[..., :3] / np.maximum(oa, 1e-3), 0)
    # the right edge: the hair runs on under the bar; feather its last 24 px (1080) so it ends soft until piece 2
    fe = np.clip((cw2 - np.arange(cw2)) / 48.0, 0, 1)[None, :, None]
    oa = oa * fe
    out = Image.fromarray((np.clip(np.dstack([orgb, oa]), 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, "lamp_cold.png"))
    mk = Image.fromarray((np.dstack([np.zeros_like(held), held, np.zeros_like(held)]) * 255 + 0.5).astype(np.uint8), "RGB")
    mk = mk.resize((cw2, ch2), Image.LANCZOS, box=box)
    mk.save(os.path.join(OUT, "lamp_mask.png"))

    def at(x, y):
        return [round((x - x0) * s, 2), round((y - y0) * s, 2)]
    oc = at(cx, cy)
    canvas = [round(cw, 2), round(ch, 2)]
    at_scr = [round(RIGHT_X - cw, 2), round(1080 - ch, 2)]
    geo = {
        "shape": "drowned", "seed": SEED, "canvas": canvas, "at": at_scr,
        "orb_c": oc, "orb_r": round(r * s, 2), "orb_vis": round(r * s - 0.6, 2),
        "level_foot": -1,
        "font_mid": oc, "number_y": oc[1],
        "eye": [round(cw - 2, 2), round(CHAIN_Y - at_scr[1], 2)],
        "foot": canvas[1], "top": 0, "floor": 1080, "top_line": at_scr[1],
        "fade_at": [0, 0], "fade_size": [canvas[0], round(BAR_LINE - at_scr[1], 2)],
        "flame_full": 0, "glass_px": round(2 * r * s, 1),
        "oil_top": round(oc[1] - r * s, 2), "oil_bot": round(oc[1] + r * s, 2),
        "font_x": [round(oc[0] - r * s, 2), round(oc[0] + r * s, 2)], "skip": [0, 0],
    }
    json.dump(geo, open(os.path.join(OUT, "lamp_geo.json"), "w"), indent=1)
    print(json.dumps(geo))
    if check:
        bg = Image.new("RGBA", out.size, (60, 58, 70, 255))
        bg.alpha_composite(out)
        bg.save(check)


if __name__ == "__main__":
    main()
