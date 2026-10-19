# k13b round 2 (C03 s3b): the 35 deg lamp bleached her cheek (luma 160, S 0.07): down to 0.6, the bounce kept at 1/6.
def edit(shots, f):
    for c in shots["3b"]["cues"]:
        if c.get("name") == "lamp": c["energy"] = 0.6
        if c.get("name") == "bounce": c["energy"] = 0.1
