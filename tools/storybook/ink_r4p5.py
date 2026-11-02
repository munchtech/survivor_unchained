"""Ink round 4 (Storybook 3, r2 brief): p5 regenerated in p6's hand.

The base: ink_jobs/r4_p5.json job p5c50 (img2img at 0.5 over round 3's clean plate quantized and darkened to the night
inks, so the ditch geometry ink_r3 knows holds; the bold linocut hand of p6's prompt). Then:

    python tools/storybook/ink_r4p5.py cart [seeds]    # GPU: the wagon overturned on its side (broad-mask Krea inpaint)
    python tools/storybook/ink_r4p5.py base SEED       # CPU: out/ink_r4/p5_base.png = BASE + that wagon, snow dimmed to
                                                       #      moonlit blue-gray, the cages inked black (fire between bars)
    python tools/storybook/ink_r4p5.py prep            # GPU: MoGe depth + SAM masks of the base (the ink_layers inputs)
then `ink_layers.py masks p5`, `fills p5`, `ink_r3.py init|gen|sheet`, `ink_layers.py build p5`, and
    python tools/storybook/ink_r4p5.py sheet [TAG]     # CPU: the one pick sheet (rest + 1:1 wide-key crop + runners-up)
    python tools/storybook/ink_r4p5.py share           # CPU: black/navy share of p5's and p6's posted wholes
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_layers as L  # noqa: E402

R4 = os.path.join(HERE, "out", "ink_r4")
BASE = os.path.join(R4, "p5c50_s202.png")
OUT_BASE = os.path.join(R4, "p5_base.png")
CART_BOX = (600, 470, 1100, 750)       # gen px: the wagon on the road (broad elliptical mask)
CART_SEEDS = (11, 23, 47, 202)
CART_DN = 0.92
CART = ("On the road in the middle ground a big wooden farm wagon lies overturned on its side across the road, its bed tipped "
        "up toward us, one big spoked wheel up in the air, the other wheels on the ground, carved as bold black shapes with "
        "thin pale moonlit edges.")
LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
STEM = (1336, 419, 1353, 463)   # gen px: the post under the fourth cage (it hangs: the post goes, the rings stay)
SNOW_MAX = 0.42        # the snow's lightness cap (moonlit blue-gray, not paper): the snow ink 687c8e is 0.47
SNOW_HUE = np.array([0.80, 0.92, 1.12], np.float32)


def prompt():
    j = [x for x in json.load(open(os.path.join(HERE, "ink_jobs", "r4_p5.json"), encoding="utf-8"))["jobs"] if x["name"] == "p5c50"][0]
    return j["prompt"]


def full(p):
    return (p + " " + json.load(open(os.path.join(HERE, "ink_jobs", "r4_p5.json"), encoding="utf-8"))["style"]).strip()


def ellipse(shape, box):
    H, W = shape
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).ellipse(box, fill=255)
    return np.asarray(im) > 127


def cart(seeds):
    import ink_comfy as C
    img = Image.open(BASE)
    W, H = img.size
    m = ellipse((H, W), CART_BOX)
    mp = os.path.join(R4, "_cart_mask.png")
    L.save_mask(m, mp)
    p = prompt().replace("On the road in the middle ground a wooden wagon lies overturned on its side, one wheel in the air.", CART)
    for s in seeds:
        dst = os.path.join(R4, f"p5_cart_s{s}.png")
        if os.path.exists(dst):
            continue
        raw = os.path.join(R4, f"_raw_cart_s{s}.png")
        C.krea(full(p), W, H, s, raw, init=BASE, denoise=CART_DN, mask=mp)
        L.composite_back(BASE, raw, mp).save(dst)
        print("cart", s, flush=True)


def flames(a):
    l = a @ LUM
    return (a[..., 2] > 0.72) & (l > 0.55) & (a[..., 2] > a[..., 0] + 0.06)


def base(seed):
    src = os.path.join(R4, f"p5_cart_s{seed}.png") if seed else BASE
    a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255
    H, W = a.shape[:2]
    l = a @ LUM
    yy = np.arange(H)[:, None] * np.ones((1, W))
    # the fire: bright blue px in the cages' band (the ford, y 0.25-0.5 H) and their reflections; the rest of the
    # light is snow and goes down to a dim moonlit blue-gray
    cages = L.load_mask(os.path.join(R4, "_cages.png")) if os.path.exists(os.path.join(R4, "_cages.png")) else np.zeros((H, W), bool)
    fire = (flames(a) | (cages & (l > 0.45))) & (yy < 0.55 * H)
    fire = nd.binary_dilation(fire, iterations=1)
    k = np.minimum(1.0, SNOW_MAX / np.maximum(l, 1e-6))
    snow = a * k[..., None]
    snow = np.where((l > 0.3)[..., None], np.clip(snow * SNOW_HUE, 0, 1), snow)
    out = np.where(fire[..., None], a, snow)
    x0, y0, x1, y1 = STEM            # each row of the post: the water a little left and right of it, blended
    for y in range(y0, y1):
        lft, rgt = out[y, x0 - 12:x0 - 4].mean(0), out[y, x1 + 4:x1 + 12].mean(0)
        t = np.linspace(0, 1, x1 - x0)[:, None]
        out[y, x0:x1] = lft * (1 - t) + rgt * t
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT_BASE)
    print("base", src, "fire px", int(fire.sum()), "->", OUT_BASE)


def prep():
    import ink_comfy as C
    w = lambda n: os.path.join(L.WORK, f"p5_{n}")
    C.depth(OUT_BASE, w("depth.png"))
    C.sam(OUT_BASE, "wooden cart", w("sam_wooden_cart.png"))
    C.sam(OUT_BASE, "tree", w("t_tree.png"), 0.3)
    C.sam(OUT_BASE, "iron fire basket on a post", w("sam_iron_fire_basket_on_a_post.png"))
    print("prep done")


def share():
    """Black / navy share (ink index after ink_post's quantize) of p5's and p6's posted wholes."""
    import ink_post as IP
    names = list(IP.INKS)
    for p in ("p5", "p6"):
        a = np.asarray(Image.open(os.path.join(L.OUT, p, "_posted_whole.png")).convert("RGB")).astype(np.float32) / 255
        a = a[::2, ::2]
        idx = IP.quantize(a)
        sh = {n: float((idx == i).mean()) for i, n in enumerate(names)}
        print(p, " ".join(f"{n} {sh[n]:.2f}" for n in ("black", "navy", "slate", "snow", "parchment", "cage")),
              f"black+navy {sh['black'] + sh['navy']:.2f}")


def sheet(runners=("d65_s11", "d65_s23")):
    """One half-size sheet: the pick at rest, the 1:1 crop at its wide key, the runners-up as thumbnails."""
    import ink_r3 as R3
    pick = L.P5_DROWNED_R3
    rest = Image.open(os.path.join(L.OUT, "p5", "_posted_whole.png")).convert("RGB")
    W = 1800
    r0 = rest.resize((W, round(rest.height * W / rest.width)), Image.LANCZOS)
    R3.crop(pick)
    c = Image.open(os.path.join(L.OUT, f"crop_p5_r3_{pick}_wide.png")).convert("RGB").crop((0, 0, 960, 1080))  # left half, 1:1
    c2 = Image.open(os.path.join(L.OUT, f"crop_p5_r3_{pick}_wide.png")).convert("RGB").crop((960, 0, 1920, 1080))
    th = []
    for t in runners:
        im = Image.open(L.wd("p5", f"S_drowned_r3_{t}.png")).convert("RGB")
        th.append(im.resize((W // 2 - 4, round(im.height * (W // 2 - 4) / im.width)), Image.LANCZOS))
    H = r0.height + 4 + 1080 + 4 + th[0].height
    S = Image.new("RGB", (W, H), (20, 20, 20))
    S.paste(r0, (0, 0))
    S.paste(c.resize((W // 2 - 2, round(1080 * (W // 2 - 2) / 960))).crop((0, 0, W // 2 - 2, 1080)), (0, r0.height + 4))
    S.paste(c2.resize((W // 2 - 2, round(1080 * (W // 2 - 2) / 960))).crop((0, 0, W // 2 - 2, 1080)), (W // 2 + 2, r0.height + 4))
    for i, im in enumerate(th):
        S.paste(im, (i * (W // 2 + 2), r0.height + 1088))
    d = ImageDraw.Draw(S)
    for xy, t in [((8, 6), f"p5 r4 pick {pick} at rest (posted whole)"), ((8, r0.height + 10), "1:1 at the wide key (left | right half)"),
                  ((8, r0.height + 1094), "runners-up: " + ", ".join(runners))]:
        d.rectangle([xy[0] - 4, xy[1] - 2, xy[0] + 7 * len(t), xy[1] + 12], fill=(0, 0, 0))
        d.text(xy, t, fill=(255, 230, 120))
    S = S.resize((W // 2, H // 2), Image.LANCZOS)
    p = os.path.join(L.OUT, "sheet_p5_r4_half.jpg")
    S.save(p, quality=86)
    print(p)


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "cart":
        cart([int(x) for x in sys.argv[2:]] or CART_SEEDS)
    elif a == "base":
        base(int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    elif a == "prep":
        prep()
    elif a == "share":
        share()
    elif a == "sheet":
        # re-pick: python ink_r4p5.py sheet [runner tags]; the pick is ink_layers.P5_DROWNED_R3 (set it, build p5, sheet)
        sheet(tuple(sys.argv[2:]) or ("d65_s11", "d65_s23"))
