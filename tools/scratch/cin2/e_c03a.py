def edit(S, f):
    for c in S["12"]["cues"]:
        if c.get("do") == "atmosphere":
            c.clear(); c.update({"do": "atmosphere", "preset": "Dawn", "from": "Night", "k1": 0.2, "over": 7.0})
