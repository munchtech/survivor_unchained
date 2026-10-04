"""Pictures of a fight, for checking it as the player sees it.

    python tools/combat/shots.py NAME PEOPLE [game options...]

runs the game at 1920x1080 straight into an arena of PEOPLE (pack, dead,
lamplings, kerchiefs) and passes the rest through, e.g.

    python tools/combat/shots.py rh kerchiefs --tier 2 --minute 29.95 \
        --give "oathblade:8@oathkeeper,arcweb:8@tempest_coil,hoarfrost:8,+might:5" \
        --auto --on boss --until 150 --seconds 5 --every 15 --count 9

--on boss takes a frame of each boss move as it is marked, its Break, its
arrival and each announcement (godot/src/Shots.cs); --marks draws every
telegraph round the survivor; --boss DEF[:NAME] and --spare put a story's foe
at the half hour. Frames land in godot/.shots/ (not committed); the old frames
of NAME are cleared first. GODOT overrides the engine's path.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "godot"
GODOT = os.environ.get("GODOT", r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe")

name, people = sys.argv[1], sys.argv[2]
args = [GODOT, "--path", str(ROOT), "--resolution", "1920x1080", "--",
        "--quick", "warden", "--zone", "arena", "--people", people, "--shot", name] + sys.argv[3:]
shots = ROOT / ".shots"
if shots.is_dir():
    for f in shots.iterdir():
        if f.name.startswith(name + "_") or f.name == name + ".png":
            f.unlink()
try:
    out = subprocess.run(args, capture_output=True, text=True, timeout=900, encoding="utf-8", errors="replace")
    text = out.stdout + out.stderr
except subprocess.TimeoutExpired as e:
    text = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
    print("TIMEOUT")
saved = [l for l in text.splitlines() if "saved" in l]
print(f"{len(saved)} frames")
for l in saved:
    print(l.split("/")[-1])
for l in [l for l in text.splitlines() if ("ERROR" in l or "Exception" in l) and "saved" not in l][:20]:
    print("ERR", l[:300])
