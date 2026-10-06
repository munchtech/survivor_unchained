"""List conversations with node counts; or grep all text in content JSON for a regex (case-insensitive).
Usage: overview_s7.py            -> conversation list
       overview_s7.py grep REGEX -> every string in content JSON + cinematics matching, with its path"""
import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a38d66ae66583ace1"
C = os.path.join(WT, "godot", "data", "content")
CIN = os.path.join(WT, "godot", "data", "cinematics")

def walk(x, path):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from walk(v, path + [str(k)])
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from walk(v, path + [str(i)])
    elif isinstance(x, str):
        yield path, x

if len(sys.argv) > 2 and sys.argv[1] == "grep":
    rx = re.compile(sys.argv[2], re.I)
    files = [(f, os.path.join(C, f)) for f in sorted(os.listdir(C)) if f.endswith(".json")]
    files += [("cin/" + f, os.path.join(CIN, f)) for f in sorted(os.listdir(CIN)) if f.endswith(".json")]
    for name, p in files:
        d = json.load(open(p, encoding="utf-8"))
        for path, s in walk(d, []):
            if rx.search(s) or rx.search("/".join(path)):
                print(f"{name}:{'/'.join(path)}: {s[:300]}")
else:
    d = json.load(open(os.path.join(C, "dialogue.json"), encoding="utf-8"))
    for k, v in d.items():
        if isinstance(v, dict) and "nodes" in v:
            print(k, len(v["nodes"]))
        else:
            print(k, type(v).__name__)
