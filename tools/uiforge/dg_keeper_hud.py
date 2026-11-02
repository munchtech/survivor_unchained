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
# UI 27 (the owner, 2 Nov: "slide them inward", "the dead space ... doesn't need to be so wide", "the same height";
# "their backs are flush touching the hotbar"): the ends pulled in 11 px a side (was 626 / 1294) and steeper (the foot
# 9 px out of PL_X0, was 19); the girl lowered and smaller, the keeper risen, both slid in so each back comes down into
# the bar's top line just inward of the volute (asserted in main()).
VOL_R, PL_X0, PL_X1, PL_TOP, ARCH_R = 12.0, 637.0, 1283.0, 1003.0, MED_R + 6.0
INSET = 6.5
INL = 6.5            # snap: the inlay's top run centred on the 1080 px row 1009 (was 6.0: on the 1008/1009 seam)
FOOT_X = 628.0       # UI 24: the designed end, a straight side tangent to the volute down to this x at the screen foot
TUCK_MIN = 4.0       # UI 24: every figure edge row from the panel top sits at least this far under the panel (asserted)
CLEAR = (3.0, 8.0)   # UI 27: the nearest live part at each end (flask, dash, their tags) from the end's inlay (asserted)
FLUSH = (0.0, 7.0)   # UI 27: the 12 rows over PL_TOP, each back's edge this far inward of the volute's inner end
LD_PLATE = np.array([0.0, -0.816, 0.578], np.float32)   # P1: lit from straight above (the field's z kept)
PANEL_RECT = (600, 988, 720, 92)                          # symmetric about 960 (UI 27: was 576, 768 wide)
S, ANCHOR = 0.94, (295.33, 1080.0)                        # the reference frame (G1, the keeper's mirrored lock, the shine)
GIRL_AT, GIRL_SIZE = (294.83, 822.0), (474.67, 258.0)    # place() convention (the frame's best match)
G_S, G_D = 0.876, (69.2, 1.9)                             # UI 27: her own group scale about ANCHOR, then this offset
                                                          # (r2: x 49.5 -> 69.2: her flared strand cut, her back's own mass meets the top line)
GLOBE = (378.0, 960.0, 59.4)
K_S, K_TOP, GAP_R = 0.28, 205.0, -17.0                    # the keeper's frame (as UI 24 built it)
KF_X1 = 1294.0                                            # the keeper's frame was set off UI 24's PL_X1
K_D = (-40, -12)                                           # UI 27: the keeper sprite moved by whole px (x, y: up 12; r2 x -20 -> -40)
FLASK_S = 0.84                                            # UI 27 r2 (the owner: "potion should be same size as space button"): the
FLASK_IN = 0.80                                           # draught sits in the dash's seat (its ring and well at the dash's 0.84,
FLASK_DY = -7.0                                           # mirrored), the flask art inside its hole at FLASK_IN (r <= 22.5 of 23)
LOCK_ON = False                                           # UI 27 r2: the keeper's mirrored back lock dropped (its loop spilled over the
                                                          # bar; under the bar the keeper's own robe tucks, asserted)
BAND = 45                                                 # UI 27 r2: the rows over PL_TOP where each back is a clean line (back_line)
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


def girl_screen_rect(ref=False):
    """her art's rect on screen: G_S about her outer bottom corner (ANCHOR), then G_D (UI 27). ref: the reference
    frame (UI 24's 0.94, no offset), which G1, the keeper's mirrored lock and the hair shine's run are set in."""
    s, (dx, dy) = (S, (0.0, 0.0)) if ref else (G_S, G_D)
    x0 = ANCHOR[0] + (GIRL_AT[0] - ANCHOR[0]) * s + dx
    y0 = ANCHOR[1] + (GIRL_AT[1] - ANCHOR[1]) * s + dy
    return x0, y0, GIRL_SIZE[0] * s, GIRL_SIZE[1] * s


def girl_to_screen(px, py):
    """a reference-frame screen point (0.94) to the screen now (G_S, G_D)"""
    k = G_S / S
    return ANCHOR[0] + (px - ANCHOR[0]) * k + G_D[0], ANCHOR[1] + (py - ANCHOR[1]) * k + G_D[1]


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
    kx0 = KF_X1 + GAP_R + 1.0 - k_left * K_S
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
    """the mirrored back lock's window (mock7 KLOCK block), moved by K1; X, Y in mock pixel-index units. UI 24: no top
    fade here (it read as a smudge): main() tapers each strand to a tip above LOCK_TOP (lock_taper)."""
    dx, dy = LOCK_D
    # UI 27: X, Y are the keeper's frame (the screen less K_D). The lock's inner cut is the keeper's back over the bar:
    # the mirror of her contact (her edge on the row over PL_TOP), so the two backs meet the top line mirror-true
    gc = girl_contact()
    w = sm(1336.0 + dx, 1318.0 + dx, X) * (X + 0.5 > 1920.0 - gc - K_D[0])
    # below the cap the lock reaches no further in than her edge's mirror (so both ends tuck the same under one mirrored end)
    ge = girl_edge_rows()
    xc = 1920.0 - np.interp(Y + K_D[1] + 0.5, np.arange(1080) + 0.5, ge) - K_D[0]
    top = PL_TOP - K_D[1]
    return w * np.maximum(sm(xc - 1.0, xc + 1.0, X + 0.5), 1 - sm(top + VOL_R - 4, top + VOL_R, Y + 0.5))


def girl_contact():
    """UI 27: her back's contact with the top line: her edge on the row just over PL_TOP (screen px)"""
    return float(girl_edge_rows()[int(PL_TOP) - 1])


LOCK_TOP, LOCK_R = 969.0, 14.0     # UI 24: the lock's strands end in rounded tips: none above LOCK_TOP, a LOCK_R px dome


def lock_taper(Lk, Y, Z):
    """UI 24: the mirrored lock's strands end in rounded tips (a sculpted bronze lock's end) instead of a fade: s px
    below LOCK_TOP a texel stays where the strand's half-width there (its alpha's inner distance, 1080 px) exceeds
    R - sqrt(R^2 - (R - s)^2): a thick strand domes, a thin one ends near the top; premultiplied in and out"""
    m = Lk[..., 3] > 0.5
    din = ndimage.distance_transform_edt(m) / Z
    sd = np.clip(Y - LOCK_TOP, 0, None)
    thr = np.where(sd < LOCK_R, LOCK_R - np.sqrt(np.clip(LOCK_R ** 2 - (LOCK_R - sd) ** 2, 0, None)), 0.0)
    tap = np.clip((din - thr) * Z + 0.5, 0, 1) * (Y >= LOCK_TOP)
    return Lk * tap[..., None]


_GE = {}


def girl_edge_rows():
    """her right edge (alpha > 0.5, 1080 px) per screen row, from her (fixed) art at its rect now; -1e3 where none"""
    if 'ge' not in _GE:
        art = girl_art()[0]
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


def clean_edges(L, region, protect=None, ramp=2.0, min_keep=2000):
    """UI 24, the statues' inner edges: straight RGBA L; region 0..1 (where to work). (1) a crisp silhouette: the
    0.5 alpha contour from a 4x bicubic upsample, alpha = its signed distance over a ramp of `ramp` texels (2 texels of
    the 2x art = 1 px at 1080), so faint wisps and soft mattes go; (2) islands: alpha components (> 0.05) smaller than
    min_keep texels in the region are removed (protect: a bool mask that counts as solid when labelling, e.g. the
    orb's hole); (3) decontamination: within 3 texels of the edge the colour is lifted to the interior's (never
    darkened, so the lit rims stay), no dark ring. Returns (L, n_islands_removed)."""
    a = np.clip(L[..., 3], 0, 1)
    h, w = a.shape
    up = cv2.resize(a, (w * 4, h * 4), interpolation=cv2.INTER_CUBIC) > 0.5
    sdu = (ndimage.distance_transform_edt(up) - ndimage.distance_transform_edt(~up)).astype(np.float32)
    sd = sdu.reshape(h, 4, w, 4).mean((1, 3)) / 4.0
    a_new = np.clip(sd / ramp + 0.5, 0, 1)
    a2 = a * (1 - region) + a_new * region
    solid = a2 > 0.05
    if protect is not None:
        solid = solid | protect
    lab, n = ndimage.label(solid, structure=np.ones((3, 3)))
    sz = ndimage.sum(np.ones_like(a2), lab, range(1, n + 1))
    small = 1 + np.nonzero(sz < min_keep)[0]
    kill = np.isin(lab, small) & (region > 0.5)
    a2 = np.where(kill, 0.0, a2)
    core = ndimage.binary_erosion(a > 0.97, iterations=2)
    rgb = L[..., :3]
    num = np.stack([G_(rgb[..., c] * core, 2.5) for c in range(3)], -1)
    den = G_(core.astype(np.float32), 2.5)[..., None]
    col = np.where(den > 0.02, num / np.maximum(den, 1e-4), rgb)
    t = (sm(3.0, 0.5, sd) * region * (den[..., 0] > 0.02))[..., None]
    rgb2 = rgb * (1 - t) + np.maximum(rgb, col) * t
    return np.dstack([rgb2, a2]).astype(np.float32), int(len(small))


# ================================================================== UI 27 r2: the backs over the bar, clean lines
SOLID_W = 10.0      # px at 1080: from each back's edge inward the figure is solid this far, every row of the band


def runs(m):
    """a bool row's runs of True: (starts, ends), ends exclusive"""
    d = np.diff(np.r_[0, m.astype(np.int8), 0])
    return np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]


def flush_floor(e, ylo, sign):
    """the line a back may not stop short of (UI 27's flush): the volute's inner end (vie) + 0.5 px inward over the 12
    rows over PL_TOP, eased in from the back's own edge over the 12 rows before (sign +1 the girl, -1 the keeper,
    mirrored); e per 1080 row from ylo"""
    vie = PL_X0 + 2 * VOL_R
    tgt = vie + 0.5 if sign > 0 else 1920 - vie - 0.5
    yy = ylo + np.arange(len(e))
    i0 = int(PL_TOP) - 24 - ylo
    t = sm(PL_TOP - 24, PL_TOP - 12, yy)
    fl = e[i0] + (tgt - e[i0]) * t
    return np.where(yy >= PL_TOP - 24, fl, -1e9 * sign)


def fill_strip(rgb, a, strip):
    """the texels of strip made solid, their colour inpainted from the figure round them (straight rgb, alpha)"""
    if not strip.any():
        return rgb, a, 0
    hole = strip & (a < 0.9)
    u8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    unknown = ndimage.binary_dilation(hole, iterations=1) | (a < 0.5)          # (known: the opaque figure only)
    inp = cv2.inpaint(u8, unknown.astype(np.uint8) * 255, 4, cv2.INPAINT_TELEA).astype(np.float32) / 255
    rgb = np.where(hole[..., None], inp, rgb)
    return rgb, np.where(strip, np.maximum(a, 1.0), a), int(hole.sum())


def girl_back_line(art):
    """UI 27 r2 (the owner: "erase the stuff that spills up top"): her back over the bar, the BAND rows over PL_TOP,
    is her hair's own mass: the flared strand that leaves it (and the see-through hook between them) is cut away
    along the mass's edge (the mass's edge where the strand stands apart from it; between its last clear row over the
    band and the strand's foot, a straight run), held to flush_floor and never moving back out going down. Returns
    (art, ylo, c per row, px2 filled)."""
    x0, y0, w, h = girl_screen_rect()
    Z, WX = 4, 560
    ylo, yhi = int(PL_TOP) - BAND, int(PL_TOP)
    a4 = place(art, (x0 - WX) * Z, (y0 - ylo) * Z, w * Z, h * Z, (200 * Z, (yhi - ylo) * Z))[..., 3]
    e = np.full(yhi - ylo, np.nan)
    c600 = (600 - WX) * Z
    for r in range(yhi - ylo):
        st, en = runs(a4[r * Z + Z // 2] > 0.5)
        k = [i for i in range(len(st)) if st[i] <= c600 < en[i]]
        assert k, ('her mass not over x 600', ylo + r)
        k = k[0]
        apart = any(en[j] - st[j] > 2 for j in range(k + 1, len(st)))
        if r == 0 or apart:
            e[r] = WX + en[k] / Z
    kn = np.nonzero(~np.isnan(e))[0]
    e = np.interp(np.arange(len(e)), kn, e[kn])
    c = np.maximum.accumulate(np.maximum(e, flush_floor(e, ylo, 1)))
    H_, W_ = art.shape[:2]
    ay, ax = np.mgrid[0:H_, 0:W_].astype(np.float32)
    X, Y = x0 + (ax + 0.5) * w / W_, y0 + (ay + 0.5) * h / H_
    rc = ylo + 0.5 + np.arange(len(c))
    cv_, ev = np.interp(Y, rc, c), np.interp(Y, rc, e)
    band = (Y >= ylo) & (Y < PL_TOP + 2)
    keep = np.where(band, np.clip(cv_ + 0.75 - X, 0, 1), 1.0)
    a = art[..., 3] * keep
    strip = band & (Y < PL_TOP) & (X <= cv_) & (X >= ev - 1.0)
    rgb, a2, nf = fill_strip(art[..., :3], a, strip & (np.clip(cv_ + 0.75 - X, 0, 1) > 0.5))
    # (over the bar the edge is the line itself, a 1 px ramp, so no resample wobbles it; under it UI 24's clean_edges)
    a2 = np.where(band & (Y < PL_TOP) & (X >= cv_ - 3.0), np.clip(cv_ + 0.75 - X, 0, 1), a2)
    out = np.dstack([rgb, a2]).astype(np.float32)
    region = ((Y >= PL_TOP) * sm(PL_TOP + 16, PL_TOP + 12, Y) * sm(596.0, 604.0, X)).astype(np.float32)
    out, _ = clean_edges(out, region)
    return out, ylo, c, nf * (w / W_) * (h / H_)


def keeper_back_line(K, Xi, Yi, Z):
    """UI 27 r2: the keeper's back over the bar, the mirror of girl_back_line: with the mirrored lock gone his robe's
    own edge, held to flush_floor (mirrored), never moving back out going down; premultiplied K in the sprite's frame
    (Xi, Yi its mock pixel-index units). Returns (K, c per row from PL_TOP - BAND, px2 filled)."""
    Ks, a = straight(K), K[..., 3]
    Xs, Ys = Xi + 0.5 + K_D[0], Yi + 0.5 + K_D[1]
    ylo, yhi = int(PL_TOP) - BAND, int(PL_TOP)
    e = np.full(yhi - ylo, 1e9)
    for r in range(ylo, yhi):
        for j in np.nonzero((Ys[:, 0] >= r) & (Ys[:, 0] < r + 1))[0]:
            m = (a[j] > 0.5) & (Xs[j] < 1330)
            if m.any():
                e[r - ylo] = min(e[r - ylo], Xs[j][np.nonzero(m)[0].min()] - 0.5 / Z)
    assert (e < 1330).all(), 'the keeper has no back in the band'
    c = np.minimum.accumulate(np.minimum(e, flush_floor(e, ylo, -1)))
    rc = ylo + 0.5 + np.arange(len(c))
    cv_, ev = np.interp(Ys, rc, c), np.interp(Ys, rc, e)
    band = (Ys >= ylo) & (Ys < PL_TOP)
    a = a * np.where(band & (Xs < 1330), np.clip(Xs - (cv_ - 0.75), 0, 1), 1.0)
    strip = band & (Xs >= cv_ - 0.5) & (Xs <= ev + 1.0) & (np.clip(Xs - cv_ + 0.75, 0, 1) > 0.5)
    rgb, a2, nf = fill_strip(Ks, a, strip)
    return np.dstack([rgb * a2[..., None], a2]).astype(np.float32), c, nf / (Z * Z)


_GA = {}


def girl_art():
    """her art: girl_R6 with G1 (fix_girl), then UI 24's clean_edges on her inner (right, back) side, art x > 540 (her
    face, hand and the orb hole are left of it); cached. Returns (art, n_g1, n_islands)."""
    if 'a' not in _GA:
        art, n_g1 = fix_girl(load_rgba(os.path.join(SRC, 'girl_R6.png')))
        h, w = art.shape[:2]
        xx = np.mgrid[0:h, 0:w][1].astype(np.float32)
        art, n_isl = clean_edges(art, sm(520.0, 560.0, xx))
        # UI 24, her lowest back locks by the end cap: the grey-teal shadow mass (art x 630-740, y 340-516) warmed to the
        # bronze's shadow and lifted a little, so it reads as shadowed bronze running under the cap, not mud
        yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
        lab = lab_of(art[..., :3])
        wm = sm(620.0, 640.0, xx) * sm(330.0, 350.0, yy) * sm(48.0, 32.0, lab[..., 0] * 100 / 255) * np.clip(art[..., 3], 0, 1)
        lab2 = lab.copy()
        lab2[..., 0] = lab[..., 0] * (1 + 0.22 * wm)
        lab2[..., 1] = lab[..., 1] + (131.0 - lab[..., 1]) * 0.7 * wm
        lab2[..., 2] = lab[..., 2] + (138.0 - lab[..., 2]) * 0.7 * wm
        rgb = lab2rgb(lab2)
        art = np.dstack([np.where(wm[..., None] > 0.003, rgb, art[..., :3]), art[..., 3]])
        art, _, _GA['back'], _GA['fill'] = girl_back_line(art)
        _GA['a'] = (art, n_g1, n_isl)
    return _GA['a']


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


def end_line():
    """UI 24: the left end's straight side, tangent to the volute (centre VL, radius VOL_R) through (FOOT_X, 1080):
    returns (x_t, y_t, slope): the tangent point and dx/dy (< 0, the side leans out toward the foot)"""
    cx, cy, r = PL_X0 + VOL_R, PL_TOP + VOL_R, VOL_R
    fx, fy = FOOT_X, 1080.0
    dx, dy = cx - fx, cy - fy
    L = np.hypot(dx, dy)
    base = np.arctan2(dy, dx)
    # the tangent from the foot that touches the circle's outer (left) side
    ang = base - np.arcsin(r / L)
    ux, uy = np.cos(ang), np.sin(ang)
    tl = np.sqrt(L * L - r * r)
    xt, yt = fx + ux * tl, fy + uy * tl
    return xt, yt, ux / uy


def end_contour(y):
    """UI 24, the designed end (replaces P1's traced contour): the left end's outer x per 1080 px y: the volute's
    left arc above the tangent point, the straight side below it (mirror-symmetric about 960 for the right end)"""
    y = np.asarray(y, np.float64)
    cx, cy, r = PL_X0 + VOL_R, PL_TOP + VOL_R, VOL_R
    xt, yt, sl = end_line()
    arc = cx - np.sqrt(np.clip(r * r - (y - cy) ** 2, 0, None))
    lin = xt + (y - yt) * sl
    return np.where(y < yt, np.where(y >= PL_TOP, arc, 1e3), lin)


def plate(Z):
    """the middle plate at Z x the 1080 px, on the panel rect (PANEL_RECT): premultiplied RGBA. UI 24: the ends are the
    designed end_contour (volute + a straight side tangent to it), every line is a hard step on the supersample grid
    (exact coverage at 2x, so whole and even at 1080): a 1 px dark outline, a 1 px light bevel, the 1 px gold inlay."""
    x0, y0, w, h = PANEL_RECT
    x1, y1 = x0 + w, y0 + h
    ss = 4 * Z
    X, Y = ss_grid(x0, y0, x1, y1, ss)
    from PIL import ImageDraw as _D
    VL = (PL_X0 + VOL_R, PL_TOP + VOL_R)
    VR_ = (PL_X1 - VOL_R, PL_TOP + VOL_R)
    mim = Image.new('L', (w * ss, (h + 20) * ss), 0)
    dd_ = _D.Draw(mim)
    dd_.ellipse(((960 - ARCH_R - x0) * ss, (SEAT_Y - ARCH_R - y0) * ss, (960 + ARCH_R - x0) * ss, (SEAT_Y + ARCH_R - y0) * ss), fill=255)
    arch = np.asarray(mim)[: h * ss] > 127
    xm = np.minimum(X, 1920 - X)
    body = (Y >= PL_TOP) & (xm >= end_contour(Y[:, :1]))
    mb = body | arch
    mb = mb | mb[:, ::-1]
    mbc = ndimage.binary_closing(mb, structure=np.ones((3, 3)), iterations=10 * Z)
    mb = np.where(xm > VL[0] + VOL_R + 8, mbc, mb)          # fillets only where the arch meets the top run
    mb = mb | mb[:, ::-1]
    # the signed distance to the edge between samples (the EDT counts to the nearest sample centre: half a sample off)
    sd = np.where(mb, ndimage.distance_transform_edt(mb) - 0.5, 0.5 - ndimage.distance_transform_edt(~mb)) / ss
    sd = G_(sd, 0.5 * Z)
    inside = mb.astype(np.float32)
    bev = 2.4 * sm(1.0, 4.0, sd)
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
        sock -= 1.2 * np.exp(-np.clip(dd - SEAT_R, 0, None) / 0.8) * (dd > SEAT_R - 1)
    dd = np.hypot(X - 960, Y - SEAT_Y)
    sock -= 1.2 * np.exp(-np.clip(dd - MED_R, 0, None) / 0.8) * (dd > MED_R - 1)
    Hh = bev + groove + sock
    gy, gx = np.gradient(Hh * 1.0, 1 / ss)
    nrm = np.dstack([-gx, -gy, np.ones_like(gx)]); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    Ld = LD_PLATE / np.linalg.norm(LD_PLATE)
    diff = np.clip(nrm @ Ld, 0, 1)
    gy0_, gx0_ = np.gradient((bev + sock) * 1.0, 1 / ss)                # UI 24: the inlay lit by the plate, not its groove
    n0 = np.dstack([-gx0_, -gy0_, np.ones_like(gx0_)]); n0 /= np.linalg.norm(n0, axis=-1, keepdims=True)
    diff0 = np.clip(n0 @ Ld, 0, 1)
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
    vmask = np.clip(0.25 + 0.6 * mot, 0, 1) * 0.35 * sm(8.5, 9.5, sd) * sm(2.0, 3.0, line_d)
    alb = base * (1 + 0.10 * mot + 0.05 * brushed)[..., None]
    alb = alb * (1 - vmask[..., None]) + verd * vmask[..., None]
    edge = 0.6 * sm(3.6, 2.2, sd)                             # UI 24: the polished slope behind the bevel line, quieter
    inlay_line = (line_d < 0.5).astype(np.float32)          # UI 24: a hard 1 px line (was a 0.75 px gaussian)
    polished = np.array([0.46, 0.35, 0.22], np.float32)
    alb = alb * (1 - edge[..., None]) + polished * edge[..., None]
    lin = np.array([0.86, 0.68, 0.40], np.float32)
    col = alb * (0.28 + 0.95 * diff)[..., None] + np.array([1.0, 0.85, 0.6], np.float32) * (spec * (0.25 + 0.75 * edge))[..., None] * 0.6
    col = col * (1 - inlay_line[..., None] * 0.9) + lin * (inlay_line * (0.75 + 0.55 * diff0))[..., None]
    # UI 24: the rim, hard steps: a 1 px dark outline, then a 1 px light bevel (lit a little more on the top run)
    outline = (sd < 1.0)[..., None]
    bevel1 = ((sd >= 1.0) & (sd < 2.0))[..., None]
    light = np.array([0.80, 0.62, 0.38], np.float32) * (0.62 + 0.45 * diff)[..., None]
    col = np.where(bevel1, light, col)
    col = np.where(outline, np.array([0.040, 0.030, 0.022], np.float32), col)
    rgba = np.dstack([col * inside[..., None], inside])
    # P2 (UI 24: tight): a 1.5 px contact shadow (35 %) just outside each end's rim, onto the figures; none on the top run
    endz = sm(PL_X0 + 2 * VOL_R + 10, PL_X0 + 2 * VOL_R + 2, xm)
    ring = ((sd < 0) & (sd > -1.5)).astype(np.float32)
    sh = 0.35 * ring * endz
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
        ring = ((d < SEAT_R) & (d >= WELL_R)).astype(np.float64)       # UI 24: hard steps (exact coverage at 2x)
        t = np.clip((d - WELL_R) / BEZ, 0, 1)
        tilt = (t - 0.5) * 1.6
        nx, ny = dx / (d + 1e-3) * tilt, dy / (d + 1e-3) * tilt
        Ld = np.array([-0.5, -0.65, 0.58]); Ld /= np.linalg.norm(Ld)
        nz = np.sqrt(np.clip(1 - tilt ** 2 * 0.5, 0.1, 1))
        diff = np.clip(nx * Ld[0] + ny * Ld[1] + nz * Ld[2], 0, 1)
        spec = np.clip(diff, 0, 1) ** 24
        c = np.array([0.55, 0.42, 0.26]) * (0.30 + 1.05 * diff)[..., None] + np.array([1, 0.88, 0.64]) * (spec * 0.6)[..., None]
        inner = ((d >= WELL_R) & (d < WELL_R + 0.75)).astype(np.float64)   # a crisp dark inner lip
        c = c * (1 - 0.7 * inner[..., None])
        outl = ((d >= SEAT_R) & (d < SEAT_R + 1.0)).astype(np.float64)     # a crisp 1 px dark outline
        a = np.clip(ring + outl, 0, 1)
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


def clearances():
    """UI 27: each live part at the ends (the flask and its R tag at the left; the dash ring and its SPACE tag at the
    right, mirrored) from the inner edge of the end's inlay (sd = INL + 0.5 from the end's contour), px at 1080. The
    flask is its texture's alpha at its drawn rect; the dash its ring (DgSmall.RingD 64 at 0.84); the tags the chips
    (KeyTag: 16 tall, max(18, text + 9) wide: R 19, SPACE 54.4 in Alegreya Sans 800 16 tracked 0.6)."""
    yy = np.linspace(PL_TOP, 1080, 3000)
    cx = end_contour(yy)
    B = np.stack([cx[cx < 900], yy[cx < 900]], 1)
    # (UI 27 r2: the flask sits in the dash's seat, mirrored: its ring at FLASK_S round (FLASK_X, SEAT_Y + FLASK_DY), the
    # flask art inside it at FLASK_IN)
    fl = np.asarray(Image.open(os.path.join(UI, 'dg_meters', 'flask_full.png')).convert('RGBA'), np.float32)[..., 3] / 255
    fw, fh = 39 * FLASK_S * FLASK_IN, 56 * FLASK_S * FLASK_IN
    j, i = np.nonzero(fl > 0.5)
    fp = np.stack([FLASK_X - fw / 2 + (i + 0.5) * fw / fl.shape[1], SEAT_Y + FLASK_DY - fh / 2 + (j + 0.5) * fh / fl.shape[0]], 1)
    th = np.linspace(0, 2 * np.pi, 720)
    fp = np.concatenate([fp, np.stack([FLASK_X + 32 * FLASK_S * np.cos(th), SEAT_Y + FLASK_DY + 32 * FLASK_S * np.sin(th)], 1)])
    dp = np.stack([1920 - (DASH_X + 32 * 0.84 * np.cos(th)), SEAT_Y - 7 + 32 * 0.84 * np.sin(th)], 1)
    g = np.mgrid[0:41, 0:41].reshape(2, -1) / 40.0
    rect = lambda x0, w: np.stack([x0 + g[1] * w, 1061 + g[0] * 16], 1)
    out = {}
    for k, P in (('flask', fp), ('R', rect(round(FLASK_X - 9.5), 19)), ('dash', dp), ('SPACE', rect(1920 - (round(DASH_X - 27.2) + 54.4), 54.4))):
        d = np.sqrt(((P[:, None, :] - B[None]) ** 2).sum(-1)).min(1)
        out[k] = round(float(d.min() - (INL + 0.5)), 2)
    return out


# ================================================================== UI 27: the bar baked at a bottom-HUD scale
VARIANTS = (0.85,)   # hud.json bottomScale values with their own bake (DgPanel draws it when the knob matches)


def variant_consts(k):
    """the plate's design at the bottom HUD's scale k (about the screen's bottom middle), in SCREEN px, so every line
    stays a hard whole px: the top line and the end's x on whole px, the inlay's run on a row's middle, the volute a
    whole radius; seats, coin and arch at their mapped places (they are live-drawn there by the scaled HUD)."""
    mx = lambda x: 960 + (x - 960) * k
    my = lambda y: 1080 + (y - 1080) * k
    x0 = float(round(mx(PL_X0)))
    vr = float(round(VOL_R * k))
    rx0, ry0 = int(np.floor(mx(PANEL_RECT[0]))), int(np.floor(my(PANEL_RECT[1])))
    return dict(PL_X0=x0, PL_X1=1920 - x0, PL_TOP=float(round(my(PL_TOP))), VOL_R=vr, INL=round(INL * k - 0.5) + 0.5,
                FOOT_X=x0 - (PL_X0 - FOOT_X) * k, SEAT_Y=my(SEAT_Y), SEAT_XS=[mx(x) for x in SEAT_XS], WELL_R=WELL_R * k,
                BEZ=BEZ * k, SEAT_R=SEAT_R * k, MED_R=MED_R * k, ARCH_R=ARCH_R * k,
                PANEL_RECT=(rx0, ry0, 1920 - 2 * rx0, 1080 - ry0))


def bake_variant(k, Z):
    """the plate, bezels and coin at k (variant_consts), premultiplied, and its screen rect"""
    g = globals()
    keep = {n: g[n] for n in variant_consts(k)}
    try:
        g.update(variant_consts(k))
        P = plate(Z)
        P = over(P, bezels(Z))
        P = over(P, coin_static(Z, os.path.join(UI, 'dg_river')))
        return P, list(PANEL_RECT), {n: g[n] for n in ('PL_X0', 'PL_TOP', 'VOL_R', 'INL', 'FOOT_X')}
    finally:
        g.update(keep)


# ================================================================== the bake
def main():
    gr = json.load(open(os.path.join(SRC, 'keeper_grade.json')))
    Z = 2
    rep = {}
    # ---- the girl
    art, n_g1, n_isl = girl_art()
    cur = load_rgba(os.path.join(UI, 'lamp_life', 'drowned', 'lamp_cold.png'))
    assert art.shape == cur.shape, (art.shape, cur.shape)
    rep['girl islands removed'] = n_isl
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
    # (the keeper is built in its frame, UI 24's screen; UI 27 moves the whole sprite by K_D whole px)
    gx0, gy0, gw, gh = girl_screen_rect(ref=True)
    lx0 = 1920 - (gx0 + gw) + LOCK_D[0]
    # the sprite's rect: whole 1080 px round the keeper and the lock, down to the frame row that lands on the foot
    rx0 = int(np.floor(min(kx0, 1920 - girl_contact() - K_D[0] - 1))) - 2
    ry0 = int(np.floor(min(ky0, 966 + LOCK_D[1]))) - 2
    rx1 = int(np.ceil(kx0 + kw * K_S)) + 2
    ry1 = 1080 - K_D[1]
    rep['keeper source below the foot (px)'] = round(ky0 + kh * K_S - ry1, 2)
    assert ky0 + kh * K_S >= ry1 + 4, rep                   # UI 27: no visible cut at the screen's foot
    cvz = ((rx1 - rx0) * Z, (ry1 - ry0) * Z)
    Kp = place(np.dstack([rgb, a]), (kx0 - rx0) * Z, (ky0 - ry0) * Z, kw * K_S * Z, kh * K_S * Z, cvz)
    Fp = place(np.dstack([np.ones_like(rgb), fire * a]), (kx0 - rx0) * Z, (ky0 - ry0) * Z, kw * K_S * Z, kh * K_S * Z, cvz)[..., 3]
    jj, ii = np.mgrid[0:cvz[1], 0:cvz[0]].astype(np.float32)
    Xi, Yi = rx0 + (ii + 0.5) / Z - 0.5, ry0 + (jj + 0.5) / Z - 0.5      # mock pixel-index units
    # (UI 27: her art's foot rows repeated down, so the risen lock still runs past the screen's foot)
    pad = int(np.ceil((-K_D[1] + 4) * art.shape[0] / gh)) if K_D[1] < 0 else 0
    lart = np.concatenate([art, np.repeat(art[-1:], pad, 0)], 0)
    Lk = place(lart[:, ::-1].copy(), (lx0 - rx0) * Z, (gy0 + LOCK_D[1] - ry0) * Z, gw * Z, gh * lart.shape[0] / art.shape[0] * Z, cvz)
    Lk = lock_taper(Lk * lock_window(Xi, Yi)[..., None], Yi, Z)
    ls = straight(Lk)
    Lk = np.dstack([final_grade(ls, np.zeros(ls.shape[:2], np.float32), gr) * Lk[..., 3:4], Lk[..., 3]])
    K = over(Lk, Kp) if LOCK_ON else Kp
    K, n_plug = plug_holes(K, (Xi > 1240) & (Yi > 960), 60 * Z * Z)
    rep['K1 hole px plugged (2x)'] = n_plug
    K, k_back, k_fill = keeper_back_line(K, Xi, Yi, Z)
    rep['back line fill px2 (girl, keeper)'] = [round(_GA['fill'], 1), round(k_fill, 1)]
    # K4
    bcx = kx0 + gr['BOWL_C'] * K_S
    rim_y = ky0 + gr['RIM_C'] * K_S
    egx, egy = bcx, rim_y - 0.62 * EG_R
    dgl = np.hypot(Xi - egx, Yi - egy)
    away = (1 - np.clip(G_((Fp > 0.05).astype(np.float32), 3.0 * Z) * 3, 0, 1)) * sm(EG_R + 8, EG_R + 20, dgl)
    ks = straight(K)
    ks = k4_curve(ks, away, gr['K4_thr'])
    K = np.dstack([ks * K[..., 3:4], K[..., 3]])
    # UI 24: his inner (left) side cleaned like hers (crisp, islands, decontaminated), x < 1350
    Ks, n_kisl = clean_edges(np.dstack([straight(K), K[..., 3]]), sm(1360.0, 1340.0, Xi))
    K = np.dstack([Ks[..., :3] * Ks[..., 3:4], Ks[..., 3]])
    rep['keeper islands removed'] = n_kisl
    bl, br = kx0 + gr['BOWL_L'] * K_S, kx0 + gr['BOWL_R'] * K_S
    front = sm(rim_y - 1.0, rim_y + 1.5, Yi) * (Xi > bl - 2) * (Xi < br + 2)
    kd = os.path.join(UI, 'dg_keeper')
    save_rgba(os.path.join(kd, 'keeper.png'), np.dstack([straight(K), K[..., 3]]))
    save_rgba(os.path.join(kd, 'keeper_lip.png'), np.dstack([straight(K), K[..., 3] * front]))
    # ---- the panel at 2x
    # the figures' edges at 2x: her art (scaled) and the keeper sprite, full width rows from the panel's top
    py0 = PANEL_RECT[1]
    nrow = (1080 - py0) * Z
    gx0, gy0, gw, gh = girl_screen_rect()
    sx0, sy0, sx1 = rx0 + K_D[0], ry0 + K_D[1], rx1 + K_D[0]          # the keeper sprite's rect on the screen
    ga = place(art, gx0 * Z, (gy0 - py0) * Z, gw * Z, gh * Z, (1920 * Z, nrow))[..., 3]
    ka = np.zeros((nrow, 1920 * Z), np.float32)
    ka[:, sx0 * Z:sx1 * Z] = K[(py0 - sy0) * Z:, :, 3]
    rows, ge, ke = figure_edges(ga, ka, Z, py0)
    cl = end_contour(rows)
    P = plate(Z)
    P = over(P, bezels(Z))
    P = over(P, coin_static(Z, os.path.join(UI, 'dg_river')))
    save_rgba(os.path.join(UI, 'dg_panel', 'panel.png'), np.dstack([straight(P), P[..., 3]]))
    variants = []
    for vk in VARIANTS:
        Pv, vrect, vc = bake_variant(vk, Z)
        name = f'dg_panel/panel_{int(round(vk * 100)):03d}.png'
        save_rgba(os.path.join(UI, *name.split('/')), np.dstack([straight(Pv), Pv[..., 3]]))
        variants.append({'scale': vk, 'texture': name, 'screen_rect': vrect, 'design': {n: round(float(v), 3) for n, v in vc.items()}})
    rep['bar variants'] = variants
    # UI 24: every row from the panel top: each figure tucks >= TUCK_MIN under its end, and no backdrop shows between
    # (a hole the figure itself encloses, a hair loop, is not a gap: the checks read the figures with their holes filled)
    pa, half = P[..., 3], P.shape[1] // 2
    gaf = ndimage.binary_fill_holes(place(art, gx0 * Z, (gy0 - 820) * Z, gw * Z, gh * Z, (1920 * Z, 260 * Z))[..., 3] > 0.5)
    gaf = gaf[(py0 - 820) * Z:]
    kaf = np.zeros((nrow, 1920 * Z), bool)
    kaf[:, sx0 * Z:sx1 * Z] = ndimage.binary_fill_holes(K[..., 3] > 0.5)[(py0 - sy0) * Z:]
    tg, tk, gaps = [], [], 0
    for r in range(pa.shape[0]):
        if rows[r] < PL_TOP + 0.5:
            continue
        lc = np.nonzero(pa[r, :half] > 0.5)[0].min()
        rc = np.nonzero(pa[r, half:] > 0.5)[0].max() + half
        tg.append(ge[r] - (PANEL_RECT[0] + lc / Z)); tk.append((PANEL_RECT[0] + (rc + 1) / Z) - ke[r])
        gl, gk = PANEL_RECT[0] * Z + lc - 1, PANEL_RECT[0] * Z + rc + 1
        if not gaf[r, gl] or not kaf[r, gk]:
            gaps += 1
            rep.setdefault('gap at', []).append(round(float(rows[r]), 2))
    rep['tuck min (girl, keeper)'] = [round(min(tg), 2), round(min(tk), 2)]
    rep['gap rows'] = gaps
    assert min(tg) >= TUCK_MIN and min(tk) >= TUCK_MIN and gaps == 0, rep
    # UI 27, flush backs: the 12 rows over PL_TOP, each back's edge FLUSH inward of its volute's inner end (vie); no
    # statue px over the panel further in than that (never along the top line over the seats); the contacts mirror
    kfull = np.zeros((1080 * Z, 1920 * Z), np.float32)
    kfull[sy0 * Z:1080 * Z, sx0 * Z:sx1 * Z] = K[..., 3]
    gfull = place(art, gx0 * Z, gy0 * Z, gw * Z, gh * Z, (1920 * Z, 1080 * Z))[..., 3]
    vie = PL_X0 + 2 * VOL_R
    fl = {'girl': [], 'keeper': []}
    g_in, k_in = -1e3, 1e9
    g_top = k_top_ = None
    for r in range(int(PL_TOP)):
        gmr = (gfull[r * Z:r * Z + Z, :960 * Z] > 0.5).any(0)
        km = (kfull[r * Z:r * Z + Z, 960 * Z:] > 0.5).any(0)
        if gmr.any():
            g_top = r if g_top is None else g_top
            e = (np.nonzero(gmr)[0].max() + 1) / Z; g_in = max(g_in, e)
            if r >= PL_TOP - 12: fl['girl'].append(round(e - vie, 2))
        if km.any():
            k_top_ = r if k_top_ is None else k_top_
            e = 960 + np.nonzero(km)[0].min() / Z; k_in = min(k_in, e)
            if r >= PL_TOP - 12: fl['keeper'].append(round((1920 - vie) - e, 2))
    rep['flush rows over PL_TOP, px inward of the volute end (girl, keeper)'] = [fl['girl'], fl['keeper']]
    gc, kc = vie + fl['girl'][-1], (1920 - vie) - fl['keeper'][-1]
    rep['contacts (girl, keeper, mirror error)'] = [round(gc, 2), round(kc, 2), round(gc + kc - 1920, 2)]
    rep['furthest in over the panel (girl, keeper)'] = [round(g_in, 2), round(k_in, 2)]
    rep['tops (girl, keeper)'] = [g_top, k_top_]
    assert len(fl['girl']) == 12 and len(fl['keeper']) == 12, rep
    assert all(FLUSH[0] <= v <= FLUSH[1] for v in fl['girl'] + fl['keeper']), rep
    assert g_in <= vie + FLUSH[1] and k_in >= 1920 - vie - FLUSH[1] and abs(gc + kc - 1920) <= 1.0, rep
    assert abs(g_top - k_top_) <= 2 and -K_D[1] <= 12, rep
    # UI 27 r2: the BAND rows over PL_TOP: each back's edge never moves back out going down (no notch, wedge or loop),
    # and from it inward the figure is solid SOLID_W px in every sub-row (no see-through between edge and mass)
    eg, ek, sol = [], [], {'girl': 1e9, 'keeper': 1e9}
    for r in range(int(PL_TOP) - BAND, int(PL_TOP)):
        gm_ = gfull[r * Z:r * Z + Z, :960 * Z] > 0.5
        km_ = kfull[r * Z:r * Z + Z, 960 * Z:] > 0.5
        eg.append((np.nonzero(gm_.any(0))[0].max() + 1) / Z)
        ek.append(960 + np.nonzero(km_.any(0))[0].min() / Z)
        for q in range(Z):
            i1 = np.nonzero(gm_[q])[0].max()
            run = i1 - (np.nonzero(~gm_[q, :i1 + 1])[0].max() if (~gm_[q, :i1 + 1]).any() else -1)
            sol['girl'] = min(sol['girl'], run / Z)
            i0 = np.nonzero(km_[q])[0].min()
            nz = np.nonzero(~km_[q, i0:])[0]
            sol['keeper'] = min(sol['keeper'], (nz.min() if len(nz) else km_.shape[1] - i0) / Z)
    back_out = [max(0.0, float(-np.diff(eg).min())), max(0.0, float(np.diff(ek).max()))]
    rep['band: worst move back out going down (girl, keeper), solid px from the edge'] = [back_out, {k: round(v, 2) for k, v in sol.items()}]
    rep['band edges every 5th row (girl, keeper)'] = [eg[::5], ek[::5]]
    rep['band back-out rows'] = [int(PL_TOP) - BAND + 1 + int(i) for i in np.nonzero(np.diff(eg) < -0.01)[0]] + [int(PL_TOP) - BAND + 1 + int(i) for i in np.nonzero(np.diff(ek) > 0.01)[0]]
    assert max(back_out) <= 0.01 and min(sol.values()) >= SOLID_W, rep
    # UI 27: her orb and her hand: the orb >= 52 px, the hand under it (her palm, ref x <= 398) whole on the screen
    orb = list(girl_to_screen(ANCHOR[0] + (GLOBE[0] - ANCHOR[0]) * S, ANCHOR[1] + (GLOBE[1] - ANCHOR[1]) * S)) + [GLOBE[2] * G_S]
    hand = gm[..., 1]
    rgx0, rgy0, rgw, rgh = girl_screen_rect(ref=True)
    cols = int((398 - rgx0) / rgw * hand.shape[1])
    hr = np.nonzero((hand[:, :cols] > 0.3).any(1))[0].max() + 1
    palm = gy0 + hr * gh / hand.shape[0]
    rep['orb (x, y, r)'] = [round(v, 2) for v in orb]; rep['palm foot'] = round(palm, 2)
    assert orb[2] >= 52.0 and palm <= 1078.0, rep
    # UI 27: the live parts at each end from the end's inlay
    cle = clearances()
    rep['clearance to the inlay (flask, R, dash, SPACE)'] = cle
    near = min(min(cle['flask'], cle['R']), min(cle['dash'], cle['SPACE']))
    assert all(v >= CLEAR[0] for v in cle.values()) and near <= CLEAR[1], rep
    # ---- the fire
    shutil.copy(os.path.join(SRC, 'fw_9931_0.png'), os.path.join(kd, 'fire.png'))
    shutil.copy(os.path.join(SRC, 'fo_9932_0.png'), os.path.join(kd, 'fire_ready.png'))
    # ---- the geometry
    geo = geometry(kx0 + K_D[0], ky0 + K_D[1], (sx0, sy0, rx1 - rx0, ry1 - ry0), gr, rows, cl, (g_top, k_top_))
    geo['panel']['variants'] = variants
    geo['panel']['variants_note'] = ('UI 27: the bar baked at a bottom-HUD scale, in screen px (2x): DgPanel draws texture at screen_rect '
                                     'when hud.json bottomScale is scale (its 1 px lines stay whole there)')
    json.dump(geo, open(os.path.join(kd, 'hud_a_geo.json'), 'w'), indent=1)
    rep['keeper rect'] = geo['keeper']['rect']; rep['glass'] = geo['glass']['center']
    print(json.dumps(rep))


def geometry(kx0, ky0, krect, gr, rows, cl, tops):
    gx0, gy0, gw, gh = girl_screen_rect()
    orb = girl_to_screen(ANCHOR[0] + (GLOBE[0] - ANCHOR[0]) * S, ANCHOR[1] + (GLOBE[1] - ANCHOR[1]) * S)
    bcx = kx0 + gr['BOWL_C'] * K_S
    rim_y = ky0 + gr['RIM_C'] * K_S
    sel = rows >= PL_TOP + VOL_R
    return {
        'note': 'tools/uiforge/dg_keeper_hud.py: HUD A (the keeper). 1080 px screen coords; rects are [x, y, w, h], continuous '
                'edges (pixel i spans [i, i+1]); every texture is 2x its rect. Day and night use the same sprites.',
        'heights': {'left': 1080 - tops[0], 'middle': int(1080 - (SEAT_Y - ARCH_R)), 'right': 1080 - tops[1]},
        'bottom_note': 'UI 27: hud.json bottomScale scales all of this about the bottom middle of the screen (960, 1080) at run time',
        'girl': {'texture': 'lamp_life/drowned/lamp_cold.png', 'mask': 'lamp_life/drowned/lamp_mask.png',
                 'rect_unscaled': [GIRL_AT[0], GIRL_AT[1], GIRL_SIZE[0], GIRL_SIZE[1]],
                 'rect_unscaled_note': 'mock place() rect; lamp_geo.json at is 295.33 (the mock matched the frame at -0.5)',
                 'group_anchor': list(ANCHOR), 'group_scale': G_S, 'group_offset': list(G_D),
                 'group_note': 'UI 27: her screen px = group_anchor + (unscaled - group_anchor) group_scale + group_offset',
                 'ref_scale': S,
                 'rect': [round(gx0, 3), round(gy0, 3), round(gw, 3), round(gh, 3)],
                 'globe': [round(orb[0], 3), round(orb[1], 3), round(GLOBE[2] * G_S, 3)],
                 'shine_run': 's = x + 0.5 (clamp(y, 840, 1040) - 840) + 1.1 max(y - 975, 0) smoothstep(520, 575, x); front 640 (mock7.py path_s, line 108); '
                              'UI 27: x, y in the reference frame (group_anchor + (unscaled - group_anchor) ref_scale), so it follows her',
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
                  'flask': {'center': [FLASK_X, SEAT_Y + FLASK_DY], 'scale': FLASK_S, 'inner': FLASK_IN, 'count_badge': [FLASK_X + 15, SEAT_Y - 28, 9],
                            'note': 'UI 27 r2: the draught in the dash seat (ring and well as the dash, mirrored), the flask inside at inner'},
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
