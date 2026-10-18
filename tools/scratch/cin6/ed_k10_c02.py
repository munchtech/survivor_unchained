# k10 (C02): the scene's darker night, mist on the river, the drowned against a lamp behind them; side keys on s4 and s8.
def edit(shots, f):
    c = shots["1"]["cues"]
    c.insert(0, {"do": "atmosphere", "preset": "night", "key": 0.4, "hemi": 0.45, "env": 0.45, "exposure": 0.92, "fog": 1.5, "fogColor": "#0a1018", "rim": 0.6})
    c.insert(1, {"do": "mist", "name": "river", "where": {"abs": [7.0, -1.15, -41.0]}, "size": [26, 1.5, 18], "density": 0.45, "color": "#8494aa", "falloff": 2.0})
    c.insert(2, {"do": "glow", "name": "back", "where": {"abs": [11.5, 0.6, -50.0]}, "color": "#8ac8ff", "size": 0.001, "energy": 3, "spread": 0.001, "halo": 0, "light": 4.0, "range": 14})
    shots["4"]["cues"].insert(0, {"do": "rig", "name": "key", "energy": 1.4, "color": "#8ac8ff", "angle": 30,
        "from": {"actor": "her", "bone": "eyes", "off": [0.25, -0.15, -0.9]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}})
    for x in shots["8"]["cues"]:
        if x.get("do") == "glow" and x.get("name") == "held": x["where"]["off"] = [0.34, 0.02, -0.14]; x["light"] = 0.45
        if x.get("do") == "rig" and x.get("name") == "ember": x["energy"] = 0.35; x["from"]["off"] = [-0.3, -0.1, -0.1]
    c12 = shots["12"]["cues"]
    c12.insert(0, {"do": "atmosphere", "preset": "night", "from": "now", "over": 2.0})
    c12.insert(1, {"do": "mist", "name": "river", "density": 0, "over": 2.0})
