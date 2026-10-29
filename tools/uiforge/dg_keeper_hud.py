"""UI 23, HUD A "the keeper" (the owner's pick): bake the judged 2D mockup's art at 2x the 1080 screen px.

    python tools/uiforge/dg_keeper_hud.py            (reads tools/uiforge/dg_keeper_src only)

The source of truth was the UI 23 mockup (R6 mock7.py, env DXG=0 GAP_R=-17 KEEPER=ks60_2304_0 KLOCK=1) with the judge's
fixes; its reference copy with the fixes is mock8.py (same folder in the session scratch). This script ports its math:
  girl   art/ui/lamp_life/drowned/lamp_cold.png (girl_R6.png, 2x as before; the globe hole kept for the orb shader) with
         G1 (a see-through window in her hair at screen x 604-616, y 1016-1040 filled with hair + one strand), and
         lamp_mask.png (R her fingertips over the glass, G the R5 hand and forearm). Then run dg_xp_mask.py (hair shine).
  keeper art/ui/dg_keeper/keeper.png (straight RGBA, 2x): gen ks60_2304_0 (Krea 2 turbo i2i) cut, two bilateral passes,
         the Lab grade onto the girl, the mock's final a/b shift and gain (keeper_grade.json, dumped by mock8 day), the
         mirrored back lock (K1: 10 px left, 4 px down), K4 (the brightest tenth +12/255 luma, -0.03 saturation, away
         from the fire). Day and night use this one sprite (K3). keeper_lip.png: the bowl's front, drawn over the glass.
  panel  art/ui/dg_panel/panel.png (2x): the plate (P1 one end piece mirrored, lit from straight above, the end contour
         = the more outward figure edge set 7 px in; P2 a 3 px contact shadow at the ends; the inlay snapped to whole
         1080 px), the seat bezels, the coin's dish, ring and XP groove. Live (not baked): icons, flask, dash, the XP
         fill, the level number, key tags, rank chips, the glass.
  fire   art/ui/dg_keeper/fire.png (idle wall of flame, gen fw_9931_0), fire_ready.png (READY orb, gen fo_9932_0).
  geo    art/ui/dg_keeper/hud_a_geo.json (1080 px screen coords; rects are continuous left/top edges, pixel i = [i, i+1]).
"""
import json, os, shutil, sys
import numpy as np
from PIL import Image
from scipy import ndimage
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC = os.path.join(HERE, 'dg_keeper_src')
UI = os.path.join(ROOT, 'godot', 'art', 'ui')
G_ = ndimage.gaussian_filter
LUMW = np.array([0.2126, 0.7152, 0.0722], np.float32)
W1, H1 = 1920, 1080

# ---------------------------------------------------------------- the design (1080 px), as in mock7/mock8
WELL_R, BEZ = 31.5, 3.5
SEAT_R = WELL_R + BEZ
SEAT_Y, MED_R, GAP = 1042.0, 37.0, 5.0
PITCH = 2 * SEAT_R + GAP
SEAT_XS = [960 - MED_R - GAP - SEAT_R - k * PITCH for k in (2, 1, 0)] + [960 + MED_R + GAP + SEAT_R + k * PITCH for k in (0, 1, 2)]
FLASK_X = SEAT_XS[0] - SEAT_R - 4 - 21
DASH_X = 1920 - FLASK_X
VOL_R, PL_X0, PL_X1, PL_TOP, ARCH_R = 12.0, 626.0, 1294.0, 1003.0, MED_R + 6.0
INSET = 6.5
INL = 6.5            # snap: the inlay's top run centred on the 1080 px row 1009 (was 6.0: on the 1008/1009 seam)
TUCK = 7.0           # P1: the end side sits this far over the more outward figure's edge
DEPTH = (4.0, 10.0)  # every figure edge row sits this far under the panel
LD_PLATE = np.array([0.0, -0.816, 0.578], np.float32)   # P1: lit from straight above (the field's z kept)
PANEL_RECT = (576, 988, 768, 92)                          # symmetric about 960
S, ANCHOR = 0.94, (295.33, 1080.0)
GIRL_AT, GIRL_SIZE = (294.83, 822.0), (474.67, 258.0)    # place() convention (the frame's best match)
GLOBE = (378.0, 960.0, 59.4)
K_S, K_TOP, GAP_R = 0.28, 205.0, -17.0
LOCK_D = (-10.0, 4.0)                                     # K1: the mirrored back lock moved left and down
EG_R = 37.0


def sm(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def load_rgba(p):
    return np.asarray(Image.open(p).convert('RGBA'), np.float32) / 255


def load_rgb(p):
    return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255


def premul(a):
    o = a.copy(); o[..., :3] *= o[..., 3:4]; return o


def straight(L):
    a = np.maximum(L[..., 3:4], 1e-5)
    return np.where(L[..., 3:4] > 1e-4, L[..., :3] / a, 0)


def over(dst, src):
    return src + dst * (1 - src[..., 3:4])


def place(art, x0, y0, w, h, canvas):
    """parts.place with any canvas: straight RGBA art to the rect (x0, y0, w, h) in canvas px, premultiplied out."""
    pm = premul(art)
    ah, aw = pm.shape[:2]
    sx, sy = aw / w, ah / h
    X0, Y0 = int(np.floor(x0)) - 1, int(np.floor(y0)) - 1
    X1, Y1 = int(np.ceil(x0 + w)) + 1, int(np.ceil(y0 + h)) + 1
    ow, oh = X1 - X0, Y1 - Y0
    aff = (sx, 0, (X0 - x0) * sx + 0.5 * sx - 0.5, 0, sy, (Y0 - y0) * sy + 0.5 * sy - 0.5)
    out = np.zeros((canvas[1], canvas[0], 4), np.float32)
    chans = []
    for k in range(4):
        im = Image.fromarray(np.ascontiguousarray(pm[..., k]), 'F')
        if sx > 1.5 or sy > 1.5:
            im = im.resize((max(1, round(aw / sx)), max(1, round(ah / sy))), Image.LANCZOS)
            chans.append(np.asarray(im.transform((ow, oh), Image.AFFINE, (1.0, 0, X0 - x0, 0, 1.0, Y0 - y0), resample=Image.BICUBIC)))
        else:
            chans.append(np.asarray(im.transform((ow, oh), Image.AFFINE, aff, resample=Image.BICUBIC)))
    r = np.stack(chans, -1)
    r[..., 3] = np.clip(r[..., 3], 0, 1)
    r[..., :3] = np.clip(r[..., :3], 0, r[..., 3:4] + 1e-6)
    xa, ya, xb, yb = max(0, X0), max(0, Y0), min(canvas[0], X1), min(canvas[1], Y1)
    if xb > xa and yb > ya:
        out[ya:yb, xa:xb] = r[ya - Y0:yb - Y0, xa - X0:xb - X0]
    return out


def ss_grid(x0, y0, x1, y1, ss):
    gy, gx = np.mgrid[0:int(round((y1 - y0) * ss)), 0:int(round((x1 - x0) * ss))].astype(np.float32)
    return x0 + (gx + 0.5) / ss, y0 + (gy + 0.5) / ss


def ss_down(a, ss):
    h, w = a.shape[:2]
    return a.reshape(h // ss, ss, w // ss, ss, *a.shape[2:]).mean((1, 3))


def lab_of(rgb):
    return cv2.cvtColor((np.clip(rgb, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)


def lab2rgb(lab):
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32) / 255


def save_rgba(path, L_straight):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray((np.clip(L_straight, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(path, optimize=True)


def girl_screen_rect(dxg=0.0):
    """her art's rect on screen after the 0.94 about her outer bottom corner"""
    x0 = ANCHOR[0] + (GIRL_AT[0] - ANCHOR[0]) * S + dxg
    y0 = ANCHOR[1] + (GIRL_AT[1] - ANCHOR[1]) * S
    return x0, y0, GIRL_SIZE[0] * S, GIRL_SIZE[1] * S


# ================================================================== the girl (G1) and her masks
G1_SCREEN = (604, 1016, 616, 1040)
G1_TONE = np.array([39, 36, 29], np.float32) / 255
G1_STRAND = [(666.0, 386.0), (670.0, 396.0), (673.5, 406.0), (675.5, 416.0), (676.5, 426.0)]   # art px, down the hole


def screen_to_art(px, py):
    ax, ay = ANCHOR[0] + (px - ANCHOR[0]) / S, ANCHOR[1] + (py - ANCHOR[1]) / S
    return (ax - GIRL_AT[0]) * 949 / GIRL_SIZE[0], (ay - GIRL_AT[1]) * 516 / GIRL_SIZE[1]


def fix_girl(art):
    """G1: the see-through window in her hair (screen x 604-616, y 1016-1040) filled with hair: the surround inpainted,
    toned to the hollow's (39,36,29), one strand line down its long axis."""
    a = art[..., 3]
    x0, y0 = screen_to_art(G1_SCREEN[0], G1_SCREEN[1])
    x1, y1 = screen_to_art(G1_SCREEN[2], G1_SCREEN[3])
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    box = (xx > x0 - 12) & (xx < x1 + 12) & (yy > y0 - 12) & (yy < y1 + 12)
    solid = a > 0.5
    hole = ndimage.binary_fill_holes(solid) & ~solid & box
    if not hole.any():
        return art, 0
    hole_d = ndimage.binary_dilation(hole, iterations=2) & box
    u8 = (np.clip(art[..., :3], 0, 1) * 255).astype(np.uint8)
    inp = cv2.inpaint(u8, hole_d.astype(np.uint8) * 255, 6, cv2.INPAINT_TELEA).astype(np.float32) / 255
    fill = inp * 0.45 + G1_TONE * 0.55
    # one strand: a thin lit line down the hollow
    pts = np.array(G1_STRAND, np.float32)
    dmin = np.full(a.shape, 1e3, np.float32)
    for (ax_, ay_), (bx_, by_) in zip(pts[:-1], pts[1:]):
        vx, vy = bx_ - ax_, by_ - ay_
        t = np.clip(((xx - ax_) * vx + (yy - ay_) * vy) / (vx * vx + vy * vy), 0, 1)
        dmin = np.minimum(dmin, np.hypot(xx - ax_ - t * vx, yy - ay_ - t * vy))
    ln = np.exp(-(dmin / 1.0) ** 2)[..., None]
    fill = fill * (1 - 0.65 * ln) + np.array([86, 76, 58], np.float32) / 255 * 0.65 * ln
    wgt = np.clip(G_(hole_d.astype(np.float32), 0.8) * 1.6, 0, 1) * box
    wgt = np.maximum(wgt, hole)
    out = art.copy()
    out[..., :3] = art[..., :3] * (1 - wgt[..., None]) + fill * wgt[..., None]
    out[..., 3] = np.maximum(a, (hole_d & ndimage.binary_fill_holes(solid)).astype(np.float32))
    return out, int(hole.sum())


def lamp_mask(art):
    """R: her parts over the glass (the R5 fingertips and thumb inside the globe's circle); G: the R5 hand and forearm"""
    h, w = art.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    gx, gy, gr = 166.3, 276.0, 118.8            # the globe in art px (girl5.py)
    d = np.hypot(xx - gx, yy - gy)
    R = art[..., 3] * sm(gr + 1.5, gr - 0.5, d)
    hand = np.asarray(Image.open(os.path.join(SRC, 'hand_R5.png')), np.float32) / 255
    Gm = np.clip(hand, 0, 1) * art[..., 3]
    return np.dstack([R, Gm, np.zeros_like(R)])


# ================================================================== the keeper
def keeper_source():
    k_rgb = load_rgb(os.path.join(SRC, 'ks60_2304_0.png'))
    k_a = load_rgba(os.path.join(SRC, 'ks60_2304_0_cut.png'))[..., 3]
    return k_rgb, k_a


def keeper_geom(k_a):
    k_top = np.nonzero((k_a > 0.5).any(1))[0].min()
    k_left = np.nonzero((k_a > 0.5).any(0))[0].min()
    kx0 = PL_X1 + GAP_R + 1.0 - k_left * K_S
    ky0 = (1080 - K_TOP) - k_top * K_S
    return kx0, ky0


def keeper_graded(k_rgb, k_a, gr):
    """keeper_layer() in the source's own pixels: two bilateral passes, the Lab grade onto the girl (gr: the numbers
    mock8 measured on the girl), the fire kept; then the mock's final a/b shift and gain."""
    a = np.clip(k_a, 0, 1)
    st = np.clip(k_rgb / np.maximum(a, 0.25)[..., None], 0, 1)
    st = np.where(a[..., None] > 0.02, st, 0)
    u8 = (st * 255).astype(np.uint8)
    for _ in range(2):
        u8 = cv2.bilateralFilter(u8, 0, 18, 6)
    st = u8.astype(np.float32) / 255
    hsv = cv2.cvtColor((st * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    fire = sm(0.45, 0.75, hsv[..., 1] / 255) * sm(0.35, 0.65, hsv[..., 2] / 255) * (hsv[..., 0] < 30)
    fire = G_(fire, 1.0)
    lab = lab_of(st)
    lab2 = lab.copy()
    lab2[..., 0] = np.interp(lab[..., 0], gr['kq'], gr['gq'])
    lab2[..., 1] = gr['g_a'] + (lab[..., 1] - gr['ka']) * (gr['sg'] / gr['sk'])
    lab2[..., 2] = gr['g_b'] + (lab[..., 2] - gr['kb']) * (gr['sg'] / gr['sk'])
    rgb = lab2rgb(lab2)
    rgb = rgb * (1 - fire[..., None]) + st * fire[..., None]
    return final_grade(rgb, fire, gr), a, fire


def final_grade(rgb, fire, gr):
    kl = lab_of(rgb)
    kl[..., 1] += gr['DA'] * (1 - fire); kl[..., 2] += gr['DB'] * (1 - fire)
    rgb = lab2rgb(kl)
    return rgb * (gr['kgain'] * (1 - fire) + fire)[..., None]


def k4_curve(rgb, away, thr):
    """K4: the brightest tenth of the bronze (luma over the keeper's p90 thr) +12/255 luma and -0.03 saturation,
    feathered in over 0.03 of luma so the midtones (and p90 itself) stay; away: 1 off the fire and the glass."""
    Y = rgb @ LUMW
    w = sm(thr, thr + 0.03, Y) * away
    out = rgb + (12.0 / 255) * w[..., None]
    V = out.max(-1); mn = out.min(-1)
    Sat = (V - mn) / np.maximum(V, 1e-4)
    S2 = np.clip(Sat - 0.03 * w, 0, 1)
    f = np.where(Sat > 1e-3, S2 / np.maximum(Sat, 1e-3), 1.0)
    out = V[..., None] - (V[..., None] - out) * f[..., None]
    return np.clip(out, 0, 1)


def lock_window(X, Y):
    """the mirrored back lock's window (mock7 KLOCK block), moved by K1; X, Y in mock pixel-index units"""
    dx, dy = LOCK_D
    w = sm(1336.0 + dx, 1318.0 + dx, X) * sm(966.0 + dy, 984.0 + dy, Y) * (X > 1280 + dx)
    # below the cap the lock reaches no further in than her edge's mirror (so both ends tuck the same under one mirrored end)
    ge = girl_edge_rows()
    xc = 1920.0 - np.interp(Y + 0.5, np.arange(1080) + 0.5, ge)
    return w * np.maximum(sm(xc - 1.0, xc + 1.0, X + 0.5), 1 - sm(PL_TOP + VOL_R - 4, PL_TOP + VOL_R, Y + 0.5))


_GE = {}


def girl_edge_rows():
    """her right edge (alpha > 0.5, 1080 px) per screen row, from her (fixed) art at its 0.94 rect; -1e3 where none"""
    if 'ge' not in _GE:
        art, _ = fix_girl(load_rgba(os.path.join(SRC, 'girl_R6.png')))
        x0, y0, w, h = girl_screen_rect()
        a = place(art, x0 * 4, y0 * 4, w * 4, h * 4, (960 * 4, 1080 * 4))[..., 3]
        ge = np.full(1080, -1e3)
        for r in range(1080):
            m = (a[r * 4:r * 4 + 4] > 0.5).any(0)
            if m.any():
                ge[r] = (np.nonzero(m)[0].max() + 1) / 4.0
        _GE['ge'] = ge
    return _GE['ge']


def plug_holes(L, region, max_area):
    """K1: fill small see-through holes in a premultiplied layer's alpha inside region (bool), colour from round it"""
    solid = L[..., 3] > 0.5
    holes = ndimage.binary_fill_holes(solid) & ~solid & region
    lab, n = ndimage.label(holes)
    if n == 0:
        return L, 0
    sz = ndimage.sum(np.ones_like(L[..., 3]), lab, range(1, n + 1))
    hole = np.isin(lab, 1 + np.nonzero(sz <= max_area)[0])
    if not hole.any():
        return L, 0
    hd = ndimage.binary_dilation(hole, iterations=1) & (L[..., 3] < 0.98)
    num = np.stack([G_(L[..., c] * solid, 2.0) for c in range(3)], -1)
    den = G_(solid.astype(np.float32), 2.0)[..., None]
    col = num / np.maximum(den, 1e-4)
    out = L.copy()
    m = hd[..., None]
    out[..., :3] = np.where(m, col, L[..., :3])
    out[..., 3] = np.where(hd, 1.0, L[..., 3])
    return out, int(hole.sum())


# ================================================================== the panel (P1, P2, snapped inlay)
def figure_edges(ga, ka, Z, y0):
    """per row (1080-px row centres) the girl's right edge and the keeper's left edge (alpha > 0.5); ga, ka are
    full-width (1920 Z) arrays from screen row y0."""
    n = ga.shape[0]
    rows = y0 + (np.arange(n) + 0.5) / Z
    half = int(960 * Z)
    ge = np.array([np.nonzero(ga[r, :half] > 0.5)[0].max() + 1.0 if (ga[r, :half] > 0.5).any() else -1e3 for r in range(n)]) / Z
    ke = np.array([np.nonzero(ka[r, half:] > 0.5)[0].min() + half if (ka[r, half:] > 0.5).any() else 1e9 for r in range(n)]) / Z
    return rows, ge, ke


def end_contour(rows, ge, ke):
    """P1: one end (the left), mirrored: the plate's end side = the more outward of the two figure edges (the keeper's
    mirrored about 960), set TUCK px in, held so every row of both edges sits DEPTH[0]..DEPTH[1] px under the panel."""
    km = 1920.0 - ke
    a_ = np.where(ge < -100, km, ge)
    b_ = np.where(km < -100, a_, km)
    a_ = np.where(a_ < -100, b_, a_)
    lo_e, hi_e = np.minimum(a_, b_), np.maximum(a_, b_)
    c = lo_e - TUCK
    c = np.maximum(c, hi_e - DEPTH[1])
    c = np.minimum(c, lo_e - DEPTH[0])
    return c


def plate(Z, rows, cl, verbose=False):
    """the middle plate at Z x the 1080 px, on the panel rect (PANEL_RECT): premultiplied RGBA"""
    x0, y0, w, h = PANEL_RECT
    x1, y1 = x0 + w, y0 + h
    ss = 4 * Z
    X, Y = ss_grid(x0, y0, x1, y1, ss)
    from PIL import ImageDraw as _D
    VL = (PL_X0 + VOL_R, PL_TOP + VOL_R)
    VR_ = (PL_X1 - VOL_R, PL_TOP + VOL_R)
    pts = [(PL_X0 + INSET, 1100), (PL_X0 + INSET, VL[1]), (VL[0], PL_TOP), (VR_[0], PL_TOP), (PL_X1 - INSET, VR_[1]),
           (PL_X1 - INSET, 1100)]
    mim = Image.new('L', (w * ss, (h + 20) * ss), 0)
    dd_ = _D.Draw(mim)
    dd_.polygon([((px - x0) * ss, (py - y0) * ss) for px, py in pts], fill=255)
    for (vx, vy) in (VL, VR_):
        dd_.ellipse(((vx - VOL_R - x0) * ss, (vy - VOL_R - y0) * ss, (vx + VOL_R - x0) * ss, (vy + VOL_R - y0) * ss), fill=255)
    dd_.ellipse(((960 - ARCH_R - x0) * ss, (SEAT_Y - ARCH_R - y0) * ss, (960 + ARCH_R - x0) * ss, (SEAT_Y + ARCH_R - y0) * ss), fill=255)
    mb = np.asarray(mim)[: h * ss] > 127
    mb = mb | mb[:, ::-1]
    mbc = ndimage.binary_closing(mb, structure=np.ones((3, 3)), iterations=10 * Z)
    near_v = (np.hypot(X - VL[0], Y - VL[1]) < VOL_R + 6) | (np.hypot(X - VR_[0], Y - VR_[1]) < VOL_R + 6)
    mb = np.where(near_v, mb, mbc)
    # P1: below the volute the end side follows the end contour (left end; mirrored for the right)
    yr = Y[:, :1]
    cle = np.interp(yr, rows, cl)
    below = yr >= PL_TOP + VOL_R
    left = (X >= cle) & (X <= PL_X0 + INSET + 1) & below
    left = left & (X < 960)
    mb = mb | left | left[:, ::-1]
    mb = mb | mb[:, ::-1]
    sd = (ndimage.distance_transform_edt(mb) - ndimage.distance_transform_edt(~mb)) / ss
    sd = G_(sd, 1.0 * Z)
    inside = np.clip(sd * 1.0 + 0.5, 0, 1)
    bev = 2.4 * sm(0.0, 3.2, sd)
    spir = np.full(X.shape, 1e3, np.float32)
    for (vx, vy), sg in ((VL, 1), (VR_, -1)):
        tt = np.linspace(0, 1, 160)
        ph = -np.pi / 2 - sg * tt * 2 * np.pi * 1.15
        rr_ = (VOL_R - INL) * (1 - 0.82 * tt)
        px_, py_ = vx + rr_ * np.cos(ph), vy + rr_ * np.sin(ph)
        win = (np.abs(X - vx) < VOL_R + 2) & (np.abs(Y - vy) < VOL_R + 2)
        if win.any():
            d2 = np.min((X[win][:, None] - px_[None]) ** 2 + (Y[win][:, None] - py_[None]) ** 2, 1)
            spir[win] = np.minimum(spir[win], np.sqrt(d2))
    in_v = np.minimum(np.hypot(X - VL[0], Y - VL[1]), np.hypot(X - VR_[0], Y - VR_[1])) < VOL_R - INL + 1.2
    line_d = np.where(in_v, np.minimum(np.abs(sd - INL), spir), np.abs(sd - INL))
    groove = -0.9 * np.exp(-((line_d + 1.0) / 0.9) ** 2) + 0.9 * np.exp(-(line_d / 0.7) ** 2)
    sock = np.zeros_like(X)
    for sx in SEAT_XS:
        dd = np.hypot(X - sx, Y - SEAT_Y)
        sock -= 1.2 * np.exp(-np.clip(dd - SEAT_R, 0, None) / 2.0) * (dd > SEAT_R - 1)
    dd = np.hypot(X - 960, Y - SEAT_Y)
    sock -= 1.2 * np.exp(-np.clip(dd - MED_R, 0, None) / 2.0) * (dd > MED_R - 1)
    Hh = bev + groove + sock
    gy, gx = np.gradient(Hh * 1.0, 1 / ss)
    nrm = np.dstack([-gx, -gy, np.ones_like(gx)]); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    Ld = LD_PLATE / np.linalg.norm(LD_PLATE)
    diff = np.clip(nrm @ Ld, 0, 1)
    hv = Ld + np.array([0, 0, 1.0], np.float32); hv /= np.linalg.norm(hv)
    spec = np.clip(nrm @ hv, 0, 1) ** 40
    # the mottle drawn at the 4x grid (one realisation for every Z), then resized
    rng = np.random.default_rng(21)
    sh4 = (h * 4, w * 4)
    mot = G_(rng.normal(0, 1, sh4).astype(np.float32), 24) * 9 + G_(rng.normal(0, 1, sh4).astype(np.float32), 5) * 2.2
    brushed = G_(rng.normal(0, 1, sh4).astype(np.float32), (0.6, 10)) * 3.0
    if Z != 1:
        mot = cv2.resize(mot, (X.shape[1], X.shape[0]), interpolation=cv2.INTER_LINEAR)
        brushed = cv2.resize(brushed, (X.shape[1], X.shape[0]), interpolation=cv2.INTER_LINEAR)
    base = np.array([0.150, 0.112, 0.078], np.float32)
    verd = np.array([0.075, 0.115, 0.100], np.float32)
    vmask = np.clip(0.25 + 0.6 * mot, 0, 1) * 0.35 * (sd > 9) * (line_d > 2.5)
    alb = base * (1 + 0.10 * mot + 0.05 * brushed)[..., None]
    alb = alb * (1 - vmask[..., None]) + verd * vmask[..., None]
    edge = sm(3.6, 2.4, sd) * (sd > -0.5)
    inlay_line = np.exp(-(line_d / 0.75) ** 2)
    polished = np.array([0.46, 0.35, 0.22], np.float32)
    alb = alb * (1 - edge[..., None]) + polished * edge[..., None]
    lin = np.array([0.86, 0.68, 0.40], np.float32)
    col = alb * (0.28 + 0.95 * diff)[..., None] + np.array([1.0, 0.85, 0.6], np.float32) * (spec * (0.25 + 0.75 * edge))[..., None] * 0.6
    col = col * (1 - inlay_line[..., None] * 0.9) + lin * (inlay_line * (0.75 + 0.55 * diff))[..., None]
    outline = sm(0.0, 0.9, sd) * (1 - sm(0.9, 1.6, sd))
    col = col * (1 - 0.6 * outline[..., None])
    rgba = np.dstack([col * inside[..., None], inside])
    sh = np.clip(1 - inside, 0, 1) * np.exp(-np.clip(-sd, 0, None) / 3.0) * 0.55
    # P2: a 3 px contact shadow (35 %) just outside each end's rim and under each cap, onto the figures
    endz = sm(PL_X0 + 2 * VOL_R + 10, PL_X0 + 2 * VOL_R + 2, np.minimum(X, 1920 - X))
    ring3 = np.clip(1 - inside, 0, 1) * sm(3.6, 2.4, -sd) * (sd < 0)
    cap = np.zeros_like(X)
    for (vx, vy) in (VL, VR_):
        cap = np.maximum(cap, sm(VOL_R + 0.5, VOL_R - 1.0, np.hypot(X - vx, Y - (vy + 2.5))) * (Y > vy))
    p2 = 0.35 * np.maximum(ring3, cap * np.clip(1 - inside, 0, 1)) * endz
    sh = np.maximum(sh, p2)
    rgba[..., 3] = rgba[..., 3] + sh * (1 - rgba[..., 3])
    return ss_down(rgba, 4)          # 4 samples per output px a side (ss = 4 Z)


def bezels(Z):
    """the seats' slim bezels (seat_layer() without the wells), premultiplied, on the panel rect at Z"""
    x0, y0, w, h = PANEL_RECT
    out = np.zeros((h * Z, w * Z, 4), np.float32)
    ss = 4 * Z
    for sx in SEAT_XS:
        bx0, by0 = int(sx - SEAT_R - 3), int(SEAT_Y - SEAT_R - 3)
        bx1, by1 = int(sx + SEAT_R + 4), int(SEAT_Y + SEAT_R + 4)
        X, Y = ss_grid(bx0, by0, bx1, by1, ss)
        dx, dy = X - sx, Y - SEAT_Y
        d = np.hypot(dx, dy)
        ring = np.clip(SEAT_R - d + 0.5, 0, 1) * np.clip(d - WELL_R + 0.5, 0, 1)
        t = np.clip((d - WELL_R) / BEZ, 0, 1)
        tilt = (t - 0.5) * 1.6
        nx, ny = dx / (d + 1e-3) * tilt, dy / (d + 1e-3) * tilt
        Ld = np.array([-0.5, -0.65, 0.58]); Ld /= np.linalg.norm(Ld)
        nz = np.sqrt(np.clip(1 - tilt ** 2 * 0.5, 0.1, 1))
        diff = np.clip(nx * Ld[0] + ny * Ld[1] + nz * Ld[2], 0, 1)
        spec = np.clip(diff, 0, 1) ** 24
        c = np.array([0.55, 0.42, 0.26]) * (0.30 + 1.05 * diff)[..., None] + np.array([1, 0.88, 0.64]) * (spec * 0.6)[..., None]
        inner = np.exp(-((d - WELL_R - 0.2) / 0.6) ** 2)
        c = c * (1 - 0.7 * inner[..., None])
        outl = np.clip(SEAT_R + 1.0 - d + 0.5, 0, 1) * (1 - np.clip(SEAT_R - d + 0.5, 0, 1))
        a = np.clip(ring + outl * 0.9, 0, 1)
        rgb = c * ring[..., None] + np.array([0.03, 0.024, 0.018]) * outl[..., None]
        piece = ss_down(np.dstack([rgb, a]).astype(np.float32), 4)
        ox, oy = (bx0 - x0) * Z, (by0 - y0) * Z
        ph, pw = piece.shape[:2]
        hh, ww = min(ph, out.shape[0] - oy), min(pw, out.shape[1] - ox)
        sub = np.zeros_like(out)
        sub[oy:oy + hh, ox:ox + ww] = piece[:hh, :ww]
        out = over(out, sub)
    return out


def coin_static(Z, dgr):
    """the coin's dish (well_2), ring (ring_2) and the XP ring's dark groove, on the panel rect at Z"""
    x0, y0, w, h = PANEL_RECT
    cx, cy, R = 960.0, SEAT_Y, MED_R
    cv = (w * Z, h * Z)
    out = np.zeros((h * Z, w * Z, 4), np.float32)
    well = load_rgba(os.path.join(dgr, 'well_2.png'))
    out = over(out, place(well, (cx - R * 0.80 - x0) * Z, (cy - R * 0.80 - y0) * Z, R * 1.6 * Z, R * 1.6 * Z, cv))
    ring = load_rgba(os.path.join(dgr, 'ring_2.png'))
    out = over(out, place(ring, (cx - R - x0) * Z, (cy - R - y0) * Z, 2 * R * Z, 2 * R * Z, cv))
    gy, gx = np.mgrid[0:h * Z, 0:w * Z].astype(np.float32)
    X, Y = x0 + (gx + 0.5) / Z, y0 + (gy + 0.5) / Z
    d = np.hypot(X - cx, Y - cy)
    r0, r1 = R * 0.775, R * 0.985
    ch = np.clip(np.minimum(d - r0, r1 - d) * Z + 0.5, 0, 1)
    groove = np.zeros_like(out)
    groove[..., :3] = np.array([0.03, 0.035, 0.045], np.float32) * ch[..., None]
    groove[..., 3] = ch * 0.92
    return over(out, groove)


# ================================================================== the bake
def main():
    gr = json.load(open(os.path.join(SRC, 'keeper_grade.json')))
    Z = 2
    rep = {}
    # ---- the girl
    art = load_rgba(os.path.join(SRC, 'girl_R6.png'))
    cur = load_rgba(os.path.join(UI, 'lamp_life', 'drowned', 'lamp_cold.png'))
    assert art.shape == cur.shape, (art.shape, cur.shape)
    art, n_g1 = fix_girl(art)
    gm = lamp_mask(art)
    dd = os.path.join(UI, 'lamp_life', 'drowned')
    save_rgba(os.path.join(dd, 'lamp_cold.png'), art)
    Image.fromarray((np.clip(gm, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(dd, 'lamp_mask.png'))
    rep['G1 px filled (art)'] = n_g1
    # ---- the keeper at 2x
    k_rgb, k_a = keeper_source()
    kh, kw = k_a.shape
    kx0, ky0 = keeper_geom(k_a)
    rgb, a, fire = keeper_graded(k_rgb, k_a, gr)
    gx0, gy0, gw, gh = girl_screen_rect()
    lx0 = 1920 - (gx0 + gw) + LOCK_D[0]
    # the sprite's rect: whole 1080 px round the keeper and the lock
    rx0 = int(np.floor(min(kx0, 1280 + LOCK_D[0]))) - 2
    ry0 = int(np.floor(min(ky0, 966 + LOCK_D[1]))) - 2
    rx1 = int(np.ceil(kx0 + kw * K_S)) + 2
    ry1 = 1080
    cvz = ((rx1 - rx0) * Z, (ry1 - ry0) * Z)
    Kp = place(np.dstack([rgb, a]), (kx0 - rx0) * Z, (ky0 - ry0) * Z, kw * K_S * Z, kh * K_S * Z, cvz)
    Fp = place(np.dstack([np.ones_like(rgb), fire * a]), (kx0 - rx0) * Z, (ky0 - ry0) * Z, kw * K_S * Z, kh * K_S * Z, cvz)[..., 3]
    jj, ii = np.mgrid[0:cvz[1], 0:cvz[0]].astype(np.float32)
    Xi, Yi = rx0 + (ii + 0.5) / Z - 0.5, ry0 + (jj + 0.5) / Z - 0.5      # mock pixel-index units
    Lk = place(art[:, ::-1].copy(), (lx0 - rx0) * Z, (gy0 + LOCK_D[1] - ry0) * Z, gw * Z, gh * Z, cvz)
    Lk = Lk * lock_window(Xi, Yi)[..., None]
    ls = straight(Lk)
    Lk = np.dstack([final_grade(ls, np.zeros(ls.shape[:2], np.float32), gr) * Lk[..., 3:4], Lk[..., 3]])
    K = over(Lk, Kp)
    K, n_plug = plug_holes(K, (Xi > 1240) & (Yi > 960), 60 * Z * Z)
    rep['K1 hole px plugged (2x)'] = n_plug
    # K4
    bcx = kx0 + gr['BOWL_C'] * K_S
    rim_y = ky0 + gr['RIM_C'] * K_S
    egx, egy = bcx, rim_y - 0.62 * EG_R
    dgl = np.hypot(Xi - egx, Yi - egy)
    away = (1 - np.clip(G_((Fp > 0.05).astype(np.float32), 3.0 * Z) * 3, 0, 1)) * sm(EG_R + 8, EG_R + 20, dgl)
    ks = straight(K)
    ks = k4_curve(ks, away, gr['K4_thr'])
    K = np.dstack([ks * K[..., 3:4], K[..., 3]])
    bl, br = kx0 + gr['BOWL_L'] * K_S, kx0 + gr['BOWL_R'] * K_S
    front = sm(rim_y - 1.0, rim_y + 1.5, Yi) * (Xi > bl - 2) * (Xi < br + 2)
    kd = os.path.join(UI, 'dg_keeper')
    save_rgba(os.path.join(kd, 'keeper.png'), np.dstack([straight(K), K[..., 3]]))
    save_rgba(os.path.join(kd, 'keeper_lip.png'), np.dstack([straight(K), K[..., 3] * front]))
    # ---- the panel at 2x
    # the figures' edges at 2x: her art (scaled) and the keeper sprite, full width rows from the panel's top
    py0 = PANEL_RECT[1]
    nrow = (1080 - py0) * Z
    ga = place(art, gx0 * Z, (gy0 - py0) * Z, gw * Z, gh * Z, (1920 * Z, nrow))[..., 3]
    ka = np.zeros((nrow, 1920 * Z), np.float32)
    ka[:, rx0 * Z:rx1 * Z] = K[(py0 - ry0) * Z:, :, 3]
    rows, ge, ke = figure_edges(ga, ka, Z, py0)
    cl = end_contour(rows, ge, ke)
    P = plate(Z, rows, cl)
    P = over(P, bezels(Z))
    P = over(P, coin_static(Z, os.path.join(UI, 'dg_river')))
    save_rgba(os.path.join(UI, 'dg_panel', 'panel.png'), np.dstack([straight(P), P[..., 3]]))
    # ---- the fire
    shutil.copy(os.path.join(SRC, 'fw_9931_0.png'), os.path.join(kd, 'fire.png'))
    shutil.copy(os.path.join(SRC, 'fo_9932_0.png'), os.path.join(kd, 'fire_ready.png'))
    # ---- the geometry
    geo = geometry(kx0, ky0, (rx0, ry0, rx1 - rx0, ry1 - ry0), gr, rows, cl)
    json.dump(geo, open(os.path.join(kd, 'hud_a_geo.json'), 'w'), indent=1)
    rep['keeper rect'] = geo['keeper']['rect']; rep['glass'] = geo['glass']['center']
    print(json.dumps(rep))


def geometry(kx0, ky0, krect, gr, rows, cl):
    gx0, gy0, gw, gh = girl_screen_rect()
    bcx = kx0 + gr['BOWL_C'] * K_S
    rim_y = ky0 + gr['RIM_C'] * K_S
    sel = rows >= PL_TOP + VOL_R
    return {
        'note': 'tools/uiforge/dg_keeper_hud.py: HUD A (the keeper). 1080 px screen coords; rects are [x, y, w, h], continuous '
                'edges (pixel i spans [i, i+1]); every texture is 2x its rect. Day and night use the same sprites.',
        'heights': {'left': 237, 'middle': 81, 'right': 205},
        'girl': {'texture': 'lamp_life/drowned/lamp_cold.png', 'mask': 'lamp_life/drowned/lamp_mask.png',
                 'rect_unscaled': [GIRL_AT[0], GIRL_AT[1], GIRL_SIZE[0], GIRL_SIZE[1]],
                 'rect_unscaled_note': 'mock place() rect; lamp_geo.json at is 295.33 (the mock matched the frame at -0.5)',
                 'group_anchor': list(ANCHOR), 'group_scale': S, 'dxg': 0,
                 'rect': [round(gx0, 3), round(gy0, 3), round(gw, 3), round(gh, 3)],
                 'globe': [round(ANCHOR[0] + (GLOBE[0] - ANCHOR[0]) * S, 3), round(ANCHOR[1] + (GLOBE[1] - ANCHOR[1]) * S, 3), round(GLOBE[2] * S, 3)],
                 'shine_run': 's = x + 0.5 (clamp(y, 840, 1040) - 840) + 1.1 max(y - 975, 0) smoothstep(520, 575, x); front 640 (mock7.py path_s, line 108)',
                 'hair_mask': 'dg_river/xp_light.png R = the hair outline (1 - tail) + hair_R6; G ridges (1 - tail) (dg_xp_mask.py)'},
        'keeper': {'texture': 'dg_keeper/keeper.png', 'lip': 'dg_keeper/keeper_lip.png', 'rect': list(map(int, krect)),
                   'source': 'gen ks60_2304_0', 'source_rect': [round(kx0, 3), round(ky0, 3), 1200 * K_S, 800 * K_S],
                   'draw': 'keeper, then the glass, then keeper_lip over the glass; the glass glow (additive) x (1 - 0.75 lip alpha); '
                           'then the girl, then the panel'},
        'panel': {'texture': 'dg_panel/panel.png', 'rect': list(PANEL_RECT), 'top_line': [PL_X0 + VOL_R, PL_X1 - VOL_R, PL_TOP],
                  'x': [PL_X0, PL_X1], 'volute_r': VOL_R, 'volutes': [[PL_X0 + VOL_R, PL_TOP + VOL_R], [PL_X1 - VOL_R, PL_TOP + VOL_R]],
                  'end_contour_left': [[round(float(y), 2), round(float(x), 2)] for y, x in zip(rows[sel][::4], cl[sel][::4])],
                  'end_contour_note': '[y, x] of the left end below the volute; the right end is 1920 - x',
                  'seats': [[round(x, 2), SEAT_Y] for x in SEAT_XS], 'well_r': WELL_R, 'seat_r': SEAT_R,
                  'coin': {'center': [960.0, SEAT_Y], 'r': MED_R, 'arch_r': ARCH_R,
                           'xp_ring': {'r0': round(MED_R * 0.775, 3), 'r1': round(MED_R * 0.985, 3), 'mid': round(MED_R * 0.88, 3),
                                       'fill_from': '12 o\'clock clockwise', 'core_sigma': 1.9,
                                       'day': {'hue': [0.353, 0.635, 0.839], 'core': [0.812, 0.910, 1.0]},
                                       'night': {'hue': [0.612, 0.494, 0.878], 'core': [0.886, 0.831, 1.0]},
                                       'track_tint': 0.22, 'lip': 0.35, 'head_glint': [2.6, 0.9],
                                       'tick': 'live: 1.2 px wide gold (0.95,0.80,0.52) at 12 o\'clock over r0-1.5..r1+1.5 (mock7.py medallion, line 632)'},
                           'level_number': {'at': [960.0, SEAT_Y + 1], 'font': 'cinzel-700', 'size': 23, 'anchor': 'mm', 'stroke': 1,
                                            'day': [214, 234, 255], 'night': [232, 222, 255]}},
                  'flask': {'center': [FLASK_X, SEAT_Y - 9], 'scale': S, 'count_badge': [FLASK_X + 15, SEAT_Y - 9 - 19, 9]},
                  'dash': {'center': [DASH_X, SEAT_Y - 7], 'scale': 0.84},
                  'key_tags': {'R': [FLASK_X, 1061], 'SPACE': [DASH_X, 1061], 'Q': [round(bcx + 6, 2), round(rim_y + 52, 2)],
                               'note': '[centre x, top y], 16 px high, radius 3, alegreya-sans-800 16, tracking 0.6; lit when READY: "Q  READY"'},
                  'rank_chips': [[round(x + 24.5, 2), SEAT_Y - 24.5, 9] for x in SEAT_XS]},
        'glass': {'center': [round(bcx, 3), round(rim_y - 0.62 * EG_R, 3)], 'r': EG_R, 'bezel_outer': EG_R + 3.6,
                  'lip_y': round(rim_y, 3), 'bowl': [round(kx0 + gr['BOWL_L'] * K_S, 2), round(kx0 + gr['BOWL_R'] * K_S, 2)],
                  'fire': 'dg_keeper/fire.png (idle), fire_ready.png (READY)',
                  'constants': {
                      'center_y': 'lip_y - 0.62 r (mock7.py 689)',
                      'pad': '2.2 r idle, 3.2 r READY; the window top extends 10 / 30 px more (293-294)',
                      'level': 'vis_bot = min(cy + r, lip_y + 1); lvl = vis_bot - charge (vis_bot - (cy - r)); READY cy - r - 6 (313-315)',
                      'idle_fire_uv': 'u = (x - cx) / 0.115 + 424, v = clamp((y - lvl) / 0.115 + 330, 0, 767) on fire.png 768^2; x 1.12 (325-327)',
                      'ready_fire_uv': 'u = 383.5 + (x - cx) / r 318, v = 383 + (y - cy) / r 318 on fire_ready.png; x 1.25 + 0.04 (329-330)',
                      'ready_heart': 'exp(-(d / 0.46 r)^2) (0.70 + 0.30 clamp(1.4 luma(fire))), screen (1.0, 0.95, 0.80) x 0.95 (333-336)',
                      'ready_wash': 'screen (1.0, 0.72, 0.30) x 0.55 exp(-(d / 0.80 r)^2) (335)',
                      'radial': 'fire x (0.68 + 0.32 (1 - (d/r)^4)) (337)',
                      'glass': '(0.050, 0.036, 0.030) + (0.30, 0.10, 0.02) 0.35 exp(-max(lvl - y, 0) / 9); screen with fire (339-342)',
                      'optics': 'x (0.72 + 0.28 (1 - (d/r)^6)); fresnel (0.95,0.80,0.60) 0.20 over d/r 0.82..1; window at (cx - 0.42 r, cy - 0.46 r) '
                                'size (0.30 r, 0.17 r) 0.35; glint sigma (1.6, 1.2) 0.55 (346-353)',
                      'bezel': 'r..r+3.6 bronze (0.36,0.27,0.16) (0.45 + 1.1 lit), lit = clamp(0.55 - 0.315 (dx+dy)/d, 0.1, 1); charge arc amber '
                               '(1.0,0.62,0.20) clockwise from 12; READY 0.55 bezel + 0.65 (1.0,0.70,0.30); outline r+3.6..r+4.6 0.85 (354-367)',
                      'halo': 'exp(-max(d - r, 0) / (r 0.85 READY | 0.22 idle)) (1 - smoothstep(0.72 pad, 0.98 pad, d)); colour (1.0,0.62,0.22) x 0.95 READY, '
                              '(1.0,0.50,0.12) x (0.10 + 0.2 charge) idle; additive, x (1 - 0.75 lip alpha) (370-375, 694)',
                      'ready_flames': '5 tongues (pos, height) (-0.55,0.55) (-0.25,0.95) (0.02,1.35) (0.28,0.85) (0.55,0.5), 30 px x height, '
                                      'width 6 (0.7 + 0.5 h); 11 embers seed 17 (376-410)',
                      'ready_core_luma': 'about 0.92 inside 0.35 r at charge 1 (mock CORE)'}}}


if __name__ == '__main__':
    main()
