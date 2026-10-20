F0R = dict(v=(-0.25,0.12,0.18), pole=(-0.8,-0.3,-0.4), blade=(-0.506,0.861,0.051), kn=(-0.862,-0.507,-0.000))
FL = dict(v=(0.15, -0.27, -0.02), pole=(0.5, -0.8, -0.3))
def cast_flick(rig):
    keys = [
        (0, body(stance(0.07, weight=-0.3), hips=(-10, -2, 0), spine=(-18, -4, 0), head=(22, 0, 0),
                 hand_r=arm(F0R["v"], F0R["pole"], blade=_n(*F0R["blade"]), knuckles=None if F0R["kn"] is None else _n(*F0R["kn"])),
                 hand_l=arm((0.06, -0.20, 0.30), (0.8, -0.4, -0.3)), fingers_r="grip", fingers_l="open"), "fast"),
        (3, body(stance(0.09, weight=0.4), hips=(6, 6, 0), spine=(10, 8, 0), head=(-12, -4, 0),
                 hand_r=arm((0.02, -0.04, 0.52), (-0.8, -0.4, -0.2), blade=_n(0.0, -0.05, 1.0)),
                 hand_l=arm(FL["v"], FL["pole"]), fingers_r="grip", fingers_l="spread"), "ease"),
        (8, body(stance(0.09, weight=0.4), hips=(6, 6, 0), spine=(11, 8, 0), head=(-13, -4, 0),
                 hand_r=arm((0.02, -0.06, 0.51), (-0.8, -0.4, -0.2), blade=_n(0.0, -0.1, 1.0)),
                 hand_l=arm((FL["v"][0], FL["v"][1] - 0.01, FL["v"][2]), FL["pole"]), fingers_r="grip", fingers_l="spread"), "auto"),
        (18, body(stance(0.06), hand_r=arm((0.0, -0.36, 0.14), (-0.6, -0.4, -0.5), blade=_n(-0.1, 0.5, 0.85)),
                  hand_l=arm((0.0, -0.38, 0.08), (0.6, -0.4, -0.5)), fingers_r="grip", fingers_l="relaxed"), "ease"),
    ]
    return build("cast_flick", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 0.0, "weapon": "wand"})
