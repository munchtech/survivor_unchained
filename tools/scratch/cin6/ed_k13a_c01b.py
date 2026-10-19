# k13a pass 2 (C01): s3's scene moon (atmosphere key, nearly overhead) lit her chest third: down to 0.12, the face's
# warm/cool split carried by the rigs (key up, moon overhead and wider on the head); eyes further toward the key.
# s6 grade 0.55 and its nape rig less saturated (skin 0.49-0.53 at 0.62). s7 higher over her shoulder so the prints read
# past the frost grass, the tilt ending low along the trail. s8b lips pressed to a hairline (mouth_open -0.08).
def edit(shots, f):
    for c in shots["3"]["cues"]:
        if c.get("do") == "atmosphere": c["key"] = 0.12
        if c.get("name") == "key": c.update({"energy": 0.7, "from": {"actor": "her", "bone": "head", "off": [-0.38, -0.7, 0.0]}})
        if c.get("name") == "moon": c.update({"energy": 0.6, "angle": 14, "from": {"actor": "her", "bone": "head", "off": [0.0, 1.0, 0.15]}})
        if c.get("name") == "fill": c["energy"] = 0.12
        if c.get("do") == "gaze": c["look"] = [0.9, 0.05]
    for c in shots["6"]["cues"]:
        if c.get("do") == "grade": c["sat"] = 0.55
        if c.get("name") == "nape": c["color"] = "#ff9a60"
    c7 = shots["7"]["cam"]
    c7.update({"pos": [-9.52, 1.55, 91.95], "at": [-8.72, 0.0, 87.2], "focus": 4.4})
    c7["move"].update({"at": [-7.6, 0.6, 74.0], "start": 0.8, "focus": {"abs": [-7.6, 0.6, 74.0]}})
    for c in shots["8b"]["cues"]:
        if c.get("do") == "face" and "at" not in c: c["keys"]["mouth_open"] = -0.08
