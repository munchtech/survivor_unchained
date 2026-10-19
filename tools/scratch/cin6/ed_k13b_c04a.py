# k13b (C04 A): round-2 fixes; A2 cut (its dawn ramp, place and idle carried onto A3 at the same moment).
def edit(shots, f):
    a2 = shots["A2"]
    f["shots"] = [s for s in f["shots"] if s["id"] != "A2"]
    a3 = shots["A3"]
    # A2's ramp was k0 0.2 -> 1 over 9 s from A2's start; A3 began 2.2 s in (0.2 + 0.8 * 2.2 / 9 = 0.396).
    a3["cues"] = [{"do": "atmosphere", "preset": "dawn", "from": "night", "k0": 0.396, "over": 6.8},
                  {"do": "place", "mark": "road"},
                  {"do": "anim", "clip": "@idle", "blend": 0},
                  # 8. the dawn sun on her: behind the camera, 30 deg up, a 35 deg cone on face and shoulders.
                  {"do": "rig", "name": "sun", "energy": 2.0, "color": "#ffc890", "angle": 35,
                   "from": {"actor": "her", "bone": "eyes", "off": [2.0, 1.15, 0.0]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.15, 0]}}] + a3["cues"]
    # 11. A4: the tilt ends low: the camera down to 0.35 m, the frame's top at her knees.
    a4 = shots["A4"]
    a4["cam"]["move"] = {"pos": {"mark": "road", "off": [0.4, 0.35, -3.2]}, "at": {"mark": "road", "off": [0, -0.58, 0]},
                         "start": 0, "end": 2.0, "ease": "inout"}
    # 14. A5: pan 3 deg left (the globe off the right edge).
    shots["A5"]["cam"]["at"]["off"] = [-0.04, -0.1, 0.02]
    # 5. A7: the sun a side key 65 deg off the lens, 35 deg cone over face and neck; the lens light only a catch-light.
    for c in shots["A7"]["cues"]:
        if c.get("name") == "sun":
            c.update({"angle": 35})
            c["from"]["off"] = [0.93, 0.35, -0.36]  # frame left, the east, where A3 and A5 have the sun
            c["aim"]["off"] = [0, -0.06, 0]
        if c.get("name") == "eye": c["energy"] = 0.1
    # 6. A8: the road mist thin, a dawn haze, not ink.
    for c in shots["A8"]["cues"]:
        if c.get("do") == "mist" and "where" in c: c["density"] = 0.3
