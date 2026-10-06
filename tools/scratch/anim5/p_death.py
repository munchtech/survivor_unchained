from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\actions.py")
t = p.read_text(encoding="utf-8")
E = [
    # The fall's last pose: the legs lie on the ground; a bent knee goes out
    # to the side along it, never down into it.
    ('''        "foot_l": {"pos": (0.24, 0.0, -1.12), "rot": (10, -88, 0), "pole": (0.6, -1, 0.2)},
        "foot_r": {"pos": (-0.12, 0.04, -1.02), "rot": (-6, -80, 0), "pole": (-0.4, -1, 0.3)},''',
     '''        # (A bent knee lies out to the side along the ground: bent toward
        # the ground it went 13 cm into it, and she sank at the fall.)
        "foot_l": {"pos": (0.24, 0.0, -1.12), "rot": (10, -88, 0), "pole": (1.0, 0.15, 0.3)},
        "foot_r": {"pos": (-0.12, 0.04, -1.02), "rot": (-6, -80, 0), "pole": (-1.0, 0.15, 0.3)},'''),
    # On her knees: the hips high enough over them that the knees rest on the ground, not in it.
    ('''                   "hips": {"pos": (0, -0.52, -0.08)}},
                  hips=(4, 10, 6), spine=(6, 22, 8), neck=(0, 12, 0), head=(6, 14, 10),''',
     '''                   "hips": {"pos": (0, -0.47, -0.08)}},
                  hips=(4, 10, 6), spine=(6, 22, 8), neck=(0, 12, 0), head=(6, 14, 10),'''),
    ('''                   "hips": {"pos": (0, -0.64, -0.14)}},
                  hips=(6, 44, 6), spine=(6, 26, 8), neck=(0, 10, 0), head=(14, 6, 10),''',
     '''                   "hips": {"pos": (0, -0.55, -0.10)}},
                  hips=(6, 44, 6), spine=(6, 26, 8), neck=(0, 10, 0), head=(14, 6, 10),'''),
]
for a, b in E:
    assert t.count(a) == 1, a[:50]
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("ok")
