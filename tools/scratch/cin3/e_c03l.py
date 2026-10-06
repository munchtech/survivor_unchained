def edit(shots, f):
    c = shots["4"]["cam"]
    c["pos"] = {"actor": "warden", "bone": "hand_l", "off": [1.6, -0.6, 1.4]}
    c["at"] = {"actor": "warden", "bone": "hand_l", "off": [0, -0.55, 0], "track": True}
    c["lens"] = 35
