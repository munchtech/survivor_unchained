# Face 30's lighting notes, first values (UNJUDGED): python jedit.py <cine> ed_light.py
EYE = {"do": "rig", "name": "eye", "energy": 0.3, "color": "#fff3e6", "angle": 14, "from": {"lens": [0, 0.25, 0]}, "aim": {"actor": "her", "bone": "eyes"}}


def edit(shots, f):
    if f["id"] == "c01":
        shots["8"]["cues"].insert(0, dict(EYE))
        # warm fill under her left eye (screen right), as the coals would give
        shots["8"]["cues"].insert(1, {"do": "rig", "name": "under", "energy": 0.25, "color": "#ffc890", "angle": 18,
                                      "from": {"lens": [0.35, -0.3, 0]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}})
        shots["8b"]["cues"].insert(0, dict(EYE))
        # a cool rim on her crown against the dark (behind her, the camera looks north): from north, above
        shots["7"]["cues"].insert(0, {"do": "rig", "name": "rim", "energy": 0.8, "color": "#b9c9ff", "angle": 20,
                                      "from": {"actor": "her", "bone": "head", "off": [0.4, 0.7, -1.6]}, "aim": {"actor": "her", "bone": "head", "off": [0, 0.08, 0]}})
    if f["id"] == "c04a":
        shots["A5"]["cues"].insert(0, dict(EYE))
        shots["A7"]["cues"].insert(0, dict(EYE))
    if f["id"] == "c02":
        s = shots["8"]
        s["cam"]["at"]["off"] = [0, 0.01, 0]
        for c in s["cues"]:
            if c.get("do") == "glow" and c.get("name") == "held":
                c["light"] = 1.0
                c["color"] = "#a8d2ff"
