"""UI 17, The Drowned Girl, piece 4: the Flare's coal map from a Krea painting of a live coal.

    python tools/uiforge/dg_coal.py CAND.png [--out godot/art/ui/dg_river/coal_map.png] [--size 232] [--inset 0.90]

The painting (Krea 2 turbo, seed 9301: "a single round lump of live coal ... black charcoal plates split by a web of
deep molten cracks", on black) is cropped to the round inside its silhouette (inset of its radius) and split into
what shaders/hud_dg_coal.gdshader heats by the meter:
  R  the plates' own light, the cracks' glow taken out (the darkest channel), the cracks themselves dark;
  G  the cracks: warm, saturated and bright in the painting; brighter = deeper (the shader heats them first);
  B  the plates' edges the cracks light (the cracks spread a few px, less the cracks).
Saved at twice the size shown (UiArt halves it), so 232 px for the eddy's 57 px radius."""
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def main():
    args = sys.argv[1:]
    src = args[0]
    out = args[args.index("--out") + 1] if "--out" in args else os.path.join(ROOT, "godot", "art", "ui", "dg_river", "coal_map.png")
    size = int(args[args.index("--size") + 1]) if "--size" in args else 232
    inset = float(args[args.index("--inset") + 1]) if "--inset" in args else 0.90
    rgb = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255
    mx = rgb.max(axis=2)
    sil = (cv2.GaussianBlur(mx, (0, 0), 3) > 0.05).astype(np.uint8)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(sil)
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    cx, cy = cent[k]
    area = stats[k, cv2.CC_STAT_AREA]
    r = np.sqrt(area / np.pi) * inset
    x0, y0 = int(round(cx - r)), int(round(cy - r))
    crop = rgb[y0:y0 + int(2 * r), x0:x0 + int(2 * r)]
    crop = cv2.resize(crop, (size, size), interpolation=cv2.INTER_AREA)
    R, G, B = crop[..., 0], crop[..., 1], crop[..., 2]
    hi, lo = crop.max(axis=2), crop.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1e-3)
    warm = (R >= G) & (G >= B * 0.8)
    crack = smooth(0.40, 0.80, sat) * smooth(0.18, 0.55, hi) * warm
    crack = crack * (0.55 + 0.45 * smooth(0.45, 1.0, (R + G) / 2))
    crack = cv2.GaussianBlur(crack.astype(np.float32), (0, 0), 0.6)
    rock = np.clip(lo * 1.15, 0, 1) * (1 - smooth(0.15, 0.6, crack))
    spread = cv2.GaussianBlur(crack, (0, 0), size / 60)
    edge = np.clip(spread * 2.2 - crack, 0, 1)
    out_img = np.dstack([rock, crack, edge, np.ones_like(rock)])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    Image.fromarray((np.clip(out_img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(out)
    print(f"{out}: {size} px from {src} (circle {cx:.0f},{cy:.0f} r {r:.0f}); crack mean {crack.mean():.3f}, rock mean {rock.mean():.3f}")


if __name__ == "__main__":
    main()
