# cine6 r3n: after the snatch in s8 the heart's rigs blew her face and arm white-blue from close range: the heart goes further
# and lower (into his claws below frame), its glow down, the face/palm rigs softened to a low blue from below.
def edit(shots, f):
    s8 = shots["8"]; T = 3.2
    for c in s8["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart" and c.get("at") == T + 0.05:
            c["to"] = {"mark": "her", "off": [0.9, -0.1, -1.2]}; c["dur"] = 0.2
    s8["cues"] += [
        {"at": T + 0.05, "do": "lamp", "actor": "heart", "glow": 1.0, "over": 0.3},
        {"at": T + 0.05, "do": "rig", "name": "spill", "from": {"actor": "heart"}, "aim": {"actor": "her", "bone": "head"}, "color": "#4f8cff", "energy": 0.8, "angle": 40, "range": 3},
        {"at": T + 0.05, "do": "rig", "name": "chin", "from": {"actor": "heart"}, "aim": {"actor": "her", "bone": "head"}, "color": "#4f8cff", "energy": 0.0, "angle": 40, "range": 3},
    ]
