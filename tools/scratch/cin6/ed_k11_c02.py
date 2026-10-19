# k11b (C02): s8 restaged (30 deg round, 80 mm, lamp out of frame left, ember on the near cheek, eyes to the lamp);
# s4 relit (deeper, softer blue key raised, ember on the near cheek); the night: water down, per-shot mist for the high
# cameras (s1, s11), no rim on the drowned in s1-s2, s2 backed off, s10 lit rows + focus + tilt, s11 tilt/truck;
# post globes 2 stops down until s12 brings them back; s3 CUT (lead).
def edit(shots, f):
    thick = {"do": "mist", "name": "river", "where": {"abs": [7.0, -0.8, -41.0]}, "size": [26, 2.2, 18], "density": 0.75, "color": "#8494aa", "falloff": 2.0}
    low = {"do": "mist", "name": "river", "where": {"abs": [7.0, -1.15, -41.0]}, "size": [26, 1.5, 18], "density": 0.45, "color": "#8494aa", "falloff": 2.0}
    base = {"do": "atmosphere", "preset": "night", "key": 0.4, "hemi": 0.45, "env": 0.45, "exposure": 0.92, "fog": 1.5, "fogColor": "#0a1018", "rim": 0.6}
    c1 = shots["1"]["cues"]
    for c in c1:
        if c.get("do") == "atmosphere": c["rim"] = 0
        if c.get("do") == "mist": c.update(thick)
    c1[3:3] = [{"do": "water", "level": 0.4}] + [{"do": "globe", "light": i, "level": 0.25} for i in (4, 5, 6)]
    shots["1"]["cam"] = {"pos": [3.4, 1.5, -25.4], "at": {"abs": [3.6, -0.95, -44.0]}, "lens": 28}
    shots["2"]["cam"]["pos"] = {"abs": [3.73, -0.75, -34.58]}
    shots["2"]["cues"] = [dict(low)]
    f["shots"] = [s for s in f["shots"] if s["id"] != "3"]
    c4 = shots["4"]["cues"]
    c4[0] = {"do": "rig", "name": "key", "energy": 0.8, "color": "#6a9ae6", "angle": 30, "from": {"actor": "her", "bone": "eyes", "off": [0.25, 0.1, -0.9]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}}
    c4[0:0] = [dict(base)]
    c4.insert(2, {"do": "rig", "name": "ember", "energy": 0.55, "color": "#ff6a33", "angle": 30, "range": 0.6, "from": {"actor": "her", "bone": "eyes", "off": [-0.35, -0.1, -0.2]}, "aim": {"actor": "her", "bone": "eyes", "off": [-0.05, -0.05, 0]}})
    s8 = shots["8"]
    s8["cam"] = {"pos": {"actor": "her", "bone": "eyes", "off": [-0.5, 0.05, -0.87]}, "at": {"actor": "her", "bone": "eyes", "off": [0, -0.045, 0]}, "lens": 80, "focus": {"actor": "her", "bone": "eyes"}, "fstop": 2.0}
    for c in s8["cues"]:
        if c.get("do") == "rig" and c.get("name") == "ember": c["energy"] = 0.6; c["range"] = 0.6; c["from"]["off"] = [-0.35, -0.15, -0.25]
        if c.get("do") == "glow" and c.get("name") == "held": c["where"]["off"] = [0.4, 0.1, -0.15]; c["light"] = 0.22; c["range"] = 0.8
    s8["cues"].insert(4, {"do": "gaze", "look": [-0.3, -0.25], "wander": 0.06})
    s10 = shots["10"]
    s10["cam"] = {"pos": {"abs": [1.4, -0.5, -31.6]}, "at": {"abs": [10.4, -1.18, -43.4]}, "lens": 65, "focus": {"abs": [10.4, -0.7, -43.4]}, "fstop": 2.8}
    s10["cues"].insert(0, {"do": "rig", "name": "rows", "energy": 3.0, "color": "#8ac8ff", "angle": 20, "from": {"actor": "her", "bone": "head", "off": [0, 0.3, 0]}, "aim": {"abs": [10.4, -0.7, -43.4]}})
    shots["11"]["cam"] = {"pos": [-6.34, 0.7, -25.05], "at": {"abs": [5.16, 2.18, -39.05]}, "lens": 24}
    shots["11"]["cues"].insert(0, dict(thick))
    c12 = shots["12"]["cues"]
    c12[2:2] = [{"do": "water", "level": 1, "over": 2.0}] + [{"do": "globe", "light": i, "level": 1, "over": 2.0} for i in (4, 5, 6)]
