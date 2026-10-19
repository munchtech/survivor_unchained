# k13a pass 3 (C01): s3's throat third still lit (the key's wide cone and a fill from the lens, which also put a
# catchlight dead centre: the doll stare): the key tight on her face, the fill off the lens toward the top of frame and
# narrow, the moon bluer. s8b lips pressed further (-0.2; -0.08 thinned the gap only a little).
def edit(shots, f):
    for c in shots["3"]["cues"]:
        if c.get("name") == "key": c.update({"energy": 0.9, "angle": 12, "aim": {"actor": "her", "bone": "head", "off": [0, 0.02, 0.05]}})
        if c.get("name") == "moon": c.update({"energy": 0.5, "color": "#8aa8ff"})
        if c.get("name") == "fill": c.update({"energy": 0.08, "angle": 10, "from": {"lens": [0, 0.35, 0]}})
    for c in shots["8b"]["cues"]:
        if c.get("do") == "face" and "at" not in c: c["keys"]["mouth_open"] = -0.2
