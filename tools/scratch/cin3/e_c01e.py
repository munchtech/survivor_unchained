"""C01: looks with the head, not the body. 7: over her shoulder to the trail and its prints; held through 8b;
10: whipped round to R1 as she rises, then let go."""


def edit(shots, f):
    s = shots["7"]
    s["cues"] = [c for c in s["cues"] if c.get("do") != "look"]
    s["cues"].insert(0, {"at": 0.0, "do": "head", "where": [-8.9, 0.3, 86.5], "over": 1.2})
    s = shots["10"]
    s["cues"] = [c for c in s["cues"] if c.get("do") != "look"]
    s["cues"].insert(0, {"at": 0.12, "do": "head", "where": {"mark": "r1", "off": [0, 1.2, 0]}, "over": 0.18})
    s["cues"].append({"at": 1.4, "do": "head", "amount": 0, "over": 0.5})
