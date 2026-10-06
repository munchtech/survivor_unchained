"""Print each place's ground layers: name, source, metres a tile, mean linear colour."""
import json, os
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0b61c278bdd5c994\godot\art\arena"
for p in ["barrow", "hollow", "ruts", "dig"]:
    d = json.load(open(os.path.join(WT, p, "layers.json")))
    print(p)
    for l in d["layers"]:
        m = l["mean"]
        y = 0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]
        print("  ", {k: v for k, v in l.items() if k != "mean"}, "Y=%.3f" % y)
