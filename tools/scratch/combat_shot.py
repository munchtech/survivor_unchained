"""Run the game for boss pictures: python combat_shot.py NAME PEOPLE [extra game args...]
Frames land in godot/.shots/ of the combat worktree."""
import subprocess, sys, os, shutil

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"

name, people = sys.argv[1], sys.argv[2]
extra = sys.argv[3:]
args = [GODOT, "--path", WT, "--resolution", "1920x1080", "--",
        "--quick", "warden", "--zone", "arena", "--people", people, "--shot", name] + extra
shots = os.path.join(WT, ".shots")
for f in os.listdir(shots) if os.path.isdir(shots) else []:
    if f.startswith(name + "_") or f == name + ".png":
        os.remove(os.path.join(shots, f))
try:
    out = subprocess.run(args, capture_output=True, text=True, timeout=900, encoding="utf-8", errors="replace")
    text = out.stdout + out.stderr
except subprocess.TimeoutExpired as e:
    text = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
    print("TIMEOUT")
saved = [l for l in text.splitlines() if "saved" in l]
errs = [l for l in text.splitlines() if ("ERROR" in l or "Exception" in l) and "saved" not in l]
print(f"{len(saved)} frames")
for l in saved:
    print(l.split("/")[-1])
for l in errs[:20]:
    print("ERR", l[:300])
