"""p3 dawn state from the chosen re-carved night plate (ink_recarve.py dawn <name>), registered on the night plate.

1. Krea inpaint at full denoise inside two figure regions (gen px, from the p3_N1 layout): the standing dead ->
   lying fallen where he stood; the Watchman + speared dead -> the Watchman leaning on his spear, the dead at his
   feet. composite_back: outside the (1 px feathered) mask the night pixels exactly.
2. Dawn regrade, two ways: (n) numeric (pixel-exact registration: sky lifted to gray with a gold band along the
   hill line, ember orange drained to dark ash, the field lifted and cooled); (k) Krea img2img 0.30 on (n).
Outputs out/ink_rc/dawn/<name>_dawn_<seed>_{n,k}.png (gen) + posted, and a sheet beside the posted night plate.
"""
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

import ink_recarve as RC

D = os.path.join(RC.OUT, "dawn")
# gen px (2432x896): region boxes + their ground bands (the fallen lie wider than the standing)
REGIONS = [[(500, 40, 850, 790), (360, 600, 980, 860)],          # the standing dead -> fallen on the frost
           [(930, 60, 2010, 740), (930, 520, 2060, 860)]]        # the Watchman + speared dead -> leaning; dead at his feet
SEEDS = (11, 23, 31)
INPAINT = (
    "Gray first light of dawn on a frozen field beside a rutted dirt road. On the frost a gaunt dead man in a torn ragged "
    "tunic lies fallen flat on his back, plain dead, dark, no light in him. An old Watch soldier with a gray beard, a long "
    "slate blue-gray wool cloak and tabard, a round wooden shield slung on his arm, stands tired and leans with both "
    "hands on his long upright spear planted in the ground, head bowed, a small iron oil lamp at his belt guttering low. "
    "At his feet a second dead man lies fallen face down on the frost, dark and empty; a few dull gray dead stones on the "
    "frost. The frost carved in long gouge strokes, pale gray-blue; large masses of solid black.")
REGRADE = (
    "Dawn on the same frozen field: a pale gray sky carved in long sweeping gouge lines with one thin band of gold light "
    "along the low hills, the frost pale gray, the dead lying on the frost, the soldier leaning on his spear. No ember, "
    "no orange glow; cold gray morning, black ink shapes.")


def mask(shape):
    m = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(m)
    for boxes in REGIONS:
        for b in boxes:
            d.rounded_rectangle(b, 40, fill=255)
    return np.asarray(m) > 127


def hill_line(rgb):
    """Per column, the first row (below 4% height) where the blurred luminance drops under 60% of the sky's."""
    L = nd.gaussian_filter(rgb.mean(-1), 4)
    H, W = L.shape
    sky = np.median(L[: int(H * 0.08)])
    below = L < sky * 0.6
    below[: int(H * 0.04)] = False
    y = np.where(below.any(0), below.argmax(0), int(H * 0.3))
    y = np.clip(y, int(H * 0.08), int(H * 0.5))
    return nd.median_filter(y, 61).astype(np.float32)


def regrade(rgb):
    H, W = rgb.shape[:2]
    hy = hill_line(rgb)
    yy = np.arange(H, dtype=np.float32)[:, None]
    sky = np.clip((hy[None] - yy) / 6 + 0.5, 0, 1)                     # 1 above the hill line
    out = rgb.copy()
    lum = rgb.mean(-1, keepdims=True)
    # ember drained: warm pixels -> dark ash
    warm = np.clip((rgb[..., 0] - rgb[..., 2] - 0.08) / 0.15, 0, 1)[..., None]
    out = out * (1 - warm) + (lum * 0.55 + np.array([0.06, 0.065, 0.075])) * warm
    # field: lifted and cooled to a gray morning
    gray = out.mean(-1, keepdims=True)
    field = 0.55 * out + 0.45 * gray
    field = np.clip(field * 1.3 + 0.03, 0, 1) * np.array([0.97, 1.0, 1.04])
    # sky: gray, lighter toward the hills, a gold band just above them
    t = np.clip(1 - (hy[None] - yy) / np.maximum(hy[None], 1), 0, 1)[..., None]   # 0 at the top, 1 at the hill line
    skyc = np.clip(gray * 0.6 + 0.30 + 0.18 * t, 0, 1) * np.array([0.95, 0.97, 1.0])
    band = np.exp(-((hy[None] - yy) / 28.0) ** 2)[..., None] * (yy <= hy[None] + 4)[..., None]
    gold = np.array([0.90, 0.70, 0.38])
    skyc = skyc * (1 - 0.75 * band) + gold * (0.55 + 0.45 * gray) * 0.75 * band
    s = sky[..., None]
    return np.clip(field * (1 - s) + skyc * s, 0, 1)


def dawn(name):
    import ink_comfy as C
    import ink_layers as IL
    import ink_r5 as R
    os.makedirs(D, exist_ok=True)
    src = os.path.join(RC.OUT, name + ".png")
    night = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255
    m = mask(night.shape)
    mp = os.path.join(D, "_mask.png")
    Image.fromarray((m * 255).astype(np.uint8)).save(mp)
    prompt = (RC.R2["prefix"] + " " + INPAINT + " " + RC.R2["style"]).strip()
    rp = (RC.R2["prefix"] + " " + REGRADE + " " + RC.R2["style"]).strip()
    H, W = night.shape[:2]
    posted = []
    for s in SEEDS:
        fig = os.path.join(D, f"{name}_fig_{s}.png")
        if not os.path.exists(fig):
            raw = os.path.join(D, f"_raw_{s}.png")
            C.krea(prompt, W, H, s, raw, init=src, denoise=1.0, mask=mp)
            IL.composite_back(src, raw, mp).save(fig)
        f = np.asarray(Image.open(fig).convert("RGB")).astype(np.float32) / 255
        n = os.path.join(D, f"{name}_dawn_{s}_n.png")
        Image.fromarray((regrade(f) * 255 + 0.5).astype(np.uint8)).save(n)
        k = os.path.join(D, f"{name}_dawn_{s}_k.png")
        if not os.path.exists(k):
            C.krea(rp, W, H, s, k, init=n, denoise=0.30)
        for g in (n, k):
            p = os.path.join(D, "posted_" + os.path.basename(g))
            R.post_one(g, p, w=5400)
            posted.append(p)
        print(s, flush=True)
    R.sheet_of([os.path.join(RC.OUT, "posted", name + ".png")] + posted, os.path.join(RC.OUT, f"{name}_dawn_sheet_half.jpg"),
               cols=3, tw=900)
