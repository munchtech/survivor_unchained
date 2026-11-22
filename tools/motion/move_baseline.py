"""Shoot the movement baseline's takes (--moves12, godot/src/Game/MoveShots.cs) at 1:1 (1920x1080, 60 fps).

  python tools/motion/move_baseline.py [s01,s03,...|all]

One godot turn (tools/turn.py) for the whole batch, given back in a finally. Per take it runs the game in her den (Warden, hollow dungeon
on a test map, at the ruler's clearing's middle plus START_OFF, no foes, facing mode always, no cinematics), with the scripted input and
the logs of MoveShots. Output per take: godot/.shots/move_baseline/TAKE/ (git-ignored) with log.txt, ticks.csv, frames.csv and clip.mp4
(the movie cut from S0-0.5 s to END, H.264 crf 18, yuv420p, 60 fps); the AVI is deleted. The clearing's radius is printed from the log
("at boss-mid: ruler's clearing (x, z) r R"), to check the start offsets against.
"""
import os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GODOT = os.environ.get("GODOT", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe")
FFMPEG = "C:/Users/munch/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
TURN = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
FPS = 60

# --at-off DX,DZ: metres from the clearing's middle, where she stands at S0. Change here.
START_OFF = {
    "s01": (-8, 0), "s03": (-5, 0), "s04": (-6, 5), "s05": (-4, 3), "s06": (0, -4), "s07": (0, 4), "s08": (-3, 3), "s09": (-9, 0),
    "s10a": (-7, 4), "s10b": (-7, 0), "s10c": (-7, 4), "s10d": (0, -2), "s10e": (0, -8), "s11": (-9, 0), "s12": (-6, 0),
    "s13": (-5, 0), "s12d": None,
    "p01": (-8, 0), "p03": (-5, 0), "p08": (-3, 3), "p08b": (-3, 3), "p10a": (-7, 4), "p10b": (-7, 0),
}
# Takes in a den room with foes on (not boss-mid, no --no-foes, no --at-off): her start is --at X,Z beside a pack.
# env S12D_AT=default boots at the den's own arrival (with --moves12-foes, to list where the packs stand).
DEN_AT = {"s12d": "58,104"}   # a pack of 5 wolves stands near (58, 89) at seed 1; at S0 (fight time 2 s) they are 5-9 m up-screen (-Z, key W) of this spot
EXTRA_ARGS = {"s12d": ["--moves12-at", "2"]}   # s12d: S0 at fight time 2 s, while the arrival pack still stands 7-9 m off   # per take: extra game flags, e.g. {"s01": ["--moves12-at", "5"]}


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else "all"
    takes = list(START_OFF) if want == "all" else [t.strip() for t in want.split(",") if t.strip()]
    for t in takes:
        if t not in START_OFF:
            sys.exit(f"unknown take {t}; known: {' '.join(START_OFF)}")
    ov = ROOT / "godot" / "override.cfg"
    if ov.exists():
        ov.unlink()
    label = os.environ.get("TURN_LABEL", "task1: moves12")
    subprocess.run([sys.executable, TURN, "take", "godot", label, "--wait", "1800"], check=True)
    try:
        for t in takes:
            run_take(t)
    finally:
        subprocess.run([sys.executable, TURN, "give", "godot", label])


def run_take(t):
    out = ROOT / "godot" / ".shots" / os.environ.get("MOVES_OUT", "move_baseline") / t
    out.mkdir(parents=True, exist_ok=True)
    for old in ("ticks.csv", "frames.csv", "clip.mp4", "movie.avi"):
        (out / old).unlink(missing_ok=True)
    avi = out / "movie.avi"
    inp = "pad" if t.startswith("p") else "kbm"
    flags = os.environ.get("MOVES_FLAGS", "").split()
    if t in DEN_AT:
        at = os.environ.get("S12D_AT", DEN_AT[t])
        place = [] if at in ("default", "DISCOVER") else ["--at", at]
        boot = ["--quick", "warden", "--zone", "map", "--dungeon", "hollow", "--seed", "1"] + place + ["--facing-mode", "always", "--nocine"]
        boot += ["--moves12-foes"]   # lists the living foes at S0-2 s and S0 in log.txt
    else:
        dx, dz = START_OFF[t]
        boot = ["--quick", "warden", "--zone", "map", "--dungeon", "hollow", "--seed", "1", "--at", "boss-mid", "--at-off", f"{dx},{dz}",
                "--no-foes", "--facing-mode", "always", "--nocine"]
    gargs = [GODOT, "--path", str(ROOT / "godot"), "--resolution", "1920x1080", "--write-movie", str(avi),
             "--fixed-fps", str(FPS), "--audio-driver", "Dummy", "--quit-after", "9000", "--"] + boot + [
             "--moves12", t, "--moves12-input", inp, "--moves12-out", str(out)] + EXTRA_ARGS.get(t, []) + flags
    print("RUN", " ".join(gargs), "| MOVES_FLAGS:", " ".join(flags) or "(none)", flush=True)
    with open(out / "log.txt", "w", encoding="utf-8", errors="replace") as lf:
        r = subprocess.run(gargs, stdout=lf, stderr=subprocess.STDOUT)
    log = (out / "log.txt").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"at boss-mid: ruler's clearing \(([-\d.]+), ([-\d.]+)\) r ([\d.]+)", log)
    s0 = re.search(r"MOVES12 S0 frame (\d+)", log)
    end = re.search(r"MOVES12 END frame (\d+)", log)
    print(f"{t}: exit {r.returncode}; clearing r {m[3] if m else '?'}; S0 frame {s0[1] if s0 else '-'}; END frame {end[1] if end else '-'}", flush=True)
    if avi.exists() and s0 and end:
        a = max(0, int(s0[1]) - FPS // 2)
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(avi), "-ss", f"{a / FPS:.4f}", "-t", f"{(int(end[1]) - a) / FPS:.4f}",
                        "-r", str(FPS), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(out / "clip.mp4")], check=True)
    if avi.exists():
        avi.unlink()


if __name__ == "__main__":
    main()
