p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70\tools\anim\clips\warden.py"
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)


rep('''- rise_stiff (C02 shot 5): on his back under the river, the knees drawn
  up; he sits up slowly, rests a beat on his knees, then gets his feet
  under him and rises straight up. Take 1: the others twist off their
  line or jack-knife like a sit-up.''', '''- rise_stiff (C02 shot 5): on his back under the river, the knees drawn
  up; he sits up slowly, rests a beat on his knees, then gets his feet
  under him and rises straight up, standing by 3.8 s of the shot's 5.
  Take 1: the others twist off their line or jack-knife like a sit-up.
  The lamp never touches the water: his left forearm is held up from
  the elbow as he lies, the lamp kept high and wide as he sits, and at
  his side as he stands (keyed over the take, whose left hand pushes on
  the ground).''')
rep('''def rise_stiff(name, rig: Rig):
    # From 0.9 s, as the knees come up (the take lies still before then).
    c = make(rig, name, "kimodo", "rise_stiff_1.bvh", warp_=[(0.9, 6.6, 5.7)], place="keep",
             note="the Warden (C02): up from his back under the river, slow and stiff")
    if c is None:
        return None
    c = _grounded(rig.sk, c)
    c.meta["hold"] = True
    return c''', '''def _ease(keys, fr):
    """Smoothstep between (frame, value) keys."""
    if fr <= keys[0][0]:
        return np.array(keys[0][1], float)
    for (f0, a), (f1, b) in zip(keys, keys[1:]):
        if fr <= f1:
            u = (fr - f0) / (f1 - f0)
            u = u * u * (3 - 2 * u)
            return np.array(a, float) + (np.array(b, float) - np.array(a, float)) * u
    return np.array(keys[-1][1], float)


def rise_stiff(name, rig: Rig):
    # From 0.9 s, as the knees come up (the take lies still before then):
    # the sit-up in 1.9 s, the rest on his knees 0.8 s, up in 1.5 s.
    base = make(rig, name, "kimodo", "rise_stiff_1.bvh", warp_=[(0.9, 3.5, 1.9), (3.5, 4.5, 0.8), (4.5, 6.6, 1.5)],
                place="keep", note="the Warden (C02): up from his back under the river, slow and stiff, the lamp kept up")
    if base is None:
        return None
    base = _grounded(rig.sk, base)
    sk = rig.sk
    I = sk.index
    g, p = sk.fk(base.rot, base.pos)
    # The lamp hand from the left shoulder, in his space: the forearm stood
    # up off the elbow as he lies; out wide and high as he sits; then at
    # his side, a little forward, as he stands.
    lamp = [(0, (0.10, 0.27, 0.16)), (12, (0.12, 0.28, 0.16)), (57, (0.30, 0.10, 0.22)), (81, (0.30, 0.06, 0.24)),
            (104, (0.20, -0.30, 0.26)), (base.frames - 1, (0.10, -0.44, 0.16))]
    pole = [(0, (0.4, -1.0, 0.0)), (57, (0.8, -0.6, -0.2)), (104, (0.7, -0.2, -0.7))]
    keys = []
    for fr in range(base.frames):
        hand_l = {"pos": tuple(p[fr, I["upperarm_l"]] + _ease(lamp, fr)), "pole": tuple(_ease(pole, fr)), "frame": "char"}
        keys.append((fr, {"hand_l": hand_l, "fingers_l": "fist"}, "linear"))
    return build(name, rig, keys, base=base, meta=dict(base.meta, hold=True))''')
rep('''    lamp = [(0, (0.27, 0.92, 0.06)), (24, (0.24, 1.00, 0.30)), (48, (0.14, 0.86, 0.50)), (72, (0.06, 0.66, 0.60)),
            (n - 1, (0.05, 0.64, 0.61))]''', '''    lamp = [(0, (0.27, 0.92, 0.06)), (24, (0.24, 1.00, 0.32)), (48, (0.15, 0.86, 0.54)), (72, (0.08, 0.66, 0.66)),
            (n - 1, (0.08, 0.64, 0.67))]''')
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
