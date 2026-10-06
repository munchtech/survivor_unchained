from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\actions.py")
t = p.read_text(encoding="utf-8")
E = [('(8, {"hips": {"pos": (0.0, -0.58, -0.28), "rot": (2, 60, 2)}', '(8, {"hips": {"pos": (0.0, -0.53, -0.28), "rot": (2, 60, 2)}'),
     ('''                   "hips": {"pos": (0, -0.55, -0.12)}},
                  hips=(0, 24, 0), spine=(0, 16, 0), neck=(0, -6, 0), head=(0, -6, 0),''',
      '''                   "hips": {"pos": (0, -0.50, -0.12)}},
                  hips=(0, 24, 0), spine=(0, 16, 0), neck=(0, -6, 0), head=(0, -6, 0),''')]
for a, b in E:
    assert t.count(a) == 1, a[:40]
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("ok")
