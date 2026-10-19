# Round 3 (solver), pass 2: she comes round past R1's line a little toward the lens (her body ends about -1.30).
def edit(shots, f):
    for c in shots["11"]["cues"]:
        if c.get("do") == "look": c.update({"at": 0.3, "where": {"mark": "reach", "off": [0.24, 0, -2.99]}, "over": 1.0})
