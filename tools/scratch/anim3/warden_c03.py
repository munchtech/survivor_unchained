

# --------------------------------------------------------------------- C03 --
# The Warden's end, keyed: Kimodo's kneel_fall takes drop him to his knees in
# a second and dive him onto his face with the arms flung out ahead, all in
# three seconds. C03 wants a slow, heavy kneel with the lamp held up and
# steady, a long look at it while the arm begins to shake, the fist lowered
# until the lamp goes into the river, and then a fold forward into the water,
# still. So three clips, each starting where the last ends, so the cinematic
# can cut them to its shots:
# - kneel_lamp (shots 2, 3, 3b): down on the right knee, then the left; the
#   greatsword let go at 1.4 s; the lamp brought up before his face and held
#   there, the eyes on it; breathing; from 6 s the arm begins to shake, and
#   by 10 s it shakes badly. Held shaking.
# - lamp_down (shot 4): the fist sinks; the lamp meets the water at 1.1 s
#   and goes under; the arm comes to rest on his thigh, the head bowed.
# - fold_forward (shot 5): over onto his face in the water without a hand put
#   out, the legs sliding out behind; face down and still by 2.4 s.
# Water in C03 stands about 0.34 of his metres (0.85 m) over the bed he kneels
# on, so the lamp's flame, 0.25 under his fist, meets it with the fist at 0.6.

WATER = 0.34


def _knelt(P, H, breath=0.0, sag=0.0):
    """Upright on both knees, the shins back along the bed, the toes behind."""
    return {"hips": {"pos": H(0, 0.50 - 0.02 * sag, -0.02), "rot": (0, 4 + 4 * sag, 0)},
            "spine": (0, 2 + 1.5 * breath + 8 * sag, 0), "clav_l": (2 * breath, 4), "clav_r": (2 * breath - 3 * sag, 6),
            "foot_l": {"pos": P(0.14, 0.02, -0.36), "rot": (8, -70, 0), "pole": (0.2, -1, 0.5)},
            "foot_r": {"pos": P(-0.15, 0.02, -0.38), "rot": (-8, -70, 0), "pole": (-0.2, -1, 0.5)}}


def _hand(P, at, pole, knuckles=None):
    h = {"frame": "char", "pos": P(*at), "pole": pole}
    if knuckles is not None:
        h["knuckles"] = knuckles
    return h


def kneel_lamp(name, rig: Rig):
    P, H = _kit(rig)
    lamp_up = (0.12, 1.12, 0.34)
    look = dict(neck=(4, 6, 0), head=(10, 10, 4))
    sword = _hand(P, (-0.30, 0.86, 0.06), (-0.4, 0.0, -1.0))
    sword["blade"], sword["knuckles"] = (0.0, -0.95, 0.3), (0.0, -0.3, -0.95)
    hang_r = _hand(P, (-0.26, 0.38, 0.02), (-0.5, 0.0, -1.0))
    keys = [
        # Reeling from the blow, the lamp still before him.
        (0, {"hips": {"pos": H(0, 0.92, 0.0), "rot": (0, 8, 0)}, "spine": (0, 10, 0), "neck": (0, 8, 0), "head": (0, 10, 0),
             "foot_l": {"pos": P(0.14, 0, 0.12), "rot": (10, 0, 0)}, "foot_r": {"pos": P(-0.15, 0, -0.08), "rot": (-12, 0, 0)},
             "hand_l": _hand(P, (0.24, 1.10, 0.22), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)), "hand_r": sword,
             "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP}, "ease"),
        # The knees go; the lamp is held up out of instinct.
        (14, {"hips": {"pos": H(0, 0.74, 0.02), "rot": (0, 10, 0)}, "spine": (0, 8, 0), "neck": (0, 6, 0), "head": (0, 6, 0),
              "foot_l": {"pos": P(0.14, 0, 0.12), "rot": (10, 0, 0), "pole": (0.2, 0, 1)},
              "foot_r": {"pos": P(-0.15, 0.02, -0.10), "rot": (-12, -10, 0), "pole": (-0.2, 0, 1)},
              "hand_l": _hand(P, (0.22, 1.12, 0.28), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)), "hand_r": sword,
              "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP}, "auto"),
        # The right knee down on the bed, the left foot still before him.
        (28, {"hips": {"pos": H(0, 0.58, 0.0), "rot": (-6, 8, 4)}, "spine": (4, 10, 0), "neck": (0, 8, 0), "head": (2, 8, 0),
              "foot_l": {"pos": P(0.14, 0, 0.16), "rot": (10, 0, 0), "pole": (0.2, 0.3, 1)},
              "foot_r": {"pos": P(-0.15, 0.02, -0.38), "rot": (-8, -70, 0), "pole": (-0.2, -1, 0.5)},
              "hand_l": _hand(P, (0.18, 1.06, 0.30), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)), "hand_r": sword,
              "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP}, "auto"),
        # The greatsword let go (C03: at 1.4 s it leaves his hand and sinks).
        (40, {"hips": {"pos": H(0, 0.57, 0.0), "rot": (-6, 9, 4)}, "spine": (4, 11, 0), "neck": (0, 8, 0), "head": (2, 8, 0),
              "foot_l": {"pos": P(0.14, 0, 0.16), "rot": (10, 0, 0), "pole": (0.2, 0.3, 1)},
              "foot_r": {"pos": P(-0.15, 0.02, -0.38), "rot": (-8, -70, 0), "pole": (-0.2, -1, 0.5)},
              "hand_l": _hand(P, (0.17, 1.06, 0.31), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)),
              "hand_r": _hand(P, (-0.30, 0.66, 0.10), (-0.5, 0.0, -1.0)), "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP}, "auto"),
        (44, {"hips": {"pos": H(0, 0.56, 0.0), "rot": (-5, 9, 4)}, "spine": (4, 11, 0), "neck": (0, 8, 0), "head": (2, 8, 0),
              "foot_l": {"pos": P(0.14, 0, 0.16), "rot": (10, 0, 0), "pole": (0.2, 0.3, 1)},
              "foot_r": {"pos": P(-0.15, 0.02, -0.38), "rot": (-8, -70, 0), "pole": (-0.2, -1, 0.5)},
              "hand_l": _hand(P, (0.16, 1.07, 0.31), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)),
              "hand_r": _hand(P, (-0.29, 0.60, 0.08), (-0.5, 0.0, -1.0)), "fingers_l": LAMP_FIST, "fingers_r": "open"}, "auto"),
        # The left knee down too: on both knees in the river.
        (56, {**_knelt(P, H, sag=1.0), "neck": (0, 10, 0), "head": (4, 8, 0),
              "hand_l": _hand(P, (0.15, 1.05, 0.32), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)), "hand_r": hang_r,
              "fingers_l": LAMP_FIST, "fingers_r": "relaxed"}, "auto"),
        # Up straight, and the lamp brought up before his face; he looks at it.
        (74, {**_knelt(P, H, breath=0.5), **look, "hand_l": _hand(P, lamp_up, (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)),
              "hand_r": hang_r, "fingers_l": LAMP_FIST, "fingers_r": "relaxed"}, "ease"),
    ]
    # Breathing while he looks; the arm sagging a little once it shakes.
    for i, fr in enumerate(range(104, 316, 30)):
        breath = 1.0 if i % 2 == 0 else 0.0
        sag = min(1.0, max(0.0, (fr - 180) / 135))
        at = (lamp_up[0], lamp_up[1] - 0.04 * sag, lamp_up[2] - 0.02 * sag)
        keys.append((fr, {**_knelt(P, H, breath=breath), **look, "hand_l": _hand(P, at, (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)),
                          "hand_r": hang_r, "fingers_l": LAMP_FIST, "fingers_r": "relaxed"}, "ease"))

    def shake(fr, pose):
        """From 6 s the lamp-arm shakes, the tremor growing for four seconds."""
        grow = min(1.0, max(0.0, (fr - 180) / 120)) ** 1.5
        if grow <= 0:
            return pose
        t = fr / 30
        d = 0.012 * grow * np.array([math.sin(2 * math.pi * 6.3 * t) + 0.4 * math.sin(2 * math.pi * 9.1 * t + 1),
                                     0.8 * math.sin(2 * math.pi * 7.7 * t + 0.6), 0.5 * math.sin(2 * math.pi * 5.2 * t + 2)])
        h = dict(pose["hand_l"])
        h["pos"] = tuple(np.array(h["pos"]) + d)
        return {**pose, "hand_l": h}

    return build(name, rig, keys, post=shake, meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/clips/warden.py)",
                                                     "note": "the Warden (C03): down on his knees, the lamp held up and looked at; the arm begins to shake"})


def lamp_down(name, rig: Rig):
    P, H = _kit(rig)
    hang_r = _hand(P, (-0.26, 0.38, 0.02), (-0.5, 0.0, -1.0))
    up = (0.12, 1.08, 0.32)
    keys = [
        (0, {**_knelt(P, H), "neck": (4, 6, 0), "head": (10, 10, 4), "hand_l": _hand(P, up, (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)),
             "hand_r": hang_r, "fingers_l": LAMP_FIST, "fingers_r": "relaxed"}, "ease"),
        # The shoulders give; the fist starts down.
        (15, {**_knelt(P, H, sag=0.4), "neck": (4, 10, 0), "head": (8, 14, 4),
              "hand_l": _hand(P, (0.14, 0.92, 0.33), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)), "hand_r": hang_r,
              "fingers_l": LAMP_FIST, "fingers_r": "relaxed"}, "auto"),
        # The lamp meets the river (its flame goes out here, 1.1 s).
        (33, {**_knelt(P, H, sag=0.8), "neck": (2, 14, 0), "head": (4, 18, 2),
              "hand_l": _hand(P, (0.17, WATER + 0.26, 0.33), (0.8, -0.3, -0.5), (0.0, 1.0, 0.2)), "hand_r": hang_r,
              "fingers_l": LAMP_FIST, "fingers_r": "relaxed"}, "auto"),
        # Under, and the arm comes to rest on his thigh; the head bowed.
        (52, {**_knelt(P, H, sag=1.0), "neck": (0, 18, 0), "head": (0, 22, 0),
              "hand_l": _hand(P, (0.18, 0.46, 0.30), (0.6, 0.0, -0.8), (0.0, 0.6, 0.8)), "hand_r": hang_r,
              "fingers_l": LAMP_FIST, "fingers_r": "relaxed"}, "ease"),
        (75, {**_knelt(P, H, breath=-0.5, sag=1.0), "neck": (0, 19, 0), "head": (0, 23, 0),
              "hand_l": _hand(P, (0.18, 0.45, 0.30), (0.6, 0.0, -0.8), (0.0, 0.6, 0.8)), "hand_r": hang_r,
              "fingers_l": LAMP_FIST, "fingers_r": "relaxed"}, "ease"),
    ]
    return build(name, rig, keys, meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/clips/warden.py)",
                                        "note": "the Warden (C03): the fist lowered, the lamp into the river"})


def fold_forward(name, rig: Rig):
    P, H = _kit(rig)
    knelt = _knelt(P, H, breath=-0.5, sag=1.0)
    rest_l = _hand(P, (0.18, 0.45, 0.30), (0.6, 0.0, -0.8), (0.0, 0.6, 0.8))
    hang_r = _hand(P, (-0.26, 0.38, 0.02), (-0.5, 0.0, -1.0))
    keys = [
        (0, {**knelt, "neck": (0, 19, 0), "head": (0, 23, 0), "hand_l": rest_l, "hand_r": hang_r,
             "fingers_l": LAMP_FIST, "fingers_r": "relaxed"}, "ease"),
        # The last of him goes: the head drops, the shoulders roll in.
        (12, {**knelt, "spine": (0, 14, 0), "neck": (0, 24, 0), "head": (4, 26, 6), "clav_l": (-4, 10), "clav_r": (-4, 10),
              "hand_l": rest_l, "hand_r": hang_r, "fingers_l": LAMP_FIST, "fingers_r": "relaxed"}, "ease"),
        # Tipping over the knees, slow, then faster.
        (32, {**knelt, "hips": {"pos": H(0, 0.47, 0.06), "rot": (4, 30, 4)}, "spine": (4, 20, 4), "neck": (0, 18, 0), "head": (8, 20, 10),
              "hand_l": _hand(P, (0.20, 0.42, 0.24), (0.7, 0.0, -0.7)), "hand_r": _hand(P, (-0.22, 0.36, 0.10), (-0.7, 0.0, -0.7)),
              "fingers_l": LAMP_FIST, "fingers_r": "relaxed"}, "auto"),
        (46, {**knelt, "hips": {"pos": H(0, 0.40, 0.14), "rot": (8, 58, 8)}, "spine": (6, 14, 6), "neck": (6, -2, 0), "head": (20, 4, 14),
              "foot_l": {"pos": P(0.16, 0.02, -0.50), "rot": (8, -80, 0), "pole": (0.2, -0.2, 1)},
              "foot_r": {"pos": P(-0.15, 0.03, -0.54), "rot": (-8, -80, 0), "pole": (-0.2, -0.2, 1)},
              "hand_l": arm((0.14, -0.36, -0.16), (0.6, -0.2, -0.5)), "hand_r": arm((-0.12, -0.36, -0.18), (-0.6, -0.2, -0.5)),
              "fingers_l": LAMP_FIST, "fingers_r": "open"}, "linear"),
        # Into the water face first, no hand put out; the legs slide out behind.
        (54, merge(_on_face(P, H), hips={"pos": H(0.0, 0.13, 0.34), "rot": (6, 90, 4)}, neck=(10, -6, 0), head=(24, -2, 0),
                   foot_l={"pos": P(0.30, 0.10, -0.34), "rot": (20, 120, -30), "pole": (1, 0.1, 0.4)},
                   foot_r={"pos": P(-0.16, 0.08, -0.58), "rot": (-15, 120, 0), "pole": (-0.2, -1, 0)},
                   hand_l={"frame": "char", "pos": P(0.30, 0.08, 0.80), "pole": (1, 0.3, -0.2), "knuckles": (0.2, 0, 1)},
                   fingers_l=LAMP_FIST), "auto"),
        (60, merge(_on_face(P, H), hips={"pos": H(0.0, 0.15, 0.36), "rot": (8, 87, 6)}, neck=(16, -12, 0), head=(36, -8, 0),
                   fingers_l=LAMP_FIST), "auto"),
        (72, merge(_on_face(P, H, 1.0), fingers_l=LAMP_FIST), "ease"),
        (120, merge(_on_face(P, H, 1.0), fingers_l=LAMP_FIST), "ease"),
    ]
    keys = _in_char(rig, keys)
    return build(name, rig, keys, meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/clips/warden.py)",
                                        "note": "the Warden (C03): folded forward into the river, face down, still"})


# name: function(name, rig) -> Clip or None (the take not on this machine).
CLIPS = {"rise_stiff": rise_stiff, "bend_lift": bend_lift, "kneel_lamp": kneel_lamp, "lamp_down": lamp_down,
         "fold_forward": fold_forward}
