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
    """Per column, the top of the dark hill band: the first row (from 15% height) where the heavily blurred
    luminance drops under 0.125; median-smoothed across x so the risen heads in the sky don't pull it up."""
    L = nd.gaussian_filter(rgb.mean(-1), 12)
    H, W = L.shape
    below = L < 0.125
    below[: int(H * 0.15)] = False
    y = np.where(below.any(0), below.argmax(0), int(H * 0.28))
    y = np.clip(y, int(H * 0.18), int(H * 0.42))
    return nd.uniform_filter1d(nd.median_filter(y, 301).astype(np.float32), 151)


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
    field = np.clip(field, 0, 1) ** 0.62 * np.array([0.96, 0.99, 1.03])
    # sky: gray, lighter toward the hills, a gold band just above them
    t = np.clip(1 - (hy[None] - yy) / np.maximum(hy[None], 1), 0, 1)[..., None]   # 0 at the top, 1 at the hill line
    skyc = np.clip(gray * 0.6 + 0.30 + 0.18 * t, 0, 1) * np.array([0.95, 0.97, 1.0])
    band = np.exp(-((hy[None] - yy) / 48.0) ** 2)[..., None] * (yy <= hy[None] + 4)[..., None]
    gold = np.array([0.90, 0.70, 0.38])
    skyc = skyc * (1 - 0.9 * band) + gold * (0.75 + 0.35 * gray) * 0.9 * band
    s = sky[..., None]
    return np.clip(field * (1 - s) + skyc * s, 0, 1)


def fig_mask(src, shape):
    """Tight figure masks: SAM 'person' on the night plate (dilated), kept inside REGIONS' upper boxes, plus a
    ground ellipse per region where the fallen will lie."""
    import ink_comfy as C
    sp = os.path.join(D, "_sam_person.png")
    if not os.path.exists(sp):
        C.sam(src, "person", sp, threshold=0.3)
    sam = np.asarray(Image.open(sp).convert("L").resize((shape[1], shape[0]))) > 127
    box = np.zeros(shape[:2], bool)
    for (x0, y0, x1, y1), _ in REGIONS:
        box[y0:y1, x0:x1] = True
    m = nd.binary_dilation(sam & box, iterations=28)
    g = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(g)
    for cx, cy, rx, ry in GROUND:
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    return m | (np.asarray(g) > 127)


GROUND = [(680, 770, 380, 95), (1640, 785, 360, 85)]   # gen px: where the two fallen lie


def soft_back(init, fill, mask, feather=24):
    """The fill inside the mask, blended over `feather` px just inside its edge; outside the mask the init exactly."""
    a = np.asarray(Image.open(init).convert("RGB")).astype(np.float32)
    b = np.asarray(Image.open(fill).convert("RGB").resize((a.shape[1], a.shape[0]), Image.LANCZOS)).astype(np.float32)
    m = np.asarray(Image.open(mask).convert("L")) > 127
    w = np.clip(nd.distance_transform_edt(m) / feather, 0, 1)
    return Image.fromarray((a * (1 - w[..., None]) + b * w[..., None] + 0.5).astype(np.uint8))


def dawn(name):
    import ink_comfy as C
    import ink_layers as IL
    import ink_r5 as R
    os.makedirs(D, exist_ok=True)
    src = os.path.join(RC.OUT, name + ".png")
    night = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255
    H, W = night.shape[:2]
    base = os.path.join(D, f"{name}_base.png")                 # the whole plate regraded, pixel-registered
    Image.fromarray((regrade(night) * 255 + 0.5).astype(np.uint8)).save(base)
    m = mask(night.shape)          # the region boxes (SAM 'person' finds only the standing dead here)
    # above the hill line only the night figures' own dark silhouettes (sky and the gold band stay the base's)
    hy = hill_line(night)
    yy = np.arange(H)[:, None]
    dark = nd.binary_dilation(nd.gaussian_filter(night.mean(-1), 4) < 0.13, iterations=22)
    m &= (yy >= hy[None] + 18) | dark
    m = nd.binary_opening(m, iterations=3)
    mp = os.path.join(D, "_mask4.png")
    Image.fromarray((m * 255).astype(np.uint8)).save(mp)
    prompt = (RC.R2["prefix"] + " " + INPAINT + " " + RC.R2["style"]).strip()
    rp = (RC.R2["prefix"] + " " + REGRADE + " " + RC.R2["style"]).strip()
    posted = [os.path.join(RC.OUT, "posted", name + ".png")]
    p = os.path.join(D, "posted_" + os.path.basename(base))
    R.post_one(base, p, w=5400)
    posted.append(p)
    for s in SEEDS:
        n = os.path.join(D, f"{name}_dawn4_{s}_n.png")
        if not os.path.exists(n):
            raw = os.path.join(D, f"_raw4_{s}.png")
            C.krea(prompt, W, H, s, raw, init=base, denoise=1.0, mask=mp)
            soft_back(base, raw, mp).save(n)
        outs = [n]
        if s == SEEDS[0]:
            k = os.path.join(D, f"{name}_dawn4_{s}_k25.png")
            if not os.path.exists(k):
                C.krea(rp, W, H, s, k, init=n, denoise=0.25)
            outs.append(k)
        for g in outs:
            p = os.path.join(D, "posted_" + os.path.basename(g))
            R.post_one(g, p, w=5400)
            posted.append(p)
        print(s, flush=True)
    R.sheet_of(posted, os.path.join(RC.OUT, f"{name}_dawn4_sheet_half.jpg"), cols=3, tw=900)
