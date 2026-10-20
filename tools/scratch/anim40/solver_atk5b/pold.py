def cast_flick(rig):
    """The wand's spell: the whole arm whipped out from over the shoulder at
    the foe, ending pointed straight at it, the free hand flung open behind
    for balance.

    (anim 41, solver 2) The wind-up hand out beside the hat's brim, not behind her head: its wand went back over
    her left and its crystal came out through the hat's crown. Now the hand is 19 cm further out, beside her head
    (the wand's tip 60 cm out from her head's axis, clear of the brim), the wand up and back, the knuckles keyed so
    the whip's hand and forearm spins are 24/11 deg a frame (65 and 54 before). The free arm at the aim was flung
    out level from the shoulder (a T, its elbow keyed out to the side): now its elbow hangs bent, down and a
    little out, the hand at her hip-to-ribs height, 14 cm out from her side and a little behind."""
    # (anim 42) Her whole body plays it standing (meta stance): a caster's step, the left foot ahead, knees soft,
    # the weight rocking back at the wind-up and forward into the flick. The free hand starts low at her left side
    # (not cupped at her chest) and at the aim hangs long and close, the fingers relaxed; the wand arm reaches
    # forward of her shoulder, the elbow a little soft (not locked).
    def step(weight):
        p = stance(0.015, l=(0.15, 0.14), r=(-0.15, -0.10))
        p["hips"]["pos"] = (0.02 * weight, -0.015 - 0.01 * abs(weight), 0.035 * weight)
        return p
    keys = [
        (0, body(step(-0.4), hips=(-10, -2, 0), spine=(-18, -4, 0), head=(22, 0, 0),
                 hand_r=arm((-0.25, 0.12, 0.18), (-0.8, -0.3, -0.4), blade=_n(-0.506, 0.861, 0.051),
                            knuckles=_n(-0.862, -0.507, 0.0)),
                 hand_l=arm((0.08, -0.48, 0.06), (0.3, -0.2, -1.0)), fingers_r="grip", fingers_l="relaxed"), "fast"),
        (3, body(step(0.6), hips=(6, 6, 0), spine=(10, 6, 0), head=(-12, -4, 0),
                 hand_r=arm((0.02, -0.05, 0.51), (-0.8, -0.4, -0.2), blade=_n(0.0, -0.05, 1.0)),
                 hand_l=arm((0.10, -0.46, -0.06), (0.3, -0.3, -1.0)), fingers_r="grip", fingers_l="relaxed"), "ease"),
        (8, body(step(0.6), hips=(6, 6, 0), spine=(11, 6, 0), head=(-13, -4, 0),
                 hand_r=arm((0.02, -0.07, 0.505), (-0.8, -0.4, -0.2), blade=_n(0.0, -0.1, 1.0)),
                 hand_l=arm((0.10, -0.46, -0.07), (0.3, -0.3, -1.0)), fingers_r="grip", fingers_l="relaxed"), "auto"),
        (18, body(step(0.0), hand_r=arm((0.0, -0.36, 0.14), (-0.6, -0.4, -0.5), blade=_n(-0.1, 0.5, 0.85)),
                  hand_l=arm((0.0, -0.38, 0.08), (0.6, -0.4, -0.5)), fingers_r="grip", fingers_l="relaxed"), "ease"),
    ]
    return build("cast_flick", rig, keys, lead=STRIKE, meta={"layer": "upper", "stance": True, "contact": 0.0,
                                                             "weapon": "wand"})

