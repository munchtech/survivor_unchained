# k11b pass 2 (C04 A): A5 panned right so the near ford post leaves frame left; A8's road mist thicker.
def edit(shots, f):
    shots["A5"]["cam"]["at"]["off"] = [-0.27, -0.1, 0.13]
    for c in shots["A8"]["cues"]:
        if c.get("do") == "mist" and "where" in c: c["density"] = 1.6
