p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a435f4dd0ac80df75\tools\anim\crowd.py"
s = open(p, encoding="utf-8").read()
a_start = s.index("        # Down: folded over, the fists into the ground before the feet.")
a_end = s.index("    keys = _in_char(rig, keys)\n    return build(name, rig, keys, meta={\"layer\": \"full\", \"hold\": True, \"source\": \"keyed (tools/anim/crowd.py)\",\n                                        \"note\": \"a heavy's slam")
new = '''        # Down: folded over into a squat, the fists into the ground before the feet.
        (29, {**wide, "hips": {"pos": H(0, 0.50, -0.12), "rot": (0, 44, 0)}, "spine": (0, 40, 0), "neck": (0, 2, 0), "head": (0, -8, 0),
              "clav_l": (-4, 16), "clav_r": (-4, 16), **down(0.14)}, "fast"),
        (34, {**wide, "hips": {"pos": H(0, 0.46, -0.13), "rot": (0, 48, 0)}, "spine": (0, 42, 0), "neck": (0, 4, 0), "head": (0, -6, 0),
              "clav_l": (-6, 18), "clav_r": (-6, 18), **down(0.08)}, "ease"),
        (45, {**wide, "hips": {"pos": H(0, 0.48, -0.13), "rot": (0, 46, 0)}, "spine": (0, 40, 0), "neck": (0, 4, 0), "head": (0, -8, 0),
              "clav_l": (-4, 16), "clav_r": (-4, 16), **down(0.09)}, "ease"),
    ]
'''
s = s[:a_start] + new + s[a_end:]
# The impact hands: placed on the ground in her space.
a = '''    keys = [
        # The gather: down into the knees, the fists low and in, the chest over them.'''
b = '''    def down(y):
        """The fists on the ground before the feet (armed: the axe head down flat in front)."""
        if armed:
            return {"hand_r": {"frame": "char", "pos": P(-0.06, y, 0.46), "pole": (-0.8, 0.4, -0.3), "blade": (0.0, -0.15, 1.0)},
                    "hand_l": arm((-0.10, -0.30, 0.22), (0.9, -0.4, -0.3)), "fingers_l": "fist", "fingers_r": "grip"}
        return {"hand_l": {"frame": "char", "pos": P(0.09, y, 0.42), "pole": (0.8, 0.4, -0.3), "knuckles": (0.0, -0.4, 0.9)},
                "hand_r": {"frame": "char", "pos": P(-0.09, y, 0.42), "pole": (-0.8, 0.4, -0.3), "knuckles": (0.0, -0.4, 0.9)},
                "fingers_l": "fist", "fingers_r": "fist"}

    keys = [
        # The gather: down into the knees, the fists low and in, the chest over them.'''
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")
