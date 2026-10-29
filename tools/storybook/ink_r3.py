"""Ink round 3 (Storybook 3): p5's drowned in one hand, baked into the road layer.

    python tools/storybook/ink_r3.py init                 # CPU: layout init (clean plate + darkened round-2 figures in the
                                                          #      ditch water), the broad ditch masks, an overlay to check
    python tools/storybook/ink_r3.py gen [dn,seed ...]    # GPU: one broad-mask Krea img2img per ditch per candidate
                                                          #      (default: denoise 0.5/0.6/0.7 x seeds 11/23/47), cached
    python tools/storybook/ink_r3.py sheet                # CPU: sheet_p5_r3.jpg (one row per candidate) + 1:1 crops
    python tools/storybook/ink_r3.py crop TAG [TAG]       # CPU: 1920x1080 crop at the wide key for these candidates
    python tools/storybook/ink_r3.py seams [TAG ...]      # CPU: straight-edge scan of the drowned-vs-clean matte + every key
Ship one: set ink_layers.P5_DROWNED_R3 = "<tag>" (e.g. "d60_s23") and run `ink_layers.py build p5`.
Candidate tag: d<denoise*100>_s<seed>; its whole is _work/p5/S_drowned_r3_<tag>.png (gen px).
"""
import json
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_layers as L  # noqa: E402
import ink_r2 as R2  # noqa: E402

LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
BLACK = np.array([0x0e, 0x0d, 0x14], np.float32) / 255
NAVY = np.array([0x1c, 0x26, 0x42], np.float32) / 255
PALE = np.array([0.74, 0.78, 0.80], np.float32)

# the ditch water's centre lines (gen px), far end first
DITCH = {"left": [(585, 566), (555, 632), (482, 712), (380, 774), (292, 818), (146, 893), (0, 962)],
         "right": [(1243, 561), (1330, 640), (1389, 668), (1535, 765), (1681, 839), (1901, 897), (2048, 941)]}
COUNT = {"left": 7, "right": 8}
ROAD = [(790, 470), (1110, 470), (1430, 1088), (520, 1088)]       # the road's centre: never masked
WATER = 0.13           # the shins: the bottom of each figure fades into the ditch water
DENOISE = (0.5, 0.6, 0.7)
SEEDS = (11, 23, 47)
SCALE = 2

PROMPT_R3 = ("Grim woodcut of the drowned dead risen from the river like ghosts: dead men and women standing upright in the "
             "flooded ditches along the road, water to the shins; heads hanging forward and tilted; long lank black wet hair "
             "hanging down over their faces like curtains, in strands with river weed, only a sliver of a corpse-white face "
             "showing; thin corpse-white arms hanging limp, pale dead hands; soaked dark rags of torn linen shifts and wool tunics "
             "hanging in shreds from thin bodies; barefoot, bare shins in the black water. Motionless, waiting, every face turned "
             "toward the road. Medieval winter night, deep dark, snowy banks, frosted reeds, bare black trees. No hoods, no hats, "
             "no beards. The picture is mostly black.")
# round 4 (r2 brief): the judge read round 3 as "a procession of nuns": no robes, no belts, no folded hands, no matching poses
PROMPT = ("Grim woodcut of the drowned dead risen from the river: corpses standing in a flooded ditch at night, water to the "
          "shins, each one different, crowded unevenly, some close together, some alone, tall and short, some turned away, one "
          "leaning. Waterlogged rags of torn shirts and shifts clinging to thin dead bodies, hanging in strips, water running "
          "off the hems; bare heads, long hair plastered flat with river weed hanging over the faces, heads hung forward and "
          "tilted; arms hanging slack at their sides, pale dead hands; one or two pale hollow-eyed dead faces glimpsed between "
          "the wet hair. Lit only by cold pale blue light from the ford, rims of cold blue on wet hair and shoulders. No robes, "
          "no hoods, no belts or ropes, no folded hands, no hats, no beards, not a procession. Winter night, snowy banks, "
          "frosted reeds. Everything else is black and deep blue-black ink.")


def tag(dn, s):
    return f"d{round(dn * 100)}_s{s}"


def height(y):
    return 0.535 * (y - 354)          # perspective: the pick's figures' heights by foot height


def along(pts, t):
    """Point at fraction t of the polyline's length."""
    p = np.array(pts, np.float32)
    seg = np.hypot(*np.diff(p, axis=0).T)
    c = np.r_[0, np.cumsum(seg)]
    d = t * c[-1]
    i = min(len(seg) - 1, int(np.searchsorted(c, d, side="right") - 1))
    f = (d - c[i]) / seg[i]
    return p[i] + f * (p[i + 1] - p[i])


def darken(rgb, a):
    """Rags to near-black navy (their folds kept as navy steps); only the face and the hands stay pale."""
    hh, ww = a.shape
    l = rgb @ LUM
    pale = (l > 0.45) & (a > 0.5)
    lab, n = nd.label(pale)
    keep = np.zeros_like(pale)
    for i, sl in enumerate(nd.find_objects(lab)):
        c = lab[sl] == i + 1
        area = c.sum()
        y0, y1 = sl[0].start, sl[0].stop
        if (y0 < 0.20 * hh and y1 < 0.30 * hh and area < 0.02 * hh * hh) or (y0 > 0.25 * hh and area < 0.003 * hh * hh):
            keep[sl] |= c
    keep = nd.binary_dilation(keep, iterations=1)
    t = np.clip(l / 0.75, 0, 1)[..., None]
    dark = BLACK + (NAVY - BLACK) * t + np.clip(t - 0.8, 0, 1) * (NAVY - BLACK) * 1.5
    k = nd.gaussian_filter(keep.astype(np.float32), 0.7)[..., None]
    out = (dark * (1 - k) + rgb * k).astype(np.float32)
    # a long ragged shift to below the knee (no trouser legs): each row between the hips and the torn hem filled across
    rng = np.random.default_rng(int(a.sum()) % 7919)
    a = a.copy()
    y0 = int(0.42 * hh)
    hem = 0.74 * hh + np.repeat(rng.uniform(-0.035, 0.035, ww // 3 + 2) * hh, 3)[:ww]
    for y in range(y0, int(0.80 * hh)):
        xs = np.nonzero(a[y] > 0.5)[0]
        if len(xs) < 2:
            continue
        cols = np.arange(xs.min(), xs.max() + 1)
        cols = cols[y < hem[cols]]
        fill = a[y, cols] < 0.5
        out[y, cols[fill]] = BLACK + (NAVY - BLACK) * 0.4
        a[y, cols] = 1.0
    shin = (np.arange(hh)[:, None] >= hem[None, :] + 1) & (a > 0.5)     # bare shins below the hem, dim pale
    out[shin] = out[shin] * 0.4 + PALE * 0.35
    return hair(out, a)


def hair(rgb, a, seed=0):
    """Long wet hair plastered over the head and hanging past the shoulders in strands, a narrow pale face between
    (the cue Krea needs for 'drowned', not 'villager'). Returns (rgb, alpha) with the hair added to the alpha."""
    hh, ww = a.shape
    rng = np.random.default_rng(int(a.sum()) % 9973 + seed)
    pad = int(0.1 * ww) + 2
    a = np.pad(a, ((0, 0), (pad, pad)))
    rgb = np.pad(rgb, ((0, 0), (pad, pad), (0, 0)), mode="edge")
    rgb[a < 0.05] = BLACK
    ys, xs = np.nonzero(a[:int(0.12 * hh)] > 0.5)
    if not len(xs):
        return rgb, a
    top = ys.min()
    hx = xs.mean()
    row = np.nonzero(a[top + int(0.06 * hh)] > 0.5)[0]
    hw = float(np.clip((row.max() - row.min()) / 2 if len(row) else 0.06 * hh, 0.04 * hh, 0.07 * hh))
    im = Image.new("L", (a.shape[1], hh), 0)
    d = ImageDraw.Draw(im)
    d.ellipse([hx - 1.05 * hw, top - 0.1 * hw, hx + 1.05 * hw, top + 1.1 * hw], fill=255)       # the plastered crown
    lo = top + hh * rng.uniform(0.30, 0.40)
    for sx in (-1, 1):                                                                        # the two curtains
        d.polygon([(hx + sx * 1.05 * hw, top + 0.5 * hw), (hx + sx * 0.5 * hw, top + 0.6 * hw),
                   (hx + sx * 0.55 * hw, top + 2.3 * hw), (hx + sx * 0.5 * hw, lo - 0.05 * hh), (hx + sx * 1.25 * hw, lo + rng.uniform(-0.03, 0.03) * hh)], fill=255)
        for _ in range(3):                                                                    # loose strands
            x = hx + sx * rng.uniform(0.6, 1.2) * hw
            d.line([(x, top + hw), (x + sx * rng.uniform(-0.2, 0.3) * hw, lo + rng.uniform(0.0, 0.06) * hh)],
                   fill=255, width=max(1, int(0.18 * hw)))
    x = hx + rng.uniform(-0.3, 0.3) * hw                                                      # a strand across the face
    d.line([(x, top + 0.9 * hw), (x + rng.uniform(-0.2, 0.2) * hw, top + 2.6 * hw)], fill=255, width=max(1, int(0.14 * hw)))
    face = Image.new("L", (a.shape[1], hh), 0)      # the narrow pale dead face, turned left (the frieze's facing)
    fx = hx - 0.12 * hw
    ImageDraw.Draw(face).ellipse([fx - 0.42 * hw, top + 0.75 * hw, fx + 0.38 * hw, top + 2.2 * hw], fill=255)
    fd = ImageDraw.Draw(face)
    for ex in (-0.17, 0.13):                          # black eye sockets and a slack open jaw: a dead face, not a villager
        fd.ellipse([fx + (ex - 0.11) * hw, top + 1.12 * hw, fx + (ex + 0.11) * hw, top + 1.4 * hw], fill=0)
    fd.ellipse([fx - 0.1 * hw, top + 1.68 * hw, fx + 0.06 * hw, top + 1.98 * hw], fill=0)
    f = nd.gaussian_filter(np.asarray(face, np.float32) / 255, 0.6)
    holes = nd.gaussian_filter(((np.asarray(face) == 0) & nd.binary_fill_holes(np.asarray(face) > 0)).astype(np.float32), 0.5)
    rgb = rgb * (1 - f[..., None]) + PALE * f[..., None]
    rgb = rgb * (1 - holes[..., None]) + BLACK * holes[..., None]
    m = nd.gaussian_filter(np.asarray(im, np.float32) / 255, 0.6)
    m = m * (1 - 0.85 * f)       # the strands only thinly over the face
    rgb = rgb * (1 - m[..., None]) + BLACK * m[..., None]
    return rgb.astype(np.float32), np.maximum(a, m)


def head_ok(a):
    """A whole figure with a head on top (not a cut-off torso or a figure with a raised arm by its head)."""
    hh = a.shape[0]
    ys, xs = np.nonzero(a > 0.5)
    if not len(ys) or ys.min() > 0.03 * hh:
        return False
    row = np.nonzero(a[ys.min() + int(0.06 * hh)] > 0.5)[0]
    return len(row) > 0 and 0.05 * hh < row.max() - row.min() < 0.15 * hh


def layout():
    """[(ditch, cx, fy, h, seed, idx)] far first: 15 figures, varied spacing/height/offset, no figure used twice."""
    rng = np.random.default_rng(29)
    pool = [(s, i) for s in L.P5_SEEDS for i, f in enumerate(R2.frieze_figures(s)) if head_ok(f[1])]
    order = rng.permutation(len(pool))
    out, j = [], 0
    for k, pts in DITCH.items():
        n = COUNT[k]
        ts = np.sort(np.clip((np.arange(n) + 0.5) / n + rng.uniform(-0.28, 0.28, n) / n, 0.02, 0.97))
        for t in ts:
            x, y = along(pts, t)
            y += rng.normal(0, 8)
            h = height(y) * rng.uniform(0.86, 1.12)
            s, i = pool[order[j]]
            j += 1
            out.append((k, float(x), float(y), float(h), s, i))
    out.sort(key=lambda f: f[2])
    return out


def build_init():
    base = np.asarray(Image.open(L.wd("p5", "S_clean.png")).convert("RGB")).astype(np.float32) / 255
    H, W = base.shape[:2]
    figs = {s: R2.frieze_figures(s) for s in L.P5_SEEDS}
    canvas = base.copy()
    fig = np.zeros((H, W), np.float32)
    rng = np.random.default_rng(31)
    rects = {"left": [], "right": []}
    for k, cx, fy, h, s, i in layout():
        rgb, a, face = figs[s][i]
        rgb, a = darken(rgb, a)
        toward = 1 if k == "left" else -1
        if (face and face != toward) or (not face and rng.random() < 0.5):
            rgb, a = rgb[:, ::-1], a[:, ::-1]
        th = max(8, int(h))
        tw = max(2, int(rgb.shape[1] * th / rgb.shape[0] * rng.uniform(0.92, 1.08)))
        r = np.asarray(Image.fromarray((rgb * 255 + 0.5).astype(np.uint8)).resize((tw, th), Image.LANCZOS)).astype(np.float32) / 255
        aa = np.clip(np.asarray(Image.fromarray(a.astype(np.float32)).resize((tw, th), Image.LANCZOS)), 0, 1)
        wl = int(th * (1 - WATER))
        aa = aa * (1 - np.clip((np.arange(th) - wl) / max(1, 0.04 * th), 0, 1))[:, None]
        x0, y0 = int(cx - tw / 2), int(fy - th * (1 - WATER * 0.5))
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + tw), min(H, y0 + th)
        if xb <= xa or yb <= ya:
            continue
        al = aa[ya - y0:yb - y0, xa - x0:xb - x0, None]
        canvas[ya:yb, xa:xb] = canvas[ya:yb, xa:xb] * (1 - al) + r[ya - y0:yb - y0, xa - x0:xb - x0] * al
        fig[ya:yb, xa:xb] = np.maximum(fig[ya:yb, xa:xb], al[..., 0])
        rects[k].append((cx - 0.42 * h, fy - 1.12 * h, cx + 0.42 * h, fy + 0.14 * h))
    Image.fromarray((canvas * 255 + 0.5).astype(np.uint8)).save(L.wd("p5", "r3_init.png"))
    cart = nd.binary_dilation(L.load_mask(os.path.join(L.WORK, "p5_sam_wooden_cart.png")), iterations=14)
    road = L.poly_mask((H, W), [(x / W, y / H) for x, y in ROAD])
    allm = np.zeros((H, W), bool)
    boxes = {}
    for k, rs in rects.items():
        im = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(im)
        for r in rs:
            d.rectangle(r, fill=255)
        m = np.asarray(im) > 127
        m = nd.binary_closing(np.pad(m, 40), iterations=36)[40:-40, 40:-40]
        m = nd.binary_dilation(m, iterations=10) & ~cart & ~road
        L.save_mask(m, L.wd("p5", f"r3_mask_{k}.png"))
        ys, xs = np.nonzero(m)
        x0, y0 = max(0, xs.min() - 24) // 8 * 8, max(0, ys.min() - 24) // 8 * 8
        x1, y1 = min(W, -(-(xs.max() + 25) // 8) * 8), min(H, -(-(ys.max() + 25) // 8) * 8)
        boxes[k] = [int(x0), int(y0), int(x1), int(y1)]
        allm |= m
    L.save_mask(allm, L.wd("p5", "r3_mask.png"))
    figm = nd.binary_dilation(fig > 0.3, iterations=6) & allm
    L.save_mask(figm, L.wd("p5", "r3_fig.png"))
    json.dump(boxes, open(L.wd("p5", "r3_boxes.json"), "w"), indent=1)
    ov = (canvas * 255).astype(np.uint8)
    e = allm & ~nd.binary_erosion(allm, iterations=3)
    ov[e] = (255, 60, 60)
    Image.fromarray(ov[400:]).resize((1024, 344), Image.LANCZOS).save(L.wd("p5", "r3_init.jpg"), quality=85)
    print("init: figures", len(layout()), "boxes", boxes, "mask px", int(allm.sum()))


def recolor(img, ref, m):
    """Krea's warm sepia into the plate's night inks: its lightness matched to the init's (inside the mask) and carried
    through the ink ramp (black, navy, slate, snow, pale dead skin), so ink_post never finds parchment or rose here."""
    l = img @ LUM
    r = ref @ LUM
    sel = m > 0.5
    q = np.linspace(0, 100, 201)
    l = np.interp(l, np.percentile(l[sel], q), np.percentile(r[sel], q))
    xs = [p for p, _ in R2.RAMP]
    out = np.stack([np.interp(l, xs, [c[i] for _, c in R2.RAMP]) for i in range(3)], -1)
    # keep the init's own hue where it was the plate (the snow's blue), the ramp where figures were drawn
    plate = np.clip(ref - r[..., None] + l[..., None], 0, 1)      # the init's chroma carried additively (no ratio blow-up)
    return np.clip(0.5 * out + 0.5 * plate, 0, 1).astype(np.float32)


def soft_mask(m, s=6.0):
    return np.clip(nd.gaussian_filter(m.astype(np.float32), s) * 1.6 - 0.3, 0, 1) * nd.binary_dilation(m, iterations=2)


FEATHER = 44        # gen px: the ditch masks ramp 0 -> 1 inward over this (round 5: the old soft_mask cut its tail at ~0.33)
GROUND_IN, GROUND_RAMP = 12, 48
NEAR = 30                            # gen px: how far Krea's ground reaches past its figures     # gen px: where Krea's ground (not its figures) starts inside a ditch mask, its ramp
TONE_BAND = 110     # gen px past the feather: Krea's ground tone eased back to the clean plate's near the mask edge


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def edge_feather(m):
    """Round 5 (seam fix): (alpha, tone weight) of a ditch mask. alpha rises from exactly 0 on the mask's edge (the
    rectangles' straight sides) to 1 FEATHER px inside; the tone weight is 1 out to the feather, 0 by TONE_BAND further in."""
    e = nd.distance_transform_edt(m)
    return smooth(e / FEATHER).astype(np.float32), (1 - smooth((e - FEATHER) / TONE_BAND)).astype(np.float32)


def tone_match(small, clean, exclude, w):
    """Krea's low frequencies pulled to the clean plate's by weight w (its ink detail kept): the local mean offset taken
    over the ground only (not the figures: much darker than the plate, or the init's figure mask), sigma 14."""
    dl = (small - clean) @ LUM
    g = ((dl > -0.22) & ~exclude).astype(np.float32)
    den = nd.gaussian_filter(g, 14)
    off = np.stack([nd.gaussian_filter((small[..., i] - clean[..., i]) * g, 14) for i in range(3)], -1) / np.maximum(den, 1e-3)[..., None]
    off *= np.clip(den / 0.15, 0, 1)[..., None]
    return np.clip(small - off * w[..., None], 0, 1).astype(np.float32)


def seam_runs(img, T=6.0, MIN=40, matte=False, comp=None, plate=None):
    """Straight hard edges in an image (or a difference matte): a same-signed step > T/255 (any sign on a matte) between neighbouring px
    (2 px apart) that runs >= MIN px down one column (+-1 px) or along one row. On a matte (matte=True) only steps that
    leave the untouched plate count (one side under 2/255: a composite's edge, not Krea's own strokes); given the
    composite and the plate (luminance 0-1), only where the composite shows the step, half again over the plate's own.
    Returns (count, longest, [(dir, x, y, len)])."""
    a = img @ LUM * 255 if img.ndim == 3 else img * 255
    out = []
    for d, arr in (("v", a), ("h", a.T)):
        s = arr[:, 2:] - arr[:, :-2]
        zero = np.minimum(np.abs(arr[:, 2:]), np.abs(arr[:, :-2])) < 2 if matte else True
        if comp is not None:
            ca, pa = (q * 255 if d == "v" else q.T * 255 for q in (comp, plate))
            cs, ps = np.abs(ca[:, 2:] - ca[:, :-2]), np.abs(pa[:, 2:] - pa[:, :-2])
            zero = zero & (cs > T) & (cs > 1.5 * ps)
        for sign in ((0,) if matte else (1, -1)):                      # a matte's edge: |step| (its sign follows the content)
            b = nd.maximum_filter(((np.abs(s) if matte else sign * s) > T) & zero, size=(1, 3))
            # vertical runs per column
            pad = np.concatenate([np.zeros((1, b.shape[1]), np.int8), b.astype(np.int8), np.zeros((1, b.shape[1]), np.int8)])
            dd = np.diff(pad, axis=0)
            for x in range(b.shape[1]):
                st, en = np.nonzero(dd[:, x] == 1)[0], np.nonzero(dd[:, x] == -1)[0]
                for y0, y1 in zip(st, en):
                    if y1 - y0 >= MIN:
                        out.append((d, x + 1, int(y0), int(y1 - y0)) if d == "v" else (d, int(y0), x + 1, int(y1 - y0)))
    # neighbouring columns of one edge count once
    out.sort(key=lambda r: -r[3])
    kept = []
    for r in out:
        if not any(k[0] == r[0] and abs(k[1] - r[1]) <= 3 and abs(k[2] - r[2]) <= 3 + k[3] for k in kept):
            kept.append(r)
    return len(kept), (kept[0][3] if kept else 0), kept[:12]


def seam_check(t):
    """The drowned-vs-clean difference matte of candidate t, scanned for straight edges (round 5)."""
    clean = np.asarray(Image.open(L.wd("p5", "S_clean.png")).convert("RGB")).astype(np.float32) / 255
    img = np.asarray(Image.open(L.wd("p5", f"S_drowned_r3_{t}.png")).convert("RGB")).astype(np.float32) / 255
    n, best, runs = seam_runs((img - clean) @ LUM, matte=True)
    print(f"seam check {t}: difference matte straight edges >= 40 px: {n}, longest {best}", runs[:6])
    return n, best


def gen(cands):
    import ink_comfy as C
    import ink_gen
    init = np.asarray(Image.open(L.wd("p5", "r3_init.png")).convert("RGB")).astype(np.float32) / 255
    clean = np.asarray(Image.open(L.wd("p5", "S_clean.png")).convert("RGB")).astype(np.float32) / 255
    boxes = json.load(open(L.wd("p5", "r3_boxes.json")))
    prompt = L.full(L.PLATES["p5"]["r"], PROMPT)
    road = nd.gaussian_filter(L.load_mask(L.wd("p5", "M_road.png")).astype(np.float32), 1.5)
    init_fig = L.load_mask(L.wd("p5", "r3_fig.png"))
    for dn, s in cands:
        t = tag(dn, s)
        dst = L.wd("p5", f"S_drowned_r3_{t}.png")
        if os.path.exists(dst):
            continue
        t0 = time.time()
        out = clean.copy()
        fig = init_fig.copy()
        drawn = {}
        for k, (x0, y0, x1, y1) in boxes.items():
            w, h = (x1 - x0) * SCALE, (y1 - y0) * SCALE
            ip = L.wd("p5", f"r3_in_{k}.png")
            if not os.path.exists(ip):
                Image.fromarray((init[y0:y1, x0:x1] * 255 + 0.5).astype(np.uint8)).resize((w, h), Image.LANCZOS).save(ip)
            raw = L.wd("p5", f"r3_raw_{k}_{t}.png")
            if not os.path.exists(raw):
                C.krea(prompt, w, h, s, raw, init=ip, denoise=dn)
                side = {"generator": "Krea 2 turbo (local ComfyUI), img2img", "model": ink_gen.MODEL, "settings": ink_gen.SETTINGS,
                        "prompt": prompt, "seed": s, "size": [w, h], "init": os.path.basename(ip), "denoise": dn,
                        "made": time.strftime("%Y-%m-%d %H:%M")}
                json.dump(side, open(raw[:-4] + ".json", "w", encoding="utf-8"), indent=1)
            small = np.asarray(Image.open(raw).convert("RGB").resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(np.float32) / 255
            mk = L.load_mask(L.wd("p5", f"r3_mask_{k}.png"))
            m = soft_mask(mk)[y0:y1, x0:x1]
            small = recolor(small, init[y0:y1, x0:x1], m)
            m, tw = (a[y0:y1, x0:x1] for a in edge_feather(mk))                  # round 5: feathered from the mask's edge
            e = nd.distance_transform_edt(mk)[y0:y1, x0:x1]
            raw_small = small
            # the figures as Krea drew them (not only the init's): where it differs from the clean plate, in solid pieces
            d = nd.gaussian_filter(np.abs((small - clean[y0:y1, x0:x1]) @ LUM), 2.0) > 0.2
            d = nd.binary_fill_holes(nd.binary_closing(d, iterations=4)) & (m > 0.3)
            d = L.clean_comps(nd.binary_opening(d, iterations=2), 300)
            fig[y0:y1, x0:x1] |= nd.binary_dilation(d, iterations=3)
            # the tone match after the figure search (which keeps round 4's figure/road-layer masks)
            drawn[k] = (tone_match(raw_small, clean[y0:y1, x0:x1], init_fig[y0:y1, x0:x1], tw), e)
        # what the road layer carries: its own ground and every figure (the trees/far layers stay the clean plate)
        L.save_mask(fig, L.wd("p5", f"r3_fig_{t}.png"))
        keep = np.clip(np.maximum(road, nd.gaussian_filter(fig.astype(np.float32), 1.5)), 0, 1)
        for k, (x0, y0, x1, y1) in boxes.items():
            small, e = drawn[k]
            # round 5: near the mask's edge only the figures come from Krea (their own drawn contours, cut softly where
            # one crosses the edge); Krea's ground fades in from GROUND_IN px inside over GROUND_RAMP, the plate's outside it
            # the figures: the found pieces, and wherever Krea's (tone-matched) drawing is darker than the plate on average
            # (a dark figure over the plate's snow stripes matches the dark stripes half the time, so the piece search
            # misses it; the darkness doesn't)
            dark = nd.gaussian_filter((clean[y0:y1, x0:x1] - small) @ LUM, 3.0)
            # Krea's ground only around its figures (their shins' water, reflections): far from any, the plate's own, so
            # the hand-over follows the figures' contours instead of the mask's straight sides
            fk = fig[y0:y1, x0:x1]
            near = nd.gaussian_filter(nd.binary_dilation(fk, iterations=NEAR).astype(np.float32), NEAR / 2.5)
            a_f = np.maximum(nd.gaussian_filter(fk.astype(np.float32), 1.5) * smooth(e / FEATHER),
                             smooth((dark - 0.03) / 0.07) * smooth(e / FEATHER) * near)
            m = np.maximum(smooth((e - GROUND_IN) / GROUND_RAMP) * near * keep[y0:y1, x0:x1], a_f)
            out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - m[..., None]) + small * m[..., None]
        Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(dst)
        print("drowned r3", t, f"{time.time() - t0:.0f}s", flush=True)
        seam_check(t)


def posted(t, P=None):
    """The candidate's posted whole at target px + the lamps' glow (float)."""
    import ink_build as B
    import ink_post as IP
    P = P or B.Plate("p5")
    img = IP.post(IP.upscale(Image.open(L.wd("p5", f"S_drowned_r3_{t}.png")), P.TW, P.TH))
    for gname, gz, col in P.P["glows"]:
        g = B.glow(P, L.load_mask(L.wd("p5", f"glow_{gname}.png")), gname)
        c = np.array([int(col[j:j + 2], 16) for j in (0, 2, 4)], np.float32) / 255
        img = np.clip(img + c * g[..., None], 0, 1)
    return img, P


def crop(t, P=None):
    """The player's frame at the plate's final wide key (rest, zoom 1): 1920x1080 with the 2.39 bars."""
    img, P = posted(t, P)
    X, Y, zoom, _ = P.P["cams"][-1]
    hw, hh = 1600 / zoom / P.upp, 900 / zoom / P.upp
    im = Image.fromarray((img * 255 + 0.5).astype(np.uint8)).crop((round(X / P.upp - hw), round(Y / P.upp - hh),
                                                                    round(X / P.upp + hw), round(Y / P.upp + hh)))
    im = im.resize((1920, 1080), Image.LANCZOS)
    bar = round(1080 * (1 - L.BAND) / 2)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1920, bar], fill=(0, 0, 0))
    d.rectangle([0, 1080 - bar, 1920, 1080], fill=(0, 0, 0))
    p = os.path.join(L.OUT, f"crop_p5_r3_{t}_wide.png")
    im.save(p)
    print(p)
    return P


def key_seams(t, P=None):
    """Round 5: the candidate's posted whole vs the clean plate's, framed at each of the plate's camera keys (1920x1080
    inside the 2.39 band, as the player sees it), the difference scanned for straight edges >= 40 screen px."""
    import shutil
    cp = L.wd("p5", "S_drowned_r3_cleanref.png")
    shutil.copy(L.wd("p5", "S_clean.png"), cp)
    a, P = posted(t, P)
    b, _ = posted("cleanref", P)
    os.remove(cp)
    bar = round(1080 * (1 - L.BAND) / 2)
    res = []
    for X, Y, zoom, _ in P.P["cams"]:
        hw, hh = 1600 / zoom / P.upp, 900 / zoom / P.upp
        box = (round(X / P.upp - hw), round(Y / P.upp - hh), round(X / P.upp + hw), round(Y / P.upp + hh))
        fr = [np.asarray(Image.fromarray((q * 255 + 0.5).astype(np.uint8)).crop(box).resize((1920, 1080), Image.LANCZOS))
              .astype(np.float32)[bar + 2:1080 - bar - 2, 2:-2] / 255 for q in (a, b)]
        n, best, runs = seam_runs((fr[0] - fr[1]) @ LUM, matte=True)
        res.append((zoom, n, best))
        print(f"key seams {t} cam {X},{Y} zoom {zoom}: straight edges >= 40 px: {n}, longest {best}", runs[:4])
    return res


def sheet(cands):
    import ink_build as B
    P = None
    rows = []
    for dn, s in cands:
        t = tag(dn, s)
        if not os.path.exists(L.wd("p5", f"S_drowned_r3_{t}.png")):
            continue
        img, P = posted(t, P)
        im = B.to_im(img[P.TH // 2:]).resize((1600, round((P.TH - P.TH // 2) * 1600 / P.TW)), Image.LANCZOS)
        B.label(im, f"p5 drowned r3  {t}  (denoise {dn}, seed {s})")
        rows.append(im)
    S = Image.new("RGB", (1600, sum(r.height + 4 for r in rows)), (20, 20, 20))
    y = 0
    for r in rows:
        S.paste(r, (0, y))
        y += r.height + 4
    p = os.path.join(L.OUT, "sheet_p5_r3.jpg")
    S.save(p, quality=90)
    print(p)


def cands_from(args):
    if not args:
        return [(dn, s) for dn in DENOISE for s in SEEDS]
    return [(float(a.split(",")[0]), int(a.split(",")[1])) for a in args]


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "init":
        build_init()
    elif a == "gen":
        gen(cands_from(sys.argv[2:]))
    elif a == "seams":                                   # round 5: the straight-edge scan (gen matte + every key)
        P = None
        for t in sys.argv[2:] or [L.P5_DROWNED_R3]:
            seam_check(t)
            key_seams(t, P)
    elif a == "sheet":
        sheet(cands_from(sys.argv[2:]))
    elif a == "crop":
        P = None
        for t in sys.argv[2:]:
            P = crop(t, P)
