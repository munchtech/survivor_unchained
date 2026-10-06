def edit(S, f):
    S["1"]["cam"] = {"pos": [4.4, 1.5, -25.4], "at": {"abs": [4.6, -0.3, -44.0]}, "lens": 28}
    # The lamp in the fist, until his own lamp reads at this size: a glow held where his hand is.
    S["1"]["cues"].insert(3, {"do": "glow", "name": "lamp", "where": {"abs": [6.45, 0.12, -44.0]}, "color": "#8ac8ff", "size": 0.06, "energy": 4, "spread": 7, "halo": 0.6, "light": 1.6, "range": 6})
    S["3"]["cam"] = {"pos": {"abs": [5.2, -0.45, -42.1]}, "at": {"abs": [6.45, 0.0, -44.0]}, "lens": 85, "move": {"push": 0.25, "ease": "linear"}}
    S["5"]["cues"] = [c for c in S["5"]["cues"] if not (c.get("do") == "glow")]
    S["5"]["cues"].insert(0, {"do": "glow", "name": "lamp", "remove": True})
    for c in S["5"]["cues"]:
        if c.get("actor") == "warden" and c.get("do") in ("place", "move"):
            c["heading"] = -0.6
    S["5"]["cam"] = {"pos": {"abs": [2.4, -0.7, -40.2]}, "at": {"abs": [5.0, 1.5, -44.5]}, "lens": 24}
    S["9"]["cam"] = {"pos": [3.3, 0.5, -31.3], "at": {"actor": "warden", "bone": "head"}, "lens": 50}
