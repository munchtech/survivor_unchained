"""A scratch copy of a cinematic with camera variants of some shots, for one previs run (not committed).
python mkt.py SRC_ID VARIANTS.py   ->  godot/data/cinematics/_t<SRC_ID>.json
VARIANTS.py defines V = {"after_shot_id": [ {"id": "6aB", "cam": {...}, ...overrides}, ... ]}:
each variant copies the shot it follows (its cues and timing), then takes the overrides."""
import copy, importlib.util, json, os, sys

G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7a4c20bcfd7ccfd3"
sys.path.insert(0, os.path.join(G, "tools", "cinematics"))
import timeline_fmt

src, vf = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("v", vf); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
d = json.load(open(os.path.join(G, "godot", "data", "cinematics", f"{src}.json"), encoding="utf-8"))
d["id"] = f"_t{src}"
only = getattr(m, "ONLY", None)
out = []
for s in d["shots"]:
    if only is None or s["id"] in only or s.get("black") or s.get("hold"):
        out.append(s)
    for v in m.V.get(s["id"], []):
        n = copy.deepcopy(s)
        n.update(copy.deepcopy(v))
        out.append(n)
d["shots"] = out
if hasattr(m, "EDIT"):
    m.EDIT({s["id"]: s for s in out}, d)
p = os.path.join(G, "godot", "data", "cinematics", f"_t{src}.json")
open(p, "w", encoding="utf-8", newline="\n").write(timeline_fmt.fmt(d) + "\n")
print(p, [s["id"] for s in out])
