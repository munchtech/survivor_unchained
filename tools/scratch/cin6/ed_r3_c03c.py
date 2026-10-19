# Lead, after the solver: he faces south in s9-s10 (open to the s9 east camera and s10's), the heart in his arms there;
# in s11 he has turned away from her to dive (G3 "half over his shoulder"), seen 3/4 from the north-east, her beyond him.
S9_FACE = {"mark": "her", "off": [1.0, 0, 3.0]}
S11_FACE = {"mark": "her", "off": [3.0, 0, -1.5]}
def edit(shots, f):
    for c in shots["9"]["cues"]:
        if c.get("do") == "anim" and c.get("actor") == "grim": c["where"] = S9_FACE
        if c.get("do") == "move" and c.get("actor") == "heart": c["to"] = {"mark": "her", "off": [1.0, 0.56, -0.28]}
    s11 = shots["11"]
    s11["cam"]["pos"] = {"mark": "her", "off": [2.0, 1.38, -2.9]}
    s11["cam"]["at"] = {"mark": "her", "off": [0.7, 1.15, -0.4]}
    s11["cues"][0:0] = [{"do": "anim", "actor": "grim", "clip": "hug", "where": S11_FACE},
                        {"do": "move", "actor": "heart", "to": {"mark": "her", "off": [1.2, 0.56, -0.6]}, "dur": 0.05}]
