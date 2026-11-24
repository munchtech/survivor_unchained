"""Blind side-by-side sheets of two bodies' den runs (tools/body/switch_film.py tags) for a judge.

    python tools/body/switch_pairs.py <tag_a> <tag_b> --out <dir> [--seed N]

Reads godot/.shots/switch/<tag>/{start,kit,start_close,kit_close}/*.png and film_*.mp4 of both tags (the same scripted
run on two bodies). For each still in both: <out>/pair_<set>_<still>.png, the two whole 1:1 game frames side by side
(left/right drawn at random per pair, labelled X and Y only) and <out>/crop_<set>_<still>.png, a 1:1 crop about her
(the frame's centre, where the den camera keeps her) from each, side by side, no scaling. Films: <out>/film_<set>.mp4,
the two films side by side in one order drawn at random. The key (which side is which tag) goes to <out>/../key_<name>.json,
outside the judge's folder. Derivation: the owner's bar ("cannot tell them apart", side by side at the game camera, no
zoom-ins); a judge told which is which reads for the difference it expects, so the sides are hidden.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHOTS = os.path.join(ROOT, "godot", ".shots", "switch")
SETS = ("start", "kit", "start_close", "kit_close")
CROP = (720, 720)   # 1:1 pixels about the frame's centre


def label(im, text):
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("arial.ttf", 40)
    except OSError:
        f = ImageFont.load_default()
    d.rectangle((0, 0, 70, 56), fill=(0, 0, 0))
    d.text((14, 6), text, fill=(255, 255, 255), font=f)
    return im


def side(a, b, gap=12):
    out = Image.new("RGB", (a.width + b.width + gap, max(a.height, b.height)), (255, 255, 255))
    out.paste(a, (0, 0))
    out.paste(b, (a.width + gap, 0))
    return out


def crop(im):
    cx, cy = im.width // 2, im.height // 2
    w, h = CROP
    return im.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2))


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    os.makedirs(args.out, exist_ok=True)
    key = {"a": args.a, "b": args.b, "pairs": {}, "films": {}}
    for s in SETS:
        da, db = (os.path.join(SHOTS, t, s) for t in (args.a, args.b))
        if not (os.path.isdir(da) and os.path.isdir(db)):
            continue
        for f in sorted(os.listdir(da)):
            if not f.endswith(".png") or not os.path.exists(os.path.join(db, f)):
                continue
            ia, ib = (Image.open(os.path.join(d, f)).convert("RGB") for d in (da, db))
            flip = rng.random() < 0.5
            x, y = (ib, ia) if flip else (ia, ib)
            name = f"{s}_{f[:-4]}"
            side(label(x.copy(), "X"), label(y.copy(), "Y")).save(os.path.join(args.out, f"pair_{name}.png"))
            side(label(crop(x), "X"), label(crop(y), "Y")).save(os.path.join(args.out, f"crop_{name}.png"))
            key["pairs"][name] = {"X": args.b if flip else args.a, "Y": args.a if flip else args.b}
    for s in ("start", "kit"):
        fa, fb = (os.path.join(SHOTS, t, f"film_{s}.mp4") for t in (args.a, args.b))
        if not (os.path.exists(fa) and os.path.exists(fb)):
            continue
        flip = rng.random() < 0.5
        x, y = (fb, fa) if flip else (fa, fb)
        out = os.path.join(args.out, f"film_{s}.mp4")
        subprocess.check_call([ffmpeg(), "-y", "-loglevel", "error", "-i", x, "-i", y, "-filter_complex",
                               "[0:v][1:v]hstack=inputs=2[v]", "-map", "[v]", "-c:v", "libx264", "-crf", "16",
                               "-pix_fmt", "yuv420p", out])
        key["films"][s] = {"left (X)": args.b if flip else args.a, "right (Y)": args.a if flip else args.b}
    kp = os.path.join(os.path.dirname(os.path.abspath(args.out)), f"key_{os.path.basename(os.path.abspath(args.out))}.json")
    with open(kp, "w") as fh:
        json.dump(key, fh, indent=1)
    print(f"pairs {len(key['pairs'])}, films {len(key['films'])} -> {args.out}; key {kp}")


if __name__ == "__main__":
    main()
