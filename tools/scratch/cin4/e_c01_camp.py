def edit(shots, f):
    # The fire is coals only now: no flames, and its light low over them, dimmer.
    for c in shots["1"]["cues"]:
        if c["do"] == "fire":
            c["flames"] = 0.0
        if c["do"] == "light":
            c["level"] = 0.24
    # Shot 5 as written: from the fire's far (west) side, through the coals' light, at her.
    s5 = shots["5"]
    s5["cam"] = {"pos": [-11.6, 0.5, 91.05], "at": {"actor": "her", "bone": "chest", "off": [0, 0.1, 0]}, "lens": 45,
                 "focus": {"actor": "her", "bone": "head"}, "fstop": 2.4}
    s5["note"] = "From the fire's far (west) side, low, in the coals' light: she pushes up onto her elbow, her face down, her hair hanging."
    # Shot 6: her face and her hands both in, as she comes up onto her heels.
    shots["6"]["cam"]["at"] = {"actor": "her", "bone": "chest", "off": [0, 0.22, 0], "track": True}
    shots["6"]["cam"]["lens"] = 35
    shots["6"]["note"] = "Front three-quarter from her left, across the coals: she comes up onto her heels and looks down at her hands, the cord and the full flask; across at the bedroll, dry; down again. N1."
    # Shot 6a: focus on the hand wherever this body puts it.
    shots["6a"]["cam"]["focus"] = {"actor": "her", "bone": "hand_r", "track": True}
