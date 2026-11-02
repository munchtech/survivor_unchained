"""Storybook 5, solver C (sb5-patch-C): local fixes on p3 (night), p3d (dawn) and p4 (keepers) after the r9 judge.

    python tools/storybook/ink_sb5_c.py gpu      # Krea 2 turbo inpaints, every candidate cached (one gpu turn)
    python tools/storybook/ink_sb5_c.py sheet    # crops of the candidates for the pick -> out/sb5/c_sheet_*.jpg
    python tools/storybook/ink_sb5_c.py make     # compose the picks (PICK below) into the sources the build reads:
                                                 #   out/sb5/p3n_sb5.png (gen px; ink_layers.PLATES p3 gen)
                                                 #   out/sb5/dawn_sb5.png (gen px; PLATES p3d gen)
                                                 #   out/ink_layers/p4/_base_sb5.png (posted px; plate_p4 prefers it)

p3 / p3d work in gen px before the post (like ink_rc_fix: crop x3, inpaint, back through a feathered mask). p4 works on
the posted base (1 unit a px, as ink_p4_wisp) and posts every new pixel (ink_post, registered by offset). The p4 Krea
scale is kept near the plate's own gen scale (base / 2.32) so the new carving has the plate's line density.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_recarve as RC  # noqa: E402

OUT = os.path.join(HERE, "out", "sb5")
CAND = os.path.join(OUT, "cand")
P3_SRC = os.path.join(HERE, "out", "ink_rc", "fix", "p3dead_d65_s11.png")
P3D_SRC = os.path.join(HERE, "out", "ink_rc", "dawn2", "dawn2_d40_s47.png")
P4_DIR = os.path.join(HERE, "out", "ink_layers", "p4")
P4_SRC = os.path.join(P4_DIR, "_base_nowisp.png")
PRE, STY = RC.R2["prefix"], RC.R2["style"]


def ells_mask(shape, ells):
    m = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(m)
    for cx, cy, rx, ry in ells:
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    return np.asarray(m) > 127


def feather(m, f):
    return np.clip(nd.distance_transform_edt(m) / f, 0, 1)


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32)


# ---------------------------------------------------------------- masks (full-image px)
def p3d_spear():
    """dawn2's spear runs off the top of the picture: its top 130 gen px moved down D px and pointed; the sky
    above it is the Krea fill. Returns (init with the moved blade, fill mask, blade mask)."""
    a = load(P3D_SRC)
    x0, x1, y1, D, T = 1330, 1420, 80, 52, 34
    sub = a[:y1, x0:x1]
    dark = sub.mean(-1) < 70
    lab, n = nd.label(dark)
    keep = np.zeros_like(dark)
    for i in range(1, n + 1):   # the shaft: the component touching the top row
        c = lab == i
        if c[0].any() and c.sum() > 200:
            keep |= c
    blade = np.zeros(a.shape[:2], bool)
    blade[D:y1 + D, x0:x1] = keep[:y1 - 0]
    ys, xs = np.nonzero(blade)
    cx = np.median(xs[ys < D + 20])
    for y in range(D, D + T):   # the point
        hw = 1 + (y - D) / T * 10
        row = blade[y]
        row[: int(cx - hw)] = False
        row[int(cx + hw) + 1:] = False
    init = a.copy()
    shifted = np.zeros_like(a)
    shifted[D:y1 + D, x0:x1] = a[:y1, x0:x1]
    init[blade] = shifted[blade]
    old = np.zeros(a.shape[:2], bool)
    old[:y1, x0:x1] = keep
    fill = nd.binary_dilation(old, iterations=4) & ~nd.binary_dilation(blade, iterations=1)
    fill[D + T + 40:] = False
    return init, fill, blade


def p4_sky_line(a, x0, x1, run=45):
    """Per column, the first row where `run` rows in a row are hill (blue-dominant and dim, or black)."""
    sub = a[:, x0:x1]
    lum = sub.mean(-1) / 255
    dark = ((sub[..., 2] > sub[..., 0] + 10) & (lum < 0.4)) | (lum < 0.12)
    cs = np.cumsum(np.vstack([np.zeros((1, dark.shape[1])), dark]), 0)
    full = (cs[run:] - cs[:-run]) >= run
    first = np.where(full.any(0), full.argmax(0), a.shape[0])
    return nd.median_filter(first, 31)


def p4_seam_mask(a):
    """r1 (picked): the sky across the join, x 896-1416, down to the hills (520 at most)."""
    x0, x1, cx, half = 760, 1560, 1156, 260
    line = p4_sky_line(a, x0, x1)
    m = np.zeros(a.shape[:2], bool)
    for i, x in enumerate(range(x0, x1)):
        if abs(x - cx) < half:
            m[:min(520, max(0, line[i] - 6)), x] = True
    return m


def p4_seam_mask_wide(a):
    """TRIED, not used: the whole left sky up to past the seam (x 0-1450, so no new edge inside the frame on the left; the right edge
    lands in like orange hatching), down to the hills (the far valley's sky down to 640 at most)."""
    x0, x1 = 0, 1450
    line = p4_sky_line(a, x0, x1)
    m = np.zeros(a.shape[:2], bool)
    for i, x in enumerate(range(x0, x1)):
        m[:min(640, max(0, line[i] - 6)), x] = True
    return m


ROSE = np.array([0x7a, 0x4c, 0x58], np.float32)


def p4_water_mask(a):
    x0, y0, x1, y1 = 1440, 870, 3700, 1785
    sub = a[y0:y1, x0:x1]
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    rose = (r > b + 8) & (r > g + 20) & (sub.mean(-1) > 55)
    rose = nd.binary_closing(rose, iterations=6)
    rose = nd.binary_fill_holes(rose)
    rose = nd.binary_opening(rose, iterations=4)
    lab, n = nd.label(rose)
    if n:
        sizes = nd.sum(rose, lab, range(1, n + 1))
        rose = np.isin(lab, 1 + np.nonzero(sizes > 20000)[0])
    m = np.zeros(a.shape[:2], bool)
    m[y0:y1, x0:x1] = rose
    return m


def p4_water_init(a, m):
    """Rose to navy, lower water first (the top keeps a little rose: the sky's reflection near the far bank)."""
    out = a.copy()
    ys = np.arange(a.shape[0])[:, None].repeat(a.shape[1], 1)
    w = np.clip((ys - 930) / 320, 0, 1) * 0.85 + 0.1
    lum = a.mean(-1, keepdims=True) / 255
    navy = np.array([0x1c, 0x26, 0x42], np.float32) * (0.6 + 1.6 * lum)
    navy = np.minimum(navy, np.array([0x68, 0x7c, 0x8e], np.float32))
    mix = a * (1 - w[..., None]) + navy * w[..., None]
    out[m] = mix[m]
    return out


P4_PROPS = [(4380, 318, 118, 84), (4228, 248, 92, 88), (4118, 206, 50, 44), (4335, 238, 52, 42)]
P4_HAZE = [(4468, 228, 70, 84)]


# ---------------------------------------------------------------- jobs
# name: (space, src fn, box, mask fn, k, prompt, denoises, seeds)
def jobs():
    p3 = lambda: load(P3_SRC)
    p4 = lambda: load(P4_SRC)

    def props_mask(a):
        return ells_mask(a.shape, P4_PROPS)

    def haze_mask(a):
        return ells_mask(a.shape, P4_HAZE) & ~nd.binary_dilation(props_mask(a), iterations=10)

    return {
        "p3hand": ("gen", p3, (150, 450, 420, 730), lambda a: ells_mask(a.shape, [(262, 605, 62, 100)]), 3,
                   "Night. A dead man's gaunt bony hand and forearm thrust straight up out of a black crack in the frozen "
                   "ground, the fingers clawed and stiff. The hand is carved solid in dark slate gray with black gouge "
                   "lines, a dead hand, not lit. Under it, deep in the crack in the soil, ember orange light glows.",
                   (0.6, 0.7), (11, 47)),
        "p3spear": ("gen", p3, (1560, 100, 2080, 460),
                    lambda a: ells_mask(a.shape, [(1675, 195, 70, 62), (1885, 312, 42, 36), (2003, 318, 18, 14)]), 3,
                    "Night. A gaunt dead man bent forward, run through the body by a long iron spear. His head hangs "
                    "forward in profile: a gaunt sunken face, lank wet hair, a small ember orange glint in his dark eye "
                    "socket. Ember orange light spills out of the wound where the spear blade comes out of his back, "
                    "like a lamp behind paper: bold orange carved marks inside the black. Dim slate blue sky behind, "
                    "carved in long gouge lines.", (0.55, 0.65), (11, 47)),
        "p3dtip": ("gen", None, (1270, 0, 1480, 180), None, 3,
                   "Gray first light of dawn: a pale gray sky carved in long sweeping gouge lines. Only sky, nothing "
                   "else, no pole, no spear.", (0.9,), (11, 47)),
        "p4seam": ("post", p4, (760, 0, 1560, 560), p4_seam_mask, 0.6,
                   "A sunset sky carved in long sweeping curved gouge lines, one continuous set of curved strokes running "
                   "across the whole sky, orange strokes over pale yellow light, cooler pale blue-gray strokes toward the "
                   "upper left, darker dusky rose toward the top. No clouds, no figures.", (0.85,), (11, 47)),
        "p4water": ("post", p4, (1440, 840, 3720, 1785), p4_water_mask, 0.55,
                    "A dark navy river at dusk, wide and calm, its whole surface carved in long horizontal ripple gouge "
                    "lines, black and slate blue strokes on dark navy, a faint dusky rose glow of the sunset sky reflected "
                    "only near the far bank. No boats, no figures.", (0.55, 0.65), (11, 47)),
        "p4props": ("post", p4, (3980, 60, 4660, 470), props_mask, 1.5,
                    "An old Watchman's hands hold a heavy round earthen clay oil jug, tilted, a thin dark stream of oil "
                    "pouring from its lip down into a Watch post lamp standing on top of a square stone post: a small "
                    "square lantern with a black iron cage frame, glass panes and a small flame inside, a ring handle on "
                    "top. Behind, a bright sunset sky carved in sweeping gouge lines, orange strokes over pale yellow "
                    "light. No teapot, no genie lamp.", (0.7, 0.8), (11, 47)),
        # the props pick left a soft dark smudge where the floating block was: repainted as sky on top of that pick
        "p4clean": ("post", lambda: load(cand_path("p4props", 0.7, 47)), (3990, 100, 4230, 290),
                    lambda a: ells_mask(a.shape, [(4106, 188, 46, 36)]), 1.5,
                    "A bright sunset sky carved in long sweeping gouge lines, orange strokes over pale yellow light, "
                    "clear open sky. No smoke, no clouds, no black shapes.", (0.75,), (11, 47)),
        "p4haze": ("post", p4, (4300, 40, 4640, 380), haze_mask, 1.5,
                   "A bright sunset sky carved in long straight gouge lines like rays of light, orange strokes over pale "
                   "yellow light, clear open sky. No smoke, no clouds, no glow, no figure.", (0.8,), (11, 47)),
    }


def cand_path(name, dn, seed):
    return os.path.join(CAND, f"{name}_d{round(dn * 100)}_s{seed}.png")


def run(name, spec, dn, seed):
    """Writes the candidate's full-size patched image (cached). gen-space jobs stay unposted; post-space are posted."""
    import ink_comfy as C
    dst = cand_path(name, dn, seed)
    if os.path.exists(dst):
        return dst
    space, srcf, box, maskf, k, prompt, _, _ = spec
    if name == "p3dtip":
        img, m, _ = p3d_spear()
    else:
        img = srcf()
        m = maskf(img)
    x0, y0, x1, y1 = box
    cw, ch = max(16, int((x1 - x0) * k) // 16 * 16), max(16, int((y1 - y0) * k) // 16 * 16)
    tmp = os.path.join(CAND, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    ci, mi = os.path.join(tmp, f"{name}_crop.png"), os.path.join(tmp, f"{name}_mask.png")
    Image.fromarray(img[y0:y1, x0:x1].astype(np.uint8)).resize((cw, ch), Image.LANCZOS).save(ci)
    mm = nd.binary_dilation(m, iterations=3) if space == "gen" else m
    Image.fromarray((mm[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((cw, ch), Image.NEAREST).save(mi)
    raw = os.path.join(tmp, f"{name}_raw_d{round(dn * 100)}_s{seed}.png")
    C.krea(f"{PRE} {prompt} {STY}", cw, ch, seed, raw, init=ci, denoise=dn, mask=mi)
    back = np.asarray(Image.open(raw).convert("RGB").resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(np.float32)
    if space == "post":
        import ink_post as IP
        back = IP.post(back / 255, offset=(x0, y0)) * 255
    w = feather(m, 10 if space == "gen" else 24)[y0:y1, x0:x1, None]
    out = img.copy()
    out[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - w) + back * w
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(dst)
    return dst


def gpu(only=None):
    os.makedirs(CAND, exist_ok=True)
    for name, spec in jobs().items():
        if only and name not in only:
            continue
        for dn in spec[6]:
            for s in spec[7]:
                print(run(name, spec, dn, s), flush=True)


def sheet():
    import ink_r5 as R
    J = jobs()
    for group in (("p3hand", "p3spear", "p3dtip"), ("p4seam", "p4water"), ("p4props", "p4haze")):
        tiles = []
        for name in group:
            space, srcf, box, maskf, k, prompt, dns, seeds = J[name]
            src = P3D_SRC if name == "p3dtip" else (P3_SRC if space == "gen" else P4_SRC)
            for f in [src] + [cand_path(name, d, s) for d in dns for s in seeds]:
                if not os.path.exists(f):
                    continue
                p = os.path.join(CAND, "_tmp", "_c_" + name + "_" + os.path.basename(f))
                Image.open(f).convert("RGB").crop(box).save(p)
                tiles.append(p)
        R.sheet_of(tiles, os.path.join(OUT, f"c_sheet_{group[0]}.jpg"), cols=5, tw=360)


# picks: name -> (denoise, seed) or None (keep the source there)
PICK = {"p3hand": (0.6, 47), "p3spear": (0.55, 47), "p3dtip": None, "p4seam": (0.85, 47), "p4water": (0.65, 11),
        "p4props": (0.7, 47), "p4clean": (0.75, 11), "p4haze": (0.8, 47)}


def paste(dst, name, spec):
    """dst (full image) gets the picked candidate inside that job's feathered mask."""
    if PICK.get(name) is None:
        return dst
    space, srcf, box, maskf, k = spec[:5]
    cand = load(cand_path(name, *PICK[name]))
    if name == "p3dtip":
        _, m, blade = p3d_spear()
        m = m | blade
    else:
        m = maskf(load(P3_SRC if space == "gen" else P4_SRC))
    w = feather(nd.binary_dilation(m, iterations=2), 10 if space == "gen" else 24)
    if name == "p4seam":   # its left edge (pale blue strokes both sides) and the 520 cut in the far valley fade out
        H, W = w.shape
        xs, ys = np.arange(W)[None, :], np.arange(H)[:, None]
        w = w * np.clip((xs - 896) / 150, 0, 1) * np.clip((1416 - xs) / 160, 0, 1) * np.clip((520 - ys) / 90, 0, 1)
    w = w[..., None]
    return dst * (1 - w) + cand * w


def save(a, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8)).save(p)
    print("wrote", p)


def bush_rim(a):
    """p4: the salmon rim on the near bush's left edge (a cut-out halo of the willow refill) to the bush's black."""
    x0, y0, x1, y1 = 1630, 560, 1780, 830
    sub = a[y0:y1, x0:x1]
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    sal = (r > b + 25) & (r > g + 25)
    dark = sub.mean(-1) < 45
    near = nd.binary_dilation(dark, iterations=14)
    fix = sal & near
    col = np.median(sub[dark], 0) if dark.any() else np.array([20, 22, 34], np.float32)
    sub[fix] = col * (0.9 + 0.2 * (sub[fix].mean(-1, keepdims=True) / 255))
    a[y0:y1, x0:x1] = sub
    return a


def wound_light(a):
    """p3: the speared man's inner light (Krea won't draw it): carved ember marks spilling from where the spear leaves
    his body, and a glint at his eye. Warm, so ink_rc_build makes them part of the ember add layer (drains at dawn)."""
    im = Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    EMB, GOLD = (255, 138, 58), (255, 208, 122)
    ox, oy = 1888, 310

    def slit(cx, cy, ang, ln, wd, col):   # a lens-shaped gouge (tapered both ends), like the torn-cloth light marks
        t = np.deg2rad(ang)
        ux, uy, px, py = np.cos(t), np.sin(t), -np.sin(t), np.cos(t)
        pts = []
        for i in range(9):
            s_ = -1 + i / 4
            w_ = wd * (1 - s_ * s_) ** 0.7
            pts.append((cx + ux * s_ * ln / 2 + px * w_, cy + uy * s_ * ln / 2 + py * w_))
        for i in range(8, -1, -1):
            s_ = -1 + i / 4
            w_ = wd * (1 - s_ * s_) ** 0.7
            pts.append((cx + ux * s_ * ln / 2 - px * w_, cy + uy * s_ * ln / 2 - py * w_))
        d.polygon(pts, fill=col)

    for dx, dy, ang, ln, wd in ((-7, -3, 76, 17, 2.4), (0, 2, 82, 22, 3.0), (7, -1, 70, 14, 2.2), (-13, 7, 86, 11, 1.8),
                                (4, 15, 96, 10, 1.7), (12, 9, 64, 8, 1.5)):
        slit(ox + dx, oy + dy, ang, ln, wd, EMB)
    slit(ox, oy + 1, 82, 12, 1.2, GOLD)
    ex, ey = 1680, 215
    d.ellipse((ex - 3, ey - 2, ex + 3, ey + 2), fill=EMB)
    d.ellipse((ex - 1.2, ey - 1, ex + 1.2, ey + 1), fill=GOLD)
    return np.asarray(im).astype(np.float32)


def dawn_tip(a):
    """p3d: the spear's blade moved down and pointed (p3d_spear), the sky where the shaft was filled from the sky one
    stroke-length along its own gouge direction (the strokes run down to the right), so the hatching stays continuous."""
    init, fill, blade = p3d_spear()
    out = a.copy()
    out[blade] = init[blade]
    ys, xs = np.nonzero(fill)
    for dx, dy in ((46, 16), (-46, -16), (70, 25)):
        sy, sx = np.clip(ys + dy, 0, a.shape[0] - 1), np.clip(xs + dx, 0, a.shape[1] - 1)
        ok = ~fill[sy, sx] & ~blade[sy, sx] & (a[sy, sx].mean(-1) > 60)
        out[ys[ok], xs[ok]] = a[sy[ok], sx[ok]]
        fill = fill.copy()
        fill[ys[ok], xs[ok]] = False
        ys, xs = ys[~ok], xs[~ok]
    return out


def make():
    J = jobs()
    p3 = load(P3_SRC)
    for n in ("p3hand", "p3spear"):
        p3 = paste(p3, n, J[n])
    p3 = wound_light(p3)
    save(p3, os.path.join(OUT, "p3n_sb5.png"))
    d = dawn_tip(load(P3D_SRC))
    save(d, os.path.join(OUT, "dawn_sb5.png"))
    rgba = np.asarray(Image.open(P4_SRC).convert("RGBA")).astype(np.float32)
    b = rgba[..., :3]
    for n in ("p4seam", "p4water", "p4props", "p4clean", "p4haze"):
        b = paste(b, n, J[n])
    b = bush_rim(b)
    rgba = np.dstack([b, rgba[..., 3]])
    Image.fromarray(np.clip(rgba + 0.5, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(P4_DIR, "_base_sb5.png"))
    print("wrote", os.path.join(P4_DIR, "_base_sb5.png"))


if __name__ == "__main__":
    {"gpu": lambda: gpu(sys.argv[2:]), "sheet": sheet, "make": make}[sys.argv[1]]()


# ---------------------------------------------------------------- p3d: the dawn band (posted px, called by ink_rc_build)
STRAW = np.array([0.88, 0.80, 0.60], np.float32)     # pale straw/ochre (parchment leaning ochre; gold stays the ember's)
FIGURE_BOX = (2900, 0, 3650, 1500)                    # posted px: the Watchman (no pink-fleck fix across him)
TREE_COLS = (4250, 4560)
RIDGE = [(0, 300), (400, 380), (800, 432), (1200, 480), (1600, 540), (2000, 568), (2400, 584), (2800, 592), (3400, 600),
         (3800, 592), (4000, 585), (4200, 545), (4400, 500), (4600, 455), (4800, 420), (5100, 390), (5400, 365)]                              # posted px: the tree's trunk


def ridge_line(lit, y0=250, y1=1000, run=40):
    lum = lit.mean(-1)
    dark = lum[y0:y1] < 0.2
    cs = np.cumsum(np.vstack([np.zeros((1, dark.shape[1])), dark]), 0)
    full = (cs[run:] - cs[:-run]) >= run
    first = np.where(full.any(0), full.argmax(0), y1 - y0) + y0
    # the hand-read ridge (posted px) is the guide; the measured line is used where it agrees (the Watchman, the tree
    # and the thin far horizon break the measure)
    xs = np.arange(len(first))
    guide = np.interp(xs, *zip(*RIDGE))
    raw = nd.median_filter(first, 41, mode="nearest").astype(np.float32)
    line = np.where(np.abs(raw - guide) < 40, raw, guide)
    for a, b in ((FIGURE_BOX[0], FIGURE_BOX[2]), TREE_COLS):
        line[a:b] = guide[a:b]
    return np.round(nd.gaussian_filter1d(line, 12, mode="nearest")).astype(int)


def dawn_band(lit, band=150, rise=200):
    """One continuous band of first light just above the hills: the sky's paper there goes pale straw (its gouge strokes
    stay), fading upward along the paper between the strokes (warm carved lines rising into the lower sky). The pink
    flecks along the ridge go straw above it and hill-black below it."""
    H, W, _ = lit.shape
    out = lit.copy()
    ridge = ridge_line(lit)
    ys = np.arange(H)[:, None]
    above = ridge[None, :] - ys                       # >0 above the ridge
    w = np.where(above < 0, 0, np.where(above <= band, 1.0, np.clip(1 - (above - band) / rise, 0, 1) ** 2.2))
    r, g, b = lit[..., 0], lit[..., 1], lit[..., 2]
    lum = lit.mean(-1)
    sky = (b > r + 0.02) & (lum > 0.33)
    paper = np.clip((lum - 0.33) / 0.15, 0, 1)
    ref = np.median(lit[sky & (above > band) & (above < band + rise)], 0)
    tinted = lit * (STRAW / ref)[None, None, :]
    k = (w * paper * sky)[..., None]
    out = out * (1 - k) + tinted * k
    pink = (r > b + 0.06) & (r > g + 0.03) & (above > -130) & (above < band + 80)
    x0, y0, x1, y1 = FIGURE_BOX
    pink[y0:y1, x0:x1] = False
    pink = nd.binary_dilation(pink, iterations=2) & (r > b - 0.02)
    hill = np.median(lit[(lum < 0.15)], 0)
    up_ = pink & (above >= 0)
    out[up_] = (STRAW * np.clip(lum[up_] / max(1e-3, float(ref.mean())), 0.6, 1.05)[:, None])
    out[pink & (above < 0)] = hill
    import ink_post as IP
    return np.clip(np.minimum(out, IP.LIGHT), 0, 1)
