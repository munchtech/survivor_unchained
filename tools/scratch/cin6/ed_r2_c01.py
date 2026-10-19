# Judges j1r2/j2r2 (cinematics 3, round 2): C01.
def edit(shots, f):
    shots["6"]["dur"] = 6.4                                   # 1.6 s tail after the gaze
    # s8: the eye light flattened her (the ember already gives the catchlights): off.
    shots["8"]["cues"] = [c for c in shots["8"]["cues"] if not (c.get("do") == "rig" and c.get("name") == "eye")]
    for c in shots["7"]["cues"]:
        if c.get("do") == "rig" and c.get("name") == "rim":
            # Warm (the lamp up the road), above and just ahead of her crown (she faces -z), skimming the top the camera sees.
            c["color"] = "#ffd9b0"; c["energy"] = 2.0; c["angle"] = 25
            c["from"] = {"actor": "her", "bone": "eyes", "off": [0, 0.30, -0.15]}
            c["aim"] = {"actor": "her", "bone": "eyes", "off": [0, 0.12, 0.07]}
