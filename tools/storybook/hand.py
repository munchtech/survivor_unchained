"""The storybook's own hand: one treatment laid over every painting so the
plates read as one painter's work, not as a model's (no airbrushed micro-detail,
no plastic sheen). Each step is ours and deterministic:

  simplify  flatten micro-detail into brush patches (Kuwahara)
  palette   the plate's colors pulled toward the book's palette; only the
            story's hues stay strong (ember orange-gold, the cage's cold blue)
  edges     pigment pooling at the edges of washes
  ink       a drawn contour (XDoG) over the paint
  paper     our procedural paper and granulation
  grain     a fine tooth

    python tools/storybook/hand.py <in.png> [<in2.png> ...] --preset nocturne [--out DIR] [--side]
"""
import argparse
import json
import os

import cv2
import numpy as np

PRESETS = {
    # Night plates: deep washes, ink black, warm paper in the lights.
    "nocturne": dict(kuwahara=4, desat=0.55, shadow="#1a1d2a", light="#e8dcc4", split=0.35, story_boost=1.08,
                     edges=0.35, ink=0.55, ink_sigma=1.4, ink_min=60, paper=0.16, gran=0.10, grain=0.025),
    "light": dict(kuwahara=3, desat=0.35, shadow="#22222c", light="#efe4cf", split=0.25, story_boost=1.04,
                  edges=0.25, ink=0.4, ink_sigma=1.2, ink_min=40, paper=0.12, gran=0.07, grain=0.02),
    "raw": dict(kuwahara=0, desat=0, shadow="#000000", light="#ffffff", split=0, story_boost=1.0,
                edges=0, ink=0, ink_sigma=1.4, ink_min=60, paper=0, gran=0, grain=0),
}


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def kuwahara(img, r):
    """Classic four-quadrant Kuwahara: each pixel takes the mean of whichever
    of its four (r+1)^2 quadrants varies least. Box filters keep it fast."""
    if r <= 0:
        return img
    k = r + 1
    lum = img.mean(axis=2)
    means, vars_ = [], []
    for dy, dx in ((0, 0), (0, r), (r, 0), (r, r)):
        m = cv2.boxFilter(img, -1, (k, k), anchor=(dx, dy), borderType=cv2.BORDER_REFLECT)
        ml = cv2.boxFilter(lum, -1, (k, k), anchor=(dx, dy), borderType=cv2.BORDER_REFLECT)
        m2 = cv2.boxFilter(lum * lum, -1, (k, k), anchor=(dx, dy), borderType=cv2.BORDER_REFLECT)
        means.append(m)
        vars_.append(m2 - ml * ml)
    idx = np.argmin(np.stack(vars_), axis=0)
    out = np.zeros_like(img)
    for i, m in enumerate(means):
        out[idx == i] = m[idx == i]
    return out


def story_masks(img):
    """How much each pixel is ember (orange-gold) or the cage's blue."""
    hsv = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    h, s, v = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255

    def band(lo, hi, soft=8):
        a = np.clip((h - (lo - soft)) / soft, 0, 1) * np.clip(((hi + soft) - h) / soft, 0, 1)
        return a * np.clip((s - 0.25) / 0.35, 0, 1) * np.clip((v - 0.2) / 0.3, 0, 1)
    return band(8, 52), band(185, 228)


def palette(img, p):
    ember, blue = story_masks(img)
    keep = np.clip(ember + blue, 0, 1)[..., None]
    lum = (img @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    gray = np.repeat(lum, 3, axis=2)
    muted = img * (1 - p["desat"]) + gray * p["desat"]
    # Split tone: shadows toward the night wash, lights toward the paper.
    sh, li = hexrgb(p["shadow"]), hexrgb(p["light"])
    tone = sh * (1 - lum) + li * lum
    muted = muted * (1 - p["split"]) + (tone * lum * 2 * (lum < 0.5) + (1 - 2 * (1 - tone) * (1 - lum)) * (lum >= 0.5)) * p["split"]
    story = np.clip(img * p["story_boost"], 0, 1)
    return np.clip(muted * (1 - keep) + story * keep, 0, 1)


def edges_pool(img, base, amt):
    """Pigment gathers where a wash stops: darken along the paint's own edges."""
    if amt <= 0:
        return img
    lum = cv2.GaussianBlur(base.mean(axis=2), (0, 0), 1.2)
    gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
    g = np.sqrt(gx * gx + gy * gy)
    g = np.clip(g / (np.percentile(g, 98) + 1e-6), 0, 1)
    return img * (1 - amt * 0.5 * g[..., None])


def ink_lines(base, sigma, min_area, w):
    """XDoG contours from the simplified paint, kept only where they are long
    enough to read as a drawn line, then given a slightly broken brush edge."""
    lum = base.mean(axis=2)
    g1 = cv2.GaussianBlur(lum, (0, 0), sigma)
    g2 = cv2.GaussianBlur(lum, (0, 0), sigma * 1.6)
    d = g1 - 0.985 * g2
    e = np.where(d >= -0.004, 1.0, 1.0 + np.tanh(160 * (d + 0.004))).astype(np.float32)
    line = (e < 0.5).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(line, connectivity=8)
    big = np.zeros(n, bool)
    big[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_area * (w / 1792.0)
    line = big[lab].astype(np.float32)
    rng = np.random.default_rng(3)
    brk = cv2.GaussianBlur(rng.random(line.shape).astype(np.float32), (0, 0), 2.0)
    brk = np.clip((brk - 0.42) * 6, 0, 1)
    line = cv2.GaussianBlur(line * brk, (0, 0), 0.6)
    return np.clip(line * 1.4, 0, 1)


def paper_tex(h, w, seed=7):
    """Our paper: soft cloudy sizing, fibers along one grain, fine tooth."""
    rng = np.random.default_rng(seed)
    cloud = np.zeros((h, w), np.float32)
    for s, a in ((64, 0.5), (24, 0.3), (8, 0.2)):
        n = rng.random((h // s + 2, w // s + 2)).astype(np.float32)
        cloud += a * cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    fib = rng.random((h, w)).astype(np.float32)
    fib = cv2.GaussianBlur(fib, (0, 0), sigmaX=6, sigmaY=0.7)
    tooth = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 0.8)
    t = 0.55 * (cloud - cloud.mean()) / (cloud.std() + 1e-6) + 0.3 * (fib - fib.mean()) / (fib.std() + 1e-6) + 0.35 * (tooth - tooth.mean()) / (tooth.std() + 1e-6)
    return t / (np.abs(t).max() + 1e-6)


def treat(img, p):
    h, w = img.shape[:2]
    base = kuwahara(img, int(round(p["kuwahara"] * w / 1792.0))) if p["kuwahara"] else img
    out = palette(base, p)
    out = edges_pool(out, base, p["edges"])
    if p["ink"]:
        line = ink_lines(base, p["ink_sigma"] * w / 1792.0, p["ink_min"], w)
        ink = hexrgb("#120f0d")
        out = out * (1 - p["ink"] * line[..., None]) + ink * p["ink"] * line[..., None]
    if p["paper"] or p["gran"]:
        t = paper_tex(h, w)
        lum = out.mean(axis=2)
        # Granulation settles in the washes, not in bare paper or in solid ink.
        gmask = np.clip(1 - np.abs(lum - 0.4) / 0.4, 0, 1)
        out = out * (1 + (p["paper"] * 0.5 + p["gran"] * gmask[..., None] * 0.8) * t[..., None] * 0.5)
    if p["grain"]:
        rng = np.random.default_rng(11)
        out = out + (rng.standard_normal((h, w, 1)).astype(np.float32) * p["grain"])
    return np.clip(out, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--preset", default="nocturne")
    ap.add_argument("--set", default="", help="key=value,... over the preset")
    ap.add_argument("--out", default=None)
    ap.add_argument("--side", action="store_true", help="also write raw|treated side by side")
    a = ap.parse_args()
    p = dict(PRESETS[a.preset])
    for kv in filter(None, a.set.split(",")):
        k, v = kv.split("=")
        p[k] = v if v.startswith("#") else float(v)
    for f in a.inputs:
        img = cv2.cvtColor(cv2.imread(f, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
        out = treat(img, p)
        d = a.out or os.path.join(os.path.dirname(f), "hand_" + a.preset)
        os.makedirs(d, exist_ok=True)
        name = os.path.splitext(os.path.basename(f))[0]
        cv2.imwrite(os.path.join(d, name + ".png"), cv2.cvtColor((out * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR))
        json.dump({"source": os.path.basename(f), "preset": a.preset, "params": p, "tool": "tools/storybook/hand.py"},
                  open(os.path.join(d, name + ".json"), "w"), indent=1)
        if a.side:
            both = np.concatenate([img, out], axis=1)
            cv2.imwrite(os.path.join(d, name + "_side.jpg"), cv2.cvtColor((both * 255).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(name)


if __name__ == "__main__":
    main()
