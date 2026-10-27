"""HUD A2 "Lamps Are Lit": cut the Krea oil lamp into the game's life-lamp layers (godot/art/ui/lamp_life/).

Source: the Krea paintings logged in ui_assets.json ("lamp_life_*"): lamp_b seed 4203 (cut from black) and
flame_gold seed 4201. Out, at twice the 1080 size (the HUD scales x4/3 at 1440):
  lamp_lit.png   the lamp as painted, its flame lifted out (the shader draws it), the chimney shortened,
                 the brass cooled to iron, the glass made see-through (alpha), a forged eye on the font's
                 right strap for the chain.
  lamp_cold.png  the same with the flame's painted light taken off the glass and the collar (the shader
                 mixes lit and cold by the flame's light).
  lamp_mask.png  R the oil font's inside (where her life is), G the font glass's own highlights (laid over
                 the oil), B the glass (chimney and font: lit warm by the flame), A 1 - half the glass's whole
                 inside (iron over it included: the rim and the shield's arc follow its outer edge).
  lamp_flame.png the painted flame, light-keyed (premultiplied: rgb is its light, a its cover).
  lamp_geo.json  where things are, in 1080 px from the canvas's top left (the C# constants come from it).
Run: python tools/uiforge/lamp_life_cut.py [squat|tall|globe|font] [--check out.png]
(each shape is a data block in SHAPES; squat writes lamp_life/, the others lamp_life/<shape>/; LifeLamp reads
the one chosen by --lamp-shape. Sources kept in C:/Users/munch/Desktop/survivorsunchained_inputs/ui14_lamp_src/
and ui15_lamp_src/)
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "..", "..", "godot", "art", "ui", "lamp_life")
INPUTS = "C:/Users/munch/Desktop/survivorsunchained_inputs"
SRC14, SRC15 = INPUTS + "/ui14_lamp_src/", INPUTS + "/ui15_lamp_src/"

# A shape is a data block: its painting (BiRefNet cut), the rows in that painting (source px, before any cut or
# stretch), and where it sits on the screen. Keys:
#   src        the cut painting; flame the painted flame (light-keyed); ring the eye's carrying ring
#   cut        (y0, y1) rows taken out of the chimney's straight tube (shorter); stretch (y0, y1, f) rows
#              of the tube drawn f times taller (a short painted chimney made to hold the flame)
#   waist      the collar's top (the chimney's foot); font (top, bottom) the oil glass's rows
#   wick_y     the wick's row (paintings with no painted flame; else it is found from the flame)
#   inset      px from the silhouette to the glass's inside; band the share of the widest row a glass row
#              must span to hold oil; strap the squat's centre strap (px either side of the middle)
#   bands      the cage's iron across the glass (the oil goes behind it): (x_edge, top, bottom at the edge,
#              x_mid, top, bottom at the middle), a band seen from a little above (its rows a parabola); the
#              level skips it (the shader's skip: the surface never rests behind it, so her life reads at
#              every height). straps [(points, width, search)]: iron down the glass along a polyline (the
#              globe's ribs; search > 0 snaps each row to the darkest run within that many px, then smooths)
#   scale      "wide": the font this wide at 1080 (wide, canvas fixed); "fit": the whole lamp, flame tip
#              included, between top_line and floor (1080 px), the canvas sized round it
#   floor      the foot's screen row (1080); top_line nothing above it; flame_full the flame's height at full
SHAPES = {
    # The squat lamp (26 Oct, the owner: "too much screenspace vertically"): Krea squat_a seed 4203, its rows
    # in the cut source: the chimney's neck 15-110 taken out; the bulb's waist (the collar's top) at 300; the
    # font's glass 525-825 (its widest at 675); the cradle under it to the foot.
    "squat": dict(src=SRC14 + "squat_a_4203_cut.png", flame=SRC14 + "cand_4201.png", ring=SRC14 + "cand_4203_cut.png",
                  out="", cut=(15, 110), waist=300, font=(525, 825), inset=22, band=0.55, strap=(34, 28),
                  scale="wide", wide=140, canvas=(176, 196), ring_px=74, floor=1052, top_line=904,
                  flame_full=34, number_y=182),
    # UI 15 (27 Oct, the owner: "elongated a little"; "the orb shape might be better"): three shapes for one pick.
    # tall: Krea seed 4311, an upright egg of glass in a cradle (a gold-inlaid band and a front strap).
    "tall": dict(src=SRC15 + "tall_4311_cut.png", out="tall", stretch=(62, 138, 2.0), waist=145, wick_y=145,
                 font=(232, 838), inset=10, band=0.35,
                 bands=[(260, 556, 612, 512, 556, 618)], straps=[([(512, 556), (512, 900)], 62, 0)],
                 scale="fit", floor=1064, top_line=900, flame_full=30),
    # globe: Krea seed 4301, a full glass sphere in a cage of four iron ribs and an equator band.
    "globe": dict(src=SRC15 + "globe_4301_cut.png", out="globe", stretch=(78, 182, 1.7), waist=192, wick_y=192,
                  font=(296, 792), inset=8, band=0.3,
                  bands=[(225, 543, 586, 508, 572, 622)],
                  straps=[([(395, 300), (365, 350), (345, 400), (330, 460), (325, 520), (326, 580), (330, 640),
                            (345, 700), (365, 760), (380, 790)], 19, 10),
                          ([(590, 300), (625, 350), (648, 400), (662, 460), (668, 520), (668, 580), (665, 640),
                            (650, 700), (625, 760), (610, 790)], 19, 10),
                          ([(300, 340), (275, 400), (255, 460), (245, 520), (244, 590), (248, 650), (262, 700),
                            (290, 750)], 16, 8),
                          ([(718, 340), (742, 400), (762, 460), (770, 520), (771, 590), (768, 650), (755, 700),
                            (730, 750)], 16, 8)],
                  scale="fit", floor=1064, top_line=900, flame_full=30),
    # font: Krea seed 4302, a flattened glass sphere under a crowned collar, in a cradle (band, front strap).
    "font": dict(src=SRC15 + "font_4302_cut.png", out="font", stretch=(48, 146, 1.4), waist=152, wick_y=152,
                 font=(384, 808), inset=10, band=0.4,
                 bands=[(190, 546, 594, 510, 546, 602)], straps=[([(510, 546), (510, 900)], 46, 0),
                                                                  ([(510, 600), (510, 690)], 30, 0)],
                 scale="fit", floor=1064, top_line=900, flame_full=30),
}
for _k in ("tall", "globe", "font"):
    SHAPES[_k].setdefault("flame", SRC14 + "cand_4201.png")
    SHAPES[_k].setdefault("ring", SRC14 + "cand_4203_cut.png")
FOOT_PAD = 2          # 1080 px under the foot inside the canvas
RING_1080 = 13.6      # the eye's ring's height at 1080 (the squat's: 74 source px at its scale)


def blur(a, s):
    return nd.gaussian_filter(a, s) if s > 0 else a


def load(p):
    im = Image.open(p).convert("RGBA")
    return im.crop(im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox())


def main(shape, check=None):
    S = dict(SHAPES[shape])
    out = os.path.join(ART, S["out"])
    src = load(S["src"])
    if S["scale"] == "fit":
        # (the UI 15 shapes' rows and columns are the painting's own: moved into the cut's crop)
        bx, by = Image.open(S["src"]).getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()[:2]
        for key in ("waist", "wick_y"):
            S[key] -= by
        S["font"] = tuple(v - by for v in S["font"])
        S["stretch"] = (S["stretch"][0] - by, S["stretch"][1] - by, S["stretch"][2])
    a = np.asarray(src, np.float32) / 255
    sil0 = a[..., 3] > 0.5
    top0 = int(np.where(sil0.any(1))[0][0])
    # 1. the chimney shortened (CUT rows out of its straight tube, crossfaded over 8 rows) or stretched
    if "cut" in S:
        y0, y1 = S["cut"]
        top, bot = a[:y0], a[y1:]
        n = 8
        w = np.linspace(0, 1, n)[:, None, None]
        seam = top[-n:] * (1 - w) + bot[:n] * w
        a = np.concatenate([top[:-n], seam, bot[n:]], axis=0)
        d = y1 - y0
        rowmap = lambda y: y - d if y >= y1 else y
    elif "stretch" in S:
        y0, y1, f = S["stretch"]
        mid = nd.zoom(a[y0:y1], (round((y1 - y0) * f) / (y1 - y0), 1, 1), order=1)
        a = np.concatenate([a[:y0], mid, a[y1:]], axis=0)
        d = mid.shape[0] - (y1 - y0)
        rowmap = lambda y: y + d if y >= y1 else (y0 + (y - y0) * f if y > y0 else y)
    else:
        rowmap = lambda y: y
    H, W = a.shape[:2]
    A = a[..., 3].copy()
    rgb = a[..., :3].copy()
    lum = rgb.mean(2)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rows = (A > 0.5).sum(1)
    waist, ft, fb = (int(round(rowmap(v))) for v in (S["waist"], *S["font"]))
    fr = ft + int(np.argmax(rows[ft:fb]))
    xs = np.where(A[fr] > 0.5)[0]
    fx0, fx1 = xs[0], xs[-1]
    cx = (fx0 + fx1) / 2
    g_top = int(np.where(rows > rows[:waist].max() * 0.6)[0][0])
    top_row = int(np.where(rows > 0)[0][0])
    print(f"{shape}: src {W}x{H}  font rows {ft}-{fb} widest {fr} x {fx0}-{fx1}  bulb {g_top}-{waist}")

    # 2. the painted flame lifted out (inside the globe: bright, warm)
    br = rgb.max(2)
    globe = (yy >= g_top) & (yy <= waist + 6)
    fm = globe & (br > 0.6) & (rgb[..., 0] > rgb[..., 2] + 0.12) & (np.abs(xx - cx) < 60)
    if "wick_y" in S:
        # (no flame painted: the wick at the chimney's foot, in the chimney's middle)
        fm[:] = False
        wy = rowmap(S["wick_y"])
        cr = np.where(A[int(wy) - 6] > 0.5)[0]
        wick = (float((cr[0] + cr[-1]) / 2), float(wy))
    else:
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
    chim_top = H * 0.035 if S["scale"] == "wide" else top_row + 3
    chim = (yy < waist - 4) & (yy > chim_top)
    chim_in = nd.binary_erosion(sil & chim, iterations=6)
    # the font's glass: the silhouette's font rows, in from its iron frame
    font_sil = sil & (yy >= ft) & (yy <= fb)
    font_in = nd.binary_erosion(font_sil, iterations=S["inset"])
    # keep only the glass band between the frame's top and bottom rims: rows whose inside spans most of the width
    fw = font_in.sum(1)
    band = fw > (fx1 - fx0) * S["band"]
    font_in &= band[:, None]
    strap = np.zeros_like(font_in)
    if "strap" in S:
        s0 = int(cx) - S["strap"][0]  # (the squat's strap: 366-423 in the source; the darkest-window search drifts right)
        strap[:, s0:s0 + S["strap"][0] + S["strap"][1]] = True
    inside = font_in & ~strap   # the glass's inside (the squat's strap out): the rim and the shield's arc
    # the cage's iron over the glass (painting px, moved into the cut and its stretch)
    for xe, te, be, xm, tm, bm in S.get("bands", []):
        u2 = ((xx - (xm - bx)) / (xm - xe)) ** 2
        t_ = rowmap(tm - by) + (te - tm) * u2
        b_ = rowmap(bm - by) + (be - bm) * u2
        strap |= font_in & (yy >= t_) & (yy <= b_)
    sl_ = blur(lum, 1.5)
    for pts, w, search in S.get("straps", []):
        py = np.array([rowmap(y - by) for _, y in pts])
        px_ = np.array([x - bx for x, _ in pts], np.float32)
        ys_ = np.arange(int(py[0]), min(int(py[-1]), H - 1) + 1)
        xc = np.interp(ys_, py, px_)
        if search:
            # each row snapped to its darkest w-wide run near the line, then smoothed (a cubic down the rib)
            k_ = np.ones(int(w)) / int(w)
            snap = []
            for y, x0_ in zip(ys_, xc):
                lo = int(x0_ - search - w / 2)
                c = np.convolve(sl_[y, lo:lo + int(2 * search + w)], k_, mode="valid")
                snap.append(lo + int(np.argmin(c)) + w / 2)
            xc = np.polyval(np.polyfit(ys_, snap, 3), ys_)
        for y, x0_ in zip(ys_, xc):
            strap[y, max(0, int(x0_ - w / 2)):int(x0_ + w / 2) + 1] = True
    oil = font_in & ~strap
    oil = blur(oil.astype(np.float32), 0.9)
    oil_rows = np.where(oil.max(1) > 0.5)[0]
    o_top, o_bot = int(oil_rows[0]), int(oil_rows[-1])
    # a band across the glass (the oil hidden over most of the middle's width): the level skips it
    mid = slice(int(cx - (fx1 - fx0) * 0.22), int(cx + (fx1 - fx0) * 0.22))
    cover = (oil[:, mid] > 0.5).mean(1)
    hid = np.zeros(H, bool)
    hid[o_top:o_bot + 1] = cover[o_top:o_bot + 1] < 0.35
    lab, n = nd.label(hid)
    skip = (0.0, 0.0)
    if n:
        sz = nd.sum(hid, lab, range(1, n + 1))
        big = 1 + int(np.argmax(sz))
        if sz[big - 1] > 6:
            ys_ = np.where(lab == big)[0]
            skip = (float(ys_[0]), float(ys_[-1] + 1))
    print(f"oil rows {o_top}-{o_bot}  skip {skip}")
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

    # the scale (2x the 1080 size): the squat's font a set width; the others fitted between the top line and
    # the floor, the flame's tip at full (flame_full over the wick) and the chimney's top both under the line
    if S["scale"] == "wide":
        k = 2 * S["wide"] / (fx1 - fx0)
    else:
        room = S["floor"] - S["top_line"]
        k = 2 * min((room - S["flame_full"] - 0.5) / (H - wick[1]), (room - 0.5) / (H - top_row))

    # 5. the eye for the chain: the carrying ring on top, turned on its side, on the font's right frame
    # (the ring is the tall lamp's carrying ring, krea lamp_b seed 4203: the same hand)
    rs = load(S["ring"])
    ra_ = np.asarray(rs, np.float32) / 255
    rrows = (ra_[..., 3] > 0.5).sum(1)
    r_bot = int(np.where(rrows > 60)[0][0]) - 1
    rx0, rx1 = np.where(ra_[:r_bot, :, 3].max(0) > 0.5)[0][[0, -1]]
    ring = ra_[:r_bot, rx0:rx1 + 1]
    g_ = ring[..., :3].mean(2, keepdims=True)
    ring[..., :3] = g_ * np.array([0.84, 0.82, 0.84]) + (ring[..., :3] - g_) * 0.25
    ring_im = Image.fromarray((np.clip(ring, 0, 1) * 255).astype(np.uint8), "RGBA").rotate(-90, expand=True, resample=Image.BICUBIC)
    kr = S.get("ring_px", RING_1080 * 2 / k) / ring_im.height
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
    inside = blur(inside.astype(np.float32), 0.9)
    oil, hl, glass_m, inear, inside = (place(m, 1)[..., 0] for m in (oil, hl, glass, iron_near, inside))
    rim = np.asarray(ring_im, np.float32) / 255
    ra = rim[..., 3:4]
    for img in (lit, cold):
        img[ey:ey + ring_im.height, ex:ex + ring_im.width] = img[ey:ey + ring_im.height, ex:ex + ring_im.width] * (1 - ra) + rim[..., :3] * ra
    A2[ey:ey + ring_im.height, ex:ex + ring_im.width] = np.maximum(A2[ey:ey + ring_im.height, ex:ex + ring_im.width], ra[..., 0])
    for m in (oil, hl, glass_m, inside):
        m[ey:ey + ring_im.height, ex:ex + ring_im.width] *= (1 - ra[..., 0])
    # the eye's hole: the ring's dark middle (its centre in the rotated ring)
    eye_c = (ex + ring_im.width * 0.62, ey + ring_im.height / 2)
    W2 = W + pad

    # 6. into the canvas at 2x the 1080 size
    if "canvas" in S:
        CANVAS = S["canvas"]
    else:
        # wide enough for the lamp and its eye, centred on the font; tall enough for the smoke over the wick
        half = max(cx, W2 - cx) * k / 2 + 6
        CANVAS = (max(176, 2 * int(np.ceil(half))), int(np.ceil((H - wick[1]) * k / 2 + 90 + FOOT_PAD)))
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
    os.makedirs(out, exist_ok=True)
    canvas(rgba(lit, A2), "RGBA").save(os.path.join(out, "lamp_lit.png"))
    canvas(rgba(cold, A2), "RGBA").save(os.path.join(out, "lamp_cold.png"))
    # (A: 1 - inside / 2, never 0, so no import's alpha-border fix can touch the other channels)
    mk = canvas(np.stack([oil, hl, glass_m], 2), "RGB")
    mk.putalpha(canvas(0.5 * inside, "L").point(lambda v: 255 - v))
    mk.save(os.path.join(out, "lamp_mask.png"))

    # 7. the flame: light-keyed, cropped above its wick holder, its foot at the bottom middle
    f = np.asarray(Image.open(S["flame"]).convert("RGB"), np.float32) / 255
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
    fl.save(os.path.join(out, "lamp_flame.png"))

    def at(p):  # source px -> 1080 px in the canvas
        return [round((ox + p[0] * k) / 2, 2), round((oy + p[1] * k) / 2, 2)]
    geo = dict(canvas=list(CANVAS), wick=at(wick), oil_top=at((cx, o_top))[1], oil_bot=at((cx, o_bot))[1],
               font_mid=at((cx, (ft + fb) / 2)), font_x=[at((fx0, 0))[0], at((fx1, 0))[0]], eye=at(eye_c),
               chim_top=at((cx, chim_top))[1], globe=[at((cx, g_top))[1], at((cx, waist))[1]], foot=at((cx, H))[1],
               flame_aspect=round(fl.height / fl.width, 3))
    # where it stands (1080): the foot's screen row, nothing above top_line, the flame's height at full, and the
    # number on the foot (between the oil's foot and the lamp's)
    geo.update(shape=shape, skip=[at((cx, skip[0]))[1], at((cx, skip[1]))[1]] if skip[1] > 0 else [0, 0], floor=S["floor"], top_line=S["top_line"], flame_full=S["flame_full"],
               number_y=S.get("number_y", round((geo["oil_bot"] + geo["foot"]) / 2, 2)),
               top=at((cx, top_row))[1])
    json.dump(geo, open(os.path.join(out, "lamp_geo.json"), "w"), indent=1)
    print(json.dumps(geo))
    if check:
        c = Image.new("RGBA", (cw, ch), (60, 70, 60, 255))
        c.alpha_composite(Image.open(os.path.join(out, "lamp_lit.png")))
        mm = np.asarray(Image.open(os.path.join(out, "lamp_mask.png")), np.float32) / 255
        ov = np.asarray(c, np.float32) / 255
        ov[..., 0] = np.maximum(ov[..., 0], mm[..., 0] * 0.8)
        ov[..., 2] = np.maximum(ov[..., 2], mm[..., 2] * 0.5)
        side = Image.fromarray((ov * 255).astype(np.uint8), "RGBA")
        cc = Image.new("RGBA", (cw, ch), (60, 70, 60, 255)); cc.alpha_composite(Image.open(os.path.join(out, "lamp_cold.png")))
        sheet = Image.new("RGB", (cw * 3, ch)); sheet.paste(c.convert("RGB"), (0, 0)); sheet.paste(cc.convert("RGB"), (cw, 0)); sheet.paste(side.convert("RGB"), (cw * 2, 0))
        sheet.save(check)


# UI 16 (27 Oct, the owner: "the typical orbs that these games have, but lets have what they are encased in show
# our themes"): a classic life orb (the glass and the blood drawn by shaders/hud_orb.gdshader) in a painted casing.
# A casing is a data block: its Krea painting (on flat black, keyed by its light; no BiRefNet), the glass's
# opening (fitted by a radial scan to the iron's inner edge), and row bands remapped [(y0, y1, f)] (f < 1
# shorter, f > 1 taller: a stem cut, an arch's legs drawn longer; none may cross the opening). Keys:
#   front    (cx, cy, a, b): an ellipse's lower half; the painting under it stays over the glass (a bowl's lip)
#   erase    [(x0, y0, x1, y1)]: pale painted bits cleared (the lamp's wick: the shader's flame stands there);
#            clear: the same, all of it
#   ember    (y0, y1): rows whose orange glow is the embers (mask R; the cold painting has them dark)
#   wick     (x, y): the flame's foot; flame_full its height at full (1080 px); eye the chain's first link;
#   break_   (deg, width deg, splay px): the shackle snapped there (orb_break); luma the iron's mean light;
#   rim      a cool light line on the outer edge above the glass's middle (its strength);
#   number   where her life's figures stand (none: on the glass, high in its middle, clear of the level's read); tint the iron's cool cast (blue-black); clip rows cut off below
# Out to lamp_life/<theme>/: lamp_lit.png (the casing, the embers glowing), lamp_cold.png (embers dark),
# lamp_mask.png (R embers, G the iron near the flame), lamp_flame.png (lamp only), lamp_geo.json.
SRC16 = INPUTS + "/ui16_orb_src/"
ORBS = {
    # The Broken Link (round 2, the judge: round 1's Krea 4604 read as a pale porthole with a latch): Krea link2
    # seed 4613, a heavy hammered shackle ring, an iron link through its foot into a rusted one; the break made
    # here (break_: at 2 o'clock, a jagged gap with bright raw fracture faces, the lower end splayed outward)
    "link": dict(src=SRC16 + "link2/cand_4613.png", rows=[], tint=(0.80, 0.85, 0.95), luma=0.19,
                 break_=(-34, 13, 34), bar=(420, (70, 110)), eye=(826, 734), eye_ring=True, clip=990,
                 backplate=True),
    # The Held Dead's Warmth: Krea seed 4603, a riveted arch over a pierced brazier bowl; the arch's legs drawn
    # longer so the glass sits whole on the bowl's lip, the bowl squashed, the embers through its slots
    "ember": dict(src=SRC16 + "ember/cand_4603.png", rows=[(430, 520, 2.0), (620, 960, 0.62)], fit_top=True,
                  front=(509, 565, 440, 37), ember=(600, 960), rim=1.0,
                  slots=(665, 905, (0, 2, 4, 7, 9, 11)), eye_ring=True, tint=(0.78, 0.80, 0.86), dark=0.82,
                  eye=(930, 600)),
    # Lamps Are Lit (round 2, the judge: round 1's crowned gimbal read as a desk globe): Krea lamp2 seed 4615, a
    # forged ring frame on three claws, a burner cup on an arm off its upper right shoulder (the flame stands in
    # it, beside the glass, not over it); the wick cleared, the claws shortened
    "lamp": dict(src=SRC16 + "lamp2/cand_4615.png", rows=[(830, 970, 0.55)], luma=0.19,
                 erase=[(835, 30, 905, 118)], wick=(862, 112), flame_full=24, tint=(0.80, 0.83, 0.92),
                 eye=(744, 925)),
}
ORB_TUCK = 6          # painting px the glass runs on under the iron round its opening
ORB_FLOOR, ORB_TOP = 1066, 904


def orb_fit(m, c0, top=False, maxr=420):
    """The opening's circle: the first iron along 180 rays from a guess, outliers (a gap, a link) dropped
    (top: the rays of its upper half only, an arch's)."""
    pts = []
    for t in np.linspace(np.pi, 2 * np.pi, 90) if top else np.linspace(0, 2 * np.pi, 180, endpoint=False):
        for r in range(30, maxr):
            x, y = int(c0[0] + r * np.cos(t)), int(c0[1] + r * np.sin(t))
            if not (0 <= x < m.shape[1] and 0 <= y < m.shape[0]):
                break
            if m[y, x]:
                pts.append((x, y, r))
                break
    P = np.array(pts, float)
    med = np.median(P[:, 2])
    P = P[np.abs(P[:, 2] - med) < 0.12 * med]
    A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]
    cx, cy, c = np.linalg.lstsq(A, P[:, 0] ** 2 + P[:, 1] ** 2, rcond=None)[0]
    return cx, cy, float(np.sqrt(c + cx * cx + cy * cy))


def orb_break(rgb, A, cx, cy, r, ang, width, splay):
    """The shackle snapped: a gap at ang degrees (0 = 3 o'clock, negative up) width degrees wide, its edges
    ragged; the end below it splayed outward (splay px at the break, easing back over 40 degrees); the fracture
    faces (px within ~6 of the gap) returned for raw metal."""
    H, W = A.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rr = np.hypot(xx - cx, yy - cy)
    th = np.degrees(np.arctan2(yy - cy, xx - cx))
    rng = np.random.default_rng(16)
    jag = np.interp(rr, np.arange(0, 600, 9), rng.uniform(-1, 1, len(np.arange(0, 600, 9)))) * width * 0.07
    t0, t1 = ang - width / 2 + jag, ang + width / 2 - jag * 0.7
    # the lower end bent out: sample it from nearer the middle
    past = np.clip(t0 - th, 0, None)
    s = splay * np.clip(1 - past / 40, 0, 1) ** 2 * (th < t0)
    src_r = rr - s
    sx = cx + src_r * np.cos(np.radians(th))
    sy = cy + src_r * np.sin(np.radians(th))
    warp = lambda a_: nd.map_coordinates(a_, [sy, sx], order=1, mode="constant")
    rgb = np.stack([warp(rgb[..., i]) for i in range(3)], 2)
    A = warp(A)
    ring = rr > r - 4
    gap = ((th > t0) & (th < t1) & ring).astype(np.float32)
    gap = blur(gap, 0.8)
    A = A * (1 - gap)
    # the faces: just outside the gap's two edges, on the iron
    dist = np.minimum(np.abs(th - t0), np.abs(th - t1)) * np.radians(1) * rr
    face = np.clip(1.3 - dist / 20, 0, 1) * (1 - gap) * (A > 0.5) * ring
    face *= 0.6 + 0.4 * blur(rng.random((H, W)), 0.6) / 0.5 * 0.5
    return rgb, A, blur(face.astype(np.float32), 0.7)


def orb_bar(rgb, A, cx, cy, r_in, r_out, skip):
    """The shackle shaded as a round bar lit from the upper left (a lit ridge, its lower right in shadow), its
    hammered texture kept at 60%; the sector skip (degrees, 90 = 6 o'clock: the link through it) left as painted."""
    H, W = A.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rr = np.hypot(xx - cx, yy - cy)
    dx, dy = (xx - cx) / np.maximum(rr, 1), (yy - cy) / np.maximum(rr, 1)
    sgn = np.clip(2 * (rr - r_in) / (r_out - r_in) - 1, -1, 1)
    nz = np.sqrt(np.clip(1 - sgn * sgn, 0, 1))
    L = np.array([-0.55, -0.65, 0.55]); L /= np.linalg.norm(L)
    Hh = L + np.array([0, 0, 1.0]); Hh /= np.linalg.norm(Hh)
    nx, ny = sgn * dx, sgn * dy
    diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    spec = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1) ** 28
    tone = 0.07 + 0.42 * diff + 0.40 * spec
    lum = rgb.mean(2)
    detail = lum - blur(lum, 5)
    bar = (tone + 0.6 * detail)[..., None] * np.array([0.95, 1.0, 1.08])
    th = np.degrees(np.arctan2(yy - cy, xx - cx))
    keep = np.clip((np.abs(th - (skip[0] + skip[1]) / 2) - (skip[1] - skip[0]) / 2) / 10, 0, 1)
    w = (A > 0.02) * (rr > r_in - 6) * (rr < r_out + 45) * keep
    # (the link through its foot: brought up to the ring's light, its texture calmed)
    link = (A > 0.02) * (1 - keep) * (rr > r_in - 6)
    calm = np.stack([blur(rgb[..., i], 1.5) for i in range(3)], 2) * 0.6 + rgb * 0.4
    rgb = rgb * (1 - link[..., None]) + np.clip(calm * 1.45, 0, 1) * link[..., None]
    return rgb * (1 - w[..., None]) + bar * w[..., None]


def orb_slots(rgb, A, y0, y1, keep):
    """A grille's slots thinned to heavier bars: the slots (dark or glowing runs in rows y0-y1) numbered left to
    right, those not in keep filled with the iron either side (blended across, the left bar's grain laid on)."""
    lum = rgb.mean(2)
    hot = (rgb[..., 0] - rgb[..., 2] > 0.14) & (rgb[..., 0] > 0.22)
    m = np.zeros(lum.shape, bool)
    m[y0:y1] = ((lum < 0.09) | hot)[y0:y1] & (A[y0:y1] > 0.5)
    m = nd.binary_opening(m, iterations=1)
    lab, n = nd.label(m)
    sz = nd.sum(m, lab, range(1, n + 1))
    big = [i + 1 for i in range(n) if sz[i] > 800]
    big.sort(key=lambda i: nd.center_of_mass(m, lab, i)[1])
    print(f"slots: {len(big)} found, keeping {keep}")
    out = rgb.copy()
    detail = rgb - np.stack([blur(rgb[..., i], 4) for i in range(3)], 2)
    for j, i in enumerate(big):
        if j in keep:
            continue
        sm = nd.binary_dilation(lab == i, iterations=3)
        ys = np.where(sm.any(1))[0]
        for y in ys:
            xs_ = np.where(sm[y])[0]
            a, b = xs_[0] - 2, xs_[-1] + 3
            w = b - a
            t_ = np.linspace(0, 1, w)[:, None]
            base = rgb[y, a] * (1 - t_) + rgb[y, b] * t_
            out[y, a:b] = base + detail[y, a - w:b - w] * 0.8
    return out


def orb(theme, check=None):
    S = ORBS[theme]
    out = os.path.join(ART, theme)
    rgb = np.asarray(Image.open(S["src"]).convert("RGB"), np.float32) / 255
    H0, W0 = rgb.shape[:2]
    lum = blur(rgb.mean(2), 1.2)
    # keyed by its light (the black ground 0.00-0.03): soft alpha, specks dropped
    A = np.clip((lum - 0.035) / 0.035, 0, 1)
    lab, n = nd.label(A > 0.5)
    sz = nd.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.where(sz > 3000)[0])
    A *= blur(nd.binary_dilation(keep, iterations=3).astype(np.float32), 1.0)
    for x0, y0, x1, y1 in S.get("erase", []):
        pale = (rgb[y0:y1, x0:x1].mean(2) > 0.32) & (rgb[y0:y1, x0:x1, 0] - rgb[y0:y1, x0:x1, 2] > 0.06)
        pale = blur(nd.binary_dilation(pale, iterations=3).astype(np.float32), 1.5)
        A[y0:y1, x0:x1] *= 1 - pale
    for x0, y0, x1, y1 in S.get("clear", []):
        A[y0:y1, x0:x1] = 0
    if "clip" in S:
        A[S["clip"]:] *= 0
    cx, cy, r = orb_fit(A > 0.5, (W0 / 2, H0 * 0.42), S.get("fit_top", False))
    print(f"{theme}: opening c ({cx:.1f}, {cy:.1f}) r {r:.1f}")
    face = np.zeros((H0, W0), np.float32)
    if "break_" in S:
        rgb, A, face = orb_break(rgb, A, cx, cy, r, *S["break_"])
    if "bar" in S:
        rgb = orb_bar(rgb, A, cx, cy, r, *S["bar"])
    if "slots" in S:
        rgb = orb_slots(rgb, A, *S["slots"])
    # the embers: orange light in the bowl's rows (lit keeps them; cold has them dark, the shader brings them up)
    emb = np.zeros((H0, W0), np.float32)
    if "ember" in S:
        e0, e1 = S["ember"]
        o = np.clip((rgb[..., 0] - rgb[..., 2] - 0.14) * 4, 0, 1) * np.clip((rgb[..., 0] - 0.22) * 4, 0, 1)
        emb[e0:e1] = o[e0:e1]
        emb = blur(emb, 0.8)
    # the iron cooled to blue-black, the painting's light kept
    g = rgb.mean(2, keepdims=True)
    iron = g * np.array(S["tint"]) * S.get("dark", 1.0) + (rgb - g) * 0.18
    if "luma" in S:
        # (the iron at the HUD's own value: its mean light over the casing)
        cur = float((iron.mean(2) * A).sum() / max(A.sum(), 1))
        iron *= S["luma"] / cur
        print(f"{theme}: iron luma {cur:.3f} -> {S['luma']}")
    # the fracture's raw metal: bright, cold, ragged
    raw = np.array([0.40, 0.42, 0.46]) * (0.8 + 0.4 * np.random.default_rng(7).random((H0, W0, 1)))
    iron = iron * (1 - face[..., None]) + raw * face[..., None]
    if "rim" in S:
        # a cool line of light on the outer edge above the glass's middle (it holds against dark ground)
        edge = np.clip(A - blur(nd.grey_erosion(A, size=(7, 7)), 1.0), 0, 1) * (yy_ := np.mgrid[0:H0, 0:W0][0] < cy)
        edge *= np.hypot(np.mgrid[0:H0, 0:W0][1] - cx, np.mgrid[0:H0, 0:W0][0] - cy) > r + 12
        iron += edge[..., None] * np.array([0.30, 0.34, 0.42]) * S["rim"]
    lit = iron * (1 - emb[..., None]) + rgb * emb[..., None]
    cold = iron * (1 - emb[..., None]) + rgb * emb[..., None] * 0.12
    for y0, y1, f in S["rows"]:
        # (the opening's upper half stays as painted; under its middle a band may draw an arch's legs longer)
        assert y1 <= cy - r or y0 >= cy, f"{theme}: band {y0}-{y1} crosses the opening's upper half"
    # the row bands remapped: out row -> painting row, piecewise linear
    knots_s, knots_o, o_, s_ = [0.0], [0.0], 0.0, 0.0
    for y0, y1, f in sorted(S["rows"]):
        o_ += y0 - s_; knots_s.append(y0); knots_o.append(o_)
        o_ += (y1 - y0) * f; knots_s.append(y1); knots_o.append(o_)
        s_ = y1
    o_ += H0 - s_; knots_s.append(H0); knots_o.append(o_)
    H = int(round(o_))
    src_rows = np.interp(np.arange(H) + 0.5, knots_o, knots_s) - 0.5
    rowmap = lambda y: float(np.interp(y, knots_s, knots_o))
    grid = [np.repeat(src_rows[:, None], W0, 1), np.tile(np.arange(W0, dtype=np.float32), (H, 1))]
    remap = lambda a_: nd.map_coordinates(a_, grid, order=1, mode="nearest")
    lit = np.stack([remap(lit[..., i]) for i in range(3)], 2)
    cold = np.stack([remap(cold[..., i]) for i in range(3)], 2)
    A, emb = remap(A), remap(emb)
    cy_o = rowmap(cy)
    yy, xx = np.mgrid[0:H, 0:W0].astype(np.float32)
    # the opening cleared (the glass shows), feathered 1.5 px; under a bowl's lip the painting stays in front
    hole = np.clip((r - 2 - np.hypot(xx - cx, yy - cy_o)) / 1.5, 0, 1)
    if "front" in S:
        fx, fy, fa, fb = S["front"]
        lip = rowmap(fy) + fb * np.sqrt(np.clip(1 - ((xx - fx) / fa) ** 2, 0, 1))
        hole *= np.clip((lip - yy) / 1.5, 0, 1)
    A *= 1 - hole
    if S.get("backplate"):
        # an opaque soot plate in any gap inside the casing's outline (the scene never shows through it)
        disk = np.hypot(xx - cx, yy - cy_o) < r + ORB_TUCK
        inner = nd.binary_fill_holes((A > 0.3) | disk) & ~(np.hypot(xx - cx, yy - cy_o) < r - 2)
        plate = blur((inner & (A < 0.95)).astype(np.float32), 0.7) * inner
        soot = np.array([0.035, 0.036, 0.042])
        lit = lit * A[..., None] + soot * plate[..., None] * (1 - A[..., None])
        cold = cold * A[..., None] + soot * plate[..., None] * (1 - A[..., None])
        A = np.maximum(A, plate)
        lit /= np.maximum(A, 1e-3)[..., None]; cold /= np.maximum(A, 1e-3)[..., None]
    sil = A > 0.3
    rows_ = np.where(sil.any(1))[0]
    top_row, bot_row = int(rows_[0]), int(rows_[-1]) + 1
    cols_ = np.where(sil.any(0))[0]
    x0_, x1_ = int(cols_[0]), int(cols_[-1]) + 1
    # the scale: all of it (the flame's tip at full included) between ORB_TOP and ORB_FLOOR
    room = ORB_FLOOR - ORB_TOP - FOOT_PAD
    ff = S.get("flame_full", 0)
    k1 = room / (bot_row - top_row)
    if "wick" in S:
        k1 = min(k1, (room - ff) / (bot_row - rowmap(S["wick"][1])))
    print(f"{theme}: k {k1:.4f}  glass {2 * r * k1:.1f} px  casing {(bot_row - top_row) * k1:.1f} px")
    # into the canvas at twice the 1080 size, the orb's middle at the canvas's middle
    half = max(cx - x0_, x1_ - cx) * k1 + 4
    if S.get("eye_ring"):
        half = max(half, (S["eye"][0] - cx) * k1 + 30)
    CANVAS = (2 * int(np.ceil(half)), int(room + FOOT_PAD + 2))
    cw, ch = CANVAS[0] * 2, CANVAS[1] * 2
    K = 2 * k1
    ox = round(cw / 2 - cx * K)
    oy = round(ch - FOOT_PAD * 2 - bot_row * K)
    lw, lh = round(W0 * K), round(H * K)
    def canvas(arr, mode):
        im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), mode).resize((lw, lh), Image.LANCZOS)
        c = Image.new(mode, (cw, ch), 0 if mode == "L" else (0,) * len(mode))
        c.paste(im, (ox, oy))
        return c
    # (the colour bled out under the alpha's edge, so filtering keeps no dark fringe)
    wsum = blur(A, 3)[..., None]
    def bleed(c_):
        est = np.stack([blur(c_[..., i] * A, 3) for i in range(3)], 2) / np.maximum(wsum, 1e-4)
        return np.where(A[..., None] > 0.02, c_, est)
    os.makedirs(out, exist_ok=True)
    L_im = canvas(np.concatenate([bleed(lit), A[..., None]], 2), "RGBA")
    C_im = canvas(np.concatenate([bleed(cold), A[..., None]], 2), "RGBA")
    eye_px = None
    if S.get("eye_ring"):
        # the chain's eye: the squat lamp's forged carrying ring (Krea lamp_b seed 4203), on its side, its left end
        # on the casing's iron at the eye; the HUD's chain hangs from its hole
        rs = load(S.get("ring", SRC14 + "cand_4203_cut.png"))
        ra_ = np.asarray(rs, np.float32) / 255
        rrows = (ra_[..., 3] > 0.5).sum(1)
        r_bot = int(np.where(rrows > 60)[0][0]) - 1
        rx0, rx1 = np.where(ra_[:r_bot, :, 3].max(0) > 0.5)[0][[0, -1]]
        ring = ra_[:r_bot, rx0:rx1 + 1].copy()
        g_ = ring[..., :3].mean(2, keepdims=True)
        ring[..., :3] = g_ * np.array([0.80, 0.84, 0.92]) * 0.8 + (ring[..., :3] - g_) * 0.15
        ri = Image.fromarray((np.clip(ring, 0, 1) * 255).astype(np.uint8), "RGBA").rotate(-90, expand=True, resample=Image.BICUBIC)
        kr = RING_1080 * 2 * 1.3 / ri.height
        ri = ri.resize((max(1, round(ri.width * kr)), round(ri.height * kr)), Image.LANCZOS)
        ex2 = ox + S["eye"][0] * K - ri.width * 0.12
        ey2 = oy + rowmap(S["eye"][1]) * K - ri.height / 2
        for im_ in (L_im, C_im):
            im_.alpha_composite(ri, (round(ex2), round(ey2)))
        eye_px = [round((ex2 + ri.width * 0.62) / 2, 2), round((ey2 + ri.height / 2) / 2, 2)]
    L_im.save(os.path.join(out, "lamp_lit.png"))
    C_im.save(os.path.join(out, "lamp_cold.png"))
    near = np.zeros((H, W0), np.float32)
    if "wick" in S:
        yy2, xx2 = np.mgrid[0:H, 0:W0].astype(np.float32)
        near = np.exp(-np.hypot(xx2 - S["wick"][0], (yy2 - rowmap(S["wick"][1])) * 0.8) / 120) * (A > 0.3)
    mk = canvas(np.stack([emb, near, np.zeros_like(emb)], 2), "RGB")
    mk.putalpha(255)
    mk.save(os.path.join(out, "lamp_mask.png"))
    def at(x, y):  # painting px (before the remap) -> 1080 px in the canvas
        return [round((ox + x * K) / 2, 2), round((oy + rowmap(y) * K) / 2, 2)]
    c1080 = at(cx, cy)
    geo = dict(shape=theme, canvas=list(CANVAS), orb_c=c1080, orb_r=round((r + ORB_TUCK) * k1, 2), orb_vis=round(r * k1, 2),
               font_mid=c1080, eye=at(*S["eye"]), foot=round((oy + bot_row * K) / 2, 2), top=round((oy + top_row * K) / 2, 2),
               floor=ORB_FLOOR, top_line=ORB_TOP,
               number_y=at(*S["number"])[1] if "number" in S else round(c1080[1] - 0.45 * r * k1, 2), flame_full=ff, glass_px=round(2 * r * k1, 1))
    geo["footprint"] = round(geo["foot"] - geo["top"], 1)
    if eye_px:
        geo["eye"] = eye_px
    if "wick" in S:
        import shutil
        geo["wick"] = at(*S["wick"])
        shutil.copy(os.path.join(ART, "lamp_flame.png"), os.path.join(out, "lamp_flame.png"))
        geo["flame_aspect"] = round(Image.open(os.path.join(out, "lamp_flame.png")).height / 128, 3)
        geo["footprint"] = round(geo["foot"] - min(geo["top"], geo["wick"][1] - ff), 1)
    # (the lamp's keys LifeLamp still reads, kept sane)
    geo.update(oil_top=round(c1080[1] - geo["orb_vis"], 2), oil_bot=round(c1080[1] + geo["orb_vis"], 2),
               font_x=[round(c1080[0] - geo["orb_vis"], 2), round(c1080[0] + geo["orb_vis"], 2)], skip=[0, 0])
    json.dump(geo, open(os.path.join(out, "lamp_geo.json"), "w"), indent=1)
    print(json.dumps(geo))
    if check:
        c = Image.new("RGBA", (cw, ch), (40, 52, 70, 255))
        gy, gx = np.mgrid[0:ch, 0:cw].astype(np.float32)
        q = np.hypot(gx - c1080[0] * 2, gy - c1080[1] * 2) < geo["orb_r"] * 2
        g_ = np.zeros((ch, cw, 4), np.uint8); g_[q] = (150, 20, 25, 255)
        c.alpha_composite(Image.fromarray(g_, "RGBA")); c.alpha_composite(Image.open(os.path.join(out, "lamp_lit.png")))
        c2 = Image.new("RGBA", (cw, ch), (40, 52, 70, 255)); c2.alpha_composite(Image.open(os.path.join(out, "lamp_cold.png")))
        sh = Image.new("RGB", (cw * 2, ch)); sh.paste(c.convert("RGB"), (0, 0)); sh.paste(c2.convert("RGB"), (cw, 0)); sh.save(check)


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    chk = sys.argv[sys.argv.index("--check") + 1] if "--check" in sys.argv else None
    if chk in args: args.remove(chk)
    sh_ = args[0] if args else "squat"
    orb(sh_, chk) if sh_ in ORBS else main(sh_, chk)
