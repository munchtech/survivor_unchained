"""How each cinematic ends: its end mark and its last shot's camera and cues."""
import json, os, sys
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aece7b87e89b13f19\godot\data\cinematics"
for f in sys.argv[1:] or sorted(x[:-5] for x in os.listdir(G) if x.endswith(".json") and not x.startswith("_")):
    d = json.load(open(os.path.join(G, f + ".json"), encoding="utf-8"))
    e = d.get("end", {})
    print(f"== {f}: end {e}  mark {d['marks'].get(e.get('her'))}")
    for s in d["shots"][-2:]:
        print(f"  {s['id']} {s.get('type')} {s.get('dur')} cam {json.dumps(s.get('cam'))[:260]}")
        for c in s.get("cues", []):
            print("     ", json.dumps(c)[:220])
