"""HUD A2 "Lamps Are Lit": cut the Krea oil lamp into the game's life-lamp layers (godot/art/ui/lamp_life/).

Source: the Krea paintings logged in ui_assets.json ("lamp_life_*"): lamp_b seed 4203 (cut from black) and
flame_gold seed 4201. Out, at twice the 1080 size (the HUD scales x4/3 at 1440):
  lamp_lit.png   the lamp as painted, its flame lifted out (the shader draws it), the chimney shortened,
                 the brass cooled to iron, the glass made see-through (alpha), a forged eye on the font's
                 right strap for the chain.
  lamp_cold.png  the same with the flame's painted light taken off the glass and the collar (the shader
                 mixes lit and cold by the flame's light).
  lamp_mask.png  R the oil font's inside (where her life is), G the font glass's own highlights (laid over
                 the oil), B the glass (chimney and font: lit warm by the flame), A the iron near the flame.
  lamp_flame.png the painted flame, light-keyed (premultiplied: rgb is its light, a its cover).
  lamp_geo.json  where things are, in 1080 px from the canvas's top left (the C# constants come from it).
Run: python tools/uiforge/lamp_life_cut.py <squat_cut.png> <flame.png> <ring_lamp_cut.png> [--check out.png]
(the sources are kept in C:/Users/munch/Desktop/survivorsunchained_inputs/ui14_lamp_src/)
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "godot", "art", "ui", "lamp_life")

# The squat lamp (26 Oct, the owner: "too much screenspace vertically"): Krea squat_a seed 4203, its rows in the
# cut source: the chimney's neck 15-110 taken out; the bulb's waist (the collar's top) at 300; the font's glass
# 525-825 (its widest at 675); the cradle under it to the foot.
WIDE = 140            # the lamp's widest (the cradle round the font) at 1080: the glass inside it about 130
CUT = (15, 110)
WAIST, FONT = 300, (525, 825)
CANVAS = (176, 196)   # 1080 px: the quad (the lamp 146 tall at its foot, room above for the smoke)
FOOT_PAD = 2          # 1080 px under the foot inside the canvas
SW = 56               # the centre strap's width (source px)


def blur(a, s):
    return nd.gaussian_filter(a, s) if s > 0 else a


def load(p):
    im = Image.open(p).convert("RGBA")
    return im.crop(im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox())


def main(src_p, flame_p, ring_p, check=None):
    src = load(src_p)
    a = np.asarray(src, np.float32) / 255
    # 1. the chimney shortened: CUT rows out of its straight tube, crossfaded over 8 rows
    y0, y1 = CUT
    top, bot = a[:y0], a[y1:]
    n = 8
    w = np.linspace(0, 1, n)[:, None, None]
    seam = top[-n:] * (1 - w) + bot[:n] * w
    a = np.concatenate([top[:-n], seam, bot[n:]], axis=0)
    H, W = a.shape[:2]
    A = a[..., 3].copy()
    rgb = a[..., :3].copy()
    lum = rgb.mean(2)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rows = (A > 0.5).sum(1)
    d = CUT[1] - CUT[0]
    waist, ft, fb = WAIST - d, FONT[0] - d, FONT[1] - d
    fr = ft + int(np.argmax(rows[ft:fb]))
    xs = np.where(A[fr] > 0.5)[0]
    fx0, fx1 = xs[0], xs[-1]
    cx = (fx0 + fx1) / 2
    g_top = int(np.where(rows > rows[:waist].max() * 0.6)[0][0])
    tube_w = float(np.median(rows[:max(3, CUT[0])]))
    print(f"src {W}x{H}  font rows {ft}-{fb} widest {fr} x {fx0}-{fx1}  bulb {g_top}-{waist}")

    # 2. the painted flame lifted out (inside the globe: bright, warm)
    br = rgb.max(2)
    globe = (yy >= g_top) & (yy <= waist + 6)
    fm = globe & (br > 0.6) & (rgb[..., 0] > rgb[..., 2] + 0.12) & (np.abs(xx - cx) < 60)
    lab, k = nd.label(fm)
    if k:
        sizes = nd.sum(fm, lab, range(1, k + 1))
        fm = lab == (1 + int(np.argmax(sizes)))
    fys, fxs = np.where(fm)
    wick = (float(np.average(fxs)), float(fys.max()))
    fmask = blur(nd.binary_dilation(fm, iterations=4).astype(np.float32), 2.0)
    # the hole: the glass behind the flame, a dim warm-dark (the shader's flame sits over it)
    keep = (1 - (fmask > 0.02)).astype(np.float32) * (A > 0.5)
    fill = np.zeros_like(rgb)
    for s_ in (3, 6, 12, 24):
        num = np.stack([blur(rgb[..., i] * keep, s_) for i in range(3)], 2)
        den = blur(keep, s_)[..., None]
        est = num / np.maximum(den, 1e-4)
        take = (den > 0.05) & (fill.sum(2, keepdims=True) == 0)
        fill = np.where(take, est, fill)
    rgb = rgb * (1 - fmask[..., None]) + fill * fmask[..., None] * 0.8

    # 3. masks: the glass (globe and tube: see-through), the font's inside, the centre strap
    sil = A > 0.5
    chim = (yy < waist - 4) & (yy > H * 0.035)
    chim_in = nd.binary_erosion(sil & chim, iterations=6)
    # the font's glass: the silhouette's font rows, in from its iron frame
    font_sil = sil & (yy >= ft) & (yy <= fb)
    font_in = nd.binary_erosion(font_sil, iterations=22)
    # keep only the glass band between the frame's top and bottom rims: rows whose inside spans most of the width
    fw = font_in.sum(1)
    band = fw > (fx1 - fx0) * 0.55
    font_in &= band[:, None]
    # the centre strap: the dark vertical band at the middle (found per row: the darkest 34 px window near cx)
    # (one band for all rows: the median of each row's darkest 36 px window near the middle)
    sl = blur(lum, 1.0)
    starts = []
    for y in np.where(band)[0]:
        lo = int(cx - 70)
        c = np.convolve(sl[y, lo:lo + 140], np.ones(SW) / SW, mode="valid")
        starts.append(lo + int(np.argmin(c)))
    s0 = int(cx) - 34  # (the painting's strap: 366-423 in the source; the darkest-window search drifts right)
    strap = np.zeros_like(font_in)
    strap[:, s0:s0 + 62] = True
    oil = font_in & ~strap
    oil = blur(oil.astype(np.float32), 0.9)
    oil_rows = np.where(oil.max(1) > 0.5)[0]
    o_top, o_bot = int(oil_rows[0]), int(oil_rows[-1])
    print(f"oil rows {o_top}-{o_bot}")
    # the font glass's own light (laid over the oil): the bright streaks
    hl = np.clip(lum - blur(lum, 6) - 0.03, 0, 1) * 2.4 + np.clip(lum - 0.55, 0, 1) * 1.6
    hl = np.clip(hl, 0, 1) * (oil > 0.05)

    # 4. iron cooled (no brass) outside the glass; the flame's light kept apart (lit vs cold)
    glass = np.maximum(blur(chim_in.astype(np.float32), 1.0), blur(font_in.astype(np.float32), 1.0) * (1 - strap))
    iron = sil & (glass < 0.5)
    g = rgb.mean(2, keepdims=True)
    warm = np.clip((rgb[..., 0:1] - rgb[..., 2:3]) - 0.04, 0, 1) * 4
    cool_iron = g * np.array([0.84, 0.82, 0.84]) + (rgb - g) * 0.25
    near = np.exp(-np.maximum(0, yy - wick[1]) / (0.09 * H)) * np.exp(-np.maximum(0, wick[1] - 60 - yy) / (0.1 * H))
    lit = rgb.copy()
    # iron: brass cast cooled; the collar keeps a warm catch where the flame lights it (into lit only)
    lit = np.where(iron[..., None], cool_iron + (rgb - cool_iron) * np.clip(warm, 0, 1) * near[..., None] * 0.9, lit)
    cold = np.where(iron[..., None], cool_iron, rgb)
    # the glass: cold = the painting's light taken off (a dark smoke-green glass with its own highlights)
    gl_cold = g * np.array([0.42, 0.46, 0.46]) + np.clip(lum - blur(lum, 5), 0, 1)[..., None] * 0.9
    gl_w = np.clip(glass, 0, 1)[..., None] * (1 - oil[..., None] * 0)  # the font's glass too (its empty part)
    cold = cold * (1 - gl_w) + gl_cold * gl_w
    iron_near = (iron & (near > 0.25)).astype(np.float32) * np.clip(warm[..., 0], 0, 1)
    # alpha: the glass see-through, darkest where the painting is dark, its highlights opaque
    see = np.clip(0.38 + lum * 3.0, 0.38, 1.0)
    A2 = A * (1 - glass * (1 - see))

    # 5. the eye for the chain: the carrying ring on top, turned on its side, on the font's right frame
    # (the ring is the tall lamp's carrying ring, krea lamp_b seed 4203: the same hand)
    rs = load(ring_p)
    ra_ = np.asarray(rs, np.float32) / 255
    rrows = (ra_[..., 3] > 0.5).sum(1)
    r_bot = int(np.where(rrows > 60)[0][0]) - 1
    rx0, rx1 = np.where(ra_[:r_bot, :, 3].max(0) > 0.5)[0][[0, -1]]
    ring = ra_[:r_bot, rx0:rx1 + 1]
    g_ = ring[..., :3].mean(2, keepdims=True)
    ring[..., :3] = g_ * np.array([0.84, 0.82, 0.84]) + (ring[..., :3] - g_) * 0.25
    ring_im = Image.fromarray((np.clip(ring, 0, 1) * 255).astype(np.uint8), "RGBA").rotate(-90, expand=True, resample=Image.BICUBIC)
    kr = 74 / ring_im.height
    ring_im = ring_im.resize((int(ring_im.width * kr), int(ring_im.height * kr)), Image.LANCZOS)
    eye_y = int(fr + (fb - fr) * 0.55)
    xr = np.where(A[eye_y] > 0.5)[0][-1]
    ex, ey = xr - 10, eye_y - ring_im.height // 2
    pad = ring_im.width
    def place(arr, ch):
        big = np.zeros((H, W + pad, ch), np.float32)
        big[:, :W] = arr if arr.ndim == 3 else arr[..., None]
        return big
    lit, cold = place(lit, 3), place(cold, 3)
    A2 = place(A2, 1)[..., 0]
    oil, hl, glass_m, inear = (place(m, 1)[..., 0] for m in (oil, hl, glass, iron_near))
    rim = np.asarray(ring_im, np.float32) / 255
    ra = rim[..., 3:4]
    for img in (lit, cold):
        img[ey:ey + ring_im.height, ex:ex + ring_im.width] = img[ey:ey + ring_im.height, ex:ex + ring_im.width] * (1 - ra) + rim[..., :3] * ra
    A2[ey:ey + ring_im.height, ex:ex + ring_im.width] = np.maximum(A2[ey:ey + ring_im.height, ex:ex + ring_im.width], ra[..., 0])
    for m in (oil, hl, glass_m):
        m[ey:ey + ring_im.height, ex:ex + ring_im.width] *= (1 - ra[..., 0])
    # the eye's hole: the ring's dark middle (its centre in the rotated ring)
    eye_c = (ex + ring_im.width * 0.62, ey + ring_im.height / 2)
    W2 = W + pad

    # 6. into the canvas at 2x the 1080 size
    k = 2 * WIDE / (fx1 - fx0)
    cw, ch = CANVAS[0] * 2, CANVAS[1] * 2
    lw, lh = round(W2 * k), round(H * k)
    ox = round(cw / 2 - cx * k)
    oy = ch - FOOT_PAD * 2 - lh
    print(f"scale {k:.3f}: lamp {lw}x{lh} at ({ox},{oy}) in {cw}x{ch}")

    def canvas(arr, mode):
        im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), mode).resize((lw, lh), Image.LANCZOS)
        c = Image.new(mode, (cw, ch), 0 if mode == "L" else (0,) * len(mode))
        c.paste(im, (ox, oy))
        return c
    def rgba(rgb_, a_):
        # straight alpha; the colour bled out under the edge so the filtering keeps no dark fringe
        return np.concatenate([rgb_, a_[..., None]], 2)
    os.makedirs(OUT, exist_ok=True)
    canvas(rgba(lit, A2), "RGBA").save(os.path.join(OUT, "lamp_lit.png"))
    canvas(rgba(cold, A2), "RGBA").save(os.path.join(OUT, "lamp_cold.png"))
    m = np.stack([oil, hl, glass_m], 2)
    canvas(m, "RGB").save(os.path.join(OUT, "lamp_mask.png"))

    # 7. the flame: light-keyed, cropped above its wick holder, its foot at the bottom middle
    f = np.asarray(Image.open(flame_p).convert("RGB"), np.float32) / 255
    fa = np.clip((f.max(2) - 0.06) * 1.4, 0, 1)
    # the wick holder (brass, under the blue root at 0.88 of the frame) cropped off, the foot faded over 3%
    hF, wF = fa.shape
    r0, r1 = int(0.06 * hF), int(0.885 * hF)
    c0, c1 = int(0.37 * wF), int(0.63 * wF)
    f, fa = f[r0:r1, c0:c1], fa[r0:r1, c0:c1]
    fade = np.clip((f.shape[0] - np.arange(f.shape[0])) / (0.03 * hF), 0, 1)[:, None]
    fa = fa * fade
    f = f * fade[..., None]
    prem = f * 1.0  # the light (on black: already its light)
    fl = Image.fromarray((np.clip(np.concatenate([prem, fa[..., None]], 2), 0, 1) * 255).astype(np.uint8), "RGBA")
    fl = fl.resize((128, round(128 * fl.height / fl.width)), Image.LANCZOS)
    fl.save(os.path.join(OUT, "lamp_flame.png"))

    def at(p):  # source px -> 1080 px in the canvas
        return [round((ox + p[0] * k) / 2, 2), round((oy + p[1] * k) / 2, 2)]
    geo = dict(canvas=list(CANVAS), wick=at(wick), oil_top=at((cx, o_top))[1], oil_bot=at((cx, o_bot))[1],
               font_mid=at((cx, (ft + fb) / 2)), font_x=[at((fx0, 0))[0], at((fx1, 0))[0]], eye=at(eye_c),
               chim_top=at((cx, H * 0.035))[1], globe=[at((cx, g_top))[1], at((cx, waist))[1]], foot=at((cx, H))[1],
               flame_aspect=round(fl.height / fl.width, 3))
    json.dump(geo, open(os.path.join(OUT, "lamp_geo.json"), "w"), indent=1)
    print(json.dumps(geo))
    if check:
        c = Image.new("RGBA", (cw, ch), (60, 70, 60, 255))
        c.alpha_composite(Image.open(os.path.join(OUT, "lamp_lit.png")))
        mm = np.asarray(Image.open(os.path.join(OUT, "lamp_mask.png")), np.float32) / 255
        ov = np.asarray(c, np.float32) / 255
        ov[..., 0] = np.maximum(ov[..., 0], mm[..., 0] * 0.8)
        ov[..., 2] = np.maximum(ov[..., 2], mm[..., 2] * 0.5)
        side = Image.fromarray((ov * 255).astype(np.uint8), "RGBA")
        cc = Image.new("RGBA", (cw, ch), (60, 70, 60, 255)); cc.alpha_composite(Image.open(os.path.join(OUT, "lamp_cold.png")))
        sheet = Image.new("RGB", (cw * 3, ch)); sheet.paste(c.convert("RGB"), (0, 0)); sheet.paste(cc.convert("RGB"), (cw, 0)); sheet.paste(side.convert("RGB"), (cw * 2, 0))
        sheet.save(check)


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    chk = sys.argv[sys.argv.index("--check") + 1] if "--check" in sys.argv else None
    if chk in args: args.remove(chk)
    main(args[0], args[1], args[2], chk)
