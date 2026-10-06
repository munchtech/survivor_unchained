"""Bring the C02 to C04 cinematic takes' index entries back from the voice branch (7fc0013)."""
import json, subprocess

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af7a79bc783cca7bc"
CONVS = ("cin_none_cross", "cin_heart_goes_down", "cin_first_light")
src = json.loads(subprocess.run(["git", "-C", WT, "show", "7fc0013:godot/data/vo/index.json"], capture_output=True, check=True).stdout.decode("utf-8-sig"))["lines"]
p = WT + r"\godot\data\vo\index.json"
raw = open(p, encoding="utf-8").read()
d = json.loads(raw.lstrip("\ufeff"))
n = 0
for k, v in src.items():
    if any(f"dlg.{c}." in k for c in CONVS):
        d["lines"][k] = v
        n += 1
d["lines"] = dict(sorted(d["lines"].items()))
open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
print("restored", n, "entries")
# Also save the voice branch's whole index for the animatic (C01's lamp and call are not there yet).
open(WT + r"\..\..\..\..\..\..\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\cine\vo_index_7fc0013.json", "w", encoding="utf-8").write(json.dumps({"lines": src}))
