"""Storybook 5, solver P (sb5-p1p5-build): p5 rebuilt from ChatGPT p5_E2, p1's forge without the torch procession,
and the new door plate p1d from ChatGPT p1_D2 / p1_D2_shut (sources copied to out/sb5/).

    python tools/storybook/ink_sb5_p.py prep     # p5: E2 cropped as R1 was + the f1 flatten -> out/sb5/p/_init_*
    python tools/storybook/ink_sb5_p.py gpu      # Krea: p5 re-carve (0.40 x2 seeds, 0.30 light pass), p1 procession
                                                 # out (posted base), p1d the chain off the shut slab (one gpu turn)
    python tools/storybook/ink_sb5_p.py sheet    # crops for the picks -> out/sb5/p_sheet_*.jpg
    python tools/storybook/ink_sb5_p.py make     # the picks (PICK) -> out/sb5/p5e2_sb5.png (gen px, ink_layers.PLATES
                                                 # p5 gen), out/ink_layers/p1/{base,torches}_sb5p.png, and
                                                 # out/ink_layers/p1d/ (layers.json + PNGs)

p5 follows ink_recarve (f1 flatten, Krea img2img 0.40 at the carve size) and ink_rc_build (night + cold post); the
p5 "cages" inpaint of ink_rc_fix is NOT used. Where the re-carve redraws the cressets, the hanging lamp + chain or
the dead faces, those regions come back from the light pass (KEEP below).
p1d: the open plate posted (ink_post), its doorway gold an add layer that dims as the slab closes; the slab (the shut
picture's, its chain inpainted off) slides in behind a foreground cut of the right jamb; on the drum hit a hard switch
to the full shut picture, its seams an add layer that flickers and settles.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_recarve as RC  # noqa: E402

SB5 = os.path.join(HERE, "out", "sb5")
OUT = os.path.join(SB5, "p")
CAND = os.path.join(OUT, "cand")
LAY = os.path.join(HERE, "out", "ink_layers")
PRE, STY = RC.R2["prefix"], RC.R2["style"]

# ---------------------------------------------------------------- p5
E2 = os.path.join(SB5, "p5_E2.png")
P5_BOX, P5_GEN = (0, 104, 1536, 920), (2048, 1088)          # as ink_recarve's p5R1
P5_PROMPT = (
    "A shadow puppet theatre scene in carved black ink. Winter night at a river ford: a black sky carved in long "
    "sweeping gouge lines, low black hills, the black river across the middle of the picture. On the near bank three "
    "medieval iron cressets, open cages of flat black iron straps, each on one straight iron post driven into the "
    "snow, each burning with a small white-hot core in cold pale blue flame, its light falling on the snow around its "
    "post. Midstream the fourth light: a round lamp basket of woven iron straps glowing white-blue inside, hanging "
    "just above the water from an iron chain that rises straight up into the black sky; under it a broken vertical "
    "reflection and rings carved on the black water. A rutted dirt road comes from the ford down toward us; beside it "
    "a heavy wooden farm wagon lies overturned on its side, one spoked wheel up. On both sides of the road the black "
    "water floods the snowy banks, and in it stand the drowned dead, knee-deep, in irregular clumps, heads hung "
    "forward, long wet hair hanging over pale gaunt dead faces, thin bodies in soaked ragged shifts, arms slack, "
    "barefoot, no hats. The snow and the road are carved all over in long gouge strokes, dim blue-gray; everything "
    "away from the lights sinks into black and deep blue-black. No warm light, no orange, no yellow; the only color "
    "is the cold blue light.")
P5_RUNS = [(0.40, 47), (0.40, 202), (0.30, 47)]

# ---------------------------------------------------------------- p1 (posted base, 1 unit a px)
P1_BASE = os.path.join(LAY, "p1", "base.png")
P1_TORCH = os.path.join(LAY, "p1", "torches.png")
P1_PROC = [(2170, 730), (2330, 700), (2560, 760), (2600, 860), (2690, 960), (2640, 1060), (2700, 1150), (2800, 1250),
           (3070, 1330), (3070, 1740), (2420, 1740), (2330, 1330), (2250, 1120), (2170, 960)]
P1_PROMPT = ("Night, a high stone ledge. At the top dark red cloaks of Roman legionaries and the rim of a round blue "
             "shield; across the middle the dusky rose-red rock edge of the ledge; below it a steep black cliff face "
             "carved in slate blue gouge strokes, falling away into darkness. Empty rock: no people, no torches, no "
             "fire, no flames.")
# the whole-band repaint (p1proc) left a flat slab of ledge and a soft seam: only the walkers come out (p1path), the
# path they walked stays, empty
P1_PATH_PROMPT = ("Night. An empty narrow stone path of slate blue rock going steeply down along a black cliff, nobody on "
                  "it; behind it at the top the dark red cloaks of Roman legionaries and a round blue shield. No people "
                  "on the path, no torches, no fire, no flames.")


def proc_mask(b):
    """The walkers on p1's path (posted px): warm or light pixels (tunics, faces, flames) and the torches layer's
    flames inside P1_PROC, closed into figures and grown 14 px."""
    poly = poly_mask(b.shape, P1_PROC)
    r, bl = b[..., 0] / 255, b[..., 2] / 255
    m = ((r - bl) > 0.10) & (r > 0.25) | (b.mean(-1) / 255 > 0.45)
    t = np.asarray(Image.open(P1_TORCH).convert("RGBA"))[..., 3] > 40
    m[:t.shape[0]] |= t
    m = nd.binary_opening(m & poly, iterations=1)
    m = nd.binary_closing(m, iterations=12)
    return nd.binary_dilation(m, iterations=14) & nd.binary_dilation(poly, iterations=10)


# ---------------------------------------------------------------- p1d (ChatGPT px, 1677 x 938)
D2, D2S = os.path.join(SB5, "p1_D2.png"), os.path.join(SB5, "p1_D2_shut.png")
LINTEL_TOP = 132                   # the lintel's top-left corner (ChatGPT px row; the picture's highest door part)
SLAB = (607, 298, 878, 742)        # the shut slab inside its gold seams (x0, y0, x1, y1)
SLAB_TOP = (295, 610, 0.234)       # r3: the shut slab's top seam, row = a + (x - b) * c (ChatGPT px)
CHAIN = (607, 452, 878, 612)       # the chain across it (inpainted off for the sliding slab)
SLAB_PROMPT = ("A massive plain stone door slab, dark blue-gray granite carved in fine stippled gouge marks, two long "
               "thin cracks running diagonally across it, dimly lit. Plain stone only: no chain, no metal, no iron.")
JOBS = {   # name: (space, crop box, k, prompt, denoise list, seeds)
    "p1proc": ("post", (2060, 620, 3100, 1760), 0.6, P1_PROMPT, (0.85, 0.95), (11, 47)),
    "p1path": ("post", (2060, 620, 3100, 1760), 0.6, P1_PATH_PROMPT, (0.9, 1.0), (11, 47)),
    "p1path2": ("post", (2060, 620, 3100, 1760), 0.6, P1_PATH_PROMPT, (0.6, 0.75, 0.9), (11, 47)),   # Telea-filled init
    "p1slab": ("gen", (560, 400, 930, 680), 3, SLAB_PROMPT, (0.9, 1.0), (11, 47)),
}
PICK = {"p5": None, "p1proc": (0.85, 11), "p1slab": None}   # p1slab None: slab_clone()
KEEP = []   # p5 (gen px ellipses cx, cy, rx, ry) taken back from the 0.30 pass if the 0.40 one redraws them


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32)


def save(a, p, alpha=None):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    a = np.clip(a + 0.5, 0, 255).astype(np.uint8)
    if alpha is not None:
        a = np.dstack([a, np.clip(alpha * 255 + 0.5, 0, 255).astype(np.uint8)])
    Image.fromarray(a).save(p)
    print("wrote", os.path.relpath(p, HERE))


def poly_mask(shape, pts):
    m = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return np.asarray(m) > 127


def ells(shape, es):
    m = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(m)
    for cx, cy, rx, ry in es:
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    return np.asarray(m) > 127


def feather(m, f):
    return np.clip(nd.distance_transform_edt(m) / f, 0, 1)


def rect(shape, box):
    m = np.zeros(shape[:2], bool)
    x0, y0, x1, y1 = box
    m[y0:y1, x0:x1] = True
    return m


# ---------------------------------------------------------------- prep / gpu
def prep():
    os.makedirs(OUT, exist_ok=True)
    im = Image.open(E2).convert("RGB").crop(P5_BOX).resize(P5_GEN, Image.LANCZOS)
    im.save(os.path.join(OUT, "_init_p5E2_f0.png"))
    rgb, _ = RC.flatten(np.asarray(im)[..., ::-1].copy(), "f1")
    Image.fromarray(rgb).save(os.path.join(OUT, "_init_p5E2_f1.png"))
    print("prep done")


def p5_path(dn, seed):
    return os.path.join(OUT, f"p5E2_f1_d{round(dn * 100)}_s{seed}.png")


def cand_path(name, dn, seed):
    return os.path.join(CAND, f"{name}_d{round(dn * 100)}_s{seed}.png")


def job_src(name):
    return load(D2S) if name == "p1slab" else load(P1_BASE)


def job_mask(name, img):
    if name == "p1proc":
        return poly_mask(img.shape, P1_PROC)
    if name.startswith("p1path"):
        return proc_mask(img)
    return rect(img.shape, CHAIN)


def run(name, dn, seed):
    import ink_comfy as C
    dst = cand_path(name, dn, seed)
    if os.path.exists(dst):
        return dst
    space, box, k, prompt, _, _ = JOBS[name]
    img = job_src(name)
    m = job_mask(name, img)
    x0, y0, x1, y1 = box
    cw, ch = max(16, int((x1 - x0) * k) // 16 * 16), max(16, int((y1 - y0) * k) // 16 * 16)
    tmp = os.path.join(CAND, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    ci, mi = os.path.join(tmp, f"{name}_crop.png"), os.path.join(tmp, f"{name}_mask.png")
    crop = img[y0:y1, x0:x1].astype(np.uint8)
    mm = nd.binary_dilation(m, iterations=3)
    if name.startswith("p1path"):   # the walkers filled first (Telea), or Krea keeps their ghosts at any denoise
        import cv2
        crop = cv2.inpaint(crop, mm[y0:y1, x0:x1].astype(np.uint8), 25, cv2.INPAINT_TELEA)
    Image.fromarray(crop).resize((cw, ch), Image.LANCZOS).save(ci)
    Image.fromarray((mm[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((cw, ch), Image.NEAREST).save(mi)
    raw = os.path.join(tmp, f"{name}_raw_d{round(dn * 100)}_s{seed}.png")
    C.krea(f"{PRE} {prompt} {STY}", cw, ch, seed, raw, init=ci, denoise=dn, mask=mi)
    back = np.asarray(Image.open(raw).convert("RGB").resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(np.float32)
    if space == "post":
        import ink_post as IP
        back = IP.post(back / 255, offset=(x0, y0)) * 255
    w = feather(nd.binary_dilation(m, iterations=2), 24 if space == "post" else 6)[y0:y1, x0:x1, None]
    out = img.copy()
    out[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - w) + back * w
    save(out, dst)
    return dst


def gpu(only=None):
    import ink_comfy as C
    os.makedirs(CAND, exist_ok=True)
    init = os.path.join(OUT, "_init_p5E2_f1.png")
    for dn, seed in P5_RUNS:
        dst = p5_path(dn, seed)
        if not os.path.exists(dst):
            C.krea(f"{PRE} {P5_PROMPT} {STY}", P5_GEN[0], P5_GEN[1], seed, dst, init=init, denoise=dn)
        print(dst, flush=True)
    for name, spec in JOBS.items():
        if only and name not in only:
            continue
        for dn in spec[4]:
            for s in spec[5]:
                print(run(name, dn, s), flush=True)


# ---------------------------------------------------------------- sheets
def p5_preview(src):
    """The night + cold post at a third of the posted size (a look only)."""
    import ink_post as IP
    import ink_rc_build as B
    im, _ = B.night(np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255, 0.7)
    return IP.post(IP.upscale(im, 1800), light="cold")


def sheet():
    import ink_r5 as R
    tmp = os.path.join(OUT, "_sheet")
    os.makedirs(tmp, exist_ok=True)
    tiles = []
    src0 = os.path.join(OUT, "_init_p5E2_f0.png")
    for f in [src0] + [p5_path(d, s) for d, s in P5_RUNS]:
        if os.path.exists(f):
            p = os.path.join(tmp, "pv_" + os.path.basename(f))
            save(p5_preview(f) * 255 if f != src0 else load(f), p)
            tiles.append(p)
    R.sheet_of(tiles, os.path.join(SB5, "p_sheet_p5.jpg"), cols=2, tw=1200)
    # close crops (gen px): the cressets + lamp, the near-left dead, the near-right dead
    for tag, box in (("lights", (700, 150, 1400, 520)), ("deadL", (0, 520, 520, 1088)), ("deadR", (1500, 520, 2048, 1088))):
        t2 = []
        for f in [src0] + [p5_path(d, s) for d, s in P5_RUNS]:
            if os.path.exists(f):
                p = os.path.join(tmp, f"c_{tag}_" + os.path.basename(f))
                Image.open(f).convert("RGB").crop(box).save(p)
                t2.append(p)
        R.sheet_of(t2, os.path.join(SB5, f"p_sheet_p5_{tag}.jpg"), cols=2, tw=600)
    for name, (space, box, *_r) in JOBS.items():
        t3 = []
        srcf = D2S if name == "p1slab" else P1_BASE
        for f in [srcf] + [cand_path(name, d, s) for d in JOBS[name][4] for s in JOBS[name][5]]:
            if os.path.exists(f):
                p = os.path.join(tmp, f"j_{name}_" + os.path.basename(f))
                Image.open(f).convert("RGB").crop(box).save(p)
                t3.append(p)
        R.sheet_of(t3, os.path.join(SB5, f"p_sheet_{name}.jpg"), cols=3, tw=450)


# ---------------------------------------------------------------- make
def make_p5():
    """PICK p5 None: no re-carve. Every Krea pass (0.30 and 0.40, two seeds; p_sheet_p5*.jpg) redrew the three things
    the plate must keep: the hanging lamp lost its chain (or became a flame on the water), the cressets went back to
    stands, and the drowned turned into hatted villagers with no faces. So the plate is E2 itself (cropped and sized
    as the carve was) and the shared night + cold post (ink_rc_build.build_p5) puts it in the one hand and paper."""
    if PICK["p5"] is None:
        a = load(os.path.join(OUT, "_init_p5E2_f0.png"))
    else:
        a = load(p5_path(*PICK["p5"]))
        if KEEP:
            light = load(p5_path(0.30, 47))
            w = feather(ells(a.shape, KEEP), 8)[..., None]
            a = a * (1 - w) + light * w
    save(a, os.path.join(SB5, "p5e2_sb5.png"))


def make_p1():
    base = load(P1_BASE)
    cand = load(cand_path("p1proc", *PICK["p1proc"]))
    m = poly_mask(base.shape, P1_PROC)
    w = feather(nd.binary_dilation(m, iterations=2), 24)[..., None]
    save(base * (1 - w) + cand * w, os.path.join(LAY, "p1", "base_sb5p.png"))
    t = np.asarray(Image.open(P1_TORCH).convert("RGBA")).astype(np.float32)
    kill = feather(nd.binary_dilation(poly_mask(t.shape, P1_PROC), iterations=30), 20)
    t[..., 3] *= 1 - kill
    Image.fromarray(np.clip(t + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(LAY, "p1", "torches_sb5p.png"))
    print("wrote p1 torches_sb5p.png")


P1D_W = 3300   # posted px = canvas units (1 a px), as p1


def warm(im):
    return np.clip((im[..., 0] - im[..., 2]) / 255 - 0.04, 0, None) / 0.2


def jamb_edge(op):
    """Per row: the right jamb's front-face edge (the end of its lit inner face), ChatGPT px; read off the picture
    (882 at the jamb's top, row 360, leaning out to 897 at the floor, row 740), +2 into the front face."""
    y = np.arange(op.shape[0])
    return 884 + np.clip((y - 360) / 380, 0, 1) * 15


def slab_clone():
    """The shut slab with its chain cloned off (Krea's inpaints came out a flat gray card in another texture): the chain
    band (rows 446-618) from the slab's own stone 86 rows above (its top half) and 86 below (its bottom half), the two
    met along a ragged line (no crossfade blur), feathered 6 rows into the picture at the band's edges."""
    sh = load(D2S)
    a = sh.copy()
    x0, x1, y0, y1 = 600, 885, 446, 618
    n, W = y1 - y0, x1 - x0
    rng = np.random.default_rng(5)
    cut = (n // 2 + nd.gaussian_filter1d(rng.normal(0, 40, W), 6)).clip(20, n - 20)
    top = sh[y0 - 86:y1 - 86, x0:x1]
    bot = sh[y0 + 86:y1 + 86, x0:x1]
    rows = np.arange(n)[:, None]
    wb = np.clip((rows - cut[None, :]) / 3 + 0.5, 0, 1)[..., None]
    band = top * (1 - wb) + bot * wb
    we = np.clip(np.minimum(rows, n - 1 - rows) / 6, 0, 1)[..., None]
    a[y0:y1, x0:x1] = sh[y0:y1, x0:x1] * (1 - we) + band * we
    return a


def make_p1d():
    import ink_post as IP
    op, sh = load(D2), load(D2S)
    H, W = op.shape[:2]
    k = P1D_W / W
    PH = round(H * k)

    def post(a):
        return IP.post(IP.upscale(a / 255, P1D_W, PH), light="warm")

    def up(m):
        return np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize((P1D_W, PH), Image.BILINEAR)).astype(np.float32) / 255

    e = jamb_edge(op)
    xs = np.arange(W)[None, :]
    right = xs >= e[:, None]                                   # the jamb and the rock to its right
    # the doorway gold: warm light inside the opening, on its reveals and the floor spill, left of the jamb edge
    reg = rect(op.shape, (560, 250, 1100, 938)) & ~(right & (np.arange(H)[:, None] < 760))
    gw = np.clip(warm(op), 0, 1) * feather(reg, 12)
    dim = op * (1 - 0.72 * gw[..., None])
    lit_p, dim_p = post(op), post(dim)
    dim_p = np.minimum(dim_p, lit_p)
    gold = np.clip(lit_p - dim_p, 0, 1)
    # the slab: the shut picture's, its chain inpainted off
    sc = slab_clone() if PICK["p1slab"] is None else load(cand_path("p1slab", *PICK["p1slab"]))
    slab_p = post(sc)
    shut_p = post(sh)
    # the shut seams: the shut picture with its gold dimmed, the seams an add layer on top
    sreg = rect(sh.shape, (540, 250, 960, 938))
    sw = np.clip(warm(sh), 0, 1) * feather(sreg, 12)
    sdim_p = np.minimum(post(sh * (1 - 0.6 * sw[..., None])), shut_p)
    seams = np.clip(shut_p - sdim_p, 0, 1)

    def crop_add(col, region):
        col = col * region[..., None]
        nz = col.max(-1) > 1.5 / 255
        ys, xs_ = np.nonzero(nz)
        y0, y1, x0, x1 = max(ys.min() - 4, 0), ys.max() + 5, max(xs_.min() - 4, 0), xs_.max() + 5
        a = nz[y0:y1, x0:x1].astype(np.float32)
        a = np.maximum(a, nd.binary_dilation(a > 0, iterations=2) * 1.0)
        return col[y0:y1, x0:x1], a, x0, y0

    layers = []   # (name, blend, rgb, alpha, x0, y0)
    layers.append(("base", "mix", dim_p, np.ones(dim_p.shape[:2], np.float32), 0, 0))
    layers.append(("gold", "add") + crop_add(gold, np.ones(gold.shape[:2])))
    sx0, sy0, sx1, sy1 = [round(v * k) for v in SLAB]
    layers.append(("slab", "mix", slab_p[sy0:sy1, sx0:sx1], np.ones((sy1 - sy0, sx1 - sx0), np.float32), sx0, sy0))
    # the right jamb in front of the slab (cut from the base: the same pixels, so it never shows by itself)
    jm = up(right & (np.arange(H)[:, None] < 760)) > 0.5
    ys, xs_ = np.nonzero(jm)
    jx0, jy0, jx1, jy1 = xs_.min(), ys.min(), xs_.max() + 1, ys.max() + 1
    layers.append(("jamb", "mix", dim_p[jy0:jy1, jx0:jx1], jm[jy0:jy1, jx0:jx1].astype(np.float32), jx0, jy0))
    # r3: the lintel (its rune face and the lit soffit under it) in front of the slab too: everything above the shut
    # slab's top seam (SLAB_TOP, read off p1_D2_shut), so the slab slides in under it and its top at the hit is the shut
    # picture's; the soffit's gold rides on it as its own add layer (the gold layer's keys)
    ys_, xs__ = np.mgrid[0:PH, 0:P1D_W].astype(np.float32) / k
    lm = (ys_ < SLAB_TOP[0] + (xs__ - SLAB_TOP[1]) * SLAB_TOP[2]) & (ys_ >= 230) & (xs__ >= 595) & (xs__ < 1000)
    ly, lx = np.nonzero(lm)
    lx0, ly0, lx1, ly1 = lx.min(), ly.min(), lx.max() + 1, ly.max() + 1
    la = nd.gaussian_filter(lm[ly0:ly1, lx0:lx1].astype(np.float32), 0.7)
    layers.append(("lintel", "mix", dim_p[ly0:ly1, lx0:lx1], la, lx0, ly0))
    layers.append(("lintel_gold", "add", gold[ly0:ly1, lx0:lx1], la, lx0, ly0))
    # r3: a warm rim on the slab's leading (left) edge, facing the glow: carved (on the stone's light strokes only),
    # 16 units wide (~9 frame px), moved with the slab, dimmed with the gold
    RW = 16
    sl = slab_p[sy0:sy1, sx0:sx0 + RW]
    lum = sl @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    fall = np.clip(1 - (np.arange(RW, dtype=np.float32) - 3) / (RW - 3), 0, 1)[None, :] ** 1.3
    ra = np.clip(fall * (0.35 + 0.65 * np.clip((lum - 0.12) / 0.18, 0, 1)), 0, 1)
    rcol = np.empty(sl.shape, np.float32)
    rcol[:] = np.array([1.0, 0.69, 0.33], np.float32)
    rcol = rcol * (0.55 + 0.45 * fall[..., None])
    layers.append(("rim", "add", rcol, ra, sx0, sy0))
    layers.append(("shut", "mix", sdim_p, np.ones(sdim_p.shape[:2], np.float32), 0, 0))
    layers.append(("seams", "add") + crop_add(seams, np.ones(seams.shape[:2])))
    out = os.path.join(LAY, "p1d")
    os.makedirs(out, exist_ok=True)
    rec = []
    for name, blend, rgb, a, x0, y0 in layers:
        IP.save(rgb, os.path.join(out, name + ".png"), a)
        rec.append(dict(file=name + ".png", name=name, z=1.0, blend=blend, state=None, seed=None, pos=[float(x0), float(y0)],
                        scale=1.0, size_px=[rgb.shape[1], rgb.shape[0]]))
    feats = {"slab": [sx0, sy0, sx1, sy1], "jamb_edge_mid": round(float(e[550]) * k, 1), "k": k,
             "lintel_top": round(LINTEL_TOP * k, 1), "floor": round(745 * k, 1)}
    json.dump(dict(plate="p1d", title="The door shut", source="sb5/p1_D2.png + p1_D2_shut.png (ChatGPT)",
                   canvas_units=[P1D_W, PH], image_px=[P1D_W, PH], units_per_px=1.0, rest=[P1D_W / 2, PH / 2],
                   features=feats, layers=rec), open(os.path.join(out, "layers.json"), "w", encoding="utf-8"), indent=1)
    print("p1d", feats)
    # a look: the open plate, the slab half in, and the shut, at a third
    look = []
    for frac in (1.0, 0.5, 0.0):
        comp = dim_p + gold * (0.35 + 0.65 * frac)
        dx = round((jx0 - sx0) * frac) if frac < 1 else jx0 - sx0
        x = sx0 + dx
        x1 = min(x + (sx1 - sx0), P1D_W)
        comp[sy0:sy1, x:x1] = slab_p[sy0:sy1, sx0:sx0 + (x1 - x)]
        jj = jm[jy0:jy1, jx0:jx1][..., None]
        comp[jy0:jy1, jx0:jx1] = comp[jy0:jy1, jx0:jx1] * (1 - jj) + dim_p[jy0:jy1, jx0:jx1] * jj
        look.append(comp)
    look.append(np.clip(sdim_p + seams, 0, 1))
    th = [Image.fromarray((np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((P1D_W // 4, PH // 4), Image.LANCZOS) for c in look]
    s = Image.new("RGB", (th[0].width * 2 + 8, th[0].height * 2 + 8), "#202020")
    for i, t in enumerate(th):
        s.paste(t, ((i % 2) * (t.width + 8), (i // 2) * (t.height + 8)))
    s.save(os.path.join(SB5, "p_p1d_look.jpg"), quality=88)


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "prep":
        prep()
    elif a == "gpu":
        gpu(sys.argv[2:])
    elif a == "sheet":
        sheet()
    elif a == "make":
        for p in sys.argv[2:] or ["p5", "p1", "p1d"]:
            {"p5": make_p5, "p1": make_p1, "p1d": make_p1d}[p]()
