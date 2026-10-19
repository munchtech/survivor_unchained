"""One hand over every plate (style round 2, after judge r1 found four hands).

The judge's master: P7's values and restraint, P4's ink weight on figures, a warm
umber ground showing through the darks, opaque paint only in the light, darks as
flat glazes, no surface patterns, no metal glints. Two deterministic steps wrap
one shared repaint (gen.py, the same hand prompt and settings for every plate):

  prep    the init for the repaint: the warm ground in the darks, a warm ink
          black point, stray strong hues capped; plus a soft-edge control map
          taken from a simplified copy (the big shapes, not the old brushwork)
  finish  the same ground step, lighter, after the repaint: one palette and
          one black point for every plate
  strays  the judge's measure: share of pixels with value > 0.3, saturation
          > 0.5 and hue outside 18-50 and 195-220 degrees

    python tools/storybook/unify.py prep <in.png>... --out DIR [--recolor-red]
    python tools/storybook/unify.py finish <in.png>... --out DIR
    python tools/storybook/unify.py strays <in.png>...
"""
import argparse
import json
import os

import cv2
import numpy as np

W = np.array([0.299, 0.587, 0.114], np.float32)
UMBER = "#4a3322"   # the warm ground
INK = "#15100c"     # the warm black point

PREP = dict(lo=0.05, hi=0.32, amt=0.55, base=0.65, tex=0.35, black_hi=0.06, black=0.75, cap=0.48)
FINISH = dict(lo=0.04, hi=0.26, amt=0.30, base=0.6, tex=0.4, black_hi=0.05, black=0.6, cap=0.48)


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def smooth(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def hsv(img):
    u = cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    return u[..., 0] * 360 / 255, u[..., 1] / 255, u[..., 2] / 255


def story(img):
    """0..1: how much each pixel is a story hue (ember 18-50, cage blue 195-220)."""
    h, s, v = hsv(img)

    def band(lo, hi, soft=6):
        return np.clip((h - (lo - soft)) / soft, 0, 1) * np.clip(((hi + soft) - h) / soft, 0, 1)
    return np.clip(band(18, 50) + band(195, 220), 0, 1)


def gaps(h, w, seed=17):
    """The ground showing between strokes: soft, long, slightly diagonal marks."""
    rng = np.random.default_rng(seed)
    k = w / 1792.0
    n = cv2.resize(rng.random((h // 10 + 2, w // 10 + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    ker = np.zeros((31, 31), np.float32)
    cv2.line(ker, (2, 21), (28, 9), 1.0, 1)
    ker /= ker.sum()
    n = cv2.filter2D(n, -1, ker)
    n = cv2.GaussianBlur(n, (0, 0), 2 * k)
    return np.clip((n - n.mean()) / (n.std() * 3 + 1e-6) + 0.5, 0, 1)


def ground(img, p):
    hgt, wid = img.shape[:2]
    L = img @ W
    Ls = cv2.GaussianBlur(L, (0, 0), 2.0)
    show = np.clip(p["base"] + p["tex"] * (gaps(hgt, wid) - 0.5) * 2, 0, 1)
    _, sat, _ = hsv(img)
    # Neutral darks are glazes over the ground; saturated passages (a dusk sky) are opaque color.
    show = show * (1 - smooth(p["lo"], p["hi"], Ls)) * p["amt"] * (1 - story(img)) * (1 - smooth(0.35, 0.6, sat))
    um = hexrgb(UMBER)
    tinted = um[None, None, :] * (L / float(um @ W))[..., None]
    out = img * (1 - show[..., None]) + tinted * show[..., None]
    k = ((1 - smooth(0.0, p["black_hi"], Ls)) * p["black"])[..., None]
    out = out * (1 - k) + hexrgb(INK) * k
    return cap(out, p["cap"])


def cap(img, c):
    """Stray strong hues held at saturation c (exactly, in HSV). Glowing reds
    (bright, hue 330-18) are fire, so they turn toward ember orange instead;
    dull reds (the Legion's rust) only lose saturation."""
    f = cv2.cvtColor(np.clip(img, 0, 1).astype(np.float32), cv2.COLOR_RGB2HSV)  # H 0-360, S, V 0-1
    h, s, v = f[..., 0], f[..., 1], f[..., 2]
    red = (h >= 330) | (h < 18)
    glow = red & (v > 0.55) & (s > 0.45)
    hd = np.where(h >= 330, h - 360, h)  # -30..18
    h = np.where(glow, 18 + (hd + 30) / 48 * 8, h)
    inside = (((h >= 18) & (h <= 50)) | ((h >= 195) & (h <= 220)))
    vm = smooth(0.22, 0.3, v)
    s = np.where(inside, s, s - np.clip(s - c, 0, None) * vm)
    out = cv2.cvtColor(np.stack([h, s, v], -1).astype(np.float32), cv2.COLOR_HSV2RGB)
    return np.clip(out, 0, 1)


def recolor_red(img):
    """P4's light was red; the ember is gold. Reds that glow are turned to ember gold."""
    h, s, v = hsv(img)
    red = (np.clip(1 - np.minimum(np.abs(h - 0), np.abs(h - 360)) / 22, 0, 1)
           * smooth(0.35, 0.6, s) * smooth(0.25, 0.5, v))
    gold = np.stack([np.ones_like(v), 0.74 * np.ones_like(v), 0.36 * np.ones_like(v)], -1) * v[..., None]
    gold = np.clip(gold * 1.05, 0, 1)
    m = cv2.GaussianBlur(red, (0, 0), 1.5)[..., None]
    return img * (1 - m) + gold * m


def soft_edges(img):
    """A soft-edge (HED-like) map of the big shapes: white lines on black."""
    k = img.shape[1] / 1792.0
    u8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    s = cv2.pyrMeanShiftFiltering(u8, sp=int(12 * k), sr=26)
    g = cv2.cvtColor(s, cv2.COLOR_RGB2GRAY)
    g = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(g)
    g = cv2.GaussianBlur(g, (0, 0), 1.6 * k)
    e = cv2.Canny(g, 24, 64)
    n, lab, st, _ = cv2.connectedComponentsWithStats((e > 0).astype(np.uint8), connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = st[1:, cv2.CC_STAT_AREA] >= 40 * k
    e = keep[lab].astype(np.float32)
    e = cv2.dilate(e, np.ones((2, 2), np.uint8))
    return np.clip(cv2.GaussianBlur(e, (0, 0), 1.1 * k) * 1.6, 0, 1)


def strays(img):
    h, s, v = hsv(img)
    out = ~(((h >= 18) & (h <= 50)) | ((h >= 195) & (h <= 220)))
    return float(((v > 0.3) & (s > 0.5) & out).mean())


def load(f):
    return cv2.cvtColor(cv2.imread(f, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB).astype(np.float32) / 255


def save(f, img):
    cv2.imwrite(f, cv2.cvtColor((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "finish", "strays"])
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out", default=None)
    ap.add_argument("--recolor-red", action="store_true")
    ap.add_argument("--simplify", action="store_true", help="prep: flatten the old brushwork first (mean shift)")
    a = ap.parse_args()
    for f in a.inputs:
        img = load(f)
        name = os.path.splitext(os.path.basename(f))[0]
        if a.cmd == "strays":
            print(f"{name}: strays {strays(img) * 100:.2f}%")
            continue
        d = a.out or os.path.dirname(f)
        os.makedirs(d, exist_ok=True)
        if a.cmd == "prep":
            if a.recolor_red:
                img = recolor_red(img)
            if a.simplify:
                k = img.shape[1] / 1792.0
                u8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
                img = cv2.pyrMeanShiftFiltering(u8, sp=int(10 * k), sr=20).astype(np.float32) / 255
            save(os.path.join(d, name + "_init.png"), ground(img, PREP))
            save(os.path.join(d, name + "_edge.png"), soft_edges(img)[..., None].repeat(3, 2))
            json.dump({"source": f, "step": "prep", "params": PREP, "recolor_red": a.recolor_red, "simplify": a.simplify,
                       "tool": "tools/storybook/unify.py"},
                      open(os.path.join(d, name + "_init.json"), "w"), indent=1)
        else:
            out = ground(img, FINISH)
            save(os.path.join(d, name + ".png"), out)
            json.dump({"source": f, "step": "finish", "params": FINISH, "tool": "tools/storybook/unify.py"},
                      open(os.path.join(d, name + ".json"), "w"), indent=1)
            print(f"{name}: strays {strays(out) * 100:.2f}%")


if __name__ == "__main__":
    main()
