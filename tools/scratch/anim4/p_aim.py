p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017\tools\anim\clips\story.py"
s = open(p, encoding="utf-8").read()
rep = [
    ('''            "hand_l": arm((0.09, -0.21, 0.30), (0.7, -0.6, -0.3)), "hand_r": arm((-0.07, -0.25, 0.26), (-0.7, -0.6, -0.3)),
            "clav_l": (4 + 2.5 * b, 4), "clav_r": (4 + 2.5 * b, 4), "fingers_l": _f(0.45, 0.3), "fingers_r": _f(0.45, 0.3)}''',
     '''            # (Not aimed: the hands hang off the forearms as they fall.)
            "hand_l": {**arm((0.09, -0.21, 0.30), (0.7, -0.6, -0.3)), "aim": 0.0},
            "hand_r": {**arm((-0.07, -0.25, 0.26), (-0.7, -0.6, -0.3)), "aim": 0.0},
            "clav_l": (4 + 2.5 * b, 4), "clav_r": (4 + 2.5 * b, 4), "fingers_l": _f(0.45, 0.3), "fingers_r": _f(0.45, 0.3)}'''),
    ('''                   "knuckles": (0.1, 0.25 * hands - 0.35 * (1 - hands), 1.0), "blade": (1.0, 0.0, -0.1)},''',
     '''                   "knuckles": (0.1, 0.25 * hands - 0.35 * (1 - hands), 1.0), "blade": (1.0, 0.0, -0.1), "aim": 1.0},'''),
    ('''                   "knuckles": (-0.1, 0.25 * hands - 0.35 * (1 - hands), 1.0), "blade": (-1.0, 0.0, -0.1)},''',
     '''                   "knuckles": (-0.1, 0.25 * hands - 0.35 * (1 - hands), 1.0), "blade": (-1.0, 0.0, -0.1), "aim": 1.0},'''),
]
for a, b in rep:
    assert a in s, a[:70]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")
