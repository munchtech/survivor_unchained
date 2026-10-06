"""C03: animation's keyed clips for the Warden's end; the heart rises from his chest, which is now
nearer her (he falls forward, face down at her feet)."""


def edit(shots, f):
    for c in shots["2"]["cues"]:
        if c.get("do") == "anim" and c.get("actor") == "warden":
            c.update({"clip": "folk/m_kneel_lamp", "from": 0, "speed": 1, "blend": 0.6})
    s4 = shots["4"]
    s4["cues"].insert(0, {"at": 0.0, "do": "anim", "actor": "warden", "clip": "folk/m_lamp_down", "from": 0, "speed": 1, "blend": 0.3})
    s4["cam"]["at"] = {"actor": "warden", "bone": "hand_l", "off": [0, -0.55, 0], "track": True}
    s5 = shots["5"]
    for c in s5["cues"]:
        if c.get("do") == "anim" and c.get("actor") == "warden":
            c.update({"clip": "folk/m_fold_forward", "from": 0, "speed": 1, "blend": 0.2})
        if c.get("do") == "place" and c.get("actor") == "heart":
            c["where"] = {"mark": "w", "off": [0, 0, 2.0], "y": -1.25}
    s5["cam"]["at"] = {"mark": "w", "off": [0, 0.5, 1.6]}
    for c in shots["6"]["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart":
            c["to"] = {"mark": "w", "off": [0, 0, 2.0], "y": -0.35}
    shots["6"]["cam"]["pos"] = {"mark": "w", "off": [1.8, 0.9, 3.2]}
