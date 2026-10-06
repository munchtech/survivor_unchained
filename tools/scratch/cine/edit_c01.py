"""Patch shot fields in a timeline and write it back in the house layout:
python edit_c01.py FILE PATCH.json   where PATCH is {"<shot id>": {"cam.pos": value, ...}}
(a value of null deletes the key)."""
import json, sys

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2dfc75e2d351105a\tools\cinematics")
from timeline_fmt import fmt

p, patch = sys.argv[1], json.load(open(sys.argv[2], encoding="utf-8"))
d = json.load(open(p, encoding="utf-8"))
for shot, kv in patch.items():
    s = next(x for x in d["shots"] if x["id"] == shot)
    for k, val in kv.items():
        path = k.split(".")
        o = s
        for part in path[:-1]:
            o = o.setdefault(part, {})
        if val is None:
            o.pop(path[-1], None)
        else:
            o[path[-1]] = val
open(p, "w", encoding="utf-8").write(fmt(d))
print("patched", list(patch))
