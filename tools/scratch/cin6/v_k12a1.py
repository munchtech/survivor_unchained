# k12a1: four ways to stage C01 s3 on lie_side_wake (her face stays upright-ish).
EYES = {"actor": "her", "bone": "eyes"}
LIGHT = [
    {"do": "atmosphere", "preset": "night", "key": 0.4, "hemi": 0.1575, "env": 0.1575, "exposure": 0.92, "fog": 1.5, "fogColor": "#0a1018", "rim": 0.6, "elevation": 75},
    {"do": "light", "light": 0, "level": 0.06, "color": "#ff9a5a", "rate": 0.45},
    # Ember from the coals' near edge, low: the lower half of her face.
    {"do": "rig", "name": "ember", "energy": 0.32, "color": "#ffb070", "angle": 30, "from": {"mark": "fire", "off": [0.3, 0.1, -0.05]}, "aim": {"actor": "her", "bone": "head"}},
    # Moon from high and in front of her brow: the upper half, cool.
    {"do": "rig", "name": "moon", "energy": 0.55, "color": "#a9bfff", "angle": 30, "from": {"actor": "her", "bone": "head", "off": [-0.45, 1.3, -0.55]}, "aim": {"actor": "her", "bone": "head"}},
]
EYES_OPEN = [
    {"at": 2.0, "do": "lids", "value": 0, "over": 0.15},
    {"at": 2.0, "do": "face", "keys": {"eyes_wide": 0.25}, "over": 0.2},
    {"at": 2.6, "do": "face", "keys": {"eyes_wide": 0.05}, "over": 1.0},
    {"at": 2.2, "do": "lids", "value": None},
]


def s3(cam, extra=()):
    def fn(shots, f):
        s = shots["3"]
        s["cam"] = cam
        s["cues"] = [dict(c) for c in LIGHT] + list(extra) + [dict(c) for c in EYES_OPEN]
    return fn


VARIANTS = {
    # (a) ground level across the coals, 60 mm.
    "A": s3({"pos": [-11.55, 0.17, 90.72], "at": {**EYES, "off": [0, -0.04, 0]}, "lens": 60, "focus": EYES, "fstop": 2.0}),
    # (a') the same line from 0.5 m, a touch down onto her face (the chin over the throat).
    "B": s3({"pos": [-11.55, 0.5, 90.72], "at": {**EYES, "off": [0, -0.04, 0]}, "lens": 60, "focus": EYES, "fstop": 2.0}),
    # (c) high three-quarter, the whole figure small, and she pushes up onto her forearm.
    "C": s3({"pos": [-12.1, 2.2, 92.2], "at": {"actor": "her", "bone": "chest", "off": [0, 0.05, 0], "track": True}, "lens": 40,
             "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 4.0},
            [{"do": "anim", "clip": "her/lie_side_wake", "from": 1.5, "speed": 1.0, "blend": 0}]),
    # High front three-quarter close-up: looking down onto her face, the ground behind it.
    "F": s3({"pos": [-10.214, 1.02, 90.226], "at": {**EYES, "off": [0, -0.05, 0]}, "lens": 50, "focus": EYES, "fstop": 2.8}),
}
