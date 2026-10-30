"""Storybook 5 patch, solver AB (judge r1 fixes on p0, p2, p6, p7, p7u): patched copies of the built layers.

    python tools/storybook/ink_sb5_ab.py gpu      # Krea inpaints (cached, out/ink_sb5ab/): crop x k, inpaint, back, posted
    python tools/storybook/ink_sb5_ab.py sheet    # candidates beside the original, half size
    python tools/storybook/ink_sb5_ab.py apply    # CPU: writes <layer>_sb5.png (+ new layers) beside the built ones

The originals in out/ink_layers/<plate>/ are never touched; sb_wire_ink.py swaps in the _sb5 files (SB5_AB there).
Every changed pixel goes through ink_post (the shared inks and paper) at its place in the plate's posted image.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_post as IP  # noqa: E402

LY = os.path.join(HERE, "out", "ink_layers")
OUT = os.path.join(HERE, "out", "ink_sb5ab")
R2 = json.load(open(os.path.join(HERE, "ink_jobs", "r2.json"), encoding="utf-8"))
PRE, STY = R2["prefix"], R2["style"]
LUMW = np.array([0.2126, 0.7152, 0.0722], np.float32)


def rgba(plate, f):
    return np.asarray(Image.open(os.path.join(LY, plate, f)).convert("RGBA")).astype(np.float32) / 255


def save(a, plate, f):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(LY, plate, f))


def ells(shape, es):
    m = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(m)
    for cx, cy, rx, ry in es:
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    return np.asarray(m) > 127


def door_mask(c):
    """The open doorway's white light (the opening), in a p2 base crop."""
    lum = c[..., :3] @ LUMW
    m = nd.binary_opening(lum > 0.62, iterations=2)
    lab, n = nd.label(m)
    big = np.argmax(nd.sum(m, lab, range(1, n + 1))) + 1
    return nd.binary_fill_holes(nd.binary_closing(lab == big, iterations=6))


def p7_wedge_mask(c, box):
    """The flat pale wedge and the disk: the whole box but the traveler as seen at 82.2 (traveler px = water + (32, -426))."""
    t = rgba("p7", "traveler.png")[..., 3]
    x0, y0, x1, y1 = box
    a = t[y0 - 426:y1 - 426, x0 + 32:x1 + 32] > 0.5
    return ~nd.binary_dilation(a, iterations=3)


# name, plate, layer, crop box (layer px), mask (ellipses or fn(crop) -> bool), prompt, denoise, seeds, light, k
JOBS = [
    ("door", "p2", "base.png", (800, 2560, 1300, 3562), door_mask,
     "Night. A buried megalith doorway of rough dark standing stones, SHUT: one plain flat rectangular stone slab fills the "
     "whole opening from post to post, dark gray carved stone with chisel marks and cracks, closed tight. Thin hairline seams "
     "of gold light leak only along the slab's edges. No opening, no white light, no door handle.", 1.0, (11, 47), "warm", 1.5),
    ("lintel", "p2", "base.png", (1260, 2440, 1560, 2760), [(1410, 2610, 80, 95)],
     "The squared rough end of a long plain stone lintel block: a flat chiselled stone face with cracks and chisel marks, dark "
     "gray stone. No spiral, no wood grain, no log end, no rings.", 0.85, (11, 47), "warm", 3),
    ("hearth", "p2", "base.png", (1000, 740, 1240, 920), [(1108, 828, 48, 40)],
     "Inside a stone hearth a bright fire: tall carved flames of gold and pale yellow over glowing logs, the flames clean, "
     "nothing dark in them.", 0.8, (11, 47), "warm", 3),
    ("cart", "p2", "base.png", (1700, 580, 2080, 860), [(1890, 718, 122, 64)],
     "On a wooden handcart, a heaped load of glowing ember stones: rough jagged lumps of rock glowing hot gold and orange from "
     "within, bright gold-white cracks, hard angular shapes, not fruit, not round.", 0.75, (11, 47), "warm", 3),
    ("stall", "p2", "base.png", (1220, 760, 1560, 960), [(1392, 868, 104, 32)],
     "On a market stall table, a row of glowing ember stones: rough jagged lumps of rock glowing hot gold and orange from "
     "within, bright gold-white cracks, hard angular shapes, not fruit, not bread.", 0.75, (11, 47), "warm", 3),
    ("wedge", "p7", "water.png", (880, 2150, 1340, 2640), p7_wedge_mask,
     "Night, cold blue moonlight. Wet dark stones at the river's edge: flat slabs of wet black stone and pebbles carved with "
     "short gouge strokes, small glints of cold blue on their wet tops, black water between them.", 1.0, (11, 47), "cold", 2),
    ("blot", "p0", "lit.png", (2300, 900, 2720, 1200), [(2502, 1055, 140, 92)],
     "The flat top of a weathered stone window sill lit warm by a small lamp: rough flat stone, cracks and chisel marks, "
     "nothing on it.", 1.0, (11, 47), "warm", 2.5),
]


def cand(name, seed):
    return os.path.join(OUT, f"{name}_s{seed}.png")


def gpu():
    import ink_comfy as C
    os.makedirs(OUT, exist_ok=True)
    for name, plate, f, box, mspec, prompt, dn, seeds, light, k in JOBS:
        img = rgba(plate, f)
        x0, y0, x1, y1 = box
        crop = img[y0:y1, x0:x1]
        m = mspec(crop, box) if mspec is p7_wedge_mask else (mspec(crop) if callable(mspec) else ells(img.shape, mspec)[y0:y1, x0:x1])
        md = nd.binary_dilation(m, iterations=6)
        np.save(os.path.join(OUT, f"_{name}_mask.npy"), md)
        cw, ch = int((x1 - x0) * k) // 16 * 16, int((y1 - y0) * k) // 16 * 16
        ci, mi = os.path.join(OUT, f"_{name}_crop.png"), os.path.join(OUT, f"_{name}_mask.png")
        Image.fromarray((crop[..., :3] * 255 + 0.5).astype(np.uint8)).resize((cw, ch), Image.LANCZOS).save(ci)
        Image.fromarray((md * 255).astype(np.uint8)).resize((cw, ch), Image.NEAREST).save(mi)
        for s in seeds:
            dst = cand(name, s)
            if os.path.exists(dst):
                continue
            raw = os.path.join(OUT, f"_{name}_raw_{s}.png")
            C.krea(f"{PRE} {prompt} {STY}", cw, ch, s, raw, init=ci, denoise=dn, mask=mi)
            back = np.asarray(Image.open(raw).convert("RGB").resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(np.float32) / 255
            back = IP.post(back, offset=(x0, y0), light=light)
            w = np.clip(nd.distance_transform_edt(md) / 8.0, 0, 1)[..., None]
            out = crop[..., :3] * (1 - w) + back * w
            Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(dst)
            print(name, s, flush=True)


def sheet():
    rows = []
    for name, plate, f, box, *_ in JOBS:
        x0, y0, x1, y1 = box
        o = Image.fromarray((rgba(plate, f)[y0:y1, x0:x1, :3] * 255).astype(np.uint8))
        ims = [o] + [Image.open(cand(name, s)) for s in JOBS[[j[0] for j in JOBS].index(name)][7] if os.path.exists(cand(name, s))]
        sc = 0.5 if max(o.size) > 400 else 1.0
        ims = [i.resize((int(i.width * sc), int(i.height * sc))) for i in ims]
        row = Image.new("RGB", (sum(i.width for i in ims) + 8 * len(ims), max(i.height for i in ims)), (255, 0, 255))
        x = 0
        for i in ims:
            row.paste(i, (x, 0))
            x += i.width + 8
        rows.append(row)
    W = max(r.width for r in rows)
    S = Image.new("RGB", (W, sum(r.height + 8 for r in rows)), (255, 0, 255))
    y = 0
    for r in rows:
        S.paste(r, (0, y))
        y += r.height + 8
    S.save(os.path.join(OUT, "sheet.jpg"), quality=88)
    print(os.path.join(OUT, "sheet.jpg"), S.size)


# ---------------------------------------------------------------- CPU fixes
# picked from sheet.jpg; the lintel and the blot inpaints drew pale flat lumps (rejected): those two are clones of
# the plate's own stone beside them instead (CLONES)
PICKS = {"door": 47, "hearth": 11, "cart": 11, "stall": 11, "wedge": 11}
CLONES = {"lintel": ((1410, 2610, 80, 95), (-170, 0)), "blot": ((2440, 1055, 115, 110), (260, 0))}


def clone(img, name, feather=14):
    """The ellipse filled from the same layer offset by off (feathered)."""
    e, off = CLONES[name]
    m = ells(img.shape, [e])
    w = np.clip(nd.distance_transform_edt(m) / feather, 0, 1)[..., None]
    sh = np.roll(img, (-off[1], -off[0]), axis=(0, 1))
    img[..., :3] = img[..., :3] * (1 - w) + sh[..., :3] * w


def put(img, name):
    job = [j for j in JOBS if j[0] == name][0]
    x0, y0, x1, y1 = job[3]
    img[y0:y1, x0:x1, :3] = np.asarray(Image.open(cand(name, PICKS[name])).convert("RGB")).astype(np.float32) / 255
    return job[3]


def carved_light(img, cx, cy, r, col, k, rng_mask=None):
    """Warm light on the drawn strokes only (the black stays black): + col * k * falloff * stroke, inside r."""
    H, W = img.shape[:2]
    x0, y0, x1, y1 = max(0, int(cx - r)), max(0, int(cy - r)), min(W, int(cx + r) + 1), min(H, int(cy + r) + 1)
    Y, X = np.mgrid[y0:y1, x0:x1]
    d = np.hypot(X - cx, Y - cy) / r
    f = np.clip(1 - d, 0, 1) ** 1.6
    lum = img[y0:y1, x0:x1, :3] @ LUMW
    stroke = np.clip((lum - 0.12) / 0.2, 0, 1)
    if rng_mask is not None:
        f = f * rng_mask[y0:y1, x0:x1]
    img[y0:y1, x0:x1, :3] = np.clip(img[y0:y1, x0:x1, :3] + np.array(col, np.float32) * (k * f * stroke)[..., None], 0, 1)


def p0():
    lit = rgba("p0", "lit.png")
    dark = rgba("p0", "dark.png")
    clone(lit, "blot")
    clone(dark, "blot")
    save(dark, "p0", "dark_sb5.png")
    # the lit picture only near the flame: full within ~250 frame px (410 units), the unlit plate by ~750 px (1225 units)
    fx, fy = 1675, 800
    H, W = lit.shape[:2]
    Y, X = np.mgrid[0:H, 0:W]
    d = np.hypot(X - fx, (Y - fy) * 1.05)
    s = np.clip((d - 410) / (1225 - 410), 0, 1)
    fall = 1 - s * s * (3 - 2 * s)
    lit[..., 3] *= fall
    save(lit, "p0", "lit_sb5.png")
    # the glow (an add layer, a soft blur) falls only on the lit strokes: carved, not airbrushed
    g = rgba("p0", "glow.png")
    gx, gy = 994, 94
    sub = rgba("p0", "lit.png")[gy:gy + g.shape[0], gx:gx + g.shape[1], :3] @ LUMW
    g[..., 3] *= np.clip((sub - 0.18) / 0.25, 0, 1) * 0.85 + 0.15
    save(g, "p0", "glow_sb5.png")
    # the flame: a smooth gradient -> four carved bands with vertical gouge edges
    fl = rgba("p0", "flame.png")
    a = fl[..., 3]
    lum = fl[..., :3] @ LUMW
    rng = np.random.default_rng(5)
    gouge = nd.gaussian_filter(rng.normal(0, 1, fl.shape[:2]), (6, 0.8))
    gouge /= np.abs(gouge).max() + 1e-6
    v = lum + 0.10 * gouge
    inks = np.array([[0.99, 0.95, 0.80], [0.98, 0.82, 0.42], [0.93, 0.58, 0.20], [0.70, 0.32, 0.10]], np.float32)
    band = np.select([v > 0.80, v > 0.66, v > 0.50], [0, 1, 2], 3)
    col = inks[band]
    fl[..., :3] = np.where((a > 0.02)[..., None], col, fl[..., :3])
    fl[..., 3] = np.clip((a - 0.25) / 0.3, 0, 1)
    save(fl, "p0", "flame_sb5.png")


def p2():
    base = rgba("p2", "base.png")
    orig = base.copy()
    for n in ("door", "hearth", "cart", "stall"):
        put(base, n)
    clone(base, "lintel")
    H, W = base.shape[:2]
    # the door's light: only the seams round the shut slab (a band just inside the old opening's edge)
    dm = np.load(os.path.join(OUT, "_door_mask.npy"))
    x0, y0, x1, y1 = 800, 2560, 1300, 3562
    op = np.zeros((H, W), bool)
    op[y0:y1, x0:x1] = nd.binary_erosion(dm, iterations=6)
    seam = op & ~nd.binary_erosion(op, iterations=9)
    seam = nd.gaussian_filter(seam.astype(np.float32), 1.5)
    dg = rgba("p2", "door_glow.png")
    gx, gy = 574, 2461
    dg[..., 3] *= np.clip(seam[gy:gy + dg.shape[0], gx:gx + dg.shape[1]] * 1.4, 0, 1)
    save(dg, "p2", "door_glow_sb5.png")
    # the warm stones are the threads layer's orange drops (add, over dull stones drawn in the base): rows of identical
    # drops -> each glowing core warped smaller or bigger, turned, squashed, its heat varied; a third go out (the dull
    # base stone stays); carved light round each in the base. The threads themselves: brighter bottom-to-top.
    rng = np.random.default_rng(21)
    for f, (px, py) in (("threads.png", (154, 1168)), ("threads_glow.png", (75, 1107))):
        t = rgba("p2", f)
        o = t.copy()
        th, tw = t.shape[:2]
        orange = (o[..., 0] - o[..., 2] > 0.28) & (o[..., 3] > 0.05)
        y = py + np.arange(th)[:, None]
        ramp = np.clip(0.28 + 0.72 * (3450 - y) / 1250.0, 0.28, 1.0)
        if f == "threads_glow.png":
            # the soft halo follows the new threads (their ramp, the changed and the gone stones): old x new/old (blurred)
            na, oa = (np.pad(a, ((py0, 0), (px0, 0)))[:th, :tw] for a in (thr_new, thr_old))
            ratio = nd.gaussian_filter(na, 10) / np.maximum(nd.gaussian_filter(oa, 10), 1e-3)
            t[..., 3] *= np.clip(ratio, 0, 1)
            save(t, "p2", "threads_glow_sb5.png")
            continue
        t[..., 3] = np.where(orange, t[..., 3], t[..., 3] * ramp)
        if f == "threads.png":
            hot = orange & (o[..., 3] > 0.3)
            hot[:max(0, 1450 - py)] = False
            lab, n = nd.label(nd.binary_closing(hot, iterations=1))
            kept = gone = 0
            for i, s in enumerate(nd.find_objects(lab)):
                comp = lab[s] == i + 1
                A = int(comp.sum())
                if A < 20 or A > 6000:
                    continue
                y0, x0 = s[0].start, s[1].start
                h, w = comp.shape
                md = nd.binary_dilation(comp, iterations=2)
                Y0, X0 = max(0, y0 - 2), max(0, x0 - 2)
                reg = np.zeros((th, tw), bool)
                reg[y0:y0 + h, x0:x0 + w] = comp
                reg = nd.binary_dilation(reg, iterations=2) if A < 3000 else reg
                patch = o[y0:y0 + h, x0:x0 + w].copy()
                patch[..., 3] *= comp
                t[..., 3] = np.where(reg & orange, 0, t[..., 3])
                if rng.random() < 0.33:
                    gone += 1
                    continue
                sc, ang, sq = rng.uniform(0.5, 1.15), rng.uniform(-60, 60), rng.uniform(0.7, 1.3)
                heat = rng.uniform(0.0, 1.0)
                pa = Image.fromarray((patch * 255 + 0.5).astype(np.uint8), "RGBA")
                nw, nh = max(3, int(w * sc * sq)), max(3, int(h * sc / sq))
                pa = np.asarray(pa.resize((nw, nh), Image.LANCZOS).rotate(ang, Image.BICUBIC, expand=True)).astype(np.float32) / 255
                gold = np.array([1.0, 0.80, 0.42], np.float32)
                rgb = np.clip(pa[..., :3] * (1 - 0.5 * heat) + gold * 0.5 * heat, 0, 1)
                al = pa[..., 3] * (0.45 + 0.55 * heat)
                cy = y0 + h / 2 + rng.uniform(-0.15, 0.15) * h
                cx = x0 + w / 2 + rng.uniform(-0.15, 0.15) * w
                ty, tx = int(cy - pa.shape[0] / 2), int(cx - pa.shape[1] / 2)
                if ty < 0 or tx < 0 or ty + pa.shape[0] > th or tx + pa.shape[1] > tw:
                    continue
                dst = t[ty:ty + pa.shape[0], tx:tx + pa.shape[1]]
                a_new = al + dst[..., 3] * (1 - al)
                dst[..., :3] = np.where(al[..., None] > 0, (rgb * al[..., None] + dst[..., :3] * dst[..., 3:] * (1 - al[..., None]))
                                        / np.maximum(a_new[..., None], 1e-4), dst[..., :3])
                dst[..., 3] = a_new
                kept += 1
                carved_light(base, px + cx, py + cy, max(nw, nh) * (1.3 + 1.2 * heat), (1.0, 0.55, 0.18), 0.05 + 0.13 * heat)
            print("p2 warm stones:", kept, "kept,", gone, "out")
        thr_old, thr_new = o[..., 3], t[..., 3]
        px0, py0 = 154 - 75, 1168 - 1107          # the threads' place in the glow layer
        save(t, "p2", f.replace(".png", "_sb5.png"))
    # the ember heaps: their gold light on the hands and the wood beside them
    carved_light(base, 1890, 715, 230, (1.0, 0.62, 0.22), 0.45)
    carved_light(base, 1392, 865, 190, (1.0, 0.62, 0.22), 0.40)
    save(base, "p2", "base_sb5.png")


# p6: the far bank's four lamps (far px) and the water line below them
P6_LAMPS = [(901, 641), (970, 640), (1009, 664), (1118, 666)]


def p6():
    near = rgba("p6", "near.png")
    orig = near.copy()
    # paint out the old reflections (a cloned row on the near layer): the water from beside each blob
    x0, y0, x1, y1 = 2270, 700, 2580, 800
    sub = near[y0:y1, x0:x1]
    lum = sub[..., :3] @ LUMW
    m = nd.binary_dilation((lum > 0.42) & (sub[..., 3] > 0.5), iterations=4)
    lab, n = nd.label(m)
    for i, s in enumerate(nd.find_objects(lab)):
        comp = lab[s] == i + 1
        w = s[1].stop - s[1].start
        for ox in (w + 14, -(w + 14), 2 * w + 20, -(2 * w + 20)):
            src = m[s[0], s[1].start + ox:s[1].stop + ox] if 0 <= s[1].start + ox and s[1].stop + ox <= m.shape[1] else None
            if src is not None and src.shape == comp.shape and not (src & comp).any() and not src.any():
                break
        ys_, xs_ = np.nonzero(comp)
        sy, sx = ys_ + s[0].start + y0, xs_ + s[1].start + x0
        near[sy, sx, :3] = orig[sy, sx + ox, :3]
    print("p6 near: reflections painted out:", n)
    save(near, "p6", "near_sb5.png")
    # the new reflections: on the far layer's own grid (z 3), each a broken vertical streak under its lamp
    far = rgba("p6", "far.png")
    rng = np.random.default_rng(11)
    W0, H0 = 300, 140                     # far px box: x 860..1160, y 735..875
    bx, by = 860, 735
    S = 4
    im = Image.new("RGBA", (W0 * S, H0 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pale = (205, 214, 222)
    warm = (232, 205, 150)
    for k, (lx, ly) in enumerate(P6_LAMPS):
        n_d = int(rng.integers(4, 8))
        y = 745 + rng.integers(0, 6) - by
        wid = rng.uniform(11, 20)
        for j in range(n_d):
            hh = rng.uniform(1.6, 3.2)
            x = lx - bx + rng.uniform(-2.5, 2.5)
            ww = wid * rng.uniform(0.55, 1.0) * (1 - 0.55 * j / n_d)
            c = warm if j == 0 else pale
            a = int(255 * (0.95 - 0.5 * j / n_d))
            # a tapered gouge mark (lens): a polygon thick in the middle, pointed at both ends
            pts = [((x - ww / 2) * S, y * S), (x * S, (y - hh / 2) * S), ((x + ww / 2) * S, y * S), (x * S, (y + hh / 2) * S)]
            d.polygon(pts, fill=c + (a,))
            y += hh + rng.uniform(2.5, 7.5) * (1 + 0.4 * j / n_d)
            if y > H0 - 6:
                break
    st = np.asarray(im.resize((W0, H0), Image.LANCZOS)).astype(np.float32) / 255
    al = st[..., 3]
    rgb = IP.post(np.where(al[..., None] > 0, st[..., :3] / np.maximum(al[..., None], 1e-3), 0), offset=(bx + 1412, by))
    out = np.dstack([rgb, al])
    save(out, "p6", "lamp_refl_sb5.png")
    print("p6 lamp_refl: far px box", (bx, by, bx + W0, by + H0))


def p7():
    w = rgba("p7", "water.png")
    put(w, "wedge")
    save(w, "p7", "water_sb5.png")


# p7u: one irregular column of bubbles rising from where the traveler went in (layer px at scale 1, pos (0, 700))
P7U_BOX = (0, 700, 3200, 1100)            # canvas units: x, y, w, h


def p7u():
    rng = np.random.default_rng(88)
    X0, Y0, W0, H0 = P7U_BOX
    S = 3
    im = Image.new("RGBA", (W0 * S, H0 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ring = (150, 178, 200, 255)
    hi = (225, 238, 248, 255)
    bubbles = []
    yb, yt = H0 - 20, 140                  # the column's foot and top (layer px)
    for i in range(70):
        f = rng.uniform(0, 1) ** 0.8         # 0 at the foot .. 1 at the top: more of them up high
        y = yb - f * (yb - yt)
        xc = 1480 + 90 * np.sin(f * 4.1 + 0.6) + 55 * np.sin(f * 9.3)
        spread = 26 + 150 * f ** 1.4
        x = xc + rng.normal(0, spread * 0.55)
        r = rng.uniform(3.5, 9) + (rng.uniform(4, 16) if rng.random() < 0.25 * (0.4 + f) else 0)
        if any(np.hypot(x - bx, y - by) < r + br + 4 for bx, by, br in bubbles):
            continue
        bubbles.append((x, y, r))
    for x, y, r in bubbles:
        t = max(1.6, 0.17 * r)
        sq = rng.uniform(0.88, 1.0)
        # the ring: thicker at the lower right (the carved weight), the inside empty
        d.ellipse(((x - r) * S, (y - r * sq) * S, (x + r) * S, (y + r * sq) * S), outline=ring, width=int(t * S))
        d.arc(((x - r) * S, (y - r * sq) * S, (x + r) * S, (y + r * sq) * S), 10, 120, fill=ring, width=int(t * 1.7 * S))
        # one small crescent highlight at the top left
        rr = r * 0.62
        d.arc(((x - rr) * S, (y - rr * sq) * S, (x + rr) * S, (y + rr * sq) * S), 200, 250, fill=hi, width=max(S, int(t * 1.1 * S)))
    st = np.asarray(im.resize((W0, H0), Image.LANCZOS)).astype(np.float32) / 255
    al = st[..., 3]
    rgb = np.where(al[..., None] > 0, st[..., :3] / np.maximum(al[..., None], 1e-3), 0)
    rgb = IP.post(rgb, offset=(X0, Y0), light="cold")
    save(np.dstack([rgb, al]), "p7u", "bubbles_sb5.png")
    print("p7u bubbles:", len(bubbles))


def apply(which):
    for p in which or ("p0", "p2", "p6", "p7", "p7u"):
        globals()[p]()


if __name__ == "__main__":
    {"gpu": lambda: gpu(), "sheet": lambda: sheet(), "apply": lambda: apply(sys.argv[2:])}[sys.argv[1]]()
