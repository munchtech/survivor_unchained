def edit(S, f):
    S["4"]["cam"] = {"pos": {"mark": "w", "off": [2.8, 1.0, 2.2]}, "at": {"actor": "warden", "bone": "hand_l", "off": [0, -0.25, 0]}, "lens": 35}
    S["10"]["cam"] = {"pos": {"mark": "her", "off": [0.55, 1.25, -0.3]}, "at": {"mark": "her", "off": [0.35, 1.55, -1.25]}, "lens": 28}
    for c in S["6"]["cues"]:
        if c.get("do") == "lamp" and c.get("actor") == "heart":
            c["glow"] = 0.8
