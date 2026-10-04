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

Every atlas is checked before it is written, and refused (nothing written,
exit 2) when any frame fails:
- the clip itself must not run off its own frame: an effect cut by the
  camera's edge shows a flat side however softly the cell then fades;
- every cell's border must be black and transparent, and almost none of
  its light may lie past nine tenths of the way out, so no frame ever shows
  the square of its quad at any scale, turn or blend.
`--force` writes it anyway (for looking at a bad take); `--check ATLAS...`
checks atlases already made; `--clean ATLAS...` fades an old atlas's cells
in from their edges (when its clip is gone) and checks it.
"""
import argparse
import json
import sys

import imageio.v3 as iio
import numpy as np
from PIL import Image

# What counts as clean. A cell's outermost texels may hold no light at all
# (an 8-bit 1 is noise); past 0.97 of the way to its edge, next to none; and
# past 0.9, no more than 1% of the frame's light.
BORDER_MAX = 1.5 / 255
RIM_MAX = 4 / 255
RING_SHARE = 0.01
# How bright the clip may be at its own edge before the effect is taken to
# run out of frame (after the black floor is taken off).
SOURCE_EDGE_MAX = 0.08


def cell_faults(alpha, rgb=None):
    """What is wrong with one cell (alpha 0..1, square): a list of words, empty if clean."""
    n = alpha.shape[0]
    g = (np.arange(n) + 0.5) / n * 2 - 1
    r = np.sqrt(g[None, :] ** 2 + g[:, None] ** 2)
    faults = []
    b = max(1, n // 64)
    border = np.concatenate([alpha[:b].ravel(), alpha[-b:].ravel(), alpha[:, :b].ravel(), alpha[:, -b:].ravel()])
    if rgb is not None:
        cb = np.concatenate([rgb[:b].reshape(-1, rgb.shape[2]), rgb[-b:].reshape(-1, rgb.shape[2]),
                             rgb[:, :b].reshape(-1, rgb.shape[2]), rgb[:, -b:].reshape(-1, rgb.shape[2])])
        border = np.maximum(border, cb.max(axis=1))
    if border.max() > BORDER_MAX:
        faults.append(f"border {border.max() * 255:.0f}/255")
    rim = alpha[r > 0.97]
    if rim.size and rim.max() > RIM_MAX:
        faults.append(f"rim {rim.max() * 255:.0f}/255")
    total = alpha.sum()
    if total > 1:
        share = float(alpha[r > 0.9].sum() / total)
        if share > RING_SHARE:
            faults.append(f"{share * 100:.1f}% of its light near the edge")
    return faults


def atlas_faults(atlas, grid, frames):
    """Each faulty frame of an atlas (float RGBA, 0..1): [(frame, [words])]."""
    cell = atlas.shape[0] // grid
    bad = []
    for k in range(frames):
        y, x = divmod(k, grid)
        c = atlas[y * cell:(y + 1) * cell, x * cell:(x + 1) * cell]
        f = cell_faults(c[..., 3], c[..., :3])
        if f:
            bad.append((k, f))
    return bad


def check(path):
    meta = json.load(open(path.rsplit(".", 1)[0] + ".json"))
    atlas = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255.0
    bad = atlas_faults(atlas, meta["grid"], meta["frames"])
    for k, f in bad:
        print(f"{path} frame {k}: " + ", ".join(f))
    print(f"{path}: {'REFUSED' if bad else 'clean'} ({len(bad)} of {meta['frames']} frames at fault)")
    return not bad


def clean(path):
    """An atlas already made, brought inside its cells: each cell faded to
    nothing round its edge (from nine tenths of the way out) and its colour
    held under its alpha. For atlases whose clip is gone or whose look must
    not change; a new one is cut clean."""
    meta = json.load(open(path.rsplit(".", 1)[0] + ".json"))
    atlas = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255.0
    grid = meta["grid"]
    cell = atlas.shape[0] // grid
    g = (np.arange(cell) + 0.5) / cell * 2 - 1
    r = np.sqrt(g[None, :] ** 2 + g[:, None] ** 2)
    edge = np.clip((0.985 - r) / 0.085, 0, 1)
    # The outermost texels to nothing, whatever the circle leaves there.
    b = max(1, cell // 64)
    edge[:b] = edge[-b:] = 0
    edge[:, :b] = edge[:, -b:] = 0
    edge = (edge * edge * (3 - 2 * edge)).astype(np.float32)
    tile = np.tile(edge, (grid, grid))
    atlas[..., 3] *= tile
    atlas[..., :3] = np.minimum(atlas[..., :3] * tile[..., None], atlas[..., 3:4])
    Image.fromarray((atlas * 255 + 0.5).astype(np.uint8), "RGBA").save(path)
    return check(path)


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--check", "--clean"):
        fn = check if sys.argv[1] == "--check" else clean
        ok = all([fn(p) for p in sys.argv[2:]])
        raise SystemExit(0 if ok else 2)
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("out")
    ap.add_argument("--force", action="store_true", help="write the atlas even when frames fail the edge check")
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
    i0, i1 = int(a.start * (n - 1)), int(a.end * (n - 1))
    # The clip must hold its whole effect: light at its own edge means the
    # camera cut it off, and a cut effect has a flat side whatever is done
    # to it after. The worst frame taken is named.
    fh, fw = frames.shape[1:3]
    eb = max(2, int(0.02 * min(fh, fw)))
    cut = []
    for k in range(i0, i1 + 1):
        f = np.clip((frames[k].max(axis=2) - a.floor) / (1 - a.floor), 0, 1)
        edge = max(f[:eb].max(), f[-eb:].max(), f[:, :eb].max(), f[:, -eb:].max())
        if edge > SOURCE_EDGE_MAX:
            cut.append((k, edge))
    if cut:
        k, e = max(cut, key=lambda c: c[1])
        print(f"the effect runs off the clip's edge in {len(cut)} of {i1 - i0 + 1} frames (worst: frame {k}, {e * 255:.0f}/255)")
        if not a.force:
            raise SystemExit(2)
    # Fade toward the clip's own edges first: an effect that fills its frame
    # (frost, lightning) is cut off there in straight lines, and the square
    # crop reaches past the frame's top and bottom, so those lines would show.
    band = 0.25 * min(fh, fw)
    yy = np.minimum(np.arange(fh), fh - 1 - np.arange(fh))[:, None]
    xx = np.minimum(np.arange(fw), fw - 1 - np.arange(fw))[None, :]
    border = np.clip(np.minimum(yy, xx) / band, 0, 1)
    border = (border * border * (3 - 2 * border)).astype(np.float32)
    frames *= border[None, :, :, None]
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
    # Never past the clip's own frame: its edge inside the cell would show as
    # a straight line however softly the cell fades. The round fade of the
    # cell then takes whatever reaches the frame's edge away to nothing.
    side = min(side, w, h)
    cx = min(max(cx, side / 2), w - side / 2)
    cy = min(max(cy, side / 2), h - side / 2)
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
    # No frame may carry light out to the edge of its cell: that shows in the
    # game as the square of the cell. Checked as it will be stored (8 bits).
    stored = np.round(atlas * 255) / 255
    bad = atlas_faults(stored, a.grid, count)
    for k, f in bad:
        print(f"frame {k}: " + ", ".join(f))
    if bad and not a.force:
        raise SystemExit(f"refused: {len(bad)} of {count} frames show light at the edge of their cell")
    Image.fromarray((atlas * 255 + 0.5).astype(np.uint8), "RGBA").save(a.out)
    meta = {"grid": a.grid, "frames": count, "fps": round(count / max(1e-3, (i1 - i0) / 24), 2), "source": a.clip.replace("\\", "/").split("/")[-1]}
    with open(a.out.rsplit(".", 1)[0] + ".json", "w") as fh:
        json.dump(meta, fh)
    print(f"{a.out}: {count} frames, {a.grid * a.cell}px, from {i1 - i0 + 1} of {n} source frames")


if __name__ == "__main__":
    main()
