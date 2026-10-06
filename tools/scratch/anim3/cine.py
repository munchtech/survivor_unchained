"""A cinematic's stills in the engine, at 1920x1080: python cine.py CINE NAME UNTIL [extra game args]
Stills land in godot/.shots/NAME_*.png."""
import glob
import os
import subprocess
import sys
import time

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
cine, name, until = sys.argv[1], sys.argv[2], sys.argv[3]
extra = sys.argv[4:]
zone = "lowford"
if "--zone" in extra:
    i = extra.index("--zone"); zone = extra[i + 1]; del extra[i:i + 2]
for f in glob.glob(os.path.join(WT, ".shots", f"{name}_*")):
    os.remove(f)
t0 = time.time()
args = [GODOT, "--path", WT, "--resolution", "1920x1080", "--fixed-fps", "30", "--", "--quick", "warden", "--sex", "female",
        "--zone", zone, "--cine", cine, "--shot", name, "--until", until, "--cinebones"] + extra
p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
for ln in (p.stdout + p.stderr).splitlines():
    if "cinebones" in ln or "no clip" in ln or "SCRIPT ERROR" in ln or "Unhandled" in ln or ("cinema" in ln and ("WARN" in ln or "ERR" in ln)):
        print(ln[:300])
files = sorted(glob.glob(os.path.join(WT, ".shots", f"{name}_*.png")), key=os.path.getmtime)
print(f"{len(files)} stills in {time.time() - t0:.0f} s")
for f in files:
    print(os.path.basename(f))
