"""Storybook 4, sb00-p3p5-build: local fixes on the re-carved p3/p5 sources (gen px), before the post.

    python tools/storybook/ink_rc_fix.py gpu      # Krea inpaints (cached): p3 the standing dead's inner light,
                                                  # p5 the wagon and the cages, p3 dawn candidates
    python tools/storybook/ink_rc_fix.py sheet    # crops of the candidates (half size) for the pick

Each local fix crops a box around its subject, upscales it x3, inpaints there (more detail), downscales and puts it
back only inside its feathered mask. Outputs out/ink_rc/fix/.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_recarve as RC  # noqa: E402

FIX = os.path.join(RC.OUT, "fix")
P3 = os.path.join(RC.OUT, "p3N1_f1_d40_s47.png")
P5 = os.path.join(RC.OUT, "p5R1_f1_d40_s47.png")
PRE, STY = RC.R2["prefix"], RC.R2["style"]

# (name, src, crop box gen px, ellipses (cx, cy, rx, ry) gen px, prompt, denoise list, seeds)
LOCAL = [
    ("p3dead", P3, (500, 30, 820, 430), [(635, 128, 62, 60), (662, 250, 100, 85)],
     "Night. A gaunt dead man standing, torn ragged tunic, face blank and slack, not a skull. Ember orange light "
     "burns inside him and shows only at his open slack mouth, in his two empty dark eye sockets and through the "
     "torn wounds in his chest, like a lamp behind paper: small bold orange carved marks inside the black. "
     "The rest of him black ink and dim slate blue.", (0.55, 0.65), (11, 47)),
    ("p5wagon", P5, (520, 500, 1120, 840), [(640, 570, 110, 60), (820, 690, 300, 120), (1000, 760, 140, 70)],
     "Night, snow. A heavy wooden farm wagon lying on its side across a rutted road, one big spoked wheel up in the "
     "air, its planks and wheel carved in pale frosted blue-gray lines against black, a clear readable shape.",
     (0.45, 0.55), (11, 47)),
    ("p5cages", P5, (720, 380, 1330, 560), [(783, 474, 36, 28), (897, 452, 36, 28), (1267, 477, 36, 28)],
     "Night. Crude black iron fire baskets on short posts, rough uneven forged iron bars, blacksmith work, cold blue "
     "fire inside.", (0.40, 0.50), (11, 47)),
]


def ell_mask(shape, ells, feather=10):
    m = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(m)
    for cx, cy, rx, ry in ells:
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    m = np.asarray(m) > 127
    return m, np.clip(nd.distance_transform_edt(m) / feather, 0, 1)


def local(name, src, box, ells, prompt, dn, seed):
    import ink_comfy as C
    dst = os.path.join(FIX, f"{name}_d{round(dn * 100)}_s{seed}.png")
    if os.path.exists(dst):
        return dst
    img = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    x0, y0, x1, y1 = box
    k = 3
    cw, ch = (x1 - x0) * k // 16 * 16, (y1 - y0) * k // 16 * 16
    crop = Image.fromarray(img[y0:y1, x0:x1].astype(np.uint8)).resize((cw, ch), Image.LANCZOS)
    ci = os.path.join(FIX, f"_{name}_crop.png")
    crop.save(ci)
    m, w = ell_mask(img.shape, ells)
    mc = Image.fromarray((m[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((cw, ch), Image.NEAREST)
    mi = os.path.join(FIX, f"_{name}_mask.png")
    mc.save(mi)
    raw = os.path.join(FIX, f"_{name}_raw_{seed}_{round(dn * 100)}.png")
    C.krea(f"{PRE} {prompt} {STY}", cw, ch, seed, raw, init=ci, denoise=dn, mask=mi)
    back = np.asarray(Image.open(raw).convert("RGB").resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(np.float32)
    out = img.copy()
    ww = w[y0:y1, x0:x1, None]
    out[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - ww) + back * ww
    Image.fromarray((out + 0.5).astype(np.uint8)).save(dst)
    return dst


# ---------------------------------------------------------------- p3 dawn (its own plate after a hard cut)
DAWN_SRC = os.path.join(RC.OUT, "dawn", "p3N1_f1_d40_s47_dawn_23_n.png")   # seed 23's figures (round 1), boxed
DAWN_PROMPT = (
    "Gray first light of dawn on a frozen field beside a rutted dirt road, low dark hills, a pale gray sky carved in "
    "long sweeping gouge lines with one thin band of gold light along the hills. On the frost a gaunt dead man in a "
    "torn ragged tunic lies fallen flat on his back, plain dead, dark. An old Watch soldier with a gray beard, a long "
    "slate blue-gray wool cloak and tabard, a round wooden shield slung on his arm, stands tired and leans with both "
    "hands on his long upright spear planted in the ground, head bowed, a small iron oil lamp at his belt guttering "
    "low. At his feet a second dead man lies fallen face down on the frost, dark and empty; a few dull gray dead "
    "stones on the frost. No ember, no orange glow; cold gray morning, the frost carved in long gouge strokes, pale "
    "gray-blue; large masses of solid black.")


def dawn_init():
    """seed 23's dawn with the boxes' low frequencies carried outward: outside the inpaint boxes the plate's local
    mean colour is pulled to the boxes' (normalised convolution), fading over ~250 gen px, so an img2img over it has no
    tonal block to keep."""
    import ink_recarve_dawn as D
    dst = os.path.join(FIX, "_dawn_init.png")
    if os.path.exists(dst):
        return dst
    a = np.asarray(Image.open(DAWN_SRC).convert("RGB")).astype(np.float32)
    m = D.mask(a.shape).astype(np.float32)
    s = 70
    def nc(v, w):
        return nd.gaussian_filter(v * w, s) / np.maximum(nd.gaussian_filter(w, s), 1e-3)
    inside = np.dstack([nc(a[..., c], m) for c in range(3)])
    outside = np.dstack([nc(a[..., c], 1 - m) for c in range(3)])
    dist = nd.distance_transform_edt(m < 0.5)
    t = np.clip(1 - dist / 250, 0, 1)[..., None] * (1 - m[..., None])
    out = a + t * (inside - outside)
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(dst)
    return dst


def dawn_jobs():
    import ink_comfy as C
    init = dawn_init()
    out = []
    for dn, seed in ((0.55, 23), (0.65, 23), (0.65, 47)):
        dst = os.path.join(FIX, f"dawn_i{round(dn * 100)}_s{seed}.png")
        if not os.path.exists(dst):
            C.krea(f"{PRE} {DAWN_PROMPT} {STY}", 2432, 896, seed, dst, init=init, denoise=dn)
        out.append(dst)
    for seed in (23, 47):
        dst = os.path.join(FIX, f"dawn_t2i_s{seed}.png")
        if not os.path.exists(dst):
            C.krea(f"{PRE} {DAWN_PROMPT} {STY}", 2432, 896, seed, dst)
        out.append(dst)
    return out


def gpu():
    os.makedirs(FIX, exist_ok=True)
    for name, src, box, ells, prompt, dns, seeds in LOCAL:
        for dn in dns:
            for s in seeds:
                print(local(name, src, box, ells, prompt, dn, s), flush=True)
    for p in dawn_jobs():
        print(p, flush=True)


def sheet():
    import ink_r5 as R
    tiles = []
    for name, src, box, ells, prompt, dns, seeds in LOCAL:
        x0, y0, x1, y1 = box
        fs = [src] + [os.path.join(FIX, f"{name}_d{round(d * 100)}_s{s}.png") for d in dns for s in seeds]
        for f in fs:
            p = os.path.join(FIX, "_c_" + name + "_" + os.path.basename(f))
            Image.open(f).convert("RGB").crop(box).save(p)
            tiles.append(p)
    R.sheet_of(tiles, os.path.join(FIX, "local_sheet.jpg"), cols=5, tw=360)
    R.sheet_of([dawn_init()] + sorted(os.path.join(FIX, f) for f in os.listdir(FIX) if f.startswith("dawn_")),
               os.path.join(FIX, "dawn_sheet.jpg"), cols=3, tw=640)


if __name__ == "__main__":
    {"gpu": gpu, "sheet": sheet}[sys.argv[1]]()
