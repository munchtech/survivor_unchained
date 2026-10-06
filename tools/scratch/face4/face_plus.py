"""face_plus.py out.json slider=v ... : face_shapes.FACE plus those slider settings (as their targets), incr and decr pairs netted."""
import json
import sys

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994\tools\assets")
import face_shapes as fs  # noqa: E402
import face_presets as fp  # noqa: E402

sliders = {a.split("=")[0]: float(a.split("=")[1]) for a in sys.argv[2:]}
face = dict(fs.FACE)
for t, w in fp.to_targets(sliders).items():
    face[t] = round(face.get(t, 0.0) + w, 3)
json.dump(face, open(sys.argv[1], "w"), indent=1)
print(len(face), "targets")
