"""1:1 crops round her for the armor 4 judge: crop_<frame>.png for play frames, lod_cmp_<calling>.png (full | gameplay)."""
import os, sys, numpy as np
from PIL import Image
O = sys.argv[1] if len(sys.argv) > 1 else "godot/.shots/armor4/"
W, H = 240, 300


def load(n):
    return np.asarray(Image.open(os.path.join(O, n + ".png")).convert("RGB")).astype(int)


def centre(a, b, fallback):
    d = np.abs(a - b).sum(2) > 30
    d[:, :120] = False; d[:, -120:] = False     # (a one-pixel column at the frame's right edge flickers between runs)
    if d.sum() < 20:
        return fallback
    ys, xs = np.nonzero(d)
    return int(np.median(ys)), int(np.median(xs))


def crop(im, c):
    cy, cx = c
    y0 = min(max(0, cy - H // 2), im.shape[0] - H); x0 = min(max(0, cx - W // 2), im.shape[1] - W)
    return Image.fromarray(im[y0:y0 + H, x0:x0 + W].astype(np.uint8)), (x0, y0)


# her centre at the play camera: where plain and gilded differ (only her top does)
mid = (540, 960)
try:
    c_play = centre(load("j_plain_play"), load("j_gilded_play"), mid)
    c_play = (c_play[0] + 20, c_play[1])     # (the top sits above her middle: drop the box a little)
except FileNotFoundError:
    c_play = mid
print("play centre", c_play)
for n in ("j_plain_play", "j_etched_play", "j_gilded_play", "j_gilded_run_play", "j_gilded_fight_play"):
    try:
        im = load(n)
    except FileNotFoundError:
        print(n, "MISSING"); continue
    c, at = crop(im, c_play if "run" not in n and "fight" not in n else mid)
    c.save(os.path.join(O, "crop_" + n + ".png")); print("crop", n, at)
for k in ("warden", "arcanist", "stalker", "reaver"):
    try:
        a, b = load("lod_off_" + k), load("lod_on_" + k)
    except FileNotFoundError:
        print(k, "MISSING"); continue
    d = np.abs(a - b).sum(2) > 30
    c = centre(a, b, mid)
    ca, at = crop(a, c); cb, _ = crop(b, c)
    s = Image.new("RGB", (2 * W + 6, H), (0, 0, 0)); s.paste(ca, (0, 0)); s.paste(cb, (W + 6, 0))
    s.save(os.path.join(O, "lod_cmp_" + k + ".png"))
    print("lod", k, "differing px", int(d.sum()), "crop at", at)
