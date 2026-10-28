"""UI 17, The Drowned Girl, round 2: the Flare's coal map from a Krea painting of a banked ember.

    python tools/uiforge/dg_coal.py CUT.png [--size 232] [--k 0.98] [--oy 0.20] [--preview P.png]

The painting (Krea 2 turbo, seed 9601: "a single banked ember: one irregular lump of hardwood charcoal ... plates of
very different sizes ... cracks from fine hairline threads to two or three wide deep fissures", cut with BiRefNet) keeps
its own lumpy silhouette. It is fitted, width-wise, into a square map and split into what shaders/hud_dg_coal.gdshader
heats by the meter:
  R  the plates' own light (the ash bloom and the charcoal), the fire's glow taken out;
  G  the cracks: how deep (the painting's fire, saturated and bright, brightest in the wide fissures): the shader heats
     the deep ones to white at their cores and leaves the hairlines red;
  B  the plates' edges and faces the cracks light (their warm cast in the painting, plus the cracks spread a little);
  A  the silhouette.
Saved at twice the size shown (UiArt halves it) to godot/art/ui/dg_meters/coal_map.png; the map's half size and its
middle's offset in the eddy hole's radii (k, ox, oy: the coal sits low in the eddy's cup) go to meters_geo.json "coal".
"""
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


def arg(args, name, default, kind=float):
    return kind(args[args.index(name) + 1]) if name in args else default


def main():
    args = sys.argv[1:]
    src = args[0]
    size = arg(args, "--size", 232, int)
    k = arg(args, "--k", 0.98)
    oy = arg(args, "--oy", 0.20)
    im = Image.open(src).convert("RGBA")
    bb = im.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    im = im.crop(bb)
    w, h = im.size
    side = max(w, h)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(im, ((side - w) // 2, (side - h) // 2))
    arr = np.asarray(sq.resize((size, size), Image.LANCZOS)).astype(np.float32) / 255
    rgb, a = arr[..., :3], arr[..., 3]
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hi, lo = rgb.max(axis=2), rgb.min(axis=2)
    warm = np.clip((R - B) / np.maximum(R, 1e-3), 0, 1)
    # the fire: saturated red-orange and bright; deepest where brightest
    fire = smooth(0.55, 0.85, warm) * smooth(0.22, 0.70, R)
    crack = np.clip(fire * (0.45 + 0.55 * smooth(0.35, 0.95, (R + G) / 1.6)), 0, 1)
    crack = np.clip(crack / max(np.percentile(crack[a > 0.5], 99.5), 1e-3), 0, 1) ** 0.8
    # the hairlines: thin dark seams between the plates (a black-hat of the plates' light), shallow: red at most
    lum = (0.3 * R + 0.55 * G + 0.15 * B).astype(np.float32)
    seam = cv2.morphologyEx(lum, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    seam = smooth(0.06, 0.22, seam) * (a > 0.9)
    crack = np.maximum(crack, 0.32 * seam)
    crack = cv2.GaussianBlur(crack.astype(np.float32), (0, 0), 0.5)
    # the plates: their light without the fire's cast (the coolest channel), the cracks dark
    rock = np.clip(lo * 1.25, 0, 1) * (1 - smooth(0.10, 0.5, crack))
    # what the cracks light: the warm cast on the plates, and the cracks spread a few px
    cast = smooth(0.18, 0.55, warm) * smooth(0.15, 0.6, R) * (1 - crack)
    spread = cv2.GaussianBlur(crack, (0, 0), size / 90)
    edge = np.clip(0.75 * cast + np.clip(spread * 1.8 - crack, 0, 1), 0, 1)
    out = np.dstack([rock, crack, edge, a])
    os.makedirs(DIR, exist_ok=True)
    dst = os.path.join(DIR, "coal_map.png")
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(dst)
    gp = os.path.join(DIR, "meters_geo.json")
    geo = json.load(open(gp, encoding="utf-8")) if os.path.exists(gp) else {}
    geo["coal"] = {"k": k, "ox": 0.0, "oy": oy, "aspect": round(h / w, 3), "src": os.path.basename(src)}
    json.dump(geo, open(gp, "w", encoding="utf-8"), indent=1)
    if "--preview" in args:
        pv = np.concatenate([np.dstack([c] * 3) for c in (rock, crack, edge, a)], axis=1)
        Image.fromarray((pv * 255).astype(np.uint8)).save(args[args.index("--preview") + 1])
    print(f"{dst}: {size} px, coal {w}x{h} (aspect {h / w:.2f}); crack mean {crack[a > 0.5].mean():.3f}, rock {rock[a > 0.5].mean():.3f}, edge {edge[a > 0.5].mean():.3f}")


if __name__ == "__main__":
    main()
