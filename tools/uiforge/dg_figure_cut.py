"""The Drowned Girl HUD, piece 1 (UI 16): cut her bronze figure for the life orb (--hud drowned).

    python tools/uiforge/dg_figure_cut.py [--check out.png]

Source: a Krea 2 turbo painting (tools/comfy/ui_assets.json "hud_dg_figure"), its BiRefNet cut beside it, in
survivorsunchained_inputs/ui16_dg_src/. The painted glass orb is fitted with a circle and cut out of the figure
(hud_orb.gdshader theme 3 draws the live orb there, under her fingers); what of her hand lies over the glass
stays as the casing in front of it. The figure is graded to mid-low value bronze (unsaturated against the blood),
scaled so the glass is ORB_D px across at 1080 (the art at 2x), and cropped from above her head to HEAD_H px
below it (the screen's foot cuts the rest). Writes godot/art/ui/lamp_life/drowned/lamp_cold.png and lamp_geo.json.

dg2 (the judge: the hand weak, the thumb over the bottom band, the bronze olive and dim): the source is seed 6305
with its hand and forearm inpainted from d1b's cradle (dg2_hand.png, Krea 2 turbo masked img2img over a guide
of d1b's hand; face and hair untouched), the palm under the glass. Her hand inside the glass's circle is KEPT in
lamp_cold (behind the glass: hud_dg_orb.gdshader draws the glass over it and shows it darkened through the
empty glass), so nothing of her covers the glass and its lowest quarter is always clear. lamp_mask.png: R her
parts over the glass (none), G her hand and forearm (held at full when the figure fades). The grade warms the
highlights (brow, nose, lips, knuckles, hair crests), deepens the verdigris and tones down the shoulder's hot spot.

dg3 (the judge: the orb against her nose and lips, the cradle hidden behind the glass, the forearm a vertical stalk):
the orb moved to d1b's spacing, its top at her lips and ~25 px of air to her chin (the source padded PADL px on the
left for it); the old orb, hand and forearm cleared and a new cradle inpainted under the glass (dg3_hand.png: Krea 2
turbo masked img2img over a sketch: palm under the glass, fingertips over the rim at 7-8 o'clock, thumb at 4-5, a
short diagonal wrist-thick forearm). Her fingertips and thumb are the front layer over the glass (mask R), only in its
outer RING px (1080); the rest of the glass's inside is the shader's (nothing of her behind it).

dg4 (the judge, round 3 notes: "the hand reads as a paddle"; the orb ~10 px higher, its top at the groove above her lip):
the orb's centre at (378, 950) on the screen (was 382, 960; her head unmoved), 26 px of air to her chin; a new cradle
inpainted (dg4_hand.png, ui17 p1: three fingertips fanned apart up the glass's lower left, each over the rim no more
than the RING, a thumb pad at 4-5 o'clock, the palm under the glass). Her hand and forearm lifted HAND_LIFT brighter
and the orb's red laid on the faces next to its lower half (RED_BOUNCE).

ui17 A3 (the judge: "regroup the hair into 4-6 locks"; "the bronze ... leans toward shiny AI gold"): the source is
dg6_hair.png, dg5_hand.png with its hair repainted as large locks (Krea 2 turbo + darkbrush 0.8, masked, denoise 0.70,
seed 9300, over a guide that is dg5_hand regrouped by value into LOCKS by lock_pass; its alpha dg5_hand's: scripts and
prompt in survivorsunchained_inputs/ui17_dg_src/patches/README.txt). The bronze pass now keeps dg5's verdigris, darkens
the broad light (BZ), adds verdigris in the deep hollows (more in the hair's grooves) and only tight old-brass ridges.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = r"C:\Users\munch\Desktop\survivorsunchained_inputs\ui16_dg_src"
SEED = 6305
NAME = "dg5_hand"          # the inpainted source (and NAME_cut.png, its alpha); ui17 A: dg5 = fuller fingers, round pads; A3 tried dg6_hair (the hair as locks): the owner rejected it ("the hair that remains looks bad": clumps, loops lost), UI 18 restored dg5 hair (ui17_dg_src/patches/README.txt)
PADL = 128                 # the source's left padding (dg3: the orb further left)
GLASS = (238.64, 336.6, 139.8)  # dg4's glass (placed by the guide, screen (378, 950)): centre, radius
RING = 12.0                # her fingertips and thumb may lie over the glass's outer RING px (1080), no further in
OUT = os.path.join(WT, "godot", "art", "ui", "lamp_life", "drowned")

ORB_D = 120.0       # the glass across at 1080
HEAD_H = 252.0      # her head's top to the screen's foot at 1080 (ui17 A: 262 -> 252, the owner's "a little tighter": she and the orb sink 10 px)
PAD = 6             # clear round her in the quad, 1080 px
RIGHT_X = 770.0     # the quad's right edge on the screen (the hair runs on under the draught's glass)
BAR_LINE = 930.0    # the bar's top line: above it, she fades when something is behind her
CHAIN_Y = 1047.0    # the chain's row (the ring orb's eye)
GRADE = dict(value=0.80, sat=0.86, gamma=1.06)
SHOULDER = (530.0 + PADL, 560.0, 70.0)   # the hot spot on her shoulder (source px): toned down
HAND_LIFT = 0.06    # her hand and forearm a touch brighter than the rest of her bronze (ui17 A: 0.22 read yellow)
RED_BOUNCE = (0.0, 0.0, 0.0)   # (ui17 A: the orb's red on her is live now, hud_dg_orb.gdshader, scaled to her life)
STRAND_GAIN = 1.0   # ui17 A: the hair's joined highlights (strand_pass); UI 18: back on with dg5's hair
HAND_MATCH = 1.0    # ui17 A (the judge: "yellower than her body"): her hand's hue matched to her neck and shoulder


# ui17 A (the judge's polish list, "Bronze: tight highlights on the raised edges ... green patina only in the hollows;
# no blotches on shoulder or cheek"): the bronze pass, run on her figure here and on the river (dg_river_cut.py)
CHEEK = (545.0, 238.0, 38.0, 44.0)      # source px (dg4_hand.png, already padded) (x, y, rx, ry): smoothed (the blotches), never her features
SHOULDER_E = (650.0, 590.0, 110.0, 70.0)


def bronze_pass(g, a, smooth_mask=None, scale=1.0, ridge_k=None, round_mask=None, verd_k=None):
    """g: graded RGB (0..1), a: alpha; scale: source px per the figure's source px (the river's are coarser).
    The verdigris kept only in the hollows (where the bronze is darker than round it), bronzed elsewhere at its own
    value; the raised edges' highlights tightened (a narrow warm lift where the bronze is lighter than round it);
    the blotches smoothed where smooth_mask says (edge-keeping)."""
    import cv2
    g = g.astype(np.float32)
    if smooth_mask is not None:
        sm = cv2.bilateralFilter(g, 9, 0.07, 5.0 * scale)
        sm = cv2.bilateralFilter(sm, 9, 0.05, 5.0 * scale)
        g = g + (sm - g) * smooth_mask[..., None]
    if round_mask is not None:
        # (a round form, the shoulder: its patchy hot spots blurred into one smooth fall of light)
        pa = np.dstack([g * a[..., None], a])
        bl = cv2.GaussianBlur(pa, (0, 0), 6.0 * scale)
        bl = bl[..., :3] / np.maximum(bl[..., 3:], 1e-3)
        g = g + (np.clip(bl, 0, 1) - g) * (round_mask * (a > 0.5))[..., None]
    # ui17 A3 (the judge: "darker base, continuous verdigris in the hollows, highlights tight on the ridges only"; the
    # round-2 pass had bronzed the verdigris away and the bust read as shiny gold): back to dg5's verdigris and value
    L = 0.3 * g[..., 0] + 0.59 * g[..., 1] + 0.11 * g[..., 2]
    on = (a > 0.5).astype(np.float32)
    # (1) a darker base: the broad light (blurred) pulled down, its brights the most; the carving's detail kept
    Lb = cv2.GaussianBlur(L, (0, 0), 6.0 * scale)
    base = Lb * BZ["base"] - np.clip(Lb - BZ["knee"], 0, None) * BZ["comp"]
    Ln = np.clip(base + (L - Lb), 0, 1)
    g = g * (Ln / np.maximum(L, 1e-3))[..., None]
    # (2) the bronze's body a dark old brown, less yellow (the round-2 gold): its hue pulled toward BODY at its own value
    L = 0.3 * g[..., 0] + 0.59 * g[..., 1] + 0.11 * g[..., 2]
    body = L[..., None] * np.array(BZ["body"], np.float32)
    g = g + (body - g) * BZ["body_k"]
    # (3) the verdigris, continuous in the hollows: where the bronze is darker than round it (two scales, smoothed so it
    # runs as a line, never a speckle), and the source's own green kept off the raised parts, its blotches blurred
    cav = np.clip((cv2.GaussianBlur(L, (0, 0), 7.0 * scale) - L) / 0.05, 0, 1)
    cav = np.maximum(cav, np.clip((cv2.GaussianBlur(L, (0, 0), 3.0 * scale) - L) / 0.04, 0, 1) * 0.5)
    cav = cv2.GaussianBlur(cav, (0, 0), 1.3 * scale)
    gr = np.clip((g[..., 1] - g[..., 0]) * 6.0 + 0.25, 0, 1)
    gr = cv2.GaussianBlur(gr, (0, 0), 2.5 * scale)
    Ls = cv2.GaussianBlur(L, (0, 0), 1.2 * scale)
    ridge = np.clip((Ls - cv2.GaussianBlur(L, (0, 0), 3.5 * scale)) / 0.06 - 0.25, 0, 1)
    vk = BZ["verd_cav"] if verd_k is None else verd_k
    vw = np.clip(np.maximum(np.clip((cav - BZ["cav_t"]) / 0.4, 0, 1) * vk, gr * BZ["verd_src"]) * (1 - ridge), 0, 1) * on
    Lv = np.maximum(L, BZ["verd_floor"])
    verd = Lv[..., None] * np.array(BZ["verd"], np.float32)
    g = g + (verd - g) * vw[..., None]
    # (4) tight highlights on the raised edges only, old brass (not new gold)
    lit = np.clip((Ls - 0.22) / 0.22, 0, 1)
    rk = 1.0 if ridge_k is None else ridge_k
    g = g + np.array(BZ["ridge"], np.float32) * (ridge * lit * on * rk)[..., None]
    return np.clip(g, 0, 1)


# ui17 A3: the bronze pass's numbers (the figure, the river and the seats' rings all take them: one material)
BZ = dict(base=0.92, knee=0.28, comp=0.50, body=(1.32, 0.97, 0.60), body_k=0.15,
          cav_t=0.45, verd_cav=0.30, verd_src=0.0, verd_floor=0.11, verd=(0.66, 1.16, 1.00), ridge=(0.13, 0.10, 0.06))


def strand_pass(g, a, mask, scale=1.0, gain=1.0):
    """ui17 A (the judge: "hair: ... highlights run unbroken from her crown into the river"): the hair's highlights
    carried along its own strands. The strands' direction from the bronze's structure tensor; each highlight (the
    bronze lighter than round it) averaged along that direction ~16 px each way (line integral convolution), so the
    painted dashes join into running lines; the gain is laid back as a warm lift where mask says."""
    import cv2
    L = (0.3 * g[..., 0] + 0.59 * g[..., 1] + 0.11 * g[..., 2]).astype(np.float32)
    hp = np.clip(L - cv2.GaussianBlur(L, (0, 0), 2.5 * scale), 0, None) * (a > 0.5)
    Ls = cv2.GaussianBlur(L, (0, 0), 1.5 * scale)
    ix, iy = cv2.Sobel(Ls, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(Ls, cv2.CV_32F, 0, 1, ksize=3)
    sg = 5.0 * scale
    j11, j22, j12 = (cv2.GaussianBlur(v, (0, 0), sg) for v in (ix * ix, iy * iy, ix * iy))
    phi = 0.5 * np.arctan2(2 * j12, j11 - j22)          # across the strands
    vx, vy = -np.sin(phi).astype(np.float32), np.cos(phi).astype(np.float32)   # along them
    H, W = L.shape
    gy, gx = np.mgrid[:H, :W].astype(np.float32)
    acc, wsum = hp.copy(), np.ones_like(hp)
    step = 1.4 * scale
    for sgn in (1.0, -1.0):
        px, py = gx.copy(), gy.copy()
        dx, dy = vx * sgn, vy * sgn
        for k in range(12):
            nx = cv2.remap(vx, px, py, cv2.INTER_LINEAR)
            ny = cv2.remap(vy, px, py, cv2.INTER_LINEAR)
            flip = np.sign(nx * dx + ny * dy + 1e-6)
            dx, dy = nx * flip, ny * flip
            px, py = px + dx * step, py + dy * step
            wk = 1.0 - k / 12.0
            acc += cv2.remap(hp, px, py, cv2.INTER_LINEAR) * wk
            wsum += wk
    lic = acc / wsum
    add = np.clip(lic * 2.4 - hp, 0, None) * mask * (a > 0.5)
    return np.clip(g + np.array([1.0, 0.78, 0.45], np.float32) * (add * gain)[..., None], 0, 1)


# ui17 A3 (the judge: "regroup the hair into 4-6 locks; the thin ribbons read busy"): four locks' centre lines (source
# px), crown to the river, used by lock_pass
LOCKS = [
    [(690, 50), (780, 95), (815, 180), (828, 300), (845, 400), (895, 485), (1000, 532), (1160, 556)],
    [(640, 45), (720, 120), (762, 230), (778, 340), (805, 440), (865, 515), (985, 562), (1160, 588)],
    [(605, 78), (665, 172), (705, 282), (727, 382), (762, 470), (832, 540), (955, 597), (1100, 650)],
    [(588, 160), (625, 255), (660, 352), (690, 442), (742, 522), (822, 592), (905, 650)],
]
LOCK_GAIN = 0.0     # (the procedural regroup: off, the hair is repainted, NAME)
HAIR_LIFT = 0.0     # (A3's lift/gamma/extra verdigris were for the repainted locks; UI 18: off with dg5's hair)
HAIR_GAMMA = 0.0
HAIR_VERD = 0.30    # = BZ["verd_cav"]: her hair takes the body's verdigris
LOCK = dict(flatten=0.6, edge=0.65, groove=0.85, crest=(0.20, 0.15, 0.09))


def lock_field(shape, alpha, locks, oxy=(0.0, 0.0), k=1.0):
    """Each pixel's place across its lock: s in -1 (the upper groove) .. 0 (the centre line) .. +1 (the lower groove), a
    Voronoi of the locks' centre lines (points scaled by k and shifted by oxy into this image)."""
    from scipy.spatial import cKDTree
    H, W = shape
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    P = np.c_[xx.ravel(), yy.ravel()]
    D, S = [], []
    for L in locks:
        p = np.array(L, np.float32) * k + np.array(oxy, np.float32)
        pts = [p[0]]
        for a0, b0 in zip(p[:-1], p[1:]):
            n = int(np.hypot(*(b0 - a0)) / 1.5) + 1
            pts += [a0 + (b0 - a0) * t for t in np.linspace(0, 1, n)[1:]]
        p = np.array(pts)
        d, i = cKDTree(p).query(P)
        i2, i1 = np.clip(i + 1, 0, len(p) - 1), np.clip(i - 1, 0, len(p) - 1)
        tx, ty = p[i2, 0] - p[i1, 0], p[i2, 1] - p[i1, 1]
        cr = tx * (P[:, 1] - p[i, 1]) - ty * (P[:, 0] - p[i, 0])
        D.append(d.reshape(H, W).astype(np.float32)); S.append(np.sign(cr).reshape(H, W).astype(np.float32))
    D, S = np.stack(D), np.stack(S)
    o = np.argsort(D, axis=0)
    d1 = np.take_along_axis(D, o[:1], 0)[0]
    d2 = np.take_along_axis(D, o[1:2], 0)[0]
    side = np.take_along_axis(S, o[:1], 0)[0]
    dout = ndimage.distance_transform_edt(alpha > 0.5).astype(np.float32)
    d2 = np.minimum(d2, d1 + 2 * dout)
    return 2 * d1 / np.maximum(d1 + d2, 1e-3) * side


def lock_pass(g, a, mask, s, scale=1.0):
    """The hair regrouped by value: inside each lock the thin ribbons' contrast flattened, the lock rounded (darker to
    its edges), dark verdigris grooves between the locks, one warm highlight running along each lock's upper crest."""
    import cv2
    m = mask[..., None]
    lp = cv2.GaussianBlur(g, (0, 0), 3.0 * scale)
    g1 = lp + (g - lp) * (1 - LOCK["flatten"])
    cyl = np.sqrt(np.clip(1 - s * s, 0, 1))
    shade = 1 - LOCK["edge"] * (1 - cyl ** 1.3)
    groove = np.clip((np.abs(s) - 0.80) / 0.20, 0, 1)
    L = 0.3 * g1[..., 0] + 0.59 * g1[..., 1] + 0.11 * g1[..., 2]
    Lf = cv2.GaussianBlur(L, (0, 0), 20.0 * scale)
    g1 = g1 * shade[..., None]
    verd = np.maximum(L * 0.7, 0.06)[..., None] * np.array([0.66, 1.16, 1.00], np.float32)
    g1 = g1 + (verd - g1) * (groove * LOCK["groove"])[..., None]
    crest = np.exp(-((s + 0.36) / 0.13) ** 2) * np.clip((Lf - 0.10) / 0.25, 0.15, 1)
    g1 = g1 + np.array(LOCK["crest"], np.float32) * crest[..., None]
    return np.clip(g * (1 - m) + g1 * m, 0, 1)


def fit_circle(alpha, box):
    """The glass's edge against the black: on each row of its upper part (above her fingers) the run that starts
    at its left edge ends at its right (where it meets her lips, the run's end is her lips: those rows are the
    outliers dropped); a least-squares circle through both ends."""
    x0, y0, x1, y1 = box
    pts = []
    for y in range(y0, y0 + int(0.55 * (y1 - y0))):
        row = alpha[y, max(x0 - 20, 0):] > 0.5
        on = np.nonzero(row)[0]
        if not len(on):
            continue
        a = on[0]
        off = np.nonzero(~row[a:])[0]
        if not len(off):
            continue
        pts += [(a + max(x0 - 20, 0), y), (a + off[0] + max(x0 - 20, 0), y)]
    P = np.array(pts, float)
    for _ in range(3):
        A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]
        cx, cy, c = np.linalg.lstsq(A, P[:, 0] ** 2 + P[:, 1] ** 2, rcond=None)[0]
        r = np.sqrt(c + cx * cx + cy * cy)
        res = np.abs(np.hypot(P[:, 0] - cx, P[:, 1] - cy) - r)
        P = P[res < max(1.5, 2.5 * np.median(res))]
    return cx, cy, float(r), len(P)


def main():
    check = sys.argv[sys.argv.index("--check") + 1] if "--check" in sys.argv else None
    rgb = np.asarray(Image.open(os.path.join(SRC, f"{NAME}.png")).convert("RGB"), np.float32) / 255
    alpha = np.asarray(Image.open(os.path.join(SRC, f"{NAME}_cut.png")).convert("RGBA"), np.float32)[..., 3] / 255
    H, W = alpha.shape
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    cx, cy, r = GLASS
    print(f"glass: centre ({cx:.1f}, {cy:.1f}) r {r:.1f}")
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.hypot(xx - cx, yy - cy)
    inside = d < r + 1.5
    # her bronze (even lit red by the glass, under ~2.4 red over green; never the smoked glass's violet)
    bronze = (R / (G + 0.03) < 2.4) & (B < 0.92 * G) & (alpha > 0.5) & (np.maximum(R, G) > 0.06)
    glint = (np.min(rgb, axis=2) > 0.55)
    # her fingertips and thumb over the glass: the bronze inside its outer RING joined to her hand outside it (the
    # painted orb's own glints and reflections float free); deeper in, nothing of her
    s0 = ORB_D / (2 * r)
    ring_px = RING / s0
    # (only where the fingertips and thumb are: 7-8 o'clock and 4-5; under the glass's foot her palm is behind it)
    th = np.degrees(np.arctan2(yy - cy, xx - cx))
    sector = ((th > 18) & (th < 64)) | ((th > 116) | (th < -170))   # (dg4: the fingertips reach 9 o'clock)
    # (dg4: a fingertip's dark nail and shadowed tip count too, or the tips come out square)
    dark = (np.max(rgb, axis=2) < 0.10) & (alpha > 0.5)
    cand = ndimage.binary_opening(inside & (bronze | dark) & ~glint & (d > r - ring_px - 2) & sector, iterations=1)
    lab, n = ndimage.label(cand | (bronze & ~inside & (d < r + 60)))
    ring = (d > r + 2) & (d < r + 8) & (yy > cy) & bronze
    keep = set(np.unique(lab[ring])) - {0}
    hand_in = inside & np.isin(lab, list(keep)) & cand
    hand_in = ndimage.binary_fill_holes(ndimage.binary_closing(hand_in, iterations=2)) & inside & (d > r - ring_px - 2)
    hs = ndimage.gaussian_filter(hand_in.astype(np.float32), 0.9)
    front = np.clip(hs * 1.6 - 0.3, 0, 1) * (d < r + 1.5) * np.clip((d - (r - ring_px - 2)) / 2.0, 0, 1)
    front *= ndimage.gaussian_filter(sector.astype(np.float32), 2.0)
    glass = np.clip((r + 1.5 - d) / 1.5, 0, 1)
    hole = glass * (1 - front)
    # (the painted blood's glow spilt past the glass onto the black: not her)
    spill = (~inside) & (R > 1.8 * G) & (R > 1.5 * B) & ~bronze
    a = alpha * (1 - hole) * (1 - ndimage.gaussian_filter(spill.astype(np.float32), 1.0))
    # (dg4: the painted glass's own rim a few px outside the fitted circle, a pale double rim: only her bronze stays)
    ghost = (d >= r + 1.0) & (d < r + 12) & ~bronze
    a = a * (1 - np.clip(ndimage.gaussian_filter(ghost.astype(np.float32), 0.8) * 1.5, 0, 1))
    # her hand and forearm (held at full in the fade): left of her neck and chest, below the glass's middle
    bnd = np.interp(yy, [0, 520, 600, 660, 768], [300, 292, 268, 255, 250]) + PADL
    held = ndimage.gaussian_filter(((xx < bnd) & (yy > cy - 0.2 * r) & (a > 0.05)).astype(np.float32), 2.0)
    held = np.maximum(held, front)
    # grade: warm bronze, the blood still reads first
    lum = (0.3 * R + 0.59 * G + 0.11 * B)[..., None]
    g = lum + (rgb - lum) * GRADE["sat"]
    g = np.clip(g, 0, 1) ** GRADE["gamma"] * GRADE["value"]
    gl = (0.3 * g[..., 0] + 0.59 * g[..., 1] + 0.11 * g[..., 2])[..., None]
    # (the highlights warmed toward old gold: brow, nose, lips, knuckles, the hair's crests)
    hi = np.clip((gl - 0.30) / 0.35, 0, 1)
    g = g * (1 + hi * np.array([0.16, 0.04, -0.14]))
    # (the verdigris deepened: where green leads red, darker and a richer blue-green)
    green = np.clip((G - R) * 6.0 + 0.2, 0, 1)[..., None] * (1 - hi)
    g = g * (1 - green) + g * np.array([0.62, 0.86, 0.84]) * green
    # (the shoulder's hot spot toned down)
    sx, sy, sr = SHOULDER
    sm = np.exp(-((xx - sx) ** 2 + (yy - sy) ** 2) / (2 * sr * sr))[..., None]
    gl = (0.3 * g[..., 0] + 0.59 * g[..., 1] + 0.11 * g[..., 2])[..., None]
    over = np.clip(gl - 0.42, 0, None)
    g = g - sm * over * 0.55 * (g / np.maximum(gl, 1e-3))
    # (dg4: her hand brighter, and the blood's light on its faces next to the glass: palm edge, fingers, thumb)
    hm = held[..., None]
    g = g * (1 + HAND_LIFT * hm)
    near = np.clip(1 - (d - r) / 42.0, 0, 1) * np.clip((yy - (cy + 0.15 * r)) / (0.25 * r), 0, 1)
    gl = (0.3 * g[..., 0] + 0.59 * g[..., 1] + 0.11 * g[..., 2])[..., None]
    g = g + (near ** 1.4 * held)[..., None] * np.array(RED_BOUNCE) * np.clip(gl * 2.5, 0.35, 1.0)
    g = np.clip(g, 0, 1)
    # (ui17 A) her hand's hue matched to her body's: each channel scaled so the lit hand's mean colour has her neck
    # and shoulder's ratios at its own brightness
    gl = 0.3 * g[..., 0] + 0.59 * g[..., 1] + 0.11 * g[..., 2]
    lit = (a > 0.9) & (gl > 0.15)
    hk, bk = lit & (held > 0.8), lit & (held < 0.05) & (xx > bnd + 40)
    hm_, bm_ = g[hk].mean(0), g[bk].mean(0)
    k = (bm_ / bm_.mean()) / (hm_ / hm_.mean())
    print(f"hand match: hand {hm_.round(3)} body {bm_.round(3)} gain {k.round(3)}")
    g = np.clip(g * (1 + (k - 1) * HAND_MATCH * held[..., None]), 0, 1)
    # (ui17 A) the bronze pass: patina to the hollows, tight highlights, the cheek's and shoulder's blotches smoothed
    def ell(e):
        return np.clip(1.6 - 1.6 * np.sqrt(((xx - e[0]) / e[2]) ** 2 + ((yy - e[1]) / e[3]) ** 2), 0, 1)
    # (her face passed: the pass at half there, its value kept)
    face = ell((520.0, 190.0, 95.0, 150.0))
    # (ui17 A3) the hair regrouped into LOCKS (before the bronze pass, so its grooves take the verdigris)
    skin_l = np.clip(np.maximum.reduce([ell((515.0, 200.0, 112.0, 178.0)), ell((555.0, 420.0, 105.0, 135.0)), ell((650.0, 600.0, 135.0, 95.0))]) * 1.6, 0, 1)
    hair_l = (alpha > 0.5) * (1 - skin_l) * (1 - held) * (xx > 430) * (1 - ((xx < 610) & (yy > 440)))
    hair_l = ndimage.gaussian_filter(ndimage.binary_erosion(hair_l > 0.5, iterations=2).astype(np.float32), 3.0)
    if LOCK_GAIN > 0:
        g = g + (lock_pass(g, a, hair_l, lock_field(a.shape, alpha, LOCKS)) - g) * LOCK_GAIN
    g0 = g
    # (ui17 A3: the repainted locks a touch lighter, and more verdigris in their grooves than on her skin)
    g = np.clip(g, 0, 1) ** (1 - HAIR_GAMMA * hair_l)[..., None] * (1 + HAIR_LIFT * hair_l)[..., None]
    g = bronze_pass(g, a, ell(CHEEK) * 0.85, ridge_k=1 - 0.5 * face, round_mask=ell(SHOULDER_E) * 0.8,
                    verd_k=BZ["verd_cav"] + (HAIR_VERD - BZ["verd_cav"]) * hair_l)
    g = g0 + (g - g0) * (1 - 0.5 * face)[..., None]
    # (ui17 A) the hair's highlights joined along its strands: her hair only (not her face, neck, shoulder or hand)
    skin = np.clip(np.maximum.reduce([ell((520.0, 200.0, 110.0, 175.0)), ell((560.0, 420.0, 120.0, 140.0)), ell(SHOULDER_E) * 1.3]) * 1.5, 0, 1)
    hair = (1 - skin) * (1 - held) * (xx > 430)
    g = strand_pass(g, a, hair, gain=STRAND_GAIN)

    # the scale: the glass ORB_D across at 1080, the art at 2x
    s = ORB_D / (2 * r)             # source px -> 1080 px
    rows = np.nonzero(alpha.max(axis=1) > 0.5)[0]
    head_top = rows[0]
    cols = np.nonzero(alpha.max(axis=0) > 0.5)[0]
    left = cols[0]
    x0 = left - PAD / s
    y0 = head_top - PAD / s
    y1 = head_top + HEAD_H / s
    x1 = W
    cw, ch = (x1 - x0) * s, (y1 - y0) * s
    cw2, ch2 = int(np.floor(cw * 2)), int(np.floor(ch * 2))   # (floor: the box never past the source)
    rgba = np.dstack([g, a]).astype(np.float32)
    # premultiply for the resample, then back
    pm = np.dstack([rgba[..., :3] * rgba[..., 3:], rgba[..., 3:]])
    im = Image.fromarray((np.clip(pm, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    box = (x0, y0, x0 + cw2 / (2 * s), y0 + ch2 / (2 * s))
    im = im.transform((cw2, ch2), Image.EXTENT, box, Image.BICUBIC) if False else \
        im.resize((cw2, ch2), Image.LANCZOS, box=box)
    o = np.asarray(im, np.float32) / 255
    oa = o[..., 3:]
    orgb = np.where(oa > 1e-3, o[..., :3] / np.maximum(oa, 1e-3), 0)
    # the right edge: the hair runs on under the bar; feather its last 24 px (1080) so it ends soft until piece 2
    fe = np.clip((cw2 - np.arange(cw2)) / 48.0, 0, 1)[None, :, None]
    oa = oa * fe
    out = Image.fromarray((np.clip(np.dstack([orgb, oa]), 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, "lamp_cold.png"))
    mk = Image.fromarray((np.dstack([front, held, np.zeros_like(held)]) * 255 + 0.5).astype(np.uint8), "RGB")
    mk = mk.resize((cw2, ch2), Image.LANCZOS, box=box)
    mk.save(os.path.join(OUT, "lamp_mask.png"))

    def at(x, y):
        return [round((x - x0) * s, 2), round((y - y0) * s, 2)]
    oc = at(cx, cy)
    canvas = [round(cw, 2), round(ch, 2)]
    at_scr = [round(RIGHT_X - cw, 2), round(1080 - ch, 2)]
    geo = {
        "shape": "drowned", "seed": SEED, "canvas": canvas, "at": at_scr,
        "orb_c": oc, "orb_r": round(r * s, 2), "orb_vis": round(r * s - 0.6, 2),
        "level_foot": -1,
        "font_mid": oc, "number_y": oc[1],
        "eye": [round(cw - 2, 2), round(CHAIN_Y - at_scr[1], 2)],
        "foot": canvas[1], "top": 0, "floor": 1080, "top_line": at_scr[1],
        "fade_at": [0, 0], "fade_size": [canvas[0], round(BAR_LINE - at_scr[1], 2)],
        "flame_full": 0, "glass_px": round(2 * r * s, 1),
        "oil_top": round(oc[1] - r * s, 2), "oil_bot": round(oc[1] + r * s, 2),
        "font_x": [round(oc[0] - r * s, 2), round(oc[0] + r * s, 2)], "skip": [0, 0],
    }
    json.dump(geo, open(os.path.join(OUT, "lamp_geo.json"), "w"), indent=1)
    print(json.dumps(geo))
    if check:
        bg = Image.new("RGBA", out.size, (60, 58, 70, 255))
        bg.alpha_composite(out)
        bg.save(check)


if __name__ == "__main__":
    main()
