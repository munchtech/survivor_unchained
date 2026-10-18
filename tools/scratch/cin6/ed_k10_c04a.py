# k10 (C04 A5-A7): the close-ups' own exposure (the birches' shade behind her) and a low side key from the sun (east: her right).
def edit(shots, f):
    for c in shots["A2"]["cues"]:
        if c.get("do") == "atmosphere": c["over"] = 9.0   # done before A5 sets its own
    sun = {"do": "rig", "name": "sun", "energy": 1.8, "color": "#ffc890", "angle": 30,
           "from": {"actor": "her", "bone": "eyes", "off": [0.9, 0.35, 0.1]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}}
    shots["A5"]["cues"][0:0] = [{"do": "atmosphere", "preset": "dawn", "exposure": 0.78, "hemi": 0.6, "env": 0.6}, dict(sun)]
    shots["A6"]["cues"].insert(0, dict(sun))
    shots["A7"]["cues"].insert(0, dict(sun))
    shots["A8"]["cues"].insert(0, {"do": "atmosphere", "preset": "dawn", "from": "now", "over": 1.5})
