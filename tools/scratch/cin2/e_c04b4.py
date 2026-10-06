W = [30.9, 7.9, -6.6]


def edit(S, f):
    f["marks"]["window"] = [W[0], W[1], W[2]]
    for c in S["B1"]["cues"]:
        if c.get("do") == "glow":
            c["where"] = {"abs": W}
    S["B4a"]["cam"] = {"pos": [4.0, 1.8, 8.0], "at": {"abs": W}, "lens": 135}
    S["B4a"]["still"] = 0.3
    for c in S["B4"]["cues"]:
        if c.get("do") == "look":
            c["where"] = {"abs": W}
