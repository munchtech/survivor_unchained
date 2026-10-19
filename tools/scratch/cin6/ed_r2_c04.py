def edit(shots, f):
    if "A7" in shots: shots["A7"]["cam"]["at"]["off"][1] = -0.03
    if "A2" in shots: shots["A2"]["dur"] = 2.2
    if "B4a" in shots: shots["B4a"]["dur"] = 1.7
    if "B4b" in shots: shots["B4b"]["dur"] = 1.7
