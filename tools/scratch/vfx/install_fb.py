"""Cut clips into atlases and install them in the game: python install_fb.py NAME[:start:end:pad:gain] ...

Each is cut by tools/comfy/flipbook.py (which refuses any frame showing its square
or cut off), then copied into godot/art/fx/fb with an import file like holy_burst's."""
import os
import shutil
import subprocess
import sys

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a560452c597415545"
CLIPS = r"C:\Users\munch\Desktop\survivorsunchained\tools\comfy\out\clips"
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb")
FB = os.path.join(WT, "godot", "art", "fx", "fb")

for spec in sys.argv[1:]:
    parts = spec.split(":")
    name = parts[0]
    start, end, pad, gain = (parts + ["0", "1", "0.15", "1"][len(parts) - 1:])[1:5] if len(parts) > 1 else ("0", "1", "0.15", "1")
    out = os.path.join(TMP, name + ".png")
    r = subprocess.run([sys.executable, os.path.join(WT, "tools", "comfy", "flipbook.py"), os.path.join(CLIPS, name + ".mp4"), out,
                        "--start", start, "--end", end, "--pad", pad, "--gain", gain], capture_output=True, text=True)
    print(name, (r.stdout + r.stderr).strip().splitlines()[-1])
    if r.returncode != 0:
        continue
    shutil.copy(out, FB)
    shutil.copy(os.path.join(TMP, name + ".json"), FB)
    with open(os.path.join(FB, "holy_burst.png.import"), encoding="utf-8") as f:
        imp = [l for l in f.read().splitlines(True) if not l.startswith("uid=")]
    with open(os.path.join(FB, name + ".png.import"), "w", encoding="utf-8", newline="") as f:
        f.write("".join(imp).replace("holy_burst", name))
    print("  installed")
