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
    # (c2) which frames are over: offsets from the press (frames), so a bright frame can be laid against the log's beats
    bright = [i - 6 for i in range(len(ratio)) if ratio[i] > 1.5]
    knees = [i - 6 for i in range(len(knee)) if knee[i] > 0.03]
    bm = re.search(r"flare blow \S+: main \S+ at \+([\d.]+) s real", log)
    rl = re.search(r"flare release frame (\d+) at \+([\d.]+) s", log)
    print(f"    over 1.5x at press+{bright[:12]}{'...' if len(bright) > 12 else ''} frames; over knee 3% at {knees[:12]}; "
          f"release +{float(rl.group(2)) * 60 if rl else float('nan'):.0f} f, main blow +{float(bm.group(1)) * 60 if bm else float('nan'):.0f} f")
    # (a2) the true hold: f+0.12 against the stop's last held frame (two before the release), and the frame-to-frame motion
    # inside the stop over clip.mp4 (480x270, outside 30 px round her, the HUD's bottom 40 px left out)
    if (d / "f_stop_end.png").exists() and rl:
        fe = np.asarray(Image.open(d / "f_stop_end.png").convert("RGB")).astype(np.int16)
        span = float(rl.group(2)) - 2 / 60 - 0.12
        print(f"(a2) true hold: mean |stop end - f+0.12| outside 120 px = {np.abs(fe - f1).mean(axis=2)[out120].mean():.2f} over {span:.2f} s")
        hh = outside((h, w), (her[0] / 4, her[1] / 4), 30)
        hh[h - 40:] = False
        r0, r1 = 6 + 7, 6 + int(round(float(rl.group(2)) * 60)) - 2
        steps = [np.abs(fr[i].astype(np.int16) - fr[i - 1]).mean(axis=2)[hh].mean() for i in range(r0 + 1, min(r1 + 1, len(fr)))]
        if steps: print(f"     frame-to-frame in the stop (press+8..release-2): mean {np.mean(steps):.2f}, max {np.max(steps):.2f}")
        # (after the camera's push-in, 0.18 s, FLARE_LOOK §1.4: what still moves while the world is held; the pre-press
        # frame-to-frame is the floor, TAA's and the fight's)
        h0 = 6 + 12
        held = [np.abs(fr[i].astype(np.int16) - fr[i - 1]).mean(axis=2)[hh].mean() for i in range(h0 + 1, min(r1 + 1, len(fr)))]
        pre_s = [np.abs(fr[i].astype(np.int16) - fr[i - 1]).mean(axis=2)[hh].mean() for i in range(1, 6)]
        if held: print(f"     held (press+12..release-2, after the push): frame-to-frame mean {np.mean(held):.2f}, max {np.max(held):.2f}; before the press {np.mean(pre_s):.2f}")
    # (e) loudness (long.wav: 4 s of fight before the press): short-term (3 s) LUFS max of the fight before the press against
    # the blow's (windows starting from the press), the stop's momentary (0.4 s) loudness of the flare stem and of the rest,
    # and the sample peak from the press on
    if (d / "long.wav").exists():
        import soundfile as sf, pyloudnorm as pyln
        tape, sr = sf.read(str(d / "long.wav"), dtype="float64", always_2d=True)
        stem, _ = sf.read(str(d / "long_flare.wav"), dtype="float64", always_2d=True)
        ps = float((d / "long.txt").read_text().split()[1])
        meter = pyln.Meter(sr)
        def lufs(x, a0, a1):
            a0, a1 = max(0, int(a0 * sr)), min(len(x), int(a1 * sr))
            if a1 - a0 < int(0.4 * sr): return float("nan")
            with np.errstate(divide="ignore"):
                v = meter.integrated_loudness(x[a0:a1]) if a1 - a0 >= int(0.4 * sr) else float("nan")
            return v
        def st_max(x, t0, t1, win):
            vals = [lufs(x, s, s + win) for s in np.arange(t0, t1 - win + 1e-6, 0.1)]
            vals = [v for v in vals if np.isfinite(v)]
            return max(vals) if vals else float("nan")
        fight = st_max(tape, max(0, ps - 3.0 - 0.95), ps, 3.0)
        tb = (float(bm.group(1)) if bm else 0.5)
        blow = st_max(tape, ps, min(len(tape) / sr, ps + tb + 3.0), 3.0)
        blow_m = st_max(tape, ps + tb - 0.1, ps + tb + 0.8, 0.4)
        fight_m = st_max(tape, ps - 3.0, ps, 0.4)
        stopl = float(rl.group(2)) if rl else 0.35
        world = tape - stem
        w_pre = lufs(world, ps - 0.5, ps - 0.05)
        w_stop = lufs(world, ps + 0.05, ps + max(0.45, stopl))
        s_stop = lufs(stem, ps + 0.05, ps + max(0.45, stopl))
        peak = 20 * np.log10(max(1e-9, np.abs(tape[int(ps * sr):]).max()))
        print(f"(e) loudness: short-term max fight {fight:.1f} LUFS, blow {blow:.1f} (blow - fight {blow - fight:+.1f} dB); momentary max "
              f"fight {fight_m:.1f}, blow {blow_m:.1f}; the stop: flare stem {s_stop:.1f}, the rest {w_stop:.1f} (before the press "
              f"{w_pre:.1f}: ducked {w_stop - w_pre:+.1f} dB); sample peak from the press {peak:.1f} dBFS")
    ids = re.findall(r"\[soundlog\] (flare\.\S+) (\d+) (\w+)", log)
    if ids: print("(f) flare cues:", ", ".join(f"{i} x{n} {k}" for i, n, k in ids))
    # (d)
    for line in re.findall(r"flare marks .*", log) + re.findall(r"flare hover .*", log) + re.findall(r"flare grade: .*", log):
        print("(d)", line.strip())


ap = argparse.ArgumentParser()
ap.add_argument("names", nargs="+")
ap.add_argument("--pre", type=float, default=1.0)
a = ap.parse_args()
for n in a.names:
    measure(n, a.pre)
