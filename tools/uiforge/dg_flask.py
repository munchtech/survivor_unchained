"""UI 17, The Drowned Girl, piece 5: the draught's hair-bound flask from a Krea painting.

    python tools/uiforge/dg_flask.py CUT.png [--h 56] [--hue 7]

The painting (Krea 2 turbo; round 3, seed 9952: "a small round-bellied glass potion flask ... plain clear glass with no
decoration ... a bright luminous scarlet cordial ... one single crisp white highlight"; the judge: "one cream swirl
band is still a stripe. Plain glass, red liquid, one highlight", so the hair strand of round 2 is gone; cut with BiRefNet) is cropped to its silhouette and saved at twice the size shown (UiArt halves it), --h px tall
shown, as two pictures shaders/hud_dg_flask.gdshader blends by the draught's level:
  flask_full.png   as painted, its liquid turned --hue degrees toward scarlet and lifted, so it reads apart from
                   the life orb's deep garnet;
  flask_empty.png  the liquid gone: the glass dark and cool where it was, its highlights kept.
The liquid's top and foot (0..1 of the picture's height) go into godot/art/ui/dg_meters/meters_geo.json as "flask"."""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DIR = os.path.join(ROOT, "godot", "art", "ui", "dg_meters")


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def main():
    args = sys.argv[1:]
    src = args[0]
    h_shown = int(args[args.index("--h") + 1]) if "--h" in args else 56
    hue = float(args[args.index("--hue") + 1]) if "--hue" in args else 7
    im = Image.open(src).convert("RGBA")
    bb = im.getchannel("A").point(lambda v: 255 if v > 16 else 0).getbbox()
    im = im.crop(bb)
    H = h_shown * 2
    W = int(round(im.width * H / im.height))
    im = im.resize((W, H), Image.LANCZOS)
    arr = np.asarray(im).astype(np.float32) / 255
    rgb, a = arr[..., :3], arr[..., 3]
    hsv = cv2.cvtColor((rgb * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    hh, ss, vv = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
    red = ((hh < 14) | (hh > 340)).astype(np.float32)
    liq = red * smooth(0.45, 0.75, ss) * smooth(0.15, 0.35, vv) * (a > 0.5)
    # (round 3: the liquid as one body, its highlights and pale specks inside it included, so the empty glass keeps none)
    body = cv2.morphologyEx((liq > 0.3).astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    ff = body.copy()
    cv2.floodFill(ff, np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8), (0, 0), 1)
    body = body | (1 - ff)
    liq = np.maximum(liq, cv2.dilate(body, np.ones((3, 3), np.uint8)).astype(np.float32) * (a > 0.5))
    liq = cv2.GaussianBlur(liq, (0, 0), 0.8)
    # full: the liquid toward scarlet and a little brighter
    hs = hsv.copy()
    hs[..., 0] = np.where(liq > 0.05, (hh + hue * liq) % 360 / 2, hsv[..., 0])
    hs[..., 2] = np.clip(vv * (1 + 0.12 * liq), 0, 1) * 255
    full = cv2.cvtColor(hs.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32) / 255
    # empty: where the liquid was, dark cool glass
    lum = rgb.max(axis=2, keepdims=True)
    dark = lum * 0.22 * np.array([0.62, 0.68, 0.80], np.float32) + 0.015
    empty = rgb * (1 - liq[..., None]) + dark * liq[..., None]
    for name, c in (("flask_full.png", full), ("flask_empty.png", empty)):
        Image.fromarray((np.dstack([np.clip(c, 0, 1), a]) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(DIR, name))
    rows = np.where(liq.max(axis=1) > 0.5)[0]
    top, bot = float(rows.min()) / H, float(rows.max() + 1) / H
    gp = os.path.join(DIR, "meters_geo.json")
    geo = json.load(open(gp, encoding="utf-8")) if os.path.exists(gp) else {}
    geo["flask"] = {"w": W / 2, "h": H / 2, "top": round(top, 4), "bot": round(bot, 4)}
    json.dump(geo, open(gp, "w", encoding="utf-8"), indent=1)
    print(f"flask {W // 2}x{H // 2} shown, liquid {top:.3f}..{bot:.3f}")


if __name__ == "__main__":
    main()
