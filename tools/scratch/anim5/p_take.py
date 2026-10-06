p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\story.py"
s = open(p, encoding="utf-8").read()
rep = [
    ('''        (36, {"foot_l": foot((0.32, 0, 0.12), T * 0.85, 1), "foot_r": foot((-0.08, 0, 0.24), T * 0.6, -1),
              "hips": {"pos": _hips_at(0.97, 0.18, 0.06, T * 0.75), "rot": (T * 0.8, 10, 0)},''',
     '''        (36, {"foot_l": foot((0.26, 0, 0.18), T * 0.85, 1), "foot_r": foot((-0.07, 0, 0.18), T * 0.6, -1),
              "hips": {"pos": _hips_at(0.99, 0.18, 0.06, T * 0.75), "rot": (T * 0.8, 10, 0)},'''),
    ('''        (44, {"foot_l": foot((0.30, 0, 0.20), T, 1), "foot_r": foot((-0.05, 0, 0.14), T, -1),
              "hips": {"pos": _hips_at(0.96, 0.17, 0.10, T), "rot": (T, 9, 0)},''',
     '''        (44, {"foot_l": foot((0.22, 0, 0.30), T, 1), "foot_r": foot((-0.05, 0, 0.06), T, -1),
              "hips": {"pos": _hips_at(1.0, 0.17, 0.08, T), "rot": (T, 8, 0)},'''),
    ('''        (60, {"foot_l": foot((0.30, 0, 0.20), T, 1), "foot_r": foot((-0.05, 0, 0.14), T, -1),
              "hips": {"pos": _hips_at(0.965, 0.17, 0.10, T), "rot": (T, 9, 0)},''',
     '''        (60, {"foot_l": foot((0.22, 0, 0.30), T, 1), "foot_r": foot((-0.05, 0, 0.06), T, -1),
              "hips": {"pos": _hips_at(1.003, 0.17, 0.08, T), "rot": (T, 8, 0)},'''),
    ('''        y = 1.08 + rise
        l = {"frame": "char", "pos": _yaw((0.045 + part, y, 0.30), T),''',
     '''        y = 1.10 + rise
        l = {"frame": "char", "pos": _yaw((0.045 + part, y, 0.40), T),'''),
    ('''        r = {"frame": "char", "pos": _yaw((-0.045 - part, y, 0.30), T),''',
     '''        r = {"frame": "char", "pos": _yaw((-0.045 - part, y, 0.40), T),'''),
]
for a, b in rep:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")
