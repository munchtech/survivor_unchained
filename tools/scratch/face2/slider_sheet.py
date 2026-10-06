"""slider_sheet.py out.json [group ...]: FaceSheet looks, each slider at -1 and +1 (and her own face first)."""
import json
import sys

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6784044c82f101d9\tools\assets")
import face_shapes as fs  # noqa: E402

groups = sys.argv[2:]
looks = [{"name": "00_base", "face": {}, "hair": "pixie"}]
for s, (g, *_r) in fs.SLIDERS.items():
    if groups and g not in groups:
        continue
    for v, tag in ((-1, "m"), (1, "p")):
        looks.append({"name": f"{s}_{tag}", "face": {s: v}, "hair": "pixie"})
json.dump(looks, open(sys.argv[1], "w"), indent=0)
print(len(looks), "looks")
