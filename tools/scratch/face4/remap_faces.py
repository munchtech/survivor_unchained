import json
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994\godot\data\content\looks.json"
d = json.load(open(p, encoding="utf-8"))
faces = d["heroes"]["female"]["faces"]
ren = {"cheekbones": "cheekbone_width", "jaw": "jaw_width"}
for f in faces:
    f["shape"] = {ren.get(k, k): v for k, v in f["shape"].items()}
json.dump(faces, open(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4\faces_interim.json", "w"), indent=1)
print(len(faces))
