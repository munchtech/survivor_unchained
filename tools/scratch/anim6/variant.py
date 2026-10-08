"""Write godot/art/people/rig_helpers.json with the share bones' bulge set:
    python variant.py <elbow bulge> <elbow max> <knee bulge> <knee max> [shoulder bulge] [shoulder max]
(HerJoints reads the file at run time: no import needed.)"""
import json
import sys
from pathlib import Path

F = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ae2a9884e3e51609c\godot\art\people\rig_helpers.json")
d = json.loads(F.read_text())
eb, em, kb, km = map(float, sys.argv[1:5])
sb, sm = (float(sys.argv[5]), float(sys.argv[6])) if len(sys.argv) > 6 else (None, None)
for h in d["helpers"]:
    if h["name"].startswith("lowerarm_share"):
        h["bulge"], h["bulge_max"] = eb, em
    elif h["name"].startswith("calf_share"):
        h["bulge"], h["bulge_max"] = kb, km
    elif h["name"].startswith("upperarm_share") and sb is not None:
        h["bulge"], h["bulge_max"] = sb, sm
F.write_text(json.dumps(d, indent=1) + "\n")
print("spec:", [(h["name"], h.get("bulge"), h.get("bulge_max")) for h in d["helpers"] if h["kind"] == "share"])
