# cine6 r3j: s8 the chin spill went past blue light into pale blue skin: chin 2.5 -> 1.3, her warm key 0.45 -> 0.6.
def edit(shots, f):
    for c in shots["8"]["cues"]:
        if c.get("do") == "rig" and c.get("name") == "chin": c["energy"] = 1.3
        if c.get("do") == "rig" and c.get("name") == "skin": c["energy"] = 0.6
