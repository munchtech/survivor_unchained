"""The Drowned Girl HUD, piece 1 (UI 16): cut her bronze figure for the life orb (--hud drowned).

    python tools/uiforge/dg_figure_cut.py [--check out.png]

Source: a Krea 2 turbo painting (tools/comfy/ui_assets.json "hud_dg_figure"), its BiRefNet cut beside it, in
survivorsunchained_inputs/ui16_dg_src/. The painted glass orb is fitted with a circle and cut out of the figure
(hud_orb.gdshader theme 3 draws the live orb there, under her fingers); what of her hand lies over the glass
stays as the casing in front of it. The figure is graded to mid-low value bronze (unsaturated against the blood),
scaled so the glass is ORB_D px across at 1080 (the art at 2x), and cropped from above her head to HEAD_H px
below it (the screen's foot cuts the rest). Writes godot/art/ui/lamp_life/drowned/lamp_cold.png and lamp_geo.json.
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
OUT = os.path.join(WT, "godot", "art", "ui", "lamp_life", "drowned")

ORB_D = 120.0       # the glass across at 1080
HEAD_H = 262.0      # her head's top to the screen's foot at 1080
PAD = 6             # clear round her in the quad, 1080 px
RIGHT_X = 770.0     # the quad's right edge on the screen (the hair runs on under the draught's glass)
BAR_LINE = 930.0    # the bar's top line: above it, she fades when something is behind her
CHAIN_Y = 1047.0    # the chain's row (the ring orb's eye)
GRADE = dict(value=0.72, sat=0.70, gamma=1.10)


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
    rgb = np.asarray(Image.open(os.path.join(SRC, f"cand_{SEED}.png")).convert("RGB"), np.float32) / 255
    alpha = np.asarray(Image.open(os.path.join(SRC, f"cut_{SEED}.png")).convert("RGBA"), np.float32)[..., 3] / 255
    H, W = alpha.shape
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    red = (R > 0.18) & (R > 1.9 * G) & (R > 1.6 * B)
    lab, n = ndimage.label(red)
    big = 1 + int(np.argmax(ndimage.sum(red, lab, range(1, n + 1))))
    ys, xs = np.nonzero(lab == big)
    c0 = (xs.mean(), ys.mean())
    r0 = np.sqrt(len(xs) / np.pi)
    cx, cy, r, npts = fit_circle(alpha, (xs.min(), ys.min() - int(0.6 * (ys.max() - ys.min())), xs.max(), ys.max()))
    print(f"glass: centre ({cx:.1f}, {cy:.1f}) r {r:.1f} from {npts} edge points")

    # the glass inside its edge (a px over, to take the painted rim) and her fingers over it: the bronze inside
    # the circle that joins the hand below it (not the painted speculars, which float free in the glass)
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.hypot(xx - cx, yy - cy)
    inside = d < r + 1.5
    # (the glass's blood is red over green ~3 and up; her bronze, even lit red by it, under ~2.2)
    # (and warm or green, never the smoked empty glass's violet: blue under green)
    bronze = (R / (G + 0.03) < 2.4) & (B < 0.92 * G) & (alpha > 0.5) & (np.maximum(R, G) > 0.08)
    # (the white glints are bronze-free: low chroma and bright)
    glint = (np.min(rgb, axis=2) > 0.55)
    cand = inside & bronze & ~glint
    cand = ndimage.binary_opening(cand, iterations=2)
    lab, n = ndimage.label(cand | (bronze & ~inside & (d < r + 40)))
    ring = (d > r + 2) & (d < r + 6) & (yy > cy) & bronze
    keep = set(np.unique(lab[ring])) - {0}
    finger = inside & np.isin(lab, list(keep)) & cand
    # (its holes filled, and a px wider: the painted dark outline round each finger is the finger's)
    finger = ndimage.binary_fill_holes(ndimage.binary_closing(finger, iterations=2))
    finger = ndimage.binary_dilation(finger, iterations=1) & inside
    # soft edges: 1.2 source px each way
    fs = ndimage.gaussian_filter(finger.astype(np.float32), 1.2)
    glass = np.clip((r + 1.5 - d) / 1.5, 0, 1)
    hole = glass * (1 - np.clip(fs * 1.6 - 0.3, 0, 1))
    if "--debug" in sys.argv:
        dbg = (np.dstack([finger, cand, inside]) * 255).astype(np.uint8)
        Image.fromarray(dbg).crop((0, 0, 400, 360)).save(sys.argv[sys.argv.index("--debug") + 1])
    a = alpha * (1 - hole)

    # grade: mid-low value bronze, a little less saturated (the blood reads first)
    lum = (0.3 * R + 0.59 * G + 0.11 * B)[..., None]
    g = lum + (rgb - lum) * GRADE["sat"]
    g = np.clip(g, 0, 1) ** GRADE["gamma"] * GRADE["value"]

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

    def at(x, y):
        return [round((x - x0) * s, 2), round((y - y0) * s, 2)]
    oc = at(cx, cy)
    # the level's foot: the lowest glass row her thumb leaves clear over the glass's middle half
    vis = (hole > 0.5)
    feet = []
    for x in range(int(cx - 0.45 * r), int(cx + 0.45 * r)):
        col = np.nonzero(vis[:, x])[0]
        if len(col):
            feet.append(col.max())
    foot = float(np.percentile(feet, 60)) - 2
    canvas = [round(cw, 2), round(ch, 2)]
    at_scr = [round(RIGHT_X - cw, 2), round(1080 - ch, 2)]
    geo = {
        "shape": "drowned", "seed": SEED, "canvas": canvas, "at": at_scr,
        "orb_c": oc, "orb_r": round(r * s, 2), "orb_vis": round(r * s - 0.6, 2),
        "level_foot": round((foot - y0) * s, 2),
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
