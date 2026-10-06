"""calib.py <base.json> <out faces.json> : base face, and each slider at -2, -1, +1, +2 over it."""
import json
import sys

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abfa9bb430ec2391e\tools\assets")
import face_shapes as fs

base = json.load(open(sys.argv[1], encoding="utf-8-sig"))
out = {"base": dict(base, **{"-": True})}
for name, (group, *_rest, plus, minus) in fs.SLIDERS.items():
    for k in (-2, -1, 1, 2):
        f = dict(base)
        for t, w in (plus if k > 0 else minus).items():
            f[t] = round(f.get(t, 0.0) + abs(k) * w, 3)
        f["-"] = True
        out[f"{fs.SLIDER_GROUPS.index(group)}{group}_{name}_{'m' if k < 0 else 'p'}{abs(k)}"] = f
json.dump(out, open(sys.argv[2], "w"), indent=0)
print(len(out))
