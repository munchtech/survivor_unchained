"""Measure a Flare clip folder (tools/fx/flare_clip.py's output) by numbers, H7 phase A (the stop, the grade, the budget).

  python tools/fx/flare_measure.py NAME [NAME ...] [--pre 1.0]

For each folder in C:/Users/munch/Desktop/survivorsunchained_inputs/flare_h7/NAME/:
  (a) hold: mean absolute pixel difference (0-255, sRGB) between f+0.12 and f+0.32 outside a 120 px circle round her;
  (b) grade at f+0.22 against f-0.10: mean luminance ratio; the world's shade (pixels under the frame's median
      luminance, outside a 250 px circle round her) as Oklab hue (deg) and chroma; the share of chroma that is warm
      (Oklab hue 20-110 deg) outside that circle;
  (c) FLARE_LOOK 1.6's budget over clip.mp4 from the press to +3 s (every frame, 480x270): the peak mean luminance
      against the pre-press frame and how many frames sit over 1.5x; the worst frame's share of pixels over the knee
      (sRGB value 0.95); whole-frame swings (a frame mean 20%+ above the mean 6 frames before) per second, the worst 1 s;
  (d) the log's 'flare marks' line (rings drawn against FlareMarks.Count).
Her screen point is the log's 'flare her screen X,Y' line, else (960, 536).
"""
import argparse, re, subprocess
from pathlib import Path
import numpy as np
from PIL import Image

OUT = Path("C:/Users/munch/Desktop/survivorsunchained_inputs/flare_h7")
FFMPEG = "C:/Users/munch/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"


def lin(a):
    a = a / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def oklab(rgb_lin):
    r, g, b = rgb_lin[..., 0], rgb_lin[..., 1], rgb_lin[..., 2]
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, A, B


def lum(rgb8):
    x = lin(rgb8.astype(np.float64))
    return 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]


def frame(d, o):
    return np.asarray(Image.open(d / f"f{o:+.2f}.png").convert("RGB"))


def outside(shape, c, r):
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    return (xx - c[0]) ** 2 + (yy - c[1]) ** 2 > r * r


def measure(name, pre):
    d = OUT / name
    log = (d / "log.txt").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"flare her screen (\d+),(\d+)", log)
    her = (int(m.group(1)), int(m.group(2))) if m else (960, 536)
    print(f"== {name} (her at {her[0]},{her[1]})")
    # (a)
    f1, f2 = frame(d, 0.12).astype(np.int16), frame(d, 0.32).astype(np.int16)
    out120 = outside(f1.shape, her, 120)
    print(f"(a) hold: mean |f+0.32 - f+0.12| outside 120 px = {np.abs(f2 - f1).mean(axis=2)[out120].mean():.2f}")
    # (b)
    f0, fg = frame(d, -0.10), frame(d, 0.22)
    l0, lg = lum(f0), lum(fg)
    out250 = outside(fg.shape, her, 250)
    L, A, B = oklab(lin(fg.astype(np.float64)))
    C = np.hypot(A, B)
    H = np.degrees(np.arctan2(B, A)) % 360
    shade = out250 & (lg < np.median(lg))
    sh_a, sh_b = A[shade].mean(), B[shade].mean()
    warm = (H >= 20) & (H <= 110)
    print(f"(b) grade: mean lum f+0.22 / f-0.10 = {lg.mean() / max(l0.mean(), 1e-6):.3f} ({lg.mean():.4f} / {l0.mean():.4f}); "
          f"shade Oklab hue {np.degrees(np.arctan2(sh_b, sh_a)) % 360:.0f} deg, chroma {np.hypot(sh_a, sh_b):.3f} (mean C {C[shade].mean():.3f}); "
          f"warm share of chroma outside her pool {C[out250 & warm].sum() / max(C[out250].sum(), 1e-9):.2%}")
    L0, A0, B0 = oklab(lin(f0.astype(np.float64)))
    H0 = np.degrees(np.arctan2(B0, A0)) % 360
    C0 = np.hypot(A0, B0)
    print(f"    (f-0.10 for reference: warm share {C0[out250 & (H0 >= 20) & (H0 <= 110)].sum() / max(C0[out250].sum(), 1e-9):.2%})")
    # (c)
    w, h = 480, 270
    raw = subprocess.run([FFMPEG, "-loglevel", "error", "-ss", f"{max(0, pre - 0.1):.3f}", "-t", "3.1", "-i", str(d / "clip.mp4"),
                          "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    means = np.array([lum(x).mean() for x in fr])
    knee = np.array([(x.max(axis=2) >= 242).mean() for x in fr])
    base = means[0]
    ratio = means / max(base, 1e-6)
    over = int((ratio > 1.5).sum())
    swings = [i for i in range(6, len(means)) if means[i] > 1.2 * means[i - 6] and (i == 6 or not means[i - 1] > 1.2 * means[i - 7])]
    worst = max((sum(1 for s in swings if i <= s < i + 60) for i in range(len(means))), default=0)
    print(f"(c) budget over {len(fr)} frames: peak mean lum {ratio.max():.2f}x pre-press (frames over 1.5x: {over}); "
          f"worst over-knee share {knee.max():.2%} (frame {int(knee.argmax())}); swings {len(swings)}, worst 1 s {worst}")
    # (d)
    for line in re.findall(r"flare marks .*", log) + re.findall(r"flare hover .*", log) + re.findall(r"flare grade: .*", log):
        print("(d)", line.strip())


ap = argparse.ArgumentParser()
ap.add_argument("names", nargs="+")
ap.add_argument("--pre", type=float, default=1.0)
a = ap.parse_args()
for n in a.names:
    measure(n, a.pre)
