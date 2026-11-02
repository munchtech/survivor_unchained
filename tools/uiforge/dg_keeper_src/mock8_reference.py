"""R6 (UI 22 reviser 3): her locks down her back (girl6.py -> girl_R6.png), the girl shifted DXG, a symmetric plate
with curled-lock end caps, the keeper REDO (gen/kk65_6022_0), the chalice B REDO (gen/cb75_6032_0), READY brightest.
Equal gaps: GAP_L (girl to plate) and GAP_R (plate to the right element), both measured as the min distance between
the alpha masks.
R5 docstring: R5 (UI 22 reviser 2): her hand repainted (girl5.py), layouts A (the keeper) and B (the Flare brazier, no figure).
python mock5.py day|night [charge] [tag] [A|B]   (R4 notes below)

Left: the Drowned Girl (today's art, hair healed to end in curled lock tips: girl_R4.png), 0.94 about her outer bottom
corner, the shine on her hair. Right: the keeper as a bust (gen/ks55_9924_1, Krea i2i of keeper_guide_smooth.png), her
bronze quantile-matched to the girl's, holding the Flare: an ember glass set in a slim bronze bezel, sitting in her bowl,
filled with fire to the charge level; READY = full, white-hot, flames over it, the Q chip lit "Q READY".
Middle: its own piece, a dark bronze plate with crisp bevelled edges and an inlaid line, an arch round the level coin;
flask [R], three seats, the coin (level + XP ring), three seats, dash [SPACE]. Seats: today's wells at 1:1 (63 px icon)
in a slim crisp bezel. layout "alt": the keeper holds coals only, the Flare is a socket at the plate's right end."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
import cv2
import parts
import json
from cfg import WT
sys.path.insert(0, os.path.join(WT, 'tools', 'uiforge'))
import dg_keeper_hud as HB
HERE = os.path.dirname(os.path.abspath(__file__))
parts.GIRL = os.path.join(HERE, "girl_R4.png")
from parts import *

NIGHT = len(sys.argv) > 1 and sys.argv[1] == "night"
CHARGE = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
TAG = sys.argv[3] if len(sys.argv) > 3 else "R4"
LAYOUT = sys.argv[4] if len(sys.argv) > 4 else "A"
ALT = False
B = LAYOUT == "B"
READY = CHARGE >= 0.999
KEEPER = os.environ.get("KEEPER", "kk65_6022_0")
DXG = int(os.environ.get("DXG", "0"))       # the girl moved left (px)
GAP_R = float(os.environ.get("GAP_R", "14.2" if LAYOUT == "B" else "3.0"))   # placement offset -> a measured gap of ~22.8
S = 0.94
FONTS = os.path.join(WT, "godot", "art", "fonts")
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
lumw = np.array([0.2126, 0.7152, 0.0722], np.float32)
G_ = ndimage.gaussian_filter

# ---- the middle's layout
WELL_R = 31.5                 # today's well (the icon) at 1:1
BEZ = 3.5                     # the slim bezel
SEAT_R = WELL_R + BEZ         # 35
SEAT_Y = 1042.0
MED_R = 37.0
GAP = 5.0
PITCH = 2 * SEAT_R + GAP
SEAT_XS = [960 - MED_R - GAP - SEAT_R - k * PITCH for k in (2, 1, 0)] + \
          [960 + MED_R + GAP + SEAT_R + k * PITCH for k in (0, 1, 2)]
FLASK_X = SEAT_XS[0] - SEAT_R - 4 - 21
DASH_X = 1920 - FLASK_X
VOL_R = 12.0                   # the end caps: a curled lock tip (volute) at each end of the top line
PL_X0 = float(os.environ.get("PL_X0", "626"))
PL_X1 = 1920 - PL_X0
PL_TOP = 1003.0
ARCH_R = MED_R + 6.0
XP_FRAC = 0.35 if NIGHT else 0.62
LEVEL = 14
SHINE_FRONT = float(os.environ.get("SHINE", "640"))

bd = load_rgb(OUT + (r"\bd21nx_hud0.png" if NIGHT else r"\bd21vx_hud1.png"))
hudf = load_rgb(OUT + (r"\bd21n_hud0.png" if NIGHT else r"\bd21v_hud5.png"))
canvas = np.dstack([bd, np.ones(bd.shape[:2], np.float32)])


def straight(L):
    a = np.maximum(L[..., 3:4], 1e-5)
    return np.where(L[..., 3:4] > 1e-4, L[..., :3] / a, 0)


def sm(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ================================================================== the girl
from girl5 import girl_layer5
_g1, _ng1 = HB.fix_girl(load_rgba(os.path.join(HERE, "girl_R6.png")))
Image.fromarray((np.clip(_g1, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(HERE, "girl_R6g.png"))
GIRL_ART = os.path.join(HERE, "girl_R6g.png")
G0 = girl_layer5(NIGHT, art_path=GIRL_ART)
G = scale_layer(G0, S, 295.33, 1080)
GLOBE_S = (295.33 + (378 - 295.33) * S, 1080 - (1080 - 960) * S, 59.4 * S)
mk = np.asarray(Image.open(os.path.join(DGR, "xp_light.png")).convert("RGB"), np.float32) / 255
M = place(np.dstack([mk, np.ones(mk.shape[:2], np.float32)]), 295, 822, 1310, 258)
M = scale_layer(M, S, 295.33, 1080)
_hm = np.asarray(Image.open(os.path.join(HERE, "hair_R6.png")), np.float32) / 255
_tw = np.asarray(Image.open(os.path.join(HERE, "tail_R6.png")), np.float32) / 255
TM = place(np.dstack([_hm, _tw, _tw * 0, np.ones_like(_hm)]), *GIRL_AT, *GIRL_SIZE)
TM = scale_layer(TM, S, 295.33, 1080)


def shift_x(L, dx):
    out = np.zeros_like(L)
    if dx < 0:
        out[:, :dx] = L[:, -dx:]
    elif dx > 0:
        out[:, dx:] = L[:, :-dx]
    else:
        out = L.copy()
    return out


G = shift_x(G, DXG); M = shift_x(M, DXG); TM = shift_x(TM, DXG)
GLOBE_S = (GLOBE_S[0] + DXG, GLOBE_S[1], GLOBE_S[2])
HAIR = M[..., 0] * (1 - TM[..., 1]) + TM[..., 0]
CREST = M[..., 1] * (1 - TM[..., 1])


def path_s(x, y):
    # R6: crown -> back of the head (along x, as before), then down her back (the locks' run to the bottom edge)
    return x + 0.5 * (np.clip(y, 840, 1040) - 840) + 1.1 * np.clip(y - 975, 0, None) * sm(520 + DXG, 575 + DXG, x)


def glint(front, peak=1.0, trail=0.20, lead=18.0, tail=190.0):
    dd = path_s(xx, yy) - front
    return np.where(dd > 0, peak * np.exp(-(dd / lead) ** 2), peak * np.exp(-(dd / 30) ** 2) + trail * np.exp(dd / tail))


def shine_on(L, mask, crest):
    k = np.clip(glint(SHINE_FRONT) * mask, 0, 0.9)
    fc = straight(L)
    lum = fc @ lumw
    cr = np.maximum(sm(0.30, 0.85, crest), sm(0.40, 0.75, lum))
    k = k * (0.45 + 0.55 * cr)
    c = np.array([0.88, 0.83, 1.0] if NIGHT else [0.80, 0.89, 1.0], np.float32)
    cool = c[None, None] * np.clip(lum * 1.15 + 0.16, 0, 0.95)[..., None]
    out = L.copy()
    out[..., :3] = (fc * (1 - k[..., None]) + cool * k[..., None]) * L[..., 3:4]
    return out


G = shine_on(G, HAIR, CREST)
gfc = straight(G)
gm = (G[..., 3] > 0.98) & (np.hypot(xx - GLOBE_S[0], yy - GLOBE_S[1]) > GLOBE_S[2] + 4)


def lab_of(rgb):
    return cv2.cvtColor((np.clip(rgb, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)


G_LAB = lab_of(gfc)
QS = np.linspace(0.5, 99.5, 41)
G_Q = [np.percentile(G_LAB[..., c][gm], QS) for c in range(3)]

# ================================================================== the keeper (a bust)
K_S = float(os.environ.get("K_S", "0.28"))
K_TOP = float(os.environ.get("K_TOP", "205"))
k_rgb = np.asarray(Image.open(os.path.join(HERE, "gen", KEEPER + ".png")).convert("RGB"), np.float32) / 255
k_a = np.asarray(Image.open(os.path.join(HERE, "gen", KEEPER + "_cut.png")).convert("RGBA"), np.float32)[..., 3] / 255
kh, kw = k_a.shape
k_top = np.nonzero((k_a > 0.5).any(1))[0].min()
BOWL_C, RIM_C, BOWL_L, BOWL_R = 875.0, 452.0, 655.0, 1095.0      # measured on kk65_6022_0 (canvas px)
if KEEPER == 'ks60_2304_0':
    BOWL_C, RIM_C, BOWL_L, BOWL_R = 880.0, 401.0, 690.0, 1140.0  # K2: ks60's lip top (apex 880, y 401), tips 622..1135, hood < 680
KGRADE = os.path.join(HERE, 'keeper_grade.json')
FIXED = NIGHT and os.environ.get('KFIX', '1') == '1'
GR = json.load(open(KGRADE)) if FIXED else {}
k_left = np.nonzero((k_a > 0.5).any(0))[0].min()
kx0 = PL_X1 + GAP_R + 1.0 - k_left * K_S
ky0 = (1080 - K_TOP) - k_top * K_S
if B:
    # ---- layout B: no figure. The Flare brazier (gen/c78_9973_0, Krea i2i of b_guide2.png): a chalice of hair-like
    # bronze locks rising behind the glass like a flame, a cup and a foot; the painted orb (512, 520) r 172 is replaced by
    # the ember glass drawn larger, r_gen 198 at (512, 502), so it sits deeper in the cup and the whole stays low.
    BR_GEN = os.environ.get("BR_GEN", "cb75_6032_0")
    BR_R = float(os.environ.get("BR_R", "52"))   # the glass on screen
    BR_LMAP = float(os.environ.get("BR_LMAP", "1.0"))    # 0 = the painting's own values, 1 = the girl's quantiles
    BR_P90 = float(os.environ.get("BR_P90", "0.95"))       # p90 luma target relative to the girl's
    BR_CURL = os.environ.get("BR_CURL", "0") == "1"      # keep the front curl lock over the glass
    ORB0, ORB1 = (561.0, 380.0, 229.0), (561.0, 380.0, 226.0)    # cb75_6032_0: what is replaced; the drawn glass
    CUP_Y, CURL = 566.0, (0.0, 0.0, 1.0)         # the front band's top at the glass's centre line (visible bottom)
    BR_FOOT = float(os.environ.get("BR_FOOT", "1088"))
    K_S = BR_R / ORB1[2]
    _im = np.asarray(Image.open(os.path.join(HERE, "gen", BR_GEN + ".png")).convert("RGB"), np.float32) / 255
    _h, _w = _im.shape[:2]
    _gy, _gx = np.mgrid[0:_h, 0:_w].astype(np.float32)
    _mx = _im.max(-1)
    _warm = (_im[..., 0] - _im[..., 2]) / np.maximum(_mx, 1e-3)
    _abg = sm(0.022, 0.07, _mx)
    _bronze = sm(0.18, 0.30, _warm) * sm(0.05, 0.11, _mx)
    _in0 = sm(ORB0[2] + 1.5, ORB0[2] - 1.5, np.hypot(_gx - ORB0[0], _gy - ORB0[1]))
    _in1 = sm(ORB1[2] + 1.0, ORB1[2] - 1.0, np.hypot(_gx - ORB1[0], _gy - ORB1[1]))
    _curl = sm(CURL[2] + 2, CURL[2] - 2, np.hypot(_gx - CURL[0], _gy - CURL[1]))
    # R6: inside the painted orb only the bronze (the locks over its shoulders, the band across its foot) is solid
    _labi = cv2.cvtColor((_im * 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    _chr = G_(np.hypot(_labi[..., 1] - 128, _labi[..., 2] - 128), 2.0)
    _dor = np.hypot(_gx - ORB1[0], _gy - ORB1[1])
    _fb = ndimage.binary_closing(ndimage.binary_opening((_chr > 15) & ((_gy > 540) | (_dor > ORB1[2] - 22)), iterations=3), iterations=3)
    _below = G_(_fb.astype(np.float32), 1.0) * _abg
    k_a = _abg * (1 - _in0) + _below * _in0
    _lab, _n = ndimage.label(k_a > 0.5)
    _sz = ndimage.sum(np.ones_like(k_a), _lab, range(1, _n + 1))
    k_a = k_a * G_(ndimage.binary_dilation(np.isin(_lab, 1 + np.nonzero(_sz > 800)[0]), iterations=2).astype(np.float32), 1.0)
    k_rgb = np.clip(np.where(_in0[..., None] > 0.5, _im, _im / np.maximum(_abg, 0.3)[..., None]), 0, 1) * k_a[..., None]
    # in front of the (larger) glass: the cup below its lip, and the curl
    _front = np.maximum(_below * _abg, _curl * _bronze * BR_CURL) * _in1
    kh, kw = k_a.shape
    _left = np.nonzero((k_a > 0.5).any(0))[0].min()
    kx0 = PL_X1 + GAP_R + 1.0 - _left * K_S
    _foot = np.nonzero((k_a > 0.5).any(1))[0].max()
    ky0 = BR_FOOT - _foot * K_S
    RIM_C = CUP_Y
    BOWL_C = ORB1[0]


GRD = {}


def keeper_layer():
    a = np.clip(k_a, 0, 1)
    st = np.clip(k_rgb / np.maximum(a, 0.25)[..., None], 0, 1)
    st = np.where(a[..., None] > 0.02, st, 0)
    if not B and os.environ.get("K_BIL", "1") == "1":
        # R6: Krea's painterly mottle off the broad planes (edge-preserving), toward the girl's smooth cast surfaces
        u8 = (st * 255).astype(np.uint8)
        for _ in range(2):
            u8 = cv2.bilateralFilter(u8, 0, 18, 6)
        st = u8.astype(np.float32) / 255
    hsv = cv2.cvtColor((st * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    fire = sm(0.45, 0.75, hsv[..., 1] / 255) * sm(0.35, 0.65, hsv[..., 2] / 255) * (hsv[..., 0] < 30)
    fire = G_(fire, 1.0)
    m = (a > 0.98) & (fire < 0.05)
    lab = lab_of(st)
    lab2 = lab.copy()
    kq = np.percentile(lab[..., 0][m], QS)          # value: quantile map onto the girl's
    gq = G_Q[0]
    if FIXED:
        kq, gq = np.array(GR['kq']), np.array(GR['gq'])
    lab2[..., 0] = np.interp(lab[..., 0], kq, gq)
    if B:
        lab2[..., 0] = lab[..., 0] * (1 - BR_LMAP) + lab2[..., 0] * BR_LMAP
    # hue and saturation: one chroma scale (the girl's spread over the keeper's) about the girl's mean -> same patina
    ka, kb = lab[..., 1][m].mean(), lab[..., 2][m].mean()
    sk = np.sqrt(lab[..., 1][m].var() + lab[..., 2][m].var())
    sg = np.sqrt(G_LAB[..., 1][gm].var() + G_LAB[..., 2][gm].var())
    g_a, g_b = G_LAB[..., 1][gm].mean(), G_LAB[..., 2][gm].mean()
    if FIXED:
        ka, kb, sk, sg, g_a, g_b = GR['ka'], GR['kb'], GR['sk'], GR['sg'], GR['g_a'], GR['g_b']
    GRD.update(kq=[float(v) for v in kq], gq=[float(v) for v in gq], ka=float(ka), kb=float(kb), sk=float(sk), sg=float(sg),
               g_a=float(g_a), g_b=float(g_b))
    lab2[..., 1] = g_a + (lab[..., 1] - ka) * (sg / sk)
    lab2[..., 2] = g_b + (lab[..., 2] - kb) * (sg / sk)
    rgb = cv2.cvtColor(np.clip(lab2, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32) / 255
    rgb = rgb * (1 - fire[..., None]) + st * fire[..., None]
    L = place(np.dstack([rgb, a]), kx0, ky0, kw * K_S, kh * K_S)
    F = place(np.dstack([np.ones((kh, kw, 3), np.float32), fire * a]), kx0, ky0, kw * K_S, kh * K_S)[..., 3]
    return L, F


K, KFIRE = keeper_layer()
# UI 23 (judge hud23-mock fix 1): a lock on the keeper's back falls into the right end cap, mirroring her tail lock
if not B and os.environ.get("KLOCK", "1") == "1":
    _raw = shift_x(scale_layer(place(load_rgba(GIRL_ART), *GIRL_AT, *GIRL_SIZE), S, 295.33, 1080), DXG)
    _mir = shift_x(_raw[:, ::-1].copy(), int(HB.LOCK_D[0]))
    _mir = np.concatenate([np.zeros((int(HB.LOCK_D[1]), W, 4), np.float32), _mir[:H - int(HB.LOCK_D[1])]], 0)
    _w = HB.lock_window(xx, yy)
    _lock = _mir * _w[..., None]
    K = over(_lock, K)
    K, _nplug = HB.plug_holes(K, (xx > 1240) & (yy > 960), 60)
    print('K1 plugged px', _nplug)
    if os.environ.get("DUMP_K") == "1":
        # the re-surface guide, in the keeper image's own pixels: its smoothed, girl-graded paint + the lock, on black
        from scipy.ndimage import map_coordinates as _mc
        _vv, _uu = np.mgrid[0:kh, 0:kw].astype(np.float32)
        _sx, _sy = kx0 + (_uu + 0.5) * K_S - 0.5, ky0 + (_vv + 0.5) * K_S - 0.5
        _Ls = np.dstack([_mc(_lock[..., c], [_sy, _sx], order=1) for c in range(4)])
        _a = np.clip(k_a, 0, 1)
        _st = np.clip(k_rgb / np.maximum(_a, 0.25)[..., None], 0, 1) * (_a[..., None] > 0.02)
        _u8 = (_st * 255).astype(np.uint8)
        for _ in range(3):
            _u8 = cv2.bilateralFilter(_u8, 0, 22, 7)
        _kp = _u8.astype(np.float32) / 255 * _a[..., None]
        _out = _kp + _Ls[..., :3] * (1 - _a[..., None])
        _al = np.clip(_a + _Ls[..., 3] * (1 - _a), 0, 1)
        Image.fromarray((np.clip(_out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(HERE, "keeper_guide23.png"))
        Image.fromarray((_al * 255 + 0.5).astype(np.uint8)).save(os.path.join(HERE, "keeper_guide23_alpha.png"))
        print("DUMPED guide", kw, kh, "kx0", kx0, "ky0", ky0, "K_S", K_S)
        sys.exit(0)
bcx = kx0 + BOWL_C * K_S
rim_y = ky0 + RIM_C * K_S
bl, br = kx0 + BOWL_L * K_S, kx0 + BOWL_R * K_S
# the bowl's front (below the rim line), to lay back over the ember glass
BOWL_FRONT = K[..., 3] * sm(rim_y - 1.0, rim_y + 1.5, yy) * (xx > bl - 2) * (xx < br + 2)
if B:
    KFIRE = KFIRE * 0
    BOWL_FRONT = np.clip(place(np.dstack([np.ones((kh, kw, 3), np.float32), _front]), kx0, ky0, kw * K_S, kh * K_S)[..., 3], 0, 1)
    BR_GLASS = (kx0 + ORB1[0] * K_S, ky0 + ORB1[1] * K_S)


# ================================================================== supersampled drawing helpers
def ss_grid(x0, y0, x1, y1, ss=4):
    gy, gx = np.mgrid[0:(y1 - y0) * ss, 0:(x1 - x0) * ss].astype(np.float32)
    return x0 + (gx + 0.5) / ss, y0 + (gy + 0.5) / ss


def ss_down(a, ss=4):
    h, w = a.shape[:2]
    return a.reshape(h // ss, ss, w // ss, ss, *a.shape[2:]).mean((1, 3))


def to_canvas(rgba_small, x0, y0):
    out = np.zeros((H, W, 4), np.float32)
    h, w = rgba_small.shape[:2]
    hh, ww = min(h, H - y0), min(w, W - x0)
    out[y0:y0 + hh, x0:x0 + ww] = rgba_small[:hh, :ww]
    return out


# ================================================================== the Flare: an ember glass in a slim bezel
def ember_glass(cx, cy, r, charge, ready, front_mask=None):
    """premultiplied RGBA layer + additive glow. The glass: smoky dark, fire filling it from the bottom to the charge
    level (of the visible span when it sits in the bowl), a bright meniscus with tongues licking above it, a crisp gold
    bezel; READY: full, a white-hot heart, the bezel lit, flames over the top, a halo."""
    pad = int(r * (3.2 if ready else 2.2))
    x0, y0, x1, y1 = int(cx - pad), int(cy - pad - (30 if ready else 10)), int(cx + pad), int(cy + pad)
    X, Y = ss_grid(x0, y0, x1, y1)
    dx, dy = X - cx, Y - cy
    d = np.hypot(dx, dy)
    rb = r + 3.6                                   # bezel outer
    body = np.clip(r - d + 0.5, 0, 1)
    bez = np.clip(rb - d + 0.5, 0, 1) * (1 - body)
    rng = np.random.default_rng(3)
    # fbm for the fire's texture (upward streaks)
    def fbm(sx, sy, oct_=4, seed=0):
        acc, amp, tot = 0, 1.0, 0
        rr = np.random.default_rng(seed)
        for o in range(oct_):
            f = 2 ** o
            ph = rr.uniform(0, 6.28, 4)
            acc = acc + amp * (np.sin(sx * 0.21 * f + ph[0] + np.sin(sy * 0.13 * f + ph[1]) * 1.7) *
                               np.cos(sy * 0.09 * f + ph[2] + np.sin(sx * 0.17 * f + ph[3]) * 1.3))
            tot += amp; amp *= 0.55
        return acc / tot
    vis_bot = cy + r if front_mask is None else min(cy + r, rim_y + 1)
    span = vis_bot - (cy - r)
    lvl = vis_bot - charge * span if not ready else cy - r - 6
    # the fire: Krea-painted textures (gen/fw_9931_0: a wall of flame, its crown of tongues set on the level;
    # gen/fo_9932_0: an orb full of fire, for READY), on smoky dark glass by a screen blend
    def tex(n):
        return np.asarray(Image.open(os.path.join(HERE, "gen", n + ".png")).convert("RGB"), np.float32) / 255

    def samp(T_, u, v):
        return np.stack([ndimage.map_coordinates(T_[..., c], [v, u], order=1, mode="nearest") for c in range(3)], -1)
    radial = np.clip(d / r, 0, 1)
    if not ready:
        kt = 0.115
        fire = samp(tex("fw_9931_0"), (X - cx) / kt + 384 + 40, np.clip((Y - lvl) / kt + 330, 0, 767))
        fire = fire * 1.12
    else:
        fire = samp(tex("fo_9932_0"), 383.5 + (X - cx) / r * 318, 383 + (Y - cy) / r * 318)
        fire = np.clip(fire * 1.25 + 0.04, 0, 1)
        # R6: READY is the brightest state: a white-gold heart filling the middle of the glass, gold toward the rim
        # the heart breathes through the flames: modulated by the fire's own texture so it never reads as a flat disc
        ft = fire @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        heart = (np.exp(-(d / (0.46 * r)) ** 2) * (0.70 + 0.30 * np.clip(ft * 1.4, 0, 1)))[..., None]
        fire = 1 - (1 - fire) * (1 - np.array([1.0, 0.72, 0.30], np.float32) * (np.exp(-(d / (0.80 * r)) ** 2) * 0.55)[..., None])
        fire = 1 - (1 - fire) * (1 - np.array([1.0, 0.95, 0.80], np.float32) * heart * 0.95)
    fire = np.clip(fire * (0.68 + 0.32 * (1 - radial ** 4))[..., None], 0, 1)
    lv = lvl
    orange = np.array([1.00, 0.42, 0.07], np.float32)
    gold = np.array([1.00, 0.76, 0.32], np.float32)
    white = np.array([1.00, 0.95, 0.84], np.float32)
    # the smoky glass: dark warm, lit faintly by the fire below the level
    glass = np.array([0.050, 0.036, 0.030], np.float32) + np.array([0.30, 0.10, 0.02], np.float32) *         (np.exp(-np.clip(lv - Y, 0, None) / 9) * 0.35 * (charge > 0.02))[..., None]
    col = 1 - (1 - glass) * (1 - fire)
    # glass optics: an inner rim darkening, a fresnel rim, the upper-left window highlight, a small sharp glint
    col = col * (0.72 + 0.28 * np.clip(1 - radial ** 6, 0, 1))[..., None]
    fres = np.clip((radial - 0.82) / 0.18, 0, 1) ** 2
    col = col + np.array([0.95, 0.80, 0.60], np.float32) * (fres * 0.20 * np.clip(-(dx + dy) / r * 0.7 + 0.5, 0, 1))[..., None]
    hx, hy = cx - 0.42 * r, cy - 0.46 * r
    win = np.exp(-(((X - hx) / (0.30 * r)) ** 2 + ((Y - hy) / (0.17 * r)) ** 2))
    col = col * (1 - 0.35 * win[..., None]) + np.array([1.0, 0.97, 0.92], np.float32) * (win * 0.35)[..., None]
    gl = np.exp(-(((X - (hx - 0.1 * r)) / 1.6) ** 2 + ((Y - (hy - 0.02 * r)) / 1.2) ** 2))
    col = col + (gl * 0.55)[..., None]
    # the bezel: polished bronze, lit from the upper left; lit gold when ready
    t = np.clip((d - r) / (rb - r), 0, 1)
    lit = np.clip(0.55 - 0.45 * (dx + dy) / (d + 1e-3) * 0.7, 0.1, 1)
    bezc = np.array([0.36, 0.27, 0.16], np.float32) * (0.45 + 1.1 * lit)[..., None]
    bezc = bezc + np.array([0.9, 0.75, 0.5], np.float32) * (np.exp(-((t - 0.45) / 0.22) ** 2) * lit * 0.35)[..., None]
    # the charge on the bezel: lit amber clockwise from 12 o'clock (the same grammar as the XP ring on the coin)
    ang = (np.arctan2(dx, -dy) + 2 * np.pi) % (2 * np.pi) / (2 * np.pi)
    arc = np.clip((charge - ang) * 2 * np.pi * r + 0.5, 0, 1) * np.clip(4 * (charge > 0.01), 0, 1)
    amber = np.array([1.0, 0.62, 0.20], np.float32) * (0.75 + 0.35 * np.exp(-((t - 0.5) / 0.3) ** 2))[..., None]
    bezc = bezc * 0.42 * (1 - arc[..., None]) + amber * 1.1 * arc[..., None]
    if ready:
        bezc = bezc * 0.55 + np.array([1.0, 0.70, 0.30], np.float32) * 0.65
    outline = np.clip(rb + 1.0 - d + 0.5, 0, 1) * (1 - np.clip(rb - d + 0.5, 0, 1))
    rgb = col * body[..., None] + bezc * bez[..., None]
    a = np.clip(body + bez + outline * 0.85, 0, 1)
    rgb = rgb + np.array([0.03, 0.022, 0.016], np.float32) * outline[..., None]
    # additive light: the halo on the air, flames over the top when READY
    add = np.zeros(X.shape + (3,), np.float32)
    halo = np.exp(-np.clip(d - r, 0, None) / (r * (0.85 if ready else 0.22))) * (d > r)
    halo = halo * (1 - sm(0.72 * pad, 0.98 * pad, d))
    add += (np.array([1.0, 0.62, 0.22], np.float32) if ready else np.array([1.0, 0.50, 0.12], np.float32)) *         (halo * (0.95 if ready else 0.10 + 0.2 * charge))[..., None]
    if ready:
        rr = np.random.default_rng(9)
        for i, (pos, hm) in enumerate([(-0.55, 0.55), (-0.25, 0.95), (0.02, 1.35), (0.28, 0.85), (0.55, 0.5)]):
            fx0 = cx + pos * r
            base = cy - np.sqrt(max(r * r - (pos * r) ** 2, 0)) + 4
            hgt = 30 * hm
            v = np.clip((base - Y) / hgt, -0.4, 1.4)
            lean = 2.5 * np.sin(v * 2.4 + i * 1.9) * v
            wid = 6.0 * (0.7 + 0.5 * hm) * np.clip(1 - v, 0, 1) ** 0.8
            q = (X - fx0 - lean) / np.maximum(wid, 0.4)
            bodyf = np.exp(-q ** 2) * sm(-0.3, 0.05, v) * (1 - sm(0.5, 1.0, v))
            coref = np.exp(-(q / 0.45) ** 2) * sm(-0.2, 0.05, v) * (1 - sm(0.15, 0.55, v))
            colv = np.where(v[..., None] < 0.45, gold + (orange - gold) * (v[..., None] / 0.45),
                            orange + (np.array([0.8, 0.2, 0.04], np.float32) - orange) * np.clip((v[..., None] - 0.45) / 0.55, 0, 1))
            add += colv * (bodyf * 0.85)[..., None] + white * (coref * 0.6)[..., None]
        # R5: embers, not dashes: round hot specks of mixed size drifting up and out of the flames, each a white-gold
        # core in a soft orange glow, dimmer and redder as they rise; a few trail a faint short curl of their path
        er = np.random.default_rng(17)
        for k in range(11):
            up = er.uniform(0.1, 1.0)
            ex = cx + er.normal(0, 0.30) * r * (0.6 + 0.8 * up)
            ey = cy - r - 8 - up * (r * 0.95 + 14)
            sz = er.uniform(0.75, 1.45) * (1.15 - 0.40 * up)
            br = er.uniform(0.65, 1.0) * (1.05 - 0.55 * up)
            dd2 = (X - ex) ** 2 + (Y - ey) ** 2
            core = np.exp(-dd2 / (2 * (0.42 * sz) ** 2))
            glow = np.exp(-dd2 / (2 * (1.9 * sz) ** 2))
            hot = np.array([1.0, 0.86, 0.55], np.float32) * (1 - up) + np.array([1.0, 0.55, 0.18], np.float32) * up
            add += hot * (core * 1.7 * br)[..., None] + np.array([1.0, 0.35, 0.06], np.float32) * (glow * 0.42 * br)[..., None]
            if k % 3 == 0:
                # a faint curl below it: where it came from
                sw = er.choice([-1, 1]) * er.uniform(1.5, 3.0)
                for j in range(1, 9):
                    tj = j / 8
                    px_, py_ = ex - sw * np.sin(tj * 2.2), ey + tj * 7.5
                    add += hot * (np.exp(-((X - px_) ** 2 + (Y - py_) ** 2) / (2 * 0.38 ** 2)) * 0.16 * br * (1 - tj))[..., None]
    else:
        # idle: two or three small tongues inside the glass above the level are already drawn; a couple of sparks
        for k in range(2):
            ex = cx + rng.uniform(-0.4, 0.4) * r
            ey = lvl - rng.uniform(6, 14)
            e = np.exp(-(((X - ex) / 0.6) ** 2 + ((Y - ey) / 1.8) ** 2)) * (d < r - 2)
            add += gold * (e * 0.7)[..., None]
    L = np.dstack([rgb, a])
    Ls = ss_down(L); As = ss_down(add)
    Lc, Ac = to_canvas(Ls, x0, y0), np.zeros((H, W, 3), np.float32)
    hh, ww = min(As.shape[0], H - y0), min(As.shape[1], W - x0)
    Ac[y0:y0 + hh, x0:x0 + ww] = As[:hh, :ww]
    return Lc, Ac, (cx, cy, r, lvl)


# ================================================================== the middle plate
def plate():
    """A dark bronze plate: chamfered ends, an arch round the coin; a crisp bevelled edge (lit from the upper left), an
    inlaid gold line inside it, a short inlaid curl ending at each end, sockets pressed round each seat."""
    x0, x1, y0, y1 = int(PL_X0) - 48, int(PL_X1) + 49, 988, 1080
    ss = 4
    X, Y = ss_grid(x0, y0, x1, y1, ss)
    # R6 outline: a long top line; each end curls down into a volute like her curled lock tips (a disc of VOL_R at the
    # top corner, the end's side tucked in under it by INSET), an arch round the coin; signed distance from a 4x raster
    from PIL import ImageDraw as _D
    INSET = 6.5
    VL, VR_ = (PL_X0 + VOL_R, PL_TOP + VOL_R), (PL_X1 - VOL_R, PL_TOP + VOL_R)
    pts = [(PL_X0 + INSET, 1100), (PL_X0 + INSET, VL[1]), (VL[0], PL_TOP), (VR_[0], PL_TOP), (PL_X1 - INSET, VR_[1]),
           (PL_X1 - INSET, 1100)]
    mim = Image.new("L", ((x1 - x0) * ss, (y1 - y0 + 20) * ss), 0)
    dd_ = _D.Draw(mim)
    dd_.polygon([((px - x0) * ss, (py - y0) * ss) for px, py in pts], fill=255)
    for (vx, vy) in (VL, VR_):
        dd_.ellipse(((vx - VOL_R - x0) * ss, (vy - VOL_R - y0) * ss, (vx + VOL_R - x0) * ss, (vy + VOL_R - y0) * ss), fill=255)
    dd_.ellipse(((960 - ARCH_R - x0) * ss, (SEAT_Y - ARCH_R - y0) * ss, (960 + ARCH_R - x0) * ss, (SEAT_Y + ARCH_R - y0) * ss), fill=255)
    mb = np.asarray(mim)[: (y1 - y0) * ss] > 127
    # soften the arch's joins only (not the curls' undersides): close, then keep the original near the volutes
    mbc = ndimage.binary_closing(mb, structure=np.ones((3, 3)), iterations=10)
    near_v = (np.hypot(X - VL[0], Y - VL[1]) < VOL_R + 6) | (np.hypot(X - VR_[0], Y - VR_[1]) < VOL_R + 6)
    mb = np.where(near_v, mb, mbc)
    # UI 23 BOOKENDS: below each volute the plate's end side follows its figure's edge, TUCK px over it (no gap)
    if os.environ.get("BOOK", "1") == "1":
        TUCK = float(os.environ.get("TUCK", "7"))
        ga, ka = G[..., 3] > 0.5, K[..., 3] > 0.5
        rows = np.arange(y0, y1)
        ge = np.array([np.nonzero(ga[r, :960])[0].max() + 1.0 if ga[r, :960].any() else -1e3 for r in rows])
        ke = np.array([np.nonzero(ka[r, 960:])[0].min() + 960.0 if ka[r, 960:].any() else 1e4 for r in rows])
        yr = Y[:, :1]
        gel, kel = np.interp(yr, rows + 0.5, ge), np.interp(yr, rows + 0.5, ke)
        below = yr >= float(os.environ.get("BOOK_Y", str(PL_TOP + VOL_R)))
        mb = mb | ((X >= gel - TUCK) & (X <= PL_X0 + INSET + 1) & below) | ((X <= kel + TUCK) & (X >= PL_X1 - INSET - 1) & below)
        print("BOOK girl edge", [int(v) for v in ge[::8]], " keeper edge", [int(v) for v in ke[::8]], "rows", list(rows[::8]))
    sd = (ndimage.distance_transform_edt(mb) - ndimage.distance_transform_edt(~mb)) / ss
    sd = G_(sd, 1.0)
    inside = np.clip(sd * 1.0 + 0.5, 0, 1)
    # height: bevel (0..3 px rises 2.4), a flat field, the inlay groove at 7 px, the seats' sockets
    bev = 2.4 * sm(0.0, 3.2, sd)
    INL = 6.0
    # the volutes' spirals: from the inlay ring (radius VOL_R - INL) one turn inward to the eye, a raised polished coil
    spir = np.full(X.shape, 1e3, np.float32)
    for (vx, vy), sg in ((VL, 1), (VR_, -1)):
        tt = np.linspace(0, 1, 160)
        ph = -np.pi / 2 - sg * tt * 2 * np.pi * 1.15          # start at the top of the ring, curl outward-down, in
        rr_ = (VOL_R - INL) * (1 - 0.82 * tt)
        px_, py_ = vx + rr_ * np.cos(ph), vy + rr_ * np.sin(ph)
        win = (np.abs(X - vx) < VOL_R + 2) & (np.abs(Y - vy) < VOL_R + 2)
        if win.any():
            d2 = np.min((X[win][:, None] - px_[None]) ** 2 + (Y[win][:, None] - py_[None]) ** 2, 1)
            spir[win] = np.minimum(spir[win], np.sqrt(d2))
    in_v = np.minimum(np.hypot(X - VL[0], Y - VL[1]), np.hypot(X - VR_[0], Y - VR_[1])) < VOL_R - INL + 1.2
    line_d = np.where(in_v, np.minimum(np.abs(sd - INL), spir), np.abs(sd - INL))
    groove = -0.9 * np.exp(-((line_d + 1.0) / 0.9) ** 2) + 0.9 * np.exp(-(line_d / 0.7) ** 2)
    # seats/coin/flask/dash sockets: a soft dish round each
    sock = np.zeros_like(X)
    for sx in SEAT_XS:
        dd = np.hypot(X - sx, Y - SEAT_Y)
        sock -= 1.2 * np.exp(-np.clip(dd - SEAT_R, 0, None) / 2.0) * (dd > SEAT_R - 1)
    dd = np.hypot(X - 960, Y - SEAT_Y)
    sock -= 1.2 * np.exp(-np.clip(dd - MED_R, 0, None) / 2.0) * (dd > MED_R - 1)
    Hh = bev + groove + sock
    # an inlaid curl at each end: the inlay line, nearing the end, turns down into a small spiral
    gy, gx = np.gradient(Hh * 1.0, 1 / ss)
    nrm = np.dstack([-gx, -gy, np.ones_like(gx) * 1.0]); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    Ld = np.array([-0.5, -0.65, 0.58], np.float32); Ld /= np.linalg.norm(Ld)
    diff = np.clip(nrm @ Ld, 0, 1)
    hv = Ld + np.array([0, 0, 1.0], np.float32); hv /= np.linalg.norm(hv)
    spec = np.clip(nrm @ hv, 0, 1) ** 40
    # albedo: dark bronze field with a slow mottle and faint verdigris in the low places
    rng = np.random.default_rng(21)
    mot = G_(rng.normal(0, 1, X.shape).astype(np.float32), 24) * 9 + G_(rng.normal(0, 1, X.shape).astype(np.float32), 5) * 2.2
    brushed = G_(rng.normal(0, 1, X.shape).astype(np.float32), (0.6, 10)) * 3.0
    base = np.array([0.150, 0.112, 0.078], np.float32)
    verd = np.array([0.075, 0.115, 0.100], np.float32)
    vmask = np.clip(0.25 + 0.6 * mot, 0, 1) * 0.35 * (sd > 9) * (line_d > 2.5)
    alb = base * (1 + 0.10 * mot + 0.05 * brushed)[..., None]
    alb = alb * (1 - vmask[..., None]) + verd * vmask[..., None]
    # the edge band (bevel) and the inlay are polished bronze, brighter albedo
    edge = sm(3.6, 2.4, sd) * (sd > -0.5)
    inlay_line = np.exp(-(line_d / 0.75) ** 2)
    polished = np.array([0.46, 0.35, 0.22], np.float32)
    alb = alb * (1 - edge[..., None]) + polished * edge[..., None]
    lin = np.array([0.86, 0.68, 0.40], np.float32)
    col = alb * (0.28 + 0.95 * diff)[..., None] + np.array([1.0, 0.85, 0.6], np.float32) * (spec * (0.25 + 0.75 * edge))[..., None] * 0.6
    col = col * (1 - inlay_line[..., None] * 0.9) + lin * (inlay_line * (0.75 + 0.55 * diff))[..., None]
    # a fine dark outline at the plate's edge (crisp against the game)
    outline = sm(0.0, 0.9, sd) * (1 - sm(0.9, 1.6, sd))
    col = col * (1 - 0.6 * outline[..., None])
    # the drop shadow onto the game, above and round the plate
    rgba = np.dstack([col * inside[..., None], inside])
    sh = np.clip(1 - inside, 0, 1) * np.exp(-np.clip(-sd, 0, None) / 3.0) * 0.55
    rgba[..., 3] = rgba[..., 3] + sh * (1 - rgba[..., 3])
    small = ss_down(rgba, ss)
    return to_canvas(small, x0, y0)


# ================================================================== seats: today's wells at 1:1 in a slim crisp bezel
def fill_notch(P, c=35.5, r0=23.0, r1=32.5, half=21.0, src=27.0):
    """R5: today's rank tab dips into each well at 12 o'clock (a small notch at the top of the cut). Refill that wedge
    (|angle from 12| < half deg, r0..r1) along the circle from the well's own rim shading at +-src deg, feathered."""
    n = 1440
    pol = cv2.warpPolar(P, (48, n), (c, c), 48, cv2.WARP_POLAR_LINEAR)
    deg = np.arange(n) * 360.0 / n
    a = (deg - 270.0)
    ok = (np.abs(a) > src) & (np.abs(a) < src + 6)
    out = pol.copy()
    rows = np.nonzero(np.abs(a) < src)[0]
    for k in range(4):
        for ri in range(48):
            out[rows, ri, k] = np.interp(a[rows], a[ok], pol[ok, ri, k])
    back = cv2.warpPolar(out, (P.shape[1], P.shape[0]), (c, c), 48, cv2.WARP_POLAR_LINEAR | cv2.WARP_INVERSE_MAP)
    gy, gx = np.mgrid[0:P.shape[0], 0:P.shape[1]].astype(np.float32)
    dx, dy = gx - c, gy - c
    rr = np.hypot(dx, dy)
    ang = np.degrees(np.arctan2(dx, -dy))
    m = sm(half + 3, half - 3, np.abs(ang)) * sm(r0 - 1.5, r0 + 1.5, rr) * (dy < 0)
    return P * (1 - m[..., None]) + back * m[..., None]


def seat_layer():
    out = np.zeros((H, W, 4), np.float32)
    bz = np.zeros((H, W, 4), np.float32)
    ss = 4
    for i, sx in enumerate(SEAT_XS):
        # the well as rendered today (icon, cooldown, the well's own rim shading), cut at r 31.5, moved to its new seat
        ox, oy = SEATS_X[i], 1031
        cut_ = cut(hudf, disc(ox, oy, WELL_R + 0.3, 0.9))[oy - 36:oy + 36, ox - 36:ox + 36]
        cut_ = fill_notch(cut_)
        out = over(out, piece_at(cut_, sx, SEAT_Y, 1.0, 72))
        # the bezel
        bx0, by0 = int(sx - SEAT_R - 3), int(SEAT_Y - SEAT_R - 3)
        bx1, by1 = int(sx + SEAT_R + 4), int(SEAT_Y + SEAT_R + 4)
        X, Y = ss_grid(bx0, by0, bx1, by1, ss)
        dx, dy = X - sx, Y - SEAT_Y
        d = np.hypot(dx, dy)
        ring = np.clip(SEAT_R - d + 0.5, 0, 1) * np.clip(d - WELL_R + 0.5, 0, 1)
        t = np.clip((d - WELL_R) / BEZ, 0, 1)
        # a rounded bezel profile: normal tilts outward across it
        tilt = (t - 0.5) * 1.6
        nx, ny = dx / (d + 1e-3) * tilt, dy / (d + 1e-3) * tilt
        Ld = np.array([-0.5, -0.65, 0.58]); Ld /= np.linalg.norm(Ld)
        nz = np.sqrt(np.clip(1 - tilt ** 2 * 0.5, 0.1, 1))
        diff = np.clip(nx * Ld[0] + ny * Ld[1] + nz * Ld[2], 0, 1)
        spec = np.clip(diff, 0, 1) ** 24
        c = np.array([0.55, 0.42, 0.26]) * (0.30 + 1.05 * diff)[..., None] + np.array([1, 0.88, 0.64]) * (spec * 0.6)[..., None]
        inner = np.exp(-((d - WELL_R - 0.2) / 0.6) ** 2)          # a fine dark line between bezel and well
        c = c * (1 - 0.7 * inner[..., None])
        outl = np.clip(SEAT_R + 1.0 - d + 0.5, 0, 1) * (1 - np.clip(SEAT_R - d + 0.5, 0, 1))
        a = np.clip(ring + outl * 0.9, 0, 1)
        rgb = c * ring[..., None] + np.array([0.03, 0.024, 0.018]) * outl[..., None]
        bz = over(bz, to_canvas(ss_down(np.dstack([rgb, a]).astype(np.float32), ss), bx0, by0))
    return out, bz


def flask_dash():
    out = np.zeros((H, W, 4), np.float32)
    fl = load_rgba(os.path.join(DGR, "flask_full.png"))
    e, dx, dy = locate(hudf, fl, 719, 1018, 47.5, 64)
    Lf = place(fl, 719 - 23.75 + dx, 1018 - 32 + dy, 47.5, 64)
    m = np.clip(Lf[..., 3] * 1.05, 0, 1) * np.clip(719 + dx + 17.5 - xx, 0, 1)   # not today's count beside it
    Pf = cut(hudf, m)[1018 + dy - 42:1018 + dy + 42, 719 + dx - 42:719 + dx + 42]
    fy = SEAT_Y - 9
    out = over(out, piece_at(Pf, FLASK_X, fy, S))
    ring = load_rgba(os.path.join(DGR, "ring_3.png"))
    Lr = place(ring, 1279 - 32, 1028 - 32, 64, 64)
    mm = np.maximum(Lr[..., 3], disc(1279, 1028, 25.5, 1.0))
    Pd = cut(hudf, mm)[1028 - 42:1028 + 42, 1279 - 42:1279 + 42]
    out = over(out, piece_at(Pd, DASH_X, SEAT_Y - 7, 0.84))
    return out, (FLASK_X, fy), (DASH_X, SEAT_Y - 7)


def medallion():
    cx, cy, R = 960.0, SEAT_Y, MED_R
    out = np.zeros((H, W, 4), np.float32)
    d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    ang = (np.degrees(np.arctan2(xx + 0.5 - cx, -(yy + 0.5 - cy))) + 360) % 360 / 360
    well = load_rgba(os.path.join(DGR, "well_2.png"))
    out = over(out, place(well, cx - R * 0.80, cy - R * 0.80, R * 1.6, R * 1.6))
    ring = load_rgba(os.path.join(DGR, "ring_2.png"))
    out = over(out, place(ring, cx - R, cy - R, 2 * R, 2 * R))
    r0, r1 = R * 0.775, R * 0.985
    ch = np.clip(np.minimum(d - r0, r1 - d) + 0.5, 0, 1)
    groove = np.zeros((H, W, 4), np.float32)
    groove[..., :3] = np.array([0.03, 0.035, 0.045], np.float32) * ch[..., None]
    groove[..., 3] = ch * 0.92
    out = over(out, groove)
    ST = out
    out = np.zeros((H, W, 4), np.float32)
    f = XP_FRAC
    mid = (r0 + r1) / 2
    li = np.clip(np.minimum(d - (r0 + 0.8), (r1 - 0.8) - d) + 0.5, 0, 1)
    fill = li * np.clip((f - ang) * 2 * np.pi * mid + 0.5, 0, 1)
    core = np.exp(-((d - mid) / 1.9) ** 2)
    c_core = np.array([0.886, 0.831, 1.0] if NIGHT else [0.812, 0.910, 1.0], np.float32)
    c_hue = np.array([0.612, 0.494, 0.878] if NIGHT else [0.353, 0.635, 0.839], np.float32)
    col = c_hue[None, None] * (1 - core[..., None]) + c_core[None, None] * core[..., None]
    out = over(out, np.dstack([col * fill[..., None], fill]))
    out[..., :3] += c_hue[None, None] * (li * (1 - fill) * 0.22)[..., None]
    lip = np.exp(-((d - (r1 + 0.6)) / 0.9) ** 2) * np.clip((f - ang) * 2 * np.pi * r1 + 0.5, 0, 1)
    out[..., :3] += c_hue[None, None] * (lip * 0.35)[..., None]
    ta = f * 2 * np.pi
    tx, ty = cx + mid * np.sin(ta), cy - mid * np.cos(ta)
    gl = np.exp(-((xx + 0.5 - tx) ** 2 + (yy + 0.5 - ty) ** 2) / (2 * 2.6 ** 2))
    out[..., :3] += c_core[None, None] * (gl * 0.9 * (d < r1 + 3))[..., None]
    tick = np.clip(1.2 - np.abs(xx + 0.5 - cx), 0, 1) * np.clip(np.minimum(d - (r0 - 1.5), (r1 + 1.5) - d) + 0.5, 0, 1) * (yy < cy)
    out = over(out, np.dstack([np.array([0.95, 0.80, 0.52], np.float32) * tick[..., None], tick]))
    return ST, out


# ================================================================== text: rank tags, key chips, the level
def text_layer(q_at, ready, flask_at, dash_at):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    fk = ImageFont.truetype(os.path.join(FONTS, "alegreya-sans-800.woff2"), 16)
    fr = ImageFont.truetype(os.path.join(FONTS, "cinzel-700.woff2"), 15)

    def chip(cx, top, text, track=0.6, lit=False):
        tw = dr.textlength(text, font=fk) + track * (len(text) - 1)
        w = max(18, tw + 9); h = 16
        x0 = round(cx - w / 2); y0 = round(top)
        if lit:
            dr.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=3, fill=(70, 34, 8, 245), outline=(255, 190, 90, 255))
            colr = (255, 236, 196, 255)
        else:
            dr.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=3, fill=(22, 18, 14, 238), outline=(138, 108, 70, 255))
            colr = (240, 230, 208, 255)
        x = cx - tw / 2
        for ch in text:
            dr.text((x, y0 + h / 2 + 0.5), ch, font=fk, fill=colr, anchor="lm")
            x += dr.textlength(ch, font=fk) + track
        return (x0, y0, x0 + w, y0 + h)
    chip(flask_at[0], 1061, "R")
    chip(dash_at[0], 1061, "SPACE")
    qbox = chip(q_at[0], q_at[1], "Q  READY" if ready else "Q", lit=ready)
    fc = ImageFont.truetype(os.path.join(FONTS, "alegreya-sans-800.woff2"), 17)
    bx, by = flask_at[0] + 15, flask_at[1] - 19
    dr.ellipse((bx - 9, by - 9, bx + 9, by + 9), fill=(20, 16, 13, 248), outline=(166, 128, 80, 255), width=1)
    dr.text((bx + 0.5, by + 1), "2", font=fr, fill=(248, 238, 216, 255), anchor="mm")
    # rank tags at half past one on each seat, over the bezel (no height added)
    for x, rk in zip(SEAT_XS, ["1", "3", "5", "8", "3", "5"]):
        bx, by = x + 24.5, SEAT_Y - 24.5
        dr.ellipse((bx - 9, by - 9, bx + 9, by + 9), fill=(20, 16, 13, 248), outline=(166, 128, 80, 255), width=1)
        dr.text((bx + 0.5, by + 1), rk, font=fr, fill=(248, 238, 216, 255), anchor="mm")
    fl = ImageFont.truetype(os.path.join(FONTS, "cinzel-700.woff2"), 23)
    col = (232, 222, 255, 255) if NIGHT else (214, 234, 255, 255)
    dr.text((960, SEAT_Y + 1), str(LEVEL), font=fl, fill=col, anchor="mm", stroke_width=1, stroke_fill=(8, 12, 18, 255))
    a = np.asarray(im, np.float32) / 255
    return premul(a), qbox


# ================================================================== assemble
_rows, _ge, _ke = HB.figure_edges(G[988:, :, 3], K[988:, :, 3], 1, 988)
CL = HB.end_contour(_rows, _ge, _ke)
PL = np.zeros((H, W, 4), np.float32)
PL[988:1080, 576:1344] = HB.plate(1, _rows, CL)
SE_W, SE_B = seat_layer()
SE = over(SE_W, SE_B)
FD, flask_at, dash_at = flask_dash()
ME_ST, ME_LV = medallion()
ME = over(ME_ST, ME_LV)
if B:
    EG_R = BR_R
    egx, egy = BR_GLASS
    EG, EGA, eg_info = ember_glass(egx, egy, EG_R, CHARGE, READY, front_mask=True)
    q_at = (egx, 1061)
elif not ALT:
    EG_R = 37.0
    egx, egy = bcx, rim_y - 0.62 * EG_R
    EG, EGA, eg_info = ember_glass(egx, egy, EG_R, CHARGE, READY, front_mask=True)
    q_at = (bcx + 6, rim_y + 52)
else:
    # the alternative: the Flare as a socket at the plate's right end (past the dash), the keeper holds her coals
    EG_R = 33.0
    egx, egy = PL_X1 + 14 + EG_R, SEAT_Y - 4
    EG, EGA, eg_info = ember_glass(egx, egy, EG_R, CHARGE, READY, front_mask=None)
    q_at = (egx, 1061)
T, qbox = text_layer(q_at, READY, flask_at, dash_at)

kgain = GR['kgain'] if FIXED else 1.0
g_sel = gm & ~(HAIR * glint(SHINE_FRONT) > 0.05)
K_BASE = K.copy()
DA = DB = 0.0
for it in range(7):
    if it in (3, 5):
        # the a/b means as seen in the final frame (the game's light included): shift the keeper's patina onto the girl's
        labf = lab_of(np.clip(out[..., :3], 0, 1))
        if FIXED:
            DA, DB = GR['DA'], GR['DB']
        else:
            DA += labf[..., 1][g_sel].mean() - labf[..., 1][km].mean()
            DB += labf[..., 2][g_sel].mean() - labf[..., 2][km].mean()
        kl = lab_of(straight(K_BASE))
        kl[..., 1] += DA * (1 - KFIRE); kl[..., 2] += DB * (1 - KFIRE)
        krgb = cv2.cvtColor(np.clip(kl, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32) / 255
        K = np.dstack([krgb * K_BASE[..., 3:4], K_BASE[..., 3]])
    Kg = K.copy()
    Kg[..., :3] = K[..., :3] * (kgain * (1 - KFIRE) + KFIRE)[..., None]
    if it == 6 and os.environ.get('K4', '1') == '1':
        _away = (1 - np.clip(G_((KFIRE > 0.05).astype(np.float32), 3.0) * 3, 0, 1)) * sm(EG_R + 8, EG_R + 20, np.hypot(xx - egx, yy - egy))
        _ks = straight(Kg)
        if FIXED:
            K4_THR = GR['K4_thr']
        else:
            K4_THR = float(np.percentile((_ks @ lumw)[(Kg[..., 3] > 0.98) & (KFIRE < 0.05) & (_away > 0.5)], 90))
        Kg = np.dstack([HB.k4_curve(_ks, _away, K4_THR) * Kg[..., 3:4], Kg[..., 3]])
    out = canvas.copy()
    out = over(out, Kg)
    if not ALT and not (B and it < 6):          # B: the bronze's tone is measured without the glass (charge-independent)
        out = over(out, EG)
        fr_ = Kg * BOWL_FRONT[..., None] / np.maximum(Kg[..., 3:4], 1e-4)   # the bowl's front lip back over the glass
        out = over(out, fr_)
        out[..., :3] += EGA * (1 - 0.75 * BOWL_FRONT)[..., None]
    out = over(out, G)
    out = over(out, PL)
    for L in (SE, FD, ME):
        out = over(out, L)
    if ALT:
        out = over(out, EG)
        out[..., :3] += EGA
    out = over(out, T)
    Yc = np.clip(out[..., :3], 0, 1) @ lumw
    kfc = straight(K)
    km = (K[..., 3] > 0.98) & (KFIRE < 0.05) & ((EGA @ lumw) < 0.03) & (EG[..., 3] < 0.05)
    if B:
        km = (K[..., 3] > 0.98) & (np.hypot(xx - egx, yy - egy) > EG_R + 10) & (yy < 1052)
    if B and it == 6:
        break
    g90, k90 = np.percentile(Yc[g_sel], 90), np.percentile(Yc[km], 90)
    NF = 1.0                    # K3: no night dim (the same sprite day and night)
    if FIXED:
        kgain = GR['kgain']
    else:
        kgain *= (g90 * NF / k90) if not B else (g90 * BR_P90 * NF / k90)
if not NIGHT and not B and os.environ.get('DUMP_GRADE', '1') == '1':
    GRD.update(DA=float(DA), DB=float(DB), kgain=float(kgain), K4_thr=K4_THR, BOWL_C=BOWL_C, RIM_C=RIM_C, BOWL_L=BOWL_L,
               BOWL_R=BOWL_R, kx0=float(kx0), ky0=float(ky0), K_S=K_S,
               note='mock8.py day (DXG=0 GAP_R=-17 KEEPER=ks60_2304_0 KLOCK=1): the keeper grade the bake applies')
    json.dump(GRD, open(KGRADE, 'w'), indent=1)
# the shield badge on her hair
_hb = load_rgb(os.path.join(OUT, "bd21v_hud5.png"))[864:892, 590:630]
_al = np.clip(((_hb[..., 2] - _hb[..., 0]) * 255 - 8) / 30, 0, 1)
_c = _hb.reshape(-1, 3)[np.argmax((_hb[..., 2] - _hb[..., 0]).ravel())]
_badge = np.dstack([np.broadcast_to(_c, _hb.shape).copy(), _al])
out = over(out, place(_badge, DXG + 295.33 + (590 - 295.33) * S, 1080 - (1080 - 864) * S, 40 * S, 28 * S))
res = Image.fromarray((np.clip(out[..., :3], 0, 1) * 255 + 0.5).astype(np.uint8))
name = f"mock_{TAG}_{'night' if NIGHT else 'day'}"
res.save(os.path.join(HERE, name + ".png"))
res.crop((0, 760, 1920, 1080)).save(os.path.join(HERE, name + "_bottom.png"))
if READY:
    res.crop((1240, 760, 1920, 1080)).save(os.path.join(HERE, f"mock_{LAYOUT}_ready.png"))


# ---- numbers
def top_of(L, x0, x1, thr=0.2):
    rows = np.nonzero((L[:, x0:x1, 3] > thr).any(1))[0]
    return 1080 - rows.min() if len(rows) else 0


def lab_meas(sel):
    lab = lab_of(np.clip(out[..., :3], 0, 1))
    Y = np.clip(out[..., :3], 0, 1) @ lumw
    return np.percentile(Y[sel], 50), np.percentile(Y[sel], 90), lab[..., 1][sel].mean() - 128, lab[..., 2][sel].mean() - 128


mid_L = over(over(over(PL, SE), FD), ME)
mid_L[..., 3] = np.where(PL[..., 3] > 0.6, mid_L[..., 3], np.maximum(SE[..., 3], ME[..., 3]))
right_top = max(top_of(Kg, 1240, 1920), 1080 - np.nonzero(((EG[..., 3] > 0.2) | ((EGA @ lumw) > 0.08))[:, 1240:].any(1))[0].min())
print(f"heights from the bottom: left {top_of(G, 0, 640)}  middle {top_of(PL, 600, 1320, 0.6)} (plate, arch)  seats "
      f"{1080 - int(SEAT_Y - SEAT_R - 1)}  right {right_top} (keeper {top_of(Kg, 1240, 1920)})")
print(f"seat icon (well) {2 * WELL_R:.0f} px vs today's {2 * WELL_R:.0f} px at 1:1 (seat outer {2 * SEAT_R + 2:.0f} vs today's {SEAT_D})")
gp = lab_meas(g_sel); kp = lab_meas(km)
print(f"luma p50/p90  girl {gp[0]:.3f}/{gp[1]:.3f}  keeper {kp[0]:.3f}/{kp[1]:.3f};  Lab a/b mean  girl {gp[2]:.2f}/{gp[3]:.2f}  "
      f"keeper {kp[2]:.2f}/{kp[3]:.2f}  (gain {kgain:.3f})")
_gr = [int(np.nonzero((G[y0_:y0_ + 10, :, 3] > 0.2).any(0))[0].max()) for y0_ in range(960, 1080, 10)]
print("girl right edge by 10-row band from y 960:", _gr)
print("plate x", round(PL_X0, 1), round(PL_X1, 1), "keeper x0", round(kx0, 1), "left edge of keeper",
      int(np.nonzero((Kg[..., 3] > 0.2).any(0))[0].min()), "girl right edge", int(np.nonzero((G[..., 3] > 0.2).any(0))[0].max()),
      "bowl", round(bcx, 1), round(rim_y, 1), "glass", [round(v, 1) for v in eg_info], "flask", flask_at, "dash", dash_at)

# ---- R6 numbers: gaps (min distance between alpha masks), the glass core
from scipy.ndimage import distance_transform_edt as _edt
_pl = PL[..., 3] > 0.85
_dpl = _edt(~_pl)
_gm = G[..., 3] > 0.25
_rm = (Kg[..., 3] > 0.25) | (EG[..., 3] > 0.5)
_rm[:, :1100] = False
print(f"GAPS girl->plate {_dpl[_gm].min():.1f}  plate->right {_dpl[_rm].min():.1f}  plate x {PL_X0:.1f}..{PL_X1:.1f} (centre {(PL_X0 + PL_X1) / 2:.1f})")
_cx, _cy, _r, _ = eg_info
_core = np.hypot(xx - _cx, yy - _cy) < 0.35 * _r
print(f"CORE luma {Yc[_core].mean():.3f} (charge {CHARGE})  glass centre {_cx:.1f},{_cy:.1f} r {_r}")
print(f"HEIGHTS left {top_of(G, 0, 700)}  middle {top_of(PL, 600, 1320, 0.6)}  right {right_top}")
_L = lab_of(np.clip(out[..., :3], 0, 1))
print(f"TONES girl p50/p90 {np.percentile(Yc[g_sel], 50):.3f}/{np.percentile(Yc[g_sel], 90):.3f} a/b {_L[..., 1][g_sel].mean() - 128:.2f}/{_L[..., 2][g_sel].mean() - 128:.2f}"
      f"   right p50/p90 {np.percentile(Yc[km], 50):.3f}/{np.percentile(Yc[km], 90):.3f} a/b {_L[..., 1][km].mean() - 128:.2f}/{_L[..., 2][km].mean() - 128:.2f}")
