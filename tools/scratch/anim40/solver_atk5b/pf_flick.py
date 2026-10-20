# parametric cast_flick (exec'd into clips.actions); globals FP override
import math as _m
_FP = dict(feet_l=(0.24, 0.10), feet_r=(-0.24, -0.10), crouch=0.035, wz=0.06, wx=0.02,
           b0=_n(-0.506, 0.861, 0.051), k0=_n(-0.862, -0.507, 0.0), a0=(-0.25, 0.12, 0.18),
           a3=(0.02, -0.05, 0.51), b3=_n(0.0, -0.05, 1.0), k3=None,
           a8=(0.02, -0.07, 0.505), b8=_n(0.0, -0.1, 1.0), k8=None, pole8=(-0.8, -0.4, -0.2),
           l8=(0.10, -0.46, -0.07), lpole8=(0.3, -0.3, -1.0), sp8=(11, 6, 0), hp8=(6, 6, 0), hd8=(-13, -4, 0))
_FP.update(globals().get("FP", {}))
def _pole(yaw, s):
    a = _m.radians(yaw); return (_m.sin(a) + s * 0.25, 0, _m.cos(a))
def cast_flick(rig):
    F = _FP
    def step(weight):
        p = stance(F["crouch"], l=F["feet_l"], r=F["feet_r"])
        p["foot_l"]["pole"] = _pole(10, 1); p["foot_r"]["pole"] = _pole(-14, -1)
        p["hips"]["pos"] = (F["wx"] * weight, -F["crouch"] - 0.012 * abs(weight), F["wz"] * weight)
        return p
    def hr(a, pole, b, k):
        return arm(a, pole, blade=b, **({"knuckles": k} if k is not None else {}))
    keys = [
        (0, body(step(-0.4), hips=(-10, -2, 0), spine=(-18, -4, 0), head=(22, 0, 0),
                 hand_r=hr(F["a0"], (-0.8, -0.3, -0.4), F["b0"], F["k0"]),
                 hand_l=arm((0.08, -0.48, 0.06), (0.3, -0.2, -1.0)), fingers_r="grip", fingers_l="relaxed"), "fast"),
        (3, body(step(0.6), hips=(6, 6, 0), spine=(10, 6, 0), head=(-12, -4, 0),
                 hand_r=hr(F["a3"], (-0.8, -0.4, -0.2), F["b3"], F["k3"]),
                 hand_l=arm(F["l8"], F["lpole8"]), fingers_r="grip", fingers_l="relaxed"), "ease"),
        (8, body(step(0.6), hips=F["hp8"], spine=F["sp8"], head=F["hd8"],
                 hand_r=hr(F["a8"], F["pole8"], F["b8"], F["k8"]),
                 hand_l=arm(F["l8"], F["lpole8"]), fingers_r="grip", fingers_l="relaxed"), "auto"),
        (18, body(step(0.0), hand_r=arm((0.0, -0.36, 0.14), (-0.6, -0.4, -0.5), blade=_n(-0.1, 0.5, 0.85)),
                  hand_l=arm((0.0, -0.38, 0.08), (0.6, -0.4, -0.5)), fingers_r="grip", fingers_l="relaxed"), "ease"),
    ]
    return build("cast_flick", rig, keys, lead=STRIKE, meta={"layer": "upper", "stance": True, "contact": 0.0,
                                                             "weapon": "wand"})
