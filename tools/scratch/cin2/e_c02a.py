def edit(S, f):
    S["2"]["cam"] = {"pos": {"abs": [6.0, -0.75, -37.6]}, "at": {"abs": [11.0, -0.5, -44.5]}, "lens": 35}
    S["3"]["cam"] = {"pos": {"abs": [4.1, -0.75, -42.2]}, "at": {"abs": [5.0, -0.3, -44.3]}, "lens": 85, "move": {"push": 0.3, "ease": "linear"}}
    for c in S["1"]["cues"]:
        if c.get("do") == "glow": c.update({"size": 0.05, "spread": 6, "light": 1.5, "range": 5})
    S["5"]["still"] = 4.2
    for c in S["5"]["cues"]:
        if c.get("do") == "anim": c["speed"] = 0.45
        if c.get("do") == "move" and c.get("actor") == "warden": c["dur"] = 1.2
    S["6"]["cam"]["at"] = {"actor": "warden", "bone": "chest", "off": [0, 0.5, 0], "track": True}
    S["6"]["cam"]["lens"] = 28
    S["7"]["cam"] = {"pos": [-4.6, 1.2, -29.4], "at": {"abs": [2.8, 0.9, -32.3]}, "lens": 28}
    for c in S["7"]["cues"]:
        if c.get("do") == "anim" and c.get("actor") == "warden": c["clip"] = "Idle_Lantern"
    S["8"]["cam"] = {"pos": {"actor": "her", "bone": "eyes", "off": [-0.45, -0.03, -0.95]}, "at": {"actor": "her", "bone": "eyes", "off": [0, -0.035, 0]}, "lens": 135, "focus": {"actor": "her", "bone": "eyes"}, "fstop": 2.0}
    S["8"]["cues"].insert(1, {"do": "glow", "name": "held", "where": {"abs": [2.3, 0.98, -31.5]}, "color": "#8ac8ff", "size": 0.05, "energy": 3, "spread": 5, "halo": 0.5, "light": 2.0, "range": 2.2})
    S["9"]["cues"].append({"at": 1.4, "do": "glow", "name": "held", "remove": True})
    S["10"]["cam"] = {"pos": {"abs": [1.8, -0.6, -32.0]}, "at": {"abs": [9.6, -0.3, -43.5]}, "lens": 28}
