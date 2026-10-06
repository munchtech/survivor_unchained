"""Run the game for skill pictures, from the skills worktree.

    python shot.py NAME [game args after --...]

Frames land in godot/.shots/ of the skills worktree. The engine runs at a
fixed 60 fps so a frame sequence is evenly spaced in game time however long
a screenshot takes to save."""
import os
import subprocess
import sys

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a560452c597415545\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"

name = sys.argv[1]
extra = sys.argv[2:]
args = [GODOT, "--path", WT, "--resolution", "1920x1080", "--fixed-fps", "60", "--audio-driver", "Dummy", "--", "--shot", name] + extra
shots = os.path.join(WT, ".shots")
for f in os.listdir(shots) if os.path.isdir(shots) else []:
    # Only this run's own frames: a base run's name is the start of its evolutions' names too.
    import re
    if f == name + ".png" or re.fullmatch(re.escape(name) + r"_(\d\d|(evolve|fall|focus|morning|chid|result|say_[a-z_]+)_\d+)\.png", f):
        os.remove(os.path.join(shots, f))
try:
    out = subprocess.run(args, capture_output=True, text=True, timeout=900, encoding="utf-8", errors="replace")
    text = out.stdout + out.stderr
except subprocess.TimeoutExpired as e:
    text = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
    print("TIMEOUT")
saved = [l for l in text.splitlines() if "saved" in l]
errs = [l for l in text.splitlines() if ("ERROR" in l or "Exception" in l or "SHADER" in l) and "saved" not in l and "leaked" not in l and "get_singleton" not in l]
print(f"{len(saved)} frames")
for l in errs[:12]:
    print("ERR", l[:300])
