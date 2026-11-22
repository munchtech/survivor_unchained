"""Film the den at the game camera, 1:1 (1920x1080, 60 fps fixed), for the Godot 4.5 -> 4.7 look comparison.

  GODOT=<console exe> python tools/scratch/godot47/den_film.py TAG [SECONDS]

The den (hollow dungeon on a test map, seed 1) from its mouth with its foes, the autopilot fighting through, HUD on.
--fixed-fps makes each frame one 1/60 s step, so both engines play the same takes frame for frame as far as the sim
is deterministic. Output: godot/.shots/godot47/film_TAG.mp4 (H.264 crf 16) and film_TAG.log; the AVI is deleted.
One godot turn (tools/turn.py), given back in a finally.
"""
import os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GODOT = os.environ.get("GODOT", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe")
FFMPEG = "C:/Users/munch/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
TURN = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
FPS = 60


def main():
    tag = sys.argv[1]
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 45
    out = ROOT / "godot" / ".shots" / "godot47"
    out.mkdir(parents=True, exist_ok=True)
    avi = out / f"film_{tag}.avi"
    frames = int(secs * FPS)
    gargs = [GODOT, "--path", str(ROOT / "godot"), "--resolution", "1920x1080", "--write-movie", str(avi),
             "--fixed-fps", str(FPS), "--audio-driver", "Dummy", "--quit-after", str(frames), "--",
             "--quick", "warden", "--sex", "female", "--zone", "map", "--dungeon", "hollow", "--seed", "1", "--auto", "human"]
    label = f"p1-godot47: film {tag}"
    subprocess.run([sys.executable, TURN, "take", "godot", label, "--wait", "1800", "--stale-ok"], check=True)
    try:
        print("RUN", " ".join(gargs), flush=True)
        with open(out / f"film_{tag}.log", "w", encoding="utf-8", errors="replace") as lf:
            r = subprocess.run(gargs, stdout=lf, stderr=subprocess.STDOUT)
        print(f"exit {r.returncode}", flush=True)
    finally:
        subprocess.run([sys.executable, TURN, "give", "godot", label])
    if avi.exists():
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(avi), "-r", str(FPS), "-c:v", "libx264", "-crf", "16",
                        "-pix_fmt", "yuv420p", "-an", str(out / f"film_{tag}.mp4")], check=True)
        avi.unlink()
        print("film", out / f"film_{tag}.mp4")


if __name__ == "__main__":
    main()
