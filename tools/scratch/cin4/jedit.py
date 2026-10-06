"""Edit a cinematic timeline's shots by id, keeping the file's one-line-per-thing layout.
python jedit.py c02 edits.py   (edits.py defines edit(shots, f) mutating the parsed JSON)"""
import json, os, sys, importlib.util
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7a4c20bcfd7ccfd3"
sys.path.insert(0, os.path.join(G, "tools", "cinematics"))
cid, script = sys.argv[1], sys.argv[2]
p = os.path.join(G, "godot", "data", "cinematics", f"{cid}.json")
f = json.load(open(p, encoding="utf-8"))
spec = importlib.util.spec_from_file_location("e", script)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
shots = {s["id"]: s for s in f["shots"]}
m.edit(shots, f)
try:
    import timeline_fmt
    text = timeline_fmt.fmt(f)
except Exception as e:
    print("fmt fallback:", e)
    text = json.dumps(f, indent=2, ensure_ascii=False)
open(p, "w", encoding="utf-8", newline="\n").write(text + ("" if text.endswith("\n") else "\n"))
print("written", p)
