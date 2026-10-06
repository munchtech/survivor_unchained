"""Runs the game for pictures: python game.py <shot-name> <game args...> (vat-fresh=1 to rebake)."""
import subprocess
import sys

GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
PROJ = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017\godot"
name = sys.argv[1]
rest = sys.argv[2:]
args = [GODOT, "--path", PROJ, "--resolution", "1920x1080", "--fixed-fps", "30", "--", "--shot", name] + rest
r = subprocess.run(args, capture_output=True, text=True, timeout=900)
for line in (r.stdout + r.stderr).splitlines():
    if "saved" in line or "ERROR" in line or "Exception" in line:
        print(line[:300])
