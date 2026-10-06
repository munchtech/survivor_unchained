p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a435f4dd0ac80df75\tools\anim\clips\soul.py"
s = open(p, encoding="utf-8").read()
rep = [
('''    then up, a hand pushing the hair back."""
    def bent(b, up=0.0):''',
'''    then up, a hand pushing the hair back.

    Hands and head are placed from the body's own knees and head (hers are
    narrower and lower than the hero's)."""
    # How much further out the knees are, and the head higher and forward, than hers.
    kx = float(rig.prest[rig.I["calf_l"]][0]) + 0.6 * rig.feet_out - 0.103
    head = rig.prest[rig.I["Head"]]
    hy, hz = float(head[1]) - 1.666, float(head[2]) + 0.036

    def bent(b, up=0.0):'''),
('''            "hand_l": {"pos": (0.12, 0.56, 0.24), "pole": (0.9, 0.2, -0.3), "knuckles": (0.2, -0.6, 0.75)},
            "hand_r": {"pos": (-0.13, 0.55, 0.22), "pole": (-0.9, 0.2, -0.3), "knuckles": (-0.2, -0.6, 0.75)},''',
'''            "hand_l": {"pos": (0.12 + kx, 0.56, 0.24), "pole": (0.9, 0.2, -0.3), "knuckles": (0.2, -0.6, 0.75)},
            "hand_r": {"pos": (-0.13 - kx, 0.55, 0.22), "pole": (-0.9, 0.2, -0.3), "knuckles": (-0.2, -0.6, 0.75)},'''),
('''                   hand_l={"pos": (0.10, 1.66, 0.06), "pole": (1.0, 0.3, -0.2), "knuckles": (0.0, 0.4, -0.9)},''',
'''                   hand_l={"pos": (0.10, 1.66 + hy, 0.06 + hz), "pole": (1.0, 0.3, -0.2), "knuckles": (0.0, 0.4, -0.9)},'''),
]
for a, b in rep:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")
