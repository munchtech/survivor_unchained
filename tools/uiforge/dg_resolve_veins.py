"""M4 (docs/design/M4_HUD.md section 2): Resolve as heat rising through the Drowned Girl's hair. Writes
godot/art/ui/lamp_life/drowned/lamp_veins.png at the figure's 2x (lamp_cold.png's size), channels:
  R  vein strength: the hair's raised ridges (dg_figure_cut.ridge_map, the bronze pass's highlights) read off the
     finished figure, inside the hair, dilated 1 px;
  G  the gauge coordinate g: geodesic distance inside the hair from the crown, 1 at the crown, 0 at the tips (so the
     front runs as an arc across the locks, never a horizontal cut);
  B  the soft hair mask (dg_figure_cut's hair_l, resampled as the figure is).
and adds a "resolve" block (the crown point in the quad's 1080 px, the params) to lamp_geo.json, its other keys kept.
hud_dg_resolve.gdshader draws it (LifeLamp's quad, ResolveVeins.cs feeds it).
Usage: python tools/uiforge/dg_resolve_veins.py [--check SHEET.png]  (the sheet: R, G, B beside the figure, half size)
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dg_figure_cut as fc  # noqa: E402

PARAMS = dict(
    mask_on=0.35,      # B above this is hair for the gauge's walk
    ridge_gain=1.6,    # R = ridge * gain, clipped
    ridge_floor=0.12,  # ridges under this are speckle: dropped
    dilate=1,          # px (2x) the veins grow
    g_blur=4.0,        # px (2x): the gauge smoothed inside the hair (no stair steps at the front)
    tip_pct=99.0,      # the geodesic distance at this percentile is g 0 (the farthest specks don't set the scale)
    along=0.55,        # a step along the strands costs this much less (the front runs up the locks, not as a cut)
    flow_sigma=6.0,    # px (2x): the strands' direction smoothed over this
)


def resample(src, info):
    """A source-px float map onto the 2x canvas, as dg_figure_cut resamples the figure."""
    im = Image.fromarray(src.astype(np.float32), "F")
    return np.asarray(im.resize(info["size"], Image.BILINEAR, box=info["box"]), np.float32)


def strands(L, sigma):
    """The strands' direction (unit, along them) and its coherence 0..1, from the bronze's structure tensor (as
    dg_figure_cut.strand_pass reads it)."""
    import cv2
    Ls = cv2.GaussianBlur(L, (0, 0), 1.5)
    ix, iy = cv2.Sobel(Ls, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(Ls, cv2.CV_32F, 0, 1, ksize=3)
    j11, j22, j12 = (cv2.GaussianBlur(v, (0, 0), sigma) for v in (ix * ix, iy * iy, ix * iy))
    phi = 0.5 * np.arctan2(2 * j12, j11 - j22)          # across the strands
    coh = np.sqrt((j11 - j22) ** 2 + 4 * j12 ** 2) / np.maximum(j11 + j22, 1e-6)
    return -np.sin(phi), np.cos(phi), np.clip(coh, 0, 1)


def geodesic(mask, seed, flow=None, along=0.0):
    """Distance (px) inside mask from seed (y, x), 16-connected (no octagon facets); inf where unreachable. flow
    (vx, vy, coherence): a step along the strands costs up to `along` less, so the front runs up the locks."""
    H, W = mask.shape
    idx = -np.ones((H, W), np.int64)
    ys, xs = np.nonzero(mask)
    idx[ys, xs] = np.arange(len(ys))
    rows, cols, wts = [], [], []
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1), (1, 2), (2, 1), (1, -2), (2, -1)):
        y2, x2 = ys + dy, xs + dx
        ok = (y2 >= 0) & (y2 < H) & (x2 >= 0) & (x2 < W)
        y1_, x1_, y2, x2 = ys[ok], xs[ok], y2[ok], x2[ok]
        a, b = idx[y1_, x1_], idx[y2, x2]
        k = b >= 0
        ln = np.hypot(dy, dx)
        wt = np.full(k.sum(), ln, np.float32)
        if flow is not None and along > 0:
            vx, vy, coh = flow
            ux = (vx[y1_[k], x1_[k]] + vx[y2[k], x2[k]] * np.sign(vx[y1_[k], x1_[k]] * vx[y2[k], x2[k]] + vy[y1_[k], x1_[k]] * vy[y2[k], x2[k]] + 1e-6))
            uy = (vy[y1_[k], x1_[k]] + vy[y2[k], x2[k]] * np.sign(vx[y1_[k], x1_[k]] * vx[y2[k], x2[k]] + vy[y1_[k], x1_[k]] * vy[y2[k], x2[k]] + 1e-6))
            un = np.maximum(np.hypot(ux, uy), 1e-6)
            c = np.abs(ux * dx + uy * dy) / (un * ln)
            ch = 0.5 * (coh[y1_[k], x1_[k]] + coh[y2[k], x2[k]])
            wt = wt * (1 - along * ch * c * c)
        rows.append(a[k]); cols.append(b[k]); wts.append(wt)
    r, c, w = np.concatenate(rows), np.concatenate(cols), np.concatenate(wts)
    n = len(ys)
    g = coo_matrix((w, (r, c)), shape=(n, n)).tocsr()
    s = idx[seed]
    if s < 0:
        d2 = (ys - seed[0]) ** 2 + (xs - seed[1]) ** 2
        s = int(np.argmin(d2))
    d = dijkstra(g, directed=False, indices=s)
    out = np.full((H, W), np.inf, np.float32)
    out[ys, xs] = d
    return out


def main():
    check = sys.argv[sys.argv.index("--check") + 1] if "--check" in sys.argv else None
    P = PARAMS
    info = fc.main(info_only=True)
    cold = np.asarray(Image.open(os.path.join(fc.OUT, "lamp_cold.png")).convert("RGBA"), np.float32) / 255
    assert cold.shape[1] == info["size"][0] and cold.shape[0] == info["size"][1], "lamp_cold.png is not this cut's size"
    oa = cold[..., 3]
    # B: the hair mask on the canvas (only where the finished figure stands)
    hair = np.clip(resample(info["hair_l"], info), 0, 1) * np.clip(oa * 1.2, 0, 1)
    # R: the ridges of the finished figure (its painted patches too), the bronze pass's own map at the 2x scale
    L = (0.3 * cold[..., 0] + 0.59 * cold[..., 1] + 0.11 * cold[..., 2]).astype(np.float32)
    k = 2 * info["s"]                          # 2x canvas px per source px
    _, ridge = fc.ridge_map(L, k)
    ridge = np.where(ridge > P["ridge_floor"], ridge, 0)
    veins = np.clip(ridge * P["ridge_gain"], 0, 1) * hair
    if P["dilate"]:
        veins = ndimage.grey_dilation(veins, size=(2 * P["dilate"] + 1,) * 2)
    veins *= np.clip(hair * 2, 0, 1)
    # G: the crown = the hair's topmost point (the middle of its top row band)
    on = hair > P["mask_on"]
    on = ndimage.binary_opening(on, iterations=1)
    lab, n = ndimage.label(on)
    if n > 1:   # the main body of hair only
        sizes = ndimage.sum(on, lab, range(1, n + 1))
        on = lab == (1 + int(np.argmax(sizes)))
    body = ndimage.binary_dilation(on, iterations=6)
    hair *= body
    veins *= body
    ys, xs = np.nonzero(on)
    top = ys.min()
    band = ys < top + 6
    crown = (int(round(ys[band].mean())) + 3, int(round(xs[band].mean())))
    d = geodesic(on, crown, strands(L, P["flow_sigma"]), P["along"])
    fin = np.isfinite(d)
    dmax = float(np.percentile(d[fin], P["tip_pct"]))
    g = np.where(fin, np.clip(1 - d / dmax, 0, 1), 0).astype(np.float32)
    # smoothed inside the hair (normalised blur), carried a few px past its edge so the soft mask's rim has a gauge
    w = on.astype(np.float32)
    gb = ndimage.gaussian_filter(g * w, P["g_blur"]) / np.maximum(ndimage.gaussian_filter(w, P["g_blur"]), 1e-4)
    near = ndimage.distance_transform_edt(~on, return_indices=True)[1]
    gb = np.where(on, gb, gb[near[0], near[1]])
    g = np.clip(gb, 0, 1)
    out = np.dstack([veins, g, hair])
    img = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
    img.save(os.path.join(fc.OUT, "lamp_veins.png"))
    gp = os.path.join(fc.OUT, "lamp_geo.json")
    geo = json.load(open(gp))
    geo["resolve"] = {
        "tex": "lamp_veins.png", "crown": [round(crown[1] / 2, 2), round(crown[0] / 2, 2)],
        "tip_cost": round(dmax / 2, 1), **P,
    }
    json.dump(geo, open(gp, "w"), indent=1)
    print(f"veins: {img.size[0]}x{img.size[1]} crown (1080 px in the quad) {geo['resolve']['crown']} tips at {dmax / 2:.0f} px")
    print(f"veins: hair {on.mean() * 100:.1f}% of the quad, veins >0.5 {(veins > 0.5).sum() / max(on.sum(), 1) * 100:.1f}% of the hair")
    if check:
        Hh, Ww = g.shape
        sheet = Image.new("RGB", (Ww * 2, Hh * 2), (40, 38, 46))
        fig = Image.new("RGBA", (Ww, Hh), (60, 58, 70, 255))
        fig.alpha_composite(Image.open(os.path.join(fc.OUT, "lamp_cold.png")).convert("RGBA"))
        sheet.paste(fig.convert("RGB"), (0, 0))
        for i, (ch, at) in enumerate(((veins, (Ww, 0)), (g * (hair > 0.05), (0, Hh)), (hair, (Ww, Hh)))):
            sheet.paste(Image.fromarray((np.clip(ch, 0, 1) * 255).astype(np.uint8), "L").convert("RGB"), at)
        # the gauge's isolines over G (every 0.1), so an arc reads as an arc
        sg = np.asarray(sheet).copy()
        iso = (np.abs((g * 10) - np.round(g * 10)) < 0.06) & (hair > 0.2)
        yy, xx = np.nonzero(iso)
        sg[yy + Hh, xx] = (255, 80, 40)
        cy, cx = crown
        sg[max(0, cy - 4 + Hh):cy + 5 + Hh, max(0, cx - 4):cx + 5] = (60, 160, 255)
        Image.fromarray(sg).resize((Ww, Hh), Image.LANCZOS).save(check)
        print(f"check sheet: {check}")


if __name__ == "__main__":
    main()
