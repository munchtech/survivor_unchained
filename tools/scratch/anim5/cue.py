"""Local cue trials on a cinematic's timeline (never committed: the timelines are cinematics').
python cue.py <cine> <edits.py>   applies EDITS(d) from edits.py to godot/data/cinematics/<cine>.json
python cue.py <cine> off          puts the file back (git checkout)"""
import json
import runpy
import subprocess
import sys
from pathlib import Path

WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274")
cine, what = sys.argv[1], sys.argv[2]
p = WT / "godot" / "data" / "cinematics" / f"{cine}.json"
subprocess.run(["git", "-C", str(WT), "checkout", "--", str(p.relative_to(WT)).replace("\\", "/")], check=True)
if what != "off":
    d = json.loads(p.read_text(encoding="utf-8"))
    runpy.run_path(what)["EDITS"](d)
    p.write_text(json.dumps(d, indent=1), encoding="utf-8")
print(cine, what)
