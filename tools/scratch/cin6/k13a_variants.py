"""Variant timelines for one batch: python k12_variants.py make VARIANTS.py | clean
VARIANTS.py defines VARIANTS = {"A": fn(shots, f), ...}; each writes godot/data/cinematics/k13av<A>.json,
a copy of the base cinematic (BASE, default c01) with fn applied. `clean` deletes every k13av*.json.
Shoot them with "cine": "k13avA" etc.; delete them right after (tests glob the folder)."""
import copy, glob, importlib.util, json, os, sys
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92"
D = os.path.join(W, "godot", "data", "cinematics")
sys.path.insert(0, os.path.join(W, "tools", "cinematics"))
import timeline_fmt
if sys.argv[1] == "clean":
    for p in glob.glob(os.path.join(D, "k13av*.json")): os.remove(p); print("removed", p)
    sys.exit(0)
spec = importlib.util.spec_from_file_location("v", sys.argv[2]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
base = json.load(open(os.path.join(D, getattr(m, "BASE", "c01") + ".json"), encoding="utf-8"))
for k, fn in m.VARIANTS.items():
    f = copy.deepcopy(base); f["id"] = "k13av" + k
    fn({s["id"]: s for s in f["shots"]}, f)
    p = os.path.join(D, f"k13av{k}.json")
    open(p, "w", encoding="utf-8", newline="\n").write(timeline_fmt.fmt(f).rstrip("\n") + "\n")
    print("written", p)
