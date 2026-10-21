# cine6 r3o: s8 after the snatch read gray-blue and the heart a blob at her waist: warm key back up, blue lower, the heart away.
def edit(shots, f):
    s8 = shots["8"]; T = 3.2
    for c in s8["cues"]:
        if c.get("at") == T + 0.05 and c.get("do") == "move": c["to"] = {"mark": "her", "off": [1.4, -0.6, -1.6]}
        if c.get("at") == T + 0.05 and c.get("do") == "lamp": c["glow"] = 0.6
        if c.get("at") == T + 0.05 and c.get("do") == "rig" and c.get("name") == "spill": c["energy"] = 0.4
    s8["cues"].append({"at": T + 0.05, "do": "rig", "name": "skin", "from": {"lens": [0.95, 0.55, -0.95]}, "aim": {"actor": "her", "bone": "head"},
                       "color": "#ffd8b0", "energy": 0.9, "angle": 32, "range": 6})
