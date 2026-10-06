p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017\tools\anim\clips\story.py"
s = open(p, encoding="utf-8").read()
a = s.index('    ready_l = arm((0.10, -0.26, 0.26), (0.7, -0.6, -0.3))\n    ready_r = arm((-0.08, -0.30, 0.22), (-0.7, -0.6, -0.3))\n    keys = [\n        (0, start, "ease"),')
b = s.index('    return contact_build("kneel_to_stand_snap"')
new = '''    keys = [
        (0, start, "ease"),
        (3, merge(start, head=(0, 14, 0)), "ease"),
        # The snap: the head round to it, a little up; the eyes are already there.
        (7, merge(start, neck=(14, 6, 0), head=(44, 2, -4), spine=(4, 12, 0), clav_l=(3, 0), clav_r=(3, 0)), "auto"),
        # The shoulders after it; up off her heels, the hips swinging up and
        # forward about the knees (a thigh's length from them), the hands off
        # her thighs.
        (10, merge(start, hips={"pos": _hips_at(0.40, -0.02, 0.0, 10), "rot": (12, 16, 0)}, spine=(12, 10, 0), neck=(14, 2, 0),
                   head=(26, 0, -2), clav_l=(4, 2), clav_r=(4, 2),
                   hand_l=arm((0.12, -0.34, 0.12), (0.7, -0.4, -0.5)), hand_r=arm((-0.12, -0.36, 0.08), (-0.7, -0.4, -0.5)),
                   fingers_l=_f(0.35, 0.2), fingers_r=_f(0.35, 0.2)), "auto"),
        # On her knees, the left knee coming up and through, the chest going
        # forward over where the foot will land.
        (13, {"hips": {"pos": _hips_at(0.52, 0.06, 0.0, 30), "rot": (30, 22, -4)}, "spine": (8, 14, 0), "neck": (8, -2, 0), "head": (12, -4, -2),
              "foot_l": foot((0.13, 0.16, 0.06), 30, pitch=-70, pole=(0.2, 0.3, 1.0)),
              "foot_r": merge(knelt_r, pos=_yaw((-0.11, -0.045, -0.12), 20), rot=(16, 140, 0)),
              "hand_l": arm((0.13, -0.26, 0.22), (0.7, -0.6, -0.3)), "hand_r": arm((-0.14, -0.36, -0.02), (-0.6, -0.4, -0.6)),
              "clav_l": (2, 4), "clav_r": (2, 0), "fingers_l": _f(0.35, 0.2), "fingers_r": _f(0.35, 0.2)}, "auto"),
        # The foot planted ahead, toward it; the weight onto it, the back toes tucked under.
        (16, {"hips": {"pos": _hips_at(0.60, 0.14, 0.02, T), "rot": (T - 6, 26, -4)}, "spine": (6, 14, 0), "neck": (4, -6, 0), "head": (6, -6, 0),
              "foot_l": foot((0.14, 0.0, 0.30), T, pole=(0.25, 0.3, 1.0)),
              "foot_r": foot((-0.12, 0.07, -0.40), T - 10, pitch=50, toe=55, pole=(-0.05, -0.8, 1.0), side=-1),
              "hand_l": arm((0.13, -0.22, 0.26), (0.7, -0.6, -0.3)), "hand_r": arm((-0.13, -0.32, -0.04), (-0.6, -0.4, -0.6)),
              "clav_l": (2, 4), "clav_r": (0, 0), "fingers_l": _f(0.35, 0.2), "fingers_r": _f(0.35, 0.2)}, "auto"),
        # The drive up off it, the back knee off the ground and coming through.
        (20, {"hips": {"pos": _hips_at(0.86, 0.17, 0.03, T), "rot": (T - 2, 14, -3)}, "spine": (2, 8, 0), "neck": (2, -4, 0), "head": (4, -4, 0),
              "foot_l": foot((0.14, 0.0, 0.30), T, pole=(0.25, 0.2, 1.0)),
              "foot_r": foot((-0.13, 0.11, -0.14), T - 6, pitch=-30, toe=10, pole=(-0.05, -0.2, 1.0), side=-1),
              "hand_l": arm((0.11, -0.24, 0.26), (0.7, -0.6, -0.3)), "hand_r": arm((-0.09, -0.29, 0.14), (-0.7, -0.5, -0.4)),
              "clav_l": (2, 2), "clav_r": (2, 2), "fingers_l": _f(0.35, 0.2), "fingers_r": _f(0.35, 0.2)}, "auto"),
        # On her feet, square to it, set, the hands up and open.
        (23, _ready(T, 1.0, over=dict(hips={"pos": _hips_at(1.0, 0.13, 0.0, T), "rot": (T, 7, 0)}, fingers_l=_f(0.4, 0.25), fingers_r=_f(0.4, 0.25))), "auto"),
        # It lands in her knees, and settles.
        (27, _ready(T, 0.6), "ease"),
    ]
    # Held on it, breathing hard and fast, then slowing.
    for i, fr in enumerate(range(36, 106, 9)):
        keys.append((fr, _ready(T, (1.0 if i % 2 == 0 else -0.6) * max(0.3, 1.0 - i * 0.1)), "ease"))
'''
s = s[:a] + new + s[b:]
anchor = '''def kneel_to_stand_snap(rig):'''
helper = '''def _ready(turn, breath=0.0, over=None):
    """Standing set and ready, empty-handed, facing `turn` degrees to her
    left: the left foot a little ahead, the knees soft, the weight forward,
    the hands up and open before her; breathing (breath -1..1)."""
    from clips.actions import arm

    def foot(at, side):
        return {"pos": _yaw(at, turn), "rot": (turn + 6 * side, 0, 0), "pole": _yaw((0.15 * side, 0.0, 1.0), turn)}

    b = breath
    pose = {"hips": {"pos": _hips_at(0.985 + 0.004 * b, 0.12, 0.0, turn), "rot": (turn, 8, 0)}, "spine": (0, 8 - 2.5 * b, 0),
            "neck": (0, -2 + b, 0), "head": (4, -1, 0),
            "foot_l": foot((0.13, 0.0, 0.24), 1), "foot_r": foot((-0.13, 0.0, -0.02), -1),
            "hand_l": arm((0.10, -0.26, 0.26), (0.7, -0.6, -0.3)), "hand_r": arm((-0.08, -0.30, 0.22), (-0.7, -0.6, -0.3)),
            "clav_l": (4 + 2.5 * b, 4), "clav_r": (4 + 2.5 * b, 4), "fingers_l": _f(0.45, 0.3), "fingers_r": _f(0.45, 0.3)}
    pose.update(over or {})
    return pose


def kneel_to_stand_snap(rig):'''
s = s.replace(anchor, helper, 1)
# cup_hands stands in the same stance.
old_body = '''    def body(y, spine, neck, head, cl=(3, 4), cr=(3, 4)):
        return {"foot_l": foot((0.15, 0.0, 0.34), 1), "foot_r": foot((-0.15, 0.0, 0.04), -1),
                "hips": {"pos": _hips_at(y, 0.23, 0.0, T), "rot": (T, 8, 0)}, "spine": spine, "neck": neck, "head": head,
                "clav_l": cl, "clav_r": cr}'''
new_body = '''    def body(y, spine, neck, head, cl=(3, 4), cr=(3, 4)):
        return {"foot_l": foot((0.13, 0.0, 0.24), 1), "foot_r": foot((-0.13, 0.0, -0.02), -1),
                "hips": {"pos": _hips_at(y + 0.05, 0.12, 0.0, T), "rot": (T, 8, 0)}, "spine": spine, "neck": neck, "head": head,
                "clav_l": cl, "clav_r": cr}'''
assert old_body in s
s = s.replace(old_body, new_body)
open(p, "w", encoding="utf-8").write(s)
print("ok")
