# k10 pass 2 (C01): s3 framed whole from the side her face points, rigs down; s11 on the clip's own turn, side-on from the NE.
def edit(shots, f):
    f["shots"] = [s for s in f["shots"] if not s["id"].startswith("3v")]
    s3 = shots["3"]
    s3["cam"] = {"pos": {"actor": "her", "bone": "head", "off": [-1.25, 0.1, -0.45]}, "at": {"actor": "her", "bone": "head", "off": [0, -0.02, 0]},
                 "lens": 85, "focus": {"actor": "her", "bone": "head"}, "fstop": 2.0, "move": {"push": 0.08, "ease": "linear"}}
    for c in s3["cues"]:
        if c.get("do") == "rig": c["energy"] = 0.5 if c["name"] == "moon" else 0.45
    for c in shots["1"]["cues"]:
        if c.get("do") == "head": c["amount"] = 1.0; c["where"] = [-10.2, 0.0, 90.2]
    s11 = shots["11"]
    s11["cues"] = [c for c in s11["cues"] if c.get("do") != "look"]
    s11["cam"] = {"pos": [-6.0, 1.3, 87.6], "at": [-9.0, 1.15, 89.6], "lens": 32, "focus": {"mark": "reach", "off": [0, 1.0, 0]}, "fstop": 4.0}
