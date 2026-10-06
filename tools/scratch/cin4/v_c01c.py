def EDIT(shots, d):
    for c in shots["1"]["cues"]:
        if c["do"] == "light":
            c["level"] = 0.24
        if c["do"] == "fire":
            c["flames"] = 0.0


V = {
    "5": [
        {"id": "5C", "cam": {"pos": [-11.6, 0.5, 91.05], "at": {"actor": "her", "bone": "chest", "off": [0, 0.1, 0]}, "lens": 45, "focus": {"actor": "her", "bone": "head"}, "fstop": 2.4}},
    ],
    "6a": [
        {"id": "6aC", "cam": {"pos": [-9.95, 0.75, 91.35], "at": [-10.2, 0.28, 90.6], "lens": 40, "focus": {"actor": "her", "bone": "hand_r"}, "fstop": 2.8}},
        # Lower, the hand against the dark beyond the ring.
        {"id": "6aE", "cam": {"pos": [-10.1, 0.42, 91.45], "at": [-10.1, 0.36, 90.55], "lens": 40, "focus": {"actor": "her", "bone": "hand_r"}, "fstop": 2.4}},
    ],
}
