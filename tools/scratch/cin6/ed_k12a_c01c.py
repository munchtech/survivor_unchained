# k12a pass 3 (C01): s3's lights back to k12a3V's (moon high in front of her brow 0.55, ember from the ring's edge
# 0.32; the overhead moon of pass 1 never reached the face, which went all ember, S 0.58-0.73), a grade 0.8 on s3 and
# back to 1 on s6.
def edit(shots, f):
    for c in shots["3"]["cues"]:
        if c.get("name") == "moon": c.update({"energy": 0.55, "angle": 30, "from": {"actor": "her", "bone": "head", "off": [-0.45, 1.3, -0.55]}})
        if c.get("name") == "ember": c.update({"energy": 0.32, "angle": 30, "color": "#ffb070", "from": {"mark": "fire", "off": [0.3, 0.1, -0.05]}, "aim": {"actor": "her", "bone": "head"}})
    shots["3"]["cues"].insert(0, {"do": "grade", "sat": 0.8})
    shots["6"]["cues"].insert(0, {"do": "grade", "sat": 1})
