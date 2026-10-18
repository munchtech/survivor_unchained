"""python writewrap.py <WRAP key> <solve.py out json>: fistfit.write_wrap with that wrap (keyed.py)."""
import sys, json
from pathlib import Path
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6b5a13d0be70144d\tools\anim")
import fistfit as F
w = json.load(open(sys.argv[2]))["wrap"]
w["bends"] = {k: tuple(v) for k, v in w["bends"].items()}
F.write_wrap(sys.argv[1], w)
print("written", sys.argv[1])
