"""Move the try-takes (k_) out of out/folk to the scratch takes folder, then repack folk.res.
Takes a Godot turn for the pack and gives it back."""
import shutil
import subprocess
import sys
from pathlib import Path

WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70")
TURN = r"C:\Users\munch\Desktop\survivorsunchained\tools\turn.py"
KEEP = Path(__file__).parent / "takes"
KEEP.mkdir(exist_ok=True)
for f in (WT / "tools/anim/out/folk").glob("*_k_*.json"):
    shutil.move(str(f), KEEP / f.name)
    print("moved", f.name)
if subprocess.run([sys.executable, TURN, "take", "godot", "animation: folk pack", "--wait", "10"]).returncode:
    sys.exit(1)
try:
    sys.path.insert(0, str(WT / "tools/anim"))
    import folk
    folk.pack()
finally:
    subprocess.run([sys.executable, TURN, "give", "godot", "animation: folk pack"])
