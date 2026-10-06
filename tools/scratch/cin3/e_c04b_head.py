"""C04 B: Rook lifts her head to the lamp (not her body), and brings it back down to the survivor."""


def edit(shots, f):
    for c in shots["B4"]["cues"]:
        if c.get("do") == "look":
            c["do"] = "head"
            c["over"] = 0.7
    s = shots["B4b"]
    s["cues"] = [c for c in s["cues"] if c.get("do") != "look"]
    s["cues"].insert(0, {"do": "head", "actor": "rook", "amount": 0, "over": 0.6})
