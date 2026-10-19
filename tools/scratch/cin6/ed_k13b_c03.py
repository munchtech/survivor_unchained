# k13b (C03 s3b): the lamp re-rigged (35 deg cone, low screen-right about 50 deg off the lens), a 2700 K bounce
# on the shadow side at 1/6, the moon rim up to 1.0.
def edit(shots, f):
    cs = shots["3b"]["cues"]
    for c in cs:
        if c.get("name") == "lamp":
            c.update({"energy": 1.2, "angle": 35})
            c["from"]["off"] = [-0.42, -0.3, -0.74]
        if c.get("name") == "moon": c["energy"] = 1.0
    i = next(k for k, c in enumerate(cs) if c.get("name") == "moon")
    cs.insert(i + 1, {"do": "rig", "name": "bounce", "energy": 0.2, "color": "#ffa757", "angle": 50,
                      "from": {"actor": "her", "bone": "eyes", "off": [0.8, -0.15, -0.14]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.06, 0]}})
