"""A beast's bristles, drawn: the atlas its bristle cards cut from.

    python tools/creatures/bristles.py OUT.png [--size 1024] [--palette boar]

Each column is a clump of a kind, root at the top and tips at the bottom:
  crest  coarse bristles gathered at the root and splayed to separate
         spikes at the tips, with daylight between them: a boar's ridge,
         the hedge down its back that reads from above;
  fringe finer and closer, laid back (cheeks, shoulders, the hump's sides);
  tuft   gathered toward a point (the tail's end).
Drawn three times larger and shrunk, so every edge is soft; each bristle
runs from a near-black root through the hide's umber to a grizzled tip.
RGB is the paint (the crowd shader takes it as albedo), alpha the bristles
(cut at about 0.45); the gaps carry the nearest bristle's colour so
filtering at an edge takes no black from them.
"""
import argparse

import numpy as np

KINDS = ["crest"] * 4 + ["fringe"] * 3 + ["tuft"]

PALETTES = {
    # The Verge's tusker: roots near-black, the shaft a dark umber, and the
    # tips grizzled: rust, ash grey, and here and there a pale one.
    "boar": {"root": (12, 10, 8), "shaft": (36, 27, 20), "tips": [(118, 78, 48), (132, 122, 108), (92, 62, 42), (176, 160, 134)]},
}

SPEC = {
    #          count  root spread  splay   length       thickness (root px at 1024)
    "crest": (30, 0.10, 1.35, (0.55, 1.0), (3.2, 5.5)),
    "fringe": (60, 0.25, 0.5, (0.45, 0.9), (1.8, 3.0)),
    "tuft": (45, 0.22, -0.6, (0.6, 1.0), (1.6, 2.8)),
}


def padded(img):
    from scipy import ndimage
    have = img[..., 3] > 8
    _, (iy, ix) = ndimage.distance_transform_edt(~have, return_indices=True)
    img[..., :3] = img[iy, ix, :3]
    return img


def draw(path, size=1024, palette="boar", over=3, seed=7):
    from PIL import Image, ImageDraw
    pal = PALETTES[palette]
    cols = len(KINDS)
    cw, h = size // cols * over, size * over
    out = np.zeros((size, size, 4), np.float32)
    for col, kind in enumerate(KINDS):
        r = np.random.default_rng(seed * 100 + col)
        n, spread, splay, reach, thick = SPEC[kind]
        rgb = Image.new("RGB", (cw, h), (0, 0, 0))
        alpha = Image.new("L", (cw, h), 0)
        dc, da = ImageDraw.Draw(rgb), ImageDraw.Draw(alpha)
        for i in range(n):
            u = r.normal(0, spread)
            x0 = (0.5 + u) * cw
            # Where its tip ends up: pushed out from the middle (splayed), or in (gathered).
            x1 = (0.5 + u * (1 + splay) + r.normal(0, 0.06)) * cw
            length = r.uniform(*reach)
            t = np.linspace(0, length, 48)
            f = t / length
            bow = r.normal(0, 0.03) * cw
            xs = x0 + (x1 - x0) * f ** 1.3 + bow * np.sin(np.pi * f)
            ys = (0.01 + t * 0.98) * h
            xs = np.clip(xs, 2 * over, cw - 2 * over)
            w0 = r.uniform(*thick) * over
            tip = pal["tips"][r.integers(len(pal["tips"]))]
            grizzle = r.uniform(0.5, 0.75) if r.random() > 0.15 else 2.0     # a few stay dark to the tip
            dark = r.uniform(0.8, 1.15)
            for k in range(len(t) - 1):
                g = f[k]
                if g < 0.2:
                    m = g / 0.2
                    c = tuple(int((pal["root"][j] * (1 - m) + pal["shaft"][j] * m) * dark) for j in range(3))
                elif g < grizzle:
                    c = tuple(int(pal["shaft"][j] * dark) for j in range(3))
                else:
                    m = min(1.0, (g - grizzle) / 0.12)
                    c = tuple(int(pal["shaft"][j] * dark * (1 - m) + tip[j] * m) for j in range(3))
                w = max(1, int(round(w0 * (1 - 0.8 * g ** 1.4))))
                seg = [(xs[k], ys[k]), (xs[k + 1], ys[k + 1])]
                dc.line(seg, fill=c, width=w)
                da.line(seg, fill=255 if g < 0.92 else int(255 * (1 - (g - 0.92) / 0.08 * 0.6)), width=w)
        small_c = np.asarray(rgb.resize((cw // over, h // over), Image.LANCZOS), np.float32)
        small_a = np.asarray(alpha.resize((cw // over, h // over), Image.LANCZOS), np.float32)
        # Drawn over black: the colour un-premultiplied by its coverage.
        cov = np.maximum(small_a[..., None] / 255.0, 0.35)
        small_c = np.where(small_a[..., None] > 4, np.clip(small_c / cov, 0, 255), 0)
        x = col * (size // cols)
        out[:, x:x + cw // over, :3] = small_c
        out[:, x:x + cw // over, 3] = small_a
    Image.fromarray(np.clip(padded(out), 0, 255).astype(np.uint8)).save(path)
    return {"columns": KINDS, "path": path}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--palette", default="boar")
    a = ap.parse_args()
    print(draw(a.out, a.size, a.palette))
