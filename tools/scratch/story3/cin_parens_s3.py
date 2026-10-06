"""List every parenthesis in the cinematic conversations (cin_*), split into lower-case
directions and capitalised narration, so the subtitle rule can be checked against the data."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
C = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9\godot\data\content\dialogue.json"
d = json.load(open(C, encoding="utf-8"))
for c, conv in d.items():
    if not c.startswith("cin_"):
        continue
    for k, n in conv["nodes"].items():
        t = n["text"]; vs = t if isinstance(t, list) else [{"text": t}]
        for i, x in enumerate(vs):
            for m in re.finditer(r"\(([^)]*)\)", x["text"]):
                kind = "NARR" if m.group(1)[:1].isupper() else "dir "
                print(kind, f"{c}.{k}.{i}", n.get("speaker", ""), "|", m.group(0)[:90])
