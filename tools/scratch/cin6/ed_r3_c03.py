# Round 3 (solver): C03 s9-s11. Grimtunnel waist-deep (sink 0.55) beside the Warden rather than on him,
# the heart held to his chest in his arms (his "hug" role), its light down to 0.4, her heading turned
# 0.26 off the Warden, s10/s11 reframed on the sunk height.
GRIM = [0.55, 0, -0.85]
HEART = [0.43, 0.56, -0.665]
def edit(shots, f):
    s9 = shots["9"]
    for c in s9["cues"]:
        if c.get("do") == "spawn" and c.get("actor") == "grim":
            c["where"] = {"mark": "her", "off": GRIM}; c["sink"] = 0.55
        if c.get("do") == "move" and c.get("actor") == "heart":
            c["to"] = {"mark": "her", "off": HEART}
    s9["cues"][1:1] = [
        {"do": "place", "mark": "her", "heading": 2.88},
        {"do": "lamp", "actor": "heart", "glow": 0.4},
        {"at": 0.5, "do": "anim", "actor": "grim", "clip": "hug"},
    ]
    s10 = shots["10"]
    s10["cam"]["pos"] = {"mark": "her", "off": [0.9, 1.75, 0.6]}
    s10["cam"]["at"] = {"mark": "her", "off": [0.55, 0.92, -0.85]}
    s11 = shots["11"]
    s11["cam"]["pos"] = {"mark": "her", "off": [3.2, 1.38, -1.6]}
    s11["cam"]["at"] = {"mark": "her", "off": [0.45, 1.12, -0.8]}
    for c in s11["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart":
            c["to"] = {"mark": "her", "off": GRIM, "y": -2.2}
