p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70\tools\anim\clips\warden.py"
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)


# Fingers from rest, so a keyed grip closes properly (the take's hands are loose and the thumb out).
rep('''def _pole(p, I, side, fr):''', '''def _bare_hands(sk, clip: Clip):
    """The take's fingers put back to rest, so the keyed grip and fist close
    from there (a take's hands are loose, the thumbs out)."""
    for j, n in enumerate(sk.names):
        if any(n.startswith(f) for f in ("thumb_", "index_", "middle_", "ring_", "pinky_")):
            clip.rot[:, j] = sk.rest_rot[j]
    return clip


def _pole(p, I, side, fr):''')
rep('''    base = _settled(sk, _grounded(sk, base))''', '''    base = _bare_hands(sk, _settled(sk, _grounded(sk, base)))''')
# The lamp hangs from the top of the fist (WardenView): the fist is kept upright, the knuckles up.
rep('''    lamp = [(0, (0.10, 0.27, 0.16)), (12, (0.12, 0.28, 0.16)), (57, (0.30, 0.10, 0.22)), (81, (0.30, 0.08, 0.24)),
            (104, (0.28, -0.08, 0.30)), (n - 1, (0.12, -0.40, 0.18))]
    pole = [(0, (0.4, -1.0, 0.0)), (57, (0.8, -0.6, -0.2)), (104, (0.8, -0.3, -0.5)), (n - 1, (0.7, -0.2, -0.7))]''',
    '''    lamp = [(0, (0.10, 0.27, 0.16)), (12, (0.12, 0.28, 0.16)), (57, (0.30, 0.10, 0.22)), (81, (0.30, 0.08, 0.24)),
            (104, (0.26, -0.10, 0.32)), (n - 1, (0.12, -0.26, 0.30))]
    pole = [(0, (0.4, -1.0, 0.0)), (57, (0.8, -0.6, -0.2)), (104, (0.8, -0.4, -0.4)), (n - 1, (0.6, -0.5, -0.6))]''')
rep('''        hand_l = {"pos": tuple(p[fr, I["upperarm_l"]] + _ease(lamp, fr)), "pole": tuple(_ease(pole, fr)), "frame": "char"}
        hand_r = {"pole": _pole(p, I, "r", fr),''', '''        hand_l = {"pos": tuple(p[fr, I["upperarm_l"]] + _ease(lamp, fr)), "pole": tuple(_ease(pole, fr)), "frame": "char",
                  "knuckles": (0.0, 1.0, 0.15)}
        hand_r = {"pole": _pole(p, I, "r", fr),''')
rep('''    sk = rig.sk
    I = sk.index
    g, p = sk.fk(base.rot, base.pos)
    n = base.frames
    # The lamp's path''', '''    sk = rig.sk
    base = _bare_hands(sk, base)
    I = sk.index
    g, p = sk.fk(base.rot, base.pos)
    n = base.frames
    # The lamp's path''')
rep('''    # C02 (his size 2.5, in the river 0.45 below her).
    lamp = [(0, (0.27, 0.92, 0.06)), (30, (0.25, 1.00, 0.30)), (55, (0.15, 0.92, 0.58)), (80, (0.10, 0.88, 0.72)),
            (100, (0.09, 0.87, 0.74)), (160, (0.08, 0.86, 0.75)), (n - 1, (0.09, 0.86, 0.74))]''', '''    # C02 (his size 2.5, in the river 0.45 below her); the flame hangs 0.25
    # of his metres under the fist, so the fist is held that much higher.
    lamp = [(0, (0.27, 0.92, 0.06)), (30, (0.25, 1.06, 0.30)), (55, (0.15, 1.04, 0.56)), (80, (0.10, 1.00, 0.70)),
            (100, (0.09, 0.99, 0.72)), (160, (0.08, 0.98, 0.73)), (n - 1, (0.09, 0.98, 0.72))]''')
rep('''        hand_l = {"pos": tuple(_ease(lamp, fr) + tremble(fr) + sway), "pole": (0.8, -0.5, -0.3), "frame": "char",
                  "knuckles": (-0.2, 0.2, 0.96)}''', '''        hand_l = {"pos": tuple(_ease(lamp, fr) + tremble(fr) + sway), "pole": (0.8, -0.6, -0.2), "frame": "char",
                  "knuckles": (-0.1, 1.0, 0.2)}''')
# The bend keeps the feet where the take plants them.
rep('''warp_=[(0.9, 1.7, 1.4), (1.7, 1.95, 0.8), (1.95, 2.05, 0.7), (2.05, 2.15, 6.0)], place="pin",''',
    '''warp_=[(0.9, 1.7, 1.4), (1.7, 1.95, 0.8), (1.95, 2.05, 0.7), (2.05, 2.15, 6.0)], place="keep",''')
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
