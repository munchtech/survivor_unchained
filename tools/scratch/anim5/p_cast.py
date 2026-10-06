from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\actions.py")
t = p.read_text(encoding="utf-8")
a = t[t.index("def cast_raise("):t.index("def cast_flick(")]
b = '''def cast_raise(rig):
    """The arcanist's great working: the staff swept up overhead in both
    hands, held across the sky, and brought down upright, its foot striking
    the ground before her, both fists on it.

    (A staff goes through the fist square to it: held upright overhead it
    asked a wrist bent back along the forearm, and brought down to a hand
    hanging low it asked the same the other way; the hand turned over in a
    frame. Across overhead and upright before her chest, it sits in the
    fists as staffs do.)"""
    keys = [
        (0, body(stance(0.06), spine=(0, -6, 0), head=(0, -14, 0),
                 hand_r=arm((0.06, 0.32, 0.10), (-0.6, 0.2, -0.6), blade=_n(1.0, 0.1, 0.1)),
                 hand_l=arm((0.0, 0.34, 0.10), (0.6, 0.2, -0.6)), fingers_l="grip", fingers_r="grip"), "ease"),
        (6, body(stance(0.06), spine=(0, -10, 0), head=(0, -20, 0),
                 hand_r=arm((0.06, 0.40, 0.08), (-0.6, 0.2, -0.6), blade=_n(1.0, 0.15, 0.1)),
                 hand_l=arm((0.0, 0.42, 0.08), (0.6, 0.2, -0.6)), fingers_l="grip", fingers_r="grip"), "fast"),
        (10, body(stance(0.14, weight=0.3), hips=(0, 14, 0), spine=(0, 18, 0), head=(0, -10, 0),
                  hand_r=arm((0.10, -0.24, 0.30), (-0.7, -0.6, -0.2), blade=_n(0.0, 0.97, -0.25)),
                  hand_l=arm((-0.26, -0.06, 0.26), (0.8, -0.4, -0.3)), fingers_l="grip", fingers_r="grip"), "ease"),
        (16, body(stance(0.14, weight=0.3), hips=(0, 15, 0), spine=(0, 19, 0), head=(0, -10, 0),
                  hand_r=arm((0.10, -0.25, 0.30), (-0.7, -0.6, -0.2), blade=_n(0.0, 0.97, -0.25)),
                  hand_l=arm((-0.26, -0.07, 0.26), (0.8, -0.4, -0.3)), fingers_l="grip", fingers_r="grip"), "auto"),
        (28, body(stance(0.06), hand_l=arm((-0.02, -0.40, -0.05), (1.0, 0.0, -0.7), knuckles=_n(0.2, -0.6, 0.6)),
                  hand_r=arm((-0.16, -0.28, 0.12), (-0.8, -0.3, -0.6), blade=_n(-0.12, 1.0, 0.18)),
                  fingers_l="relaxed", fingers_r="grip"), "ease"),
    ]
    return build("cast_raise", rig, keys, meta={"layer": "upper", "contact": 10 / 30, "weapon": "staff"})


'''
t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("ok")
