"""Storybook 5 fix round 3, solver B (judge r2 on p0 and p2): round-3 copies of solver AB's _sb5 layers.

    python tools/storybook/ink_sb5_r3b.py [p0] [p2]    # CPU only; writes <layer>_r3b.png beside the built ones

sb_wire_ink.py swaps them in (SB5_R3) and wires p2's new layers (branches). The _sb5 files are never touched.
Every changed or new pixel goes through ink_post at its place in the plate (the shared inks and paper).
  p0: the pale hair tuft under the letterbox (no head) darkened to the cloak; the lit wash's rose turned ~35 deg to
      ember orange (the warm-hued pixels only).
  p2: the crude pale dolmen -> p1d's SHUT gate (p1_D2_shut: jambs, rune lintel, slab, chain, gold seams) deep in the
      rock, darkened to p2's values, feathered into the strata (the old capstone and its hooked curl gone with it);
      door_glow re-cut to the gate's seams; the green pebbles -> dark stone; the warm drops (candy-corn triangles) ->
      irregular carved lumps; a new "branches" layer: the root strokes and the road's strokes to the hearth in
      ember/gold ink, revealed upward (sb_wire_ink: the light travels up to the surface, 18.8-23.8 s).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_post as IP  # noqa: E402

LY = os.path.join(HERE, "out", "ink_layers")
D2S = os.path.join(HERE, "out", "sb5", "p1_D2_shut.png")
LUMW = np.array([0.2126, 0.7152, 0.0722], np.float32)

# p2: the gate (D2_shut px) and where it goes in p2 (units = px)
GATE_SRC = (370, 70, 1100, 800)                      # the crop of p1_D2_shut taken
GATE_POLY = [(444, 124), (998, 296), (992, 384), (1018, 754), (404, 754), (428, 248)]   # jambs + lintel + slab
GATE_DST = (537, 2440)                               # the crop's top-left in p2
GATE_K = 1.5                                         # p2 units a D2 px
OLD_DOLMEN = [(612, 2560), (700, 2496), (1490, 2505), (1500, 2600), (1565, 3475), (612, 3475)]
BRANCH_ZONE = [(150, 1330), (900, 1250), (1700, 1250), (2450, 1330), (2450, 1830), (150, 1830)]
ROAD_PATH = [(1300, 1330), (1240, 1150), (1180, 990), (1130, 870)]   # the roots' top up the road to the hearth
BRANCH_BOX = (100, 820, 2500, 1900)                  # the branches layer's box (x0, y0, x1, y1)


def rgba(plate, f):
    return np.asarray(Image.open(os.path.join(LY, plate, f)).convert("RGBA")).astype(np.float32) / 255


def save(a, plate, f):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(LY, plate, f))
    print("wrote", plate, f)


def poly(shape, pts):
    m = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255)
    return np.asarray(m) > 127


def feather(m, f):
    return np.clip(nd.distance_transform_edt(m) / f, 0, 1)


def hue_rot(rgb, deg, w):
    """Rotate hue by deg where w (0-1) (Rodrigues about the gray axis: keeps lightness roughly)."""
    th = np.deg2rad(deg)
    c, s = np.cos(th), np.sin(th)
    k = 1 / 3
    sq = np.sqrt(k)
    M = np.array([[c + (1 - c) * k, k * (1 - c) - sq * s, k * (1 - c) + sq * s],
                  [k * (1 - c) + sq * s, c + k * (1 - c), k * (1 - c) - sq * s],
                  [k * (1 - c) - sq * s, k * (1 - c) + sq * s, c + k * (1 - c)]], np.float32)
    out = np.clip(rgb @ M.T, 0, 1)
    return rgb * (1 - w[..., None]) + out * w[..., None]


# ---------------------------------------------------------------- p0
HUE_SHIFT = False    # item 7 tried (+35 deg on the rose): the hand and the sill went olive-khaki, not gold; off
TUFT = (870, 165, 240, 190)    # the pale hair tuft under the letterbox (units, ellipse cx cy rx ry)


def p0():
    for f in ("dark", "lit"):
        a = rgba("p0", f + "_sb5.png")
        H, W = a.shape[:2]
        Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
        cx, cy, rx, ry = TUFT
        d = np.hypot((X - cx) / rx, (Y - cy) / ry)
        w = np.clip((1.0 - d) / 0.25, 0, 1)
        rgb = a[..., :3]
        lum = rgb @ LUMW
        dark = IP.BLACK + (rgb - IP.BLACK) * np.clip(0.055 / np.maximum(lum, 1e-3), 0, 1)[..., None]   # to the cloak's value
        rgb = rgb * (1 - w[..., None]) + np.minimum(rgb, dark) * w[..., None]
        if f == "lit" and HUE_SHIFT:   # the rose wash toward ember orange (rose-hued pixels only)
            mx, mn = rgb.max(-1), rgb.min(-1)
            sat = np.clip((mx - mn) / 0.06, 0, 1)
            # rose = red highest, blue above green (hue ~300-360): the lamp-yellows and oranges are left alone
            rose = np.clip((rgb[..., 2] - rgb[..., 1]) / 0.04 + 0.5, 0, 1) * (rgb[..., 0] >= mx - 1e-6) * sat
            rgb = hue_rot(rgb, 35, rose)
        a[..., :3] = rgb
        save(a, "p0", f + "_r3b.png")


# ---------------------------------------------------------------- p2
def gate(base):
    """The shut gate into the base; returns (gate warm-seam glow RGBA, its box)."""
    sh = np.asarray(Image.open(D2S).convert("RGB")).astype(np.float32) / 255
    x0s, y0s, x1s, y1s = GATE_SRC
    crop = sh[y0s:y1s, x0s:x1s]
    w, h = round((x1s - x0s) * GATE_K), round((y1s - y0s) * GATE_K)
    up = np.asarray(Image.fromarray((crop * 255 + 0.5).astype(np.uint8)).resize((w, h), Image.LANCZOS)).astype(np.float32) / 255
    X0, Y0 = GATE_DST
    gp = poly((h, w), [((x - x0s) * GATE_K, (y - y0s) * GATE_K) for x, y in GATE_POLY])
    warm = np.clip(((up[..., 0] - up[..., 2]) - 0.10) / 0.18, 0, 1) * (up[..., 0] > 0.3)
    warm = warm * gp
    # p2's values: the gate's stone well down (a deep gate, never a lit panel), the rock round it near black; the warm
    # seams kept
    k_stone = np.where(gp, 0.52, 0.45)[..., None]
    rgb = up * k_stone * (1 - warm[..., None]) + up * 0.95 * warm[..., None]
    post = IP.post(rgb, offset=(X0, Y0))
    H, W = base.shape[:2]
    big = np.zeros((H, W), bool)
    big[Y0:Y0 + h, X0:X0 + w] = nd.binary_dilation(gp, iterations=8)
    big |= nd.binary_dilation(poly((H, W), OLD_DOLMEN), iterations=50)   # the old outline fully under (feather 40)
    al = feather(big, 40)[Y0:Y0 + h, X0:X0 + w]
    # the feather only inside the crop's own frame (no hard crop edge): fade the last 30 px of the crop
    edge = np.minimum.reduce([np.arange(w)[None, :].repeat(h, 0), np.arange(w)[::-1][None, :].repeat(h, 0),
                              np.arange(h)[:, None].repeat(w, 1), np.arange(h)[::-1][:, None].repeat(w, 1)])
    al = al * np.clip(edge / 30, 0, 1)
    assert big[Y0:Y0 + h, X0:X0 + w].sum() == big.sum(), "p2 gate: the old dolmen reaches past the gate crop"
    base[Y0:Y0 + h, X0:X0 + w, :3] = base[Y0:Y0 + h, X0:X0 + w, :3] * (1 - al[..., None]) + post * al[..., None]
    glow = np.dstack([post * 0.55, np.clip(warm * 1.2, 0, 1) * al])
    return glow, (X0, Y0, w, h)


def green_to_stone(base):
    """The green pebbles (olive fills inside dark outlines) -> dark slate stone, their carving kept."""
    rgb = base[..., :3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    m = (g - b > 0.012) & (g - r > 0.0)
    m = nd.binary_opening(nd.binary_closing(m, iterations=2), iterations=2)
    seed = nd.binary_erosion(m, iterations=4)            # stones, not the thin thread lines
    lab, n = nd.label(m)
    keep = np.isin(lab, np.unique(lab[seed])[1:])
    keep = nd.binary_dilation(keep, iterations=2) & (g - b > -0.01)
    lum = rgb @ LUMW
    slate = np.array([0.55, 0.62, 0.95], np.float32)     # a cold dark stone (navy-slate), as the dull pebbles
    new = np.clip(lum[..., None] * 0.85 * slate / (slate @ LUMW), 0, 1)
    w = nd.gaussian_filter(keep.astype(np.float32), 1.0)[..., None]
    ys, xs = np.nonzero(keep)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    patch = rgb[y0:y1, x0:x1] * (1 - w[y0:y1, x0:x1]) + new[y0:y1, x0:x1] * w[y0:y1, x0:x1]
    post = IP.post(patch, offset=(x0, y0))
    ww = w[y0:y1, x0:x1]
    base[y0:y1, x0:x1, :3] = rgb[y0:y1, x0:x1] * (1 - ww) + post * ww
    print("p2 green stones -> dark:", n, "regions,", int(keep.sum()), "px")


def lumps(t, px, py):
    """threads_sb5's warm drops (orange, triangle-shaped) -> irregular carved lumps of the same size and heat."""
    rng = np.random.default_rng(33)
    th, tw = t.shape[:2]
    orange = (t[..., 0] - t[..., 2] > 0.28) & (t[..., 3] > 0.05)
    hot = orange & (t[..., 3] > 0.3)
    hot[:max(0, 1450 - py)] = False
    lab, n = nd.label(nd.binary_closing(hot, iterations=1))
    inks = np.array([[0.99, 0.86, 0.52], [0.98, 0.66, 0.28], [0.86, 0.45, 0.16], [0.55, 0.26, 0.10]], np.float32)
    done = 0
    for i, s in enumerate(nd.find_objects(lab)):
        comp = lab[s] == i + 1
        A = int(comp.sum())
        if A < 20 or A > 6000:
            continue
        y0, x0 = s[0].start, s[1].start
        ys, xs = np.nonzero(comp)
        cy, cx = y0 + ys.mean(), x0 + xs.mean()
        heat = float(np.clip(t[s][..., 3][comp].mean(), 0.3, 1))
        reg = nd.binary_dilation(orange[s] & comp | comp, iterations=2)
        sub = t[s]
        sub[..., 3] = np.where(reg, 0, sub[..., 3])
        # an irregular lump: a radius that wanders with the angle (low harmonics), flattened a little, turned
        R = np.sqrt(A / np.pi) * rng.uniform(0.9, 1.1)
        L = int(R * 1.6) + 3
        Y, X = np.mgrid[-L:L + 1, -L:L + 1].astype(np.float32)
        ang = rng.uniform(0, np.pi)
        sq = rng.uniform(0.72, 0.95)
        Xr, Yr = X * np.cos(ang) + Y * np.sin(ang), (-X * np.sin(ang) + Y * np.cos(ang)) / sq
        th_ = np.arctan2(Yr, Xr)
        rr = np.ones_like(th_)
        for kh in (2, 3, 5):
            rr += rng.uniform(0.04, 0.13) * np.cos(kh * th_ + rng.uniform(0, 6.28))
        d = np.hypot(Xr, Yr) / (R * rr)
        a = np.clip((1 - d) * R / 1.2, 0, 1)
        if a.sum() < 4:
            continue
        # carved bands: the hot core off-center (upper side), gouge-marked
        g = nd.gaussian_filter(rng.normal(0, 1, a.shape), (0.8, 2.5))
        g /= np.abs(g).max() + 1e-6
        v = np.clip(1 - np.hypot(X + R * 0.2, Y + R * 0.3) / (R * 1.1), 0, 1) * (0.55 + 0.45 * heat) + 0.12 * g
        band = np.select([v > 0.62, v > 0.4, v > 0.18], [0, 1, 2], 3)
        col = inks[band]
        al = a * (0.55 + 0.45 * heat)
        ty, tx = int(round(cy)) - L, int(round(cx)) - L
        if ty < 0 or tx < 0 or ty + a.shape[0] > th or tx + a.shape[1] > tw:
            continue
        dst = t[ty:ty + a.shape[0], tx:tx + a.shape[1]]
        a_new = al + dst[..., 3] * (1 - al)
        dst[..., :3] = np.where(al[..., None] > 0, (col * al[..., None] + dst[..., :3] * dst[..., 3:] * (1 - al[..., None]))
                                / np.maximum(a_new[..., None], 1e-4), dst[..., :3])
        dst[..., 3] = a_new
        done += 1
    # through the shared inks at its place (the add layer's colour only)
    t[..., :3] = IP.post(t[..., :3], offset=(px, py))
    print("p2 warm lumps:", done)


def branches(base):
    """The root strokes (light blue-gray carving in the dark ground) and the road's strokes up to the hearth, in
    ember/gold ink: a mix layer the plate reveals upward."""
    x0, y0, x1, y1 = BRANCH_BOX
    c = base[y0:y1, x0:x1, :3]
    H, W = c.shape[:2]
    lum = c @ LUMW
    zone = poly(base.shape, BRANCH_ZONE)[y0:y1, x0:x1]
    loc = nd.uniform_filter(lum, 41)
    roots = zone & (c[..., 2] > c[..., 0] + 0.02) & (lum > 0.12) & (loc < 0.26)
    roots = nd.binary_opening(roots, iterations=1)
    # the road: its carved light strokes in a corridor from the roots' top to the hearth, fading up the road
    road = np.zeros((H, W), np.float32)
    im = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(im)
    pts = [(x - x0, y - y0) for x, y in ROAD_PATH]
    for (ax, ay), (bx, by), wd in zip(pts, pts[1:], (260, 200, 140)):
        dr.line([(ax, ay), (bx, by)], fill=255, width=wd)
        dr.ellipse((bx - wd / 2, by - wd / 2, bx + wd / 2, by + wd / 2), fill=255)
    corr = nd.gaussian_filter(np.asarray(im).astype(np.float32) / 255, 30)
    stroke = np.clip((lum - 0.13) / 0.10, 0, 1) * (c[..., 0] >= c[..., 2] - 0.02)
    road = corr * stroke * np.clip(nd.distance_transform_edt(~zone) / 60, 0, 1) * 0.5   # a warm tint, soft from the roots' top
    rs = np.clip((lum - 0.10) / 0.08, 0, 1) * roots
    a = np.clip(np.maximum(rs, road), 0, 1)
    gold, ember = np.array([1.0, 0.82, 0.48], np.float32), np.array([1.0, 0.55, 0.22], np.float32)
    v = np.clip((lum - 0.12) / 0.25, 0, 1)[..., None]
    col = ember * (1 - v) + gold * v
    col = IP.post(col * (0.75 + 0.25 * v), offset=(x0, y0))
    print("p2 branches:", int((a > 0.3).sum()), "px")
    return np.dstack([col, a])


def p2():
    base = rgba("p2", "base_sb5.png")
    glow, (gx, gy, gw, gh) = gate(base)
    save(glow, "p2", "door_glow_r3b.png")
    print("p2 door_glow box", gx, gy, gw, gh)
    green_to_stone(base)
    save(base, "p2", "base_r3b.png")
    t = rgba("p2", "threads_sb5.png")
    lumps(t, 154, 1168)
    save(t, "p2", "threads_r3b.png")
    save(branches(base), "p2", "branches_r3b.png")


if __name__ == "__main__":
    for p in sys.argv[1:] or ["p0", "p2"]:
        globals()[p]()
