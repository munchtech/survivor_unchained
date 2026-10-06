HEAD = {"actor": "warden", "bone": "head", "off": [0, 0.3, 0]}


def edit(S, f):
    S["1"]["cam"] = {"pos": {"mark": "w", "off": [-1.6, 3.7, 2.6]}, "at": HEAD, "lens": 50, "focus": HEAD, "fstop": 2.8}
    S["2"]["cam"] = {"pos": {"mark": "w", "off": [-6.0, 0.5, 5.5]}, "at": {"mark": "w", "off": [0, 1.5, 0]}, "lens": 28}
    S["3"]["cam"] = {"pos": {"mark": "w", "off": [0.8, 0.8, 2.2]}, "at": HEAD, "lens": 50, "focus": HEAD, "fstop": 2.8}
    S["4"]["cam"] = {"pos": {"mark": "w", "off": [2.0, 0.5, 2.6]}, "at": {"actor": "warden", "bone": "hand_l", "off": [0, -0.3, 0]}, "lens": 65}
    S["5"]["cam"] = {"pos": {"mark": "her", "off": [1.3, 1.7, 3.6]}, "at": {"mark": "w", "off": [0, 0.5, -1.2]}, "lens": 28}
    for c in S["5"]["cues"]:
        if c.get("do") == "place" and c.get("actor") == "heart":
            c["where"] = {"mark": "w", "off": [0, 0, -2.4], "y": -1.25}
    S["6"]["cam"] = {"pos": {"mark": "w", "off": [1.8, 0.9, -0.8]}, "at": {"mark": "w", "off": [0, 0, -2.4], "y": -0.5}, "lens": 50, "move": {"push": 0.6, "ease": "slow"}}
    for c in S["6"]["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart":
            c["to"] = {"mark": "w", "off": [0, 0, -2.4], "y": -0.2}
    for c in S["7"]["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart":
            c["dur"] = 3.4
    S["8"]["cam"] = {"pos": {"actor": "heart", "off": [-1.4, 0.05, 0.25]}, "at": {"actor": "heart", "off": [0, 0, 0.18]}, "lens": 85, "focus": {"actor": "heart"}, "fstop": 2.0}
    S["9"]["cam"] = {"pos": {"mark": "her", "off": [3.0, 1.5, -0.6]}, "at": {"mark": "her", "off": [0.2, 0.8, -1.1]}, "lens": 35}
    for c in S["9"]["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart":
            c["to"] = {"mark": "her", "off": [0.35, 1.05, -1.0]}
    S["10"]["cam"] = {"pos": {"actor": "her", "bone": "eyes", "off": [0.25, 0.05, -0.3]}, "at": {"mark": "her", "off": [0.35, 0.9, -1.25]}, "lens": 35}
    S["11"]["cam"] = {"pos": {"mark": "her", "off": [3.2, 1.2, -1.6]}, "at": {"mark": "her", "off": [0.35, 0.6, -1.25]}, "lens": 35}
    S["12"]["cam"] = {"pos": {"abs": [34.0, 6.5, -38.5]}, "at": {"mark": "her", "off": [0, 0, 0]}, "lens": 24}
    S["12"]["cues"].insert(0, {"do": "event", "name": "grim_gone"})
