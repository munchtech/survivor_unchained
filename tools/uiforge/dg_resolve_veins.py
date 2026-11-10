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
    # the back of her head (lead 9 fix D): the bronze there is dull, so a lock's ridge dips under the floor every few px
    # and read as dashes. Inside back_box the ridges are joined along the strands before the gain, dilate and clamps.
    back_box=(598, 60, 949, 516),  # px (2x) x0, y0, x1, y1: the hair behind the front locks, down to the canvas foot (D2: was 345)
    join_gap=12,       # px (2x): a ridge is carried this far along the strand from each end (a gap of twice this closes)
    join_min=70,       # px (2x): a joined ridge shorter than this is speckle, not a lock: dropped
    join_split=345,    # px (2x): a line that starts at or below this (D2: the hair's lower strands) is judged by join_min_low
    join_min_low=40,   # px (2x): the lower strands are shorter, so 40 px not 70 (a line starting above join_split keeps join_min)
    join_seen=0.35,    # a joined ridge must already be vein over this share of its length (no vein where no strand is)
    # the weight clamp, baked as A (lead 9 fix D4; it was the shader's 72-tap loop): no vein is drawn brighter than its
    # middle clamp_px; the rest of a wide ridge is its ember edge. clamp_lo / clamp_hi are the shader's r_lo / r_hi.
    clamp_px=7.5,      # px (2x): a vein's greatest bright width (about 3 px on screen at the HUD's 0.85)
    clamp_lo=0.5, clamp_hi=0.85,
    clamp_wide=3.25,   # px (2x): in back_box the clamp acts only where a disc of this radius fits in the ridge (wider than 6.5)
    clamp_grow=4.5,    # px (2x): ... and this far round such a place (the clamp's own reach is 3.6)
    # the lone ticks (lead 10 fix B): the dark hair between the front locks and back_box holds short ridges on no line
    # (a 7 px stroke at frame (671, 947), a bright dash at (666, 990), flecks). Each lit as a lone tick. drop_lone() takes
    # them out of R before the clamp; the long lines that cross the box are never touched (they are not short).
    lone_box=(522, 20, 598, 312),  # px (2x) x0, y0, x1, y1: frame x 654-677, y 897-1005 at the HUD's 0.85; a vein must lie wholly inside
    lone_max=27,       # px (2x): a vein shorter than this (10 px on screen) ...
    lone_near=3.5,     # px (2x): ... with no longer vein within this (1.3 px on screen: nearer, it reads as that line's edge) is dropped
    # fix B2: dim ridges (R under clamp_lo, so no vein for drop_lone) that are no line, each a box x0, y0, x1, y1 (px at 2x, x1/y1 exclusive).
    # R over 0.15 inside a box goes to 0. (562, 230, 567, 245) = frame x 659.6-663.6, y 974-981: the dash beside the front loop's strand
    drop_boxes=[(562, 230, 567, 245)],
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


def thin(on):
    """Zhang-Suen thinning: a 1 px centre line of a binary shape."""
    a = np.pad(on.astype(np.uint8), 1)
    while True:
        gone = 0
        for step in (0, 1):
            n = [np.roll(a, sh, (0, 1)) for sh in ((1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1))]  # N NE E SE S SW W NW
            b = sum(n)
            t = sum((n[i] == 0) & (n[(i + 1) % 8] == 1) for i in range(8))
            if step == 0:
                c = (n[0] * n[2] * n[4] == 0) & (n[2] * n[4] * n[6] == 0)
            else:
                c = (n[0] * n[2] * n[6] == 0) & (n[0] * n[4] * n[6] == 0)
            kill = (a == 1) & (b >= 2) & (b <= 6) & (t == 1) & c
            kill[0], kill[-1], kill[:, 0], kill[:, -1] = False, False, False, False
            gone += int(kill.sum())
            a[kill] = 0
        if not gone:
            return a[1:-1, 1:-1].astype(bool)


def join_ridges(ridge, flow, hair, P):
    """The back of the head's ridges as whole lines (inside P["back_box"] only; the rest is returned as it came). The
    crest lines (the ridge's maxima across the strand) are closed along the strands' direction over join_gap, thinned,
    and the lines that are long and were mostly vein already are kept: where such a line's ridge is under the front
    locks' own level it is lifted to it, at their width (both read off the hair outside the box). The rest in the box
    (ticks on no line) is dropped."""
    vx, vy, _ = flow
    H, W = ridge.shape
    yy, xx = np.mgrid[0:H, 0:W]

    def at(a, dx, dy):
        return a[np.clip(np.rint(yy + dy).astype(int), 0, H - 1), np.clip(np.rint(xx + dx).astype(int), 0, W - 1)]

    x0, y0, x1, y1 = P["back_box"]
    box = np.zeros((H, W), bool)
    box[y0:y1, x0:x1] = True
    rs = ndimage.gaussian_filter(ridge, 1.0)
    crest = (rs >= at(rs, -vy, vx)) & (rs >= at(rs, vy, -vx)) & (ridge > 0) & (hair > 0.5)
    C = ndimage.binary_dilation(crest, structure=np.ones((3, 3), bool))
    D = C.copy()
    for k in range(1, P["join_gap"] + 1):
        D |= at(C, vx * k, vy * k) | at(C, -vx * k, -vy * k)
    E = D.copy()
    for k in range(1, P["join_gap"] + 1):
        E &= at(D, vx * k, vy * k) & at(D, -vx * k, -vy * k)
    sk = thin(E | C)
    lab, n = ndimage.label(sk, structure=np.ones((3, 3)))
    ids = np.arange(1, n + 1)
    length = ndimage.sum(sk, lab, ids)
    seen = ndimage.sum(sk & (ridge > 0), lab, ids) / np.maximum(length, 1)
    inbox = ndimage.sum(sk & box, lab, ids) / np.maximum(length, 1)
    top = np.array(ndimage.minimum(yy, lab, ids)) if n else np.zeros(0)
    lower = (inbox > 0.5) & (top >= P["join_split"])
    good = (length >= np.where(lower, P["join_min_low"], P["join_min"])) & (seen >= P["join_seen"])
    keep = np.isin(lab, ids[good])
    # the front locks' own level and half width (the lines outside the box)
    core = ridge * P["ridge_gain"] > 0.5
    ref = keep & ~box & core
    peak = float(np.median(ridge[ref]))
    hw = float(np.median(ndimage.distance_transform_edt(core)[ref]))
    lift = keep & box & (ridge < peak)
    # (+0.23: with it the lifted core measures the front locks' width after the gain and the dilate, l9_measure.py)
    prof = np.clip(hw + 0.23 - ndimage.distance_transform_edt(~lift), 0, 1) * peak
    near = ndimage.distance_transform_edt(~keep) <= hw + 2
    out = np.where(box, np.maximum(np.where(near, ridge, 0), prof), ridge)
    kb = keep & box
    print(f"join: back box {int((good & (inbox > 0.5)).sum())} lines kept (lengths {sorted(int(v) for v in length[good & (inbox > 0.5)])}), "
          f"{int(((length >= 8) & ~good & (inbox > 0.5)).sum())} short ones dropped; front level {peak:.2f}, half width {hw:.2f} px")
    print(f"join: cause: share of a kept line under the core level (R 0.5) before: back {(~core[kb]).mean() * 100:.0f}%, "
          f"front {(~core[keep & ~box]).mean() * 100:.0f}%; median ridge on the line: back {np.median(ridge[kb]):.2f}, front {np.median(ridge[keep & ~box]):.2f}")
    return out


def clamp_cover(R, P):
    """A, the vein's bright middle (1) against its ember edge (0), at the texel centers. The rule the shader ran per
    screen px until fix D4: a vein px goes if, along one of 8 lines, the vein's edge is within a of it and the vein runs
    on more than a + clamp_px the other way. New, in back_box (the joined thin veins): only on a ridge wider than the
    clamp. Run on every vein it also cut each joint of two thin veins (the px facing the joining vein has an edge ahead
    and that vein behind), so a joined lock lit as pieces. Outside back_box the rule is as it was (the front locks'
    judged weight: the same gate there lit a third more bright middle)."""
    t = np.clip((R - P["clamp_lo"]) / (P["clamp_hi"] - P["clamp_lo"]), 0, 1)
    s0 = t * t * (3 - 2 * t)
    at = lambda dx, dy: ndimage.shift(s0, (-dy, -dx), order=1, mode="nearest")
    trim = np.zeros_like(s0)
    for i in range(8):
        ox, oy = np.cos(i * 0.785398), np.sin(i * 0.785398)
        for a in (1.0, 2.2, 3.6):
            far = a + P["clamp_px"]
            trim = np.maximum(trim, (1 - at(ox * a, oy * a)) * at(-ox * far, -oy * far) * at(-ox * far * 0.5, -oy * far * 0.5))
    r = int(np.ceil(P["clamp_wide"]))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    wide = ndimage.binary_opening(s0 > 0.5, structure=(xx * xx + yy * yy) <= P["clamp_wide"] ** 2)
    x0, y0, x1, y1 = P["back_box"]
    back = np.zeros(s0.shape, bool)
    back[y0:y1, x0:x1] = True
    trim = np.where((s0 > 0.02) & (~back | (ndimage.distance_transform_edt(~wide) <= P["clamp_grow"])), trim, 0)
    print(f"clamp: {int(((trim > 0.5) & (s0 > 0.5)).sum())} vein px in an ember edge, {int(((trim <= 0.5) & (s0 > 0.5)).sum())} in a bright middle")
    return np.clip(1 - trim, 0, 1).astype(np.float32)


def drop_lone(veins, P):
    """R without its lone ticks (lead 10 fix B): a vein (R over clamp_lo, where the shader starts to light it,
    8-connected) that lies wholly in lone_box, is shorter than lone_max (the longer side of its bounds) and has no
    vein of lone_max or longer within lone_near. Its px and 2 px round them go to 0 (so cover, bright middle and
    clamp are gone at every level); px of any other vein are left as they are."""
    s8 = np.ones((3, 3), bool)
    on = veins > P["clamp_lo"]
    lab, n = ndimage.label(on, structure=s8)
    objs = ndimage.find_objects(lab)
    ln = np.array([max(s[0].stop - s[0].start, s[1].stop - s[1].start) for s in objs])
    far = ndimage.distance_transform_edt(~np.isin(lab, np.nonzero(ln >= P["lone_max"])[0] + 1))
    x0, y0, x1, y1 = P["lone_box"]
    out = veins.copy()
    for i, s in enumerate(objs, 1):
        cy0, cy1, cx0, cx1 = s[0].start, s[0].stop, s[1].start, s[1].stop
        if ln[i - 1] >= P["lone_max"] or cx0 < x0 or cx1 > x1 or cy0 < y0 or cy1 > y1:
            continue
        k = lab == i
        gap = float(far[k].min())
        if gap <= P["lone_near"]:
            print(f"lone: kept x {cx0}-{cx1} y {cy0}-{cy1} (len {ln[i - 1]}, peak {veins[k].max():.2f}): a longer vein {gap:.1f} px away")
            continue
        out[ndimage.binary_dilation(k, structure=s8, iterations=2) & ~(on & ~k)] = 0
        print(f"lone: DROPPED x {cx0}-{cx1} y {cy0}-{cy1} (len {ln[i - 1]}, peak {veins[k].max():.2f}, nearest longer vein {gap:.1f} px)")
    for bx0, by0, bx1, by1 in P.get("drop_boxes", []):
        sub = out[by0:by1, bx0:bx1]
        print(f"drop_boxes: x {bx0}-{bx1} y {by0}-{by1}: {int((sub > 0.15).sum())} px of R (peak {sub.max():.2f}) to 0")
        sub[sub > 0.15] = 0
    return out


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
    flow = strands(L, P["flow_sigma"])
    ridge = join_ridges(ridge, flow, hair, P)   # fix D: the back's broken ridges joined, then the same gain, dilate and clamps
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
    veins0 = veins                              # (the clamp of every other vein is read off R as it was, below)
    veins = drop_lone(veins, P)                 # fix B: no lone tick between the front locks and back_box
    ys, xs = np.nonzero(on)
    top = ys.min()
    band = ys < top + 6
    crown = (int(round(ys[band].mean())) + 3, int(round(xs[band].mean())))
    d = geodesic(on, crown, flow, P["along"])
    fin = np.isfinite(d)
    dmax = float(np.percentile(d[fin], P["tip_pct"]))
    g = np.where(fin, np.clip(1 - d / dmax, 0, 1), 0).astype(np.float32)
    # smoothed inside the hair (normalised blur), carried a few px past its edge so the soft mask's rim has a gauge
    w = on.astype(np.float32)
    gb = ndimage.gaussian_filter(g * w, P["g_blur"]) / np.maximum(ndimage.gaussian_filter(w, P["g_blur"]), 1e-4)
    near = ndimage.distance_transform_edt(~on, return_indices=True)[1]
    gb = np.where(on, gb, gb[near[0], near[1]])
    g = np.clip(gb, 0, 1)
    # A: the clamp, from R as the shader reads it (8 bit)
    q8 = lambda v: np.floor(np.clip(v, 0, 1) * 255 + 0.5).astype(np.float32) / 255
    core = clamp_cover(q8(veins0), P)
    if (veins != veins0).any():   # fix B: only the dropped ticks' own px take the new clamp (a line beside one keeps its judged edge)
        core = np.where(veins != veins0, clamp_cover(q8(veins), P), core)
    out = np.dstack([veins, g, hair, core])
    img = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    img.save(os.path.join(fc.OUT, "lamp_veins.png"))
    # A is data: Godot's alpha-border fix would paint R, G and B over wherever A is 0 (the ember edges)
    ip = os.path.join(fc.OUT, "lamp_veins.png.import")
    if os.path.exists(ip):
        it = open(ip, newline="").read()
        if "process/fix_alpha_border=true" in it:
            open(ip, "w", newline="").write(it.replace("process/fix_alpha_border=true", "process/fix_alpha_border=false"))
            print("veins: lamp_veins.png.import: process/fix_alpha_border set false (A is data)")
    print("veins: REIMPORT before any shot (Godot --headless --import): a game run loads the old import as it is")
    gp = os.path.join(fc.OUT, "lamp_geo.json")
    geo = json.load(open(gp))
    geo["resolve"] = {
        "tex": "lamp_veins.png", "crown": [round(crown[1] / 2, 2), round(crown[0] / 2, 2)],
        "tip_cost": round(dmax / 2, 1), **{k: v for k, v in P.items() if k != "back_box" and not k.startswith(("join_", "clamp_", "lone_", "drop_"))},   # (the join's own: bake only)
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
