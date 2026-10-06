def edit(S, f):
    for c in S["7"]["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart":
            c["to"] = {"mark": "her", "off": [0.42, 1.2, -0.5]}
    S["8"]["cam"] = {"pos": {"mark": "her", "off": [1.55, 1.3, -0.3]}, "at": {"mark": "her", "off": [0.43, 1.24, -0.18]}, "lens": 85,
                     "focus": {"actor": "heart"}, "fstop": 2.0}
    for c in S["8"]["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart":
            c["to"] = {"mark": "her", "off": [0.44, 1.24, -0.3]}
    S["10"]["cam"] = {"pos": {"mark": "her", "off": [0.55, 1.25, -0.3]}, "at": {"mark": "her", "off": [0.35, 1.35, -1.25]}, "lens": 35}
    for c in S["9"]["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart":
            c["to"] = {"mark": "her", "off": [0.35, 1.05, -1.0]}
