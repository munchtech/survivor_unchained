# k11b pass 3: s4 ember between passes 1 and 2; s10's rows light up; A5 half the pan back, every post globe dimmed.
def edit(shots, f):
    if f["id"] == "c02":
        for c in shots["4"]["cues"]:
            if c.get("do") == "rig" and c.get("name") == "ember": c["energy"] = 0.4
        for c in shots["10"]["cues"]:
            if c.get("do") == "rig" and c.get("name") == "rows": c["energy"] = 8.0
    else:
        a5 = shots["A5"]; a5["cam"]["at"]["off"] = [-0.13, -0.1, 0.06]
        a5["cues"] = [c for c in a5["cues"] if c.get("do") != "globe"]
        a5["cues"][3:3] = [{"do": "globe", "light": i, "level": 0.25} for i in (4, 5, 6)]
