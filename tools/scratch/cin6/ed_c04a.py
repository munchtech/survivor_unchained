def edit(shots, f):
    c = shots["A1"]["cues"]
    c.insert(4, {"at": 0.6, "do": "line", "id": "cin_first_light.reeds", "when": {"facts": ["!prologue.reeds_said"]}})
