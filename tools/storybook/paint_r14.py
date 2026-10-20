"""Round 14's content paints, made into the r13 picks BEFORE the shared repaint
(so the repaint folds them into the same hand). Each one is a fix from judge r1's
list that the generator would not draw from words:

  p1  the near legionaries darkened to near-plane shapes (the torch flame kept)
  p4  the spearhead buried in a gold burst at the wound; the face grayed and the
      eyes and mouth turned to glowing gold sockets (the dead, lit from inside)
  p7  the ford's stepping stones across the shallows, snow on their tops
  p9  exactly three blue lamp points, uneven, low by the water (the warm points
      beside them painted out)

    python tools/storybook/paint_r14.py --out tools/storybook/out/style_r14/src
"""
import argparse
import json
import os

import cv2
import numpy as np

R13 = "tools/storybook/out/style_r13/"
PICKS = {"p1": R13 + "p1_t_s23.png", "p4": R13 + "p4_t_s37.png", "p7": R13 + "p7_i_s11.png", "p9": R13 + "p9_t_s23.png"}


def load(f):
    return cv2.cvtColor(cv2.imread(f, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB).astype(np.float32) / 255


def save(f, img):
    cv2.imwrite(f, cv2.cvtColor((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR))


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def ellipse_mask(shape, cx, cy, rx, ry, soft=1.2, ang=0.0, wobble=0.0, seed=0):
    h, w = shape[:2]
    m = np.zeros((h, w), np.float32)
    if wobble:
        rng = np.random.default_rng(seed)
        t = np.linspace(0, 2 * np.pi, 48, endpoint=False)
        r = 1 + wobble * (0.6 * np.sin(2 * t + rng.uniform(0, 6)) + 0.4 * np.sin(3 * t + rng.uniform(0, 6)))
        a = np.radians(ang)
        xs = cx + rx * r * np.cos(t) * np.cos(a) - ry * r * np.sin(t) * np.sin(a)
        ys = cy + rx * r * np.cos(t) * np.sin(a) + ry * r * np.sin(t) * np.cos(a)
        cv2.fillPoly(m, [np.stack([xs, ys], 1).round().astype(np.int32)], 1.0, cv2.LINE_AA)
    else:
        cv2.ellipse(m, (int(round(cx)), int(round(cy))), (int(round(rx)), int(round(ry))), ang, 0, 360, 1.0, -1, cv2.LINE_AA)
    return cv2.GaussianBlur(m, (0, 0), soft) if soft else m


def over(img, m, col):
    return img * (1 - m[..., None]) + col * m[..., None]


def glow(img, cx, cy, r, col, amt):
    """Additive soft light (a gaussian falloff)."""
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)) * amt
    return img + g[..., None] * col


def inpaint(img, m):
    u8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    out = cv2.inpaint(u8, (m > 0.5).astype(np.uint8) * 255, 5, cv2.INPAINT_TELEA)
    return out.astype(np.float32) / 255


def p1(img):
    """The two near soldiers as dark near-plane shapes: their region's darks and mids
    pulled down by half, the rim light and the torch flame kept."""
    h, w = img.shape[:2]
    m = np.zeros((h, w), np.float32)
    cv2.rectangle(m, (30, 200), (520, h), 1.0, -1)
    m = cv2.GaussianBlur(m, (0, 0), 28)
    v = img.max(2)
    keep = np.clip((v - 0.55) / 0.25, 0, 1)            # the flame and the brightest rim stay
    k = m * (1 - keep) * 0.5
    return img * (1 - k[..., None])


def p4(img):
    """The visible spearhead painted out and a gold burst laid over the wound; the face
    grayed, the eyes and the open mouth made into glowing gold sockets."""
    hsv = cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32) / 255
    blade = np.zeros(img.shape[:2], np.float32)
    zone = (slice(380, 470), slice(655, 768))                          # the bare blade in front of his chest:
    blade[zone] = ((hsv[..., 2] > 0.55) & (hsv[..., 1] < 0.35))[zone]  # bright, unsaturated pixels (measured)
    cv2.line(blade, (664, 403), (762, 431), 1.0, 10, cv2.LINE_AA)     # and its shadow side, on the fitted line
    blade = cv2.dilate(blade, np.ones((9, 9), np.uint8))
    img = inpaint(img, blade)
    shaft = np.zeros(img.shape[:2], np.float32)
    cv2.line(shaft, (744, 439), (772, 451), 1.0, 6, cv2.LINE_AA)       # the shaft (fitted line) runs on into the wound
    img = over(img, cv2.GaussianBlur(shaft, (0, 0), 0.8), rgb("#1c1712"))
    gold, hot = rgb("#e8a33c"), rgb("#ffe2a0")
    img = glow(img, 745, 439, 30, gold, 0.55)
    img = glow(img, 745, 439, 10, hot, 0.6)
    face = ellipse_mask(img.shape, 764, 246, 40, 50, soft=8)
    gray = img.mean(2, keepdims=True) * np.array([0.98, 1.0, 0.94], np.float32)
    img = img * (1 - 0.45 * face[..., None]) + gray * 0.45 * face[..., None]
    dark = rgb("#1a120a")
    for cx, cy, rx, ry in ((748, 244, 6, 4), (776, 237, 6, 4), (766, 271, 8, 5)):
        img = over(img, ellipse_mask(img.shape, cx, cy, rx + 1.5, ry + 1.5, soft=1.0), dark)
        img = over(img, ellipse_mask(img.shape, cx, cy, rx * 0.8, ry * 0.75, soft=1.2), rgb("#f2b54e"))
        img = glow(img, cx, cy, 2.2, hot, 0.9)
        img = glow(img, cx, cy, 9, gold, 0.28)
    return img


STONES = [(830, 964, 48, 15), (930, 884, 42, 13), (1020, 824, 37, 11), (1110, 770, 32, 10),
          (1200, 720, 28, 8), (1280, 670, 24, 7), (1350, 624, 20, 6), (1410, 590, 17, 5)]


def p7(img):
    """A line of flat dark stepping stones with snow on their tops across the shallows,
    from the near bank under the fourth light's reflection to the far bank."""
    body, face, shadow = rgb("#232a33"), rgb("#161b22"), rgb("#0b0f14")
    rng = np.random.default_rng(7)
    for i, (cx, cy, rx, ry) in enumerate(STONES):
        cx, cy = cx + rng.uniform(-6, 6) * rx / 40, cy + rng.uniform(-3, 3) * rx / 40
        rx, ry = rx * rng.uniform(0.85, 1.15), ry * 1.25
        near_light = np.exp(-((cx - 980) ** 2 + (cy - 700) ** 2) / (2 * 220.0 ** 2))
        snow = rgb("#8d9bab") * (1 - near_light) + rgb("#97b6da") * near_light
        img = over(img, ellipse_mask(img.shape, cx + 2, cy + ry * 0.8, rx * 1.1, ry * 0.6, soft=2.0) * 0.6, shadow)
        img = over(img, ellipse_mask(img.shape, cx, cy + ry * 0.25, rx, ry * 0.85, soft=1.1, wobble=0.1, seed=i), face)
        img = over(img, ellipse_mask(img.shape, cx, cy - ry * 0.1, rx * 0.95, ry * 0.7, soft=1.1, wobble=0.08, seed=50 + i), body)
        img = over(img, ellipse_mask(img.shape, cx - rx * 0.06, cy - ry * 0.4, rx * 0.72, ry * 0.38, soft=1.2,
                                     wobble=0.15, seed=100 + i), snow)
    return img


def p9(img):
    """Exactly three blue lamps, uneven, low by the water: the warm point paired with the
    blue lamp at 1221 painted out (with its reflection); the warm point at 1436 and its
    reflection recolored to the lamps' cold blue (hue 218), so the three sit at
    1221, 1371 and 1436 (gaps 150 and 65)."""
    m = np.zeros(img.shape[:2], np.float32)
    cv2.circle(m, (1201, 490), 9, 1.0, -1)
    cv2.rectangle(m, (1196, 490), (1206, 526), 1.0, -1)
    img = inpaint(img, m)
    r = np.zeros(img.shape[:2], np.float32)
    cv2.circle(r, (1436, 500), 12, 1.0, -1)
    cv2.rectangle(r, (1429, 500), (1443, 530), 1.0, -1)
    r = cv2.GaussianBlur(r, (0, 0), 1.5)
    v = img.max(2, keepdims=True)
    lit = np.clip((v - 0.2) / 0.3, 0, 1)
    blue = v * rgb("#3f8fff") / rgb("#3f8fff").max()
    core = rgb("#d6ebff") * v
    hot = np.clip((v - 0.75) / 0.2, 0, 1)
    new = blue * (1 - hot) + core * hot
    k = (r[..., None] * lit)
    img = img * (1 - k) + new * k
    return glow(img, 1436, 500, 7, rgb("#3f8fff"), 0.3)     # a halo like the other two


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="tools/storybook/out/style_r14/src")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    fix = {"p1": p1, "p4": p4, "p7": p7, "p9": p9}
    for k, f in PICKS.items():
        save(os.path.join(a.out, k + ".png"), fix[k](load(f)))
        json.dump({"source": f, "step": "paint_r14." + k, "what": fix[k].__doc__.strip(), "tool": "tools/storybook/paint_r14.py"},
                  open(os.path.join(a.out, k + ".json"), "w"), indent=1)
        print(k, "->", os.path.join(a.out, k + ".png"))


if __name__ == "__main__":
    main()
