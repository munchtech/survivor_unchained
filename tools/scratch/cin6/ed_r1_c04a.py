def edit(shots, f):
    shots["A2"]["dur"] = 2.4
    shots["A3"]["cam"]["at"]["off"] = [0, 1.52, 0]
    shots["A5"]["cam"]["at"]["off"] = [0, -0.04, 0]
    shots["A7"]["cam"]["at"]["off"] = [0, -0.05, 0]
    shots["A7"]["note"] = shots["A7"]["note"].replace("hold 3 s of silence", "hold 1.5 s of silence")
    for k in ("A5", "A7"):
        for c in shots[k]["cues"]:
            if c.get("do") == "rig" and c.get("name") == "eye": c["angle"] = 5
