# k11b pass 2 (C02): s4/s8 ember halved and narrowed onto the near cheek (it flooded both cheeks orange); s8's lamp up.
def edit(shots, f):
    for c in shots["4"]["cues"]:
        if c.get("do") == "rig" and c.get("name") == "ember": c.update({"energy": 0.28, "angle": 16, "color": "#ff7a4a"})
    for c in shots["8"]["cues"]:
        if c.get("do") == "rig" and c.get("name") == "ember": c.update({"energy": 0.25, "angle": 14, "color": "#ff7a4a"}); c["aim"]["off"] = [-0.06, -0.06, -0.03]
        if c.get("do") == "glow" and c.get("name") == "held": c["light"] = 0.5
