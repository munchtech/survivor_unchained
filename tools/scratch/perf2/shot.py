"""A screenshot of the game with a kept build: python shot.py BUILD NAME [game args...] [--engine "..."]
Runs at 2560x1440 with --fixed-fps 60, so two builds given the same args show the same moment."""
import os
import shutil
import subprocess
import sys

W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7145e18b3eb78294"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
BIN = os.path.join(W, "godot", ".godot", "mono", "temp", "bin", "Debug")

argv = sys.argv[1:]
engine = []
if "--engine" in argv:
    i = argv.index("--engine")
    engine = argv[i + 1].split()
    del argv[i:i + 2]
build, name, rest = argv[0], argv[1], argv[2:]
for f in os.listdir(build):
    if f.startswith("SurvivorUnchained."):
        shutil.copy2(os.path.join(build, f), os.path.join(BIN, f))
cmd = [GODOT, "--path", os.path.join(W, "godot"), "--resolution", "2560x1440", "--fixed-fps", "60", *engine, "--", "--shot", name, *rest]
p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
for l in p.stdout.splitlines():
    if l.startswith("saved") or "ERROR" in l or l.startswith("perf"):
        print(l)
print("exit", p.returncode)
