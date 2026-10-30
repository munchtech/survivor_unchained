"""Ink round 4 (Storybook 3, r2 brief): p6 patches, keeping the drawing.

    python tools/storybook/ink_r4p6.py patch          # CPU: paint out the sky-fill blob (z10, beside the tree), the far2-fill
                                                      #      oval (by the water), the inherited letter in the clean plate
    python tools/storybook/ink_r4p6.py river [seeds]  # GPU: broad Krea inpaint over the river in p6's prompt (gouge-carved,
                                                      #      reflecting the rose band and the blue points), candidates cached
    python tools/storybook/ink_r4p6.py apply SEED     # CPU: that river candidate into S_clean and S_whole (the rest check's whole)
Originals are kept in _work/p6/_r4bak/ (patch restores from them first, so every step re-runs from the same start).
Then `ink_layers.py build p6`.
"""
import os
import shutil
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_layers as L  # noqa: E402

LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
BAK = L.wd("p6", "_r4bak")
SKY_BOX = (1180, 110, 1440, 300)        # gen px: the sky fill's lavender blob behind the big tree (frame 72.0)
FAR_BOX = (1180, 372, 1425, 474)        # the far2 fill's pale oval and smears under the hill's foot (frame 80.5)
LETTER_BOX = (366, 466, 446, 552)       # the sitter's letter and the stick left of it in the clean plate (frame 75.5)
RIVER_SEEDS = (11, 23, 47, 202)
RIVER_DN = 0.78
WALK2_STONE = (1880, 640, 1990, 700)    # gen px: walk2's stepping stone (feet canvas 4201,1461): never repainted
RIVER = ("A wide river at dusk seen from its near bank, the water carved in long horizontal gouge lines, deep blue-black ink "
         "with thin carved strokes reflecting the dull rose band of the sky and broken short glints of cold pale blue light, "
         "flat stones at its edge, dark trees on the far side.")


def ld(name, d=None):
    return np.asarray(Image.open(os.path.join(d or L.wd("p6"), name)).convert("RGB")).astype(np.float32) / 255


def sv(a, name):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(L.wd("p6", name))


def orig(name):
    os.makedirs(BAK, exist_ok=True)
    b = os.path.join(BAK, name)
    if not os.path.exists(b):
        shutil.copy(L.wd("p6", name), b)
    return ld(name, BAK)


def fill_nearest(img, hole, src_ok):
    """Each hole px takes the colour of the nearest src_ok px, then a light blur inside the hole (no hard rim)."""
    _, (iy, ix) = nd.distance_transform_edt(~src_ok, return_indices=True)
    out = img.copy()
    out[hole] = img[iy[hole], ix[hole]]
    bl = np.dstack([nd.gaussian_filter(out[..., c], 1.5) for c in range(3)])
    w = nd.gaussian_filter(hole.astype(np.float32), 1.5)[..., None]
    return out * (1 - w) + bl * w


def box_mask(shape, b, feather=0):
    m = np.zeros(shape, bool)
    m[b[1]:b[3], b[0]:b[2]] = True
    return m


def letter_mask(clean):
    x0, y0, x1, y1 = LETTER_BOX
    reg = clean[y0:y1, x0:x1]
    l = reg @ LUM
    sat = reg.max(-1) - reg.min(-1)
    pale = (l > 0.42) & (sat < 0.25)                        # the blue-white letter
    orange = (reg[..., 0] > 0.45) & (reg[..., 0] > reg[..., 2] + 0.15)
    m = np.zeros(clean.shape[:2], bool)
    lt = nd.binary_dilation(pale, iterations=3)
    # the stick: orange px within 10 px of the letter, above the sack's top (the sack is a wide orange-lit mass)
    near = nd.distance_transform_edt(~lt) <= 26
    stick = orange & near & ~nd.binary_opening(orange, iterations=4)
    m[y0:y1, x0:x1] = nd.binary_dilation(lt | stick, iterations=2)
    return m


def patch():
    sky = orig("S_sky.png")
    Msky = L.load_mask(L.wd("p6", "M_sky.png"))
    H, W = Msky.shape
    x0, y0, x1, y1 = SKY_BOX
    ok = nd.binary_erosion(Msky, iterations=8)          # SAM's sky keeps the tree's rim: never copy from or keep it
    hole = box_mask((H, W), SKY_BOX) & ~ok
    hole |= box_mask((H, W), SKY_BOX) & nd.binary_dilation(hole, iterations=12) & (sky @ LUM < 0.12)   # the blob's outline
    out = sky.copy()
    left = np.zeros((H, W), bool)          # holes with no sky to copy from on their row: nearest sky below
    for y in range(y0, y1):
        for x in np.nonzero(hole[y])[0]:
            sx = x - (x1 - x0)
            while sx > 0 and not ok[y, sx]:
                sx -= 37
            if sx > 0:
                out[y, x] = sky[y, sx]
            else:
                left[y, x] = True
    out = fill_nearest(out, left, ok & ~hole)
    w = nd.gaussian_filter(hole.astype(np.float32), 2.0)[..., None]
    sv(sky * (1 - w) + out * w, "S_sky.png")
    far = orig("S_far2.png")
    Mfar = L.load_mask(L.wd("p6", "M_far.png"))
    fb = box_mask((H, W), FAR_BOX) & ~Mfar
    l = far @ LUM
    pale = fb & (l > 0.1)
    pale = nd.binary_dilation(pale, iterations=3) & fb
    sv(fill_nearest(far, pale, (l <= 0.1) & ~pale), "S_far2.png")
    clean = orig("S_clean.png")
    lm = letter_mask(clean)
    L.save_mask(lm, L.wd("p6", "letter.png"))       # build: the sit state's cut takes the letter (it stays in the reading pose)
    lc = clean @ LUM
    sv(fill_nearest(clean, lm, ~nd.binary_dilation(lm, iterations=2) & (lc < 0.16)), "S_clean.png")
    for f in ("S_whole.png",):
        if os.path.exists(L.wd("p6", f)):
            os.remove(L.wd("p6", f))
    print("patched: sky px", int(hole.sum()), "far2 px", int(pale.sum()), "letter px", int(lm.sum()))


def river_mask():
    rv = L.load_mask(os.path.join(L.WORK, "p6_sam_river.png"))
    H, W = rv.shape
    stones = box_mask((H, W), WALK2_STONE)
    m = nd.binary_erosion(rv, iterations=6) & ~nd.binary_dilation(stones, iterations=8)
    m &= np.arange(W)[None] > 0.6 * W               # the near river right of the hill's foot (the last key's view)
    m = L.clean_comps(m, 2000)
    L.save_mask(m, L.wd("p6", "r4_river_mask.png"))
    return m


def river(seeds):
    import ink_comfy as C
    m = river_mask()
    H, W = m.shape
    for s in seeds:
        dst = L.wd("p6", f"r4_river_s{s}.png")
        if os.path.exists(dst):
            continue
        C.krea(L.full("r2", RIVER + " " + L.P6_CLEAN), W, H, s, L.wd("p6", f"raw_r4_river_s{s}.png"), init=L.wd("p6", "S_clean.png"),
               denoise=RIVER_DN, mask=L.wd("p6", "r4_river_mask.png"))
        L.composite_back(L.wd("p6", "S_clean.png"), L.wd("p6", f"raw_r4_river_s{s}.png"), L.wd("p6", "r4_river_mask.png")).save(dst)
        print("river", s, flush=True)


def apply(seed):
    m = L.load_mask(L.wd("p6", "r4_river_mask.png")).astype(np.float32)
    m = nd.gaussian_filter(m, 1.0) * (m > 0)
    new = ld(f"r4_river_s{seed}.png")
    clean = ld("S_clean.png")
    sv(clean * (1 - m[..., None]) + new * m[..., None], "S_clean.png")
    pk = L.pick("p6")
    sv(pk * (1 - m[..., None]) + new * m[..., None], "S_whole.png")     # the rest check's whole: the pick with this river
    print("river", seed, "applied")


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "patch":
        patch()
    elif a == "river":
        river([int(x) for x in sys.argv[2:]] or RIVER_SEEDS)
    elif a == "apply":
        apply(int(sys.argv[2]))
