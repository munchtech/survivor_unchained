"""Storybook 5, fix round 3 (solver AC: p3, p3d, p4, p5, p6, p7, p7u after the judge's r2): patched copies beside the
built layers, CPU only (drawn carved marks, clones, posts).

    python tools/storybook/ink_sb5_r3.py apply [p7 p6 p5 p4 p3 p3d]   # writes <layer>_r3.png beside the built layers
    python tools/storybook/ink_sb5_r3.py look <name>                   # comparison crops into the scratch folder

sb_wire_ink.py swaps the _r3 files in (SB5_R3 there, ahead of SB5_AB). Sources (never touched): the _sb5 patches of
ink_sb5_ab.py / ink_sb5_c.py / ink_sb5_p.py and the built layers in out/ink_layers/<plate>/.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_post as IP  # noqa: E402

LY = os.path.join(HERE, "out", "ink_layers")
LUMW = np.array([0.2126, 0.7152, 0.0722], np.float32)
LOOK = os.environ.get("R3_LOOK", os.path.join(HERE, "out", "sb5", "r3"))


def rgba(plate, f):
    return np.asarray(Image.open(os.path.join(LY, plate, f)).convert("RGBA")).astype(np.float32) / 255


def save(a, plate, f):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(LY, plate, f))
    print("wrote", plate, f)


def lens(d, cx, cy, ang, ln, wd, col, S=1.0, bend=0.0):
    """A carved gouge: lens-shaped (tapered both ends), optionally bent (bend = sideways offset at the middle, px)."""
    t = np.deg2rad(ang)
    ux, uy, px, py = np.cos(t), np.sin(t), -np.sin(t), np.cos(t)
    top, bot = [], []
    for i in range(13):
        s_ = -1 + i / 6
        w_ = wd * (1 - s_ * s_) ** 0.7
        b_ = bend * (1 - s_ * s_)
        x, y = cx + ux * s_ * ln / 2 + px * b_, cy + uy * s_ * ln / 2 + py * b_
        top.append(((x + px * w_) * S, (y + py * w_) * S))
        bot.append(((x - px * w_) * S, (y - py * w_) * S))
    d.polygon(top + bot[::-1], fill=col)


def posted_marks(draw_fn, shape, offset, light="warm", S=3, post=True):
    """Marks drawn at S x by draw_fn(ImageDraw, S) on a clear canvas of shape (h, w): -> (rgb posted, alpha).
    post=False keeps the drawn colors (the inks would snap them) and only lays the shared paper grain on them."""
    h, w = shape
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(im), S)
    st = np.asarray(im.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255
    al = st[..., 3]
    rgb = np.where(al[..., None] > 0, st[..., :3] / np.maximum(al[..., None], 1e-3), 0)
    if not post:
        fib_t, blo_t = IP.paper()
        fib = IP._sample(fib_t, offset[0], offset[1], h, w)
        blo = IP._sample(blo_t, offset[0], offset[1], h, w)
        g = 1 + IP.GRAIN * np.clip(fib, -3, 3) + IP.BLOTCH * np.clip(blo, -3, 3)
        return np.clip(rgb * g[..., None], 0, 1), al
    return IP.post(rgb, offset=offset, light=light), al


def over(dst, rgb, al):
    dst[..., :3] = dst[..., :3] * (1 - al[..., None]) + rgb * al[..., None]


# ---------------------------------------------------------------- p7 (82.2): the wet-stones patch's right edge
P7_BOX = (880, 2150, 1340, 2640)          # ink_sb5_ab "wedge" (water layer px; 0.9 frame px a layer px at 82.2)


def p7():
    w0 = rgba("p7", "water.png")
    w1 = rgba("p7", "water_sb5.png")
    x0, y0, x1, y1 = P7_BOX
    H, W = w1.shape[:2]
    out = w1.copy()
    sub = out[y0:y1, x0:x1, :3]
    # quieter stones: the highlights down ~15% and the pebble detail softened toward the cloak's and water's weight
    lum = sub @ LUMW
    soft = nd.gaussian_filter(sub, (1.3, 1.3, 0))
    sub = sub * 0.45 + soft * 0.55
    hi = np.clip((lum - 0.25) / 0.35, 0, 1)[..., None]
    sub = sub * (1 - 0.15 * hi)
    out[y0:y1, x0:x1, :3] = sub
    # the irregular waterline: right of edge(y) the river comes back (the built water there is the dark carved river)
    rng = np.random.default_rng(822)
    ys = np.arange(H)
    edge = (1300 + 14 * np.sin(ys / 37.0 + 0.8) + 9 * np.sin(ys / 13.0 + 2.1) + 6 * np.sin(ys / 5.3)
            - 0.10 * np.clip(ys - 2400, 0, None))
    X = np.arange(W)[None, :]
    k = np.clip((X - edge[:, None]) / 7.0 + 0.5, 0, 1)
    k[:y0] = 0
    k[:, x1:] = 1
    k[:y0] = 0
    k = k[..., None]
    out[..., :3] = out[..., :3] * (1 - k) + w0[..., :3] * k
    # the wet black lip where the stones go under (a broken keyline just inside the waterline)
    lip = np.exp(-((X - edge[:, None] + 9) / 6.0) ** 2) * (0.75 + 0.25 * np.sin(np.arange(H) / 6.1))[:, None]
    lip[:y0 + 60] = 0
    out[..., :3] *= (1 - 0.55 * lip)[..., None]
    # carved ripple strokes: broken arcs along the waterline, curving round under the flask (~1390, 2405)
    bx0, by0, bx1, by1 = 1180, 2300, 1560, 2640
    pale = (80, 103, 146, 255)       # the river's own pale cuts are ~(66, 86, 126)
    pale2 = (112, 138, 178, 255)

    def draw(d, S):
        cx, cy = 1392 - bx0, 2408 - by0
        for i, (r, n) in enumerate(((70, 4), (98, 5), (128, 5), (160, 6), (196, 6))):
            for j in range(n):
                a = np.deg2rad(rng.uniform(35, 150))
                x, y = cx + r * np.cos(a) * 1.0, cy + r * np.sin(a) * 0.42
                tang = np.rad2deg(np.arctan2(0.42 * np.cos(a), -np.sin(a)))
                if x > (edge[int(y + by0)] - bx0) + 150 or x < (edge[int(y + by0)] - bx0) - 25:
                    continue
                col = pale2 if (i < 2 and j == 0) else pale
                lens(d, x, y, tang, rng.uniform(18, 34), rng.uniform(1.1, 1.9), col, S, bend=rng.uniform(-2, 2))
        for yy in range(int(by0) + 120, int(by1), 17):   # along the waterline itself: short cuts hugging the edge
            ex = edge[yy] - bx0 + rng.uniform(-4, 6)
            lens(d, ex, yy - by0 + rng.uniform(-3, 3), rng.uniform(-14, 10), rng.uniform(14, 26), rng.uniform(1.0, 1.6),
                 pale, S)
    rgb, al = posted_marks(draw, (by1 - by0, bx1 - bx0), (bx0, by0), post=False)
    al = al * 0.92
    reg = out[by0:by1, bx0:bx1]
    over(reg, rgb, al)
    save(out, "p7", "water_r3.png")


# ---------------------------------------------------------------- p3 (30.5): an ember slit between the risen's lips
P3_MOUTH = (1453, 393, -7.0, 40, 2.2)      # field px: centre, angle, length, half width (30.5: frame ~715-745, 255-262)
P3_EMBER_OFF = (166, 350)                 # field px -> ember px (ember pos (116.2, 245) rc at 0.7)


def p3():
    cx, cy, ang, ln, wd = P3_MOUTH
    f = rgba("p3", "field.png")
    e = rgba("p3", "ember.png")
    b = (int(cx - 50), int(cy - 20), int(cx + 50), int(cy + 20))
    sh = (b[3] - b[1], b[2] - b[0])
    lx, ly = cx - b[0], cy - b[1]

    def draw(d, S):
        lens(d, lx, ly, ang, ln, wd, (255, 138, 58, 255), S, bend=1.2)
        lens(d, lx + 2, ly + 0.3, ang, ln * 0.55, wd * 0.45, (255, 208, 122, 255), S, bend=1.0)
    rgb, al = posted_marks(draw, sh, (b[0], b[1]), post=False)
    over(f[b[1]:b[3], b[0]:b[2]], rgb, al)
    save(f, "p3", "field_r3.png")
    ox, oy = P3_EMBER_OFF
    reg = e[b[1] - oy:b[3] - oy, b[0] - ox:b[2] - ox]
    reg[..., :3] = reg[..., :3] * (1 - al[..., None]) + rgb * al[..., None]
    reg[..., 3] = np.maximum(reg[..., 3], al * 0.7)
    save(e, "p3", "ember_r3.png")


# ---------------------------------------------------------------- p3d (39.0 / 44.0): stray red dashes in the sky
P3D_RED = [(3612, 450, 70), (4182, 485, 70), (1411, 227, 70)]   # dawn px (centre, radius)


def p3d():
    """Every red gouge in the sky above the hills (the judge named four at 39.0 / 44.0) becomes the sky's navy stroke,
    its light kept; the Watchman's box and the ground are left alone."""
    import ink_sb5_c as C
    a = rgba("p3d", "dawn.png")
    rgb = a[..., :3]
    H, W = rgb.shape[:2]
    ridge = C.ridge_line(rgb)
    above = np.arange(H)[:, None] < (ridge[None, :] - 8)
    x0, y0, x1, y1 = C.FIGURE_BOX
    above[y0:y1, x0:x1] = False
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = rgb @ LUMW
    spots = np.zeros_like(above)
    for cx, cy, r in P3D_RED:            # the judge's named dashes (one sits in the Watchman's box, above his head)
        spots[cy - r:cy + r, cx - r:cx + r] = True
    above[y0:y1, x0:x1] = spots[y0:y1, x0:x1] & (np.arange(H)[:, None] < (ridge[None, :] - 8))[y0:y1, x0:x1]
    red = (R > G + 0.12) & (G < B + 0.06) & above
    red = nd.binary_dilation(red, iterations=1) & (R > G + 0.05) & (G < B + 0.08) & above
    stroke = above & ~red & (B > R + 0.03)
    navy = np.median(rgb[stroke & (lum <= np.percentile(lum[stroke], 50))], 0)
    rgb[red] = navy * np.clip(lum[red] / max(1e-3, float(navy @ LUMW)), 0.8, 1.15)[:, None]
    print("p3d: red px retinted", int(red.sum()), "navy", navy.round(3))
    save(a, "p3d", "dawn_r3.png")


# ---------------------------------------------------------------- p6 (78.0 / 80.5): the far bank's four lamps
# far px (1.03 frame px each at 80.5): the old bulbs-on-stems are painted out and four iron lights drawn in their place,
# each a different shape, a cold-blue flame and a ragged carved halo; their reflections go on the water below
# (far py 720-783 = frame y ~455-520 at 80.5), on the reveal layer sb_wire_ink makes (P6_LAMP_REFL).
P6_LAMPS = [(901, 641, "box"), (970, 640, "cresset"), (1009, 664, "hook"), (1118, 666, "belly")]
P6_REFL_BOX = (840, 705, 340, 110)        # far px x, y, w, h of lamp_refl_r3.png
IRON = (10, 11, 16, 255)
FLAME = (120, 175, 235, 255)
CORE = (205, 228, 250, 255)


def p6_lamp(d, S, x, y, kind, rng):
    """One iron light, its flame centre at (x, y) (local px)."""
    P = lambda pts: [(px * S, py * S) for px, py in pts]
    # the ragged halo: a dark-navy patch of light with a torn, chipped edge (the iron reads against it), a paler
    # inner ring, a few loose chips outside
    def blob(r0, jit, col, n=26):
        pts = []
        for i in range(n):
            t = 2 * np.pi * i / n
            r = r0 * (1 + rng.uniform(-jit, jit)) * (1.12 if i % 2 else 0.9)
            pts.append((x + r * np.cos(t), y - 3 + r * np.sin(t) * 1.05))
        d.polygon(P(pts), fill=col)
    blob(15, 0.22, (34, 50, 80, 255))
    blob(9.5, 0.25, (56, 82, 124, 255), 18)
    for i in range(9):
        t = rng.uniform(0, 2 * np.pi)
        r = rng.uniform(16, 21)
        lens(d, x + r * np.cos(t), y - 3 + r * np.sin(t), np.rad2deg(t) + 90 + rng.uniform(-30, 30), rng.uniform(3, 6),
             rng.uniform(0.8, 1.2), (40, 58, 90, 255), S)
    if kind == "box":        # a square lantern with a pitched cap and a ring, on a short post
        d.polygon(P([(x - 6, y - 7), (x + 6, y - 7), (x + 6, y + 7), (x - 6, y + 7)]), fill=IRON)
        d.polygon(P([(x - 8, y - 7), (x, y - 14), (x + 8, y - 7)]), fill=IRON)
        d.ellipse(P([(x - 2.2, y - 18.5), (x + 2.2, y - 14)]), outline=IRON, width=int(1.3 * S))
        d.polygon(P([(x - 1.6, y + 7), (x + 1.6, y + 7), (x + 1.3, y + 30), (x - 1.3, y + 30)]), fill=IRON)
        for wx in (-3.2, 2.6):
            lens(d, x + wx, y + 0.5, 90, 10, 1.5, FLAME, S)
        lens(d, x - 0.3, y + 1, 90, 7, 0.9, CORE, S)
    elif kind == "cresset":  # an open iron basket on a pole, the flame rising out of the top
        for k, (yy, hw) in enumerate(((y + 1, 8), (y + 5, 6.5), (y + 9, 4.5))):
            d.line(P([(x - hw, yy), (x + hw, yy)]), fill=IRON, width=int(1.6 * S))
        for sx in (-1, 1):
            d.line(P([(x + sx * 8, y + 1), (x + sx * 3.5, y + 11)]), fill=IRON, width=int(1.5 * S))
        d.line(P([(x, y + 11), (x, y + 34)]), fill=IRON, width=int(2.4 * S))
        for dx, ln, wd, ang in ((-3, 13, 2.4, 96), (1.5, 17, 2.8, 84), (4.5, 10, 2.0, 74)):
            lens(d, x + dx, y - ln / 2 + 2, ang, ln, wd, FLAME, S, bend=rng.uniform(-1.5, 1.5))
        lens(d, x + 0.5, y - 3, 86, 9, 1.1, CORE, S)
        d.line(P([(x - 7, y + 1.5), (x + 7, y + 1.5)]), fill=IRON, width=int(1.4 * S))
    elif kind == "hook":     # a crooked pole with an arm, the lantern hanging under it
        px_ = x - 11
        d.line(P([(px_, y + 26), (px_ + 0.8, y - 8), (px_ + 1.5, y - 16)]), fill=IRON, width=int(2.2 * S))
        d.line(P([(px_ + 1.5, y - 15), (x + 3, y - 17)]), fill=IRON, width=int(1.8 * S))
        d.line(P([(x + 0.5, y - 17), (x + 0.5, y - 9)]), fill=IRON, width=int(1.0 * S))
        d.polygon(P([(x - 4, y - 9), (x + 5, y - 9), (x + 6, y + 6), (x - 5, y + 6)]), fill=IRON)
        d.polygon(P([(x - 3, y + 6), (x + 4, y + 6), (x + 0.5, y + 9)]), fill=IRON)
        lens(d, x + 0.5, y - 1.5, 90, 10, 2.4, FLAME, S)
        lens(d, x + 0.5, y - 1, 90, 6, 1.0, CORE, S)
    else:                    # a squat round-bellied lantern with a handle arch, on a stone
        d.ellipse(P([(x - 7, y - 7), (x + 7, y + 7)]), fill=IRON)
        d.arc(P([(x - 6, y - 15), (x + 6, y - 3)]), 180, 360, fill=IRON, width=int(1.4 * S))
        d.polygon(P([(x - 8, y + 7), (x + 9, y + 7), (x + 11, y + 22), (x - 10, y + 22)]), fill=(22, 24, 32, 255))
        for ang in (-50, -15, 20, 55):
            t = np.deg2rad(ang - 90)
            lens(d, x + 4 * np.cos(t), y + 4 * np.sin(t) + 0.5, ang + 90, 5.5, 1.3, FLAME, S)
        d.ellipse(P([(x - 1.8, y - 1.5), (x + 1.8, y + 2.5)]), fill=CORE)


def p6():
    far = rgba("p6", "far.png")
    rng = np.random.default_rng(78)
    # paint out the old bulbs and stems: each bright pixel near a lamp from the dark bank beside it
    x0, y0, x1, y1 = 860, 600, 1160, 705
    sub = far[y0:y1, x0:x1]
    lum = sub[..., :3] @ LUMW
    m = np.zeros(lum.shape, bool)
    for lx, ly, _ in P6_LAMPS:
        m[ly - 22 - y0:ly + 36 - y0, lx - 16 - x0:lx + 16 - x0] = True
    m &= nd.binary_dilation(lum > 0.16, iterations=3)
    m = nd.binary_dilation(m, iterations=2)
    dark = sub[..., :3][(lum < 0.08) & ~m]
    fill = dark[rng.integers(0, len(dark), int(m.sum()))]
    sub[m, :3] = fill
    print("p6 far: old lamp px painted out", int(m.sum()))
    bx0, by0, bx1, by1 = 860, 600, 1160, 705

    def draw(d, S):
        for lx, ly, kind in P6_LAMPS:
            p6_lamp(d, S, lx - bx0, ly - by0, kind, rng)
    rgb, al = posted_marks(draw, (by1 - by0, bx1 - bx0), (bx0, by0), S=4, post=False)
    over(far[by0:by1, bx0:bx1], rgb, al)
    save(far, "p6", "far_r3.png")
    # the reflections on the water below each: 3-5 short broken horizontal cuts, wider and dimmer downward
    X0, Y0, W0, H0 = P6_REFL_BOX

    def refl(d, S):
        for lx, ly, kind in P6_LAMPS:
            n = int(rng.integers(3, 6))
            y = 722 + rng.uniform(0, 5) - Y0
            for j in range(n):
                ln = rng.uniform(7, 12) * (1 + 0.35 * j)
                x = lx - X0 + rng.uniform(-2.5, 2.5)
                parts = 1 if j == 0 else int(rng.integers(1, 3))
                for q in range(parts):
                    off = 0 if parts == 1 else (q - 0.5) * ln * 0.8
                    c = (140, 186, 236, 255) if j == 0 else ((96, 140, 200, 255) if j < 3 else (64, 96, 146, 255))
                    lens(d, x + off, y, rng.uniform(-3, 3), ln * (0.9 if parts == 1 else 0.6), rng.uniform(1.0, 1.6), c, S)
                y += rng.uniform(9, 14)
                if y > H0 - 4:
                    break
    rgb, al = posted_marks(refl, (H0, W0), (X0 + 1412, Y0), S=4, post=False)
    save(np.dstack([rgb, al]), "p6", "lamp_refl_r3.png")


# ---------------------------------------------------------------- p5: one engraver's weight, and p7's lamp
P5_LAMP_AT = (1925, 445, 74, 92)          # land px: the old ball cage (centre, half sizes) incl. its glow core
P5_CHAIN_END = (1925, 362)                # where the chain meets the cage's top ring (the new arch's top)
P5_FAR = (190, 700)                       # land rows of the far banks (frame y 140-330 over the plate's camera)


def p5_hand(a):
    """POST only: snow speckle -> horizontal carved strokes (a 3 x 9 median where the picture is pale snow; figures,
    being dark, fall outside), dark line work +~2 px (a 3 x 3 minimum where it is ink), the mid-darks crushed toward
    black (hardest across the far banks). The lamp and the cressets (the fires layer's footprint) are kept out."""
    rgb = a[..., :3]
    H, W = rgb.shape[:2]
    lum = rgb @ LUMW
    keep = np.zeros((H, W), bool)
    cx, cy, rx, ry = P5_LAMP_AT
    Y, X = np.mgrid[0:H, 0:W]
    keep |= (((X - cx) / (rx + 6)) ** 2 + ((Y - cy) / (ry + 6)) ** 2) < 1
    fires = rgba("p5", "fires.png")
    fl = (fires[..., :3] @ LUMW) * fires[..., 3] > 0.08
    keep[305:305 + fl.shape[0], 1219:1219 + fl.shape[1]] |= nd.binary_dilation(fl, iterations=26)
    keepw = np.clip(nd.gaussian_filter(keep.astype(np.float32), 18) * 1.6, 0, 1)
    keep = keepw > 0.5
    snow = nd.gaussian_filter((lum > 0.30).astype(np.float32), 7) > 0.5
    snow &= ~keep
    med = np.stack([nd.median_filter(rgb[..., c], size=(3, 9)) for c in range(3)], -1)
    out = np.where(snow[..., None], med, rgb)
    l2 = out @ LUMW
    mn = nd.minimum_filter(l2, size=3)
    arg = nd.minimum_filter(out, size=(3, 3, 1))
    thick = (mn < 0.13) & (l2 > mn + 0.04) & ~keep
    out = np.where(thick[..., None], arg, out)
    # the crush: a toe on the luminance (below lo -> black ink, lo..hi eased), stronger across the far banks
    ys = np.arange(H)[:, None]
    far = np.clip(np.minimum(ys - P5_FAR[0], P5_FAR[1] - ys) / 60.0, 0, 1)
    lo = 0.06 + 0.12 * far
    hi = 0.20 + 0.16 * far
    l3 = out @ LUMW
    t = np.clip((l3 - lo) / (hi - lo), 0, 1)
    gain = np.where(l3 < hi, (t ** 1.6 * hi + (1 - t ** 1.6) * float(IP.BLACK @ LUMW)) / np.maximum(l3, 1e-4), 1.0)
    out = out * gain[..., None]
    out = np.maximum(out, IP.BLACK)
    out = out * (1 - keepw[..., None]) + rgb * keepw[..., None]
    print("p5 hand: snow px", int(snow.sum()), "thickened", int(thick.sum()))
    return out


def p5_lamp(a):
    """The ball cage out (its place refilled from the glow round it), p7's open strap basket in: cut from p7's posted
    lamp layer (the arch top down), scaled to the cage's size, toned to p5's night, a cold flame rising from its open
    top. The chain, the drip of light and the rings stay."""
    cx, cy, rx, ry = P5_LAMP_AT
    rgb = a[..., :3]
    H, W = rgb.shape[:2]
    Y, X = np.mgrid[0:H, 0:W]
    m = (((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2) < 1
    m &= Y > P5_CHAIN_END[1] - 6
    known = (~m).astype(np.float32)
    bg = np.stack([nd.gaussian_filter(rgb[..., c] * known, 16) for c in range(3)], -1)
    bg /= np.maximum(nd.gaussian_filter(known, 16), 1e-3)[..., None]
    fib_t, blo_t = IP.paper()
    g = 1 + IP.GRAIN * np.clip(IP._sample(fib_t, 0, 0, H, W), -3, 3)
    rgb[m] = np.clip(bg[m] * g[m][:, None], 0, 1)
    # the basket (p7 lamp px y >= 880: the handle arch's top and the bowl)
    lamp = rgba("p7", "lamp.png")
    bk = lamp[880:, :]
    ys_, xs_ = np.nonzero(bk[..., 3] > 0.5)
    bk = bk[ys_.min():ys_.max() + 1, xs_.min():xs_.max() + 1]
    tw = 132
    th = int(round(bk.shape[0] * tw / bk.shape[1]))
    im = Image.fromarray((bk * 255 + 0.5).astype(np.uint8), "RGBA").resize((tw, th), Image.LANCZOS)
    b = np.asarray(im).astype(np.float32) / 255
    # toned to p5's night: its light carried on p5's cold blues (the cage's pale band colour), its darks to p5's ink
    bl = b[..., :3] @ LUMW
    cold = np.array([0.62, 0.74, 0.92], np.float32)
    ink = np.asarray(IP.BLACK, np.float32)
    t = np.clip(bl / 0.75, 0, 1)[..., None]
    b[..., :3] = ink * (1 - t) + cold * t
    x0 = int(P5_CHAIN_END[0] - tw / 2)
    y0 = int(P5_CHAIN_END[1] - 4)
    # the flame: carved tongues rising from the open top, behind the front bands (drawn first)
    fx, fy = P5_CHAIN_END[0], y0 + int(0.42 * th)

    def flame(d, S):
        rng = np.random.default_rng(575)
        for dx, ln, wd, ang in ((-16, 26, 3.2, 104), (-7, 46, 4.2, 94), (3, 54, 4.6, 87), (12, 36, 3.6, 80), (19, 20, 2.6, 72)):
            lens(d, 60 + dx, 74 - ln / 2, ang, ln, wd, (110, 165, 230, 255), S, bend=rng.uniform(-4, 4))
        for dx, ln, wd in ((-5, 30, 1.8), (4, 36, 2.0)):
            lens(d, 60 + dx, 76 - ln / 2, 91, ln, wd, (205, 228, 250, 255), S, bend=rng.uniform(-2, 2))
    frgb, fal = posted_marks(flame, (90, 120), (fx - 60, fy - 70), post=False)
    over(a[fy - 70:fy + 20, fx - 60:fx + 60], frgb, fal)
    reg = a[y0:y0 + th, x0:x0 + tw]
    over(reg, b[..., :3], b[..., 3])
    return a


def p5():
    a = rgba("p5", "land.png")
    a[..., :3] = p5_hand(a)
    a = p5_lamp(a)
    save(a, "p5", "land_r3.png")


# ---------------------------------------------------------------- p4 (51-55 s): the jug, re-carved and pouring
P4_JUG_O = (3980, 80)                     # base px of the jug crop's origin (the coordinates below are crop px)
P4_JUG_REGION = (105, 70, 322, 232)       # where the old jug and its fringe are (crop px)
P4_VENT = (371, 146)                      # the lantern's top vent
JUG_CLAY, JUG_SHADE, JUG_HI = (162, 86, 50, 255), (104, 50, 34, 255), (238, 196, 140, 255)


def _ell(cx, cy, rx, ry, rot, t0=0, t1=360, n=48):
    r = np.deg2rad(rot)
    out = []
    for t in np.linspace(np.deg2rad(t0), np.deg2rad(t1), n):
        x, y = rx * np.cos(t), ry * np.sin(t)
        out.append((cx + x * np.cos(r) - y * np.sin(r), cy + x * np.sin(r) + y * np.cos(r)))
    return out


def p4_jug(b):
    """The jug re-carved in the lantern's hand (flat clay, black keyline and shadow gouges, three cut highlights), tipped
    so its lip pours onto the lantern's top vent down a thin dark-gold oil line; the old smudge and its dark-red fringe
    replaced by the sky cloned along its own stroke direction."""
    ox, oy = P4_JUG_O
    W_, H_ = 420, 260
    x0, y0, x1, y1 = P4_JUG_REGION
    sub = b[oy:oy + H_, ox:ox + W_, :3]
    lum = sub @ LUMW
    R, G, B = sub[..., 0], sub[..., 1], sub[..., 2]
    S = 4
    body = _ell(205, 166, 66, 57, -8)
    neck = [(250, 126), (280, 136), (282, 160), (254, 192)]
    lip = _ell(286, 148, 7, 15, -22)
    spout = [(288, 135), (303, 148), (289, 159)]
    handle_o = _ell(196, 122, 50, 34, -8, 185, 345, 30)
    handle_i = _ell(196, 124, 40, 25, -8, 345, 185, 30)

    def shape_mask(polys, grow=0):
        im = Image.new("L", (W_ * S, H_ * S), 0)
        d = ImageDraw.Draw(im)
        for pl in polys:
            d.polygon([(x * S, y * S) for x, y in pl], fill=255)
            if grow:
                d.line([(x * S, y * S) for x, y in pl + pl[:1]], fill=255, width=int(2 * grow * S), joint="curve")
        return im
    solid = [body, neck, lip, spout]
    newm = np.asarray(shape_mask(solid + [handle_o + handle_i], 3.2).resize((W_, H_), Image.LANCZOS)) > 60
    old = np.zeros(lum.shape, bool)
    old[y0:y1, x0:x1] = True
    old &= (lum < 0.45) & ~(B > R + 0.03)
    old[240:] = False
    old[222:240] &= (R > B + 0.06)[222:240]     # under the belly only the reddish fringe (the hands' keylines stay)
    old[:, :150] = False                       # the man's hood and shoulder behind the jug's left stay his
    old = nd.binary_closing(old, iterations=2)
    fill = nd.binary_dilation(old, iterations=3) & ~newm & ~(B > R + 0.03)
    fill[240:] = False
    fill[222:240] &= old[222:240]
    fill[:, :150] = False
    out = sub.copy()
    ys, xs = np.nonzero(fill)
    for dx, dy in ((64, -36), (-64, 36), (110, -62), (-110, 62), (150, -84), (0, -90), (40, -110)):
        sy, sx = np.clip(ys + dy, 0, H_ - 1), np.clip(xs + dx, 0, W_ - 1)
        ok = ~fill[sy, sx] & ~old[sy, sx] & ~newm[sy, sx] & (sub[sy, sx] @ LUMW > 0.35) & (sub[sy, sx, 0] > sub[sy, sx, 2])
        out[ys[ok], xs[ok]] = sub[sy[ok], sx[ok]]
        fill[ys[ok], xs[ok]] = False
        ys, xs = ys[~ok], xs[~ok]
    print("p4 jug: old px", int(old.sum()), "left unfilled", len(ys))
    INK = (12, 10, 12, 255)

    def draw(d, S):
        P = lambda pts: [(x * S, y * S) for x, y in pts]
        for pl in solid:                                   # the keyline: every part grown 3 px in black
            d.polygon(P(pl), fill=INK)
            d.line(P(pl + pl[:1]), fill=INK, width=int(6 * S), joint="curve")
        d.polygon(P(handle_o + handle_i), fill=INK)
        d.line(P(handle_o), fill=INK, width=int(3 * S))
        d.line(P(_ell(196, 123, 45, 29.5, -8, 190, 340, 26)), fill=JUG_SHADE, width=int(3.2 * S))
        for pl in solid:
            d.polygon(P(pl), fill=JUG_CLAY)
        d.polygon(P(_ell(286, 148, 4, 11, -22)), fill=INK)          # the open mouth
        # the shade side in woodcut: a black crescent under the belly, then parallel tapering cuts above it
        d.polygon(P(_ell(208, 172, 62, 50, -8, 10, 170, 30) + _ell(212, 160, 58, 48, -8, 160, 15, 30)), fill=INK)
        for k, (ry, t0, t1) in enumerate(((42, 35, 150), (36, 50, 135), (30, 65, 118))):
            arc = _ell(207, 164, ry * 1.18, ry, -8, t0, t1, 20)
            for i in range(len(arc) - 1):
                w = (2.6 - 0.6 * k) * np.sin(np.pi * (i + 0.5) / (len(arc) - 1)) ** 0.8
                d.line(P(arc[i:i + 2]), fill=INK, width=max(1, int(w * S)))
        d.line(P([(256, 186), (272, 168), (281, 158)]), fill=INK, width=int(2.2 * S))   # the neck's underside
        # three cut highlights following the lit shoulder's curve
        for k, (r_, t0, t1, w0) in enumerate(((50, 200, 250, 2.8), (50, 258, 290, 2.4), (44, 205, 232, 1.6))):
            arc = _ell(205, 166, r_ * 1.14, r_, -8, t0, t1, 14)
            for i in range(len(arc) - 1):
                w = w0 * np.sin(np.pi * (i + 0.5) / (len(arc) - 1)) ** 0.7
                d.line(P(arc[i:i + 2]), fill=JUG_HI, width=max(1, int(w * S)))
        lens(d, 268, 137, 196, 12, 1.4, JUG_HI, S)
        # the oil: from the spout's tip down onto the vent, a thin dark-gold line with a brighter core, a drop below
        sx_, sy_ = 303, 149
        vx, vy = P4_VENT
        pts = [(sx_ + (vx - sx_) * t, sy_ + (vy - sy_ + 6) * t ** 2.2 - 3 * np.sin(np.pi * t)) for t in np.linspace(0, 1, 17)]
        d.line(P(pts), fill=(160, 112, 34, 255), width=int(3.4 * S), joint="curve")
        d.line(P(pts[1:13]), fill=(232, 184, 74, 255), width=int(1.4 * S))
    rgb, al = posted_marks(draw, (H_, W_), (ox, oy), S=S, post=False)
    over(out, rgb, al)
    b[oy:oy + H_, ox:ox + W_, :3] = out
    return b


P4_WATER_LOOK = [(1100, 850, 3300, 1500), (2600, 880, 3900, 1785)]
P4_SKY_COLS = [(2160, 2340), (2500, 2760), (2960, 3150)]     # base px under the bright sky (the old salmon peaks)


def p4_water(b):
    """The rose stipple and its sawtooth 'reflections' out: the river carved like the cool water on its left: a dark
    navy ground and long horizontal cuts (wider apart and longer toward the near bank), the sky's light only as a few
    broken gold and orange cuts under the bright sky near the far bank."""
    import ink_sb5_c as C
    m = C.p4_water_mask(b[..., :3] * 255)
    ys, xs = np.nonzero(m)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    H_, W_ = y1 - y0, x1 - x0
    rng = np.random.default_rng(475)
    S = 2

    def draw(d, S):
        d.rectangle((0, 0, W_ * S, H_ * S), fill=(23, 29, 48, 255))
        y = 4.0
        while y < H_:
            f = y / H_                                   # 0 far .. 1 near
            gap = 11 + 22 * f ** 1.2
            x = rng.uniform(-200, 0)
            while x < W_:
                ln = rng.uniform(90, 300) * (1 + 1.2 * f)
                if rng.random() < 0.8:
                    c = (int(rng.uniform(84, 118)), int(rng.uniform(100, 132)), int(rng.uniform(124, 148)), 255)
                    lens(d, x + ln / 2, y + rng.uniform(-2, 2), rng.uniform(-0.8, 0.8), ln,
                         rng.uniform(1.6, 2.6) * (1 + 1.0 * f), c, S, bend=rng.uniform(-3, 3))
                x += ln + rng.uniform(20, 90) * (1 + f)
            y += gap * rng.uniform(0.8, 1.25)
        # the sky's light: broken gold / orange cuts under the bright sky, near the far bank, thinning downward
        for cx0, cx1 in P4_SKY_COLS:
            for k in range(int(rng.integers(14, 20))):
                yy = rng.uniform(6, 150) ** 1.0
                f = yy / 150
                if rng.random() < f * 0.6:
                    continue
                xc = rng.uniform(cx0, cx1) - x0
                ln = rng.uniform(90, 200) * (1.1 - 0.5 * f)
                col = (226, 168, 76, 255) if rng.random() < 0.55 else (214, 112, 52, 255)
                for q in range(int(rng.integers(1, 3))):
                    lens(d, xc + q * (ln * 0.7), 8 + yy, rng.uniform(-0.6, 0.6), ln * 0.55, rng.uniform(1.6, 2.4), col, S)
    rgb, al = posted_marks(draw, (H_, W_), (x0, y0), S=S, post=False)
    w = np.clip(nd.distance_transform_edt(m[y0:y1, x0:x1]) / 8.0, 0, 1)
    reg = b[y0:y1, x0:x1, :3]
    b[y0:y1, x0:x1, :3] = reg * (1 - w[..., None]) + rgb * w[..., None]
    # the rest of the river (the far bank's and the pillar's dark reflections): its rose cuts to the cut blue
    full = b[..., :3]
    Y, X = np.mgrid[0:full.shape[0], 0:full.shape[1]]
    river = (Y > 958) & (X > 1440) & (X < 3760 - (Y - 960) * 0.2) & ~nd.binary_erosion(m, iterations=9)
    R, G, B = full[..., 0], full[..., 1], full[..., 2]
    rose = river & (R > B + 0.03) & (R > G + 0.07)
    lum = full @ LUMW
    blue = np.array([0.40, 0.48, 0.58], np.float32)
    full[rose] = blue * np.clip(lum[rose] / float(blue @ LUMW), 0.25, 1.1)[:, None]
    print("p4 water: px", int(m.sum()), "box", (x0, y0, x1, y1), "rose cuts recut blue", int(rose.sum()))
    return b


def p4():
    b = rgba("p4", "_base_sb5.png")
    b = p4_water(b)
    b = p4_jug(b)
    save(b, "p4", "_base_r3.png")


def look(name):
    os.makedirs(LOOK, exist_ok=True)
    if name in ("p3", "p3d"):
        f, g, boxes = (("field.png", "field_r3.png", [(1400, 330, 1580, 460)]) if name == "p3" else
                       ("dawn.png", "dawn_r3.png", [(cx - 80, cy - 60, cx + 80, cy + 60) for cx, cy, _ in P3D_RED]))
        a = Image.open(os.path.join(LY, name, f)).convert("RGB")
        b = Image.open(os.path.join(LY, name, g)).convert("RGB")
        tiles = [im.crop(bx).resize(((bx[2] - bx[0]) * 2, (bx[3] - bx[1]) * 2)) for bx in boxes for im in (a, b)]
        W = sum(t.size[0] for t in tiles[:2])
        im = Image.new("RGB", (W, sum(t.size[1] for t in tiles[::2])))
        y = 0
        for i in range(0, len(tiles), 2):
            im.paste(tiles[i], (0, y))
            im.paste(tiles[i + 1], (tiles[i].size[0], y))
            y += tiles[i].size[1]
        im.save(os.path.join(LOOK, name + ".png"))
    if name == "p4":
        a = Image.open(os.path.join(LY, "p4", "_base_sb5.png")).convert("RGB")
        b = Image.open(os.path.join(LY, "p4", "_base_r3.png")).convert("RGB")
        for tag, box in (("jug", (3980, 80, 4460, 420)),) + tuple((f"w{i}", bx) for i, bx in enumerate(P4_WATER_LOOK)):
            A, B = a.crop(box), b.crop(box)
            if A.size[0] > 700:
                A, B = A.resize((A.size[0] // 2, A.size[1] // 2)), B.resize((B.size[0] // 2, B.size[1] // 2))
            im = Image.new("RGB", (A.size[0], A.size[1] * 2))
            im.paste(A, (0, 0))
            im.paste(B, (0, A.size[1]))
            im.save(os.path.join(LOOK, f"p4_{tag}.png"))
    if name == "p5":
        a = Image.open(os.path.join(LY, "p5", "land.png")).convert("RGB")
        b = Image.open(os.path.join(LY, "p5", "land_r3.png")).convert("RGB")
        for tag, box in (("w", (300, 150, 3300, 1750)), ("lamp", (1780, 250, 2080, 620)), ("dead", (300, 900, 1000, 1500))):
            if tag == "w":
                A, B = a.crop(box).resize((750, 400)), b.crop(box).resize((750, 400))
            else:
                A, B = a.crop(box), b.crop(box)
            im = Image.new("RGB", (A.size[0] * 2, A.size[1]))
            im.paste(A, (0, 0))
            im.paste(B, (A.size[0], 0))
            im.save(os.path.join(LOOK, f"p5_{tag}.png"))
    if name == "p6":
        a = Image.open(os.path.join(LY, "p6", "far.png")).convert("RGB").crop((860, 590, 1160, 800))
        b = Image.open(os.path.join(LY, "p6", "far_r3.png")).convert("RGBA").crop((860, 590, 1160, 800))
        r = Image.open(os.path.join(LY, "p6", "lamp_refl_r3.png")).convert("RGBA")
        x0, y0 = P6_REFL_BOX[:2]
        b.alpha_composite(r, (x0 - 860, y0 - 590))
        im = Image.new("RGB", (1200, 420))
        im.paste(a.resize((600, 420)), (0, 0))
        im.paste(b.convert("RGB").resize((600, 420)), (600, 0))
        im.save(os.path.join(LOOK, "p6.png"))
    if name == "p7":
        a = Image.open(os.path.join(LY, "p7", "water_sb5.png")).convert("RGB")
        b = Image.open(os.path.join(LY, "p7", "water_r3.png")).convert("RGB")
        box = (1000, 2250, 1560, 2640)
        im = Image.new("RGB", (1120, 390))
        im.paste(a.crop(box), (0, 0))
        im.paste(b.crop(box), (560, 0))
        im.save(os.path.join(LOOK, "p7.png"))


def apply(which):
    for p in which or ("p7",):
        globals()[p]()


if __name__ == "__main__":
    {"apply": lambda: apply(sys.argv[2:]), "look": lambda: look(sys.argv[2])}[sys.argv[1]]()
