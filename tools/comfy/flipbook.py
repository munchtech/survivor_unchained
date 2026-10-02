"""A clip of an effect shot on black, cut into a flipbook atlas for the game.

    python tools/comfy/flipbook.py <clip.mp4> <out.png> [--grid 8] [--cell 256]
        [--start 0] [--end 1] [--pad 0.06] [--gain 1.0] [--alpha luma|max]

The effect's extent is found over the whole clip (everything brighter than
the black around it), squared and padded, so every frame shares one frame of
reference and nothing jumps. `grid`² frames are taken evenly between
`start` and `end` (fractions of the clip) and laid out left to right, top to
bottom. Colour is stored premultiplied by its own alpha, so the same atlas
draws additive (fire, sparks, magic) or blended (smoke, dust) without a dark
fringe; alpha comes from the brightest channel (`max`, for fire) or from
luminance (`luma`, for smoke). The edges of every cell fade to nothing so a
crop that grazes the effect never shows a hard line.
"""
import argparse
import json

import imageio.v3 as iio
import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("out")
    ap.add_argument("--grid", type=int, default=8)
    ap.add_argument("--cell", type=int, default=256)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=1.0)
    ap.add_argument("--pad", type=float, default=0.06)
    ap.add_argument("--gain", type=float, default=1.0)
    ap.add_argument("--alpha", choices=["luma", "max"], default="max")
    ap.add_argument("--floor", type=float, default=0.04, help="black level taken as nothing")
    ap.add_argument("--round", type=float, default=0.55, help="radius (0..1 of the cell) where the edge starts to fade")
    ap.add_argument("--keep", type=float, default=0.01, help="share of the light allowed outside the crop")
    a = ap.parse_args()

    frames = np.stack([f[..., :3] for f in iio.imiter(a.clip)]).astype(np.float32) / 255.0
    n = len(frames)
    # Fade toward the clip's own edges first: an effect that fills its frame
    # (frost, lightning) is cut off there in straight lines, and the square
    # crop reaches past the frame's top and bottom, so those lines would show.
    fh, fw = frames.shape[1:3]
    band = 0.12 * min(fh, fw)
    yy = np.minimum(np.arange(fh), fh - 1 - np.arange(fh))[:, None]
    xx = np.minimum(np.arange(fw), fw - 1 - np.arange(fw))[None, :]
    border = np.clip(np.minimum(yy, xx) / band, 0, 1)
    border = (border * border * (3 - 2 * border)).astype(np.float32)
    frames *= border[None, :, :, None]
    i0, i1 = int(a.start * (n - 1)), int(a.end * (n - 1))
    count = a.grid * a.grid
    pick = [frames[round(i0 + k * (i1 - i0) / max(1, count - 1))] for k in range(count)]

    # Where the effect is, over all the frames taken: where most of its
    # light falls, weighted by brightness, so a few sparks thrown wide do not
    # shrink the effect to a speck in the middle of every cell.
    peak = np.max(np.stack(pick).max(axis=3), axis=0)
    weight = np.clip(peak - a.floor, 0, None) ** 2
    if weight.sum() <= 0:
        raise SystemExit("nothing brighter than black in the clip")
    def span(axis_weight):
        c = np.cumsum(axis_weight) / axis_weight.sum()
        return np.searchsorted(c, a.keep / 2), np.searchsorted(c, 1 - a.keep / 2)
    x0, x1 = span(weight.sum(axis=0))
    y0, y1 = span(weight.sum(axis=1))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    side = max(x1 - x0, y1 - y0) * (1 + a.pad * 2)
    h, w = peak.shape
    half = side / 2
    box = (int(cx - half), int(cy - half), int(cx + half), int(cy + half))

    # A soft vignette per cell: nothing reaches the cell's edge.
    g = np.linspace(-1, 1, a.cell)
    r = np.sqrt(g[None, :] ** 2 + g[:, None] ** 2)
    # Round, and soft from `round` outward: a clip that fills its whole frame
    # (frost, lightning) would otherwise show the square of its cell.
    edge = np.clip((1.0 - r) / max(1e-3, 1.0 - a.round), 0, 1)
    edge = edge * edge * (3 - 2 * edge)

    atlas = np.zeros((a.grid * a.cell, a.grid * a.cell, 4), np.float32)
    for k, f in enumerate(pick):
        im = Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8))
        # Crop with black beyond the clip's edge.
        canvas = Image.new("RGB", (box[2] - box[0], box[3] - box[1]))
        canvas.paste(im, (-box[0], -box[1]))
        c = np.asarray(canvas.resize((a.cell, a.cell), Image.LANCZOS)).astype(np.float32) / 255.0
        c = np.clip((c - a.floor) / (1 - a.floor), 0, 1) * a.gain
        if a.alpha == "max":
            alpha = c.max(axis=2)
        else:
            alpha = c @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        alpha = np.clip(alpha, 0, 1) * edge
        rgb = np.clip(c, 0, 1) * edge[..., None]
        y, x = divmod(k, a.grid)
        atlas[y * a.cell:(y + 1) * a.cell, x * a.cell:(x + 1) * a.cell] = np.dstack([rgb, alpha])
    Image.fromarray((atlas * 255 + 0.5).astype(np.uint8), "RGBA").save(a.out)
    meta = {"grid": a.grid, "frames": count, "fps": round(count / max(1e-3, (i1 - i0) / 24), 2), "source": a.clip.replace("\\", "/").split("/")[-1]}
    with open(a.out.rsplit(".", 1)[0] + ".json", "w") as fh:
        json.dump(meta, fh)
    print(f"{a.out}: {count} frames, {a.grid * a.cell}px, from {i1 - i0 + 1} of {n} source frames")


if __name__ == "__main__":
    main()
