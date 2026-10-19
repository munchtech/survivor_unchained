# k11b (C04 A): A6 CUT (lead); A5 restaged as an MCU from her left-front (posts out of frame, and the cut to A7's frontal CU
# is a cut-in, not a jump); harder sun (narrow, fill a stop down); lips together; A7 eyes off the lens down-left, lids
# lower, one slow drift, a blink; A8 trucked right, low dawn mist on the road and up the hill, faded before play.
def edit(shots, f):
    sun = {"do": "rig", "name": "sun", "energy": 1.8, "color": "#ffc890", "angle": 14, "from": {"actor": "her", "bone": "eyes", "off": [0.9, 0.35, 0.1]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}}
    a5 = shots["A5"]
    a5["cam"] = {"pos": {"actor": "her", "bone": "eyes", "off": [-0.8, -0.12, -1.7]}, "at": {"actor": "her", "bone": "eyes", "off": [0, -0.1, 0]}, "lens": 50, "focus": {"actor": "her", "bone": "eyes"}, "fstop": 2.0}
    for c in a5["cues"]:
        if c.get("do") == "atmosphere": c["hemi"] = 0.3; c["env"] = 0.3
        if c.get("do") == "rig" and c.get("name") == "sun": c.update(sun)
        if c.get("do") == "face" and c.get("at") == 0.8: c["keys"]["mouth_open"] = 0
        if c.get("do") == "face" and c.get("at") == 2.0: c["keys"] = {"mouth_open": 0, "smile": 0.08}
    a5["cues"].insert(3, {"do": "globe", "light": 4, "level": 0.25})
    f["shots"] = [s for s in f["shots"] if s["id"] != "A6"]
    a7 = shots["A7"]
    a7["cues"] = [dict(sun)] + [c for c in a7["cues"] if not (c.get("do") == "rig" and c.get("name") == "sun") and c.get("do") != "gaze"]
    for c in a7["cues"]:
        if c.get("do") == "face": c["keys"] = {"nose_wrinkle": 0, "squint": 0, "frown": 0, "mouth_open": 0, "smile": 0, "brows_sad": 0.45}
    a7["cues"] += [{"do": "gaze", "look": [-0.3, 0.22], "wander": 0.04},
        {"do": "lids", "value": 0.15, "over": 0.5},
        {"at": 2.2, "do": "gaze", "look": [-0.22, 0.27], "wander": 0.04, "snap": True},
        {"at": 3.1, "do": "gaze", "look": [-0.14, 0.3], "wander": 0.04},
        {"at": 3.9, "do": "gaze", "look": [-0.08, 0.31], "wander": 0.04},
        {"at": 4.6, "do": "lids", "value": 1, "over": 0.08},
        {"at": 4.72, "do": "lids", "value": 0.15, "over": 0.15}]
    a8 = shots["A8"]
    a8["cam"]["pos"]["off"] = [1.6, 0.6, 3.0]; a8["cam"]["at"] = [1.0, 4.0, -110.0]
    m = {"do": "mist", "color": "#cbb9b0", "falloff": 2.5, "density": 0.55}
    a8["cues"][1:1] = [dict(m, name="road1", where=[0.5, 0, -68.0], size=[30, 1.4, 12], sink=0.6),
        dict(m, name="road2", where=[0.5, 0, -80.0], size=[34, 1.6, 12], sink=1.0),
        dict(m, name="road3", where=[0.5, 0, -92.0], size=[38, 1.8, 12], sink=1.0),
        dict(m, name="road4", where=[0.5, 0, -104.0], size=[42, 2.2, 14], sink=1.0)]
    a8["cues"] += [{"at": 2.5, "do": "mist", "name": n, "density": 0, "over": 2.6} for n in ("road1", "road2", "road3", "road4")]
