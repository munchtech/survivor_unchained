"""Scratch: python crowd.py VISUAL ROLE out.png [N=8 STEP=0.1 START=0 YAW=90 W=1800 H=400 LIFT=12 CELL=]"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1e3002b800ee55ac")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
env = dict(os.environ, VISUAL=sys.argv[1], ROLE=sys.argv[2], OUT=str(Path(sys.argv[3]).resolve()))
for a in sys.argv[4:]:
    k, v = a.split("=", 1)
    env[k] = v
r = subprocess.run([GODOT, "--path", str(REPO / "godot"), "-s", "res://tools_scenes/crowd_sheet.gd", "--", "--vat-fresh"],
                   env=env, capture_output=True, text=True, timeout=240)
for line in (r.stdout + r.stderr).splitlines():
    if any(k in line for k in ("CROWDSHEET", "SCRIPT", "Exception", "error CS")) or ("ERROR" in line and "RID" not in line and "singleton" not in line):
        print(line[:300])
