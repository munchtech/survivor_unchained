def edit(S, f):
    S["6"]["cam"] = {"pos": {"mark": "w", "off": [1.8, 0.9, -0.8]}, "at": {"actor": "heart", "track": True}, "lens": 50, "move": {"push": 0.6, "ease": "slow"}}
    for c in S["6"]["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart":
            c["to"] = {"mark": "w", "off": [0, 0, -2.4], "y": -0.35}
    S["9"]["cam"] = {"pos": {"mark": "her", "off": [3.4, 1.6, 0.6]}, "at": {"mark": "her", "off": [0.2, 1.0, -0.9]}, "lens": 28}
    S["10"]["cam"] = {"pos": {"actor": "her", "bone": "eyes", "off": [0.4, 0.15, 0.4]}, "at": {"mark": "her", "off": [0.35, 1.3, -1.25]}, "lens": 35}
