"""Storybook 4: SB00 p0, p1, p2, p4 from the round-6 picks (Krea 2 turbo, ink_jobs/r6_p0p4.json):
border crop, clean-up inpaints in the plate's own prompt, layers + states, layers.json in
ink_build's format (read by sb_wire_ink.py) and a contact sheet per plate.

    python tools/storybook/ink_r6.py prep  [plates]   # CPU: crop the parchment border, numeric masks
    python tools/storybook/ink_r6.py sam   [plates]   # GPU: SAM 3 masks (p1 slab, p4 willow)
    python tools/storybook/ink_r6.py fills [plates]   # GPU: Krea inpaints (cached; several seeds where a pick is needed)
    python tools/storybook/ink_r6.py build [plates]   # CPU: post, cut, layers.json, sheet

The plate entries (src, crop, target, rest, cams) are in ink_layers.PLATES (r6=True); everything
here is at the crop's own size ("gen" px) until build Lanczos-ups to the target width (1 image
px = 1 canvas unit) and posts with ink_post (one hand, one paper). Picks of inpaint seeds: R6_PICKS.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_layers as L  # noqa: E402
import ink_post as IP  # noqa: E402

JOB = json.load(open(os.path.join(HERE, "ink_jobs", "r6_p0p4.json"), encoding="utf-8"))
LUMW = np.array([0.2126, 0.7152, 0.0722], np.float32)
R6_PICKS = {"p1_lintel2": 47, "p1_curve2": 202, "p1_noslab": 11, "p0_noflame": 31, "p4_nodup": 11, "p4_behind2": 47}


def prompt(plate, old=None, new=None, *more):
    p = [j for j in JOB["jobs"] if j["name"] == plate][0]["prompt"]
    pairs = [(old, new)] + list(zip(more[::2], more[1::2])) if old else []
    for o, n in pairs:
        assert o in p, (plate, o)
        p = p.replace(o, n)
    return (JOB["prefix"] + " " + p + " " + JOB["style"]).strip()


def wd(plate, name):
    return L.wd(plate, name)


def img(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255


def crop_img(plate):
    return img(wd(plate, "crop.png"))


def box(shape, x0, y0, x1, y1):
    m = np.zeros(shape[:2], bool)
    m[int(y0):int(y1), int(x0):int(x1)] = True
    return m


# ---------------------------------------------------------------- where things are (crop px)
P1_LINTEL = (470, 990, 890, 1078)        # the lintel's lettered face
P1_OPEN = (566, 1124, 808, 1558)         # inside the doorway, between the posts (the curve)
P0_FLAME = (912, 360, 990, 552)          # the flame on the wick
P4_DUP = (2290, 200, 2480, 560)          # a second Watchman on a ladder at a far-right post


# ---------------------------------------------------------------- prep (CPU)
def prep(plate):
    P = L.PLATES[plate]
    im = Image.open(os.path.join(HERE, "out", P["src"])).convert("RGB")
    if P.get("crop"):
        l, t, r, b = P["crop"]
        im = im.crop((l, t, im.width - r, im.height - b))
    im.save(wd(plate, "crop.png"))
    a = np.asarray(im).astype(np.float32) / 255
    lum = a @ LUMW
    H, W = lum.shape
    if plate == "p0":
        x0, y0, x1, y1 = P0_FLAME
        Y, X = np.mgrid[0:H, 0:W]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        ell = ((X - cx) / ((x1 - x0) / 2)) ** 2 + ((Y - cy) / ((y1 - y0) / 2)) ** 2 <= 1
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        f = ell & ((lum > 0.5) | ((b > r + 0.08) & (lum > 0.22)))
        f = nd.binary_fill_holes(nd.binary_closing(f, iterations=2))
        lab, n = nd.label(f)
        f = lab == (1 + np.argmax(nd.sum(f, lab, range(1, n + 1))))
        L.save_mask(f, wd(plate, "flame.png"))
        L.save_mask(nd.binary_dilation(f, iterations=12), wd(plate, "fm_noflame.png"))
        print(plate, "flame px", int(f.sum()), "bbox", np.nonzero(f.any(0))[0][[0, -1]], np.nonzero(f.any(1))[0][[0, -1]])
    if plate == "p1":
        L.save_mask(box(a.shape, *P1_LINTEL), wd(plate, "fm_lintel.png"))
        L.save_mask(box(a.shape, *P1_OPEN), wd(plate, "fm_curve.png"))
    if plate == "p4":
        L.save_mask(box(a.shape, *P4_DUP), wd(plate, "fm_nodup.png"))
    print(plate, "crop", im.size)


# ---------------------------------------------------------------- SAM (GPU)
def sam(plate):
    import ink_comfy as C
    if plate == "p1":
        C.sam(wd(plate, "crop.png"), "large flat standing stone slab", wd(plate, "sam_slab.png"), 0.3)
    if plate == "p4":
        C.sam(wd(plate, "crop.png"), "willow tree", wd(plate, "sam_willow.png"), 0.3)


def slab_mask():
    m = L.load_mask(wd("p1", "sam_slab.png"))
    lab, n = nd.label(m)
    keep = np.zeros_like(m)
    for i in range(1, n + 1):       # the slab right of the opening, not the doorposts or the lintel
        ys, xs = np.nonzero(lab == i)
        if xs.mean() > P1_OPEN[2] and ys.mean() > P1_OPEN[1] and len(xs) > 2000:
            keep |= lab == i
    return nd.binary_fill_holes(keep)


def willow_mask():
    m = L.load_mask(wd("p4", "sam_willow.png"))
    H, W = m.shape
    lab, n = nd.label(m)
    keep = np.zeros_like(m)
    for i in range(1, n + 1):       # the foreground willow (centre), not the far one at right
        ys, xs = np.nonzero(lab == i)
        if xs.mean() < 0.72 * W and len(xs) > 500:
            keep |= lab == i
    return keep


# ---------------------------------------------------------------- fills (GPU)
P1_CURVE = ("inside the dark doorway, deep in the black, the smooth pale flank of something vast fills the opening: one broad curved "
            "surface of pale hide with heavy rounded ribs running across it, seen very close, curving away into the dark, glowing a "
            "faint cold pale, nothing else; ")
P1_LINTEL_T = ("a massive doorway of fitted megalith stones, its lintel a weathered plain stone block with rough chiselled faces "
               "and a few worn shallow carved marks, unreadable, no letters, no writing; ")


# round 2 (the first: faces on the lintel, an egg/boulder in the doorway)
P1_LINTEL2 = ("a massive doorway of fitted megalith stones, its lintel one long rough weathered stone block, plain, only cracks, "
              "chips and chisel marks on it, nothing carved, no symbols, no faces; ")
P1_CURVE2 = ("inside the dark doorway, filling it from side to side: the curving side of a colossal sleeping creature seen far too "
             "close, pale bone-white skin stretched over many thick parallel ribs that run across the opening in long gentle arcs "
             "with dark grooves between them, the whole surface glowing a faint cold white; ")


P4_BEHIND = ("A wide river at night seen from its near bank: dark water carved with long horizontal gouge strokes, a few dull "
             "reflections; the far bank with low black bushes and rounded dark trees; low dark hills beyond; above them the sky "
             "carved with long sweeping gouge lines, dull gold near the horizon. Empty: no lamps, no lights, no figures, no posts, "
             "no tree in the foreground.")


def fill_jobs(plate):
    """(name, init, mask, prompt, seeds)"""
    if plate == "p0":
        return [("noflame", "crop", "fm_noflame.png",
                 prompt("p0", "The small flame has just caught on the wick, warm yellow, carved as a few bold shapes, and its warm light falls "
                              "on the fingers and the stone around it.",
                        "The lamp is not lit yet: the wick is a short dark stub, nothing burning above it, only the plain dark stone wall "
                        "behind it.",
                        "The only warm color is the small yellow flame and its light; no blue in the flame.",
                        "The striker has not sparked yet; no fire anywhere."),
                 (31, 37))]
    if plate == "p1":
        old = "a massive doorway of fitted megalith stones with carved letters on its lintel; inside the dark doorway one smooth pale curved surface with ribs, part of something vast, glowing faint pale; "
        return [("lintel2", "crop", "fm_lintel.png", prompt("p1", old, P1_LINTEL2 + "inside the dark doorway a faint pale glow; "), (47, 202, 303)),
                ("curve2", "@lintel2", "fm_curve.png", prompt("p1", old, P1_LINTEL2 + P1_CURVE2), (11, 23, 47, 202)),
                ("noslab", "@curve2", "fm_noslab.png",
                 prompt("p1", "a great flat stone slab stands to the right of the doorway.",
                        "to the right of the doorway only the dark rough rock wall of the cut and stony ground, nothing standing there."),
                 (11, 23))]
    if plate == "p4":
        return [("nodup", "crop", "fm_nodup.png",
                 prompt("p4", "Right: the same kind", "Far right, only the dark weeping willow on the bank and the dark river, nobody there, no post, "
                                                      "no ladder. Right of the centre: the same kind"), (11, 23)),
                ("behind2", "@nodup", "fm_behind.png",
                 (JOB["prefix"] + " " + P4_BEHIND + " " + JOB["style"]), (23, 47))]
    return []


def run_fills(plate):
    import ink_comfy as C
    if plate == "p1" and not os.path.exists(wd(plate, "fm_noslab.png")):
        L.save_mask(nd.binary_dilation(slab_mask(), iterations=10), wd(plate, "fm_noslab.png"))
    if plate == "p4" and not os.path.exists(wd(plate, "fm_behind.png")):
        P = L.PLATES["p4"]
        ug = P["target"] / crop_img("p4").shape[1]
        mg = int(np.ceil(1.15 * margin_units("p4") / ug)) + 6
        w = willow_mask()
        keep = L.load_mask(wd(plate, "keep_watch.png"))    # the Watchman, his ladder and post stay as drawn (SAM, prep by hand)
        L.save_mask((nd.distance_transform_edt(~w) <= mg) & ~keep, wd(plate, "fm_behind.png"))
        print("p4 behind margin gen px", mg)
    for name, init, mask, pr, seeds in fill_jobs(plate):
        for s in seeds:
            dst = wd(plate, f"S_{name}_s{s}.png")
            if os.path.exists(dst):
                continue
            ini = wd(plate, "crop.png") if init == "crop" else wd(plate, f"S_{init[1:]}_s{R6_PICKS[plate + '_' + init[1:]]}.png")
            H, W = img(ini).shape[:2]
            raw = wd(plate, f"raw_{name}_s{s}.png")
            C.krea(pr, W, H, s, raw, init=ini, denoise=1.0, mask=wd(plate, mask))
            L.composite_back(ini, raw, wd(plate, mask)).save(dst)
            print(plate, name, s, flush=True)


def margin_units(plate):
    """The most a layer at z moves against the z=1 plane over the plate's camera keys (units)."""
    P = L.PLATES[plate]
    m = 0
    for z in [z for _, z in P["layers"] if z != 1]:
        for cam in P["cams"]:
            for u in (-1, 0, 1):
                a, b = L.lens_point(P["rest"], cam, z, u, 0), L.lens_point(P["rest"], cam, 1, u, 0)
                m = max(m, abs(a[0] - b[0]), abs(a[1] - b[1]))
    return m


def review(plate):
    """One small strip of the fill seeds around their masks (a working look)."""
    out = []
    for name, init, mask, _, seeds in fill_jobs(plate):
        m = L.load_mask(wd(plate, mask))
        ys, xs = np.nonzero(m)
        pad = 40
        bb = (max(0, xs.min() - pad), max(0, ys.min() - pad), xs.max() + pad, ys.max() + pad)
        ims = [Image.open(wd(plate, "crop.png") if init == "crop" else wd(plate, f"S_{init[1:]}_s{R6_PICKS[plate + '_' + init[1:]]}.png")).crop(bb)]
        ims += [Image.open(wd(plate, f"S_{name}_s{s}.png")).crop(bb) for s in seeds if os.path.exists(wd(plate, f"S_{name}_s{s}.png"))]
        h = 300
        ims = [i.resize((max(1, round(i.width * h / i.height)), h)) for i in ims]
        row = Image.new("RGB", (sum(i.width + 4 for i in ims), h), (40, 40, 40))
        x = 0
        for i in ims:
            row.paste(i, (x, 0))
            x += i.width + 4
        out.append(row)
    S = Image.new("RGB", (max(r.width for r in out), sum(r.height + 6 for r in out)), (20, 20, 20))
    y = 0
    for r in out:
        S.paste(r, (0, y))
        y += r.height + 6
    if S.width > 1600:
        S = S.resize((1600, round(S.height * 1600 / S.width)))
    S.save(os.path.join(L.OUT, f"r6_review_{plate}.jpg"), quality=85)


# ---------------------------------------------------------------- build (CPU)
class Plate:
    def __init__(self, plate):
        self.p = plate
        self.P = L.PLATES[plate]
        c = crop_img(plate)
        self.h, self.w = c.shape[:2]
        self.TW = self.P["target"]
        self.TH = round(self.h * self.TW / self.w)
        self.upp = 1.0
        self.ug = self.TW / self.w

    def S(self, name):
        return wd(self.p, "crop.png") if name == "crop" else wd(self.p, f"S_{name}_s{R6_PICKS[self.p + '_' + name]}.png")

    def posted(self, path_or_arr):
        im = path_or_arr if isinstance(path_or_arr, Image.Image) else Image.open(path_or_arr).convert("RGB")
        return IP.post(IP.upscale(im, self.TW, self.TH))

    def up(self, m, blur=0.8):
        a = np.clip(nd.gaussian_filter(m.astype(np.float32), blur), 0, 1) if blur else m.astype(np.float32)
        return np.clip(np.asarray(Image.fromarray(a).resize((self.TW, self.TH), Image.BICUBIC)), 0, 1)


def cut(rgb, alpha, pad=4):
    ys, xs = np.nonzero(alpha > 0.004)
    H, W = alpha.shape
    x0, y0, x1, y1 = max(0, xs.min() - pad), max(0, ys.min() - pad), min(W, xs.max() + pad + 1), min(H, ys.max() + pad + 1)
    a = alpha[y0:y1, x0:x1]
    return np.dstack([rgb[y0:y1, x0:x1], np.where(a < 0.004, 0, a)]), int(x0), int(y0)


def glow_rgba(T, m_full, sig, peak, col):
    """An add layer: soft glow of a mask in one colour."""
    s = T.TW / 2048
    g = sum(nd.gaussian_filter(m_full, a * s) * w for a, w in zip(sig, (1, 2.5, 5)))
    g = g / max(1e-6, np.percentile(g[m_full > 0.5], 90)) if (m_full > 0.5).any() else g
    g = np.clip(g * peak, 0, 1)
    c = np.array([int(col[j:j + 2], 16) for j in (0, 2, 4)], np.float32) / 255
    return cut(np.broadcast_to(c, g.shape + (3,)).copy(), g)


def diff_rgba(a, b, m_full):
    """An add layer that is exactly a - b (>= 0) inside m_full: colour normalised, alpha = its strength."""
    d = np.clip(a - b, 0, 1) * m_full[..., None]
    al = d.max(-1)
    rgb = np.where(al[..., None] > 1e-4, d / np.maximum(al[..., None], 1e-4), 0)
    return cut(rgb, al)


def bg_fill(a, m, sigma):
    """Normalised convolution: what lies around a mask, smeared into it."""
    w = (~m).astype(np.float32)
    num = np.dstack([nd.gaussian_filter(a[..., c] * w, sigma) for c in range(3)])
    den = nd.gaussian_filter(w, sigma)[..., None]
    return num / np.maximum(den, 1e-4)


def unlit_p0(rgb, T):
    """Dusk before the flame: the posted lit picture darkened to blue, no warm light; the window's view kept."""
    lum = rgb @ LUMW
    dark = (lum ** 1.25 * 0.55)[..., None] * np.array([0.70, 0.80, 1.12], np.float32)
    win = np.zeros((T.h, T.w), np.float32)
    win[0:425, 1150:1515] = 1          # the window's view (crop px): sky, hills, river
    win = T.up(nd.gaussian_filter(win, 10), 0)[..., None]
    out = win * rgb * np.array([0.82, 0.84, 0.92], np.float32) + (1 - win) * dark
    return np.clip(np.maximum(out, IP.BLACK * 0.9), 0, 1)


def radial_map(T, cx, cy, path, size=(512, None)):
    w = size[0]
    h = round(w * T.TH / T.TW)
    Y, X = np.mgrid[0:h, 0:w]
    d = np.hypot((X + 0.5) * T.TW / w - cx, ((Y + 0.5) * T.TH / h - cy) * 1.15)
    d = d / d.max()
    Image.fromarray((np.clip(d, 0, 1) ** 0.8 * 255).astype(np.uint8)).save(path)


def vertical_map(T, path, w=256):
    h = round(w * T.TH / T.TW)
    v = 1 - (np.arange(h) + 0.5) / h                 # dark (first) at the bottom
    rng = np.random.default_rng(3)
    n = nd.gaussian_filter(rng.normal(0, 1, (h, w)), 6)
    v = np.clip(v[:, None] + 0.04 * n / np.abs(n).max(), 0, 1)
    Image.fromarray((v * 255).astype(np.uint8)).save(path)


def build(plate):
    import ink_build as B
    T = Plate(plate)
    out = os.path.join(L.OUT, plate)
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".png"):
            os.remove(os.path.join(out, f))
    layers = []       # dict(name, z, blend, rgba, x0, y0, state, extra)

    def add(name, rgba_xy, z=1.0, blend="mix", state=None, **extra):
        rgba, x0, y0 = rgba_xy
        layers.append(dict(name=name, z=z, blend=blend, rgba=rgba, x0=x0, y0=y0, state=state, extra=extra))

    full1 = lambda rgb: (np.dstack([rgb, np.ones(rgb.shape[:2], np.float32)]), 0, 0)
    c = crop_img(plate)
    lum = c @ LUMW
    H, W = lum.shape
    if plate == "p0":
        lit = T.posted(T.S("noflame"))
        orig = T.posted(T.S("crop"))
        add("dark", full1(unlit_p0(lit, T)))
        add("lit", full1(lit))
        flame = L.load_mask(wd(plate, "flame.png"))
        fa = T.up(nd.binary_dilation(flame, iterations=2), 1.2)
        frgb = orig.copy()
        blue = (frgb[..., 2] > frgb[..., 0] + 0.03) & (fa > 0.05)      # the comps: no blue in the flame (a warm oil flame)
        warm = np.array([1.0, 0.78, 0.42], np.float32) * (frgb @ LUMW)[..., None] * 1.25
        frgb = np.where(blue[..., None], np.clip(warm, 0, 1), frgb)
        add("flame", cut(frgb, fa))
        add("glow", glow_rgba(T, T.up(flame, 0), (20, 70, 220), 0.30, "ffb35a"), blend="add")
        ys, xs = np.nonzero(T.up(flame, 0) > 0.5)
        T.flame = (float(xs.mean()), float(ys.max()), float(ys.min()))
        radial_map(T, xs.mean(), ys.mean(), os.path.join(out, "lit_map.png"))
    elif plate == "p1":
        cur = T.posted(T.S("curve2"))
        nos = img(T.S("noslab"))
        op = box(c.shape, *P1_OPEN)
        x0, y0, x1, y1 = P1_OPEN                  # the empty doorway: black, a little past the box at the sides (r7a: a
        nos[y0 + 2:y1 - 2, x0 - 4:x1 + 8] = IP.BLACK   # pale sliver of the old shell stayed at the right post)
        base = T.posted(Image.fromarray((nos * 255 + 0.5).astype(np.uint8)))
        add("base", full1(base))
        add("curve", cut(cur, T.up(op, 1.5)))
        clum = cur @ LUMW
        bright = (T.up(op, 0) > 0.5) & (clum > np.percentile(clum[T.up(op, 0) > 0.5], 70))
        add("curve_glow", glow_rgba(T, bright.astype(np.float32), (10, 40, 110), 0.22, "c9d8f2"), blend="add")
        sl = slab_mask()
        add("slab", cut(cur, T.up(sl, 0.9)))
        r_, g_, b_ = c[..., 0], c[..., 1], c[..., 2]
        fire = (r_ > 0.72) & (g_ > 0.28) & (b_ < 0.42) & (r_ > b_ + 0.3) & (lum > 0.42)
        fire = L.clean_comps(fire, 6)
        add("torches", glow_rgba(T, T.up(fire, 0), (4, 16, 50), 0.35, "ffa64a"), blend="add")
        ys, xs = np.nonzero(sl)
        T.slab = [float(xs.min() * T.ug), float(xs.max() * T.ug), float(ys.min() * T.ug), float(ys.max() * T.ug)]
        T.open = [v * T.ug for v in P1_OPEN]
    elif plate == "p2":
        gl = int(0.33 * H)                                     # below the ground line
        r_, g_, b_ = c[..., 0], c[..., 1], c[..., 2]
        thr = ((lum > 0.55) | ((r_ > 0.6) & (r_ > b_ + 0.25))) & (np.arange(H)[:, None] > gl)
        door = box(c.shape, *P2_DOOR)
        thr &= ~door
        thr = nd.binary_dilation(L.clean_comps(thr, 4), iterations=1)
        dim = c.copy()
        bg = bg_fill(c, thr, 3.0)
        dim[thr] = 0.25 * c[thr] + 0.75 * bg[thr]
        orig = T.posted(T.S("crop"))
        base = T.posted(Image.fromarray((dim * 255 + 0.5).astype(np.uint8)))
        add("base", full1(base))
        thr_up = T.up(nd.binary_dilation(thr, iterations=2), 1.0)
        add("threads", diff_rgba(orig, base, thr_up), blend="add")
        add("threads_glow", glow_rgba(T, T.up(thr, 0), (3, 10, 30), 0.22, "ffb060"), blend="add")
        lights = (r_ > 0.7) & (g_ > 0.42) & (b_ < 0.5) & (lum > 0.52) & (np.arange(H)[:, None] < gl)
        lights = L.clean_comps(lights, 4)
        add("lights", glow_rgba(T, T.up(lights, 0), (5, 20, 60), 0.4, "ffb24e"), blend="add")
        dw = door & (lum > 0.6)
        add("door_glow", glow_rgba(T, T.up(dw, 0), (8, 30, 90), 0.28, "d8e2f4"), blend="add")
        ys, xs = np.nonzero(door)
        T.door = [float(xs.mean() * T.ug), float(ys.mean() * T.ug)]
    elif plate == "p4":
        nod = T.posted(T.S("nodup"))
        add("base", full1(T.posted(T.S("behind2"))))       # the pick with the willow's place (+ margin) refilled
        wa = T.up(willow_mask(), 0.8)
        add("willow", cut(nod, wa), z=L.PLATES["p4"]["layers"][1][1])
        r_, g_, b_ = c[..., 0], c[..., 1], c[..., 2]
        flames = (lum > 0.72) & (r_ > b_ + 0.18) & (g_ > 0.55)
        flames = L.clean_comps(flames, 3)
        add("lamps", glow_rgba(T, T.up(flames, 0), (4, 14, 45), 0.4, "ffc867"), blend="add")
    # ---- files + layers.json (ink_build's format)
    rec = []
    for ly in layers:
        f = ly["name"] + ".png"
        IP.save(ly["rgba"][..., :3], os.path.join(out, f), ly["rgba"][..., 3])
        rec.append(dict(file=f, name=ly["name"], z=ly["z"], blend=ly["blend"], state=ly["state"], seed=None,
                        pos=[float(ly["x0"]), float(ly["y0"])], scale=1.0, size_px=[ly["rgba"].shape[1], ly["rgba"].shape[0]]))
    # checks: every camera key's view inside the canvas (z=1) and inside the base for nearer layers
    P = T.P
    checks = {"keys": []}
    for cam in P["cams"]:
        a, b = L.lens_point(P["rest"], cam, 1, -1, -1), L.lens_point(P["rest"], cam, 1, 1, 1)
        checks["keys"].append({"cam": cam, "clear_l_t_r_b": [round(a[0]), round(a[1]), round(T.TW - b[0]), round(T.TH - b[1])]})
    feat = {k: getattr(T, k) for k in ("flame", "slab", "open", "door") if hasattr(T, k)}
    meta = dict(plate=plate, title=L.COMPS[plate]["title"], source=P["src"], crop=P.get("crop"), canvas_units=[T.TW, T.TH],
                image_px=[T.TW, T.TH], units_per_px=1.0, rest=list(P["rest"]), features=feat, checks=checks, layers=rec,
                inpaints={k: v for k, v in R6_PICKS.items() if k.startswith(plate)})
    json.dump(meta, open(os.path.join(out, "layers.json"), "w", encoding="utf-8"), indent=1)
    print(plate, json.dumps(checks))
    # ---- sheet: the rest composite, the camera keys, the layers
    allv = sorted([ly for ly in layers], key=lambda d: -d["z"])
    SW = 1600
    rows = []
    for cam in P["cams"][:4]:
        rgb, _ = B.render(T, allv, cam, 640, 360)
        im = B.to_im(rgb)
        B.label(im, f"{plate} key x{cam[0]} y{cam[1]} zoom{cam[2]}")
        rows.append(im)
    kr = Image.new("RGB", (SW, 364), (30, 30, 30))
    for j, im in enumerate(rows[:4]):
        im = im.resize((396, 223))
        kr.paste(im, (j * 400, 0))
    cells = Image.new("RGB", (SW, 400), (30, 30, 30))
    cw = SW // max(1, len(layers)) - 4
    for j, ly in enumerate(layers):
        bg = B.checker(T.TW, T.TH, 64) if ly["blend"] == "mix" else np.full((T.TH, T.TW, 3), 0.05, np.float32)
        B.over(bg, ly["rgba"], ly["x0"], ly["y0"], add=ly["blend"] == "add")
        im = B.to_im(bg)
        im.thumbnail((cw, 396))
        B.label(im, f"{ly['name']} z{ly['z']} {ly['blend']}")
        cells.paste(im, (j * (cw + 4), 0))
    S = Image.new("RGB", (SW, kr.height + cells.height + 6), (20, 20, 20))
    S.paste(kr, (0, 0))
    S.paste(cells, (0, kr.height + 6))
    S.save(os.path.join(L.OUT, f"sheet_{plate}.jpg"), quality=86)


P2_DOOR = (326, 1094, 546, 1504)      # the buried door (crop px), its white light inside


def main():
    stage = sys.argv[1]
    plates = sys.argv[2:] or [p for p, v in L.PLATES.items() if v.get("r6")]
    for p in plates:
        if stage == "prep":
            prep(p)
        elif stage == "sam":
            sam(p)
        elif stage == "fills":
            run_fills(p)
            if fill_jobs(p):
                review(p)
        elif stage == "build":
            build(p)


if __name__ == "__main__":
    main()
