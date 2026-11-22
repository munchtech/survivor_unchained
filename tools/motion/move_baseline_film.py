"""Task 1 (movement baseline): the takes' clips (tools/motion/move_baseline.py) joined into one film, in shot order.

  python tools/motion/move_baseline_film.py OUT.mp4

Each clip already carries its label and the input state drawn in game (MoveShots overlay). Order: shots 1+2 to 12 with
keyboard and mouse, then the pad takes (1+2, 3, 8, 10 across, 10 against).
"""
import subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "godot/.shots/move_baseline"
FFMPEG = "C:/Users/munch/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
ORDER = ["s01", "s03", "s04", "s05", "s06", "s07", "s08", "s09", "s10a", "s10b", "s10c", "s10d", "s10e", "s11", "s12", "p01", "p03", "p08", "p08b", "p10a", "p10b"]

out = Path(sys.argv[1])
clips = [D / t / "clip.mp4" for t in ORDER if (D / t / "clip.mp4").exists()]
missing = [t for t in ORDER if not (D / t / "clip.mp4").exists()]
lst = Path(tempfile.mkstemp(suffix=".txt", dir=str(D))[1])
lst.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "libx264", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "60", "-an", str(out)], check=True)
lst.unlink()
print(f"{out}: {len(clips)} clips; missing {missing}")
