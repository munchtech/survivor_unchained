"""Storybook 4 round 5: p5 own-canvas candidates (ink_jobs/r5_p5.json), the p7u basket, p7's water under the traveler.

    python tools/storybook/ink_r5.py p7u_prep              # init (cage painted out) + mask for ink_jobs/r5_p7u.json
    python tools/storybook/ink_r5.py post_p5               # post every out/ink_r5/p5r5*.png at 3600 + contact sheet
    python tools/storybook/ink_r5.py campath <name> [...]  # 4 simulated 1:1 game frames (letterboxed) per pick
    python tools/storybook/ink_r5.py p7_water              # fill out/ink_layers/p7/water.png under the traveler
    python tools/storybook/ink_r5.py p7_sim <t> [...]      # p7 at plate time t through the lens (debug)
Camera units (sb_wire_ink.Plate.cam): a frame shows 3200/zoom x 1800/zoom canvas units; the band 1339/zoom.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
R5 = os.path.join(OUT, "ink_r5")
BAND = 1339 / 1800

# p5 staging for the camera sheet: (t, x, y, zoom) in the posted plate's px (3600 wide = canvas units).
# Per pick the ford/fourth-light point is set in P5_FORD (posted px); default the comps' (1880, 700).
P5_FORD = {"p5r5c_s47_nc": (1795, 560), "p5r5a_s202_nc": (1300, 700)}


def font(sz):
    try:
        return ImageFont.truetype("arial.ttf", sz)
    except OSError:
        return ImageFont.load_default()


def p7u_prep():
    src = os.path.join(OUT, "ink_r4_p7", "p7u4_s47.png")
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    H, W = im.shape[:2]
    yy, xx = np.mgrid[:H, :W]
    cx, cy, rx, ry = 985, 300, 150, 170
    m = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
    ring = (((xx - cx) / (rx + 40)) ** 2 + ((yy - cy) / (ry + 40)) ** 2 <= 1) & ~m
    lum = im.mean(-1)
    glare = np.median(im[ring & (lum > np.median(lum[ring]))], axis=0)
    init = im.copy()
    init[m] = glare
    soft = nd.gaussian_filter(m.astype(np.float32), 12)
    init = im * (1 - soft[..., None]) + init * soft[..., None]
    os.makedirs(R5, exist_ok=True)
    Image.fromarray(init.clip(0, 255).astype(np.uint8)).save(os.path.join(R5, "_p7u_init.png"))
    mk = nd.binary_dilation(m, iterations=10)
    Image.fromarray((mk * 255).astype(np.uint8)).save(os.path.join(R5, "_p7u_mask.png"))
    print("p7u init + mask", glare)


def post_one(src, dst, w=3600, light="warm"):
    import ink_post
    if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(src):
        return
    ink_post.save(ink_post.post(ink_post.upscale(Image.open(src), w), light=light), dst)


def post_p5():
    names = sorted(f[:-4] for f in os.listdir(R5) if f.startswith("p5r5") and f.endswith(".png") and "_post" not in f)
    os.makedirs(os.path.join(R5, "posted"), exist_ok=True)
    tiles = []
    for n in names:
        dst = os.path.join(R5, "posted", n + ".png")
        post_one(os.path.join(R5, n + ".png"), dst)
        tiles.append((n, Image.open(dst).resize((900, 475), Image.LANCZOS)))
    for f in sorted(os.listdir(os.path.join(R5, "posted"))):   # the night-toned + cold-light posts (ink_r5.py night)
        if f.endswith("_nc.png"):
            tiles.append((f[:-4] + "  (night tone + cold light)", Image.open(os.path.join(R5, "posted", f)).resize((900, 475), Image.LANCZOS)))
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 900 + (cols + 1) * 10, rows * 505 + 10), "#202020")
    d = ImageDraw.Draw(sheet)
    for i, (n, t) in enumerate(tiles):
        x, y = 10 + (i % cols) * 910, 10 + (i // cols) * 505
        sheet.paste(t, (x, y))
        d.text((x, y + 478), n, fill="#e0e0e0", font=font(22))
    p = os.path.join(R5, "p5r5_sheet_half.jpg")
    sheet.save(p, quality=90)
    print(p)


def frame(img, x, y, zoom, label=None):
    """A 1920x1080 game frame of a canvas-unit image centred (x, y) at zoom, letterboxed to 2.39."""
    w, h = 3200 / zoom, 1800 / zoom
    box = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    f = img.crop(tuple(round(v) for v in box)).resize((1920, 1080), Image.LANCZOS)
    bar = round(1080 * (1 - BAND) / 2)
    d = ImageDraw.Draw(f)
    d.rectangle((0, 0, 1920, bar), fill="black")
    d.rectangle((0, 1080 - bar, 1920, 1080), fill="black")
    if label:
        d.text((20, 20), label, fill="#c0c0c0", font=font(30))
    return f


def p5_keys(name):
    fx, fy = P5_FORD.get(name, (1880, 700))
    return [(0.0, fx - 60, fy + 10, 1.55, "open close on the ford + fourth light"),
            (6.5, fx, fy, 1.6, "end of the slow push"),
            (10.5, (fx + 1800) / 2, (fy + 1000) / 2 + 30, 1.25, "pulling back up the road"),
            (14.5, 1800, 1000, 1.0, "the full wide: the drowned")]


def campath(names):
    for n in names:
        img = Image.open(os.path.join(R5, "posted", n + ".png")).convert("RGB")
        fr = [frame(img, x, y, z, f"{n}  t={t:.1f}s (56+)  zoom {z}  {lab}") for t, x, y, z, lab in p5_keys(n)]
        sheet = Image.new("RGB", (1920 * 2 + 10, 1080 * 2 + 10), "#202020")
        for i, f in enumerate(fr):
            sheet.paste(f, ((i % 2) * 1930, (i // 2) * 1090))
        p = os.path.join(R5, f"{n}_campath_half.jpg")
        sheet.resize((sheet.width // 2, sheet.height // 2), Image.LANCZOS).save(p, quality=90)
        os.makedirs(os.path.join(R5, "frames"), exist_ok=True)
        for i, f in enumerate(fr):
            f.save(os.path.join(R5, "frames", f"{n}_f{i}.png"))
        print(p)


# ---------------------------------------------------------------- p7: the water under the traveler
def _row_mirror(img, m):
    """Each masked run of each row filled by mirroring the unmasked pixels beyond its right end (left end at the edge)."""
    out = img.copy()
    H, W = m.shape
    for y in range(H):
        row = m[y]
        if not row.any():
            continue
        xs = np.flatnonzero(np.diff(np.concatenate([[0], row.astype(np.int8), [0]])))
        for a, b in zip(xs[::2], xs[1::2]):   # run [a, b)
            n = b - a
            if b < W:
                src = b + (b - 1 - np.arange(a, b))              # mirror about b - 0.5
                src = np.where(src >= W, (W - 1) - (src - W) % W, src)
                src = np.where(m[y, np.clip(src, 0, W - 1)], np.clip(b + (np.arange(n) % max(1, W - b)), 0, W - 1), src)
            else:
                src = (a - 1) - (np.arange(a, b) - a)
                src = np.clip(src, 0, W - 1)
            out[y, a:b] = img[y, np.clip(src, 0, W - 1)]
    return out


def p7_water():
    d = os.path.join(OUT, "ink_layers", "p7")
    meta = json.load(open(os.path.join(d, "layers.json"), encoding="utf-8"))
    water_e = [e for e in meta["layers"] if e["name"] == "water"][0]
    trav_e = [e for e in meta["layers"] if e["file"] == "traveler.png"][0]
    bak = os.path.join(d, "_water_before_r5.png")
    if not os.path.exists(bak):
        Image.open(os.path.join(d, "water.png")).save(bak)
    w = np.asarray(Image.open(bak).convert("RGBA")).copy()
    t = np.asarray(Image.open(os.path.join(d, "traveler.png")).convert("RGBA"))
    sc = water_e["scale"]
    ox, oy = round(trav_e["pos"][0] / sc), round(trav_e["pos"][1] / sc)
    m = np.zeros(w.shape[:2], bool)
    th, tw = t.shape[:2]
    m[oy:oy + th, ox:ox + tw] = t[..., 3] > 12
    m = nd.binary_dilation(m, iterations=4)
    filled = _row_mirror(w[..., :3], m)
    # a soft 3-px vertical blend so mirrored rows don't stair-step
    sm = nd.uniform_filter(filled.astype(np.float32), size=(3, 1, 1))
    filled = np.where(m[..., None], sm, filled).astype(np.uint8)
    w[..., :3] = np.where(m[..., None], filled, w[..., :3])
    Image.fromarray(w, "RGBA").save(os.path.join(d, "water.png"))
    print("p7 water: filled", int(m.sum()), "px under the traveler")


def p7_sim(times):
    """p7 through the lens at plate times (sb_wire_ink's camera): every base layer + blue_rim, keys ignored except opacity-0."""
    import sb_wire_ink as W
    picks = json.load(open(W.PICKS, encoding="utf-8"))
    P, plate = W.plate_p7(picks.get("p7", {}))
    cams = plate["camera"]
    shift = P.shift
    lay = sorted(plate["layers"], key=lambda L: -L["z"])
    srcs = {L["id"]: os.path.join(W.LAYERS, "p7", P.used[L["id"] + ".png"]) for L in lay}
    for t in times:
        # camera at t (piecewise linear, ignoring ease)
        k = [(c["t"], (c["x"], c["y"], c["zoom"])) for c in cams]
        X, Y, Z = [W.pw([(a, v[i]) for a, v in k], t) for i in range(3)]
        R = (1600, 900)
        f = Image.new("RGB", (1920, 1080), "black")
        for L in lay:
            ks = L.get("keys")
            op = W.pw([(q["t"], q.get("opacity", 1)) for q in ks], t) if ks and "opacity" in ks[0] else 1
            if op <= 0.01:
                continue
            z = L["z"]
            im = Image.open(srcs[L["id"]]).convert("RGBA")
            # screen px -> layer canvas: c = R + (cam - R)/z + (s - centre) * units_per_px
            upp = 3200 / Z / 1920
            cx, cy = R[0] + (X - R[0]) / z, R[1] + (Y - R[1]) / z
            x0, y0 = cx - 960 * upp, cy - 540 * upp
            sc = L["scale"]
            px0, py0 = (x0 - L["pos"][0]) / sc, (y0 - L["pos"][1]) / sc
            pw_ = 1920 * upp / sc
            ph_ = 1080 * upp / sc
            crop = im.transform((1920, 1080), Image.EXTENT, (px0, py0, px0 + pw_, py0 + ph_), Image.BILINEAR)
            if op < 1:
                a = np.asarray(crop).copy()
                a[..., 3] = (a[..., 3] * op).astype(np.uint8)
                crop = Image.fromarray(a)
            if L.get("blend") == "add":
                a = np.asarray(crop).astype(np.float32)
                base = np.asarray(f).astype(np.float32)
                f = Image.fromarray(np.clip(base + a[..., :3] * a[..., 3:] / 255, 0, 255).astype(np.uint8))
            else:
                f.paste(crop.convert("RGB"), (0, 0), crop)
        p = os.path.join(R5, f"p7_sim_{t:.2f}.jpg")
        os.makedirs(R5, exist_ok=True)
        f.resize((960, 540), Image.LANCZOS).save(p, quality=90)
        print(p, (round(X), round(Y), round(Z, 2)))


def night(src, dst, k=0.5, reach=70):
    """The night tone step before the post: everything sinks to k of its light except pools round the blue fires
    (saturated blue or blue-white cores, blurred out to ~reach gen px), so snow posts as dim blue-gray, not parchment."""
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255
    l = im.mean(-1)
    fire = ((im[..., 2] - im[..., 0] > 0.10) & (l > 0.5)) | (l > 0.93)
    fire = nd.binary_opening(fire, iterations=1)
    pool = nd.gaussian_filter(nd.binary_dilation(fire, iterations=6).astype(np.float32), reach)
    pool = np.clip(pool / max(1e-6, np.quantile(pool[fire], 0.5) if fire.any() else 1), 0, 1)
    g = k + (1 - k) * pool
    out = im * g[..., None]
    Image.fromarray((out.clip(0, 1) * 255 + 0.5).astype(np.uint8)).save(dst)


def post_night(names, k=0.7, light="cold", tag="nc"):
    """Night tone + ink_post's cold light step (p7u's): lights go snow / cage blue / ice, never parchment or rose."""
    os.makedirs(os.path.join(R5, "posted"), exist_ok=True)
    for n in names:
        tmp = os.path.join(R5, "_night_" + n + ".png")
        night(os.path.join(R5, n + ".png"), tmp, k)
        dst = os.path.join(R5, "posted", f"{n}_{tag}.png")
        if os.path.exists(dst):
            os.remove(dst)
        post_one(tmp, dst, light=light)
        print(n + "_" + tag)


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "p7u_prep":
        p7u_prep()
    elif a == "post_p5":
        post_p5()
    elif a == "campath":
        campath(sys.argv[2:])
    elif a == "night":
        post_night(sys.argv[2:])
    elif a == "p7_water":
        p7_water()
    elif a == "p7_sim":
        p7_sim([float(x) for x in sys.argv[2:]])
