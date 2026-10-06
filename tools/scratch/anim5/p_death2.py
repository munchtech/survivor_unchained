from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\actions.py")
t = p.read_text(encoding="utf-8")
E = [
    ('''                   "hips": {"pos": (0, -0.55, -0.10)}},
                  hips=(6, 44, 6), spine=(6, 26, 8), neck=(0, 10, 0), head=(14, 6, 10),''',
     '''                   "hips": {"pos": (0, -0.51, -0.10)}},
                  hips=(6, 44, 6), spine=(6, 26, 8), neck=(0, 10, 0), head=(14, 6, 10),'''),
    ('''        "hand_r": {"pos": (-0.14, 0.05, 0.20), "pole": (-1, 0.5, 0), "knuckles": (0.2, 0, 1)},''',
     '''        "hand_r": {"pos": (-0.18, 0.06, 0.20), "pole": (-1, 0.25, -0.2), "knuckles": (0.2, 0, 1)},'''),
]
for a, b in E:
    assert t.count(a) == 1, a[:50]
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("ok")
