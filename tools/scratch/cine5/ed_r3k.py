# cine6 r3k: the confirmation judge's s9 restage: a medium on her from just behind and above Grimtunnel's hat, his lanterns a soft
# glow at the bottom edge, the heart's blue on her from below; his lines play over her. s8 notes: chin light bluer and -25%, f/5.6.
def edit(shots, f):
    s8, s9 = shots["8"], shots["9"]
    s8["cam"]["fstop"] = 5.6
    for c in s8["cues"]:
        if c.get("do") == "rig" and c.get("name") == "chin": c.update({"energy": 1.0, "color": "#4f8cff"})
    s9["cam"] = {"pos": {"mark": "her", "off": [1.8, 1.8, -1.3]}, "at": {"mark": "her", "off": [0.0, 1.55, 0.0]}, "lens": 50,
                 "focus": {"actor": "her", "bone": "eyes"}, "fstop": 2.8, "move": {"push": 0.12, "ease": "slow"}}
    s9["type"] = "MS"
    s9["note"] = ("A medium on her from just behind Grimtunnel's hat (his model is a placeholder: only his lanterns' glow at the bottom edge): "
                  "the burst, she snaps into her guard and looks down at him, the heart's blue on her from below. G1; sniffs; G2 over her; "
                  "G3 starts and runs on over the crane.")
    for c in s9["cues"]:
        if c.get("do") == "rig" and c.get("name") == "skin": c["energy"] = 0.5
    s9["cues"] += [
        {"do": "rig", "name": "spill", "from": {"actor": "heart"}, "aim": {"actor": "her", "bone": "head"}, "color": "#4f8cff", "energy": 1.4, "angle": 40, "range": 3},
        {"do": "rig", "name": "chin", "from": {"actor": "heart"}, "aim": {"actor": "her", "bone": "head"}, "color": "#4f8cff", "energy": 0.0, "angle": 40, "range": 3},
    ]
