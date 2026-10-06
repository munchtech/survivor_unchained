p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\story.py"
s = open(p, encoding="utf-8").read()
rep = [
    ('''        y = 1.10 + rise
        l = {"frame": "char", "pos": _yaw((0.045 + part, y, 0.40), T), "pole": _yaw((0.8, -0.5, -0.3), T),
             "knuckles": _yaw((-0.35, 0.25, 0.9), T), "blade": _yaw((0.2, 0.1, 1.0), T)}
        r = {"frame": "char", "pos": _yaw((-0.045 - part, y, 0.40), T), "pole": _yaw((-0.8, -0.5, -0.3), T),
             "knuckles": _yaw((0.35, 0.25, 0.9), T), "blade": _yaw((-0.2, 0.1, 1.0), T)}''',
     '''        # Palms up side by side (her left hand's palm is its +X, her right's
        # its -X), the fingers forward and a little up, the thumbs outward.
        y = 1.15 + rise
        l = {"frame": "char", "pos": _yaw((0.05 + part, y, 0.36), T), "pole": _yaw((0.8, -0.5, -0.3), T),
             "knuckles": _yaw((0.12, 0.25, 1.0), T), "blade": _yaw((1.0, 0.15, -0.1), T)}
        r = {"frame": "char", "pos": _yaw((-0.05 - part, y, 0.36), T), "pole": _yaw((-0.8, -0.5, -0.3), T),
             "knuckles": _yaw((-0.12, 0.25, 1.0), T), "blade": _yaw((-1.0, 0.15, -0.1), T)}'''),
    ('''            "hand_l": arm((0.10, -0.26, 0.26), (0.7, -0.6, -0.3)), "hand_r": arm((-0.08, -0.30, 0.22), (-0.7, -0.6, -0.3)),
            "clav_l": (4 + 2.5 * b, 4), "clav_r": (4 + 2.5 * b, 4), "fingers_l": _f(0.45, 0.3), "fingers_r": _f(0.45, 0.3)}''',
     '''            "hand_l": arm((0.09, -0.21, 0.30), (0.7, -0.6, -0.3)), "hand_r": arm((-0.07, -0.25, 0.26), (-0.7, -0.6, -0.3)),
            "clav_l": (4 + 2.5 * b, 4), "clav_r": (4 + 2.5 * b, 4), "fingers_l": _f(0.45, 0.3), "fingers_r": _f(0.45, 0.3)}'''),
]
for a, b in rep:
    assert a in s, a[:80]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")
