"""Skin numbers for a frame: python meas.py IMG x0 y0 x1 y1 [--sat 0.8,0.7] [--crop out.jpg]
Box in full-res pixels (1920x1080). Prints, over the box:
  skin: pixels with hue 8-50 deg, V > 0.22, S > 0.08 (the hair is redder and darker; lips and eyes mostly fall out):
        mean HSV saturation, median, mean hue, mean luma (Rec.709 on sRGB 0-255), share of the box.
  all : every pixel with V > 0.22 (a judge's rough box measure).
--sat: the same numbers with Godot's adjustment saturation simulated (mix toward the channel mean, sRGB)."""
import sys
import numpy as np
from PIL import Image

a = sys.argv[1:]
img, (x0, y0, x1, y1) = a[0], map(int, a[1:5])
sats = [1.0]
crop = None
if "--sat" in a: sats += [float(s) for s in a[a.index("--sat") + 1].split(",")]
if "--crop" in a: crop = a[a.index("--crop") + 1]
im = Image.open(img).convert("RGB")
if crop: im.crop((x0, y0, x1, y1)).save(crop, quality=90)
px = np.asarray(im, np.float32)[y0:y1, x0:x1].reshape(-1, 3) / 255.0


def hsv(p):
    mx, mn = p.max(1), p.min(1)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = p[:, 0], p[:, 1], p[:, 2]
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, s, mx


for k in sats:
    q = px if k == 1.0 else np.clip(px.mean(1, keepdims=True) + k * (px - px.mean(1, keepdims=True)), 0, 1)
    h, s, v = hsv(q)
    luma = (q @ np.array([0.2126, 0.7152, 0.0722])) * 255
    skin = (h >= 8) & (h <= 50) & (v > 0.22) & (s > 0.08)
    allm = v > 0.22
    if skin.sum() == 0:
        print(f"sat x{k}: no skin pixels"); continue
    print(f"sat x{k}: skin S mean {s[skin].mean():.3f} med {np.median(s[skin]):.3f} hue {h[skin].mean():.0f} luma {luma[skin].mean():.0f} "
          f"share {skin.mean():.2f} | all S {s[allm].mean():.3f} luma {luma[allm].mean():.0f} | RGB {tuple(int(x) for x in (q[skin].mean(0) * 255))}")
