"""A capture for the owner: a run's 60 fps frames (godot/.shots/NAME_N.png) and its --wav tape, muxed to an mp4.

    python tools/fxsim/cap.py NAME WAV START OUT.mp4 [--fps 60] [--offset 0]

START is the game second the first frame was shot at (the run's --seconds); the tape runs from the game's start,
so it is cut at START (+ --offset, to fix any lag measured between the BOOM's transient and its frame).
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

import imageio_ffmpeg

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", ".shots")


def main():
    name, wav, start, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
    av = sys.argv[5:]
    fps = float(av[av.index("--fps") + 1]) if "--fps" in av else 60.0
    off = float(av[av.index("--offset") + 1]) if "--offset" in av else 0.0
    fs = sorted(glob.glob(os.path.join(SHOTS, f"{name}_[0-9]*.png")), key=lambda p: int(p.rsplit("_", 1)[1][:-4]))
    if not fs:
        print("no frames for", name); sys.exit(1)
    tmp = tempfile.mkdtemp(prefix="cap_", dir=SHOTS)
    try:
        for i, f in enumerate(fs):
            shutil.copyfile(f, os.path.join(tmp, f"{i:04d}.png"))
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [ff, "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(tmp, "%04d.png"),
               "-ss", f"{start + off:.4f}", "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow",
               "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-shortest", out]
        subprocess.run(cmd, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("CAPTURE", out, len(fs), "frames", f"{len(fs) / fps:.2f}s")


main()
