# Round 3 (solver), pass 2: Grimtunnel further east, clear of her blade's tip; turned to her; the heart in his
# arms for that; s10 from beside her at her eye height (lower, longer lens, under his brim); s11 her eyes in.
GRIM = [1.0, 0, -0.5]
HEART = [0.80, 0.56, -0.40]
def edit(shots, f):
    s9 = shots["9"]
    cues = []
    for c in s9["cues"]:
        if c.get("do") == "spawn" and c.get("actor") == "grim": c["where"] = {"mark": "her", "off": GRIM}
        if c.get("do") == "move" and c.get("actor") == "heart": c["to"] = {"mark": "her", "off": HEART}
        if c.get("do") == "anim" and c.get("actor") == "grim": c["where"] = {"mark": "her"}
        cues.append(c)
        if c.get("do") == "event" and c.get("name") == "grim_up":
            cues.append({"do": "anim", "actor": "grim", "where": {"mark": "her"}})
    s9["cues"] = cues
    s10 = shots["10"]
    s10["cam"]["pos"] = {"mark": "her", "off": [1.55, 1.72, 2.0]}
    s10["cam"]["at"] = {"mark": "her", "off": [0.92, 0.9, -0.45]}
    s10["cam"]["lens"] = 45
    s11 = shots["11"]
    s11["cam"]["pos"] = {"mark": "her", "off": [3.4, 1.38, -1.6]}
    s11["cam"]["at"] = {"mark": "her", "off": [0.55, 1.25, -0.4]}
    s11["cam"]["lens"] = 32
    for c in s11["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart": c["to"] = {"mark": "her", "off": GRIM, "y": -2.2}
