"""A beast's bristles, drawn: the atlas its bristle cards cut from.

    python tools/creatures/bristles.py OUT.png [--size 1024] [--palette boar]

Each column is a clump of a kind, root at the top and tips at the bottom:
  crest  long, stiff, coarse bristles, standing apart, split at the tips
         (a boar's ridge, the hedge down its back that reads from above);
  fringe shorter and denser, laid closer (cheeks, shoulders, the hump);
  tuft   gathered toward a point (the tail's end).
Drawn three times larger and shrunk, so every edge is soft; the colour runs
from the root's near-black through the hide's brown to grizzled tips, each
bristle a little different. RGB is the paint (the crowd shader takes it as
albedo), alpha the bristles (cut at about 0.45); the gaps carry the nearest
bristle's colour so filtering at an edge takes no black from them.
"""
import argparse

import numpy as np

KINDS = ["crest"] * 4 + ["fringe"] * 3 + ["tuft"]

PALETTES = {
    # The Verge's tusker: roots near-black, the shaft a dark umber, and the
    # last third grizzled: rust, ash grey, and here and there a pale tip.
    "boar": {"root": (14, 11, 9), "shaft": (38, 28, 21), "tips": [(110, 72, 44), (128, 118, 104), (84, 58, 40), (168, 150, 124)]},
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
        n = {"crest": 70, "fringe": 160, "tuft": 90}[kind]
        spread = {"crest": 0.22, "fringe": 0.24, "tuft": 0.16}[kind]
        reach = {"crest": (0.55, 1.0), "fringe": (0.45, 0.85), "tuft": (0.6, 1.0)}[kind]
        gather = {"crest": (-0.25, 0.15), "fringe": (-0.1, 0.2), "tuft": (0.5, 0.9)}[kind]
        thick = {"crest": (2.6, 4.2), "fringe": (1.6, 2.6), "tuft": (1.4, 2.4)}[kind]
        rgb = Image.new("RGB", (cw, h), (0, 0, 0))
        alpha = Image.new("L", (cw, h), 0)
        dc, da = ImageDraw.Draw(rgb), ImageDraw.Draw(alpha)
        for i in range(n):
            x0 = np.clip(r.normal(0.5, spread), 0.04, 0.96) * cw
            t0 = r.uniform(0.0, 0.03)
            t1 = min(1.0, t0 + r.uniform(*reach))
            t = np.linspace(t0, t1, 60)
            f = (t - t0) / (t1 - t0)
            # Stiff: one gentle bend each, no waves; a crest bristle fans out
            # from the clump (splayed), a tuft's come together.
            bend = r.normal(0, 0.05) * cw
            xs = x0 + (cw / 2 - x0) * r.uniform(*gather) * f ** 1.5 + bend * f ** 2
            ys = t * h
            w0 = r.uniform(*thick) * over
            tip = pal["tips"][r.integers(len(pal["tips"]))]
            grizzle = r.uniform(0.55, 0.8)       # where the tip colour starts
            dark = r.uniform(0.75, 1.1)
            for k in range(len(t) - 1):
                g = f[k]
                if g < 0.25:
                    a_ = g / 0.25
                    c = tuple(int((pal["root"][j] * (1 - a_) + pal["shaft"][j] * a_) * dark) for j in range(3))
                elif g < grizzle:
                    c = tuple(int(pal["shaft"][j] * dark) for j in range(3))
                else:
                    a_ = min(1, (g - grizzle) / 0.15)
                    c = tuple(int(pal["shaft"][j] * dark * (1 - a_) + tip[j] * a_) for j in range(3))
                w = max(1, int(round(w0 * (1 - 0.8 * g))))
                seg = [(xs[k], ys[k]), (xs[k + 1], ys[k + 1])]
                dc.line(seg, fill=c, width=w)
                da.line(seg, fill=int(255 * (1 if g < 0.9 else (1 - g) / 0.1 * 0.8 + 0.2)), width=w)
            # A split end on the coarse ones: two short hairs off the tip.
            if kind == "crest" and r.random() < 0.6:
                for s in (-1, 1):
                    end = (xs[-1], ys[-1])
                    da.line([(xs[-6], ys[-6]), (end[0] + s * r.uniform(2, 6) * over, end[1] + r.uniform(0, 4) * over)], fill=150, width=max(1, int(w0 * 0.25)))
                    dc.line([(xs[-6], ys[-6]), (end[0] + s * r.uniform(2, 6) * over, end[1] + r.uniform(0, 4) * over)], fill=tip, width=max(1, int(w0 * 0.25)))
        small_c = np.asarray(rgb.resize((cw // over, h // over), Image.LANCZOS), np.float32)
        small_a = np.asarray(alpha.resize((cw // over, h // over), Image.LANCZOS), np.float32)
        # Colour drawn over black: un-premultiply by the coverage.
        cov = np.maximum(small_a[..., None] / 255.0, 1e-3)
        small_c = np.where(small_a[..., None] > 4, np.clip(small_c / np.maximum(cov, 0.35), 0, 255), 0)
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
