from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\actions.py")
t = p.read_text(encoding="utf-8")
a = '''        (8, {"hips": {"pos": (0.0, -0.70, -0.30), "rot": (2, 60, 2)}, "spine": (0, 10, 0), "neck": (0, -10, 0),
             "head": (0, -20, 0),
             "foot_l": {"pos": (0.16, 0.02, -0.80), "rot": (6, -80, 0), "pole": (0.3, -1, 0.2)},
             "foot_r": {"pos": (-0.14, 0.02, -0.82), "rot": (-6, -80, 0), "pole": (-0.2, -1, 0.2)},'''
b = '''        # On her hands and knees: the hips over the knees, the shins along
        # the ground behind them. (Lower, the knees went 17 cm into it.)
        (8, {"hips": {"pos": (0.0, -0.58, -0.28), "rot": (2, 60, 2)}, "spine": (0, 10, 0), "neck": (0, -10, 0),
             "head": (0, -20, 0),
             "foot_l": {"pos": (0.16, 0.02, -0.74), "rot": (6, -80, 0), "pole": (0.3, -1, 0.2)},
             "foot_r": {"pos": (-0.14, 0.02, -0.76), "rot": (-6, -80, 0), "pole": (-0.2, -1, 0.2)},'''
assert t.count(a) == 1
t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("ok")
