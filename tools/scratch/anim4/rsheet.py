"""Sheets of a clip on her (anim_review.gd) with any env: python rsheet.py out.png clip K=V ...
Common: VIEW, FRAMES, STEP, START, W, H, COLS, LOOK, OFF, LOOKOFF, FOV, FIXCAM, WEAPON, OUTFIT, HAIR, MODEL, ZOOM."""
import os
import subprocess
import sys
from pathlib import Path

WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
out = Path(sys.argv[1])
if not out.is_absolute():
    out = Path(__file__).parent / "sh" / out
out.parent.mkdir(exist_ok=True)
clip = sys.argv[2]
env = dict(os.environ, VIEW="front", FRAMES="10", STEP="3", W="480", H="270", OUTFIT="warden", HAIR="ponytail")
for a in sys.argv[3:]:
    k, v = a.split("=", 1)
    env[k] = v
r = subprocess.run([GODOT, "--path", str(WT / "godot"), "--fixed-fps", "30", "-s", "res://tools_scenes/anim_review.gd", "--", clip, str(out)],
                   env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
ok = [l for l in r.stdout.splitlines() if "SHEET" in l or "DBG" in l]
print("\n".join(ok) if ok else "\n".join(l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l or "SCRIPT" in l)[:3000])
