"""Storybook 4, sb00-prejudge-fixes: the p3 dawn plate remade in the night plate's hand.

    python tools/storybook/ink_dawn2.py gpu      # fence inpaint, tone to the night, flatten f1, Krea img2img (gpu turn)
    python tools/storybook/ink_dawn2.py sheet    # half-size sheet: the night plate, then the candidates

The old dawn (ink_rc/fix/dawn_i65_s23.png) was another hand (fine hatching, a pale washed sky, a wire fence). Here:
1. the fence and its posts inpainted to frosted field and hedge (crop x2, masked Krea);
2. its lightness pulled toward the night plate's (luminance histogram match, blended 0.65, hue kept) so the sky is
   gray, not white, and the blacks are heavy;
3. the same flatten f1 (ink_recarve.flatten) and Krea img2img at 0.40/0.45 x 2 seeds with the p3 prompt turned to
   dawn. Same gen size (2432x896) so ink_layers' rest/upp registration holds. Outputs out/ink_rc/dawn2/.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_recarve as RC  # noqa: E402

OUT = os.path.join(RC.OUT, "dawn2")
SRC = os.path.join(RC.OUT, "fix", "dawn_i65_s23.png")
NIGHT = os.path.join(RC.OUT, "fix", "p3dead_d65_s11.png")
PRE, STY = RC.R2["prefix"], RC.R2["style"]
FENCE_BOX = (1700, 240, 2432, 620)                        # gen px crop for the fence inpaint
FENCE_RECTS = [(1740, 330, 1955, 578), (2025, 330, 2432, 578)]   # the fence's posts + wire, the trunk left alone
FENCE_PROMPT = ("Gray dawn. An open pale frosted winter field carved in long horizontal gouge strokes, pale gray-blue "
                "frost, tufts of dry winter grass in black ink at its near edge, a low dark hedge far behind. No "
                "fence, no posts, no wire.")
DAWN_PROMPT = (
    "A shadow puppet theatre frieze in carved black ink. Gray first light of dawn on a frozen field beside a rutted "
    "dirt road, low dark hills under a heavy gray sky carved in long sweeping gouge lines, one thin band of dull gold "
    "light along the hills. Center an old Watch soldier with a gray beard, a long slate blue-gray wool cloak and "
    "tabard, a round wooden shield on his arm and a small iron oil lamp at his belt, its flame guttering low, stands "
    "tired and leans on his long upright spear planted in the ground, head bowed; his breath smokes white in the cold. "
    "At left a gaunt dead man in a torn ragged tunic lies fallen flat on his back on the frost, plain dead, dark. At "
    "his feet a second dead man lies fallen face down on the frost, dark and empty; a few dull gray dead stones. At "
    "right a bare winter tree and a low dark hedge. The ember is gone dull: no orange glow, the dead never breathe. "
    "The frost and field are carved in long gouge strokes, pale gray-blue; large masses of solid black. Everything is "
    "black, slate and deep blue-black ink; the only warm color is the thin gold band and the small lamp flame.")
SEEDS = (47, 11)
DENOISE = (0.40, 0.45)


def fence_out(dn=0.9, seed=47):
    import ink_comfy as C
    dst = os.path.join(OUT, "_nofence.png")
    if os.path.exists(dst):
        return dst
    img = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
    m = Image.new("L", (img.shape[1], img.shape[0]), 0)
    d = ImageDraw.Draw(m)
    for r in FENCE_RECTS:
        d.rectangle(r, fill=255)
    m = np.asarray(m) > 127
    w = np.clip(nd.distance_transform_edt(m) / 30, 0, 1)
    x0, y0, x1, y1 = FENCE_BOX
    k = 2
    cw, ch = (x1 - x0) * k // 16 * 16, (y1 - y0) * k // 16 * 16
    ci, mi, raw = (os.path.join(OUT, f) for f in ("_fence_crop.png", "_fence_mask.png", "_fence_raw.png"))
    Image.fromarray(img[y0:y1, x0:x1].astype(np.uint8)).resize((cw, ch), Image.LANCZOS).save(ci)
    Image.fromarray((m[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((cw, ch), Image.NEAREST).save(mi)
    C.krea(f"{PRE} {FENCE_PROMPT} {STY}", cw, ch, seed, raw, init=ci, denoise=dn, mask=mi)
    back = np.asarray(Image.open(raw).convert("RGB").resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(np.float32)
    out = img.copy()
    ww = w[y0:y1, x0:x1, None]
    out[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - ww) + back * ww
    Image.fromarray((out + 0.5).astype(np.uint8)).save(dst)
    return dst


def toned(src, blend=0.65):
    """Lightness toward the night plate's (histogram match on mean RGB, blended), each pixel scaled so hue holds."""
    dst = os.path.join(OUT, "_toned.png")
    a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255
    n = np.asarray(Image.open(NIGHT).convert("RGB")).astype(np.float32).mean(-1) / 255
    l = a.mean(-1)
    order = np.argsort(l, axis=None)
    q = np.empty(l.size, np.float32)
    ns = np.sort(n, axis=None)
    q[order] = ns[np.linspace(0, ns.size - 1, l.size).astype(np.int64)]
    m = q.reshape(l.shape)
    t = blend * m + (1 - blend) * l
    out = np.clip(a * (t / np.maximum(l, 1e-4))[..., None], 0, 1)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(dst)
    return dst


def gpu():
    import ink_comfy as C
    os.makedirs(OUT, exist_ok=True)
    nf = fence_out()
    tn = toned(nf)
    bgr = np.asarray(Image.open(tn).convert("RGB"))[..., ::-1].copy()
    rgb, _ = RC.flatten(bgr, "f1")
    init = os.path.join(OUT, "_init_f1.png")
    Image.fromarray(rgb).save(init)
    for dn in DENOISE:
        for s in SEEDS:
            dst = os.path.join(OUT, f"dawn2_d{round(dn * 100)}_s{s}.png")
            if not os.path.exists(dst):
                C.krea(f"{PRE} {DAWN_PROMPT} {STY}", 2432, 896, s, dst, init=init, denoise=dn)
            print(dst, flush=True)


def sheet():
    import ink_rc_build as B
    import ink_layers as L
    P = dict(L.PLATES["p3d"])
    tiles = [NIGHT, os.path.join(OUT, "_init_f1.png")] + [os.path.join(OUT, f"dawn2_d{round(d * 100)}_s{s}.png")
                                                          for d in DENOISE for s in SEEDS]
    ims = []
    for f in tiles:
        im = np.asarray(Image.open(f).convert("RGB").resize((1216, 448), Image.LANCZOS)).astype(np.float32) / 255
        if "dawn2_" in f or f == NIGHT:   # posted, as the plate shows it
            im = B.IP.post(im, light=P["light"])
        ims.append((np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8))
    cols = 2
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (1216 * cols, 448 * rows), (20, 20, 20))
    for i, im in enumerate(ims):
        sh.paste(Image.fromarray(im), ((i % cols) * 1216, (i // cols) * 448))
    p = os.path.join(OUT, "dawn2_sheet_half.jpg")
    sh.save(p, quality=88)
    print(p)


if __name__ == "__main__":
    {"gpu": gpu, "sheet": sheet}[sys.argv[1]]()
