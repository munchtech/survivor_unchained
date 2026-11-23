"""Old against new, side by side: the same take shot twice (two folders under godot/.shots), the two clips in one film.

  python tools/motion/move_films.py BEFORE AFTER OUT [take,take,...]

For each take present in godot/.shots/BEFORE and godot/.shots/AFTER (or the listed ones, if present in both) writes
godot/.shots/OUT/TAKE_old_new.mp4: the two clip.mp4 side by side, each scaled to 960 wide (never cropped, the game camera frame
whole), "OLD" top-left of the left half and "NEW" top-left of the right. Without a font for drawtext, a 40 px strip on top
carries no text (and the script says so).
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "godot/.shots"
FFMPEG = "C:/Users/munch/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
FONT = r"C\:/Windows/Fonts/arialbd.ttf"   # ffmpeg filter escaping of "C:/Windows/Fonts/arialbd.ttf"


def graph(text):
    if text:
        lab = lambda t, x: f"drawtext=fontfile='{FONT}':text='{t}':x={x}+12:y=10:fontsize=40:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=6"
        return f"[0:v]scale=960:-2[a];[1:v]scale=960:-2[b];[a][b]hstack=inputs=2,{lab('OLD', 0)},{lab('NEW', 960)}[v]"
    return "[0:v]scale=960:-2[a];[1:v]scale=960:-2[b];[a][b]hstack=inputs=2,pad=iw:ih+40:0:40[v]"


def main():
    if len(sys.argv) < 4: sys.exit(__doc__)
    before, after, out = (SHOTS / a for a in sys.argv[1:4])
    want = [t.strip() for t in sys.argv[4].split(",") if t.strip()] if len(sys.argv) > 4 else sorted(p.name for p in before.iterdir() if p.is_dir())
    out.mkdir(parents=True, exist_ok=True)
    fontless = not Path(FONT.replace("\\", "")).exists()
    for t in want:
        a, b = before / t / "clip.mp4", after / t / "clip.mp4"
        if not (a.exists() and b.exists()): continue
        dst = out / f"{t}_old_new.mp4"
        for text in ([] if fontless else [True]) + [False]:
            r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(a), "-i", str(b), "-filter_complex", graph(text), "-map", "[v]",
                                "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "60", "-an", str(dst)], capture_output=True, text=True)
            if r.returncode == 0:
                print(f"{dst}: {t}, OLD left / NEW right" + ("" if text else " (no drawtext font: a 40 px strip on top, no labels)"))
                break
        else: print(f"{t}: ffmpeg failed: {r.stderr[-300:]}")


if __name__ == "__main__":
    main()
