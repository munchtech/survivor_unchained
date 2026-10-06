from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\actions.py")
t = p.read_text(encoding="utf-8")
a = '''        "hand_l": {"pos": (0.56, 0.04, 0.16), "pole": (1, 0.3, -0.3), "knuckles": (0.6, 0, 0.8)},
        "hand_r": {"pos": (-0.18, 0.06, 0.20), "pole": (-1, 0.25, -0.2), "knuckles": (0.2, 0, 1)},'''
b = '''        # The flung arm palm down, so a shield strapped to it lies face up
        # on it (the forearm takes the whole roll); the arm under her palm
        # up, so what is in the hand lies flat out from under her. (Left as
        # the arms fell, the shield stood on its edge 18 cm into the ground
        # and the blade stood up over her back.)
        "hand_l": {"pos": (0.56, 0.04, 0.16), "pole": (1, 0.3, -0.3), "knuckles": (0.6, 0, 0.8), "blade": (-0.8, 0, 0.6),
                   "twist": 1.0},
        "hand_r": {"pos": (-0.18, 0.06, 0.20), "pole": (-1, 0.25, -0.2), "knuckles": (0.2, 0, 1), "blade": (-1, 0, 0.2)},'''
assert t.count(a) == 1
t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("ok")
