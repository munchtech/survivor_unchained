"""Side by side of two den films (4.5.1 left, 4.7.2 right) at chosen seconds, and the numbers that tell a look change.

  python tools/scratch/godot47/compare.py FILM_A FILM_B OUT_DIR [SECONDS,...]

Per second: both frames (1:1 PNG), their mean luma, mean RGB, share of pixels near white (luma > 0.9: glow),
mean luma of the darkest and brightest tenths, and the mean absolute difference between the two frames. A sheet
sheet.png puts each pair side by side at half size (960x540 each), rows top to bottom in time order.
"""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

FFMPEG = "C:/Users/munch/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"


def frame(film, t, png):
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(film), "-frames:v", "1", str(png)], check=True)
    return np.asarray(Image.open(png).convert("RGB")).astype(np.float32) / 255


def stats(a):
    l = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    s = np.sort(l.ravel())
    n = len(s) // 10
    return dict(luma=l.mean(), rgb=a.reshape(-1, 3).mean(0), white=(l > 0.9).mean() * 100, dark10=s[:n].mean(), bright10=s[-n:].mean())


def main():
    fa, fb, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    secs = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else [28, 31, 34, 37, 40, 43]
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    print("sec | luma A/B | R,G,B A | R,G,B B | white% A/B | dark10 A/B | bright10 A/B | MAE")
    for t in secs:
        a = frame(fa, t, out / f"a_{t:g}.png")
        b = frame(fb, t, out / f"b_{t:g}.png")
        sa, sb = stats(a), stats(b)
        mae = np.abs(a - b).mean()
        print(f"{t:g} | {sa['luma']:.4f}/{sb['luma']:.4f} | {','.join(f'{v:.3f}' for v in sa['rgb'])} | {','.join(f'{v:.3f}' for v in sb['rgb'])} | "
              f"{sa['white']:.2f}/{sb['white']:.2f} | {sa['dark10']:.4f}/{sb['dark10']:.4f} | {sa['bright10']:.4f}/{sb['bright10']:.4f} | {mae:.4f}")
        half = lambda x: Image.fromarray((x * 255).astype(np.uint8)).resize((960, 540), Image.LANCZOS)
        row = Image.new("RGB", (1920, 540))
        row.paste(half(a), (0, 0)); row.paste(half(b), (960, 0))
        rows.append(row)
    sheet = Image.new("RGB", (1920, 540 * len(rows)))
    for i, r in enumerate(rows):
        sheet.paste(r, (0, 540 * i))
    sheet.save(out / "sheet.png")
    print("sheet", out / "sheet.png")


if __name__ == "__main__":
    main()
