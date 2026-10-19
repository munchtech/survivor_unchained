# Judges j1/j2 round 1 (cinematics 2).
def edit(shots, f):
    shots["6a"]["dur"] = 2.0
    shots["10"]["cam"]["at"]["off"] = [0, 0.03, 0]           # top of her head clear of the bar
    s11 = shots["11"]
    s11["dur"] = 2.2
    for c in s11["cues"]:
        if c.get("clip") == "PickUp_Table": c["from"] = 0.45     # the cut lands mid-bend, hand to the hilt
        if c.get("clip") == "@idle": c["at"] = 1.0                # comes round ready sooner (no 1 s freeze)
    s12 = shots["12"]
    s12["cam"]["at"] = {"actor": "her", "bone": "chest", "off": [0, 0.2, 0], "track": True}   # on her, not the end mark
    for k in ("8", "8b"):
        for c in shots[k]["cues"]:
            if c.get("do") == "rig" and c.get("name") == "eye": c["angle"] = 5
    shots["8b"]["cam"]["move"] = {"push": 0.05, "ease": "linear"}
    for c in shots["7"]["cues"]:
        if c.get("do") == "rig" and c.get("name") == "rim":
            c["from"] = {"actor": "her", "bone": "head", "off": [0, 0.45, -0.5]}   # the far side of her head from the camera
            c["energy"] = 1.5
