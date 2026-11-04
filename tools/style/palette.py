"""The look bible's numbers (docs/design/LOOK_BIBLE.md): each frame's value structure and where its colour sits, in Oklab.

    python tools/style/palette.py DIR            -> every DIR/frames/NN_id.png (tools/style/frames.py's output); DIR/palette.md + DIR/palette.jpg
    python tools/style/palette.py a.png b.png    -> those files (whole frame), printed

Per frame, over the world (the HUD's bands cut off on play frames: y 8%-80% of the height; the full frame elsewhere):
  Lp50, Lp95   value: Oklab L percentiles (0-1); key   p95/p50 (how far the lit brights stand over the middle)
  pool         std/mean of L on a 32x18 downsample: light in pools (high) or flat (low)
  shC shH      the shadows (L < 0.32): mean chroma and its hue (Oklab degrees, chroma-weighted): the bible wants colour there
  gray%        share of the shadows that are grey (C < 0.015): slate, the thing the bible forbids
  midC         the mid values' chroma (0.40 <= L <= 0.75): dull midtones (mud, stone, cloth) gain the most under vibrance
  hiH hiC      the brights (L > 0.80): their hue and chroma (ember/lantern amber ~55-75, moon/frost ~230-260)
  warm/cold    the share of all chroma in warm hues (h 20-110) and cold ones (h 180-300)
palette.jpg: per frame its eight main colours (median cut over the world crop), dark to light, beside the frame's
thumbnail: the twelve read as one game when their strips share a family."""
import os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PLAY = {"04", "05", "06", "09", "10", "12"}   # frames with the HUD over the world


def oklab(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    l = 0.4122214708 * c[..., 0] + 0.5363325363 * c[..., 1] + 0.0514459929 * c[..., 2]
    m = 0.2119034982 * c[..., 0] + 0.6806995451 * c[..., 1] + 0.1073969566 * c[..., 2]
    s = 0.0883024619 * c[..., 0] + 0.2817188376 * c[..., 1] + 0.6299787005 * c[..., 2]
    l, m, s = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    b = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, a, b


def hue(a, b, w):
    if w.sum() <= 0: return float("nan")
    return float(np.degrees(np.arctan2((b * w).sum(), (a * w).sum())) % 360)


def stats(path, play):
    im = Image.open(path).convert("RGB")
    if play: im = im.crop((0, int(im.height * 0.08), im.width, int(im.height * 0.80)))
    sm = im.resize((480, int(480 * im.height / im.width)), Image.BILINEAR)
    x = np.asarray(sm).astype(np.float64)
    L, a, b = oklab(x); C = np.hypot(a, b); H = np.degrees(np.arctan2(b, a)) % 360
    p50, p95 = np.percentile(L, [50, 95])
    lo = np.asarray(im.resize((32, 18), Image.BOX)).astype(np.float64); Ll = oklab(lo)[0]
    sh = L < 0.32; mid = (L >= 0.40) & (L <= 0.75); hi = L > 0.80
    warm = ((H >= 20) & (H <= 110)); cold = ((H >= 180) & (H <= 300))
    r = dict(Lp50=p50, Lp95=p95, key=p95 / max(p50, 1e-3), pool=Ll.std() / max(Ll.mean(), 1e-3),
             shC=C[sh].mean() if sh.any() else float("nan"), shH=hue(a[sh], b[sh], C[sh]) if sh.any() else float("nan"),
             gray=(C[sh] < 0.015).mean() * 100 if sh.any() else float("nan"), sh=sh.mean() * 100,
             midC=C[mid].mean() if mid.any() else float("nan"),
             hiH=hue(a[hi], b[hi], C[hi]) if hi.any() else float("nan"), hiC=C[hi].mean() if hi.any() else float("nan"),
             warm=C[warm].sum() / max(C.sum(), 1e-6) * 100, cold=C[cold].sum() / max(C.sum(), 1e-6) * 100)
    q = sm.quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:24]).reshape(8, 3); cnt = np.bincount(np.asarray(q).ravel(), minlength=8)[:8]
    order = np.argsort(oklab(pal.astype(np.float64))[0])
    return r, [(tuple(int(v) for v in pal[i]), int(cnt[i])) for i in order], im


COLS = ["Lp50", "Lp95", "key", "pool", "shC", "shH", "gray", "midC", "hiH", "hiC", "warm", "cold"]


def row(name, r):
    f = lambda k: "-" if r[k] != r[k] else (f"{r[k]:.0f}" if k in ("shH", "hiH", "gray", "warm", "cold") else f"{r[k]:.3f}" if k in ("shC", "midC", "hiC") else f"{r[k]:.2f}")
    return f"| {name} | " + " | ".join(f(k) for k in COLS) + " |"


def main(args):
    if len(args) == 1 and os.path.isdir(args[0]):
        d = args[0]; fr = os.path.join(d, "frames")
        files = sorted(os.path.join(fr, f) for f in os.listdir(fr) if f.endswith(".png") and f[:2].isdigit())
    else:
        d, files = None, args
    lines = ["| frame | " + " | ".join(COLS) + " |", "|---" * (len(COLS) + 1) + "|"]
    strips = []
    for p in files:
        name = os.path.splitext(os.path.basename(p))[0]
        r, pal, im = stats(p, d is not None and name[:2] in PLAY)
        lines.append(row(name, r)); strips.append((name, pal, im))
    print("\n".join(lines))
    if d is None: return
    open(os.path.join(d, "palette.md"), "w", encoding="utf-8").write(
        "# The twelve frames' numbers (tools/style/palette.py)\n\n" + "\n".join(lines) + "\n")
    tw, th, sw = 320, 180, 80
    S = Image.new("RGB", (tw + sw * 8, th * len(strips)), (12, 12, 12)); dr = ImageDraw.Draw(S)
    try: font = ImageFont.truetype("arial.ttf", 16)
    except Exception: font = ImageFont.load_default()
    for k, (name, pal, im) in enumerate(strips):
        y = k * th
        S.paste(im.resize((tw, th), Image.LANCZOS), (0, y))
        tot = sum(c for _, c in pal) or 1
        for j, (col, c) in enumerate(pal):
            dr.rectangle([tw + j * sw, y, tw + (j + 1) * sw - 2, y + th - 2], fill=col)
            dr.text((tw + j * sw + 4, y + th - 20), f"{100 * c / tot:.0f}%", fill=(255, 255, 255) if sum(col) < 380 else (0, 0, 0), font=font)
        dr.rectangle([0, y, 10 * len(name) + 8, y + 20], fill=(0, 0, 0)); dr.text((4, y + 1), name, fill=(255, 230, 120), font=font)
    S.save(os.path.join(d, "palette.jpg"), quality=88)
    print(os.path.join(d, "palette.jpg"))


if __name__ == "__main__":
    if not sys.argv[1:]: print(__doc__); sys.exit(1)
    main(sys.argv[1:])
